"""The staff administration surface — branch scope and the capability catalogue.

MP-19 turns the thin staff page into a management screen: edit, deactivate,
change role, change branch scope, grant delegable capabilities.  The role rules
and the last-active-administrator guard are pinned in ``test_identity.py``, and
the grant rules in ``test_capability_grants.py``.  This module pins the two
things the screen needed and did not have:

* **branch scope is editable.**  Before MP-19 the scope could only be set when
  the account was created, so moving a receptionist to another branch meant
  creating a second account and leaving the first one behind;
* **the delegable catalogue is readable.**  The browser asks the server what may
  be granted instead of carrying its own copy of
  :data:`common.permissions.DELEGABLE_CAPABILITIES`, which would drift until the
  UI offered a capability the API refuses.

Every write keeps both sides in the trail, an out-of-scope or foreign branch is
the same non-disclosing ``404`` an unknown id gets, and staff management stays
organization authority: a branch administrator may read the roster, and every
write is refused with ``403``.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org)
from common.models import AuditEvent, StaffUser
from common.permissions import DELEGABLE_CAPABILITIES

ORG = "mp19-org"
OTHER_ORG = "mp19-other-org"
BR = "mp19-br"
BR2 = "mp19-br2"
OTHER_BR = "mp19-other-br"
ADMIN = "mp19_admin"
BRANCH_ADMIN = "mp19_bradm"
RECP = "mp19_recp"
OTHER_RECP = "mp19_other_recp"


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
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(BRANCH_ADMIN, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(OTHER_RECP, "receptionist", OTHER_ORG, OTHER_BR)
    # The module mutates this row, and reference rows are reused across runs, so
    # the baseline is restored rather than assumed.
    with db_session() as s:
        row = s.query(StaffUser).filter(StaffUser.username == RECP).one()
        row.display_name, row.role, row.status = "Mp19 Recp", "receptionist", "active"
        row.branch_id = BR
        s.commit()
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _user_id(username):
    with db_session() as s:
        return s.query(StaffUser).filter(
            StaffUser.username == username).one().id


def _branch_of(username):
    with db_session() as s:
        return s.query(StaffUser).filter(
            StaffUser.username == username).one().branch_id


def _events(action, target_id, skip=0):
    """Audit rows for one action and target, oldest first.

    The trail is append-only and shared across a module run, so a test asserts on
    the rows it appended (``skip`` = how many already existed) rather than on the
    whole history — the same distinction an auditor reading the trail makes.
    """
    with db_session() as s:
        rows = s.query(AuditEvent).filter(
            AuditEvent.action == action,
            AuditEvent.target_id == target_id).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()
    return rows[skip:]


def _event_count(action, target_id):
    with db_session() as s:
        return s.query(AuditEvent).filter(
            AuditEvent.action == action,
            AuditEvent.target_id == target_id).count()


def _patch(client, username, body, actor=ADMIN):
    return client.patch(f"/api/v1/staff/users/{_user_id(username)}",
                        headers=headers(actor), json=body)


class TestCapabilityCatalogue:
    def test_the_catalogue_is_the_delegable_set(self, client):
        response = client.get("/api/v1/staff/capabilities", headers=headers(ADMIN))
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["capabilities"] == sorted(DELEGABLE_CAPABILITIES)
        assert "appointment.modify" not in body["capabilities"]
        assert "org.manage" not in body["capabilities"]

    def test_a_branch_admin_may_read_the_catalogue(self, client):
        """``staff.read`` is enough to see the list; granting needs more."""
        response = client.get("/api/v1/staff/capabilities",
                              headers=headers(BRANCH_ADMIN))
        assert response.status_code == 200, response.text

    def test_a_receptionist_may_not_read_the_catalogue(self, client):
        response = client.get("/api/v1/staff/capabilities", headers=headers(RECP))
        assert response.status_code == 403, response.text

    def test_an_unauthenticated_read_is_401(self, client):
        assert client.get("/api/v1/staff/capabilities").status_code == 401


class TestBranchScope:
    def test_an_org_admin_moves_a_user_to_another_branch(self, client):
        response = _patch(client, RECP, {"branch_id": BR2})
        assert response.status_code == 200, response.text
        assert response.json()["branch_id"] == BR2
        assert _branch_of(RECP) == BR2

    def test_a_scope_change_is_audited_with_both_sides(self, client):
        seen = _event_count("staff.branch_scope_changed", _user_id(RECP))
        _patch(client, RECP, {"branch_id": BR2})
        events = _events("staff.branch_scope_changed", _user_id(RECP), skip=seen)
        assert len(events) == 1, "one change, one event"
        assert events[0].before == {"branch_id": BR}
        assert events[0].after == {"branch_id": BR2}
        assert events[0].actor_role == "org_admin"
        assert events[0].organization_id == ORG

    def test_the_generic_update_event_carries_the_previous_record(self, client):
        seen = _event_count("staff.updated", _user_id(RECP))
        _patch(client, RECP, {"branch_id": BR2, "display_name": "Moved Clerk"})
        events = _events("staff.updated", _user_id(RECP), skip=seen)
        assert len(events) == 1
        assert events[0].before["branch_id"] == BR
        assert events[0].before["display_name"] == "Mp19 Recp"
        assert events[0].after["branch_id"] == BR2
        assert events[0].after["display_name"] == "Moved Clerk"

    def test_clearing_the_scope_makes_the_user_organization_wide(self, client):
        seen = _event_count("staff.branch_scope_changed", _user_id(RECP))
        response = _patch(client, RECP, {"branch_id": ""})
        assert response.status_code == 200, response.text
        assert response.json()["branch_id"] in (None, "")
        assert _branch_of(RECP) is None
        events = _events("staff.branch_scope_changed", _user_id(RECP), skip=seen)
        assert events[0].after == {"branch_id": ""}

    def test_an_unchanged_scope_writes_no_scope_event(self, client):
        seen = _event_count("staff.branch_scope_changed", _user_id(RECP))
        _patch(client, RECP, {"display_name": "Same Branch"})
        assert _events("staff.branch_scope_changed", _user_id(RECP), skip=seen) == []
        assert _branch_of(RECP) == BR

    def test_a_foreign_branch_is_a_non_disclosing_404(self, client):
        response = _patch(client, RECP, {"branch_id": OTHER_BR})
        assert response.status_code == 404, response.text
        assert response.json()["detail"] == "branch not found"
        assert _branch_of(RECP) == BR, "a refused change must not be half-applied"

    def test_an_unknown_branch_is_the_same_404(self, client):
        response = _patch(client, RECP, {"branch_id": "no-such-branch"})
        assert response.status_code == 404, response.text
        assert response.json()["detail"] == "branch not found"

    def test_a_branch_admin_cannot_manage_staff_at_all(self, client):
        """``staff.manage`` is organization authority; ``staff.read`` is not.

        A branch administrator may read the roster and the capability catalogue,
        but every write — name, role, status, scope — is refused by the server
        before tenancy is even considered.  The screen therefore never shows the
        management controls to a branch administrator as a substitute for this
        check: hiding a button is not an authorization boundary.
        """
        for body in ({"display_name": "Not Allowed"}, {"branch_id": BR2}):
            response = _patch(client, RECP, body, actor=BRANCH_ADMIN)
            assert response.status_code == 403, response.text
        assert _branch_of(RECP) == BR

    def test_a_foreign_users_scope_cannot_be_changed(self, client):
        response = _patch(client, OTHER_RECP, {"branch_id": OTHER_BR})
        assert response.status_code == 404, response.text
        assert response.json()["detail"] == "user not found"


class TestRoleChangeTrail:
    def test_a_role_change_records_the_previous_role(self, client):
        seen = _event_count("staff.updated", _user_id(RECP))
        response = _patch(client, RECP, {"role": "assistant"})
        assert response.status_code == 200, response.text
        events = _events("staff.updated", _user_id(RECP), skip=seen)
        assert len(events) == 1
        assert events[0].before["role"] == "receptionist"
        assert events[0].after["role"] == "assistant"

    def test_deactivation_records_the_previous_status(self, client):
        seen = _event_count("staff.updated", _user_id(RECP))
        response = _patch(client, RECP, {"status": "inactive"})
        assert response.status_code == 200, response.text
        events = _events("staff.updated", _user_id(RECP), skip=seen)
        assert events[0].before["status"] == "active"
        assert events[0].after["status"] == "inactive"
