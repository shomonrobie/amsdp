"""Tests for Patient Service — BR §10–§11."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patient.main import app, _patients_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _patients_db.clear()


class TestPatientRegistration:
    def test_register_patient(self):
        resp = client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "Jamila Begum",
            "mobile": "01711111111",
        })
        assert resp.status_code == 201
        data = resp.json()["patient"]
        assert data["name"] == "Jamila Begum"
        assert data["organization_id"] == "org-1"

    def test_register_without_name_422(self):
        resp = client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "", "mobile": "",
        })
        assert resp.status_code == 422

    def test_duplicate_mobile_warns(self):
        _patients_db.clear()
        client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "A", "mobile": "01711111111",
        })
        resp = client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "B", "mobile": "01711111111",
        })
        assert resp.status_code == 201
        assert len(resp.json()["duplicates"]) == 1

    def test_cross_org_duplicate_no_warning(self):
        _patients_db.clear()
        client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "A", "mobile": "01711111111",
        })
        resp = client.post("/api/v1/patients", json={
            "organization_id": "org-2", "name": "B", "mobile": "01711111111",
        })
        assert resp.status_code == 201
        assert len(resp.json()["duplicates"]) == 0


class TestPatientSearch:
    @classmethod
    def setup_class(cls):
        _patients_db.clear()
        client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "Jamila Begum",
            "mobile": "01711111111",
        })
        client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "Rahim Molla",
            "mobile": "01722222222",
        })
        client.post("/api/v1/patients", json={
            "organization_id": "org-2", "name": "Karim Molla",
            "mobile": "01733333333",
        })

    def test_search_by_name(self):
        resp = client.get("/api/v1/patients?organization_id=org-1&q=Jamila")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_cross_org_isolated(self):
        resp = client.get("/api/v1/patients?organization_id=org-2&q=Molla")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["name"] == "Karim Molla"

    def test_search_all_in_org(self):
        resp = client.get("/api/v1/patients?organization_id=org-1")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


class TestPatientMerge:
    @classmethod
    def setup_class(cls):
        _patients_db.clear()
        r1 = client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "Dupli A", "mobile": "01711111111",
        })
        r2 = client.post("/api/v1/patients", json={
            "organization_id": "org-1", "name": "Dupli B", "mobile": "01711111111",
        })
        cls.p1 = r1.json()["patient"]["id"]
        cls.p2 = r2.json()["patient"]["id"]

    def test_merge_patients(self):
        resp = client.post("/api/v1/patients/merge", json={
            "primary_patient_id": self.p1,
            "duplicate_patient_id": self.p2,
            "reason": "same patient",
        })
        assert resp.status_code == 200
        assert resp.json()["merged"] is True

    def test_merge_not_found(self):
        resp = client.post("/api/v1/patients/merge", json={
            "primary_patient_id": "nonexistent",
            "duplicate_patient_id": "nonexistent2",
            "reason": "test",
        })
        assert resp.status_code == 404

    def test_merge_cross_org_422(self):
        r3 = client.post("/api/v1/patients", json={
            "organization_id": "org-2", "name": "Other", "mobile": "01799999999",
        })
        other_id = r3.json()["patient"]["id"]
        resp = client.post("/api/v1/patients/merge", json={
            "primary_patient_id": self.p1,
            "duplicate_patient_id": other_id,
            "reason": "attempt cross-org",
        })
        assert resp.status_code == 422