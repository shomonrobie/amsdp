"""QUE-006 F4 — the queue payload carries the appointment's booking snapshot.

An announcement tells the patient which room to walk into, so that room has to
be the one they were given at booking or check-in — the snapshot on
``appointments`` (``AMSDP-FACILITY-DOCTOR-01``), never the doctor's *current*
schedule session.  The queue service resolves that snapshot for a whole page in
one query and serialises it as four additive fields:

    room_id, room_name, location_label, room_source

This module is the test of record for that contract.  It has three parts:

* **Pure helpers** (``common/locations.py``) — the label format, the empty
  "no room" answer, and the rule that a floor or department without a room name
  is *not* announceable (the caller must fall back to the approved room-less
  sentence rather than invent a room).
* **The serializer** (``queuing/main._entry_to_dict``) — additive and backward
  compatible: an entry with no resolved room keeps four empty strings instead of
  raising, which is what keeps every pre-existing caller working.
* **End to end over PostgreSQL** — a real staff JWT, a real queue entry, and the
  real ``GET /api/v1/queue`` page, asserting the snapshot appears, that a
  walk-in announces without a room, that two appointments on one page keep their
  own rooms, that the page costs **one** appointments query, and that the
  recovery payload (``queuing/recovery._entry_payload``) reports the same room.

Rows are written to the throwaway development database and cleared with
``purge_org`` at the start of every test; reference rows (organization, branch,
doctor, user) are reused because the append-only audit trail points at them.
"""

import os
import sys
import uuid
from contextlib import contextmanager
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import event

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "queuing"))

from amsdp_test_support import (ensure_branch, ensure_doctor, ensure_org,  # noqa: E402
                                ensure_patient, ensure_user, headers,
                                purge_org)

from common.database import SessionFactory, engine  # noqa: E402
from common.locations import (NO_ROOM, ROOM_SOURCE_APPOINTMENT,  # noqa: E402
                             location_label, room_payload)
from common.models import Appointment, QueueEntry  # noqa: E402

from queuing import recovery  # noqa: E402
from queuing.main import _entry_to_dict, app as queue_app  # noqa: E402

queue_client = TestClient(queue_app)

ORG = "queue-room-org"
BR = "queue-room-br"
DOC = "queue-room-doc"
PAT = "queue-room-pat"
DESK = "queue_room_desk"
TODAY = date.today()


# ---------------------------------------------------------------------------
# Fixtures / seed helpers
# ---------------------------------------------------------------------------

def _seed():
    """Clean slate first, then the reference rows.

    ``purge_org`` deletes the organization's *business* rows — and a patient is a
    business row, so it must be re-created afterwards or the appointment insert
    fails its foreign key. Reference rows (organization, branch, doctor, user)
    are idempotent and kept forever because the append-only audit trail points at
    them.
    """
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Room Snapshot")
    ensure_patient(PAT, ORG, name="Room Snapshot Patient")
    ensure_user(DESK, "receptionist", ORG, BR)


def _appointment(*, room: str = "204", floor: str = "2nd Floor",
                 department: str = "Cardiology") -> str:
    """An appointment row carrying the booking-time chamber snapshot.

    Only the ``*_name`` columns are set: the snapshot is what an announcement
    needs, and leaving the ``*_id`` foreign keys NULL keeps the fixture free of
    facility-hierarchy rows this module does not test.
    """
    appointment_id = str(uuid.uuid4())
    s = SessionFactory()
    try:
        s.add(Appointment(
            id=appointment_id, organization_id=ORG, branch_id=BR,
            patient_id=PAT, doctor_id=DOC, appointment_date=TODAY,
            start_time="10:00", status="BOOKED", status_history=[],
            booking_source="reception", appointment_type="scheduled",
            floor_name=floor, department_name=department, room_name=room))
        s.commit()
    finally:
        s.close()
    return appointment_id


def _entry(position: int, token: str, *, appointment_id=None,
           entry_source: str = "appointment", status: str = "waiting") -> str:
    entry_id = str(uuid.uuid4())
    s = SessionFactory()
    try:
        s.add(QueueEntry(
            id=entry_id, organization_id=ORG, branch_id=BR, doctor_id=DOC,
            date=TODAY, position=position, token=token, status=status,
            patient_id=PAT, appointment_id=appointment_id,
            entry_source=entry_source, status_history=[], position_history=[]))
        s.commit()
    finally:
        s.close()
    return entry_id


def _queue_page() -> dict:
    r = queue_client.get(
        "/api/v1/queue",
        params={"doctor_id": DOC, "date": str(TODAY), "branch_id": BR},
        headers=headers(DESK))
    assert r.status_code == 200, r.text
    return r.json()


def _entry_payload(page: dict, entry_id: str) -> dict:
    by_id = {e["id"]: e for e in page["entries"]}
    assert entry_id in by_id, f"entry {entry_id} missing from page: {page}"
    return by_id[entry_id]


@contextmanager
def _count_appointment_selects():
    """Record every SQL statement that reads ``appointments``."""
    statements = []

    def _record(conn, cursor, statement, parameters, context, executemany):
        if "FROM appointments" in statement:
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", _record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _record)


class _Snapshot:
    """Duck-typed stand-in for the three snapshot columns on ``Appointment``."""

    def __init__(self, floor_name=None, department_name=None, room_name=None,
                 room_id=None):
        self.floor_name = floor_name
        self.department_name = department_name
        self.room_name = room_name
        self.room_id = room_id


# ---------------------------------------------------------------------------
# Pure helpers — one definition of how a snapshot reads
# ---------------------------------------------------------------------------

def test_location_label_names_the_chamber_snapshot():
    label = location_label(_Snapshot("2nd Floor", "Cardiology", "204"))
    assert label == "2nd Floor / Cardiology / 204"


def test_location_label_omits_parts_the_clinic_does_not_model():
    # A small clinic with no building model still reads sensibly.
    assert location_label(_Snapshot(None, None, "204")) == "204"
    assert location_label(_Snapshot("Ground Floor", None, "104")) == \
        "Ground Floor / 104"


def test_location_label_of_no_snapshot_is_empty():
    assert location_label(None) == ""
    assert location_label(_Snapshot()) == ""


def test_no_room_is_the_empty_answer_and_clears_every_field():
    payload = room_payload(None)
    assert payload == NO_ROOM
    assert payload == {"room_id": "", "room_name": "", "label": "", "source": ""}


def test_room_payload_without_a_room_name_is_not_announceable():
    """A floor or department alone must never be published as a room.

    The approved sentence names a room; with no room name the caller announces
    the approved room-less variant.  ``source`` staying empty is what tells it
    to do that — a non-empty source here would announce a room that does not
    exist.
    """
    payload = room_payload(_Snapshot("2nd Floor", "Cardiology", None, "flr-2"))
    assert payload["room_name"] == ""
    assert payload["source"] == ""
    assert payload["label"] == "2nd Floor / Cardiology"


def test_room_payload_names_the_booking_snapshot_as_its_source():
    payload = room_payload(_Snapshot("2nd Floor", "Cardiology", "204", "room-204"))
    assert payload == {
        "room_id": "room-204",
        "room_name": "204",
        "label": "2nd Floor / Cardiology / 204",
        "source": ROOM_SOURCE_APPOINTMENT,
    }


# ---------------------------------------------------------------------------
# Serializer — additive, backward compatible
# ---------------------------------------------------------------------------

def test_entry_dict_without_a_room_keeps_four_empty_room_fields():
    """Every pre-existing caller passes no room and must keep working."""
    entry = QueueEntry(
        id="e-no-room", organization_id=ORG, branch_id=BR, doctor_id=DOC,
        date=TODAY, position=1, token="T-001", status="waiting",
        patient_id=PAT, appointment_id=None, entry_source="walk_in",
        status_history=[], position_history=[])

    payload = _entry_to_dict(entry)

    assert payload["room_id"] == ""
    assert payload["room_name"] == ""
    assert payload["location_label"] == ""
    assert payload["room_source"] == ""
    # The pre-existing contract is unchanged.
    assert payload["token"] == "T-001"
    assert payload["entry_source"] == "walk_in"


def test_entry_dict_carries_the_resolved_room():
    entry = QueueEntry(
        id="e-room", organization_id=ORG, branch_id=BR, doctor_id=DOC,
        date=TODAY, position=1, token="T-002", status="waiting",
        patient_id=PAT, appointment_id="appt-1", entry_source="appointment",
        status_history=[], position_history=[])

    room = room_payload(_Snapshot("2nd Floor", "Cardiology", "204", "room-204"))
    payload = _entry_to_dict(entry, room)

    assert payload["room_id"] == "room-204"
    assert payload["room_name"] == "204"
    assert payload["location_label"] == "2nd Floor / Cardiology / 204"
    assert payload["room_source"] == ROOM_SOURCE_APPOINTMENT


# ---------------------------------------------------------------------------
# End to end over the real queue service
# ---------------------------------------------------------------------------

def test_queue_page_announces_the_snapshotted_chamber():
    _seed()
    appointment_id = _appointment()
    entry_id = _entry(1, "T-F4-001", appointment_id=appointment_id)

    payload = _entry_payload(_queue_page(), entry_id)

    assert payload["room_name"] == "204"
    assert payload["location_label"] == "2nd Floor / Cardiology / 204"
    assert payload["room_source"] == ROOM_SOURCE_APPOINTMENT


def test_walk_in_entry_announces_without_a_room():
    """Option R1 scope: walk-ins have no captured room, so they degrade.

    The empty ``room_source`` is the signal the announcer uses to speak the
    approved room-less sentence instead of inventing a room number.
    """
    _seed()
    entry_id = _entry(1, "T-F4-002", appointment_id=None, entry_source="walk_in")

    payload = _entry_payload(_queue_page(), entry_id)

    assert payload["room_name"] == ""
    assert payload["location_label"] == ""
    assert payload["room_source"] == ""


def test_enqueue_endpoint_reports_no_room_for_a_walk_in():
    _seed()
    r = queue_client.post(
        "/api/v1/queue/enqueue",
        json={"doctor_id": DOC, "patient_id": PAT, "branch_id": BR,
              "date": str(TODAY), "entry_source": "walk_in"},
        headers=headers(DESK))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["room_name"] == ""
    assert body["room_source"] == ""


def test_each_entry_on_one_page_keeps_its_own_room():
    """The snapshot is resolved per entry, not once for the page."""
    _seed()
    first = _entry(1, "T-F4-003", appointment_id=_appointment(room="204"))
    second = _entry(2, "T-F4-004",
                    appointment_id=_appointment(room="305", floor="3rd Floor",
                                                department="Neurology"))

    page = _queue_page()

    assert _entry_payload(page, first)["room_name"] == "204"
    assert _entry_payload(page, second)["room_name"] == "305"
    assert _entry_payload(page, second)["location_label"] == \
        "3rd Floor / Neurology / 305"


def test_a_page_of_entries_costs_one_appointments_query():
    """No N+1: the room snapshot is batch-resolved for the whole page."""
    _seed()
    shared = _appointment(room="204")
    for index in range(1, 4):
        _entry(index, f"T-F4-10{index}", appointment_id=shared)

    with _count_appointment_selects() as statements:
        page = _queue_page()

    assert len(page["entries"]) == 3
    assert len(statements) == 1, statements


def test_recovery_payload_reports_the_same_room():
    """A recovered/missed-turn entry announces the room it always had."""
    _seed()
    appointment_id = _appointment()
    entry_id = _entry(1, "T-F4-005", appointment_id=appointment_id,
                      status="skipped")

    session = SessionFactory()
    try:
        entry = session.query(QueueEntry).filter(
            QueueEntry.id == entry_id).first()
        payload = recovery._entry_payload(session, entry)
    finally:
        session.close()

    assert payload["room_name"] == "204"
    assert payload["location_label"] == "2nd Floor / Cardiology / 204"
    assert payload["room_source"] == ROOM_SOURCE_APPOINTMENT


def test_queue_page_never_leaks_another_branch():
    """Scope is enforced before serialisation, so a foreign branch is a 404.

    Not a room-format assertion: it pins that adding the room fields did not add
    a way to read another branch's row.
    """
    _seed()
    r = queue_client.get(
        "/api/v1/queue",
        params={"doctor_id": DOC, "date": str(TODAY),
                "branch_id": "not-my-branch"},
        headers=headers(DESK))
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"
