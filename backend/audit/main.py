"""AMSDP Audit Service — read-only, tenant-scoped access to the audit trail.

Audit rows are written by the service that performs the action, inside that
action's own transaction (``common.audit.record_audit``), so the trail is
append-only and atomic with the change it describes.

Sequence 4 hardening (WP3/WP8)
------------------------------
This module used to be the M1 in-memory stub: it accepted ``POST /api/v1/audit``
from any anonymous caller and served every organization's events to anyone who
knew an id. It now:

* exposes **no write endpoint** — an HTTP caller can never forge or rewrite an
  audit row; the trail is written only by the service performing the action;
* requires ``audit.read`` and derives the tenant from the authenticated token;
* answers a foreign organization with a **non-disclosing 404**, never 403;
* scopes branch-bound users to their own branch;
* reads the persistent ``audit_events`` table instead of a process-local dict.
"""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query

from common.auth import AuthContext, record_platform_access, require_permission
from common.database import SessionFactory
from common.models import AuditEvent
from common.health import install_health
from common.denial_audit import install_denial_audit

app = FastAPI(title="AMSDP Audit Service")
install_health(app, "audit")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
# The trail is append-only, so a refused read is recorded, never dropped.
install_denial_audit(app, "audit")

#: Hard ceiling per query so one call can never dump the whole trail.
MAX_EVENTS = 500


def _row_to_dict(e: AuditEvent) -> dict:
    """Stable wire shape — the keys the M1 contract already published."""
    return {
        "event_id": e.id,
        "id": e.id,
        "service": e.service,
        "organization_id": e.organization_id,
        "branch_id": e.branch_id or "",
        "action": e.action,
        "target_type": e.target_type,
        "target_id": e.target_id,
        "actor_id": e.actor_id,
        "actor_role": e.actor_role or "",
        "before": e.before,
        "after": e.after,
        "reason": e.reason or "",
        "timestamp": e.timestamp.isoformat() if e.timestamp else "",
    }


def _scoped_org(auth: AuthContext, org_id: str) -> None:
    """Non-disclosing tenant gate: a foreign organization is 404, never 403.

    Owner decision Q-1: reading another tenant's trail is a *platform*
    capability (``platform.cross_org``), not an accident of a role string, and
    every such read is recorded in the target organization's own trail so the
    tenant can see that platform support looked at it.
    """
    if auth.organization_id == org_id:
        return
    if not auth.can_cross_org:
        raise HTTPException(404, "organization not found")
    record_platform_access(auth, org_id, service="audit")


def _apply_branch_scope(query, auth: AuthContext):
    """Branch-bound users only ever see their own branch's events."""
    if auth.is_super_admin or auth.is_org_admin:
        return query
    if auth.branch_id:
        return query.filter(AuditEvent.branch_id == auth.branch_id)
    return query


@app.get("/api/v1/audit/organization/{org_id}")
def get_org_events(org_id: str,
                   auth: AuthContext = Depends(require_permission("audit.read"))):
    """Events recorded for one organization, newest first."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        q = _apply_branch_scope(
            session.query(AuditEvent).filter(AuditEvent.organization_id == org_id),
            auth)
        return [_row_to_dict(e) for e in
                q.order_by(AuditEvent.timestamp.desc()).limit(MAX_EVENTS).all()]
    finally:
        session.close()


@app.get("/api/v1/audit/{target_id}")
def get_events(target_id: str, action: Optional[str] = Query(None),
               actor: Optional[str] = Query(None),
               auth: AuthContext = Depends(require_permission("audit.read"))):
    """Events for one target inside the caller's own organization.

    An unknown target and a target owned by another tenant are indistinguishable:
    both return an empty list, so this endpoint is not an existence oracle.
    """
    session = SessionFactory()
    try:
        q = _apply_branch_scope(
            session.query(AuditEvent).filter(
                AuditEvent.target_id == target_id,
                AuditEvent.organization_id == auth.organization_id),
            auth)
        if action:
            q = q.filter(AuditEvent.action == action)
        if actor:
            q = q.filter(AuditEvent.actor_id == actor)
        return [_row_to_dict(e) for e in
                q.order_by(AuditEvent.timestamp.desc()).limit(MAX_EVENTS).all()]
    finally:
        session.close()
