"""Additional endpoints — user listing, update, permission check.

PostgreSQL-backed with shared auth/authorization.
"""

from typing import Optional

from fastapi import HTTPException, Depends, APIRouter

from models import StaffUserUpdate, StaffUserResponse, PermissionCheck
from permissions import check as perm_check

from common.database import SessionFactory
from common.models import StaffUser
from common.auth import AuthContext, get_current_user, require_permission
from common.audit import record_audit

router = APIRouter()


def _user_to_dict(user):
    return StaffUserResponse(
        id=user.id, organization_id=user.organization_id,
        branch_id=user.branch_id, doctor_id=user.doctor_id or None,
        username=user.username,
        display_name=user.display_name, role=user.role,
        locale=user.locale or "en", status=user.status or "active",
    )


@router.get("/api/v1/staff/users")
def list_staff(
    organization_id: Optional[str] = None,
    auth: AuthContext = Depends(require_permission("staff.read")),
):
    """List staff users.  super_admin sees all; others see their own org."""
    session = SessionFactory()
    try:
        q = session.query(StaffUser)
        if not auth.is_super_admin:
            q = q.filter(StaffUser.organization_id == auth.organization_id)
        elif organization_id:
            q = q.filter(StaffUser.organization_id == organization_id)
        return [_user_to_dict(u) for u in q.all()]
    finally:
        session.close()


@router.get("/api/v1/staff/users/{user_id}")
def get_staff_user(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    """Get a staff user.  super_admin can read any; others scoped to same org."""
    session = SessionFactory()
    try:
        user = session.query(StaffUser).filter(StaffUser.id == user_id).first()
        if not user:
            # Same body as the tenant refusal below: an unknown id and another
            # tenant's id must be byte-identical responses (Sequence 4, WP3).
            raise HTTPException(404, "user not found")
        # Sequence 4: a foreign tenant/branch is a non-disclosing 404 (.clinerules
        # §3).  A 403 here would confirm the id exists somewhere else.
        if not auth.is_super_admin and user.organization_id != auth.organization_id:
            raise HTTPException(404, "user not found")
        if not auth.is_super_admin and not auth.is_org_admin and auth.branch_id:
            if user.branch_id != auth.branch_id:
                raise HTTPException(404, "user not found")
        return _user_to_dict(user)
    finally:
        session.close()


@router.patch("/api/v1/staff/users/{user_id}")
def update_staff_user(
    user_id: str,
    data: StaffUserUpdate,
    auth: AuthContext = Depends(require_permission("staff.manage")),
):
    """Update a staff user.  Scoped by org/branch.  super_admin can update any."""
    session = SessionFactory()
    try:
        user = session.query(StaffUser).filter(StaffUser.id == user_id).first()
        if not user:
            raise HTTPException(404, "user not found")
        if not auth.is_super_admin:
            if user.organization_id != auth.organization_id:
                raise HTTPException(404, "user not found")
            if not auth.is_org_admin and auth.branch_id:
                if user.branch_id != auth.branch_id:
                    raise HTTPException(404, "user not found")
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.email is not None:
            user.email = data.email
        if data.mobile is not None:
            user.mobile = data.mobile
        if data.locale is not None:
            user.locale = data.locale
        if data.role is not None:
            user.role = data.role
        if data.status is not None:
            user.status = data.status
        if data.doctor_id is not None:
            if data.doctor_id:
                from common.models import Doctor
                doc = session.query(Doctor).filter(
                    Doctor.id == data.doctor_id,
                    Doctor.organization_id == user.organization_id).first()
                if not doc:
                    raise HTTPException(
                        422, "doctor_id must reference a doctor in the same organization")
            user.doctor_id = data.doctor_id or None
        record_audit(session, service="identity", org_id=user.organization_id,
            action="staff.updated", target_type="staff_user", target_id=user.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=user.branch_id or "",
            after={"role": user.role, "status": user.status or "active",
                   "display_name": user.display_name})
        session.commit()
        return _user_to_dict(user)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/api/v1/staff/check-permission")
def check_permission(
    data: PermissionCheck,
    auth: AuthContext = Depends(get_current_user),
):
    """Check whether a user (within same org) has a specific permission."""
    session = SessionFactory()
    try:
        target = session.query(StaffUser).filter(
            StaffUser.id == data.user_id
        ).first()
        if not target:
            raise HTTPException(404, "user not found")
        if not auth.is_super_admin and target.organization_id != auth.organization_id:
            raise HTTPException(404, "user not found")
        authorized = perm_check(data.resource, target.role)
        return {"authorized": authorized}
    finally:
        session.close()