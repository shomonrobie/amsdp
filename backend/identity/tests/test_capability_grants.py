"""Staff capability grants — the administrative surface (owner decision Q4).

Q4 asks for a capability an administrator grants deliberately and revokes
independently of the role: "central reception may book across branches, for now".
The role matrix cannot express that, so it is a named, branch-scopable,
individually revocable grant (``staff_capability_grants``).

What this module pins:

* only an **organization administrator** (or the platform administrator) may
  grant or revoke — a branch administrator is refused, because the capability
  exists to cross exactly the boundary they administer;
* only :data:`common.permissions.DELEGABLE_CAPABILITIES` may be granted, so the
  surface can never hand out ``appointment.modify`` or ``org.manage``;
* a grant is idempotent (same row, still one authority) and a revocation is a
  **state change, never a delete** — the trail keeps who held what, and when;
* every grant and revocation is audited;
* a foreign tenant's user is a non-disclosing ``404``.

The behaviour the grant actually unlocks (booking into another branch, and the
fact that it does *not* unlock reads) is covered in
``appointment/tests/test_cross_branch_capability.py``.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org)
from common.models import AuditEvent, StaffCapabilityGrant, StaffUser

ORG = "grant-org"
OTHER_ORG = "grant-other-org"
BR = "grant-br"
BR2 = "grant-br2"
OTHER_BR = "grant-other-br"
SUPER = "grant_super"
ADMIN = "grant_admin"
OTHER_ADMIN = "grant_other_admin"
BRANCH_ADMIN = "grant_bradm"
RECP = "grant_recp"
FOREIGN_RECP = "grant_foreign_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("identity"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(SUPER, "super_admin", ORG, BR)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "org_admin", OTHER_ORG, OTHER_BR)
    ensure_user(BRANCH_ADMIN, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(FOREIGN_RECP, "receptionist", OTHER_ORG, OTHER_BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _user_id(username):
    with db_session() as s:
        return s.query(StaffUser).filter(
            StaffUser.username == username).one().id


def _grant(client, username, capability, *, actor=ADMIN, branch_id=None,
           reason="central reception"):
    body = {"capability": capability, "reason": reason}
    if branch_id:
        body["branch_id"] = branch_id
    return client.post(f"/api/v1/staff/users/{_user_id(username)}/capabilities",
                       headers=headers(actor), json=body)


def _rows(username):
    with db_session() as s:
        user_id = _user_id(username)
        return s.query(StaffCapabilityGrant).filter(
            StaffCapabilityGrant.staff_user_id == user_id).all()


def _audit_actions(target_id):
    with db_session() as s:
        return [row.action for row in s.query(AuditEvent).filter(
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp).all()]


class TestGranting:
    def test_an_org_admin_grants_a_delegable_capability(self, client):
        response = _grant(client, RECP, "appointment.book_cross_branch")
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["capability"] == "appointment.book_cross_branch"
        assert body["branch_id"] == ""
        assert body["status"] == "active"
        assert body["granted_by"] == _user_id(ADMIN)
        assert body["reason"] == "central reception"
        assert "staff.capability_granted" in _audit_actions(_user_id(RECP))
        rows = _rows(RECP)
        assert len(rows) == 1 and rows[0].status == "active"

    def test_a_grant_can_be_scoped_to_one_branch(self, client):
        response = _grant(client, RECP, "appointment.create_unscheduled",
                          branch_id=BR2)
        assert response.status_code == 201, response.text
        assert response.json()["branch_id"] == BR2

    def test_regranting_the_same_capability_is_idempotent(self, client):
        """Re-granting re-activates one row; it never stacks two authorities."""
        first = _grant(client, RECP, "appointment.check_in")
        assert first.status_code == 201, first.text
        second = _grant(client, RECP, "appointment.check_in")
        assert second.status_code == 201, second.text
        assert second.json()["id"] == first.json()["id"]
        assert len(_rows(RECP)) == 1

    def test_list_returns_the_active_grants(self, client):
        _grant(client, RECP, "appointment.check_in")
        _grant(client, RECP, "appointment.book_cross_branch")
        listing = client.get(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities",
            headers=headers(BRANCH_ADMIN))
        assert listing.status_code == 200, listing.text
        assert {row["capability"] for row in listing.json()} == {
            "appointment.check_in", "appointment.book_cross_branch"}

    def test_the_super_admin_may_grant_in_another_organization(self, client):
        response = _grant(client, FOREIGN_RECP, "appointment.check_in",
                          actor=SUPER)
        assert response.status_code == 201, response.text
        rows = _rows(FOREIGN_RECP)
        assert len(rows) == 1 and rows[0].organization_id == OTHER_ORG


class TestRefusals:
    def test_a_non_delegable_capability_is_refused(self, client):
        response = _grant(client, RECP, "appointment.modify")
        assert response.status_code == 422, response.text
        assert "capability must be one of" in response.json()["detail"]
        assert _rows(RECP) == []

    def test_an_unknown_capability_is_refused(self, client):
        response = _grant(client, RECP, "appointment.god_mode")
        assert response.status_code == 422, response.text
        assert _rows(RECP) == []

    def test_a_branch_admin_cannot_grant(self, client):
        response = _grant(client, RECP, "appointment.book_cross_branch",
                          actor=BRANCH_ADMIN)
        assert response.status_code == 403, response.text
        assert _rows(RECP) == []

    def test_a_receptionist_cannot_grant_anything(self, client):
        response = _grant(client, RECP, "appointment.book_cross_branch",
                          actor=RECP)
        assert response.status_code == 403, response.text
        assert _rows(RECP) == []

    def test_another_organizations_admin_gets_a_404(self, client):
        response = _grant(client, RECP, "appointment.check_in",
                          actor=OTHER_ADMIN)
        assert response.status_code == 404, response.text
        assert _rows(RECP) == []

    def test_a_foreign_users_grants_are_not_listable(self, client):
        _grant(client, FOREIGN_RECP, "appointment.check_in", actor=SUPER)
        listing = client.get(
            f"/api/v1/staff/users/{_user_id(FOREIGN_RECP)}/capabilities",
            headers=headers(ADMIN))
        assert listing.status_code == 404, listing.text


class TestRevocation:
    def test_revocation_is_a_state_change_that_is_audited(self, client):
        granted = _grant(client, RECP, "appointment.book_cross_branch")
        assert granted.status_code == 201, granted.text
        revoked = client.delete(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/"
            "appointment.book_cross_branch", headers=headers(ADMIN))
        assert revoked.status_code == 200, revoked.text
        assert revoked.json() == {"revoked": 1,
                                  "capability": "appointment.book_cross_branch"}
        rows = _rows(RECP)
        assert len(rows) == 1, "the row must be kept as a revoked record"
        assert rows[0].status == "revoked"
        assert rows[0].revoked_by == _user_id(ADMIN)
        assert rows[0].revoked_at is not None
        assert "staff.capability_revoked" in _audit_actions(_user_id(RECP))

    def test_a_revoked_grant_is_hidden_unless_asked_for(self, client):
        _grant(client, RECP, "appointment.check_in")
        client.delete(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/"
            "appointment.check_in", headers=headers(ADMIN))
        active = client.get(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities",
            headers=headers(ADMIN))
        assert active.json() == []
        full = client.get(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities",
            params={"include_revoked": "true"}, headers=headers(ADMIN))
        assert [row["status"] for row in full.json()] == ["revoked"]

    def test_revoking_an_unknown_grant_is_404(self, client):
        response = client.delete(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/"
            "appointment.check_in", headers=headers(ADMIN))
        assert response.status_code == 404, response.text

    def test_a_branch_admin_cannot_revoke(self, client):
        _grant(client, RECP, "appointment.check_in")
        response = client.delete(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/"
            "appointment.check_in", headers=headers(BRANCH_ADMIN))
        assert response.status_code == 403, response.text
        assert _rows(RECP)[0].status == "active"

    def test_a_revoked_grant_can_be_granted_again(self, client):
        """The row is re-activated with a fresh grant, and stays one row."""
        first = _grant(client, RECP, "appointment.check_in")
        client.delete(
            f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/"
            "appointment.check_in", headers=headers(ADMIN))
        again = _grant(client, RECP, "appointment.check_in")
        assert again.status_code == 201, again.text
        assert again.json()["id"] == first.json()["id"]
        assert again.json()["status"] == "active"
        assert again.json()["revoked_at"] == ""
        assert len(_rows(RECP)) == 1
