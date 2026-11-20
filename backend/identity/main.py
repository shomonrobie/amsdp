"""AMSDP Identity & Access Service — FastAPI application.

PostgreSQL-backed using the shared common.models.StaffUser model.
"""

import logging
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid, bcrypt, jwt
import sqlalchemy as sa

from models import (
    StaffUserCreate, StaffUserLogin, StaffUserUpdate,
    StaffUserResponse, TokenResponse, PermissionCheck,
    _SECRET, _ALGO, _TOKEN_HOURS,
)
from permissions import check as perm_check, PERMISSIONS, can_grant_role

from common.database import SessionFactory
from common.models import StaffUser
from common.auth import AuthContext, get_current_user, require_permission
from common.audit import record_audit
from common import login_throttle
from common.health import install_health
from common.denial_audit import install_denial_audit

# PO-RBAC-01: load active doctor assignments for a staff member.
def _assigned_doctor_ids(staff_user_id: str) -> Optional[list[str]]:
    """Return the list of actively assigned doctor IDs for a staff member.

    Return contract:
      - None: the ``staff_doctor_assignments`` table does not exist yet
        (pre-migration).  Callers may fall back to legacy ``StaffUser.doctor_id``.
      - list[str]: the table exists; may be an empty list meaning "no active
        assignments".  Callers must NOT fall back to legacy ``doctor_id``.

    If the table exists but the query fails, the exception propagates so the
    caller fails closed rather than silently falling back to legacy
    ``StaffUser.doctor_id`` (which could restore access after revocation).
    """
    session = SessionFactory()
    try:
        from sqlalchemy import inspect as sa_inspect
        if not sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
            return None
        rows = session.execute(
            sa.text("""
                SELECT doctor_id FROM staff_doctor_assignments
                WHERE staff_user_id = :uid AND status = 'active'
            """), {"uid": staff_user_id}
        ).scalars().all()
        return list(rows)
    finally:
        session.close()

logger = logging.getLogger(__name__)

app = FastAPI(title="AMSDP Identity & Access Service")
install_health(app, "identity")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "identity")



from routes import router as identity_router  # noqa
app.include_router(identity_router)


def _user_to_response(user: StaffUser) -> StaffUserResponse:
    assigned = _assigned_doctor_ids(user.id)
    # Fall back to legacy single doctor_id only when the table does not exist
    # yet (pre-migration).  When the table exists but no active rows are found
    # (assigned == []), legacy doctor_id must NOT be used — an explicit
    # revocation must remain effective.
    if assigned is None and user.doctor_id:
        assigned = [user.doctor_id]
    return StaffUserResponse(
        id=user.id,
        organization_id=user.organization_id,
        branch_id=user.branch_id,
        doctor_id=user.doctor_id or None,
        # PO-RBAC-01: all active doctor assignments for this staff member.
        # ``assigned`` is None only when the assignment table does not exist
        # yet (pre-migration); the API always answers with a list.
        doctor_ids=list(assigned or []),
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        locale=user.locale or "en",
        status=user.status or "active",
    )


def _get_user_or_404(session, user_id: str) -> StaffUser:
    user = session.query(StaffUser).filter(StaffUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "user not found")
    return user


# ---------------------------------------------------------------------------
# Login throttling (Sequence 4, WP3; made durable for SEQ4-THROTTLE-D1)
# ---------------------------------------------------------------------------
# A sliding-window limiter keyed on (client IP, username).  Scope is deliberate:
#
# * Per (IP, username), not per IP — one noisy user cannot lock out a shared
#   office NAT, and one attacker IP cannot spray every account unnoticed.
# * No account lockout.  Locking an account on failed attempts converts this
#   control into a denial-of-service tool against a known username.  We only
#   slow the attacker down and keep answering 401.
# * A *successful* login clears the bucket, so legitimate users recover
#   immediately instead of waiting out the window.
# * State is **in PostgreSQL** (``login_attempts``), not in this process, so the
#   window is shared by every uvicorn worker and every replica and survives a
#   restart.  Sequence 4 finding SEQ4-THROTTLE-D1 was exactly this gap: with N
#   workers the old in-process dict handed an attacker N windows.  See
#   ``common/login_throttle.py`` for the mechanism (advisory-locked count).
_LOGIN_WINDOW_SECONDS = login_throttle.default_window_seconds()
_LOGIN_MAX_ATTEMPTS = login_throttle.default_max_attempts()


def _login_bucket_key(request: Request, username: str) -> Tuple[str, str]:
    client = getattr(request, "client", None)
    host = getattr(client, "host", None) or "unknown"
    # Cap the username so an oversized body cannot grow the bucket key unbounded.
    return login_throttle.bucket_key(host, username)


def _login_throttle(session, request: Request, username: str) -> None:
    """Record an attempt and refuse with 429 once the window is saturated.

    Fails **open** (and loudly) if the throttle store itself is unavailable: the
    credential check that follows reads the same database, so an outage cannot
    turn into an authentication bypass, and refusing every login on a throttle
    error would be a self-inflicted denial of service.
    """
    ip, user = _login_bucket_key(request, username)
    try:
        login_throttle.record_attempt(
            session, ip, user,
            max_attempts=_LOGIN_MAX_ATTEMPTS,
            window_seconds=_LOGIN_WINDOW_SECONDS,
        )
    except HTTPException:
        raise
    except Exception:
        # No IP, no username, no credential material in the log line.
        logger.warning("login throttle unavailable; attempt allowed "
                       "(logins still require a valid credential)")


def _login_succeeded(session, request: Request, username: str) -> None:
    ip, user = _login_bucket_key(request, username)
    try:
        login_throttle.clear_bucket(session, ip, user)
    except Exception:                      # pragma: no cover - defensive
        logger.warning("login throttle could not be cleared after success")


def _reset_login_throttle() -> None:
    """Test hook: forget every stored login attempt."""
    session = SessionFactory()
    try:
        login_throttle.reset(session)
    finally:
        session.close()


@app.post("/api/v1/staff/users", status_code=201)
def create_staff_user(
    data: StaffUserCreate,
    auth: AuthContext = Depends(require_permission("staff.manage")),
):
    if not data.organization_id or not data.role:
        raise HTTPException(422, "organization_id and role are required")
    if data.role not in PERMISSIONS:
        raise HTTPException(422, f"unknown role: {data.role}")
    # Enforce org scope: non-super-admin can only create users in their own org
    if not auth.is_super_admin and data.organization_id != auth.organization_id:
        raise HTTPException(422, "cannot create user in a different organization")
    # PO-RBAC-03: prevent self-escalation — a caller cannot create a user
    # with a role at or above their own level (super_admin excepted).
    if not auth.is_super_admin and not can_grant_role(auth.role, data.role):
        raise HTTPException(403, "cannot grant a role at or above your own level")

    # PO-RBAC-01: resolve the doctor assignment list.
    # ``doctor_ids`` (list) takes precedence; legacy ``doctor_id`` is a fallback.
    doctor_ids = list(data.doctor_ids) if data.doctor_ids else (
        [data.doctor_id] if data.doctor_id else []
    )
    # Validate every doctor: exists, active, same organization.
    from common.models import Doctor, StaffDoctorAssignment
    session = SessionFactory()
    try:
        for did in doctor_ids:
            doc = session.query(Doctor).filter(
                Doctor.id == did,
                Doctor.organization_id == data.organization_id,
                Doctor.status == "active",
            ).first()
            if not doc:
                raise HTTPException(
                    422, f"doctor_id {did} must reference an active doctor "
                         f"in the same organization")
    finally:
        session.close()

    pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    session = SessionFactory()
    try:
        # Legacy single field: keep the first assigned doctor for compatibility.
        legacy_doctor_id = doctor_ids[0] if doctor_ids else None
        user = StaffUser(
            id=str(uuid.uuid4()),
            organization_id=data.organization_id,
            branch_id=data.branch_id,
            doctor_id=legacy_doctor_id,
            username=data.username,
            password_hash=pw_hash,
            display_name=data.display_name,
            role=data.role,
            email=data.email,
            mobile=data.mobile,
            locale=data.locale,
            status="active",
        )
        session.add(user)
        session.flush()
        # Create explicit assignment rows for every validated doctor.
        # Resilient to missing table (pre-migration): check first.
        from sqlalchemy import inspect as sa_inspect
        if sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
            for did in doctor_ids:
                session.add(StaffDoctorAssignment(
                    id=str(uuid.uuid4()),
                    staff_user_id=user.id,
                    doctor_id=did,
                    organization_id=data.organization_id,
                    status="active",
                ))
        record_audit(session, service="identity", org_id=user.organization_id,
            action="staff.created", target_type="staff_user", target_id=user.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=user.branch_id or "",
            after={"username": user.username, "display_name": user.display_name,
                   "role": user.role, "status": user.status,
                   "doctor_ids": doctor_ids})
        session.commit()
        return {"user_id": user.id, "display_name": user.display_name, "role": user.role}
    except Exception as exc:
        session.rollback()
        # Duplicate username is a client error, not a server fault
        if "duplicate key" in str(exc) and "username" in str(exc):
            raise HTTPException(422, "username already exists")
        raise
    finally:
        session.close()


@app.post("/api/v1/staff/login", response_model=TokenResponse)
def staff_login(data: StaffUserLogin, request: Request):
    """Authenticate a staff user.

    Sequence 4 (WP3): login attempts are throttled per (client IP, username) so a
    public deployment cannot be password-sprayed.  The window is generous
    (default 20/min, ``AMSDP_LOGIN_MAX_ATTEMPTS`` / ``AMSDP_LOGIN_WINDOW_SECONDS``)
    and a *successful* login clears the bucket, so a shared NAT or a demo machine
    is never locked out.  No account lockout is applied — that would let an
    attacker deny service to a known username.  The counters live in the
    database, so the limit is identical across every worker and replica
    (SEQ4-THROTTLE-D1).
    """
    session = SessionFactory()
    try:
        _login_throttle(session, request, data.username)
        user = session.query(StaffUser).filter(
            StaffUser.username == data.username
        ).first()
        if not user:
            raise HTTPException(401, "invalid credentials")
        if not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
            raise HTTPException(401, "invalid credentials")
        if user.status != "active":
            raise HTTPException(403, "account is not active")
        _login_succeeded(session, request, data.username)

        payload = {
            "sub": user.id, "org": user.organization_id,
            "branch": user.branch_id, "role": user.role,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=_TOKEN_HOURS)).timestamp()),
        }
        token = jwt.encode(payload, _SECRET, algorithm=_ALGO)
        return TokenResponse(token=token, user=_user_to_response(user))
    finally:
        session.close()


@app.get("/api/v1/staff/validate")
def validate_token(authorization: str = Header("")):
    token = authorization.replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGO])
        session = SessionFactory()
        try:
            user = session.query(StaffUser).filter(
                StaffUser.id == payload["sub"]
            ).first()
            if not user or user.status != "active":
                raise HTTPException(403, "user not found or inactive")
            return {
                "valid": True, "user_id": payload["sub"],
                "organization_id": payload["org"],
                "branch_id": payload.get("branch"),
                "role": payload["role"], "locale": user.locale,
            }
        finally:
            session.close()
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token")
