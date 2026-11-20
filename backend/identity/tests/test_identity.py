"""Tests for Identity & Access Service - Sprint 1 (PostgreSQL-backed)."""

import sys, os, uuid, bcrypt
import concurrent.futures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from identity.main import app
from identity.permissions import check as perm_check
from identity.models import _SECRET, _ALGO
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import StaffUser, Organization, Doctor
from common.auth import _load_assigned_doctor_ids

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


class TestSelfEscalation:
    """PO-RBAC-03: Users cannot grant themselves or others higher roles."""

    def _mk_token(self, role, org_id=TEST_ORG_ID, branch_id=None):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                branch_id=branch_id, username=f"esc_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Esc Test", role=role,
                status="active")
            session.add(u); session.commit()
            uid = u.id
        finally:
            session.close()
        return jwt.encode({"sub": uid, "org": org_id, "branch": branch_id,
                           "role": role,
                           "exp": int((datetime.now(timezone.utc)
                                       + timedelta(hours=1)).timestamp())},
                          _SECRET, algorithm=_ALGO)

    def test_receptionist_cannot_create_org_admin(self):
        tok = self._mk_token("receptionist")
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {tok}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("esc1"),
                "password": "x", "display_name": "Escalator", "role": "org_admin"})
        assert r.status_code == 403, r.text

    def test_receptionist_cannot_create_super_admin(self):
        tok = self._mk_token("receptionist")
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {tok}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("esc2"),
                "password": "x", "display_name": "Escalator", "role": "super_admin"})
        assert r.status_code == 403, r.text

    def test_branch_admin_cannot_create_org_admin(self):
        tok = self._mk_token("branch_admin")
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {tok}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("esc3"),
                "password": "x", "display_name": "Escalator", "role": "org_admin"})
        assert r.status_code == 403, r.text

    def test_org_admin_can_create_branch_admin(self):
        tok = self._mk_token("org_admin")
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {tok}"},
            json={"organization_id": TEST_ORG_ID, "username": _uniq("esc4"),
                "password": "x", "display_name": "Escalator", "role": "branch_admin"})
        assert r.status_code == 201, r.text

    def test_super_admin_can_create_any_role(self):
        for role in ["assistant", "doctor", "receptionist", "branch_admin",
                     "org_admin", "super_admin"]:
            r = client.post("/api/v1/staff/users",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
                json={"organization_id": TEST_ORG_ID,
                      "username": _uniq("esc5"), "password": "x",
                      "display_name": "Escalator", "role": role})
            assert r.status_code == 201, f"{role}: {r.text}"

    def test_user_cannot_update_own_role_higher(self):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"esc_own_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Own Escalator",
                role="receptionist", status="active")
            session.add(u); session.commit()
            uid = u.id
        finally:
            session.close()
        tok = jwt.encode({"sub": uid, "org": TEST_ORG_ID, "branch": None,
                          "role": "receptionist",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "org_admin"})
        assert r.status_code == 403, r.text

    def test_user_cannot_update_own_role_to_super_admin(self):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"esc_own2_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Own Escalator 2",
                role="receptionist", status="active")
            session.add(u); session.commit()
            uid = u.id
        finally:
            session.close()
        tok = jwt.encode({"sub": uid, "org": TEST_ORG_ID, "branch": None,
                          "role": "receptionist",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "super_admin"})
        assert r.status_code == 403, r.text

    def test_org_admin_cannot_update_own_role_to_super_admin(self):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"esc_own3_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Own Escalator 3",
                role="org_admin", status="active")
            session.add(u); session.commit()
            uid = u.id
        finally:
            session.close()
        tok = jwt.encode({"sub": uid, "org": TEST_ORG_ID, "branch": None,
                          "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "super_admin"})
        assert r.status_code == 403, r.text

    def test_can_grant_role_function(self):
        from identity.permissions import can_grant_role, role_level
        assert can_grant_role("super_admin", "super_admin") is True
        assert can_grant_role("super_admin", "org_admin") is True
        assert can_grant_role("org_admin", "branch_admin") is True
        assert can_grant_role("org_admin", "org_admin") is False
        assert can_grant_role("org_admin", "super_admin") is False
        assert can_grant_role("receptionist", "org_admin") is False
        assert can_grant_role("receptionist", "receptionist") is False
        assert role_level("assistant") == 1
        assert role_level("super_admin") == 6
        assert role_level("unknown_role") == 0


class TestLastOrgAdmin:
    """PO-RBAC-04: Protect the last active Organization Admin."""

    def _mk_org(self, tag):
        session = SessionFactory()
        try:
            org_id = f"last_org_{tag}"
            org = session.query(Organization).filter(Organization.id == org_id).first()
            if org is None:
                org = Organization(id=org_id, name=f"Last Org {tag}",
                                   code=f"LAST{tag.upper()}")
                session.add(org)
                session.commit()
            return org_id
        finally:
            session.close()

    def _mk_org_admin_token(self, org_id):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                branch_id=None, username=f"last_oa_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Last OA",
                role="org_admin", status="active")
            session.add(u); session.commit()
            uid = u.id
        finally:
            session.close()
        return jwt.encode({"sub": uid, "org": org_id, "branch": None,
                           "role": "org_admin",
                           "exp": int((datetime.now(timezone.utc)
                                       + timedelta(hours=1)).timestamp())},
                          _SECRET, algorithm=_ALGO)

    def _mk_second_org_admin(self, org_id):
        session = SessionFactory()
        try:
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                branch_id=None, username=f"last_oa2_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Second OA",
                role="org_admin", status="active")
            session.add(u); session.commit()
            return u.id
        finally:
            session.close()

    def test_cannot_remove_only_org_admin(self):
        tag = uuid.uuid4().hex[:6]
        org_id = self._mk_org(tag)
        tok = self._mk_org_admin_token(org_id)
        import jwt as _jwt
        payload = _jwt.decode(tok, _SECRET, algorithms=[_ALGO])
        uid = payload["sub"]
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "receptionist"})
        assert r.status_code == 403, r.text

    def test_cannot_deactivate_only_org_admin(self):
        tag = uuid.uuid4().hex[:6]
        org_id = self._mk_org(tag)
        tok = self._mk_org_admin_token(org_id)
        import jwt as _jwt
        payload = _jwt.decode(tok, _SECRET, algorithms=[_ALGO])
        uid = payload["sub"]
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"status": "inactive"})
        assert r.status_code == 403, r.text

    def test_can_remove_one_org_admin_when_another_remains(self):
        tag = uuid.uuid4().hex[:6]
        org_id = self._mk_org(tag)
        tok = self._mk_org_admin_token(org_id)
        self._mk_second_org_admin(org_id)
        import jwt as _jwt
        payload = _jwt.decode(tok, _SECRET, algorithms=[_ALGO])
        uid = payload["sub"]
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "receptionist"})
        assert r.status_code == 200, r.text
        session = SessionFactory()
        try:
            remaining = session.query(StaffUser).filter(
                StaffUser.organization_id == org_id,
                StaffUser.role == "org_admin",
                StaffUser.status == "active",
            ).count()
            assert remaining == 1
        finally:
            session.close()

    def test_can_deactivate_one_org_admin_when_another_remains(self):
        tag = uuid.uuid4().hex[:6]
        org_id = self._mk_org(tag)
        tok = self._mk_org_admin_token(org_id)
        self._mk_second_org_admin(org_id)
        import jwt as _jwt
        payload = _jwt.decode(tok, _SECRET, algorithms=[_ALGO])
        uid = payload["sub"]
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"status": "inactive"})
        assert r.status_code == 200, r.text
        session = SessionFactory()
        try:
            remaining = session.query(StaffUser).filter(
                StaffUser.organization_id == org_id,
                StaffUser.role == "org_admin",
                StaffUser.status == "active",
            ).count()
            assert remaining == 1
        finally:
            session.close()

    def test_org_isolation(self):
        tag = uuid.uuid4().hex[:6]
        org_id = self._mk_org(tag)
        tok = self._mk_org_admin_token(org_id)
        foreign_org = f"foreign_org_{uuid.uuid4().hex[:8]}"
        session = SessionFactory()
        try:
            session.add(Organization(id=foreign_org, name="Foreign",
                                     code=foreign_org.upper()))
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=foreign_org,
                branch_id=None, username=f"foreign_oa_{uuid.uuid4().hex[:6]}",
                password_hash=pw_hash, display_name="Foreign OA",
                role="org_admin", status="active")
            session.add(u); session.commit()
            foreign_uid = u.id
        finally:
            session.close()
        r = client.patch(f"/api/v1/staff/users/{foreign_uid}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"role": "receptionist"})
        assert r.status_code == 404, r.text


class TestMultiDoctorValidation:
    """PO-RBAC-01: Multi-doctor assignment validation."""

    def _mk_tag(self):
        return uuid.uuid4().hex[:6]

    def _mk_foreign_org_and_doctor(self, session, tag):
        foreign_org_id = f"foreign_org_{tag}"
        foreign_doc_id = f"foreign_doc_{tag}"
        org = session.query(Organization).filter(
            Organization.id == foreign_org_id).first()
        if org is None:
            org = Organization(id=foreign_org_id,
                               name=f"Foreign Org {tag}",
                               code=f"FOR{tag.upper()}")
            session.add(org)
        doc = session.query(Doctor).filter(Doctor.id == foreign_doc_id).first()
        if doc is None:
            doc = Doctor(id=foreign_doc_id, organization_id=foreign_org_id,
                         name=f"Foreign Doctor {tag}",
                         mobile=f"017{tag[:8]}")
            session.add(doc)
        session.commit()
        return foreign_org_id, foreign_doc_id

    def test_create_cross_org_doctor_assignment_rejected(self):
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            self._mk_foreign_org_and_doctor(session, tag)
        finally:
            session.close()
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID,
                  "username": _uniq("md_cross_org"),
                  "password": "x", "display_name": "Cross Org",
                  "role": "assistant",
                  "doctor_ids": [f"foreign_doc_{tag}"]})
        assert r.status_code == 422, r.text

    def test_create_nonexistent_doctor_rejected(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID,
                  "username": _uniq("md_nonexist"),
                  "password": "x", "display_name": "Nonexist",
                  "role": "assistant",
                  "doctor_ids": ["does-not-exist-doctor-id"]})
        assert r.status_code == 422, r.text

    def test_create_inactive_doctor_rejected(self):
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc_id = f"inactive_doc_{tag}"
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                doc = Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                             name=f"Inactive Doctor {tag}",
                             mobile=f"017{tag[:8]}", status="inactive")
                session.add(doc)
                session.commit()
        finally:
            session.close()
        r = client.post("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"organization_id": TEST_ORG_ID,
                  "username": _uniq("md_inactive"),
                  "password": "x", "display_name": "Inactive",
                  "role": "assistant",
                  "doctor_ids": [doc_id]})
        assert r.status_code == 422, r.text

    def test_update_cannot_introduce_invalid_doctor(self):
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc_id = f"valid_doc_{tag}"
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                doc = Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                             name=f"Valid Doctor {tag}",
                             mobile=f"017{tag[:8]}")
                session.add(doc)
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"md_upd_{tag}",
                password_hash=pw_hash, display_name="Upd Test",
                role="assistant", doctor_id=doc_id, status="active")
            session.add(u)
            from common.models import StaffDoctorAssignment
            session.add(StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc_id, organization_id=TEST_ORG_ID,
                status="active"))
            session.commit()
            uid = u.id
        finally:
            session.close()
        r = client.patch(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            json={"doctor_ids": ["does-not-exist-doctor-id"]})
        assert r.status_code == 422, r.text

    def test_legacy_doctor_id_still_accessible(self):
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc_id = f"legacy_doc_{tag}"
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                doc = Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                             name=f"Legacy Doctor {tag}",
                             mobile=f"017{tag[:8]}")
                session.add(doc)
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"legacy_{tag}",
                password_hash=pw_hash, display_name="Legacy",
                role="doctor", doctor_id=doc_id, status="active")
            session.add(u)
            # PO-RBAC-01: the f8a1b2c3d4e5 migration backfills the legacy
            # doctor_id into an explicit assignment row, so a migrated account
            # carries both.  The assignment table is authoritative; removed
            # rows are a revocation and must not be re-derived from doctor_id.
            from common.models import StaffDoctorAssignment
            session.add(StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc_id, organization_id=TEST_ORG_ID,
                status="active"))
            session.commit()
            uid = u.id
        finally:
            session.close()
        r = client.get(f"/api/v1/staff/users/{uid}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["doctor_id"] == doc_id
        assert doc_id in body["doctor_ids"]


class TestLastOrgAdminConcurrency:
    """PO-RBAC-04: Last active Organization Admin concurrency protection."""

    def _mk_tag(self):
        return uuid.uuid4().hex[:6]

    def _mk_org_and_two_admins(self, tag):
        session = SessionFactory()
        try:
            org_id = f"conc_org_{tag}"
            org = session.query(Organization).filter(
                Organization.id == org_id).first()
            if org is None:
                org = Organization(id=org_id, name=f"Conc Org {tag}",
                                   code=f"CON{tag.upper()}")
                session.add(org)
            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            ids = []
            for i in range(2):
                u = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                    branch_id=None,
                    username=f"conc_oa_{tag}_{i}",
                    password_hash=pw_hash, display_name=f"Conc OA {i}",
                    role="org_admin", status="active")
                session.add(u)
                ids.append(u.id)
            session.commit()
            return org_id, ids
        finally:
            session.close()

    def test_concurrent_deactivation_one_remains(self):
        """Two concurrent deactivation requests for different admins.

        Exercises the organization-row serialization mechanism: each request
        locks the organization row via ``with_for_update()`` before checking
        the active-org-admin count.  PostgreSQL row-level locking ensures only
        one transaction can hold the lock at a time, so exactly one
        deactivation succeeds and the other is rejected (403).
        """
        tag = self._mk_tag()
        org_id, admin_ids = self._mk_org_and_two_admins(tag)

        # Create a separate authenticated token for each admin.
        tokens = []
        for aid in admin_ids:
            tok = jwt.encode(
                {"sub": aid, "org": org_id, "branch": None,
                 "role": "org_admin",
                 "exp": int((datetime.now(timezone.utc)
                             + timedelta(hours=1)).timestamp())},
                _SECRET, algorithm=_ALGO,
            )
            tokens.append((aid, tok))

        results = [None, None]

        def deactivate_other(index: int) -> None:
            """Each thread deactivates the OTHER admin."""
            target_id = admin_ids[1 - index]
            tok = tokens[index][1]
            r = client.patch(
                f"/api/v1/staff/users/{target_id}",
                headers={"Authorization": f"Bearer {tok}"},
                json={"status": "inactive"},
            )
            results[index] = r.status_code

        # Submit both requests concurrently so they genuinely overlap at the
        # database level.  The organization-row lock serializes them.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(deactivate_other, i) for i in range(2)
            ]
            done, not_done = concurrent.futures.wait(
                futures, timeout=10,
                return_when=concurrent.futures.ALL_COMPLETED,
            )
            assert len(done) == 2, (
                f"Concurrent deactivation timed out: "
                f"{len(not_done)} futures incomplete"
            )

        statuses = [s for s in results if s is not None]
        assert statuses.count(200) == 1, (
            f"Expected exactly 1 successful deactivation, got {statuses}"
        )
        assert statuses.count(403) == 1, (
            f"Expected exactly 1 denied deactivation, got {statuses}"
        )

        # Verify at least one active org_admin remains in the database.
        session = SessionFactory()
        try:
            remaining = session.query(StaffUser).filter(
                StaffUser.organization_id == org_id,
                StaffUser.role == "org_admin",
                StaffUser.status == "active",
            ).count()
            assert remaining == 1, (
                f"Expected 1 remaining active org_admin, got {remaining}"
            )
        finally:
            session.close()


class TestDoctorAssignmentLoading:
    """PO-RBAC-01 / Correction A: Doctor assignment loading fails closed.

    Tests that when the staff_doctor_assignments table exists but a query
    fails, legacy StaffUser.doctor_id fallback is NOT used (fail closed).
    """

    def _mk_tag(self):
        return uuid.uuid4().hex[:6]

    def test_table_absent_legacy_fallback_ok(self):
        """When the assignment table doesn't exist, return None — callers may
        then fall back to the legacy ``StaffUser.doctor_id`` column."""
        session = SessionFactory()
        try:
            from unittest.mock import patch
            # Mock sqlalchemy.inspect to return an inspector saying table
            # doesn't exist yet (pre-migration compatibility).
            with patch('sqlalchemy.inspect') as mock_inspect:
                mock_inspect.return_value.has_table.return_value = False
                result = _load_assigned_doctor_ids(session, "some-user-id")
                assert result is None
        finally:
            session.close()

    def test_table_exists_with_active_assignments(self):
        """When table exists with active assignments, return those IDs only."""
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc1_id = f"load_doc1_{tag}"
            doc2_id = f"load_doc2_{tag}"
            for did in [doc1_id, doc2_id]:
                doc = session.query(Doctor).filter(Doctor.id == did).first()
                if doc is None:
                    doc = Doctor(id=did, organization_id=TEST_ORG_ID,
                                 name=f"Load Doctor {did[-4:]}",
                                 mobile=f"017{tag[:8]}")
                    session.add(doc)

            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"load_user_{tag}",
                password_hash=pw_hash, display_name="Load User",
                role="assistant", status="active")
            session.add(u)

            from common.models import StaffDoctorAssignment
            session.add(StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc1_id, organization_id=TEST_ORG_ID,
                status="active"))
            session.add(StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc2_id, organization_id=TEST_ORG_ID,
                status="active"))
            session.commit()

            result = _load_assigned_doctor_ids(session, u.id)
            assert set(result) == {doc1_id, doc2_id}
        finally:
            session.close()

    def test_table_exists_no_active_assignments_returns_empty(self):
        """When the table exists but no active assignments remain, return []
        — the caller must NOT fall back to legacy ``doctor_id``."""
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc_id = f"load_none_{tag}"
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                doc = Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                             name="Load None Doctor",
                             mobile=f"017{tag[:8]}")
                session.add(doc)

            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"load_none_user_{tag}",
                password_hash=pw_hash, display_name="Load None User",
                role="assistant", doctor_id=doc_id, status="active")
            session.add(u)
            session.commit()

            result = _load_assigned_doctor_ids(session, u.id)
            assert result == []
        finally:
            session.close()

    def test_query_failure_propagates_fail_closed(self):
        """When table exists but query fails, exception propagates — no
        silent fallback to legacy doctor_id."""
        from unittest.mock import patch
        session = SessionFactory()
        try:
            with patch.object(session, 'execute', side_effect=Exception("DB error")):
                try:
                    _load_assigned_doctor_ids(session, "some-user-id")
                    assert False, "Expected exception to propagate (fail closed)"
                except Exception:
                    pass  # Expected — fail closed, no legacy fallback
        finally:
            session.close()

    def test_revoked_assignment_still_denied_with_legacy_doctor_id(self):
        """Revoked assignment: access remains denied even though legacy
        doctor_id still references the revoked doctor."""
        tag = self._mk_tag()
        session = SessionFactory()
        try:
            doc_id = f"load_revoked_{tag}"
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                doc = Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                             name="Revoked Doctor",
                             mobile=f"017{tag[:8]}")
                session.add(doc)

            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"load_rev_user_{tag}",
                password_hash=pw_hash, display_name="Revoked User",
                role="assistant", doctor_id=doc_id, status="active")
            session.add(u)

            from common.models import StaffDoctorAssignment
            sda = StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc_id, organization_id=TEST_ORG_ID,
                status="active")
            session.add(sda)
            session.commit()
            # Revoke it
            session.delete(sda)
            session.commit()

            result = _load_assigned_doctor_ids(session, u.id)
            assert result == []
        finally:
            session.close()

    def test_get_current_user_ignores_legacy_doctor_id_after_revocation(self):
        """PO-RBAC-01 regression: a revoked assignment must not be restored by
        the legacy ``StaffUser.doctor_id`` column.

        The account keeps ``doctor_id`` (pre-migration data) while the active
        assignment row has been removed.  ``get_current_user()`` must carry an
        empty ``assigned_doctor_ids`` and ``can_access_doctor()`` must fail
        closed for that doctor.
        """
        from fastapi.security import HTTPAuthorizationCredentials
        from common.auth import get_current_user

        tag = self._mk_tag()
        doc_id = f"load_regr_{tag}"
        session = SessionFactory()
        try:
            doc = session.query(Doctor).filter(Doctor.id == doc_id).first()
            if doc is None:
                session.add(Doctor(id=doc_id, organization_id=TEST_ORG_ID,
                                   name=f"Regression Doctor {tag}",
                                   mobile=f"017{tag[:8]}"))

            pw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=TEST_ORG_ID,
                branch_id=None, username=f"load_regr_user_{tag}",
                password_hash=pw_hash, display_name="Regression User",
                role="assistant", doctor_id=doc_id, status="active")
            session.add(u)

            from common.models import StaffDoctorAssignment
            sda = StaffDoctorAssignment(
                id=str(uuid.uuid4()), staff_user_id=u.id,
                doctor_id=doc_id, organization_id=TEST_ORG_ID,
                status="active")
            session.add(sda)
            session.commit()
            user_id = u.id

            # Revoke only the explicit assignment; the legacy column survives.
            session.delete(sda)
            session.commit()
            assert session.query(StaffUser).filter(
                StaffUser.id == user_id).one().doctor_id == doc_id
        finally:
            session.close()

        tok = jwt.encode(
            {"sub": user_id, "org": TEST_ORG_ID, "branch": None,
             "role": "assistant",
             "exp": int((datetime.now(timezone.utc)
                         + timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
        auth = get_current_user(HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=tok))
        assert auth.assigned_doctor_ids == []
        assert auth.can_access_doctor(doc_id) is False