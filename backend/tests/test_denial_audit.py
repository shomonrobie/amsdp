"""Denial auditing (owner decision Q-2) — every 403/404/422 is recorded.

``.clinerules`` §3: "Denials are recorded (audited), never silently swallowed."
Before Q-2 no refusal left any trace.  These tests assert the new contract on the
real stack (FastAPI app + PostgreSQL trail), not on a stub:

* a denial raised by a permission dependency (403), by the tenant gate (404) and
  by request validation (422) is persisted with actor, organization and branch;
* a denial is recorded **once** — no duplicate rows from overlapping hooks;
* a request that is not a denial writes nothing;
* the 401 exclusion is deliberate and visible: it is logged, not stored, because
  ``audit_events.organization_id`` is NOT NULL and an unverified token must never
  be allowed to choose which tenant's trail a row lands in;
* tokens travelled in the path are redacted before they are stored.

Rows are read back through ``common.database`` — the same engine the services
use — so a green test means the row is really in PostgreSQL.
"""

import logging
import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from amsdp_test_support import (db_session, ensure_branch, ensure_org,  # noqa: E402
                                ensure_user, headers, load_app)
from common.denial_audit import DENIAL_ACTION, safe_path             # noqa: E402
from common.models import AuditEvent                                  # noqa: E402

ORG = "q2-denial-org"
OTHER = "q2-denial-other-org"
BRANCH = "q2-denial-branch"

#: key -> (username, role, organization, branch)
USERS = {
    "orgadm": ("q2_denial_orgadm", "org_admin", ORG, None),
    "ast": ("q2_denial_ast", "assistant", ORG, BRANCH),
    "rec": ("q2_denial_rec", "receptionist", ORG, BRANCH),
}

audit_client = TestClient(load_app("audit"))
patient_client = TestClient(load_app("patient"))


@pytest.fixture(scope="module", autouse=True)
def seeded():
    """Create this module's reference rows once (never deleted)."""
    ensure_org(ORG)
    ensure_org(OTHER)
    ensure_branch(BRANCH, ORG)
    ids = {}
    for username, role, org, branch in USERS.values():
        ids[username] = ensure_user(username, role, org, branch)
    return ids


def _denials(target_id: str | None = None, actor_id: str | None = None) -> list:
    """Rows with the denial action, oldest first."""
    with db_session() as s:
        q = s.query(AuditEvent).filter(AuditEvent.action == DENIAL_ACTION)
        if target_id is not None:
            q = q.filter(AuditEvent.target_id == target_id)
        if actor_id is not None:
            q = q.filter(AuditEvent.actor_id == actor_id)
        return [(e.id, e.service, e.organization_id, e.branch_id, e.target_id,
                 e.actor_id, e.actor_role, e.reason, e.after)
                for e in q.order_by(AuditEvent.timestamp).all()]


def _one(target_id: str) -> tuple:
    rows = _denials(target_id=target_id)
    assert rows, f"no denial audit row for {target_id!r}"
    return rows[-1]


# ---------------------------------------------------------------------------
# 403 — permission dependency
# ---------------------------------------------------------------------------

def test_403_from_permission_dependency_is_recorded(seeded):
    target = f"GET /api/v1/audit/organization/{ORG}"
    before = len(_denials(target_id=target))
    r = audit_client.get(f"/api/v1/audit/organization/{ORG}",
                         headers=headers(USERS["ast"][0]))
    assert r.status_code == 403, r.text
    rows = _denials(target_id=target)
    assert len(rows) == before + 1, "a refused read must produce exactly one row"
    (_id, service, org_id, branch_id, _target, actor_id, actor_role,
     reason, after) = rows[-1]
    assert service == "audit"
    assert org_id == ORG
    assert actor_id == seeded[USERS["ast"][0]]
    assert actor_role == "assistant"
    assert branch_id == BRANCH
    assert reason == "denied status=403"
    assert after["status"] == 403


# ---------------------------------------------------------------------------
# 404 — tenant gate (non-disclosing)
# ---------------------------------------------------------------------------

def test_404_from_tenant_gate_is_recorded(seeded):
    target = f"GET /api/v1/audit/organization/{OTHER}"
    before = len(_denials(target_id=target))
    r = audit_client.get(f"/api/v1/audit/organization/{OTHER}",
                         headers=headers(USERS["orgadm"][0]))
    assert r.status_code == 404, r.text
    assert len(_denials(target_id=target)) == before + 1
    (_id, service, org_id, _branch, _target, actor_id, actor_role,
     reason, after) = _one(target)
    assert (service, org_id, actor_role) == ("audit", ORG, "org_admin")
    assert actor_id == seeded[USERS["orgadm"][0]]
    assert reason == "denied status=404"
    assert after["status"] == 404


# ---------------------------------------------------------------------------
# 422 — request validation
# ---------------------------------------------------------------------------

def test_422_from_validation_is_recorded(seeded):
    target = "GET /api/v1/patients"
    before = len(_denials(target_id=target))
    r = patient_client.get("/api/v1/patients?limit=1000",
                           headers=headers(USERS["rec"][0]))
    assert r.status_code == 422, r.text
    rows = _denials(target_id=target)
    assert len(rows) == before + 1
    assert rows[-1][1] == "patient"          # recorded by the patient service
    assert rows[-1][7] == "denied status=422"


# ---------------------------------------------------------------------------
# Nothing is recorded for a request that is not a denial
# ---------------------------------------------------------------------------

def test_allowed_request_writes_no_denial_row(seeded):
    target = "GET /api/v1/patients"
    before = len(_denials(target_id=target))
    r = patient_client.get("/api/v1/patients?limit=5",
                           headers=headers(USERS["rec"][0]))
    assert r.status_code == 200, r.text
    assert len(_denials(target_id=target)) == before


# ---------------------------------------------------------------------------
# 401 — deliberate, visible exclusion
# ---------------------------------------------------------------------------

def test_unauthenticated_denial_is_logged_not_stored(seeded, caplog):
    target = f"GET /api/v1/audit/organization/{ORG}"
    before = len(_denials(target_id=target))
    with caplog.at_level(logging.WARNING, logger="amsdp.denial_audit"):
        r = audit_client.get(f"/api/v1/audit/organization/{ORG}")
    assert r.status_code == 401, r.text
    assert len(_denials(target_id=target)) == before, (
        "a 401 has no verified tenant and must not be written to any trail")
    assert any("without tenant context" in m for m in caplog.messages), (
        "the exclusion must be visible in the log, not silent")


def test_forged_token_is_not_used_for_attribution(seeded):
    """A forged token must never choose which tenant's trail a row lands in."""
    import jwt

    target = f"GET /api/v1/audit/organization/{ORG}"
    before = len(_denials(target_id=target))
    forged = jwt.encode(
        {"sub": seeded[USERS["ast"][0]], "org": OTHER, "role": "assistant",
         "branch": BRANCH, "exp": 9999999999},
        "not-the-platform-key", algorithm="HS256")
    r = audit_client.get(f"/api/v1/audit/organization/{ORG}",
                         headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401, r.text
    assert len(_denials(target_id=target)) == before
    # The forged organization claim must not have produced a row anywhere.
    assert not _denials(actor_id=seeded[USERS["ast"][0]]) or all(
        row[2] != OTHER for row in _denials(actor_id=seeded[USERS["ast"][0]]))


# ---------------------------------------------------------------------------
# Redaction of token-bearing paths
# ---------------------------------------------------------------------------

def test_token_like_segment_is_redacted(seeded):
    token_like = uuid.uuid4().hex + uuid.uuid4().hex[:8]     # 40 chars
    r = patient_client.get(f"/api/v1/patients/{token_like}",
                           headers=headers(USERS["rec"][0]))
    assert r.status_code == 404, r.text
    row = _one("GET /api/v1/patients/{redacted}")
    assert token_like not in row[4]
    assert row[8]["status"] == 404
    assert headers(USERS["rec"][0])["Authorization"].split()[-1] not in str(row)


def test_safe_path_keeps_short_segments_and_redacts_long_ones():
    assert safe_path("/api/v1/audit/organization/q2-denial-org") == \
        "/api/v1/audit/organization/q2-denial-org"
    assert safe_path("/api/v1/track/" + "a1b2c3d4" * 5) == \
        "/api/v1/track/{redacted}"
    assert safe_path("") == "/"


