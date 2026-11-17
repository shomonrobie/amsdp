"""AMSDP Queue Management Service — BR §24–§31.

PostgreSQL-backed with token safety, position history, walk-in policies,
tenant/branch isolation, and role-based authorization.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date as date_type, datetime, timezone

import logging

from common.database import SessionFactory
from common.models import QueueEntry, QueueSequence, Appointment, Patient, Doctor, Branch
from common.auth import AuthContext, get_current_user, require_permission, branch_accessible
from common.audit import record_audit
from common.queue_tokens import allocate_daily_token, token_for
from common.timeutil import operational_today
from common.log_redaction import install_token_redaction
from common.health import install_health
from common.denial_audit import install_denial_audit

app = FastAPI(title="AMSDP Queue Management Service")
install_health(app, "queuing")
# Q-2: every 403/404/422 answered by this service is written to the audit trail.
install_denial_audit(app, "queuing")

try:
    from .display import router as display_router
except ImportError:
    from display import router as display_router
app.include_router(display_router)

# Sequence 3 — missed-turn recovery (BR §27A). Kept in its own module so the
# recovery contract stays readable and independently testable.
try:
    from .recovery import router as recovery_router
except ImportError:
    from recovery import router as recovery_router
app.include_router(recovery_router)

logger = logging.getLogger(__name__)


def _notify(event: str, *args) -> None:
    """Best-effort notification hook (Sequence 3).

    Never raises: a messaging failure must not fail a queue operation, and the
    hook itself opens its own session so nothing leaks into this transaction.
    """
    try:
        from common.notifications import hooks as notification_hooks
        getattr(notification_hooks, event)(*args)
    except Exception:
        logger.warning("notification hook %s failed", event, exc_info=False)


#: Queue actions after which a pending visit reminder must be cancelled.
CLOSING_ACTIONS = ("start_consultation", "complete_consultation",
                   "cancel", "mark_no_show")


@app.on_event("startup")
def _install_security_filters():
    install_token_redaction()

WALK_IN_POLICIES = ("end_of_queue", "first_come", "reserved_capacity", "staff_placement")
ACTIVE_STATUSES = ("waiting", "called", "in_consultation", "skipped")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _entry_to_dict(e):
    return {"id": e.id, "queue_entry_id": e.id,
        "organization_id": e.organization_id, "branch_id": e.branch_id,
        "doctor_id": e.doctor_id, "date": str(e.date),
        "position": e.position, "token": e.token,
        "patient_id": e.patient_id, "appointment_id": e.appointment_id,
        "entry_source": e.entry_source, "status": e.status,
        "status_history": e.status_history or [],
        "position_history": e.position_history or [],
        "notes": e.notes or "", "added_by": e.added_by or "",
        "created_at": str(e.created_at) if e.created_at else ""}


def _next_sequence(session, doctor_id: str, day):
    """Return the next atomic daily sequence for a doctor."""
    return allocate_daily_token(session, doctor_id, day)[0]


def _token_for(doctor_id: str, seq: int) -> str:
    return token_for(doctor_id, seq)


def _scoped_entry_or_404(session, auth, entry_id: str):
    entry = session.query(QueueEntry).filter(
        QueueEntry.id == entry_id,
        QueueEntry.organization_id == auth.organization_id,
    ).first()
    if not entry:
        raise HTTPException(404, "queue entry not found")
    # P0-1: enforce branch scope on the entry's *stored* branch.  The
    # authenticated actor must be authorized for that branch; a caller is
    # never allowed to reach another branch's entry by supplying an id.
    if not branch_accessible(auth, entry.branch_id):
        raise HTTPException(404, "queue entry not found")
    return entry


@app.get("/api/v1/queue")
def get_queue(doctor_id: str = Query(...), date: str = Query(...),
              branch_id: str = Query(None), auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        try: day = datetime.strptime(date, "%Y-%m-%d").date()
        except: raise HTTPException(422, "invalid date")
        # RBAC-R3: a doctor or assistant may only view their own assigned
        # doctor's queue.  A caller-supplied doctor_id must match their
        # staff_user.doctor_id assignment; it cannot be used to expand access.
        # When auth.doctor_id is unset (no doctor assignment), fail closed.
        if auth.role in ("doctor", "assistant"):
            if not auth.can_access_doctor(doctor_id):
                raise HTTPException(404, "not found")
        q = session.query(QueueEntry).filter(
            QueueEntry.organization_id == auth.organization_id,
            QueueEntry.doctor_id == doctor_id, QueueEntry.date == day,
            QueueEntry.status.in_(ACTIVE_STATUSES))
        if branch_id:
            # P0-2: validate the caller-supplied branch against authenticated
            # scope.  Reject unauthorized branch selection (non-disclosing
            # 404) so a branch-scoped actor cannot read another branch's queue.
            if not branch_accessible(auth, branch_id):
                raise HTTPException(404, "not found")
            q = q.filter(QueueEntry.branch_id == branch_id)
        elif auth.branch_id and not (auth.is_super_admin or auth.is_org_admin):
            q = q.filter(QueueEntry.branch_id == auth.branch_id)
        entries = q.order_by(QueueEntry.position).all()
        result = [_entry_to_dict(e) for e in entries]
        pnames = {p.id: p.name for p in session.query(Patient).filter(
            Patient.id.in_({e.patient_id for e in entries})).all()}
        dnames = {d.id: d.name for d in session.query(Doctor).filter(
            Doctor.id.in_({e.doctor_id for e in entries})).all()}
        for r in result:
            r["patient_name"] = pnames.get(r["patient_id"], "")
            r["doctor_name"] = dnames.get(r["doctor_id"], "")
        return {"date": date, "branch_id": branch_id, "doctor_id": doctor_id,
                "doctor_name": dnames.get(doctor_id, ""), "waiting": len(result),
                "entries": result}
    finally:
        session.close()

class CheckInRequest(BaseModel):
    appointment_id: str
    branch_id: str = ""
    date: str = ""
    notes: str = ""
    walk_in_policy: str = "end_of_queue"
    position: Optional[int] = None

@app.post("/api/v1/queue/check-in", status_code=201)
def check_in_appointment(data: CheckInRequest,
                          auth: AuthContext = Depends(require_permission("queue.checkin"))):
    import uuid
    session = SessionFactory()
    try:
        appt = session.query(Appointment).filter(
            Appointment.id == data.appointment_id,
            Appointment.organization_id == auth.organization_id).first()
        if not appt:
            raise HTTPException(404, "appointment not found")
        if appt.status in ("CANCELLED", "NO_SHOW", "COMPLETED"):
            raise HTTPException(422, f"cannot check in a {appt.status} appointment")
        dup = session.query(QueueEntry).filter(
            QueueEntry.appointment_id == appt.id,
            QueueEntry.status.in_(ACTIVE_STATUSES)).first()
        if dup:
            raise HTTPException(422, "appointment is already queued")
        # P0-3: the check-in branch is the appointment's stored branch.  A
        # caller may not select another branch by supplying branch_id in the
        # body, and must be authorized for the appointment's branch.
        target_branch = appt.branch_id
        if data.branch_id and data.branch_id != appt.branch_id:
            raise HTTPException(404, "not found")
        if not branch_accessible(auth, target_branch):
            raise HTTPException(404, "not found")
        # C2: a doctor or assistant may check in only their own assigned
        # doctor's appointments.  Fail closed when no assignment exists.
        if auth.role in ("doctor", "assistant"):
            if not auth.can_access_doctor(appt.doctor_id):
                raise HTTPException(404, "appointment not found")
        day = appt.appointment_date
        seq = _next_sequence(session, appt.doctor_id, day)
        token = _token_for(appt.doctor_id, seq)
        pos = data.position if (data.walk_in_policy == "staff_placement" and data.position) else seq
        entry = QueueEntry(id=str(uuid.uuid4()),
            organization_id=appt.organization_id,
            branch_id=target_branch,
            doctor_id=appt.doctor_id, date=day, position=pos, token=token,
            patient_id=appt.patient_id, appointment_id=appt.id,
            entry_source="appointment", status="waiting",
            status_history=[{"from": "", "to": "waiting", "actor": auth.user_id, "at": _now_iso()}],
            position_history=[{"from": 0, "to": pos, "actor": auth.user_id, "at": _now_iso()}],
            notes=data.notes, added_by=auth.user_id)
        session.add(entry)
        h = list(appt.status_history or [])
        h.append({"from": appt.status, "to": "IN_QUEUE", "actor": auth.user_id, "at": _now_iso()})
        appt.status_history = h; appt.status = "IN_QUEUE"
        record_audit(session, service="queuing", org_id=auth.organization_id,
                     branch_id=entry.branch_id, action="queue.checkin",
                     target_type="queue_entry", target_id=entry.id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     after={"status": "waiting", "position": pos, "token": token},
                     reason="check-in from appointment")
        session.commit()
        result = _entry_to_dict(entry); result["patient_name"] = ""
        # Sequence 3: the patient is physically here — cancel the pending
        # reminder and re-plan the reminders of everybody still waiting.
        _notify("on_appointment_closed", appt.id, "checked in to queue")
        _notify("on_queue_changed", entry.organization_id, entry.doctor_id,
                entry.date, "queue check-in")
        return result
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


class QueueEnqueueRequest(BaseModel):
    doctor_id: str
    patient_id: str
    branch_id: str = ""
    date: str = ""
    entry_source: str = "walk_in"
    notes: str = ""
    walk_in_policy: str = "end_of_queue"
    position: Optional[int] = None

@app.post("/api/v1/queue/enqueue", status_code=201)
def enqueue_patient(data: QueueEnqueueRequest,
                     auth: AuthContext = Depends(require_permission("queue.checkin"))):
    import uuid
    if data.entry_source not in ("walk_in", "extra", "appointment"):
        raise HTTPException(422, f"invalid entry_source: {data.entry_source}")
    if data.walk_in_policy not in WALK_IN_POLICIES:
        raise HTTPException(422, f"invalid walk_in_policy: {data.walk_in_policy}")
    session = SessionFactory()
    try:
        # Facility-local day (BR §8), never the UTC date.
        day = operational_today(session, auth.organization_id)
        if data.date:
            try: day = datetime.strptime(data.date, "%Y-%m-%d").date()
            except: raise HTTPException(422, "invalid date")
        patient = session.query(Patient).filter(
            Patient.id == data.patient_id,
            Patient.organization_id == auth.organization_id).first()
        if not patient: raise HTTPException(422, "patient not found")
        doctor = session.query(Doctor).filter(
            Doctor.id == data.doctor_id,
            Doctor.organization_id == auth.organization_id).first()
        if not doctor: raise HTTPException(422, "doctor not found")
        # C2: a doctor or assistant may enqueue only for their own assigned
        # doctor.  Fail closed when no assignment exists.
        if auth.role in ("doctor", "assistant"):
            if not auth.can_access_doctor(data.doctor_id):
                raise HTTPException(404, "doctor not found")
        # RBAC-R1: enforce the caller's branch scope.  A caller-supplied
        # branch_id is validated before use; an unauthorized branch selection
        # is rejected (non-disclosing 404).  The fallback is the caller's own
        # token branch.  The target branch must exist and belong to the
        # caller's organization.
        target_branch = data.branch_id or auth.branch_id or ""
        if not target_branch:
            raise HTTPException(404, "not found")
        branch_row = session.query(Branch).filter(
            Branch.id == target_branch,
            Branch.organization_id == auth.organization_id).first()
        if not branch_row:
            raise HTTPException(404, "not found")
        if not branch_accessible(auth, target_branch):
            raise HTTPException(404, "not found")
        seq = _next_sequence(session, data.doctor_id, day)
        token = _token_for(data.doctor_id, seq)
        pos = data.position if (data.walk_in_policy == "staff_placement" and data.position) else seq
        entry = QueueEntry(id=str(uuid.uuid4()),
            organization_id=auth.organization_id,
            branch_id=target_branch,
            doctor_id=data.doctor_id, date=day, position=pos, token=token,
            patient_id=data.patient_id, appointment_id=None,
            entry_source=data.entry_source, status="waiting",
            status_history=[{"from": "", "to": "waiting", "actor": auth.user_id, "at": _now_iso()}],
            position_history=[{"from": 0, "to": pos, "actor": auth.user_id, "at": _now_iso()}],
            notes=data.notes, added_by=auth.user_id)
        session.add(entry)
        record_audit(session, service="queuing", org_id=auth.organization_id,
                     branch_id=entry.branch_id, action="queue.enqueue",
                     target_type="queue_entry", target_id=entry.id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     after={"status": "waiting", "position": pos, "token": token,
                            "entry_source": data.entry_source},
                     reason=f"enqueue ({data.entry_source})")
        session.commit()
        # Sequence 3: a new patient changes everyone's expected time.
        _notify("on_queue_changed", entry.organization_id, entry.doctor_id,
                entry.date, f"patient enqueued ({data.entry_source})")
        result = _entry_to_dict(entry)
        result["patient_name"] = patient.name; result["doctor_name"] = doctor.name
        return result
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
# ---------------------------------------------------------------------------
# Queue entry actions (status transitions)
# ---------------------------------------------------------------------------

class QueueAction(BaseModel):
    action: str            # start_consultation | complete_consultation | cancel | mark_no_show | reinsert | call
    reason: str = ""
    actor: str = ""

# Allowed transitions per current status
_TRANSITIONS = {
    "waiting":         ("call", "start_consultation", "cancel", "mark_no_show"),
    "called":          ("start_consultation", "cancel", "mark_no_show"),
    "in_consultation": ("complete_consultation",),
    "skipped":         ("call", "reinsert", "start_consultation", "cancel"),
    "completed":       (),
    "cancelled":       (),
    "no_show":         (),
}
_NEXT_STATUS = {
    "call": "called", "start_consultation": "in_consultation",
    "complete_consultation": "completed", "cancel": "cancelled",
    "mark_no_show": "no_show", "reinsert": "waiting",
}

@app.patch("/api/v1/queue/{entry_id}")
def queue_action(entry_id: str, data: QueueAction,
                 auth: AuthContext = Depends(get_current_user)):
    # Consultation actions require the queue.consult permission (doctor+)
    if data.action in ("start_consultation", "complete_consultation"):
        require_permission("queue.consult")(auth)
    elif data.action in ("call", "cancel", "mark_no_show", "reinsert"):
        require_permission("queue.manage")(auth)
    else:
        raise HTTPException(422, f"unknown action: {data.action}")

    session = SessionFactory()
    try:
        entry = _scoped_entry_or_404(session, auth, entry_id)
        # RBAC-R3: a doctor or assistant may act only on their own assigned
        # doctor's queue entries.  When auth.doctor_id is unset (no doctor
        # assignment), fail closed.  Applies to all actions, not just
        # consultation.
        if auth.role in ("doctor", "assistant"):
            if not auth.can_access_doctor(entry.doctor_id):
                raise HTTPException(404, "queue entry not found")
        allowed = _TRANSITIONS.get(entry.status, ())
        if data.action not in allowed:
            raise HTTPException(422, f"cannot {data.action} from {entry.status}")
        new_status = _NEXT_STATUS[data.action]
        if data.action == "cancel" and not data.reason:
            raise HTTPException(422, "cancellation reason required")
        sh = list(entry.status_history or [])
        sh.append({"from": entry.status, "to": new_status,
                   "action": data.action, "actor": auth.user_id,
                   "reason": data.reason, "at": _now_iso()})
        entry.status_history = sh
        entry.status = new_status
        # PQT lifecycle: revoke tracking token when consultation starts
        if data.action == "start_consultation" and entry.appointment_id:
            from common.tracking_tokens import revoke_for_appointment
            revoke_for_appointment(session, entry.appointment_id,
                                   reason="consultation started")
        # If consultation complete, mark the related appointment COMPLETED
        if data.action == "complete_consultation" and entry.appointment_id:
            appt = session.query(Appointment).filter(
                Appointment.id == entry.appointment_id).first()
            if appt and appt.status not in ("COMPLETED", "CANCELLED", "NO_SHOW"):
                h = list(appt.status_history or [])
                h.append({"from": appt.status, "to": "COMPLETED",
                          "actor": auth.user_id, "at": _now_iso()})
                appt.status_history = h; appt.status = "COMPLETED"
        record_audit(session, service="queuing", org_id=auth.organization_id,
                     branch_id=entry.branch_id, action=f"queue.{data.action}",
                     target_type="queue_entry", target_id=entry.id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before={"status": sh[-1]["from"] if sh else ""},
                     after={"status": new_status}, reason=data.reason)
        session.commit()
        # Sequence 3: a served/cancelled visit needs no reminder; any queue
        # change re-plans the reminders of patients still waiting.
        if data.action in CLOSING_ACTIONS and entry.appointment_id:
            _notify("on_appointment_closed", entry.appointment_id,
                    f"queue {data.action}")
        _notify("on_queue_changed", entry.organization_id, entry.doctor_id,
                entry.date, f"queue {data.action}")
        return _entry_to_dict(entry)
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Manual reorder — preserves tokens, records position history
# ---------------------------------------------------------------------------

class QueueReorder(BaseModel):
    entry_ids: list[str]
    reason: str = ""
    actor: str = ""

@app.post("/api/v1/queue/reorder")
def reorder_queue(data: QueueReorder,
                  auth: AuthContext = Depends(require_permission("queue.reorder"))):
    session = SessionFactory()
    try:
        entries = session.query(QueueEntry).filter(
            QueueEntry.id.in_(data.entry_ids),
            QueueEntry.organization_id == auth.organization_id).all()
        by_id = {e.id: e for e in entries}
        if len(by_id) != len(data.entry_ids):
            raise HTTPException(422, "one or more entries not found in scope")
        # P0-5: validate queue homogeneity — every entry must belong to the
        # same authorized branch/doctor/date queue context, and the caller
        # must be authorized for that branch.  Reject mixed-queue or
        # unauthorized entries; raise before any mutation so an invalid
        # reorder is never partially applied.
        queue_context = None
        for eid in data.entry_ids:
            entry = by_id[eid]
            if entry.status not in ACTIVE_STATUSES:
                raise HTTPException(422, f"entry {eid} is not in a reorderable state")
            if not branch_accessible(auth, entry.branch_id):
                raise HTTPException(404, "queue entry not found")
            # C2: a doctor or assistant may reorder only their own assigned
            # doctor's entries.
            if auth.role in ("doctor", "assistant"):
                if not auth.can_access_doctor(entry.doctor_id):
                    raise HTTPException(404, "queue entry not found")
            key = (entry.branch_id, entry.doctor_id, entry.date)
            if queue_context is None:
                queue_context = key
            elif key != queue_context:
                raise HTTPException(
                    422, "entries must belong to the same branch, doctor and date")
        for idx, eid in enumerate(data.entry_ids, start=1):
            entry = by_id[eid]
            if entry.position != idx:
                ph = list(entry.position_history or [])
                ph.append({"from": entry.position, "to": idx,
                           "actor": auth.user_id, "reason": data.reason,
                           "at": _now_iso()})
                old_pos = entry.position
                entry.position_history = ph
                entry.position = idx
                record_audit(session, service="queuing", org_id=auth.organization_id,
                             branch_id=entry.branch_id, action="queue.reorder",
                             target_type="queue_entry", target_id=entry.id,
                             actor_id=auth.user_id, actor_role=auth.role,
                             before={"position": old_pos}, after={"position": idx},
                             reason=data.reason)
        session.commit()
        seen = set()
        for e in entries:
            key = (e.doctor_id, e.date)
            if key in seen:
                continue
            seen.add(key)
            # Sequence 3: manual reordering moves everybody's expected time.
            _notify("on_queue_changed", e.organization_id, e.doctor_id, e.date,
                    "manual reorder")
        return {"reordered": len(data.entry_ids), "matched": len(entries)}
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# History (all statuses for a doctor/date)
# ---------------------------------------------------------------------------

@app.get("/api/v1/queue/history")
def queue_history(doctor_id: str = Query(...), date: str = Query(...),
                  status: str = Query(None), branch_id: str = Query(None),
                  auth: AuthContext = Depends(get_current_user)):
    session = SessionFactory()
    try:
        try: day = datetime.strptime(date, "%Y-%m-%d").date()
        except: raise HTTPException(422, "invalid date")
        # RBAC-R3: doctor/assistant may only view their own assigned doctor's
        # queue history.  When auth.doctor_id is unset (no doctor assignment),
        # fail closed.
        if auth.role in ("doctor", "assistant"):
            if not auth.can_access_doctor(doctor_id):
                raise HTTPException(404, "not found")
        q = session.query(QueueEntry).filter(
            QueueEntry.organization_id == auth.organization_id,
            QueueEntry.doctor_id == doctor_id, QueueEntry.date == day)
        if status: q = q.filter(QueueEntry.status == status)
        if branch_id:
            # C1: validate the caller-supplied branch against authenticated
            # scope.  Reject unauthorized branch selection (non-disclosing
            # 404).
            if not branch_accessible(auth, branch_id):
                raise HTTPException(404, "not found")
            q = q.filter(QueueEntry.branch_id == branch_id)
        elif not auth.is_super_admin and not auth.is_org_admin and auth.branch_id:
            # C1: branch-scoped users restricted to their token branch when
            # branch_id is omitted.
            q = q.filter(QueueEntry.branch_id == auth.branch_id)
        entries = q.order_by(QueueEntry.position).all()
        return [_entry_to_dict(e) for e in entries]
    finally:
        session.close()
        session.close()