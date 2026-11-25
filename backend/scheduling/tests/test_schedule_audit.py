"""Schedule and capacity changes leave a trail (owner decision Q5).

Q5 asks for the two things an operator cannot reconstruct after the fact:
**who changed a doctor's hours or capacity, and what the values were before and
after**.  The scheduling service therefore writes a specific event for each kind
of change — creation, activation, effective dates, templates, capacity — rather
than one opaque "schedule updated" row.

Each test reads the audit events from the database and asserts the values, not
just the event names: an event that says "capacity changed" without saying from
``1`` to ``3`` cannot answer the question it exists for.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_user, headers, load_app,
                               purge_org)
from common.models import AuditEvent, DoctorBranch

ORG = "schaudit-org"
BR = "schaudit-br"
DOC = "schaudit-doc"
ADMIN = "schaudit_admin"
RECP = "schaudit_recp"

WEEKDAY = 0          # Monday — the day the templates below publish on
MORNING = [{"day_of_week": WEEKDAY, "start_time": "09:00", "end_time": "10:00",
            "slot_duration_minutes": 15, "max_patients": 1}]


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("scheduling"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Audited", mobile="01700007001")
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    # A session can only be opened where the doctor is assigned, and the
    # assignment is a real row rather than a convention.
    with db_session() as s:
        if s.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == DOC,
                DoctorBranch.branch_id == BR).first() is None:
            s.add(DoctorBranch(id="schaudit-db", doctor_id=DOC,
                               branch_id=BR, is_primary=True, status="active"))
            s.commit()
    yield
    purge_org(ORG)


def _create(client, templates=None):
    response = client.post("/api/v1/schedules", headers=headers(ADMIN), json={
        "doctor_id": DOC, "organization_id": ORG, "branch_id": BR,
        "effective_from": "2031-01-01",
        "slot_templates": MORNING if templates is None else templates})
    assert response.status_code == 201, response.text
    return response.json()


def _events(action, target_id, reason=None):
    """The audit rows for one action, optionally only those with one reason.

    The MP-18 projection tests set up a session *and then* act on it, and both
    writes emit ``schedule.templates_changed`` on the same schedule id.  Counting
    every row therefore counted the setup as a failure; the reason filter is how
    a test names the one event it is about.
    """
    with db_session() as s:
        rows = s.query(AuditEvent).filter(
            AuditEvent.action == action,
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()
    return [row for row in rows if reason is None or row.reason == reason]


def _actions(target_id):
    with db_session() as s:
        return [row.action for row in s.query(AuditEvent).filter(
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()]


class TestScheduleAudit:
    def test_creating_a_schedule_is_audited(self, client):
        schedule = _create(client)
        events = _events("schedule.created", schedule["id"])
        assert len(events) == 1
        event = events[0]
        assert event.actor_id, "the actor is kept"
        assert event.actor_role == "branch_admin"
        assert event.branch_id == BR
        assert event.after["slot_templates"] == MORNING

    def test_a_capacity_change_carries_before_and_after(self, client):
        schedule = _create(client)
        widened = MORNING[0] | {"max_patients": 3}
        response = client.patch(
            f"/api/v1/schedules/{schedule['id']}", headers=headers(ADMIN),
            json={"slot_templates": [widened]})
        assert response.status_code == 200, response.text

        events = _events("schedule.capacity_change", schedule["id"])
        assert len(events) == 1
        event = events[0]
        window = f"{WEEKDAY} 09:00-10:00"
        assert event.before == {"capacity": {window: 1}}
        assert event.after == {"capacity": {window: 3}}
        assert event.reason == "slot capacity"

    def test_moving_the_hours_is_audited_separately_from_capacity(self, client):
        schedule = _create(client)
        moved = MORNING[0] | {"start_time": "10:00", "end_time": "11:00"}
        response = client.patch(
            f"/api/v1/schedules/{schedule['id']}", headers=headers(ADMIN),
            json={"slot_templates": [moved]})
        assert response.status_code == 200, response.text
        events = _events("schedule.templates_changed", schedule["id"])
        assert len(events) == 1
        assert events[0].before == {"windows": {f"{WEEKDAY} 09:00-10:00": 1}}
        assert events[0].after == {"windows": {f"{WEEKDAY} 10:00-11:00": 1}}

    def test_retiring_a_schedule_is_audited(self, client):
        schedule = _create(client)
        response = client.patch(
            f"/api/v1/schedules/{schedule['id']}", headers=headers(ADMIN),
            json={"status": "inactive"})
        assert response.status_code == 200, response.text
        events = _events("schedule.status_change", schedule["id"])
        assert len(events) == 1
        assert events[0].before == {"status": "active"}
        assert events[0].after == {"status": "inactive"}

    def test_the_generic_update_event_keeps_the_whole_before_and_after(self, client):
        schedule = _create(client)
        client.patch(f"/api/v1/schedules/{schedule['id']}",
                     headers=headers(ADMIN),
                     json={"slot_templates": [MORNING[0] | {"max_patients": 2}]})
        events = _events("schedule.updated", schedule["id"])
        assert len(events) == 1
        assert events[0].before["slot_templates"] == MORNING
        assert events[0].after["slot_templates"][0]["max_patients"] == 2


class TestSessionAudit:
    def _session(self, client, schedule_id, **extra):
        body = {"day_of_week": WEEKDAY, "start_time": "09:00",
                "end_time": "10:00", "slot_duration_minutes": 15,
                "max_patients": 1}
        body.update(extra)
        return client.post(f"/api/v1/schedules/{schedule_id}/sessions",
                           headers=headers(ADMIN), json=body)

    def test_creating_a_session_is_audited(self, client):
        schedule = _create(client)
        created = self._session(client, schedule["id"])
        assert created.status_code == 201, created.text
        session_id = created.json()["id"]
        events = _events("schedule.session.create", session_id)
        assert len(events) == 1
        assert events[0].after["start_time"] == "09:00"
        assert events[0].after["max_patients"] == 1

    def test_a_session_capacity_change_is_audited_with_both_values(self, client):
        schedule = _create(client)
        session_id = self._session(client, schedule["id"]).json()["id"]
        updated = client.patch(f"/api/v1/sessions/{session_id}",
                               headers=headers(ADMIN),
                               json={"max_patients": 4})
        assert updated.status_code == 200, updated.text
        events = _events("schedule.session.capacity_change", session_id)
        assert len(events) == 1
        assert events[0].before == {"max_patients": 1}
        assert events[0].after == {"max_patients": 4}

    def test_retiring_a_session_is_audited(self, client):
        schedule = _create(client)
        session_id = self._session(client, schedule["id"]).json()["id"]
        retired = client.delete(f"/api/v1/sessions/{session_id}",
                                headers=headers(ADMIN))
        assert retired.status_code in (200, 204), retired.text


class TestScheduleProjectionAudit:
    """MP-18 — a session write is also a *schedule* write.

    ``scheduling.session.sync_slot_templates`` rebuilds ``schedules.slot_templates``
    from the active sessions on every create, edit and retire: that list is the
    projection ``available-slots`` and the calendar read.  Before MP-18 the trail
    recorded the session change but not the schedule row it moved, which is the
    silent mutation the acceptance criterion forbids.  These tests assert the
    schedule-side event directly, on the schedule's own id.
    """

    def _session(self, client, schedule_id, start="11:00", end="12:00"):
        created = client.post(
            f"/api/v1/schedules/{schedule_id}/sessions", headers=headers(ADMIN),
            json={"day_of_week": WEEKDAY, "start_time": start, "end_time": end,
                  "slot_duration_minutes": 15, "max_patients": 1})
        assert created.status_code == 201, created.text
        return created.json()["id"]

    def test_creating_a_session_audits_the_schedule_projection(self, client):
        schedule = _create(client)
        self._session(client, schedule["id"])
        events = _events("schedule.templates_changed", schedule["id"])
        assert len(events) == 1
        event = events[0]
        assert event.target_type == "schedule"
        assert event.reason == "session created"
        assert event.before == {"windows": {f"{WEEKDAY} 09:00-10:00": 1}}
        assert event.after == {"windows": {f"{WEEKDAY} 09:00-10:00": 1,
                                           f"{WEEKDAY} 11:00-12:00": 1}}

    def test_moving_a_session_audits_both_window_sets(self, client):
        schedule = _create(client)
        session_id = self._session(client, schedule["id"])
        moved = client.patch(f"/api/v1/sessions/{session_id}",
                             headers=headers(ADMIN),
                             json={"start_time": "13:00", "end_time": "14:00"})
        assert moved.status_code == 200, moved.text
        events = _events("schedule.templates_changed", schedule["id"], "session updated")
        assert len(events) == 1
        assert f"{WEEKDAY} 11:00-12:00" in events[0].before["windows"]
        assert f"{WEEKDAY} 13:00-14:00" in events[0].after["windows"]
        assert f"{WEEKDAY} 11:00-12:00" not in events[0].after["windows"]

    def test_retiring_the_last_session_audits_the_window_disappearing(self, client):
        schedule = _create(client)
        session_id = self._session(client, schedule["id"])
        retired = client.delete(f"/api/v1/sessions/{session_id}",
                                headers=headers(ADMIN))
        assert retired.status_code in (200, 204), retired.text
        events = _events("schedule.templates_changed", schedule["id"], "session retired")
        assert len(events) == 1
        assert f"{WEEKDAY} 11:00-12:00" in events[0].before["windows"]
        assert events[0].after == {"windows": {f"{WEEKDAY} 09:00-10:00": 1}}
        assert events[0].reason == "session retired"

    def test_an_edit_that_does_not_move_a_window_writes_no_schedule_event(self, client):
        """The event says the *published windows* moved, so it must not be noise."""
        schedule = _create(client)
        session_id = self._session(client, schedule["id"])
        quiet = client.patch(f"/api/v1/sessions/{session_id}",
                             headers=headers(ADMIN),
                             json={"slot_duration_minutes": 20})
        assert quiet.status_code == 200, quiet.text
        assert _events("schedule.templates_changed", schedule["id"], "session updated") == []
        # The change itself is still in the trail, on the session.
        assert "schedule.session.update" in _actions(session_id)
