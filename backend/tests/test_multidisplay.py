"""Multi-display DQDS — MP-35 … MP-46 (specification MD-01 … MD-19).

These tests drive the **public** route, because that is where every acceptance
criterion lives: scope must be filtered in SQL, a switched-off field must be
absent from the *raw* body, an unchanged board must revalidate to ``304`` and a
state-changing verb must be refused.  Asserting the parsed payload alone would
not prove any of that — a field hidden by the page but present in the response
is exactly the failure MD-17 exists to prevent.

Fixtures are written straight to the database: the admin surface that creates a
display is MP-39 and does not exist yet.  Nothing here asserts MP-39 behaviour,
and no test claims the demonstration (MP-40).
"""
import sys, os, uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "queuing"))

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from common.database import SessionFactory
from common.models import (Organization, Branch, Doctor, Patient, QueueEntry,
                           DoctorBranch, FacilityDepartment, FacilityRoom,
                           QueueDisplay, QueueDisplayDoctor, AuditEvent)
from common.timeutil import operational_today
from queuing.main import app

client = TestClient(app)

ORG = "mdisp-org"
BR = "mdisp-br"
BR2 = "mdisp-br-2"
ORG2 = "mdisp-org-2"
BR_OTHER = "mdisp-br-other"

DOC_A = "mdisp-doc-a"          # chamber room 1 (cardiology)
DOC_B = "mdisp-doc-b"          # chamber room 2 (medicine)
DOC_C = "mdisp-doc-c"          # no chamber at all

DEPT_CARDIO = "mdisp-dep-cardio"
DEPT_MEDICINE = "mdisp-dep-medicine"
ROOM_1 = "mdisp-room-1"
ROOM_2 = "mdisp-room-2"

PAT = "mdisp-pat"
TODAY = date.today()



def _purge(session):
    """Remove only this module's rows, children first."""
    ids = [d.id for d in session.query(QueueDisplay).filter(
        QueueDisplay.organization_id.in_([ORG, ORG2])).all()]
    if ids:
        session.query(QueueDisplayDoctor).filter(
            QueueDisplayDoctor.display_id.in_(ids)).delete(
                synchronize_session=False)
        session.query(AuditEvent).filter(
            AuditEvent.target_id.in_(ids)).delete(synchronize_session=False)
        session.query(QueueDisplay).filter(
            QueueDisplay.id.in_(ids)).delete(synchronize_session=False)
    session.query(QueueEntry).filter(
        QueueEntry.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
    session.query(DoctorBranch).filter(
        DoctorBranch.branch_id.in_([BR, BR2, BR_OTHER])).delete(
            synchronize_session=False)
    session.query(FacilityRoom).filter(
        FacilityRoom.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
    session.query(FacilityDepartment).filter(
        FacilityDepartment.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
    session.query(Patient).filter(Patient.id == PAT).delete()
    session.query(Doctor).filter(
        Doctor.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
    session.query(Branch).filter(
        Branch.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
    session.query(Organization).filter(
        Organization.id.in_([ORG, ORG2])).delete(synchronize_session=False)


def _seed():
    """Reset and re-create this module's fixture facility in two transactions.

    The purge commits separately from the insert: a failed insert can then never
    leave the module's own rows behind to collide with the next run's primary
    keys.
    """
    session = SessionFactory()
    try:
        _purge(session)
        session.commit()
    finally:
        session.close()

    session = SessionFactory()
    try:
        session.add(Organization(id=ORG, name="Multi Display Hospital",
                                 code=ORG, timezone="Asia/Dhaka"))
        session.add(Organization(id=ORG2, name="Other Hospital", code=ORG2))
        session.add(Branch(id=BR, organization_id=ORG, name="Main", code=BR))
        session.add(Branch(id=BR2, organization_id=ORG, name="Annex", code=BR2))
        session.add(Branch(id=BR_OTHER, organization_id=ORG2, name="Other",
                           code=BR_OTHER))
        for doc_id, name in ((DOC_A, "Dr. Amina"), (DOC_B, "Dr. Babul"),
                             (DOC_C, "Dr. Chowdhury")):
            session.add(Doctor(id=doc_id, organization_id=ORG, name=name,
                               mobile=f"0170{doc_id[-1]}000000"))
        session.add(Patient(id=PAT, organization_id=ORG, name="Test Patient",
                            mobile="01700000999", sex="male"))
        session.add(FacilityDepartment(id=DEPT_CARDIO, organization_id=ORG,
                                       branch_id=BR, name="Cardiology",
                                       code="cardio"))
        session.add(FacilityDepartment(id=DEPT_MEDICINE, organization_id=ORG,
                                       branch_id=BR, name="Medicine",
                                       code="medicine"))
        session.add(FacilityRoom(id=ROOM_1, organization_id=ORG, branch_id=BR,
                                 department_id=DEPT_CARDIO, name="Room 301",
                                 code="301"))
        session.add(FacilityRoom(id=ROOM_2, organization_id=ORG, branch_id=BR,
                                 department_id=DEPT_MEDICINE, name="Room 205",
                                 code="205"))
        session.add(DoctorBranch(id="mdisp-db-a", doctor_id=DOC_A, branch_id=BR,
                                 room_id=ROOM_1, status="active"))
        session.add(DoctorBranch(id="mdisp-db-b", doctor_id=DOC_B, branch_id=BR,
                                 room_id=ROOM_2, status="active"))
        session.add(DoctorBranch(id="mdisp-db-c", doctor_id=DOC_C, branch_id=BR,
                                 status="active"))
        session.commit()
    finally:
        session.close()



def _display(code, *, branch=BR, org=ORG, scope="branch", status="active",
             language="bn", department_id=None, room_id=None, footer="",
             show_room=True, show_wait=True, show_count=True, members=()):
    """Persist one display (MP-39's create API does not exist yet)."""
    session = SessionFactory()
    try:
        row = QueueDisplay(
            id=str(uuid.uuid4()), organization_id=org, branch_id=branch,
            name=f"{code} display", code=code, language=language,
            scope_type=scope, department_id=department_id, room_id=room_id,
            footer_text=footer, show_room=show_room,
            show_estimated_wait=show_wait, show_waiting_count=show_count,
            status=status)
        session.add(row)
        session.flush()
        for doctor_id in members:
            session.add(QueueDisplayDoctor(display_id=row.id,
                                           doctor_id=doctor_id))
        session.commit()
        return row.id
    finally:
        session.close()


def _entry(status, token, position, doctor, *, history=None, day=TODAY):
    session = SessionFactory()
    try:
        session.add(QueueEntry(id=str(uuid.uuid4()), organization_id=ORG,
                               branch_id=BR, doctor_id=doctor, date=day,
                               position=position, token=token, status=status,
                               patient_id=PAT, entry_source="appointment",
                               status_history=history or [],
                               position_history=[]))
        session.commit()
    finally:
        session.close()


def _consultations(doctor, durations):
    """Completed entries today whose history records a real consultation."""
    start = datetime.now(timezone.utc) - timedelta(hours=2)
    for index, minutes in enumerate(durations):
        began = start + timedelta(minutes=index * 30)
        _entry("completed", f"X-{index}", 100 + index, doctor, history=[
            {"from": "waiting", "to": "in_consultation", "at": began.isoformat()},
            {"from": "in_consultation", "to": "completed",
             "at": (began + timedelta(minutes=minutes)).isoformat()},
        ])


def _reset():
    """Drop this test's queue rows and reset the in-process limiter state."""
    from queuing.display import _DQDS_RATE, _DISABLED_NOTED
    _DQDS_RATE.clear()
    _DISABLED_NOTED.clear()
    session = SessionFactory()
    try:
        session.query(QueueEntry).filter(
            QueueEntry.organization_id == ORG).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def _url(display=None, branch=BR, org=ORG):
    base = f"/api/v1/queue/display/{org}/{branch}"
    return f"{base}?display={display}" if display else base


def _audit_rows(action):
    session = SessionFactory()
    try:
        return session.query(AuditEvent).filter(
            AuditEvent.action == action).count()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def fresh():
    """Every test starts from the same seeded facility with an empty queue."""
    _seed()
    _reset()
    yield
    _reset()

# ---------------------------------------------------------------------------
# MP-35 — the registry itself
# ---------------------------------------------------------------------------

def test_two_displays_persist_independently_in_one_branch():
    """AC-01: two configurations, one branch, no shared state."""
    reception = _display("reception", scope="doctors", members=[DOC_A],
                         language="en", footer="Please wait")
    cardio = _display("cardio", scope="department",
                      department_id=DEPT_CARDIO, language="bn")
    session = SessionFactory()
    try:
        rows = {d.code: d for d in session.query(QueueDisplay).filter(
            QueueDisplay.branch_id == BR).all()}
    finally:
        session.close()
    assert set(rows) == {"reception", "cardio"}
    assert rows["reception"].id == reception
    assert rows["cardio"].id == cardio
    assert rows["reception"].language == "en"
    assert rows["cardio"].department_id == DEPT_CARDIO
    assert rows["reception"].scope_type == "doctors"
    assert rows["cardio"].scope_type == "department"


def test_a_duplicate_code_in_the_same_branch_is_refused():
    _display("reception")
    session = SessionFactory()
    try:
        session.add(QueueDisplay(id=str(uuid.uuid4()), organization_id=ORG,
                                 branch_id=BR, name="second", code="reception",
                                 language="bn", scope_type="branch",
                                 status="active"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_the_same_code_in_another_branch_is_allowed():
    """The unique key is (branch, code): 'reception' exists in both branches."""
    _display("reception", branch=BR)
    _display("reception", branch=BR2)
    session = SessionFactory()
    try:
        count = session.query(QueueDisplay).filter(
            QueueDisplay.code == "reception").count()
    finally:
        session.close()
    assert count == 2


@pytest.mark.parametrize("kwargs", [
    {"scope": "department"},
    {"scope": "room"},
])
def test_a_half_configured_scope_is_refused_by_the_database(kwargs):
    """A scope without its target would silently widen to the whole branch."""
    session = SessionFactory()
    try:
        session.add(QueueDisplay(id=str(uuid.uuid4()), organization_id=ORG,
                                 branch_id=BR, name="broken", code="broken",
                                 language="bn", status="active",
                                 scope_type=kwargs["scope"]))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


@pytest.mark.parametrize("column,value", [
    ("scope_type", "queue"),
    ("language", "fr"),
    ("status", "deleted"),
])
def test_an_unknown_scope_language_or_status_is_refused(column, value):
    session = SessionFactory()
    try:
        row = QueueDisplay(id=str(uuid.uuid4()), organization_id=ORG,
                           branch_id=BR, name="bad", code="bad",
                           language="bn", scope_type="branch",
                           status="active")
        setattr(row, column, value)
        session.add(row)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()

# ---------------------------------------------------------------------------
# MP-36 — resolution and server-side scope
# ---------------------------------------------------------------------------

def test_a_doctor_scoped_display_hides_every_out_of_scope_token():
    """AC-02/AC-05: the out-of-scope token appears nowhere in the raw body."""
    _display("reception", scope="doctors", members=[DOC_A])
    _entry("called", "A-001", 1, DOC_A)
    _entry("waiting", "B-001", 1, DOC_B)
    _entry("waiting", "C-001", 1, DOC_C)

    r = client.get(_url("reception"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert [d["doctor_name"] for d in body["doctors"]] == ["Dr. Amina"]
    assert body["doctors"][0]["currently_serving"] == "A-001"
    assert "B-001" not in r.text
    assert "C-001" not in r.text
    assert "Dr. Babul" not in r.text
    assert body["display"]["code"] == "reception"
    assert body["display"]["scope_type"] == "doctors"


def test_an_empty_doctor_scope_is_empty_and_never_the_branch():
    """A configuration mistake must not publish the whole branch."""
    _display("nothing", scope="doctors", members=[])
    _entry("waiting", "A-002", 2, DOC_A)
    _entry("waiting", "B-001", 1, DOC_B)
    r = client.get(_url("nothing"))
    assert r.status_code == 200, r.text
    assert r.json()["doctors"] == []
    assert "A-002" not in r.text


def test_an_unknown_display_404s_exactly_like_an_unknown_branch():
    unknown_branch = client.get(_url(branch="nope"))
    unknown_display = client.get(_url("nope"))
    assert unknown_branch.status_code == unknown_display.status_code == 404
    assert unknown_branch.json() == unknown_display.json() == {"detail": "not found"}
    assert unknown_display.headers["cache-control"] == "no-store"


def test_a_disabled_display_404s_identically_and_is_audited_once():
    """AC-21: identical 404, and one throttled audit row per five minutes."""
    _display("off", status="disabled")
    _entry("waiting", "A-002", 2, DOC_A)
    before = _audit_rows("queue.display.disabled_requested")

    first = client.get(_url("off"))
    second = client.get(_url("off"))

    assert first.status_code == second.status_code == 404
    assert first.json() == {"detail": "not found"}
    assert first.headers["cache-control"] == "no-store"
    assert "A-002" not in first.text
    assert _audit_rows("queue.display.disabled_requested") == before + 1


def test_unknown_codes_write_no_audit_rows():
    """AC-21: 100 anonymous probes add zero rows to an append-only trail."""
    from queuing.display import _DQDS_RATE
    before = _audit_rows("queue.display.disabled_requested")
    for index in range(100):
        if index % 10 == 0:
            _DQDS_RATE.clear()          # the limiter is not what is under test
        assert client.get(_url(f"probe-{index}")).status_code == 404
    assert _audit_rows("queue.display.disabled_requested") == before


def test_a_display_of_another_branch_is_not_resolvable():
    _display("reception", branch=BR2)
    _entry("waiting", "A-002", 2, DOC_A)
    r = client.get(_url("reception"))
    assert r.status_code == 404, r.text


def test_a_display_of_another_organisation_is_never_resolvable():
    """Tenancy: the row is looked up inside the branch's organisation only."""
    _display("reception", org=ORG2, branch=BR_OTHER)
    r = client.get(_url("reception"))
    assert r.status_code == 404, r.text


def test_the_default_board_keeps_its_historic_payload():
    """Specification 5.2: the two-segment route behaves exactly as before."""
    _display("reception", scope="doctors", members=[DOC_A])
    _entry("called", "A-001", 1, DOC_A)
    _entry("waiting", "B-001", 1, DOC_B)

    r = client.get(_url())
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"organization", "branch", "doctors", "updated_at"}
    assert len(body["doctors"]) == 2
    for row in body["doctors"]:
        assert set(row.keys()) == {"doctor_name", "currently_serving",
                                   "patients_waiting"}
    assert r.headers["cache-control"] == "public, max-age=10"

# ---------------------------------------------------------------------------
# MP-37 / MP-41 — department and room scope, room label
# ---------------------------------------------------------------------------

def test_a_department_display_shows_only_that_departments_doctors():
    """AC-03: resolved through doctor_branches.room_id -> room.department_id."""
    _display("cardio", scope="department", department_id=DEPT_CARDIO)
    _entry("waiting", "A-002", 2, DOC_A)      # room 301, cardiology
    _entry("waiting", "B-001", 1, DOC_B)      # room 205, medicine
    _entry("waiting", "C-001", 1, DOC_C)      # no chamber at all

    r = client.get(_url("cardio"))
    assert r.status_code == 200, r.text
    assert [d["doctor_name"] for d in r.json()["doctors"]] == ["Dr. Amina"]
    assert "B-001" not in r.text
    assert "C-001" not in r.text


def test_a_room_display_shows_only_that_rooms_doctor():
    """AC-15: room scope lists its assigned doctor and nobody else."""
    _display("room-205", scope="room", room_id=ROOM_2)
    _entry("waiting", "A-002", 2, DOC_A)
    _entry("waiting", "B-001", 1, DOC_B)

    r = client.get(_url("room-205"))
    assert r.status_code == 200, r.text
    assert [d["doctor_name"] for d in r.json()["doctors"]] == ["Dr. Babul"]
    assert r.json()["display"]["scope_type"] == "room"
    assert "A-002" not in r.text


def test_a_doctor_without_a_chamber_renders_no_room_label():
    """AC-07: '—' in the page, ``null`` in the payload — never an empty string."""
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    _entry("waiting", "C-001", 1, DOC_C)

    r = client.get(_url("all"))
    assert r.status_code == 200, r.text
    rows = {d["doctor_name"]: d for d in r.json()["doctors"]}
    assert rows["Dr. Amina"]["room_name"] == "Room 301"
    assert rows["Dr. Chowdhury"]["room_name"] is None


# ---------------------------------------------------------------------------
# MP-42 — estimated waiting time
# ---------------------------------------------------------------------------

def test_a_measured_estimate_comes_from_todays_completed_consultations(monkeypatch):
    """AC-16: n >= 3 samples -> the measured mean, marked as an estimate."""
    monkeypatch.setenv("AMSDP_AVG_SERVICE_MINUTES", "10")
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    _consultations(DOC_A, [12, 12, 12])

    row = client.get(_url("all")).json()["doctors"][0]
    assert row["estimated_wait_minutes"] == 12
    assert row["estimate"] is True


def test_a_doctor_without_samples_shows_the_facility_default(monkeypatch):
    monkeypatch.setenv("AMSDP_AVG_SERVICE_MINUTES", "7")
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    _consultations(DOC_A, [12, 12])            # two samples: not a measurement

    row = client.get(_url("all")).json()["doctors"][0]
    assert row["estimated_wait_minutes"] == 7
    assert row["estimate"] is True


def test_the_estimate_is_always_a_positive_integer(monkeypatch):
    monkeypatch.setenv("AMSDP_AVG_SERVICE_MINUTES", "0")
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    _consultations(DOC_A, [0.2, 0.2, 0.2])     # rounds up, never below 1

    row = client.get(_url("all")).json()["doctors"][0]
    assert isinstance(row["estimated_wait_minutes"], int)
    assert row["estimated_wait_minutes"] >= 1


# ---------------------------------------------------------------------------
# MP-43 — refresh on change
# ---------------------------------------------------------------------------

def test_an_unchanged_board_revalidates_to_304():
    """AC-17: identical projection -> same weak ETag -> empty 304."""
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)

    first = client.get(_url("all"))
    etag = first.headers["etag"]
    assert etag.startswith("W/")
    assert first.json()["board_version"] == etag[3:-1]

    second = client.get(_url("all"), headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.content == b""
    assert second.headers["etag"] == etag
    assert second.headers["cache-control"] == "public, max-age=10"
    assert second.headers["x-ratelimit-limit"]      # 304s stay in the bucket


def test_a_queue_change_changes_the_board_version():
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    before = client.get(_url("all")).json()

    _entry("called", "A-001", 1, DOC_A)
    after = client.get(_url("all")).json()

    assert after["board_version"] != before["board_version"]
    assert after["doctors"][0]["currently_serving"] == "A-001"
    assert after["doctors"][0]["patients_waiting"] == 2


def test_the_version_does_not_change_when_only_the_clock_does():
    """A version that drifted with ``updated_at`` would defeat revalidation."""
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    first = client.get(_url("all")).json()
    second = client.get(_url("all")).json()
    assert first["board_version"] == second["board_version"]
    assert first["updated_at"] != "" and second["updated_at"] != ""


# ---------------------------------------------------------------------------
# MP-44 — facility-local operational day
# ---------------------------------------------------------------------------

def test_the_board_publishes_the_facility_day_and_timezone():
    """AC-18: 'today' is the facility's date, and it is stated in the body."""
    _display("all", scope="branch")
    _entry("waiting", "A-002", 2, DOC_A)
    _entry("waiting", "Y-001", 1, DOC_A, day=TODAY - timedelta(days=1))

    body = client.get(_url("all")).json()
    session = SessionFactory()
    try:
        facility_day = operational_today(session, ORG).isoformat()
    finally:
        session.close()
    assert body["operational_date"] == facility_day
    assert body["timezone"] == "Asia/Dhaka"
    assert "Y-001" not in str(body)


# ---------------------------------------------------------------------------
# MP-45 — facility-controlled public fields
# ---------------------------------------------------------------------------

def test_a_switched_off_field_is_absent_from_the_raw_response():
    """AC-19: suppression happens server-side, not in the page."""
    _display("quiet", scope="branch", show_room=False, show_wait=False,
             show_count=False, footer="Shhh", language="bn")
    _entry("waiting", "A-002", 2, DOC_A)

    r = client.get(_url("quiet"))
    assert r.status_code == 200, r.text
    body = r.json()
    row = body["doctors"][0]
    assert "room_name" not in row
    assert "estimated_wait_minutes" not in row
    assert "estimate" not in row
    assert "patients_waiting" not in row
    assert "room_name" not in r.text
    assert "estimated_wait_minutes" not in r.text
    # The board still serves its allowed information.
    assert row["currently_serving"] is None
    assert body["display"]["footer_text"] == "Shhh"
    assert body["display"]["language"] == "bn"


def test_the_default_policy_publishes_all_four_fields():
    _display("loud", scope="branch", footer="Welcome", language="en")
    _entry("waiting", "A-002", 2, DOC_A)

    body = client.get(_url("loud")).json()
    row = body["doctors"][0]
    assert row["room_name"] == "Room 301"
    assert row["patients_waiting"] == 1
    assert row["estimate"] is True
    assert body["display"] == {"code": "loud", "name": "loud display",
                               "language": "en", "scope_type": "branch",
                               "footer_text": "Welcome"}


# ---------------------------------------------------------------------------
# MP-46 — read-only public surface
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("verb", ["post", "put", "patch", "delete"])
def test_a_state_changing_verb_is_refused(verb):
    """AC-20: 405, ``Allow: GET``, no-store, and never a cookie."""
    _display("all", scope="branch")
    r = getattr(client, verb)(_url("all"))
    assert r.status_code == 405
    assert r.headers["allow"] == "GET"
    assert r.headers["cache-control"] == "no-store"
    assert "set-cookie" not in r.headers


def test_a_successful_board_sets_no_cookie():
    _display("all", scope="branch")
    r = client.get(_url("all"))
    assert r.status_code == 200
    assert "set-cookie" not in r.headers


# ---------------------------------------------------------------------------
# MP-42 regression — a scoped board must not fabricate a sample size
# ---------------------------------------------------------------------------

def test_a_scoped_board_does_not_multiply_its_estimate_samples(monkeypatch):
    """One completed consultation stays one sample on a doctor-scoped board.

    The completed-consultation query is filtered by ``QueueEntry.doctor_id``.
    Filtering it by ``Doctor.id`` instead cross-joins ``queue_entries`` with
    ``doctors`` and multiplies every sample by the number of doctors — here one
    sample would become three and the facility default would be replaced by a
    "measurement" that never happened.
    """
    monkeypatch.setenv("AMSDP_AVG_SERVICE_MINUTES", "9")
    _display("reception", scope="doctors", members=[DOC_A])
    _entry("waiting", "A-002", 2, DOC_A)
    _consultations(DOC_A, [30])                # exactly one sample, not three

    rows = client.get(_url("reception")).json()["doctors"]
    assert [r["doctor_name"] for r in rows] == ["Dr. Amina"]
    assert rows[0]["estimated_wait_minutes"] == 9

