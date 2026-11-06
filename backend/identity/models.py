"""AMSDP Identity & Access Service — Sprint 1 (D1/D4/D5/D6 approved).

Models and configuration.
"""

from pydantic import BaseModel
from typing import Optional
import os

_SECRET = os.environ.get("AMSDP_JWT_SECRET", "dev-synthetic-key-replace-in-prod")
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