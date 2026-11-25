"""Booking around blocked periods — BR §15 / MP-16 (the enforcement half).

``test_schedule_blocks.py`` proves the block exists, is audited, is cancelable
and is published as unavailable by ``available-slots``.  This module proves the
other half of the requirement — *a blocked period cannot be booked* — and that
the authorised exception BR §15 allows is real, narrow and audited:

* an ordinary booking inside a block is refused with a stable
  ``blocked_period`` code, and nothing is written;
* a booking outside the block, on another day, for another doctor or after a
  cancellation still succeeds (the guard must not over-refuse);
* ``override_block`` is refused with 403 to a caller without
  ``schedule.manage``, refused with 422 without a reason, and when it is allowed
  it writes the appointment **and** an ``appointment.block_override`` audit row;
* a refused reschedule leaves the original visit untouched — proving the guard
  runs inside the same transaction as the move.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_all_day_session,
                               ensure_branch, ensure_doctor, ensure_org,
                               ensure_patient, ensure_schedule, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment, AuditEvent, Schedule, ScheduleBlock

ORG = "mp16-appt-org"
BR = "mp16-appt-br"
OTHER_ORG = "mp16-appt-other-org"
DOC = "mp16-appt-doc"
DOC2 = "mp16-appt-doc2"
PAT = "mp16-appt-pat"
RECP = "mp16_appt_recp"
ADMIN = "mp16_appt_admin"

DAY = "2031-04-15"
OTHER_DAY = "2031-04-16"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Blocked", mobile="01700002001")
    ensure_doctor(DOC2, ORG, name="Dr. Second", mobile="01700002002")
    # Capacity 2, published for every weekday: the fixture must not depend on
    # which weekday the dates above fall on.
    ensure_schedule(DOC, ORG, BR, capacity=2)
    ensure_all_day_session(DOC, ORG, BR, capacity=2)
    ensure_schedule(DOC2, ORG, BR, capacity=2)
    ensure_all_day_session(DOC2, ORG, BR, capacity=2)
    ensure_patient(PAT, ORG, name="Blocked Patient", mobile="01700002003")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _add_block(day=DAY, start="09:00", end="09:30", doctor=DOC,
               status="active") -> str:
    """Insert a block directly: the write API has its own suite."""
    with db_session() as s:
        schedule = s.query(Schedule).filter(
            Schedule.doctor_id == doctor,
            Schedule.organization_id == ORG).first()
        row = ScheduleBlock(
            organization_id=ORG, branch_id=BR, schedule_id=schedule.id,
            doctor_id=doctor, start_date=date.fromisoformat(day),
            end_date=date.fromisoformat(day), start_time=start, end_time=end,
            reason="medical leave", status=status)
        s.add(row)
        s.commit()
        return row.id


def _book(client, *, day=DAY, start="09:00", doctor=DOC, user=RECP, **extra):
    body = {"patient_id": PAT, "doctor_id": doctor, "appointment_date": day,
            "start_time": start}
    body.update(extra)
    return client.post("/api/v1/appointments", headers=headers(user), json=body)


def _appointments():
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.organization_id == ORG).all()


class TestBlockedBookingRefused:
    def test_booking_inside_a_blocked_window_is_refused(self, client):
        _add_block()
        r = _book(client)
        assert r.status_code == 422, r.text
        assert "blocked_period" in r.text
        assert _appointments() == [], "a refused booking writes nothing"

    def test_a_blocked_slot_is_measured_as_a_window_not_a_minute(self, client):
        """09:07 consumes the 09:00–09:15 slot, which the block covers."""
        _add_block()
        r = _book(client, start="09:07")
        assert r.status_code == 422, r.text
        assert "blocked_period" in r.text

    def test_booking_outside_the_blocked_window_succeeds(self, client):
        _add_block()
        assert _book(client, start="10:00").status_code == 201

    def test_touching_the_block_boundary_is_allowed(self, client):
        """A booking that starts when the block ends is not inside it."""
        _add_block(start="09:00", end="09:30")
        assert _book(client, start="09:30").status_code == 201

    def test_whole_day_block_refuses_every_time(self, client):
        _add_block(start=None, end=None)
        assert _book(client, start="09:00").status_code == 422
        assert _book(client, start="16:00").status_code == 422
        assert _appointments() == []

    def test_block_on_another_day_does_not_refuse(self, client):
        _add_block(day=OTHER_DAY)
        assert _book(client, day=DAY).status_code == 201

    def test_another_doctors_block_does_not_refuse(self, client):
        _add_block(doctor=DOC2)
        assert _book(client, doctor=DOC).status_code == 201

    def test_cancelled_block_does_not_refuse(self, client):
        _add_block(status="cancelled")


class TestBlockOverride:
    def test_override_without_the_capability_is_refused(self, client):
        _add_block()
        r = _book(client, override_block=True, override_reason="urgent case")
        assert r.status_code == 403, r.text
        assert "schedule.manage" in r.text
        assert _appointments() == []

    def test_override_without_a_reason_is_refused(self, client):
        _add_block()
        r = _book(client, user=ADMIN, override_block=True)
        assert r.status_code == 422, r.text
        assert "reason required" in r.text
        assert _appointments() == []

    def test_override_books_and_is_audited(self, client):
        block_id = _add_block()
        r = _book(client, user=ADMIN, override_block=True,
                  override_reason="patient travelling tomorrow")
        assert r.status_code == 201, r.text
        booked = r.json()
        assert booked["start_time"] == "09:00"
        with db_session() as s:
            row = s.query(AuditEvent).filter(
                AuditEvent.action == "appointment.block_override",
                AuditEvent.target_id == block_id).first()
            assert row is not None
            assert row.organization_id == ORG
            assert row.reason == "patient travelling tomorrow"
            assert row.after["appointment_date"] == DAY
            assert row.after["start_time"] == "09:00"
            assert row.before["window"] == "09:00–09:30"

    def test_an_override_of_an_unblocked_hour_writes_no_override_audit(self, client):
        """The flag must not create an exception record when there is nothing to except."""
        block_id = _add_block()
        r = _book(client, user=ADMIN, start="10:00", override_block=True,
                  override_reason="no block at this hour")
        assert r.status_code == 201, r.text
        with db_session() as s:
            assert s.query(AuditEvent).filter(
                AuditEvent.action == "appointment.block_override",
                AuditEvent.target_id == block_id).count() == 0


class TestBlockedReschedule:
    def _booked(self, client, day=DAY, start="09:00") -> str:
        r = _book(client, day=day, start=start)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_reschedule_into_a_blocked_window_is_refused(self, client):
        appointment_id = self._booked(client, day=DAY)
        _add_block(day=OTHER_DAY)
        r = client.post(f"/api/v1/appointments/{appointment_id}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": OTHER_DAY, "new_start_time": "09:00"})
        assert r.status_code == 422, r.text
        assert "blocked_period" in r.text
        # The refusal is inside the move's transaction: the original visit is
        # untouched and no replacement was created.
        with db_session() as s:
            original = s.query(Appointment).filter(
                Appointment.id == appointment_id).first()
            assert original.status == "BOOKED"
            assert str(original.appointment_date) == DAY
            assert s.query(Appointment).filter(
                Appointment.organization_id == ORG).count() == 1

    def test_reschedule_outside_the_block_succeeds(self, client):
        appointment_id = self._booked(client, day=DAY)
        _add_block(day=OTHER_DAY, start="09:00", end="09:30")
        r = client.post(f"/api/v1/appointments/{appointment_id}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": OTHER_DAY, "new_start_time": "11:00"})
        assert r.status_code == 200, r.text
        assert r.json()["new_appointment_id"]

    def test_reschedule_override_with_a_reason_succeeds(self, client):
        appointment_id = self._booked(client, day=DAY)
        block_id = _add_block(day=OTHER_DAY)
        r = client.post(f"/api/v1/appointments/{appointment_id}/reschedule",
                        headers=headers(ADMIN),
                        json={"new_date": OTHER_DAY, "new_start_time": "09:00",
                              "reason": "patient must be seen today",
                              "override_block": True})
        assert r.status_code == 200, r.text
        with db_session() as s:
            row = s.query(AuditEvent).filter(
                AuditEvent.action == "appointment.block_override",
                AuditEvent.target_id == block_id).first()
            assert row is not None
            assert row.reason == "patient must be seen today"
            assert row.after["appointment_date"] == OTHER_DAY

    def test_reschedule_override_by_the_front_desk_is_refused(self, client):
        appointment_id = self._booked(client, day=DAY)
        _add_block(day=OTHER_DAY)
        r = client.post(f"/api/v1/appointments/{appointment_id}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": OTHER_DAY, "new_start_time": "09:00",
                              "reason": "please squeeze in",
                              "override_block": True})
        assert r.status_code == 403, r.text

        assert _book(client).status_code == 201
