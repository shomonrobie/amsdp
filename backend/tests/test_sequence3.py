"""Sequence 3 tests — missed-turn recovery, notification outbox, org config.

Covers (see docs/implementation/AMSDP_SEQ_03_COMPLETION_REPORT.md):
* WP2  queue missed-turn / recovery contract (BR §27A)
* WP4  outbox + mock provider + worker state machine
* WP5  N1 confirmation / N2 reminder planning, cancellation, re-planning
* WP6  org-admin notification configuration API (server-side validation)

Every test scopes its own organization and users, so the suite is repeatable and
never deletes rows it does not own (audit events are append-only and never
removed).
"""
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "queuing"))

from common.auth import _ALGO, _SECRET
from common.database import SessionFactory
from common.models import (Appointment, AuditEvent, Branch, Doctor, Notification,
                           Organization, Patient, QueueEntry, StaffUser,
                           TrackingToken)
from common.notifications import outbox, worker
from common.notifications import config as notif_config
from common.notifications import hooks as notif_hooks
from common.notifications.providers import ProviderResult

from queuing.main import app as queue_app
from appointment.main import app as appointment_app
from organization.main import app as organization_app

queue_client = TestClient(queue_app)
appointment_client = TestClient(appointment_app)
org_client = TestClient(organization_app)

ORG = "sq3-org"
BR = "sq3-br"
DOC = "sq3-doc"
PAT = "sq3-pat"
ORG2 = "sq3-org2"
BR2 = "sq3-br2"
DOC2 = "sq3-doc2"
PAT2 = "sq3-pat2"
TZ = ZoneInfo("Asia/Dhaka")
TODAY = date.today()

#: role, organization, branch
USERS = {
    "orgadm": ("sq3_orgadm", "org_admin", ORG, None),
    "bradm": ("sq3_bradm", "branch_admin", ORG, BR),
    "recp": ("sq3_recp", "receptionist", ORG, BR),
    "dr": ("sq3_dr", "doctor", ORG, BR),
    "ast": ("sq3_ast", "assistant", ORG, BR),
}
PASSWORD = "testpass123"


# ---------------------------------------------------------------------------
# Fixtures / seed helpers
# ---------------------------------------------------------------------------

def _seed():
    """Purge this suite's business rows, then ensure the reference rows exist.

    Organizations, branches, doctors and staff users are **never deleted**: the
    append-only audit trail references them by foreign key, so removing them
    would rewrite history. They are created once and reused.
    """
    s = SessionFactory()
    try:
        appointment_ids = [row[0] for row in s.query(Appointment.id).filter(
            Appointment.organization_id.in_([ORG, ORG2])).all()]
        s.query(Notification).filter(
            Notification.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
        s.query(QueueEntry).filter(
            QueueEntry.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
        if appointment_ids:
            s.query(TrackingToken).filter(
                TrackingToken.appointment_id.in_(appointment_ids)).delete(
                synchronize_session=False)
        s.query(Appointment).filter(
            Appointment.organization_id.in_([ORG, ORG2])).delete(
            synchronize_session=False)
        s.commit()

        if not s.query(Organization).filter(Organization.id == ORG).first():
            s.add(Organization(id=ORG, name="Sequence Three Hospital", code=ORG,
                               timezone="Asia/Dhaka", locale="en"))
        if not s.query(Organization).filter(Organization.id == ORG2).first():
            s.add(Organization(id=ORG2, name="Other Hospital", code=ORG2,
                               timezone="Asia/Dhaka", locale="en"))
        s.commit()
        if not s.query(Branch).filter(Branch.id == BR).first():
            s.add(Branch(id=BR, organization_id=ORG, name="Main", code=BR))
        if not s.query(Branch).filter(Branch.id == BR2).first():
            s.add(Branch(id=BR2, organization_id=ORG2, name="Other", code=BR2))
        s.commit()
        if not s.query(Doctor).filter(Doctor.id == DOC).first():
            s.add(Doctor(id=DOC, organization_id=ORG, name="Dr. Sequence",
                         mobile="01700000001"))
        if not s.query(Doctor).filter(Doctor.id == DOC2).first():
            s.add(Doctor(id=DOC2, organization_id=ORG2, name="Dr. Foreign",
                         mobile="01700000002"))
        s.commit()
        for pid, name, mobile, sex in ((PAT, "Queue Patient", "01700000123",
                                        "male"),
                                       (PAT2, "Foreign Patient", "01700000456",
                                        "female")):
            org = ORG if pid == PAT else ORG2
            s.query(Patient).filter(Patient.id == pid).delete()
            s.add(Patient(id=pid, organization_id=org, name=name,
                          mobile=mobile, sex=sex))
        s.commit()

        pw = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
        for username, role, org, branch in USERS.values():
            user = s.query(StaffUser).filter(
                StaffUser.username == username).first()
            if user is None:
                s.add(StaffUser(id=str(uuid.uuid4()), organization_id=org,
                                username=username, password_hash=pw,
                                display_name=username.title(), role=role,
                                status="active", branch_id=branch))
            else:
                user.organization_id, user.branch_id = org, branch
                user.role, user.status = role, "active"
        s.commit()
    finally:
        s.close()


@pytest.fixture(autouse=True)
def _fresh_state():
    """Re-seed reference rows and a default (all channels off) org config."""
    _seed()
    _reset_org_config()
    yield


def _token(username: str) -> str:
    s = SessionFactory()
    try:
        user = s.query(StaffUser).filter(StaffUser.username == username).first()
        payload = {"sub": user.id, "org": user.organization_id,
                   "branch": user.branch_id, "role": user.role}
    finally:
        s.close()
    payload["exp"] = int((datetime.now(timezone.utc)
                          + timedelta(hours=2)).timestamp())
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def _headers(key: str) -> dict:
    """Authorization header for one of this suite's users.

    ``key`` is normally a :data:`USERS` key (``"recp"``). A literal username is
    also accepted, so a helper can target an ad-hoc account. Resolution by key
    is deliberate: the shared dev database also holds unrelated test users whose
    usernames collide with these short keys (e.g. ``recp`` in ``m2-test-org``),
    and a naive username lookup would silently authenticate the wrong tenant.
    """
    username = USERS[key][0] if key in USERS else key
    return {"Authorization": f"Bearer {_token(username)}"}


def _set_org_config(org_config, org_id: str = ORG):
    s = SessionFactory()
    try:
        org = s.query(Organization).filter(Organization.id == org_id).first()
        org.config = org_config
        s.commit()
    finally:
        s.close()


def _reset_org_config():
    """Return both suite organizations to the safe default: nothing enabled."""
    s = SessionFactory()
    try:
        for org in s.query(Organization).filter(
                Organization.id.in_([ORG, ORG2])).all():
            org.config = {}
        s.commit()
    finally:
        s.close()


def _enabled_config(lead: int = 10, channel: str = "whatsapp") -> dict:
    return {"notification_config": {
        "whatsapp": {"enabled": channel == "whatsapp", "provider": "mock"},
        "sms": {"enabled": channel == "sms", "provider": "mock"},
        "reminder_lead_minutes": lead,
    }}


def _queue_entry(status: str, position: int, token: str, *,
                 appointment_id=None, org=ORG, branch=BR, doctor=DOC,
                 patient=PAT, day=TODAY):
    entry_id = str(uuid.uuid4())
    s = SessionFactory()
    try:
        s.add(QueueEntry(id=entry_id, organization_id=org, branch_id=branch,
                         doctor_id=doctor, date=day, position=position,
                         token=token, status=status, patient_id=patient,
                         appointment_id=appointment_id,
                         entry_source="appointment", status_history=[],
                         position_history=[]))
        s.commit()
    finally:
        s.close()
    return entry_id


def _entry(entry_id: str) -> QueueEntry:
    s = SessionFactory()
    try:
        e = s.query(QueueEntry).filter(QueueEntry.id == entry_id).first()
        s.expunge(e)
        return e
    finally:
        s.close()


def _notifications(appointment_id: str):
    s = SessionFactory()
    try:
        rows = s.query(Notification).filter(
            Notification.appointment_id == appointment_id).all()
        for r in rows:
            s.expunge(r)
        return sorted(rows, key=lambda r: (r.notification_type, r.channel))
    finally:
        s.close()


def _audit_actions(target_id: str):
    s = SessionFactory()
    try:
        return [e.action for e in s.query(AuditEvent).filter(
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp).all()]
    finally:
        s.close()


def _book(start_time: str, day=None, doctor=DOC, patient=PAT) -> dict:
    payload = {"patient_id": patient, "doctor_id": doctor,
               "appointment_date": str(day or (TODAY + timedelta(days=2))),
               "start_time": start_time, "appointment_type": "scheduled",
               "booking_source": "reception", "notes": ""}
    r = appointment_client.post("/api/v1/appointments", json=payload,
                                headers=_headers("recp"))
    assert r.status_code == 201, r.text
    return r.json()


def _local(*, days=2, hh=10, mm=0) -> datetime:
    return datetime.combine(TODAY + timedelta(days=days),
                            datetime.min.time(), tzinfo=TZ).replace(
        hour=hh, minute=mm)


# ---------------------------------------------------------------------------
# WP2 — missed-turn recovery (BR §27A)
# ---------------------------------------------------------------------------

def test_missed_turn_marks_skipped_and_preserves_identity():
    entry_id = _queue_entry("waiting", 2, "T-SQ3-002")
    before = _entry(entry_id)

    r = queue_client.post(f"/api/v1/queue/{entry_id}/missed-turn",
                          json={"reason": "no response when called"},
                          headers=_headers("recp"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == entry_id
    assert body["status"] == "skipped"
    assert body["token"] == before.token
    assert body["position"] == before.position
    assert body["recovery"]["state"] == "awaiting_recovery"
    assert body["recovery"]["token_preserved"] is True

    after = _entry(entry_id)
    assert after.status == "skipped"
    assert after.status_history[-1]["action"] == "missed_turn"
    assert "queue.missed_turn" in _audit_actions(entry_id)


def test_missed_turn_is_idempotent_only_once():
    entry_id = _queue_entry("waiting", 1, "T-SQ3-001")
    url = f"/api/v1/queue/{entry_id}/missed-turn"
    assert queue_client.post(url, json={}, headers=_headers("recp")).status_code == 200
    again = queue_client.post(url, json={}, headers=_headers("recp"))
    assert again.status_code == 422
    assert "already recorded" in again.json()["detail"]


@pytest.mark.parametrize("status", ["in_consultation", "completed",
                                    "cancelled", "no_show"])
def test_missed_turn_rejects_non_waiting_states(status):
    entry_id = _queue_entry(status, 1, f"T-SQ3-{status}")
    r = queue_client.post(f"/api/v1/queue/{entry_id}/missed-turn",
                          json={}, headers=_headers("recp"))
    assert r.status_code == 422


def test_recover_renumbers_queue_and_keeps_token():
    first = _queue_entry("waiting", 2, "T-B-001")
    second = _queue_entry("waiting", 4, "T-B-002")
    skipped = _queue_entry("skipped", 7, "T-B-003")
    before = _entry(skipped)

    r = queue_client.post(f"/api/v1/queue/{skipped}/recover", json={},
                          headers=_headers("recp"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "waiting"
    assert body["recovery"]["mode"] == "end_of_queue"
    assert body["recovery"]["position"] == 3
    assert body["recovery"]["repositioned_others"] == 2

    after = _entry(skipped)
    assert after.status == "waiting"
    assert after.position == 3
    assert after.token == before.token
    assert after.id == before.id
    assert after.position_history[-1]["to"] == 3
    assert after.status_history[-1]["action"] == "recover"
    assert _entry(first).position == 1
    assert _entry(second).position == 2
    assert "queue.recover" in _audit_actions(skipped)
    assert "queue.reposition" in _audit_actions(first)


def test_recover_rejects_non_skipped_entry():
    entry_id = _queue_entry("waiting", 1, "T-F-001")
    r = queue_client.post(f"/api/v1/queue/{entry_id}/recover", json={},
                          headers=_headers("recp"))
    assert r.status_code == 422
    assert "skipped" in r.json()["detail"]


def test_recover_override_requires_reason_and_repositions():
    first = _queue_entry("waiting", 1, "T-C-001")
    second = _queue_entry("waiting", 2, "T-C-002")
    skipped = _queue_entry("skipped", 3, "T-C-003")
    url = f"/api/v1/queue/{skipped}/recover"

    no_reason = queue_client.post(url, json={"target_position": 1},
                                  headers=_headers("recp"))
    assert no_reason.status_code == 422
    assert "reason" in no_reason.json()["detail"]

    too_far = queue_client.post(
        url, json={"target_position": 9, "reason": "clinical priority"},
        headers=_headers("recp"))
    assert too_far.status_code == 422

    ok = queue_client.post(url, json={"target_position": 1,
                                      "reason": "emergency follow-up"},
                           headers=_headers("recp"))
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["recovery"]["mode"] == "position_override"
    assert body["recovery"]["position"] == 1
    assert _entry(first).position == 2
    assert _entry(second).position == 3
    assert "queue.reposition" in _audit_actions(first)


def test_recovery_cross_branch_and_cross_org_are_404():
    other_branch = _queue_entry("skipped", 1, "T-ISO-001", branch=BR2)
    foreign = _queue_entry("skipped", 1, "T-ISO-002", org=ORG2, branch=BR2,
                           doctor=DOC2, patient=PAT2)
    for entry_id in (other_branch, foreign):
        r = queue_client.post(f"/api/v1/queue/{entry_id}/recover", json={},
                              headers=_headers("recp"))
        assert r.status_code == 404, r.text
        assert r.json()["detail"] == "queue entry not found"
        # Nothing changed for the untouchable entry.
        assert _entry(entry_id).status == "skipped"

    # The missed-turn route is scoped by the same gate: no disclosure, no change.
    foreign_waiting = _queue_entry("waiting", 2, "T-ISO-003", org=ORG2,
                                   branch=BR2, doctor=DOC2, patient=PAT2)
    missed = queue_client.post(f"/api/v1/queue/{foreign_waiting}/missed-turn",
                               json={"reason": "x"}, headers=_headers("recp"))
    assert missed.status_code == 404, missed.text
    assert missed.json()["detail"] == "queue entry not found"
    assert _entry(foreign_waiting).status == "waiting"


def test_assistant_cannot_recover_or_confirm_missed_turn():
    entry_id = _queue_entry("waiting", 1, "T-PERM-001")
    r1 = queue_client.post(f"/api/v1/queue/{entry_id}/missed-turn", json={},
                           headers=_headers("ast"))
    assert r1.status_code == 403
    r2 = queue_client.post(f"/api/v1/queue/{entry_id}/recover", json={},
                           headers=_headers("ast"))
    assert r2.status_code == 403
    assert _entry(entry_id).status == "waiting"


def test_doctor_may_confirm_and_recover_within_their_queue():
    entry_id = _queue_entry("waiting", 1, "T-DOC-001")
    assert queue_client.post(f"/api/v1/queue/{entry_id}/missed-turn",
                             json={"reason": "patient stepped out"},
                             headers=_headers("dr")).status_code == 200
    r = queue_client.post(f"/api/v1/queue/{entry_id}/recover",
                          json={"reason": "patient returned"},
                          headers=_headers("dr"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "waiting"


def test_recovery_survives_notification_failure(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("notification subsystem unavailable")

    monkeypatch.setattr(notif_hooks, "on_queue_changed", _boom)
    skipped = _queue_entry("skipped", 1, "T-RESIL-001")
    r = queue_client.post(f"/api/v1/queue/{skipped}/recover", json={},
                          headers=_headers("recp"))
    assert r.status_code == 200, r.text
    assert _entry(skipped).status == "waiting"


# ---------------------------------------------------------------------------
# WP4/WP5 — outbox, provider, worker, N1/N2
# ---------------------------------------------------------------------------

def test_notification_config_defaults_to_everything_disabled():
    cfg = notif_config.get_notification_config(None)
    assert cfg["whatsapp"]["usable"] is False
    assert cfg["whatsapp"]["status"] == "disabled"
    assert cfg["sms"]["status"] == "disabled"
    assert cfg["reminder_lead_minutes"] == 10


def test_booking_creates_confirmation_and_planned_reminder():
    _set_org_config(_enabled_config(lead=10))
    appt = _book("10:00")

    rows = _notifications(appt["id"])
    assert len(rows) == 2
    confirmation, reminder = rows
    assert confirmation.notification_type == outbox.CONFIRMATION
    assert confirmation.channel == "whatsapp"
    assert confirmation.status == "pending"
    assert confirmation.recipient_mobile == "01700000123"
    assert "Dr. Sequence" in confirmation.payload["body"]
    assert reminder.notification_type == outbox.REMINDER
    expected = _local(days=2, hh=10) - timedelta(minutes=10)
    delta = abs((outbox.as_utc(reminder.scheduled_at) - expected).total_seconds())
    assert delta < 2, (reminder.scheduled_at, expected)


def test_no_messages_when_org_has_not_enabled_a_channel():
    appt = _book("11:00")
    assert _notifications(appt["id"]) == []


def test_walk_in_booking_creates_no_message():
    _set_org_config(_enabled_config())
    r = appointment_client.post(
        "/api/v1/appointments/walk-in",
        json={"patient_id": PAT, "doctor_id": DOC, "notes": "walked in"},
        headers=_headers("recp"))
    assert r.status_code == 201, r.text
    assert _notifications(r.json()["id"]) == []


def test_appointment_starting_now_gets_no_reminder():
    _set_org_config(_enabled_config())
    start = datetime.now(TZ) + timedelta(minutes=1)
    appt = _book(f"{start.hour:02d}:{start.minute:02d}", day=TODAY)
    rows = _notifications(appt["id"])
    assert [r.notification_type for r in rows] == [outbox.CONFIRMATION]


def test_repeated_booking_hook_does_not_duplicate_rows():
    _set_org_config(_enabled_config())
    appt = _book("09:30")
    first = _notifications(appt["id"])
    assert len(first) == 2
    keys = {r.dedup_key for r in first}

    again = notif_hooks.on_appointment_booked(appt["id"])
    second = _notifications(appt["id"])
    assert len(second) == 2
    assert {r.dedup_key for r in second} == keys
    assert again["channels"][0]["confirmation"] == "deduplicated"
    assert again["channels"][0]["reminder"] == "deduplicated"


def test_worker_marks_sent_but_never_delivered():
    _set_org_config(_enabled_config())
    appt = _book("09:00")

    summary = worker.run_once()
    assert summary["processed"] >= 1

    confirmation = [r for r in _notifications(appt["id"])
                    if r.notification_type == outbox.CONFIRMATION][0]
    assert confirmation.attempt_count == 1
    assert confirmation.status == "sent"
    assert confirmation.status != "delivered"
    assert confirmation.sent_at is not None
    assert confirmation.delivered_at is None
    assert confirmation.provider_message_id.startswith("mock-")


def test_cancelling_appointment_cancels_unsettled_messages():
    _set_org_config(_enabled_config())
    appt = _book("12:00")

    r = appointment_client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"status": "CANCELLED", "reason": "patient request"},
        headers=_headers("recp"))
    assert r.status_code == 200, r.text

    rows = _notifications(appt["id"])
    assert rows, "the rows must remain on record after cancellation"
    assert all(row.status == "cancelled" for row in rows), [r.status for r in rows]
    assert all(row.cancel_reason for row in rows)
    # Cancelled rows are never sent by the worker.
    worker.run_once()
    assert all(row.status == "cancelled" for row in _notifications(appt["id"]))


def test_provider_failure_retries_then_fails(monkeypatch):
    _set_org_config(_enabled_config())
    appt = _book("12:30")

    class _FailingProvider:
        name = "mock"

        def __init__(self, channel=""):
            self.channel = channel

        def send(self, **_kwargs):
            return ProviderResult(ok=False, provider="mock",
                                  error="provider timeout", retryable=True)

    monkeypatch.setattr(outbox, "get_provider",
                        lambda name, channel="": _FailingProvider(channel))

    first = worker.run_once()
    assert first["retry_scheduled"] >= 1
    row = [r for r in _notifications(appt["id"])
           if r.notification_type == outbox.CONFIRMATION][0]
    assert row.status == "retry_scheduled"
    assert row.next_attempt_at is not None
    assert row.error == "provider timeout"

    # Exhaust the attempt budget: the row becomes permanently failed.
    row_s = SessionFactory()
    try:
        stored = row_s.query(Notification).filter(
            Notification.id == row.id).first()
        stored.next_attempt_at = None
        stored.attempt_count = stored.max_attempts - 1
        row_s.commit()
    finally:
        row_s.close()

    second = worker.run_once()
    assert second["failed"] >= 1
    row = [r for r in _notifications(appt["id"])
           if r.notification_type == outbox.CONFIRMATION][0]
    assert row.status == "failed"
    assert row.sent_at is None


def test_queue_change_replans_pending_reminder():
    _set_org_config(_enabled_config(lead=10))
    start = datetime.now(TZ) + timedelta(minutes=30)
    appt = _book(f"{start.hour:02d}:{start.minute:02d}", day=TODAY)

    reminder = [r for r in _notifications(appt["id"])
                if r.notification_type == outbox.REMINDER][0]
    baseline = outbox.as_utc(reminder.scheduled_at)

    # Five patients are waiting ahead of this appointment: the estimate now
    # dominates the scheduled slot (5 x AVG_SERVICE_MINUTES > 30 minutes).
    own = _queue_entry("waiting", 6, "T-REPLAN-006",
                       appointment_id=appt["id"])
    for position in range(1, 6):
        _queue_entry("waiting", position, f"T-REPLAN-{position:03d}")

    summary = notif_hooks.on_queue_changed(ORG, DOC, TODAY, "queue changed")
    assert summary["replanned"] >= 1

    replanned = [r for r in _notifications(appt["id"])
                 if r.notification_type == outbox.REMINDER][0]
    assert replanned.id == reminder.id, "re-planning amends, never duplicates"
    assert replanned.dedup_key == reminder.dedup_key
    assert outbox.as_utc(replanned.scheduled_at) > baseline + timedelta(minutes=5)
    assert replanned.status == "pending"
    assert _entry(own).position == 6


# ---------------------------------------------------------------------------
# WP6 — organization notification configuration API
# ---------------------------------------------------------------------------

def test_org_admin_reads_and_updates_notification_config():
    read = org_client.get(f"/api/v1/orgs/{ORG}/notification-config",
                          headers=_headers("orgadm"))
    assert read.status_code == 200, read.text
    assert read.json()["whatsapp"]["status"] == "disabled"
    assert read.json()["platform"]["implemented_providers"] == ["mock"]
    assert "api_key" not in json.dumps(read.json()).lower()

    put = org_client.put(f"/api/v1/orgs/{ORG}/notification-config",
                         json={"whatsapp_enabled": True,
                               "reminder_lead_minutes": 5},
                         headers=_headers("orgadm"))
    assert put.status_code == 200, put.text
    updated = put.json()
    assert updated["whatsapp"]["enabled"] is True
    assert updated["whatsapp"]["status"] == "configured"
    assert updated["whatsapp"]["usable"] is True
    assert updated["sms"]["enabled"] is False
    assert updated["reminder_lead_minutes"] == 5
    assert updated["updated_by"]

    again = org_client.get(f"/api/v1/orgs/{ORG}/notification-config",
                           headers=_headers("orgadm"))
    assert again.json()["whatsapp"]["enabled"] is True
    assert "notification_config.updated" in _audit_actions(ORG)


def test_notification_config_rejects_unapproved_provider_and_lead():
    bad_provider = org_client.put(
        f"/api/v1/orgs/{ORG}/notification-config",
        json={"whatsapp_provider": "twilio"}, headers=_headers("orgadm"))
    assert bad_provider.status_code == 422
    assert "not available" in bad_provider.json()["detail"]

    bad_lead = org_client.put(
        f"/api/v1/orgs/{ORG}/notification-config",
        json={"reminder_lead_minutes": 7}, headers=_headers("orgadm"))
    assert bad_lead.status_code == 422
    assert "reminder_lead_minutes" in bad_lead.json()["detail"]

    no_change = org_client.put(
        f"/api/v1/orgs/{ORG}/notification-config", json={},
        headers=_headers("orgadm"))
    assert no_change.status_code == 422


def test_branch_admin_cannot_read_notification_config():
    r = org_client.get(f"/api/v1/orgs/{ORG}/notification-config",
                       headers=_headers("bradm"))
    assert r.status_code == 403


def test_cross_org_notification_config_is_non_disclosing_404():
    get_config = org_client.get(f"/api/v1/orgs/{ORG2}/notification-config",
                                headers=_headers("orgadm"))
    assert get_config.status_code == 404
    put_config = org_client.put(f"/api/v1/orgs/{ORG2}/notification-config",
                                json={"whatsapp_enabled": True},
                                headers=_headers("orgadm"))
    assert put_config.status_code == 404
    status = org_client.get(f"/api/v1/orgs/{ORG2}/notification-status",
                            headers=_headers("orgadm"))
    assert status.status_code == 404

    # The foreign organization was not modified.
    s = SessionFactory()
    try:
        org2 = s.query(Organization).filter(Organization.id == ORG2).first()
        assert not ((org2.config or {}).get("notification_config") or {})
    finally:
        s.close()


def test_notification_status_separates_sent_from_delivered():
    _set_org_config(_enabled_config())
    _book("13:00")
    worker.run_once()

    r = org_client.get(f"/api/v1/orgs/{ORG}/notification-status",
                       headers=_headers("orgadm"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["last_24h"]["sent"] >= 1
    assert body["last_24h"]["delivered"] == 0
    assert body["latest_message"]["status"] == "sent"
    assert body["latest_message"]["delivered_at"] == ""
    assert body["platform"]["integration_status"] == "mock-only"


def test_unusable_provider_config_sends_nothing():
    _set_org_config({"notification_config": {
        "whatsapp": {"enabled": True, "provider": "twilio"},
        "reminder_lead_minutes": 10}})
    appt = _book("14:00")
    assert _notifications(appt["id"]) == []






