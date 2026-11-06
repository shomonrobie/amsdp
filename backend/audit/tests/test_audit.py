"""Tests for Audit Service."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit.main import app, _audit_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _audit_db.clear()


class TestAudit:
    def test_record_event(self):
        resp = client.post("/api/v1/audit", json={
            "service": "identity", "organization_id": "org-1",
            "action": "created", "target_type": "staff_user",
            "target_id": "user-1", "actor_id": "admin",
            "actor_role": "super_admin",
        })
        assert resp.status_code == 201
        assert resp.json()["event_id"]

    def test_get_events_by_target(self):
        resp = client.get("/api/v1/audit/user-1")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 1
        assert events[0]["target_id"] == "user-1"

    def test_filter_by_action(self):
        resp = client.get("/api/v1/audit/user-1?action=created")
        assert resp.status_code == 200
        for e in resp.json():
            assert e["action"] == "created"

    def test_get_org_events(self):
        # Record events for org-2
        client.post("/api/v1/audit", json={
            "service": "patient", "organization_id": "org-2",
            "action": "created", "target_type": "patient",
            "target_id": "pat-99", "actor_id": "staff",
            "actor_role": "receptionist",
        })
        resp = client.get("/api/v1/audit/organization/org-2")
        assert resp.status_code == 200
        for e in resp.json():
            assert e["organization_id"] == "org-2"

    def test_multiple_events_same_target(self):
        client.post("/api/v1/audit", json={
            "service": "appointment", "organization_id": "org-1",
            "action": "status_change", "target_type": "appointment",
            "target_id": "appt-1", "actor_id": "staff",
            "actor_role": "receptionist",
            "after": {"status": "confirmed"},
        })
        client.post("/api/v1/audit", json={
            "service": "appointment", "organization_id": "org-1",
            "action": "status_change", "target_type": "appointment",
            "target_id": "appt-1", "actor_id": "staff",
            "actor_role": "receptionist",
            "after": {"status": "arrived"},
        })
        resp = client.get("/api/v1/audit/appt-1")
        assert resp.status_code == 200
        # Most recent first (sorted reverse chrono)
        assert len(resp.json()) >= 2

    def test_empty_target(self):
        resp = client.get("/api/v1/audit/nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []