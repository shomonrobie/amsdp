"""AMSDP Organization Service — Sprint 2.

Manages organizations (tenants), branches, and platform-level settings.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Organization Service")
_orgs_db: dict[str, dict] = {}
_branches_db: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class OrgCreate(BaseModel):
    name: str
    code: str
    timezone: str = "Asia/Dhaka"
    locale: str = "bn"
    facility_type: str = "hospital"
    address: str = ""
    config: dict = {}

class OrgUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    status: Optional[str] = None

class BranchCreate(BaseModel):
    organization_id: str
    name: str
    code: str
    address: str = ""
    phone: Optional[str] = None
    config: dict = {}

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None

# ---------------------------------------------------------------------------
# Organization endpoints
# ---------------------------------------------------------------------------
@app.post("/api/v1/orgs", status_code=201)
def create_org(data: OrgCreate):
    org_id = str(uuid.uuid4())
    org = {"id": org_id, "name": data.name, "code": data.code,
           "timezone": data.timezone, "locale": data.locale,
           "facility_type": data.facility_type, "address": data.address,
           "config": data.config, "status": "active",
           "created_at": str(datetime.utcnow())}
    _orgs_db[org_id] = org
    return org

@app.get("/api/v1/orgs")
def list_orgs():
    return list(_orgs_db.values())

@app.get("/api/v1/orgs/{org_id}")
def get_org(org_id: str):
    org = _orgs_db.get(org_id)
    if not org: raise HTTPException(404, "organization not found")
    return org

@app.patch("/api/v1/orgs/{org_id}")
def update_org(org_id: str, data: OrgUpdate):
    org = _orgs_db.get(org_id)
    if not org: raise HTTPException(404)
    for field in ("name", "address", "timezone", "locale", "status"):
        val = getattr(data, field, None)
        if val is not None:
            org[field] = val
    return org

# ---------------------------------------------------------------------------
# Branch endpoints
# ---------------------------------------------------------------------------
@app.post("/api/v1/branches", status_code=201)
def create_branch(data: BranchCreate):
    if data.organization_id not in _orgs_db:
        raise HTTPException(404, "organization not found")
    branch_id = str(uuid.uuid4())
    branch = {"id": branch_id, "organization_id": data.organization_id,
              "name": data.name, "code": data.code, "address": data.address,
              "phone": data.phone, "config": data.config, "status": "active",
              "created_at": str(datetime.utcnow())}
    _branches_db[branch_id] = branch
    return branch

@app.get("/api/v1/orgs/{org_id}/branches")
def list_branches(org_id: str):
    if org_id not in _orgs_db:
        raise HTTPException(404, "organization not found")
    return [b for b in _branches_db.values() if b["organization_id"] == org_id]

@app.get("/api/v1/branches/{branch_id}")
def get_branch(branch_id: str):
    branch = _branches_db.get(branch_id)
    if not branch: raise HTTPException(404)
    return branch

@app.patch("/api/v1/branches/{branch_id}")
def update_branch(branch_id: str, data: BranchUpdate):
    branch = _branches_db.get(branch_id)
    if not branch: raise HTTPException(404)
    for field in ("name", "address", "phone", "status"):
        val = getattr(data, field, None)
        if val is not None:
            branch[field] = val
    return branch