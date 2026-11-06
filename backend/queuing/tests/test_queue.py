"""Tests for Queue Management Service — BR §24, §30–§31."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from queuing.main import app, _queues_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _queues_db.clear()


class TestQueue:
    def test_enqueue_scheduled(self):
        resp = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
            "patient_id": "pat-1", "appointment_id": "appt-1",
            "entry_source": "appointment",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["position"] == 1
        assert data["token"].startswith("T-")
        assert data["status"] == "waiting"

    def test_enqueue_walk_in(self):
        resp = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
            "patient_id": "pat-2",
            "entry_source": "walk_in",
        })
        assert resp.status_code == 201
        assert resp.json()["entry_source"] == "walk_in"
        assert resp.json()["position"] == 2

    def test_get_queue_ordered(self):
        resp = client.get("/api/v1/queue", params={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
        })
        assert resp.status_code == 200
        positions = [e["position"] for e in resp.json()["entries"]]
        assert positions == sorted(positions)

    def test_queue_action_call(self):
        resp = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
            "patient_id": "pat-3", "entry_source": "appointment",
        })
        eid = resp.json()["queue_entry_id"]
        resp2 = client.patch(f"/api/v1/queue/{eid}",
                             json={"action": "call"})
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "called"

    def test_queue_full_lifecycle(self):
        resp = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
            "patient_id": "pat-4", "entry_source": "appointment",
        })
        eid = resp.json()["queue_entry_id"]
        client.patch(f"/api/v1/queue/{eid}", json={"action": "call"})
        client.patch(f"/api/v1/queue/{eid}", json={"action": "mark_arrived"})
        resp3 = client.patch(f"/api/v1/queue/{eid}",
                             json={"action": "complete_service"})
        assert resp3.json()["status"] == "served"

    def test_invalid_action_rejected(self):
        resp = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
            "patient_id": "pat-5", "entry_source": "appointment",
        })
        eid = resp.json()["queue_entry_id"]
        # cannot mark_arrived from waiting without first calling
        resp2 = client.patch(f"/api/v1/queue/{eid}",
                             json={"action": "mark_arrived"})
        assert resp2.status_code == 422

    def test_reorder_queue(self):
        _queues_db.clear()
        e1 = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-2", "date": "2026-04-15",
            "patient_id": "pat-a", "entry_source": "appointment",
        }).json()["queue_entry_id"]
        e2 = client.post("/api/v1/queue/enqueue", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-2", "date": "2026-04-15",
            "patient_id": "pat-b", "entry_source": "appointment",
        }).json()["queue_entry_id"]
        # swap positions
        resp = client.post("/api/v1/queue/reorder",
                           json={"entry_ids": [e2, e1]})
        assert resp.status_code == 200
        assert resp.json()["reordered"] == 2

    def test_history(self):
        resp = client.get("/api/v1/queue/history", params={
            "organization_id": "org-1", "branch_id": "branch-1",
            "doctor_id": "doc-1", "date": "2026-04-15",
        })
        assert resp.status_code == 200