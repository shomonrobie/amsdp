"""Check-in authorization matrix (owner decision Q3).

Q3 makes ``appointment.check_in`` its own capability instead of a side effect of
``appointment.modify``.  The capability is held by:

* the front desk and the organization/branch administrators — for the branch
  they work in;
* a **doctor** for their own patients (and nobody else's);
* an **assistant** for the doctor(s) they are explicitly assigned to.

The assignment half of that rule is enforced by the route
(``AuthContext.can_access_doctor``), not by the role list, and it fails closed: a
doctor or assistant with no active assignment can check nobody in.  Every refusal
is the same non-disclosing ``404`` a foreign id produces, so a probe cannot learn
that an appointment exists.

The matrix below pins all twelve outcomes on the appointment door, then checks
that the queue door answers identically — the two doors are the finding's point.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_all_day_session,
                                ensure_branch, ensure_doctor, ensure_org,
                                ensure_patient, ensure_schedule, ensure_user,
                                headers, load_app, purge_org)
from common.models import Appointment, QueueEntry, StaffDoctorAssignment, StaffUser

ORG = "chk-org"
BR = "chk-br"
BR2 = "chk-br2"
DOC = "chk-doc"
DOC2 = "chk-doc2"
PAT = "chk-pat"

SUPER = "chk_super"
ORGADM = "chk_orgadm"
BRADM = "chk_bradm"
RECP = "chk_recp"
RECP2 = "chk_recp2"
DOC_USER = "chk_docuser"
DOC_USER_X = "chk_docuser_x"
DOC_USER_NONE = "chk_docuser_none"
ASSIST = "chk_assist"
ASSIST_X = "chk_assist_x"
ASSIST_NONE = "chk_assist_none"

DAY = "2031-06-05"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Own", mobile="01700005001")
    ensure_doctor(DOC2, ORG, name="Dr. Other", mobile="01700005002")
    ensure_patient(PAT, ORG, name="Checked In Patient", mobile="01700005003")
    ensure_schedule(DOC, ORG, BR)
    ensure_all_day_session(DOC, ORG, BR)
    ensure_schedule(DOC2, ORG, BR)
    ensure_all_day_session(DOC2, ORG, BR)
    ensure_user(SUPER, "super_admin", ORG, BR)
    ensure_user(ORGADM, "org_admin", ORG, BR)
    ensure_user(BRADM, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(RECP2, "receptionist", ORG, BR2)
    ensure_user(DOC_USER, "doctor", ORG, BR)
    ensure_user(DOC_USER_X, "doctor", ORG, BR)
    ensure_user(DOC_USER_NONE, "doctor", ORG, BR)
    ensure_user(ASSIST, "assistant", ORG, BR)
    ensure_user(ASSIST_X, "assistant", ORG, BR)
    ensure_user(ASSIST_NONE, "assistant", ORG, BR)
    _assign(DOC_USER, DOC)
    _assign(DOC_USER_X, DOC2)
    _assign(ASSIST, DOC)
    _assign(ASSIST_X, DOC2)
    yield
    purge_org(ORG)


def _assign(username, doctor_id):
    """Create the explicit staff→doctor assignment the route checks."""
    with db_session() as s:
        user = s.query(StaffUser).filter(StaffUser.username == username).one()
        s.query(StaffDoctorAssignment).filter(
            StaffDoctorAssignment.staff_user_id == user.id).delete(
            synchronize_session=False)
        s.add(StaffDoctorAssignment(
            id=f"chk-assign-{username}", staff_user_id=user.id,
            doctor_id=doctor_id, organization_id=ORG, status="active"))
        s.commit()


def _confirmed_booking(client, *, doctor=DOC):
    """A CONFIRMED appointment — ``BOOKED`` is not a check-in source."""
    booked = client.post("/api/v1/appointments", headers=headers(RECP), json={
        "patient_id": PAT, "doctor_id": doctor, "appointment_date": DAY,
        "start_time": "09:00"})
    assert booked.status_code == 201, booked.text
    appointment_id = booked.json()["id"]
    confirmed = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        headers=headers(RECP), json={"status": "CONFIRMED"})
    assert confirmed.status_code == 200, confirmed.text
    return appointment_id


def _check_in(client, appointment_id, user):
    return client.post(f"/api/v1/appointments/{appointment_id}/check-in",
                       headers=headers(user),
                       json={"status": "CHECKED_IN"})


def _status(appointment_id):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.id == appointment_id).one().status


def _queue_rows(appointment_id):
    with db_session() as s:
        return s.query(QueueEntry).filter(
            QueueEntry.appointment_id == appointment_id).all()


def _assert_allowed(client, user, *, doctor=DOC):
    appointment_id = _confirmed_booking(client, doctor=doctor)
    response = _check_in(client, appointment_id, user)
    assert response.status_code == 200, (user, response.text)
    assert response.json()["status"] == "CHECKED_IN"
    assert _status(appointment_id) == "CHECKED_IN"
    assert len(_queue_rows(appointment_id)) == 1
    return appointment_id


def _assert_refused(client, user, expected=404, *, doctor=DOC):
    appointment_id = _confirmed_booking(client, doctor=doctor)
    response = _check_in(client, appointment_id, user)
    assert response.status_code == expected, (user, response.text)
    assert _status(appointment_id) == "CONFIRMED", "a refused check-in wrote"
    assert _queue_rows(appointment_id) == []
    return response


class TestCheckInMatrix:
    """Twelve outcomes: who may check a patient in, and what a refusal looks like."""

    def test_unauthenticated_is_401(self, client):
        appointment_id = _confirmed_booking(client)
        response = client.post(
            f"/api/v1/appointments/{appointment_id}/check-in",
            json={"status": "CHECKED_IN"})
        assert response.status_code == 401
        assert _status(appointment_id) == "CONFIRMED"

    def test_super_admin_may_check_in(self, client):
        _assert_allowed(client, SUPER)

    def test_org_admin_may_check_in(self, client):
        _assert_allowed(client, ORGADM)

    def test_branch_admin_may_check_in(self, client):
        _assert_allowed(client, BRADM)

    def test_receptionist_may_check_in_in_own_branch(self, client):
        _assert_allowed(client, RECP)

    def test_receptionist_from_another_branch_is_404(self, client):
        """BR2's desk cannot touch a BR appointment — fail closed, unannounced."""
        _assert_refused(client, RECP2)

    def test_doctor_may_check_in_own_patient(self, client):
        _assert_allowed(client, DOC_USER)

    def test_doctor_without_assignment_is_404(self, client):
        """``can_access_doctor`` fails closed when no assignment is loaded."""
        _assert_refused(client, DOC_USER_NONE)

    def test_doctor_cannot_check_in_another_doctors_patient(self, client):
        _assert_refused(client, DOC_USER_X)

    def test_assistant_assigned_to_the_doctor_may_check_in(self, client):
        _assert_allowed(client, ASSIST)

    def test_assistant_assigned_to_another_doctor_is_404(self, client):
        _assert_refused(client, ASSIST_X)

    def test_assistant_without_assignment_is_404(self, client):
        _assert_refused(client, ASSIST_NONE)


class TestTheQueueDoorAgrees:
    """F-07's actual claim: both doors are behind the same authority."""

    def test_the_queue_door_refuses_an_unassigned_assistant(self):
        appointment_client = TestClient(load_app("appointment"))
        queue_client = TestClient(load_app("queuing"))
        appointment_id = _confirmed_booking(appointment_client)
        response = queue_client.post(
            "/api/v1/queue/check-in", headers=headers(ASSIST_NONE),
            json={"appointment_id": appointment_id})
        assert response.status_code == 404, response.text
        assert _status(appointment_id) == "CONFIRMED"
        assert _queue_rows(appointment_id) == []

    def test_the_queue_door_admits_an_assigned_assistant(self):
        appointment_client = TestClient(load_app("appointment"))
        queue_client = TestClient(load_app("queuing"))
        appointment_id = _confirmed_booking(appointment_client)
        response = queue_client.post(
            "/api/v1/queue/check-in", headers=headers(ASSIST),
            json={"appointment_id": appointment_id})
        assert response.status_code == 201, response.text
        assert _status(appointment_id) == "IN_QUEUE"
        rows = _queue_rows(appointment_id)
        assert len(rows) == 1 and rows[0].status == "waiting"

    def test_the_queue_door_refuses_a_receptionist_from_another_branch(self):
        appointment_client = TestClient(load_app("appointment"))
        queue_client = TestClient(load_app("queuing"))
        appointment_id = _confirmed_booking(appointment_client)
        response = queue_client.post(
            "/api/v1/queue/check-in", headers=headers(RECP2),
            json={"appointment_id": appointment_id})
        assert response.status_code == 404, response.text
        assert _queue_rows(appointment_id) == []
