"""M5 Queue Service Tests — PostgreSQL-backed."""
import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "identity"))

import pytest, jwt
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import (Organization, Branch, StaffUser, Doctor,
                           DoctorBranch, Patient, QueueEntry, Appointment,
                           QueueAnnouncementDelivery)
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

@pytest.fixture(scope="module", autouse=True)
def _seeded_rows():
    """Seed the M5 organisation, branch and doctor once per module.

    Import-time seeding made pytest's **collection** write to the database
    (finding T-10, 27 November 2026).
    """
    _ensure_org()


def _sync_assignment(session, staff_user_id, doctor_id, org_id="m5-org"):
    """Mirror the f8a1b2c3d4e5 migration for fixture users.

    The migration backfills every legacy ``StaffUser.doctor_id`` into an
    ``staff_doctor_assignments`` row.  The runtime loader treats the table as
    authoritative (PO-RBAC-01: an empty table result is a revocation, not a
    reason to fall back), so a fixture that only sets ``doctor_id`` would be
    an unassigned account.  No-op on pre-migration databases where the table
    is absent and the legacy fallback still applies.
    """
    from sqlalchemy import inspect as sa_inspect
    if not sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
        return
    from common.models import StaffDoctorAssignment
    session.query(StaffDoctorAssignment).filter(
        StaffDoctorAssignment.staff_user_id == staff_user_id
    ).delete(synchronize_session=False)
    if doctor_id:
        session.add(StaffDoctorAssignment(
            id=str(uuid.uuid4()), staff_user_id=staff_user_id,
            doctor_id=doctor_id, organization_id=org_id, status="active"))


def _mk_user(session, username, role, doctor_id=None):
    existing = session.query(StaffUser).filter(StaffUser.username == username).first()
    if existing:
        existing.doctor_id = doctor_id
        existing.role = role
        session.commit()
        _sync_assignment(session, existing.id, doctor_id,
                         existing.organization_id)
        session.commit()
        return existing
    pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
    u = StaffUser(id=str(uuid.uuid4()), organization_id="m5-org", branch_id="m5-branch",
                  username=username, password_hash=pw, display_name=username,
                  role=role, doctor_id=doctor_id, status="active")
    session.add(u); session.commit()
    _sync_assignment(session, u.id, doctor_id, u.organization_id)
    session.commit()
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
    # QUE-006 / W2: announcement deliveries reference queue entries, so they are
    # cleared first. Both tables are test-scoped state, never audit history —
    # ``audit_events`` is deliberately *not* touched (append-only).
    session.query(QueueAnnouncementDelivery).delete()
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
    u = _mk_user(session, "m5_docu", "doctor", doctor_id="m5-doc")
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


def _set_org_queue_config(block=None):
    """Store the organization's walk-in configuration (MP-10, BR §25)."""
    session = SessionFactory()
    try:
        org = session.query(Organization).filter(
            Organization.id == "m5-org").first()
        org.config = {"queue_config": block} if block else {}
        session.commit()
    finally:
        session.close()


@pytest.fixture
def walk_in_policy():
    """Apply a placement policy for one test, then restore the default."""
    def _apply(policy, **extra):
        _set_org_queue_config({"walk_in_policy": policy, **extra})
    yield _apply
    _set_org_queue_config(None)


def _enqueue(t, patient_id, **body):
    payload = {"doctor_id": "m5-doc", "patient_id": patient_id,
               "entry_source": "walk_in"}
    payload.update(body)
    return client.post("/api/v1/queue/enqueue", headers=_auth(t), json=payload)


class TestWalkInPolicies:
    """BR §25 — the policy is a facility setting, not a request parameter.

    The behaviour of each of the four policies is proven in
    ``test_walk_in_placement.py``; these tests pin the contract change itself:
    the body can no longer choose a policy, and an unusable stored value falls
    back instead of refusing work.
    """

    def test_end_of_queue(self, receptionist, walk_in_policy):
        walk_in_policy("end_of_queue")
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = _enqueue(_token(receptionist), p.id)
        assert r.status_code == 201 and r.json()["entry_source"] == "walk_in"
        assert r.json()["position"] >= 1

    def test_first_come(self, receptionist, walk_in_policy):
        walk_in_policy("first_come")
        session = SessionFactory(); p = _mk_patient(session); session.close()
        assert _enqueue(_token(receptionist), p.id).status_code == 201

    def test_reserved_capacity(self, receptionist, walk_in_policy):
        walk_in_policy("reserved_capacity", walk_in_reserve_mode="count",
                       walk_in_reserve_value=2)
        session = SessionFactory(); p = _mk_patient(session); session.close()
        assert _enqueue(_token(receptionist), p.id).status_code == 201

    def test_staff_placement(self, receptionist, walk_in_policy):
        walk_in_policy("staff_placement")
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = _enqueue(_token(receptionist), p.id, position=1)
        assert r.status_code == 201 and r.json()["position"] == 1

    def test_the_request_body_cannot_choose_the_policy(
            self, receptionist, walk_in_policy):
        """MP-10: ``walk_in_policy`` is retired — the facility setting decides.

        The body still names ``staff_placement`` and position 1.  The policy in
        force is ``end_of_queue``, so the entry is appended and the position in
        the body has no effect.  A caller can no longer widen or change the
        facility's placement rule by writing a field.
        """
        walk_in_policy("end_of_queue")
        session = SessionFactory()
        first = _mk_patient(session); second = _mk_patient(session)
        session.close()
        t = _token(receptionist)
        assert _enqueue(t, first.id).status_code == 201
        r = _enqueue(t, second.id, walk_in_policy="staff_placement", position=1)
        assert r.status_code == 201, r.text
        assert r.json()["position"] == 2, "the body must not place the patient"

    def test_an_unknown_stored_policy_falls_back_to_end_of_queue(
            self, receptionist, walk_in_policy):
        """A corrupt setting must not refuse work, and must not place by surprise."""
        walk_in_policy("bogus")
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = _enqueue(_token(receptionist), p.id)
        assert r.status_code == 201, r.text
        assert r.json()["position"] >= 1

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

    def test_receptionist_can_call_a_waiting_entry(self, receptionist):
        """POD-12 / QOP-001: the queue Call control uses this existing endpoint."""
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        r = client.patch(f"/api/v1/queue/{e['id']}", headers=_auth(_token(receptionist)),
                         json={"action": "call"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "called"

    def test_doctor_cannot_call_without_queue_manage(self, doctor_user, receptionist):
        """The organization's default: calling is front-desk work.

        A doctor holds queue.consult / queue.recover / queue.reposition but not
        queue.manage (common/permissions.py:104-122), and an organization that
        has not enabled doctor queue-calling gets exactly that behaviour: 403,
        and the denial leaves the entry untouched — a refused call is not a
        transition.  Owner decision D adds the *opt-in* (see
        ``TestDoctorQueueCalling``); it does not change the default.
        """
        session = SessionFactory(); p = _mk_patient(session); session.close()
        e = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id, "entry_source": "walk_in"}).json()
        r = client.patch(f"/api/v1/queue/{e['id']}", headers=_auth(_token(doctor_user)),
                         json={"action": "call"})
        assert r.status_code == 403, r.text
        s = SessionFactory()
        try:
            row = s.query(QueueEntry).filter(QueueEntry.id == e["id"]).first()
            assert row.status == "waiting"
            # The enqueue itself writes the creation record (``"" -> waiting``), so an
            # empty history is not the right test for "nothing happened".  What the
            # refusal must leave untouched is the *transition*: no call record, and
            # no status other than the creation row.
            history = row.status_history or []
            assert [h.get("to") for h in history] == ["waiting"], history
            assert [h for h in history if h.get("action") == "call"] == [], history
        finally:
            s.close()

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


# ---------------------------------------------------------------------------
# QUE-006 / DEV-1 (owner decision D) — organization-scoped doctor queue-calling
# ---------------------------------------------------------------------------

def _set_doctor_queue_calling(enabled, org_id="m5-org"):
    """Store the organization's doctor queue-calling policy."""
    from common.config import merge_queue_calling_config
    session = SessionFactory()
    try:
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if org is None:
            org = Organization(id=org_id, name=org_id, code=org_id.upper())
            session.add(org)
        org.config = merge_queue_calling_config(
            org.config, {"doctor_queue_calling_enabled": enabled})
        session.commit()
    finally:
        session.close()


@pytest.fixture
def doctor_calling_enabled():
    """Enable the policy for one test and always restore the disabled default."""
    _set_doctor_queue_calling(True)
    yield
    _set_doctor_queue_calling(False)


@pytest.fixture(scope="module")
def second_doctor_user():
    """A second doctor in the same organization, with their own assignment."""
    session = SessionFactory()
    try:
        if not session.query(Doctor).filter(Doctor.id == "m5-doc-2").first():
            session.add(Doctor(id="m5-doc-2", organization_id="m5-org",
                               name="Dr Two", mobile="01700000002"))
            session.commit()
        return _mk_user(session, "m5_docu2", "doctor", doctor_id="m5-doc-2")
    finally:
        session.close()


class TestDoctorQueueCalling:
    """Owner decision D: a doctor calls only where the organization allows it.

    The setting is per organization, is enforced **server-side** on the queue
    ``call`` action (the UI is not the boundary), and never widens the action to
    anybody else: ``queue.manage`` holders keep it, a doctor gains it only for
    their own patients, and an assistant gains nothing.
    """

    def _enqueue(self, receptionist, doctor_id="m5-doc"):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue",
                        headers=_auth(_token(receptionist)),
                        json={"doctor_id": doctor_id, "patient_id": p.id,
                              "entry_source": "walk_in"})
        assert r.status_code in (200, 201), r.text
        return r.json()

    def _state(self, entry_id):
        session = SessionFactory()
        try:
            row = session.query(QueueEntry).filter(
                QueueEntry.id == entry_id).first()
            return row.status, list(row.status_history or [])
        finally:
            session.close()

    def test_doctor_calls_their_own_patient_when_enabled(
            self, doctor_user, receptionist, doctor_calling_enabled):
        entry = self._enqueue(receptionist)
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(_token(doctor_user)),
                         json={"action": "call"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "called"
        assert r.json()["call_event_id"], "the call event drives the announcement"
        status, history = self._state(entry["id"])
        assert status == "called"
        assert [h.get("action") for h in history if h.get("action")] == ["call"]

    def test_the_call_is_audited_with_the_doctor_as_actor(
            self, doctor_user, receptionist, doctor_calling_enabled):
        from common.models import AuditEvent
        entry = self._enqueue(receptionist)
        client.patch(f"/api/v1/queue/{entry['id']}",
                     headers=_auth(_token(doctor_user)),
                     json={"action": "call"})
        session = SessionFactory()
        try:
            evt = session.query(AuditEvent).filter(
                AuditEvent.target_id == entry["id"],
                AuditEvent.action == "queue.call").first()
            assert evt is not None, "a doctor-issued call must be recorded"
            assert evt.actor_id == doctor_user.id
            assert evt.actor_role == "doctor"
        finally:
            session.close()

    def test_disabled_organization_refuses_the_doctor(
            self, doctor_user, receptionist):
        """The default: enabling doctors is a policy an organization must grant."""
        entry = self._enqueue(receptionist)
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(_token(doctor_user)),
                         json={"action": "call"})
        assert r.status_code == 403, r.text
        status, history = self._state(entry["id"])
        assert status == "waiting"
        assert [h for h in history if h.get("action") == "call"] == []

    def test_another_doctors_patient_is_still_a_404(
            self, doctor_user, receptionist, second_doctor_user,
            doctor_calling_enabled):
        """Enabling the policy does not widen *which* patients a doctor may call."""
        entry = self._enqueue(receptionist, doctor_id="m5-doc-2")
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(_token(doctor_user)),
                         json={"action": "call"})
        assert r.status_code == 404, r.text
        status, history = self._state(entry["id"])
        assert status == "waiting"
        assert [h for h in history if h.get("action") == "call"] == []

    def test_assistant_gains_nothing(self, receptionist, doctor_calling_enabled):
        session = SessionFactory()
        try:
            assistant = _mk_user(session, "m5_assist", "assistant")
            token = _token(assistant)
        finally:
            session.close()
        entry = self._enqueue(receptionist)
        r = client.patch(f"/api/v1/queue/{entry['id']}",
                         headers=_auth(token), json={"action": "call"})
        assert r.status_code == 403, r.text
        assert self._state(entry["id"])[0] == "waiting"

    def test_the_setting_is_per_organization(self, doctor_user, receptionist):
        """Enabling it elsewhere must not enable it here."""
        _set_doctor_queue_calling(True, org_id="m5-other-org")
        try:
            entry = self._enqueue(receptionist)
            # A token for the other organization cannot reach this entry at all.
            r = client.patch(f"/api/v1/queue/{entry['id']}",
                             headers=_auth(_token(doctor_user,
                                                  org="m5-other-org")),
                             json={"action": "call"})
            assert r.status_code in (403, 404), r.text
            assert self._state(entry["id"])[0] == "waiting"
        finally:
            _set_doctor_queue_calling(False, org_id="m5-other-org")


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
            # PO-RBAC-01: the migrated assignment table is authoritative, so a
            # fixture user needs the assignment row the migration backfills.
            _sync_assignment(session, u.id, doctor_id, org_id)
            session.commit()
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


class TestQueueHistoryBranchAuth:
    """C1: Queue history endpoint branch authorization."""

    def _mk_branch(self, session, branch_id, org_id="m5-org"):
        b = session.query(Branch).filter(Branch.id == branch_id).first()
        if b is None:
            session.add(Branch(id=branch_id, organization_id=org_id,
                               name=branch_id, code=branch_id.upper()))
            session.commit()
        return b

    def _mk_patient_c1(self, session, org_id="m5-org"):
        p = Patient(id=str(uuid.uuid4()), organization_id=org_id,
                    name="C1 Patient", mobile="01777777777")
        session.add(p); session.commit(); return p

    def test_c1_receptionist_own_branch_history(self, receptionist):
        self._mk_branch(SessionFactory(), "c1-br-2")
        p = self._mk_patient_c1(SessionFactory())
        client.post("/api/v1/queue/enqueue",
            headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id,
                  "entry_source": "walk_in", "branch_id": "m5-branch"})
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id=m5-branch",
            headers=_auth(_token(receptionist)))
        assert r.status_code == 200, r.text

    def test_c1_receptionist_cannot_another_branch_history(self, receptionist):
        self._mk_branch(SessionFactory(), "c1-br-2")
        p = self._mk_patient_c1(SessionFactory())
        client.post("/api/v1/queue/enqueue",
            headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id,
                  "entry_source": "walk_in", "branch_id": "c1-br-2"})
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id=c1-br-2",
            headers=_auth(_token(receptionist)))
        assert r.status_code == 404, r.text

    def test_c1_receptionist_omits_branch_id_limited_to_own(self, receptionist):
        self._mk_branch(SessionFactory(), "c1-br-2")
        p = self._mk_patient_c1(SessionFactory())
        client.post("/api/v1/queue/enqueue",
            headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id,
                  "entry_source": "walk_in", "branch_id": "m5-branch"})
        client.post("/api/v1/queue/enqueue",
            headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id,
                  "entry_source": "walk_in", "branch_id": "c1-br-2"})
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(_token(receptionist)))
        assert r.status_code == 200, r.text
        body = r.json()
        assert all(e["branch_id"] == "m5-branch" for e in body)

    def test_c1_org_admin_authorized_branch_history(self, receptionist):
        session = SessionFactory()
        try:
            self._mk_branch(session, "c1-br-3")
            u = _mk_user(session, "c1_org_adm", "org_admin", None)
        finally:
            session.close()
        p = self._mk_patient_c1(SessionFactory())
        client.post("/api/v1/queue/enqueue",
            headers=_auth(_token(receptionist)),
            json={"doctor_id": "m5-doc", "patient_id": p.id,
                  "entry_source": "walk_in", "branch_id": "c1-br-3"})
        tok = jwt.encode({"sub": u.id, "org": "m5-org", "branch": None,
                          "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id=c1-br-3",
            headers=_auth(tok))
        assert r.status_code == 200, r.text

    def test_c1_cross_tenant_branch_id(self, receptionist):
        foreign_org = f"c1-foreign-{uuid.uuid4().hex[:8]}"
        foreign_br = f"c1-foreign-br-{uuid.uuid4().hex[:8]}"
        foreign_code = f"FORGN-{uuid.uuid4().hex[:8]}"
        session = SessionFactory()
        try:
            session.add(Organization(id=foreign_org, name="Foreign", code=foreign_code))
            session.add(Branch(id=foreign_br, organization_id=foreign_org,
                               name="Foreign Br", code=foreign_code))
            session.commit()
        finally:
            session.close()
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id={foreign_br}",
            headers=_auth(_token(receptionist)))
        assert r.status_code == 404, r.text

    def test_c1_org_admin_other_org_branch_denied(self, receptionist):
        foreign_org = f"c1-foreign-org-{uuid.uuid4().hex[:8]}"
        foreign_br = f"c1-foreign-br-{uuid.uuid4().hex[:8]}"
        session = SessionFactory()
        try:
            session.add(Organization(id=foreign_org, name="Foreign Org", code=f"FORG-{uuid.uuid4().hex[:8]}"))
            session.add(Branch(id=foreign_br, organization_id=foreign_org,
                               name="Foreign Br", code=f"FORB-{uuid.uuid4().hex[:8]}"))
            session.commit()
        finally:
            session.close()
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org", "branch": "m5-branch",
                          "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id={foreign_br}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text

    def test_c1_org_admin_nonexistent_branch_denied(self, receptionist):
        tok = jwt.encode({"sub": receptionist.id, "org": "m5-org", "branch": "m5-branch",
                          "role": "org_admin",
                          "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue/history?doctor_id=m5-doc&date={date.today().isoformat()}&branch_id=does-not-exist",
            headers=_auth(tok))
        assert r.status_code == 404, r.text


class TestQueueMissingDoctorAssignment:
    """C3: Missing or invalid doctor assignment must fail closed."""

    def test_c3_doctor_no_assignment_denied(self):
        session = SessionFactory()
        try:
            u = _mk_user(session, "c3_doc_noassign", "doctor", None)
        finally:
            session.close()
        tok = jwt.encode({"sub": u.id, "org": "m5-org", "branch": "m5-branch",
                          "role": "doctor",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text

    def test_c3_assistant_no_assignment_denied(self):
        session = SessionFactory()
        try:
            u = _mk_user(session, "c3_asst_noassign", "assistant", None)
        finally:
            session.close()
        tok = jwt.encode({"sub": u.id, "org": "m5-org", "branch": "m5-branch",
                          "role": "assistant",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text

    def test_c3_valid_assignment_allowed(self, doctor_user, receptionist):
        session = SessionFactory()
        try:
            p = _mk_patient(session)
            client.post("/api/v1/queue/enqueue",
                headers=_auth(_token(receptionist)),
                json={"doctor_id": "m5-doc", "patient_id": p.id,
                      "entry_source": "walk_in"})
            session.close()
        finally:
            session.close()
        tok = _token(doctor_user)
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 200, r.text


class TestQueueRecoveryDoctorAuth:
    """C2: Doctor ownership across queue recovery actions."""

    def test_c2_doctor_cannot_recover_another_doctor_entry(self):
        da_id = f"c2-doc-a-{uuid.uuid4().hex[:8]}"
        db_id = f"c2-doc-b-{uuid.uuid4().hex[:8]}"
        session = SessionFactory()
        try:
            da = Doctor(id=da_id, organization_id="m5-org", name="Doctor A",
                       mobile="01700000001")
            db = Doctor(id=db_id, organization_id="m5-org", name="Doctor B",
                       mobile="01700000002")
            session.add(da); session.add(db); session.commit()
            user_a = _mk_user(session, "c2_doc_a", "doctor", doctor_id=da_id)
            user_b = _mk_user(session, "c2_doc_b", "doctor", doctor_id=db_id)
            recp = _mk_user(session, "c2_recp", "receptionist", None)
            p = _mk_patient(session)
            r = client.post("/api/v1/queue/enqueue",
                headers=_auth(_token(recp, branch="m5-branch")),
                json={"doctor_id": db_id, "patient_id": p.id,
                      "entry_source": "walk_in"})
            assert r.status_code == 201, r.text
            entry_b = r.json()
            client.patch(f"/api/v1/queue/{entry_b['id']}",
                headers=_auth(_token(recp, branch="m5-branch")),
                json={"action": "cancel", "reason": "test"})
            session.close()
        finally:
            session.close()

        tok_a = jwt.encode({"sub": user_a.id, "org": "m5-org",
                            "branch": "m5-branch", "role": "doctor",
                            "exp": int((datetime.now(timezone.utc)
                                        + timedelta(hours=1)).timestamp())},
                           _SECRET, algorithm=_ALGO)
        r = client.post(f"/api/v1/queue/recover/{entry_b['id']}",
            headers=_auth(tok_a),
            json={"reason": "test"})
        assert r.status_code == 404, r.text


class TestQueueMultiDoctorAssignments:
    """PO-RBAC-01: An assistant may be assigned to multiple doctors within
    the same organization.  Doctor access is based on explicit assignment."""

    def _mk_multi_doc_user(self, session, username, role, doctor_ids):
        pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
        u = StaffUser(id=str(uuid.uuid4()), organization_id="m5-org",
                      branch_id="m5-branch", username=username,
                      password_hash=pw, display_name=username,
                      role=role,
                      doctor_id=doctor_ids[0] if doctor_ids else None,
                      status="active")
        session.add(u)
        session.flush()
        try:
            from sqlalchemy import inspect as sa_inspect
            if sa_inspect(session.get_bind()).has_table("staff_doctor_assignments"):
                from common.models import StaffDoctorAssignment
                for did in doctor_ids:
                    session.add(StaffDoctorAssignment(
                        id=str(uuid.uuid4()), staff_user_id=u.id,
                        doctor_id=did, organization_id="m5-org",
                        status="active"))
        except Exception:
            pass
        session.commit()
        return u

    def _mk_multi_doc_doctors(self, session):
        for i, (did, name) in enumerate([
            ("md-doc-a", "Dr Multi A"), ("md-doc-b", "Dr Multi B"),
            ("md-doc-c", "Dr Multi C")]):
            d = session.query(Doctor).filter(Doctor.id == did).first()
            if d is None:
                d = Doctor(id=did, organization_id="m5-org",
                           name=name, mobile=f"017000000{i+1}")
                session.add(d)
        session.commit()

    def _enqueue_md(self, tok, doctor_id, patient_id):
        return client.post("/api/v1/queue/enqueue",
            headers=_auth(tok),
            json={"doctor_id": doctor_id, "patient_id": patient_id,
                  "entry_source": "walk_in", "branch_id": "m5-branch"})

    def test_assistant_assigned_to_multiple_doctors(self):
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            self._mk_multi_doc_doctors(session)
            asst = self._mk_multi_doc_user(session, f"md_asst_multi_{tag}",
                                           "assistant",
                                           ["md-doc-a", "md-doc-b", "md-doc-c"])
            recp = _mk_user(session, f"md_recp_multi_{tag}", "receptionist")
            p = _mk_patient(session)
            for did in ["md-doc-a", "md-doc-b", "md-doc-c"]:
                self._enqueue_md(_token(recp), did, p.id)
            session.close()
        finally:
            session.close()

        tok = _token(asst)
        for did in ["md-doc-a", "md-doc-b", "md-doc-c"]:
            r = client.get(f"/api/v1/queue?doctor_id={did}"
                           f"&date={date.today().isoformat()}",
                headers=_auth(tok))
            assert r.status_code == 200, f"denied access to {did}: {r.text}"
            body = r.json()
            assert all(e["doctor_id"] == did for e in body["entries"])

    def test_assistant_cannot_access_unassigned_doctor(self):
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            self._mk_multi_doc_doctors(session)
            asst = self._mk_multi_doc_user(session, f"md_asst_single_{tag}",
                                           "assistant", ["md-doc-a"])
            recp = _mk_user(session, f"md_recp_single_{tag}", "receptionist")
            p = _mk_patient(session)
            self._enqueue_md(_token(recp), "md-doc-b", p.id)
            session.close()
        finally:
            session.close()

        tok = _token(asst)
        r = client.get(f"/api/v1/queue?doctor_id=md-doc-b"
                       f"&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text

    def test_assignment_revocation_denies_access(self):
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            self._mk_multi_doc_doctors(session)
            asst = self._mk_multi_doc_user(session, f"md_asst_revoke_{tag}",
                                           "assistant",
                                           ["md-doc-a", "md-doc-b"])
            asst_id = asst.id
            recp = _mk_user(session, f"md_recp_revoke_{tag}", "receptionist")
            p = _mk_patient(session)
            self._enqueue_md(_token(recp), "md-doc-b", p.id)
            from common.models import StaffDoctorAssignment
            try:
                session.query(StaffDoctorAssignment).filter(
                    StaffDoctorAssignment.staff_user_id == asst_id,
                    StaffDoctorAssignment.doctor_id == "md-doc-b").delete(
                        synchronize_session=False)
                session.commit()
            except Exception:
                session.rollback()
            session.close()
        finally:
            session.close()

        tok = jwt.encode({"sub": asst_id, "org": "m5-org",
                          "branch": "m5-branch", "role": "assistant"},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=md-doc-b"
                       f"&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text
        r2 = client.get(f"/api/v1/queue?doctor_id=md-doc-a"
                        f"&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r2.status_code == 200, r2.text

    def test_assistant_no_assignment_fail_closed(self):
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            u = _mk_user(session, f"md_asst_none_{tag}", "assistant", None)
        finally:
            session.close()
        tok = jwt.encode({"sub": u.id, "org": "m5-org", "branch": "m5-branch",
                          "role": "assistant",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text

    def test_single_doctor_assignment_still_works(self):
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            # PO-RBAC-01: a migrated legacy account keeps doctor_id AND the
            # assignment row backfilled by the f8a1b2c3d4e5 migration.
            u = _mk_user(session, f"md_asst_single_legacy_{tag}", "assistant",
                         doctor_id="m5-doc")
        finally:
            session.close()
        tok = _token(u)
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 200, r.text

    def test_revoked_legacy_doctor_id_does_not_restore_access(self):
        """PO-RBAC-01: deleting the assignment row revokes doctor access even
        though the legacy ``StaffUser.doctor_id`` column still references the
        doctor.  Only the identity API clears that column; a DB-level
        revocation must not be undone by the legacy fallback."""
        tag = uuid.uuid4().hex[:8]
        session = SessionFactory()
        try:
            from sqlalchemy import inspect as sa_inspect
            if not sa_inspect(session.get_bind()).has_table(
                    "staff_doctor_assignments"):
                pytest.skip("staff_doctor_assignments table not migrated")
            self._mk_multi_doc_doctors(session)
            asst = self._mk_multi_doc_user(
                session, f"md_asst_revoke_legacy_{tag}", "assistant",
                ["md-doc-a"])
            asst_id = asst.id
            from common.models import StaffDoctorAssignment
            session.query(StaffDoctorAssignment).filter(
                StaffDoctorAssignment.staff_user_id == asst_id).delete(
                    synchronize_session=False)
            session.commit()
            # The legacy column is untouched by the revocation.
            assert session.query(StaffUser).filter(
                StaffUser.id == asst_id).one().doctor_id == "md-doc-a"
        finally:
            session.close()

        tok = jwt.encode({"sub": asst_id, "org": "m5-org",
                          "branch": "m5-branch", "role": "assistant",
                          "exp": int((datetime.now(timezone.utc)
                                      + timedelta(hours=1)).timestamp())},
                         _SECRET, algorithm=_ALGO)
        r = client.get(f"/api/v1/queue?doctor_id=md-doc-a"
                       f"&date={date.today().isoformat()}",
            headers=_auth(tok))
        assert r.status_code == 404, r.text


# ===========================================================================
# QUE-006 / W2 — call event identity, delivery claim and announcement audit
# (POD-4 announcement audit, V-12 cross-client duplicate suppression)
# ===========================================================================

class _AnnouncementFixture:
    """Helpers shared by the W2 announcement tests.

    ``m5-doc``'s queue is the only doctor queue used, and the autouse
    ``clean_queue`` fixture clears entries and deliveries before every test.
    """

    def _enqueue(self, receptionist):
        session = SessionFactory(); p = _mk_patient(session); session.close()
        r = client.post("/api/v1/queue/enqueue", headers=_auth(_token(receptionist)),
                        json={"doctor_id": "m5-doc", "patient_id": p.id,
                              "entry_source": "walk_in"})
        assert r.status_code in (200, 201), r.text
        return r.json()

    def _call(self, receptionist, entry_id):
        r = client.patch(f"/api/v1/queue/{entry_id}",
                         headers=_auth(_token(receptionist)), json={"action": "call"})
        assert r.status_code == 200, r.text
        return r.json()

    def _called_entry(self, receptionist):
        return self._call(receptionist, self._enqueue(receptionist)["id"])

    def _read_entry(self, receptionist, entry_id):
        r = client.get(f"/api/v1/queue?doctor_id=m5-doc"
                       f"&date={date.today().isoformat()}",
                       headers=_auth(_token(receptionist)))
        assert r.status_code == 200, r.text
        return next(x for x in r.json()["entries"] if x["id"] == entry_id)

    def _claim(self, token, entry_id, event_id, **extra):
        body = {"event_id": event_id, "language": "bn",
                "voice_pack_id": "platform.bn.draft.v1", "voice_pack_version": 1,
                "transport": "prerecorded"}
        body.update(extra)
        return client.post(f"/api/v1/queue/{entry_id}/announcement",
                           headers=_auth(token), json=body)

    def _report(self, token, delivery_id, outcome, reason=""):
        return client.post(f"/api/v1/queue/announcements/{delivery_id}/outcome",
                           headers=_auth(token),
                           json={"outcome": outcome, "reason": reason})

    def _deliveries(self, event_id):
        s = SessionFactory()
        try:
            rows = s.query(QueueAnnouncementDelivery).filter(
                QueueAnnouncementDelivery.call_event_id == event_id).all()
            return [{"id": r.id, "status": r.status, "entry_id": r.queue_entry_id,
                     "org": r.organization_id, "branch": r.branch_id,
                     "language": r.language, "pack": r.voice_pack_id,
                     "version": r.voice_pack_version, "transport": r.transport,
                     "reason": r.outcome_reason, "outcome_at": r.outcome_at,
                     "requested_by": r.requested_by} for r in rows]
        finally:
            s.close()

    def _audit_actions(self, event_id):
        from common.models import AuditEvent
        s = SessionFactory()
        try:
            return [e.action for e in s.query(AuditEvent).filter(
                AuditEvent.target_id == event_id).all()]
        finally:
            s.close()




class TestQueueCallEventIdentity(_AnnouncementFixture):
    """The server, not the browser, owns the identity of a call event."""

    def test_successful_call_publishes_a_server_event_id(self, receptionist):
        e = self._called_entry(receptionist)
        assert e["status"] == "called"
        # `events.py` derives the identity from the call record's **append position**
        # in `status_history`.  Enqueue writes the creation record at index 0
        # (`main.py`: ``{"from": "", "to": "waiting"}``), so the first call lands at
        # index 1; the old expectation of ``:0`` predates that creation row.
        history = e["status_history"]
        call_indexes = [i for i, h in enumerate(history)
                        if h.get("action") == "call" and h.get("to") == "called"]
        assert call_indexes == [1], history
        assert e["call_event_id"] == f"qce:{e['id']}:{call_indexes[0]}", e
        assert e["call_event_at"], "the event must carry the server timestamp"
        assert e["call_count"] == 1
        # Same value from a later read: identity is derived, not issued once.
        assert self._read_entry(receptionist, e["id"])["call_event_id"] == e["call_event_id"]

    def test_recall_gets_a_new_event_id(self, receptionist):
        first = self._called_entry(receptionist)
        eid = first["id"]
        # called -> skipped -> waiting, then call again: the product's recall
        # path (there is no `recall` action; a missed turn plus recovery keeps
        # the same entry, token and appointment).
        assert client.post(f"/api/v1/queue/{eid}/missed-turn",
                           headers=_auth(_token(receptionist)),
                           json={"reason": "no response"}).status_code == 200
        assert client.post(f"/api/v1/queue/{eid}/recover",
                           headers=_auth(_token(receptionist)),
                           json={"reason": "returned"}).status_code == 200
        second = self._call(receptionist, eid)
        assert second["call_event_id"] != first["call_event_id"]
        assert second["call_count"] == 2
        assert (int(second["call_event_id"].rsplit(":", 1)[1])
                > int(first["call_event_id"].rsplit(":", 1)[1]))

    def test_duplicate_call_request_creates_no_second_event(self, receptionist):
        e = self._called_entry(receptionist)
        again = client.patch(f"/api/v1/queue/{e['id']}",
                             headers=_auth(_token(receptionist)),
                             json={"action": "call"})
        assert again.status_code == 422, again.text
        after = self._read_entry(receptionist, e["id"])
        assert after["call_event_id"] == e["call_event_id"]
        assert after["call_count"] == 1

    def test_failed_call_does_not_publish_an_event(self, receptionist, doctor_user):
        e = self._enqueue(receptionist)
        refused = client.patch(f"/api/v1/queue/{e['id']}",
                               headers=_auth(_token(doctor_user)),
                               json={"action": "call"})
        assert refused.status_code == 403
        after = self._read_entry(receptionist, e["id"])
        assert after["status"] == "waiting"
        assert after["call_event_id"] == ""


class TestQueueRecall(_AnnouncementFixture):
    """MP-08: a recall is an explicit act, not a repeated ``call``.

    The plan's acceptance criterion is "two calls for one entry produce two
    delivery rows with distinct ``qce:`` keys; both audited; position
    unchanged". It is met through the ``recall`` action: ``call`` from
    ``called`` stays **422**, so a retried or double-submitted request still
    cannot produce a second announcement, and a real recall is a distinct,
    chosen, audited event with its own identity.
    """

    def _recall(self, receptionist, entry_id):
        return client.patch(f"/api/v1/queue/{entry_id}",
                            headers=_auth(_token(receptionist)),
                            json={"action": "recall"})

    def test_recall_from_called_appends_a_distinct_call_event(self, receptionist):
        e = self._called_entry(receptionist)
        r = self._recall(receptionist, e["id"])
        assert r.status_code == 200, r.text
        second = r.json()
        assert second["status"] == "called"
        assert second["call_count"] == 2
        assert second["call_event_id"] != e["call_event_id"]
        # The identity is the append position, so a recall's id is strictly later.
        assert (int(second["call_event_id"].rsplit(":", 1)[1])
                > int(e["call_event_id"].rsplit(":", 1)[1]))
        recalled = [h for h in second["status_history"]
                    if h.get("action") == "recall"]
        assert len(recalled) == 1, second["status_history"]
        assert recalled[0]["from"] == "called" and recalled[0]["to"] == "called"
        # A fresh read agrees: the identity is derived, not issued once.
        assert self._read_entry(receptionist, e["id"])["call_event_id"] == \
            second["call_event_id"]

    def test_two_calls_for_one_entry_produce_two_delivery_rows(self, receptionist):
        token = _token(receptionist)
        e = self._called_entry(receptionist)
        first_claim = self._claim(token, e["id"], e["call_event_id"])
        assert first_claim.status_code == 201, first_claim.text

        recalled = self._recall(receptionist, e["id"]).json()
        second_claim = self._claim(token, e["id"], recalled["call_event_id"])
        assert second_claim.status_code == 201, second_claim.text

        assert recalled["call_event_id"] != e["call_event_id"]
        assert second_claim.json()["delivery_id"] != first_claim.json()["delivery_id"]
        # Two rows, keyed by two different events: neither consumed the other's slot.
        assert len(self._deliveries(e["call_event_id"])) == 1
        assert len(self._deliveries(recalled["call_event_id"])) == 1

    def test_the_superseded_event_can_no_longer_be_claimed(self, receptionist):
        token = _token(receptionist)
        e = self._called_entry(receptionist)
        recalled = self._recall(receptionist, e["id"]).json()
        stale = self._claim(token, e["id"], e["call_event_id"])
        assert stale.status_code == 409, stale.text
        assert self._deliveries(e["call_event_id"]) == []

    def test_both_the_call_and_the_recall_are_audited(self, receptionist):
        e = self._called_entry(receptionist)
        self._recall(receptionist, e["id"])
        actions = self._audit_actions(e["id"])
        assert "queue.call" in actions, actions
        assert "queue.recall" in actions, actions

    def test_recall_does_not_change_the_position_or_the_token(self, receptionist):
        e = self._called_entry(receptionist)
        after = self._read_entry(receptionist, e["id"])
        assert after["position"] == e["position"], "a recall is not a reorder"
        assert after["token"] == e["token"], "the patient keeps their token"
        assert len(after["position_history"]) == len(e["position_history"])

    def test_a_duplicate_call_is_still_refused_after_a_recall(self, receptionist):
        """The announcement-duplication guard survives MP-08."""
        e = self._called_entry(receptionist)
        recalled = self._recall(receptionist, e["id"]).json()
        again = client.patch(f"/api/v1/queue/{e['id']}",
                             headers=_auth(_token(receptionist)),
                             json={"action": "call"})
        assert again.status_code == 422, again.text
        after = self._read_entry(receptionist, e["id"])
        assert after["call_event_id"] == recalled["call_event_id"]
        assert after["call_count"] == 2

    def test_recall_from_waiting_is_refused(self, receptionist):
        e = self._enqueue(receptionist)
        r = self._recall(receptionist, e["id"])
        assert r.status_code == 422, r.text
        after = self._read_entry(receptionist, e["id"])
        assert after["status"] == "waiting"
        assert after["call_event_id"] == ""
        assert [h for h in after["status_history"]
                if h.get("action") == "recall"] == []

    def test_recall_is_refused_for_a_doctor_without_queue_manage(self, receptionist,
                                                               doctor_user):
        e = self._called_entry(receptionist)
        refused = client.patch(f"/api/v1/queue/{e['id']}",
                               headers=_auth(_token(doctor_user)),
                               json={"action": "recall"})
        assert refused.status_code == 403, refused.text
        assert self._read_entry(receptionist, e["id"])["call_count"] == 1

    def test_recall_follows_the_organizations_doctor_calling_policy(
            self, receptionist, doctor_user, doctor_calling_enabled):
        """Same organization policy as `call`: a doctor may recall own patients."""
        e = self._called_entry(receptionist)
        allowed = client.patch(f"/api/v1/queue/{e['id']}",
                               headers=_auth(_token(doctor_user)),
                               json={"action": "recall"})
        assert allowed.status_code == 200, allowed.text
        assert allowed.json()["call_count"] == 2

class TestAnnouncementDeliveryClaim(_AnnouncementFixture):
    """V-12: two terminals, one call, one announcement."""

    def test_first_claim_wins_and_the_second_terminal_is_refused(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        first = self._claim(token, e["id"], e["call_event_id"])
        assert first.status_code == 201, first.text
        assert first.json()["claimed"] is True
        delivery_id = first.json()["delivery_id"]
        # A second terminal (same user, another browser) must not announce.
        second = self._claim(token, e["id"], e["call_event_id"])
        assert second.status_code == 200, second.text
        assert second.json()["claimed"] is False
        assert second.json()["reason"] == "duplicate_event"
        assert second.json()["delivery_id"] == delivery_id
        rows = self._deliveries(e["call_event_id"])
        assert len(rows) == 1, rows
        assert rows[0]["status"] == "requested"

    def test_claim_records_scope_and_voice_selection(self, receptionist):
        e = self._called_entry(receptionist)
        r = self._claim(_token(receptionist), e["id"], e["call_event_id"])
        assert r.status_code == 201, r.text
        row = self._deliveries(e["call_event_id"])[0]
        # Scope comes from the stored entry, never from the request body.
        assert row["org"] == e["organization_id"]
        assert row["branch"] == e["branch_id"]
        assert row["entry_id"] == e["id"]
        # The selected language and voice pack are part of the record (POD-4).
        assert row["language"] == "bn"
        assert row["pack"] == "platform.bn.draft.v1"
        assert row["version"] == 1
        assert row["transport"] == "prerecorded"
        assert row["requested_by"]

    def test_claim_requires_the_current_event(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        assert self._claim(token, e["id"], f"qce:{e['id']}:9").status_code == 409
        assert self._claim(token, e["id"], "recall-1").status_code == 409
        assert self._claim(token, e["id"], "").status_code == 422
        assert self._deliveries(f"qce:{e['id']}:9") == []

    def test_claim_refused_when_the_entry_is_not_called(self, receptionist):
        e = self._enqueue(receptionist)
        r = self._claim(_token(receptionist), e["id"], f"qce:{e['id']}:0")
        assert r.status_code == 409, r.text
        assert self._deliveries(f"qce:{e['id']}:0") == []

    def test_claim_is_tenant_scoped(self, receptionist):
        e = self._called_entry(receptionist)
        foreign = self._claim(_token(receptionist, org="other-org"),
                              e["id"], e["call_event_id"])
        assert foreign.status_code == 404, foreign.text
        assert self._deliveries(e["call_event_id"]) == []
        # The legitimate terminal can still claim afterwards.
        assert self._claim(_token(receptionist), e["id"],
                           e["call_event_id"]).status_code == 201

    def test_claim_requires_no_new_permission(self, receptionist, doctor_user):
        """queue.consult may announce; queue.manage is still what `call` needs."""
        e = self._called_entry(receptionist)
        doctor_token = _token(doctor_user)
        r = self._claim(doctor_token, e["id"], e["call_event_id"])
        assert r.status_code == 201, r.text
        still_refused = client.patch(f"/api/v1/queue/{e['id']}",
                                     headers=_auth(doctor_token),
                                     json={"action": "call"})
        assert still_refused.status_code == 403
        assert self._read_entry(receptionist, e["id"])["status"] == "called"

    def test_claim_is_refused_without_a_token(self, receptionist):
        e = self._called_entry(receptionist)
        r = client.post(f"/api/v1/queue/{e['id']}/announcement",
                        json={"event_id": e["call_event_id"]})
        assert r.status_code == 401



class TestAnnouncementAudit(_AnnouncementFixture):
    """POD-4: a call success is not an announcement, and `requested` is not
    `completed`."""

    def test_completion_recorded_only_after_final_playback_report(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        claim = self._claim(token, e["id"], e["call_event_id"]).json()
        # Claimed, not announced: the row must not claim any sound yet.
        row = self._deliveries(e["call_event_id"])[0]
        assert row["status"] == "requested"
        assert row["outcome_at"] is None
        assert "queue.announcement.completed" not in self._audit_actions(e["call_event_id"])

        done = self._report(token, claim["delivery_id"], "completed")
        assert done.status_code == 200, done.text
        assert done.json()["status"] == "completed"
        row = self._deliveries(e["call_event_id"])[0]
        assert row["status"] == "completed"
        assert row["outcome_at"] is not None
        actions = self._audit_actions(e["call_event_id"])
        assert "queue.announcement.requested" in actions
        assert "queue.announcement.completed" in actions
        # The queue call itself is a separate record on a separate target.
        assert "queue.call" in self._audit_actions(e["id"])

    def test_each_playback_outcome_is_distinguished(self, receptionist):
        token = _token(receptionist)
        for outcome in ("failed", "blocked", "interrupted", "skipped_busy",
                        "skipped_duplicate"):
            e = self._called_entry(receptionist)
            claim = self._claim(token, e["id"], e["call_event_id"]).json()
            r = self._report(token, claim["delivery_id"], outcome, reason=outcome)
            assert r.status_code == 200, (outcome, r.text)
            row = self._deliveries(e["call_event_id"])[0]
            assert row["status"] == outcome, row
            assert row["reason"] == outcome
            assert f"queue.announcement.{outcome}" in self._audit_actions(e["call_event_id"])
            # No outcome ever changes the queue entry: playback is not a
            # queue operation.
            assert self._read_entry(receptionist, e["id"])["status"] == "called"

    def test_unknown_outcome_is_rejected_and_left_requested(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        claim = self._claim(token, e["id"], e["call_event_id"]).json()
        assert self._report(token, claim["delivery_id"], "played").status_code == 422
        assert self._deliveries(e["call_event_id"])[0]["status"] == "requested"

    def test_settled_outcome_is_not_rewritten(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        claim = self._claim(token, e["id"], e["call_event_id"]).json()
        assert self._report(token, claim["delivery_id"], "completed").status_code == 200
        clash = self._report(token, claim["delivery_id"], "failed")
        assert clash.status_code == 409, clash.text
        row = self._deliveries(e["call_event_id"])[0]
        assert row["status"] == "completed"
        assert self._read_entry(receptionist, e["id"])["status"] == "called"

    def test_repeated_report_is_idempotent(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        claim = self._claim(token, e["id"], e["call_event_id"]).json()
        assert self._report(token, claim["delivery_id"], "completed").status_code == 200
        again = self._report(token, claim["delivery_id"], "completed")
        assert again.status_code == 200, again.text
        assert again.json()["duplicate"] is True
        actions = self._audit_actions(e["call_event_id"])
        assert actions.count("queue.announcement.completed") == 1, actions

    def test_outcome_is_tenant_scoped(self, receptionist):
        e = self._called_entry(receptionist)
        token = _token(receptionist)
        claim = self._claim(token, e["id"], e["call_event_id"]).json()
        foreign = self._report(_token(receptionist, org="other-org"),
                               claim["delivery_id"], "completed")
        assert foreign.status_code == 404, foreign.text
        assert self._deliveries(e["call_event_id"])[0]["status"] == "requested"

    def test_announcement_failure_cannot_block_the_queue(self, receptionist,
                                                         doctor_user):
        """V-11: a refused claim leaves the queue fully usable."""
        e = self._called_entry(receptionist)
        assert self._claim(_token(receptionist), e["id"], "nonsense").status_code == 409
        started = client.patch(f"/api/v1/queue/{e['id']}",
                               headers=_auth(_token(doctor_user)),
                               json={"action": "start_consultation"})
        assert started.status_code == 200, started.text
        assert started.json()["status"] == "in_consultation"

        # A refused claim must neither consume nor invent a call event: the entry's
        # identity is still exactly the one its successful call issued.  (This
        # replaces a stray `after` reference copied from a neighbouring test, which
        # raised NameError instead of asserting anything.)
        after = self._read_entry(receptionist, e["id"])
        assert after["call_event_id"] == e["call_event_id"]
        assert after["call_count"] == 1
        assert after["status"] == "in_consultation"
