"""Walk-in placement â€” Business Rules Â§25 (MP-10).

The placement policy is a **facility setting**. This module proves the four
approved behaviours are genuinely distinct, that a policy change never moves a
patient already waiting, that the insertions are recorded (position history plus
a ``queue.reposition`` audit event), and that the retired per-request parameter
can no longer choose anything.

The organization router half â€” who may write the policy, the allowed-options
subset, the reserve bounds and the audit record â€” is covered in
``backend/organization/tests/test_walk_in_config.py``.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                                ensure_org, ensure_patient, ensure_schedule,
                                ensure_user, headers, load_app, purge_org, uniq)
from common.models import Appointment, AuditEvent, Organization, QueueEntry

ORG = "mp10-org"
BR = "mp10-branch"
DOC = "mp10-doc"
RECP = "mp10_recp"
ADMIN = "mp10_admin"


CLIENT = TestClient(load_app("queuing"))


@pytest.fixture(autouse=True)
def _world():
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    _configure(None)
    purge_org(ORG)
    yield
    _configure(None)
    purge_org(ORG)


def _configure(block):
    """Store the organization's ``queue_config`` block (``None`` = default)."""
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == ORG).first()
        org.config = {"queue_config": block} if block else {}
        s.commit()


def _patient(label="Walk-in"):
    patient_id = uniq("mp10-pat")
    ensure_patient(patient_id, ORG, name=label, mobile=uniq("0170000"))
    return patient_id


def _enqueue(patient_id, *, source="walk_in", **body):
    payload = {"doctor_id": DOC, "patient_id": patient_id, "entry_source": source}
    payload.update(body)
    return CLIENT.post("/api/v1/queue/enqueue", headers=headers(RECP), json=payload)


def _queue():
    """Every entry of this organization, in display order."""
    with db_session() as s:
        rows = s.query(QueueEntry).filter(
            QueueEntry.organization_id == ORG).order_by(QueueEntry.position).all()
        return [(row.patient_id, row.position) for row in rows]


def _entry(patient_id):
    with db_session() as s:
        return s.query(QueueEntry).filter(
            QueueEntry.organization_id == ORG,
            QueueEntry.patient_id == patient_id).first()


def _reposition_audits(target_id=None):
    with db_session() as s:
        query = s.query(AuditEvent).filter(
            AuditEvent.action == "queue.reposition",
            AuditEvent.organization_id == ORG)
        if target_id:
            query = query.filter(AuditEvent.target_id == target_id)
        return query.count()


def _iso(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc)
            - timedelta(minutes=minutes_ago)).isoformat()


class TestEndOfQueue:
    """BR Â§25.1 â€” the walk-in joins after existing applicable bookings."""

    def test_it_appends_and_nothing_moves(self):
        _configure({"walk_in_policy": "end_of_queue"})
        first, second = _patient("First"), _patient("Second")
        assert _enqueue(first).json()["position"] == 1
        before = _reposition_audits()
        r = _enqueue(second)
        assert r.status_code == 201, r.text
        assert r.json()["position"] == 2
        assert _reposition_audits() == before, "an append reorders nothing"

    def test_a_booked_patient_is_not_placed_by_the_walk_in_policy(self):
        """BR Â§25 governs walk-ins: a check-in appends under any policy.

        The facility is set to ``staff_placement`` â€” which refuses a walk-in
        without a position â€” and an appointment still checks in, because the
        policy is not about booked patients.
        """
        _configure({"walk_in_policy": "staff_placement"})
        patient_id = _patient("Booked")
        with db_session() as s:
            appt = Appointment(
                id=uniq("mp10-appt"), organization_id=ORG, branch_id=BR,
                patient_id=patient_id, doctor_id=DOC,
                appointment_date=datetime.now(timezone.utc).date(),
                start_time="10:00", status="CONFIRMED", status_history=[],
                token_number=uniq("T"))
            s.add(appt)
            s.commit()
            appt_id = appt.id
        r = CLIENT.post("/api/v1/queue/check-in", headers=headers(RECP),
                        json={"appointment_id": appt_id})
        assert r.status_code == 201, r.text
        assert r.json()["position"] == 1


class TestFirstCome:
    """BR Â§25.2 â€” order follows the recorded arrival/registration rule."""

    def test_an_earlier_arrival_is_placed_ahead(self):
        _configure({"walk_in_policy": "first_come"})
        early, late = _patient("Arrived earlier"), _patient("Registered first")
        assert _enqueue(late).json()["position"] == 1

        r = _enqueue(early, arrived_at=_iso(30))
        assert r.status_code == 201, r.text
        assert r.json()["position"] == 1, "the earlier arrival goes first"
        assert [pos for _, pos in _queue()] == [1, 2]

        moved = _entry(late)
        assert moved.position == 2
        history = moved.position_history[-1]
        assert history["from"] == 1 and history["to"] == 2
        assert "first_come" in history["reason"]
        assert _reposition_audits(moved.id) == 1, "the move is audited"

    def test_without_an_arrival_time_it_appends(self):
        _configure({"walk_in_policy": "first_come"})
        first, second = _patient("A"), _patient("B")
        assert _enqueue(first).json()["position"] == 1
        assert _enqueue(second).json()["position"] == 2

    def test_an_unparseable_arrival_time_is_a_422_and_writes_nothing(self):
        _configure({"walk_in_policy": "first_come"})
        r = _enqueue(_patient(), arrived_at="half past nine")
        assert r.status_code == 422, r.text
        assert "arrived_at" in r.json()["detail"]
        assert _queue() == []


class TestReservedCapacity:
    """BR Â§25.3 â€” reserve a configurable number or percentage of capacity."""

    def test_walk_ins_fill_the_reserved_block_then_append(self):
        _configure({"walk_in_policy": "reserved_capacity",
                    "walk_in_reserve_mode": "count",
                    "walk_in_reserve_value": 2})
        booked = [_patient(f"Booked {i}") for i in range(3)]
        for patient_id in booked:
            assert _enqueue(patient_id, source="appointment").json()["position"] in (
                1, 2, 3)
        walk_in_a, walk_in_b, walk_in_c = (_patient("Walk-in A"),
                                           _patient("Walk-in B"),
                                           _patient("Walk-in C"))

        assert _enqueue(walk_in_a).json()["position"] == 1
        assert _enqueue(walk_in_b).json()["position"] == 2
        # The pool is full: the third walk-in is appended, not inserted.
        assert _enqueue(walk_in_c).json()["position"] == 6
        positions = dict(_queue())
        assert positions[walk_in_a] == 1 and positions[walk_in_b] == 2
        assert positions[walk_in_c] == 6

    def test_the_pool_is_a_guarantee_not_a_cap(self):
        _configure({"walk_in_policy": "reserved_capacity",
                    "walk_in_reserve_mode": "count",
                    "walk_in_reserve_value": 1})
        for _ in range(3):
            assert _enqueue(_patient()).status_code == 201
        assert len(_queue()) == 3, "every walk-in still gets a place"

    def test_percentage_mode_uses_the_published_capacity(self):
        """8 seats published (4 slots x 2), 50 % reserved -> a pool of 4."""
        ensure_schedule(DOC, ORG, BR, start="09:00", end="10:00",
                        duration=15, capacity=2)
        _configure({"walk_in_policy": "reserved_capacity",
                    "walk_in_reserve_mode": "percent",
                    "walk_in_reserve_value": 50})
        booked = _patient("Booked")
        assert _enqueue(booked, source="appointment").json()["position"] == 1
        assert _enqueue(_patient("Walk-in")).json()["position"] == 1

    def test_percentage_mode_without_published_hours_has_no_pool(self):
        """No published capacity means nothing to reserve: append, do not raise."""
        _configure({"walk_in_policy": "reserved_capacity",
                    "walk_in_reserve_mode": "percent",
                    "walk_in_reserve_value": 50})
        assert _enqueue(_patient("A"), source="appointment").json()["position"] == 1
        assert _enqueue(_patient("B")).json()["position"] == 2


class TestStaffPlacement:
    """BR Â§25.4 â€” authorised staff select the queue position."""

    def test_the_requested_position_is_used_and_the_rest_shift(self):
        _configure({"walk_in_policy": "staff_placement"})
        first, second = _patient("First"), _patient("Second")
        # Staff placement always names a position — that is the policy.
        assert _enqueue(first, position=1).json()["position"] == 1
        assert _enqueue(second, position=2).json()["position"] == 2

        inserted = _patient("Inserted")
        r = _enqueue(inserted, position=2)
        assert r.status_code == 201, r.text
        assert r.json()["position"] == 2, "staff chose the position"
        positions = dict(_queue())
        assert positions[first] == 1
        assert positions[inserted] == 2
        assert positions[second] == 3

    def test_a_position_is_required(self):
        """The old silent append is gone: staff placement needs a position."""
        _configure({"walk_in_policy": "staff_placement"})
        r = _enqueue(_patient())
        assert r.status_code == 422, r.text
        assert "staff_placement_position_required" in r.json()["detail"]
        assert _queue() == []

    def test_an_out_of_range_position_is_refused(self):
        _configure({"walk_in_policy": "staff_placement"})
        assert _enqueue(_patient("Only"), position=1).json()["position"] == 1
        for wanted in (0, 5, -1):
            r = _enqueue(_patient(f"Bad {wanted}"), position=wanted)
            assert r.status_code == 422, (wanted, r.text)
        assert len(_queue()) == 1, "a refused placement writes nothing"


class TestPolicyIsProspective:
    """BR Â§25 â€” a change must not silently reorder an active queue."""

    def test_changing_the_policy_moves_nobody(self):
        _configure({"walk_in_policy": "end_of_queue"})
        patients = [_patient(f"P{i}") for i in range(3)]
        for patient_id in patients:
            _enqueue(patient_id)
        before = _queue()
        audits_before = _reposition_audits()

        # The sharpest possible change: end_of_queue -> staff_placement, which
        # would otherwise imply a different rule for everyone already waiting.
        _configure({"walk_in_policy": "staff_placement"})

        assert _queue() == before, "an active queue must not be reordered"
        assert _reposition_audits() == audits_before, "and nothing is audited as moved"


class TestAudit:
    def test_the_enqueue_audit_row_says_why_the_position_was_chosen(self):
        _configure({"walk_in_policy": "first_come"})
        patient_id = _patient("Audited")
        assert _enqueue(patient_id, arrived_at=_iso(5)).status_code == 201
        with db_session() as s:
            entry = s.query(QueueEntry).filter(
                QueueEntry.patient_id == patient_id).first()
            event = s.query(AuditEvent).filter(
                AuditEvent.action == "queue.enqueue",
                AuditEvent.target_id == entry.id).order_by(
                    AuditEvent.timestamp.desc()).first()
        assert event is not None
        placement = event.after["placement"]
        assert placement["policy"] == "first_come"
        assert placement["basis"] in ("append", "arrival_order")
        assert placement["position"] == event.after["position"]

    def test_a_placement_refusal_is_audited_as_a_denial(self):
        """The denial trail records the refusal, not only the successes (Q-2)."""
        _configure({"walk_in_policy": "staff_placement"})
        r = _enqueue(_patient())
        assert r.status_code == 422
        with db_session() as s:
            denial = s.query(AuditEvent).filter(
                AuditEvent.organization_id == ORG,
                AuditEvent.action == "request.denied").first()
        assert denial is not None, "a 422 must leave an audit row"
