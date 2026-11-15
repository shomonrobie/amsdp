"""AMSDP Facility Service — floors, departments, rooms, specialities.

AMSDP-FACILITY-DOCTOR-01.  Mounted on the Organization service because the
facility hierarchy *is* organization configuration: a floor, a department or a
room belongs to a branch, and a branch belongs to an organization.

Design rules enforced here
--------------------------
1. **Tenant isolation is server-side.**  The organization is always read from
   the branch row (itself read from the token-visible org), never from the
   request body.  A branch or room from another organization is a
   non-disclosing **404** (``require_org_access``), never a 403.
2. **Branch scope matters.**  ``require_branch_access`` runs in addition, so a
   receptionist token stamped with branch A cannot read branch B's rooms.
3. **Parent integrity.**  A room may reference a floor and/or department only
   if that floor/department belongs to *the same branch* — otherwise the
   facility tree would describe a room on a floor of another clinic.
4. **Nothing is deleted.**  ``DELETE`` retires (``status="inactive"``) so
   schedules and appointments keep resolving the location they were booked
   into.  Retiring a floor/department that still has active rooms is refused
   (409) — the operator must move the rooms first.
5. **Codes are unique per branch** (``uq_*_branch_code``), compared
   case-insensitively, and normalised to upper case.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from common.database import SessionFactory
from common.models import (
    Branch, FacilityDepartment, FacilityFloor, FacilityRoom, ScheduleSession,
    Specialty,
)
from common.auth import (
    AuthContext, require_branch_access, require_org_access, require_permission,
)
from common.audit import record_audit

router = APIRouter()

SERVICE = "organization"
CODE_MAX = 40
NAME_MAX = 120
ROOM_TYPES = ("consultation", "procedure", "ward", "diagnostic", "other")
STATUSES = ("active", "inactive")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class FloorCreate(BaseModel):
    name: str
    code: Optional[str] = None
    level: Optional[int] = None
    description: str = ""


class FacilityUpdate(BaseModel):
    """Shared patch body for floors/departments/rooms.

    Only the fields present are applied, so the same class serves all three
    resources and a partial update can never blank a column by omission.
    """
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None


class RoomCreate(BaseModel):
    name: str
    code: Optional[str] = None
    floor_id: Optional[str] = None
    department_id: Optional[str] = None
    room_type: str = "consultation"
    capacity: Optional[int] = None
    description: str = ""


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    floor_id: Optional[str] = None
    department_id: Optional[str] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SpecialtyCreate(BaseModel):
    code: Optional[str] = None
    name_en: str
    name_bn: str = ""
    sort_order: int = 0


class SpecialtyUpdate(BaseModel):
    code: Optional[str] = None
    name_en: Optional[str] = None
    name_bn: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_CODE_ALLOWED = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"


def _clean_name(value, label: str = "name") -> str:
    name = (value or "").strip()
    if not name:
        raise HTTPException(422, f"{label} is required")
    if len(name) > NAME_MAX:
        raise HTTPException(422, f"{label} must be at most {NAME_MAX} characters")
    return name


def _clean_code(value, fallback: str = "") -> str:
    """Normalise a code to upper case, or derive one from *fallback* (a name).

    Derivation keeps the operator flow short ("Ground Floor" → ``GROUND-FLOOR``)
    while the stored value stays a stable, unique, machine-safe key.
    """
    raw = (value or "").strip()
    if not raw:
        raw = fallback
    code = "".join(
        c for c in raw.upper().replace(" ", "-") if c in _CODE_ALLOWED)
    code = code.strip("-._")
    if not code:
        raise HTTPException(422, "code is required")
    if len(code) > CODE_MAX:
        raise HTTPException(422, f"code must be at most {CODE_MAX} characters")
    return code


def _clean_status(value) -> Optional[str]:
    if value is None:
        return None
    status = (value or "").strip().lower()
    if status not in STATUSES:
        raise HTTPException(422, f"status must be one of {', '.join(STATUSES)}")
    return status


def _branch_or_404(session, branch_id: str) -> Branch:
    branch = session.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        # A branch in another tenant is indistinguishable from a missing one.
        raise HTTPException(404, "not found")
    return branch


def _scoped_branch(session, branch_id: str, auth: AuthContext) -> Branch:
    """Load *branch_id* and enforce org + branch scope for *auth*."""
    branch = _branch_or_404(session, branch_id)
    require_org_access(branch.organization_id, service=SERVICE)(auth)
    require_branch_access(branch.id, service=SERVICE)(auth)
    return branch


def _assert_same_branch(session, branch_id: str, floor_id, department_id):
    """A room's floor/department must belong to the room's own branch."""
    if floor_id:
        floor = session.query(FacilityFloor).filter(
            FacilityFloor.id == floor_id).first()
        if not floor or floor.branch_id != branch_id:
            raise HTTPException(422, "floor does not belong to this branch")
    if department_id:
        dept = session.query(FacilityDepartment).filter(
            FacilityDepartment.id == department_id).first()
        if not dept or dept.branch_id != branch_id:
            raise HTTPException(422, "department does not belong to this branch")


def _code_taken(session, model, branch_id: str, code: str, exclude_id=None) -> bool:
    query = session.query(model).filter(
        model.branch_id == branch_id, model.code == code)
    if exclude_id:
        query = query.filter(model.id != exclude_id)
    return session.query(query.exists()).scalar()


def _audit(session, auth: AuthContext, action: str, target_type: str,
           target_id: str, org_id: str, branch_id: Optional[str] = None,
           before=None, after=None) -> None:
    record_audit(session, service=SERVICE, org_id=org_id, branch_id=branch_id,
                 action=action, target_type=target_type, target_id=target_id,
                 actor_id=auth.user_id, actor_role=auth.role,
                 before=before, after=after)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _floor_to_dict(f: FacilityFloor) -> dict:
    return {"id": f.id, "organization_id": f.organization_id,
            "branch_id": f.branch_id, "name": f.name, "code": f.code,
            "level": f.level, "description": f.description or "",
            "status": f.status or "active",
            "created_at": str(f.created_at) if f.created_at else ""}


def _department_to_dict(d: FacilityDepartment) -> dict:
    return {"id": d.id, "organization_id": d.organization_id,
            "branch_id": d.branch_id, "name": d.name, "code": d.code,
            "description": d.description or "",
            "status": d.status or "active",
            "created_at": str(d.created_at) if d.created_at else ""}


def _room_to_dict(r: FacilityRoom) -> dict:
    return {"id": r.id, "organization_id": r.organization_id,
            "branch_id": r.branch_id, "name": r.name, "code": r.code,
            "floor_id": r.floor_id,
            "floor_name": r.floor.name if r.floor else None,
            "department_id": r.department_id,
            "department_name": r.department.name if r.department else None,
            "room_type": r.room_type or "consultation",
            "capacity": r.capacity, "description": r.description or "",
            "status": r.status or "active",
            "created_at": str(r.created_at) if r.created_at else ""}


def _specialty_to_dict(s: Specialty) -> dict:
    return {"id": s.id, "organization_id": s.organization_id, "code": s.code,
            "name_en": s.name_en, "name_bn": s.name_bn or "",
            "sort_order": s.sort_order or 0, "status": s.status or "active"}


def _active_room_count(session, branch_id: str, floor_id=None,
                       department_id=None) -> int:
    query = session.query(FacilityRoom).filter(
        FacilityRoom.branch_id == branch_id,
        FacilityRoom.status == "active")
    if floor_id:
        query = query.filter(FacilityRoom.floor_id == floor_id)
    if department_id:
        query = query.filter(FacilityRoom.department_id == department_id)
    return query.count()


# ---------------------------------------------------------------------------
# Floors
# ---------------------------------------------------------------------------

@router.get("/api/v1/branches/{branch_id}/floors")
def list_floors(
    branch_id: str,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_permission("facility.read")),
):
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        query = session.query(FacilityFloor).filter(
            FacilityFloor.branch_id == branch.id)
        if not include_inactive:
            query = query.filter(FacilityFloor.status == "active")
        return [_floor_to_dict(f) for f in query.order_by(FacilityFloor.name).all()]
    finally:
        session.close()


@router.post("/api/v1/branches/{branch_id}/floors", status_code=201)
def create_floor(
    branch_id: str,
    data: FloorCreate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        name = _clean_name(data.name)
        code = _clean_code(data.code, fallback=name)
        if _code_taken(session, FacilityFloor, branch.id, code):
            raise HTTPException(
                409, "a floor with this code already exists at this branch")
        floor = FacilityFloor(
            organization_id=branch.organization_id, branch_id=branch.id,
            name=name, code=code, level=data.level,
            description=(data.description or "").strip(), status="active")
        session.add(floor)
        session.flush()
        _audit(session, auth, "facility.floor.created", "facility_floor",
               floor.id, branch.organization_id, branch.id,
               after=_floor_to_dict(floor))
        session.commit()
        return _floor_to_dict(floor)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            409, "a floor with this code already exists at this branch")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/api/v1/floors/{floor_id}")
def update_floor(
    floor_id: str,
    data: FacilityUpdate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        floor = session.query(FacilityFloor).filter(
            FacilityFloor.id == floor_id).first()
        if not floor:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, floor.branch_id, auth)
        before = _floor_to_dict(floor)
        if data.name is not None:
            floor.name = _clean_name(data.name)
        if data.code is not None:
            code = _clean_code(data.code, fallback=floor.name)
            if _code_taken(session, FacilityFloor, branch.id, code,
                           exclude_id=floor.id):
                raise HTTPException(
                    409, "a floor with this code already exists at this branch")
            floor.code = code
        if data.level is not None:
            floor.level = data.level
        if data.description is not None:
            floor.description = data.description.strip()
        if data.status is not None:
            status = _clean_status(data.status)
            if status == "inactive" and floor.status != "inactive":
                if _active_room_count(session, branch.id, floor_id=floor.id):
                    raise HTTPException(
                        409, "move or retire this floor's rooms first")
            floor.status = status
        session.flush()
        _audit(session, auth, "facility.floor.updated", "facility_floor",
               floor.id, branch.organization_id, branch.id,
               before=before, after=_floor_to_dict(floor))
        session.commit()
        return _floor_to_dict(floor)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/floors/{floor_id}")
def retire_floor(
    floor_id: str,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    """Retire a floor (never a physical delete) — history must keep resolving."""
    session = SessionFactory()
    try:
        floor = session.query(FacilityFloor).filter(
            FacilityFloor.id == floor_id).first()
        if not floor:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, floor.branch_id, auth)
        if _active_room_count(session, branch.id, floor_id=floor.id):
            raise HTTPException(409, "move or retire this floor's rooms first")
        before = _floor_to_dict(floor)
        floor.status = "inactive"
        session.flush()
        _audit(session, auth, "facility.floor.retired", "facility_floor",
               floor.id, branch.organization_id, branch.id,
               before=before, after=_floor_to_dict(floor))
        session.commit()
        return _floor_to_dict(floor)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@router.get("/api/v1/branches/{branch_id}/departments")
def list_departments(
    branch_id: str,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_permission("facility.read")),
):
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        query = session.query(FacilityDepartment).filter(
            FacilityDepartment.branch_id == branch.id)
        if not include_inactive:
            query = query.filter(FacilityDepartment.status == "active")
        return [_department_to_dict(d)
                for d in query.order_by(FacilityDepartment.name).all()]
    finally:
        session.close()


@router.post("/api/v1/branches/{branch_id}/departments", status_code=201)
def create_department(
    branch_id: str,
    data: FloorCreate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    """Create a department.

    The body model is shared with floors (name/code/description); ``level`` is
    ignored because a department has no building level.
    """
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        name = _clean_name(data.name)
        code = _clean_code(data.code, fallback=name)
        if _code_taken(session, FacilityDepartment, branch.id, code):
            raise HTTPException(
                409, "a department with this code already exists at this branch")
        department = FacilityDepartment(
            organization_id=branch.organization_id, branch_id=branch.id,
            name=name, code=code,
            description=(data.description or "").strip(), status="active")
        session.add(department)
        session.flush()
        _audit(session, auth, "facility.department.created",
               "facility_department", department.id, branch.organization_id,
               branch.id, after=_department_to_dict(department))
        session.commit()
        return _department_to_dict(department)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            409, "a department with this code already exists at this branch")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/api/v1/departments/{department_id}")
def update_department(
    department_id: str,
    data: FacilityUpdate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        department = session.query(FacilityDepartment).filter(
            FacilityDepartment.id == department_id).first()
        if not department:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, department.branch_id, auth)
        before = _department_to_dict(department)
        if data.name is not None:
            department.name = _clean_name(data.name)
        if data.code is not None:
            code = _clean_code(data.code, fallback=department.name)
            if _code_taken(session, FacilityDepartment, branch.id, code,
                           exclude_id=department.id):
                raise HTTPException(
                    409, "a department with this code already exists at this branch")
            department.code = code
        if data.description is not None:
            department.description = data.description.strip()
        if data.status is not None:
            status = _clean_status(data.status)
            if status == "inactive" and department.status != "inactive":
                if _active_room_count(session, branch.id,
                                      department_id=department.id):
                    raise HTTPException(
                        409, "move or retire this department's rooms first")
            department.status = status
        session.flush()
        _audit(session, auth, "facility.department.updated",
               "facility_department", department.id, branch.organization_id,
               branch.id, before=before, after=_department_to_dict(department))
        session.commit()
        return _department_to_dict(department)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/departments/{department_id}")
def retire_department(
    department_id: str,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        department = session.query(FacilityDepartment).filter(
            FacilityDepartment.id == department_id).first()
        if not department:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, department.branch_id, auth)
        if _active_room_count(session, branch.id,
                              department_id=department.id):
            raise HTTPException(409, "move or retire this department's rooms first")
        before = _department_to_dict(department)
        department.status = "inactive"
        session.flush()
        _audit(session, auth, "facility.department.retired",
               "facility_department", department.id, branch.organization_id,
               branch.id, before=before, after=_department_to_dict(department))
        session.commit()
        return _department_to_dict(department)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

def _clean_room_type(value) -> str:
    room_type = (value or "consultation").strip().lower()
    if room_type not in ROOM_TYPES:
        raise HTTPException(
            422, f"room_type must be one of {', '.join(ROOM_TYPES)}")
    return room_type


def _clean_capacity(value) -> Optional[int]:
    if value is None:
        return None
    try:
        capacity = int(value)
    except (TypeError, ValueError):
        raise HTTPException(422, "capacity must be a whole number")
    if capacity < 0:
        raise HTTPException(422, "capacity cannot be negative")
    return capacity


def _room_sessions(session, room_id: str):
    return session.query(ScheduleSession).filter(
        ScheduleSession.room_id == room_id,
        ScheduleSession.status == "active")


@router.get("/api/v1/branches/{branch_id}/rooms")
def list_rooms(
    branch_id: str,
    floor_id: Optional[str] = None,
    department_id: Optional[str] = None,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_permission("facility.read")),
):
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        query = session.query(FacilityRoom).filter(
            FacilityRoom.branch_id == branch.id)
        if floor_id:
            query = query.filter(FacilityRoom.floor_id == floor_id)
        if department_id:
            query = query.filter(FacilityRoom.department_id == department_id)
        if not include_inactive:
            query = query.filter(FacilityRoom.status == "active")
        return [_room_to_dict(r) for r in query.order_by(FacilityRoom.name).all()]
    finally:
        session.close()


@router.post("/api/v1/branches/{branch_id}/rooms", status_code=201)
def create_room(
    branch_id: str,
    data: RoomCreate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)
        name = _clean_name(data.name)
        code = _clean_code(data.code, fallback=name)
        _assert_same_branch(session, branch.id, data.floor_id, data.department_id)
        if _code_taken(session, FacilityRoom, branch.id, code):
            raise HTTPException(
                409, "a room with this code already exists at this branch")
        room = FacilityRoom(
            organization_id=branch.organization_id, branch_id=branch.id,
            floor_id=data.floor_id or None,
            department_id=data.department_id or None,
            name=name, code=code, room_type=_clean_room_type(data.room_type),
            capacity=_clean_capacity(data.capacity),
            description=(data.description or "").strip(), status="active")
        session.add(room)
        session.flush()
        _audit(session, auth, "facility.room.created", "facility_room",
               room.id, branch.organization_id, branch.id,
               after=_room_to_dict(room))
        session.commit()
        return _room_to_dict(room)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            409, "a room with this code already exists at this branch")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/api/v1/rooms/{room_id}")
def update_room(
    room_id: str,
    data: RoomUpdate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    """Patch a room.  An explicit ``null`` clears floor_id / department_id."""
    session = SessionFactory()
    try:
        room = session.query(FacilityRoom).filter(
            FacilityRoom.id == room_id).first()
        if not room:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, room.branch_id, auth)
        provided = getattr(data, "model_fields_set", set())
        before = _room_to_dict(room)
        if data.name is not None:
            room.name = _clean_name(data.name)
        if data.code is not None:
            code = _clean_code(data.code, fallback=room.name)
            if _code_taken(session, FacilityRoom, branch.id, code,
                           exclude_id=room.id):
                raise HTTPException(
                    409, "a room with this code already exists at this branch")
            room.code = code
        next_floor = room.floor_id
        next_department = room.department_id
        if "floor_id" in provided:
            next_floor = data.floor_id or None
        if "department_id" in provided:
            next_department = data.department_id or None
        if next_floor != room.floor_id or next_department != room.department_id:
            _assert_same_branch(session, branch.id, next_floor, next_department)
            room.floor_id = next_floor
            room.department_id = next_department
        if data.room_type is not None:
            room.room_type = _clean_room_type(data.room_type)
        if data.capacity is not None:
            room.capacity = _clean_capacity(data.capacity)
        if data.description is not None:
            room.description = data.description.strip()
        if data.status is not None:
            status = _clean_status(data.status)
            if status == "inactive" and room.status != "inactive":
                if _room_sessions(session, room.id).count():
                    raise HTTPException(
                        409, "this room has active schedule sessions")
            room.status = status
        session.flush()
        _audit(session, auth, "facility.room.updated", "facility_room",
               room.id, branch.organization_id, branch.id,
               before=before, after=_room_to_dict(room))
        session.commit()
        return _room_to_dict(room)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/rooms/{room_id}")
def retire_room(
    room_id: str,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        room = session.query(FacilityRoom).filter(
            FacilityRoom.id == room_id).first()
        if not room:
            raise HTTPException(404, "not found")
        branch = _scoped_branch(session, room.branch_id, auth)
        if _room_sessions(session, room.id).count():
            raise HTTPException(409, "this room has active schedule sessions")
        before = _room_to_dict(room)
        room.status = "inactive"
        session.flush()
        _audit(session, auth, "facility.room.retired", "facility_room",
               room.id, branch.organization_id, branch.id,
               before=before, after=_room_to_dict(room))
        session.commit()
        return _room_to_dict(room)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Specialities — organization-owned catalogue (shared by all branches)
# ---------------------------------------------------------------------------

@router.get("/api/v1/orgs/{org_id}/specialties")
def list_specialties(
    org_id: str,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_permission("facility.read")),
):
    require_org_access(org_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        query = session.query(Specialty).filter(
            Specialty.organization_id == org_id)
        if not include_inactive:
            query = query.filter(Specialty.status == "active")
        rows = query.order_by(Specialty.sort_order, Specialty.name_en).all()
        return [_specialty_to_dict(s) for s in rows]
    finally:
        session.close()


@router.post("/api/v1/orgs/{org_id}/specialties", status_code=201)
def create_specialty(
    org_id: str,
    data: SpecialtyCreate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    require_org_access(org_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        name_en = _clean_name(data.name_en, "name_en")
        code = _clean_code(data.code, fallback=name_en)
        if session.query(Specialty.id).filter(
                Specialty.organization_id == org_id,
                Specialty.code == code).first():
            raise HTTPException(409, "a speciality with this code already exists")
        specialty = Specialty(
            organization_id=org_id, code=code, name_en=name_en,
            name_bn=(data.name_bn or "").strip(),
            sort_order=int(data.sort_order or 0), status="active")
        session.add(specialty)
        session.flush()
        _audit(session, auth, "facility.specialty.created", "specialty",
               specialty.id, org_id, None, after=_specialty_to_dict(specialty))
        session.commit()
        return _specialty_to_dict(specialty)
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "a speciality with this code already exists")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/api/v1/specialties/{specialty_id}")
def update_specialty(
    specialty_id: str,
    data: SpecialtyUpdate,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    session = SessionFactory()
    try:
        specialty = session.query(Specialty).filter(
            Specialty.id == specialty_id).first()
        if not specialty:
            raise HTTPException(404, "not found")
        org_id = specialty.organization_id
        require_org_access(org_id, service=SERVICE)(auth)
        before = _specialty_to_dict(specialty)
        if data.name_en is not None:
            specialty.name_en = _clean_name(data.name_en, "name_en")
        if data.code is not None:
            code = _clean_code(data.code, fallback=specialty.name_en)
            if session.query(Specialty.id).filter(
                    Specialty.organization_id == org_id,
                    Specialty.code == code,
                    Specialty.id != specialty.id).first():
                raise HTTPException(
                    409, "a speciality with this code already exists")
            specialty.code = code
        if data.name_bn is not None:
            specialty.name_bn = data.name_bn.strip()
        if data.sort_order is not None:
            specialty.sort_order = int(data.sort_order)
        if data.status is not None:
            specialty.status = _clean_status(data.status)
        session.flush()
        _audit(session, auth, "facility.specialty.updated", "specialty",
               specialty.id, org_id, None,
               before=before, after=_specialty_to_dict(specialty))
        session.commit()
        return _specialty_to_dict(specialty)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/specialties/{specialty_id}")
def retire_specialty(
    specialty_id: str,
    auth: AuthContext = Depends(require_permission("facility.manage")),
):
    """Retire a speciality.  Existing doctor links stay readable."""
    session = SessionFactory()
    try:
        specialty = session.query(Specialty).filter(
            Specialty.id == specialty_id).first()
        if not specialty:
            raise HTTPException(404, "not found")
        org_id = specialty.organization_id
        require_org_access(org_id, service=SERVICE)(auth)
        before = _specialty_to_dict(specialty)
        specialty.status = "inactive"
        session.flush()
        _audit(session, auth, "facility.specialty.retired", "specialty",
               specialty.id, org_id, None,
               before=before, after=_specialty_to_dict(specialty))
        session.commit()
        return _specialty_to_dict(specialty)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Whole facility tree — one round trip for the UI
# ---------------------------------------------------------------------------

@router.get("/api/v1/branches/{branch_id}/facility")
def get_facility_tree(
    branch_id: str,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_permission("facility.read")),
):
    """Return this branch's floors, departments and rooms in one response."""
    session = SessionFactory()
    try:
        branch = _scoped_branch(session, branch_id, auth)

        def _rows(model):
            query = session.query(model).filter(model.branch_id == branch.id)
            if not include_inactive:
                query = query.filter(model.status == "active")
            return query.order_by(model.name).all()

        return {
            "branch": {"id": branch.id, "name": branch.name,
                       "organization_id": branch.organization_id},
            "floors": [_floor_to_dict(f) for f in _rows(FacilityFloor)],
            "departments": [_department_to_dict(d)
                            for d in _rows(FacilityDepartment)],
            "rooms": [_room_to_dict(r) for r in _rows(FacilityRoom)],
        }
    finally:
        session.close()



