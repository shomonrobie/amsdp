"""Organization appointment policy API (owner decisions Q1 and Q5).

Two numbers decide whether a patient who arrives without a booking can be seen,
and they belong to the organization, not to a code constant:

``unscheduled_daily_limit``
    how many outside-session patients one doctor may accept per day;

``allow_unscheduled``
    whether the override is available at all.

The booking path reads them through :func:`common.config.get_appointment_config`
and the audit trail records every change with its before/after values (Q5).
Routes follow the sibling ``notification_config`` surface: prefixed with the
organization, resolved from the token, and a foreign ``org_id`` is a
non-disclosing 404.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from common.audit import record_audit
from common.auth import AuthContext, require_permission
from common.config import (get_appointment_config, merge_appointment_config,
                           MAX_UNSCHEDULED_DAILY_LIMIT)
from common.database import SessionFactory
from common.models import Organization

router = APIRouter(prefix="/api/v1/orgs/{org_id}/appointment-config",
                   tags=["appointment-config"])


class AppointmentConfigUpdate(BaseModel):
    unscheduled_daily_limit: Optional[int] = None
    allow_unscheduled: Optional[bool] = None


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


@router.get("")
def get_appointment_config_endpoint(
        org_id: str,
        auth: AuthContext = Depends(require_permission("org.read"))):
    """The policy in force, plus who last changed it and when."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        view = get_appointment_config(org.config)
        stored = (org.config or {}).get("appointment_config") or {}
        view["updated_at"] = stored.get("updated_at", "")
        view["updated_by"] = stored.get("updated_by", "")
        view["max_unscheduled_daily_limit"] = MAX_UNSCHEDULED_DAILY_LIMIT
        return view
    finally:
        session.close()


@router.put("")
def update_appointment_config_endpoint(
        org_id: str, data: AppointmentConfigUpdate,
        auth: AuthContext = Depends(require_permission("org.manage"))):
    """Change the outside-session policy; every change is audited."""
    _scoped_org(auth, org_id)
    if data.unscheduled_daily_limit is not None:
        if not 1 <= data.unscheduled_daily_limit <= MAX_UNSCHEDULED_DAILY_LIMIT:
            raise HTTPException(
                422, "unscheduled_daily_limit must be between 1 and "
                     f"{MAX_UNSCHEDULED_DAILY_LIMIT}")
    if data.unscheduled_daily_limit is None and data.allow_unscheduled is None:
        raise HTTPException(422, "no changes supplied")

    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        before = get_appointment_config(org.config)
        new_config = merge_appointment_config(org.config, {
            "unscheduled_daily_limit": data.unscheduled_daily_limit,
            "allow_unscheduled": data.allow_unscheduled})
        from datetime import datetime, timezone
        new_config["appointment_config"]["updated_at"] = datetime.now(
            timezone.utc).isoformat()
        new_config["appointment_config"]["updated_by"] = auth.user_id
        org.config = new_config
        after = get_appointment_config(new_config)
        record_audit(session, service="organization", org_id=org_id,
                     action="appointment_config.updated",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason="walk-in / unscheduled capacity policy")
        session.commit()
        view = get_appointment_config(org.config)
        view["updated_at"] = new_config["appointment_config"]["updated_at"]
        view["updated_by"] = auth.user_id
        view["max_unscheduled_daily_limit"] = MAX_UNSCHEDULED_DAILY_LIMIT
        return view
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
