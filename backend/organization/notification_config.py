"""Organization notification configuration API (Sequence 3, WP6).

BR §35–§36 + PQV §D: an **organization admin** decides whether WhatsApp/SMS
messages are sent and how long before the visit the reminder goes out. A
**Super Admin** (platform operator) alone decides which providers exist — that
control lives in the ``AMSDP_NOTIFICATION_PROVIDERS`` environment allow-list,
never in an HTTP payload, so an organization can never point the outbox at an
unapproved provider.

Routes are prefixed ``/api/v1/orgs/{org_id}`` and always resolve the caller's
organization from the token; a foreign ``org_id`` fails closed as a
**non-disclosing 404** (``_scoped_org``), never as 403 and never by trusting the
identifier in the request.  The older organization endpoints still use the
shared :func:`common.auth.require_org_access` helper, which answers 403; the new
Sequence 3 surface deliberately follows the stricter 404 contract.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import AuthContext, require_permission
from common.database import SessionFactory
from common.models import Notification, Organization
from common.notifications import config as notif_config
from common.notifications import outbox
from common.notifications.providers import describe_platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orgs/{org_id}", tags=["notification-config"])


class NotificationConfigUpdate(BaseModel):
    whatsapp_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    whatsapp_provider: Optional[str] = None
    sms_provider: Optional[str] = None
    reminder_lead_minutes: Optional[int] = None


def _scoped_org(auth: AuthContext, org_id: str) -> str:
    """Non-disclosing tenant gate: a foreign organization is 404, not 403."""
    if auth.is_super_admin or auth.organization_id == org_id:
        return org_id
    raise HTTPException(404, "organization not found")


def _org_or_404(session, org_id: str) -> Organization:
    org = session.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        raise HTTPException(404, "organization not found")
    return org


@router.get("/notification-config")
def get_notification_config_endpoint(
        org_id: str,
        auth: AuthContext = Depends(require_permission("org.read"))):
    """Current settings, channel status and platform capability (no secrets)."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        view = notif_config.public_view(org_id, org.config)
        stored = (org.config or {}).get("notification_config") or {}
        view["updated_at"] = stored.get("updated_at", "")
        view["updated_by"] = stored.get("updated_by", "")
        return view
    finally:
        session.close()


@router.put("/notification-config")
def update_notification_config_endpoint(
        org_id: str, data: NotificationConfigUpdate,
        auth: AuthContext = Depends(require_permission("org.manage"))):
    """Update toggles, providers and reminder timing.

    Validation is server-side and non-negotiable: an unknown provider, an
    unapproved lead time or a foreign organization is rejected with 422/404.
    The UI is never the boundary.
    """
    _scoped_org(auth, org_id)
    updates = {k: v for k, v in data.dict().items() if v is not None}
    errors = notif_config.validate_updates(updates)
    if errors:
        raise HTTPException(422, "; ".join(errors))
    if not updates:
        raise HTTPException(422, "no changes supplied")

    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        before_view = notif_config.get_notification_config(org.config)
        new_config = notif_config.merge_notification_config(org.config, updates)
        new_config["notification_config"]["updated_at"] = datetime.now(
            timezone.utc).isoformat()
        new_config["notification_config"]["updated_by"] = auth.user_id
        org.config = new_config
        after_view = notif_config.get_notification_config(new_config)

        def _audit_state(view):
            return {"whatsapp": {"enabled": view["whatsapp"]["enabled"],
                                 "provider": view["whatsapp"]["provider"]},
                    "sms": {"enabled": view["sms"]["enabled"],
                            "provider": view["sms"]["provider"]},
                    "reminder_lead_minutes": view["reminder_lead_minutes"]}

        record_audit(session, service="organization", org_id=org_id,
                     action="notification_config.updated",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=_audit_state(before_view),
                     after=_audit_state(after_view),
                     reason="notification settings")
        session.commit()
        view = notif_config.public_view(org_id, org.config)
        view["updated_at"] = new_config["notification_config"]["updated_at"]
        view["updated_by"] = auth.user_id
        return view
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


@router.get("/notification-status")
def notification_status(
        org_id: str,
        auth: AuthContext = Depends(require_permission("org.read"))):
    """Delivery health for this organization (last 24h + lifetime counters).

    ``sent`` and ``delivered`` are reported separately and honestly: with the
    mock adapter every successful message is ``sent`` only, because no handset
    acknowledged it.
    """
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        cfg = notif_config.get_notification_config(org.config)
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        last24 = outbox.stats(session, org_id, since=since)
        lifetime = outbox.stats(session, org_id)
        # "Latest" means the last message the outbox *touched*, not merely the
        # last row inserted: a reminder scheduled days ahead is inserted after
        # the confirmation that is sent immediately, so ordering by
        # ``created_at`` alone would hide the delivery outcome.
        latest = session.query(Notification).filter(
            Notification.organization_id == org_id).order_by(
            Notification.updated_at.desc().nullslast(),
            Notification.created_at.desc()).first()
        return {
            "organization_id": org_id,
            "channels": {"whatsapp": cfg["whatsapp"], "sms": cfg["sms"]},
            "platform": describe_platform(),
            "last_24h": last24,
            "lifetime": lifetime,
            "latest_message": {
                "type": latest.notification_type,
                "channel": latest.channel,
                "status": latest.status,
                "scheduled_at": latest.scheduled_at.isoformat()
                                if latest and latest.scheduled_at else "",
                "sent_at": latest.sent_at.isoformat() if latest and latest.sent_at else "",
                "delivered_at": (latest.delivered_at.isoformat()
                                 if latest and latest.delivered_at else ""),
                "error": latest.error or "",
            } if latest else None,
        }
    finally:
        session.close()

