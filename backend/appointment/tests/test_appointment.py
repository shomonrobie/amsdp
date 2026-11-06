"""Tests for Appointment Service — BR §16–§20."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from appointment.main import app, _appointments_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _appointments_db.clear()


class TestAppointmentCreate:
    def test_create_appointment(self):
        resp = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-1", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "scheduled"
        assert resp.json()["token_number"].startswith("T-")

    def test_create_walk_in(self):
        resp = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-2", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
            "appointment_type": "walk_in",
        })
        assert resp.status_code == 201
        assert resp.json()["appointment_type"] == "walk_in"

    def test_create_without_patient_422(self):
        resp = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "", "doctor_id": "",
            "appointment_date": "2026-04-15",
        })
        assert resp.status_code == 422


class TestAppointmentRead:
    @classmethod
    def setup_class(cls):
        _appointments_db.clear()
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-3", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        cls.appt_id = r.json()["id"]

    def test_get_appointment(self):
        resp = client.get(f"/api/v1/appointments/{self.appt_id}")
        assert resp.status_code == 200

    def test_get_missing_404(self):
        resp = client.get("/api/v1/appointments/nonexistent")
        assert resp.status_code == 404

    def test_list_by_doctor_and_date(self):
        resp = client.get("/api/v1/appointments?doctor_id=doc-1&date=2026-04-15")
        assert resp.status_code == 200


class TestAppointmentStatus:
    def test_scheduled_to_confirmed(self):
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-4", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        appt_id = r.json()["id"]
        r2 = client.patch(f"/api/v1/appointments/{appt_id}/status",
                          json={"status": "confirmed"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "confirmed"

    def test_invalid_transition_rejected(self):
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-5", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        appt_id = r.json()["id"]
        r2 = client.patch(f"/api/v1/appointments/{appt_id}/status",
                          json={"status": "arrived"})
        assert r2.status_code == 422

    def test_full_lifecycle(self):
        r = client.post("/api/v1/appointments", json={
            "organization_id": "org-1", "branch_id": "branch-1",
            "patient_id": "pat-6", "doctor_id": "doc-1",
            "appointment_date": "2026-04-15",
        })
        a = r.json()["id"]
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "confirmed"})
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "arrived"})
        client.patch(f"/api/v1/appointments/{a}/status", json={"status": "in_progress"})
        r5 = client.patch(f"/api/v1/appointments/{a}/status",
                          json={"status": "completed"})
        assert r5.json()["status"] == "completed"