"""AMSDP Doctor Service — BR §9, PostgreSQL-backed.

Facility-local doctor records. No central doctor identity.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional

from common.database import SessionFactory
from common.models import Doctor, DoctorBranch, Branch
from common.auth import AuthContext, require_permission, get_current_user
from common.health import install_health

app = FastAPI(title="AMSDP Doctor Service")
install_health(app, "doctor")


class DoctorCreate(BaseModel):
    name: str
    mobile: str
    speciality: str = ""
    qualification: str = ""
    registration_number: Optional[str] = None
    consultation_fee: Optional[float] = None
    branch_ids: list[str] = []
    locale: str = "bn"

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    consultation_fee: Optional[float] = None
    branch_ids: Optional[list[str]] = None
    status: Optional[str] = None


def _doctor_to_dict(d):
    return {
        "id": d.id, "organization_id": d.organization_id,
        "name": d.name, "mobile": d.mobile,
        "speciality": d.speciality or "",
        "qualification": d.qualification or "",
        "registration_number": d.registration_number or "",
        "consultation_fee": d.consultation_fee,
        "locale": d.locale or "bn",
        "status": d.status or "active",
        "branch_ids": [db.branch_id for db in d.branch_assignments],
        "created_at": str(d.created_at) if d.created_at else "",
    }


@app.post("/api/v1/doctors", status_code=201)
def create_doctor(
    data: DoctorCreate,
    auth: AuthContext = Depends(require_permission("doctor.*")),
):
    if not data.name.strip() or not data.mobile.strip():
        raise HTTPException(422, "name and mobile are required")
    import uuid
    session = SessionFactory()
    try:
        doctor = Doctor(
            id=str(uuid.uuid4()),
            organization_id=auth.organization_id,
            name=data.name.strip(), mobile=data.mobile.strip(),
            speciality=data.speciality, qualification=data.qualification,
            registration_number=data.registration_number,
            consultation_fee=data.consultation_fee, locale=data.locale,
        )
        session.add(doctor)
        for bid in data.branch_ids:
            branch = session.query(Branch).filter(
                Branch.id == bid,
                Branch.organization_id == auth.organization_id,
            ).first()
            if branch:
                session.add(DoctorBranch(doctor_id=doctor.id, branch_id=bid))
        session.commit()
        return _doctor_to_dict(doctor)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/v1/doctors")
def search_doctors(
    branch_id: str = Query(None), speciality: str = Query(None),
    q: str = Query(""),
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        query = session.query(Doctor).filter(
            Doctor.organization_id == auth.organization_id)
        if q:
            query = query.filter(Doctor.name.ilike(f"%{q}%"))
        if speciality:
            query = query.filter(Doctor.speciality == speciality)
        doctors = query.order_by(Doctor.name).all()
        result = []
        for d in doctors:
            d_dict = _doctor_to_dict(d)
            if branch_id and branch_id not in d_dict["branch_ids"]:
                continue
            result.append(d_dict)
        return {"items": result, "total": len(result)}
    finally:
        session.close()


@app.get("/api/v1/doctors/{doctor_id}")
def get_doctor(
    doctor_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        doctor = session.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.organization_id == auth.organization_id,
        ).first()
        if not doctor:
            raise HTTPException(404)
        return _doctor_to_dict(doctor)
    finally:
        session.close()


@app.patch("/api/v1/doctors/{doctor_id}")
def update_doctor(
    doctor_id: str, data: DoctorUpdate,
    auth: AuthContext = Depends(require_permission("doctor.*")),
):
    session = SessionFactory()
    try:
        doctor = session.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.organization_id == auth.organization_id,
        ).first()
        if not doctor:
            raise HTTPException(404)
        for field in ("name", "mobile", "speciality", "qualification", "status"):
            val = getattr(data, field, None)
            if val is not None: setattr(doctor, field, val)
        if data.consultation_fee is not None:
            doctor.consultation_fee = data.consultation_fee
        if data.branch_ids is not None:
            # Clear and rebuild branch assignments
            session.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == doctor_id).delete()
            for bid in data.branch_ids:
                branch = session.query(Branch).filter(
                    Branch.id == bid,
                    Branch.organization_id == auth.organization_id,
                ).first()
                if branch:
                    session.add(DoctorBranch(doctor_id=doctor.id, branch_id=bid))
        session.commit()
        return _doctor_to_dict(doctor)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()