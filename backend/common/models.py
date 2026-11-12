"""AMSDP Shared Data Model — Declarative SQLAlchemy models.

Covers all MVP entities.  Service ownership is indicated by the
``__service__`` attribute for cross-service clarity.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Date,
    ForeignKey, JSON, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Organization — service: organization
# ---------------------------------------------------------------------------

class Organization(Base):
    __tablename__ = "organizations"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    name            = Column(String(200), nullable=False)
    code            = Column(String(50), nullable=False, unique=True)
    timezone        = Column(String(50), default="Asia/Dhaka")
    locale          = Column(String(10), default="bn")
    facility_type   = Column(String(50), default="hospital")
    address         = Column(Text, default="")
    config          = Column(JSON, default=dict)
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)


class Branch(Base):
    __tablename__ = "branches"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name            = Column(String(200), nullable=False)
    code            = Column(String(50), nullable=False)
    address         = Column(Text, default="")
    phone           = Column(String(30))
    config          = Column(JSON, default=dict)
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    organization    = relationship("Organization", backref="branches")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_branch_org_code"),
    )


# ---------------------------------------------------------------------------
# Staff / Identity — service: identity
# ---------------------------------------------------------------------------

class StaffUser(Base):
    __tablename__ = "staff_users"
    __service__ = "identity"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"))
    doctor_id       = Column(String, ForeignKey("doctors.id"))
    username        = Column(String(100), nullable=False, unique=True)
    password_hash   = Column(String(255), nullable=False)
    display_name    = Column(String(200), nullable=False)
    role            = Column(String(30), nullable=False)
    email           = Column(String(200))
    mobile          = Column(String(30))
    locale          = Column(String(10), default="en")
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    organization    = relationship("Organization")
    branch          = relationship("Branch")
    doctor          = relationship("Doctor")

    __table_args__ = (
        Index("idx_staff_org", "organization_id"),
        Index("idx_staff_role", "role"),
    )


# ---------------------------------------------------------------------------
# Login attempts — service: identity (durable login throttle)
# ---------------------------------------------------------------------------

class LoginAttempt(Base):
    """One recorded login attempt, shared by every worker and replica.

    Sequence 4 finding SEQ4-THROTTLE-D1: the limiter's state lived in a
    module-level dict inside ``identity/main.py``, so N uvicorn workers (or N
    replicas) each handed out the full allowance to the same attacker, and a
    restart cleared every bucket.  The counters live here instead — in the same
    PostgreSQL instance the services already use — so the window is shared,
    durable and survives a restart, with no new infrastructure.

    These rows are **operational** data, not audit data: the limiter prunes
    attempts that fell out of the window and a successful login deletes the
    bucket.  The append-only security trail of *denials* is ``audit_events``
    (``.clinerules`` §3) and is never touched by this table.

    Only the client IP and the (length-capped, case-folded) username are stored:
    never a password, a token, or a request body.
    """
    __tablename__ = "login_attempts"
    __service__ = "identity"

    id           = Column(String, primary_key=True, default=_new_id)
    client_ip    = Column(String(45), nullable=False)      # wide enough for IPv6
    username     = Column(String(120), nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False,
                          default=_utcnow)

    __table_args__ = (
        # Covers the per-bucket window count (the hot path).
        Index("idx_login_attempts_key", "client_ip", "username", "attempted_at"),
        # Covers the global prune of expired buckets.
        Index("idx_login_attempts_time", "attempted_at"),
    )


# ---------------------------------------------------------------------------
# Doctor — service: doctor
# ---------------------------------------------------------------------------

class Doctor(Base):
    __tablename__ = "doctors"
    __service__ = "doctor"

    id                  = Column(String, primary_key=True, default=_new_id)
    organization_id     = Column(String, ForeignKey("organizations.id"), nullable=False)
    name                = Column(String(200), nullable=False)
    mobile              = Column(String(30), nullable=False)
    speciality          = Column(String(100), default="")
    qualification       = Column(String(200), default="")
    registration_number = Column(String(100))
    consultation_fee    = Column(Float)
    locale              = Column(String(10), default="bn")
    status              = Column(String(20), default="active")
    created_at          = Column(DateTime(timezone=True), default=_utcnow)

    organization        = relationship("Organization")

    __table_args__ = (
        Index("idx_doctor_org", "organization_id"),
    )


class DoctorBranch(Base):
    __tablename__ = "doctor_branches"
    __service__ = "doctor"

    id          = Column(String, primary_key=True, default=_new_id)
    doctor_id   = Column(String, ForeignKey("doctors.id"), nullable=False)
    branch_id   = Column(String, ForeignKey("branches.id"), nullable=False)

    doctor      = relationship("Doctor", backref="branch_assignments")
    branch      = relationship("Branch")

    __table_args__ = (
        UniqueConstraint("doctor_id", "branch_id", name="uq_doctor_branch"),
    )



# ---------------------------------------------------------------------------
# Patient — service: patient
# ---------------------------------------------------------------------------

class Patient(Base):
    __tablename__ = "patients"
    __service__ = "patient"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name            = Column(String(200), nullable=False)
    mobile          = Column(String(30), nullable=False)
    date_of_birth   = Column(String(20))
    # Reported age (years) used only when DOB is not disclosed; never used to
    # fabricate a DOB. DOB remains the authoritative age source when present.
    age             = Column(Integer)
    sex             = Column(String(10))
    address         = Column(Text)
    national_id     = Column(String(50))
    status          = Column(String(20), default="active")
    merged_into     = Column(String)
    merge_reason    = Column(String)
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    organization    = relationship("Organization")

    __table_args__ = (
        Index("idx_patient_org", "organization_id"),
        Index("idx_patient_org_mobile", "organization_id", "mobile"),
    )


# ---------------------------------------------------------------------------
# Schedule — service: scheduling
# ---------------------------------------------------------------------------

class Schedule(Base):
    __tablename__ = "schedules"
    __service__ = "scheduling"

    id                  = Column(String, primary_key=True, default=_new_id)
    doctor_id           = Column(String, ForeignKey("doctors.id"), nullable=False)
    organization_id     = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id           = Column(String, ForeignKey("branches.id"), nullable=False)
    appointment_model   = Column(String(30), default="time_slot")
    effective_from      = Column(Date)
    effective_to        = Column(Date)
    slot_templates      = Column(JSON, default=list)
    status              = Column(String(20), default="active")
    created_at          = Column(DateTime(timezone=True), default=_utcnow)

    doctor              = relationship("Doctor")
    organization        = relationship("Organization")
    branch              = relationship("Branch")

    __table_args__ = (
        Index("idx_schedule_doctor", "doctor_id"),
        Index("idx_schedule_org", "organization_id"),
    )




# ---------------------------------------------------------------------------
# Appointment — service: appointment
# ---------------------------------------------------------------------------

class Appointment(Base):
    __tablename__ = "appointments"
    __service__ = "appointment"

    id                    = Column(String, primary_key=True, default=_new_id)
    organization_id       = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id             = Column(String, ForeignKey("branches.id"), nullable=False)
    patient_id            = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id             = Column(String, ForeignKey("doctors.id"), nullable=False)
    appointment_date      = Column(Date, nullable=False)
    start_time            = Column(String(10))
    serial_number         = Column(Integer)
    appointment_type      = Column(String(30), default="scheduled")
    booking_source        = Column(String(30), default="reception")
    status                = Column(String(30), default="BOOKED")
    status_history        = Column(JSON, default=list)
    token_number          = Column(String(50))
    notes                 = Column(Text)
    created_by            = Column(String)
    rescheduled_from      = Column(String)
    rescheduled_to        = Column(String)
    reschedule_reason     = Column(String)
    created_at            = Column(DateTime(timezone=True), default=_utcnow)

    organization          = relationship("Organization")
    branch                = relationship("Branch")
    patient               = relationship("Patient")
    doctor                = relationship("Doctor")

    __table_args__ = (
        Index("idx_appt_doctor_date", "doctor_id", "appointment_date"),
        Index("idx_appt_patient", "patient_id"),
    )


# ---------------------------------------------------------------------------
# Queue — service: queuing
# ---------------------------------------------------------------------------

class QueueEntry(Base):
    __tablename__ = "queue_entries"
    __service__ = "queuing"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"), nullable=False)
    doctor_id       = Column(String, ForeignKey("doctors.id"), nullable=False)
    date            = Column(Date, nullable=False)
    position        = Column(Integer, nullable=False)
    token           = Column(String(50), nullable=False)
    patient_id      = Column(String, ForeignKey("patients.id"), nullable=False)
    appointment_id  = Column(String, ForeignKey("appointments.id"))
    entry_source    = Column(String(30), default="appointment")
    status          = Column(String(30), default="waiting")
    status_history  = Column(JSON, default=list)
    position_history = Column(JSON, default=list)
    notes           = Column(Text)
    added_by        = Column(String)
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    organization    = relationship("Organization")
    branch          = relationship("Branch")
    doctor          = relationship("Doctor")
    patient         = relationship("Patient")
    appointment     = relationship("Appointment")

    __table_args__ = (
        Index("idx_queue_doctor_date", "doctor_id", "date"),
        Index("idx_queue_org", "organization_id"),
    )


class QueueSequence(Base):
    """Concurrency-safe per-(doctor,date) token/position sequence.

    Postgres atomic UPSERT on (doctor_id, date) guarantees unique daily
    sequence values even under concurrent bookings.
    """
    __tablename__ = "queue_sequences"
    __service__ = "queuing"

    doctor_id   = Column(String, ForeignKey("doctors.id"), primary_key=True)
    date        = Column(Date, primary_key=True)
    last_value  = Column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Audit — service: audit
# ---------------------------------------------------------------------------

class TrackingToken(Base):
    """PQT tracking token — one per eligible appointment.

    Per the Gate 1 security model:
    - token_hash = sha256(raw_token + pepper).hexdigest()   (UNIQUE)
    - Pepper is a backend env var (AMSDP_TRACKING_PEPPER), never stored here.
    - token_prefix = first 8 base64 chars of raw token (display reference only).
    - Revoked/expired rows return 404 (indistinguishable from never-issued).
    """
    __tablename__ = "tracking_tokens"
    __service__ = "appointment"

    id              = Column(String, primary_key=True, default=_new_id)
    appointment_id  = Column(String, ForeignKey("appointments.id"), nullable=False, unique=True)
    token_hash      = Column(String(64), nullable=False)
    token_prefix    = Column(String(8), nullable=False)
    status          = Column(String(20), nullable=False, default="active")
    eligible_at     = Column(DateTime(timezone=True), default=_utcnow)
    revoked_at      = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    appointment     = relationship("Appointment", backref="tracking_token")

    # Declared exactly as the migrated database has it.  ``a1f2b3c4d5e6`` also
    # created a plain index (``ix_tracking_tokens_hash``) on the same column; a
    # UNIQUE constraint already maintains a B-tree on ``token_hash``, so the
    # extra index only added write cost and planner noise (Sequence 4 finding
    # SEQ4-INDEX-P3).  Migration ``e6c1a9b3d5f8`` drops it, so the model must not
    # declare it or ``alembic check`` would report drift.
    __table_args__ = (
        UniqueConstraint("token_hash", name="tracking_tokens_token_hash_key"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __service__ = "audit"

    id              = Column(String, primary_key=True, default=_new_id)
    service         = Column(String(50), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"))
    action          = Column(String(50), nullable=False)
    target_type     = Column(String(50), nullable=False)
    target_id       = Column(String, nullable=False)
    actor_id        = Column(String, nullable=False)
    actor_role      = Column(String(30))
    before          = Column(JSON)
    after           = Column(JSON)
    reason          = Column(Text, default="")
    timestamp       = Column(DateTime(timezone=True), default=_utcnow)

    organization    = relationship("Organization")


# ---------------------------------------------------------------------------
# Notifications — service: notifications (Sequence 3 / M9-D outbox)
# ---------------------------------------------------------------------------

class Notification(Base):
    """Persistent notification outbox row (BR §35–§36, PQV §D, M9 §14).

    One row per (event, channel, recipient context). Rows are never deleted:
    obsolete pending rows are moved to ``cancelled`` so the record of what was
    scheduled remains auditable.

    Delivery states (PQV §D.8):
    ``pending`` → ``processing`` → ``sent`` (provider accepted) →
    ``delivered`` (provider ack only) | ``failed`` | ``retry_scheduled`` |
    ``cancelled``.

    A mock adapter never sets ``delivered``.
    """

    __tablename__ = "notifications"
    __service__ = "notifications"

    id                = Column(String, primary_key=True, default=_new_id)
    organization_id   = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id         = Column(String, ForeignKey("branches.id"))
    appointment_id    = Column(String, ForeignKey("appointments.id"))
    queue_entry_id    = Column(String)
    patient_id        = Column(String, ForeignKey("patients.id"))
    notification_type = Column(String(40), nullable=False)   # appointment_confirmation | pre_visit_reminder
    channel           = Column(String(20), nullable=False)   # whatsapp | sms
    recipient_mobile  = Column(String(30), nullable=False)
    payload           = Column(JSON, default=dict)
    dedup_key         = Column(String(160), nullable=False, unique=True)
    status            = Column(String(20), nullable=False, default="pending")
    attempt_count     = Column(Integer, nullable=False, default=0)
    max_attempts      = Column(Integer, nullable=False, default=3)
    scheduled_at      = Column(DateTime(timezone=True), nullable=False)
    next_attempt_at   = Column(DateTime(timezone=True))
    last_attempt_at   = Column(DateTime(timezone=True))
    sent_at           = Column(DateTime(timezone=True))
    delivered_at      = Column(DateTime(timezone=True))
    provider          = Column(String(40), default="mock")
    provider_message_id = Column(String(120))
    error             = Column(String(500))
    cancel_reason     = Column(String(200))
    cancelled_at      = Column(DateTime(timezone=True))
    created_at        = Column(DateTime(timezone=True), default=_utcnow)
    updated_at        = Column(DateTime(timezone=True), default=_utcnow,
                               onupdate=_utcnow)

    organization      = relationship("Organization")

    __table_args__ = (
        Index("idx_notif_org_status", "organization_id", "status"),
        Index("idx_notif_due", "status", "scheduled_at"),
        Index("idx_notif_appointment", "appointment_id"),
    )
