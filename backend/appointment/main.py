"""AMSDP Appointment Service — BR §16–§20."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Appointment Service")
_appointments_db: dict[str, dict] = {}

class AppointmentCreate(BaseModel):
    organization_id: str
    branch_id: str
    patient_id: str
    doctor_id: str
    appointment_date: str
    start_time: Optional[str] = None
    serial_number: Optional[int] = None
    appointment_type: str = "scheduled"
    notes: str = ""
    created_by: str = ""

class AppointmentReschedule(BaseModel):
    new_date: str; new_start_time: Optional[str] = None; reason: str = ""

class AppointmentStatusUpdate(BaseModel):
    status: str; reason: str = ""

@app.post("/api/v1/appointments", status_code=201)
def create_appointment(data: AppointmentCreate):
    if not data.patient_id or not data.doctor_id:
        raise HTTPException(422, "patient and doctor are required")
    appointment_id = str(uuid.uuid4())
    serial = data.serial_number or len([
        a for a in _appointments_db.values()
        if a["doctor_id"] == data.doctor_id
        and a["appointment_date"] == data.appointment_date
    ]) + 1
    record = {
        "id": appointment_id, "organization_id": data.organization_id,
        "branch_id": data.branch_id, "patient_id": data.patient_id,
        "doctor_id": data.doctor_id, "appointment_date": data.appointment_date,
        "start_time": data.start_time, "serial_number": serial,
        "appointment_type": data.appointment_type,
        "status": "scheduled", "status_history": [],
        "token_number": f"T-{data.doctor_id[:6]}-{serial:03d}",
        "notes": data.notes, "created_by": data.created_by,
        "created_at": str(datetime.utcnow()),
    }
    _appointments_db[appointment_id] = record
    return record

@app.get("/api/v1/appointments")
def list_appointments(
    patient_id: str = Query(None), doctor_id: str = Query(None),
    date: str = Query(None), organization_id: str = Query(None),
    status: str = Query(None),
):
    results = list(_appointments_db.values())
    if patient_id: results = [a for a in results if a["patient_id"] == patient_id]
    if doctor_id: results = [a for a in results if a["doctor_id"] == doctor_id]
    if date: results = [a for a in results if a["appointment_date"] == date]
    if organization_id:
        results = [a for a in results if a["organization_id"] == organization_id]
    if status: results = [a for a in results if a["status"] == status]
    return results

@app.get("/api/v1/appointments/{appointment_id}")
def get_appointment(appointment_id: str):
    appt = _appointments_db.get(appointment_id)
    if not appt: raise HTTPException(404)
    return appt

@app.patch("/api/v1/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, data: AppointmentStatusUpdate, actor: str = ""):
    appt = _appointments_db.get(appointment_id)
    if not appt: raise HTTPException(404)
    transitions = {
        "scheduled": ["confirmed", "cancelled"],
        "confirmed": ["arrived", "cancelled"],
        "arrived": ["in_progress", "no_show"],
        "in_progress": ["completed", "cancelled"],
    }
    allowed = transitions.get(appt["status"], [])
    if data.status not in allowed:
        raise HTTPException(422, f"cannot go from {appt['status']} to {data.status}")
    appt["status_history"].append({
        "from": appt["status"], "to": data.status,
        "reason": data.reason, "actor": actor or "system",
    })
    appt["status"] = data.status
    return appt

@app.post("/api/v1/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: str, data: AppointmentReschedule):
    appt = _appointments_db.get(appointment_id)
    if not appt: raise HTTPException(404)
    if appt["status"] in ("completed", "cancelled"):
        raise HTTPException(422, "cannot reschedule a completed/cancelled appointment")
    new_id = str(uuid.uuid4())
    new_record = {**appt, "id": new_id, "appointment_date": data.new_date,
                  "start_time": data.new_start_time,
                  "status": "scheduled", "rescheduled_from": appointment_id,
                  "reschedule_reason": data.reason}
    _appointments_db[new_id] = new_record
    appt["status"] = "rescheduled"
    appt["rescheduled_to"] = new_id
    return {"new_appointment_id": new_id, "original_appointment_id": appointment_id}