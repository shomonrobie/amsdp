"""Sequence 4 regression tests — history is really written to the database.

Finding SEQ4-HISTORY-P0 (found in the Sequence 4 acceptance run): every history
mutation used to do ``h = row.status_history or []; h.append(...);
row.status_history = h``.  Because the loaded value *is* the committed value,
SQLAlchemy's ``is_equal`` sees no change and omits the column from the UPDATE, so
the row kept only its first history entry while the API returned the full list
and reported success.  Dependents: BR §18 traceability, Workflow D step 6
("the system records the change history") and Workflow E step 4.

These tests assert the value **read back from a fresh session**, not the value
echoed by the response, which is what hid the bug.

The reference rows and clients come from ``test_sequence3`` so the suite keeps a
single seeding story and never deletes rows it does not own.
"""
import os
import sys
from datetime import timedelta

from sqlalchemy import text

sys.path.insert(0, os.path.dirname(__file__))

from test_sequence3 import (DOC, PAT, TODAY, _audit_actions, _book,  # noqa: E402
                            _entry, _fresh_state, _headers,
                            appointment_client, queue_client)

from common.database import SessionFactory                   # noqa: E402
from common.models import Appointment, QueueEntry            # noqa: E402
from common.timeutil import operational_today                # noqa: E402


def _db_history(appointment_id: str):
    """status_history as stored in the database (fresh session, no cache)."""
    s = SessionFactory()
    try:
        a = s.query(Appointment).filter(Appointment.id == appointment_id).first()
        return list(a.status_history or [])
    finally:
        s.close()


def _db_entry(entry_id: str):
    return _entry(entry_id)


def _entries_for(appointment_id: str):
    """Queue entries created for one appointment (fresh session)."""
    s = SessionFactory()
    try:
        return s.query(QueueEntry).filter(
            QueueEntry.appointment_id == appointment_id).all()
    finally:
        s.close()


def _entry_from_appointment(appointment_id: str):
    rows = _entries_for(appointment_id)
    return rows[0] if rows else None


def _sequence_value(doctor_id: str, day) -> int:
    """The shared daily counter that every enqueue path must allocate from."""
    s = SessionFactory()
    try:
        row = s.execute(
            text("SELECT last_value FROM queue_sequences "
                 "WHERE doctor_id = :d AND date = :dt"),
            {"d": doctor_id, "dt": day}).fetchone()
        return row[0] if row else 0
    finally:
        s.close()


class TestAppointmentHistoryPersists:
    def test_status_transition_appends_and_persists(self, _fresh_state):
        a = _book("09:00")
        assert len(_db_history(a["id"])) == 1
        r = appointment_client.patch(
            f"/api/v1/appointments/{a['id']}/status",
            json={"status": "CONFIRMED"}, headers=_headers("recp"))
        assert r.status_code == 200, r.text
        hist = _db_history(a["id"])
        assert len(hist) == 2, hist
        assert hist[-1]["from"] == "BOOKED"
        assert hist[-1]["to"] == "CONFIRMED"

    def test_cancel_appends_and_persists(self, _fresh_state):
        a = _book("09:30")
        r = appointment_client.post(
            f"/api/v1/appointments/{a['id']}/cancel",
            json={"status": "CANCELLED", "reason": "patient request"},
            headers=_headers("recp"))
        assert r.status_code == 200, r.text
        assert [h["to"] for h in _db_history(a["id"])] == ["BOOKED", "CANCELLED"]

    def test_reschedule_records_the_true_previous_status(self, _fresh_state):
        a = _book("10:00")
        r = appointment_client.post(
            f"/api/v1/appointments/{a['id']}/reschedule",
            json={"new_date": str(TODAY + timedelta(days=3)),
                  "reason": "patient unavailable"}, headers=_headers("recp"))
        assert r.status_code == 200, r.text
        last = _db_history(a["id"])[-1]
        # The old code set status="RESCHEDULED" *before* reading it, so it
        # recorded the transition RESCHEDULED -> RESCHEDULED.
        assert (last["from"], last["to"]) == ("BOOKED", "RESCHEDULED"), last


class TestQueueHistoryPersists:
    def _check_in(self, start_time: str) -> dict:
        a = _book(start_time)
        r = queue_client.post("/api/v1/queue/check-in",
                              json={"appointment_id": a["id"]},
                              headers=_headers("recp"))
        assert r.status_code == 201, r.text
        return r.json()

    def test_action_appends_and_persists(self, _fresh_state):
        entry = self._check_in("11:00")
        assert len(_db_entry(entry["id"]).status_history) == 1
        r = queue_client.patch(f"/api/v1/queue/{entry['id']}",
                               json={"action": "call"}, headers=_headers("recp"))
        assert r.status_code == 200, r.text
        row = _db_entry(entry["id"])
        assert row.status == "called"
        assert len(row.status_history) == 2, row.status_history
        assert row.status_history[-1]["to"] == "called"

    def test_missed_turn_appends_and_persists(self, _fresh_state):
        entry = self._check_in("11:30")
        r = queue_client.post(f"/api/v1/queue/{entry['id']}/missed-turn",
                              json={"reason": "no response"},
                              headers=_headers("recp"))
        assert r.status_code in (200, 201), r.text
        row = _db_entry(entry["id"])
        assert row.status == "skipped"
        assert len(row.status_history) == 2, row.status_history
        assert row.status_history[-1]["action"] == "missed_turn"


class TestOperationalDate:
    """Finding SEQ4-TZ-P1 — one operational day for the whole visit.

    ``POST /appointments/walk-in`` derived "today" from UTC while the queue
    service derived it from the facility clock, so in a UTC+6 facility a walk-in
    registered after local midnight got an appointment dated the previous day
    and a queue entry dated the current one: one visit, two days.
    """

    def test_walk_in_appointment_and_entry_share_the_facility_day(self, _fresh_state):
        r = appointment_client.post(
            "/api/v1/appointments/walk-in",
            json={"patient_id": PAT, "doctor_id": DOC,
                  "placement": "end_of_queue"},
            headers=_headers("recp"))
        assert r.status_code in (200, 201), r.text
        walk_in = r.json()
        today = str(operational_today())
        assert walk_in["appointment_date"] == today, walk_in["appointment_date"]

        e = queue_client.post(
            "/api/v1/queue/enqueue",
            json={"doctor_id": DOC, "patient_id": PAT,
                  "entry_source": "walk_in", "walk_in_policy": "end_of_queue"},
            headers=_headers("recp"))
        assert e.status_code == 201, e.text
        assert e.json()["date"] == today, e.json()["date"]

    def test_queue_board_answers_on_the_facility_day(self, _fresh_state):
        e = queue_client.post(
            "/api/v1/queue/enqueue",
            json={"doctor_id": DOC, "patient_id": PAT,
                  "entry_source": "walk_in", "walk_in_policy": "end_of_queue"},
            headers=_headers("recp"))
        assert e.status_code == 201, e.text
        board = queue_client.get(
            "/api/v1/queue",
            params={"doctor_id": DOC, "date": str(operational_today())},
            headers=_headers("recp"))
        assert board.status_code == 200, board.text
        ids = [x["id"] for x in board.json()["entries"]]
        assert e.json()["id"] in ids, "the entry is missing from today's board"


class TestSingleTokenAuthority:
    """Finding SEQ4-TOKEN-P1 — one token per patient per doctor per day.

    The appointment service used to mint tokens from ``count(*) + 1`` while the
    queuing service used the atomic ``queue_sequences`` counter, so a walk-in
    enqueued after a scheduled check-in was issued a token that was already live
    (two active entries ``T-<DOC>-001`` for one doctor on one day).
    """

    def _walk_in(self):
        return queue_client.post(
            "/api/v1/queue/enqueue",
            json={"doctor_id": DOC, "patient_id": PAT,
                  "entry_source": "walk_in"}, headers=_headers("recp"))

    def _confirmed_booking(self, start_time: str) -> dict:
        """A BOOKED appointment moved to CONFIRMED (BOOKED cannot check in)."""
        a = _book(start_time, day=TODAY)
        r = appointment_client.patch(
            f"/api/v1/appointments/{a['id']}/status",
            json={"status": "CONFIRMED"}, headers=_headers("recp"))
        assert r.status_code == 200, r.text
        return a

    def _check_in(self, appointment_id: str):
        return appointment_client.post(
            f"/api/v1/appointments/{appointment_id}/check-in",
            json={"status": "CHECKED_IN"}, headers=_headers("recp"))

    def test_appointment_check_in_then_walk_in_keeps_tokens_unique(self, _fresh_state):
        a = self._confirmed_booking("14:00")
        r = self._check_in(a["id"])
        assert r.status_code == 200, r.text
        scheduled = _entry_from_appointment(a["id"])
        assert scheduled is not None, "check-in did not create a queue entry"
        # The shared counter — not a per-service count — decided the serial.
        assert scheduled.position == _sequence_value(DOC, scheduled.date), (
            "appointment check-in bypassed the shared token counter")

        w = self._walk_in()
        assert w.status_code == 201, w.text
        walk_in = w.json()
        assert walk_in["token"] != scheduled.token, (
            f"duplicate token {walk_in['token']} for {DOC} on {scheduled.date}")

    def test_appointment_check_in_allocates_from_the_shared_counter(self, _fresh_state):
        a = self._confirmed_booking("14:30")
        r = self._check_in(a["id"])
        assert r.status_code == 200, r.text
        first = _entry_from_appointment(a["id"])
        w = self._walk_in()
        assert w.status_code == 201, w.text
        second = _entry(w.json()["id"])
        # Both serials come from queue_sequences, so they are consecutive.
        assert second.position == first.position + 1, (first.position,
                                                       second.position)
        assert second.token.endswith(f"-{second.position:03d}")

    def test_appointment_check_in_records_history_and_audit(self, _fresh_state):
        a = self._confirmed_booking("15:00")
        r = self._check_in(a["id"])
        assert r.status_code == 200, r.text
        entry = _entry_from_appointment(a["id"])
        assert entry is not None
        row = _db_entry(entry.id)
        # The old code created the row with no history at all.
        assert len(row.status_history) == 1, row.status_history
        assert row.status_history[0]["to"] == "waiting"
        assert len(row.position_history) == 1, row.position_history
        # …and wrote no queue.checkin audit event.
        assert "queue.checkin" in _audit_actions(entry.id)

    def test_repeat_check_in_is_idempotent(self, _fresh_state):
        a = self._confirmed_booking("15:30")
        for _ in range(2):
            r = self._check_in(a["id"])
            assert r.status_code == 200, r.text
        entries = _entries_for(a["id"])
        assert len(entries) == 1, [e.token for e in entries]


class TestFacilityZone:
    """The facility day comes from ``organizations.timezone``, not the process TZ.

    Without this, a container whose ``TZ`` is UTC would reintroduce SEQ4-TZ-P1
    even with every service calling ``operational_today()``.
    """

    def _org(self, tz):
        import uuid as _uuid
        from common.models import Organization
        s = SessionFactory()
        try:
            org = Organization(id=f"tz-probe-{_uuid.uuid4().hex[:8]}",
                               name="TZ probe", code=f"TZP-{_uuid.uuid4().hex[:6]}",
                               timezone=tz)
            s.add(org); s.commit()
            return org.id
        finally:
            s.close()

    def _drop(self, org_id):
        from common.models import Organization
        s = SessionFactory()
        try:
            s.query(Organization).filter(Organization.id == org_id).delete()
            s.commit()
        finally:
            s.close()

    def test_operational_date_follows_the_organization_time_zone(self):
        from datetime import datetime
        from common.timeutil import facility_zone, operational_today
        org_id = self._org("Pacific/Kiritimati")
        try:
            s = SessionFactory()
            try:
                zone = facility_zone(s, org_id)
                # The zone itself must come from the organization; comparing only
                # dates can coincide with the default zone and hide a regression.
                assert zone.key == "Pacific/Kiritimati", zone.key
                assert operational_today(s, org_id) == datetime.now(zone).date()
            finally:
                s.close()
        finally:
            self._drop(org_id)

    def test_unknown_zone_falls_back_to_the_default(self):
        from common.timeutil import DEFAULT_TZ, facility_zone
        org_id = self._org("not/a-time-zone")
        try:
            s = SessionFactory()
            try:
                assert facility_zone(s, org_id).key == DEFAULT_TZ
                assert facility_zone(None, None).key == DEFAULT_TZ
            finally:
                s.close()
        finally:
            self._drop(org_id)

