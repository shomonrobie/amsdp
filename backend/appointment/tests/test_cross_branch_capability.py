"""Cross-branch booking through an explicit grant (owner decision Q4).

The scenario Q4 was decided for: a central receptionist books a patient into a
doctor's *second* branch — a branch she may book into but must not be able to
read.  The role matrix cannot express that, so it is a named capability
(``appointment.book_cross_branch``) granted to one person by an administrator
and revocable on its own.

What this module proves, end to end and through the real HTTP surface:

* without the grant the other branch's published hours are simply not reachable
  (the booking is refused and nothing is written there);
* with the grant the booking succeeds, is filed in the other branch, and the
  creation event records ``cross_branch: true``;
* the grant widens **booking only** — reading the appointment still answers the
  non-disclosing ``404`` a foreign branch always produces;
* revocation takes effect on the very next request, with no token reissue and no
  cache to clear.

The administrative surface of the grant itself (who may grant, audit, refusal
codes) is covered in ``identity/tests/test_capability_grants.py``.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_all_day_session,
                                ensure_branch, ensure_doctor, ensure_org,
                                ensure_patient, ensure_schedule, ensure_user,
                                headers, load_app, purge_org)
from common.models import Appointment, AuditEvent, StaffUser

ORG = "xb-org"
BR = "xb-br"
BR2 = "xb-br2"
DOC2 = "xb-doc2"
PAT = "xb-pat"
RECP = "xb_recp"
ADM = "xb_adm"
CAPABILITY = "appointment.book_cross_branch"
DAY = "2031-06-06"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(scope="module")
def identity():
    return TestClient(load_app("identity"))


@pytest.fixture(autouse=True)
def _world(client, identity):
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_doctor(DOC2, ORG, name="Dr. Two Branches", mobile="01700006001")
    ensure_patient(PAT, ORG, name="Cross Branch Patient", mobile="01700006002")
    # The doctor works only in BR2, so any BR-scoped booking has to cross.
    ensure_schedule(DOC2, ORG, BR2)
    ensure_all_day_session(DOC2, ORG, BR2)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(ADM, "org_admin", ORG, BR)
    yield
    purge_org(ORG)


def _user_id(username):
    with db_session() as s:
        return s.query(StaffUser).filter(
            StaffUser.username == username).one().id


def _grant(identity):
    response = identity.post(
        f"/api/v1/staff/users/{_user_id(RECP)}/capabilities",
        headers=headers(ADM),
        json={"capability": CAPABILITY, "reason": "central reception"})
    assert response.status_code == 201, response.text
    return response.json()


def _revoke(identity):
    response = identity.delete(
        f"/api/v1/staff/users/{_user_id(RECP)}/capabilities/{CAPABILITY}",
        headers=headers(ADM))
    assert response.status_code == 200, response.text
    return response.json()


def _book(client, *, start="09:00"):
    return client.post("/api/v1/appointments", headers=headers(RECP), json={
        "patient_id": PAT, "doctor_id": DOC2, "appointment_date": DAY,
        "start_time": start})


def _rows_in_other_branch():
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.organization_id == ORG,
            Appointment.branch_id == BR2).all()


def _created_events():
    with db_session() as s:
        return s.query(AuditEvent).filter(
            AuditEvent.action == "appointment.created",
            AuditEvent.organization_id == ORG).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()


class TestWithoutTheGrant:
    def test_the_other_branch_is_unreachable(self, client):
        """Fail closed: the BR2 hours are not visible, so nothing is booked."""
        response = _book(client)
        assert response.status_code == 422, response.text
        assert "unscheduled_requires_override" in response.json()["detail"]
        assert _rows_in_other_branch() == []


class TestWithTheGrant:
    def test_the_booking_crosses_the_branch_boundary(self, client, identity):
        _grant(identity)
        response = _book(client)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["branch_id"] == BR2
        assert body["organization_id"] == ORG
        rows = _rows_in_other_branch()
        assert [row.id for row in rows] == [body["id"]]

    def test_the_crossing_is_audited_as_such(self, client, identity):
        _grant(identity)
        booked = _book(client)
        assert booked.status_code == 201, booked.text
        event = _created_events()[-1]
        assert event.target_id == booked.json()["id"]
        assert event.after["cross_branch"] is True
        assert event.branch_id == BR2
        assert event.actor_id == _user_id(RECP)

    def test_the_grant_does_not_unlock_reading(self, client, identity):
        """Booking authority is not read authority — the read still 404s."""
        _grant(identity)
        booked = _book(client)
        assert booked.status_code == 201, booked.text
        appointment_id = booked.json()["id"]
        detail = client.get(f"/api/v1/appointments/{appointment_id}",
                            headers=headers(RECP))
        assert detail.status_code == 404, detail.text
        # The branch's own staff can read it, so the row really is there.
        assert client.get(f"/api/v1/appointments/{appointment_id}",
                          headers=headers(ADM)).status_code == 200

    def test_revocation_applies_to_the_next_request(self, client, identity):
        """No token reissue, no cache: the next call is refused again."""
        _grant(identity)
        assert _book(client).status_code == 201
        _revoke(identity)
        before = len(_rows_in_other_branch())
        refused = _book(client, start="09:15")
        assert refused.status_code == 422, refused.text
        assert len(_rows_in_other_branch()) == before == 1
