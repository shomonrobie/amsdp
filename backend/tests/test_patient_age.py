"""M7-B8 — Patient age & optional DOB tests (real DB, patient service).

Covers: both age+DOB, DOB only, age only, neither; DOB-derived age computation
(boundary months); validation rejections; edit behaviour; no DOB fabrication.
"""
import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "identity"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "patient"))

import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import Organization, Branch, StaffUser, Patient
from identity.models import _SECRET, _ALGO
from patient.main import app, _age_from_dob

ORG_ID = "m7p-org"


def _ensure():
    s = SessionFactory()
    try:
        if not s.query(Organization).filter(Organization.id == ORG_ID).first():
            s.add(Organization(id=ORG_ID, name="M7-P Org", code="M7P-ORG"))
        if not s.query(Branch).filter(Branch.id == "m7p-branch").first():
            s.add(Branch(id="m7p-branch", organization_id=ORG_ID, name="Main", code="M7P-BR"))
        u = s.query(StaffUser).filter(StaffUser.username == "m7p_rec").first()
        if not u:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=ORG_ID,
                          branch_id="m7p-branch", username="m7p_rec", password_hash=pw,
                          display_name="M7-P Receptionist", role="receptionist", status="active")
            s.add(u)
        s.commit()
    finally:
        s.close()


_ensure()

client = TestClient(app)


def _token():
    s = SessionFactory()
    try:
        u = s.query(StaffUser).filter(StaffUser.username == "m7p_rec").first()
    finally:
        s.close()
    return jwt.encode({"sub": u.id, "org": ORG_ID, "branch": "m7p-branch",
        "role": u.role, "exp": int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


def _org_admin_token():
    s = SessionFactory()
    try:
        u = s.query(StaffUser).filter(StaffUser.username == "m7p_rec").first()
        # Create/ensure an org_admin for update operations
        admin = s.query(StaffUser).filter(
            StaffUser.username == "m7p_admin").first()
        if admin is None:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            admin = StaffUser(id=str(uuid.uuid4()), organization_id=ORG_ID,
                              branch_id="m7p-branch", username="m7p_admin",
                              password_hash=pw, display_name="M7-P Org Admin",
                              role="org_admin", status="active")
            s.add(admin)
            s.commit()
    finally:
        s.close()
    return jwt.encode({"sub": admin.id, "org": ORG_ID, "branch": "m7p-branch",
        "role": "org_admin", "exp": int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


TOKEN = _token()
H = {"Authorization": "Bearer " + TOKEN}
H_OA = {"Authorization": "Bearer " + _org_admin_token()}


def _register(mobile, **extra):
    body = {"organization_id": ORG_ID, "name": "Age Test Patient", "mobile": mobile}
    body.update(extra)
    return client.post("/api/v1/patients", headers=H, json=body)


def _uniq_mobile():
    return "0178" + uuid.uuid4().hex[:8]


# --- registration combinations --------------------------------------------

def test_both_age_and_dob():
    dob = "2000-06-15"
    r = _register(_uniq_mobile(), age=45, date_of_birth=dob)
    assert r.status_code == 201
    p = r.json()["patient"]
    assert p["age_source"] == "dob"       # DOB stays authoritative
    assert p["date_of_birth"] == dob
    assert p["age"] == 45                 # reported age still stored raw
    assert p["age_from_dob"] == _age_from_dob(dob)


def test_dob_only():
    dob = "2010-01-01"
    r = _register(_uniq_mobile(), date_of_birth=dob)
    assert r.status_code == 201
    p = r.json()["patient"]
    assert p["age_source"] == "dob"
    assert p["age"] is None
    assert p["age_from_dob"] == _age_from_dob(dob)


def test_age_only():
    r = _register(_uniq_mobile(), age=33)
    assert r.status_code == 201
    p = r.json()["patient"]
    assert p["age_source"] == "reported"
    assert p["age"] == 33
    assert p["age_from_dob"] is None
    # CRITICAL: a DOB must NEVER be fabricated from a reported age
    assert p["date_of_birth"] == ""


def test_neither_provided():
    r = _register(_uniq_mobile())
    assert r.status_code == 201
    p = r.json()["patient"]
    assert p["age_source"] == ""
    assert p["age"] is None and p["age_from_dob"] is None and p["date_of_birth"] == ""


# --- computation correctness -------------------------------------------------

def test_age_from_dob_boundaries():
    today = datetime.now(timezone.utc).date()
    import datetime as _dt
    # exactly 20 years ago today -> 20; birthday tomorrow -> 19
    assert _age_from_dob(today.replace(year=today.year - 20).isoformat(), today) == 20
    tmr = today + _dt.timedelta(days=1)
    assert _age_from_dob(tmr.replace(year=today.year - 20).isoformat(), today) == 19
    yst = today - _dt.timedelta(days=1)
    assert _age_from_dob(yst.replace(year=today.year - 20).isoformat(), today) == 20


def test_age_from_dob_none_for_missing():
    assert _age_from_dob(None) is None
    assert _age_from_dob("") is None
    assert _age_from_dob("not-a-date") is None


# --- validation --------------------------------------------------------------

def test_future_dob_rejected():
    r = _register(_uniq_mobile(), date_of_birth="2999-01-01")
    assert r.status_code == 422


def test_bad_dob_format_rejected():
    r = _register(_uniq_mobile(), date_of_birth="15-06-2000")
    assert r.status_code == 422


def test_age_range_rejected():
    assert _register(_uniq_mobile(), age=200).status_code == 422
    assert _register(_uniq_mobile(), age=-1).status_code == 422

# --- editing ------------------------------------------------------------------

def test_update_adds_age_then_dob_wins():
    mobile = _uniq_mobile()
    pid = _register(mobile, age=40).json()["patient"]["id"]
    # reported first
    r = client.get(f"/api/v1/patients/{pid}", headers=H)
    assert r.json()["age_source"] == "reported"
    # adding a DOB makes it authoritative
    r = client.patch(f"/api/v1/patients/{pid}", headers=H_OA,
                     json={"date_of_birth": "1984-05-05"})
    assert r.status_code == 200
    j = r.json()
    assert j["age_source"] == "dob"
    assert j["age_from_dob"] == _age_from_dob("1984-05-05")
    assert j["age"] == 40  # reported value retained but not authoritative


def test_update_clears_dob_falls_back_to_reported_age():
    mobile = _uniq_mobile()
    pid = _register(mobile, age=52, date_of_birth="1974-03-03").json()["patient"]["id"]
    r = client.patch(f"/api/v1/patients/{pid}", headers=H_OA, json={"date_of_birth": ""})
    assert r.status_code == 200
    j = r.json()
    assert j["age_source"] == "reported"
    assert j["age_from_dob"] is None and j["age"] == 52


def test_privacy_dob_remains_optional_in_listing():
    # ensure the search/list contract carries the new fields
    r = client.get("/api/v1/patients?q=&page=1", headers=H)
    assert r.status_code == 200
    assert all("age_source" in p and "age_from_dob" in p and "age" in p
               for p in r.json()["items"])


def test_existing_patient_back_compat():
    # a patient that predates the field still returns age_source '' (no crash)
    s = SessionFactory()
    try:
        old = Patient(id=str(uuid.uuid4()), organization_id=ORG_ID,
                      name="Legacy Patient", mobile=_uniq_mobile())
        s.add(old); s.commit()
        oid = old.id
    finally:
        s.close()
    r = client.get(f"/api/v1/patients/{oid}", headers=H)
    assert r.status_code == 200
    assert r.json()["age_source"] == ""
    assert r.json()["age"] is None and r.json()["age_from_dob"] is None