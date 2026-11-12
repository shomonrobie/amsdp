"""Cross-service end-to-end test — the AMSDP MVP workflow, one token at a time.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined module
imported eight services by file path, reached into their private in-memory dicts
(``_users_db``, ``_orgs_db``, ``_appointments_db``, …), cleared them between
tests, and called the APIs without credentials.  The dicts no longer exist and
every route now requires a permission, so the module could neither import nor
pass.

This version walks the *real* workflow across service boundaries, exactly as the
browser does:

    login → validate → create staff → create doctor → register patient
    → schedule → available slots → book → check in → call/consult/complete
    → audit trail → tenant isolation

Each request is authenticated with a real signed JWT and each service keeps its
own app instance (no shared process state), so a green run means the services
agree on the database, the token contract and the audit trail — not that a
dictionary was mutated.

Coverage note.  The legacy module's ``test_13_audit`` posted an audit event by
hand (``POST /api/v1/audit``).  That route does not exist and must not: the audit
trail is written by the services themselves (``common.audit.record_audit``) and
is append-only, so a client cannot fabricate events.  Instead the rewritten step
reads the events the workflow actually produced.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (PASSWORD, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org, uniq)

ORG = "legacy-e2e-org"
BR = "legacy-e2e-br"
OTHER_ORG = "legacy-e2e-other"
OTHER_BR = "legacy-e2e-other-br"
DOC_SEED = "legacy-e2e-doc-seed"
PAT_SEED = "legacy-e2e-pat-seed"
ORG_ADMIN = "legacy_e2e_org_admin"
ADMIN = "legacy_e2e_admin"
OTHER_ADMIN = "legacy_e2e_other_admin"

BOOKING_DATE = "2026-04-15"

#: Values carried between ordered steps, as the browser carries a session.
STATE: dict = {}


@pytest.fixture(scope="module", autouse=True)
def _world():
    # Purge first: purge_org removes this organization's patients and schedules,
    # so reference rows are (re)created afterwards and are present for the flow.
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_doctor(DOC_SEED, ORG)
    ensure_patient(PAT_SEED, ORG)
    ensure_user(ORG_ADMIN, "org_admin", ORG, BR)
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "branch_admin", OTHER_ORG, OTHER_BR)
    STATE.clear()
    yield
    # Teardown (end of module): no business rows left behind; reference rows
    # stay, because the append-only audit trail references them.
    purge_org(ORG)
    purge_org(OTHER_ORG)


@pytest.fixture(scope="module")
def svc():
    """One client per service, each with its own imported app."""
    names = ("identity", "organization", "patient", "doctor", "scheduling",
             "appointment", "queuing", "audit")
    clients = {name: TestClient(load_app(name)) for name in names}

    class Services:
        identity = clients["identity"]
        organization = clients["organization"]
        patient = clients["patient"]
        doctor = clients["doctor"]
        scheduling = clients["scheduling"]
        appointment = clients["appointment"]
        queuing = clients["queuing"]
        audit = clients["audit"]

    return Services


def _auth(user_key: str) -> dict:
    return headers(STATE[user_key])


class TestMvpWorkflow:
    """Ordered: each step depends on the artefacts of the one before it."""

    def test_01_login(self, svc):
        STATE["org_admin"], STATE["admin"] = ORG_ADMIN, ADMIN

        wrong = svc.identity.post("/api/v1/staff/login", json={
            "username": ADMIN, "password": "definitely-not-the-password"})
        assert wrong.status_code == 401

        good = svc.identity.post("/api/v1/staff/login", json={
            "username": ADMIN, "password": PASSWORD})
        assert good.status_code == 200, good.text
        body = good.json()
        assert body["token"]
        assert body["user"]["username"] == ADMIN
        assert body["user"]["role"] == "branch_admin"
        assert body["user"]["organization_id"] == ORG

    def test_02_validate_reports_the_token_tenant(self, svc):
        r = svc.identity.get("/api/v1/staff/validate", headers=_auth("admin"))
        assert r.status_code == 200
        assert r.json()["organization_id"] == ORG
        assert r.json()["role"] == "branch_admin"
        assert r.json()["valid"] is True

    def test_03_create_staff_through_the_api(self, svc):
        username = uniq("e2e_recp")
        r = svc.identity.post("/api/v1/staff/users", headers=_auth("org_admin"),
                              json={"organization_id": ORG, "branch_id": BR,
                                    "username": username, "password": "recppass1",
                                    "display_name": "E2E Reception",
                                    "role": "receptionist"})
        assert r.status_code == 201, r.text
        assert r.json()["role"] == "receptionist"
        STATE["receptionist"] = username
        STATE["receptionist_id"] = r.json()["user_id"]

        # The created credential really works: log in as the new user.
        login = svc.identity.post("/api/v1/staff/login",
                                  json={"username": username,
                                        "password": "recppass1"})
        assert login.status_code == 200, login.text
        assert login.json()["user"]["role"] == "receptionist"

    def test_04_staff_cannot_be_created_in_another_org(self, svc):
        r = svc.identity.post("/api/v1/staff/users", headers=_auth("org_admin"),
                              json={"organization_id": OTHER_ORG,
                                    "username": uniq("e2e_foreign"),
                                    "password": "recppass1",
                                    "display_name": "Foreign",
                                    "role": "receptionist"})
        assert r.status_code == 422

    def test_05_create_doctor(self, svc):
        r = svc.doctor.post("/api/v1/doctors", headers=_auth("admin"), json={
            "name": "Dr. E2E", "mobile": "01811111111",
            "speciality": "Medicine", "branch_ids": [BR]})
        assert r.status_code == 201, r.text
        STATE["doctor_id"] = r.json()["id"]
        assert r.json()["organization_id"] == ORG

    def test_06_create_doctor_staff_user_linked_to_the_doctor(self, svc):
        username = uniq("e2e_doc")
        r = svc.identity.post("/api/v1/staff/users", headers=_auth("org_admin"),
                              json={"organization_id": ORG, "branch_id": BR,
                                    "doctor_id": STATE["doctor_id"],
                                    "username": username, "password": "docpass12",
                                    "display_name": "Dr. E2E", "role": "doctor"})
        assert r.status_code == 201, r.text
        STATE["doctor"] = username
        login = svc.identity.post("/api/v1/staff/login",
                                  json={"username": username,
                                        "password": "docpass12"})
        assert login.status_code == 200, login.text

    def test_07_register_patient(self, svc):
        r = svc.patient.post("/api/v1/patients", headers=_auth("receptionist"),
                             json={"name": "Jamila Begum", "mobile": "01822222222",
                                   "sex": "female", "address": "Mirpur"})
        assert r.status_code == 201, r.text
        STATE["patient_id"] = r.json()["patient"]["id"]
        assert r.json()["duplicates"] == []

    def test_08_create_schedule(self, svc):
        r = svc.scheduling.post("/api/v1/schedules", headers=_auth("admin"), json={
            "doctor_id": STATE["doctor_id"], "organization_id": ORG,
            "branch_id": BR, "effective_from": "2026-01-01",
            "slot_templates": [{"day_of_week": 0, "start_time": "09:00",
                                "end_time": "12:00",
                                "slot_duration_minutes": 15,
                                "max_patients": 4}]})
        assert r.status_code == 201, r.text
        STATE["schedule_id"] = r.json()["id"]

    def test_09_available_slots(self, svc):
        r = svc.scheduling.get(
            f"/api/v1/schedules/{STATE['schedule_id']}/available-slots",
            params={"date_str": BOOKING_DATE}, headers=_auth("receptionist"))
        assert r.status_code == 200, r.text
        slots = r.json()["slots"]
        # 09:00–12:00 in 15-minute steps is twelve slots.
        assert len(slots) == 12
        assert slots[0]["start_time"] == "09:00"
        assert slots[0]["available"] == 4

    def test_10_book_an_appointment(self, svc):
        r = svc.appointment.post("/api/v1/appointments",
                                 headers=_auth("receptionist"), json={
                                     "organization_id": ORG, "branch_id": BR,
                                     "patient_id": STATE["patient_id"],
                                     "doctor_id": STATE["doctor_id"],
                                     "appointment_date": BOOKING_DATE,
                                     "start_time": "09:00"})
        assert r.status_code == 201, r.text
        body = r.json()
        STATE["appointment_id"] = body["id"]
        assert body["status"] == "BOOKED"
        assert body["organization_id"] == ORG
        assert body["token_number"].startswith("T-")
        assert body["serial_number"] == 1

    def test_11_the_slot_is_now_taken(self, svc):
        r = svc.scheduling.get(
            f"/api/v1/schedules/{STATE['schedule_id']}/available-slots",
            params={"date_str": BOOKING_DATE}, headers=_auth("admin"))
        first = r.json()["slots"][0]
        assert first["booked"] == 1
        assert first["available"] == 3

    def test_12_check_in_puts_the_patient_in_the_queue(self, svc):
        r = svc.queuing.post("/api/v1/queue/check-in",
                             headers=_auth("receptionist"),
                             json={"appointment_id": STATE["appointment_id"]})
        assert r.status_code == 201, r.text
        entry = r.json()
        STATE["queue_entry_id"] = entry["id"]
        assert entry["position"] == 1
        assert entry["status"] == "waiting"
        assert entry["entry_source"] == "appointment"
        assert entry["token"].startswith("T-")
        # Check-in moves the appointment into the queue, service-side.
        appt = svc.appointment.get(
            f"/api/v1/appointments/{STATE['appointment_id']}",
            headers=_auth("admin")).json()
        assert appt["status"] == "IN_QUEUE"

    def test_13_double_check_in_is_rejected(self, svc):
        r = svc.queuing.post("/api/v1/queue/check-in",
                             headers=_auth("receptionist"),
                             json={"appointment_id": STATE["appointment_id"]})
        assert r.status_code == 422

    def test_14_queue_lifecycle_completes_the_visit(self, svc):
        entry_id = STATE["queue_entry_id"]
        call = svc.queuing.patch(f"/api/v1/queue/{entry_id}",
                                 headers=_auth("receptionist"),
                                 json={"action": "call"})
        assert call.status_code == 200, call.text
        assert call.json()["status"] == "called"

        # Reception cannot start a consultation — that is the doctor's step.
        assert svc.queuing.patch(f"/api/v1/queue/{entry_id}",
                                 headers=_auth("receptionist"),
                                 json={"action": "start_consultation"}
                                 ).status_code == 403

        start = svc.queuing.patch(f"/api/v1/queue/{entry_id}",
                                  headers=_auth("doctor"),
                                  json={"action": "start_consultation"})
        assert start.status_code == 200, start.text
        assert start.json()["status"] == "in_consultation"

        done = svc.queuing.patch(f"/api/v1/queue/{entry_id}",
                                 headers=_auth("doctor"),
                                 json={"action": "complete_consultation"})
        assert done.status_code == 200, done.text
        assert done.json()["status"] == "completed"
        history = [h["to"] for h in done.json()["status_history"]]
        assert history == ["waiting", "called", "in_consultation", "completed"]

        appt = svc.appointment.get(
            f"/api/v1/appointments/{STATE['appointment_id']}",
            headers=_auth("admin")).json()
        assert appt["status"] == "COMPLETED"

    def test_15_completed_entry_accepts_no_further_action(self, svc):
        r = svc.queuing.patch(f"/api/v1/queue/{STATE['queue_entry_id']}",
                              headers=_auth("receptionist"),
                              json={"action": "call"})
        assert r.status_code == 422

    def test_16_the_audit_trail_records_the_workflow(self, svc):
        appt_events = svc.audit.get(
            f"/api/v1/audit/{STATE['appointment_id']}",
            headers=_auth("admin"))
        assert appt_events.status_code == 200, appt_events.text
        assert "appointment.created" in {e["action"] for e in appt_events.json()}

        entry_events = svc.audit.get(
            f"/api/v1/audit/{STATE['queue_entry_id']}",
            headers=_auth("admin")).json()
        actions = {e["action"] for e in entry_events}
        assert {"queue.checkin", "queue.call", "queue.start_consultation",
                "queue.complete_consultation"} <= actions
        for event in entry_events:
            assert event["organization_id"] == ORG
            assert event["target_id"] == STATE["queue_entry_id"]

    def test_17_org_audit_feed_is_tenant_scoped(self, svc):
        r = svc.audit.get(f"/api/v1/audit/organization/{ORG}",
                          headers=_auth("admin"))
        assert r.status_code == 200
        events = r.json()
        assert events, "the workflow must have produced audit events"
        assert {e["organization_id"] for e in events} == {ORG}
        # Newest first (BR Part X: the trail is read chronologically, not rewritten).
        timestamps = [e["timestamp"] for e in events]
        assert timestamps == sorted(timestamps, reverse=True)

        foreign = svc.audit.get(f"/api/v1/audit/organization/{OTHER_ORG}",
                                headers=_auth("admin"))
        assert foreign.status_code == 404

    def test_18_audit_requires_the_permission(self, svc):
        r = svc.audit.get(f"/api/v1/audit/{STATE['appointment_id']}",
                          headers=_auth("receptionist"))
        assert r.status_code == 403
        assert svc.audit.get(f"/api/v1/audit/{STATE['appointment_id']}").status_code == 401

    def test_19_other_tenants_see_nothing(self, svc):
        STATE["other_admin"] = OTHER_ADMIN
        appt = svc.appointment.get(
            f"/api/v1/appointments/{STATE['appointment_id']}",
            headers=_auth("other_admin"))
        assert appt.status_code == 404
        # An unknown target and a foreign target are indistinguishable.
        events = svc.audit.get(
            f"/api/v1/audit/{STATE['appointment_id']}",
            headers=_auth("other_admin"))
        assert events.status_code == 200
        assert events.json() == []

    def test_20_staff_user_listing_is_org_scoped(self, svc):
        r = svc.identity.get("/api/v1/staff/users", headers=_auth("org_admin"))
        assert r.status_code == 200
        assert {u["organization_id"] for u in r.json()} == {ORG}

    def test_21_permission_checks(self, svc):
        """The RBAC matrix as the services enforce it (BR §8)."""
        url = "/api/v1/staff/check-permission"
        allowed = svc.identity.post(url, headers=_auth("org_admin"), json={
            "user_id": STATE["receptionist_id"], "resource": "patient.create"})
        assert allowed.status_code == 200
        assert allowed.json()["authorized"] is True

        denied = svc.identity.post(url, headers=_auth("org_admin"), json={
            "user_id": STATE["receptionist_id"], "resource": "org.manage"})
        assert denied.status_code == 200
        assert denied.json()["authorized"] is False

        foreign = svc.identity.post(url, headers=_auth("other_admin"), json={
            "user_id": STATE["receptionist_id"], "resource": "patient.create"})
        assert foreign.status_code == 404
