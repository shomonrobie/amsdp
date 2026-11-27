"""M2 Security Tests — Identity endpoint protection, RBAC, tenant isolation.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "identity"))

import pytest, jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import StaffUser, Organization, Branch
from common.permissions import PERMISSIONS
from identity.models import _SECRET, _ALGO
import uuid as _uuid

def _uniq(name):
    return f"{name}_{_uuid.uuid4().hex[:6]}"

def _ensure_orgs_and_branches():
    session = SessionFactory()
    try:
        for oid, code in [("m2-test-org", "M2-TEST"), ("other-org-999", "OTHER-ORG")]:
            if not session.query(Organization).filter(Organization.id == oid).first():
                session.add(Organization(id=oid, name=code, code=code))
        for bid, oid in [("main-branch", "m2-test-org"), ("branch-a", "m2-test-org"),
                         ("branch-b", "m2-test-org"), ("other-branch", "other-org-999")]:
            if not session.query(Branch).filter(Branch.id == bid).first():
                session.add(Branch(id=bid, organization_id=oid, name=bid, code=bid))
        session.commit()
    finally:
        session.close()

@pytest.fixture(scope="module", autouse=True)
def _orgs_and_branches():
    """Seed this module's organisations and branches once per module.

    This used to run at **import** time, which made *collection* write to
    whatever database the suite was pointed at — and, because the rows landed
    before any test executed, it silently satisfied another module's fixture:
    ``identity/tests/test_identity.py::TestDoctorLink`` passed in a whole-tree
    run and failed when run alone (D-3).  Seeding inside a fixture keeps
    collection pure and removes the accidental cross-module dependency
    (finding T-10, 27 November 2026).
    """
    _ensure_orgs_and_branches()


from identity.main import app
client = TestClient(app)


def _create_user(session, username, role, org_id="m2-test-org", branch_id=None):
    import bcrypt, uuid
    kw = {}
    if branch_id:
        kw["branch_id"] = branch_id
    pw_hash = bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode()
    user = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
        username=username, password_hash=pw_hash,
        display_name=username.title(), role=role, status="active", **kw)
    session.add(user)
    session.commit()
    return user


def _token_for(username):
    session = SessionFactory()
    user = session.query(StaffUser).filter(StaffUser.username == username).first()
    session.close()
    if not user:
        return None
    return jwt.encode({"sub": user.id, "org": user.organization_id,
        "branch": user.branch_id, "role": user.role,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


@pytest.fixture(autouse=True)
def clean_users():
    """Upsert the six (plus cross-org) test users used by this suite.

    Idempotent and NON-destructive: never deletes other staff users (the old
    implementation wiped the whole staff_users table on every run, destroying
    demo accounts). Same-username rows are updated in place.
    """
    TEST_USERS = [
        ("super", "super_admin", "m2-test-org", None),
        ("orgadm", "org_admin", "m2-test-org", None),
        ("bradm", "branch_admin", "m2-test-org", "main-branch"),
        ("recp", "receptionist", "m2-test-org", "main-branch"),
        ("dr", "doctor", "m2-test-org", "main-branch"),
        ("ast", "assistant", "m2-test-org", "main-branch"),
        ("other", "branch_admin", "other-org-999", "other-branch"),
    ]
    session = SessionFactory()
    try:
        for username, role, org_id, branch_id in TEST_USERS:
            user = session.query(StaffUser).filter(
                StaffUser.username == username).first()
            if not user:
                user = _create_user(session, username, role, org_id, branch_id)
            else:
                user.role, user.organization_id = role, org_id
                user.branch_id = branch_id
                user.status = "active"
                session.commit()
        yield
    finally:
        session.close()
# 1. Missing token
class TestMissingToken:
    def test_list_staff_without_token(self):
        assert client.get("/api/v1/staff/users").status_code == 401
    def test_get_user_without_token(self):
        assert client.get("/api/v1/staff/users/any").status_code == 401
    def test_create_without_token(self):
        r = client.post("/api/v1/staff/users", json=dict(organization_id="x",
            username="x", password="x", display_name="x", role="receptionist"))
        assert r.status_code == 401

# 2. Invalid token
class TestInvalidToken:
    def test_garbage(self):
        r = client.get("/api/v1/staff/users",
            headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401
    def test_wrong_secret(self):
        bad = jwt.encode({"sub":"x","org":"o","role":"r"},"wrong",algorithm="HS256")
        r = client.get("/api/v1/staff/users",
            headers={"Authorization": f"Bearer {bad}"})
        assert r.status_code == 401
# 3. Expired token
class TestExpiredToken:
    def test_expired(self):
        u = SessionFactory().query(StaffUser).filter(
            StaffUser.username=="super").first()
        t = jwt.encode({"sub":u.id,"org":u.organization_id,
            "branch":u.branch_id,"role":u.role,
            "exp":int((datetime.now(timezone.utc)-timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
        assert client.get("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {t}"}).status_code == 401

# 4. Inactive account
class TestInactive:
    def test_inactive_rejected(self):
        session = SessionFactory()
        u = _create_user(session, _uniq("inactive"), "receptionist")
        u.status = "inactive"; session.commit(); session.close()
        t = _token_for(u.username)
        assert client.get("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {t}"}).status_code == 403

# 5. Valid super_admin
class TestValidSuper:
    def test_login(self):
        r = client.post("/api/v1/staff/login",
            json={"username":"super","password":"testpass123"})
        assert r.status_code == 200; assert r.json()["token"]
    def test_list_users(self):
        r = client.get("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {_token_for('super')}"})
        assert r.status_code == 200; assert len(r.json()) >= 6
    def test_create_user(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {_token_for('super')}"},
            json=dict(organization_id="m2-test-org", username=_uniq("newu"),
                password="x", display_name="N", role="receptionist"))
        assert r.status_code == 201
# 6. Unauthorized role
class TestUnauthorized:
    def test_recp_cannot_list(self):
        assert client.get("/api/v1/staff/users",headers={
            "Authorization":f"Bearer {_token_for('recp')}"}).status_code == 403
    def test_recp_cannot_create(self):
        assert client.post("/api/v1/staff/users",headers={
            "Authorization":f"Bearer {_token_for('recp')}"},
            json=dict(organization_id="m2-test-org",username="x",
                password="x",display_name="X",role="receptionist")
            ).status_code == 403
    def test_org_admin_can(self):
        t = _token_for("orgadm")
        assert client.get("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {t}"}).status_code == 200
        assert client.post("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {t}"},json=dict(
                organization_id="m2-test-org",username=_uniq("oc"),
                password="x",display_name="OC",role="receptionist")
            ).status_code == 201

# 7. Cross-org
class TestCrossOrg:
    """Sequence 4: a foreign organization answers 404, never 403.

    A 403 would confirm that the staff id exists in another tenant; the
    non-disclosing 404 (``.clinerules`` §3) makes it indistinguishable from an
    unknown id.
    """
    def test_cross_get(self):
        session = SessionFactory()
        o = session.query(StaffUser).filter(StaffUser.username=="other").first()
        session.close()
        assert client.get(f"/api/v1/staff/users/{o.id}",
            headers={"Authorization":f"Bearer {_token_for('orgadm')}"}
            ).status_code == 404
    def test_cross_update(self):
        session = SessionFactory()
        o = session.query(StaffUser).filter(StaffUser.username=="other").first()
        session.close()
        assert client.patch(f"/api/v1/staff/users/{o.id}",
            headers={"Authorization":f"Bearer {_token_for('orgadm')}"},
            json={"display_name":"H"}).status_code == 404
    def test_unknown_id_is_indistinguishable(self):
        """Unknown id and foreign id must produce the same status and body."""
        session = SessionFactory()
        o = session.query(StaffUser).filter(StaffUser.username=="other").first()
        session.close()
        headers = {"Authorization":f"Bearer {_token_for('orgadm')}"}
        foreign = client.get(f"/api/v1/staff/users/{o.id}", headers=headers)
        unknown = client.get("/api/v1/staff/users/does-not-exist-999", headers=headers)
        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json() == unknown.json()

# 8. Cross-branch
class TestCrossBranch:
    def test_branch_admin_cross_denied(self):
        session = SessionFactory()
        bradm = session.query(StaffUser).filter(
            StaffUser.username=="bradm").first()
        bb = _create_user(session, _uniq("branchb"), "receptionist", branch_id="branch-b")
        t = jwt.encode({"sub":bradm.id,"org":bradm.organization_id,
            "branch":"main-branch","role":"branch_admin",
            "exp":int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())},
            _SECRET, algorithm=_ALGO)
        session.close()
        assert client.get(f"/api/v1/staff/users/{bradm.id}",
            headers={"Authorization":f"Bearer {t}"}).status_code == 200
        # Another branch is a non-disclosing 404 (never 403).
        assert client.get(f"/api/v1/staff/users/{bb.id}",
            headers={"Authorization":f"Bearer {t}"}).status_code == 404

# 9. Org override
class TestOrgOverride:
    def test_cannot_force_other_org(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {_token_for('orgadm')}"},
            json=dict(organization_id="other-org-999", username="ov",
                password="x", display_name="OV", role="receptionist"))
        assert r.status_code == 422

# 10. Super admin boundaries
class TestSuperBoundaries:
    def test_super_cross_org_read(self):
        session = SessionFactory()
        o = session.query(StaffUser).filter(StaffUser.username=="other").first()
        session.close()
        assert client.get(f"/api/v1/staff/users/{o.id}",
            headers={"Authorization":f"Bearer {_token_for('super')}"}
            ).status_code == 200
    def test_super_cross_org_create(self):
        r = client.post("/api/v1/staff/users",
            headers={"Authorization":f"Bearer {_token_for('super')}"},
            json=dict(organization_id="other-org-999", username=_uniq("sc"),
                password="x", display_name="SC", role="receptionist"))
        assert r.status_code == 201

# 11. Validate
class TestValidate:
    def test_valid(self):
        assert client.get("/api/v1/staff/validate",
            headers={"Authorization":f"Bearer {_token_for('super')}"}
            ).json()["valid"] is True
    
def test_no_token():
        assert client.get("/api/v1/staff/validate").status_code == 401


# 12. Login throttling (Sequence 4, WP3)
class TestLoginThrottle:
    """Password spraying is slowed down without ever locking an account out."""

    @pytest.fixture(autouse=True)
    def _throttle(self, monkeypatch):
        import identity.main as idm
        idm._reset_login_throttle()
        monkeypatch.setattr(idm, "_LOGIN_MAX_ATTEMPTS", 3)
        yield
        idm._reset_login_throttle()

    def _attempt(self, username, password="wrongpass"):
        return client.post("/api/v1/staff/login",
            json={"username": username, "password": password})

    def test_repeated_failures_get_429(self):
        name = _uniq("spray")
        assert [self._attempt(name).status_code for _ in range(3)] == [401, 401, 401]
        r = self._attempt(name)
        assert r.status_code == 429
        assert int(r.headers["Retry-After"]) > 0

    def test_limit_is_per_username(self):
        a, b = _uniq("spraya"), _uniq("sprayb")
        for _ in range(3):
            self._attempt(a)
        assert self._attempt(a).status_code == 429
        # A different username is unaffected: no shared-IP lockout.
        assert self._attempt(b).status_code == 401

    def test_success_clears_the_bucket(self):
        for _ in range(2):
            assert self._attempt("recp").status_code == 401
        assert self._attempt("recp", "testpass123").status_code == 200
        # The successful login reset the window, so this is 401, not 429.
        assert self._attempt("recp").status_code == 401