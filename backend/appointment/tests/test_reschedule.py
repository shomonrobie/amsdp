"""Reschedule and edge-case tests for the Appointment Service.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined version
used the removed ``_appointments_db`` fixture.  These scenarios assert on the
database, because a reschedule is two rows plus a link between them — exactly
the kind of write an in-memory fixture used to hide.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment

ORG = "legacy-resched-org"
BR = "legacy-resched-br"
DOC = "legacy-resched-doc"
PAT = "legacy-resched-pat"
RECP = "legacy_resched_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    ensure_org(ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Reschedule", mobile="01700002001")
    ensure_patient(PAT, ORG, name="Reschedule Patient", mobile="01700002002")
    ensure_user(RECP, "receptionist", ORG, BR)
    yield
    # Teardown: no business rows left behind; reference rows stay (audit).
    purge_org(ORG)


def _book(client, start="09:00"):
    r = client.post("/api/v1/appointments", headers=headers(RECP), json={
        "patient_id": PAT, "doctor_id": DOC,
        "appointment_date": "2031-05-15", "start_time": start})
    assert r.status_code == 201, r.text
    return r.json()


def _row(appointment_id):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.id == appointment_id).first()


def _complete(client, appointment_id):
    for status in ("CONFIRMED", "CHECKED_IN", "IN_QUEUE",
                   "IN_CONSULTATION", "COMPLETED"):
        r = client.patch(f"/api/v1/appointments/{appointment_id}/status",
                         headers=headers(RECP), json={"status": status})
        assert r.status_code == 200, r.text


class TestReschedule:
    def test_reschedule_creates_linked_appointment(self, client):
        original = _book(client)
        r = client.post(f"/api/v1/appointments/{original['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": "2031-05-16",
                              "reason": "patient request"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["original_appointment_id"] == original["id"]
        assert body["new_appointment_id"] != original["id"]

        old = _row(original["id"])
        new = _row(body["new_appointment_id"])
        # Both rows really exist in the database and point at each other.
        assert old.status == "RESCHEDULED"
        assert old.rescheduled_to == new.id
        assert new.status == "BOOKED"
        assert new.rescheduled_from == old.id
        assert str(new.appointment_date) == "2031-05-16"

    def test_reschedule_records_the_previous_status(self, client):
        original = _book(client)
        client.post(f"/api/v1/appointments/{original['id']}/reschedule",
                    headers=headers(RECP),
                    json={"new_date": "2031-05-17", "reason": "clash"})
        last = _row(original["id"]).status_history[-1]
        assert (last["from"], last["to"]) == ("BOOKED", "RESCHEDULED")

    def test_cannot_reschedule_completed(self, client):
        original = _book(client)
        _complete(client, original["id"])
        r = client.post(f"/api/v1/appointments/{original['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": "2031-05-16", "reason": "test"})
        assert r.status_code == 422
        assert "cannot reschedule" in r.json()["detail"]

    def test_cannot_reschedule_cancelled(self, client):
        original = _book(client)
        r = client.post(f"/api/v1/appointments/{original['id']}/cancel",
                        headers=headers(RECP),
                        json={"status": "CANCELLED", "reason": "changed mind"})
        assert r.status_code == 200, r.text
        again = client.post(
            f"/api/v1/appointments/{original['id']}/reschedule",
            headers=headers(RECP),
            json={"new_date": "2031-05-16", "reason": "test"})
        assert again.status_code == 422

    def test_cancel_requires_a_reason(self, client):
        original = _book(client)
        r = client.post(f"/api/v1/appointments/{original['id']}/cancel",
                        headers=headers(RECP), json={"status": "CANCELLED"})
        assert r.status_code == 422
        assert _row(original["id"]).status == "BOOKED"

    def test_reschedule_rejects_an_invalid_date(self, client):
        original = _book(client)
        r = client.post(f"/api/v1/appointments/{original['id']}/reschedule",
                        headers=headers(RECP),
                        json={"new_date": "16/05/2031", "reason": "typo"})
        assert r.status_code == 422
