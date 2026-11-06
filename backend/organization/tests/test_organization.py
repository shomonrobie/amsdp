"""Tests for Organization Service — Sprint 2."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from organization.main import app, _orgs_db, _branches_db
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    _orgs_db.clear()
    _branches_db.clear()


class TestOrgLifecycle:
    def test_create_org(self):
        resp = client.post("/api/v1/orgs", json={
            "name": "Uposhak Clinic", "code": "UPC-001",
            "facility_type": "clinic", "address": "Dhaka",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Uposhak Clinic"
        assert data["code"] == "UPC-001"
        assert data["status"] == "active"

    def test_get_org(self):
        resp = client.post("/api/v1/orgs", json={
            "name": "Green Clinic", "code": "GRN-001",
            "facility_type": "clinic",
        })
        org_id = resp.json()["id"]
        resp2 = client.get(f"/api/v1/orgs/{org_id}")
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Green Clinic"

    def test_get_missing_org_404(self):
        resp = client.get("/api/v1/orgs/nonexistent")
        assert resp.status_code == 404

    def test_update_org(self):
        resp = client.post("/api/v1/orgs", json={
            "name": "Old Name", "code": "OLD-001",
            "facility_type": "clinic",
        })
        org_id = resp.json()["id"]
        resp2 = client.patch(f"/api/v1/orgs/{org_id}", json={
            "name": "New Name", "address": "New Address",
        })
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "New Name"

    def test_list_orgs(self):
        resp = client.get("/api/v1/orgs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestBranchLifecycle:
    @classmethod
    def setup_class(cls):
        _orgs_db.clear()
        _branches_db.clear()
        resp = client.post("/api/v1/orgs", json={
            "name": "MultiBranch Hospital", "code": "MBH-001",
            "facility_type": "hospital",
        })
        cls.org_id = resp.json()["id"]

    def test_create_branch(self):
        resp = client.post("/api/v1/branches", json={
            "organization_id": self.org_id,
            "name": "Main Branch", "code": "MBH-MAIN",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Main Branch"
        assert data["organization_id"] == self.org_id

    def test_create_branch_invalid_org_404(self):
        resp = client.post("/api/v1/branches", json={
            "organization_id": "bad-org",
            "name": "Ghost Branch", "code": "GHOST",
        })
        assert resp.status_code == 404

    def test_list_branches_scoped_to_org(self):
        resp = client.get(f"/api/v1/orgs/{self.org_id}/branches")
        assert resp.status_code == 200
        branches = resp.json()
        for b in branches:
            assert b["organization_id"] == self.org_id

    def test_get_branch(self):
        resp = client.post("/api/v1/branches", json={
            "organization_id": self.org_id,
            "name": "Branch A", "code": "MBH-A",
        })
        branch_id = resp.json()["id"]
        resp2 = client.get(f"/api/v1/branches/{branch_id}")
        assert resp2.status_code == 200
        assert resp2.json()["organization_id"] == self.org_id

    def test_update_branch(self):
        resp = client.post("/api/v1/branches", json={
            "organization_id": self.org_id,
            "name": "Old Branch", "code": "MBH-OLD",
        })
        branch_id = resp.json()["id"]
        resp2 = client.patch(f"/api/v1/branches/{branch_id}", json={
            "name": "Updated Branch",
        })
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Updated Branch"

    def test_get_missing_branch_404(self):
        resp = client.get("/api/v1/branches/nonexistent")
        assert resp.status_code == 404