"""AMSDP Patient Service — BR §10–§11, PostgreSQL-backed.

Org-scoped patient records shared across branches within an org.

**Q-1 / MP-44 — one operational day, and it is the facility's.**  This service
used to answer "today" twice, from the *server's* clock: the date-of-birth
future check (``datetime.now().date()``) and the age calculation
(``date.today()``).  Both now come from :func:`common.timeutil.operational_today`,
which reads ``organizations.timezone`` (BR §8) and therefore agrees with the
queue board, the dashboard and the display.  On a host that is not the facility's
time zone the old code answered a different day: at 02:00 Dhaka on a UTC host a
newborn's date of birth was rejected as "in the future", and every patient's age
was a day stale between the two midnights.  The day is now read **once per
request** and threaded down, so the list endpoint does not run one organization
lookup per patient.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional

from common.database import SessionFactory
from common.models import Patient
from common.auth import AuthContext, require_permission, get_current_user
from common.health import install_health
from common.denial_audit import install_denial_audit
from common.timeutil import operational_today

app = FastAPI(title="AMSDP Patient Service")
install_health(app, "patient")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "patient")


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


def _validate_dob(date_of_birth: Optional[str], today=None):
    """Validate an optional YYYY-MM-DD date of birth. Returns '' or normalized value.

    ``today`` is the *facility's* operational day (Q-1/MP-44).  Callers that
    already hold a session pass it in so the day is read once per request; when
    it is omitted the helper resolves it from the facility zone without touching
    the database — never from the host clock.
    """
    from datetime import datetime as _dt
    if date_of_birth is None or date_of_birth == "":
        return ""
    raw = str(date_of_birth).strip()
    try:
        d = _dt.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, "date_of_birth must be in YYYY-MM-DD format")
    if d > (today or operational_today()):
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

    The result never fabricates a DOB — it only ever reads one.  ``today`` is the
    facility's operational day (Q-1/MP-44); see :func:`_validate_dob`.
    """
    if not date_of_birth:
        return None
    from datetime import datetime
    try:
        dob = datetime.strptime(str(date_of_birth), "%Y-%m-%d").date()
    except ValueError:
        return None
    today = today or operational_today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return max(years, 0)


def _patient_to_dict(p, today=None):
    dob = p.date_of_birth or ""
    age_from_dob = _age_from_dob(dob, today)
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
    import uuid
    session = SessionFactory()
    try:
        # Q-1/MP-44: one facility-day read per request, used by both validators.
        facility_today = operational_today(session, auth.organization_id)
        dob = _validate_dob(data.date_of_birth, facility_today)
        age = _validate_reported_age(data.age)
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
            "patient": _patient_to_dict(patient, facility_today),
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
        # Q-1/MP-44: one facility-day read for the whole page, not one per row.
        facility_today = operational_today(session, auth.organization_id)
        return {"items": [_patient_to_dict(p, facility_today) for p in items],
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
        return _patient_to_dict(
            patient, operational_today(session, auth.organization_id))
    finally:
        session.close()


@app.patch("/api/v1/patients/{patient_id}")
def update_patient(
    patient_id: str, data: PatientUpdate,
    auth: AuthContext = Depends(require_permission("patient.update")),
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
        # Q-1/MP-44: the facility's day, read once, used by the check and the age.
        facility_today = operational_today(session, auth.organization_id)
        if data.date_of_birth is not None:
            patient.date_of_birth = _validate_dob(
                data.date_of_birth, facility_today) or None
        if data.age is not None:
            patient.age = _validate_reported_age(data.age)
        if data.sex is not None: patient.sex = data.sex
        session.commit()
        return _patient_to_dict(patient, facility_today)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()