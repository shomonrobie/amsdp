"""Clinic sessions with a chamber — AMSDP-FACILITY-DOCTOR-01.

``schedules`` says *when* a doctor is available; ``schedule_sessions`` says *when
and where*.  This module owns the session rows and keeps
``Schedule.slot_templates`` as their derived projection, so the appointment
calendar (which reads templates) keeps working unchanged while the chamber,
floor and department become real, queryable columns.

Conflict safety has two layers:

* the **database** refuses the deterministic case — one active session per
  ``(room, weekday, start)`` and per ``(doctor, weekday, start)``, through the
  partial unique indexes created in migration ``f7d2b4c6e8a1``;
* the **service** refuses partial overlaps — 09:00–13:00 against 10:00–12:00 in
  the same chamber — inside a transaction that locks the chamber row with
  ``SELECT ... FOR UPDATE``.  An EXCLUDE constraint would need ``btree_gist``,
  which this deployment does not have.

A conflict answers **409**: the request is well-formed, the schedule state
refuses it, and the client can retry with another chamber or time.  A chamber or
department from another branch is a **422**, because the body names something
that cannot belong to the parent resource, and a foreign tenant never reaches
this code at all — the organization always comes from the token.
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from common.audit import record_audit
from common.auth import (
    AuthContext, get_current_user, require_branch_access, require_permission,
)
from common.database import SessionFactory
from common.models import (
    Doctor, DoctorBranch, FacilityDepartment, FacilityFloor, FacilityRoom,
    Schedule, ScheduleSession,
)
from common.slots import normalise_template

router = APIRouter()

SERVICE = "scheduling"

#: ``HH:MM`` in 24-hour form.  Times are stored as zero-padded strings so that
#: lexicographic comparison is chronological comparison, in SQL and in Python.
HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

#: Weekday convention shared with ``Schedule.slot_templates``: 0 = Monday.
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday")

SESSION_STATUSES = ("active", "inactive")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    """A new recurring session inside an existing schedule."""

    day_of_week: int
    start_time: str
    end_time: str
    room_id: Optional[str] = None
    floor_id: Optional[str] = None
    department_id: Optional[str] = None
    slot_duration_minutes: int = 15
    max_patients: int = 1
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class SessionUpdate(BaseModel):
    """Partial update.  ``room_id=None`` means *unchanged*, not *clear*."""

    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room_id: Optional[str] = None
    floor_id: Optional[str] = None
    department_id: Optional[str] = None
    clear_chamber: bool = False
    slot_duration_minutes: Optional[int] = None
    max_patients: Optional[int] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _hhmm(value, field: str) -> str:
    text = (value or "").strip()
    if not HHMM.match(text):
        raise HTTPException(422, f"{field} must be HH:MM in 24-hour form")
    return text


def _minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def _day(value) -> int:
    try:
        day = int(value)
    except (TypeError, ValueError):
        raise HTTPException(422, "day_of_week must be a number 0..6")
    if day < 0 or day > 6:
        raise HTTPException(422, "day_of_week must be a number 0..6")
    return day


def _bounded(value, field: str, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise HTTPException(422, f"{field} must be a number")
    if number < low or number > high:
        raise HTTPException(422, f"{field} must be between {low} and {high}")
    return number


def _date(value, field: str):
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, f"{field} must be YYYY-MM-DD")


def _window(start: str, end: str):
    """Refuse an inverted or empty time window before it reaches the database."""
    if _minutes(end) <= _minutes(start):
        raise HTTPException(422, "end_time must be later than start_time")
    return start, end


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def session_dict(row: ScheduleSession) -> dict:
    """The canonical session payload (chamber names included, ids always)."""
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "branch_id": row.branch_id,
        "schedule_id": row.schedule_id,
        "doctor_id": row.doctor_id,
        "doctor_name": row.doctor.name if row.doctor else "",
        "day_of_week": row.day_of_week,
        "day_name": DAY_NAMES[row.day_of_week] if 0 <= (row.day_of_week or 0) <= 6 else "",
        "start_time": row.start_time,
        "end_time": row.end_time,
        "floor_id": row.floor_id,
        "floor_name": row.floor.name if row.floor else "",
        "department_id": row.department_id,
        "department_name": row.department.name if row.department else "",
        "room_id": row.room_id,
        "room_name": row.room.name if row.room else "",
        "slot_duration_minutes": row.slot_duration_minutes or 15,
        "max_patients": row.max_patients or 1,
        "effective_from": str(row.effective_from) if row.effective_from else "",
        "effective_to": str(row.effective_to) if row.effective_to else "",
        "status": row.status or "active",
        "created_at": str(row.created_at) if row.created_at else "",
        "updated_at": str(row.updated_at) if row.updated_at else "",
    }


def scoped_schedule(session, auth: AuthContext, schedule_id: str) -> Schedule:
    """The schedule row inside the caller's organization, or a 404."""
    schedule = session.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.organization_id == auth.organization_id).first()
    if schedule is None:
        raise HTTPException(404, "not found")
    return schedule


def scoped_session(session, auth: AuthContext, session_id: str) -> ScheduleSession:
    row = session.query(ScheduleSession).filter(
        ScheduleSession.id == session_id,
        ScheduleSession.organization_id == auth.organization_id).first()
    if row is None:
        raise HTTPException(404, "not found")
    return row


def _require_branch_assignment(session, doctor_id: str, branch_id: str) -> None:
    """A doctor can only hold sessions at a branch they are assigned to."""
    row = session.query(DoctorBranch).filter(
        DoctorBranch.doctor_id == doctor_id,
        DoctorBranch.branch_id == branch_id,
        DoctorBranch.status == "active").first()
    if row is None:
        raise HTTPException(
            422, "doctor is not assigned to this branch; assign the branch first")


def resolve_chamber(session, org_id: str, branch_id: str, floor_id=None,
                    department_id=None, room_id=None):
    """Validate the chamber triplet and derive what the client left out.

    Returns ``(floor_id, department_id, room_id)``.  When a room is given, its
    floor and department are authoritative: a request that also names a
    different floor is contradictory, not merely redundant, and is refused.
    """
    if room_id:
        room = session.query(FacilityRoom).filter(
            FacilityRoom.id == room_id,
            FacilityRoom.organization_id == org_id).first()
        if room is None or room.branch_id != branch_id:
            raise HTTPException(422, "chamber not found in this branch")
        if (room.status or "active") != "active":
            raise HTTPException(422, "chamber is retired; choose an active chamber")
        if floor_id and floor_id != room.floor_id:
            raise HTTPException(422, "chamber belongs to a different floor")
        if department_id and department_id != room.department_id:
            raise HTTPException(422, "chamber belongs to a different department")
        return (room.floor_id, room.department_id, room.id)
    if floor_id:
        floor = session.query(FacilityFloor).filter(
            FacilityFloor.id == floor_id,
            FacilityFloor.organization_id == org_id).first()
        if floor is None or floor.branch_id != branch_id:
            raise HTTPException(422, "floor not found in this branch")
        if (floor.status or "active") != "active":
            raise HTTPException(422, "floor is retired; choose an active floor")
    if department_id:
        department = session.query(FacilityDepartment).filter(
            FacilityDepartment.id == department_id,
            FacilityDepartment.organization_id == org_id).first()
        if department is None or department.branch_id != branch_id:
            raise HTTPException(422, "department not found in this branch")
        if (department.status or "active") != "active":
            raise HTTPException(422, "department is retired; choose an active one")
        if floor_id and department.floor_id and department.floor_id != floor_id:
            raise HTTPException(422, "department belongs to a different floor")
    return (floor_id, department_id, None)


def overlapping_session(session, *, org_id: str, doctor_id: str,
                        room_id=None, day_of_week: int, start_time: str,
                        end_time: str, exclude_id=None):
    """The first active session that collides with the proposed window.

    Two windows overlap when ``start < other_end and end > other_start`` — the
    zero-padded ``HH:MM`` strings compare chronologically.  Touching windows
    (09:00–12:00 and 12:00–15:00) do not overlap.
    """
    query = session.query(ScheduleSession).filter(
        ScheduleSession.organization_id == org_id,
        ScheduleSession.day_of_week == day_of_week,
        ScheduleSession.status == "active",
        ScheduleSession.start_time < end_time,
        ScheduleSession.end_time > start_time)
    if exclude_id:
        query = query.filter(ScheduleSession.id != exclude_id)
    for row in query.all():
        if row.doctor_id == doctor_id:
            return ("doctor", row)
        if room_id and row.room_id == room_id:
            return ("chamber", row)
    return (None, None)


def assert_no_conflict(session, *, org_id: str, doctor_id: str,
                       branch_id: str, room_id=None, day_of_week: int,
                       start_time: str, end_time: str, exclude_id=None) -> None:
    """Refuse a double-booking, serialising concurrent attempts on a row lock.

    The lock is taken *before* the overlap read so that a second transaction
    waits for the first to commit and then sees its row — the check cannot be
    raced.  ``btree_gist`` is unavailable here, so the exclusion is cooperative
    rather than declarative; the partial unique indexes still catch the
    exact-start collision even for a caller that bypasses this function.
    """
    if room_id:
        session.query(FacilityRoom).filter(
            FacilityRoom.id == room_id).with_for_update().first()
    else:
        session.query(DoctorBranch).filter(
            DoctorBranch.doctor_id == doctor_id,
            DoctorBranch.branch_id == branch_id).with_for_update().first()
    kind, row = overlapping_session(
        session, org_id=org_id, doctor_id=doctor_id, room_id=room_id,
        day_of_week=day_of_week, start_time=start_time, end_time=end_time,
        exclude_id=exclude_id)
    if kind == "doctor":
        raise HTTPException(
            409, f"this doctor already holds {row.start_time}-{row.end_time} "
                 f"on {DAY_NAMES[day_of_week]}")
    if kind == "chamber":
        raise HTTPException(
            409, f"this chamber is already booked {row.start_time}-"
                 f"{row.end_time} on {DAY_NAMES[day_of_week]}")


def sync_slot_templates(session, schedule: Schedule) -> None:
    """Rebuild ``schedule.slot_templates`` from its active sessions.

    The appointment calendar and ``available-slots`` read this projection, so a
    session must never be persisted without it.  ``session_id``/``room_id`` are
    carried along for the UI; the calendar ignores keys it does not know.

    MP-18 / D-1: the rebuild is a **merge**, not a replacement.  A schedule may
    declare its published hours before it declares any session — ``POST
    /api/v1/schedules`` does exactly that — so a blind rebuild from the session
    rows deleted the doctor's declared clinic hours the first time a session was
    added.  Entries the schedule itself declares carry no ``session_id`` and are
    kept; entries derived from a session always carry one and are always
    rebuilt, which is what lets a retired session's window disappear.
    """
    rows = session.query(ScheduleSession).filter(
        ScheduleSession.schedule_id == schedule.id,
        ScheduleSession.status == "active").all()
    rows.sort(key=lambda r: (r.day_of_week, r.start_time))
    from_sessions = [{
        "day_of_week": row.day_of_week,
        "start_time": row.start_time,
        "end_time": row.end_time,
        "slot_duration_minutes": row.slot_duration_minutes or 15,
        "max_patients": row.max_patients or 1,
        "session_id": row.id,
        "room_id": row.room_id,
    } for row in rows]
    covered = {(t["day_of_week"], t["start_time"], t["end_time"])
               for t in from_sessions}
    declared = []
    for template in (schedule.slot_templates or []):
        normal = normalise_template(template)
        if normal is None or "session_id" in template:
            continue
        key = (normal["day_of_week"], normal["start_time"], normal["end_time"])
        if key in covered:
            continue
        covered.add(key)
        declared.append(template)
    schedule.slot_templates = declared + from_sessions


def windows_map(templates) -> dict:
    """``{"0 09:00-10:00": 1}`` — the payload ``schedule.templates_changed`` uses.

    Kept local rather than imported from ``main``: ``main`` imports this module's
    router, so an import back would be circular.  Both sides derive the window
    through :func:`common.slots.normalise_template`, so they cannot disagree about
    what a window is or which capacity belongs to it.
    """
    out = {}
    for template in templates or []:
        normal = normalise_template(template)
        if normal is None:
            continue
        key = (f"{normal['day_of_week']} "
               f"{normal['start_time']}-{normal['end_time']}")
        out[key] = normal["max_patients"]
    return out


def audit_template_projection(session, schedule: Schedule, auth: AuthContext,
                              reason: str) -> None:
    """Rebuild the schedule projection **and audit the schedule row it changes**.

    MP-18: a session write is also a schedule write.  ``slot_templates`` is the
    projection the calendar and ``available-slots`` read, and
    :func:`sync_slot_templates` overwrites it on every session create, edit and
    retire — so without this event the schedule row changed with no
    ``schedule.*`` audit record, which is exactly the silent mutation MP-18's
    acceptance criterion forbids.

    The event is the same ``schedule.templates_changed`` the schedule ``PATCH``
    writes, with the same ``{"windows": …}`` shape, so one search finds a hours
    change wherever it was made.  It is emitted **only when the published
    windows or their capacity actually moved**: re-chambering a session, or
    editing one whose window is unchanged, records no schedule event because the
    schedule's hours did not change — the room it moved to is the *session's*
    field and is carried by ``schedule.session.update``.
    """
    stored_before = list(schedule.slot_templates or [])
    sync_slot_templates(session, schedule)
    stored_after = list(schedule.slot_templates or [])
    before, after = windows_map(stored_before), windows_map(stored_after)
    if before == after:
        return
    record_audit(session, service=SERVICE, org_id=schedule.organization_id,
                 action="schedule.templates_changed", target_type="schedule",
                 target_id=schedule.id, actor_id=auth.user_id,
                 actor_role=auth.role, branch_id=schedule.branch_id,
                 before={"windows": before}, after={"windows": after},
                 reason=reason)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/v1/schedules/{schedule_id}/sessions")
def list_schedule_sessions(
    schedule_id: str,
    include_retired: bool = Query(False),
    auth: AuthContext = Depends(get_current_user),
):
    """The schedule's sessions, ordered by weekday then start time."""
    session = SessionFactory()
    try:
        schedule = scoped_schedule(session, auth, schedule_id)
        require_branch_access(schedule.branch_id, service=SERVICE)(auth)
        query = session.query(ScheduleSession).filter(
            ScheduleSession.schedule_id == schedule.id)
        if not include_retired:
            query = query.filter(ScheduleSession.status == "active")
        rows = query.all()
        rows.sort(key=lambda r: (r.day_of_week, r.start_time))
        return [session_dict(row) for row in rows]
    finally:
        session.close()


@router.post("/api/v1/schedules/{schedule_id}/sessions", status_code=201)
def create_session(
    schedule_id: str, data: SessionCreate,
    auth: AuthContext = Depends(require_permission("schedule.manage")),
):
    """Add a clinic session — weekday, window and chamber — to a schedule.

    The doctor and the branch come from the schedule, never from the body: a
    session cannot be used to move a doctor into a branch they are not assigned
    to, and it cannot be used to reach another tenant's schedule.
    """
    session = SessionFactory()
    try:
        schedule = scoped_schedule(session, auth, schedule_id)
        require_branch_access(schedule.branch_id, service=SERVICE)(auth)
        _require_branch_assignment(session, schedule.doctor_id, schedule.branch_id)
        day = _day(data.day_of_week)
        start, end = _window(_hhmm(data.start_time, "start_time"),
                             _hhmm(data.end_time, "end_time"))
        floor_id, department_id, room_id = resolve_chamber(
            session, auth.organization_id, schedule.branch_id,
            data.floor_id, data.department_id, data.room_id)
        assert_no_conflict(
            session, org_id=auth.organization_id,
            doctor_id=schedule.doctor_id, branch_id=schedule.branch_id,
            room_id=room_id, day_of_week=day, start_time=start, end_time=end)
        row = ScheduleSession(
            organization_id=auth.organization_id,
            branch_id=schedule.branch_id,
            schedule_id=schedule.id,
            doctor_id=schedule.doctor_id,
            day_of_week=day, start_time=start, end_time=end,
            floor_id=floor_id, department_id=department_id, room_id=room_id,
            slot_duration_minutes=_bounded(
                data.slot_duration_minutes, "slot_duration_minutes", 5, 480),
            max_patients=_bounded(data.max_patients, "max_patients", 1, 500),
            effective_from=(_date(data.effective_from, "effective_from")
                            or schedule.effective_from),
            effective_to=(_date(data.effective_to, "effective_to")
                          or schedule.effective_to),
            status="active",
        )
        session.add(row)
        session.flush()
        audit_template_projection(session, schedule, auth, "session created")
        record_audit(
            session, service=SERVICE, org_id=auth.organization_id,
            action="schedule.session.create", target_type="schedule_session",
            target_id=row.id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=row.branch_id, after=session_dict(row))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                409, "another active session already starts at this time")
        return session_dict(row)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/api/v1/sessions/{session_id}")
def update_session(
    session_id: str, data: SessionUpdate,
    auth: AuthContext = Depends(require_permission("schedule.manage")),
):
    """Move a session, re-chamber it, or retire it.

    Editing re-runs the same conflict check as creation, excluding the row
    itself — otherwise a session could be moved onto a colleague's window.
    """
    session = SessionFactory()
    try:
        row = scoped_session(session, auth, session_id)
        require_branch_access(row.branch_id, service=SERVICE)(auth)
        before = session_dict(row)
        if data.day_of_week is not None:
            row.day_of_week = _day(data.day_of_week)
        if data.start_time is not None:
            row.start_time = _hhmm(data.start_time, "start_time")
        if data.end_time is not None:
            row.end_time = _hhmm(data.end_time, "end_time")
        _window(row.start_time, row.end_time)
        if data.slot_duration_minutes is not None:
            row.slot_duration_minutes = _bounded(
                data.slot_duration_minutes, "slot_duration_minutes", 5, 480)
        if data.max_patients is not None:
            row.max_patients = _bounded(data.max_patients, "max_patients", 1, 500)
        if data.clear_chamber:
            row.floor_id = None
            row.department_id = None
            row.room_id = None
        elif data.room_id is not None:
            row.floor_id, row.department_id, row.room_id = resolve_chamber(
                session, row.organization_id, row.branch_id,
                data.floor_id, data.department_id, data.room_id)
        elif data.floor_id is not None or data.department_id is not None:
            row.floor_id, row.department_id, row.room_id = resolve_chamber(
                session, row.organization_id, row.branch_id,
                data.floor_id if data.floor_id is not None else row.floor_id,
                (data.department_id if data.department_id is not None
                 else row.department_id),
                row.room_id)
        if data.effective_from is not None:
            row.effective_from = _date(data.effective_from, "effective_from")
        if data.effective_to is not None:
            row.effective_to = _date(data.effective_to, "effective_to")
        if data.status is not None:
            status = data.status.strip()
            if status not in SESSION_STATUSES:
                raise HTTPException(
                    422, "status must be one of " + ", ".join(SESSION_STATUSES))
            row.status = status
        if (row.status or "active") == "active":
            _require_branch_assignment(session, row.doctor_id, row.branch_id)
            assert_no_conflict(
                session, org_id=row.organization_id, doctor_id=row.doctor_id,
                branch_id=row.branch_id, room_id=row.room_id,
                day_of_week=row.day_of_week, start_time=row.start_time,
                end_time=row.end_time, exclude_id=row.id)
        session.flush()
        audit_template_projection(session, row.schedule, auth, "session updated")
        after = session_dict(row)
        record_audit(
            session, service=SERVICE, org_id=row.organization_id,
            action="schedule.session.update", target_type="schedule_session",
            target_id=row.id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=row.branch_id, before=before, after=after)
        # Q5: a session's capacity is the number the booking path enforces, so a
        # change to it is its own auditable event rather than a field buried in
        # the generic update payload.
        if before["max_patients"] != after["max_patients"]:
            record_audit(
                session, service=SERVICE, org_id=row.organization_id,
                action="schedule.session.capacity_change",
                target_type="schedule_session", target_id=row.id,
                actor_id=auth.user_id, actor_role=auth.role,
                branch_id=row.branch_id,
                before={"max_patients": before["max_patients"]},
                after={"max_patients": after["max_patients"]},
                reason="session capacity")

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                409, "another active session already starts at this time")
        return session_dict(row)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/sessions/{session_id}")
def retire_session(
    session_id: str,
    auth: AuthContext = Depends(require_permission("schedule.manage")),
):
    """Retire a session by setting ``status="inactive"``.

    Never a hard delete: appointments already booked into this window carry a
    snapshot of the chamber, and the audit trail must keep naming the row.
    Retiring is idempotent — a second call answers the same payload.
    """
    session = SessionFactory()
    try:
        row = scoped_session(session, auth, session_id)
        require_branch_access(row.branch_id, service=SERVICE)(auth)
        if (row.status or "active") == "inactive":
            return session_dict(row)
        before = session_dict(row)
        row.status = "inactive"
        session.flush()
        audit_template_projection(session, row.schedule, auth, "session retired")
        record_audit(
            session, service=SERVICE, org_id=row.organization_id,
            action="schedule.session.retire", target_type="schedule_session",
            target_id=row.id, actor_id=auth.user_id, actor_role=auth.role,
            branch_id=row.branch_id, before=before,
            after={"status": "inactive"})
        session.commit()
        return session_dict(row)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/api/v1/branches/{branch_id}/sessions")
def list_branch_sessions(
    branch_id: str,
    doctor_id: str = Query(None),
    include_retired: bool = Query(False),
    auth: AuthContext = Depends(get_current_user),
):
    """Every active session in a branch — the chamber-occupancy view."""
    require_branch_access(branch_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        query = session.query(ScheduleSession).filter(
            ScheduleSession.organization_id == auth.organization_id,
            ScheduleSession.branch_id == branch_id)
        if doctor_id:
            query = query.filter(ScheduleSession.doctor_id == doctor_id)
        if not include_retired:
            query = query.filter(ScheduleSession.status == "active")
        rows = query.all()
        rows.sort(key=lambda r: (r.day_of_week, r.start_time, r.doctor_id))
        return [session_dict(row) for row in rows]
    finally:
        session.close()


@router.get("/api/v1/doctors/{doctor_id}/sessions")
def list_doctor_sessions(
    doctor_id: str,
    branch_id: str = Query(None),
    include_retired: bool = Query(False),
    auth: AuthContext = Depends(get_current_user),
):
    """A doctor's sessions, with their chambers — the doctor screen's read."""
    session = SessionFactory()
    try:
        doctor = session.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.organization_id == auth.organization_id).first()
        if doctor is None:
            raise HTTPException(404, "not found")
        if branch_id:
            require_branch_access(branch_id, service=SERVICE)(auth)
        query = session.query(ScheduleSession).filter(
            ScheduleSession.doctor_id == doctor.id,
            ScheduleSession.organization_id == auth.organization_id)
        if branch_id:
            query = query.filter(ScheduleSession.branch_id == branch_id)
        if not include_retired:
            query = query.filter(ScheduleSession.status == "active")
        rows = query.all()
        rows.sort(key=lambda r: (r.day_of_week, r.start_time))
        return [session_dict(row) for row in rows]
    finally:
        session.close()




