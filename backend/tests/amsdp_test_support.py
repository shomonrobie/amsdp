"""Shared seeding and auth helpers for the PostgreSQL-backed service tests.

Sequence 4 finding LEGACY-TESTS-P1 quarantined seven modules that had been
written against the pre-database in-memory stores (``_patients_db``,
``_orgs_db``, …).  They are rewritten against the real database; this module
holds the parts every rewritten module needs, so each test file states only its
own scenario instead of re-deriving fixtures.

Conventions (they match ``tests/test_sequence3.py``, the suite's reference
seeding story):

* **Reference rows are never deleted.**  Organizations, branches, doctors and
  staff users are referenced by foreign key from the append-only
  ``audit_events`` trail, so removing them would rewrite history.  They are
  created once, idempotently, and reused.
* **Owned business rows are purged** before each test by :func:`purge_org`, in
  foreign-key order, and only for the organization the caller names.
* **Authentication is real**: :func:`headers` mints a signed JWT from a real
  ``staff_users`` row, so the tests exercise the same dependency chain
  (``common.auth.get_current_user`` → role → permission) as production.  No test
  bypasses authorization.

Every helper writes through ``common.database.SessionFactory`` — the same engine
the services use — so a passing test means the row is really in PostgreSQL.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import bcrypt                                                    # noqa: E402
import jwt                                                       # noqa: E402

from common.auth import _ALGO, _SECRET                            # noqa: E402
from common.database import SessionFactory                        # noqa: E402
from common.models import (Appointment, AppointmentSymptom, Branch, Doctor,  # noqa: E402
                           DoctorBranch, Notification, Organization, Patient,
                           QueueEntry, QueueSequence, Schedule, ScheduleSession,
                           StaffUser, SymptomCatalog, TrackingToken)

#: Password used by every user this module creates.
PASSWORD = "testpass123"


class db_session:                                    # noqa: N801 - context helper
    """``with db_session() as s:`` — a session that always closes."""

    def __enter__(self):
        self.session = SessionFactory()
        return self.session

    def __exit__(self, *exc_info):
        try:
            if exc_info[0] is not None:
                self.session.rollback()
        finally:
            self.session.close()
        return False


def uniq(prefix: str) -> str:
    """A short unique suffix, so a shared dev database never collides."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Reference rows (create once, never delete)
# ---------------------------------------------------------------------------

def ensure_org(org_id: str, *, timezone_name: str = "Asia/Dhaka") -> str:
    """Create the organization if absent; return its id."""
    with db_session() as s:
        if s.query(Organization).filter(Organization.id == org_id).first() is None:
            s.add(Organization(id=org_id, name=org_id, code=org_id.upper(),
                               timezone=timezone_name, locale="en",
                               facility_type="clinic", config={}))
            s.commit()
    return org_id


def ensure_branch(branch_id: str, org_id: str) -> str:
    with db_session() as s:
        if s.query(Branch).filter(Branch.id == branch_id).first() is None:
            s.add(Branch(id=branch_id, organization_id=org_id,
                         name=branch_id, code=branch_id.upper()))
            s.commit()
    return branch_id


def ensure_doctor(doctor_id: str, org_id: str, *, name: str = "Dr. Test",
                  mobile: str = "01700000000", speciality: str = "") -> str:
    with db_session() as s:
        if s.query(Doctor).filter(Doctor.id == doctor_id).first() is None:
            s.add(Doctor(id=doctor_id, organization_id=org_id, name=name,
                         mobile=mobile, speciality=speciality, locale="en"))
            s.commit()
    return doctor_id


def ensure_patient(patient_id: str, org_id: str, *, name: str = "Test Patient",
                   mobile: str = "01700000100", sex: str = "") -> str:
    with db_session() as s:
        if s.query(Patient).filter(Patient.id == patient_id).first() is None:
            s.add(Patient(id=patient_id, organization_id=org_id, name=name,
                          mobile=mobile, sex=sex))
            s.commit()
    return patient_id


def ensure_symptom(code: str, org_id: str, *, name_en: str = "",
                   name_bn: str = "", synonyms_en=None, synonyms_bn=None,
                   category: str = "general", specialty_hints=None,
                   sort_order: int = 100, status: str = "active",
                   symptom_id: str | None = None) -> str:
    """Create (idempotently) one catalogue entry and return its id.

    Ids are stable per ``(organization, code)`` so a test can name the entry it
    depends on without keeping a fixture map.
    """
    row_id = symptom_id or f"{org_id}::{code}"
    with db_session() as s:
        row = s.query(SymptomCatalog).filter(
            SymptomCatalog.organization_id == org_id,
            SymptomCatalog.code == code).first()
        if row is None:
            row = SymptomCatalog(
                id=row_id, organization_id=org_id, code=code,
                name_en=name_en or code.title(), name_bn=name_bn,
                synonyms_en=list(synonyms_en or []),
                synonyms_bn=list(synonyms_bn or []),
                category=category,
                specialty_hints=list(specialty_hints or []),
                sort_order=sort_order, status=status,
                source="test fixture", review_status="curated")
            s.add(row)
        else:
            row.name_en = name_en or row.name_en
            row.name_bn = name_bn or row.name_bn
            row.status = status
            row.sort_order = sort_order
        s.commit()
        return row.id


def ensure_user(username: str, role: str, org_id: str,
                branch_id: str | None = None) -> str:
    """Create (or repair) a staff user and return its id."""
    password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    with db_session() as s:
        user = s.query(StaffUser).filter(StaffUser.username == username).first()
        if user is None:
            user = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                             branch_id=branch_id, username=username,
                             password_hash=password_hash,
                             display_name=username.replace("_", " ").title(),
                             role=role, status="active", locale="en")
            s.add(user)
        else:
            user.organization_id, user.branch_id = org_id, branch_id
            user.role, user.status = role, "active"
            user.password_hash = password_hash
        s.commit()
        return user.id


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def token(username: str) -> str:
    """A valid two-hour JWT for an existing staff user."""
    with db_session() as s:
        user = s.query(StaffUser).filter(
            StaffUser.username == username).first()
        if user is None:
            raise AssertionError(f"no such staff user: {username}")
        payload = {"sub": user.id, "org": user.organization_id,
                   "branch": user.branch_id, "role": user.role}
        payload["exp"] = int((datetime.now(timezone.utc)
                              + timedelta(hours=2)).timestamp())
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def headers(username: str) -> dict:
    """``Authorization`` header for *username*."""
    return {"Authorization": f"Bearer {token(username)}"}


# ---------------------------------------------------------------------------
# Service apps
# ---------------------------------------------------------------------------

def load_app(service: str):
    """Import ``<service>/main.py`` and return its FastAPI app.

    The service directory is added to ``sys.path`` only for the duration of the
    import: ``identity`` resolves its Pydantic schemas with a bare
    ``from models import …``, and leaving every service directory on the path
    would let one service's ``models`` shadow another's (the failure mode the
    abandoned ``tests/test_e2e.py`` hit).
    """
    import importlib
    service_dir = os.path.join(BACKEND_DIR, service)
    sys.path.insert(0, service_dir)
    try:
        module = importlib.import_module(f"{service}.main")
    finally:
        try:
            sys.path.remove(service_dir)
        except ValueError:                            # pragma: no cover
            pass
    return module.app


# ---------------------------------------------------------------------------
# Cleanup of rows this suite owns
# ---------------------------------------------------------------------------

def purge_org(org_id: str) -> None:
    """Delete the *business* rows of one organization, in FK-safe order.

    Reference rows (organization, branches, doctors, staff users) are kept: the
    audit trail references them.  Nothing outside *org_id* is touched.
    """
    with db_session() as s:
        appointment_ids = [row[0] for row in s.query(Appointment.id).filter(
            Appointment.organization_id == org_id).all()]
        s.query(Notification).filter(
            Notification.organization_id == org_id).delete(
            synchronize_session=False)
        s.query(QueueEntry).filter(
            QueueEntry.organization_id == org_id).delete(
            synchronize_session=False)
        doctor_ids = [row[0] for row in s.query(Doctor.id).filter(
            Doctor.organization_id == org_id).all()]
        if doctor_ids:
            # The per-(doctor, date) token/position counters are business rows:
            # left behind, a re-run of the same flow would start at position 2.
            s.query(QueueSequence).filter(
                QueueSequence.doctor_id.in_(doctor_ids)).delete(
                synchronize_session=False)
        if appointment_ids:
            # Recorded symptoms are children of the appointment (AMSDP-SYMPTOM-01)
            # and must go before it, or the foreign key refuses the delete.
            s.query(AppointmentSymptom).filter(
                AppointmentSymptom.appointment_id.in_(appointment_ids)).delete(
                synchronize_session=False)
            s.query(TrackingToken).filter(
                TrackingToken.appointment_id.in_(appointment_ids)).delete(
                synchronize_session=False)
        s.query(Appointment).filter(
            Appointment.organization_id == org_id).delete(
            synchronize_session=False)
        # Sessions reference schedules, so they go first (AMSDP-FACILITY-DOCTOR-01).
        s.query(ScheduleSession).filter(
            ScheduleSession.organization_id == org_id).delete(
            synchronize_session=False)
        s.query(Schedule).filter(
            Schedule.organization_id == org_id).delete(
            synchronize_session=False)
        if doctor_ids:
            s.query(DoctorBranch).filter(
                DoctorBranch.doctor_id.in_(doctor_ids)).delete(
                synchronize_session=False)
        s.query(Patient).filter(Patient.organization_id == org_id).delete(
            synchronize_session=False)
        # The symptom catalogue is seeded reference data for each test
        # organization (AMSDP-SYMPTOM-01); it has no children once the
        # appointment symptom rows above are gone.
        s.query(SymptomCatalog).filter(
            SymptomCatalog.organization_id == org_id).delete(
            synchronize_session=False)
        s.commit()
