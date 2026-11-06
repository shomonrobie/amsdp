"""AMSDP Identity & Access Service — FastAPI application."""

from fastapi import FastAPI, HTTPException, Header
from datetime import datetime, timedelta
import uuid, bcrypt, jwt

from models import (
    StaffUserCreate, StaffUserLogin, StaffUserUpdate,
    StaffUserResponse, TokenResponse, PermissionCheck,
    _SECRET, _ALGO, _TOKEN_HOURS,
)
from permissions import check as perm_check, PERMISSIONS

app = FastAPI(title="AMSDP Identity & Access Service")
_users_db: dict[str, dict] = {}

# Register additional route handlers
import routes  # noqa

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/v1/staff/users", status_code=201)
def create_staff_user(data: StaffUserCreate):
    if not data.organization_id or not data.role:
        raise HTTPException(422, "organization_id and role are required")
    if data.role not in PERMISSIONS:
        raise HTTPException(422, f"unknown role: {data.role}")
    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    record = {
        "id": user_id, "organization_id": data.organization_id,
        "branch_id": data.branch_id, "username": data.username,
        "password_hash": pw_hash, "display_name": data.display_name,
        "role": data.role, "email": data.email, "mobile": data.mobile,
        "locale": data.locale, "status": "active",
        "created_at": str(datetime.utcnow()),
    }
    _users_db[user_id] = record
    return {"user_id": user_id, "display_name": data.display_name, "role": data.role}

@app.post("/api/v1/staff/login", response_model=TokenResponse)
def staff_login(data: StaffUserLogin):
    for rec in _users_db.values():
        if rec["username"] == data.username:
            if not bcrypt.checkpw(data.password.encode(), rec["password_hash"].encode()):
                raise HTTPException(401, "invalid credentials")
            if rec["status"] != "active":
                raise HTTPException(403, "account is not active")
            payload = {
                "sub": rec["id"], "org": rec["organization_id"],
                "branch": rec.get("branch_id"), "role": rec["role"],
                "exp": int((datetime.utcnow() + timedelta(hours=_TOKEN_HOURS)).timestamp()),
            }
            token = jwt.encode(payload, _SECRET, algorithm=_ALGO)
            return TokenResponse(token=token, user=StaffUserResponse(
                id=rec["id"], organization_id=rec["organization_id"],
                branch_id=rec.get("branch_id"), username=rec["username"],
                display_name=rec["display_name"], role=rec["role"],
                locale=rec["locale"], status=rec["status"],
            ))
    raise HTTPException(401, "invalid credentials")

@app.get("/api/v1/staff/validate")
def validate_token(authorization: str = Header("")):
    token = authorization.replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGO])
        user = _users_db.get(payload["sub"])
        if not user or user["status"] != "active":
            raise HTTPException(403, "user not found or inactive")
        return {"valid": True, "user_id": payload["sub"],
                "organization_id": payload["org"],
                "branch_id": payload.get("branch"),
                "role": payload["role"], "locale": user["locale"]}
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token")