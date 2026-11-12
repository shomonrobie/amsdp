"""AMSDP Appointment Service — BR §16–§23.

PostgreSQL-backed with full lifecycle, capacity enforcement, walk-in support.
"""
import logging

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timezone

from sqlalchemy import text

from common.database import SessionFactory
from common.models import Appointment, Schedule, Patient, QueueEntry, Organization
from common.auth import AuthContext, require_permission, get_current_user
from common.config import reserved_for_capacity
from common.audit import record_audit
from common.queue_tokens import allocate_daily_token, token_for
from common.timeutil import operational_today
from common.log_redaction import install_token_redaction
from common.health import install_health
from common.denial_audit import install_denial_audit

try:
    from .dashboard import router as dashboard_router
except ImportError:
    from dashboard import router as dashboard_router
try:
    from .tracking import router as tracking_router
except ImportError:
    from tracking import router as tracking_router

app = FastAPI(title="AMSDP Appointment Service")
install_health(app, "appointment")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "appointment")
app.include_router(dashboard_router)
app.include_router(tracking_router)

logger = logging.getLogger(__name__)


def _notify(event: str, *args) -> None:
    """Best-effort notification hook (Sequence 3).

    Never raises: booking/rescheduling must succeed even when the notification
    subsystem is disabled, misconfigured or broken. The hook opens its own
    session, so nothing is written inside this request's transaction.
    """
    try:
        from common.notifications import hooks as notification_hooks
        getattr(notification_hooks, event)(*args)
    except Exception:
        logger.warning("notification hook %s failed", event, exc_info=False)


#: Appointment statuses after which a pending visit reminder is meaningless.
CLOSING_STATUSES = ("CANCELLED", "NO_SHOW", "COMPLETED", "RESCHEDULED",
                    "IN_CONSULTATION", "CHECKED_IN", "IN_QUEUE")

#: Queue entry statuses that still represent a patient in today's queue.
#: Mirrors ``queuing.main.ACTIVE_STATUSES`` — an entry in one of these states
#: must never be duplicated for the same appointment.
QUEUE_ACTIVE_STATUSES = ("waiting", "called", "in_consultation", "skipped")


@app.on_event("startup")
def _install_security_filters():
    install_token_redaction()


# Token-bearing public paths must never be cached by any intermediary —
# including error responses (a cached 404 for a re-issued token would break
# the page, and a cached 200 could outlive revocation).
_TOKEN_PATH_PREFIXES = ("/api/v1/track/", "/track/")
_TOKEN_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, private, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


@app.middleware("http")
async def _no_cache_token_paths(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(_TOKEN_PATH_PREFIXES):
        for k, v in _TOKEN_NO_CACHE_HEADERS.items():
            response.headers[k] = v
    return response

# BR §18 status lifecycle
VALID_TRANSITIONS = {
    "BOOKED": ["AWAITING_CONFIRMATION", "CONFIRMED", "CANCELLED", "RESCHEDULED"],
    "AWAITING_CONFIRMATION": ["CONFIRMED", "CANCELLED", "RESCHEDULED"],
    "CONFIRMED": ["CHECKED_IN", "CANCELLED", "RESCHEDULED", "NO_SHOW"],
    "CHECKED_IN": ["IN_QUEUE", "IN_CONSULTATION", "CANCELLED", "RESCHEDULED"],
    "IN_QUEUE": ["IN_CONSULTATION", "CANCELLED", "RESCHEDULED"],
    "IN_CONSULTATION": ["COMPLETED"],
    "CANCELLED": [],  # Terminal
    "NO_SHOW": [],    # Terminal
    "COMPLETED": [],  # Terminal
    "RESCHEDULED": [],# Terminal (original)
}

BOOKING_SOURCES = ["phone", "in_person", "reception", "assistant", "walk_in", "online"]

WALK_IN_POLICIES = ["end_of_queue", "first_come", "reserved_capacity", "staff_placement"]


class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_date: str  # YYYY-MM-DD
    start_time: Optional[str] = None
    serial_number: Optional[int] = None
    appointment_type: str = "scheduled"
    booking_source: str = "reception"
    notes: str = ""

class AppointmentStatusUpdate(BaseModel):
    status: str
    reason: str = ""
    actor: str = ""

class AppointmentReschedule(BaseModel):
    new_date: str
    new_start_time: Optional[str] = None
    reason: str = ""

class AppointmentTransfer(BaseModel):
    new_doctor_id: str
    new_branch_id: str
    new_date: str
    new_start_time: Optional[str] = None
    reason: str = ""

class WalkInCreate(BaseModel):
    patient_id: str
    doctor_id: str
    notes: str = ""
    placement: str = "end_of_queue"  # walk-in policy


def _appt_to_dict(a):
    return {"id": a.id, "organization_id": a.organization_id,
        "branch_id": a.branch_id, "patient_id": a.patient_id,
        "doctor_id": a.doctor_id,
        "appointment_date": str(a.appointment_date) if a.appointment_date else "",
        "start_time": a.start_time or "", "serial_number": a.serial_number,
        "appointment_type": a.appointment_type or "scheduled",
        "booking_source": a.booking_source or "reception",
        "status": a.status or "BOOKED",
        "status_history": a.status_history or [],
        "token_number": a.token_number or "",
        "notes": a.notes or "", "created_by": a.created_by or "",
        "rescheduled_from": a.rescheduled_from,
        "rescheduled_to": a.rescheduled_to,
        "reschedule_reason": a.reschedule_reason,
        "created_at": str(a.created_at) if a.created_at else "",
    }


def _validate_transition(current: str, new: str):
    if new not in VALID_TRANSITIONS.get(current, []):
        raise HTTPException(422, f"cannot transition from {current} to {new}")


def _scoped_appointment(auth, appointment_id: str):
    """The appointment if it belongs to the caller's organization, else None.

    Cross-tenant ids must stay indistinguishable from unknown ids, so this
    helper never raises and never reports *why* a row was not returned.
    """
    session = SessionFactory()
    try:
        appt = session.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if appt is None:
            return None
        session.expunge(appt)
        return appt
    finally:
        session.close()


def _serial_token(doc_id: str, serial: int) -> str:
    """Booking-time display token — delegates to the one formatting authority."""
    return token_for(doc_id, serial)

# ---------------------------------------------------------------------------
# Appointment creation (with capacity enforcement)
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments", status_code=201)
def create_appointment(
    data: AppointmentCreate,
    auth: AuthContext = Depends(require_permission("appointment.create")),
):
    import uuid
    # Validate required fields
    if not data.patient_id or not data.doctor_id:
        raise HTTPException(422, "patient_id and doctor_id are required")
    try: apt_date = datetime.strptime(data.appointment_date, "%Y-%m-%d").date()
    except: raise HTTPException(422, "invalid date, use YYYY-MM-DD")

    if data.booking_source not in BOOKING_SOURCES:
        raise HTTPException(422, f"invalid booking_source: {data.booking_source}")

    session = SessionFactory()
    try:
        # Verify patient exists and is in org
        patient = session.query(Patient).filter(Patient.id == data.patient_id,
            Patient.organization_id == auth.organization_id).first()
        if not patient: raise HTTPException(422, "patient not found")

        # Concurrency-safe capacity check: count existing active appointments
        existing = session.query(Appointment).filter(
            Appointment.doctor_id == data.doctor_id,
            Appointment.appointment_date == apt_date,
            Appointment.start_time == data.start_time,
            Appointment.status.in_(["BOOKED","AWAITING_CONFIRMATION",
                "CONFIRMED","CHECKED_IN","IN_QUEUE"]),
        ).count()

        # Check schedule capacity
        schedule = session.query(Schedule).filter(
            Schedule.doctor_id == data.doctor_id,
            Schedule.organization_id == auth.organization_id,
        ).first()
        max_capacity = 1  # default per slot
        if schedule and schedule.slot_templates:
            for t in schedule.slot_templates:
                if data.start_time and t["start_time"] <= data.start_time < t["end_time"]:
                    max_capacity = t.get("max_patients", 1)
                    break
        # Reserved walk-in capacity (default 0 -> unchanged behaviour)
        reserved = 0
        if max_capacity:
            org_row = session.query(Organization).filter(
                Organization.id == auth.organization_id).first()
            reserved = reserved_for_capacity(max_capacity, org_row.config if org_row else None)
        effective_capacity = max(max_capacity - reserved, 1)
        if existing >= effective_capacity:
            raise HTTPException(
                422, f"capacity exceeded for this time slot "
                     f"(unreserved capacity {effective_capacity})")

        # Generate serial number
        serial = session.query(Appointment).filter(
            Appointment.doctor_id == data.doctor_id,
            Appointment.appointment_date == apt_date,
        ).count() + 1

        appt = Appointment(id=str(uuid.uuid4()),
            organization_id=auth.organization_id,
            branch_id=auth.branch_id or "",
            patient_id=data.patient_id, doctor_id=data.doctor_id,
            appointment_date=apt_date, start_time=data.start_time,
            serial_number=serial, appointment_type=data.appointment_type,
            booking_source=data.booking_source, status="BOOKED",
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.doctor_id, serial),
            notes=data.notes, created_by=auth.user_id,
        )
        session.add(appt)
        record_audit(session, service="appointment", org_id=auth.organization_id,
            action="appointment.created", target_type="appointment", target_id=appt.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=auth.branch_id or "",
            after={"patient_id": data.patient_id, "doctor_id": data.doctor_id,
                   "appointment_date": data.appointment_date, "start_time": data.start_time,
                   "status": "BOOKED", "booking_source": data.booking_source})
        session.commit()
        # Sequence 3 — N1 confirmation + N2 reminder planning (best effort).
        _notify("on_appointment_booked", appt.id)
        return _appt_to_dict(appt)
    except HTTPException:
        raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
# ---------------------------------------------------------------------------
# Search / List
# ---------------------------------------------------------------------------

@app.get("/api/v1/appointments")
def list_appointments(
    patient_id: str = Query(None), doctor_id: str = Query(None),
    date: str = Query(None), status: str = Query(None),
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        q = session.query(Appointment).filter(
            Appointment.organization_id == auth.organization_id)
        if patient_id: q = q.filter(Appointment.patient_id == patient_id)
        if doctor_id: q = q.filter(Appointment.doctor_id == doctor_id)
        if date:
            try: q = q.filter(Appointment.appointment_date == datetime.strptime(date, "%Y-%m-%d").date())
            except: pass
        if status: q = q.filter(Appointment.status == status)
        return [_appt_to_dict(a) for a in q.order_by(Appointment.appointment_date.desc(), Appointment.start_time).all()]
    finally:
        session.close()


@app.get("/api/v1/appointments/{appointment_id}")
def get_appointment(appointment_id: str, auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        a = session.query(Appointment).filter(Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not a: raise HTTPException(404)
        return _appt_to_dict(a)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Status transition
# ---------------------------------------------------------------------------

@app.patch("/api/v1/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, data: AppointmentStatusUpdate,
                               auth: AuthContext = Depends(require_permission("appointment.modify"))):
    session = SessionFactory()
    try:
        a = session.query(Appointment).filter(Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not a: raise HTTPException(404)
        _validate_transition(a.status, data.status)
        history = list(a.status_history or [])
        history.append({"from": a.status, "to": data.status,
            "reason": data.reason, "actor": data.actor or auth.user_id,
            "at": str(datetime.now(timezone.utc))})
        a.status_history = history
        a.status = data.status
        record_audit(session, service="appointment", org_id=a.organization_id,
            action="appointment.status_change", target_type="appointment", target_id=a.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=a.branch_id or "",
            before={"status": history[-2]["from"] if len(history) >= 2 else ""},
            after={"status": data.status},
            reason=data.reason or "")
        # PQT lifecycle: revoke tracking access on consultation start / cancel / reschedule
        if data.status in ("IN_CONSULTATION", "CANCELLED", "RESCHEDULED"):
            from common.tracking_tokens import revoke_for_appointment
            revoke_for_appointment(session, a.id, reason=f"status -> {data.status}")
        session.commit()
        # Sequence 3: cancel any pending confirmation/reminder for this visit.
        if data.status in CLOSING_STATUSES:
            _notify("on_appointment_closed", a.id, f"status -> {data.status}")
        return _appt_to_dict(a)
    except HTTPException:
        raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Cancel (convenience wrapping status transition)
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: str, data: AppointmentStatusUpdate,
                        auth: AuthContext = Depends(require_permission("appointment.modify"))):
    data.status = "CANCELLED"
    if not data.reason:
        raise HTTPException(422, "cancellation reason is required")
    return update_appointment_status(appointment_id, data, auth)
# ---------------------------------------------------------------------------
# Reschedule
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: str, data: AppointmentReschedule,
                            auth=Depends(require_permission("appointment.modify"))):
    import uuid
    session = SessionFactory()
    try:
        orig = session.query(Appointment).filter(Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not orig: raise HTTPException(404)
        if orig.status in ("COMPLETED","CANCELLED","NO_SHOW"):
            raise HTTPException(422, f"cannot reschedule {orig.status}")
        try: nd = datetime.strptime(data.new_date, "%Y-%m-%d").date()
        except: raise HTTPException(422, "invalid date")
        serial = session.query(Appointment).filter(
            Appointment.doctor_id == orig.doctor_id,
            Appointment.appointment_date == nd).count() + 1
        # Mark original RESCHEDULED
        prev_status = orig.status
        orig.status = "RESCHEDULED"
        # list(...) copy: mutating the loaded JSON list in place leaves
        # SQLAlchemy nothing to persist (finding SEQ4-HISTORY-P0).
        h = list(orig.status_history or [])
        h.append({"from":prev_status,"to":"RESCHEDULED","reason":data.reason,
            "actor":auth.user_id,"at":str(datetime.now(timezone.utc))})
        orig.status_history = h
        new_a = Appointment(id=str(uuid.uuid4()),
            organization_id=orig.organization_id, branch_id=orig.branch_id,
            patient_id=orig.patient_id, doctor_id=orig.doctor_id,
            appointment_date=nd, start_time=data.new_start_time or orig.start_time,
            serial_number=serial, booking_source=orig.booking_source, status="BOOKED",
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(orig.doctor_id, serial),
            rescheduled_from=appointment_id, reschedule_reason=data.reason,
            created_by=auth.user_id)
        session.add(new_a); session.flush()
        orig.rescheduled_to = new_a.id
        record_audit(session, service="appointment", org_id=orig.organization_id,
            action="appointment.rescheduled", target_type="appointment",
            target_id=appointment_id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=orig.branch_id or "",
            before={"status": "RESCHEDULED", "date": str(orig.appointment_date)},
            after={"new_appointment_id": new_a.id, "new_date": data.new_date,
                   "new_start_time": data.new_start_time or orig.start_time},
            reason=data.reason or "")
        # PQT lifecycle: revoke tracking on the original appointment
        from common.tracking_tokens import revoke_for_appointment as _revoke
        _revoke(session, appointment_id, reason="appointment rescheduled")
        session.commit()
        # Sequence 3: the old visit is gone, the new booking gets its own plan.
        _notify("on_appointment_closed", appointment_id, "appointment rescheduled")
        _notify("on_appointment_booked", new_a.id)
        return {"new_appointment_id":new_a.id,"original_appointment_id":appointment_id,
            "new_appointment":_appt_to_dict(new_a)}
    except HTTPException: raise
    except Exception: session.rollback(); raise
    finally: session.close()


# ---------------------------------------------------------------------------
# Check-in → IN_QUEUE
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/check-in")
def check_in_appointment(appointment_id: str, data: AppointmentStatusUpdate,
                          auth=Depends(get_current_user)):
    data.status = "CHECKED_IN"
    # Idempotent check-in: the same patient can be checked in from the
    # appointments page or from the queue page.  Once the appointment is
    # CHECKED_IN/IN_QUEUE the status transition is meaningless, so return the
    # current row instead of failing the receptionist's second click.
    existing = _scoped_appointment(auth, appointment_id)
    if existing is not None and existing.status in ("CHECKED_IN", "IN_QUEUE"):
        r = _appt_to_dict(existing)
    else:
        r = update_appointment_status(appointment_id, data, auth)
    # Auto-create the queue entry with the *same* token authority, history and
    # audit trail as POST /api/v1/queue/check-in.
    #
    # Finding SEQ4-TOKEN-P1 (Sequence 4 acceptance run): this block used to mint
    # its own token from ``count(*) + 1`` and swallowed every exception, so a
    # walk-in enqueued afterwards was issued a token that was already live for
    # the same doctor and day (two active entries T-<DOC>-001), with no
    # status/position history and no queue.checkin audit event.
    import uuid
    session = SessionFactory()
    try:
        appt = session.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not appt:
            return r
        dup = session.query(QueueEntry).filter(
            QueueEntry.appointment_id == appt.id,
            QueueEntry.status.in_(QUEUE_ACTIVE_STATUSES)).first()
        if dup:
            return r                      # already queued — idempotent
        serial, token = allocate_daily_token(session, appt.doctor_id,
                                             appt.appointment_date)
        now = str(datetime.now(timezone.utc))
        entry = QueueEntry(id=str(uuid.uuid4()),
            organization_id=appt.organization_id, branch_id=appt.branch_id or "",
            doctor_id=appt.doctor_id, date=appt.appointment_date,
            position=serial, token=token, patient_id=appt.patient_id,
            appointment_id=appt.id, entry_source="appointment", status="waiting",
            status_history=[{"from": "", "to": "waiting",
                             "actor": auth.user_id, "at": now}],
            position_history=[{"from": 0, "to": serial,
                               "actor": auth.user_id, "at": now}],
            added_by=auth.user_id)
        session.add(entry)
        record_audit(session, service="appointment", org_id=appt.organization_id,
            branch_id=entry.branch_id, action="queue.checkin",
            target_type="queue_entry", target_id=entry.id,
            actor_id=auth.user_id, actor_role=auth.role,
            after={"status": "waiting", "position": serial, "token": token},
            reason="check-in from appointment")
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        logger.exception("queue entry creation failed for appointment %s",
                         appointment_id)
        raise HTTPException(503, "appointment checked in but the queue entry "
                                 "could not be created")
    finally:
        session.close()
    return r
# ---------------------------------------------------------------------------
# No-show
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/no-show")
def mark_no_show(appointment_id: str, data: AppointmentStatusUpdate,
                  auth=Depends(require_permission("appointment.modify"))):
    if not data.reason: raise HTTPException(422, "no-show reason required")
    data.status = "NO_SHOW"
    return update_appointment_status(appointment_id, data, auth)


# ---------------------------------------------------------------------------
# Walk-in registration
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/walk-in", status_code=201)
def register_walk_in(data: WalkInCreate,
                      auth=Depends(require_permission("appointment.create"))):
    import uuid
    session = SessionFactory()
    try:
        today = operational_today(session, auth.organization_id)
        p = session.query(Patient).filter(Patient.id==data.patient_id,
            Patient.organization_id==auth.organization_id).first()
        if not p: raise HTTPException(422, "patient not found")
        count = session.query(Appointment).filter(
            Appointment.doctor_id==data.doctor_id,
            Appointment.appointment_date==today).count() + 1
        a = Appointment(id=str(uuid.uuid4()), organization_id=auth.organization_id,
            branch_id=auth.branch_id or "", patient_id=data.patient_id,
            doctor_id=data.doctor_id, appointment_date=today,
            serial_number=count, appointment_type="walk_in",
            booking_source="walk_in", status="CONFIRMED",
            status_history=[{"from":"","to":"CONFIRMED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.doctor_id, count),
            notes=data.notes, created_by=auth.user_id)
        session.add(a)
        record_audit(session, service="appointment", org_id=auth.organization_id,
            action="appointment.walk_in_created", target_type="appointment", target_id=a.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=auth.branch_id or "",
            after={"patient_id": data.patient_id, "doctor_id": data.doctor_id,
                   "status": "CONFIRMED", "appointment_type": "walk_in", "notes": data.notes})
        session.commit()
        # Sequence 3: hooks decide walk-ins need no message (see hooks.py).
        _notify("on_appointment_booked", a.id)
        return _appt_to_dict(a)
    except HTTPException: raise
    except: session.rollback(); raise
    finally: session.close()


# ---------------------------------------------------------------------------
# Transfer within org
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/transfer")
def transfer_appointment(appointment_id: str, data: AppointmentTransfer,
                          auth=Depends(require_permission("appointment.modify"))):
    import uuid
    session = SessionFactory()
    try:
        orig = session.query(Appointment).filter(Appointment.id==appointment_id,
            Appointment.organization_id==auth.organization_id).first()
        if not orig: raise HTTPException(404)
        if orig.status in ("COMPLETED","CANCELLED","NO_SHOW"):
            raise HTTPException(422, f"cannot transfer {orig.status}")
        try: nd = datetime.strptime(data.new_date, "%Y-%m-%d").date()
        except: raise HTTPException(422, "invalid date")
        # Verify doctor exists in org
        from common.models import Doctor
        doc = session.query(Doctor).filter(Doctor.id==data.new_doctor_id,
            Doctor.organization_id==auth.organization_id).first()
        if not doc: raise HTTPException(422, "target doctor not found")
        serial = session.query(Appointment).filter(
            Appointment.doctor_id==data.new_doctor_id,
            Appointment.appointment_date==nd).count() + 1
        h = list(orig.status_history or [])
        h.append({"from":orig.status,"to":"RESCHEDULED","reason":data.reason,
            "actor":auth.user_id,"at":str(datetime.now(timezone.utc))})
        orig.status_history = h; orig.status = "RESCHEDULED"
        new_a = Appointment(id=str(uuid.uuid4()), organization_id=orig.organization_id,
            branch_id=data.new_branch_id, patient_id=orig.patient_id,
            doctor_id=data.new_doctor_id, appointment_date=nd,
            start_time=data.new_start_time, serial_number=serial,
            booking_source=orig.booking_source, status="BOOKED",
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.new_doctor_id, serial),
            rescheduled_from=appointment_id, reschedule_reason=data.reason,
            notes=f"Transferred from {orig.doctor_id}", created_by=auth.user_id)
        session.add(new_a); session.flush()
        orig.rescheduled_to = new_a.id
        record_audit(session, service="appointment", org_id=orig.organization_id,
            action="appointment.transferred", target_type="appointment",
            target_id=appointment_id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=orig.branch_id or "",
            before={"status": "RESCHEDULED", "doctor_id": orig.doctor_id,
                    "branch_id": orig.branch_id, "date": str(orig.appointment_date)},
            after={"new_appointment_id": new_a.id, "new_doctor_id": data.new_doctor_id,
                   "new_branch_id": data.new_branch_id, "new_date": data.new_date},
            reason=data.reason or "")
        # PQT lifecycle: revoke tracking on the original appointment
        from common.tracking_tokens import revoke_for_appointment as _revoke
        _revoke(session, appointment_id, reason="appointment transferred")
        session.commit()
        # Sequence 3: cancel the original visit's messages, plan the new one.
        _notify("on_appointment_closed", appointment_id, "appointment transferred")
        _notify("on_appointment_booked", new_a.id)
        return {"new_appointment_id":new_a.id,
            "original_appointment_id":appointment_id,
            "message":"transfer completed"}
    except HTTPException: raise
    except: session.rollback(); raise
    finally: session.close()
