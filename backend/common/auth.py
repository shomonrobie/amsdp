"""AMSDP Shared Security — Authentication, RBAC, tenant/branch isolation.

FastAPI dependencies for endpoint protection.

Platform administration (owner decision Q-1, 2026-11-12)
-------------------------------------------------------
The platform administrator is no longer a hard-coded bypass.  Its authority is
expressed as two capabilities in ``common.permissions`` — ``platform.admin`` and
``platform.cross_org`` — and every shared decision point below resolves through
them:

* :attr:`AuthContext.is_super_admin` derives from ``platform.admin`` instead of
  comparing the role string, so the role checks already spread across the
  services can no longer outrun the matrix.
* :func:`require_org_access` / :func:`require_branch_access` allow a caller
  outside its own tenant **only** when it holds ``platform.cross_org``, and each
  such access is recorded in the audit trail (:func:`record_platform_access`).
"""

import logging
import os
from typing import Optional

import sqlalchemy as sa
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .audit import record_audit
from .database import SessionFactory
from .models import Branch, StaffUser

logger = logging.getLogger(__name__)

# PO-RBAC-01: load active doctor assignments, resilient to missing table
# (before the f8a1b2c3d4e5 migration is applied).
def _load_assigned_doctor_ids(session, staff_user_id: str) -> list[str]:
    """Return active doctor assignment IDs for a staff member.

    Returns [] if the assignment table does not yet exist (pre-migration) or
    if the staff member has no active assignments.

    If the table exists but the query fails, the exception propagates so the
    caller fails closed rather than silently falling back to legacy
    ``StaffUser.doctor_id`` (which could restore access after revocation).
    """
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


# PO-RBAC-04: protect the last active Organization Admin.
def count_active_org_admins(session, organization_id: str,
                            exclude_user_id: Optional[str] = None) -> int:
    """Return the number of active org_admin users in *organization_id*.

    Optionally excludes *exclude_user_id* (the user being modified).  Used to
    enforce the invariant that every active organization retains at least one
    active org_admin.
    """
    q = session.query(StaffUser).filter(
        StaffUser.organization_id == organization_id,
        StaffUser.role == "org_admin",
        StaffUser.status == "active",
    )
    if exclude_user_id:
        q = q.filter(StaffUser.id != exclude_user_id)
    return q.count()

#: Capability names reserved for platform administration (``common.permissions``).
PLATFORM_ADMIN = "platform.admin"
PLATFORM_CROSS_ORG = "platform.cross_org"


# ---------------------------------------------------------------------------
# JWT configuration
# ---------------------------------------------------------------------------

_SECRET = os.environ.get("AMSDP_JWT_SECRET")
if not _SECRET:
    _env = os.environ.get("AMSDP_ENV", "development")
    if _env != "development":
        raise RuntimeError(
            "AMSDP_JWT_SECRET is not set. "
            "A secure random secret is required in non-development environments."
        )
    _SECRET = "dev-synthetic-key-replace-in-prod"
_ALGO = "HS256"


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.  Raises HTTPException on failure."""
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token")


bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Authenticated request context
# ---------------------------------------------------------------------------

class AuthContext:
    """Injected into endpoint functions that require authentication."""

    def __init__(self, user_id: str, organization_id: str,
                 branch_id: Optional[str], role: str, username: str,
                 locale: str, status: str, token_payload: dict,
                 doctor_id: Optional[str] = None,
                 assigned_doctor_ids: Optional[list[str]] = None):
        self.user_id = user_id
        self.organization_id = organization_id
        self.branch_id = branch_id
        self.role = role
        self.username = username
        self.locale = locale
        self.status = status
        self.token_payload = token_payload
        self.doctor_id = doctor_id
        # PO-RBAC-01: explicit doctor assignments for this staff member.
        # ``doctor_id`` (legacy single assignment) remains for compatibility;
        # ``assigned_doctor_ids`` is the authoritative list for assistant/doctor
        # role access checks.  Defaults to [doctor_id] when set so existing
        # single-assignment behavior is preserved without a DB lookup.
        if assigned_doctor_ids is not None:
            self.assigned_doctor_ids = list(assigned_doctor_ids)
        elif doctor_id:
            self.assigned_doctor_ids = [doctor_id]
        else:
            self.assigned_doctor_ids = []

    def can_access_doctor(self, doctor_id: Optional[str]) -> bool:
        """Check if the authenticated user may access resources for *doctor_id*.

        BR §8 rule 5: enforce branch and doctor assignment scopes in addition
        to role permissions.  BR §7.4/§7.5: a doctor may access only their own
        operational records; an assistant may operate only for their assigned
        doctor(s).

        PO-RBAC-01: doctor access for assistant/doctor roles is based on the
        explicit ``assigned_doctor_ids`` list (loaded from
        ``staff_doctor_assignments`` at auth time).  The legacy ``doctor_id``
        column remains as a compatibility fallback.  A missing assignment
        (empty list on the token) must fail closed — it must not grant
        unrestricted doctor access.  For all other roles, no doctor
        restriction applies.
        """
        if self.role in ("doctor", "assistant"):
            if not self.assigned_doctor_ids:
                return False
            return doctor_id in self.assigned_doctor_ids
        return True

    @property
    def is_super_admin(self) -> bool:
        """Platform administrator, derived from the explicit capability matrix.

        Q-1: this used to compare ``self.role == "super_admin"``.  It now asks
        the matrix, so the capability is enumerable, testable and revocable in
        one place instead of being hard-coded in every service.
        """
        from .permissions import check as perm_check
        return perm_check(PLATFORM_ADMIN, self.role)

    @property
    def can_cross_org(self) -> bool:
        """May this caller act outside its own organization? (Q-1)

        Only the platform administrator's ``platform.cross_org`` capability
        answers yes; no tenant-level role does.
        """
        from .permissions import check as perm_check
        return perm_check(PLATFORM_CROSS_ORG, self.role)

    @property
    def is_org_admin(self) -> bool:
        return self.role == "org_admin"

    @property
    def is_branch_admin(self) -> bool:
        return self.role == "branch_admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("receptionist", "branch_admin", "assistant")


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthContext:
    """FastAPI dependency: extract and validate current user from Bearer token."""
    if credentials is None:
        raise HTTPException(401, "authentication required")
    payload = decode_token(credentials.credentials)
    uid = payload.get("sub")
    org = payload.get("org")
    role = payload.get("role")
    if not uid or not org or not role:
        raise HTTPException(401, "invalid token claims")
    session = SessionFactory()
    try:
        user = session.query(StaffUser).filter(StaffUser.id == uid).first()
        if not user:
            raise HTTPException(403, "user not found")
        if user.status != "active":
            raise HTTPException(403, "account is not active")
        # PO-RBAC-01: load explicit doctor assignments for this staff member.
        assigned = _load_assigned_doctor_ids(session, uid)
        # Fall back to the legacy single doctor_id when no assignment rows exist,
        # so existing users created before this migration keep working.
        if not assigned and user.doctor_id:
            assigned = [user.doctor_id]
    finally:
        session.close()
    return AuthContext(
        user_id=uid, organization_id=org,
        branch_id=payload.get("branch"), role=role,
        username=user.username, locale=user.locale or "en",
        status=user.status or "active", token_payload=payload,
        doctor_id=user.doctor_id,
        assigned_doctor_ids=list(assigned),
    )
def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[AuthContext]:
    """Like get_current_user but returns None instead of raising on error."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        uid = payload.get("sub")
        org = payload.get("org")
        role = payload.get("role")
        if not uid or not org or not role:
            return None
        session = SessionFactory()
        try:
            user = session.query(StaffUser).filter(StaffUser.id == uid).first()
            if not user or user.status != "active":
                return None
            # PO-RBAC-01: load explicit doctor assignments for this staff member.
            assigned = _load_assigned_doctor_ids(session, uid)
            # Fall back to the legacy single doctor_id when no assignment rows exist.
            if not assigned and user.doctor_id:
                assigned = [user.doctor_id]
        finally:
            session.close()
        return AuthContext(
            user_id=uid, organization_id=org,
            branch_id=payload.get("branch"), role=role,
            username=user.username, locale=user.locale or "en",
            status=user.status or "active", token_payload=payload,
            doctor_id=user.doctor_id,
            assigned_doctor_ids=list(assigned),
        )
    except (jwt.PyJWTError, HTTPException):
        return None


def require_permission(resource: str):
    """Dependency factory: raise 403 if the authenticated user lacks a permission.

    Usage::

        @router.get("/patients")
        def list_patients(
            ...,
            auth: AuthContext = Depends(require_permission("patient.read")),
        ):
            ...
    """
    from .permissions import check as perm_check

    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if not perm_check(resource, auth.role):
            raise HTTPException(403, "insufficient permissions")
        return auth

    return _dependency


def _organization_of_branch(branch_id: str) -> Optional[str]:
    """Owning organization of *branch_id*, or ``None`` when it cannot be read.

    Used only to attribute a platform access event to the tenant it touched, so
    it must never raise: an audit-attribution lookup may not break the request.
    """
    session = SessionFactory()
    try:
        row = session.query(Branch).filter(Branch.id == branch_id).first()
        return row.organization_id if row else None
    except Exception:                                    # pragma: no cover
        return None
    finally:
        session.close()


def record_platform_access(auth: "AuthContext", target_org_id: str, *,
                          target_type: str = "organization",
                          target_id: Optional[str] = None,
                          branch_id: Optional[str] = None,
                          service: str = "platform") -> None:
    """Record one platform administrator cross-organization access (Q-1 §6).

    The row is written into the **target** organization's trail, so the tenant
    that owns the data can see that platform support touched it; the caller's own
    organization is preserved in ``after``.  Best effort: a failure to record is
    logged and never turned into an error, because the caller has already been
    authorized and the response must not change.
    """
    org_id = target_org_id or _organization_of_branch(branch_id or "")
    if not org_id:
        logger.warning(
            "platform access not recorded: no target organization for %s %s",
            target_type, target_id or branch_id or "?")
        return
    session = SessionFactory()
    try:
        record_audit(
            session, service=service, org_id=org_id,
            branch_id=branch_id or "",
            action="platform.cross_org.access",
            target_type=target_type,
            target_id=target_id or branch_id or org_id,
            actor_id=auth.user_id, actor_role=auth.role,
            after={"capability": PLATFORM_CROSS_ORG,
                   "actor_organization_id": auth.organization_id,
                   "target_organization_id": org_id},
            reason="platform administrator cross-organization access",
        )
        session.commit()
    except Exception:                                    # pragma: no cover
        session.rollback()
        logger.warning(
            "platform access audit row could not be written for %s %s",
            target_type, target_id or branch_id or org_id)
    finally:
        session.close()


def require_org_access(target_org_id: str, service: str = "platform"):
    """Dependency factory: refuse unless the user may act on target_org_id.

    The caller's own organization is the only one it may act on.  A different
    organization is allowed **only** for a caller holding the platform
    ``platform.cross_org`` capability (owner decision Q-1), and that access is
    written to the target organization's audit trail.

    Sequence 4 (WP3/WP8): a foreign organization is a **non-disclosing 404**,
    never 403.  ``.clinerules`` §3 forbids 403 here because it would confirm
    that the identifier exists in another tenant — an existence oracle.  The new
    Sequence 3 modules (``organization/notification_config.py``, queue recovery,
    PQT, DQDS) already answer 404; this helper now matches them.
    """
    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if auth.organization_id == target_org_id:
            return auth
        if not auth.can_cross_org:
            raise HTTPException(404, "not found")
        record_platform_access(auth, target_org_id, service=service)
        return auth
    return _dependency


def require_branch_access(target_branch_id: Optional[str], service: str = "platform"):
    """Dependency factory: refuse unless the user may act on target_branch.

    org_admin can access any branch in their org.  Branch-scoped users must match
    their token branch to target.  A caller from outside the branch is allowed
    **only** with the platform ``platform.cross_org`` capability (Q-1), and that
    access is audited.

    A **mismatched** branch is a non-disclosing 404 (never 403), for the same
    reason as :func:`require_org_access`.  A missing ``target_branch_id`` for a
    branch-scoped caller is not a tenant disclosure — it says something about
    the caller's own token — so it stays a 403 ("branch scope required").
    """
    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if auth.is_org_admin:
            return auth
        if target_branch_id and auth.branch_id != target_branch_id:
            if not auth.can_cross_org:
                raise HTTPException(404, "not found")
            record_platform_access(auth, "", target_type="branch",
                                   target_id=target_branch_id,
                                   branch_id=target_branch_id, service=service)
            return auth
        if not target_branch_id and auth.branch_id:
            raise HTTPException(403, "branch scope required")
        return auth
    return _dependency


def branch_accessible(auth: AuthContext, branch_id: Optional[str]) -> bool:
    """True if the authenticated actor may act on *branch_id*.

    ``org_admin`` and callers holding ``platform.cross_org`` may act on any
    branch; every other branch-scoped actor must match their token's branch.
    A ``None`` target imposes no branch constraint.

    The check is deliberate: a caller must never be able to reach another
    branch's data merely by supplying a branch identifier it is not
    authorized for.  Organization scope is enforced separately (the queried
    rows are already filtered to ``auth.organization_id``), so this helper
    only decides branch reachability within that tenant.
    """
    if branch_id is None:
        return True
    if auth.is_org_admin or auth.can_cross_org:
        return True
    return auth.branch_id == branch_id