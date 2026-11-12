"""Tests for Identity & Access Service - Sprint 1 (PostgreSQL-backed)."""

import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from identity.main import app
from identity.permissions import check as perm_check
from identity.models import _SECRET, _ALGO
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import StaffUser, Organization

import jwt
from datetime import datetime, timedelta, timezone
# Ensure test org exists
session = SessionFactory()
try:
    org = session.query(Organization).filter(Organization.code == 'TEST-ORG').first()
    if not org:
        org = Organization(id='org-1', name='Test Org', code='TEST-ORG')
        session.add(org); session.commit()
    TEST_ORG_ID = org.id
finally:
    session.close()

# Create super_admin user for auth
session = SessionFactory()
try:
    au = session.query(StaffUser).filter(StaffUser.username == 'testadmin').first()
    if not au:
        pw_hash = bcrypt.hashpw(b'adminpass', bcrypt.gensalt()).decode()
        au = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
            username='testadmin', password_hash=pw_hash,
            display_name='Test Admin', role='super_admin', status='active')
        session.add(au); session.commit()
    ADMIN_TOKEN = jwt.encode({"sub": au.id, "org": au.organization_id,
        "branch": au.branch_id, "role": au.role,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)
finally:
    session.close()

client = TestClient(app)


def _uniq(name):
    return f"{name}_{uuid.uuid4().hex[:6]}"


def setup_module():
    """Ensure admin user exists for tests that need auth."""
    session = SessionFactory()
    try:
        au = session.query(StaffUser).filter(StaffUser.username == 'testadmin').first()
        if not au:
            pw_hash = bcrypt.hashpw(b'adminpass', bcrypt.gensalt()).decode()
            au = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                username='testadmin', password_hash=pw_hash,
                display_name='Test Admin', role='super_admin', status='active')
            session.add(au); session.commit()
        global ADMIN_TOKEN
        ADMIN_TOKEN = jwt.encode({"sub": au.id, "org": au.organization_id,
            "branch": au.branch_id, "role": au.role,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
    finally:
        session.close()


class TestStaffUserCreation:
    def test_create_user(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("rahim"),
                "password": "secret123", "display_name": "Rahim",
                "role": "receptionist", "locale": "bn"})
        assert r.status_code == 201; assert r.json()["role"] == "receptionist"
    def test_missing_org_rejected(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": "", "username": "noor",
                "password": "x", "display_name": "Noor", "role": "doctor"})
        assert r.status_code == 422
    def test_unknown_role_rejected(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": "badrole",
                "password": "x", "display_name": "Bad", "role": "ceo"})
        assert r.status_code == 422


class TestStaffLogin:
    def setup_method(self):
        global ADMIN_TOKEN
        session = SessionFactory()
        # Upsert testadmin (never delete other users)
        au = session.query(StaffUser).filter(StaffUser.username == 'testadmin').first()
        if not au:
            pw_hash = bcrypt.hashpw(b'adminpass', bcrypt.gensalt()).decode()
            au = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                username='testadmin', password_hash=pw_hash,
                display_name='Test Admin', role='super_admin', status='active')
            session.add(au)
        else:
            au.status = "active"
        session.commit()
        ADMIN_TOKEN = jwt.encode({"sub": au.id, "org": au.organization_id,
            "branch": au.branch_id, "role": au.role,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
        session.close()

    def _create_test_user(self):
        """Create a uniquely-named receptionist; returns its username."""
        username = _uniq("rahim")
        client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": username,
                "password": "secret123", "display_name": "Rahim",
                "role": "receptionist"})
        return username

    def test_login_success(self):
        name = self._create_test_user()
        r = client.post("/api/v1/staff/login",
            json={"username": name, "password": "secret123"})
        assert r.status_code == 200; assert r.json()["token"]
    def test_wrong_password(self):
        name = self._create_test_user()
        r = client.post("/api/v1/staff/login",
            json={"username": name, "password": "wrong"})
        assert r.status_code == 401
    def test_unknown_user(self):
        r = client.post("/api/v1/staff/login",
            json={"username": "nobody", "password": "x"})
        assert r.status_code == 401


class TestValidateToken:
    @classmethod
    def setup_class(cls):
        session = SessionFactory()
        # Upsert testadmin (never delete other users)
        au = session.query(StaffUser).filter(StaffUser.username == 'testadmin').first()
        if not au:
            pw_hash = bcrypt.hashpw(b'adminpass', bcrypt.gensalt()).decode()
            au = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                username='testadmin', password_hash=pw_hash,
                display_name='Test Admin', role='super_admin', status='active')
            session.add(au)
        else:
            au.status = "active"
        session.commit()
        global ADMIN_TOKEN
        ADMIN_TOKEN = jwt.encode({"sub": au.id, "org": au.organization_id,
            "branch": au.branch_id, "role": au.role,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
        session.close()
        # Create a uniquely-named doctor user for token validation; login with it
        cls.doc_user = _uniq("amin")
        client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": cls.doc_user,
                "password": "pass", "display_name": "Amin", "role": "doctor"})
        r = client.post("/api/v1/staff/login",
            json={"username": cls.doc_user, "password": "pass"})
        cls.token = r.json()["token"]

    def test_validate_valid(self):
        r = client.get("/api/v1/staff/validate",
            headers={"Authorization": f"Bearer {self.token}"})
        assert r.status_code == 200; assert r.json()["valid"]
    def test_validate_missing(self):
        r = client.get("/api/v1/staff/validate")
        assert r.status_code == 401


class TestPermissions:
    def test_super_admin_has_the_platform_capabilities(self):
        # Q-1: the platform administrator's grant is an enumerated list, not a
        # wildcard, so it is asserted capability by capability.
        assert perm_check("platform.admin", "super_admin") is True
        assert perm_check("staff.manage", "super_admin") is True
    def test_super_admin_does_not_have_an_unknown_permission(self):
        assert perm_check("anything.at.all", "super_admin") is False
    def test_receptionist_can_create_patient(self):
        assert perm_check("patient.create", "receptionist") is True
    def test_receptionist_cannot_manage_org(self):
        assert perm_check("org.manage", "receptionist") is False
    def test_doctor_cannot_reorder(self):
        assert perm_check("queue.reorder", "doctor") is False
    def test_unknown_denied(self):
        assert perm_check("patient.read", "nobody") is False


class TestDoctorLink:
    """Optional staff<->doctor linkage (M7-B6): same-org validation."""

    @classmethod
    def setup_class(cls):
        session = SessionFactory()
        from common.models import Doctor
        cls.doctor_a = session.query(Doctor).filter(Doctor.id == "m7-doc-a").first()
        if not cls.doctor_a:
            cls.doctor_a = Doctor(id="m7-doc-a", organization_id=TEST_ORG_ID,
                name="Dr Link Test", mobile="01790000001")
            session.add(cls.doctor_a)
        cls.doctor_b = session.query(Doctor).filter(Doctor.id == "m7-doc-b").first()
        if not cls.doctor_b:
            cls.doctor_b = Doctor(id="m7-doc-b", organization_id="other-org-999",
                name="Dr Other Org", mobile="01790000002")
            session.add(cls.doctor_b)
        session.commit()
        session.close()

    def test_create_with_doctor_link(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("doclink"),
                "password": "x", "display_name": "Doc Link", "role": "doctor",
                "doctor_id": "m7-doc-a"})
        assert r.status_code == 201
        uid = r.json().get("user_id")
        assert uid
        # The create response returns user_id; verify the link persisted via GET
        g = client.get(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert g.status_code == 200
        assert g.json().get("doctor_id") == "m7-doc-a"

    def test_link_cross_org_doctor_rejected(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("doclinkbad"),
                "password": "x", "display_name": "Bad Link", "role": "doctor",
                "doctor_id": "m7-doc-b"})
        assert r.status_code == 422

    def test_link_unknown_doctor_rejected(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("doclinknone"),
                "password": "x", "display_name": "No Link", "role": "doctor",
                "doctor_id": "does-not-exist"})
        assert r.status_code == 422

    def test_link_optional(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("nolink"),
                "password": "x", "display_name": "No Link Staff", "role": "receptionist"})
        assert r.status_code == 201
        assert r.json().get("doctor_id") is None