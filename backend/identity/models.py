"""AMSDP Identity & Access Service — Pydantic models.

Shared DB model is in backend/common/models.py (StaffUser).
These are API-layer schemas.
"""

from pydantic import BaseModel
from typing import Optional
import os

# Secret and token configuration
# Production must always set AMSDP_JWT_SECRET.  The fallback is for
# local dev only; the application refuses to start without a secret
# in non-dev environments.
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
_TOKEN_HOURS = 12

class StaffUserCreate(BaseModel):
    organization_id: str
    branch_id: Optional[str] = None
    username: str
    password: str
    display_name: str
    role: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    locale: str = "en"

class StaffUserLogin(BaseModel):
    username: str
    password: str

class StaffUserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    locale: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class StaffUserResponse(BaseModel):
    id: str
    organization_id: str
    branch_id: Optional[str] = None
    username: str
    display_name: str
    role: str
    locale: str
    status: str

class TokenResponse(BaseModel):
    token: str
    user: StaffUserResponse

class PermissionCheck(BaseModel):
    user_id: str
    resource: str
    context: dict = {}


class StaffUserCreate(BaseModel):
    organization_id: str
    branch_id: Optional[str] = None
    doctor_id: Optional[str] = None
    # PO-RBAC-01: explicit doctor assignments (assistant may have multiple).
    # ``doctor_ids`` takes precedence over the legacy single ``doctor_id``.
    doctor_ids: Optional[list[str]] = None
    username: str
    password: str
    display_name: str
    role: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    locale: str = "en"

class StaffUserLogin(BaseModel):
    username: str
    password: str

class StaffUserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    locale: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    # PO-RBAC-01: replace the full set of assigned doctors when provided.
    doctor_ids: Optional[list[str]] = None
    doctor_id: Optional[str] = None

class StaffUserResponse(BaseModel):
    id: str
    organization_id: str
    branch_id: Optional[str] = None
    doctor_id: Optional[str] = None
    # PO-RBAC-01: all active doctor assignments for this staff member.
    doctor_ids: Optional[list[str]] = None
    username: str
    display_name: str
    role: str
    locale: str
    status: str

class TokenResponse(BaseModel):
    token: str
    user: StaffUserResponse

class PermissionCheck(BaseModel):
    user_id: str
    resource: str
    context: dict = {}