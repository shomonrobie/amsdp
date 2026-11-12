"""Best-effort notification lifecycle hooks (Sequence 3, WP5).

Every public function here:
1. opens and closes its own session,
2. performs no business write,
3. **never raises** — messaging must never block or roll back booking,
   check-in, queue updates, consultation lifecycle, or missed-turn recovery.

The service call sites additionally wrap these in ``try/except`` (belt and
braces), so a broken notification subsystem degrades to "no messages" instead
of "clinic workflow down".

Event definitions (PQV §D, Business Rules §35–§36):
* **N1 — ``appointment_confirmation``**: sent immediately after a booking.
* **N2 — ``pre_visit_reminder``**: sent ``reminder_lead_minutes`` (5 or 10,
  org-configurable) before the *expected* visit time. While the patient sits in
  the queue the expected time is ``now + patients_ahead × AVG_SERVICE_MINUTES``,
  so a queue change re-plans the reminder instead of sending a stale one.
"""

import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..database import SessionFactory
from ..models import (Appointment, Branch, Doctor, Notification, Organization,
                      Patient, QueueEntry)
from . import outbox
from .config import AVG_SERVICE_MINUTES, get_notification_config

logger = logging.getLogger(__name__)

DEFAULT_TZ = "Asia/Dhaka"
#: A reminder closer than this to the visit is pointless — skip it.
MIN_LEAD_TO_VISIT = timedelta(minutes=2)
#: Never plan a reminder for "now"; keep a small scheduling grace.
SCHEDULE_GRACE = timedelta(seconds=30)
#: Amended reminders smaller than this delta are left alone (avoids churn).
REPLAN_TOLERANCE = timedelta(seconds=60)

_TEMPLATES = {
    outbox.CONFIRMATION: {
        "en": ("Appointment confirmed. Doctor: {doctor}. Date: {date}. "
               "Time: {time}. Serial: {serial}. Token: {token}."),
        "bn": ("আপনার অ্যাপয়েন্টমেন্ট নিশ্চিত হয়েছে। ডাক্তার: {doctor}। "
               "তারিখ: {date}। সময়: {time}। সিরিয়াল: {serial}। টোকেন: {token}।"),
    },
    outbox.REMINDER: {
        "en": ("Reminder: your visit with {doctor} is expected around {expected}. "
               "Please arrive a little early. Token: {token}."),
        "bn": ("মনে করিয়ে দিচ্ছি: {doctor}-এর সাথে আপনার ভিজিট আনুমানিক "
               "{expected}-এ। অনুগ্রহ করে কিছুটা আগে পৌঁছান। টোকেন: {token}।"),
    },
}


def _org_timezone(org) -> ZoneInfo:
    name = (getattr(org, "timezone", None) or DEFAULT_TZ)
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_TZ)


def _scheduled_start(appointment, org):
    """Wall-clock appointment start as an aware datetime, or None if unknown."""
    raw = (getattr(appointment, "start_time", None) or "").strip()
    if not raw or not getattr(appointment, "appointment_date", None):
        return None
    try:
        hh, mm = raw.split(":")[:2]
        starts = time(int(hh), int(mm))
    except (TypeError, ValueError):
        return None
    return datetime.combine(appointment.appointment_date, starts,
                            tzinfo=_org_timezone(org))


def _patients_ahead(session, appointment) -> int:
    """How many patients are still queued for this doctor before the patient."""
    entry = session.query(QueueEntry).filter(
        QueueEntry.appointment_id == appointment.id).order_by(
        QueueEntry.created_at.desc()).first()
    if entry is None or entry.status in ("completed", "cancelled", "no_show",
                                         "in_consultation"):
        return 0
    return session.query(QueueEntry).filter(
        QueueEntry.organization_id == entry.organization_id,
        QueueEntry.doctor_id == entry.doctor_id,
        QueueEntry.date == entry.date,
        QueueEntry.status.in_(("waiting", "called")),
        QueueEntry.position < entry.position,
    ).count()


def expected_visit_time(session, appointment, org, now: datetime = None):
    """Best current estimate of when this patient is actually seen.

    The scheduled slot is the floor; a live queue estimate raises it. Returns
    None when the appointment has no usable time.
    """
    now = now or outbox.utcnow()
    start = _scheduled_start(appointment, org)
    if start is None:
        return None
    estimate = now + timedelta(
        minutes=max(_patients_ahead(session, appointment), 0) * AVG_SERVICE_MINUTES)
    return max(start, estimate)


def plan_reminder_time(expected: datetime, lead_minutes: int,
                       now: datetime = None, not_before: datetime = None):
    """When to send N2, or None when no meaningful reminder can be sent."""
    now = now or outbox.utcnow()
    if expected - now < MIN_LEAD_TO_VISIT:
        return None
    when = expected - timedelta(minutes=max(int(lead_minutes or 0), 0))
    floor = now + SCHEDULE_GRACE
    if not_before and not_before > floor:
        floor = not_before
    if when < floor:
        when = floor
    return when if when < expected else None


def normalize_mobile(raw: str) -> str:
    """Return digits only (leading '+' preserved); '' when unusable."""
    raw = (raw or "").strip()
    plus = raw.startswith("+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 8 or len(digits) > 15:
        return ""
    return ("+" if plus else "") + digits


def _payload(appointment, org, patient, doctor, branch, channel: str,
             body: str) -> dict:
    """Non-clinical message context. Never contains diagnosis or notes."""
    return {
        "body": body,
        "channel": channel,
        "appointment_date": str(appointment.appointment_date),
        "start_time": appointment.start_time or "",
        "token": appointment.token_number or "",
        "doctor_name": getattr(doctor, "name", "") or "",
        "branch_name": getattr(branch, "name", "") or "",
        "patient_name": getattr(patient, "name", "") or "",
        "locale": (getattr(org, "locale", None) or "en"),
    }


def _render(template_key: str, locale: str, **values) -> str:
    table = _TEMPLATES[template_key]
    template = table.get(locale) or table["en"]
    safe = {k: ("" if v is None else v) for k, v in values.items()}
    return template.format(**safe)


def _local_time(moment: datetime, org) -> str:
    if moment is None:
        return ""
    return moment.astimezone(_org_timezone(org)).strftime("%d %b %Y %I:%M %p")


def _context(session, appointment):
    org = session.query(Organization).filter(
        Organization.id == appointment.organization_id).first()
    patient = session.query(Patient).filter(
        Patient.id == appointment.patient_id).first()
    doctor = session.query(Doctor).filter(
        Doctor.id == appointment.doctor_id).first()
    branch = None
    if appointment.branch_id:
        branch = session.query(Branch).filter(
            Branch.id == appointment.branch_id).first()
    return org, patient, doctor, branch


def _enqueue_channel(session, appointment, org, patient, doctor, branch,
                     channel: str, cfg: dict, now: datetime) -> dict:
    """Create the N1 row (now) and the N2 row (planned) for one channel."""
    result = {"channel": channel, "confirmation": None, "reminder": None}
    mobile = normalize_mobile(getattr(patient, "mobile", "") or "")
    if not mobile:
        # Never send to a number we could not normalize.
        result["skipped"] = "missing_valid_mobile"
        return result
    locale = getattr(org, "locale", None) or "en"
    provider = cfg[channel]["provider"]

    body = _render(outbox.CONFIRMATION, locale,
                   doctor=getattr(doctor, "name", ""),
                   date=str(appointment.appointment_date),
                   time=appointment.start_time or "",
                   serial=appointment.serial_number or "",
                   token=appointment.token_number or "")
    _row, created = outbox.enqueue_or_rearm(
        session, organization_id=appointment.organization_id,
        branch_id=appointment.branch_id or "", appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        notification_type=outbox.CONFIRMATION, channel=channel,
        recipient_mobile=mobile, scheduled_at=now, provider=provider,
        payload=_payload(appointment, org, patient, doctor, branch, channel, body))
    result["confirmation"] = "scheduled" if created else "deduplicated"

    expected = expected_visit_time(session, appointment, org, now)
    if expected is None:
        result["reminder"] = "no_scheduled_time"
        return result
    not_before = now + timedelta(minutes=cfg["cooldown_minutes"])
    when = plan_reminder_time(expected, cfg["reminder_lead_minutes"], now, not_before)
    if when is None:
        result["reminder"] = "not_needed"
        return result

    body = _render(outbox.REMINDER, locale,
                   doctor=getattr(doctor, "name", ""),
                   expected=_local_time(expected, org),
                   token=appointment.token_number or "")
    payload = _payload(appointment, org, patient, doctor, branch, channel, body)
    payload["expected"] = _local_time(expected, org)
    payload["reminder_lead_minutes"] = cfg["reminder_lead_minutes"]
    _row, created = outbox.enqueue_or_rearm(
        session, organization_id=appointment.organization_id,
        branch_id=appointment.branch_id or "", appointment_id=appointment.id,
        patient_id=appointment.patient_id, notification_type=outbox.REMINDER,
        channel=channel, recipient_mobile=mobile, scheduled_at=when,
        provider=provider, payload=payload)
    result["reminder"] = "scheduled" if created else "deduplicated"
    result["reminder_at"] = when.isoformat()
    return result


def on_appointment_booked(appointment_id: str) -> dict:
    """Plan N1 + N2 for a booking. Never raises; returns a small summary."""
    summary = {"appointment_id": appointment_id, "channels": [], "skipped": ""}
    try:
        session = SessionFactory()
        try:
            appt = session.query(Appointment).filter(
                Appointment.id == appointment_id).first()
            if appt is None:
                summary["skipped"] = "appointment_not_found"
                return summary
            if (appt.booking_source or "") == "walk_in" or \
                    (appt.appointment_type or "") == "walk_in":
                # Walk-ins are registered at the desk; a confirmation SMS adds noise.
                summary["skipped"] = "walk_in_needs_no_message"
                return summary
            if appt.status in ("CANCELLED", "NO_SHOW", "COMPLETED", "RESCHEDULED"):
                summary["skipped"] = f"terminal_status:{appt.status}"
                return summary
            org, patient, doctor, branch = _context(session, appt)
            if org is None or patient is None:
                summary["skipped"] = "missing_org_or_patient"
                return summary
            cfg = get_notification_config(org.config)
            now = outbox.utcnow()
            for channel in ("whatsapp", "sms"):
                channel_cfg = cfg[channel]
                if not channel_cfg["usable"]:
                    summary["channels"].append(
                        {"channel": channel, "skipped": channel_cfg["status"]})
                    continue
                summary["channels"].append(
                    _enqueue_channel(session, appt, org, patient, doctor, branch,
                                     channel, cfg, now))
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.warning("notification hook (booked) failed for %s", appointment_id,
                       exc_info=False)
        summary["skipped"] = "error"
    return summary


def on_appointment_closed(appointment_id: str, reason: str = "") -> int:
    """Cancel every unsettled message for an appointment. Never raises.

    Called on cancel, reschedule, transfer, no-show, check-in and consultation
    start — a message about a visit that will not happen must not go out.
    """
    try:
        session = SessionFactory()
        try:
            cancelled = outbox.cancel_for_appointment(
                session, appointment_id, reason=reason or "appointment closed")
            session.commit()
            return cancelled
        finally:
            session.close()
    except Exception:
        logger.warning("notification hook (closed) failed for %s", appointment_id,
                       exc_info=False)
        return 0


def on_queue_changed(organization_id: str, doctor_id: str, day,
                     reason: str = "") -> dict:
    """Re-plan pending reminders for one doctor/day after a queue change.

    A reminder whose moment has passed (or whose visit is imminent) is cancelled
    rather than sent late; a moving estimate amends ``scheduled_at`` in place,
    which keeps the dedupe key (and the history of that one message) intact.
    """
    summary = {"replanned": 0, "cancelled": 0, "unchanged": 0}
    try:
        session = SessionFactory()
        try:
            org = session.query(Organization).filter(
                Organization.id == organization_id).first()
            cfg = get_notification_config(org.config if org else None)
            now = outbox.utcnow()
            rows = session.query(Notification).join(
                Appointment, Appointment.id == Notification.appointment_id).filter(
                Notification.organization_id == organization_id,
                Notification.notification_type == outbox.REMINDER,
                Notification.status.in_(outbox.OPEN),
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == day).all()
            for row in rows:
                appt = session.query(Appointment).filter(
                    Appointment.id == row.appointment_id).first()
                if appt is None or appt.status in (
                        "CANCELLED", "NO_SHOW", "COMPLETED", "RESCHEDULED"):
                    summary["cancelled"] += outbox.cancel_rows(
                        [row], reason="appointment no longer active", now=now)
                    continue
                recent = session.query(Notification).filter(
                    Notification.appointment_id == row.appointment_id,
                    Notification.channel == row.channel,
                    Notification.notification_type == outbox.REMINDER,
                    Notification.id != row.id,
                    Notification.status.in_(("sent", "delivered")),
                    Notification.sent_at >= now - timedelta(
                        minutes=cfg["cooldown_minutes"])).first()
                if recent is not None:
                    # Cooldown: the patient already has a fresh reminder.
                    summary["cancelled"] += outbox.cancel_rows(
                        [row], reason="cooldown active", now=now)
                    continue
                expected = expected_visit_time(session, appt, org, now)
                when = None if expected is None else plan_reminder_time(
                    expected, cfg["reminder_lead_minutes"], now)
                if when is None:
                    summary["cancelled"] += outbox.cancel_rows(
                        [row], reason=f"{reason or 'queue change'} made reminder obsolete",
                        now=now)
                    continue
                current = outbox.as_utc(row.scheduled_at)
                if abs((when - current).total_seconds()) > REPLAN_TOLERANCE.total_seconds():
                    payload = dict(row.payload or {})
                    payload["expected"] = _local_time(expected, org)
                    payload["body"] = _render(
                        outbox.REMINDER, payload.get("locale") or "en",
                        doctor=payload.get("doctor_name", ""),
                        expected=payload["expected"],
                        token=payload.get("token", ""))
                    row.payload = payload
                    row.scheduled_at = when
                    row.next_attempt_at = None
                    summary["replanned"] += 1
                else:
                    summary["unchanged"] += 1
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.warning("notification hook (queue changed) failed for %s/%s",
                       doctor_id, day, exc_info=False)
        summary["error"] = True
    return summary



