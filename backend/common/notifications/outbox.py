"""Persistent notification outbox (Sequence 3 / M9 §14).

Row-level operations only — no scheduling math, no provider selection policy
(both live in ``config``/``hooks`` and ``providers``).

Invariants
----------
* One row per ``(notification_type, appointment, channel)`` — enforced by the
  ``dedup_key`` UNIQUE constraint, so a retried hook can never duplicate a
  message.
* Rows are never deleted; obsolete rows become ``cancelled`` with a reason, so
  "what was scheduled and why it did not go out" stays auditable.
* ``sent`` = the provider accepted the message. ``delivered`` requires a
  provider acknowledgement and is never inferred.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from ..models import Notification
from . import config as notif_config
from .providers import ProviderResult, ProviderUnavailable, get_provider

logger = logging.getLogger(__name__)

CONFIRMATION = "appointment_confirmation"
REMINDER = "pre_visit_reminder"

PENDING = "pending"
PROCESSING = "processing"
SENT = "sent"
DELIVERED = "delivered"
FAILED = "failed"
RETRY = "retry_scheduled"
CANCELLED = "cancelled"

#: Statuses a worker may still act on.
OPEN = (PENDING, RETRY)
#: Statuses where the row has not left the building.
UNSETTLED = (PENDING, RETRY, PROCESSING)

MAX_ATTEMPTS = int(os.environ.get("AMSDP_NOTIFICATION_MAX_ATTEMPTS", "3") or 3)
_BACKOFF_SECONDS = (30, 120, 300)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value):
    """Return *value* timezone-aware in UTC (DB columns are tz-aware)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def dedup_key(notification_type: str, appointment_id: str, channel: str) -> str:
    return f"{notification_type}:{appointment_id}:{channel}"[:160]


def enqueue_or_rearm(session, *, organization_id: str, notification_type: str,
                     channel: str, recipient_mobile: str, scheduled_at: datetime,
                     appointment_id: str = "", branch_id: str = "",
                     queue_entry_id: str = "", patient_id: str = "",
                     provider: str = notif_config.DEFAULT_PROVIDER,
                     payload: dict | None = None,
                     max_attempts: int = None) -> tuple[Notification | None, bool]:
    """Create a pending row, or re-arm a previously cancelled/failed one.

    Returns ``(row, created)`` where ``created`` is False when an identical,
    still-live row already existed (deduplication — the caller must not treat
    that as an error).
    """
    key = dedup_key(notification_type, appointment_id, channel)
    existing = session.query(Notification).filter(
        Notification.dedup_key == key).first()
    if existing is not None:
        if existing.status in (FAILED, CANCELLED):
            existing.status = PENDING
            existing.scheduled_at = scheduled_at
            existing.next_attempt_at = None
            existing.attempt_count = 0
            existing.error = None
            existing.cancel_reason = None
            existing.cancelled_at = None
            existing.recipient_mobile = recipient_mobile
            existing.payload = payload or {}
            existing.provider = provider
            return existing, True
        return existing, False

    row = Notification(
        id=str(uuid.uuid4()), organization_id=organization_id,
        branch_id=branch_id or None, appointment_id=appointment_id or None,
        queue_entry_id=queue_entry_id or None, patient_id=patient_id or None,
        notification_type=notification_type, channel=channel,
        recipient_mobile=recipient_mobile, payload=payload or {},
        dedup_key=key, status=PENDING, attempt_count=0,
        max_attempts=max_attempts or MAX_ATTEMPTS,
        scheduled_at=scheduled_at, provider=provider or notif_config.DEFAULT_PROVIDER,
    )
    session.add(row)
    session.flush()
    return row, True


def cancel_rows(rows, reason: str = "", now: datetime = None) -> int:
    """Move unsettled rows to ``cancelled`` (in place, caller commits)."""
    now = now or utcnow()
    count = 0
    for row in rows:
        if row.status in UNSETTLED:
            row.status = CANCELLED
            row.cancelled_at = now
            row.cancel_reason = (reason or "cancelled")[:200]
            row.next_attempt_at = None
            count += 1
    return count


def cancel_for_appointment(session, appointment_id: str, reason: str = "",
                           now: datetime = None) -> int:
    """Cancel every unsettled message for one appointment (cancel/reschedule/
    check-in/consultation start/no-show)."""
    if not appointment_id:
        return 0
    rows = session.query(Notification).filter(
        Notification.appointment_id == appointment_id,
        Notification.status.in_(UNSETTLED)).all()
    return cancel_rows(rows, reason=reason, now=now)


def due_rows(session, now: datetime, limit: int = 50):
    """Rows that are due now, locked so two workers cannot send the same row."""
    return session.query(Notification).filter(
        Notification.status.in_(OPEN),
        Notification.scheduled_at <= now,
        (Notification.next_attempt_at.is_(None))
        | (Notification.next_attempt_at <= now),
    ).order_by(Notification.scheduled_at).limit(limit).with_for_update(
        skip_locked=True).all()


def deliver_row(session, row, now: datetime = None) -> dict:
    """Attempt delivery for one row and persist the resulting state.

    The caller owns the commit. Provider failures never raise: they are recorded
    as ``retry_scheduled`` (transient) or ``failed`` (permanent / exhausted).
    """
    now = now or utcnow()
    row.status = PROCESSING
    row.attempt_count = int(row.attempt_count or 0) + 1
    row.last_attempt_at = now
    session.flush()

    body = (row.payload or {}).get("body", "")
    try:
        adapter = get_provider(row.provider or notif_config.DEFAULT_PROVIDER,
                               channel=row.channel)
        result = adapter.send(recipient=row.recipient_mobile, body=body,
                              notification_type=row.notification_type,
                              payload=row.payload or {})
    except ProviderUnavailable as exc:
        # Deterministic, non-retryable: no adapter exists in this build.
        row.status = FAILED
        row.error = str(exc)[:500]
        return {"id": row.id, "status": row.status, "channel": row.channel,
                "attempt": row.attempt_count, "error": row.error}
    except Exception as exc:  # defensive: an adapter must never break a worker
        logger.warning("notification adapter raised for row %s: %s",
                       row.id, type(exc).__name__)
        result = ProviderResult(ok=False, provider=row.provider or "unknown",
                                error=f"{type(exc).__name__}", retryable=True)

    if result.ok:
        row.status = DELIVERED if result.delivered else SENT
        row.sent_at = now
        row.provider_message_id = (result.provider_message_id or "")[:120]
        row.error = None
        if result.delivered:
            row.delivered_at = now
    elif not result.retryable or row.attempt_count >= int(row.max_attempts or 1):
        row.status = FAILED
        row.error = (result.error or "provider rejected the message")[:500]
    else:
        row.status = RETRY
        delay = _BACKOFF_SECONDS[min(row.attempt_count - 1,
                                     len(_BACKOFF_SECONDS) - 1)]
        row.next_attempt_at = now + timedelta(seconds=delay)
        row.error = (result.error or "transient provider error")[:500]

    return {"id": row.id, "status": row.status, "channel": row.channel,
            "attempt": row.attempt_count, "error": row.error or ""}


def process_due(session, now: datetime = None, limit: int = 50) -> dict:
    """Deliver every due row. Does NOT commit — the worker owns the transaction."""
    now = now or utcnow()
    outcomes = [deliver_row(session, row, now) for row in due_rows(session, now, limit)]
    summary = {"processed": len(outcomes), "sent": 0, "delivered": 0,
               "failed": 0, "retry_scheduled": 0, "cancelled": 0, "details": outcomes}
    for o in outcomes:
        key = "retry_scheduled" if o["status"] == RETRY else o["status"]
        if key in summary:
            summary[key] += 1
    return summary


def stats(session, organization_id: str | None = None, since: datetime = None) -> dict:
    """Counts per status — used by the org-admin provider status panel."""
    q = session.query(Notification)
    if organization_id:
        q = q.filter(Notification.organization_id == organization_id)
    if since:
        q = q.filter(Notification.created_at >= since)
    counts = {s: 0 for s in (PENDING, PROCESSING, SENT, DELIVERED, FAILED,
                             RETRY, CANCELLED)}
    for row in q.all():
        if row.status in counts:
            counts[row.status] += 1
        else:
            counts[row.status] = counts.get(row.status, 0) + 1
    counts["total"] = sum(v for k, v in counts.items() if k != "total")
    return counts

