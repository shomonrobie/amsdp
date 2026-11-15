"""AMSDP Scheduling Service — BR §14–§15.

PostgreSQL-backed with auth. Supports time-slot, serial, and hybrid models.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timezone

from common.database import SessionFactory
from common.models import Schedule
from common.auth import AuthContext, require_permission, get_current_user
from common.health import install_health
from common.denial_audit import install_denial_audit

app = FastAPI(title="AMSDP Scheduling Service")
install_health(app, "scheduling")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "scheduling")

# AMSDP-FACILITY-DOCTOR-01 — recurring clinic sessions with a chamber.  They
# project into ``schedules.slot_templates``, so the calendar keeps its contract.
try:
    from .sessions import router as sessions_router
except ImportError:                                   # script-mode import
    from sessions import router as sessions_router    # type: ignore
app.include_router(sessions_router)



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

class ScheduleUpdate(BaseModel):
    slot_templates: Optional[list[SlotTemplate]] = None
    appointment_model: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    status: Optional[str] = None


def _schedule_to_dict(s):
    return {"id": s.id, "doctor_id": s.doctor_id,
        "organization_id": s.organization_id, "branch_id": s.branch_id,
        "appointment_model": s.appointment_model or "time_slot",
        "effective_from": str(s.effective_from) if s.effective_from else "",
        "effective_to": str(s.effective_to) if s.effective_to else "",
        "slot_templates": s.slot_templates or [],
        "status": s.status or "active",
        "created_at": str(s.created_at) if s.created_at else "",
    }

@app.post("/api/v1/schedules", status_code=201)
def create_schedule(data: ScheduleCreate, auth=Depends(require_permission("schedule.*"))):
    import uuid
    session = SessionFactory()
    try:
        ef = None; et = None
        if data.effective_from:
            try: ef = datetime.strptime(data.effective_from, "%Y-%m-%d").date()
            except: pass
        if data.effective_to:
            try: et = datetime.strptime(data.effective_to, "%Y-%m-%d").date()
            except: pass
        s = Schedule(id=str(uuid.uuid4()), doctor_id=data.doctor_id,
            organization_id=auth.organization_id, branch_id=data.branch_id,
            appointment_model=data.appointment_model, effective_from=ef,
            effective_to=et, slot_templates=[t.dict() for t in data.slot_templates])
        session.add(s); session.commit()
        return _schedule_to_dict(s)
    except Exception:
        session.rollback(); raise
    finally:
        session.close()

@app.get("/api/v1/schedules")
def search_schedules(doctor_id: str = Query(None), branch_id: str = Query(None),
                     auth=Depends(get_current_user)):
    session = SessionFactory()
    try:
        q = session.query(Schedule).filter(Schedule.organization_id == auth.organization_id)
        if doctor_id: q = q.filter(Schedule.doctor_id == doctor_id)
        if branch_id: q = q.filter(Schedule.branch_id == branch_id)
        return [_schedule_to_dict(s) for s in q.all()]
    finally:
        session.close()

@app.get("/api/v1/schedules/{schedule_id}")
def get_schedule(schedule_id: str, auth=Depends(get_current_user)):
    session = SessionFactory()
    try:
        s = session.query(Schedule).filter(Schedule.id == schedule_id,
            Schedule.organization_id == auth.organization_id).first()
        if not s: raise HTTPException(404)
        return _schedule_to_dict(s)
    finally:
        session.close()

@app.patch("/api/v1/schedules/{schedule_id}")
def update_schedule(schedule_id: str, data: ScheduleUpdate,
                    auth=Depends(require_permission("schedule.*"))):
    session = SessionFactory()
    try:
        s = session.query(Schedule).filter(Schedule.id == schedule_id,
            Schedule.organization_id == auth.organization_id).first()
        if not s: raise HTTPException(404)
        if data.slot_templates is not None:
            s.slot_templates = [t.dict() for t in data.slot_templates]
        if data.appointment_model is not None: s.appointment_model = data.appointment_model
        if data.effective_from is not None:
            try: s.effective_from = datetime.strptime(data.effective_from, "%Y-%m-%d").date()
            except: pass
        if data.effective_to is not None:
            try: s.effective_to = datetime.strptime(data.effective_to, "%Y-%m-%d").date()
            except: pass
        if data.status is not None: s.status = data.status
        session.commit()
        return _schedule_to_dict(s)
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
@app.get("/api/v1/schedules/{schedule_id}/available-slots")
def get_available_slots(schedule_id: str, date_str: str = Query(...),
                         auth=Depends(get_current_user)):
    """Calculate available slots using actual appointment counts from DB."""
    from common.models import Appointment, Organization
    from common.config import get_queue_config, reserved_for_capacity
    session = SessionFactory()
    try:
        sched = session.query(Schedule).filter(Schedule.id == schedule_id,
            Schedule.organization_id == auth.organization_id).first()
        if not sched: raise HTTPException(404)
        org = session.query(Organization).filter(
            Organization.id == sched.organization_id).first()
        qcfg = get_queue_config(org.config if org else None)
        try: target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: raise HTTPException(422, "invalid date, use YYYY-MM-DD")
        slots = []
        for t in (sched.slot_templates or []):
            sh, sm = map(int, t["start_time"].split(":"))
            eh, em = map(int, t["end_time"].split(":"))
            smin, emin = sh*60+sm, eh*60+em
            dur = t.get("slot_duration_minutes", 15)
            maxp = t.get("max_patients", 1)
            for ss in range(smin, emin, dur):
                h1, m1 = divmod(ss, 60); h2, m2 = divmod(min(ss+dur, emin), 60)
                st = f"{h1:02d}:{m1:02d}"; et = f"{h2:02d}:{m2:02d}"
                booked = session.query(Appointment).filter(
                    Appointment.doctor_id == sched.doctor_id,
                    Appointment.appointment_date == target,
                    Appointment.start_time == st,
                    Appointment.status.in_(["BOOKED","AWAITING_CONFIRMATION",
                        "CONFIRMED","CHECKED_IN","IN_QUEUE"])).count()
                reserved = 0
                if qcfg["walk_in_reserve_value"] > 0 and maxp:
                    reserved = reserved_for_capacity(maxp, org.config if org else None)
                unreserved_capacity = max(maxp - reserved, 0)
                slots.append({"start_time": st, "end_time": et,
                    "max_patients": maxp, "booked": booked,
                    "reserved_walkin": reserved,
                    "unreserved_capacity": unreserved_capacity,
                    "available": max(maxp - booked, 0),
                    "available_unreserved": max(unreserved_capacity - booked, 0)})
        return {"date": date_str, "schedule_id": schedule_id,
            "doctor_id": sched.doctor_id,
            "appointment_model": sched.appointment_model,
            "walk_in_reserve_mode": qcfg["walk_in_reserve_mode"],
            "walk_in_reserve_value": qcfg["walk_in_reserve_value"],
            "slots": slots}
    finally:
        session.close()