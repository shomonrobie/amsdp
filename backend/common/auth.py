"""AMSDP Shared Security — Authentication, RBAC, tenant/branch isolation.

FastAPI dependencies for endpoint protection.
"""

import os
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .database import SessionFactory
from .models import StaffUser


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
        return self.role == "super_admin"

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


def require_org_access(target_org_id: str):
    """Dependency factory: refuse unless the user may act on target_org_id.

    super_admin may access any org.  All other roles must match.

    Sequence 4 (WP3/WP8): a foreign organization is a **non-disclosing 404**,
    never 403.  ``.clinerules`` §3 forbids 403 here because it would confirm
    that the identifier exists in another tenant — an existence oracle.  The new
    Sequence 3 modules (``organization/notification_config.py``, queue recovery,
    PQT, DQDS) already answer 404; this helper now matches them.
    """
    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if auth.is_super_admin:
            return auth
        if auth.organization_id != target_org_id:
            raise HTTPException(404, "not found")
        return auth
    return _dependency


def require_branch_access(target_branch_id: Optional[str]):
    """Dependency factory: refuse unless the user may act on target_branch.

    super_admin and org_admin can access any branch in their org.
    Branch-scoped users must match their token branch to target.

    A **mismatched** branch is a non-disclosing 404 (never 403), for the same
    reason as :func:`require_org_access`.  A missing ``target_branch_id`` for a
    branch-scoped caller is not a tenant disclosure — it says something about
    the caller's own token — so it stays a 403 ("branch scope required").
    """
    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if auth.is_super_admin or auth.is_org_admin:
            return auth
        if target_branch_id and auth.branch_id != target_branch_id:
            raise HTTPException(404, "not found")
        if not target_branch_id and auth.branch_id:
            raise HTTPException(403, "branch scope required")
        return auth
    return _dependency