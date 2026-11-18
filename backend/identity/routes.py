"""Additional endpoints — user listing, update, permission check.

PostgreSQL-backed with shared auth/authorization.
"""

from typing import Optional

import sqlalchemy as sa
from fastapi import HTTPException, Depends, APIRouter

from models import StaffUserUpdate, StaffUserResponse, PermissionCheck
from permissions import check as perm_check, can_grant_role, role_level

from common.database import SessionFactory
from common.models import StaffUser, StaffDoctorAssignment, Doctor, Organization
from common.auth import AuthContext, get_current_user, require_permission, count_active_org_admins
from common.audit import record_audit

router = APIRouter()


# PO-RBAC-01: load active doctor assignments for a staff member.
def _assigned_doctor_ids(staff_user_id: str) -> list[str]:
    """Return the list of actively assigned doctor IDs for a staff member."""
    session = SessionFactory()
    try:
        from sqlalchemy import inspect as sa_inspect
        if not sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
            return []
        rows = session.execute(
            sa.text("""
                SELECT doctor_id FROM staff_doctor_assignments
                WHERE staff_user_id = :uid AND status = 'active'
            """), {"uid": staff_user_id}
        ).scalars().all()
        return list(rows)
    except Exception:
        return []
    finally:
        session.close()


def _user_to_dict(user):
    assigned = _assigned_doctor_ids(user.id)
    # Fall back to legacy single doctor_id when no assignment rows exist.
    if not assigned and user.doctor_id:
        assigned = [user.doctor_id]
    return StaffUserResponse(
        id=user.id, organization_id=user.organization_id,
        branch_id=user.branch_id, doctor_id=user.doctor_id or None,
        # PO-RBAC-01: all active doctor assignments for this staff member.
        doctor_ids=assigned,
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
        # PO-RBAC-04: lock the user row for concurrent-safety when modifying
        # role or status of an org_admin.
        # PO-RBAC-04: lock the user row AND the organization row for
        # concurrent-safety when modifying role/status of an org_admin.
        # Locking only the user row is insufficient: two concurrent requests
        # could each deactivate a different org_admin and both pass the
        # count check, leaving zero active org_admins.  Locking the org row
        # serializes all org_admin-affecting changes within one organization.
        user = session.query(StaffUser).filter(
            StaffUser.id == user_id).with_for_update().first()
        if not user:
            raise HTTPException(404, "user not found")
        org_row = session.query(Organization).filter(
            Organization.id == user.organization_id).with_for_update().first()
        if not org_row:
            raise HTTPException(404, "organization not found")
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
        # PO-RBAC-04: save original role/status before changes for last-admin check.
        original_role = user.role
        original_status = user.status
        if data.role is not None:
            # PO-RBAC-03: prevent self-escalation — a caller cannot grant
            # themselves a higher role, regardless of their current role
            # (including super_admin).
            if user_id == auth.user_id and role_level(data.role) > role_level(user.role):
                raise HTTPException(403, "cannot escalate your own role")
            # PO-RBAC-03: a caller cannot grant another user a role at or
            # above their own level.  super_admin is exempt when granting to
            # other users only.
            if user_id != auth.user_id and not auth.is_super_admin:
                if not can_grant_role(auth.role, data.role):
                    raise HTTPException(403, "cannot grant a role at or above your own level")
            user.role = data.role
        if data.status is not None:
            user.status = data.status
        # PO-RBAC-04: prevent removal of the last active Organization Admin.
        # Check transactionally under the row lock acquired above.
        if original_role == "org_admin":
            if user.role != "org_admin":
                # Role changed away from org_admin
                remaining = count_active_org_admins(session, user.organization_id,
                                                     exclude_user_id=user_id)
                if remaining == 0:
                    raise HTTPException(403,
                        "cannot remove the last active Organization Admin")
            if original_status == "active" and user.status != "active":
                # Status changed away from active while being org_admin
                remaining = count_active_org_admins(session, user.organization_id,
                                                     exclude_user_id=user_id)
                if remaining == 0:
                    raise HTTPException(403,
                        "cannot deactivate the last active Organization Admin")
        if data.doctor_ids is not None:
            doctor_ids = list(data.doctor_ids)
        elif data.doctor_id is not None:
            doctor_ids = [data.doctor_id] if data.doctor_id else []
        else:
            doctor_ids = None
        if doctor_ids is not None:
            # Validate every doctor: exists, active, same organization.
            for did in doctor_ids:
                doc = session.query(Doctor).filter(
                    Doctor.id == did,
                    Doctor.organization_id == user.organization_id,
                    Doctor.status == "active",
                ).first()
                if not doc:
                    raise HTTPException(
                        422, f"doctor_id {did} must reference an active doctor "
                             f"in the same organization")
            # Replace all existing assignments with the new set.
            # Resilient to missing table (pre-migration): check first.
            from sqlalchemy import inspect as sa_inspect
            if sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
                session.query(StaffDoctorAssignment).filter(
                    StaffDoctorAssignment.staff_user_id == user_id
                ).delete(synchronize_session=False)
                for did in doctor_ids:
                    session.add(StaffDoctorAssignment(
                        id=str(uuid.uuid4()),
                        staff_user_id=user_id,
                        doctor_id=did,
                        organization_id=user.organization_id,
                        status="active",
                    ))
            # Keep legacy field in sync (first assigned doctor).
            user.doctor_id = doctor_ids[0] if doctor_ids else None
        elif data.doctor_id is not None:
            # Legacy single-field update path.
            if data.doctor_id:
                doc = session.query(Doctor).filter(
                    Doctor.id == data.doctor_id,
                    Doctor.organization_id == user.organization_id,
                    Doctor.status == "active",
                ).first()
                if not doc:
                    raise HTTPException(
                        422, "doctor_id must reference an active doctor "
                             "in the same organization")
                # Replace assignments with just this one doctor.
                from sqlalchemy import inspect as sa_inspect
                if sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
                    session.query(StaffDoctorAssignment).filter(
                        StaffDoctorAssignment.staff_user_id == user_id
                    ).delete(synchronize_session=False)
                    session.add(StaffDoctorAssignment(
                        id=str(uuid.uuid4()),
                        staff_user_id=user_id,
                        doctor_id=data.doctor_id,
                        organization_id=user.organization_id,
                        status="active",
                    ))
            user.doctor_id = data.doctor_id or None
        record_audit(session, service="identity", org_id=user.organization_id,
            action="staff.updated", target_type="staff_user", target_id=user.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=user.branch_id or "",
            after={"role": user.role, "status": user.status or "active",
                   "display_name": user.display_name,
                   "doctor_ids": doctor_ids})
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