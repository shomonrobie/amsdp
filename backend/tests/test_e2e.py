"""Cross-service integration tests — AMSDP MVP end-to-end workflow."""

import sys, os
_test_dir = os.path.dirname(__file__)
_backend_dir = os.path.join(_test_dir, '..')
sys.path.insert(0, _backend_dir)

# Add each service directory so bare imports (from models import …) work
for svc in ('identity', 'organization', 'patient', 'doctor',
            'scheduling', 'appointment', 'queuing', 'audit'):
    sys.path.insert(0, os.path.join(_backend_dir, svc))

import importlib.util as _util

def _import_flat(name, path):
    """Import a module by file path (works with bare sibling imports)."""
    spec = _util.spec_from_file_location(name, path, submodule_search_locations=[])
    mod = _util.module_from_spec(spec)
    # Register under the short name too so sibling imports (import routes) resolve
    sys.modules[name] = mod
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod

# First pass — load just identity (others depend on its db refs)
identity_mod = _import_flat('main', os.path.join(_backend_dir, 'identity', 'main.py'))
identity_mod._name = 'identity'  # mark which service

def _import_service(short_name):
    path = os.path.join(_backend_dir, short_name, 'main.py')
    spec = _util.spec_from_file_location(f'{short_name}_main', path, submodule_search_locations=[])
    mod = _util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod

org_mod     = _import_service('organization')
patient_mod = _import_service('patient')
doctor_mod  = _import_service('doctor')
sched_mod   = _import_service('scheduling')
appt_mod    = _import_service('appointment')
queue_mod   = _import_service('queuing')
audit_mod   = _import_service('audit')

# Restore sys.path to original
sys.path[:] = [p for p in sys.path if p not in [
    os.path.join(_backend_dir, s) for s in
    ('identity', 'organization', 'patient', 'doctor',
     'scheduling', 'appointment', 'queuing', 'audit')]]

from fastapi.testclient import TestClient

ident  = TestClient(identity_mod.app)
org    = TestClient(org_mod.app)
pat    = TestClient(patient_mod.app)
doc    = TestClient(doctor_mod.app)
sched  = TestClient(sched_mod.app)
appt   = TestClient(appt_mod.app)
queue  = TestClient(queue_mod.app)
audit  = TestClient(audit_mod.app)

_users_db = identity_mod._users_db
_orgs_db = org_mod._orgs_db
_branches_db = org_mod._branches_db
_patients_db = patient_mod._patients_db
_doctors_db = doctor_mod._doctors_db
_schedules_db = sched_mod._schedules_db
_appointments_db = appt_mod._appointments_db
_queues_db = queue_mod._queues_db
_next_token = queue_mod._next_token
_audit_db = audit_mod._audit_db

ORG_ID = BRANCH_ID = DOCTOR_ID = PATIENT_ID = STAFF_ID = None
TOKEN = APPT_ID = QUEUE_ID = SCHED_ID = None


def setup_function():
    for db in (_users_db, _orgs_db, _branches_db, _patients_db,
               _doctors_db, _schedules_db, _appointments_db,
               _queues_db, _audit_db):
        if isinstance(db, dict): db.clear()
    _next_token.clear()


class TestWorkflow:
    def test_01_create_org(self):
        global ORG_ID
        r = org.post("/api/v1/orgs", json={"name": "Uposhak Hospital", "code": "UPH-001", "facility_type": "hospital"})
        assert r.status_code == 201; ORG_ID = r.json()["id"]

    def test_02_create_branch(self):
        global BRANCH_ID
        r = org.post("/api/v1/branches", json={"organization_id": ORG_ID, "name": "Uposhak Main", "code": "UPH-MAIN"})
        assert r.status_code == 201; BRANCH_ID = r.json()["id"]

    def test_03_create_doctor(self):
        global DOCTOR_ID
        r = doc.post("/api/v1/doctors", json={"organization_id": ORG_ID, "branch_ids": [BRANCH_ID], "name": "Dr. Rahman", "mobile": "01711111111", "speciality": "Cardiology"})
        assert r.status_code == 201; DOCTOR_ID = r.json()["id"]

    def test_04_create_patient(self):
        global PATIENT_ID
        r = pat.post("/api/v1/patients", json={"organization_id": ORG_ID, "name": "Jamila Begum", "mobile": "01722222222"})
        assert r.status_code == 201; PATIENT_ID = r.json()["patient"]["id"]

    def test_05_create_staff(self):
        global STAFF_ID
        r = ident.post("/api/v1/staff/users", json={"organization_id": ORG_ID, "branch_id": BRANCH_ID, "username": "admin_uph", "password": "pass123", "display_name": "Admin Uposhak", "role": "branch_admin"})
        assert r.status_code == 201; STAFF_ID = r.json()["user_id"]

    def test_06_login(self):
        global TOKEN
        r = ident.post("/api/v1/staff/login", json={"username": "admin_uph", "password": "pass123"})
        assert r.status_code == 200; TOKEN = r.json()["token"]

    def test_07_validate(self):
        r = ident.get("/api/v1/staff/validate", headers={"Authorization": f"Bearer {TOKEN}"})
        assert r.status_code == 200; assert r.json()["organization_id"] == ORG_ID

    def test_08_create_schedule(self):
        global SCHED_ID
        r = sched.post("/api/v1/schedules", json={"doctor_id": DOCTOR_ID, "organization_id": ORG_ID, "branch_id": BRANCH_ID, "slot_templates": [{"day_of_week": 0, "start_time": "09:00", "end_time": "12:00", "slot_duration_minutes": 15, "max_patients": 4}]})
        assert r.status_code == 201; SCHED_ID = r.json()["id"]

    def test_09_available_slots(self):
        r = sched.get(f"/api/v1/schedules/{SCHED_ID}/available-slots", params={"date_str": "2026-04-15"})
        assert r.status_code == 200; assert len(r.json()["slots"]) == 12

    def test_10_create_appointment(self):
        global APPT_ID
        r = appt.post("/api/v1/appointments", json={"organization_id": ORG_ID, "branch_id": BRANCH_ID, "patient_id": PATIENT_ID, "doctor_id": DOCTOR_ID, "appointment_date": "2026-04-15", "start_time": "09:00"})
        assert r.status_code == 201; APPT_ID = r.json()["id"]
        assert r.json()["token_number"].startswith("T-")

    def test_11_enqueue(self):
        global QUEUE_ID
        r = queue.post("/api/v1/queue/enqueue", json={"organization_id": ORG_ID, "branch_id": BRANCH_ID, "doctor_id": DOCTOR_ID, "date": "2026-04-15", "patient_id": PATIENT_ID, "appointment_id": APPT_ID, "entry_source": "appointment"})
        assert r.status_code == 201; QUEUE_ID = r.json()["queue_entry_id"]
        assert r.json()["position"] == 1

    def test_12_queue_lifecycle(self):
        r = queue.patch(f"/api/v1/queue/{QUEUE_ID}", json={"action": "call", "actor": "staff"})
        assert r.status_code == 200; assert r.json()["status"] == "called"
        r = queue.patch(f"/api/v1/queue/{QUEUE_ID}", json={"action": "mark_arrived"})
        assert r.status_code == 200; assert r.json()["status"] == "arrived"
        r = queue.patch(f"/api/v1/queue/{QUEUE_ID}", json={"action": "complete_service"})
        assert r.status_code == 200; assert r.json()["status"] == "served"

    def test_13_audit(self):
        r = audit.post("/api/v1/audit", json={"service": "appointment", "organization_id": ORG_ID, "action": "created", "target_type": "appointment", "target_id": APPT_ID, "actor_id": STAFF_ID, "actor_role": "branch_admin"})
        assert r.status_code == 201
        r = audit.get(f"/api/v1/audit/{APPT_ID}")
        assert len(r.json()) >= 1

    def test_14_permission_positive(self):
        r = ident.post("/api/v1/staff/check-permission", json={"user_id": STAFF_ID, "resource": "patient.create"})
        assert r.json()["authorized"] is True

    def test_15_permission_negative(self):
        r = ident.post("/api/v1/staff/check-permission", json={"user_id": STAFF_ID, "resource": "org.manage"})
        assert r.json()["authorized"] is False
