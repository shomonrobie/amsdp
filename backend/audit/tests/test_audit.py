"""Audit service tests — authenticated, tenant-scoped, append-only (Sequence 4).

Replaces the M1 suite, which exercised the in-memory stub (an unauthenticated
write endpoint plus cross-tenant reads). Every assertion here is about a
security property the audit trail must hold.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from audit.main import app
from common.audit import record_audit
from common.database import SessionFactory
from common.models import AuditEvent, Branch, Organization, StaffUser
from identity.models import _ALGO, _SECRET

client = TestClient(app)

ORG_A = "sq4-audit-org"
ORG_B = "sq4-audit-org-b"
BR_A1 = "sq4-audit-br-a1"
BR_A2 = "sq4-audit-br-a2"
TARGET_A = "sq4-audit-target-a"
TARGET_B = "sq4-audit-target-b"
PASSWORD = "testpass123"

#: key -> (username, role, organization, branch)
USERS = {
    "super": ("sq4_audit_super", "super_admin", ORG_A, None),
    "orgadm": ("sq4_audit_orgadm", "org_admin", ORG_A, None),
    "bradm": ("sq4_audit_bradm", "branch_admin", ORG_A, BR_A1),
    "ast": ("sq4_audit_ast", "assistant", ORG_A, BR_A1),
    "orgadm_b": ("sq4_audit_orgadm_b", "org_admin", ORG_B, None),
}


def _seed():
    """Recreate this suite's reference rows and its own audit events.

    Only rows this suite owns are removed (its two target ids); organizations,
    staff users and every other organization's audit trail are left untouched.
    """
    s = SessionFactory()
    try:
        s.query(AuditEvent).filter(
            AuditEvent.target_id.in_([TARGET_A, TARGET_B])).delete(
            synchronize_session=False)
        s.commit()
        if not s.query(Organization).filter(Organization.id == ORG_A).first():
            s.add(Organization(id=ORG_A, name="Audit Org A", code="SQ4-AUDIT-A"))
        if not s.query(Organization).filter(Organization.id == ORG_B).first():
            s.add(Organization(id=ORG_B, name="Audit Org B", code="SQ4-AUDIT-B"))
        s.commit()
        for bid, oid, code in ((BR_A1, ORG_A, "SQ4-A1"), (BR_A2, ORG_A, "SQ4-A2")):
            if not s.query(Branch).filter(Branch.id == bid).first():
                s.add(Branch(id=bid, organization_id=oid, name=bid, code=code))
        s.commit()
        pw = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
        for username, role, org, branch in USERS.values():
            user = s.query(StaffUser).filter(
                StaffUser.username == username).first()
            if user is None:
                s.add(StaffUser(id=str(uuid.uuid4()), organization_id=org,
                                username=username, password_hash=pw,
                                display_name=username.title(), role=role,
                                status="active", branch_id=branch))
            else:
                user.organization_id, user.branch_id, user.role = org, branch, role
                user.status = "active"
        s.commit()
        actor = s.query(StaffUser).filter(
            StaffUser.username == USERS["orgadm"][0]).first()
        record_audit(s, service="queuing", org_id=ORG_A, branch_id=BR_A1,
                     action="queue.recover", target_type="queue_entry",
                     target_id=TARGET_A, actor_id=actor.id, actor_role="org_admin",
                     before={"position": 4}, after={"position": 9},
                     reason="missed turn")
        record_audit(s, service="queuing", org_id=ORG_A, branch_id=BR_A2,
                     action="queue.reorder", target_type="queue_entry",
                     target_id=TARGET_A, actor_id=actor.id, actor_role="org_admin",
                     before={"position": 1}, after={"position": 2},
                     reason="other branch")
        record_audit(s, service="queuing", org_id=ORG_B, branch_id=None,
                     action="queue.recover", target_type="queue_entry",
                     target_id=TARGET_B, actor_id=actor.id, actor_role="org_admin",
                     before={"position": 1}, after={"position": 5},
                     reason="foreign tenant")
        s.commit()
    finally:
        s.close()


@pytest.fixture(autouse=True)
def _fresh():
    _seed()
    yield


def _headers(key: str) -> dict:
    s = SessionFactory()
    try:
        user = s.query(StaffUser).filter(
            StaffUser.username == USERS[key][0]).first()
        payload = {"sub": user.id, "org": user.organization_id,
                   "branch": user.branch_id, "role": user.role}
    finally:
        s.close()
    payload["exp"] = int((datetime.now(timezone.utc)
                          + timedelta(hours=1)).timestamp())
    return {"Authorization": f"Bearer {jwt.encode(payload, _SECRET, algorithm=_ALGO)}"}


# 1. The write path is gone — an HTTP caller can never forge an audit row.
def test_no_write_endpoint():
    r = client.post("/api/v1/audit", json={"service": "x", "organization_id": ORG_A,
                                          "action": "faked", "target_type": "t",
                                          "target_id": TARGET_A, "actor_id": "a",
                                          "actor_role": "super_admin"})
    assert r.status_code in (404, 405), r.status_code


def test_route_table_exposes_read_methods_only():
    methods = set()
    for route in app.routes:
        methods |= {m.upper() for m in getattr(route, "methods", set())}
    assert methods <= {"GET", "HEAD", "OPTIONS"}, methods


# 2. Anonymous access.
def test_anonymous_target_read_rejected():
    assert client.get(f"/api/v1/audit/{TARGET_A}").status_code == 401


def test_anonymous_org_read_rejected():
    assert client.get(f"/api/v1/audit/organization/{ORG_A}").status_code == 401


# 3. Tenant isolation.
def test_org_admin_reads_own_org_target():
    r = client.get(f"/api/v1/audit/{TARGET_A}", headers=_headers("orgadm"))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert all(e["organization_id"] == ORG_A for e in rows)
    assert rows[0]["timestamp"] >= rows[-1]["timestamp"]  # newest first
    assert {"event_id", "action", "target_id", "actor_id", "before", "after",
            "reason", "timestamp"} <= set(rows[0])


def test_unknown_target_is_empty_not_403():
    r = client.get("/api/v1/audit/sq4-audit-does-not-exist",
                   headers=_headers("orgadm"))
    assert r.status_code == 200 and r.json() == []


def test_cross_org_target_is_not_disclosed():
    r = client.get(f"/api/v1/audit/{TARGET_B}", headers=_headers("orgadm"))
    assert r.status_code == 200 and r.json() == []


def test_cross_org_organization_is_non_disclosing_404():
    r = client.get(f"/api/v1/audit/organization/{ORG_B}", headers=_headers("orgadm"))
    assert r.status_code == 404
    assert "audit" not in r.text.lower() or r.json()["detail"] == "organization not found"


def test_super_admin_may_read_another_org():
    r = client.get(f"/api/v1/audit/organization/{ORG_B}", headers=_headers("super"))
    assert r.status_code == 200
    assert all(e["organization_id"] == ORG_B for e in r.json())


# 4. Branch scoping.
def test_branch_admin_sees_only_own_branch():
    rows = client.get(f"/api/v1/audit/{TARGET_A}", headers=_headers("bradm")).json()
    assert len(rows) == 1
    assert rows[0]["branch_id"] == BR_A1


def test_org_admin_sees_every_branch_in_org():
    rows = client.get(f"/api/v1/audit/{TARGET_A}", headers=_headers("orgadm")).json()
    assert {e["branch_id"] for e in rows} == {BR_A1, BR_A2}


# 5. RBAC.
def test_assistant_cannot_read_audit():
    for path in (f"/api/v1/audit/{TARGET_A}",
                 f"/api/v1/audit/organization/{ORG_A}"):
        assert client.get(path, headers=_headers("ast")).status_code == 403


# 6. Filters.
def test_filter_by_action():
    rows = client.get(f"/api/v1/audit/{TARGET_A}?action=queue.reorder",
                      headers=_headers("orgadm")).json()
    assert len(rows) == 1 and rows[0]["action"] == "queue.reorder"
    assert client.get(f"/api/v1/audit/{TARGET_A}?action=nope",
                      headers=_headers("orgadm")).json() == []
