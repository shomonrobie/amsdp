"""Platform administration boundary (owner decision Q-1).

The platform administrator used to be ``super_admin: ["*"]`` — an unrestricted
wildcard — plus a role-string bypass inside ``common.auth``.  These tests pin the
replacement contract:

* no role holds a bare wildcard, and an unknown permission is denied even for the
  platform administrator;
* the platform capabilities (``platform.admin`` / ``platform.cross_org``) are
  reserved to that role and to no tenant-level role;
* a capability the platform administrator is expected to keep still works, so
  the enumerated list is not quietly narrower than the job;
* crossing an organization boundary without ``platform.cross_org`` is a
  non-disclosing 404 for every tenant role;
* crossing it **with** the capability succeeds and leaves an audit row in the
  target organization's trail (Q-1 §6: audit platform administrator access).

Everything except the matrix assertions runs against the real service apps and
the real PostgreSQL trail.
"""

import os
import sys

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from amsdp_test_support import (db_session, ensure_branch, ensure_org,  # noqa: E402
                                ensure_user, headers, load_app)
from common.auth import AuthContext, require_branch_access, require_org_access  # noqa: E402
from common.models import AuditEvent                                  # noqa: E402
from common.permissions import (PLATFORM_CAPABILITIES, PERMISSIONS,   # noqa: E402
                                check)

ACCESS_ACTION = "platform.cross_org.access"

ORG = "q1-platform-org"
OTHER = "q1-platform-other-org"
BRANCH = "q1-platform-branch"
FOREIGN_BRANCH = "q1-platform-foreign-branch"

#: key -> (username, role, organization, branch)
USERS = {
    "admin": ("q1_platform_admin", "super_admin", ORG, None),
    "orgadm": ("q1_platform_orgadm", "org_admin", ORG, None),
    "bradm": ("q1_platform_bradm", "branch_admin", ORG, BRANCH),
    "rec": ("q1_platform_rec", "receptionist", ORG, BRANCH),
    "ast": ("q1_platform_ast", "assistant", ORG, BRANCH),
}

audit_client = TestClient(load_app("audit"))
identity_client = TestClient(load_app("identity"))


@pytest.fixture(scope="module", autouse=True)
def seeded():
    """Create this module's reference rows once (never deleted)."""
    ensure_org(ORG)
    ensure_org(OTHER)
    ensure_branch(BRANCH, ORG)
    ids = {}
    for username, role, org, branch in USERS.values():
        ids[username] = ensure_user(username, role, org, branch)
    ids["foreign"] = ensure_user("q1_platform_foreign", "receptionist", OTHER, None)
    return ids


def _ctx(role: str, org: str = ORG, branch: str | None = None) -> AuthContext:
    """A synthetic authenticated context for dependency-level tests."""
    return AuthContext(user_id=f"ctx-{role}", organization_id=org,
                       branch_id=branch, role=role, username=f"ctx_{role}",
                       locale="en", status="active", token_payload={})


def _access_rows(target_id: str | None = None, actor_id: str | None = None) -> list:
    with db_session() as s:
        q = s.query(AuditEvent).filter(AuditEvent.action == ACCESS_ACTION)
        if target_id is not None:
            q = q.filter(AuditEvent.target_id == target_id)
        if actor_id is not None:
            q = q.filter(AuditEvent.actor_id == actor_id)
        return [(e.organization_id, e.actor_id, e.actor_role, e.target_id,
                 e.target_type, e.after, e.service) for e in q.all()]


def _action_rows(action: str, target_id: str) -> list:
    with db_session() as s:
        return [(e.organization_id, e.actor_id, e.actor_role, e.after)
                for e in s.query(AuditEvent).filter(
                    AuditEvent.action == action,
                    AuditEvent.target_id == target_id).all()]


# ---------------------------------------------------------------------------
# The matrix (Q-1): no wildcard, unknown denied, platform capabilities reserved
# ---------------------------------------------------------------------------

def test_no_role_holds_a_bare_wildcard():
    for role, perms in PERMISSIONS.items():
        assert "*" not in perms, f"{role} still holds an unrestricted wildcard"


def test_super_admin_capabilities_are_enumerated():
    perms = PERMISSIONS["super_admin"]
    assert set(PLATFORM_CAPABILITIES) <= set(perms)
    assert len(perms) >= 10, "the platform grant must be a reviewable list"


def test_unknown_permission_is_denied_for_every_role():
    for role in PERMISSIONS:
        assert check("anything.at.all", role) is False, role


def test_platform_capabilities_are_reserved_to_the_platform_administrator():
    for role, perms in PERMISSIONS.items():
        if role == "super_admin":
            continue
        for cap in PLATFORM_CAPABILITIES:
            assert check(cap, role) is False, f"{role} must not hold {cap}"


def test_super_admin_keeps_the_documented_operational_capabilities():
    for cap in ("org.manage", "branch.manage", "staff.manage", "patient.read",
                "patient.create", "appointment.modify", "queue.manage",
                "queue.recover", "audit.read"):
        assert check(cap, "super_admin") is True, cap


def test_is_super_admin_is_derived_from_the_matrix():
    assert _ctx("super_admin").is_super_admin is True
    assert _ctx("super_admin").can_cross_org is True
    for role in ("org_admin", "branch_admin", "receptionist", "doctor",
                 "assistant"):
        assert _ctx(role).is_super_admin is False, role
        assert _ctx(role).can_cross_org is False, role
    assert _ctx("root").is_super_admin is False       # a role nobody defined


# ---------------------------------------------------------------------------
# Tenant gate, dependency level
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["org_admin", "branch_admin", "receptionist",
                                  "doctor", "assistant"])
def test_org_access_denies_every_tenant_role_with_404(role):
    with pytest.raises(HTTPException) as exc:
        require_org_access(OTHER)(auth=_ctx(role))
    assert exc.value.status_code == 404


def test_org_access_allows_own_organization():
    ctx = _ctx("receptionist")
    assert require_org_access(ORG)(auth=ctx) is ctx


def test_org_access_allows_platform_admin_and_audits_it(seeded):
    ctx = _ctx("super_admin")
    assert require_org_access(OTHER, service="unit")(auth=ctx) is ctx
    rows = _access_rows(target_id=OTHER, actor_id=ctx.user_id)
    assert rows, "cross-organization access must be recorded"
    org_id, actor_id, actor_role, _target, target_type, after, service = rows[-1]
    assert (org_id, actor_id, actor_role) == (OTHER, ctx.user_id, "super_admin")
    assert (target_type, service) == ("organization", "unit")
    assert after["actor_organization_id"] == ORG
    assert after["capability"] == "platform.cross_org"


def test_branch_access_denies_a_foreign_branch_with_404():
    with pytest.raises(HTTPException) as exc:
        require_branch_access(FOREIGN_BRANCH)(
            auth=_ctx("receptionist", branch=BRANCH))
    assert exc.value.status_code == 404


def test_branch_access_requires_a_branch_scope_for_branch_users():
    with pytest.raises(HTTPException) as exc:
        require_branch_access(None)(auth=_ctx("receptionist", branch=BRANCH))
    assert exc.value.status_code == 403


def test_branch_access_allows_org_admin_and_platform_admin(seeded):
    ensure_branch(FOREIGN_BRANCH, OTHER)
    ctx = _ctx("org_admin")
    assert require_branch_access(FOREIGN_BRANCH)(auth=ctx) is ctx
    platform = _ctx("super_admin")
    assert require_branch_access(FOREIGN_BRANCH, service="unit")(
        auth=platform) is platform
    rows = _access_rows(target_id=FOREIGN_BRANCH, actor_id=platform.user_id)
    assert rows and rows[-1][0] == OTHER
    assert rows[-1][4] == "branch"


# ---------------------------------------------------------------------------
# HTTP level: cross-organization reads and sensitive actions
# ---------------------------------------------------------------------------

def test_platform_admin_cross_org_audit_read_succeeds_and_is_audited(seeded):
    r = audit_client.get(f"/api/v1/audit/organization/{OTHER}",
                         headers=headers(USERS["admin"][0]))
    assert r.status_code == 200, r.text
    assert {e["organization_id"] for e in r.json()} == {OTHER}
    rows = _access_rows(target_id=OTHER, actor_id=seeded[USERS["admin"][0]])
    assert rows, "the read must leave a platform access row in the target trail"
    org_id, _actor, actor_role, _target, target_type, after, service = rows[-1]
    assert (org_id, actor_role, target_type, service) == (
        OTHER, "super_admin", "organization", "audit")
    assert after["actor_organization_id"] == ORG


def test_org_admin_cross_org_read_is_404_and_creates_no_platform_access(seeded):
    r = audit_client.get(f"/api/v1/audit/organization/{OTHER}",
                         headers=headers(USERS["orgadm"][0]))
    assert r.status_code == 404, r.text
    assert not _access_rows(actor_id=seeded[USERS["orgadm"][0]])


def test_platform_admin_cross_org_staff_update_is_audited(seeded):
    r = identity_client.patch(
        f"/api/v1/staff/users/{seeded['foreign']}",
        headers=headers(USERS["admin"][0]),
        json={"display_name": "Support Renamed"})
    assert r.status_code == 200, r.text
    rows = _action_rows("staff.updated", seeded["foreign"])
    assert rows, "a platform administrator's sensitive action must be audited"
    org_id, actor_id, actor_role, after = rows[-1]
    assert (org_id, actor_id, actor_role) == (
        OTHER, seeded[USERS["admin"][0]], "super_admin")
    assert after["display_name"] == "Support Renamed"


def test_org_admin_cannot_update_foreign_staff(seeded):
    r = identity_client.patch(
        f"/api/v1/staff/users/{seeded['foreign']}",
        headers=headers(USERS["orgadm"][0]),
        json={"display_name": "Hijacked"})
    assert r.status_code == 404, r.text


