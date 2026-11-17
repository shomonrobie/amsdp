"""Write the DB-backed identity main.py."""
import os

content = r'''"""AMSDP Identity & Access Service FastAPI application.

PostgreSQL-backed using the shared common.models.StaffUser model.
"""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Header
import bcrypt
import jwt

from models import (
    StaffUserCreate, StaffUserLogin, StaffUserUpdate,
    StaffUserResponse, TokenResponse, PermissionCheck,
    _SECRET, _ALGO, _TOKEN_HOURS,
)
from permissions import check as perm_check, PERMISSIONS
from common.database import SessionFactory
from common.models import StaffUser

app = FastAPI(title="AMSDP Identity & Access Service")

import routes  # noqa


def _user_to_response(user):
    return StaffUserResponse(
        id=user.id, organization_id=user.organization_id,
        branch_id=user.branch_id, username=user.username,
        display_name=user.display_name, role=user.role,
        locale=user.locale or "en", status=user.status or "active",
    )


def _get_user_or_404(session, user_id):
    user = session.query(StaffUser).filter(StaffUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "user not found")
    return user


@app.post("/api/v1/staff/users", status_code=201)
def create_staff_user(data):
    if not data.organization_id or not data.role:
        raise HTTPException(422, "organization_id and role are required")
    if data.role not in PERMISSIONS:
        raise HTTPException(422, "unknown role: %s" % data.role)
    pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    session = SessionFactory()
    try:
        user = StaffUser(
            id=str(uuid.uuid4()),
            organization_id=data.organization_id,
            branch_id=data.branch_id,
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
        session.commit()
        return {"user_id": user.id, "display_name": user.display_name, "role": user.role}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.post("/api/v1/staff/login", response_model=StaffUserResponse)
def staff_login(data):
    session = SessionFactory()
    try:
        user = session.query(StaffUser).filter(
            StaffUser.username == data.username
        ).first()
        if not user:
            raise HTTPException(401, "invalid credentials")
        if not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
            raise HTTPException(401, "invalid credentials")
        if user.status != "active":
            raise HTTPException(403, "account is not active")
        payload = {
            "sub": user.id, "org": user.organization_id,
            "branch": user.branch_id, "role": user.role,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=_TOKEN_HOURS)).timestamp()),
        }
        token = jwt.encode(payload, _SECRET, algorithm=_ALGO)
        return {"token": token, "user": _user_to_response(user)}
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
'''

path = '/home/shomonrobie/amsdp/backend/identity/main.py'
with open(path, 'w') as f:
    f.write(content)
print('Written %d bytes to %s' % (len(content), path))
