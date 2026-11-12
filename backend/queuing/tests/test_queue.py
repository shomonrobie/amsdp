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