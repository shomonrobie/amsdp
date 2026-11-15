"""AMSDP Organization & Branch Service — BR §3–§5.

PostgreSQL-backed with auth/authorization via common infrastructure.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from common.database import SessionFactory
from common.models import Organization, Branch
from common.auth import (
    AuthContext, get_current_user,
    require_permission, require_org_access,
)
from common.audit import record_audit
from common.health import install_health
from common.denial_audit import install_denial_audit

app = FastAPI(title="AMSDP Organization Service")
install_health(app, "organization")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "organization")

# Sequence 3 — organization notification settings (BR §35–§36, PQV §D).
try:
    from .notification_config import router as notification_router
except ImportError:
    from notification_config import router as notification_router
app.include_router(notification_router)

# AMSDP-FACILITY-DOCTOR-01 — facility hierarchy: floors, departments, chambers
# and the organization's speciality catalogue.  Mounted here because every one
# of those entities belongs to a branch or an organization.
try:
    from .facility import router as facility_router
except ImportError:
    from facility import router as facility_router
app.include_router(facility_router)



# ---------------------------------------------------------------------------
# Pydantic schemas
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

class OrgResponse(BaseModel):
    id: str; name: str; code: str; timezone: str; locale: str
    facility_type: str; address: str; status: str; created_at: str

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

class BranchResponse(BaseModel):
    id: str; organization_id: str; name: str; code: str
    address: str; phone: Optional[str]; status: str; created_at: str


def _org_to_dict(o):
    return OrgResponse(id=o.id, name=o.name, code=o.code,
        timezone=o.timezone, locale=o.locale,
        facility_type=o.facility_type, address=o.address or "",
        status=o.status or "active",
        created_at=str(o.created_at) if o.created_at else "").dict()

def _branch_to_dict(b):
    return BranchResponse(id=b.id, organization_id=b.organization_id,
        name=b.name, code=b.code, address=b.address or "",
        phone=b.phone, status=b.status or "active",
        created_at=str(b.created_at) if b.created_at else "").dict()


# ---------------------------------------------------------------------------
# Organization endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/orgs", status_code=201)
def create_org(
    data: OrgCreate,
    auth: AuthContext = Depends(require_permission("org.create")),
):
    session = SessionFactory()
    try:
        import uuid
        org = Organization(id=str(uuid.uuid4()), **data.dict())
        session.add(org)
        session.flush()
        record_audit(session, service="organization", org_id=org.id,
            action="organization.created", target_type="organization", target_id=org.id,
            actor_id=auth.user_id, actor_role=auth.role,
            after={"name": org.name, "code": org.code, "facility_type": org.facility_type})
        session.commit()
        return _org_to_dict(org)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/v1/orgs")
def list_orgs(
    auth: AuthContext = Depends(require_permission("org.read")),
):
    session = SessionFactory()
    try:
        q = session.query(Organization)
        if not auth.is_super_admin:
            q = q.filter(Organization.id == auth.organization_id)
        return [_org_to_dict(o) for o in q.all()]
    finally:
        session.close()


@app.get("/api/v1/orgs/{org_id}")
def get_org(
    org_id: str,
    auth: AuthContext = Depends(require_permission("org.read")),
):
    require_org_access(org_id)(auth)
    session = SessionFactory()
    try:
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(404)
        return _org_to_dict(org)
    finally:
        session.close()


@app.patch("/api/v1/orgs/{org_id}")
def update_org(
    org_id: str, data: OrgUpdate,
    auth: AuthContext = Depends(require_permission("org.manage")),
):
    require_org_access(org_id)(auth)
    session = SessionFactory()
    try:
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(404)
        for field in ("name", "address", "timezone", "locale", "status"):
            val = getattr(data, field, None)
            if val is not None:
                setattr(org, field, val)
        record_audit(session, service="organization", org_id=org.id,
            action="organization.updated", target_type="organization", target_id=org.id,
            actor_id=auth.user_id, actor_role=auth.role,
            before={"name": org.name, "status": org.status},
            after={"name": org.name, "status": org.status})
        session.commit()
        return _org_to_dict(org)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ---------------------------------------------------------------------------
# Branch endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/branches", status_code=201)
def create_branch(
    data: BranchCreate,
    auth: AuthContext = Depends(require_permission("branch.manage")),
):
    require_org_access(data.organization_id)(auth)
    session = SessionFactory()
    try:
        import uuid
        org = session.query(Organization).filter(
            Organization.id == data.organization_id).first()
        if not org:
            raise HTTPException(404, "organization not found")
        branch = Branch(id=str(uuid.uuid4()), **data.dict())
        session.add(branch)
        session.flush()
        record_audit(session, service="organization", org_id=data.organization_id,
            action="branch.created", target_type="branch", target_id=branch.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=branch.id,
            after={"name": branch.name, "code": branch.code})
        session.commit()
        return _branch_to_dict(branch)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/v1/orgs/{org_id}/branches")
def list_branches(
    org_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    require_org_access(org_id)(auth)
    session = SessionFactory()
    try:
        branches = session.query(Branch).filter(
            Branch.organization_id == org_id).all()
        return [_branch_to_dict(b) for b in branches]
    finally:
        session.close()


@app.get("/api/v1/branches/{branch_id}")
def get_branch(
    branch_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        branch = session.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise HTTPException(404)
        require_org_access(branch.organization_id)(auth)
        return _branch_to_dict(branch)
    finally:
        session.close()


@app.patch("/api/v1/branches/{branch_id}")
def update_branch(
    branch_id: str, data: BranchUpdate,
    auth: AuthContext = Depends(require_permission("branch.manage")),
):
    session = SessionFactory()
    try:
        branch = session.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise HTTPException(404)
        require_org_access(branch.organization_id)(auth)
        for field in ("name", "address", "phone", "status"):
            val = getattr(data, field, None)
            if val is not None:
                setattr(branch, field, val)
        record_audit(session, service="organization", org_id=branch.organization_id,
            action="branch.updated", target_type="branch", target_id=branch.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=branch.id,
            before={"name": branch.name, "status": branch.status},
            after={"name": branch.name, "status": branch.status})
        session.commit()
        return _branch_to_dict(branch)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Branch context endpoint — branches the authenticated user may access
# ---------------------------------------------------------------------------

@app.get("/api/v1/me/branches")
def my_branches(auth: AuthContext = Depends(get_current_user)):
    """Branches the authenticated user may switch to.

    - super_admin / org_admin: every branch in their org.
    - branch-scoped roles (receptionist, branch_admin, assistant, doctor):
      only the branch stamped in their token.

    The client must still re-send branch_id on every call; every backend
    route enforces require_branch_access independently (never trust the UI).
    """
    session = SessionFactory()
    try:
        if auth.is_super_admin or auth.is_org_admin:
            branches = session.query(Branch).filter(
                Branch.organization_id == auth.organization_id).all()
        elif auth.branch_id:
            branches = session.query(Branch).filter(
                Branch.id == auth.branch_id,
                Branch.organization_id == auth.organization_id).all()
        else:
            branches = []
        return [_branch_to_dict(b) for b in branches]
    finally:
        session.close()