"""AMSDP Shared Data Model — Declarative SQLAlchemy models.

Covers all MVP entities.  Service ownership is indicated by the
``__service__`` attribute for cross-service clarity.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Date, Boolean,
    ForeignKey, JSON, UniqueConstraint, Index, CheckConstraint, text,
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
# Facility hierarchy — service: organization
# ---------------------------------------------------------------------------
#
# AMSDP-FACILITY-DOCTOR-01.  A branch may describe its own physical structure:
#
#     branch ─┬─ floors      (optional)
#             ├─ departments (optional)
#             └─ rooms       (optional; may reference one floor, one department)
#
# The whole structure is **optional** — a single-room clinic needs none of it —
# so every consumer must read "no floor / no department" as *not recorded*,
# never as an error.  A room is the only level a schedule session and an
# appointment actually point at.
#
# Nothing here is ever deleted physically: ``status="inactive"`` retires a row,
# so schedules and appointments that reference it still resolve the location
# they were booked into.  Codes are unique per branch, not per organization,
# because two branches may both have a "Room 1".

class FacilityFloor(Base):
    __tablename__ = "facility_floors"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"), nullable=False)
    name            = Column(String(120), nullable=False)
    code            = Column(String(40), nullable=False)
    #: Building level ("2", "-1"); free-form because a branch may use "Ground".
    level           = Column(Integer)
    description     = Column(Text, default="")
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    branch          = relationship("Branch")

    __table_args__ = (
        UniqueConstraint("branch_id", "code", name="uq_floor_branch_code"),
        Index("idx_floor_branch", "branch_id"),
        Index("idx_floor_org", "organization_id"),
    )


class FacilityDepartment(Base):
    __tablename__ = "facility_departments"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"), nullable=False)
    name            = Column(String(120), nullable=False)
    code            = Column(String(40), nullable=False)
    description     = Column(Text, default="")
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    branch          = relationship("Branch")

    __table_args__ = (
        UniqueConstraint("branch_id", "code", name="uq_department_branch_code"),
        Index("idx_department_branch", "branch_id"),
        Index("idx_department_org", "organization_id"),
    )


class FacilityRoom(Base):
    __tablename__ = "facility_rooms"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id       = Column(String, ForeignKey("branches.id"), nullable=False)
    #: Both optional: a room may exist before the building is modelled.
    floor_id        = Column(String, ForeignKey("facility_floors.id"))
    department_id   = Column(String, ForeignKey("facility_departments.id"))
    name            = Column(String(120), nullable=False)
    code            = Column(String(40), nullable=False)
    #: consultation | procedure | ward | diagnostic | other
    room_type       = Column(String(30), default="consultation")
    capacity        = Column(Integer)
    description     = Column(Text, default="")
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    branch          = relationship("Branch")
    floor           = relationship("FacilityFloor")
    department      = relationship("FacilityDepartment")

    __table_args__ = (
        UniqueConstraint("branch_id", "code", name="uq_room_branch_code"),
        Index("idx_room_branch", "branch_id"),
        Index("idx_room_floor", "floor_id"),
        Index("idx_room_department", "department_id"),
        Index("idx_room_org", "organization_id"),
    )


class Specialty(Base):
    """Organization-owned speciality catalogue (structured doctor specialities).

    Free text on ``doctors.speciality`` is kept for display and for the legacy
    search filter, but a doctor's *structured* specialities are rows here — so
    "Cardiology" cannot be entered as "Cardiology ", "cardiology" and
    "Cardiologist" three times.
    """
    __tablename__ = "specialties"
    __service__ = "organization"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    code            = Column(String(50), nullable=False)
    name_en         = Column(String(120), nullable=False)
    name_bn         = Column(String(120), default="")
    sort_order      = Column(Integer, default=0)
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_specialty_org_code"),
        Index("idx_specialty_org", "organization_id"),
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
# Staff–Doctor assignments — service: identity
# ---------------------------------------------------------------------------
# PO-RBAC-01: An assistant may be assigned to multiple doctors within the same
# organization.  Doctor access is based on explicit assignment, not on
# organization membership alone.  The legacy ``StaffUser.doctor_id`` column is
# preserved as a compatibility field; new code consults this table instead.
# ---------------------------------------------------------------------------


class StaffDoctorAssignment(Base):
    """Explicit assignment of a staff member (assistant/doctor) to a doctor.

    A staff member may be assigned to multiple doctors, all within the same
    organization.  Only ``status = "active"`` assignments grant access.
    """

    __tablename__ = "staff_doctor_assignments"
    __service__ = "identity"

    id                = Column(String, primary_key=True, default=_new_id)
    staff_user_id     = Column(String, ForeignKey("staff_users.id"), nullable=False)
    doctor_id         = Column(String, ForeignKey("doctors.id"), nullable=False)
    organization_id   = Column(String, ForeignKey("organizations.id"), nullable=False)
    status            = Column(String(20), default="active", nullable=False)
    created_at        = Column(DateTime(timezone=True), default=_utcnow)

    staff_user        = relationship("StaffUser")
    doctor            = relationship("Doctor")
    organization      = relationship("Organization")

    __table_args__ = (
        UniqueConstraint(
            "staff_user_id", "doctor_id", name="uq_staff_doctor_assignment"),
        Index("idx_staff_doctor_assignment_staff", "staff_user_id"),
        Index("idx_staff_doctor_assignment_doctor", "doctor_id"),
        Index("idx_staff_doctor_assignment_org", "organization_id"),
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
    #: Canonical national form (``01XXXXXXXXX``) — see ``common/phone.py``.
    mobile              = Column(String(30), nullable=False)
    #: Display copy of the structured specialities (see ``doctor_specialties``).
    speciality          = Column(String(100), default="")
    qualification       = Column(String(200), default="")
    #: BMDC registration number.  Required for *activation* when the
    #: organization's registration policy says so (default: required) — an
    #: unregistered doctor may be recorded, but never made schedulable.
    registration_number = Column(String(100))
    #: unverified | pending_verification | verified | rejected
    #: Kept separate from ``status`` on purpose: *registration* state and
    #: *employment* state are different questions, and a rejected registration
    #: must not silently read as "inactive doctor".
    bmdc_verification_status = Column(String(30), default="unverified")
    bmdc_verified_at    = Column(DateTime(timezone=True))
    #: Profile photograph, stored inline as base64 with its declared MIME type.
    #: No object store exists in this deployment and adding one is out of scope;
    #: the size cap lives in the service (300 KB decoded), and the API emits a
    #: dedicated ``GET .../photo`` route rather than shipping bytes in the list.
    photo_mime          = Column(String(40))
    photo_base64        = Column(Text)
    photo_updated_at    = Column(DateTime(timezone=True))
    consultation_fee    = Column(Float)
    locale              = Column(String(10), default="bn")
    status              = Column(String(20), default="active")
    created_at          = Column(DateTime(timezone=True), default=_utcnow)

    organization        = relationship("Organization")

    __table_args__ = (
        Index("idx_doctor_org", "organization_id"),
        Index("idx_doctor_org_mobile", "organization_id", "mobile"),
    )


class DoctorSpecialty(Base):
    """A doctor's structured speciality (many per doctor)."""
    __tablename__ = "doctor_specialties"
    __service__ = "doctor"

    id          = Column(String, primary_key=True, default=_new_id)
    doctor_id   = Column(String, ForeignKey("doctors.id"), nullable=False)
    specialty_id = Column(String, ForeignKey("specialties.id"), nullable=False)
    created_at  = Column(DateTime(timezone=True), default=_utcnow)

    doctor      = relationship("Doctor", backref="specialty_links")
    specialty   = relationship("Specialty")

    __table_args__ = (
        UniqueConstraint("doctor_id", "specialty_id", name="uq_doctor_specialty"),
        Index("idx_doctor_specialty_doctor", "doctor_id"),
    )


class DoctorBranch(Base):
    """A doctor's assignment to a branch, with its own chamber and status.

    ``(doctor_id, branch_id)`` is unique — a doctor is assigned to a branch at
    most once.  ``is_primary`` marks the default branch for new bookings; the
    partial unique index below (mirrored in the migration) makes "exactly one
    primary per doctor" a database fact rather than a convention.
    """
    __tablename__ = "doctor_branches"
    __service__ = "doctor"

    id          = Column(String, primary_key=True, default=_new_id)
    doctor_id   = Column(String, ForeignKey("doctors.id"), nullable=False)
    branch_id   = Column(String, ForeignKey("branches.id"), nullable=False)
    #: The doctor's default chamber at this branch, when one is known.
    room_id     = Column(String, ForeignKey("facility_rooms.id"))
    #: Per-branch fee override; ``NULL`` means "use ``doctors.consultation_fee``".
    consultation_fee_override = Column(Float)
    is_primary  = Column(Boolean, default=False, nullable=False)
    status      = Column(String(20), default="active")
    created_at  = Column(DateTime(timezone=True), default=_utcnow)

    doctor      = relationship("Doctor", backref="branch_assignments")
    branch      = relationship("Branch")
    room        = relationship("FacilityRoom")

    __table_args__ = (
        UniqueConstraint("doctor_id", "branch_id", name="uq_doctor_branch"),
        Index("idx_doctor_branch_branch", "branch_id"),
        Index("uq_doctor_one_primary", "doctor_id", unique=True,
              postgresql_where=text("is_primary")),
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


class ScheduleSession(Base):
    """One recurring clinic session of a schedule, with its chamber.

    AMSDP-FACILITY-DOCTOR-01.  ``Schedule.slot_templates`` describes *when* a
    doctor is available, but it cannot say *where* — so a doctor working two
    branches, or two rooms in one branch, could not be modelled and the
    09:00–13:00 Monday slot could be assigned to two rooms at once.

    A session is the authoritative row: ``(schedule, day_of_week, start_time)``
    is unique, and the migration adds two partial unique indexes so that the
    same room — and the same doctor — cannot hold two *active* sessions that
    start at the same minute on the same weekday.  Partial overlaps are refused
    by the service inside a transaction that locks the room row, because an
    EXCLUDE constraint would need the ``btree_gist`` extension, which this
    deployment does not have.

    ``Schedule.slot_templates`` is kept as the derived projection of the active
    sessions (the appointment calendar reads it), so existing behaviour is
    unchanged for schedules that never use sessions.
    """
    __tablename__ = "schedule_sessions"
    __service__ = "scheduling"

    id                    = Column(String, primary_key=True, default=_new_id)
    organization_id       = Column(String, ForeignKey("organizations.id"), nullable=False)
    branch_id             = Column(String, ForeignKey("branches.id"), nullable=False)
    schedule_id           = Column(String, ForeignKey("schedules.id"), nullable=False)
    doctor_id             = Column(String, ForeignKey("doctors.id"), nullable=False)
    #: 0 = Monday … 6 = Sunday (the same convention as ``slot_templates``).
    day_of_week           = Column(Integer, nullable=False)
    start_time            = Column(String(5), nullable=False)   # HH:MM
    end_time              = Column(String(5), nullable=False)   # HH:MM
    floor_id              = Column(String, ForeignKey("facility_floors.id"))
    department_id         = Column(String, ForeignKey("facility_departments.id"))
    room_id               = Column(String, ForeignKey("facility_rooms.id"))
    slot_duration_minutes = Column(Integer, default=15)
    max_patients          = Column(Integer, default=1)
    effective_from        = Column(Date)
    effective_to          = Column(Date)
    status                = Column(String(20), default="active")
    created_at            = Column(DateTime(timezone=True), default=_utcnow)
    updated_at            = Column(DateTime(timezone=True), default=_utcnow,
                                   onupdate=_utcnow)

    schedule              = relationship("Schedule")
    doctor                = relationship("Doctor")
    branch                = relationship("Branch")
    floor                 = relationship("FacilityFloor")
    department            = relationship("FacilityDepartment")
    room                  = relationship("FacilityRoom")

    __table_args__ = (
        UniqueConstraint("schedule_id", "day_of_week", "start_time",
                         name="uq_session_schedule_slot"),
        Index("idx_session_schedule", "schedule_id"),
        Index("idx_session_room", "room_id"),
        Index("idx_session_doctor", "doctor_id"),
        Index("idx_session_org", "organization_id"),
        # Deterministic double-booking guards (detail: migration docstring).
        Index("uq_session_room_start", "room_id", "day_of_week", "start_time",
              unique=True, postgresql_where=text(
                  "room_id IS NOT NULL AND status = 'active'")),
        Index("uq_session_doctor_start", "doctor_id", "day_of_week", "start_time",
              unique=True, postgresql_where=text("status = 'active'")),
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
    # --- Location provenance + snapshot (AMSDP-FACILITY-DOCTOR-01) -----------
    # Which session the booking resolved its chamber from.  Both are nullable
    # because appointments created before this feature existed have no session.
    session_id            = Column(String, ForeignKey("schedule_sessions.id"))
    schedule_id           = Column(String, ForeignKey("schedules.id"))
    # The chamber is *snapshotted at booking time*, deliberately denormalised:
    # a receptionist must be able to reprint yesterday's slip showing room 204
    # after the facility has been re-organised.  Live room data would rewrite
    # history.  ``*_id`` columns are kept for later joins/analytics only.
    floor_id              = Column(String, ForeignKey("facility_floors.id"))
    floor_name            = Column(String(120))
    department_id         = Column(String, ForeignKey("facility_departments.id"))
    department_name       = Column(String(120))
    room_id               = Column(String, ForeignKey("facility_rooms.id"))
    room_name             = Column(String(120))
    # --- Symptom onset, optional and recorded at booking (AMSDP-SYMPTOM-01) --
    # A closed vocabulary (``appointment/symptoms.ONSET_CODES``) instead of a
    # date: a patient at a reception desk routinely cannot name a day, and
    # forcing one would either block the booking or invent a fact.  ``None``
    # means "not recorded", which is different from ``UNKNOWN`` ("asked, could
    # not say").  The free short note is the receptionist's own wording.
    symptom_onset_code    = Column(String(30))
    symptom_onset_note    = Column(Text)
    created_at            = Column(DateTime(timezone=True), default=_utcnow)

    organization          = relationship("Organization")
    branch                = relationship("Branch")
    patient               = relationship("Patient")
    doctor                = relationship("Doctor")
    session               = relationship("ScheduleSession")
    room                  = relationship("FacilityRoom")

    __table_args__ = (
        Index("idx_appt_doctor_date", "doctor_id", "appointment_date"),
        Index("idx_appt_patient", "patient_id"),
        Index("idx_appt_session", "session_id"),
    )


# ---------------------------------------------------------------------------
# Symptoms — service: appointment
# ---------------------------------------------------------------------------

class SymptomCatalog(Base):
    """Organization-owned catalogue of **patient-reported symptoms**.

    Scope is deliberately narrow, and the schema says so: an entry names
    something a patient can *report* ("মাথাব্যথা / headache", "কাশি / cough").
    It is not a diagnosis, a clinical finding, a disease or a triage rule —
    AMSDP never derives a condition from a selected symptom, and
    ``review_status`` exists precisely so an unreviewed entry cannot be
    presented as clinically validated.

    Bilingual by construction: ``name_bn`` is required for a displayable entry
    and both synonym lists carry the words a receptionist might actually type.

    ``specialty_hints`` is a **ranking hint only** — a list of speciality codes
    (``cardiology``, ``medicine``, …) copied from the organization's
    ``specialties.code`` values.  A cardiology booking may therefore show chest
    pain earlier, while every other symptom stays searchable and selectable.
    It is a soft tag, not a foreign key: speciality catalogues are per
    organization, and a hint must never make a symptom unselectable anywhere.

    The whole catalogue is returned to the booking UI in one response and
    searched in the browser (the same design as BanglaNameSense), so a
    keystroke never costs a request.
    """
    __tablename__ = "symptom_catalog"
    __service__ = "appointment"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    #: Stable identifier for this entry within the organization (``headache``).
    code            = Column(String(60), nullable=False)
    name_en         = Column(String(160), nullable=False)
    name_bn         = Column(String(160), default="")
    #: Recognised alternate wording, per script.  JSON lists of short strings.
    synonyms_en     = Column(JSON, default=list)
    synonyms_bn     = Column(JSON, default=list)
    #: Coarse classification for grouping and later analytics (not shown as a
    #: clinical category): general, neurological, respiratory, …
    category        = Column(String(60), default="general")
    #: Ranking hints (see the class docstring).  Never a filter.
    specialty_hints = Column(JSON, default=list)
    #: Where the wording came from, and how far it has been reviewed.
    source          = Column(String(300), default="")
    #: ``unreviewed`` | ``curated`` | ``clinically_reviewed``
    review_status   = Column(String(30), default="unreviewed")
    #: Ascending display/commonness order; a deterministic tie-break for search.
    sort_order      = Column(Integer, default=100)
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_symptom_org_code"),
        Index("idx_symptom_org", "organization_id"),
        Index("idx_symptom_org_status", "organization_id", "status"),
    )


class AppointmentSymptom(Base):
    """One symptom recorded against one appointment, as recorded at booking.

    The receptionist records two things that must stay distinguishable, so the
    table carries both shapes rather than collapsing them into a string:

    * ``kind='catalogue'`` — ``symptom_id`` references ``symptom_catalog``.
      ``name_en``/``name_bn`` are **snapshotted** at booking time, exactly like
      the chamber snapshot on ``appointments``: renaming or retiring a
      catalogue entry must never rewrite what was recorded for this visit.
    * ``kind='free_text'`` — ``symptom_id`` is NULL and ``text_reported`` holds
      the words the receptionist typed, because the complaint was not in the
      catalogue.  ``text_key`` is the case/whitespace-normalised form used for
      duplicate suppression only.

    Duplicates are prevented by two *partial* unique indexes, so the database —
    not only the service — refuses the same catalogue entry twice on one
    appointment, and the same free-text description twice::

        uq_appt_symptom_catalogue (appointment_id, symptom_id)
                                  WHERE symptom_id IS NOT NULL
        uq_appt_symptom_text      (appointment_id, text_key)
                                  WHERE symptom_id IS NULL AND text_key <> ''

    ``organization_id`` is written on every row (the tenant key is
    ``organization_id`` throughout AMSDP) even though it is derivable from the
    appointment: a cross-tenant read then fails closed on this table too, and
    the index makes that the cheap path.
    """
    __tablename__ = "appointment_symptoms"
    __service__ = "appointment"

    id              = Column(String, primary_key=True, default=_new_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    appointment_id  = Column(String, ForeignKey("appointments.id"), nullable=False)
    #: 'catalogue' | 'free_text' — never inferred at read time.
    kind            = Column(String(20), nullable=False)
    symptom_id      = Column(String, ForeignKey("symptom_catalog.id"))
    #: Snapshot of the catalogue entry (empty for free text).
    name_en         = Column(String(160), nullable=False, default="")
    name_bn         = Column(String(160), nullable=False, default="")
    #: What the receptionist typed (empty for catalogue entries).
    text_reported   = Column(Text, nullable=False, default="")
    text_key        = Column(String(300), nullable=False, default="")
    recorded_by     = Column(String)
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    symptom         = relationship("SymptomCatalog")

    __table_args__ = (
        CheckConstraint(
            "(kind = 'catalogue' AND symptom_id IS NOT NULL"
            " AND length(trim(text_reported)) = 0)"
            " OR (kind = 'free_text' AND symptom_id IS NULL"
            " AND length(trim(text_reported)) > 0)",
            name="ck_appt_symptom_shape"),
        Index("idx_appt_symptom_appt", "appointment_id"),
        Index("idx_appt_symptom_org", "organization_id"),
        Index("uq_appt_symptom_catalogue", "appointment_id", "symptom_id",
              unique=True, postgresql_where=text("symptom_id IS NOT NULL")),
        Index("uq_appt_symptom_text", "appointment_id", "text_key",
              unique=True,
              postgresql_where=text("symptom_id IS NULL AND text_key <> ''")),
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
# Platform audit events — service: platform (O-SaaS-2)
# ---------------------------------------------------------------------------
# Platform-only events belong in ``platform_audit_events``, separate from
# tenant-affecting events in ``audit_events``.  This table has NO
# ``organization_id`` — platform events are not scoped to a tenant.
# Per O-SaaS-10, the actor is identified by named platform operator identity
# plus platform role, minimizing unnecessary personal information.
# ---------------------------------------------------------------------------


class PlatformAuditEvent(Base):
    """Audit event for platform-only operations (O-SaaS-2, O-SaaS-10).

    Tenant-affecting events go to ``audit_events`` with a non-null
    ``organization_id``.  Platform-only events (platform operator provisioning,
    tenant suspension, cross-org support access initiated from the platform
    plane) go here.
    """

    __tablename__ = "platform_audit_events"
    __service__ = "platform"

    id                = Column(String, primary_key=True, default=_new_id)
    service           = Column(String(50), nullable=False)
    action            = Column(String(50), nullable=False)
    target_type       = Column(String(50), nullable=False)
    target_id         = Column(String, nullable=False)
    actor_id          = Column(String, nullable=False)
    actor_role        = Column(String(30), nullable=False)
    before            = Column(JSON)
    after             = Column(JSON)
    reason            = Column(Text, default="")
    timestamp         = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_platform_audit_action", "action"),
        Index("idx_platform_audit_time", "timestamp"),
    )


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
