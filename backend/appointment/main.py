"""AMSDP Appointment Service — BR §16–§23.

PostgreSQL-backed with full lifecycle, capacity enforcement, walk-in support.
"""
import logging

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, text

from common.database import SessionFactory
from common.models import (Appointment, Branch, Doctor, Schedule,
                           ScheduleSession, Patient, QueueEntry, Organization,
                           UNSCHEDULED_SLOT_KEY)
from common.permissions import check as permission_check

from common.auth import (AuthContext, branch_accessible, get_current_user,
                         require_permission)
from common.config import get_appointment_config, reserved_for_capacity
from common.audit import record_audit
from common.locations import location_label
from common.capacity import SlotFull, claim_seat, release_seat
from common.queue_tokens import allocate_daily_token, token_for
from common.timeutil import operational_now, operational_today
from common.log_redaction import install_token_redaction
from common.health import install_health
from common.denial_audit import install_denial_audit
# AMSDP-APPT-RELIABILITY — the slot arithmetic scheduling publishes (F-02/F-03).
from common.slots import (HHMM_PATTERN, slot_for, templates_for_day)

# AMSDP-CALENDAR-FILTER-01 — one predicate set for every appointment read.
# The grid used to apply no branch scope and no search while the list applied
# both, so the two views disagreed (diagnosis report F-3/F-4).  The helpers are
# imported the same two ways as the sibling routers, because this service is
# copied into its image and run as both a package and a top-level module.
try:
    from .appt_filters import (SEARCH_MAX_LENGTH, apply_branch_scope,
                               apply_filters, appointment_rows, match_index,
                               parse_day, row_context)
except ImportError:  # pragma: no cover — top-level module execution
    from appt_filters import (SEARCH_MAX_LENGTH, apply_branch_scope,  # type: ignore
                              apply_filters, appointment_rows, match_index,
                              parse_day, row_context)

try:
    from .dashboard import router as dashboard_router
except ImportError:
    from dashboard import router as dashboard_router
try:
    from .tracking import router as tracking_router
except ImportError:
    from tracking import router as tracking_router
# MP-23 (PO-11): BR §43 operational reports, read-only aggregates.
try:
    from .reports import router as reports_router
except ImportError:
    from reports import router as reports_router  # type: ignore
try:
    from .symptoms import (router as symptoms_router, apply_onset, copy_symptoms,
                           persist_symptoms, plan_symptoms, symptom_record_payload,
                           symptoms_by_appointment, validate_onset)
except ImportError:
    from symptoms import (router as symptoms_router, apply_onset,  # type: ignore
                          copy_symptoms, persist_symptoms, plan_symptoms,
                          symptom_record_payload, symptoms_by_appointment,
                          validate_onset)

app = FastAPI(title="AMSDP Appointment Service")
install_health(app, "appointment")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "appointment")
app.include_router(dashboard_router)
app.include_router(tracking_router)
app.include_router(reports_router)
# AMSDP-SYMPTOM-01 — the bilingual catalogue the booking form searches.
app.include_router(symptoms_router)

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

#: The status vocabulary the read filters accept.  Derived from the lifecycle
#: table so a status can never be filterable without being reachable: the
#: calendar's dropdown and the list's dropdown are built from ``VALID_TRANSITIONS``
#: in the browser, and an unknown value is a 422 here rather than an empty page.
APPOINTMENT_STATUSES = tuple(VALID_TRANSITIONS)

BOOKING_SOURCES = ["phone", "in_person", "reception", "assistant", "walk_in", "online"]

WALK_IN_POLICIES = ["end_of_queue", "first_come", "reserved_capacity", "staff_placement"]

#: The persisted appointment types (owner decision Q1).  The distinction is
#: stored, never inferred from a missing ``start_time``:
#:
#: * ``scheduled``    — the time is inside availability the doctor published
#:                      (a slot template or a clinic session).  Capacity applies.
#: * ``walk_in``      — staff registered a patient who is at the facility *now*,
#:                      during an active published session.  Capacity applies.
#: * ``unscheduled``  — staff accepted a patient outside every published session
#:                      through the explicit override: a named capability, a
#:                      recorded reason, the organization's daily limit and an
#:                      audit event (``appointment.unscheduled_override``).
APPOINTMENT_TYPES = ("scheduled", "walk_in", "unscheduled")

#: Types an appointment occupies a seat for.  ``unscheduled`` claims a seat in
#: the override pool instead of a slot window, which is why the capacity helper
#: takes the pool key from the caller.
SEATED_TYPES = APPOINTMENT_TYPES


def _require_capability(auth, capability: str, message: str) -> None:
    """403 unless the caller holds *capability* by role or explicit grant.

    One place for the Q1/Q4 refusals: the message names the capability so an
    administrator knows what to grant, and the decision is server-side.
    """
    if not auth.has_capability(capability):
        raise HTTPException(403, message)


class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_date: str  # YYYY-MM-DD
    # F-02: the time is part of the slot's identity, so it is validated at the
    # boundary instead of being stored as whatever string arrived.  A malformed
    # time used to be inserted verbatim and then never matched a slot start.
    start_time: Optional[str] = Field(None, pattern=HHMM_PATTERN)
    serial_number: Optional[int] = None
    #: ``scheduled`` (default) | ``walk_in`` (use the walk-in workflow) |
    #: ``unscheduled`` (outside-session override — Q1).
    appointment_type: str = "scheduled"
    #: Required for ``unscheduled``; recorded and audited verbatim.
    override_reason: str = ""
    #: MP-16 / BR §15: book into a blocked period anyway.  Refused with 403
    #: unless the caller holds ``schedule.manage`` (the authority that creates a
    #: block), and then requires ``override_reason`` — audited, never silent.
    override_block: bool = False
    booking_source: str = "reception"
    notes: str = ""
    # --- AMSDP-SYMPTOM-01 — all optional, nothing is ever pre-filled ---------
    # Catalogue entries and free descriptions are separate fields rather than
    # one mixed list: the receptionist's two acts (pick from the catalogue / type
    # what the patient said) have to stay distinguishable in the record.
    symptom_ids: list[str] = []
    symptom_texts: list[str] = []
    #: One of ``symptoms.ONSET_CODES``; omitted when the question was not asked.
    symptom_onset: Optional[str] = None
    symptom_onset_note: str = ""

class AppointmentStatusUpdate(BaseModel):
    status: str
    reason: str = ""
    actor: str = ""

class AppointmentReschedule(BaseModel):
    new_date: str
    # F-02/F-04: a reschedule writes a time into a slot, so it is validated and
    # capacity-checked exactly like a first booking.
    new_start_time: Optional[str] = Field(None, pattern=HHMM_PATTERN)
    reason: str = ""
    #: MP-16: the destination may be inside a blocked period; same gate and
    #: same mandatory reason as a first booking (``schedule.manage``).
    override_block: bool = False

class AppointmentTransfer(BaseModel):
    new_doctor_id: str
    new_branch_id: str
    new_date: str
    new_start_time: Optional[str] = Field(None, pattern=HHMM_PATTERN)
    reason: str = ""
    #: MP-16: a transfer is a booking at the destination.
    override_block: bool = False

class WalkInCreate(BaseModel):
    patient_id: str
    doctor_id: str
    notes: str = ""
    placement: str = "end_of_queue"  # walk-in policy
    #: Required only when the arrival falls outside every published session —
    #: that booking is persisted as ``unscheduled`` (Q1), never as a normal slot.
    reason: str = ""
    # AMSDP-SYMPTOM-01 — a walk-in is a visit like any other; the receptionist
    # asks the same two questions.  Optional here for the same reason.
    symptom_ids: list[str] = []
    symptom_texts: list[str] = []
    symptom_onset: Optional[str] = None
    symptom_onset_note: str = ""


def _location_label(a) -> str:
    """Human-readable chamber snapshot, e.g. ``2nd Floor / Cardiology / 204``.

    Delegates to ``common.locations`` so the appointment API, the printed slip
    and the QUE-006 queue announcement cannot disagree about how a location
    reads. The queue carries ``room_name`` separately for speech; this label is
    the human-facing form.
    """
    return location_label(a)


def _appt_to_dict(a, symptoms):
    """The canonical appointment payload.

    ``symptoms`` is a required argument, not an optional one: the calendar path
    batches one query for the whole visible range, and a defaulted ``[]`` would
    silently report "no symptoms recorded" for an appointment that has some.
    Passing it explicitly makes a missed call site fail loudly instead.
    """
    return {"id": a.id, "organization_id": a.organization_id,
        "branch_id": a.branch_id, "patient_id": a.patient_id,
        "doctor_id": a.doctor_id,
        "appointment_date": str(a.appointment_date) if a.appointment_date else "",
        "start_time": a.start_time or "", "serial_number": a.serial_number,
        "appointment_type": a.appointment_type or "scheduled",
        # Q1: why an outside-session appointment was accepted.  Empty for the
        # scheduled and in-session walk-in types, which never needed an override.
        "override_reason": a.override_reason or "",
        "booking_source": a.booking_source or "reception",
        "status": a.status or "BOOKED",
        "status_history": a.status_history or [],
        "token_number": a.token_number or "",
        "notes": a.notes or "", "created_by": a.created_by or "",
        "rescheduled_from": a.rescheduled_from,
        "rescheduled_to": a.rescheduled_to,
        "reschedule_reason": a.reschedule_reason,
        # --- Chamber snapshot (AMSDP-FACILITY-DOCTOR-01) --------------------
        # The *_name columns are snapshots written at booking time; the *_id
        # columns are provenance only.  Neither is ever re-derived from the
        # live facility tree, so a reprinted slip keeps its history.
        "session_id": a.session_id or "",
        "schedule_id": a.schedule_id or "",
        "floor_id": a.floor_id or "", "floor_name": a.floor_name or "",
        "department_id": a.department_id or "",
        "department_name": a.department_name or "",
        "room_id": a.room_id or "", "room_name": a.room_name or "",
        "location_label": _location_label(a),
        # --- AMSDP-SYMPTOM-01 — recorded complaints and onset ------------------
        # ``symptoms`` keeps the catalogue/free-text distinction and the
        # booking-time name snapshot; ``symptom_onset`` is "" when the question
        # was not answered ("UNKNOWN" is a different, deliberate answer).
        "symptoms": [symptom_record_payload(row) for row in (symptoms or [])],
        "symptom_onset": a.symptom_onset_code or "",
        "symptom_onset_note": a.symptom_onset_note or "",
        "created_at": str(a.created_at) if a.created_at else "",

    }


def _validate_transition(current: str, new: str):
    if new not in VALID_TRANSITIONS.get(current, []):
        raise HTTPException(422, f"cannot transition from {current} to {new}")


def _serial_token(doc_id: str, serial: int) -> str:
    """Booking-time display token — delegates to the one formatting authority."""
    return token_for(doc_id, serial)


# ---------------------------------------------------------------------------
# Location resolution (AMSDP-FACILITY-DOCTOR-01)
# ---------------------------------------------------------------------------

def _date_covered(row, day) -> bool:
    """True when the row's effective window contains ``day``."""
    if row.effective_from and row.effective_from > day:
        return False
    if row.effective_to and row.effective_to < day:
        return False
    return True


def _may_book_branch(auth, branch_id) -> bool:
    """May this actor *book into* ``branch_id``? (owner decision Q4)

    Deliberately narrower than :func:`branch_accessible`, which governs reads and
    mutations: a central-reception grant is permission to *create* an appointment
    in another branch of the same organization, and nothing else.  Every read,
    reschedule, cancel and check-in keeps using ``branch_accessible``, so the
    grant cannot be turned into cross-branch access to patient records.
    """
    if branch_accessible(auth, branch_id):
        return True
    if branch_id is None:
        return False
    return auth.has_capability("appointment.book_cross_branch", branch_id)


def _resolve_location(session, *, auth, doctor_id: str, organization_id: str,
                      branch_id, appointment_date, start_time,
                      allow_cross_branch: bool = False):
    """Resolve the session — therefore the chamber — a booking lands in.

    Returns ``(schedule, clinic_session)``.  ``clinic_session`` is ``None`` for
    a doctor with a schedule but no facility session at that hour; those
    bookings keep the pre-feature behaviour and simply carry no chamber.

    When the doctor *does* hold an active session that weekday, a time outside
    every session is refused: a booking must never exist without a chamber the
    receptionist can send the patient to.  (Owner decision Q1 keeps that refusal
    for *scheduled* bookings; the walk-in and unscheduled workflows are the
    deliberate way to see a patient outside a session.)

    F-06: only branches the caller may act on are candidates.  With
    ``allow_cross_branch`` — which the booking route sets only after the Q4
    capability check — a branch the caller may *book into* but not read is a
    candidate too.
    """
    weekday = appointment_date.weekday()          # 0 = Monday, as in models
    slot = start_time or ""

    def reachable(candidate) -> bool:
        if allow_cross_branch:
            return _may_book_branch(auth, candidate)
        return branch_accessible(auth, candidate)

    schedule_rows = [row for row in session.query(Schedule).filter(
        Schedule.doctor_id == doctor_id,
        Schedule.organization_id == organization_id).all()
        if reachable(row.branch_id)]
    schedule = None
    for row in (schedule_rows if not branch_id
                else [r for r in schedule_rows if r.branch_id == branch_id]):
        if row.status in (None, "", "active") and _date_covered(row, appointment_date):
            schedule = row
            break
    if schedule is None:
        for row in schedule_rows:
            if row.status in (None, "", "active") and _date_covered(row, appointment_date):
                schedule = row
                break

    query = session.query(ScheduleSession).filter(
        ScheduleSession.organization_id == organization_id,
        ScheduleSession.doctor_id == doctor_id,
        ScheduleSession.day_of_week == weekday,
        ScheduleSession.status == "active")
    if branch_id:
        query = query.filter(ScheduleSession.branch_id == branch_id)
    covering = [row for row in query.all()
                if _date_covered(row, appointment_date)
                and reachable(row.branch_id)]
    matched = [row for row in covering if slot and row.start_time <= slot < row.end_time]
    if covering and slot and not matched:
        raise HTTPException(
            422, "no clinic session covers this time — book inside the "
                 "doctor's session window")
    clinic = matched[0] if matched else None
    if clinic is not None and clinic.schedule is not None:
        schedule = clinic.schedule
    return schedule, clinic


def _session_covering(session, *, auth, doctor_id: str, organization_id: str,
                      day, at: str):
    """The active clinic session of *doctor_id* that contains *at* on *day*.

    Used by the walk-in workflow (Q1): a patient standing at the desk is in an
    active session or is not, and the persisted appointment type differs between
    the two.  Unlike :func:`_resolve_location` this never raises — "no session at
    this hour" is a legitimate answer that selects the override workflow.
    """
    rows = [row for row in session.query(ScheduleSession).filter(
        ScheduleSession.organization_id == organization_id,
        ScheduleSession.doctor_id == doctor_id,
        ScheduleSession.day_of_week == day.weekday(),
        ScheduleSession.status == "active").all()
        if _date_covered(row, day) and branch_accessible(auth, row.branch_id)]
    for row in rows:
        if row.start_time <= at < row.end_time:
            return row
    return None


def _apply_location(appt, schedule, clinic) -> None:
    """Copy the chamber onto the appointment as a permanent snapshot.

    Deliberately denormalised: a slip reprinted after the facility has been
    reorganised must still name the room the patient was sent to.
    """
    if clinic is not None:
        appt.session_id = clinic.id
        appt.schedule_id = clinic.schedule_id
        appt.floor_id = clinic.floor_id
        appt.floor_name = clinic.floor.name if clinic.floor else None
        appt.department_id = clinic.department_id
        appt.department_name = clinic.department.name if clinic.department else None
        appt.room_id = clinic.room_id
        appt.room_name = clinic.room.name if clinic.room else None
    elif schedule is not None:
        appt.schedule_id = schedule.id

# ---------------------------------------------------------------------------
# Write-path guards (AMSDP-APPT-RELIABILITY-01)
#
# Every route that writes a time used to do its own thing: create counted a
# string, reschedule counted nothing, transfer resolved one time and stored
# another, and the serial number was ``count(*) + 1`` in four places.  These
# helpers are the one answer, used by all four.
# ---------------------------------------------------------------------------

#: Statuses that occupy a seat in a slot (BR §23.7).  Same vocabulary the
#: availability read uses (``scheduling.main.ACTIVE_BOOKING_STATUSES``), because
#: a public "3 free" badge and a private "capacity reached" refusal must count
#: the same rows or one of them is lying.
APPOINTMENT_ACTIVE_STATUSES = ("BOOKED", "AWAITING_CONFIRMATION", "CONFIRMED",
                               "CHECKED_IN", "IN_QUEUE")


def _tenant_doctor(session, auth, doctor_id: str):
    """F-05: the doctor if this tenant has her, else ``404``.

    A booking used to accept any ``doctor_id`` string: no query ever proved the
    doctor existed in the tenant, so an appointment could name a doctor that no
    read could resolve.  Unknown and other-tenant ids answer the same 404
    (``.clinerules`` §3).
    """
    doctor = session.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.organization_id == auth.organization_id).first()
    if doctor is None:
        raise HTTPException(404, "doctor not found")
    return doctor


def _lock_doctor(session, doctor_id: str) -> None:
    """F-01: serialise every booking write for one doctor.

    The capacity check reads a count and then inserts; between those two
    statements another request could insert the seat this one is about to
    claim.  Locking the doctor's row makes count-then-insert atomic for that
    doctor *and* makes the serial/token allocation (``count(*) + 1``) safe, in
    one mechanism that needs no schema change.  The lock is released when the
    transaction ends, so a refused booking never holds it beyond the refusal.

    A database-level guarantee (a partial unique index for capacity-1 slots) is
    the stronger answer and belongs in a migration; it cannot be added silently
    here because capacity-N templates share a slot start by design, so the
    choice is recorded as open item Q2 in the gap analysis.
    """
    session.query(Doctor.id).filter(
        Doctor.id == doctor_id).with_for_update().first()


def _published_templates(schedule, clinic, appointment_date) -> list:
    """The slot templates in force for this doctor on this weekday (F-16).

    The matched clinic session comes first: a session is the richer row (it
    carries the chamber, its own duration and its own capacity) and it is what
    ``_resolve_location`` already treats as authoritative.  The schedule's
    ``slot_templates`` follow, so a doctor with sessions still honours a
    template that has no session row.
    """
    templates = []
    if clinic is not None:
        templates.append({
            "day_of_week": clinic.day_of_week,
            "start_time": clinic.start_time,
            "end_time": clinic.end_time,
            "slot_duration_minutes": clinic.slot_duration_minutes,
            "max_patients": clinic.max_patients,
        })
    if schedule is not None:
        templates.extend(schedule.slot_templates or [])
    return templates_for_day(templates, appointment_date.weekday())




# ---------------------------------------------------------------------------
# Appointment creation (with capacity enforcement)
# ---------------------------------------------------------------------------

def _org_config(session, organization_id: str) -> dict:
    """The organization's ``config`` JSON, or ``{}`` when absent."""
    org_row = session.query(Organization).filter(
        Organization.id == organization_id).first()
    return (org_row.config if org_row else None) or {}


def _unscheduled_policy(session, organization_id: str) -> dict:
    """The Q1 override policy in force for this organization."""
    return get_appointment_config(_org_config(session, organization_id))


def _guard_slot(session, *, auth, doctor_id, appointment_date, start_time,
                schedule, clinic, exclude_id=None,
                appointment_type="scheduled") -> Optional[dict]:
    """Which slot does this booking consume, and may it?  (F-02/F-03/F-04 + Q1)

    Three behaviours, in the order the gap analysis asks for them:

    * A time the configuration does not publish is refused with a message that
      says so — no more silent fallback to a capacity of one.  Owner decision Q1
      makes the refusal *explicit*: a scheduled booking outside published hours
      is refused with ``unscheduled_requires_override``, and the way to accept
      the patient is the unscheduled workflow (capability + reason + limit).
    * The seat is charged to the *slot window*, not to the minute string, so a
      09:07 booking consumes the 09:00–09:15 seat (F-03) and the calendar badge
      that counts that window agrees with the guard.
    * What is left after the walk-in reserve is the bookable capacity — the same
      arithmetic the availability read publishes.

    An ``unscheduled`` appointment does not consume a published slot at all: it
    draws on the organization's per-doctor daily override pool, whose size is
    configuration (``appointment_config.unscheduled_daily_limit``) rather than an
    invented unlimited allowance.
    """
    if appointment_type == "unscheduled":
        policy = _unscheduled_policy(session, auth.organization_id)
        if not policy["allow_unscheduled"]:
            raise HTTPException(
                422, "unscheduled_disabled: this organization does not accept "
                     "appointments outside its published sessions")
        limit = policy["unscheduled_daily_limit"]
        booked = session.query(func.count(Appointment.id)).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_type == "unscheduled",
            Appointment.status.in_(APPOINTMENT_ACTIVE_STATUSES),
        ).scalar() or 0
        if booked >= limit:
            raise HTTPException(
                422, f"unscheduled_limit: the outside-session limit of {limit} "
                     f"patient(s) per doctor per day is reached ({booked} "
                     "taken) — book a published slot or ask an administrator")
        return None

    templates = _published_templates(schedule, clinic, appointment_date)
    slot = slot_for(templates, start_time) if start_time else None
    if start_time and templates and slot is None:
        raise HTTPException(
            422, "no_slot_covers_time: this doctor publishes no slot for "
                 f"{appointment_date.isoformat()} covering {start_time} — book "
                 "inside the doctor's configured hours")
    if slot is None:
        # Q1: with no published availability there is no scheduled slot to
        # claim.  The historical fallback (one patient per exact minute, no
        # configuration consulted) is deliberately gone: an arbitrary time must
        # not be presented as a confirmed slot.  The staff override is the way
        # to accept the patient.
        raise HTTPException(
            422, "unscheduled_requires_override: this doctor publishes no "
                 f"availability for {appointment_date.isoformat()}"
                 f"{(' at ' + start_time) if start_time else ''} — use the "
                 "walk-in or unscheduled workflow, which records a reason")

    count = session.query(func.count(Appointment.id)).filter(
        Appointment.organization_id == auth.organization_id,
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.status.in_(APPOINTMENT_ACTIVE_STATUSES))
    if exclude_id:
        count = count.filter(Appointment.id != exclude_id)
    capacity = slot["max_patients"]
    count = count.filter(Appointment.start_time >= slot["start_time"],
                         Appointment.start_time < slot["end_time"])
    booked = count.scalar() or 0

    org_row = session.query(Organization).filter(
        Organization.id == auth.organization_id).first()
    reserved = reserved_for_capacity(capacity,
                                     org_row.config if org_row else None)
    effective = max(capacity - reserved, 1)
    if booked >= effective:
        raise HTTPException(
            422, f"slot_full: capacity {effective} reached for the "
                 f"{slot['start_time']}–{slot['end_time']} slot "
                 f"({booked} booked, 0 free) — choose another slot")
    return slot



def _guard_blocked(session, *, auth, doctor_id, appointment_date, start_time,
                   end_time=None, override_reason="", allow_override=False):
    """BR §15 / MP-16 — refuse a booking that falls inside a blocked period.

    The blocked period is read per **doctor** and per **day**, through the same
    :mod:`common.schedule_blocks` arithmetic ``available-slots`` uses, so the
    hour the grid publishes as unavailable is exactly the hour this guard
    refuses.  A stored row whose window cannot be read covers the whole day
    (fail-closed), which is the direction that cannot produce a phantom booking.

    ``allow_override`` is the authorised exception BR §15 allows.  It is never a
    client boolean: the caller must have passed the capability check
    (``schedule.manage`` — the authority that creates a block, so no new
    privilege is invented) and must supply a reason; the audit event
    ``appointment.block_override`` then records the block, the target slot and
    that reason, in the same transaction as the booking.  An override that is not
    persisted alongside the appointment it excuses is not an audit trail.
    """
    from common.models import ScheduleBlock
    from common.schedule_blocks import first_covering, window_label

    blocks = session.query(ScheduleBlock).filter(
        ScheduleBlock.organization_id == auth.organization_id,
        ScheduleBlock.doctor_id == doctor_id,
        ScheduleBlock.status == "active",
        ScheduleBlock.start_date <= appointment_date,
        ScheduleBlock.end_date >= appointment_date).all()
    block = first_covering(blocks, appointment_date, start_time, end_time)
    if block is None:
        return None
    label = window_label(block.start_time, block.end_time)
    if not allow_override:
        raise HTTPException(
            422,
            "blocked_period: the doctor is unavailable for a blocked period "
            f"covering {block.start_date}–{block.end_date} ({label}) — choose "
            "another time or day; an administrator holding schedule.manage may "
            "override it with a recorded reason")
    record_audit(session, service="appointment", org_id=auth.organization_id,
        action="appointment.block_override", target_type="schedule_block",
        target_id=block.id, actor_id=auth.user_id, actor_role=auth.role,
        branch_id=block.branch_id or auth.branch_id or "",
        before={"block_id": block.id,
                "start_date": str(block.start_date),
                "end_date": str(block.end_date),
                "window": label},
        after={"doctor_id": doctor_id,
               "appointment_date": str(appointment_date),
               "start_time": start_time or "",
               "end_time": end_time or ""},
        reason=override_reason)
    return block


def _claim_seat(session, *, auth, doctor_id, appointment_date, slot,
                appointment_id, appointment_type="scheduled") -> int:
    """Take the appointment's seat through the Q2 database guarantee.

    ``slot`` is what :func:`_guard_slot` returned: the window for a published
    slot, ``None`` for the unscheduled pool.  A :class:`SlotFull` refusal is
    translated into the same vocabulary the guard uses, so a caller sees one
    meaning ("this slot is full") whichever layer refused it.
    """
    if appointment_type == "unscheduled":
        capacity = _unscheduled_policy(
            session, auth.organization_id)["unscheduled_daily_limit"]
        slot_key, slot_end = UNSCHEDULED_SLOT_KEY, None
    else:
        capacity = (slot or {}).get("max_patients") or 1
        slot_key = (slot or {}).get("start_time") or "00:00"
        slot_end = (slot or {}).get("end_time")
    try:
        return claim_seat(
            session, organization_id=auth.organization_id, doctor_id=doctor_id,
            appointment_date=appointment_date, slot_key=slot_key,
            slot_end=slot_end, kind=appointment_type, capacity=capacity,
            appointment_id=appointment_id)
    except SlotFull as exc:
        raise HTTPException(
            422, f"slot_full: capacity {capacity} reached for the {slot_key} "
                 f"slot (0 free) — choose another slot [{exc}]")



def _scoped_write_appointment(session, auth, appointment_id: str):
    """F-08: the appointment this actor may write, locked for the transition.

    Tenant filter, branch scope and a row lock in one place, so a route cannot
    forget one of the three.  ``404`` covers both "unknown" and "not yours".
    """
    appt = session.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.organization_id == auth.organization_id
    ).with_for_update().first()
    if appt is None or not branch_accessible(auth, appt.branch_id):
        raise HTTPException(404, "appointment not found")
    return appt


def _apply_status_transition(session, appt, *, new_status: str, auth,
                             reason: str = "", actor: str = ""):
    """The one status write (F-07).

    Hoisted out of the route so no route can reach a transition without having
    passed a permission dependency first — check-in used to call the status
    route function directly, which is how it skipped ``appointment.modify``.
    Validates the lifecycle, appends history, audits, and revokes tracking
    access for the statuses that end a visit.
    """
    previous = appt.status
    _validate_transition(previous, new_status)
    history = list(appt.status_history or [])
    history.append({"from": previous, "to": new_status, "reason": reason,
                    "actor": actor or auth.user_id,
                    "at": str(datetime.now(timezone.utc))})
    appt.status_history = history
    appt.status = new_status
    record_audit(session, service="appointment", org_id=appt.organization_id,
        action="appointment.status_change", target_type="appointment",
        target_id=appt.id, actor_id=auth.user_id, actor_role=auth.role,
        branch_id=appt.branch_id or "",
        before={"status": previous}, after={"status": new_status},
        reason=reason or "")
    if new_status in ("IN_CONSULTATION", "CANCELLED", "RESCHEDULED"):
        from common.tracking_tokens import revoke_for_appointment
        revoke_for_appointment(session, appt.id, reason=f"status -> {new_status}")
    # Q2: the seat is held only while the appointment occupies it.  Every status
    # outside the active list frees the seat, so the allocation table and the
    # status-based capacity count cannot drift apart.
    if new_status not in APPOINTMENT_ACTIVE_STATUSES:
        release_seat(session, appt.id)
    return appt





@app.post("/api/v1/appointments", status_code=201)
def create_appointment(
    data: AppointmentCreate,
    auth: AuthContext = Depends(require_permission("appointment.create")),
):
    import uuid
    # Validate required fields
    if not data.patient_id or not data.doctor_id:
        raise HTTPException(422, "patient_id and doctor_id are required")
    try:
        apt_date = datetime.strptime(data.appointment_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(422, "invalid date, use YYYY-MM-DD")

    if data.booking_source not in BOOKING_SOURCES:
        raise HTTPException(422, f"invalid booking_source: {data.booking_source}")

    # Q1: the type is part of the request, validated at the boundary, and it
    # decides which capacity policy applies.  ``walk_in`` is refused here on
    # purpose: it has its own workflow, which stamps today's date from the
    # facility clock and resolves the active session for the arrival.
    if data.appointment_type not in APPOINTMENT_TYPES:
        raise HTTPException(
            422, "appointment_type must be one of "
                 + ", ".join(APPOINTMENT_TYPES))
    if data.appointment_type == "walk_in":
        raise HTTPException(
            422, "use_walk_in_workflow: register the patient through "
                 "POST /api/v1/appointments/walk-in")
    override_reason = (data.override_reason or "").strip()
    # MP-16 / BR §15: booking into a blocked period is the authorised exception.
    # It is gated on ``schedule.manage`` — the capability that *creates* a block,
    # so no new privilege is invented and the closed delegable list is unchanged
    # — and it demands a reason before any database work happens.
    block_override = bool(data.override_block)
    if block_override:
        _require_capability(
            auth, "schedule.manage",
            "schedule.manage is required to book into a blocked period")
        if len(override_reason) < 3:
            raise HTTPException(
                422, "reason required: booking into a blocked period must "
                     "record why the doctor accepted the patient")
    if data.appointment_type == "unscheduled":
        # The override is its own capability, needs a stated reason, and is
        # audited.  The role matrix already grants it to the front desk and to
        # doctors; the check is here so a grant (or its revocation) is honoured
        # per request.
        _require_capability(
            auth, "appointment.create_unscheduled",
            "appointment.create_unscheduled is required to book outside the "
            "doctor's published availability")
        if len(override_reason) < 3:
            raise HTTPException(
                422, "reason required: an outside-session appointment must "
                     "record why the patient was accepted")

    session = SessionFactory()
    try:
        # Verify patient exists and is in org
        patient = session.query(Patient).filter(Patient.id == data.patient_id,
            Patient.organization_id == auth.organization_id).first()
        if not patient: raise HTTPException(422, "patient not found")

        # AMSDP-SYMPTOM-01.  Both optional inputs are validated *before* any row
        # is created, so an unknown, retired or other-tenant symptom id fails the
        # whole booking rather than leaving a half-recorded visit behind.
        symptom_plan = plan_symptoms(
            session, organization_id=auth.organization_id,
            symptom_ids=data.symptom_ids, symptom_texts=data.symptom_texts)
        onset_code, onset_note = validate_onset(
            data.symptom_onset, data.symptom_onset_note)

        # F-05: the doctor must be this tenant's before anything is written.
        _tenant_doctor(session, auth, data.doctor_id)
        # Q3: a doctor or assistant books only for the doctor(s) they work for.
        if auth.role in ("doctor", "assistant") and not auth.can_access_doctor(data.doctor_id):
            raise HTTPException(404, "doctor not found")
        # F-01: hold the doctor's row for the whole count-then-insert so two
        # receptionists cannot both take the last seat; Q2 adds the database
        # constraint on top of this lock.
        _lock_doctor(session, data.doctor_id)

        # Resolve the schedule and the clinic session.  The session is the
        # authority on *where* this doctor sits at this hour, so it is resolved
        # before the capacity check: a time outside every session is refused
        # early rather than silently booked into no chamber.  Q4: a holder of
        # ``appointment.book_cross_branch`` may resolve a chamber in a branch
        # they may book into but not read.
        schedule, clinic = _resolve_location(
            session, auth=auth, doctor_id=data.doctor_id,
            organization_id=auth.organization_id, branch_id=auth.branch_id,
            appointment_date=apt_date, start_time=data.start_time,
            allow_cross_branch=auth.has_capability("appointment.book_cross_branch"))

        # F-02/F-03/F-04 + Q1: capacity is charged to the slot window (or to the
        # unscheduled pool), against the same templates the availability read
        # publishes.
        slot = _guard_slot(session, auth=auth, doctor_id=data.doctor_id,
                           appointment_date=apt_date, start_time=data.start_time,
                           schedule=schedule, clinic=clinic,
                           appointment_type=data.appointment_type)

        # MP-16 / BR §15: the blocked period is checked against the *slot the
        # booking takes*, not the minute string, so a 09:07 booking into a
        # 09:00–09:15 slot that is blocked 09:00–09:10 is refused exactly as the
        # availability read published it.
        _guard_blocked(session, auth=auth, doctor_id=data.doctor_id,
                       appointment_date=apt_date,
                       start_time=((slot or {}).get("start_time")
                                   or data.start_time),
                       end_time=(slot or {}).get("end_time"),
                       override_reason=override_reason,
                       allow_override=block_override)

        # Generate serial number.  Safe because the doctor's row is locked
        # above: two concurrent bookings can no longer both read the same
        # count and hand out the same token.
        serial = session.query(Appointment).filter(
            Appointment.doctor_id == data.doctor_id,
            Appointment.appointment_date == apt_date,
        ).count() + 1

        # The appointment's branch follows the resolved session/schedule when
        # there is one, so a doctor working two branches is filed correctly.
        branch_for_appt = (clinic.branch_id if clinic is not None
                           else (schedule.branch_id if schedule is not None
                                 else (auth.branch_id or "")))
        # Q4: booking into a branch the caller cannot *read* is only reached with
        # the cross-branch grant, and it is recorded as such on the audit event.
        cross_branch = (branch_for_appt is not None
                        and not branch_accessible(auth, branch_for_appt))
        appt = Appointment(id=str(uuid.uuid4()),
            organization_id=auth.organization_id,
            branch_id=branch_for_appt,
            patient_id=data.patient_id, doctor_id=data.doctor_id,
            appointment_date=apt_date, start_time=data.start_time,
            serial_number=serial, appointment_type=data.appointment_type,
            booking_source=data.booking_source, status="BOOKED",
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.doctor_id, serial),
            notes=data.notes, created_by=auth.user_id,
            override_reason=override_reason or None,
        )
        _apply_location(appt, schedule, clinic)
        # The onset answer is part of the visit, not of any one symptom: it is
        # recorded even when no symptom was selected.
        appt.symptom_onset_code = onset_code
        appt.symptom_onset_note = onset_note or None
        session.add(appt)
        # Flush before the children: SQLAlchemy orders INSERTs by relationship,
        # and ``appointment_symptoms`` has a foreign key but no ORM relationship
        # to lean on, so the parent row must exist first.
        session.flush()
        # Q2: claim the seat through the database guarantee.  A concurrent winner
        # leaves this request with no allocation, and the whole transaction
        # (appointment, symptoms) rolls back with it.
        seat = _claim_seat(session, auth=auth, doctor_id=data.doctor_id,
                           appointment_date=apt_date, slot=slot,
                           appointment_id=appt.id,
                           appointment_type=data.appointment_type)
        symptom_rows = persist_symptoms(session, appointment=appt,
                                        plan=symptom_plan,
                                        recorded_by=auth.user_id)
        record_audit(session, service="appointment", org_id=auth.organization_id,
            action="appointment.created", target_type="appointment", target_id=appt.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=branch_for_appt,
            after={"patient_id": data.patient_id, "doctor_id": data.doctor_id,
                   "appointment_date": data.appointment_date, "start_time": data.start_time,
                   "status": "BOOKED", "booking_source": data.booking_source,
                   "appointment_type": data.appointment_type,
                   "seat": seat,
                   "session_id": appt.session_id or "",
                   "room_id": appt.room_id or "",
                   "location": _location_label(appt),
                   # Symptom *metadata* only: catalogue ids, counts and the onset
                   # code.  The patient's free-text words stay in the clinical
                   # record (appointment_symptoms) and are not copied into the
                   # audit trail — the trail is append-only and permanent, so it
                   # holds the minimum needed to prove what happened.
                   "symptom_count": len(symptom_rows),
                   "symptom_ids": [row.symptom_id for row in symptom_rows
                                   if row.symptom_id],
                   "symptom_text_count": sum(1 for row in symptom_rows
                                             if row.kind == "free_text"),
                   "symptom_onset": appt.symptom_onset_code or "",
                   # Q4/Q1: which override, if any, this booking needed.
                   "override_reason": override_reason,
                   "cross_branch": cross_branch})

        # An outside-session acceptance gets its own event as well as the
        # creation event: "the published hours were bypassed, by whom, why" is a
        # question the trail must answer without joining anything (Q5).
        if data.appointment_type == "unscheduled":
            record_audit(session, service="appointment",
                org_id=auth.organization_id,
                action="appointment.unscheduled_override",
                target_type="appointment", target_id=appt.id,
                actor_id=auth.user_id, actor_role=auth.role,
                branch_id=branch_for_appt,
                after={"doctor_id": data.doctor_id,
                       "appointment_date": data.appointment_date,
                       "start_time": data.start_time or "",
                       "seat": seat},
                reason=override_reason)

        session.commit()
        # Sequence 3 — N1 confirmation + N2 reminder planning (best effort).
        _notify("on_appointment_booked", appt.id)
        return _appt_to_dict(appt, symptom_rows)
    except HTTPException:
        raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
#: F-17: a calendar read is a *window*, not a table scan.  The route used to
#: accept any pair of bounds — or none — so one request could walk the tenant's
#: entire history.  A year-and-a-bit is the widest window the grid can honestly
#: present (it renders one week at a time), so anything beyond it is a request
#: error rather than a slow query.
CALENDAR_MAX_SPAN_DAYS = 400
#: Width of the window assumed when the caller names no bounds at all: six
#: months either side of today.  Wide enough that no legitimate UI path loses a
#: row (the grid always names its week; the List view pages), narrow enough that
#: a bare request cannot read the tenant's whole life.
CALENDAR_DEFAULT_SPAN_DAYS = 180


def _calendar_window(session, auth, *, single_day, date_from, date_to):
    """The bounded ``(date_from, date_to)`` this calendar read will use (F-17).

    Three rules, all of them about *not* scanning history:

    * ``date`` alone keeps its existing meaning — exactly that one day.
    * no bounds at all becomes "today ± 180 days" (the operational today, so a
      timezone does not move the window).
    * a window wider than ``CALENDAR_MAX_SPAN_DAYS`` is a ``422``; a half-open
      window is completed to the same width rather than left unbounded.

    The values are returned as ISO strings so they flow through
    ``appt_filters.apply_filters`` unchanged, keeping one date-parsing rule.
    """
    if single_day:
        return date_from, date_to
    first = parse_day(date_from, "date_from") if date_from else None
    last = parse_day(date_to, "date_to") if date_to else None
    if first is None and last is None:
        today = operational_today(session, auth.organization_id)
        return (str(today - timedelta(days=CALENDAR_DEFAULT_SPAN_DAYS)),
                str(today + timedelta(days=CALENDAR_DEFAULT_SPAN_DAYS)))
    if first is None:
        first = last - timedelta(days=CALENDAR_DEFAULT_SPAN_DAYS)
    if last is None:
        last = first + timedelta(days=CALENDAR_DEFAULT_SPAN_DAYS)
    if (last - first).days > CALENDAR_MAX_SPAN_DAYS:
        raise HTTPException(
            422, f"date_range_too_wide: the calendar accepts at most "
                 f"{CALENDAR_MAX_SPAN_DAYS} days per request (asked for "
                 f"{(last - first).days}) — page through the window instead")
    return str(first), str(last)



# ---------------------------------------------------------------------------
# Search / List
# ---------------------------------------------------------------------------

@app.get("/api/v1/appointments")
def list_appointments(
    patient_id: str = Query(None), doctor_id: str = Query(None),
    date: str = Query(None), status: str = Query(None),
    date_from: str = Query(None), date_to: str = Query(None),
    q: str = Query("", max_length=SEARCH_MAX_LENGTH),
    branch_id: str = Query(None),
    auth: AuthContext = Depends(require_permission("appointment.read")),
):
    """Every appointment the caller may read in one calendar window.

    This is the Week/Day grid's read.  Since AMSDP-CALENDAR-FILTER-01 it answers
    the *same* question as the List view — the search box, the status filter, the
    doctor filter and the branch picker all apply here too — because it runs the
    same shared predicates in ``appt_filters``.  Before the fix this route took no
    ``q`` and no ``branch_id`` at all: typing in the search box changed the List
    view and left the grid untouched (F-1), and the grid ignored the branch scope
    the token carried (F-3).

    Authorization is unchanged in *kind* and stricter in *reach*:

    * tenant scope is ``organization_id`` from the token;
    * branch scope is derived from the token; a branch-scoped role naming another
      branch gets the non-disclosing 404 ``require_branch_access`` gives;
    * the route now requires ``appointment.read`` like the list does.  It used to
      accept *any* authenticated principal, so a role with no appointment
      permission could still read the day's schedule.

    Each row carries the patient/doctor/branch display names, so the grid no
    longer issues one ``GET /api/v1/patients/{id}`` per patient per week (F-7).

    F-17: the date window is now bounded (``_calendar_window``) — previously any
    request could read the tenant's whole history.
    """
    session = SessionFactory()
    try:
        date_from, date_to = _calendar_window(
            session, auth, single_day=date, date_from=date_from, date_to=date_to)
        rows = appointment_rows(session, auth)
        rows = apply_branch_scope(rows, auth, branch_id)
        if patient_id:
            rows = rows.filter(Appointment.patient_id == patient_id)
        rows = apply_filters(rows, q=q, doctor_id=doctor_id, status=status,
                             date_from=date_from, date_to=date_to,
                             statuses=APPOINTMENT_STATUSES)
        if date:
            rows = rows.filter(Appointment.appointment_date == parse_day(date, "date"))
        # Chronological, as a calendar reads.  ``id`` breaks the tie so two
        # appointments at the same minute cannot swap places between polls.
        rows = rows.order_by(Appointment.appointment_date.asc(),
                             Appointment.start_time.asc(),
                             Appointment.id.asc()).all()
        appts = [row[0] for row in rows]
        symptom_map = symptoms_by_appointment([a.id for a in appts],
                                              session=session)
        can_see_mobile = permission_check("patient.read", auth.role)
        items = []
        for row in rows:
            appt = row[0]
            payload = _appt_to_dict(appt, symptom_map.get(appt.id, []))
            payload.update(row_context(row, can_see_mobile))
            items.append(payload)
        return items
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Match date index — "your search matched, but not on this page of the calendar"
# ---------------------------------------------------------------------------
#
# Owner decision D-2 (Option B): a search reaches every authorized date.  The
# grid can only hold one week, so it cannot show a match three months away — but
# showing nothing and saying nothing is the defect (F-4).  This route answers the
# missing half of the question with **counts only**:
#
#   {"total": 6, "dates": [{"date": "2026-12-01", "count": 2}, ...],
#    "truncated": false}
#
# No patient name, no mobile, no record: the browser learns *where* the matches
# are, never what they contain, and the grid fetches that week through the normal
# route when the receptionist navigates there.  The date list is ordered by
# distance from ``near`` so its cap keeps the dates closest to what is on screen.

@app.get("/api/v1/appointments/matches")
def appointment_match_dates(
    q: str = Query("", max_length=SEARCH_MAX_LENGTH),
    branch_id: str = Query(None),
    doctor_id: str = Query(None),
    status: str = Query(None),
    date_from: str = Query(None), date_to: str = Query(None),
    near: str = Query(None),
    auth: AuthContext = Depends(require_permission("appointment.read")),
):
    """Where the current search matches, across every date the caller may read.

    Same tenant scope, same branch scope, same filters as the grid and the list —
    the counts are the counts of the records those routes would return, so the
    banner can never claim a match the calendar cannot open.
    """
    session = SessionFactory()
    try:
        return match_index(session, auth, q=q, branch_id=branch_id,
                           doctor_id=doctor_id, status=status,
                           date_from=date_from, date_to=date_to, near=near,
                           statuses=APPOINTMENT_STATUSES)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Administrative list — AMSDP-CALENDAR-UX-01 §11
# ---------------------------------------------------------------------------
#
# The calendar grid needs "every appointment in this date window", which is what
# ``GET /api/v1/appointments`` returns.  The List view needs something different:
# a *searched*, *sorted*, *paged* page of records with a matching-record total.
# Filtering that client-side would mean downloading the organization's whole
# history — exactly what the performance rules forbid — so this is the smallest
# compatible extension: one additive read route that reuses the existing payload
# (``_appt_to_dict``) instead of inventing a second row shape.
#
# Nothing here changes a lifecycle rule, a capacity rule or an authorization
# boundary that did not already exist:
#   * tenant scope is still ``organization_id`` (the one tenant key);
#   * branch scope is derived from the **token**, never from the query string;
#   * a branch-scoped caller asking for another branch gets the same
#     non-disclosing 404 ``require_branch_access`` would give;
#   * the patient's mobile number is only returned to a role that may read
#     patient records at all.

#: Page sizes the List view offers.  ``limit`` is bounded by ``le=100`` below so a
#: caller cannot turn this back into an unbounded dump.
LIST_PAGE_SIZES: tuple[int, ...] = (25, 50, 100)

#: Whitelisted sort keys → ORDER BY columns.  An unknown key answers 422 rather
#: than silently falling back: a typo must never return a differently ordered
#: page while the UI claims otherwise.
LIST_SORT_COLUMNS = {
    "date": (Appointment.appointment_date,),
    "patient": (Patient.name,),
    "doctor": (Doctor.name,),
    "branch": (Branch.name,),
    "status": (Appointment.status,),
}


@app.get("/api/v1/appointments/list")
def list_appointments_page(
    q: str = Query("", max_length=SEARCH_MAX_LENGTH),
    branch_id: str = Query(None),
    doctor_id: str = Query(None),
    status: str = Query(None),
    date_from: str = Query(None), date_to: str = Query(None),
    sort: str = Query("date"), order: str = Query("desc"),
    page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100),
    auth: AuthContext = Depends(require_permission("appointment.read")),
):
    """One page of appointments matching the calendar's search and filters.

    ``q`` matches the patient's name, the patient's mobile number (digits only,
    so ``017-0000`` and ``0170000`` agree), the appointment reference and the
    token number — the ways a receptionist identifies an appointment at the desk.
    Bangla names work because ILIKE on UTF-8 compares bytes: Bengali has no case,
    so a substring match is exactly what the search box intends.  The symptom
    catalogue's romanization normaliser is deliberately *not* applied here — that
    would be a second, divergent name-matching rule.

    The predicates themselves live in ``appt_filters`` and are shared with the
    Week/Day grid and the match index, so the three views cannot answer the same
    question differently.  An unknown ``status`` is a **422**, never an empty
    page: the UI's dropdown is built from the lifecycle table, so a value outside
    it means the request is wrong (diagnosis report F-6).
    """
    # --- filter validation (422, never a silently widened result set) --------
    # ``sort``/``order`` shape the SQL and are answered here; the toolbar filters
    # (dates, status, branch) are validated by the shared helpers, so this route
    # cannot drift from the grid and the match index.  A malformed ``date_from``
    # is still a 422: ignoring it would turn "this week" into "everything".
    if sort not in LIST_SORT_COLUMNS:
        raise HTTPException(
            422, f"invalid sort, use one of {sorted(LIST_SORT_COLUMNS)}")
    order = (order or "").lower()
    if order not in ("asc", "desc"):
        raise HTTPException(422, "invalid order, use asc or desc")
    session = SessionFactory()
    try:
        # Same join shape, same branch scope, same filters and same search as the
        # Week/Day grid and the match index — one implementation, in
        # ``appt_filters``, so "the list shows four and the week shows none"
        # cannot happen again (diagnosis report F-3).
        query = appointment_rows(session, auth)
        query = apply_branch_scope(query, auth, branch_id)
        query = apply_filters(query, q=q, doctor_id=doctor_id, status=status,
                              date_from=date_from, date_to=date_to,
                              statuses=APPOINTMENT_STATUSES)

        total = query.count()

        columns = LIST_SORT_COLUMNS[sort]
        ordering = [
            (col.desc() if order == "desc" else col.asc()).nulls_last()
            for col in columns
        ]
        if sort == "date":
            # Within a day the schedule still reads forwards, as on the grid.
            ordering.append(Appointment.start_time.asc().nulls_last())
        else:
            # Stable tie-break: newest first, then chronological.
            ordering += [Appointment.appointment_date.desc(),
                         Appointment.start_time.asc().nulls_last()]
        ordering.append(Appointment.id)

        rows = (query.order_by(*ordering)
                .offset((page - 1) * limit).limit(limit).all())
        appts = [row[0] for row in rows]
        symptom_map = symptoms_by_appointment([a.id for a in appts],
                                              session=session)
        # Contact details follow the *patient-record* permission, not the
        # appointment permission: a role that may not read patients is not shown
        # their number in a table.
        can_see_mobile = permission_check("patient.read", auth.role)

        items = []
        for row in rows:
            appt = row[0]
            payload = _appt_to_dict(appt, symptom_map.get(appt.id, []))
            payload.update(row_context(row, can_see_mobile))
            items.append(payload)

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        }
    finally:
        session.close()


@app.get("/api/v1/appointments/{appointment_id}")
def get_appointment(appointment_id: str,
                    auth: AuthContext = Depends(require_permission("appointment.read"))):
    """One appointment, with the recorded symptoms.

    F-09: this route required authentication only, so any principal in the
    tenant — including one whose role grants no appointment permission at all —
    could read another patient's visit, complaint and onset.  It now asks for
    ``appointment.read`` and applies the same branch scope as every other read;
    an out-of-scope row is a non-disclosing 404 (``.clinerules`` §3).
    """
    session = SessionFactory()
    try:
        a = session.query(Appointment).filter(Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not a or not branch_accessible(auth, a.branch_id):
            raise HTTPException(404)
        recorded = symptoms_by_appointment([a.id], session=session).get(a.id, [])
        return _appt_to_dict(a, recorded)
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
        # F-08: branch scope + row lock in one place.
        a = _scoped_write_appointment(session, auth, appointment_id)
        # F-07: the status write lives in one helper so check-in cannot skip
        # the permission dependency the route declares.
        _apply_status_transition(session, a, new_status=data.status, auth=auth,
                                 reason=data.reason, actor=data.actor)
        session.commit()
        # Sequence 3: cancel any pending confirmation/reminder for this visit.
        if data.status in CLOSING_STATUSES:
            _notify("on_appointment_closed", a.id, f"status -> {data.status}")
        recorded = symptoms_by_appointment([a.id], session=session).get(a.id, [])
        return _appt_to_dict(a, recorded)
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
    # MP-16 / BR §15: the destination may be a blocked period.  Same gate and
    # same mandatory reason as a first booking, checked before any database work.
    block_override = bool(data.override_block)
    override_reason = (data.reason or "").strip()
    if block_override:
        _require_capability(
            auth, "schedule.manage",
            "schedule.manage is required to move a visit into a blocked period")
        if len(override_reason) < 3:
            raise HTTPException(
                422, "reason required: rescheduling into a blocked period must "
                     "record why the doctor accepted the patient")
    session = SessionFactory()
    try:
        # F-08: tenant + branch scope, and the row locked for the move.
        orig = _scoped_write_appointment(session, auth, appointment_id)
        if orig.status in ("COMPLETED","CANCELLED","NO_SHOW"):
            raise HTTPException(422, f"cannot reschedule {orig.status}")
        try:
            nd = datetime.strptime(data.new_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise HTTPException(422, "invalid date")

        new_time = data.new_start_time or orig.start_time
        # F-01: serialise against concurrent bookings for the same doctor, so
        # the seat check below and the serial allocation are both sound.
        _lock_doctor(session, orig.doctor_id)

        # Q1: a reschedule keeps the appointment's category where the category
        # still describes it.  An outside-session appointment stays an override
        # (and keeps its reason); a walk-in moved to a new date/time is a booked
        # time from now on, so it becomes ``scheduled``.
        new_type = ("unscheduled" if (orig.appointment_type or "scheduled") ==
                    "unscheduled" else "scheduled")

        # The new booking carries its own chamber snapshot: the room may well
        # differ from the original (other weekday, other branch).
        new_schedule, new_clinic = _resolve_location(
            session, auth=auth, doctor_id=orig.doctor_id,
            organization_id=orig.organization_id, branch_id=orig.branch_id,
            appointment_date=nd,
            start_time=None if new_type == "unscheduled" else new_time)

        # Mark original RESCHEDULED first: the original seat is being vacated,
        # so it must not count against the destination slot (F-04).  The move
        # and the new booking commit together or not at all.  The transition
        # goes through the one status write (F-07), so history, audit and
        # tracking revocation are the same as a status change made by hand.
        _apply_status_transition(session, orig, new_status="RESCHEDULED",
                                 auth=auth, reason=data.reason)
        session.flush()

        # F-04: the destination slot is capacity-checked exactly like a first
        # booking — a reschedule used to be a way to overbook a full slot.
        new_slot = _guard_slot(session, auth=auth, doctor_id=orig.doctor_id,
                    appointment_date=nd, start_time=new_time,
                    schedule=new_schedule, clinic=new_clinic,
                    exclude_id=orig.id, appointment_type=new_type)

        # MP-16 / BR §15: the destination hour must not be inside a blocked
        # period.  The original is only marked RESCHEDULED inside this same
        # transaction, so a refusal here leaves the visit exactly where it was.
        _guard_blocked(session, auth=auth, doctor_id=orig.doctor_id,
                       appointment_date=nd,
                       start_time=(new_slot or {}).get("start_time") or new_time,
                       end_time=(new_slot or {}).get("end_time"),
                       override_reason=override_reason,
                       allow_override=block_override)

        serial = session.query(Appointment).filter(
            Appointment.doctor_id == orig.doctor_id,
            Appointment.appointment_date == nd).count() + 1
        new_branch = (new_clinic.branch_id if new_clinic is not None
                      else (new_schedule.branch_id if new_schedule is not None
                            else orig.branch_id))
        new_a = Appointment(id=str(uuid.uuid4()),
            organization_id=orig.organization_id, branch_id=new_branch,
            patient_id=orig.patient_id, doctor_id=orig.doctor_id,
            appointment_date=nd, start_time=new_time,
            serial_number=serial, booking_source=orig.booking_source, status="BOOKED",
            appointment_type=new_type,
            override_reason=None if new_type == "scheduled" else orig.override_reason,
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(orig.doctor_id, serial),
            rescheduled_from=appointment_id, reschedule_reason=data.reason,
            created_by=auth.user_id)
        _apply_location(new_a, new_schedule, new_clinic)
        session.add(new_a); session.flush()
        # Q2: the destination seat is claimed through the database guarantee, so a
        # concurrent reschedule into the same last seat cannot overbook it.
        seat = _claim_seat(session, auth=auth, doctor_id=orig.doctor_id,
                           appointment_date=nd, slot=new_slot,
                           appointment_id=new_a.id, appointment_type=new_type)
        # The complaint does not change because the day did: the recorded
        # symptoms are carried to the new visit, and the original rows stay on
        # the original (now RESCHEDULED) appointment as history.
        carried = copy_symptoms(session, source=orig, target=new_a,
                                recorded_by=auth.user_id)
        new_a.symptom_onset_code = orig.symptom_onset_code
        new_a.symptom_onset_note = orig.symptom_onset_note

        orig.rescheduled_to = new_a.id
        record_audit(session, service="appointment", org_id=orig.organization_id,
            action="appointment.rescheduled", target_type="appointment",
            target_id=appointment_id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=orig.branch_id or "",
            before={"status": "RESCHEDULED", "date": str(orig.appointment_date)},
            after={"new_appointment_id": new_a.id, "new_date": data.new_date,
                   "new_start_time": new_time, "seat": seat},
            reason=data.reason or "")
        session.commit()
        # Sequence 3: the old visit is gone, the new booking gets its own plan.
        _notify("on_appointment_closed", appointment_id, "appointment rescheduled")
        _notify("on_appointment_booked", new_a.id)
        return {"new_appointment_id":new_a.id,"original_appointment_id":appointment_id,
            "new_appointment":_appt_to_dict(new_a, carried)}
    except HTTPException: raise
    except Exception: session.rollback(); raise
    finally: session.close()


# ---------------------------------------------------------------------------
# Check-in → IN_QUEUE
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/check-in")
def check_in_appointment(appointment_id: str, data: AppointmentStatusUpdate,
                          auth: AuthContext = Depends(require_permission("appointment.check_in"))):
    """Check a patient in and put her in the queue, in one transaction.

    F-07: this route used to depend on ``get_current_user`` and then call the
    status route function directly, which is how it wrote a status change
    without the ``appointment.modify`` check the status route declares — anyone
    able to read the calendar could push a patient into the queue.  It also
    committed twice: when the queue allocation failed the appointment stayed
    CHECKED_IN with no queue entry behind it.  One permission dependency, one
    transaction, and the status write goes through the shared helper.

    Owner decision Q3: check-in is its own capability
    (``appointment.check_in``), held by the front desk, by branch/organization
    administrators, by an assistant **for their assigned doctor(s)** and by a
    doctor **for their own patients**.  It is deliberately not
    ``appointment.modify``: a doctor checking a patient in must not thereby gain
    the ability to cancel, reschedule or transfer.
    """
    import uuid
    session = SessionFactory()
    try:
        # F-08: tenant + branch scope, and the row locked for the transition.
        appt = _scoped_write_appointment(session, auth, appointment_id)
        # Q3: doctor/assistant ownership.  ``can_access_doctor`` fails closed when
        # the caller has no active assignment, so an unassigned doctor cannot
        # check in anybody — not even a patient of the doctor they used to cover.
        if auth.role in ("doctor", "assistant") and not auth.can_access_doctor(appt.doctor_id):
            raise HTTPException(404, "appointment not found")
        # Idempotent check-in: the same patient can be checked in from the
        # appointments page or from the queue page, so a second click must not
        # fail on an illegal CHECKED_IN -> CHECKED_IN transition.
        if appt.status not in ("CHECKED_IN", "IN_QUEUE"):
            _apply_status_transition(session, appt, new_status="CHECKED_IN",
                                     auth=auth, reason=data.reason,
                                     actor=data.actor)
            session.flush()

        # Auto-create the queue entry with the *same* token authority, history
        # and audit trail as POST /api/v1/queue/check-in.
        #
        # Finding SEQ4-TOKEN-P1 (Sequence 4 acceptance run): this block used to
        # mint its own token from ``count(*) + 1`` and swallow every exception,
        # so a walk-in enqueued afterwards was issued a token that was already
        # live for the same doctor and day (two active entries T-<DOC>-001),
        # with no status/position history and no queue.checkin audit event.
        dup = session.query(QueueEntry).filter(
            QueueEntry.appointment_id == appt.id,
            QueueEntry.status.in_(QUEUE_ACTIVE_STATUSES)).first()
        if dup is None:
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
        recorded = symptoms_by_appointment([appt.id], session=session).get(appt.id, [])
        return _appt_to_dict(appt, recorded)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        logger.exception("check-in failed for appointment %s", appointment_id)
        raise HTTPException(503, "check-in could not be completed — the "
                                 "appointment and the queue were left unchanged")
    finally:
        session.close()
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
    """Register a patient who is at the facility now (owner decision Q1).

    Two outcomes, both persisted explicitly and neither inferred from a missing
    time:

    * an active published session covers the arrival → ``walk_in``, charged to
      that session's slot capacity;
    * nothing covers it → the outside-session override → ``unscheduled``, which
      needs ``appointment.create_unscheduled``, a stated reason, the
      organization's daily limit, and writes ``appointment.unscheduled_override``
      to the trail.

    Whichever path runs, the appointment does **not** create a queue token:
    check-in is the separate lifecycle transition.  Capacity is claimed through
    the same Q2 seat allocation every other booking path uses.
    """
    import uuid
    reason = (data.reason or "").strip()
    session = SessionFactory()
    try:
        today = operational_today(session, auth.organization_id)
        arrival = operational_now(session, auth.organization_id).strftime("%H:%M")
        p = session.query(Patient).filter(Patient.id==data.patient_id,
            Patient.organization_id==auth.organization_id).first()
        if not p: raise HTTPException(422, "patient not found")
        # F-05: the doctor must be this tenant's; F-01: hold her row while the
        # daily serial is allocated, so two walk-ins cannot share a token.
        _tenant_doctor(session, auth, data.doctor_id)
        # Q3: a doctor or assistant may register only their own patients' visits.
        if auth.role in ("doctor", "assistant") and not auth.can_access_doctor(data.doctor_id):
            raise HTTPException(404, "doctor not found")
        _lock_doctor(session, data.doctor_id)

        # Q1: is the patient inside a session the doctor is actually holding?
        clinic = _session_covering(
            session, auth=auth, doctor_id=data.doctor_id,
            organization_id=auth.organization_id, day=today, at=arrival)
        if clinic is not None:
            appt_type = "walk_in"
            schedule = clinic.schedule
        else:
            # Outside every session: permitted only through the explicit override.
            _require_capability(
                auth, "appointment.create_unscheduled",
                "appointment.create_unscheduled is required to register a "
                "patient outside the doctor's published sessions")
            if len(reason) < 3:
                raise HTTPException(
                    422, "reason required: this arrival is outside the doctor's "
                         "published session, so record why the patient is being "
                         "accepted")
            appt_type = "unscheduled"
            schedule = None

        # Capacity first (F-02/F-03/F-04 semantics), then the seat claim (Q2).
        slot = _guard_slot(session, auth=auth, doctor_id=data.doctor_id,
                           appointment_date=today, start_time=arrival,
                           schedule=schedule, clinic=clinic,
                           appointment_type=appt_type)

        count = session.query(Appointment).filter(
            Appointment.doctor_id==data.doctor_id,
            Appointment.appointment_date==today).count() + 1
        w_branch = (clinic.branch_id if clinic is not None
                    else (schedule.branch_id if schedule is not None
                          else (auth.branch_id or "")))
        a = Appointment(id=str(uuid.uuid4()), organization_id=auth.organization_id,
            branch_id=w_branch, patient_id=data.patient_id,
            doctor_id=data.doctor_id, appointment_date=today,
            start_time=arrival,
            serial_number=count, appointment_type=appt_type,
            booking_source="walk_in", status="CONFIRMED",
            status_history=[{"from":"","to":"CONFIRMED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.doctor_id, count),
            notes=data.notes, created_by=auth.user_id,
            override_reason=reason or None)
        _apply_location(a, schedule, clinic)
        symptom_plan = plan_symptoms(
            session, organization_id=auth.organization_id,
            symptom_ids=data.symptom_ids, symptom_texts=data.symptom_texts)
        onset_code, onset_note = validate_onset(
            data.symptom_onset, data.symptom_onset_note)
        a.symptom_onset_code = onset_code
        a.symptom_onset_note = onset_note or None
        session.add(a)
        session.flush()          # parent row before its symptom rows (see create)
        seat = _claim_seat(session, auth=auth, doctor_id=data.doctor_id,
                           appointment_date=today, slot=slot,
                           appointment_id=a.id, appointment_type=appt_type)
        symptom_rows = persist_symptoms(session, appointment=a,
                                        plan=symptom_plan,
                                        recorded_by=auth.user_id)
        record_audit(session, service="appointment", org_id=auth.organization_id,
            action="appointment.walk_in_created", target_type="appointment", target_id=a.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=w_branch,
            after={"patient_id": data.patient_id, "doctor_id": data.doctor_id,
                   "status": "CONFIRMED", "appointment_type": appt_type,
                   "arrival_time": arrival, "seat": seat, "notes": data.notes,
                   "override_reason": reason,
                   "session_id": a.session_id or "",
                   "location": _location_label(a),
                   "symptom_count": len(symptom_rows),
                   "symptom_ids": [row.symptom_id for row in symptom_rows
                                   if row.symptom_id],
                   "symptom_text_count": sum(1 for row in symptom_rows
                                             if row.kind == "free_text"),
                   "symptom_onset": a.symptom_onset_code or ""},
            reason=reason)
        # Q5: the override is its own event, in addition to the registration.
        if appt_type == "unscheduled":
            record_audit(session, service="appointment",
                org_id=auth.organization_id,
                action="appointment.unscheduled_override",
                target_type="appointment", target_id=a.id,
                actor_id=auth.user_id, actor_role=auth.role, branch_id=w_branch,
                after={"doctor_id": data.doctor_id,
                       "appointment_date": str(today),
                       "arrival_time": arrival, "seat": seat},
                reason=reason)

        session.commit()
        # Sequence 3: hooks decide walk-ins need no message (see hooks.py).
        _notify("on_appointment_booked", a.id)
        return _appt_to_dict(a, symptom_rows)
    except HTTPException: raise
    except Exception: session.rollback(); raise
    finally: session.close()


# ---------------------------------------------------------------------------
# Transfer within org
# ---------------------------------------------------------------------------

@app.post("/api/v1/appointments/{appointment_id}/transfer")
def transfer_appointment(appointment_id: str, data: AppointmentTransfer,
                          auth=Depends(require_permission("appointment.modify"))):
    import uuid
    # MP-16 / BR §15: a transfer books at the destination, which may be blocked.
    block_override = bool(data.override_block)
    override_reason = (data.reason or "").strip()
    if block_override:
        _require_capability(
            auth, "schedule.manage",
            "schedule.manage is required to move a visit into a blocked period")
        if len(override_reason) < 3:
            raise HTTPException(
                422, "reason required: transferring into a blocked period must "
                     "record why the doctor accepted the patient")
    session = SessionFactory()
    try:
        # F-08: tenant + branch scope, and the original row locked for the move.
        orig = _scoped_write_appointment(session, auth, appointment_id)
        if orig.status in ("COMPLETED","CANCELLED","NO_SHOW"):
            raise HTTPException(422, f"cannot transfer {orig.status}")
        try:
            nd = datetime.strptime(data.new_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise HTTPException(422, "invalid date")
        # F-05: the target doctor must be this tenant's, and F-10: the target
        # branch must exist *in this tenant* and be one the caller may act on —
        # it used to be written verbatim, producing rows no scoped read could
        # return.
        _tenant_doctor(session, auth, data.new_doctor_id)
        if data.new_branch_id:
            target_branch = session.query(Branch).filter(
                Branch.id == data.new_branch_id,
                Branch.organization_id == auth.organization_id).first()
            if target_branch is None or not branch_accessible(auth, data.new_branch_id):
                raise HTTPException(404, "branch not found")
        # F-01: serialise with concurrent bookings for the target doctor.
        _lock_doctor(session, data.new_doctor_id)

        # F-11: one time, resolved once and stored.  The snapshot used to be
        # resolved for ``new_start_time or orig.start_time`` while the row was
        # written with ``new_start_time`` alone, so a transfer without a new
        # time carried the chamber of the old hour.
        t_time = data.new_start_time or orig.start_time
        t_schedule, t_clinic = _resolve_location(
            session, auth=auth, doctor_id=data.new_doctor_id,
            organization_id=orig.organization_id, branch_id=data.new_branch_id,
            appointment_date=nd, start_time=t_time)

        # The original visit ends as RESCHEDULED through the one status write
        # (F-07), before the destination is counted (F-04).
        _apply_status_transition(session, orig, new_status="RESCHEDULED",
                                 auth=auth, reason=data.reason)
        session.flush()

        # F-04: the destination slot obeys the same capacity rule as any other
        # booking; a transfer used to ignore capacity entirely.
        t_slot = _guard_slot(session, auth=auth, doctor_id=data.new_doctor_id,
                    appointment_date=nd, start_time=t_time,
                    schedule=t_schedule, clinic=t_clinic,
                    exclude_id=orig.id)

        # MP-16 / BR §15: the destination hour must not be inside a blocked
        # period of the receiving doctor.  The move is uncommitted at this point,
        # so a refusal here changes nothing.
        _guard_blocked(session, auth=auth, doctor_id=data.new_doctor_id,
                       appointment_date=nd,
                       start_time=(t_slot or {}).get("start_time") or t_time,
                       end_time=(t_slot or {}).get("end_time"),
                       override_reason=override_reason,
                       allow_override=block_override)

        serial = session.query(Appointment).filter(
            Appointment.doctor_id==data.new_doctor_id,
            Appointment.appointment_date==nd).count() + 1
        t_branch = t_clinic.branch_id if t_clinic is not None else data.new_branch_id
        new_a = Appointment(id=str(uuid.uuid4()), organization_id=orig.organization_id,
            branch_id=t_branch, patient_id=orig.patient_id,
            doctor_id=data.new_doctor_id, appointment_date=nd,
            start_time=t_time, serial_number=serial,
            booking_source=orig.booking_source, status="BOOKED",
            appointment_type="scheduled",
            status_history=[{"from":"","to":"BOOKED","at":str(datetime.now(timezone.utc))}],
            token_number=_serial_token(data.new_doctor_id, serial),
            rescheduled_from=appointment_id, reschedule_reason=data.reason,
            notes=f"Transferred from {orig.doctor_id}", created_by=auth.user_id)
        _apply_location(new_a, t_schedule, t_clinic)
        session.add(new_a); session.flush()
        # Q2: the transfer's destination seat is claimed like any other booking.
        seat = _claim_seat(session, auth=auth, doctor_id=data.new_doctor_id,
                           appointment_date=nd, slot=t_slot,
                           appointment_id=new_a.id, appointment_type="scheduled")
        # Same reasoning as reschedule: a transfer moves the visit, not the
        # complaint, so the recorded symptoms and onset go with it.
        copy_symptoms(session, source=orig, target=new_a, recorded_by=auth.user_id)
        new_a.symptom_onset_code = orig.symptom_onset_code
        new_a.symptom_onset_note = orig.symptom_onset_note

        orig.rescheduled_to = new_a.id
        record_audit(session, service="appointment", org_id=orig.organization_id,
            action="appointment.transferred", target_type="appointment",
            target_id=appointment_id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=orig.branch_id or "",
            before={"status": "RESCHEDULED", "doctor_id": orig.doctor_id,
                    "branch_id": orig.branch_id, "date": str(orig.appointment_date)},
            after={"new_appointment_id": new_a.id, "new_doctor_id": data.new_doctor_id,
                   "new_branch_id": data.new_branch_id, "new_date": data.new_date,
                   "new_start_time": t_time, "seat": seat},
            reason=data.reason or "")
        session.commit()
        # Sequence 3: cancel the original visit's messages, plan the new one.
        _notify("on_appointment_closed", appointment_id, "appointment transferred")
        _notify("on_appointment_booked", new_a.id)
        return {"new_appointment_id":new_a.id,
            "original_appointment_id":appointment_id,
            "message":"transfer completed"}
    except HTTPException: raise
    except Exception: session.rollback(); raise
    finally: session.close()
