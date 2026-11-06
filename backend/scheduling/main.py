"""AMSDP Scheduling Service — BR §14–§15."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

app = FastAPI(title="AMSDP Scheduling Service")
_schedules_db: dict[str, dict] = {}

class SlotTemplate(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 15
    max_patients: int = 4

class ScheduleCreate(BaseModel):
    doctor_id: str
    organization_id: str
    branch_id: str
    effective_from: str = ""
    effective_to: Optional[str] = None
    slot_templates: list[SlotTemplate] = []
    appointment_model: str = "time_slot"

class TimeSlot(BaseModel):
    date: str; start_time: str; end_time: str
    max_patients: int = 1; booked: int = 0

@app.post("/api/v1/schedules", status_code=201)
def create_schedule(data: ScheduleCreate):
    schedule_id = str(uuid.uuid4())
    record = {
        "id": schedule_id, "doctor_id": data.doctor_id,
        "organization_id": data.organization_id, "branch_id": data.branch_id,
        "appointment_model": data.appointment_model,
        "effective_from": data.effective_from,
        "slot_templates": [t.dict() for t in data.slot_templates],
        "status": "active", "created_at": str(datetime.utcnow()),
    }
    _schedules_db[schedule_id] = record
    return record

@app.get("/api/v1/schedules")
def search_schedules(
    doctor_id: str = Query(None),
    organization_id: str = Query(None),
    branch_id: str = Query(None),
):
    results = list(_schedules_db.values())
    if doctor_id: results = [s for s in results if s["doctor_id"] == doctor_id]
    if organization_id:
        results = [s for s in results if s["organization_id"] == organization_id]
    if branch_id: results = [s for s in results if s["branch_id"] == branch_id]
    return results

@app.get("/api/v1/schedules/{schedule_id}/available-slots")
def get_available_slots(schedule_id: str, date_str: str = Query(...)):
    schedule = _schedules_db.get(schedule_id)
    if not schedule: raise HTTPException(404)
    slots: list[dict] = []
    for tmpl in schedule["slot_templates"]:
        start_h, start_m = map(int, tmpl["start_time"].split(":"))
        end_h, end_m = map(int, tmpl["end_time"].split(":"))
        start_min = start_h * 60 + start_m
        end_min = end_h * 60 + end_m
        duration = tmpl["slot_duration_minutes"]
        for slot_start in range(start_min, end_min, duration):
            sh, sm = divmod(slot_start, 60)
            eh, em = divmod(min(slot_start + duration, end_min), 60)
            slots.append({
                "start_time": f"{sh:02d}:{sm:02d}",
                "end_time": f"{eh:02d}:{em:02d}",
                "max_patients": tmpl["max_patients"], "booked": 0,
            })
    return {"date": date_str, "schedule_id": schedule_id, "slots": slots}