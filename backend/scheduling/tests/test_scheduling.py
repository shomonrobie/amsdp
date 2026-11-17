"""Tests for the Scheduling Service — BR §14–§15.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined module
imported ``scheduling.main._schedules_db`` (gone) and called every route without
credentials; ``POST /api/v1/schedules`` now requires ``schedule.*``, so those
calls returned 401 instead of exercising the handler.

Two route contracts changed after the quarantined module was written and the
assertions below state the current rules:

* ``organization_id`` in the request body is **ignored** — the schedule is
  written under the caller's token tenant (``.clinerules`` §3).
* ``GET /api/v1/schedules`` filters by ``doctor_id`` / ``branch_id`` only and is
  always scoped to the caller's organization; there is no ``organization_id``
  query parameter to spoof.

Slot availability is asserted against real appointment rows, so the "booked"
arithmetic is verified rather than assumed.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment, Schedule

ORG = "legacy-sch-org"
BR = "legacy-sch-br"
OTHER_ORG = "legacy-sch-other-org"
OTHER_BR = "legacy-sch-other-br"
DOC = "legacy-sch-doc"
OTHER_DOC = "legacy-sch-other-doc"
PAT = "legacy-sch-pat"
ADMIN = "legacy_sch_admin"
OTHER_ADMIN = "legacy_sch_other_admin"
RECP = "legacy_sch_recp"
DOC_USER = "legacy_sch_doc_user"

MORNING = [{"day_of_week": 0, "start_time": "09:00", "end_time": "10:00",
            "slot_duration_minutes": 15, "max_patients": 2}]


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("scheduling"))


@pytest.fixture(autouse=True)
def _world(client):
    # Purge first, then (re)create the reference rows this test needs: purge_org
    # removes the organization's patients, so a patient seeded before the purge
    # would be gone by the time a test books against it.
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_doctor(DOC, ORG, name="Dr. Sched")
    ensure_doctor(OTHER_DOC, OTHER_ORG, name="Dr. Other", mobile="01700000001")
    ensure_patient(PAT, ORG)
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "branch_admin", OTHER_ORG, OTHER_BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(DOC_USER, "doctor", ORG, BR)
    yield
    # Teardown: no business rows left behind; reference rows stay (audit).
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _create(client, user=ADMIN, doctor_id=DOC, templates=None, **extra):
    body = {"doctor_id": doctor_id, "organization_id": ORG, "branch_id": BR,
            "effective_from": "2026-01-01",
            "slot_templates": MORNING if templates is None else templates}
    body.update(extra)
    return client.post("/api/v1/schedules", headers=headers(user), json=body)


class TestScheduleCreate:
    def test_create_schedule(self, client):
        r = _create(client)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["doctor_id"] == DOC
        assert body["branch_id"] == BR
        assert body["appointment_model"] == "time_slot"
        assert body["status"] == "active"
        assert body["slot_templates"][0]["start_time"] == "09:00"
        assert body["effective_from"] == "2026-01-01"
        with db_session() as s:
            row = s.query(Schedule).filter(Schedule.id == body["id"]).first()
            assert row is not None and row.doctor_id == DOC

    def test_body_organization_id_is_ignored(self, client):
        """The tenant is the token's, even when the body claims another org."""
        r = _create(client, organization_id=OTHER_ORG)
        assert r.status_code == 201, r.text
        assert r.json()["organization_id"] == ORG
        with db_session() as s:
            assert s.query(Schedule).filter(
                Schedule.id == r.json()["id"]).first().organization_id == ORG

    def test_appointment_model_is_honoured(self, client):
        r = _create(client, appointment_model="serial")
        assert r.status_code == 201, r.text
        assert r.json()["appointment_model"] == "serial"

    def test_receptionist_cannot_create_a_schedule(self, client):
        r = _create(client, user=RECP)
        assert r.status_code == 403

    def test_create_requires_authentication(self, client):
        r = client.post("/api/v1/schedules", json={
            "doctor_id": DOC, "organization_id": ORG, "branch_id": BR,
            "slot_templates": MORNING})
        assert r.status_code == 401


class TestScheduleSearch:
    def test_search_by_doctor(self, client):
        created = _create(client).json()["id"]
        r = client.get("/api/v1/schedules", params={"doctor_id": DOC},
                       headers=headers(ADMIN))
        assert r.status_code == 200
        assert created in [s["id"] for s in r.json()]

    def test_search_by_branch(self, client):
        _create(client)
        r = client.get("/api/v1/schedules", params={"branch_id": BR},
                       headers=headers(ADMIN))
        assert all(s["branch_id"] == BR for s in r.json())

    def test_search_is_scoped_to_the_callers_org(self, client):
        mine = _create(client).json()["id"]
        theirs = _create(client, user=OTHER_ADMIN, doctor_id=OTHER_DOC,
                         branch_id=OTHER_BR).json()["id"]
        my_list = client.get("/api/v1/schedules", headers=headers(ADMIN)).json()
        assert [s["id"] for s in my_list] == [mine]
        their_list = client.get("/api/v1/schedules",
                                headers=headers(OTHER_ADMIN)).json()
        assert [s["id"] for s in their_list] == [theirs]

    def test_doctor_role_may_read_but_not_write(self, client):
        created = _create(client).json()["id"]
        r = client.get("/api/v1/schedules", headers=headers(DOC_USER))
        assert r.status_code == 200
        assert created in [s["id"] for s in r.json()]
        assert _create(client, user=DOC_USER).status_code == 403


class TestScheduleReadUpdate:
    def test_get_schedule(self, client):
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}", headers=headers(ADMIN))
        assert r.status_code == 200
        assert r.json()["id"] == sid

    def test_get_missing_schedule_404(self, client):
        r = client.get("/api/v1/schedules/nonexistent", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_foreign_schedule_is_a_404(self, client):
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}", headers=headers(OTHER_ADMIN))
        assert r.status_code == 404

    def test_update_schedule(self, client):
        sid = _create(client).json()["id"]
        evening = [{"day_of_week": 1, "start_time": "17:00",
                    "end_time": "19:00", "slot_duration_minutes": 30,
                    "max_patients": 3}]
        r = client.patch(f"/api/v1/schedules/{sid}", headers=headers(ADMIN),
                         json={"slot_templates": evening,
                               "appointment_model": "hybrid",
                               "effective_to": "2026-12-31",
                               "status": "inactive"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["appointment_model"] == "hybrid"
        assert body["status"] == "inactive"
        assert body["effective_to"] == "2026-12-31"
        assert body["slot_templates"][0]["start_time"] == "17:00"
        with db_session() as s:
            row = s.query(Schedule).filter(Schedule.id == sid).first()
            assert row.appointment_model == "hybrid" and row.status == "inactive"

    def test_foreign_schedule_cannot_be_updated(self, client):
        sid = _create(client).json()["id"]
        r = client.patch(f"/api/v1/schedules/{sid}",
                         headers=headers(OTHER_ADMIN),
                         json={"appointment_model": "serial"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Schedule).filter(
                Schedule.id == sid).first().appointment_model == "time_slot"


def _book(client, start_time, booking_date="2026-04-15", status="BOOKED"):
    """Insert a real appointment row, the way the appointment service stores it."""
    with db_session() as s:
        s.add(Appointment(organization_id=ORG, branch_id=BR, patient_id=PAT,
                          doctor_id=DOC, appointment_date=date.fromisoformat(
                              booking_date), start_time=start_time,
                          status=status))
        s.commit()


class TestAvailableSlots:
    def test_slot_grid_is_derived_from_the_template(self, client):
        """09:00–10:00 with 15-minute slots is four slots, starting at 09:00."""
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}/available-slots",
                       params={"date_str": "2026-04-15"},
                       headers=headers(ADMIN))
        assert r.status_code == 200, r.text
        body = r.json()
        slots = body["slots"]
        assert len(slots) == 4
        assert [s["start_time"] for s in slots] == [
            "09:00", "09:15", "09:30", "09:45"]
        assert slots[0]["end_time"] == "09:15"
        assert body["appointment_model"] == "time_slot"
        assert body["date"] == "2026-04-15"
        # No reservation is configured on this organization, so all capacity
        # is bookable and nothing is held back for walk-ins.
        assert slots[0]["max_patients"] == 2
        assert slots[0]["reserved_walkin"] == 0
        assert slots[0]["available"] == 2
        assert slots[0]["available_unreserved"] == 2

    def test_booked_appointments_reduce_availability(self, client):
        sid = _create(client).json()["id"]
        _book(client, "09:00")
        slots = client.get(f"/api/v1/schedules/{sid}/available-slots",
                           params={"date_str": "2026-04-15"},
                           headers=headers(ADMIN)).json()["slots"]
        first = next(s for s in slots if s["start_time"] == "09:00")
        assert first["booked"] == 1
        assert first["available"] == 1
        second = next(s for s in slots if s["start_time"] == "09:15")
        assert second["booked"] == 0

    def test_cancelled_and_no_show_appointments_do_not_occupy_a_slot(self, client):
        sid = _create(client).json()["id"]
        _book(client, "09:00", status="CANCELLED")
        _book(client, "09:00", status="NO_SHOW")
        slots = client.get(f"/api/v1/schedules/{sid}/available-slots",
                           params={"date_str": "2026-04-15"},
                           headers=headers(ADMIN)).json()["slots"]
        first = next(s for s in slots if s["start_time"] == "09:00")
        assert first["booked"] == 0
        assert first["available"] == 2

    def test_bookings_for_another_date_are_not_counted(self, client):
        sid = _create(client).json()["id"]
        _book(client, "09:00", booking_date="2026-04-16")
        slots = client.get(f"/api/v1/schedules/{sid}/available-slots",
                           params={"date_str": "2026-04-15"},
                           headers=headers(ADMIN)).json()["slots"]
        assert slots[0]["booked"] == 0

    def test_invalid_date_is_422(self, client):
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}/available-slots",
                       params={"date_str": "15-04-2026"},
                       headers=headers(ADMIN))
        assert r.status_code == 422

    def test_unknown_schedule_is_404(self, client):
        r = client.get("/api/v1/schedules/bad-schedule/available-slots",
                       params={"date_str": "2026-01-01"},
                       headers=headers(ADMIN))
        assert r.status_code == 404

    def test_foreign_schedule_slots_are_a_404(self, client):
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}/available-slots",
                       params={"date_str": "2026-04-15"},
                       headers=headers(OTHER_ADMIN))
        assert r.status_code == 404

    def test_slots_require_authentication(self, client):
        sid = _create(client).json()["id"]
        r = client.get(f"/api/v1/schedules/{sid}/available-slots",
                       params={"date_str": "2026-04-15"})
        assert r.status_code == 401


class TestScheduleBranchAuthorization:
    """P0-6 and finding 8.2: branch scope on schedule creation and listing."""

    def test_p0_6_create_schedule_rejects_foreign_branch(self, client):
        # ADMIN is a branch_admin scoped to BR; creating a schedule at BR2
        # (same organisation, other branch) must be denied.
        ensure_branch("sch-br-2", ORG)
        r = client.post("/api/v1/schedules",
            headers=headers(ADMIN),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "sch-br-2",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        assert r.status_code == 404, r.text

    def test_p0_6_create_schedule_own_branch_succeeds(self, client):
        r = _create(client, user=ADMIN)
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == BR

    def test_p0_6_create_schedule_org_admin_org_wide(self, client):
        ensure_branch("sch-br-2", ORG)
        ensure_user("sch_org_adm", "org_admin", ORG, None)
        # org_admin retains organization-wide access across branches.
        r = client.post("/api/v1/schedules",
            headers=headers("sch_org_adm"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "sch-br-2",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        assert r.status_code == 201, r.text
        assert r.json()["branch_id"] == "sch-br-2"

    def test_p0_6_create_schedule_foreign_doctor_404(self, client):
        # The doctor must belong to the caller's organisation.
        r = client.post("/api/v1/schedules",
            headers=headers(ADMIN),
            json={"doctor_id": OTHER_DOC, "organization_id": ORG,
                  "branch_id": BR,
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        assert r.status_code == 404, r.text

    def test_8_2_list_schedules_rejects_foreign_branch(self, client):
        ensure_branch("sch-br-2", ORG)
        ensure_user("sch_org_adm2", "org_admin", ORG, None)
        client.post("/api/v1/schedules",
            headers=headers("sch_org_adm2"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "sch-br-2",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        # RECP scoped to BR must not list BR2 schedules.
        r = client.get("/api/v1/schedules",
            params={"branch_id": "sch-br-2"},
            headers=headers(RECP))
        assert r.status_code == 404, r.text

    def test_8_2_list_schedules_org_admin_org_wide(self, client):
        ensure_user("sch_org_adm3", "org_admin", ORG, None)
        r = client.get("/api/v1/schedules",
            params={"branch_id": BR},
            headers=headers("sch_org_adm3"))
        assert r.status_code == 200, r.text


class TestScheduleRBACR2:
    """RBAC-R2: complete schedule resource branch authorization."""

    def test_rbac_r2_list_without_branch_id_only_own_branch(self, client):
        ensure_branch("r2-br-2", ORG)
        ensure_user("r2_org_adm", "org_admin", ORG, None)
        client.post("/api/v1/schedules",
            headers=headers("r2_org_adm"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": BR,
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        client.post("/api/v1/schedules",
            headers=headers("r2_org_adm"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-2",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        r = client.get("/api/v1/schedules",
            headers=headers(RECP))
        assert r.status_code == 200, r.text
        body = r.json()
        assert all(s["branch_id"] == BR for s in body), body

    def test_rbac_r2_list_foreign_branch_via_param(self, client):
        ensure_branch("r2-br-2", ORG)
        ensure_user("r2_org_adm2", "org_admin", ORG, None)
        client.post("/api/v1/schedules",
            headers=headers("r2_org_adm2"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-2",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        r = client.get("/api/v1/schedules",
            params={"branch_id": "r2-br-2"},
            headers=headers(RECP))
        assert r.status_code == 404, r.text

    def test_rbac_r2_org_admin_lists_own_org_all_branches(self, client):
        ensure_branch("r2-br-3", ORG)
        ensure_user("r2_org_adm3", "org_admin", ORG, None)
        client.post("/api/v1/schedules",
            headers=headers("r2_org_adm3"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-3",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        r = client.get("/api/v1/schedules",
            params={"branch_id": "r2-br-3"},
            headers=headers("r2_org_adm3"))
        assert r.status_code == 200, r.text

    def test_rbac_r2_cannot_retrieve_foreign_branch_schedule(self, client):
        ensure_branch("r2-br-4", ORG)
        ensure_user("r2_org_adm4", "org_admin", ORG, None)
        r = client.post("/api/v1/schedules",
            headers=headers("r2_org_adm4"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-4",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        sid = r.json()["id"]
        r2 = client.get(f"/api/v1/schedules/{sid}",
            headers=headers(RECP))
        assert r2.status_code == 404, r2.text

    def test_rbac_r2_cannot_update_foreign_branch_schedule(self, client):
        ensure_branch("r2-br-5", ORG)
        ensure_user("r2_org_adm5", "org_admin", ORG, None)
        r = client.post("/api/v1/schedules",
            headers=headers("r2_org_adm5"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-5",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        sid = r.json()["id"]
        with db_session() as s:
            orig = s.query(Schedule).filter(Schedule.id == sid).one()
            orig_templates = list(orig.slot_templates)
        r2 = client.patch(f"/api/v1/schedules/{sid}",
            headers=headers(ADMIN),
            json={"slot_templates": MORNING})
        assert r2.status_code == 404, r2.text
        with db_session() as s:
            row = s.query(Schedule).filter(Schedule.id == sid).one()
            assert list(row.slot_templates) == orig_templates

    def test_rbac_r2_cannot_retrieve_foreign_branch_slots(self, client):
        ensure_branch("r2-br-6", ORG)
        ensure_user("r2_org_adm6", "org_admin", ORG, None)
        r = client.post("/api/v1/schedules",
            headers=headers("r2_org_adm6"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-6",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        sid = r.json()["id"]
        r2 = client.get(f"/api/v1/schedules/{sid}/available-slots",
            params={"date_str": "2026-04-15"},
            headers=headers(RECP))
        assert r2.status_code == 404, r2.text

    def test_rbac_r2_org_admin_org_wide_slots(self, client):
        ensure_branch("r2-br-7", ORG)
        ensure_user("r2_org_adm7", "org_admin", ORG, None)
        r = client.post("/api/v1/schedules",
            headers=headers("r2_org_adm7"),
            json={"doctor_id": DOC, "organization_id": ORG,
                  "branch_id": "r2-br-7",
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        sid = r.json()["id"]
        r2 = client.get(f"/api/v1/schedules/{sid}/available-slots",
            params={"date_str": "2026-04-15"},
            headers=headers("r2_org_adm7"))
        assert r2.status_code == 200, r2.text

    def test_rbac_r2_cross_tenant_schedule_non_disclosing(self, client):
        ensure_user("r2_other_admin", "branch_admin", OTHER_ORG, OTHER_BR)
        r = client.post("/api/v1/schedules",
            headers=headers("r2_other_admin"),
            json={"doctor_id": OTHER_DOC, "organization_id": OTHER_ORG,
                  "branch_id": OTHER_BR,
                  "effective_from": "2026-01-01",
                  "slot_templates": MORNING})
        sid = r.json()["id"]
        r2 = client.get(f"/api/v1/schedules/{sid}",
            headers=headers(RECP))
        assert r2.status_code == 404, r2.text
