"""AMSDP Doctor Service — BR §9, PostgreSQL-backed.

Facility-local doctor records. No central doctor identity.

AMSDP-FACILITY-DOCTOR-01 split the growing doctor record into two modules:

* this one — registration, listing, detail and update of the doctor record;
* ``doctor/profile.py`` — photograph, BMDC verification, structured
  specialities, multi-branch chamber assignments and the organization's
  registration policy.

Both use ``profile.doctor_dict`` as the single serialiser, so a client sees the
same payload from every endpoint.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from typing import Optional

from common.database import SessionFactory
from common.models import Doctor, DoctorBranch, DoctorSpecialty, Organization

from common.auth import AuthContext, require_permission, get_current_user
from common.health import install_health
from common.denial_audit import install_denial_audit

try:
    from .profile import (
        _audit, assert_mobile_available, clean_mobile,
        doctor_dict as _doctor_to_dict,
        enforce_activation_policy, replace_branch_assignments, scoped_doctor,
        set_specialties,
    )
    from .profile import router as profile_router
except ImportError:                                   # script-mode import
    from profile import (                             # type: ignore
        _audit, assert_mobile_available, clean_mobile,
        doctor_dict as _doctor_to_dict,
        enforce_activation_policy, replace_branch_assignments, scoped_doctor,
        set_specialties,
    )
    from profile import router as profile_router      # type: ignore

app = FastAPI(title="AMSDP Doctor Service")
install_health(app, "doctor")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "doctor")
app.include_router(profile_router)


class DoctorCreate(BaseModel):
    name: str
    mobile: str
    speciality: str = ""
    qualification: str = ""
    registration_number: Optional[str] = None
    consultation_fee: Optional[float] = None
    branch_ids: list[str] = []
    primary_branch_id: Optional[str] = None
    specialty_ids: list[str] = []
    locale: str = "bn"

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    registration_number: Optional[str] = None
    consultation_fee: Optional[float] = None
    branch_ids: Optional[list[str]] = None
    primary_branch_id: Optional[str] = None
    specialty_ids: Optional[list[str]] = None
    locale: Optional[str] = None
    status: Optional[str] = None



# The doctor payload is serialised by ``profile.doctor_dict`` — one serialiser
# for every endpoint (record, photo, verification, specialities, branches).


@app.post("/api/v1/doctors", status_code=201)
def create_doctor(
    data: DoctorCreate,
    auth: AuthContext = Depends(require_permission("doctor.*")),
):
    """Register a doctor.

    The mobile number is stored in canonical national form, so ``+880 1711
    111111`` and ``01711111111`` cannot become two records for one person.
    """
    name = (data.name or "").strip()
    if not name or not (data.mobile or "").strip():
        raise HTTPException(422, "name and mobile are required")
    mobile = clean_mobile(data.mobile)
    session = SessionFactory()
    try:
        # BR §9.6–§9.8 (MP-17): one doctor per mobile number *within* the
        # organization, unless a platform administrator has allowed duplicates
        # here.  The organization row is read first because the allowance lives
        # in its config; the lookup itself stays org-scoped, so the same number
        # is still free at another facility whatever the switch says.
        org = session.query(Organization).filter(
            Organization.id == auth.organization_id).first()
        assert_mobile_available(session, org, auth.organization_id, mobile)
        doctor = Doctor(
            organization_id=auth.organization_id,
            name=name, mobile=mobile,
            speciality=(data.speciality or "").strip(),
            qualification=(data.qualification or "").strip(),
            registration_number=(data.registration_number or "").strip() or None,
            consultation_fee=data.consultation_fee,
            locale=data.locale or "bn",
            status="active",
        )
        session.add(doctor)
        session.flush()
        enforce_activation_policy(session, doctor, org)
        replace_branch_assignments(
            session, doctor, data.branch_ids, auth.organization_id,
            data.primary_branch_id)
        if data.specialty_ids:
            set_specialties(session, doctor, data.specialty_ids,
                            auth.organization_id)
        session.flush()
        _audit(session, auth, "doctor.create", doctor.id,
               doctor.organization_id, after=_doctor_to_dict(doctor))
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
    specialty_id: str = Query(None), status: str = Query(None),
    q: str = Query(""),
    auth: AuthContext = Depends(get_current_user),
):
    """Search doctors.

    ``specialty_id``/``branch_id`` are filtered in SQL (the old code loaded every
    doctor and filtered in Python, which silently ignored pagination and got
    slower with each hire).  ``q`` also matches the mobile number and the BMDC
    registration number, because that is how staff look a doctor up.
    """
    session = SessionFactory()
    try:
        query = session.query(Doctor).options(
            selectinload(Doctor.branch_assignments).selectinload(
                DoctorBranch.branch),
            selectinload(Doctor.branch_assignments).selectinload(
                DoctorBranch.room),
            selectinload(Doctor.specialty_links).selectinload(
                DoctorSpecialty.specialty),
        ).filter(Doctor.organization_id == auth.organization_id)
        if q and q.strip():
            like = f"%{q.strip()}%"
            query = query.filter(or_(
                Doctor.name.ilike(like),
                Doctor.mobile.ilike(like),
                Doctor.registration_number.ilike(like),
            ))
        if speciality:
            query = query.filter(Doctor.speciality == speciality)
        if status:
            query = query.filter(Doctor.status == status)
        if specialty_id:
            query = query.join(
                DoctorSpecialty, DoctorSpecialty.doctor_id == Doctor.id,
            ).filter(DoctorSpecialty.specialty_id == specialty_id)
        if branch_id:
            query = query.join(
                DoctorBranch, DoctorBranch.doctor_id == Doctor.id,
            ).filter(DoctorBranch.branch_id == branch_id,
                     DoctorBranch.status == "active")
        doctors = query.order_by(Doctor.name).all()
        result = [_doctor_to_dict(d) for d in doctors]
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
        # scoped_doctor answers non-disclosing 404 for another tenant's doctor.
        return _doctor_to_dict(scoped_doctor(session, auth, doctor_id))
    finally:
        session.close()



@app.patch("/api/v1/doctors/{doctor_id}")
def update_doctor(
    doctor_id: str, data: DoctorUpdate,
    auth: AuthContext = Depends(require_permission("doctor.*")),
):
    """Update the doctor record.

    Branch assignments are *reconciled*, not deleted and rebuilt, and the
    registration policy is checked only when this request asks for activation —
    editing an already-active doctor whose credentials predate the policy must
    not fail.
    """
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        before = _doctor_to_dict(doctor)
        if data.name is not None:
            name = data.name.strip()
            if not name:
                raise HTTPException(422, "name cannot be empty")
            doctor.name = name
        if data.mobile is not None:
            mobile = clean_mobile(data.mobile)
            # MP-17: same rule on update as on create, excluding this doctor —
            # otherwise re-saving an unchanged number would collide with itself.
            org = session.query(Organization).filter(
                Organization.id == doctor.organization_id).first()
            assert_mobile_available(session, org, doctor.organization_id,
                                    mobile, exclude_doctor_id=doctor.id)
            doctor.mobile = mobile
        for field in ("speciality", "qualification", "locale"):
            val = getattr(data, field, None)
            if val is not None:
                setattr(doctor, field, val.strip())
        if data.registration_number is not None:
            doctor.registration_number = data.registration_number.strip() or None
        if data.consultation_fee is not None:
            doctor.consultation_fee = data.consultation_fee
        activating = (data.status or "").strip() == "active"
        if data.status is not None:
            status = data.status.strip()
            if status not in ("active", "inactive"):
                raise HTTPException(422, "status must be active or inactive")
            doctor.status = status
        if data.branch_ids is not None:
            replace_branch_assignments(
                session, doctor, data.branch_ids, auth.organization_id,
                data.primary_branch_id)
        elif data.primary_branch_id is not None:
            current = [a.branch_id for a in doctor.branch_assignments
                       if (a.status or "active") == "active"]
            replace_branch_assignments(
                session, doctor, current, auth.organization_id,
                data.primary_branch_id)
        if data.specialty_ids is not None:
            set_specialties(session, doctor, data.specialty_ids,
                            auth.organization_id)
        session.flush()
        if activating:
            org = session.query(Organization).filter(
                Organization.id == doctor.organization_id).first()
            enforce_activation_policy(session, doctor, org)
        after = _doctor_to_dict(doctor)
        if before != after:
            _audit(session, auth, "doctor.update", doctor.id,
                   doctor.organization_id, before=before, after=after)
        session.commit()
        return after
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
