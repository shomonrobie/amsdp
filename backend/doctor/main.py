"""AMSDP Doctor Service — BR §9."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Doctor Service")
_doctors_db: dict[str, dict] = {}

class DoctorCreate(BaseModel):
    organization_id: str
    branch_ids: list[str] = []
    name: str
    mobile: str
    speciality: str = ""
    qualification: str = ""
    registration_number: Optional[str] = None
    consultation_fee: Optional[float] = None
    locale: str = "bn"

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    speciality: Optional[str] = None
    qualification: Optional[str] = None
    consultation_fee: Optional[float] = None
    branch_ids: Optional[list[str]] = None
    status: Optional[str] = None

@app.post("/api/v1/doctors", status_code=201)
def create_doctor(data: DoctorCreate):
    if not data.name.strip() or not data.mobile.strip():
        raise HTTPException(422, "name and mobile are required")
    doctor_id = str(uuid.uuid4())
    record = {
        "id": doctor_id, "organization_id": data.organization_id,
        "branch_ids": data.branch_ids, "name": data.name.strip(),
        "mobile": data.mobile.strip(), "speciality": data.speciality,
        "qualification": data.qualification,
        "registration_number": data.registration_number,
        "consultation_fee": data.consultation_fee,
        "locale": data.locale, "status": "active",
        "created_at": str(datetime.utcnow()),
    }
    _doctors_db[doctor_id] = record
    return record

@app.get("/api/v1/doctors")
def search_doctors(
    organization_id: str = Query(...),
    branch_id: str = Query(None),
    speciality: str = Query(None),
    q: str = Query(""),
):
    results = [
        d for d in _doctors_db.values()
        if d["organization_id"] == organization_id
        and (not q or q.lower() in d["name"].lower())
        and (not speciality or d.get("speciality") == speciality)
        and (not branch_id or branch_id in d.get("branch_ids", []))
    ]
    return {"items": results, "total": len(results)}

@app.get("/api/v1/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    doctor = _doctors_db.get(doctor_id)
    if not doctor: raise HTTPException(404)
    return doctor

@app.patch("/api/v1/doctors/{doctor_id}")
def update_doctor(doctor_id: str, data: DoctorUpdate):
    doctor = _doctors_db.get(doctor_id)
    if not doctor: raise HTTPException(404)
    for field in ("name", "mobile", "speciality", "qualification", "status"):
        val = getattr(data, field, None)
        if val is not None: doctor[field] = val
    if data.branch_ids is not None: doctor["branch_ids"] = data.branch_ids
    if data.consultation_fee is not None: doctor["consultation_fee"] = data.consultation_fee
    return doctor