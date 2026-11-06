"""Tests for Scheduling Service — BR §14–§15."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scheduling.main import app, _schedules_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _schedules_db.clear()


class TestScheduling:
    def test_create_schedule(self):
        resp = client.post("/api/v1/schedules", json={
            "doctor_id": "doc-1", "organization_id": "org-1",
            "branch_id": "branch-1",
            "slot_templates": [{
                "day_of_week": 0, "start_time": "09:00",
                "end_time": "13:00", "slot_duration_minutes": 15,
                "max_patients": 4,
            }],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["doctor_id"] == "doc-1"

    def test_get_available_slots(self):
        resp = client.post("/api/v1/schedules", json={
            "doctor_id": "doc-2", "organization_id": "org-1",
            "branch_id": "branch-1",
            "slot_templates": [{
                "day_of_week": 0, "start_time": "09:00",
                "end_time": "10:00", "slot_duration_minutes": 15,
                "max_patients": 2,
            }],
        })
        sid = resp.json()["id"]
        resp2 = client.get(f"/api/v1/schedules/{sid}/available-slots",
                           params={"date_str": "2026-04-15"})
        assert resp2.status_code == 200
        slots = resp2.json()["slots"]
        # 09:00-10:00 with 15-min slots = 4 slots
        assert len(slots) == 4
        assert slots[0]["start_time"] == "09:00"

    def test_search_by_doctor(self):
        resp = client.get("/api/v1/schedules?doctor_id=doc-1")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_search_by_org(self):
        resp = client.get("/api/v1/schedules?organization_id=org-1")
        assert resp.status_code == 200

    def test_get_slots_invalid_schedule_404(self):
        resp = client.get("/api/v1/schedules/bad-schedule/available-slots",
                          params={"date_str": "2026-01-01"})
        assert resp.status_code == 404