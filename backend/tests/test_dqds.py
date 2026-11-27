"""M9-C DQDS tests — public queue display, security, rate limiting, privacy."""
import sys, os, json, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "identity"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "queuing"))

from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from common.database import SessionFactory
from common.models import (Organization, Branch, Doctor, Patient,
                           Appointment, QueueEntry, TrackingToken)
from queuing.main import app

client = TestClient(app)

ORG_CODE = "dqds-org"
BR_CODE = "dqds-br"
ORG2_CODE = "dqds-org-2"
DOC_ID = "dqds-doc-1"
DOC2_ID = "dqds-doc-2"
PAT_ID = "dqds-pat"


def _ensure():
    """Seed reference rows for the DQDS test orgs (scoped, non-destructive)."""
    s = SessionFactory()
    try:
        # Purge only this test's own data.
        s.query(QueueEntry).filter(
            QueueEntry.organization_id.in_([ORG_CODE, ORG2_CODE])).delete(
                synchronize_session=False)
        s.query(Appointment).filter(
            Appointment.organization_id.in_([ORG_CODE, ORG2_CODE])).delete(
                synchronize_session=False)
        s.query(Patient).filter(Patient.id == PAT_ID).delete()
        s.query(Doctor).filter(Doctor.id.in_(
            [DOC_ID, DOC2_ID, "dqds-doc-foreign"])).delete(
                synchronize_session=False)
        s.query(Doctor).filter(Doctor.organization_id.in_(
            [ORG_CODE, ORG2_CODE])).delete(synchronize_session=False)
        s.query(Branch).filter(Branch.organization_id.in_(
            [ORG_CODE, ORG2_CODE])).delete()
        s.query(Organization).filter(Organization.id.in_(
            [ORG_CODE, ORG2_CODE])).delete()
        for oid, name in [(ORG_CODE, "DQDS Hospital"), (ORG2_CODE, "Other Hospital")]:
            s.add(Organization(id=oid, name=name, code=oid))
        s.add(Branch(id=BR_CODE, organization_id=ORG_CODE,
                     name="Main Branch", code=BR_CODE))
        s.add(Branch(id="dqds-br-other", organization_id=ORG2_CODE,
                     name="Other Branch", code="dqds-br-other"))
        s.add(Doctor(id=DOC_ID, organization_id=ORG_CODE,
                     name="Dr. Dina", mobile="01700000001"))
        s.add(Doctor(id=DOC2_ID, organization_id=ORG_CODE,
                     name="Dr. Kamal", mobile="01700000002"))
        s.add(Patient(id=PAT_ID, organization_id=ORG_CODE,
                      name="Test Patient", mobile="01700000999", sex="male"))
        s.commit()
    finally:
        s.close()


@pytest.fixture(scope="module", autouse=True)
def _seeded_rows():
    """Seed the DQDS organisations, branches, doctors and patient once per module.

    Import-time seeding made pytest's **collection** write to the database and
    coupled this module to whichever file happened to be imported first — the
    same defect as D-3 (finding T-10, 27 November 2026).
    """
    _ensure()

TODAY = date.today()


def _queue(status: str, token: str, position: int, doctor=DOC_ID,
           branch=BR_CODE, org=ORG_CODE, patient=PAT_ID):
    s = SessionFactory()
    try:
        e = QueueEntry(id=str(uuid.uuid4()), organization_id=org,
                       branch_id=branch, doctor_id=doctor, date=TODAY,
                       position=position, token=token, status=status,
                       patient_id=patient, entry_source="appointment",
                       status_history=list(), position_history=list())
        s.add(e)
        s.commit()
    finally:
        s.close()


def _clear():
    """Remove this test's queue entries and reset the DQDS rate limiter."""
    from queuing.display import _DQDS_RATE
    _DQDS_RATE.clear()
    s = SessionFactory()
    try:
        s.query(QueueEntry).filter(
            QueueEntry.organization_id.in_([ORG_CODE, ORG2_CODE])).delete(
                synchronize_session=False)
        s.commit()
    finally:
        s.close()


# ---------------------------------------------------------------------------

def test_dqds_active_queue():
    _clear()
    _queue("waiting", "A-003", 3, doctor=DOC_ID)
    _queue("waiting", "A-004", 4, doctor=DOC_ID)
    _queue("called", "A-002", 2, doctor=DOC_ID)
    _queue("in_consultation", "A-001", 1, doctor=DOC_ID)
    _queue("waiting", "B-001", 1, doctor=DOC2_ID)

    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    body = r.json()
    assert body["organization"]["code"] == ORG_CODE
    assert body["branch"]["code"] == BR_CODE
    assert len(body["doctors"]) == 2

    d1 = [d for d in body["doctors"] if d["doctor_name"] == "Dr. Dina"][0]
    assert d1["currently_serving"] == "A-001"  # lowest-pos in_consultation
    assert d1["patients_waiting"] == 3  # waiting(2) + called(1)

    d2 = [d for d in body["doctors"] if d["doctor_name"] == "Dr. Kamal"][0]
    assert d2["currently_serving"] is None
    assert d2["patients_waiting"] == 1


def test_dqds_empty_queue():
    _clear()
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    assert r.json()["doctors"] == []


def test_dqds_unknown_org_404():
    _clear()
    assert client.get("/api/v1/queue/display/no-such-org/main").status_code == 404


def test_dqds_unknown_branch_404():
    _clear()
    assert client.get(f"/api/v1/queue/display/{ORG_CODE}/no-such-br").status_code == 404


def test_dqds_cross_org_404():
    _clear()
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/dqds-br-other")
    assert r.status_code == 404


def test_dqds_no_pii():
    """No patient identity, appointment, or tracking data reaches the display."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    body = r.json()
    body_str = json.dumps(body)

    # 1. No forbidden keys anywhere in the payload.
    forbidden_keys = {"patient_id", "patient_name", "mobile", "date_of_birth",
                      "dob", "age", "sex", "address", "national_id",
                      "appointment_id", "tracking_url", "tracking_token",
                      "token_hash", "patient", "appointment"}
    def _keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from _keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from _keys(v)
    leaked = forbidden_keys.intersection(set(_keys(body)))
    assert not leaked, f"PII/identifier keys leaked: {leaked}"

    # 2. The seeded patient's real values must not appear anywhere.
    assert "Test Patient" not in body_str
    assert "01700000999" not in body_str
    assert PAT_ID not in body_str

    # 3. Public schema is exactly the intended three fields per doctor.
    for d in body["doctors"]:
        assert set(d.keys()) == {"doctor_name", "currently_serving",
                                 "patients_waiting"}
    assert set(body.keys()) == {"organization", "branch", "doctors",
                               "updated_at"}


def test_dqds_rate_limit():
    """Rate limiter trips at 30 req/min/IP and returns 429."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    codes = [client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").status_code
             for _ in range(35)]
    assert 429 in codes, "Rate limiter did not trigger within 35 requests"
    assert codes.count(200) <= 30


def test_dqds_cache_headers():
    """Public, short-lived cache headers (deliberately different from PQT)."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "public" in cc, f"expected public in Cache-Control: {cc!r}"
    assert "max-age=10" in cc, f"expected max-age=10 in Cache-Control: {cc!r}"
    assert "no-store" not in cc, f"DQDS must not use PQT's no-store: {cc!r}"


def test_dqds_non_active_excluded():
    """completed / cancelled / no_show are excluded; skipped remains active."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    _queue("waiting", "A-002", 2, doctor=DOC_ID)
    _queue("completed", "A-003", 3, doctor=DOC_ID)
    _queue("cancelled", "A-004", 4, doctor=DOC_ID)
    _queue("no_show", "A-005", 5, doctor=DOC_ID)
    _queue("skipped", "A-006", 6, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    d1 = [d for d in r.json()["doctors"] if d["doctor_name"] == "Dr. Dina"][0]
    # waiting(2) + skipped(1) = 3
    assert d1["patients_waiting"] == 3, f"expected 3, got {d1['patients_waiting']}"


def test_dqds_updates_reflected():
    """A status change is reflected on the next (cache-bypassed) request."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    _queue("waiting", "A-002", 2, doctor=DOC_ID)
    r1 = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    d1 = [d for d in r1.json()["doctors"] if d["doctor_name"] == "Dr. Dina"][0]
    assert d1["patients_waiting"] == 2
    assert d1["currently_serving"] is None

    s = SessionFactory()
    try:
        e = s.query(QueueEntry).filter(
            QueueEntry.organization_id == ORG_CODE,
            QueueEntry.date == TODAY,
            QueueEntry.token == "A-001").first()
        e.status = "in_consultation"
        s.commit()
    finally:
        s.close()

    r2 = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    d2 = [d for d in r2.json()["doctors"] if d["doctor_name"] == "Dr. Dina"][0]
    assert d2["currently_serving"] == "A-001"
    assert d2["patients_waiting"] == 1


def test_dqds_timezone_today_only():
    """Entries from other dates are not shown."""
    _clear()
    s = SessionFactory()
    try:
        s.add(QueueEntry(id=str(uuid.uuid4()), organization_id=ORG_CODE,
                         branch_id=BR_CODE, doctor_id=DOC_ID,
                         date=TODAY + timedelta(days=1), position=1,
                         token="Z-001", status="waiting", patient_id=PAT_ID,
                         entry_source="appointment",
                         status_history=list(), position_history=list()))
        s.commit()
    finally:
        s.close()
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    assert r.json()["doctors"] == []


def test_dqds_other_org_isolation():
    """Another org's active queue never bleeds into this branch's display."""
    _clear()
    _queue("waiting", "X-001", 1, doctor=DOC_ID, branch="dqds-br-other",
           org=ORG2_CODE)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    assert r.json()["doctors"] == []


def test_dqds_public_no_auth_required():
    """The display is reachable with no Authorization header at all."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    assert "authorization" not in {k.lower() for k in r.request.headers}


def test_dqds_no_internal_helpers_leak():
    """Internal aggregation keys (e.g. _serving_rank) are not serialised."""
    _clear()
    _queue("called", "A-001", 1, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert r.status_code == 200
    body = r.json()
    for d in body["doctors"]:
        assert set(d.keys()) == {"doctor_name", "currently_serving",
                                 "patients_waiting"}, d.keys()
    assert "_serving_rank" not in json.dumps(body)


# ---------------------------------------------------------------------------
# Sequence 2 (AMSDP-M9-C3) — limiter signalling, error caching, tenant state,
# serving-token precedence and PQT-token isolation.
# ---------------------------------------------------------------------------

def _set_status(model, row_id, status):
    """Flip a seeded row's status and leave the caller to restore it."""
    s = SessionFactory()
    try:
        row = s.query(model).filter(model.id == row_id).first()
        row.status = status
        s.commit()
    finally:
        s.close()


def test_dqds_rate_limit_headers():
    """Refusal is 429 with reset signalling — never a bare 429."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    last_ok, refused = None, None
    for _ in range(35):
        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        if r.status_code == 200:
            last_ok = r
        elif r.status_code == 429 and refused is None:
            refused = r
    assert last_ok is not None, "no successful response inside the allowance"
    assert refused is not None, "rate limiter did not refuse within 35 requests"

    # Success carries the rate headers too (remaining reaches 0 on request 30).
    assert last_ok.headers["x-ratelimit-limit"] == "30"
    assert last_ok.headers["x-ratelimit-remaining"] == "0"
    assert int(last_ok.headers["x-ratelimit-reset"]) > 0

    assert int(refused.headers["retry-after"]) >= 1
    assert refused.headers["x-ratelimit-limit"] == "30"
    assert refused.headers["x-ratelimit-remaining"] == "0"
    assert int(refused.headers["x-ratelimit-reset"]) > 0
    # A refusal must never be publicly cacheable.
    assert "no-store" in refused.headers["cache-control"]


def test_dqds_not_found_is_non_disclosing_and_uncacheable():
    """Unknown org = unknown branch = cross-org branch: identical 404, no-store."""
    _clear()
    bodies = []
    for path in (f"/api/v1/queue/display/no-such-org/{BR_CODE}",
                 f"/api/v1/queue/display/{ORG_CODE}/no-such-br",
                 f"/api/v1/queue/display/{ORG_CODE}/dqds-br-other"):
        r = client.get(path)
        assert r.status_code == 404, path
        assert "no-store" in r.headers.get("cache-control", ""), path
        bodies.append(r.json())
    assert bodies[0] == bodies[1] == bodies[2] == {"detail": "not found"}




def test_dqds_inactive_org_404():
    """A suspended/expired organization serves no public display."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    _set_status(Organization, ORG_CODE, "suspended")
    try:
        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 404
    finally:
        _set_status(Organization, ORG_CODE, "active")
    assert client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").status_code == 200


def test_dqds_inactive_branch_404():
    """A disabled branch is not a valid display target."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    _set_status(Branch, BR_CODE, "inactive")
    try:
        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 404
    finally:
        _set_status(Branch, BR_CODE, "active")
    assert client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").status_code == 200


def test_dqds_inactive_doctor_not_published():
    """A deactivated doctor is not advertised on a public board."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    _set_status(Doctor, DOC_ID, "inactive")
    try:
        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 200
        assert r.json()["doctors"] == []
    finally:
        _set_status(Doctor, DOC_ID, "active")


def test_dqds_cross_org_doctor_name_never_leaks():
    """A queue row pointing at another org's doctor publishes nothing."""
    _clear()
    s = SessionFactory()
    try:
        s.add(Doctor(id="dqds-doc-foreign", organization_id=ORG2_CODE,
                     name="Dr. Foreign", mobile="01700000003"))
        s.commit()
    finally:
        s.close()
    _queue("waiting", "F-001", 1, doctor="dqds-doc-foreign")
    try:
        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 200
        assert "Dr. Foreign" not in json.dumps(r.json())
        assert r.json()["doctors"] == []
    finally:
        s = SessionFactory()
        try:
            s.query(QueueEntry).filter(
                QueueEntry.doctor_id == "dqds-doc-foreign").delete(
                    synchronize_session=False)
            s.query(Doctor).filter(
                Doctor.id == "dqds-doc-foreign").delete(synchronize_session=False)
            s.commit()
        finally:
            s.close()


def test_dqds_idle_doctor_not_listed():
    """Doctors with no active entry today are not listed (documented scope)."""
    _clear()
    _queue("waiting", "A-001", 1, doctor=DOC_ID)
    r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
    assert [d["doctor_name"] for d in r.json()["doctors"]] == ["Dr. Dina"]


def test_dqds_serving_prefers_in_consultation():
    """in_consultation wins over a called entry at a lower position."""
    _clear()
    _queue("called", "A-001", 1, doctor=DOC_ID)
    _queue("in_consultation", "A-002", 2, doctor=DOC_ID)
    _queue("waiting", "A-003", 3, doctor=DOC_ID)
    d = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").json()["doctors"][0]
    assert d["currently_serving"] == "A-002"
    # waiting + called count as waiting; in_consultation does not.
    assert d["patients_waiting"] == 2


def test_dqds_skipped_never_shown_as_serving():
    """A skipped entry still counts as waiting but is never 'currently serving'."""
    _clear()
    _queue("skipped", "A-001", 1, doctor=DOC_ID)
    d = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").json()["doctors"][0]
    assert d["currently_serving"] is None
    assert d["patients_waiting"] == 1


def test_dqds_never_returns_tracking_material():
    """Only the serving token is published; no PQT token material anywhere."""
    _clear()
    _queue("called", "A-001", 1, doctor=DOC_ID)
    _queue("waiting", "A-002", 2, doctor=DOC_ID)
    body = json.dumps(client.get(
        f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}").json())
    for marker in ("tracking", "token_hash", "token_prefix", "/track/"):
        assert marker not in body, f"PQT material leaked: {marker}"
    assert body.count("A-001") == 1, "the serving token is published exactly once"
    assert "A-002" not in body, "queued tokens must never be published"


# ---------------------------------------------------------------------------
# Gap closure (MP-06 / GAP-03) — the board's day is the facility's day.
def _queue_on(day, status: str, token: str, position: int, doctor=DOC_ID,
              org=ORG_CODE):
    """Insert one entry on an explicit day — ``_queue`` pins the module's TODAY."""
    s = SessionFactory()
    try:
        s.add(QueueEntry(id=str(uuid.uuid4()), organization_id=org,
                         branch_id=BR_CODE, doctor_id=doctor, date=day,
                         position=position, token=token, status=status,
                         patient_id=PAT_ID, entry_source="appointment",
                         status_history=list(), position_history=list()))
        s.commit()
    finally:
        s.close()


def _set_org_zone(name):
    """Point the DQDS org at ``name``; return the previous value to restore."""
    s = SessionFactory()
    try:
        org = s.query(Organization).filter(Organization.id == ORG_CODE).first()
        previous = org.timezone
        org.timezone = name
        s.commit()
        return previous
    finally:
        s.close()


# ---------------------------------------------------------------------------

def test_dqds_uses_the_facility_day_not_the_server_day(monkeypatch):
    """MP-06: the board rolls over at the facility's midnight (BR §8).

    ``2026-11-23T19:00Z`` is ``2026-11-24 01:00`` in Asia/Dhaka, so the facility
    is already on the 24th while a UTC server still calls it the 23rd. One
    in-consultation entry is filed on each day; only the facility day's may be
    published. A board that trusts the server clock publishes the previous day's
    tokens for the first six hours of every Dhaka day.

    The assertion is on ``currently_serving`` because the public schema
    deliberately exposes only the serving token plus counts — a waiting entry's
    token is never published, so a token-in-body check would be vacuous.
    """
    import common.timeutil as timeutil
    import queuing.display as display_mod

    fixed_utc = datetime(2026, 11, 23, 19, 0, tzinfo=timezone.utc)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_utc.astimezone(tz) if tz else fixed_utc.replace(tzinfo=None)

    class _ServerDate(date):
        @classmethod
        def today(cls):
            return date(2026, 11, 23)

    monkeypatch.setattr(timeutil, "datetime", _FrozenDateTime)
    # Inert after the fix; if the route ever reads the server clock again, this
    # pin makes it answer the 23rd and the assertions below fail.
    monkeypatch.setattr(display_mod, "date", _ServerDate, raising=False)

    previous = _set_org_zone("Asia/Dhaka")
    try:
        _clear()
        _queue_on(date(2026, 11, 24), "in_consultation", "F-024", 1)
        _queue_on(date(2026, 11, 24), "waiting", "F-025", 2)
        _queue_on(date(2026, 11, 23), "in_consultation", "F-023", 1)

        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 200
        dina = [d for d in r.json()["doctors"]
                if d["doctor_name"] == "Dr. Dina"][0]
        assert dina["currently_serving"] == "F-024", dina
        assert dina["patients_waiting"] == 1, dina
    finally:
        _set_org_zone(previous)
        _clear()


def test_dqds_honours_the_configured_facility_zone(monkeypatch):
    """MP-06: the day comes from ``organizations.timezone``, not a constant.

    At ``2026-11-23T19:00Z`` Dhaka is on the 24th but New York is on the 23rd at
    14:00. With the org configured ``America/New_York`` the board must publish the
    23rd's token — so a board hard-wired to Asia/Dhaka (or to the server clock)
    fails this test even though it passes the rollover test above.
    """
    import common.timeutil as timeutil

    fixed_utc = datetime(2026, 11, 23, 19, 0, tzinfo=timezone.utc)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_utc.astimezone(tz) if tz else fixed_utc.replace(tzinfo=None)

    monkeypatch.setattr(timeutil, "datetime", _FrozenDateTime)

    previous = _set_org_zone("America/New_York")
    try:
        _clear()
        _queue_on(date(2026, 11, 23), "in_consultation", "N-023", 1)
        _queue_on(date(2026, 11, 24), "in_consultation", "N-024", 1)

        r = client.get(f"/api/v1/queue/display/{ORG_CODE}/{BR_CODE}")
        assert r.status_code == 200
        dina = [d for d in r.json()["doctors"]
                if d["doctor_name"] == "Dr. Dina"][0]
        assert dina["currently_serving"] == "N-023", dina
    finally:
        _set_org_zone(previous)
        _clear()

