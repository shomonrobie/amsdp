"""M5 Queue Service Tests — PostgreSQL-backed."""
import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "identity"))

import pytest, jwt
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import (Organization, Branch, StaffUser, Doctor,
                           DoctorBranch, Patient, QueueEntry, Appointment)
from identity.models import _SECRET, _ALGO


def _ensure_org():
    session = SessionFactory()
    try:
        if not session.query(Organization).filter(Organization.code == "M5-ORG").first():
            session.add(Organization(id="m5-org", name="M5 Org", code="M5-ORG"))
        if not session.query(Branch).filter(Branch.id == "m5-branch").first():
            session.add(Branch(id="m5-branch", organization_id="m5-org", name="Main", code="M5-BR"))
        if not session.query(Doctor).filter(Doctor.id == "m5-doc").first():
            session.add(Doctor(id="m5-doc", organization_id="m5-org", name="Dr Test", mobile="01700000000"))
        session.commit()
    finally:
        session.close()

_ensure_org()


def _mk_user(session, username, role):
    existing = session.query(StaffUser).filter(StaffUser.username == username).first()
    if existing: return existing
    pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
    u = StaffUser(id=str(uuid.uuid4()), organization_id="m5-org", branch_id="m5-branch",
                  username=username, password_hash=pw, display_name=username,
                  role=role, status="active")
    session.add(u); session.commit()
    return u


def _token(user, org="m5-org", branch="m5-branch"):
    return jwt.encode({"sub": user.id, "org": org, "branch": branch, "role": user.role,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


def _mk_patient(session):
    p = Patient(id=str(uuid.uuid4()), organization_id="m5-org",
                name="Test Patient", mobile="01711112222")
    session.add(p); session.commit(); return p


def _mk_appointment(session, patient_id, status="CONFIRMED"):
    a = Appointment(id=str(uuid.uuid4()), organization_id="m5-org", branch_id="m5-branch",
                    patient_id=patient_id, doctor_id="m5-doc",
                    appointment_date=date.today(),
                    start_time="10:00", status=status, status_history=[],
                    token_number="T-TEST-001")
    session.add(a); session.commit(); return a

@pytest.fixture(autouse=True)
def clean_queue():
    session = SessionFactory()
    session.query(QueueEntry).delete()
    session.commit(); session.close()
    yield


@pytest.fixture(scope="module")
def receptionist():
    session = SessionFactory()
    u = _mk_user(session, "m5_recp", "receptionist")
    session.close(); return u


@pytest.fixture(scope="module")
def doctor_user():
    session = SessionFactory()
    u = _mk_user(session, "m5_docu", "doctor")
    session.close(); return u



def _auth(token): return {"Authorization": f"Bearer {token}"}


class TestCheckIn:
    def test_check_in_creates_entry(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); a = _mk_appointment(session, p.id); session.close()
        r = client.post("/api/v1/queue/check-in", headers=_auth(_token(receptionist)), json={"appointment_id": a.id})
        assert r.status_code == 201 and r.json()["status"] == "waiting" and r.json()["token"].startswith("T-")

    def test_duplicate_check_in_rejected(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); a = _mk_appointment(session, p.id); session.close()
        t = _token(receptionist)
        assert client.post("/api/v1/queue/check-in", headers=_auth(t), json={"appointment_id": a.id}).status_code == 201
        assert client.post("/api/v1/queue/check-in", headers=_auth(t), json={"appointment_id": a.id}).status_code == 422

    def test_completed_appointment_cannot_check_in(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); a = _mk_appointment(session, p.id, status="COMPLETED"); session.close()
        r = client.post("/api/v1/queue/check-in", headers=_auth(_token(receptionist)), json={"appointment_id": a.id})
        assert r.status_code == 422


class TestWalkInPolicies:
    def test_end_of_queue(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in", "walk_in_policy": "end_of_queue"})
        assert r.status_code == 201 and r.json()["entry_source"] == "walk_in" and r.json()["position"] >= 1

    def test_first_come(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in", "walk_in_policy": "first_come"})
        assert r.status_code == 201

    def test_reserved_capacity(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in", "walk_in_policy": "reserved_capacity"})
        assert r.status_code == 201

    def test_staff_placement(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in",
                  "walk_in_policy": "staff_placement", "position": 5})
        assert r.status_code == 201 and r.json()["position"] == 5

    def test_invalid_policy_rejected(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in", "walk_in_policy": "bogus"})
        assert r.status_code == 422

from queuing.main import app
class TestTokens:
    def test_unique_daily_tokens(self, receptionist):
        session = SessionFactory()
        ps = [_mk_patient(session) for _ in range(5)]
        session.close()
        t = _token(receptionist)
        toks = set()
        for p in ps:
            r = client.post("/api/v1/queue/enqueue", headers=_auth(t),
                json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"})
            assert r.status_code == 201
            toks.add(r.json()["token"])
        assert len(toks) == 5


class TestReorder:
    def test_reorder_preserves_token(self, receptionist):
        session = SessionFactory()
        ps = [_mk_patient(session) for _ in range(2)]
        session.close()
        t = _token(receptionist)
        e1 = client.post("/api/v1/queue/enqueue", headers=_auth(t),
            json={"doctor_id": "m5-doc", "patient_id": ps[0].id, "entry_source": "walk_in"}).json()
        e2 = client.post("/api/v1/queue/enqueue", headers=_auth(t),
            json={"doctor_id": "m5-doc", "patient_id": ps[1].id, "entry_source": "walk_in"}).json()
        tok1 = e1["token"]
        r = client.post("/api/v1/queue/reorder", headers=_auth(t),
            json={"entry_ids": [e2["id"], e1["id"]], "reason": "test"})
        assert r.status_code == 200
        q = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(t)).json()
        ent1 = next(x for x in q["entries"] if x["id"] == e1["id"])
        assert ent1["token"] == tok1
        assert ent1["position"] == 2
        assert len(ent1["position_history"]) >= 1


class TestTransitions:
    def test_lifecycle(self, receptionist, doctor_user):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        tr = _token(receptionist); td = _token(doctor_user)
        e = client.post("/api/v1/queue/enqueue", headers=_auth(tr),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        eid = e["id"]
        assert client.patch(f"/api/v1/queue/{eid}", headers=_auth(td),
            json={"action": "start_consultation"}).json()["status"] == "in_consultation"
        assert client.patch(f"/api/v1/queue/{eid}", headers=_auth(td),
            json={"action": "complete_consultation"}).json()["status"] == "completed"

    def test_invalid_transition(self, receptionist, doctor_user):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        tr = _token(receptionist); td = _token(doctor_user)
        e = client.post("/api/v1/queue/enqueue", headers=_auth(tr),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        eid = e["id"]
        client.patch(f"/api/v1/queue/{eid}", headers=_auth(tr), json={"action": "cancel", "reason": "x"})
        r = client.patch(f"/api/v1/queue/{eid}", headers=_auth(td), json={"action": "complete_consultation"})
        assert r.status_code == 422


class TestAuthorization:
    def test_receptionist_can_view(self, receptionist):
        assert client.get("/api/v1/queue?doctor_id=m5-doc&date=2026-01-01",
            headers=_auth(_token(receptionist))).status_code == 200

    def test_doctor_can_start_consultation(self, doctor_user, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        r = client.patch(f"/api/v1/queue/{e['id']}", headers=_auth(_token(doctor_user)),
                         json={"action": "start_consultation"})
        assert r.status_code == 200

    def test_receptionist_cannot_start_consultation(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        r = client.patch(f"/api/v1/queue/{e['id']}", headers=_auth(_token(receptionist)),
                         json={"action": "start_consultation"})
        assert r.status_code == 403

    def test_receptionist_cannot_complete_consultation(self, receptionist, doctor_user):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        tr = _token(receptionist); td = _token(doctor_user)
        e = client.post("/api/v1/queue/enqueue", headers=_auth(tr),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        eid = e["id"]
        client.patch(f"/api/v1/queue/{eid}", headers=_auth(td), json={"action": "start_consultation"})
        r = client.patch(f"/api/v1/queue/{eid}", headers=_auth(tr), json={"action": "complete_consultation"})
        assert r.status_code == 403

    def test_no_token_rejected(self):
        assert client.get("/api/v1/queue?doctor_id=m5-doc&date=2026-01-01").status_code == 401

    def test_cross_org_entry_not_found(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        # receptionist has queue.manage (cancel) — permission passes, org filter hides entry
        bad = client.patch(f"/api/v1/queue/{e['id']}", headers=_auth(_token(receptionist, org="other-org")),
                           json={"action": "cancel", "reason": "x"})
        assert bad.status_code in (403, 404)  # either org-permission gate or not-found leak prevention

    def test_persistence_across_db_reopen(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        # Simulate restart: fresh session query
        s2 = SessionFactory()
        q = s2.query(QueueEntry).filter(QueueEntry.id == e["id"]).first()
        assert q is not None and q.token.startswith("T-") and q.status == "waiting"
        s2.close()

    def test_queue_ops_write_audit_events(self, receptionist):
        from common.models import AuditEvent
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        s2 = SessionFactory()
        evt = s2.query(AuditEvent).filter(AuditEvent.target_id == e["id"],
            AuditEvent.action == "queue.enqueue").first()
        assert evt is not None
        assert evt.organization_id == "m5-org"
        assert evt.actor_role == "receptionist"
        s2.close()
client = TestClient(app)


class TestQueueBranchAuthorization:
    """P0-1..P0-5: branch scope enforcement across the queue endpoints.

    The catalogue's single branch (m5-branch) is extended here with a second
    branch in the same organisation so cross-branch attempts can be exercised.
    Tokens are minted with an explicit branch so a caller can be placed in a
    branch different from the entry they target.
    """

    def _ensure_branch(self, session, branch_id, org_id="m5-org"):
        b = session.query(Branch).filter(Branch.id == branch_id).first()
        if b is None:
            session.add(Branch(id=branch_id, organization_id=org_id,
                               name=branch_id, code=branch_id.upper()))
            session.commit()

    def _ensure_user_at(self, session, username, role, branch_id):
        u = session.query(StaffUser).filter(StaffUser.username == username).first()
        if u is None:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id="m5-org",
                          branch_id=branch_id, username=username,
                          password_hash=pw, display_name=username, role=role,
                          status="active")
            session.add(u); session.commit()
        return u

    def _enqueue(self, patient_id, branch_id=None, token=None):
        body = {"doctor_id": "m5-doc", "patient_id": patient_id,
                "entry_source": "walk_in"}
        if branch_id is not None:
            body["branch_id"] = branch_id
        return client.post("/api/v1/queue/enqueue", headers=_auth(token),
                           json=body)

    def test_p0_1_cross_branch_entry_denied(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_b = self._ensure_user_at(session, "p01_recp_b",
                                          "receptionist", "m5-branch-2")
            user_b_id = user_b.id
        finally:
            session.close()
        token_b = _token(user_b, branch="m5-branch-2")

        p = _mk_patient(SessionFactory())
        a = _mk_appointment(SessionFactory(), p.id, status="CONFIRMED")
        entry = self._enqueue(p.id, token=_token(receptionist)).json()
        assert entry["branch_id"] == "m5-branch"

        # P0-1: a caller in another branch cannot touch the entry (404, never 403).
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(token_b),
                         json={"action": "cancel", "reason": "x"})
        assert r.status_code == 404, r.text
        # Same-branch caller still succeeds.
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(_token(receptionist)),
                         json={"action": "cancel", "reason": "x"})
        assert r.status_code == 200, r.text

    def test_p0_2_queue_list_rejects_foreign_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
        finally:
            session.close()
        today = date.today().isoformat()
        base = f"/api/v1/queue?doctor_id=m5-doc&date={today}"

        # P0-2: caller-supplied branch_id for another branch is rejected (404).
        r = client.get(base + "&branch_id=m5-branch-2",
                       headers=_auth(_token(receptionist)))
        assert r.status_code == 404, r.text
        # Own branch still works.
        r = client.get(base + "&branch_id=m5-branch",
                       headers=_auth(_token(receptionist)))
        assert r.status_code == 200, r.text

    def test_p0_2_queue_list_org_admin_org_wide(self):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_o = self._ensure_user_at(session, "p02_org_admin",
                                          "org_admin", None)
        finally:
            session.close()
        today = date.today().isoformat()
        # org_admin retains organization-wide access across branches.
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={today}"
                       f"&branch_id=m5-branch-2",
                       headers=_auth(_token(user_o)))
        assert r.status_code == 200, r.text

    def test_p0_3_check_in_rejects_foreign_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_b = self._ensure_user_at(session, "p03_recp_b",
                                          "receptionist", "m5-branch-2")
        finally:
            session.close()
        p = _mk_patient(SessionFactory())
        a = _mk_appointment(SessionFactory(), p.id, status="CONFIRMED")
        assert a.branch_id == "m5-branch"

        # P0-3: supplying another branch_id in the body is denied.
        r = client.post("/api/v1/queue/check-in",
                        headers=_auth(_token(receptionist)),
                        json={"appointment_id": a.id, "branch_id": "m5-branch-2"})
        assert r.status_code == 404, r.text
        # A caller not authorized for the appointment's branch is denied.
        r = client.post("/api/v1/queue/check-in",
                        headers=_auth(_token(user_b, branch="m5-branch-2")),
                        json={"appointment_id": a.id})
        assert r.status_code == 404, r.text
        # Same-branch check-in succeeds.
        r = client.post("/api/v1/queue/check-in",
                        headers=_auth(_token(receptionist)),
                        json={"appointment_id": a.id})
        assert r.status_code == 201, r.text

    def test_p0_4_enqueue_rejects_foreign_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_b = self._ensure_user_at(session, "p04_recp_b",
                                          "receptionist", "m5-branch-2")
        finally:
            session.close()
        p = _mk_patient(SessionFactory())

        # P0-4: caller-supplied branch_id for another branch is denied.
        r = self._enqueue(p.id, branch_id="m5-branch-2",
                          token=_token(receptionist))
        assert r.status_code == 404, r.text
        # Falling back to the caller's own branch succeeds.
        r = self._enqueue(p.id, branch_id=None, token=_token(receptionist))
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "m5-branch"
        # A caller in branch B enqueuing with no branch_id lands in branch B.
        r = self._enqueue(p.id, branch_id=None, token=_token(user_b, branch="m5-branch-2"))
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "m5-branch-2"

    def test_p0_4_enqueue_org_admin_org_wide(self):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_o = self._ensure_user_at(session, "p04_org_admin",
                                          "org_admin", None)
        finally:
            session.close()
        p = _mk_patient(SessionFactory())
        # org_admin may enqueue into any branch of the organisation.
        r = self._enqueue(p.id, branch_id="m5-branch-2",
                          token=_token(user_o, branch=None))
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "m5-branch-2"

    def test_p0_5_reorder_rejects_mixed_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
            user_o = self._ensure_user_at(session, "p05_org_admin",
                                          "org_admin", None)
        finally:
            session.close()
        p1 = _mk_patient(SessionFactory())
        p2 = _mk_patient(SessionFactory())
        e1 = self._enqueue(p1.id, branch_id="m5-branch",
                           token=_token(receptionist)).json()
        e2 = self._enqueue(p2.id, branch_id="m5-branch-2",
                           token=_token(user_o, branch=None)).json()

        # Positions before the (rejected) reorder.
        s = SessionFactory()
        try:
            before = {row.id: row.position for row in s.query(QueueEntry).filter(
                QueueEntry.id.in_([e1["id"], e2["id"]])).all()}
        finally:
            s.close()

        # P0-5: mixed-branch reorder is rejected with no partial mutation.
        # org_admin is authorized for both branches, so the homogeneity check
        # (not the per-entry branch check) is what rejects the mix.
        r = client.post("/api/v1/queue/reorder",
                        headers=_auth(_token(user_o, branch=None)),
                        json={"entry_ids": [e1["id"], e2["id"]], "reason": "x"})
        assert r.status_code == 422, r.text

        # Neither entry moved.
        s = SessionFactory()
        try:
            after = {row.id: row.position for row in s.query(QueueEntry).filter(
                QueueEntry.id.in_([e1["id"], e2["id"]])).all()}
        finally:
            s.close()
        assert before == after

    def test_p0_5_reorder_same_branch_succeeds(self, receptionist):
        p1 = _mk_patient(SessionFactory())
        p2 = _mk_patient(SessionFactory())
        e1 = self._enqueue(p1.id, branch_id="m5-branch",
                           token=_token(receptionist)).json()
        e2 = self._enqueue(p2.id, branch_id="m5-branch",
                           token=_token(receptionist)).json()
        r = client.post("/api/v1/queue/reorder",
                        headers=_auth(_token(receptionist)),
                        json={"entry_ids": [e2["id"], e1["id"]], "reason": "swap"})
        assert r.status_code == 200, r.text
        q = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
                       headers=_auth(_token(receptionist))).json()
        pos = {x["id"]: x["position"] for x in q["entries"]}
        assert pos[e1["id"]] == 2 and pos[e2["id"]] == 1


class TestQueueEnqueueBranchOwnership:
    """RBAC-R1: queue enqueue must validate branch ownership against the
    caller's organization."""

    def _mk_patient_at(self, session, org_id="m5-org"):
        p = Patient(id=str(uuid.uuid4()), organization_id=org_id,
                    name="RBAC-R1 Patient", mobile="01799999999")
        session.add(p); session.commit(); return p

    def _ensure_branch(self, session, branch_id, org_id="m5-org"):
        b = session.query(Branch).filter(Branch.id == branch_id).first()
        if b is None:
            session.add(Branch(id=branch_id, organization_id=org_id,
                               name=branch_id, code=branch_id.upper()))
            session.commit()

    def test_rbac_r1_org_admin_cannot_enqueue_foreign_org_branch(self, receptionist):
        foreign_org = f"r1-org-2-{uuid.uuid4().hex[:8]}"
        foreign_br = f"r1-br-2-{uuid.uuid4().hex[:8]}"
        foreign_code = f"R1ORG2-{uuid.uuid4().hex[:8]}"
        session = SessionFactory()
        try:
            o2 = Organization(id=foreign_org, name="R1 Org 2", code=foreign_code)
            b2 = Branch(id=foreign_br, organization_id=foreign_org,
                        name="R1 Branch 2", code=foreign_code)
            session.add(o2); session.add(b2); session.commit()
        finally:
            session.close()

        p = self._mk_patient_at(SessionFactory())
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org",
                          "branch": None, "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(tok),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": foreign_br})
        assert r.status_code == 404, r.text

    def test_rbac_r1_org_admin_can_enqueue_own_org_other_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
        finally:
            session.close()
        p = self._mk_patient_at(SessionFactory())
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org",
                          "branch": None, "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(tok),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": "m5-branch-2"})
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "m5-branch-2"

    def test_rbac_r1_receptionist_own_branch(self, receptionist):
        p = self._mk_patient_at(SessionFactory())
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(_token(receptionist)),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": "m5-branch"})
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "m5-branch"

    def test_rbac_r1_receptionist_cannot_enqueue_other_branch(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
        finally:
            session.close()
        p = self._mk_patient_at(SessionFactory())
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(_token(receptionist)),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": "m5-branch-2"})
        assert r.status_code == 404, r.text

    def test_rbac_r1_missing_branch_rejected(self, receptionist):
        p = self._mk_patient_at(SessionFactory())
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org",
                          "branch": None, "role": "receptionist",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(tok),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in"})
        assert r.status_code == 404, r.text

    def test_rbac_r1_nonexistent_branch_rejected(self, receptionist):
        p = self._mk_patient_at(SessionFactory())
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(_token(receptionist)),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": "does-not-exist"})
        assert r.status_code == 404, r.text

    def test_rbac_r1_valid_enqueue_creates_entry_and_audit(self, receptionist):
        session = SessionFactory()
        try:
            self._ensure_branch(session, "m5-branch-2")
        finally:
            session.close()
        p = self._mk_patient_at(SessionFactory())
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org",
                          "branch": None, "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(tok),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in",
                              "branch_id": "m5-branch-2"})
        assert r.status_code == 201, r.text
        s = SessionFactory()
        try:
            entry = s.query(QueueEntry).filter(
                QueueEntry.id == r.json()["id"]).one()
            assert entry.branch_id == "m5-branch-2"
            assert entry.organization_id == "m5-org"
        finally:
            s.close()


class TestQueueDoctorAssistantOwnership:
    """RBAC-R3: doctor ownership and assistant assignment scope."""

    def _mk_doctor(self, session, doctor_id, name, org_id="m5-org"):
        d = session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if d is None:
            d = Doctor(id=doctor_id, organization_id=org_id,
                       name=name, mobile=f"017{doctor_id[-4:]}00000")
            session.add(d)
            session.commit()
        return d

    def _mk_user_with_doctor(self, session, username, role, doctor_id,
                             org_id="m5-org", branch_id="m5-branch"):
        u = session.query(StaffUser).filter(
            StaffUser.username == username).first()
        if u is None:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=org_id,
                          branch_id=branch_id, doctor_id=doctor_id,
                          username=username, password_hash=pw,
                          display_name=username, role=role, status="active")
            session.add(u); session.commit()
        return u

    def _mk_patient_rbac_r3(self, session, org_id="m5-org"):
        p = Patient(id=str(uuid.uuid4()), organization_id=org_id,
                    name="RBAC-R3 Patient", mobile="01788888888")
        session.add(p); session.commit(); return p

    def _mk_appointment_rbac_r3(self, session, patient_id, doctor_id,
                                status="CONFIRMED"):
        a = Appointment(id=str(uuid.uuid4()),
            organization_id="m5-org", branch_id="m5-branch",
            patient_id=patient_id, doctor_id=doctor_id,
            appointment_date=date.today(), start_time="10:00",
            status=status, status_history=[], token_number="T-R3-001")
        session.add(a); session.commit(); return a

    def _enqueue_rbac_r3(self, patient_id, doctor_id, token,
                         entry_source="walk_in"):
        return client.post("/api/v1/queue/enqueue",
            headers=_auth(token),
            json={"doctor_id": doctor_id, "patient_id": patient_id,
                  "entry_source": entry_source})

    def test_rbac_r3_doctor_a_cannot_list_doctor_b_queue(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-a", "Doctor A")
            self._mk_doctor(session, "rbac-r3-doc-b", "Doctor B")
            user_a = self._mk_user_with_doctor(
                session, "rbacr3_doc_a", "doctor", "rbac-r3-doc-a")
            user_b = self._mk_user_with_doctor(
                session, "rbacr3_doc_b", "doctor", "rbac-r3-doc-b")
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-b")
            entry_b = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-b",
                _token(user_b, branch="m5-branch")).json()
            session.close()
        finally:
            session.close()

        tok_a = jwt.encode({"sub": user_a.id, "org": "m5-org",
                            "branch": "m5-branch", "role": "doctor",
                            "exp": int((datetime.now(timezone.utc)
                                        + timedelta(hours=1)).timestamp())},
                           _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=rbac-r3-doc-b&date={date.today().isoformat()}",
            headers=_auth(tok_a))
        assert r.status_code == 404, r.text

    def test_rbac_r3_doctor_a_can_list_own_queue(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-c", "Doctor C")
            user_c = self._mk_user_with_doctor(
                session, "rbacr3_doc_c", "doctor", "rbac-r3-doc-c")
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-c")
            entry_c = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-c",
                _token(user_c, branch="m5-branch")).json()
            session.close()
        finally:
            session.close()

        tok_c = jwt.encode({"sub": user_c.id, "org": "m5-org",
                            "branch": "m5-branch", "role": "doctor",
                            "exp": int((datetime.now(timezone.utc)
                                        + timedelta(hours=1)).timestamp())},
                           _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=rbac-r3-doc-c&date={date.today().isoformat()}",
            headers=_auth(tok_c))
        assert r.status_code == 200, r.text
        body = r.json()
        assert all(e["doctor_id"] == "rbac-r3-doc-c" for e in body["entries"])

    def test_rbac_r3_doctor_a_cannot_consult_doctor_b_entry(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-d", "Doctor D")
            self._mk_doctor(session, "rbac-r3-doc-e", "Doctor E")
            user_d = self._mk_user_with_doctor(
                session, "rbacr3_doc_d", "doctor", "rbac-r3-doc-d")
            user_e = self._mk_user_with_doctor(
                session, "rbacr3_doc_e", "doctor", "rbac-r3-doc-e")
            recp = self._mk_user_with_doctor(
                session, "rbacr3_recp", "receptionist", None)
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-e")
            r_e = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-e",
                _token(recp, branch="m5-branch"))
            assert r_e.status_code == 201, r_e.text
            entry_e = r_e.json()
            session.close()
        finally:
            session.close()

        tok_d = jwt.encode({"sub": user_d.id, "org": "m5-org",
                            "branch": "m5-branch", "role": "doctor",
                            "exp": int((datetime.now(timezone.utc)
                                        + timedelta(hours=1)).timestamp())},
                           _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/queue/{entry_e['id']}",
            headers=_auth(tok_d),
            json={"action": "start_consultation"})
        assert r.status_code == 404, r.text

    def test_rbac_r3_doctor_can_consult_own_entry(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-f", "Doctor F")
            user_f = self._mk_user_with_doctor(
                session, "rbacr3_doc_f", "doctor", "rbac-r3-doc-f")
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-f")
            recp_f = self._mk_user_with_doctor(
                session, "rbacr3_recp_f", "receptionist", None)
            r_f = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-f",
                _token(recp_f, branch="m5-branch"))
            assert r_f.status_code == 201, r_f.text
            entry_f = r_f.json()
        finally:
            session.close()

        tok_f = jwt.encode({"sub": user_f.id, "org": "m5-org",
                            "branch": "m5-branch", "role": "doctor",
                            "exp": int((datetime.now(timezone.utc)
                                        + timedelta(hours=1)).timestamp())},
                           _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/queue/{entry_f['id']}",
            headers=_auth(tok_f),
            json={"action": "start_consultation"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "in_consultation"
    def test_rbac_r3_assistant_can_access_assigned_doctor_queue(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-h", "Doctor H")
            user_h = self._mk_user_with_doctor(
                session, "rbacr3_doc_h", "doctor", "rbac-r3-doc-h")
            asst_h = self._mk_user_with_doctor(
                session, "rbacr3_asst_h", "assistant", "rbac-r3-doc-h")
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-h")
            entry_h = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-h",
                _token(user_h, branch="m5-branch")).json()
            session.close()
        finally:
            session.close()

        tok_asst_h = jwt.encode({"sub": asst_h.id, "org": "m5-org",
                                 "branch": "m5-branch", "role": "assistant",
                                 "exp": int((datetime.now(timezone.utc)
                                             + timedelta(hours=1)).timestamp())},
                                _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=rbac-r3-doc-h&date={date.today().isoformat()}",
            headers=_auth(tok_asst_h))
        assert r.status_code == 200, r.text
        body = r.json()
        assert all(e["doctor_id"] == "rbac-r3-doc-h" for e in body["entries"])

    def test_rbac_r3_assistant_cannot_perform_consultation(self):
        session = SessionFactory()
        try:
            self._mk_doctor(session, "rbac-r3-doc-i", "Doctor I")
            user_i = self._mk_user_with_doctor(
                session, "rbacr3_doc_i", "doctor", "rbac-r3-doc-i")
            asst_i = self._mk_user_with_doctor(
                session, "rbacr3_asst_i", "assistant", "rbac-r3-doc-i")
            recp_i = self._mk_user_with_doctor(
                session, "rbacr3_recp_i", "receptionist", None)
            p = self._mk_patient_rbac_r3(session)
            a = self._mk_appointment_rbac_r3(session, p.id, "rbac-r3-doc-i")
            r_i = self._enqueue_rbac_r3(p.id, "rbac-r3-doc-i",
                _token(recp_i, branch="m5-branch"))
            assert r_i.status_code == 201, r_i.text
            entry_i = r_i.json()
            session.close()
        finally:
            session.close()

        tok_asst_i = jwt.encode({"sub": asst_i.id, "org": "m5-org",
                                 "branch": "m5-branch", "role": "assistant",
                                 "exp": int((datetime.now(timezone.utc)
                                             + timedelta(hours=1)).timestamp())},
                                _SECRET, algorithm=_ALGO)
        r = client.patch(f"/api/v1/queue/{entry_i['id']}",
            headers=_auth(tok_asst_i),
            json={"action": "start_consultation"})
        assert r.status_code == 403, r.text