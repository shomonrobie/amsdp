"""Tests for Identity & Access Service — Sprint 1."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from identity.main import app, _users_db
from identity.permissions import check as perm_check, PERMISSIONS
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _users_db.clear()


class TestStaffUserCreation:
    def test_create_user(self):
        resp = client.post("/api/v1/staff/users", json={
            "organization_id": "org-1", "username": "rahim",
            "password": "secret123", "display_name": "Rahim",
            "role": "receptionist", "locale": "bn",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"]
        assert data["role"] == "receptionist"

    def test_create_user_missing_org_rejected(self):
        resp = client.post("/api/v1/staff/users", json={
            "organization_id": "", "username": "noor",
            "password": "x", "display_name": "Noor", "role": "doctor",
        })
        assert resp.status_code == 422

    def test_create_user_unknown_role_rejected(self):
        resp = client.post("/api/v1/staff/users", json={
            "organization_id": "org-1", "username": "badrole",
            "password": "x", "display_name": "Bad", "role": "ceo",
        })
        assert resp.status_code == 422


class TestStaffLogin:
    def setup_method(self):
        _users_db.clear()
        client.post("/api/v1/staff/users", json={
            "organization_id": "org-1", "username": "rahim",
            "password": "secret123", "display_name": "Rahim",
            "role": "receptionist",
        })

    def test_login_success(self):
        resp = client.post("/api/v1/staff/login", json={
            "username": "rahim", "password": "secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"]
        assert data["user"]["role"] == "receptionist"

    def test_login_wrong_password(self):
        resp = client.post("/api/v1/staff/login", json={
            "username": "rahim", "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_unknown_user(self):
        resp = client.post("/api/v1/staff/login", json={
            "username": "nobody", "password": "x",
        })
        assert resp.status_code == 401


class TestValidateToken:
    @classmethod
    def setup_class(cls):
        _users_db.clear()
        client.post("/api/v1/staff/users", json={
            "organization_id": "org-1", "username": "amin",
            "password": "pass", "display_name": "Amin",
            "role": "doctor",
        })
        resp = client.post("/api/v1/staff/login", json={
            "username": "amin", "password": "pass",
        })
        cls.token = resp.json()["token"]

    def test_validate_valid_token(self):
        resp = client.get("/api/v1/staff/validate",
                          headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True
        assert resp.json()["role"] == "doctor"

    def test_validate_missing_token(self):
        resp = client.get("/api/v1/staff/validate")
        assert resp.status_code == 401


class TestPermissions:
    def test_super_admin_has_all(self):
        assert perm_check("anything.at.all", "super_admin") is True

    def test_receptionist_can_create_patient(self):
        assert perm_check("patient.create", "receptionist") is True

    def test_receptionist_cannot_manage_org(self):
        assert perm_check("org.manage", "receptionist") is False

    def test_doctor_cannot_reorder_queue(self):
        assert perm_check("queue.reorder", "doctor") is False

    def test_unknown_role_denied(self):
        assert perm_check("patient.read", "nobody") is False