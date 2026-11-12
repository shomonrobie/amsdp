"""AMSDP Demonstration Seed Script - M1/M4.

Idempotent, non-destructive. Creates:
- One demo organization with two branches.
- Six staff accounts (one per canonical role).
- Five doctors with branch assignments.
- Thirty fictional patients.
- A demo schedule.

Run: python3 backend/seed/seed_demo.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid, bcrypt
from datetime import datetime, timezone
from common.database import SessionFactory
from common.models import (
    Organization, Branch, StaffUser, Doctor, DoctorBranch, Patient,
    Schedule, Appointment, QueueEntry,
)

DEMO_ORG = {"id": "demo-org-001", "name": "Uposhak Hospital", "code": "UPH-001",
    "timezone": "Asia/Dhaka", "locale": "bn", "facility_type": "hospital",
    "address": "12 Gulshan Avenue, Dhaka 1212"}

DEMO_BRANCHES = [
    {"id": "demo-br-001", "name": "Main Branch", "code": "BR-UPH-001",
     "address": "12 Gulshan Avenue, Dhaka 1212", "phone": "+880-2-5551234"},
    {"id": "demo-br-002", "name": "Gulshan Clinic", "code": "BR-UPH-002",
     "address": "45 Banani Road, Dhaka 1213", "phone": "+880-2-5555678"},
]

DEMO_STAFF = [
    {"username": "admin", "role": "super_admin",
     "display_name": "Super Admin", "locale": "en"},
    {"username": "org_admin", "role": "org_admin",
     "display_name": "Org Admin", "locale": "bn"},
    {"username": "br_admin", "role": "branch_admin",
     "display_name": "Branch Admin", "locale": "bn"},
    {"username": "receptionist", "role": "receptionist",
     "display_name": "Receptionist", "locale": "bn"},
    {"username": "doctor", "role": "doctor",
     "display_name": "Doctor User", "locale": "en"},
    {"username": "assistant", "role": "assistant",
     "display_name": "Assistant", "locale": "bn"},
]

# Demo staff passwords are NOT stored in this repository.  Each account's
# password is read from AMSDP_DEMO_PASSWORD_<USERNAME> (for example
# AMSDP_DEMO_PASSWORD_ADMIN) and falls back to a single shared
# AMSDP_DEMO_PASSWORD.  Put them in the gitignored .env file — see
# .env.example — and run this script through _tools/init_demo_env.sh.


def _configured_password(username: str):
    """Return the configured demo password for an account, or None when unset."""
    return (os.environ.get(f"AMSDP_DEMO_PASSWORD_{username.upper()}")
            or os.environ.get("AMSDP_DEMO_PASSWORD"))


def _demo_password(username: str) -> str:
    """Return the configured password for a demo account, or fail loudly."""
    value = _configured_password(username)
    if not value:
        sys.exit(
            f"ERROR: no demo password configured for staff account '{username}'.\n"
            f"       Set AMSDP_DEMO_PASSWORD_{username.upper()} (or a shared\n"
            "       AMSDP_DEMO_PASSWORD) in the gitignored .env file — see\n"
            "       .env.example.  Credentials are never committed."
        )
    return value

DEMO_DOCTORS = [
    {"id": "demo-dr-001", "name": "Dr. Fatima Begum", "mobile": "01711111111",
     "speciality": "Cardiology", "qualification": "MBBS, MD (Cardiology)"},
    {"id": "demo-dr-002", "name": "Dr. Kamal Hossain", "mobile": "01711111112",
     "speciality": "General Medicine", "qualification": "MBBS, FCPS"},
    {"id": "demo-dr-003", "name": "Dr. Shahnaz Rahman", "mobile": "01711111113",
     "speciality": "Pediatrics", "qualification": "MBBS, DCH"},
    {"id": "demo-dr-004", "name": "Dr. Anwar Hossain", "mobile": "01711111114",
     "speciality": "Orthopedics", "qualification": "MBBS, MS (Ortho)"},
    {"id": "demo-dr-005", "name": "Dr. Salma Khatun", "mobile": "01711111115",
     "speciality": "Gynecology", "qualification": "MBBS, FCPS (OBGYN)"},
]

DEMO_PATIENTS = [
    {"name": "Md. Abdul Karim", "mobile": "01722222221", "sex": "male", "dob": "1980-04-12", "age": None},
    {"name": "Jamila Begum", "mobile": "01722222222", "sex": "female", "dob": None, "age": 34},
    {"name": "Rafiq Hasan", "mobile": "01722222223", "sex": "male", "dob": None, "age": None},
    {"name": "Nusrat Jahan", "mobile": "01722222224", "sex": "female", "dob": "1995-11-03", "age": None},
    {"name": "Shahidul Islam", "mobile": "01722222225", "sex": "male", "dob": None, "age": 61},
    {"name": "Rokeya Sultana", "mobile": "01722222226", "sex": "female", "dob": None, "age": 42},
    {"name": "Tariqul Islam", "mobile": "01722222227", "sex": "male", "dob": None, "age": None},
    {"name": "Farhana Akter", "mobile": "01722222228", "sex": "female", "dob": "2001-02-20", "age": None},
    {"name": "Mizanur Rahman", "mobile": "01722222229", "sex": "male", "dob": None, "age": 48},
    {"name": "Ayesha Siddiqua", "mobile": "01722222230", "sex": "female", "dob": None, "age": 7},
]

# One schedule template per doctor (Mon-Fri morning/afternoon clinic).
DEMO_SCHEDULE_TEMPLATES = [
    {"doctor_id": "demo-dr-001", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "09:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 2, "start_time": "09:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-002", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "09:00", "end_time": "14:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 1, "start_time": "14:00", "end_time": "18:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-003", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "10:00", "end_time": "14:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 3, "start_time": "10:00", "end_time": "14:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-004", "branch_id": "demo-br-002",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "09:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 3},
     ]},
    {"doctor_id": "demo-dr-005", "branch_id": "demo-br-002",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "09:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 3},
     ]},
]

# Deterministic demo appointments for TODAY so the live dashboard shows data.
# After the demo date passes, the seed re-creates them for the current day.
DEMO_APPOINTMENTS = [
    {"id": "demo-appt-001", "patient": "Md. Abdul Karim", "doctor_id": "demo-dr-001",
     "branch_id": "demo-br-001", "start_time": "09:00", "status": "CONFIRMED",
     "booking_source": "reception", "appointment_type": "scheduled"},
    {"id": "demo-appt-002", "patient": "Jamila Begum", "doctor_id": "demo-dr-002",
     "branch_id": "demo-br-001", "start_time": "09:15", "status": "CHECKED_IN",
     "booking_source": "phone", "appointment_type": "scheduled"},
    {"id": "demo-appt-003", "patient": "Rafiq Hasan", "doctor_id": "demo-dr-002",
     "branch_id": "demo-br-001", "start_time": "09:30", "status": "BOOKED",
     "booking_source": "reception", "appointment_type": "scheduled"},
    {"id": "demo-appt-004", "patient": "Nusrat Jahan", "doctor_id": "demo-dr-003",
     "branch_id": "demo-br-001", "start_time": "10:00", "status": "IN_QUEUE",
     "booking_source": "reception", "appointment_type": "scheduled"},
    {"id": "demo-appt-005", "patient": "Shahidul Islam", "doctor_id": "demo-dr-001",
     "branch_id": "demo-br-001", "start_time": "10:15", "status": "CANCELLED",
     "booking_source": "phone", "appointment_type": "scheduled"},
    {"id": "demo-appt-006", "patient": "Rokeya Sultana", "doctor_id": "demo-dr-002",
     "branch_id": "demo-br-001", "start_time": "11:00", "status": "COMPLETED",
     "booking_source": "reception", "appointment_type": "scheduled"},
    {"id": "demo-appt-007", "patient": "Tariqul Islam", "doctor_id": "demo-dr-004",
     "branch_id": "demo-br-002", "start_time": "09:00", "status": "CONFIRMED",
     "booking_source": "reception", "appointment_type": "scheduled"},
]

# A small pre-seeded queue for doctor demo-dr-002 so the doctor persona has
# work to do immediately on login (checked-in appointments waiting in queue).
DEMO_QUEUE = [
    {"token": "T-DR002-001", "position": 1, "doctor_id": "demo-dr-002",
     "patient": "Jamila Begum", "status": "waiting", "entry_source": "appointment"},
    {"token": "T-DR002-002", "position": 2, "doctor_id": "demo-dr-002",
     "patient": "Rokeya Sultana", "status": "completed", "entry_source": "appointment"},
]


def seed():
    session = SessionFactory()
    try:
        _seed_org(session)
        _seed_branch(session)
        _seed_doctors(session)
        _seed_staff(session)
        _seed_patients(session)
        _seed_schedules(session)
        _seed_appointments(session)
        _seed_queue(session)
        session.commit()
        print("Seed complete.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed_org(session):
    org = session.query(Organization).filter(Organization.id == DEMO_ORG["id"]).first()
    if org:
        print("Organization already exists, skipping.")
        return
    org = Organization(**DEMO_ORG)
    session.add(org)
    print("Created organization:", DEMO_ORG["code"])


def _seed_branch(session):
    for b in DEMO_BRANCHES:
        existing = session.query(Branch).filter(Branch.id == b["id"]).first()
        if existing:
            print(f"  Branch '{b['name']}' already exists, skipping.")
            continue
        branch = Branch(organization_id=DEMO_ORG["id"],
            id=b["id"], name=b["name"], code=b["code"],
            address=b.get("address", ""), phone=b.get("phone"))
        session.add(branch)
        print(f"  Created branch: {b['code']}")


def _seed_staff(session):
    for s in DEMO_STAFF:
        existing = session.query(StaffUser).filter(
            StaffUser.username == s["username"]
        ).first()
        if existing:
            changed = False
            if s["role"] == "doctor" and not existing.doctor_id:
                existing.doctor_id = "demo-dr-002"
                changed = True
            # Re-running the seed refreshes the hash from the environment, so a
            # rotated demo password in .env takes effect without touching the DB
            # by hand (the seed stays idempotent: same env → same credential).
            configured = _configured_password(s["username"])
            if configured:
                existing.password_hash = bcrypt.hashpw(
                    configured.encode(), bcrypt.gensalt()).decode()
                changed = True
                print(f"  Staff '{s['username']}' exists — password hash refreshed from environment.")
            if changed:
                session.commit()
            else:
                print(f"  Staff '{s['username']}' already exists, skipping.")
            continue
        pw_hash = bcrypt.hashpw(_demo_password(s["username"]).encode(), bcrypt.gensalt()).decode()
        user = StaffUser(
            id=str(uuid.uuid4()),
            organization_id=DEMO_ORG["id"],
            branch_id=DEMO_BRANCHES[0]["id"],
            doctor_id="demo-dr-002" if s["role"] == "doctor" else None,
            username=s["username"],
            password_hash=pw_hash,
            display_name=s["display_name"],
            role=s["role"],
            locale=s.get("locale", "bn"),
            status="active",
        )
        session.add(user)
        print(f"  Created staff: {s['username']} ({s['role']})")


def _seed_doctors(session):
    for d in DEMO_DOCTORS:
        existing = session.query(Doctor).filter(Doctor.id == d["id"]).first()
        if existing:
            print(f"  Doctor '{d['name']}' already exists, skipping.")
            continue
        doctor = Doctor(organization_id=DEMO_ORG["id"], **d)
        session.add(doctor)
        # Assign each doctor to the branch(es) they serve (derived from schedules)
        branch_ids = [t["branch_id"] for t in DEMO_SCHEDULE_TEMPLATES
                      if t["doctor_id"] == d["id"]] or ["demo-br-001"]
        for b in set(branch_ids):
            existing_ab = session.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == d["id"],
                DoctorBranch.branch_id == b).first()
            if not existing_ab:
                session.add(DoctorBranch(doctor_id=d["id"], branch_id=b))
        print(f"  Created doctor: {d['name']}")


def _seed_schedules(session):
    for t in DEMO_SCHEDULE_TEMPLATES:
        existing = session.query(Schedule).filter(
            Schedule.doctor_id == t["doctor_id"],
            Schedule.branch_id == t["branch_id"]).first()
        if existing:
            print(f"  Schedule for {t['doctor_id']} @ {t['branch_id']} exists, skipping.")
            continue
        sched = Schedule(
            id=f"sched-{t['doctor_id']}",
            doctor_id=t["doctor_id"],
            organization_id=DEMO_ORG["id"],
            branch_id=t["branch_id"],
            appointment_model=t["appointment_model"],
            slot_templates=t["slot_templates"],
            status="active",
        )
        session.add(sched)
        print(f"  Created schedule: {t['doctor_id']} @ {t['branch_id']}")


def _seed_appointments(session):
    from datetime import date
    today = date.today()
    patients = {p["name"]: p for p in DEMO_PATIENTS}
    for a in DEMO_APPOINTMENTS:
        pat = patients.get(a["patient"])
        if not pat:
            print(f"  Appt {a['id']}: patient {a['patient']} missing, skipping.")
            continue
        # Idempotent: an appointment id exists -> refresh the DATE only for
        # demo-owned seed rows (so a morning re-seed places the board on today);
        # never touch rows created through the application.
        existing = session.query(Appointment).filter(
            Appointment.id == a["id"]).first()
        if existing:
            if existing.created_by == "demo-seed" and existing.appointment_date != today:
                existing.appointment_date = today
                print(f"  Appointment {a['id']}: refreshed date to {today}.")
            else:
                print(f"  Appointment {a['id']} already exists, skipping.")
            continue
        from common.models import Patient as PatientModel
        pat_row = session.query(PatientModel).filter(
            PatientModel.organization_id == DEMO_ORG["id"],
            PatientModel.mobile == pat["mobile"]).first()
        if not pat_row:
            print(f"  Appointment {a['id']}: patient row missing, skipping.")
            continue
        serial = 1 + sum(1 for x in DEMO_APPOINTMENTS
                         if x["doctor_id"] == a["doctor_id"])
        appt = Appointment(
            id=a["id"], organization_id=DEMO_ORG["id"], branch_id=a["branch_id"],
            patient_id=pat_row.id, doctor_id=a["doctor_id"],
            appointment_date=today, start_time=a["start_time"],
            serial_number=serial, appointment_type=a["appointment_type"],
            booking_source=a["booking_source"], status=a["status"],
            status_history=[{"from": "", "to": a["status"],
                             "at": str(datetime.now(timezone.utc))}],
            token_number=f"T-{a['doctor_id'][-3:].upper()}-{serial:03d}",
            created_by="demo-seed",
        )
        session.add(appt)
        print(f"  Created appointment: {a['id']} ({a['status']})")


def _seed_queue(session):
    from datetime import date
    from common.models import Patient as PatientModel
    today = date.today()
    patients = {p["name"]: p for p in DEMO_PATIENTS}
    for q in DEMO_QUEUE:
        existing = session.query(QueueEntry).filter(
            QueueEntry.token == q["token"]).first()
        if existing:
            if existing.added_by == "demo-seed" and existing.date != today:
                existing.date = today
                print(f"  Queue entry {q['token']}: refreshed date to {today}.")
            else:
                print(f"  Queue entry {q['token']} already exists, skipping.")
            continue
        pat = patients.get(q["patient"])
        if not pat:
            continue
        pat_row = session.query(PatientModel).filter(
            PatientModel.organization_id == DEMO_ORG["id"],
            PatientModel.mobile == pat["mobile"]).first()
        if not pat_row:
            continue
        appt = session.query(Appointment).filter(
            Appointment.organization_id == DEMO_ORG["id"],
            Appointment.patient_id == pat_row.id,
            Appointment.doctor_id == q["doctor_id"],
            Appointment.appointment_date == today).first()
        entry = QueueEntry(
            id=f"qe-{q['token']}",
            organization_id=DEMO_ORG["id"],
            branch_id="demo-br-001",
            doctor_id=q["doctor_id"],
            date=today, position=q["position"], token=q["token"],
            patient_id=pat_row.id,
            appointment_id=appt.id if appt else None,
            entry_source=q["entry_source"], status=q["status"],
            status_history=[{"from": "", "to": q["status"],
                             "at": str(datetime.now(timezone.utc))}],
            added_by="demo-seed",
        )
        session.add(entry)
        print(f"  Created queue entry: {q['token']}")


def _seed_patients(session):
    for p in DEMO_PATIENTS:
        mobile = p["mobile"]
        existing = session.query(Patient).filter(
            Patient.organization_id == DEMO_ORG["id"],
            Patient.mobile == mobile,
        ).first()
        if existing:
            print(f"  Patient '{p['name']}' ({mobile}) already exists, skipping.")
            continue
        patient = Patient(
            id=str(uuid.uuid4()),
            organization_id=DEMO_ORG["id"],
            name=p["name"],
            mobile=mobile,
            date_of_birth=p.get("dob") or None,
            age=p.get("age"),
            sex=p["sex"],
        )
        session.add(patient)
        print(f"  Created patient: {p['name']} ({mobile})")


if __name__ == "__main__":
    seed()
    print("\nDemo accounts (passwords come from .env — never from this script):")
    print("  Login URL: http://localhost:3100/")
    for s in DEMO_STAFF:
        print(f"    {s['role']:20s}  {s['username']:16s}")
    print("  Password source: AMSDP_DEMO_PASSWORD_<USERNAME> (see .env.example)")
