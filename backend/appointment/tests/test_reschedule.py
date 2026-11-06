"""Additional appointment tests — reschedule and edge cases."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from appointment.main import app, _appointments_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _appointments_db.clear()


class TestReschedule:
    def test_reschedule_creates_linked(self):
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-8", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        appt_id = r.json()["id"]
        r2 = client.post(f"/api/v1/appointments/{appt_id}/reschedule",
                         json={"new_date": "2026-04-16", "reason": "patient request"})
        assert r2.status_code == 200
        data = r2.json()
        assert data["original_appointment_id"] == appt_id
        assert data["new_appointment_id"] != appt_id

    def test_cannot_reschedule_completed(self):
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-9", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        a = r.json()["id"]
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "confirmed"})
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "arrived"})
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "in_progress"})
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "completed"})
        r2 = client.post(f"/api/v1/appointments/{a}/reschedule",
                         json={"new_date": "2026-04-16", "reason": "test"})
        assert r2.status_code == 422