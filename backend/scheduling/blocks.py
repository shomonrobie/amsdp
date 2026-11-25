"""Blocked periods of a doctor's schedule — BR §15 / MP-16.

BR §15 lists "breaks and unavailable periods" and "blocked dates and periods"
as schedule configuration, and the MVP acceptance requires that a blocked period
**cannot be booked** unless an authorised exception is used.  Before this module
the capability did not exist anywhere in the tree (gap audit GAP-12 / F-20).

What this module owns
---------------------
* the write surface — create a block, read the blocks of a schedule, cancel one;
* the audit events ``schedule.blocked`` and ``schedule.block_cancelled`` with
  before/after values, because BR §13.6 makes configuration changes auditable;
* **not** the enforcement.  ``available-slots`` (this service) and the booking
  guard (``appointment``) both consume :mod:`common.schedule_blocks`, so the
  published availability and the accepted booking cannot disagree about what a
  block covers.

Authorisation
-------------
``schedule.manage`` (held by super/org/branch administrators through the
``schedule.*`` namespace, and **not** by a doctor, who holds ``schedule.read``)
creates and cancels.  Reading the blocks of a schedule needs only an
authenticated staff member with branch scope, like reading the schedule itself.
The organization always comes from the token; a schedule in another tenant is a
**404**, and so is a schedule in a branch the caller may not act on.  There is no
request field that can widen either.

A block is never deleted.  Cancelling stores ``status='cancelled'`` with the
actor and the reason, so the record and the audit trail stay reconcilable.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import AuthContext, branch_accessible, get_current_user, require_permission
from common.database import SessionFactory
from common.models import Schedule, ScheduleBlock
from common.schedule_blocks import BLOCK_STATUSES, normalise_window, window_label
from common.slots import is_hhmm

router = APIRouter()

SERVICE = "scheduling"

#: A block is an operational unavailability, not a sabbatical: one year is the
#: widest range a single row may cover, so a mistyped year is refused instead of
#: silently closing the doctor's calendar for a decade.
MAX_BLOCK_DAYS = 366

#: Same floor as an override reason elsewhere in the tree: a block without a
#: stated reason cannot be reviewed later.
MIN_REASON_LENGTH = 3
MAX_REASON_LENGTH = 200


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BlockCreate(BaseModel):
    """A new blocked period.

    ``end_date`` defaults to ``start_date`` (one day).  Omitting **both** times
    blocks the whole day; supplying one of the two is refused rather than
    guessed, because "half a window" has no safe interpretation.
    """

    start_date: str
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _date(value, field: str):
    text = (value or "").strip()
    if not text:
        raise HTTPException(422, f"{field} must be YYYY-MM-DD")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, f"{field} must be YYYY-MM-DD")


def _optional_date(value, field: str):
    if value is None or not str(value).strip():
        return None
    return _date(value, field)


def _reason(value, field: str = "reason", required: bool = True) -> str:
    text = (value or "").strip()
    if not text:
        if required:
            raise HTTPException(422, f"{field} is required: a blocked period "
                                     "must say why the doctor is unavailable")
        return ""
    if len(text) < MIN_REASON_LENGTH:
        raise HTTPException(422, f"{field} must be at least "
                                 f"{MIN_REASON_LENGTH} characters")
    if len(text) > MAX_REASON_LENGTH:
        raise HTTPException(422, f"{field} must be at most "
                                 f"{MAX_REASON_LENGTH} characters")
    return text


def _window(start_time, end_time):
    """Validate the optional time window; return ``(start, end)`` or ``(None, None)``."""
    start = (start_time or "").strip() or None
    end = (end_time or "").strip() or None
    if start is None and end is None:
        return (None, None)
    if start is None or end is None:
        raise HTTPException(
            422, "a blocked period needs both start_time and end_time, or "
                 "neither for a whole-day block")
    if not is_hhmm(start) or not is_hhmm(end):
        raise HTTPException(422, "start_time and end_time must be HH:MM in "
                                 "24-hour zero-padded form")
    kind, _, _ = normalise_window(start, end)
    if kind != "window":
        raise HTTPException(422, "end_time must be later than start_time")
    return (start, end)



# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def block_dict(row: ScheduleBlock) -> dict:
    """The canonical block payload (label included, window never guessed)."""
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "branch_id": row.branch_id,
        "schedule_id": row.schedule_id,
        "doctor_id": row.doctor_id,
        "doctor_name": row.doctor.name if row.doctor else "",
        "start_date": str(row.start_date) if row.start_date else "",
        "end_date": str(row.end_date) if row.end_date else "",
        "start_time": row.start_time or "",
        "end_time": row.end_time or "",
        "whole_day": not (row.start_time or row.end_time),
        "window_label": window_label(row.start_time, row.end_time),
        "reason": row.reason or "",
        "status": row.status or "active",
        "created_by": row.created_by or "",
        "created_at": str(row.created_at) if row.created_at else "",
        "cancelled_by": row.cancelled_by or "",
        "cancelled_at": str(row.cancelled_at) if row.cancelled_at else "",
        "cancel_reason": row.cancel_reason or "",
    }


def scoped_schedule(session, auth: AuthContext, schedule_id: str) -> Schedule:
    """The schedule this caller may act on, or a non-disclosing 404.

    Tenant first, then branch scope, then the answer — never the other way
    round, so an unknown id and a forbidden id are indistinguishable.
    """
    schedule = session.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.organization_id == auth.organization_id).first()
    if schedule is None or not branch_accessible(auth, schedule.branch_id):
        raise HTTPException(404, "not found")
    return schedule


def _scoped_block(session, auth: AuthContext, schedule: Schedule,
                  block_id: str) -> ScheduleBlock:
    row = session.query(ScheduleBlock).filter(
        ScheduleBlock.id == block_id,
        ScheduleBlock.schedule_id == schedule.id,
        ScheduleBlock.organization_id == auth.organization_id).first()
    if row is None:
        raise HTTPException(404, "not found")
    return row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/api/v1/schedules/{schedule_id}/blocks", status_code=201)
def create_block(schedule_id: str, data: BlockCreate,
                 auth: AuthContext = Depends(require_permission("schedule.manage"))):
    """Block a date range (optionally a time window) of one schedule."""
    start_date = _date(data.start_date, "start_date")
    end_date = _optional_date(data.end_date, "end_date") or start_date
    if end_date < start_date:
        raise HTTPException(422, "end_date must not be earlier than start_date")
    if (end_date - start_date).days + 1 > MAX_BLOCK_DAYS:
        raise HTTPException(
            422, f"a blocked period may cover at most {MAX_BLOCK_DAYS} days")
    start_time, end_time = _window(data.start_time, data.end_time)
    reason = _reason(data.reason)

    session = SessionFactory()
    try:
        schedule = scoped_schedule(session, auth, schedule_id)
        row = ScheduleBlock(
            organization_id=auth.organization_id,
            branch_id=schedule.branch_id,
            schedule_id=schedule.id,
            # The schedule's doctor, not a body field: a body could name another
            # doctor and block somebody who never asked for leave.
            doctor_id=schedule.doctor_id,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            status="active",
            created_by=auth.user_id)
        session.add(row)
        session.flush()
        record_audit(session, service=SERVICE, org_id=auth.organization_id,
                     action="schedule.blocked", target_type="schedule_block",
                     target_id=row.id, actor_id=auth.user_id, actor_role=auth.role,
                     branch_id=schedule.branch_id, after=block_dict(row),
                     reason=reason)
        session.commit()
        return block_dict(row)
    finally:
        session.close()



@router.get("/api/v1/schedules/{schedule_id}/blocks")
def list_blocks(schedule_id: str,
                date_from: str = Query(None), date_to: str = Query(None),
                include_cancelled: bool = Query(False),
                auth: AuthContext = Depends(get_current_user)):
    """The blocks of one schedule, ordered by date then time.

    ``date_from``/``date_to`` filter by **overlap** with the requested range, not
    by containment: a block spanning the range boundary is still reported, which
    is what a calendar cell needs.
    """
    lower = _optional_date(date_from, "date_from")
    upper = _optional_date(date_to, "date_to")
    if lower and upper and upper < lower:
        raise HTTPException(422, "date_to must not be earlier than date_from")
    session = SessionFactory()
    try:
        schedule = scoped_schedule(session, auth, schedule_id)
        q = session.query(ScheduleBlock).filter(
            ScheduleBlock.schedule_id == schedule.id,
            ScheduleBlock.organization_id == auth.organization_id)
        if not include_cancelled:
            q = q.filter(ScheduleBlock.status == "active")
        if lower:
            q = q.filter(ScheduleBlock.end_date >= lower)
        if upper:
            q = q.filter(ScheduleBlock.start_date <= upper)
        rows = q.order_by(ScheduleBlock.start_date,
                          ScheduleBlock.start_time.is_(None).desc(),
                          ScheduleBlock.start_time).all()
        return [block_dict(row) for row in rows]
    finally:
        session.close()


@router.delete("/api/v1/schedules/{schedule_id}/blocks/{block_id}")
def cancel_block(schedule_id: str, block_id: str,
                 reason: str = Query("", description="Why the block was cancelled"),
                 auth: AuthContext = Depends(require_permission("schedule.manage"))):
    """Cancel a block.  The row stays, with the actor and the reason."""
    session = SessionFactory()
    try:
        schedule = scoped_schedule(session, auth, schedule_id)
        row = _scoped_block(session, auth, schedule, block_id)
        status = row.status or "active"
        if status not in BLOCK_STATUSES:
            raise HTTPException(422, f"unknown block status: {status}")
        if status == "cancelled":
            raise HTTPException(422, "block is already cancelled")
        before = block_dict(row)
        row.status = "cancelled"
        row.cancelled_by = auth.user_id
        row.cancelled_at = datetime.now(timezone.utc)
        row.cancel_reason = _reason(reason, field="reason", required=False)
        session.flush()
        record_audit(session, service=SERVICE, org_id=auth.organization_id,
                     action="schedule.block_cancelled", target_type="schedule_block",
                     target_id=row.id, actor_id=auth.user_id, actor_role=auth.role,
                     branch_id=schedule.branch_id, before=before,
                     after=block_dict(row), reason=row.cancel_reason or "")
        session.commit()
        return block_dict(row)
    finally:
        session.close()
