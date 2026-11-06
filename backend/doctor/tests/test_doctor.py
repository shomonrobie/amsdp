"""Tests for Doctor Service — BR §9."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from doctor.main import app, _doctors_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _doctors_db.clear()


class TestDoctorLifecycle:
    def test_create_doctor(self):
        resp = client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "Dr. Rahman",
            "mobile": "01711111111", "speciality": "Cardiology",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Dr. Rahman"
        assert data["speciality"] == "Cardiology"

    def test_create_doctor_without_mobile_422(self):
        resp = client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "", "mobile": "",
        })
        assert resp.status_code == 422

    def test_search_doctors_by_org(self):
        _doctors_db.clear()
        client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "Dr. A", "mobile": "01711111111",
        })
        client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "Dr. B", "mobile": "01722222222",
        })
        client.post("/api/v1/doctors", json={
            "organization_id": "org-2", "name": "Dr. C", "mobile": "01733333333",
        })
        resp = client.get("/api/v1/doctors?organization_id=org-1")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_search_doctors_cross_org_isolated(self):
        resp = client.get("/api/v1/doctors?organization_id=org-2")
        assert resp.json()["total"] == 1

    def test_search_by_speciality(self):
        resp = client.get("/api/v1/doctors?organization_id=org-1&speciality=Cardiology")
        assert resp.status_code == 200

    def test_get_doctor(self):
        resp = client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "Dr. X",
            "mobile": "01755555555",
        })
        doc_id = resp.json()["id"]
        resp2 = client.get(f"/api/v1/doctors/{doc_id}")
        assert resp2.status_code == 200

    def test_get_missing_doctor_404(self):
        resp = client.get("/api/v1/doctors/nonexistent")
        assert resp.status_code == 404

    def test_update_doctor(self):
        resp = client.post("/api/v1/doctors", json={
            "organization_id": "org-1", "name": "Dr. Old",
            "mobile": "01766666666",
        })
        doc_id = resp.json()["id"]
        resp2 = client.patch(f"/api/v1/doctors/{doc_id}", json={
            "name": "Dr. Updated", "speciality": "Neurology",
        })
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Dr. Updated"
        assert resp2.json()["speciality"] == "Neurology"