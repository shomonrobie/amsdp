"""MP-23 / BR §43 operational reports — reconciliation, scoping and scope limits.

Product Owner decision **PO-11 (2026-11-26)** approved Option A: the *complete*
BR §43 reporting scope, neither an MVP subset nor anything invented.  These
tests therefore assert three separate things:

1. **Reconciliation** — every dimension sums back to the appointment total, and
   the queue figures sum back to the queue entries.  This is the MP-23 acceptance
   criterion, checked against rows the test itself inserted.
2. **Scoping** — the tenant comes from the token, a foreign branch is a
   non-disclosing 404, and another branch's rows never enter the figures.
3. **Scope limits** — BR §43 forbids revenue, billing, payment-settlement and
   clinical-performance analytics, so the payload is asserted to carry no money
   or performance field at all.  A future field added carelessly fails here.

Every fixture uses a fixed day (`DAY`) whose weekday is known, so utilisation has
a deterministic denominator instead of depending on when the suite runs.
"""

import os
import sys
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.amsdp_test_support import (        # noqa: E402
    db_session, ensure_branch, ensure_doctor, ensure_org, ensure_patient,
    ensure_session, ensure_user, headers, load_app, purge_org)

from common.models import (Appointment, QueueEntry, SlotAllocation)  # noqa: E402

#: A fixed Tuesday: ``weekday() == 1``, which is what the session fixture uses.
DAY = date(2026, 3, 10)
DAY_TEXT = DAY.isoformat()
WEEKDAY = DAY.weekday()

ORG = "mp23-org"
OTHER_ORG = "mp23-other-org"
BRANCH_A = "mp23-branch-a"
BRANCH_B = "mp23-branch-b"
DOCTOR = "mp23-doctor"
PATIENT = "mp23-patient"


@pytest.fixture(scope="module")
def client():
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BRANCH_A, ORG)
    ensure_branch(BRANCH_B, ORG)
    ensure_doctor(DOCTOR, ORG, name="Dr. Report", mobile="01700000201")
    ensure_patient(PATIENT, ORG, name="Report Patient", mobile="01700000202")
    ensure_user("mp23_admin", "org_admin", ORG)
    ensure_user("mp23_desk_a", "receptionist", ORG, BRANCH_A)
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def clean():
    purge_org(ORG)
    purge_org(OTHER_ORG)
    # ``purge_org`` removes patients too — they are *business* rows, unlike the
    # organization, branch, doctor and staff-user reference rows it keeps for the
    # audit trail.  The patient must therefore be re-created after the purge, or
    # every appointment below would violate ``appointments_patient_id_fkey``.
    ensure_patient(PATIENT, ORG, name="Report Patient", mobile="01700000202")
    yield


def _appointment(appt_id, *, status, source="reception", branch=BRANCH_A,
                 day=DAY, org=ORG, doctor=DOCTOR):
    with db_session() as s:
        s.add(Appointment(id=appt_id, organization_id=org, branch_id=branch,
                          patient_id=PATIENT, doctor_id=doctor,
                          appointment_date=day, status=status,
                          booking_source=source, appointment_type="scheduled"))
        s.commit()


def _queue_entry(entry_id, *, position, status, history, source="appointment",
                 branch=BRANCH_A, day=DAY):
    created = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    with db_session() as s:
        # ``queue_entries.token`` and ``.patient_id`` are NOT NULL: a queue row
        # without either is not a row the product can ever produce, so the
        # fixture supplies both rather than testing a shape the schema forbids.
        s.add(QueueEntry(id=entry_id, organization_id=ORG, branch_id=branch,
                         doctor_id=DOCTOR, date=day, position=position,
                         token=f"T{position}", patient_id=PATIENT,
                         status=status, entry_source=source,
                         status_history=history, created_at=created))
        s.commit()


def _report(client, who="mp23_admin", **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get("/api/v1/reports/operational" + ("?" + query if query else ""),
                      headers=headers(who))


# ---------------------------------------------------------------------------
# Reconciliation (MP-23 acceptance)
# ---------------------------------------------------------------------------

def test_every_dimension_sums_to_the_appointment_total(client):
    _appointment("mp23-a1", status="BOOKED")
    _appointment("mp23-a2", status="COMPLETED", source="walk_in")
    _appointment("mp23-a3", status="CANCELLED", source="phone")
    _appointment("mp23-a4", status="NO_SHOW", source="online")
    _appointment("mp23-a5", status="CHECKED_IN", branch=BRANCH_B)

    response = _report(client, date=DAY_TEXT)
    assert response.status_code == 200, response.text
    body = response.json()

    total = body["appointments"]["total"]
    assert total == 5
    rec = body["reconciliation"]
    assert rec["appointments_total"] == total
    assert rec["status_sum"] == total
    assert rec["by_day_sum"] == total
    assert rec["by_doctor_sum"] == total
    assert rec["by_branch_sum"] == total
    assert rec["booking_sources_sum"] == total
    assert sum(row["count"] for row in body["appointments"]["by_day"]) == total
    assert sum(row["count"] for row in body["appointments"]["by_branch"]) == total
    assert sum(row["count"] for row in body["booking_sources"]) == total


def test_br43_headline_counts_are_disjoint_and_present_balance(client):
    _appointment("mp23-h1", status="BOOKED")
    _appointment("mp23-h2", status="CONFIRMED")
    _appointment("mp23-h3", status="COMPLETED")
    _appointment("mp23-h4", status="CANCELLED")
    _appointment("mp23-h5", status="NO_SHOW")
    _appointment("mp23-h6", status="CHECKED_IN")
    _appointment("mp23-h7", status="RESCHEDULED")

    body = _report(client, date=DAY_TEXT).json()
    br43 = body["br43"]
    assert br43["booked"] == 2, "booked = BOOKED + AWAITING_CONFIRMATION + CONFIRMED"
    assert br43["completed"] == 1
    assert br43["cancelled"] == 1
    assert br43["no_show"] == 1
    assert br43["present"] == 1, "checked-in patients are present, not booked"
    # The four headline figures plus present plus rescheduled must account for
    # every row: the report never loses an appointment between its sections.
    assert (br43["booked"] + br43["completed"] + br43["cancelled"]
            + br43["no_show"] + br43["present"]
            + body["status_counts"]["RESCHEDULED"]) == body["appointments"]["total"]


def test_walk_ins_and_booking_sources_are_counted_once(client):
    _appointment("mp23-s1", status="BOOKED", source="walk_in")
    _appointment("mp23-s2", status="BOOKED", source="walk_in")
    _appointment("mp23-s3", status="BOOKED", source="phone")

    body = _report(client, date=DAY_TEXT).json()
    assert body["walk_ins"] == 2
    sources = {row["source"]: row["count"] for row in body["booking_sources"]}
    assert sources == {"walk_in": 2, "phone": 1}


def test_queue_activity_reconciles_and_counts_calls(client):
    history = [
        {"from": "waiting", "to": "called", "at": "2026-03-10T09:10:00+00:00"},
        {"from": "called", "to": "completed", "at": "2026-03-10T09:25:00+00:00"},
    ]
    _queue_entry("mp23-q1", position=1, status="completed", history=history)
    _queue_entry("mp23-q2", position=2, status="waiting", history=[],
                 source="walk_in")

    body = _report(client, date=DAY_TEXT).json()
    activity = body["queue_activity"]
    assert activity["entries"] == 2
    assert activity["calls"] == 1
    assert activity["transitions"] == 2
    assert activity["by_status"]["completed"] == 1
    assert activity["by_status"]["waiting"] == 1
    assert activity["avg_wait_minutes"] == 10.0
    assert activity["avg_service_minutes"] == 15.0
    assert body["reconciliation"]["queue_status_sum"] == 2
    sources = {row["source"]: row["count"] for row in activity["by_source"]}
    assert sources == {"appointment": 1, "walk_in": 1}



# ---------------------------------------------------------------------------
# Schedule utilisation (BR §43, "where meaningful for the appointment model")
# ---------------------------------------------------------------------------

def test_utilisation_compares_claimed_seats_with_published_capacity(client):
    # 09:00–10:00 in 15-minute slots = 4 published seats for this weekday only.
    ensure_session(DOCTOR, ORG, BRANCH_A, day_of_week=WEEKDAY,
                   start="09:00", end="10:00", duration=15, capacity=1)
    _appointment("mp23-u1", status="BOOKED")
    _appointment("mp23-u2", status="COMPLETED")
    _appointment("mp23-u3", status="BOOKED")
    with db_session() as s:
        s.add(SlotAllocation(id="mp23-seat1", organization_id=ORG,
                             doctor_id=DOCTOR, appointment_date=DAY,
                             slot_key="09:00", slot_end="09:15",
                             kind="scheduled", seat_number=1,
                             appointment_id="mp23-u1"))
        s.add(SlotAllocation(id="mp23-seat2", organization_id=ORG,
                             doctor_id=DOCTOR, appointment_date=DAY,
                             slot_key="09:15", slot_end="09:30",
                             kind="scheduled", seat_number=1,
                             appointment_id="mp23-u2"))
        # Outside published capacity: an accepted override, counted separately.
        s.add(SlotAllocation(id="mp23-seat3", organization_id=ORG,
                             doctor_id=DOCTOR, appointment_date=DAY,
                             slot_key="UNSCHEDULED", slot_end="",
                             kind="unscheduled", seat_number=1,
                             appointment_id="mp23-u3"))
        s.commit()

    body = _report(client, date=DAY_TEXT).json()
    utilisation = body["utilisation"]
    assert utilisation["capacity"] == 4
    assert utilisation["claimed"] == 2
    assert utilisation["unscheduled"] == 1
    assert utilisation["percent"] == 50.0
    per_doctor = {row["doctor_id"]: row for row in utilisation["by_doctor"]}
    assert per_doctor[DOCTOR]["capacity"] == 4
    assert per_doctor[DOCTOR]["percent"] == 50.0


def test_utilisation_is_null_rather_than_zero_when_nothing_is_published(client):
    _appointment("mp23-n1", status="BOOKED")
    body = _report(client, date="2026-03-11").json()   # a day with no session
    assert body["utilisation"]["capacity"] == 0
    assert body["utilisation"]["percent"] is None, (
        "no published capacity is not 0% utilisation — it is no utilisation figure")


# ---------------------------------------------------------------------------
# Scoping (MP-23 acceptance: org and branch enforced, 404 on violation)
# ---------------------------------------------------------------------------

def test_foreign_branch_is_a_non_disclosing_404(client):
    response = _report(client, who="mp23_desk_a", branch_id=BRANCH_B)
    assert response.status_code == 404, response.text
    assert "mp23-branch-b" not in response.text


def test_branch_scoped_principal_is_narrowed_to_its_own_branch(client):
    _appointment("mp23-sc1", status="BOOKED", branch=BRANCH_A)
    _appointment("mp23-sc2", status="BOOKED", branch=BRANCH_B)

    as_admin = _report(client, who="mp23_admin", date=DAY_TEXT).json()
    assert as_admin["appointments"]["total"] == 2
    assert as_admin["branch_id"] is None

    as_desk = _report(client, who="mp23_desk_a", date=DAY_TEXT).json()
    assert as_desk["branch_id"] == BRANCH_A, "the token's branch is the scope"
    assert as_desk["appointments"]["total"] == 1
    assert as_desk["appointments"]["by_branch"] == [
        {"branch_id": BRANCH_A, "count": 1}]


def test_another_tenants_rows_never_enter_the_report(client):
    ensure_branch("mp23-other-branch", OTHER_ORG)
    ensure_doctor("mp23-other-doc", OTHER_ORG, mobile="01700000203")
    ensure_patient("mp23-other-patient", OTHER_ORG, mobile="01700000204")
    with db_session() as s:
        s.add(Appointment(id="mp23-foreign", organization_id=OTHER_ORG,
                          branch_id="mp23-other-branch",
                          patient_id="mp23-other-patient",
                          doctor_id="mp23-other-doc",
                          appointment_date=DAY, status="BOOKED",
                          booking_source="reception"))
        s.commit()
    _appointment("mp23-own", status="BOOKED")

    body = _report(client, date=DAY_TEXT).json()
    assert body["appointments"]["total"] == 1
    assert [row["doctor_id"] for row in body["appointments"]["by_doctor"]] == [DOCTOR]


def test_unknown_doctor_in_the_tenant_is_a_404(client):
    response = _report(client, date=DAY_TEXT, doctor_id="no-such-doctor")
    assert response.status_code == 404, response.text



# ---------------------------------------------------------------------------
# Empty datasets — a day with nothing in it is still a report
# ---------------------------------------------------------------------------

def test_an_empty_day_reports_zeroes_and_no_utilisation_figure(client):
    """Nothing booked is a real answer: zeros, an empty of rows and no percentage.

    The distinction that matters: ``status_counts`` keeps every lifecycle key at
    zero (so the screen's table does not shift month to month), and utilisation
    returns ``percent: None`` rather than 0 — no published capacity is not the same
    statement as "nothing was used".
    """
    response = _report(client, date=DAY_TEXT)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["appointments"]["total"] == 0
    assert body["appointments"]["by_day"] == []
    assert body["appointments"]["by_doctor"] == []
    assert body["appointments"]["by_branch"] == []
    assert body["booking_sources"] == []
    assert body["walk_ins"] == 0
    assert set(body["status_counts"].values()) == {0}
    assert len(body["status_counts"]) >= 10, "every lifecycle status is reported"
    assert body["br43"] == {"booked": 0, "completed": 0, "cancelled": 0,
                            "no_show": 0, "present": 0}
    assert body["queue_activity"]["entries"] == 0
    assert body["queue_activity"]["avg_wait_minutes"] is None
    assert body["queue_activity"]["avg_service_minutes"] is None
    assert body["utilisation"]["capacity"] == 0
    assert body["utilisation"]["percent"] is None
    assert body["reconciliation"]["appointments_total"] == 0
    assert body["reconciliation"]["queue_entries"] == 0


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------

def test_unpadded_or_impossible_dates_are_refused(client):
    for value in ("2026-3-10", "10-03-2026", "not-a-date", "2026-13-01"):
        response = _report(client, date=value)
        assert response.status_code == 422, (value, response.text)


def test_period_and_day_are_mutually_exclusive(client):
    both = _report(client, date=DAY_TEXT, **{"from_date": DAY_TEXT,
                                            "to_date": DAY_TEXT})
    assert both.status_code == 422
    half = _report(client, **{"from_date": DAY_TEXT})
    assert half.status_code == 422


def test_inverted_and_overlong_periods_are_refused(client):
    inverted = _report(client, **{"from_date": "2026-03-11", "to_date": DAY_TEXT})
    assert inverted.status_code == 422
    overlong = _report(client, **{"from_date": "2024-01-01",
                                 "to_date": "2026-01-02"})
    assert overlong.status_code == 422


def test_a_period_reports_by_day_in_order(client):
    _appointment("mp23-p1", status="BOOKED", day=date(2026, 3, 9))
    _appointment("mp23-p2", status="BOOKED", day=DAY)
    _appointment("mp23-p3", status="BOOKED", day=DAY)

    body = _report(client, **{"from_date": "2026-03-09", "to_date": DAY_TEXT}).json()
    assert body["appointments"]["by_day"] == [
        {"date": "2026-03-09", "count": 1},
        {"date": "2026-03-10", "count": 2},
    ]
    assert body["reconciliation"]["by_day_sum"] == 3


# ---------------------------------------------------------------------------
# Scope limits — BR §43 forbids money and clinical-performance analytics
# ---------------------------------------------------------------------------

#: Words that must not appear in any key of the payload.  BR §43 permits
#: operational counts only; a revenue, settlement or performance field would be
#: an unapproved expansion of the product, so it fails the suite rather than
#: shipping quietly.
FORBIDDEN_KEYS = ("revenue", "billing", "payment", "invoice", "amount",
                  "price", "currency", "profit", "margin", "rating",
                  "performance", "score", "kpi")


def _all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_keys(item)


def test_payload_carries_no_money_or_performance_field(client):
    _appointment("mp23-x1", status="COMPLETED")
    body = _report(client, date=DAY_TEXT).json()
    offenders = sorted({key for key in _all_keys(body)
                        if any(bad in key for bad in FORBIDDEN_KEYS)})
    assert offenders == [], f"BR §43 forbids these figures: {offenders}"

