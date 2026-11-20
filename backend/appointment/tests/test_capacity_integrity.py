"""Capacity integrity enforced by the database (owner decision Q2).

The gap analysis (F-01) recorded that the only thing preventing two receptionists
from taking the last seat was an application-level ``SELECT … FOR UPDATE`` on the
doctor row: a second writer that skipped that lock — another service, a migration,
a script, a future refactor — could oversell the slot.

Q2's answer is a second, independent layer: every appointment **claims a numbered
seat** in its slot, and ``UNIQUE (doctor_id, appointment_date, slot_key,
seat_number)`` refuses the duplicate regardless of what any application believes.
``slot_key`` is the published window start (a 09:07 booking consumes 09:00–09:15)
or the literal ``UNSCHEDULED`` for the outside-hours pool.

This module tests that layer directly — independent sessions, real threads, the
constraint itself — and then through the API to prove the two layers agree.  A
sequential API-only test would pass without any constraint, which is exactly the
evidence the finding says was missing.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from amsdp_test_support import (db_session, ensure_all_day_session,
                                ensure_branch, ensure_doctor, ensure_org,
                                ensure_patient, ensure_schedule, ensure_user,
                                headers, load_app, purge_org)
from common.capacity import SlotFull, claim_seat
from common.database import SessionFactory
from common.models import Appointment, Organization, SlotAllocation

ORG = "cap-org"
BR = "cap-br"
DOC = "cap-doc"
PAT = "cap-pat"
RECP = "cap_recp"
ADM = "cap_adm"
DAY = date(2031, 6, 4)


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Capacity", mobile="01700004001")
    ensure_patient(PAT, ORG, name="Capacity Patient", mobile="01700004002")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(ADM, "org_admin", ORG, BR)
    _reset_policy()
    yield
    purge_org(ORG)


def _reset_policy(**policy):
    """Drop any appointment policy left by an earlier test (optionally set one).

    ``purge_org`` deliberately keeps the organization row (the audit trail
    references it), so the JSON policy has to be reset explicitly or a limit set
    by one test would silently apply to the next.  The HTTP surface for this is
    covered in ``organization/tests/test_appointment_config.py``; here the value
    is written directly so the test stays about capacity.
    """
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == ORG).first()
        config = dict(org.config or {})
        if policy:
            config["appointment_config"] = dict(policy)
        else:
            config.pop("appointment_config", None)
        org.config = config
        s.commit()


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _publish(*, start="09:00", end="10:00", duration=15, capacity=1):
    """Publish the doctor's hours *and* a session covering the day."""
    ensure_schedule(DOC, ORG, BR, start=start, end=end, duration=duration,
                    capacity=capacity)
    ensure_all_day_session(DOC, ORG, BR, duration=duration, capacity=capacity)


def _book(client, *, start="09:00", patient=PAT):
    return client.post("/api/v1/appointments", headers=headers(RECP), json={
        "patient_id": patient, "doctor_id": DOC,
        "appointment_date": DAY.isoformat(), "start_time": start})


def _appointment(appointment_id):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.id == appointment_id).first()


def _allocations(appointment_id):
    with db_session() as s:
        return s.query(SlotAllocation).filter(
            SlotAllocation.appointment_id == appointment_id).all()


def _seat_row(appointment_id):
    rows = _allocations(appointment_id)
    assert len(rows) == 1, f"expected exactly one seat, found {len(rows)}"
    return rows[0]


def _direct_appointment(appointment_id, *, start="09:00", status="BOOKED"):
    """An appointment row written without going through the API.

    The claim helper only needs a real parent row (``slot_allocations`` has a
    foreign key to it); the point of these tests is the seat table, not the route.
    """
    with db_session() as s:
        s.add(Appointment(
            id=appointment_id, organization_id=ORG, branch_id=BR,
            patient_id=PAT, doctor_id=DOC, appointment_date=DAY,
            start_time=start, status=status, appointment_type="scheduled",
            booking_source="reception", status_history=[]))
        s.commit()


def _claim_in_own_session(appointment_id, *, capacity=1, slot_key="09:00"):
    """Claim a seat from an *independent* session — the real concurrency shape."""
    session = SessionFactory()
    try:
        seat = claim_seat(session, organization_id=ORG, doctor_id=DOC,
                          appointment_date=DAY, slot_key=slot_key,
                          appointment_id=appointment_id, capacity=capacity)
        session.commit()
        return ("ok", seat)
    except SlotFull as exc:
        session.rollback()
        return ("full", str(exc))
    finally:
        session.close()


# ---------------------------------------------------------------------------
# The constraint itself
# ---------------------------------------------------------------------------

class TestSeatUniquenessIsInTheDatabase:
    def test_the_constraint_refuses_a_second_claim_of_the_same_seat(self):
        """No lock, no application check: two raw inserts, one seat.

        ``claim_seat`` is bypassed entirely here — the rows are inserted by hand —
        so a pass cannot be explained by application logic.
        """
        _direct_appointment("cap-raw-a")
        _direct_appointment("cap-raw-b")

        with db_session() as s:
            s.add(SlotAllocation(
                id="cap-alloc-a", organization_id=ORG, doctor_id=DOC,
                appointment_date=DAY, slot_key="09:00", kind="scheduled",
                seat_number=1, appointment_id="cap-raw-a"))
            s.commit()

        with pytest.raises(IntegrityError):
            with db_session() as s:
                s.add(SlotAllocation(
                    id="cap-alloc-b", organization_id=ORG, doctor_id=DOC,
                    appointment_date=DAY, slot_key="09:00", kind="scheduled",
                    seat_number=1, appointment_id="cap-raw-b"))
                s.commit()

        with db_session() as s:
            assert s.query(SlotAllocation).filter(
                SlotAllocation.slot_key == "09:00",
                SlotAllocation.appointment_date == DAY).count() == 1

    def test_one_appointment_cannot_hold_two_seats(self):
        """``UNIQUE (appointment_id)`` — a double claim is a bug, not data."""
        _direct_appointment("cap-raw-c")
        with db_session() as s:
            s.add(SlotAllocation(
                id="cap-alloc-c1", organization_id=ORG, doctor_id=DOC,
                appointment_date=DAY, slot_key="09:00", kind="scheduled",
                seat_number=1, appointment_id="cap-raw-c"))
            s.commit()

        with pytest.raises(IntegrityError):
            with db_session() as s:
                s.add(SlotAllocation(
                    id="cap-alloc-c2", organization_id=ORG, doctor_id=DOC,
                    appointment_date=DAY, slot_key="10:00", kind="scheduled",
                    seat_number=1, appointment_id="cap-raw-c"))
                s.commit()


class TestConcurrentClaims:
    def test_two_independent_sessions_race_for_one_seat(self):
        """Two transactions, one seat, a barrier so they really overlap."""
        _direct_appointment("cap-race-a")
        _direct_appointment("cap-race-b")
        start = threading.Barrier(2)

        def claim(appointment_id):
            start.wait(timeout=10)
            return _claim_in_own_session(appointment_id, capacity=1)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [f.result() for f in
                       (pool.submit(claim, "cap-race-a"),
                        pool.submit(claim, "cap-race-b"))]

        outcomes = sorted(state for state, _ in results)
        assert outcomes == ["full", "ok"], results
        with db_session() as s:
            assert s.query(SlotAllocation).filter(
                SlotAllocation.slot_key == "09:00",
                SlotAllocation.appointment_date == DAY).count() == 1

    def test_capacity_two_admits_two_and_refuses_the_third(self):
        for name in ("cap-two-a", "cap-two-b", "cap-two-c"):
            _direct_appointment(name)
        assert _claim_in_own_session("cap-two-a", capacity=2) == ("ok", 1)
        assert _claim_in_own_session("cap-two-b", capacity=2) == ("ok", 2)
        state, _ = _claim_in_own_session("cap-two-c", capacity=2)
        assert state == "full"


# ---------------------------------------------------------------------------
# The seat lifecycle — the table and the status-based count must agree
# ---------------------------------------------------------------------------

class TestSeatLifecycle:
    def test_a_booking_claims_the_window_not_the_minute(self, client):
        """F-03 + Q2: a 09:07 booking occupies the 09:00–09:15 seat."""
        _publish(duration=15, capacity=1)
        booked = _book(client, start="09:07")
        assert booked.status_code == 201, booked.text
        row = _seat_row(booked.json()["id"])
        assert (row.slot_key, row.seat_number) == ("09:00", 1)
        assert row.kind == "scheduled"

    def test_a_cancelled_appointment_frees_its_seat(self, client):
        _publish(duration=15, capacity=1)
        first = _book(client, start="09:00")
        assert first.status_code == 201, first.text
        first = first.json()
        assert _seat_row(first["id"]).seat_number == 1
        cancelled = client.post(
            f"/api/v1/appointments/{first['id']}/cancel",
            headers=headers(RECP),
            json={"status": "CANCELLED", "reason": "patient called"})
        assert cancelled.status_code == 200, cancelled.text
        assert _allocations(first["id"]) == []
        # The freed window is sellable again — the operator-visible consequence.
        again = _book(client, start="09:00")
        assert again.status_code == 201, again.text

    def test_a_no_show_appointment_frees_its_seat(self, client):
        _publish(duration=60, capacity=1)
        booked = _book(client, start="09:00")
        assert booked.status_code == 201, booked.text
        booked = booked.json()
        confirmed = client.patch(
            f"/api/v1/appointments/{booked['id']}/status",
            headers=headers(RECP), json={"status": "CONFIRMED"})
        assert confirmed.status_code == 200, confirmed.text
        no_show = client.patch(
            f"/api/v1/appointments/{booked['id']}/status",
            headers=headers(RECP),
            json={"status": "NO_SHOW", "reason": "did not attend"})
        assert no_show.status_code == 200, no_show.text
        assert _allocations(booked["id"]) == []

    def test_a_reschedule_moves_the_seat_and_frees_the_old_window(self, client):
        _publish(start="09:00", end="11:00", duration=60, capacity=1)
        booked = _book(client, start="09:00")
        assert booked.status_code == 201, booked.text
        booked = booked.json()
        assert _seat_row(booked["id"]).slot_key == "09:00"
        moved = client.post(
            f"/api/v1/appointments/{booked['id']}/reschedule",
            headers=headers(RECP),
            json={"new_date": DAY.isoformat(), "new_start_time": "10:00",
                  "reason": "doctor delayed"})
        assert moved.status_code == 200, moved.text
        replacement_id = moved.json()["new_appointment_id"]
        assert _allocations(booked["id"]) == []
        assert _seat_row(replacement_id).slot_key == "10:00"
        # …and the old window can be sold again.
        assert _book(client, start="09:00").status_code == 201


class TestUnscheduledPool:
    def test_the_override_pool_is_its_own_slot_key(self, client):
        """Q1 + Q2: an outside-hours acceptance draws on the daily pool."""
        _publish(duration=15, capacity=1)
        book = client.post("/api/v1/appointments", headers=headers(RECP), json={
            "patient_id": PAT, "doctor_id": DOC,
            "appointment_date": DAY.isoformat(), "start_time": "12:00",
            "appointment_type": "unscheduled",
            "override_reason": "urgent visit outside the session"})
        assert book.status_code == 201, book.text
        row = _seat_row(book.json()["id"])
        assert row.slot_key == "UNSCHEDULED"
        assert row.kind == "unscheduled"

    def test_the_pool_stops_at_the_organization_limit(self, client):
        _publish(duration=15, capacity=1)
        _reset_policy(unscheduled_daily_limit=1, allow_unscheduled=True)
        first = client.post("/api/v1/appointments", headers=headers(RECP), json={
            "patient_id": PAT, "doctor_id": DOC,
            "appointment_date": DAY.isoformat(), "start_time": "12:00",
            "appointment_type": "unscheduled",
            "override_reason": "urgent visit"})
        assert first.status_code == 201, first.text
        second = client.post("/api/v1/appointments", headers=headers(RECP), json={
            "patient_id": PAT, "doctor_id": DOC,
            "appointment_date": DAY.isoformat(), "start_time": "12:30",
            "appointment_type": "unscheduled",
            "override_reason": "second urgent visit"})
        assert second.status_code == 422, second.text
        assert "unscheduled_limit" in second.json()["detail"]
        assert len(_allocations(first.json()["id"])) == 1
