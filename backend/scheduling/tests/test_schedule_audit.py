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


def _events(action, target_id):
    with db_session() as s:
        return s.query(AuditEvent).filter(
            AuditEvent.action == action,
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()


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
        assert "schedule.session.retire" in _actions(session_id)
