"""Additional endpoints — user listing, update, permission check."""

from fastapi import HTTPException
from typing import Optional

from models import StaffUserUpdate, StaffUserResponse, PermissionCheck
from permissions import PERMISSIONS, check as perm_check

# Import the shared DB reference from main
from main import _users_db, app

@app.get("/api/v1/staff/users")
def list_staff(organization_id: Optional[str] = None):
    users = list(_users_db.values())
    if organization_id:
        users = [u for u in users if u["organization_id"] == organization_id]
    return [StaffUserResponse(
        id=u["id"], organization_id=u["organization_id"],
        branch_id=u.get("branch_id"), username=u["username"],
        display_name=u["display_name"], role=u["role"],
        locale=u["locale"], status=u["status"],
    ) for u in users]

@app.get("/api/v1/staff/users/{user_id}")
def get_staff_user(user_id: str):
    user = _users_db.get(user_id)
    if not user: raise HTTPException(404)
    return StaffUserResponse(
        id=user["id"], organization_id=user["organization_id"],
        branch_id=user.get("branch_id"), username=user["username"],
        display_name=user["display_name"], role=user["role"],
        locale=user["locale"], status=user["status"],
    )

@app.patch("/api/v1/staff/users/{user_id}")
def update_staff_user(user_id: str, data: StaffUserUpdate):
    user = _users_db.get(user_id)
    if not user: raise HTTPException(404)
    if data.display_name is not None: user["display_name"] = data.display_name
    if data.email is not None: user["email"] = data.email
    if data.mobile is not None: user["mobile"] = data.mobile
    if data.locale is not None: user["locale"] = data.locale
    if data.role is not None: user["role"] = data.role
    if data.status is not None: user["status"] = data.status
    return StaffUserResponse(**{k: user[k] for k in StaffUserResponse.__fields__})

@app.post("/api/v1/staff/check-permission")
def check_permission(data: PermissionCheck):
    user = _users_db.get(data.user_id)
    if not user: raise HTTPException(404, "user not found")
    authorized = perm_check(data.resource, user["role"])
    return {"authorized": authorized}