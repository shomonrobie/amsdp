"""Operational reports — BR §43 (MP-23, Product Owner decision PO-11, 2026-11-26).

**Scope is exactly BR §43, neither widened nor narrowed.**  The approved rule
permits: appointments by day, doctor or branch; booked/completed/cancelled/
no-show counts; walk-in counts; queue activity; booking-source counts; and
schedule utilization *where meaningful for the appointment model*.  It forbids
revenue, billing, payment-settlement and clinical-performance analytics — so no
endpoint here, and no field in any payload, computes money or grades a doctor.
The negative control is asserted in the tests, not merely intended.

**Every figure reconciles or it is not reported.**  Each dimension is a
``GROUP BY`` over the same scoped row set, and the response carries a
``reconciliation`` block naming the identities that hold:

* ``appointments_total == sum(status_counts.values())``
* ``sum(by_day) == sum(by_doctor) == sum(by_branch) == appointments_total``
* ``sum(booking_sources) == appointments_total``
* ``queue_activity.entries == sum(queue_activity.by_status.values())``

A reader can therefore check the report against the tables for a fixed day
without trusting this module (MP-23 acceptance).

**Definitions that BR §43 leaves to the model, stated once:**

``booked``      Appointments still holding a booking status (``BOOKED``,
                ``AWAITING_CONFIRMATION``, ``CONFIRMED``) — booked but not yet
                seen.  ``CHECKED_IN`` / ``IN_QUEUE`` / ``IN_CONSULTATION`` are
                *present* and are reported separately, so
                ``booked + completed + cancelled + no_show`` is deliberately not
                forced to equal the total.
``walk_ins``    ``appointments.booking_source == 'walk_in'`` — the same
                convention ``/dashboard/today`` already uses.
``queue_activity``
                Live queue entries for the period: how many were created, their
                current states, how many transitions and calls their
                ``status_history`` records, and the average wait and service
                times those histories imply.
``utilisation`` Published seat capacity versus claimed seats, per doctor and per
                day, from ``schedule_sessions`` (capacity) and
                ``slot_allocations`` (claims).  It is reported only where the
                model can actually compute it: a doctor with no active session on
                a weekday contributes capacity 0 and is listed with
                ``capacity: 0`` rather than being silently dropped or being given
                an invented denominator.  ``UNSCHEDULED`` allocations are seats
                taken *outside* published capacity and are counted separately, so
                the percentage can exceed 100 — which is a true statement about
                the day, not an error to hide.

**Authorization** (``.clinerules`` §3): the organisation always comes from the
token, never from the query string.  A ``branch_id`` the caller does not hold is
a non-disclosing **404** through ``require_branch_access``, and a ``doctor_id``
outside the organisation is also a 404.  The capability is the existing
``appointment.read`` — reports read appointments, so they add no new privilege to
the matrix; ``org_admin``/``branch_admin`` reach it through their
``appointment.*`` namespace.
"""

from collections import OrderedDict
from datetime import date as date_cls, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from common.auth import (AuthContext, get_current_user, require_branch_access,
                         require_permission)
from common.models import (Appointment, Doctor, QueueEntry, ScheduleSession,
                           SlotAllocation, UNSCHEDULED_SLOT_KEY)
from common.database import SessionFactory
from common.timeutil import operational_today

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

#: Lifecycle statuses in the order BR §8.3 lists them.  A status the model gains
#: later still appears in ``status_counts`` (iterated from the rows), so this
#: tuple orders the report; it never filters it.
LIFECYCLE = ("BOOKED", "AWAITING_CONFIRMATION", "CONFIRMED", "CHECKED_IN",
             "IN_QUEUE", "IN_CONSULTATION", "COMPLETED", "CANCELLED", "NO_SHOW",
             "RESCHEDULED")

#: The four BR §43 headline counts, and which stored statuses each covers.  The
#: "booked" definition is the one that keeps the four figures disjoint: an
#: appointment that has been checked in is present, not booked-and-waiting.
HEADLINE = OrderedDict((
    ("booked", ("BOOKED", "AWAITING_CONFIRMATION", "CONFIRMED")),
    ("completed", ("COMPLETED",)),
    ("cancelled", ("CANCELLED",)),
    ("no_show", ("NO_SHOW",)),
))

#: Present-in-facility statuses, reported so a reader can get from the headline
#: figures back to the total without subtraction.
PRESENT = ("CHECKED_IN", "IN_QUEUE", "IN_CONSULTATION")

#: Queue entry states, in the order the board shows them.
QUEUE_STATES = ("waiting", "called", "in_consultation", "skipped", "completed",
                "cancelled", "no_show")

#: A period longer than this is refused rather than left to run: a report is an
#: operational aid, and an unbounded scan is a denial-of-service on the database.
MAX_PERIOD_DAYS = 366


def _day(value: str, field: str) -> date_cls:
    """A strict ``YYYY-MM-DD`` day, or a 422.

    ``strptime`` alone accepts ``2026-1-5``; the round-trip pins the documented
    form so the report cannot answer about a different day than the one asked
    for (the same reasoning as ``/dashboard/today``).
    """
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(422, f"{field} must use YYYY-MM-DD")
    if parsed.isoformat() != value:
        raise HTTPException(422, f"{field} must use YYYY-MM-DD")
    return parsed


def _minutes(hhmm: Any) -> Optional[int]:
    """``HH:MM`` as minutes past midnight, or ``None`` if it is not that."""
    if not isinstance(hhmm, str) or len(hhmm) != 5 or hhmm[2] != ":":
        return None
    try:
        hours, mins = int(hhmm[:2]), int(hhmm[3:])
    except ValueError:
        return None
    if not (0 <= hours <= 24 and 0 <= mins < 60):
        return None
    return hours * 60 + mins


def _history(entry: Any) -> List[Dict[str, Any]]:
    rows = getattr(entry, "status_history", None)
    return [h for h in rows if isinstance(h, dict)] if isinstance(rows, list) else []


def _transition_at(history: List[Dict[str, Any]], wanted: str) -> Optional[datetime]:
    """First timestamp at which *history* recorded a move to *wanted*."""
    for step in history:
        if step.get("to") != wanted:
            continue
        raw = step.get("at")
        if not isinstance(raw, str) or not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _aware(value: Any) -> Optional[datetime]:
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _mean(values: List[float]) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def _session_capacity(sessions: List[Any], day: date_cls) -> int:
    """Published seats for one day: whole slots in each active session.

    ``max_patients`` is the seat count per slot (capacity-N slots are legitimate,
    owner decision Q2), and a whole-day session with no usable times falls back
    to one seat rather than zero — an unavailable-looking denominator would make
    utilisation meaningless exactly where a serial practice works.
    """
    total = 0
    weekday = day.weekday()
    for session in sessions:
        if getattr(session, "day_of_week", None) != weekday:
            continue
        start = getattr(session, "effective_from", None)
        end = getattr(session, "effective_to", None)
        if start and day < start:
            continue
        if end and day > end:
            continue
        seats = max(1, int(getattr(session, "max_patients", 1) or 1))
        open_min = _minutes(getattr(session, "start_time", None))
        close_min = _minutes(getattr(session, "end_time", None))
        length = int(getattr(session, "slot_duration_minutes", 0) or 0)
        if open_min is None or close_min is None or close_min <= open_min or length <= 0:
            total += seats
            continue
        total += max(1, (close_min - open_min) // length) * seats
    return total


def _buckets(rows: Dict[str, int], order) -> Dict[str, int]:
    """Status counts with a stable key order and no zero-suppression."""
    out = OrderedDict((key, 0) for key in order)
    for key, count in rows.items():
        out[key] = out.get(key, 0) + int(count)
    return dict(out)


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

@router.get("/operational")
def operational_report(
        date: Optional[str] = Query(None, description="YYYY-MM-DD; facility today when omitted"),
        from_date: Optional[str] = Query(None),
        to_date: Optional[str] = Query(None),
        branch_id: Optional[str] = Query(None),
        doctor_id: Optional[str] = Query(None),
        auth: AuthContext = Depends(require_permission("appointment.read"))):
    """The BR §43 operational report for one day or one date range.

    One request answers all five permitted dimensions, because they are five
    readings of the same scoped rows: splitting them into five endpoints would
    let a reader add figures computed over five different row sets.
    """
    if date and (from_date or to_date):
        raise HTTPException(422, "give either date or from_date/to_date, not both")
    if bool(from_date) != bool(to_date):
        raise HTTPException(422, "from_date and to_date must be given together")

    session = SessionFactory()
    try:
        if branch_id:
            require_branch_access(branch_id)(auth)
        # `.clinerules` §3: a branch-scoped principal's branch is derived from the
        # token, never left open.  Asking for no branch does not widen a
        # receptionist's report to the whole organisation — it narrows it to the
        # branch the token already holds.  An organisation-wide principal keeps
        # the organisation-wide view.
        scoped_branch = branch_id
        if not scoped_branch and not auth.is_org_admin:
            scoped_branch = auth.branch_id
        facility_today = operational_today(session, auth.organization_id)
        if date:
            day = _day(date, "date")
            d0 = d1 = day
        elif from_date:
            d0, d1 = _day(from_date, "from_date"), _day(to_date, "to_date")
            if d0 > d1:
                raise HTTPException(422, "from_date must be <= to_date")
        else:
            d0 = d1 = facility_today
        if (d1 - d0).days + 1 > MAX_PERIOD_DAYS:
            raise HTTPException(422, f"period may not exceed {MAX_PERIOD_DAYS} days")

        if doctor_id:
            owned = session.query(Doctor.id).filter(
                Doctor.id == doctor_id,
                Doctor.organization_id == auth.organization_id).first()
            if not owned:
                # A doctor outside this tenant is not disclosed as such.
                raise HTTPException(404, "not found")

        appts = session.query(Appointment).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.appointment_date >= d0,
            Appointment.appointment_date <= d1)
        if scoped_branch:
            appts = appts.filter(Appointment.branch_id == scoped_branch)
        if doctor_id:
            appts = appts.filter(Appointment.doctor_id == doctor_id)
        rows = appts.all()

        status_rows: Dict[str, int] = {}
        by_day: Dict[str, int] = {}
        by_doctor: Dict[str, int] = {}
        by_branch: Dict[str, int] = {}
        sources: Dict[str, int] = {}
        walk_ins = 0
        for a in rows:
            status_rows[a.status] = status_rows.get(a.status, 0) + 1
            key = str(a.appointment_date)
            by_day[key] = by_day.get(key, 0) + 1
            by_doctor[a.doctor_id] = by_doctor.get(a.doctor_id, 0) + 1
            by_branch[a.branch_id] = by_branch.get(a.branch_id, 0) + 1
            source = a.booking_source or "unspecified"
            sources[source] = sources.get(source, 0) + 1
            if a.booking_source == "walk_in":
                walk_ins += 1

        status_counts = _buckets(status_rows, LIFECYCLE)
        headline = {name: sum(status_counts.get(s, 0) for s in names)
                    for name, names in HEADLINE.items()}
        headline["present"] = sum(status_counts.get(s, 0) for s in PRESENT)

        queue = session.query(QueueEntry).filter(
            QueueEntry.organization_id == auth.organization_id,
            QueueEntry.date >= d0, QueueEntry.date <= d1)
        if scoped_branch:
            queue = queue.filter(QueueEntry.branch_id == scoped_branch)
        if doctor_id:
            queue = queue.filter(QueueEntry.doctor_id == doctor_id)
        entries = queue.all()

        q_status: Dict[str, int] = {}
        q_source: Dict[str, int] = {}
        transitions = 0
        calls = 0
        waits: List[float] = []
        services: List[float] = []
        for entry in entries:
            state = (entry.status or "waiting")
            q_status[state] = q_status.get(state, 0) + 1
            origin = (entry.entry_source or "unspecified")
            q_source[origin] = q_source.get(origin, 0) + 1
            history = _history(entry)
            transitions += len(history)
            called = _transition_at(history, "called")
            if called:
                calls += 1
            created = _aware(entry.created_at)
            done = _transition_at(history, "completed")
            if created and called:
                waits.append(max((called - created).total_seconds(), 0) / 60.0)
            if called and done:
                services.append(max((done - called).total_seconds(), 0) / 60.0)

        return {
            "from": str(d0), "to": str(d1), "facility_today": str(facility_today),
            "branch_id": scoped_branch, "requested_branch_id": branch_id,
            "doctor_id": doctor_id,
            "appointments": {
                "total": len(rows),
                "by_day": [{"date": k, "count": v} for k, v in sorted(by_day.items())],
                "by_doctor": [{"doctor_id": k, "count": v}
                              for k, v in sorted(by_doctor.items())],
                "by_branch": [{"branch_id": k, "count": v}
                              for k, v in sorted(by_branch.items())],
            },
            "status_counts": status_counts,
            "br43": headline,
            "walk_ins": walk_ins,
            "booking_sources": [{"source": k, "count": v}
                                for k, v in sorted(sources.items())],
            "queue_activity": {
                "entries": len(entries),
                "by_status": _buckets(q_status, QUEUE_STATES),
                "by_source": [{"source": k, "count": v}
                              for k, v in sorted(q_source.items())],
                "calls": calls,
                "transitions": transitions,
                "avg_wait_minutes": _mean(waits),
                "avg_service_minutes": _mean(services),
            },
            "utilisation": _utilisation(session, auth, d0, d1, scoped_branch, doctor_id),
            "reconciliation": {
                "appointments_total": len(rows),
                "status_sum": sum(status_counts.values()),
                "by_day_sum": sum(by_day.values()),
                "by_doctor_sum": sum(by_doctor.values()),
                "by_branch_sum": sum(by_branch.values()),
                "booking_sources_sum": sum(sources.values()),
                "queue_entries": len(entries),
                "queue_status_sum": sum(q_status.values()),
            },
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Schedule utilisation
# ---------------------------------------------------------------------------

def _utilisation(session: Any, auth: AuthContext, d0: date_cls, d1: date_cls,
                 branch_id: Optional[str], doctor_id: Optional[str]) -> Dict[str, Any]:
    """Claimed seats against published seat capacity, per doctor over the period.

    Capacity comes from **active** ``schedule_sessions`` rows only: a cancelled
    session publishes nothing, so it must not inflate the denominator.  Claims
    come from ``slot_allocations``, which the appointment service releases when a
    booking closes — the same population the capacity guarantee is enforced
    against, which is why the two can be compared at all.

    ``UNSCHEDULED`` seats are outside published capacity by definition (owner
    decision Q1's override pool) and are counted in their own field instead of
    being folded into the percentage.
    """
    published = session.query(ScheduleSession).filter(
        ScheduleSession.organization_id == auth.organization_id,
        ScheduleSession.status == "active").all()
    if branch_id:
        published = [s for s in published if s.branch_id == branch_id]
    if doctor_id:
        published = [s for s in published if s.doctor_id == doctor_id]

    allocation_query = session.query(SlotAllocation).join(
        Appointment, SlotAllocation.appointment_id == Appointment.id).filter(
            SlotAllocation.organization_id == auth.organization_id,
            SlotAllocation.appointment_date >= d0,
            SlotAllocation.appointment_date <= d1)
    if branch_id:
        allocation_query = allocation_query.filter(Appointment.branch_id == branch_id)
    if doctor_id:
        allocation_query = allocation_query.filter(SlotAllocation.doctor_id == doctor_id)
    allocations = allocation_query.all()

    days: List[date_cls] = []
    cursor = d0
    while cursor <= d1:
        days.append(cursor)
        cursor += timedelta(days=1)

    doctors = sorted({s.doctor_id for s in published}
                     | {a.doctor_id for a in allocations})
    by_doctor: List[Dict[str, Any]] = []
    capacity_total = 0
    claimed_total = 0
    unscheduled_total = 0
    for doctor in doctors:
        own = [s for s in published if s.doctor_id == doctor]
        capacity = sum(_session_capacity(own, day) for day in days)
        rows = [a for a in allocations if a.doctor_id == doctor]
        claimed = sum(1 for a in rows if a.slot_key != UNSCHEDULED_SLOT_KEY)
        outside = sum(1 for a in rows if a.slot_key == UNSCHEDULED_SLOT_KEY)
        capacity_total += capacity
        claimed_total += claimed
        unscheduled_total += outside
        by_doctor.append({
            "doctor_id": doctor, "capacity": capacity, "claimed": claimed,
            "unscheduled": outside,
            # ``None`` rather than 0 or 100 when nothing was published: a doctor
            # with no session has no utilisation, which is not the same number.
            "percent": (round(claimed / capacity * 100, 1) if capacity else None),
        })

    return {
        "capacity": capacity_total,
        "claimed": claimed_total,
        "unscheduled": unscheduled_total,
        "percent": (round(claimed_total / capacity_total * 100, 1)
                    if capacity_total else None),
        "days": len(days),
        "by_doctor": by_doctor,
    }

