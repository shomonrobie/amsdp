"""Tests for Appointment Service — BR §16–§20.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined version
was written against the removed in-memory ``_appointments_db``.  This version
drives the real service app against PostgreSQL and reads its assertions back
through ``SessionFactory``, so a green test means the row is in the database —
not in a dict the test itself populated.

Coverage kept identical to the quarantined module (booking, walk-in, validation,
read paths, BR §18 lifecycle) plus the tenant-isolation cases the in-memory
fixtures could not express.

Every test uses its own organization (``legacy-appt-org``) and purges only its
own business rows, so it can run against a shared development database.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment

ORG = "legacy-appt-org"
BR = "legacy-appt-br"
OTHER_ORG = "legacy-appt-other-org"
DOC = "legacy-appt-doc"
PAT = "legacy-appt-pat"
PAT_WALKIN = "legacy-appt-pat-walkin"
PAT_FOREIGN = "legacy-appt-pat-foreign"
RECP = "legacy_appt_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    """Fresh, isolated appointment world for each test."""
    purge_org(ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Appointment", mobile="01700001001")
    ensure_patient(PAT, ORG, name="Appointment Patient", mobile="01700001002")
    ensure_patient(PAT_WALKIN, ORG, name="Walk-in Patient", mobile="01700001003")
    ensure_patient(PAT_FOREIGN, OTHER_ORG, name="Foreign Patient",
                   mobile="01700001004")
    ensure_user(RECP, "receptionist", ORG, BR)
    yield
    # Teardown: leave no business rows behind.  The reference rows created above
    # stay, because the append-only audit trail references them.
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _book(client, *, patient=PAT, doctor=DOC, day="2031-04-15", start="09:00"):
    return client.post("/api/v1/appointments", headers=headers(RECP), json={
        "patient_id": patient, "doctor_id": doctor,
        "appointment_date": day, "start_time": start,
    })


def _rows(org=ORG):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.organization_id == org).all()


class TestAppointmentCreate:
    def test_create_appointment_persists(self, client):
        r = _book(client)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["status"] == "BOOKED"
        assert body["token_number"].startswith("T-")
        # The tenant comes from the token, never from the request body.
        assert body["organization_id"] == ORG
        assert body["branch_id"] == BR
        stored = [a for a in _rows() if a.id == body["id"]]
        assert len(stored) == 1
        assert stored[0].status == "BOOKED"
        assert stored[0].patient_id == PAT

    def test_create_walk_in(self, client):
        r = client.post("/api/v1/appointments/walk-in", headers=headers(RECP),
                        json={"patient_id": PAT_WALKIN, "doctor_id": DOC,
                              "notes": "walk-in"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["appointment_type"] == "walk_in"
        assert body["booking_source"] == "walk_in"
        with db_session() as s:
            row = s.query(Appointment).filter(
                Appointment.id == body["id"]).first()
            assert row is not None and row.appointment_type == "walk_in"

    def test_create_without_patient_422(self, client):
        r = client.post("/api/v1/appointments", headers=headers(RECP), json={
            "patient_id": "", "doctor_id": "", "appointment_date": "2031-04-15",
        })
        assert r.status_code == 422
        assert _rows() == []

    def test_booking_for_a_foreign_patient_is_refused(self, client):
        """A patient from another tenant must not be bookable at all."""
        r = _book(client, patient=PAT_FOREIGN)
        assert r.status_code == 422
        assert r.json()["detail"] == "patient not found"
        assert _rows() == []

    def test_capacity_is_enforced_per_slot(self, client):
        assert _book(client, start="10:00").status_code == 201
        # No schedule exists, so the default slot capacity is one patient.
        r = _book(client, start="10:00")
        assert r.status_code == 422
        assert "capacity" in r.json()["detail"]


class TestAppointmentRead:
    def test_get_appointment(self, client):
        appt_id = _book(client).json()["id"]
        r = client.get(f"/api/v1/appointments/{appt_id}", headers=headers(RECP))
        assert r.status_code == 200
        assert r.json()["id"] == appt_id

    def test_get_missing_404(self, client):
        r = client.get("/api/v1/appointments/nonexistent",
                       headers=headers(RECP))
        assert r.status_code == 404

    def test_foreign_tenant_appointment_is_a_404(self, client):
        """Cross-tenant ids are indistinguishable from unknown ids."""
        appt_id = _book(client).json()["id"]
        ensure_user("legacy_appt_foreign_recp", "receptionist", OTHER_ORG)
        r = client.get(f"/api/v1/appointments/{appt_id}",
                       headers=headers("legacy_appt_foreign_recp"))
        assert r.status_code == 404

    def test_list_by_doctor_and_date(self, client):
        appt_id = _book(client, day="2031-04-16").json()["id"]
        r = client.get("/api/v1/appointments",
                       params={"doctor_id": DOC, "date": "2031-04-16"},
                       headers=headers(RECP))
        assert r.status_code == 200
        assert [a["id"] for a in r.json()] == [appt_id]

    def test_list_requires_authentication(self, client):
        assert client.get("/api/v1/appointments").status_code == 401


class TestAppointmentStatus:
    def test_booked_to_confirmed(self, client):
        appt_id = _book(client).json()["id"]
        r = client.patch(f"/api/v1/appointments/{appt_id}/status",
                         headers=headers(RECP), json={"status": "CONFIRMED"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "CONFIRMED"
        with db_session() as s:
            assert s.query(Appointment).filter(
                Appointment.id == appt_id).first().status == "CONFIRMED"

    def test_invalid_transition_rejected(self, client):
        appt_id = _book(client).json()["id"]
        r = client.patch(f"/api/v1/appointments/{appt_id}/status",
                         headers=headers(RECP), json={"status": "COMPLETED"})
        assert r.status_code == 422
        assert "cannot transition" in r.json()["detail"]

    def test_full_lifecycle(self, client):
        appt_id = _book(client).json()["id"]
        for status in ("CONFIRMED", "CHECKED_IN", "IN_QUEUE",
                       "IN_CONSULTATION", "COMPLETED"):
            r = client.patch(f"/api/v1/appointments/{appt_id}/status",
                             headers=headers(RECP), json={"status": status})
            assert r.status_code == 200, (status, r.text)
            assert r.json()["status"] == status
        with db_session() as s:
            row = s.query(Appointment).filter(Appointment.id == appt_id).first()
            # Every transition is retained, not just the last one
            # (Sequence 4 finding SEQ4-HISTORY-P0).
            assert [h["to"] for h in row.status_history] == [
                "BOOKED", "CONFIRMED", "CHECKED_IN", "IN_QUEUE",
                "IN_CONSULTATION", "COMPLETED"]
