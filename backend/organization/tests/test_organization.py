"""Tests for the Organization Service — BR §4–§6.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined module
imported ``organization.main._orgs_db`` / ``_branches_db`` (in-memory dicts that
no longer exist) and called the API without credentials — every route now
requires a permission, so those calls return 401 rather than exercising the
handlers.

Rewritten against PostgreSQL with real signed tokens.  Two behaviours changed on
purpose since the quarantined module was written, and the assertions state the
current rule:

* A foreign organization/branch is a **non-disclosing 404**, never 403
  (``common.auth.require_org_access``, ``.clinerules`` §3).
* The tenant of a *new* organization still comes from the request body
  (``org.create`` is the one bootstrap route that cannot inherit a tenant), but
  every subsequent route is scoped by the caller's token.

Organizations and branches are reference rows for the append-only audit trail,
so this module never deletes them; it creates them with unique codes instead.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org, uniq)
from common.models import Branch, Organization

ORG = "legacy-org-org"
BR = "legacy-org-br"
OTHER_ORG = "legacy-org-other"
OTHER_BR = "legacy-org-other-br"
ADMIN = "legacy_org_admin"
OTHER_ADMIN = "legacy_org_other_admin"
RECP = "legacy_org_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("organization"))


@pytest.fixture(autouse=True)
def _world(client):
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "org_admin", OTHER_ORG, OTHER_BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    purge_org(ORG)
    purge_org(OTHER_ORG)
    yield
    # Teardown: no business rows left behind; reference rows stay (audit).
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _new_org(client, name="Uposhak Clinic"):
    return client.post("/api/v1/orgs", headers=headers(ADMIN), json={
        "name": name, "code": uniq("UPC").upper(),
        "facility_type": "clinic", "address": "Dhaka"})


class TestOrgLifecycle:
    def test_create_org(self, client):
        r = _new_org(client)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Uposhak Clinic"
        assert body["status"] == "active"
        assert body["facility_type"] == "clinic"
        with db_session() as s:
            assert s.query(Organization).filter(
                Organization.id == body["id"]).first() is not None

    def test_create_org_requires_permission(self, client):
        r = client.post("/api/v1/orgs", headers=headers(RECP),
                        json={"name": "Nope", "code": uniq("NO").upper()})
        assert r.status_code == 403

    def test_get_own_org(self, client):
        r = client.get(f"/api/v1/orgs/{ORG}", headers=headers(ADMIN))
        assert r.status_code == 200
        assert r.json()["id"] == ORG

    def test_get_missing_org_404(self, client):
        r = client.get("/api/v1/orgs/nonexistent", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_foreign_org_is_a_404(self, client):
        """Cross-tenant ids are non-disclosing: 404, never 403."""
        r = client.get(f"/api/v1/orgs/{OTHER_ORG}", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_list_orgs_is_scoped_to_the_callers_org(self, client):
        _new_org(client)
        r = client.get("/api/v1/orgs", headers=headers(ADMIN))
        assert r.status_code == 200
        assert [o["id"] for o in r.json()] == [ORG]

    def test_update_org(self, client):
        r = client.patch(f"/api/v1/orgs/{ORG}", headers=headers(ADMIN),
                         json={"name": "Legacy Org Renamed",
                               "address": "New Address"})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Legacy Org Renamed"
        assert r.json()["address"] == "New Address"
        with db_session() as s:
            assert s.query(Organization).filter(
                Organization.id == ORG).first().name == "Legacy Org Renamed"

    def test_update_foreign_org_is_a_404(self, client):
        r = client.patch(f"/api/v1/orgs/{OTHER_ORG}", headers=headers(ADMIN),
                         json={"name": "Hijacked"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Organization).filter(
                Organization.id == OTHER_ORG).first().name != "Hijacked"


class TestBranchLifecycle:
    def _create_branch(self, client, org_id=ORG, name="Main Branch"):
        return client.post("/api/v1/branches", headers=headers(ADMIN), json={
            "organization_id": org_id, "name": name,
            "code": uniq("BR").upper()})

    def test_create_branch(self, client):
        r = self._create_branch(client, name="Main Branch")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Main Branch"
        assert body["organization_id"] == ORG
        with db_session() as s:
            assert s.query(Branch).filter(Branch.id == body["id"]).first()

    def test_create_branch_in_another_org_is_a_404(self, client):
        r = self._create_branch(client, org_id="bad-org", name="Ghost Branch")
        assert r.status_code == 404
        r = self._create_branch(client, org_id=OTHER_ORG, name="Ghost Branch")
        assert r.status_code == 404

    def test_list_branches_is_scoped_to_the_org(self, client):
        created = self._create_branch(client, name="Scoped Branch").json()["id"]
        r = client.get(f"/api/v1/orgs/{ORG}/branches", headers=headers(ADMIN))
        assert r.status_code == 200
        branches = r.json()
        assert created in [b["id"] for b in branches]
        assert {b["organization_id"] for b in branches} == {ORG}

    def test_list_foreign_org_branches_is_a_404(self, client):
        r = client.get(f"/api/v1/orgs/{OTHER_ORG}/branches",
                       headers=headers(ADMIN))
        assert r.status_code == 404

    def test_get_branch(self, client):
        branch_id = self._create_branch(client, name="Branch A").json()["id"]
        r = client.get(f"/api/v1/branches/{branch_id}", headers=headers(ADMIN))
        assert r.status_code == 200
        assert r.json()["organization_id"] == ORG

    def test_get_missing_branch_404(self, client):
        r = client.get("/api/v1/branches/nonexistent", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_get_foreign_branch_is_a_404(self, client):
        r = client.get(f"/api/v1/branches/{OTHER_BR}", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_update_branch(self, client):
        branch_id = self._create_branch(client, name="Old Branch").json()["id"]
        r = client.patch(f"/api/v1/branches/{branch_id}",
                         headers=headers(ADMIN),
                         json={"name": "Updated Branch"})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Updated Branch"
        with db_session() as s:
            assert s.query(Branch).filter(
                Branch.id == branch_id).first().name == "Updated Branch"

    def test_update_foreign_branch_is_a_404(self, client):
        r = client.patch(f"/api/v1/branches/{OTHER_BR}",
                         headers=headers(ADMIN), json={"name": "Hijacked"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Branch).filter(
                Branch.id == OTHER_BR).first().name != "Hijacked"


class TestBranchContext:
    """``/api/v1/me/branches`` — the branches a token may switch to."""

    def test_org_admin_sees_every_branch_in_the_org(self, client):
        r = client.get("/api/v1/me/branches", headers=headers(ADMIN))
        assert r.status_code == 200
        ids = [b["id"] for b in r.json()]
        assert BR in ids
        assert {b["organization_id"] for b in r.json()} == {ORG}

    def test_branch_scoped_user_sees_only_their_branch(self, client):
        r = client.get("/api/v1/me/branches", headers=headers(RECP))
        assert r.status_code == 200
        assert [b["id"] for b in r.json()] == [BR]

    def test_requires_authentication(self, client):
        assert client.get("/api/v1/me/branches").status_code == 401
