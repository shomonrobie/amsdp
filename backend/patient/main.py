"""AMSDP Patient Service — BR §10–§11."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Patient Service")
_patients_db: dict[str, dict] = {}

class PatientCreate(BaseModel):
    organization_id: str
    name: str
    mobile: str
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None

class PatientMergeRequest(BaseModel):
    primary_patient_id: str
    duplicate_patient_id: str
    reason: str

@app.post("/api/v1/patients", status_code=201)
def register_patient(data: PatientCreate):
    if not data.name.strip() or not data.mobile.strip():
        raise HTTPException(422, "name and mobile are required")
    patient_id = str(uuid.uuid4())
    record = {
        "id": patient_id, "organization_id": data.organization_id,
        "name": data.name.strip(), "mobile": data.mobile.strip(),
        "date_of_birth": data.date_of_birth, "sex": data.sex,
        "address": data.address, "national_id": data.national_id,
        "status": "active", "created_at": str(datetime.utcnow()),
    }
    _patients_db[patient_id] = record
    duplicates = [
        {"patient_id": pid, "name": rec["name"], "mobile": rec["mobile"]}
        for pid, rec in _patients_db.items()
        if rec["organization_id"] == data.organization_id
        and rec["mobile"] == data.mobile.strip() and pid != patient_id
    ]
    return {"patient": record, "duplicates": duplicates}

@app.get("/api/v1/patients")
def search_patients(
    organization_id: str = Query(...),
    q: str = Query(""), page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    results = [
        p for p in _patients_db.values()
        if p["organization_id"] == organization_id
        and (not q or q.lower() in p["name"].lower() or q in p["mobile"])
    ]
    items = results[(page - 1) * limit : page * limit]
    return {"items": items, "total": len(results), "page": page}

@app.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: str):
    patient = _patients_db.get(patient_id)
    if not patient: raise HTTPException(404)
    return patient

@app.patch("/api/v1/patients/{patient_id}")
def update_patient(patient_id: str, data: PatientUpdate):
    patient = _patients_db.get(patient_id)
    if not patient: raise HTTPException(404)
    if data.name: patient["name"] = data.name.strip()
    if data.mobile: patient["mobile"] = data.mobile.strip()
    if data.address: patient["address"] = data.address.strip()
    return patient

@app.post("/api/v1/patients/merge", status_code=200)
def merge_patients(data: PatientMergeRequest):
    primary = _patients_db.get(data.primary_patient_id)
    duplicate = _patients_db.get(data.duplicate_patient_id)
    if not primary or not duplicate:
        raise HTTPException(404, "one or both patient IDs not found")
    if primary["organization_id"] != duplicate["organization_id"]:
        raise HTTPException(422, "cannot merge cross-org patients")
    duplicate["status"] = "merged"
    duplicate["merged_into"] = data.primary_patient_id
    duplicate["merge_reason"] = data.reason
    return {"merged": True, "primary_patient_id": data.primary_patient_id}