"""AMSDP shared persistent audit helper.

Writes rows to the existing ``audit_events`` table (PostgreSQL) using the
caller's session so the audit row commits atomically with the business
operation.

Usage::

    from common.audit import record_audit
    session = SessionFactory()
    try:
        ... business change ...
        record_audit(session, service="queuing", org_id=auth.organization_id,
                     action="queue.reorder", target_type="queue_entry",
                     target_id=entry.id, actor_id=auth.user_id,
                     actor_role=auth.role, branch_id=entry.branch_id,
                     before={"position": old}, after={"position": new},
                     reason="manual move")
        session.commit()
    ...
"""

import uuid
from datetime import datetime, timezone

from .models import AuditEvent


def record_audit(session, *, service: str, org_id: str, action: str,
                 target_type: str, target_id: str, actor_id: str,
                 actor_role: str, branch_id: str = "",
                 before: dict | None = None, after: dict | None = None,
                 reason: str = "") -> AuditEvent:
    """Add an audit event using *session*; caller owns commit/rollback."""
    event = AuditEvent(
        id=str(uuid.uuid4()),
        service=service,
        organization_id=org_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
        actor_role=actor_role,
        branch_id=branch_id or None,
        before=before,
        after=after,
        reason=reason,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(event)
    return event


# O-SaaS-2 / O-SaaS-10: platform-only events belong in ``platform_audit_events``,
# separate from tenant-affecting events in ``audit_events``.  This table has NO
# organization_id.  The actor is identified by named platform operator identity
# plus platform role, minimizing unnecessary personal information.
def record_platform_audit(session, *, service: str, action: str,
                          target_type: str, target_id: str, actor_id: str,
                          actor_role: str,
                          before: dict | None = None, after: dict | None = None,
                          reason: str = "") -> "PlatformAuditEvent":
    """Add a platform audit event using *session*; caller owns commit/rollback.

    Writes to ``platform_audit_events`` (no organization_id).  Per O-SaaS-10,
    actor identity is the named platform operator plus their platform role.
    """
    from .models import PlatformAuditEvent
    event = PlatformAuditEvent(
        id=str(uuid.uuid4()),
        service=service,
        action=action,
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
        actor_role=actor_role,
        before=before,
        after=after,
        reason=reason,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(event)
    return event