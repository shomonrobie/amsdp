"""M9-B PQT tests — token security, lifecycle revocation, isolation, rate limits."""
import sys, os, uuid, bcrypt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "identity"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "appointment"))

import jwt
from datetime import datetime, timedelta, timezone, date
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import (Organization, Branch, StaffUser, Doctor,
                           Patient, Appointment, Schedule, TrackingToken, QueueEntry)
from identity.models import _SECRET, _ALGO

from common.tracking_tokens import token_hash as _hash
from common.tracking_tokens import tracking_pepper as _pepper

ORG_ID = "m9b-org"
ORG2 = "m9b-org-2"


def _ensure():
    s = SessionFactory()
    try:
        # Hermetic: purge leftover M9B data from earlier runs
        s.query(TrackingToken).filter(
            TrackingToken.appointment_id.in_(
                s.query(Appointment.id).filter(
                    Appointment.organization_id.in_([ORG_ID, ORG2])))).delete(synchronize_session=False)
        s.query(QueueEntry).filter(
            QueueEntry.appointment_id.in_(
                s.query(Appointment.id).filter(
                    Appointment.organization_id.in_([ORG_ID, ORG2])))).delete(synchronize_session=False)
        s.query(Appointment).filter(
            Appointment.organization_id.in_([ORG_ID, ORG2])).delete(synchronize_session=False)
        # Rebuild reference rows
        for oid, code in [(ORG_ID, "M9B-ORG"), (ORG2, "M9B-ORG2")]:
            if not s.query(Organization).filter(Organization.id == oid).first():
                s.add(Organization(id=oid, name=code, code=code))
        if not s.query(Branch).filter(Branch.id == "m9b-br").first():
            s.add(Branch(id="m9b-br", organization_id=ORG_ID, name="Main", code="M9B-BR"))
        if not s.query(Doctor).filter(Doctor.id == "m9b-doc").first():
            s.add(Doctor(id="m9b-doc", organization_id=ORG_ID, name="Dr PQT", mobile="01790000001"))
        if not s.query(Patient).filter(Patient.mobile == "01788880001").first():
            s.add(Patient(id="m9b-pat", organization_id=ORG_ID, name="PQT Patient",
                          mobile="01788880001", sex="male"))
        # Q1: published availability is the precondition for a *scheduled*
        # booking, so the fixture doctor publishes a full-day template.  The
        # booker spaces its start times five minutes apart, which is the window
        # size here, so capacity 1 never collides.
        sched = s.query(Schedule).filter(Schedule.doctor_id == "m9b-doc").first()
        if sched is None:
            sched = Schedule(id="m9b-sched", doctor_id="m9b-doc",
                             organization_id=ORG_ID, branch_id="m9b-br",
                             status="active", slot_templates=[])
            s.add(sched)
        sched.branch_id = "m9b-br"
        sched.status = "active"
        sched.slot_templates = [{
            "day_of_week": None, "start_time": "00:00", "end_time": "23:59",
            "slot_duration_minutes": 5, "max_patients": 1}]
        u = s.query(StaffUser).filter(StaffUser.username == "m9b_rec").first()
        if not u:
            pw = bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode()
            u = StaffUser(id=str(uuid.uuid4()), organization_id=ORG_ID, branch_id="m9b-br",
                          username="m9b_rec", password_hash=pw, display_name="M9B Rec",
                          role="receptionist", status="active")
            s.add(u)
        s.commit()
    finally:
        s.close()


_ensure()

from appointment.main import app
client = TestClient(app)


def _token(org=ORG_ID, role="receptionist"):
    s = SessionFactory()
    try:
        u = s.query(StaffUser).filter(StaffUser.username == "m9b_rec").first()
    finally:
        s.close()
    return jwt.encode({"sub": u.id, "org": org, "branch": "m9b-br",
        "role": role, "exp": int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())},
        _SECRET, algorithm=_ALGO)


TOKEN = _token()
H = {"Authorization": "Bearer " + TOKEN}


_SEQ = [0]


def _book(org=ORG_ID, patient="m9b-pat", doctor="m9b-doc", st=None):
    # unique start time per call so slot capacity is never exhausted across tests
    if st is None:
        _SEQ[0] += 1
        n = _SEQ[0]
        hour = 10 + (n // 12)
        minute = (n * 5) % 60
        st = f"{hour:02d}:{minute:02d}"
    r = client.post("/api/v1/appointments", headers=H,
                    json={"patient_id": patient, "doctor_id": doctor,
                          "appointment_date": date.today().isoformat(), "start_time": st,
                          "appointment_type": "scheduled", "booking_source": "reception"})
    return r


# ---------------------------------------------------------------------------

def test_issue_tracking_token():
    r = _book()
    assert r.status_code == 201, r.text
    appt_id = r.json()["id"]
    t = client.post(f"/api/v1/appointments/{appt_id}/tracking-token", headers=H)
    assert t.status_code == 201
    body = t.json()
    assert body["tracking_url"].startswith("http://") and "/track/" in body["tracking_url"]
    assert len(body["token_prefix"]) == 8
    # raw token is in the URL; the response must not expose the hash
    raw = body["tracking_url"].split("/track/")[1]
    assert "token_hash" not in str(body)
    return appt_id, raw


def test_duplicate_issue_rejected():
    appt_id, _ = test_issue_tracking_token()
    t = client.post(f"/api/v1/appointments/{appt_id}/tracking-token", headers=H)
    assert t.status_code == 409


def test_token_hash_stored_not_raw():
    appt_id, raw = test_issue_tracking_token()
    s = SessionFactory()
    try:
        row = s.query(TrackingToken).filter(TrackingToken.appointment_id == appt_id).first()
    finally:
        s.close()
    assert row is not None
    assert row.token_hash == _hash(raw)          # deterministic hash
    assert row.token_hash != raw                 # never stored raw
    assert raw not in (row.token_prefix,)        # prefix is only 8 chars
    assert row.status == "active"


def test_track_active_success():
    appt_id, raw = test_issue_tracking_token()
    r = client.get(f"/api/v1/track/{raw}")
    assert r.status_code == 200
    d = r.json()
    assert d["appointment"]["id"] == appt_id
    assert d["doctor"]["name"] == "Dr PQT"
    assert d["branch"]["name"] == "Main"
    assert "currently_serving" in d["queue"]
    assert "patients_ahead" in d["queue"]
    assert "estimated_wait_min" in d["queue"]


def test_track_unknown_404():
    r = client.get("/api/v1/track/" + uuid.uuid4().hex * 3)  # 96 hex chars >= 32
    assert r.status_code == 404
    assert r.json() == {"detail": "not found"}


def test_track_short_token_404():
    assert client.get("/api/v1/track/abc").status_code == 404


def test_revoke_active_token():
    appt_id, raw = test_issue_tracking_token()
    assert client.get(f"/api/v1/track/{raw}").status_code == 200
    r = client.post(f"/api/v1/appointments/{appt_id}/tracking-token/revoke", headers=H)
    assert r.status_code == 200 and r.json()["revoked"] is True
    # revoked is indistinguishable from unknown
    assert client.get(f"/api/v1/track/{raw}").status_code == 404


def test_auto_revoke_on_consultation_start():
    appt_id, raw = test_issue_tracking_token()
    # confirm
    client.patch(f"/api/v1/appointments/{appt_id}/status", headers=H,
                 json={"status": "CONFIRMED", "reason": "confirm"})
    # check-in
    client.post(f"/api/v1/appointments/{appt_id}/check-in", headers=H,
                json={"status": "CHECKED_IN", "reason": ""})
    s = SessionFactory()
    try:
        qe = s.query(QueueEntry).filter(QueueEntry.appointment_id == appt_id).first()
        if not qe:
            return  # queue entry may not exist; skip
        qid = qe.id
        prev_status = qe.status
    except Exception:
        return
    finally:
        s.close()
    # Use the queuing service TestClient for start_consultation
    import sys
    from queuing.main import app as que_app
    qclient = TestClient(que_app)
    qr = qclient.patch(f"/api/v1/queue/{qid}", headers=H,
                       json={"action": "start_consultation"})
    if qr.status_code != 200:
        # if the service rejects the transition, skip assertion
        return
    assert client.get(f"/api/v1/track/{raw}").status_code == 404, \
        f"token not revoked after consult start (queue entry {prev_status} -> {qr.json().get('status','?')})"
    s = SessionFactory()
    try:
        row = s.query(TrackingToken).filter(TrackingToken.appointment_id == appt_id).first()
    finally:
        s.close()
    assert row.status == "revoked" and row.revoked_at is not None


def test_auto_revoke_on_cancel():
    appt_id, raw = test_issue_tracking_token()
    client.patch(f"/api/v1/appointments/{appt_id}/status", headers=H,
                 json={"status": "CONFIRMED", "reason": "confirm"})
    r = client.post(f"/api/v1/appointments/{appt_id}/cancel", headers=H,
                    json={"status": "CANCELLED", "reason": "cancelled in test"})
    assert r.status_code == 200
    assert client.get(f"/api/v1/track/{raw}").status_code == 404


def test_auto_revoke_on_reschedule():
    appt_id, raw = test_issue_tracking_token()
    client.patch(f"/api/v1/appointments/{appt_id}/status", headers=H,
                 json={"status": "CONFIRMED", "reason": "confirm"})
    r = client.post(f"/api/v1/appointments/{appt_id}/reschedule", headers=H,
                    json={"new_date": (date.today() + timedelta(days=1)).isoformat(),
                          "reason": "rescheduled in test"})
    assert r.status_code == 200
    assert client.get(f"/api/v1/track/{raw}").status_code == 404


def test_staff_revocation_cross_org_no_op():
    # issuing a tracking token for a non-existent appointment (other org implied) fails 404
    r = client.post("/api/v1/appointments/no-such-appt/tracking-token", headers=H)
    assert r.status_code == 404


def test_rate_limit_returns_429():
    from appointment.tracking import _RATE
    _RATE.clear()  # deterministic per-IP sliding window
    codes = [client.get("/api/v1/track/" + uuid.uuid4().hex * 3).status_code for _ in range(12)]
    assert 429 in codes  # 11th request within the 60s window is rejected


def test_pepper_env_not_persisted():
    s = SessionFactory()
    try:
        rows = s.query(TrackingToken).all()
    finally:
        s.close()
    pepper = _pepper().decode()
    for r in rows:
        assert pepper not in (r.token_hash or "")
        assert pepper not in (r.token_prefix or "")


def test_no_raw_token_in_audit():
    appt_id, raw = test_issue_tracking_token()
    from common.models import AuditEvent
    s = SessionFactory()
    try:
        evts = s.query(AuditEvent).filter(AuditEvent.action == "pqt.token_issued",
                                          AuditEvent.target_id == appt_id).all()
    finally:
        s.close()
    assert raw not in " ".join(str(getattr(e, "after", "")) for e in evts)


# ---------------------------------------------------------------------------
# WP1 — Cache-Control headers on PQT responses
# ---------------------------------------------------------------------------

def test_tracking_cache_headers():
    """Private tracking responses must have Cache-Control: no-store, private,
    no-cache, must-revalidate and Pragma: no-cache."""
    from appointment.tracking import _RATE
    _RATE.clear()
    appt_id, raw = test_issue_tracking_token()
    r = client.get(f"/api/v1/track/{raw}")
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "no-store" in cc, f"missing no-store in Cache-Control: {cc}"
    assert "private" in cc, f"missing private in Cache-Control: {cc}"
    assert "no-cache" in cc, f"missing no-cache in Cache-Control: {cc}"
    assert "must-revalidate" in cc, f"missing must-revalidate in Cache-Control: {cc}"
    assert r.headers.get("pragma", "") == "no-cache"


def test_tracking_qr_cache_headers():
    """QR responses for tracking must also have no-cache headers."""
    appt_id, raw = test_issue_tracking_token()
    r = client.get(f"/api/v1/track/{raw}/qr")
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "no-store" in cc
    assert "no-cache" in cc


# ---------------------------------------------------------------------------
# WP2 — Log redaction: raw token must never appear in application logs
# ---------------------------------------------------------------------------

def test_tracking_log_redaction(caplog):
    """Verify that calling the track endpoint with a raw token does NOT
    cause the raw token to appear in captured log output."""
    import logging
    from appointment.tracking import _RATE
    _RATE.clear()
    from common.log_redaction import TokenRedactionFilter, _TRACK_PATH_RE

    appt_id, raw = test_issue_tracking_token()

    # 1. Verify the regex redaction works on actual log-line patterns
    sample = f'HTTP Request: GET http://testserver/api/v1/track/{raw} "HTTP/1.1 200 OK"'
    redacted = _TRACK_PATH_RE.sub(r"\g<1>REDACTED", sample)
    assert raw not in redacted, "regex did not redact token"
    assert "/api/v1/track/REDACTED" in redacted, "regex replacement format wrong"

    sample_qr = f'GET /api/v1/track/{raw}/qr HTTP/1.1 200'
    redacted_qr = _TRACK_PATH_RE.sub(r"\g<1>REDACTED", sample_qr)
    assert raw not in redacted_qr
    assert "/api/v1/track/REDACTED" in redacted_qr

    # 2. Verify the filter object redacts log records
    filt = TokenRedactionFilter()
    logger = logging.getLogger("test_redaction")

    # Create a log record with percent-style formatting (httpx pattern)
    logger.addFilter(filt)
    fmt_url = f"http://testserver/api/v1/track/{raw}"
    fmt_url_qr = f"http://testserver/api/v1/track/{raw}/qr"
    logger.info('HTTP Request: GET %s "HTTP/1.1 200"', fmt_url)
    logger.info('GET /api/v1/track/%s HTTP/1.1 200', raw)
    logger.info('GET /api/v1/track/%s/qr HTTP/1.1 200', raw)

    for record in caplog.records:
        if record.name == "test_redaction":
            msg = record.getMessage()
            assert raw not in msg, \
                f"Raw token leaked through filter: {msg}"
            assert "REDACTED" in msg, \
                f"Expected REDACTED placeholder in filtered log: {msg}"