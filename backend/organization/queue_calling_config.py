"""Organization doctor queue-calling policy API (QUE-006 / DEV-1, decision D).

Whether a **doctor** may call their own patient forward is an organization
decision, not a code constant:

``doctor_queue_calling_enabled``
    when ``true``, a doctor holding only ``queue.consult`` may use the queue
    ``call`` action on their own patients; when ``false``, ``call`` stays
    front-desk work exactly as the role matrix says.

The queue service reads the effective value through
:func:`common.config.get_queue_calling_config`, so the stored override and the
facility-type default are resolved in one place. The routes follow the sibling
``appointment-config`` surface: prefixed with the organization, resolved from
the token, and a foreign ``org_id`` is a non-disclosing 404.

**Read is wider than write, deliberately.** A doctor needs to know whether the
Call control applies to them before rendering it, and ``org.read`` is not in the
doctor role. ``GET`` therefore answers any authenticated member of the
organization (the flag is operational policy, not personal or tenant data);
``PUT`` stays behind ``org.manage``, which only an Organization Admin (or the
platform administrator) holds. The write is audited with before/after values,
like every other organization policy change.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import AuthContext, get_current_user, require_permission
from common.config import get_queue_calling_config, merge_queue_calling_config
from common.database import SessionFactory
from common.models import Organization

router = APIRouter(prefix="/api/v1/orgs/{org_id}/queue-calling-config",
                   tags=["queue-calling-config"])


class QueueCallingConfigUpdate(BaseModel):
    doctor_queue_calling_enabled: Optional[bool] = None


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


def _view(org: Organization) -> dict:
    """The effective policy plus who last changed it and when."""
    view = get_queue_calling_config(org.config, org.facility_type)
    stored = (org.config or {}).get("queue_calling_config") or {}
    view["updated_at"] = stored.get("updated_at", "")
    view["updated_by"] = stored.get("updated_by", "")
    return view


@router.get("")
def get_queue_calling_config_endpoint(
        org_id: str,
        auth: AuthContext = Depends(get_current_user)):
    """The effective doctor queue-calling policy for this organization."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        return _view(_org_or_404(session, org_id))
    finally:
        session.close()


@router.put("")
def update_queue_calling_config_endpoint(
        org_id: str, data: QueueCallingConfigUpdate,
        auth: AuthContext = Depends(require_permission("org.manage"))):
    """Change the policy; the change is audited with its before/after values."""
    _scoped_org(auth, org_id)
    if data.doctor_queue_calling_enabled is None:
        raise HTTPException(422, "no changes supplied")

    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        before = get_queue_calling_config(org.config, org.facility_type)
        new_config = merge_queue_calling_config(org.config, {
            "doctor_queue_calling_enabled":
                data.doctor_queue_calling_enabled})
        new_config["queue_calling_config"]["updated_at"] = datetime.now(
            timezone.utc).isoformat()
        new_config["queue_calling_config"]["updated_by"] = auth.user_id
        org.config = new_config
        after = get_queue_calling_config(new_config, org.facility_type)
        record_audit(session, service="organization", org_id=org_id,
                     action="queue_calling_config.updated",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason="doctor queue-calling policy")
        session.commit()
        return _view(org)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
