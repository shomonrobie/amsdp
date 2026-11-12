"""AMSDP Patient Service — BR §10–§11, PostgreSQL-backed.

Org-scoped patient records shared across branches within an org.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional

from common.database import SessionFactory
from common.models import Patient
from common.auth import AuthContext, require_permission, get_current_user
from common.health import install_health

app = FastAPI(title="AMSDP Patient Service")
install_health(app, "patient")


class PatientCreate(BaseModel):
    organization_id: str = ""
    name: str
    mobile: str
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    address: Optional[str] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None


def _validate_dob(date_of_birth: Optional[str]):
    """Validate an optional YYYY-MM-DD date of birth. Returns '' or normalized value."""
    from datetime import datetime as _dt
    if date_of_birth is None or date_of_birth == "":
        return ""
    raw = str(date_of_birth).strip()
    try:
        d = _dt.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, "date_of_birth must be in YYYY-MM-DD format")
    if d > _dt.now().date():
        raise HTTPException(422, "date_of_birth cannot be in the future")
    return raw


def _validate_reported_age(age: Optional[int]):
    """Validate an optional reported age (0..150)."""
    if age is None:
        return None
    try:
        v = int(age)
    except (TypeError, ValueError):
        raise HTTPException(422, "age must be a whole number")
    if v < 0 or v > 150:
        raise HTTPException(422, "age must be between 0 and 150")
    return v


def _age_from_dob(date_of_birth: Optional[str], today=None):
    """Compute current age in years from a YYYY-MM-DD DOB (None if unavailable).

    The result never fabricates a DOB — it only ever reads one.
    """
    if not date_of_birth:
        return None
    from datetime import datetime, date as _date
    try:
        dob = datetime.strptime(str(date_of_birth), "%Y-%m-%d").date()
    except ValueError:
        return None
    today = today or _date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return max(years, 0)


def _patient_to_dict(p):
    dob = p.date_of_birth or ""
    age_from_dob = _age_from_dob(dob)
    # DOB-derived age is authoritative whenever a DOB exists; otherwise the
    # staff-reported age is shown. Neither is ever fabricated.
    if dob:
        age_source = "dob"
    elif p.age is not None:
        age_source = "reported"
    else:
        age_source = ""
    return {
        "id": p.id, "organization_id": p.organization_id,
        "name": p.name, "mobile": p.mobile,
        "date_of_birth": dob,
        "age": p.age,                 # reported age only (raw)
        "age_from_dob": age_from_dob, # computed from DOB (authoritative when dob set)
        "age_source": age_source,     # 'dob' | 'reported' | ''
        "sex": p.sex or "", "address": p.address or "",
        "status": p.status or "active",
        "created_at": str(p.created_at) if p.created_at else "",
    }


@app.post("/api/v1/patients", status_code=201)
def register_patient(
    data: PatientCreate,
    auth: AuthContext = Depends(require_permission("patient.create")),
):
    if not data.name.strip() or not data.mobile.strip():
        raise HTTPException(422, "name and mobile are required")
    dob = _validate_dob(data.date_of_birth)
    age = _validate_reported_age(data.age)
    import uuid
    session = SessionFactory()
    try:
        patient = Patient(
            id=str(uuid.uuid4()),
            organization_id=auth.organization_id,
            name=data.name.strip(),
            mobile=data.mobile.strip(),
            date_of_birth=dob or None,
            age=age,
            sex=data.sex, address=data.address,
        )
        session.add(patient)
        session.commit()
        # Check duplicates
        dupes = session.query(Patient).filter(
            Patient.organization_id == auth.organization_id,
            Patient.mobile == data.mobile.strip(),
            Patient.id != patient.id,
        ).all()
        return {
            "patient": _patient_to_dict(patient),
            "duplicates": [{"patient_id": d.id, "name": d.name, "mobile": d.mobile}
                          for d in dupes],
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/v1/patients")
def search_patients(
    q: str = Query(""), page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        query = session.query(Patient).filter(
            Patient.organization_id == auth.organization_id)
        if q:
            query = query.filter(
                (Patient.name.ilike(f"%{q}%")) | (Patient.mobile.contains(q)))
        total = query.count()
        items = query.order_by(Patient.created_at.desc()).offset(
            (page-1)*limit).limit(limit).all()
        return {"items": [_patient_to_dict(p) for p in items],
                "total": total, "page": page}
    finally:
        session.close()


@app.get("/api/v1/patients/{patient_id}")
def get_patient(
    patient_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        patient = session.query(Patient).filter(
            Patient.id == patient_id,
            Patient.organization_id == auth.organization_id,
        ).first()
        if not patient:
            raise HTTPException(404)
        return _patient_to_dict(patient)
    finally:
        session.close()


@app.patch("/api/v1/patients/{patient_id}")
def update_patient(
    patient_id: str, data: PatientUpdate,
    auth: AuthContext = Depends(require_permission("patient.create")),
):
    session = SessionFactory()
    try:
        patient = session.query(Patient).filter(
            Patient.id == patient_id,
            Patient.organization_id == auth.organization_id,
        ).first()
        if not patient:
            raise HTTPException(404)
        if data.name: patient.name = data.name.strip()
        if data.mobile: patient.mobile = data.mobile.strip()
        if data.address: patient.address = data.address.strip()
        if data.date_of_birth is not None:
            patient.date_of_birth = _validate_dob(data.date_of_birth) or None
        if data.age is not None:
            patient.age = _validate_reported_age(data.age)
        if data.sex is not None: patient.sex = data.sex
        session.commit()
        return _patient_to_dict(patient)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()