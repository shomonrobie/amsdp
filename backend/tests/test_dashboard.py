"""M6 Dashboard + Audit API tests — real DB aggregates."""

import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "identity"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "appointment"))

import pytest, jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import (Organization, Branch, StaffUser, Doctor,
                           Patient, Appointment, QueueEntry, AuditEvent,
                           TrackingToken)
from common.audit import record_audit
from identity.models import _SECRET, _ALGO


def _ensure():
    s = SessionFactory()
    try:
        if not s.query(Organization).filter(Organization.code == "M6-ORG").first():
            s.add(Organization(id="m6-org", name="M6 Org", code="M6-ORG"))
        if not s.query(Branch).filter(Branch.id == "m6-branch").first():
            s.add(Branch(id="m6-branch", organization_id="m6-org", name="Main", code="M6-BR"))
        if not s.query(Doctor).filter(Doctor.id == "m6-doc").first():
            s.add(Doctor(id="m6-doc", organization_id="m6-org", name="Dr M6", mobile="01799990000"))
        s.commit()
    finally:
        s.close()

_ensure()


def _user(username, role):
    s = SessionFactory()
    try:
        u = s.query(StaffUser).filter(StaffUser.username == username).first()
        if not u:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id="m6-org",
                          branch_id="m6-branch", username=username, password_hash=pw,
                          display_name=username, role=role, status="active")
            s.add(u); s.commit()
        return u
    finally:
        s.close()


def _token(user, org="m6-org"):
    return jwt.encode({"sub": user.id, "org": org, "branch": "m6-branch",
        "role": user.role, "exp": int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


@pytest.fixture(scope="module")
def admin():
    return _user("m6_admin", "org_admin")


@pytest.fixture(autouse=True)
def clean():
    # Scoped to this module's org and deleted in FK-safe order: the previous
    # org-blind ``query(Appointment).delete()`` aborted the whole module with a
    # ForeignKeyViolation whenever another suite had already issued a PQT
    # tracking token for one of its fixture appointments.
    s = SessionFactory()
    try:
        appt_ids = [r[0] for r in s.query(Appointment.id).filter(
            Appointment.organization_id == "m6-org").all()]
        if appt_ids:
            s.query(TrackingToken).filter(
                TrackingToken.appointment_id.in_(appt_ids)).delete(
                    synchronize_session=False)
        for model in (QueueEntry, Appointment, AuditEvent):
            s.query(model).filter(
                model.organization_id == "m6-org").delete(
                    synchronize_session=False)
        s.commit()
    finally:
        s.close()
    yield


from appointment.main import app
client = TestClient(app)

from common.timeutil import operational_today

_today = operational_today()   # the dashboard counts the facility-local day


def _mk_appt_today(s, patient_id, status="COMPLETED", booking="phone"):
    a = Appointment(id=str(uuid.uuid4()), organization_id="m6-org", branch_id="m6-branch",
                    patient_id=patient_id, doctor_id="m6-doc",
                    appointment_date=_today, start_time="10:00", status=status,
                    status_history=[], booking_source=booking, token_number="T-M6-1")
    s.add(a); s.commit(); return a


class TestDashboardToday:
    def test_today_counts_active_and_completed(self, admin):
        s = SessionFactory()
        p = Patient(id=str(uuid.uuid4()), organization_id="m6-org", name="P", mobile="01711111111")
        s.add(p); s.commit()
        _mk_appt_today(s, p.id, status="BOOKED", booking="phone")
        _mk_appt_today(s, p.id, status="COMPLETED", booking="phone")
        _mk_appt_today(s, p.id, status="COMPLETED", booking="walk_in")
        s.close()
        r = client.get("/api/v1/dashboard/today", headers=_auth(_token(admin)))
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 3
        assert d["scheduled"] == 1
        assert d["completed"] == 2
        assert d["walk_ins"] == 1

    def test_today_no_token(self):
        assert client.get("/api/v1/dashboard/today").status_code == 401

    def test_today_cross_org_empty(self, admin):
        r = client.get("/api/v1/dashboard/today", headers=_auth(_token(admin, org="other-org")))
        assert r.status_code == 200 and r.json()["total"] == 0

    # --- MP-22: the date selector -------------------------------------------
    def test_an_explicit_date_selects_that_day(self, admin):
        """The dashboard's date selector asks a question about one day."""
        other_day = _today - timedelta(days=2)
        s = SessionFactory()
        p = Patient(id=str(uuid.uuid4()), organization_id="m6-org", name="P",
                    mobile="01711111112")
        s.add(p); s.commit()
        _mk_appt_today(s, p.id, status="COMPLETED")            # the facility day
        a = Appointment(id=str(uuid.uuid4()), organization_id="m6-org",
                        branch_id="m6-branch", patient_id=p.id, doctor_id="m6-doc",
                        appointment_date=other_day, start_time="10:00",
                        status="COMPLETED", status_history=[],
                        booking_source="phone", token_number="T-M6-2")
        s.add(a); s.commit(); s.close()

        selected = client.get(
            "/api/v1/dashboard/today?date=" + other_day.isoformat(),
            headers=_auth(_token(admin)))
        assert selected.status_code == 200
        body = selected.json()
        assert body["date"] == other_day.isoformat()
        assert body["total"] == 1, "only the selected day is counted"

        plain = client.get("/api/v1/dashboard/today", headers=_auth(_token(admin)))
        assert plain.json()["date"] == _today.isoformat()
        assert plain.json()["total"] == 1, "the default stays the facility day"

    def test_the_facility_day_is_reported_alongside_the_selection(self, admin):
        r = client.get("/api/v1/dashboard/today?date=2026-01-05",
                       headers=_auth(_token(admin)))
        assert r.status_code == 200
        assert r.json()["facility_today"] == _today.isoformat()

    @pytest.mark.parametrize("bad", ["24-11-2026", "2026-13-01", "today", "2026-1-5"])
    def test_an_unparseable_date_is_refused_not_guessed(self, admin, bad):
        r = client.get("/api/v1/dashboard/today?date=" + bad,
                       headers=_auth(_token(admin)))
        assert r.status_code == 422, bad

    # --- Q-2: Waiting is the queue, In queue is an appointment state ---------
    def test_waiting_and_in_queue_are_different_populations(self, admin):
        """Q-2, approved 2026-11-25.

        ``queue_length`` = live queue entries (what a person standing in the room
        contributes); ``in_queue`` = appointment records whose status is
        ``IN_QUEUE``.  A walk-in enqueued without an appointment row raises the
        first and not the second — which is exactly why the two must not be
        aliased on the dashboard.
        """
        s = SessionFactory()
        p = Patient(id=str(uuid.uuid4()), organization_id="m6-org", name="P",
                    mobile="01711111113")
        s.add(p); s.commit()
        queued = _mk_appt_today(s, p.id, status="IN_QUEUE")      # an appointment record
        _mk_appt_today(s, p.id, status="CHECKED_IN")            # checked in, not queued
        _mk_appt_today(s, p.id, status="BOOKED", booking="walk_in")  # booked only

        def entry(status, position, appointment_id=None, day=None):
            e = QueueEntry(id=str(uuid.uuid4()), organization_id="m6-org",
                           branch_id="m6-branch", doctor_id="m6-doc",
                           date=day or _today, position=position,
                           token="T-M6-Q%d" % position, patient_id=p.id,
                           appointment_id=appointment_id,
                           entry_source="appointment" if appointment_id else "walk_in",
                           status=status, status_history=[], position_history=[])
            s.add(e); return e

        entry("waiting", 1, appointment_id=queued.id)   # the queued appointment
        entry("waiting", 2)                             # walk-in, no appointment row
        entry("skipped", 3)                             # walk-in still in the room
        entry("completed", 4)                           # left the queue: excluded
        entry("waiting", 5, day=_today - timedelta(days=3))   # another day: excluded
        s.commit(); s.close()

        body = client.get("/api/v1/dashboard/today",
                          headers=_auth(_token(admin))).json()
        assert body["in_queue"] == 1, "appointment records in IN_QUEUE"
        assert body["checked_in"] == 1
        assert body["scheduled"] == 1
        assert body["walk_ins"] == 1
        assert body["queue_length"] == 3, (
            "live entries awaiting a decision, on this day only: "
            "waiting + walk-in waiting + skipped")
        assert body["queue_length"] != body["in_queue"], (
            "the two figures coincide only by accident; here they differ by the "
            "appointment-less walk-ins")

    def test_a_queue_entry_from_another_day_is_not_todays_waiting(self, admin):
        """The queue figure follows the facility day, not a rolling window."""
        s = SessionFactory()
        p = Patient(id=str(uuid.uuid4()), organization_id="m6-org", name="P",
                    mobile="01711111114")
        s.add(p); s.commit()
        s.add(QueueEntry(id=str(uuid.uuid4()), organization_id="m6-org",
                         branch_id="m6-branch", doctor_id="m6-doc",
                         date=_today - timedelta(days=1), position=1,
                         token="T-M6-Y1", patient_id=p.id, appointment_id=None,
                         entry_source="walk_in", status="waiting",
                         status_history=[], position_history=[]))
        s.commit(); s.close()
        body = client.get("/api/v1/dashboard/today",
                          headers=_auth(_token(admin))).json()
        assert body["queue_length"] == 0
        assert body["in_queue"] == 0
        assert body["total"] == 0


class TestDashboardPeriod:
    def test_period_totals_and_rates(self, admin):
        s = SessionFactory()
        p = Patient(id=str(uuid.uuid4()), organization_id="m6-org", name="P", mobile="01711111111")
        s.add(p); s.commit()
        for _ in range(3):
            _mk_appt_today(s, p.id, status="COMPLETED")
        _mk_appt_today(s, p.id, status="NO_SHOW")
        s.close()
        frm = (_today - timedelta(days=30)).isoformat()
        r = client.get(f"/api/v1/dashboard/period?from_date={frm}&to_date={_today.isoformat()}",
                       headers=_auth(_token(admin)))
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 4
        assert d["completed"] == 3
        assert d["no_show"] == 1
        assert d["no_show_rate"] == 25.0


class TestDashboardAudit:
    def test_audit_search_and_filters(self, admin):
        s = SessionFactory()
        for i, action in enumerate(["queue.checkin", "queue.reorder", "queue.complete_consultation"]):
            record_audit(s, service="queuing", org_id="m6-org", branch_id="m6-branch",
                         action=action, target_type="queue_entry", target_id=f"e{i}",
                         actor_id=admin.id, actor_role=admin.role,
                         after={"position": i + 1})
        s.commit(); s.close()
        r = client.get("/api/v1/dashboard/audit?action=queue.reorder",
                       headers=_auth(_token(admin)))
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_audit_cross_org_isolated(self, admin):
        s = SessionFactory()
        record_audit(s, service="queuing", org_id="m6-org", action="queue.enqueue",
                     target_type="queue_entry", target_id="x",
                     actor_id=admin.id, actor_role="org_admin")
        s.commit(); s.close()
        r = client.get("/api/v1/dashboard/audit", headers=_auth(_token(admin, org="other-org")))
        assert r.status_code == 200 and r.json() == []
def _auth(h): return {"Authorization": f"Bearer {h}"}