"""AMSDP Demonstration Seed Script - M1/M4, demo dataset refresh.

Idempotent, non-destructive by default. Creates:

- One demo organization with two branches.
- A facility structure per branch: floors, departments, rooms.
- An organization speciality catalogue (Bangla + English names).
- A bilingual, curated symptom catalogue (Bangla + English names and synonyms,
  ~60 common patient-reported symptoms) that the appointment booking form
  searches — see ``seed/symptom_catalogue.py`` for the source and its review
  status.  Nothing in it is a diagnosis.
- Six staff accounts (one per canonical role).
- Ten doctors with BMDC numbers, structured specialities, chamber rooms and
  per-branch assignments.
- Thirty patients with Bangladeshi names, mobile numbers and addresses.
- One schedule per doctor, with weekday slot templates.
- A rolling week of appointments (-3 … +3 days around today, regenerated on
  every run so the demo never shows a stale board) with realistic statuses.
- Today's queue for the two busiest doctors.

Run: python3 backend/seed/seed_demo.py

Reset (development only): python3 backend/seed/seed_demo.py --reset
  Clears operational tables and re-seeds. Requires AMSDP_ALLOW_DESTRUCTIVE_SEED=1
  and refuses to run when AMSDP_ENV=production. The append-only audit trail
  (``audit_events``) is never deleted — see ``.clinerules`` §3 — and because it
  holds a foreign key to ``organizations``/``branches``, an organisation that has
  ever produced an audit record is kept as an audit-only husk. The reset prints
  how many rows it cleared and how many organisations it had to keep.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse, random, uuid, bcrypt
from datetime import date, datetime, timedelta, timezone
from common.database import SessionFactory
from common.models import (
    Organization, Branch, FacilityFloor, FacilityDepartment, FacilityRoom,
    Specialty, StaffUser, Doctor, DoctorBranch, DoctorSpecialty, Patient,
    Schedule, Appointment, QueueEntry, SymptomCatalog,
)
try:
    from seed.symptom_catalogue import DEMO_SYMPTOMS, demo_symptom_rows
except ImportError:                       # script-mode import (python seed_demo.py)
    from symptom_catalogue import DEMO_SYMPTOMS, demo_symptom_rows


DEMO_ORG = {"id": "demo-org-001", "name": "Uposhak Hospital", "code": "UPH-001",
    "timezone": "Asia/Dhaka", "locale": "bn", "facility_type": "hospital",
    "address": "12 Gulshan Avenue, Dhaka 1212"}

DEMO_BRANCHES = [
    {"id": "demo-br-001", "name": "Main Branch", "code": "BR-UPH-001",
     "address": "12 Gulshan Avenue, Dhaka 1212", "phone": "+880-2-5551234"},
    {"id": "demo-br-002", "name": "Gulshan Clinic", "code": "BR-UPH-002",
     "address": "45 Banani Road, Dhaka 1213", "phone": "+880-2-5555678"},
]


# --- Facility structure (AMSDP-FACILITY-DOCTOR-01) ---------------------------
# Real chambers are organised the way a Bangladeshi hospital or diagnostic
# centre actually is: a building with floors, departments spread across those
# floors, and numbered rooms inside them.  A booking snapshots the room, so the
# demo needs the tree to exist before the appointments are created.
DEMO_FLOORS = [
    {"id": "demo-fl-br1-0", "branch_id": "demo-br-001", "name": "Ground Floor",
     "code": "BR1-G", "level": 0,
     "description": "Reception, billing, pharmacy and the emergency bay"},
    {"id": "demo-fl-br1-1", "branch_id": "demo-br-001", "name": "First Floor",
     "code": "BR1-1", "level": 1, "description": "Out-patient consultation chambers"},
    {"id": "demo-fl-br1-2", "branch_id": "demo-br-001", "name": "Second Floor",
     "code": "BR1-2", "level": 2, "description": "Diagnostics, imaging and procedures"},
    {"id": "demo-fl-br2-0", "branch_id": "demo-br-002", "name": "Ground Floor",
     "code": "BR2-G", "level": 0, "description": "Clinic chambers and waiting lounge"},
]

DEMO_DEPARTMENTS = [
    {"id": "demo-dp-br1-card", "branch_id": "demo-br-001", "name": "Cardiology",
     "code": "BR1-CARD", "description": "Out-patient cardiology and ECG"},
    {"id": "demo-dp-br1-med", "branch_id": "demo-br-001", "name": "General Medicine",
     "code": "BR1-MED", "description": "General medicine and diabetes follow-up"},
    {"id": "demo-dp-br1-ped", "branch_id": "demo-br-001", "name": "Pediatrics",
     "code": "BR1-PED", "description": "Child health and immunisation advice"},
    {"id": "demo-dp-br1-ortho", "branch_id": "demo-br-001", "name": "Orthopedics",
     "code": "BR1-ORTHO", "description": "Bone, joint and trauma clinic"},
    {"id": "demo-dp-br1-gyn", "branch_id": "demo-br-001", "name": "Gynecology & Obstetrics",
     "code": "BR1-GYN", "description": "Ante-natal and gynae out-patient"},
    {"id": "demo-dp-br1-diag", "branch_id": "demo-br-001", "name": "Diagnostics",
     "code": "BR1-DIAG", "description": "Pathology, ultrasound and X-ray"},
    {"id": "demo-dp-br2-med", "branch_id": "demo-br-002", "name": "General Medicine",
     "code": "BR2-MED", "description": "Evening general medicine clinic"},
    {"id": "demo-dp-br2-gyn", "branch_id": "demo-br-002", "name": "Gynecology & Obstetrics",
     "code": "BR2-GYN", "description": "Gynae clinic"},
]


DEMO_ROOMS = [
    {"id": "demo-rm-br1-101", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-med", "name": "Chamber 101", "code": "BR1-101",
     "room_type": "consultation", "capacity": 1,
     "description": "General medicine chamber, morning shift"},
    {"id": "demo-rm-br1-102", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-med", "name": "Chamber 102", "code": "BR1-102",
     "room_type": "consultation", "capacity": 1,
     "description": "General medicine chamber, evening shift"},
    {"id": "demo-rm-br1-201", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-card", "name": "Chamber 201", "code": "BR1-201",
     "room_type": "consultation", "capacity": 1,
     "description": "Cardiology chamber with ECG machine"},
    {"id": "demo-rm-br1-202", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-ped", "name": "Chamber 202", "code": "BR1-202",
     "room_type": "consultation", "capacity": 1,
     "description": "Pediatric chamber with a child-friendly waiting area"},
    {"id": "demo-rm-br1-203", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-ortho", "name": "Chamber 203", "code": "BR1-203",
     "room_type": "consultation", "capacity": 1,
     "description": "Orthopedic chamber next to the plaster room"},
    {"id": "demo-rm-br1-204", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-1",
     "department_id": "demo-dp-br1-gyn", "name": "Chamber 204", "code": "BR1-204",
     "room_type": "consultation", "capacity": 1,
     "description": "Gynae and ante-natal chamber"},
    {"id": "demo-rm-br1-301", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-2",
     "department_id": "demo-dp-br1-diag", "name": "Ultrasound Room", "code": "BR1-301",
     "room_type": "diagnostic", "capacity": 1,
     "description": "Ultrasound and colour Doppler"},
    {"id": "demo-rm-br1-302", "branch_id": "demo-br-001", "floor_id": "demo-fl-br1-2",
     "department_id": "demo-dp-br1-diag", "name": "Pathology Lab", "code": "BR1-302",
     "room_type": "diagnostic", "capacity": 3,
     "description": "Sample collection and pathology bench"},
    {"id": "demo-rm-br2-101", "branch_id": "demo-br-002", "floor_id": "demo-fl-br2-0",
     "department_id": "demo-dp-br2-med", "name": "Chamber 101", "code": "BR2-101",
     "room_type": "consultation", "capacity": 1,
     "description": "Evening medicine chamber"},
    {"id": "demo-rm-br2-102", "branch_id": "demo-br-002", "floor_id": "demo-fl-br2-0",
     "department_id": "demo-dp-br2-gyn", "name": "Chamber 102", "code": "BR2-102",
     "room_type": "consultation", "capacity": 1,
     "description": "Gynae chamber"},
]

# --- Speciality catalogue ----------------------------------------------------
# A chamber lists specialities in both scripts: the English name prints on the
# token slip, the Bangla name is what the receptionist reads on screen.
DEMO_SPECIALTIES = [
    {"id": "demo-sp-card", "code": "cardiology", "name_en": "Cardiology",
     "name_bn": "হৃদরোগ", "sort_order": 1},
    {"id": "demo-sp-med", "code": "medicine", "name_en": "General Medicine",
     "name_bn": "মেডিসিন", "sort_order": 2},
    {"id": "demo-sp-ped", "code": "pediatrics", "name_en": "Pediatrics",
     "name_bn": "শিশু স্বাস্থ্য", "sort_order": 3},
    {"id": "demo-sp-ortho", "code": "orthopedics", "name_en": "Orthopedics",
     "name_bn": "অর্থোপেডিকস", "sort_order": 4},
    {"id": "demo-sp-gyn", "code": "gynecology", "name_en": "Gynecology & Obstetrics",
     "name_bn": "গাইনি ও প্রসূতি", "sort_order": 5},
    {"id": "demo-sp-ent", "code": "ent", "name_en": "ENT (Ear, Nose, Throat)",
     "name_bn": "নাক-কান-গলা", "sort_order": 6},
    {"id": "demo-sp-derm", "code": "dermatology", "name_en": "Dermatology",
     "name_bn": "চর্মরোগ", "sort_order": 7},
    {"id": "demo-sp-diag", "code": "diagnostics", "name_en": "Diagnostics",
     "name_bn": "ডায়াগনস্টিকস", "sort_order": 8},
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
     "speciality": "Cardiology", "qualification": "MBBS, MD (Cardiology)",
     "registration_number": "BMDC-A-41235", "bmdc_verification_status": "verified",
     "consultation_fee": 1200.0, "specialty_ids": ["demo-sp-card"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-201"},
    {"id": "demo-dr-002", "name": "Dr. Kamal Hossain", "mobile": "01711111112",
     "speciality": "General Medicine", "qualification": "MBBS, FCPS (Medicine)",
     "registration_number": "BMDC-A-38774", "bmdc_verification_status": "verified",
     "consultation_fee": 800.0, "specialty_ids": ["demo-sp-med"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-101"},
    {"id": "demo-dr-003", "name": "Dr. Shahnaz Rahman", "mobile": "01711111113",
     "speciality": "Pediatrics", "qualification": "MBBS, DCH",
     "registration_number": "BMDC-A-45110", "bmdc_verification_status": "verified",
     "consultation_fee": 700.0, "specialty_ids": ["demo-sp-ped"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-202"},
    {"id": "demo-dr-004", "name": "Dr. Anwar Hossain", "mobile": "01711111114",
     "speciality": "Orthopedics", "qualification": "MBBS, MS (Ortho)",
     "registration_number": "BMDC-A-39902", "bmdc_verification_status": "verified",
     "consultation_fee": 1000.0, "specialty_ids": ["demo-sp-ortho"],
     "branch_id": "demo-br-002", "room_id": "demo-rm-br2-101"},
    {"id": "demo-dr-005", "name": "Dr. Salma Khatun", "mobile": "01711111115",
     "speciality": "Gynecology", "qualification": "MBBS, FCPS (OBGYN)",
     "registration_number": "BMDC-A-42661", "bmdc_verification_status": "verified",
     "consultation_fee": 900.0, "specialty_ids": ["demo-sp-gyn"],
     "branch_id": "demo-br-002", "room_id": "demo-rm-br2-102"},
    {"id": "demo-dr-006", "name": "Dr. Mizanur Rahman", "mobile": "01711111116",
     "speciality": "General Medicine", "qualification": "MBBS, MD (Internal Medicine)",
     "registration_number": "BMDC-A-36448", "bmdc_verification_status": "verified",
     "consultation_fee": 800.0, "specialty_ids": ["demo-sp-med"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-102",
     "extra_branch_ids": ["demo-br-002"]},
    {"id": "demo-dr-007", "name": "Dr. Nasrin Akter", "mobile": "01711111117",
     "speciality": "Dermatology", "qualification": "MBBS, DDV",
     "registration_number": "BMDC-A-47015", "bmdc_verification_status": "verified",
     "consultation_fee": 600.0, "specialty_ids": ["demo-sp-derm"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-204"},
    {"id": "demo-dr-008", "name": "Dr. Rezaul Karim", "mobile": "01711111118",
     "speciality": "ENT", "qualification": "MBBS, MS (ENT)",
     "registration_number": "BMDC-A-40982", "bmdc_verification_status": "verified",
     "consultation_fee": 700.0, "specialty_ids": ["demo-sp-ent"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-203"},
    {"id": "demo-dr-009", "name": "Dr. Sabrina Chowdhury", "mobile": "01711111119",
     "speciality": "Gynecology", "qualification": "MBBS, FCPS (OBGYN)",
     "registration_number": "BMDC-A-48321", "bmdc_verification_status": "verified",
     "consultation_fee": 900.0, "specialty_ids": ["demo-sp-gyn"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-204"},
    {"id": "demo-dr-010", "name": "Dr. Tanvir Ahmed", "mobile": "01711111120",
     "speciality": "Cardiology", "qualification": "MBBS, D-Card",
     "registration_number": "BMDC-A-43760", "bmdc_verification_status": "pending_verification",
     "consultation_fee": 1000.0, "specialty_ids": ["demo-sp-card"],
     "branch_id": "demo-br-001", "room_id": "demo-rm-br1-201"},
]


DEMO_PATIENTS = [
    {"name": "Md. Abdul Karim", "mobile": "01811220001", "sex": "male", "dob": "1980-04-12", "age": None,
     "address": "House 14, Road 5, Dhanmondi, Dhaka"},
    {"name": "Jamila Begum", "mobile": "01811220002", "sex": "female", "dob": None, "age": 34,
     "address": "Mirpur Section 10, Dhaka"},
    {"name": "Rafiq Hasan", "mobile": "01811220003", "sex": "male", "dob": None, "age": None,
     "address": "Kazipara, Mirpur, Dhaka"},
    {"name": "Nusrat Jahan", "mobile": "01811220004", "sex": "female", "dob": "1995-11-03", "age": None,
     "address": "Uttara Sector 7, Dhaka"},
    {"name": "Shahidul Islam", "mobile": "01811220005", "sex": "male", "dob": None, "age": 61,
     "address": "Sadar Road, Barishal"},
    {"name": "Rokeya Sultana", "mobile": "01811220006", "sex": "female", "dob": None, "age": 42,
     "address": "Kandirpar, Comilla"},
    {"name": "Tariqul Islam", "mobile": "01811220007", "sex": "male", "dob": None, "age": None,
     "address": "GEC Circle, Chattogram"},
    {"name": "Farhana Akter", "mobile": "01811220008", "sex": "female", "dob": "2001-02-20", "age": None,
     "address": "Bashundhara R/A, Dhaka"},
    {"name": "Mizanur Rahman", "mobile": "01811220009", "sex": "male", "dob": None, "age": 48,
     "address": "Zindabazar, Sylhet"},
    {"name": "Ayesha Siddiqua", "mobile": "01811220010", "sex": "female", "dob": None, "age": 7,
     "address": "Shantinagar, Dhaka"},
    {"name": "Abdul Mannan", "mobile": "01811220011", "sex": "male", "dob": "1958-06-30", "age": None,
     "address": "Station Road, Jessore"},
    {"name": "Shirin Sultana", "mobile": "01811220012", "sex": "female", "dob": None, "age": 29,
     "address": "Mohakhali DOHS, Dhaka"},
    {"name": "Habibur Rahman", "mobile": "01811220013", "sex": "male", "dob": None, "age": 55,
     "address": "College Road, Rajshahi"},
    {"name": "Mahmuda Khatun", "mobile": "01811220014", "sex": "female", "dob": None, "age": 63,
     "address": "Kakrail, Dhaka"},
    {"name": "Sujon Mia", "mobile": "01811220015", "sex": "male", "dob": "1990-01-18", "age": None,
     "address": "Badda Link Road, Dhaka"},
    {"name": "Parvin Akter", "mobile": "01811220016", "sex": "female", "dob": None, "age": 38,
     "address": "Savar Bazar, Dhaka"},
    {"name": "Kamrul Hasan", "mobile": "01811220017", "sex": "male", "dob": None, "age": 44,
     "address": "Court Road, Mymensingh"},
    {"name": "Ruma Islam", "mobile": "01811220018", "sex": "female", "dob": None, "age": 26,
     "address": "Agrabad, Chattogram"},
    {"name": "Nazrul Islam", "mobile": "01811220019", "sex": "male", "dob": None, "age": 70,
     "address": "Harunabad, Kushtia"},
    {"name": "Taslima Begum", "mobile": "01811220020", "sex": "female", "dob": "1987-09-09", "age": None,
     "address": "Naogaon Sadar, Naogaon"},
    {"name": "Shafiqul Alam", "mobile": "01811220021", "sex": "male", "dob": None, "age": 51,
     "address": "Pahartali, Chattogram"},
    {"name": "Dilara Yeasmin", "mobile": "01811220022", "sex": "female", "dob": None, "age": 33,
     "address": "Brahmanbaria Sadar"},
    {"name": "Enamul Haque", "mobile": "01811220023", "sex": "male", "dob": None, "age": 47,
     "address": "Gulshan 1, Dhaka"},
    {"name": "Sultana Razia", "mobile": "01811220024", "sex": "female", "dob": None, "age": 58,
     "address": "Daudkandi, Comilla"},
    {"name": "Monir Hossain", "mobile": "01811220025", "sex": "male", "dob": "1975-12-01", "age": None,
     "address": "Khalishpur, Khulna"},
    {"name": "Rina Akter", "mobile": "01811220026", "sex": "female", "dob": None, "age": 21,
     "address": "Tejgaon Industrial Area, Dhaka"},
    {"name": "Borhan Uddin", "mobile": "01811220027", "sex": "male", "dob": None, "age": 39,
     "address": "Shibganj, Bogura"},
    {"name": "Nargis Parvin", "mobile": "01811220028", "sex": "female", "dob": None, "age": 45,
     "address": "Madhabdi, Narsingdi"},
    {"name": "Sirajul Haque", "mobile": "01811220029", "sex": "male", "dob": None, "age": 66,
     "address": "Rangpur Sadar"},
    {"name": "Momena Begum", "mobile": "01811220030", "sex": "female", "dob": None, "age": 74,
     "address": "Kotwali, Old Dhaka"},
]


# --- Schedules ---------------------------------------------------------------
# Weekday clinics only: Friday is the weekly holiday in Bangladesh and Saturday
# is a half day, so no chamber publishes slots then.  The generator below still
# creates a few off-template phone bookings on those days, because that is
# exactly what a real reception desk does.
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
         {"day_of_week": 3, "start_time": "09:00", "end_time": "13:00",
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
    {"doctor_id": "demo-dr-006", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 6, "start_time": "17:00", "end_time": "21:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 1, "start_time": "09:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 2, "start_time": "17:00", "end_time": "21:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-007", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 1, "start_time": "10:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 2, "start_time": "10:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-008", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 6, "start_time": "10:00", "end_time": "13:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 3, "start_time": "16:00", "end_time": "20:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
    {"doctor_id": "demo-dr-009", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 0, "start_time": "15:00", "end_time": "19:00",
          "slot_duration_minutes": 15, "max_patients": 3},
         {"day_of_week": 2, "start_time": "15:00", "end_time": "19:00",
          "slot_duration_minutes": 15, "max_patients": 3},
     ]},
    {"doctor_id": "demo-dr-010", "branch_id": "demo-br-001",
     "appointment_model": "time_slot",
     "slot_templates": [
         {"day_of_week": 1, "start_time": "09:00", "end_time": "12:00",
          "slot_duration_minutes": 15, "max_patients": 4},
         {"day_of_week": 3, "start_time": "09:00", "end_time": "12:00",
          "slot_duration_minutes": 15, "max_patients": 4},
     ]},
]


# --- Appointment plan --------------------------------------------------------
# A chamber's board is a *week*, not a single day: yesterday's completed visits,
# today's live queue and the rest of the week's confirmed bookings.  The plan is
# generated from the templates above on every run, from a fixed seed, so the
# demo shows a realistic board whatever day it is run on — and never a stale one.
DEMO_DAY_PROFILES = [
    (-3, ["COMPLETED", "COMPLETED", "COMPLETED", "NO_SHOW", "COMPLETED", "CANCELLED"]),
    (-2, ["COMPLETED", "COMPLETED", "CANCELLED", "COMPLETED", "NO_SHOW"]),
    (-1, ["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "NO_SHOW", "CANCELLED"]),
    (0, ["COMPLETED", "IN_CONSULTATION", "CHECKED_IN", "IN_QUEUE", "CONFIRMED",
         "CONFIRMED", "BOOKED", "AWAITING_CONFIRMATION", "CANCELLED"]),
    (1, ["CONFIRMED", "CONFIRMED", "BOOKED", "BOOKED", "AWAITING_CONFIRMATION"]),
    (2, ["CONFIRMED", "BOOKED", "BOOKED", "AWAITING_CONFIRMATION"]),
    (3, ["BOOKED", "BOOKED", "CONFIRMED"]),
]

#: Booking channel per status — reception books face to face, the portal and the
#: phone leave different traces in the log.
DEMO_SOURCE_BY_STATUS = {
    "COMPLETED": "reception", "NO_SHOW": "reception", "CANCELLED": "phone",
    "CHECKED_IN": "reception", "IN_CONSULTATION": "reception",
    "IN_QUEUE": "reception", "CONFIRMED": "phone", "BOOKED": "portal",
    "AWAITING_CONFIRMATION": "portal",
}

#: Used when a date has no published template (weekend phone bookings, which the
#: appointment API also accepts at capacity 1 — see the calendar's "O-R" note).
OFF_TEMPLATE_TIMES = ["10:00", "10:30", "11:00", "11:30", "12:00", "16:00", "16:30"]


def _minutes(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def _slot_times(doctor_id, day):
    """Published slot start times for one doctor on one date (possibly empty)."""
    entry = next((t for t in DEMO_SCHEDULE_TEMPLATES if t["doctor_id"] == doctor_id), None)
    if not entry:
        return []
    times = []
    for template in entry["slot_templates"]:
        if template["day_of_week"] != day.weekday():
            continue
        step = template["slot_duration_minutes"]
        for minute in range(_minutes(template["start_time"]), _minutes(template["end_time"]), step):
            times.append(f"{minute // 60:02d}:{minute % 60:02d}")
    return times


def _doctor_room(doctor_id):
    return next(d["room_id"] for d in DEMO_DOCTORS if d["id"] == doctor_id)


def _slot_capacity(doctor_id, day):
    for template in next(
            (t["slot_templates"] for t in DEMO_SCHEDULE_TEMPLATES
             if t["doctor_id"] == doctor_id), []):
        if template["day_of_week"] == day.weekday():
            return template.get("max_patients", 4)
    return 1

def plan_appointments(today):
    """Build the demo week: one dict per appointment, deterministic for a date."""
    rng = random.Random(20261116)
    room_index = {r["id"]: r for r in DEMO_ROOMS}
    floor_index = {f["id"]: f for f in DEMO_FLOORS}
    dept_index = {d["id"]: d for d in DEMO_DEPARTMENTS}
    doctors = [d["id"] for d in DEMO_DOCTORS]
    patients = [p["mobile"] for p in DEMO_PATIENTS]
    plan = []
    patient_cursor = 0

    for offset, statuses in DEMO_DAY_PROFILES:
        day = today + timedelta(days=offset)
        # (doctor_id, start_time) -> bookings placed, so no slot exceeds the
        # template's max_patients.
        used = {}
        for index, status in enumerate(statuses):
            for doctor_id in rng.sample(doctors, len(doctors)):
                capacity = _slot_capacity(doctor_id, day)
                for slot in (_slot_times(doctor_id, day) or OFF_TEMPLATE_TIMES):
                    key = (doctor_id, slot)
                    if used.get(key, 0) >= capacity:
                        continue
                    used[key] = used.get(key, 0) + 1
                    room = room_index[_doctor_room(doctor_id)]
                    plan.append({
                        "id": f"demo-appt-{day.isoformat()}-{index:02d}",
                        "date": day,
                        "doctor_id": doctor_id,
                        "branch_id": room["branch_id"],
                        "start_time": slot,
                        "status": status,
                        "booking_source": DEMO_SOURCE_BY_STATUS.get(status, "reception"),
                        "appointment_type": "scheduled",
                        "patient_mobile": patients[patient_cursor % len(patients)],
                        "room_id": room["id"],
                        "room_name": room["name"],
                        "floor_id": room["floor_id"],
                        "floor_name": floor_index[room["floor_id"]]["name"],
                        "department_id": room["department_id"],
                        "department_name": dept_index[room["department_id"]]["name"],
                    })
                    patient_cursor += 1
                    break
                else:
                    continue
                break
    return plan


# Today's live queue: what the doctor persona should see on login — a patient in
# the chair, two waiting, one finished, plus one walk-in that never booked.
DEMO_QUEUE_PLAN = [
    {"token": "T-DR002-001", "doctor_id": "demo-dr-002", "position": 1,
     "status": "waiting", "entry_source": "appointment", "patient_mobile": "01811220002"},
    {"token": "T-DR002-002", "doctor_id": "demo-dr-002", "position": 2,
     "status": "in_consultation", "entry_source": "appointment", "patient_mobile": "01811220009"},
    {"token": "T-DR002-003", "doctor_id": "demo-dr-002", "position": 3,
     "status": "waiting", "entry_source": "walk_in", "patient_mobile": "01811220012"},
    {"token": "T-DR002-004", "doctor_id": "demo-dr-002", "position": 4,
     "status": "completed", "entry_source": "appointment", "patient_mobile": "01811220006"},
    {"token": "T-DR001-001", "doctor_id": "demo-dr-001", "position": 1,
     "status": "waiting", "entry_source": "appointment", "patient_mobile": "01811220001"},
    {"token": "T-DR001-002", "doctor_id": "demo-dr-001", "position": 2,
     "status": "completed", "entry_source": "appointment", "patient_mobile": "01811220005"},
    # A third chamber with a live queue, so whichever doctor a demo user picks
    # first already has work on screen instead of an empty board.
    {"token": "T-DR004-001", "doctor_id": "demo-dr-004", "position": 1,
     "status": "in_consultation", "entry_source": "appointment", "patient_mobile": "01811220003"},
    {"token": "T-DR004-002", "doctor_id": "demo-dr-004", "position": 2,
     "status": "waiting", "entry_source": "walk_in", "patient_mobile": "01811220011"},
]



def seed():
    session = SessionFactory()
    try:
        _seed_org(session)
        _seed_branch(session)
        _seed_floors(session)
        _seed_departments(session)
        _seed_rooms(session)
        _seed_specialties(session)
        # AMSDP-SYMPTOM-01 — the bilingual catalogue the booking form searches.
        _seed_symptoms(session)
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


def _doctor_columns(d):
    """Only real ``doctors`` columns — the rest of the dict is seeding metadata."""
    meta = {"specialty_ids", "branch_id", "extra_branch_ids", "room_id"}
    return {k: v for k, v in d.items() if k not in meta}


def _seed_doctors(session):
    for d in DEMO_DOCTORS:
        existing = session.query(Doctor).filter(Doctor.id == d["id"]).first()
        if existing:
            print(f"  Doctor '{d['name']}' already exists, skipping.")
        else:
            session.add(Doctor(organization_id=DEMO_ORG["id"], **_doctor_columns(d)))
            print(f"  Created doctor: {d['name']}")

        for specialty_id in d.get("specialty_ids", []):
            link = session.query(DoctorSpecialty).filter(
                DoctorSpecialty.doctor_id == d["id"],
                DoctorSpecialty.specialty_id == specialty_id).first()
            if not link:
                session.add(DoctorSpecialty(doctor_id=d["id"], specialty_id=specialty_id))

        # Exactly one primary branch per doctor (a partial unique index enforces
        # it), plus any additional chambers they sit at.
        assignments = [(d["branch_id"], True)]
        assignments += [(b, False) for b in d.get("extra_branch_ids", [])]
        for branch_id, is_primary in assignments:
            existing_ab = session.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == d["id"],
                DoctorBranch.branch_id == branch_id).first()
            if existing_ab:
                continue
            session.add(DoctorBranch(
                doctor_id=d["id"], branch_id=branch_id,
                room_id=d.get("room_id") if is_primary else None,
                is_primary=is_primary, status="active"))



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
    """Seed the generated week.  Stale demo rows from an earlier run (different
    dates) are removed first, so re-running never stacks two weeks of boards."""
    today = date.today()
    plan = plan_appointments(today)

    wanted_ids = {a["id"] for a in plan}
    stale = session.query(Appointment).filter(
        Appointment.organization_id == DEMO_ORG["id"],
        Appointment.created_by == "demo-seed").all()
    for row in stale:
        if row.id not in wanted_ids:
            session.delete(row)
            print(f"  Appointment {row.id}: stale demo row removed.")

    serial_by_doctor_day = {}
    for a in plan:
        if session.query(Appointment).filter(Appointment.id == a["id"]).first():
            print(f"  Appointment {a['id']} already exists, skipping.")
            continue
        pat_row = session.query(Patient).filter(
            Patient.organization_id == DEMO_ORG["id"],
            Patient.mobile == a["patient_mobile"]).first()
        if not pat_row:
            print(f"  Appointment {a['id']}: patient row missing, skipping.")
            continue
        serial_key = (a["doctor_id"], a["date"])
        serial = serial_by_doctor_day.get(serial_key, 0) + 1
        serial_by_doctor_day[serial_key] = serial
        session.add(Appointment(
            id=a["id"], organization_id=DEMO_ORG["id"], branch_id=a["branch_id"],
            patient_id=pat_row.id, doctor_id=a["doctor_id"],
            appointment_date=a["date"], start_time=a["start_time"],
            serial_number=serial, appointment_type=a["appointment_type"],
            booking_source=a["booking_source"], status=a["status"],
            status_history=[{"from": "", "to": a["status"],
                             "at": str(datetime.now(timezone.utc))}],
            token_number=f"T-{a['doctor_id'][-3:].upper()}-{serial:03d}",
            notes="",
            room_id=a["room_id"], room_name=a["room_name"],
            floor_id=a["floor_id"], floor_name=a["floor_name"],
            department_id=a["department_id"], department_name=a["department_name"],
            created_by="demo-seed",
        ))
        print(f"  Created appointment: {a['id']} ({a['status']} {a['start_time']})")


def _seed_queue(session):
    today = date.today()
    for q in DEMO_QUEUE_PLAN:
        existing = session.query(QueueEntry).filter(
            QueueEntry.token == q["token"]).first()
        if existing:
            if existing.added_by == "demo-seed" and existing.date != today:
                existing.date = today
                print(f"  Queue entry {q['token']}: refreshed date to {today}.")
            else:
                print(f"  Queue entry {q['token']} already exists, skipping.")
            continue
        pat_row = session.query(Patient).filter(
            Patient.organization_id == DEMO_ORG["id"],
            Patient.mobile == q["patient_mobile"]).first()
        if not pat_row:
            print(f"  Queue entry {q['token']}: patient row missing, skipping.")
            continue
        appt = session.query(Appointment).filter(
            Appointment.organization_id == DEMO_ORG["id"],
            Appointment.patient_id == pat_row.id,
            Appointment.doctor_id == q["doctor_id"],
            Appointment.appointment_date == today).first()
        branch_id = next((d["branch_id"] for d in DEMO_DOCTORS
                          if d["id"] == q["doctor_id"]), DEMO_BRANCHES[0]["id"])
        session.add(QueueEntry(
            id=f"qe-{q['token']}",
            organization_id=DEMO_ORG["id"],
            branch_id=branch_id,
            doctor_id=q["doctor_id"],
            date=today, position=q["position"], token=q["token"],
            patient_id=pat_row.id,
            appointment_id=appt.id if appt else None,
            entry_source=q["entry_source"], status=q["status"],
            status_history=[{"from": "", "to": q["status"],
                             "at": str(datetime.now(timezone.utc))}],
            position_history=[{"position": q["position"],
                               "at": str(datetime.now(timezone.utc))}],
            added_by="demo-seed",
        ))
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
            address=p.get("address") or None,
        )
        session.add(patient)
        print(f"  Created patient: {p['name']} ({mobile})")


def _seed_floors(session):
    for f in DEMO_FLOORS:
        if session.query(FacilityFloor).filter(FacilityFloor.id == f["id"]).first():
            print(f"  Floor '{f['name']}' already exists, skipping.")
            continue
        session.add(FacilityFloor(organization_id=DEMO_ORG["id"], status="active", **f))
        print(f"  Created floor: {f['code']} — {f['name']}")


def _seed_departments(session):
    for d in DEMO_DEPARTMENTS:
        if session.query(FacilityDepartment).filter(FacilityDepartment.id == d["id"]).first():
            print(f"  Department '{d['name']}' already exists, skipping.")
            continue
        session.add(FacilityDepartment(organization_id=DEMO_ORG["id"], status="active", **d))
        print(f"  Created department: {d['code']} — {d['name']}")


def _seed_rooms(session):
    for r in DEMO_ROOMS:
        if session.query(FacilityRoom).filter(FacilityRoom.id == r["id"]).first():
            print(f"  Room '{r['name']}' already exists, skipping.")
            continue
        session.add(FacilityRoom(organization_id=DEMO_ORG["id"], status="active", **r))
        print(f"  Created room: {r['code']} — {r['name']}")


def _seed_specialties(session):
    for s in DEMO_SPECIALTIES:
        existing = session.query(Specialty).filter(
            Specialty.organization_id == DEMO_ORG["id"],
            Specialty.code == s["code"]).first()
        if existing:
            print(f"  Speciality '{s['code']}' already exists, skipping.")
            continue
        session.add(Specialty(organization_id=DEMO_ORG["id"], status="active", **s))
        print(f"  Created speciality: {s['name_en']} / {s['name_bn']}")


def _seed_symptoms(session):
    """Seed the bilingual symptom catalogue (AMSDP-SYMPTOM-01).

    Upsert by ``(organization, code)``: a re-run refreshes the wording of an
    existing entry instead of duplicating it, so editing ``symptom_catalogue.py``
    and re-running the seed is the supported way to change the demo wording.
    Nothing here is clinical advice — see the module docstring of
    ``seed/symptom_catalogue.py`` for the source and review status rules.
    """
    created = 0
    for row in demo_symptom_rows(DEMO_ORG["id"]):
        existing = session.query(SymptomCatalog).filter(
            SymptomCatalog.organization_id == DEMO_ORG["id"],
            SymptomCatalog.code == row["code"]).first()
        if existing:
            existing.name_en = row["name_en"]
            existing.name_bn = row["name_bn"]
            existing.synonyms_en = row["synonyms_en"]
            existing.synonyms_bn = row["synonyms_bn"]
            existing.category = row["category"]
            existing.specialty_hints = row["specialty_hints"]
            existing.sort_order = row["sort_order"]
            existing.source = row["source"]
            existing.review_status = row["review_status"]
            continue
        session.add(SymptomCatalog(**row))
        created += 1
    print(f"  Symptom catalogue: {created} created, "
          f"{len(DEMO_SYMPTOMS)} in the curated list")


#: Tables cleared by ``--reset``, children first.  ``audit_events`` and
#: ``alembic_version`` are deliberately absent: the audit trail is append-only
#: (``.clinerules`` §3) and the migration head must survive the reset.
RESET_ORDER = [
    "notifications", "tracking_tokens", "queue_sequences", "queue_entries",
    # Recorded symptoms are children of the appointment (AMSDP-SYMPTOM-01).
    "appointment_symptoms", "appointments",
    "schedule_sessions", "schedules", "doctor_specialties",
    "doctor_branches", "login_attempts", "patients", "staff_users", "doctors",
    "facility_rooms", "facility_departments", "facility_floors",
    "specialties", "symptom_catalog",
]

#: ``audit_events`` holds a NO ACTION foreign key to ``organizations`` and
#: ``branches``, and the trail is append-only.  Those two tables therefore can
#: only be cleared for rows the trail does not mention: an organisation that has
#: ever produced an audit record stays in the database as an audit-only husk, and
#: the reset reports how many it had to keep.
AUDIT_GUARDED = [
    ("branches", "branch_id"),
    ("organizations", "organization_id"),
]


def reset(session):
    """Delete operational rows so the seed starts from an empty database."""
    from sqlalchemy import text
    if os.environ.get("AMSDP_ENV", "").lower() == "production":
        sys.exit("ERROR: --reset refuses to run with AMSDP_ENV=production.")
    if os.environ.get("AMSDP_ALLOW_DESTRUCTIVE_SEED") != "1":
        sys.exit(
            "ERROR: --reset deletes every operational row in the target database.\n"
            "       Re-run with AMSDP_ALLOW_DESTRUCTIVE_SEED=1 to confirm.\n"
            "       The append-only audit trail (audit_events) is never touched."
        )
    for table in RESET_ORDER:
        deleted = session.execute(text(f"DELETE FROM {table}")).rowcount
        print(f"  Cleared {table}: {deleted} row(s)")
    for table, column in AUDIT_GUARDED:
        deleted = session.execute(text(
            f"DELETE FROM {table} t WHERE NOT EXISTS ("
            f"SELECT 1 FROM audit_events a WHERE a.{column} = t.id)")).rowcount
        kept = session.execute(text(
            f"SELECT count(*) FROM {table}")).scalar()
        print(f"  Cleared {table}: {deleted} row(s); kept {kept} with audit history")
    session.commit()
    print("Reset complete (audit_events preserved).")



def main(argv=None):
    parser = argparse.ArgumentParser(description="Seed the AMSDP demo dataset.")
    parser.add_argument("--reset", action="store_true",
                        help="delete existing operational data first (development only)")
    args = parser.parse_args(argv)

    if args.reset:
        session = SessionFactory()
        try:
            reset(session)
        finally:
            session.close()

    seed()

    print("\nDemo accounts (passwords come from .env — never from this script):")
    print("  Login URL: http://localhost:3100/")
    for s in DEMO_STAFF:
        print(f"    {s['role']:20s}  {s['username']:16s}")
    print("  Password source: AMSDP_DEMO_PASSWORD_<USERNAME> (see .env.example)")


if __name__ == "__main__":
    main()

