"""AMSDP Scheduling Service — BR §14–§15.

PostgreSQL-backed with auth. Supports time-slot, serial, and hybrid models.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date, datetime, timezone
from sqlalchemy import func

from common.database import SessionFactory
from common.models import Schedule, Branch, Doctor
from common.auth import AuthContext, require_permission, get_current_user, branch_accessible
from common.audit import record_audit
from common.health import install_health
from common.denial_audit import install_denial_audit
# AMSDP-APPT-RELIABILITY — one slot arithmetic for both services (F-03/F-15/F-16).
from common.slots import MIN_SLOT_DURATION, slot_starts, to_minutes

app = FastAPI(title="AMSDP Scheduling Service")
install_health(app, "scheduling")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "scheduling")

#: Statuses that occupy a slot (BR §23.7).  Declared once so the availability
#: read and the appointment write path cannot disagree about what "booked" means.
ACTIVE_BOOKING_STATUSES = ("BOOKED", "AWAITING_CONFIRMATION", "CONFIRMED",
                           "CHECKED_IN", "IN_QUEUE")

# AMSDP-FACILITY-DOCTOR-01 — recurring clinic sessions with a chamber.  They
# project into ``schedules.slot_templates``, so the calendar keeps its contract.
try:
    from .sessions import router as sessions_router
except ImportError:                                   # script-mode import
    from sessions import router as sessions_router    # type: ignore
app.include_router(sessions_router)



class SlotTemplate(BaseModel):
    """One recurring window of clinic hours — the definition of a slot (BR §23.3).

    Validated here instead of trusted downstream (finding F-14): readers used to
    parse these strings themselves, so a stored ``"9:00"`` turned the
    availability read into a 500 and the calendar day into an empty column.
    """

    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 15
    max_patients: int = 4

    @field_validator("day_of_week")
    @classmethod
    def _valid_day(cls, value: int) -> int:
        if not 0 <= int(value) <= 6:
            raise ValueError("day_of_week must be 0..6 (0 = Monday)")
        return int(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_clock(cls, value: str) -> str:
        text = (value or "").strip()
        if to_minutes(text) is None:
            raise ValueError("must be HH:MM in 24-hour zero-padded form")
        return text

    @field_validator("slot_duration_minutes")
    @classmethod
    def _valid_duration(cls, value: int) -> int:
        if int(value) < MIN_SLOT_DURATION:
            raise ValueError(f"slot_duration_minutes must be at least {MIN_SLOT_DURATION}")
        return int(value)

    @field_validator("max_patients")
    @classmethod
    def _valid_capacity(cls, value: int) -> int:
        if int(value) < 1:
            raise ValueError("max_patients must be at least 1")
        return int(value)

    @model_validator(mode="after")
    def _ordered_window(self):
        if to_minutes(self.end_time) <= to_minutes(self.start_time):
            raise ValueError("end_time must be later than start_time")
        return self

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

def _optional_date(value, field: str):
    """Parse an optional ``YYYY-MM-DD``, refusing instead of swallowing (F-13).

    The previous ``except: pass`` silently dropped a mistyped ``effective_from``,
    which widened the schedule to open-ended and made a bounded schedule accept
    bookings it was never meant to accept.
    """
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, f"{field} must be a valid YYYY-MM-DD date")


@app.post("/api/v1/schedules", status_code=201)
def create_schedule(data: ScheduleCreate, auth=Depends(require_permission("schedule.*"))):
    import uuid
    session = SessionFactory()
    try:
        ef = _optional_date(data.effective_from, "effective_from")
        et = _optional_date(data.effective_to, "effective_to")
        if ef and et and et < ef:
            raise HTTPException(422, "effective_to must not be earlier than effective_from")
        # P0-6: enforce branch scope.  organization_id comes from the token
        # (never the body).  The caller must be authorized for the target
        # branch, and the doctor + branch must belong to the caller's
        # organization.  Doctor multi-branch scheduling is preserved: a doctor
        # may be scheduled at any branch in the same organization.
        if not branch_accessible(auth, data.branch_id):
            raise HTTPException(404, "not found")
        doctor = session.query(Doctor).filter(
            Doctor.id == data.doctor_id,
            Doctor.organization_id == auth.organization_id).first()
        if not doctor:
            raise HTTPException(404, "doctor not found")
        branch = session.query(Branch).filter(
            Branch.id == data.branch_id,
            Branch.organization_id == auth.organization_id).first()
        if not branch:
            raise HTTPException(404, "branch not found")
        # F-12: an inactive doctor must not become schedulable.  The employment
        # state is the gate; registration state is a separate question and is
        # left to the doctor service.
        if (doctor.status or "active").lower() != "active":
            raise HTTPException(422, "doctor is not active and cannot be scheduled")
        s = Schedule(id=str(uuid.uuid4()), doctor_id=data.doctor_id,
            organization_id=auth.organization_id, branch_id=data.branch_id,
            appointment_model=data.appointment_model, effective_from=ef,
            effective_to=et, slot_templates=[t.model_dump() for t in data.slot_templates])
        session.add(s)
        session.flush()
        # F-12: schedule creation is a tenant-affecting change with no trail.
        record_audit(session, service="scheduling", org_id=auth.organization_id,
                     action="schedule.created", target_type="schedule",
                     target_id=s.id, actor_id=auth.user_id, actor_role=auth.role,
                     branch_id=s.branch_id, after=_schedule_to_dict(s))
        session.commit()
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
        if branch_id:
            # 8.2: validate the caller-supplied branch against authenticated
            # scope so a branch-scoped actor cannot list another branch's
            # schedules.  org_admin retains organization-wide access.
            if not branch_accessible(auth, branch_id):
                raise HTTPException(404, "not found")
            q = q.filter(Schedule.branch_id == branch_id)
        elif not auth.is_super_admin and not auth.is_org_admin and auth.branch_id:
            # RBAC-R2: branch-scoped users only see their own branch's
            # schedules even when branch_id is omitted.
            q = q.filter(Schedule.branch_id == auth.branch_id)
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
        # RBAC-R2: verify the caller may access the schedule's stored branch.
        if not branch_accessible(auth, s.branch_id):
            raise HTTPException(404)
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
        # RBAC-R2: verify the caller may modify this schedule's stored branch.
        # Request-body values cannot override authenticated scope.
        if not branch_accessible(auth, s.branch_id):
            raise HTTPException(404)
        if data.slot_templates is not None:
            templates = [t.model_dump() for t in data.slot_templates]
        else:
            templates = None
        ef = (_optional_date(data.effective_from, "effective_from")
              if data.effective_from is not None else None)
        et = (_optional_date(data.effective_to, "effective_to")
              if data.effective_to is not None else None)
        before = _schedule_to_dict(s)
        if templates is not None:
            s.slot_templates = templates
        if data.appointment_model is not None: s.appointment_model = data.appointment_model
        if data.effective_from is not None: s.effective_from = ef
        if data.effective_to is not None: s.effective_to = et
        if s.effective_from and s.effective_to and s.effective_to < s.effective_from:
            raise HTTPException(422, "effective_to must not be earlier than effective_from")
        if data.status is not None: s.status = data.status
        session.flush()
        # F-12: the trail records what the schedule was, not only what it became.
        record_audit(session, service="scheduling", org_id=auth.organization_id,
                     action="schedule.updated", target_type="schedule",
                     target_id=s.id, actor_id=auth.user_id, actor_role=auth.role,
                     branch_id=s.branch_id, before=before, after=_schedule_to_dict(s))
        session.commit()
        return _schedule_to_dict(s)
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
@app.get("/api/v1/schedules/{schedule_id}/available-slots")
def get_available_slots(schedule_id: str, date_str: str = Query(...),
                         auth=Depends(get_current_user)):
    """Available slots for one day, counted per slot window (F-15).

    Three defects lived here.  Every template was published on every weekday
    (``day_of_week`` was ignored), an inactive or out-of-range schedule still
    advertised free slots, and ``booked`` counted only appointments whose
    ``start_time`` equalled the slot start — so a 09:07 booking left the 09:00
    slot looking free while occupying it.  Occupancy is now read once per
    doctor/day and bucketed through ``common.slots.slot_window``, the same
    arithmetic the write path enforces (F-03), so the published number and the
    enforced number cannot disagree.
    """
    from common.models import Appointment, Organization
    from common.config import get_queue_config, reserved_for_capacity
    from common.slots import slot_starts, templates_for_day
    session = SessionFactory()
    try:
        sched = session.query(Schedule).filter(Schedule.id == schedule_id,
            Schedule.organization_id == auth.organization_id).first()
        if not sched: raise HTTPException(404)
        # RBAC-R2: verify the caller may inspect this schedule's stored branch.
        if not branch_accessible(auth, sched.branch_id):
            raise HTTPException(404)
        org = session.query(Organization).filter(
            Organization.id == sched.organization_id).first()
        qcfg = get_queue_config(org.config if org else None)
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            # Named, not bare: a bare ``except`` here would also swallow a
            # programming error and report it to the caller as a bad date.
            raise HTTPException(422, "invalid date, use YYYY-MM-DD")
        payload = {"date": date_str, "schedule_id": schedule_id,
            "doctor_id": sched.doctor_id,
            "appointment_model": sched.appointment_model,
            "walk_in_reserve_mode": qcfg["walk_in_reserve_mode"],
            "walk_in_reserve_value": qcfg["walk_in_reserve_value"],
            "slots": []}
        # An inactive schedule stores no hours, and a day outside the effective
        # range was never open — both used to publish a full grid of free slots.
        if (sched.status or "active").lower() != "active":
            return payload
        if sched.effective_from and target < sched.effective_from:
            return payload
        if sched.effective_to and target > sched.effective_to:
            return payload

        occupancy = session.query(Appointment.start_time, func.count()).filter(
            Appointment.doctor_id == sched.doctor_id,
            Appointment.appointment_date == target,
            Appointment.status.in_(ACTIVE_BOOKING_STATUSES),
            Appointment.start_time.isnot(None)).group_by(Appointment.start_time).all()
        occupancy = [(row[0], row[1]) for row in occupancy if row[0]]

        def _booked_between(window_start, window_end):
            return sum(count for start, count in occupancy
                       if window_start <= start < window_end)

        slots = []
        # One weekday filter, shared with the appointment write path (F-15/F-16):
        # an unusable template publishes nothing, a template for another weekday
        # publishes nothing, and a template without ``day_of_week`` still applies
        # to every day.
        for t in templates_for_day(sched.slot_templates or [], target.weekday()):
            maxp = t["max_patients"]
            for st, et in slot_starts(t):
                booked = _booked_between(st, et)
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
        payload["slots"] = slots
        return payload
    finally:
        session.close()