"""Organization walk-in placement policy API (MP-10 / Business Rules §24–§25).

BR §25 gives the facility a choice among four placement policies — end of
queue, first come first served, reserved capacity, staff-controlled placement —
and then says who may decide it:

    Super Admin defines available options/limits. Facility Admin selects
    policy. Only authorized users may change it. Changes are audit logged and
    apply prospectively; they must not silently reorder an active queue or
    alter existing appointments.

That sentence is what this module implements. The *platform* set of options is
:data:`common.config.WALK_IN_POLICIES`; a platform administrator may narrow it
per organization through ``allowed_walk_in_policies``. The facility's own
administrator selects one of the allowed options and the reserve split. Reads
are open to every member of the organization (the queue page has to know
whether it must ask for a position before it renders the walk-in form); writes
need ``org.manage``, which no front-desk role holds.

Routes follow the sibling ``appointment-config`` and ``queue-calling-config``
surfaces: prefixed with the organization, resolved from the token, and a
foreign ``org_id`` is a non-disclosing 404.

**Prospective only.** Writing the policy touches no queue row. Placement is
computed by ``queuing.placement`` at insertion time from the configuration in
force then, so a change can never move a patient who is already waiting.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import AuthContext, get_current_user, require_permission
from common.config import (MAX_WALK_IN_RESERVE_COUNT, MAX_WALK_IN_RESERVE_PERCENT,
                           WALK_IN_POLICIES, allowed_walk_in_policies,
                           get_walk_in_config, merge_walk_in_config)
from common.database import SessionFactory
from common.models import Organization

router = APIRouter(prefix="/api/v1/orgs/{org_id}/walk-in-config",
                   tags=["walk-in-config"])


class WalkInConfigUpdate(BaseModel):
    walk_in_policy: Optional[str] = None
    walk_in_reserve_mode: Optional[str] = None
    walk_in_reserve_value: Optional[int] = None
    # Platform-level narrowing (BR §25: "Super Admin defines available
    # options"). Only a platform administrator may set it.
    allowed_walk_in_policies: Optional[List[str]] = None


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
    """The effective policy, the options this facility may choose from, bounds."""
    view = get_walk_in_config(org.config)
    view["limits"] = {"percent": MAX_WALK_IN_RESERVE_PERCENT,
                      "count": MAX_WALK_IN_RESERVE_COUNT}
    return view


def _validate(data: WalkInConfigUpdate, org: Organization,
              auth: AuthContext) -> dict:
    """Check the request against BR §25's roles and limits; return the updates.

    Everything is validated before the row is touched, so a partly valid
    request writes nothing.
    """
    updates = {}
    if data.allowed_walk_in_policies is not None:
        if not auth.is_super_admin:
            raise HTTPException(
                403, "only a platform administrator may change the available "
                     "walk-in policies")
        choices = list(data.allowed_walk_in_policies)
        if not choices:
            raise HTTPException(422, "allowed_walk_in_policies cannot be empty")
        unknown = [c for c in choices if c not in WALK_IN_POLICIES]
        if unknown:
            raise HTTPException(
                422, "unknown walk-in policy: "
                     f"{', '.join(map(str, unknown))}; allowed: "
                     f"{', '.join(WALK_IN_POLICIES)}")
        # Canonical order, no duplicates: the stored value is a set of options,
        # not a record of the order somebody typed them in.
        updates["allowed_walk_in_policies"] = [p for p in WALK_IN_POLICIES
                                               if p in choices]

    # The allowed set that will be in force once this request is applied, so a
    # platform administrator can narrow the set and select within it in one call.
    prospective = merge_walk_in_config(org.config, updates)
    allowed = allowed_walk_in_policies(prospective)

    if data.walk_in_policy is not None:
        if data.walk_in_policy not in WALK_IN_POLICIES:
            raise HTTPException(
                422, f"unknown walk-in policy: {data.walk_in_policy}; "
                     f"allowed: {', '.join(WALK_IN_POLICIES)}")
        if data.walk_in_policy not in allowed:
            raise HTTPException(
                422, f"walk_in_policy {data.walk_in_policy} is not available to "
                     f"this organization; available: {', '.join(allowed)}")
        updates["walk_in_policy"] = data.walk_in_policy

    if data.walk_in_reserve_mode is not None:
        if data.walk_in_reserve_mode not in ("percent", "count"):
            raise HTTPException(
                422, "walk_in_reserve_mode must be 'percent' or 'count'")
        updates["walk_in_reserve_mode"] = data.walk_in_reserve_mode

    if data.walk_in_reserve_value is not None:
        mode = updates.get("walk_in_reserve_mode") or get_walk_in_config(
            org.config)["walk_in_reserve_mode"]
        limit = (MAX_WALK_IN_RESERVE_COUNT if mode == "count"
                 else MAX_WALK_IN_RESERVE_PERCENT)
        if data.walk_in_reserve_value < 0 or data.walk_in_reserve_value > limit:
            raise HTTPException(
                422, f"walk_in_reserve_value must be between 0 and {limit} "
                     f"for '{mode}' mode")
        updates["walk_in_reserve_value"] = data.walk_in_reserve_value

    if not updates:
        raise HTTPException(422, "no changes supplied")
    return updates


@router.get("")
def get_walk_in_config_endpoint(
        org_id: str,
        auth: AuthContext = Depends(get_current_user)):
    """The effective walk-in policy for this organization."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        return _view(_org_or_404(session, org_id))
    finally:
        session.close()


@router.put("")
def update_walk_in_config_endpoint(
        org_id: str, data: WalkInConfigUpdate,
        auth: AuthContext = Depends(require_permission("org.manage"))):
    """Change the policy; the change is audited with its before/after values."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        updates = _validate(data, org, auth)
        before = get_walk_in_config(org.config)
        new_config = merge_walk_in_config(org.config, updates)
        new_config["queue_config"]["updated_at"] = datetime.now(
            timezone.utc).isoformat()
        new_config["queue_config"]["updated_by"] = auth.user_id
        org.config = new_config
        after = get_walk_in_config(new_config)
        record_audit(session, service="organization", org_id=org_id,
                     action="walk_in_config.updated",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason="walk-in placement policy")
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
