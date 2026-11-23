"""QUE-006 / W2 — announcement delivery claim and outcome (POD-4, V-12).

Two endpoints, and no new permission:

``POST /api/v1/queue/{entry_id}/announcement``             claim the call event
``POST /api/v1/queue/announcements/{delivery_id}/outcome`` report the result

Why a claim exists
------------------
An audible announcement should be played **once** per queue call. A browser
cannot coordinate with another browser, so the coordination record lives on the
server: ``queue_announcement_deliveries.call_event_id`` is UNIQUE and the insert
uses ``ON CONFLICT DO NOTHING`` — the same atomic pattern as
``common/queue_tokens.py`` and the notification outbox's dedup key. The first
terminal to claim speaks; every other terminal is told ``claimed: false`` and
announces nothing, but may still report ``skipped_duplicate`` for the audit.

Authority
---------
Announcing is not a queue mutation, so no capability was invented for it. The
claim is gated on the two capabilities that already make the announcement panel
reachable — ``queue.manage`` (front desk) or ``queue.consult`` (consulting
room). Tenant and branch scope reuse the queue service's own rules: a foreign or
out-of-branch entry answers **404**, never 403. A doctor or assistant may only
claim events on their own assigned doctor's queue (RBAC-R3, mirroring
``main.queue_action``).

What this module deliberately does not do
-----------------------------------------
* It never touches the queue transaction. A claim or an outcome is its own short
  transaction, so a failure here cannot reverse a queue call (V-11).
* It never infers ``completed`` from ``requested``. Only the browser may report
  ``completed``, and only after the final clip reported ``ended`` — a started
  announcement that was interrupted resolves ``interrupted`` or ``failed``.
* It never blocks playback, and it stores no patient, doctor, phone or clinical
  data: identifiers only (``queue_entry_id``, organisation, branch, event id).
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

from common.database import SessionFactory
from common.models import QueueAnnouncementDelivery, QueueEntry
from common.auth import AuthContext, get_current_user, branch_accessible
from common.permissions import check_granted
from common.audit import record_audit

try:                    # service runs both as a package and with its dir on path
    from .events import current_call_event
except ImportError:     # pragma: no cover
    from events import current_call_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/queue", tags=["queue-announcements"])

#: Capabilities that already make the operator announcement panel reachable.
#: Announcing adds no authority beyond being allowed to work this queue.
ANNOUNCE_CAPABILITIES = ("queue.manage", "queue.consult")

#: A delivery starts ``requested`` and settles into exactly one outcome.
REQUESTED = "requested"
COMPLETED = "completed"
FAILED = "failed"
BLOCKED = "blocked"
INTERRUPTED = "interrupted"
SKIPPED_BUSY = "skipped_busy"
SKIPPED_DUPLICATE = "skipped_duplicate"

#: Outcomes a browser may report. ``requested`` is not reportable: it is set by
#: the claim itself, so "announcement was asked for" can never be confused with
#: "announcement was heard".
OUTCOMES = (COMPLETED, FAILED, BLOCKED, INTERRUPTED, SKIPPED_BUSY,
            SKIPPED_DUPLICATE)

#: Outcomes that mean no sound was produced. Kept explicit so the audit trail
#: cannot grow a new status by typo.
SILENT_OUTCOMES = (BLOCKED, SKIPPED_BUSY, SKIPPED_DUPLICATE)

_CLAIM_SQL = text("""
    INSERT INTO queue_announcement_deliveries
        (id, organization_id, branch_id, queue_entry_id, call_event_id,
         language, voice_pack_id, voice_pack_version, transport,
         requested_by, requested_by_role, requested_at, status, outcome_reason)
    VALUES
        (:id, :organization_id, :branch_id, :queue_entry_id, :call_event_id,
         :language, :voice_pack_id, :voice_pack_version, :transport,
         :requested_by, :requested_by_role, :requested_at, 'requested', '')
    ON CONFLICT (call_event_id) DO NOTHING
    RETURNING id
""")


def _now():
    return datetime.now(timezone.utc)


def _clip(value, limit: int) -> str:
    """Trim free-text input to the column contract (never truncated silently)."""
    return (value or "").strip()[:limit]


def _require_announce(auth: AuthContext) -> None:
    granted = [row["capability"] for row in auth.capability_grants]
    if any(check_granted(cap, auth.role, granted) for cap in ANNOUNCE_CAPABILITIES):
        return
    raise HTTPException(403, "insufficient permissions")


def _scoped_entry(session, auth: AuthContext, entry_id: str) -> QueueEntry:
    """Same scope rules as ``main._scoped_entry_or_404`` (kept local: importing
    ``main`` from here would be a circular import).  Foreign or out-of-branch
    entries are reported as 404, never 403."""
    entry = session.query(QueueEntry).filter(
        QueueEntry.id == entry_id,
        QueueEntry.organization_id == auth.organization_id,
    ).first()
    if not entry:
        raise HTTPException(404, "queue entry not found")
    if not branch_accessible(auth, entry.branch_id):
        raise HTTPException(404, "queue entry not found")
    if auth.role in ("doctor", "assistant") and not auth.can_access_doctor(entry.doctor_id):
        raise HTTPException(404, "queue entry not found")
    return entry


class AnnouncementClaim(BaseModel):
    """What a terminal must send to be allowed to speak a call event."""
    event_id: str
    language: str = ""
    voice_pack_id: str = ""
    voice_pack_version: int = 0
    transport: str = ""


class AnnouncementOutcome(BaseModel):
    """The real result of the playback attempt, reported after it finished."""
    outcome: str
    reason: str = ""


def _delivery_view(delivery, duplicate=False) -> dict:
    return {
        "delivery_id": delivery.id,
        "event_id": delivery.call_event_id,
        "queue_entry_id": delivery.queue_entry_id,
        "status": delivery.status,
        "reason": delivery.outcome_reason or "",
        "outcome_at": delivery.outcome_at.isoformat() if delivery.outcome_at else "",
        "duplicate": bool(duplicate),
    }


@router.post("/announcements/{delivery_id}/outcome")
def report_announcement_outcome(delivery_id: str, data: AnnouncementOutcome,
                                auth: AuthContext = Depends(get_current_user)):
    """Record what actually happened to a claimed announcement (POD-4).

    Distinguishes the three things the acceptance criteria keep apart: the queue
    call succeeded (``queue.call`` in ``status_history``), an announcement was
    attempted (``requested``), and audio playback actually finished
    (``completed``). Tenant and branch scope come from the stored row, never
    from the request body.
    """
    _require_announce(auth)
    outcome = _clip(data.outcome, 24)
    if outcome not in OUTCOMES:
        raise HTTPException(422, f"unknown announcement outcome: {outcome}")
    reason = _clip(data.reason, 120)

    session = SessionFactory()
    try:
        delivery = session.query(QueueAnnouncementDelivery).filter(
            QueueAnnouncementDelivery.id == delivery_id,
            # Tenant isolation: a foreign delivery is indistinguishable from a
            # missing one (404, non-disclosing).
            QueueAnnouncementDelivery.organization_id == auth.organization_id,
        ).first()
        if delivery is None:
            raise HTTPException(404, "announcement delivery not found")
        if delivery.branch_id and not branch_accessible(auth, delivery.branch_id):
            raise HTTPException(404, "announcement delivery not found")
        if auth.role in ("doctor", "assistant"):
            entry = session.query(QueueEntry).filter(
                QueueEntry.id == delivery.queue_entry_id).first()
            if entry is None or not auth.can_access_doctor(entry.doctor_id):
                raise HTTPException(404, "announcement delivery not found")

        if delivery.status == outcome:
            # Idempotent: a retried report must not add a second audit row.
            return _delivery_view(delivery, duplicate=True)
        if delivery.status != REQUESTED:
            # A settled announcement is never rewritten.
            raise HTTPException(409, f"announcement already resolved as {delivery.status}")

        delivery.status = outcome
        delivery.outcome_at = _now()
        delivery.outcome_reason = reason
        record_audit(session, service="queuing",
                     org_id=delivery.organization_id,
                     branch_id=delivery.branch_id or "",
                     action=f"queue.announcement.{outcome}",
                     target_type="queue_call_event",
                     target_id=delivery.call_event_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before={"status": REQUESTED},
                     after={"status": outcome,
                            "queue_entry_id": delivery.queue_entry_id,
                            "language": delivery.language,
                            "voice_pack_id": delivery.voice_pack_id,
                            "voice_pack_version": delivery.voice_pack_version,
                            "transport": delivery.transport},
                     reason=reason)
        session.commit()
        return _delivery_view(delivery)
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()


@router.post("/{entry_id}/announcement")
def claim_announcement(entry_id: str, data: AnnouncementClaim, response: Response,
                       auth: AuthContext = Depends(get_current_user)):
    """Claim the right to play one queue call event (cross-terminal dedupe).

    ``201`` means this terminal owns the event and must announce it. ``200``
    with ``claimed: false`` means another terminal already claimed it; the
    caller announces nothing and may report ``skipped_duplicate``.

    The claim is a single ``INSERT ... ON CONFLICT DO NOTHING RETURNING``, so
    two terminals racing on the same event cannot both win — no advisory lock,
    no polling and no permanent per-browser record is involved.
    """
    _require_announce(auth)
    event_id = _clip(data.event_id, 120)
    if not event_id:
        raise HTTPException(422, "event_id required")

    session = SessionFactory()
    try:
        entry = _scoped_entry(session, auth, entry_id)
        # A call event only exists while the entry stands in `called`: claiming
        # an older event would silence the terminal that owns the live one.
        if entry.status != "called":
            raise HTTPException(409, "queue entry is not currently called")
        current = current_call_event(entry.id, entry.status_history)
        if not current or current["call_event_id"] != event_id:
            raise HTTPException(409, "announcement event is not the current call")

        row_id = str(uuid.uuid4())
        inserted = session.execute(_CLAIM_SQL, {
            "id": row_id,
            "organization_id": entry.organization_id,
            "branch_id": entry.branch_id,
            "queue_entry_id": entry.id,
            "call_event_id": event_id,
            "language": _clip(data.language, 8),
            "voice_pack_id": _clip(data.voice_pack_id, 80),
            "voice_pack_version": max(0, int(data.voice_pack_version or 0)),
            "transport": _clip(data.transport, 20),
            "requested_by": auth.user_id,
            "requested_by_role": (auth.role or "")[:30] or None,
            "requested_at": _now(),
        }).first()

        if inserted is None:
            # Another terminal won the race; its row is the record of the event.
            winner = session.query(QueueAnnouncementDelivery).filter(
                QueueAnnouncementDelivery.call_event_id == event_id).first()
            session.commit()
            response.status_code = 200
            return {
                "claimed": False,
                "event_id": event_id,
                "delivery_id": winner.id if winner else "",
                "status": winner.status if winner else "",
                "reason": "duplicate_event",
            }

        delivery = session.query(QueueAnnouncementDelivery).filter(
            QueueAnnouncementDelivery.id == row_id).first()
        record_audit(session, service="queuing", org_id=entry.organization_id,
                     branch_id=entry.branch_id or "",
                     action="queue.announcement.requested",
                     target_type="queue_call_event", target_id=event_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     after={"status": REQUESTED,
                            "queue_entry_id": entry.id,
                            "language": delivery.language,
                            "voice_pack_id": delivery.voice_pack_id,
                            "voice_pack_version": delivery.voice_pack_version,
                            "transport": delivery.transport},
                     reason="")
        session.commit()
        response.status_code = 201
        return {
            "claimed": True,
            "event_id": event_id,
            "delivery_id": delivery.id,
            "status": delivery.status,
            "reason": "",
        }
    except HTTPException:
        session.rollback(); raise
    except Exception:
        session.rollback(); raise
    finally:
        session.close()
