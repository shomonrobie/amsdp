"""Regression tests for the appointment/calendar reliability gaps (F-01…F-17).

Source: ``docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md``.
Each class names the findings it pins, and the test names use the vocabulary of
that document so the §8.3 evidence table can be filled from a ``-v`` run.

What the pre-existing corpus never covered, and this module does:

* **Concurrency** (F-01) — two receptionists booking the last seat at the same
  instant.  The fix is a row lock on the doctor, so the test has to be genuinely
  parallel; a sequential test would pass without any lock.
* **The slot window as the unit of capacity** (F-03/F-04) — a 09:07 booking
  occupies 09:00–09:15, and a reschedule into a full slot is refused.
* **Cross-tenant and cross-branch writes** (F-05/F-06/F-08/F-09/F-10) — every
  one of them answers a non-disclosing ``404`` and leaves the row untouched.
* **The capability behind a write** (F-07) — an ``assistant`` may read the
  calendar and must not be able to check a patient in.
* **A bounded calendar read** (F-17) — a bare request is a window, not a scan.

Fixtures are real rows in PostgreSQL (``tests/amsdp_test_support.py``); nothing
here bypasses authentication or the permission matrix.
"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment, QueueEntry, Schedule

ORG = "appt-rel-org"
OTHER_ORG = "appt-rel-other-org"
BR = "appt-rel-br"
BR2 = "appt-rel-br2"
OTHER_BR = "appt-rel-other-br"
DOC = "appt-rel-doc"
DOC2 = "appt-rel-doc2"
OTHER_DOC = "appt-rel-other-doc"
PAT = "appt-rel-pat"
PAT2 = "appt-rel-pat2"
RECP = "appt_rel_recp"
RECP2 = "appt_rel_recp2"
ASSIST = "appt_rel_assist"
OTHER_RECP = "appt_rel_other_recp"

#: The day every booking fixture uses.  The template's ``day_of_week`` is derived
#: from this date rather than hard-coded, so a weekday bug cannot make a test
#: pass by landing on a day the template does not cover (F-15).
DAY = date(2031, 6, 2)
WEEKDAY = DAY.weekday()


@pytest.fixture(scope="module")
def app():
    return load_app("appointment")


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def _world(client):
    # Purge first: purge_org removes the organization's owned rows, so seeding a
    # patient before it would delete that patient.
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    # Distinct mobiles: the doctor service treats a duplicate mobile as a
    # conflict, and these rows are shared across the suite.
    ensure_doctor(DOC, ORG, name="Dr. Primary", mobile="01700003001")
    ensure_doctor(DOC2, ORG, name="Dr. Second", mobile="01700003002")
    ensure_doctor(OTHER_DOC, OTHER_ORG, name="Dr. Foreign",
                  mobile="01700003003")
    ensure_patient(PAT, ORG, name="Primary Patient", mobile="01700003011")
    ensure_patient(PAT2, ORG, name="Second Patient", mobile="01700003012")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(RECP2, "receptionist", ORG, BR2)
    ensure_user(ASSIST, "assistant", ORG, BR)
    ensure_user(OTHER_RECP, "receptionist", OTHER_ORG, OTHER_BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _schedule(doctor_id=DOC, *, branch_id=BR, start="09:00", end="10:00",
              duration=15, capacity=1, day=None, status=None):
    """Store one schedule row with a single template, the way the API would."""
    sid = f"appt-rel-sch-{uuid.uuid4().hex[:8]}"
    with db_session() as s:
        row = Schedule(
            id=sid, doctor_id=doctor_id, organization_id=ORG,
            branch_id=branch_id, appointment_model="time_slot",
            effective_from=date(2030, 1, 1),
            slot_templates=[{"day_of_week": WEEKDAY if day is None else day,
                             "start_time": start, "end_time": end,
                             "slot_duration_minutes": duration,
                             "max_patients": capacity}])
        if status:
            row.status = status
        s.add(row)
        s.commit()
    return sid


def _book(client, *, patient=PAT, doctor=DOC, day=DAY, start="09:00",
          user=RECP):
    return client.post("/api/v1/appointments", headers=headers(user), json={
        "patient_id": patient, "doctor_id": doctor,
        "appointment_date": day.isoformat(), "start_time": start})


def _booked(client, **kwargs):
    """Book and return the created appointment body."""
    r = _book(client, **kwargs)
    assert r.status_code == 201, r.text
    return r.json()


def _row(appointment_id):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.id == appointment_id).first()


def _status(appointment_id) -> str:
    return _row(appointment_id).status


def _confirm(client, appointment_id, *, user=RECP):
    """Advance BOOKED → CONFIRMED, the lifecycle step check-in follows."""
    r = client.patch(f"/api/v1/appointments/{appointment_id}/status",
                     headers=headers(user),
                     json={"status": "CONFIRMED", "reason": "phone confirmed"})
    assert r.status_code == 200, r.text
    return r.json()


def _count(doctor=DOC, day=DAY) -> int:
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.doctor_id == doctor,
            Appointment.appointment_date == day).count()


class TestCapacityAtomicity:
    """F-01: count-then-insert is serialised by the doctor row lock."""

    def test_two_parallel_bookings_cannot_take_the_last_seat(self, app):
        # One 60-minute slot with capacity 1: exactly one of the two parallel
        # requests may succeed.  Without the lock both read "0 booked".
        _schedule(capacity=1, duration=60)
        barrier = threading.Barrier(2)

        def _attempt(_):
            with TestClient(app) as thread_client:
                barrier.wait(timeout=30)
                return _book(thread_client).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = sorted(pool.map(_attempt, range(2)))
        assert codes == [201, 422], codes
        assert _count() == 1

    def test_the_serial_number_is_allocated_once(self, app):
        # The same lock covers ``count(*) + 1``; two tokens numbered 1 would mean
        # two patients were told they are the first of the day.
        _schedule(capacity=5, duration=60)
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: _book(TestClient(app)).status_code,
                          range(2)))
        with db_session() as s:
            serials = sorted(row[0] for row in s.query(
                Appointment.serial_number).filter(
                Appointment.doctor_id == DOC,
                Appointment.appointment_date == DAY).all())
        assert serials == [1, 2]


class TestSlotWindowCapacity:
    """F-02/F-03: a slot window is the unit of capacity, not a minute string."""

    def test_a_malformed_time_is_refused(self, client):
        _schedule()
        r = _book(client, start="9am")
        assert r.status_code == 422, r.text
        assert _count() == 0

    def test_an_off_template_time_is_refused(self, client):
        _schedule()                          # publishes 09:00–10:00 only
        r = _book(client, start="11:00")
        assert r.status_code == 422, r.text
        assert "no_slot_covers_time" in r.json()["detail"]
        assert _count() == 0

    def test_a_minute_inside_a_slot_consumes_that_slot(self, client):
        _schedule(capacity=1)                # four 15-minute slots
        _booked(client, start="09:07")
        r = _book(client, start="09:00", patient=PAT2)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert "slot_full" in detail
        assert "09:00–09:15" in detail
        assert _count() == 1

    def test_the_neighbouring_slot_stays_bookable(self, client):
        _schedule(capacity=1)
        _booked(client, start="09:00")
        body = _booked(client, start="09:15", patient=PAT2)
        assert body["start_time"] == "09:15"
        assert _count() == 2

    def test_a_capacity_of_two_admits_two_and_refuses_the_third(self, client):
        _schedule(capacity=2, duration=60)
        _booked(client, start="09:00")
        _booked(client, start="09:10", patient=PAT2)
        third = ensure_patient("appt-rel-pat3", ORG, name="Third Patient",
                               mobile="01700003013")
        r = _book(client, start="09:20", patient=third)
        assert r.status_code == 422, r.text
        assert _count() == 2


class TestRescheduleCapacity:
    """F-04: a reschedule obeys the destination slot's capacity."""

    def test_reschedule_into_a_full_slot_is_refused(self, client):
        _schedule(capacity=1, duration=30)   # 09:00–09:30 and 09:30–10:00
        first = _booked(client, start="09:00")
        occupied = _booked(client, start="09:30", patient=PAT2)
        r = client.post(f"/api/v1/appointments/{first['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": DAY.isoformat(),
                              "new_start_time": "09:30",
                              "reason": "patient asked"})
        assert r.status_code == 422, r.text
        assert "slot_full" in r.json()["detail"]
        # Nothing moved: the refusal rolled back the whole move, including the
        # RESCHEDULED transition the route applies before it checks capacity.
        assert _status(first["id"]) == "BOOKED"
        assert _row(first["id"]).rescheduled_to is None
        assert _status(occupied["id"]) == "BOOKED"
        assert _count() == 2

    def test_a_reschedule_with_a_malformed_time_is_refused(self, client):
        _schedule()
        first = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{first['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": DAY.isoformat(),
                              "new_start_time": "9am", "reason": "typo"})
        assert r.status_code == 422, r.text
        assert _status(first["id"]) == "BOOKED"

    def test_a_reschedule_within_the_original_slot_is_allowed(self, client):
        # The original seat is being vacated, so moving to another minute of the
        # same capacity-1 slot must not be refused as a full slot.
        _schedule(capacity=1, duration=60)
        first = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{first['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": DAY.isoformat(),
                              "new_start_time": "09:20",
                              "reason": "same day, later in the hour"})
        assert r.status_code == 200, r.text
        moved = _row(r.json()["new_appointment_id"])
        assert moved.start_time == "09:20"
        assert _status(first["id"]) == "RESCHEDULED"


def _insert_at(day, *, doctor=DOC, branch=BR, start="09:00", status="BOOKED"):
    """Insert a calendar row directly, for reads that do not need booking."""
    aid = f"appt-rel-x-{uuid.uuid4().hex[:8]}"
    with db_session() as s:
        s.add(Appointment(id=aid, organization_id=ORG, branch_id=branch,
                          patient_id=PAT, doctor_id=doctor, appointment_date=day,
                          start_time=start, status=status))
        s.commit()
    return aid


class TestTenantAndBranchScope:
    """F-05/F-06/F-08/F-09/F-10: scoped reads and writes fail closed with 404."""

    def test_a_foreign_doctor_cannot_be_booked(self, client):
        r = _book(client, doctor=OTHER_DOC)
        assert r.status_code == 404, r.text
        assert _count(doctor=OTHER_DOC) == 0

    def test_an_unknown_doctor_is_not_disclosed(self, client):
        r = _book(client, doctor="no-such-doctor")
        assert r.status_code == 404, r.text
        assert _count(doctor="no-such-doctor") == 0

    def test_a_schedule_in_another_branch_does_not_move_the_booking(
            self, client):
        # F-06: the location resolver must not pick up a schedule the caller's
        # token cannot reach, and must still file the appointment in the
        # caller's own branch.
        _schedule(branch_id=BR2)
        body = _booked(client, start="09:00")
        assert body["branch_id"] == BR
        assert body["schedule_id"] == ""
        with db_session() as s:
            assert s.query(Appointment).filter(
                Appointment.branch_id == BR2).count() == 0

    def test_a_cross_branch_appointment_is_invisible(self, client):
        # F-09: detail reads are branch-scoped.  The appointment is real; the
        # caller simply may not learn that it is.
        foreign = _booked(client, user=RECP2)
        for user in (RECP, ASSIST):
            r = client.get(f"/api/v1/appointments/{foreign['id']}",
                           headers=headers(user))
            assert r.status_code == 404, (user, r.status_code)
        own = client.get(f"/api/v1/appointments/{foreign['id']}",
                         headers=headers(RECP2))
        assert own.status_code == 200, own.text

    def test_a_cross_branch_status_write_is_refused(self, client):
        # F-08: the same scope rule on the write path, and the row is untouched.
        foreign = _booked(client, user=RECP2)
        r = client.patch(f"/api/v1/appointments/{foreign['id']}/status",
                         headers=headers(RECP),
                         json={"status": "CONFIRMED", "reason": "scope probe"})
        assert r.status_code == 404, r.text
        assert _status(foreign["id"]) == "BOOKED"
        ok = client.patch(f"/api/v1/appointments/{foreign['id']}/status",
                          headers=headers(RECP2),
                          json={"status": "CONFIRMED", "reason": "own branch"})
        assert ok.status_code == 200, ok.text

    def test_a_cross_branch_check_in_is_refused(self, client):
        foreign = _booked(client, user=RECP2)
        r = client.post(f"/api/v1/appointments/{foreign['id']}/check-in",
                        headers=headers(RECP),
                        json={"status": "CHECKED_IN", "reason": "scope probe"})
        assert r.status_code == 404, r.text
        assert _status(foreign["id"]) == "BOOKED"
        with db_session() as s:
            assert s.query(QueueEntry).filter(
                QueueEntry.appointment_id == foreign["id"]).count() == 0




class TestCheckInCapability:
    """F-07: check-in is an appointment write, on both doors."""

    def test_an_assistant_cannot_check_a_patient_in(self, client):
        booked = _booked(client)
        r = client.post(f"/api/v1/appointments/{booked['id']}/check-in",
                        headers=headers(ASSIST),
                        json={"status": "CHECKED_IN"})
        assert r.status_code == 403, r.text
        assert _status(booked["id"]) == "BOOKED"
        with db_session() as s:
            assert s.query(QueueEntry).filter(
                QueueEntry.appointment_id == booked["id"]).count() == 0

    def test_a_receptionist_check_in_writes_status_and_queue_together(
            self, client):
        booked = _booked(client)
        _confirm(client, booked["id"])
        r = client.post(f"/api/v1/appointments/{booked['id']}/check-in",
                        headers=headers(RECP),
                        json={"status": "CHECKED_IN"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "CHECKED_IN"
        with db_session() as s:
            entry = s.query(QueueEntry).filter(
                QueueEntry.appointment_id == booked["id"]).one()
            assert entry.status == "waiting"
            assert entry.token
            assert entry.position == 1

    def test_a_second_check_in_is_idempotent(self, client):
        booked = _booked(client)
        _confirm(client, booked["id"])
        first = client.post(f"/api/v1/appointments/{booked['id']}/check-in",
                            headers=headers(RECP),
                            json={"status": "CHECKED_IN"})
        assert first.status_code == 200, first.text
        second = client.post(f"/api/v1/appointments/{booked['id']}/check-in",
                             headers=headers(RECP),
                             json={"status": "CHECKED_IN"})
        assert second.status_code == 200, second.text
        with db_session() as s:
            assert s.query(QueueEntry).filter(
                QueueEntry.appointment_id == booked["id"]).count() == 1

    def test_the_queue_door_refuses_a_role_without_the_capability(self, app):
        # The queue service's own check-in route is the sibling door F-07
        # records.  An assistant holds neither ``queue.checkin`` nor
        # ``appointment.modify``; the refusal is what keeps the two doors
        # equivalent.  (No role holds ``queue.checkin`` without
        # ``appointment.modify`` today, so the inner capability check there is
        # defence in depth rather than an observable narrowing.)
        queue_client = TestClient(load_app("queuing"))
        booked = _booked(TestClient(app))
        r = queue_client.post("/api/v1/queue/check-in",
                              headers=headers(ASSIST),
                              json={"appointment_id": booked["id"]})
        assert r.status_code == 403, r.text
        with db_session() as s:
            assert s.query(QueueEntry).filter(
                QueueEntry.appointment_id == booked["id"]).count() == 0



class TestTransferTarget:
    """F-10/F-11: a transfer names a real in-scope branch and one time."""

    def test_a_transfer_to_an_unknown_branch_is_refused(self, client):
        _schedule()
        original = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{original['id']}/transfer",
                        headers=headers(RECP),
                        json={"new_doctor_id": DOC2,
                              "new_branch_id": "no-such-branch",
                              "new_date": DAY.isoformat()})
        assert r.status_code == 404, r.text
        assert _status(original["id"]) == "BOOKED"

    def test_a_transfer_to_an_out_of_scope_branch_is_refused(self, client):
        _schedule()
        original = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{original['id']}/transfer",
                        headers=headers(RECP),
                        json={"new_doctor_id": DOC2, "new_branch_id": BR2,
                              "new_date": DAY.isoformat()})
        # BR2 is real, but a branch-scoped receptionist may not move work into
        # it; the refusal is the same non-disclosing 404.
        assert r.status_code == 404, r.text
        assert _status(original["id"]) == "BOOKED"

    def test_a_transfer_to_a_foreign_tenant_doctor_is_refused(self, client):
        _schedule()
        original = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{original['id']}/transfer",
                        headers=headers(RECP),
                        json={"new_doctor_id": OTHER_DOC, "new_branch_id": BR,
                              "new_date": DAY.isoformat()})
        assert r.status_code == 404, r.text
        assert _status(original["id"]) == "BOOKED"

    def test_a_transfer_without_a_new_time_keeps_the_original_hour(
            self, client):
        _schedule()                                   # DOC, 09:00–10:00
        target_schedule = _schedule(doctor_id=DOC2, capacity=5)
        original = _booked(client, start="09:00")
        r = client.post(f"/api/v1/appointments/{original['id']}/transfer",
                        headers=headers(RECP),
                        json={"new_doctor_id": DOC2, "new_branch_id": BR,
                              "new_date": DAY.isoformat()})
        assert r.status_code == 200, r.text
        moved = _row(r.json()["new_appointment_id"])
        assert moved.doctor_id == DOC2
        assert moved.start_time == "09:00"
        # F-11: the chamber snapshot comes from the same resolved time, so the
        # row carries the destination schedule rather than the old hour's.
        assert moved.schedule_id == target_schedule
        assert _status(original["id"]) == "RESCHEDULED"




class TestCalendarWindow:
    """F-17: the calendar read is a window, not a scan of the tenant."""

    def _get(self, client, **params):
        return client.get("/api/v1/appointments", headers=headers(RECP),
                          params=params)

    def test_a_bare_request_is_bounded(self, client):
        today = date.today()
        inside = _insert_at(today)
        outside = _insert_at(today + timedelta(days=300))
        ids = [row["id"] for row in self._get(client).json()]
        assert inside in ids
        assert outside not in ids

    def test_an_over_wide_range_is_refused(self, client):
        today = date.today()
        r = self._get(client,
                      date_from=str(today - timedelta(days=300)),
                      date_to=str(today + timedelta(days=300)))
        assert r.status_code == 422, r.text
        assert "date_range_too_wide" in r.json()["detail"]

    def test_an_explicit_range_still_reaches_old_rows(self, client):
        today = date.today()
        old = _insert_at(today - timedelta(days=300))
        r = self._get(client,
                      date_from=str(today - timedelta(days=310)),
                      date_to=str(today - timedelta(days=290)))
        assert r.status_code == 200, r.text
        assert [row["id"] for row in r.json()] == [old]

    def test_a_single_day_read_keeps_its_meaning(self, client):
        far = _insert_at(DAY)
        r = self._get(client, date=DAY.isoformat())
        assert r.status_code == 200, r.text
        assert [row["id"] for row in r.json()] == [far]
