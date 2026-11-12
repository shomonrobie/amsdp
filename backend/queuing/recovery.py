"""AMSDP missed-turn recovery — Business Rules §27A (Sequence 3, WP2).

A patient who was called but did not respond must not lose their place or their
token. Recovery therefore *moves* the existing ``queue_entries`` row:

* the same ``id``, ``token``, ``appointment_id``, ``patient_id`` and
  ``entry_source`` are preserved — nothing is cancelled and re-created;
* only ``status`` (``skipped`` → ``waiting``) and ``position`` change;
* the default re-entry point is the end of the queue; a staff override to a
  specific position requires ``queue.reposition`` **and** a written reason;
* both actions are audited, and the position change is appended to
  ``position_history`` so the patient's queue history stays complete.

Authorization
-------------
``queue.recover`` guards both endpoints. Branch scope is derived from the
authenticated token only: a cross-branch or cross-tenant entry returns **404**
(non-disclosing), never 403.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import AuthContext, require_permission
from common.database import SessionFactory
from common.models import QueueEntry
from common.permissions import check as perm_check

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/queue", tags=["queue-recovery"])

ACTIVE_STATUSES = ("waiting", "called", "in_consultation", "skipped")
#: Statuses from which "the patient missed their turn" is a true statement.
MISSABLE_STATUSES = ("waiting", "called")
#: One position is reserved for the recovered patient when overriding.
RECOVERY_MODES = ("end_of_queue", "position_override")


class MissedTurnRequest(BaseModel):
    reason: str = ""
    actor: str = ""


class RecoveryRequest(BaseModel):
    target_position: Optional[int] = None
    reason: str = ""
    actor: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _notify(event: str, *args) -> None:
    """Best-effort notification hook — never raises, never blocks recovery."""
    try:
        from common.notifications import hooks as notification_hooks
        getattr(notification_hooks, event)(*args)
    except Exception:
        logger.warning("notification hook %s failed", event, exc_info=False)


def _entry_payload(entry):
    """Serialize with the queue service's own shape (single source of truth)."""
    try:
        from .main import _entry_to_dict
    except ImportError:  # service launched as ``main:app`` in its container
        from main import _entry_to_dict
    return _entry_to_dict(entry)


def _scoped_entry(session, auth: AuthContext, entry_id: str) -> QueueEntry:
    """Lock and scope one entry. Cross-tenant/branch is a non-disclosing 404."""
    entry = session.query(QueueEntry).filter(
        QueueEntry.id == entry_id,
        QueueEntry.organization_id == auth.organization_id,
    ).with_for_update().first()
    if entry is None:
        raise HTTPException(404, "queue entry not found")
    if not (auth.is_super_admin or auth.is_org_admin):
        if not auth.branch_id or entry.branch_id != auth.branch_id:
            raise HTTPException(404, "queue entry not found")
    return entry


def _active_queue(session, entry: QueueEntry, exclude_id: str):
    """The doctor's live queue for that day, in display order (locked).

    Positions are allocated per doctor/day (``queue_sequences``), so the scope
    here matches token allocation rather than the branch-filtered UI view.
    """
    rows = session.query(QueueEntry).filter(
        QueueEntry.organization_id == entry.organization_id,
        QueueEntry.doctor_id == entry.doctor_id,
        QueueEntry.date == entry.date,
        QueueEntry.status.in_(ACTIVE_STATUSES),
        QueueEntry.id != exclude_id,
    ).order_by(QueueEntry.position, QueueEntry.created_at).with_for_update().all()
    return list(rows)


def _renumber(session, auth: AuthContext, ordered, reason: str,
              skip_id: Optional[str] = None) -> int:
    """Write 1..N positions, appending position history + audit per change.

    ``skip_id`` leaves that row's own position untouched but still *counts* its
    slot, so rows around a recovered entry land on the right numbers.
    """
    changed = 0
    for index, row in enumerate(ordered, start=1):
        if row.id == skip_id:
            continue
        if row.position == index:
            continue
        history = list(row.position_history or [])
        history.append({"from": row.position, "to": index,
                        "actor": auth.user_id, "reason": reason,
                        "at": _now_iso()})
        row.position_history = history
        old_position = row.position
        row.position = index
        record_audit(session, service="queuing", org_id=row.organization_id,
                     branch_id=row.branch_id, action="queue.reposition",
                     target_type="queue_entry", target_id=row.id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before={"position": old_position}, after={"position": index},
                     reason=reason)
        changed += 1
    return changed


@router.post("/{entry_id}/missed-turn")
def mark_missed_turn(entry_id: str, data: MissedTurnRequest,
                     auth: AuthContext = Depends(
                         require_permission("queue.recover"))):
    """Record that the patient did not respond when called
    (``waiting`` → ``skipped``). The row, token and appointment are untouched."""
    session = SessionFactory()
    try:
        entry = _scoped_entry(session, auth, entry_id)
        if entry.status == "skipped":
            raise HTTPException(422, "missed turn is already recorded for this entry")
        if entry.status not in MISSABLE_STATUSES:
            raise HTTPException(
                422, f"cannot record a missed turn from {entry.status}")
        previous_status = entry.status
        history = list(entry.status_history or [])
        history.append({"from": previous_status, "to": "skipped",
                        "action": "missed_turn",
                        "actor": data.actor or auth.user_id,
                        "reason": data.reason, "at": _now_iso()})
        entry.status_history = history
        entry.status = "skipped"
        record_audit(session, service="queuing", org_id=entry.organization_id,
                     branch_id=entry.branch_id, action="queue.missed_turn",
                     target_type="queue_entry", target_id=entry.id,
                     actor_id=data.actor or auth.user_id, actor_role=auth.role,
                     before={"status": previous_status, "position": entry.position},
                     after={"status": "skipped", "position": entry.position,
                            "token": entry.token,
                            "appointment_id": entry.appointment_id or ""},
                     reason=data.reason)
        session.commit()
        payload = _entry_payload(entry)
        payload["recovery"] = {"state": "awaiting_recovery",
                               "previous_status": previous_status,
                               "position": entry.position,
                               "token_preserved": True,
                               "appointment_preserved": True}
        _notify("on_queue_changed", entry.organization_id, entry.doctor_id,
                entry.date, f"missed turn recorded for token {entry.token}")
        return payload
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


@router.post("/{entry_id}/recover")
def recover_entry(entry_id: str, data: RecoveryRequest,
                  auth: AuthContext = Depends(
                      require_permission("queue.recover"))):
    """Bring a skipped patient back (default: end of queue).

    Overriding the position is a separate capability and requires a reason.
    The entry keeps its identity, token and appointment — this is a move, never
    a cancel-and-rebook.
    """
    if data.target_position is not None and not perm_check(
            "queue.reposition", auth.role):
        raise HTTPException(403, "insufficient permissions for a position override")
    session = SessionFactory()
    try:
        entry = _scoped_entry(session, auth, entry_id)
        if entry.status != "skipped":
            raise HTTPException(
                422, f"only a skipped entry can be recovered (entry is "
                     f"{entry.status})")

        others = _active_queue(session, entry, entry.id)
        override = data.target_position is not None
        if override:
            if not (data.reason or "").strip():
                raise HTTPException(
                    422, "a reason is required to override the queue position")
            if data.target_position < 1 or data.target_position > len(others) + 1:
                raise HTTPException(
                    422, f"target_position must be between 1 and {len(others) + 1}")
            index = data.target_position - 1
        else:
            index = len(others)

        mode = "position_override" if override else "end_of_queue"
        reason = (data.reason or "").strip() or "recovered at end of queue"
        previous_status, previous_position = entry.status, entry.position

        status_history = list(entry.status_history or [])
        status_history.append({"from": "skipped", "to": "waiting",
                               "action": "recover", "mode": mode,
                               "actor": data.actor or auth.user_id,
                               "reason": reason, "at": _now_iso()})
        entry.status_history = status_history
        position_history = list(entry.position_history or [])
        position_history.append({"from": previous_position, "to": index + 1,
                                 "actor": data.actor or auth.user_id,
                                 "reason": reason, "mode": mode,
                                 "at": _now_iso()})
        entry.position_history = position_history
        entry.status = "waiting"
        entry.position = index + 1
        session.flush()

        ordered = others[:index] + [entry] + others[index:]
        repositioned = _renumber(
            session, auth, ordered,
            f"queue recovery: {reason}", skip_id=entry.id)

        record_audit(session, service="queuing", org_id=entry.organization_id,
                     branch_id=entry.branch_id, action="queue.recover",
                     target_type="queue_entry", target_id=entry.id,
                     actor_id=data.actor or auth.user_id, actor_role=auth.role,
                     before={"status": previous_status,
                             "position": previous_position},
                     after={"status": "waiting", "position": entry.position,
                            "mode": mode, "token": entry.token,
                            "appointment_id": entry.appointment_id or "",
                            "repositioned_others": repositioned},
                     reason=reason)
        session.commit()
        payload = _entry_payload(entry)
        payload["recovery"] = {"state": "recovered", "mode": mode,
                               "previous_status": previous_status,
                               "previous_position": previous_position,
                               "position": entry.position,
                               "queue_size": len(ordered),
                               "repositioned_others": repositioned,
                               "token_preserved": True,
                               "appointment_preserved": True}
        _notify("on_queue_changed", entry.organization_id, entry.doctor_id,
                entry.date, f"patient recovered ({mode})")
        return payload
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


