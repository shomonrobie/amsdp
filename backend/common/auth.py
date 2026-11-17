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

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .audit import record_audit
from .database import SessionFactory
from .models import Branch, StaffUser

logger = logging.getLogger(__name__)

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
                 locale: str, status: str, token_payload: dict):
        self.user_id = user_id
        self.organization_id = organization_id
        self.branch_id = branch_id
        self.role = role
        self.username = username
        self.locale = locale
        self.status = status
        self.token_payload = token_payload

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
    finally:
        session.close()
    return AuthContext(
        user_id=uid, organization_id=org,
        branch_id=payload.get("branch"), role=role,
        username=user.username, locale=user.locale or "en",
        status=user.status or "active", token_payload=payload,
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
        finally:
            session.close()
        return AuthContext(
            user_id=uid, organization_id=org,
            branch_id=payload.get("branch"), role=role,
            username=user.username, locale=user.locale or "en",
            status=user.status or "active", token_payload=payload,
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