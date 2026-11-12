"""AMSDP dashboard aggregate endpoints (read-only, real DB counts)."""

from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timezone, timedelta
from sqlalchemy import func

from common.database import SessionFactory
from common.models import Appointment, QueueEntry, AuditEvent
from common.auth import AuthContext, get_current_user, require_branch_access
from common.timeutil import operational_today

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

QUEUE_ACTIVE = ["waiting", "called", "in_consultation", "skipped"]


@router.get("/today")
def dashboard_today(doctor_id: str = Query(None), branch_id: str = Query(None),
                    auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        if branch_id:
            # Enforce branch authorization server-side (never trust the UI)
            require_branch_access(branch_id)(auth)
        # Facility-local day (BR §8), never the UTC date.
        today = operational_today(session, auth.organization_id)
        q = session.query(Appointment).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.appointment_date == today)

        if doctor_id: q = q.filter(Appointment.doctor_id == doctor_id)
        if branch_id: q = q.filter(Appointment.branch_id == branch_id)
        rows = q.all()

        counts = {s: 0 for s in ["scheduled", "confirmed", "checked_in",
                                 "in_queue", "in_consultation", "completed",
                                 "cancelled", "no_show", "rescheduled"]}
        walk_ins = 0
        for a in rows:
            if a.booking_source == "walk_in":
                walk_ins += 1
            key = {"BOOKED": "scheduled", "AWAITING_CONFIRMATION": "scheduled",
                   "CONFIRMED": "confirmed", "CHECKED_IN": "checked_in",
                   "IN_QUEUE": "in_queue", "IN_CONSULTATION": "in_consultation",
                   "COMPLETED": "completed", "CANCELLED": "cancelled",
                   "NO_SHOW": "no_show", "RESCHEDULED": "rescheduled"}.get(a.status)
            if key: counts[key] += 1

        qq = session.query(QueueEntry).filter(
            QueueEntry.organization_id == auth.organization_id,
            QueueEntry.date == today,
            QueueEntry.status.in_(QUEUE_ACTIVE))
        if doctor_id: qq = qq.filter(QueueEntry.doctor_id == doctor_id)
        if branch_id: qq = qq.filter(QueueEntry.branch_id == branch_id)
        queue_length = qq.count()

        doc_rows = session.query(Appointment.doctor_id, func.count()).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.appointment_date == today).group_by(Appointment.doctor_id).all()

        return {
            "date": str(today), "branch_id": branch_id, "doctor_id": doctor_id,
            "scheduled": counts["scheduled"], "confirmed": counts["confirmed"],
            "checked_in": counts["checked_in"], "in_queue": counts["in_queue"],
            "in_consultation": counts["in_consultation"],
            "completed": counts["completed"], "cancelled": counts["cancelled"],
            "no_show": counts["no_show"], "rescheduled": counts["rescheduled"],
            "walk_ins": walk_ins, "queue_length": queue_length, "total": len(rows),
            "per_doctor": [{"doctor_id": d, "count": c} for d, c in doc_rows],
        }
    finally:
        session.close()

@router.get("/period")
def dashboard_period(from_date: str = Query(...), to_date: str = Query(...),
                     doctor_id: str = Query(None), branch_id: str = Query(None),
                     auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        if branch_id:
            require_branch_access(branch_id)(auth)
        try:
            d0 = datetime.strptime(from_date, "%Y-%m-%d").date()
            d1 = datetime.strptime(to_date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(422, "dates must use YYYY-MM-DD")
        if d0 > d1:
            raise HTTPException(422, "from_date must be <= to_date")
        q = session.query(Appointment).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.appointment_date >= d0, Appointment.appointment_date <= d1)
        if doctor_id: q = q.filter(Appointment.doctor_id == doctor_id)
        if branch_id: q = q.filter(Appointment.branch_id == branch_id)
        rows = q.all()
        total = len(rows)
        status_counts = {}
        for a in rows:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1
        completed = status_counts.get("COMPLETED", 0)
        cancelled = status_counts.get("CANCELLED", 0)
        no_show = status_counts.get("NO_SHOW", 0)
        completion_rate = round(completed / total * 100, 1) if total else 0.0
        no_show_rate = round(no_show / total * 100, 1) if total else 0.0
        cancel_rate = round(cancelled / total * 100, 1) if total else 0.0

        qw = session.query(QueueEntry).join(Appointment, QueueEntry.appointment_id == Appointment.id).filter(
            Appointment.organization_id == auth.organization_id,
            Appointment.appointment_date >= d0, Appointment.appointment_date <= d1,
            QueueEntry.status == "completed")
        if doctor_id: qw = qw.filter(Appointment.doctor_id == doctor_id)
        if branch_id: qw = qw.filter(Appointment.branch_id == branch_id)
        waits = []
        for e in qw.all():
            created = e.created_at
            done = None
            for h in (e.status_history or []):
                if h.get("to") == "completed": done = h.get("at")
            if created and done:
                try:
                    t1 = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
                    t2 = datetime.fromisoformat(done.replace("Z", "+00:00"))
                    if t2.tzinfo is None: t2 = t2.replace(tzinfo=timezone.utc)
                    waits.append(max((t2 - t1).total_seconds(), 0) / 60.0)
                except Exception:
                    pass
        avg_wait_min = round(sum(waits) / len(waits), 1) if waits else None

        return {"from": from_date, "to": to_date, "total": total,
            "status_counts": status_counts,
            "completed": completed, "cancelled": cancelled, "no_show": no_show,
            "completion_rate": completion_rate, "no_show_rate": no_show_rate,
            "cancel_rate": cancel_rate, "avg_wait_minutes": avg_wait_min,
            "walk_in_total": sum(1 for a in rows if a.booking_source == "walk_in")}
    finally:
        session.close()


@router.get("/audit")
def dashboard_audit(action: str = Query(None), target_type: str = Query(None),
                    actor_id: str = Query(None), branch_id: str = Query(None),
                    from_date: str = Query(None), to_date: str = Query(None),
                    limit: int = Query(100, ge=1, le=500),
                    auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        if branch_id:
            require_branch_access(branch_id)(auth)
        q = session.query(AuditEvent).filter(
            AuditEvent.organization_id == auth.organization_id)
        if action: q = q.filter(AuditEvent.action == action)
        if target_type: q = q.filter(AuditEvent.target_type == target_type)
        if actor_id: q = q.filter(AuditEvent.actor_id == actor_id)
        if branch_id: q = q.filter(AuditEvent.branch_id == branch_id)
        if from_date:
            try: q = q.filter(AuditEvent.timestamp >= datetime.strptime(from_date, "%Y-%m-%d"))
            except Exception: pass
        if to_date:
            try: q = q.filter(AuditEvent.timestamp < (datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)))
            except Exception: pass
        events = q.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
        return [{"id": e.id, "service": e.service, "action": e.action,
            "target_type": e.target_type, "target_id": e.target_id,
            "actor_id": e.actor_id, "actor_role": e.actor_role or "",
            "organization_id": e.organization_id, "branch_id": e.branch_id,
            "before": e.before, "after": e.after,
            "reason": e.reason or "",
            "timestamp": str(e.timestamp) if e.timestamp else ""} for e in events]
    finally:
        session.close()