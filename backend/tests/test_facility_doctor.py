"""Facility hierarchy, doctor profile and conflict-safe sessions.

AMSDP-FACILITY-DOCTOR-01 adds four things the rest of the suite did not
exercise, so this module is their test of record:

* **Facility hierarchy** — floors, departments and rooms per branch, retired
  (never deleted) with code uniqueness scoped to the branch.
* **Doctor profile** — canonical BD mobile numbers, structured specialities,
  multi-branch chamber assignments with exactly one primary, BMDC registration
  and its verification axis, and the inline photograph.
* **Schedule sessions** — the weekday/window/chamber rows a booking resolves
  against, with conflict guards on both the doctor and the room.
* **Appointment location snapshot** — the chamber copied onto the appointment
  at booking time, which must survive later facility reorganisation.

Conventions follow ``tests/test_e2e.py``: the real FastAPI apps are imported
through :func:`amsdp_test_support.load_app`, every request carries a signed JWT
minted from a real ``staff_users`` row, and every row is written to PostgreSQL.
Reference rows (organizations, branches, doctors, users) are never deleted —
the append-only audit trail points at them — so doctors are created with a
fresh mobile number on every run instead of a fixed fixture id.
"""

import base64
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (ensure_branch, ensure_org, ensure_patient,
                                ensure_user, headers, load_app, purge_org, uniq)

ORG = "facility-doctor-org"
BR = "facility-doctor-br"
BR2 = "facility-doctor-br2"
OTHER_ORG = "facility-doctor-other-org"
OTHER_BR = "facility-doctor-other-br"

#: Organization administrator: manages the org-wide catalogue (specialities,
#: registration policy) and any branch inside the organization.
OWNER = "facility_doctor_owner"
#: Branch administrator of BR — may manage facilities at BR only.
BR_ADMIN = "facility_doctor_branch"
#: Branch administrator of BR2 — must see BR as a non-disclosing 404.
BR2_ADMIN = "facility_doctor_branch2"
#: Receptionist at BR: read-only facility access, may book appointments.
DESK = "facility_doctor_desk"
#: Organization administrator of another tenant.
FOREIGN = "facility_doctor_foreign"

#: A fixed future date: the weekday is derived, never assumed.
BOOKING_DATE = "2026-04-15"
WEEKDAY = datetime.strptime(BOOKING_DATE, "%Y-%m-%d").weekday()

#: Smallest possible PNG, so the photo endpoint is exercised on real bytes.
PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

PATIENT = "facility-doctor-patient"


@pytest.fixture(scope="module", autouse=True)
def _world():
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_patient(PATIENT, ORG, name="Facility Test Patient",
                   mobile="01700000200")
    ensure_user(OWNER, "org_admin", ORG, None)
    ensure_user(BR_ADMIN, "branch_admin", ORG, BR)
    ensure_user(BR2_ADMIN, "branch_admin", ORG, BR2)
    ensure_user(DESK, "receptionist", ORG, BR)
    ensure_user(FOREIGN, "org_admin", OTHER_ORG, OTHER_BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


@pytest.fixture(scope="module")
def svc():
    """One client per service, each with its own imported app."""
    clients = {name: TestClient(load_app(name))
               for name in ("organization", "doctor", "scheduling",
                            "appointment")}

    class Services:
        organization = clients["organization"]
        doctor = clients["doctor"]
        scheduling = clients["scheduling"]
        appointment = clients["appointment"]

    return Services


# ---------------------------------------------------------------------------
# Small builders — every one asserts its own status code, so a failure names
# the request that broke instead of surfacing later as a confusing 404.
# ---------------------------------------------------------------------------

def _mobile() -> str:
    """A fresh ``01[3-9]XXXXXXXX`` number (doctors outlive ``purge_org``)."""
    operator = "3456789"[uuid.uuid4().int % 7]
    return "01" + operator + f"{uuid.uuid4().int % 10 ** 8:08d}"


def base64_of(raw: bytes) -> str:
    """The inline base64 form the photo endpoint expects (no data URL)."""
    return base64.b64encode(raw).decode("ascii")


def _create_doctor(svc, *, branches=(BR,), name=None, mobile=None,
                   registration_number=None, specialty_ids=None):
    payload = {
        "name": name or f"Dr. Facility {uniq('doc')}",
        "mobile": mobile or _mobile(),
        "branch_ids": list(branches),
    }
    if registration_number is not None:
        payload["registration_number"] = registration_number
    if specialty_ids:
        payload["specialty_ids"] = list(specialty_ids)
    r = svc.doctor.post("/api/v1/doctors", headers=headers(OWNER), json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _create_floor(svc, *, branch_id=BR, code=None, name=None):
    r = svc.organization.post(
        f"/api/v1/branches/{branch_id}/floors", headers=headers(OWNER),
        json={"name": name or f"Floor {uniq('flr')}", "code": code})
    assert r.status_code == 201, r.text
    return r.json()


def _create_department(svc, *, branch_id=BR, code=None, name=None):
    r = svc.organization.post(
        f"/api/v1/branches/{branch_id}/departments", headers=headers(OWNER),
        json={"name": name or f"Department {uniq('dept')}", "code": code})
    assert r.status_code == 201, r.text
    return r.json()


def _create_room(svc, *, branch_id=BR, floor_id=None, department_id=None,
                 code=None, name=None, room_type="consultation"):
    r = svc.organization.post(
        f"/api/v1/branches/{branch_id}/rooms", headers=headers(OWNER),
        json={"name": name or f"Room {uniq('room')}", "code": code,
              "floor_id": floor_id, "department_id": department_id,
              "room_type": room_type})
    assert r.status_code == 201, r.text
    return r.json()


def _create_schedule(svc, doctor_id, branch_id=BR):
    r = svc.scheduling.post("/api/v1/schedules", headers=headers(OWNER), json={
        "doctor_id": doctor_id, "organization_id": ORG,
        "branch_id": branch_id})
    assert r.status_code == 201, r.text
    return r.json()


def _create_session(svc, schedule_id, *, day=WEEKDAY, start="09:00",
                    end="12:00", room_id=None, floor_id=None,
                    department_id=None, max_patients=1):
    body = {"day_of_week": day, "start_time": start, "end_time": end,
            "max_patients": max_patients}
    if room_id:
        body["room_id"] = room_id
    if floor_id:
        body["floor_id"] = floor_id
    if department_id:
        body["department_id"] = department_id
    return svc.scheduling.post(
        f"/api/v1/schedules/{schedule_id}/sessions", headers=headers(OWNER),
        json=body)


def _chamber(svc, *, branch_id=BR):
    """A floor + department + room triplet at one branch."""
    floor = _create_floor(svc, branch_id=branch_id)
    department = _create_department(svc, branch_id=branch_id)
    room = _create_room(svc, branch_id=branch_id, floor_id=floor["id"],
                        department_id=department["id"])
    return floor, department, room


# ---------------------------------------------------------------------------
# Facility hierarchy
# ---------------------------------------------------------------------------

class TestFacilityHierarchy:
    def test_tree_returns_floor_department_room(self, svc):
        floor, department, room = _chamber(svc)
        tree = svc.organization.get(
            f"/api/v1/branches/{BR}/facility", headers=headers(OWNER))
        assert tree.status_code == 200, tree.text
        body = tree.json()
        assert body["branch"]["id"] == BR
        assert floor["id"] in [f["id"] for f in body["floors"]]
        assert department["id"] in [d["id"] for d in body["departments"]]
        stored = [r for r in body["rooms"] if r["id"] == room["id"]]
        assert stored and stored[0]["floor_name"] == floor["name"]
        assert stored[0]["department_name"] == department["name"]

    def test_code_is_uppercased_and_unique_per_branch(self, svc):
        code = uniq("wrd")
        first = _create_floor(svc, code=code, name=f"Ward {code}")
        assert first["code"] == code.upper()

        duplicate = svc.organization.post(
            f"/api/v1/branches/{BR}/floors", headers=headers(OWNER),
            json={"name": f"Ward dup {code}", "code": first["code"]})
        assert duplicate.status_code == 409, duplicate.text

        # The same code is available at a different branch: uniqueness is
        # per branch, not per organization.
        elsewhere = svc.organization.post(
            f"/api/v1/branches/{BR2}/floors", headers=headers(OWNER),
            json={"name": f"Ward twin {code}", "code": first["code"]})
        assert elsewhere.status_code == 201, elsewhere.text

    def test_code_is_derived_from_the_name(self, svc):
        name = f"Ground Floor {uniq('gnd')}"
        created = svc.organization.post(
            f"/api/v1/branches/{BR}/floors", headers=headers(OWNER),
            json={"name": name})
        assert created.status_code == 201, created.text
        assert created.json()["code"] == name.upper().replace(" ", "-")

    def test_floor_retirement_is_blocked_by_an_active_room(self, svc):
        floor, department, room = _chamber(svc)
        blocked = svc.organization.delete(
            f"/api/v1/floors/{floor['id']}", headers=headers(OWNER))
        assert blocked.status_code == 409, blocked.text

        assert svc.organization.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=headers(OWNER)).status_code == 200
        retired = svc.organization.delete(
            f"/api/v1/floors/{floor['id']}", headers=headers(OWNER))
        assert retired.status_code == 200, retired.text
        assert retired.json()["status"] == "inactive"

        # Retired, not deleted: the row still exists for the audit trail.
        tree = svc.organization.get(
            f"/api/v1/branches/{BR}/facility?include_inactive=true",
            headers=headers(OWNER)).json()
        assert floor["id"] in [f["id"] for f in tree["floors"]]
        active_only = svc.organization.get(
            f"/api/v1/branches/{BR}/facility", headers=headers(OWNER)).json()
        assert floor["id"] not in [f["id"] for f in active_only["floors"]]

    def test_department_retirement_is_blocked_by_an_active_room(self, svc):
        floor, department, room = _chamber(svc)
        blocked = svc.organization.delete(
            f"/api/v1/departments/{department['id']}", headers=headers(OWNER))
        assert blocked.status_code == 409, blocked.text
        svc.organization.delete(f"/api/v1/rooms/{room['id']}",
                                headers=headers(OWNER))
        assert svc.organization.delete(
            f"/api/v1/departments/{department['id']}",
            headers=headers(OWNER)).status_code == 200

    def test_room_cannot_borrow_another_branchs_floor(self, svc):
        other_floor = _create_floor(svc, branch_id=BR2)
        crossed = svc.organization.post(
            f"/api/v1/branches/{BR}/rooms", headers=headers(OWNER),
            json={"name": f"Crossed {uniq('room')}",
                  "floor_id": other_floor["id"]})
        assert crossed.status_code == 422, crossed.text

    def test_receptionist_reads_but_cannot_manage(self, svc):
        readable = svc.organization.get(
            f"/api/v1/branches/{BR}/facility", headers=headers(DESK))
        assert readable.status_code == 200, readable.text
        denied = svc.organization.post(
            f"/api/v1/branches/{BR}/floors", headers=headers(DESK),
            json={"name": f"Desk floor {uniq('flr')}"})
        assert denied.status_code == 403, denied.text

    def test_other_branch_administrator_gets_a_non_disclosing_404(self, svc):
        hidden = svc.organization.get(
            f"/api/v1/branches/{BR}/facility", headers=headers(BR2_ADMIN))
        assert hidden.status_code == 404, hidden.text
        assert "facility-doctor-br" not in hidden.text

    def test_other_tenant_gets_a_non_disclosing_404(self, svc):
        hidden = svc.organization.get(
            f"/api/v1/branches/{BR}/facility", headers=headers(FOREIGN))
        assert hidden.status_code == 404, hidden.text


# ---------------------------------------------------------------------------
# Organization speciality catalogue
# ---------------------------------------------------------------------------

class TestSpecialities:
    def _create(self, svc, *, code=None, name_en=None):
        body = {"name_en": name_en or f"Speciality {uniq('spc')}",
                "name_bn": "কার্ডিওলজি" if name_en is None else ""}
        if code:
            body["code"] = code
        r = svc.organization.post(
            f"/api/v1/orgs/{ORG}/specialties", headers=headers(OWNER), json=body)
        assert r.status_code == 201, r.text
        return r.json()

    def test_catalogue_is_org_scoped_and_code_is_unique(self, svc):
        code = uniq("spc")
        created = self._create(svc, code=code)
        assert created["code"] == code.upper()
        assert created["name_bn"] == "কার্ডিওলজি"

        clash = svc.organization.post(
            f"/api/v1/orgs/{ORG}/specialties", headers=headers(OWNER),
            json={"name_en": f"Clash {code}", "code": created["code"]})
        assert clash.status_code == 409, clash.text

        listed = svc.organization.get(
            f"/api/v1/orgs/{ORG}/specialties", headers=headers(OWNER))
        assert listed.status_code == 200, listed.text
        assert created["id"] in [s["id"] for s in listed.json()]

    def test_retired_speciality_leaves_the_active_catalogue(self, svc):
        created = self._create(svc)
        retired = svc.organization.delete(
            f"/api/v1/specialties/{created['id']}", headers=headers(OWNER))
        assert retired.status_code == 200, retired.text
        active = svc.organization.get(
            f"/api/v1/orgs/{ORG}/specialties", headers=headers(OWNER)).json()
        assert created["id"] not in [s["id"] for s in active]
        everything = svc.organization.get(
            f"/api/v1/orgs/{ORG}/specialties?include_inactive=true",
            headers=headers(OWNER)).json()
        assert created["id"] in [s["id"] for s in everything]

    def test_specialities_mirror_into_the_doctor_text_field(self, svc):
        first = self._create(svc, name_en=f"Cardiology {uniq('c')}")
        second = self._create(svc, name_en=f"Medicine {uniq('m')}")
        doctor = _create_doctor(svc, specialty_ids=[first["id"], second["id"]])
        assert sorted(doctor["specialty_ids"]) == sorted(
            [first["id"], second["id"]])
        assert first["name_en"] in doctor["speciality"]
        assert second["name_en"] in doctor["speciality"]

        replaced = svc.doctor.put(
            f"/api/v1/doctors/{doctor['id']}/specialties",
            headers=headers(OWNER), json={"specialty_ids": [second["id"]]})
        assert replaced.status_code == 200, replaced.text
        assert [s["id"] for s in replaced.json()["items"]] == [second["id"]]
        after = svc.doctor.get(
            f"/api/v1/doctors/{doctor['id']}", headers=headers(OWNER)).json()
        assert after["specialty_ids"] == [second["id"]]
        assert after["speciality"] == second["name_en"]

    def test_speciality_from_another_tenant_is_refused(self, svc):
        foreign = svc.organization.post(
            f"/api/v1/orgs/{OTHER_ORG}/specialties",
            headers=headers(FOREIGN),
            json={"name_en": f"Foreign {uniq('f')}"})
        assert foreign.status_code == 201, foreign.text
        doctor = _create_doctor(svc)
        crossed = svc.doctor.put(
            f"/api/v1/doctors/{doctor['id']}/specialties",
            headers=headers(OWNER),
            json={"specialty_ids": [foreign.json()["id"]]})
        assert crossed.status_code == 422, crossed.text



# ---------------------------------------------------------------------------
# Doctor record: canonical mobile, photograph, branches, BMDC
# ---------------------------------------------------------------------------

class TestDoctorProfile:
    def test_mobile_is_stored_in_canonical_form(self, svc):
        national = _mobile()
        spaced = f"{national[:3]} {national[3:7]} {national[7:]}"
        doctor = _create_doctor(svc, mobile=spaced)
        assert doctor["mobile"] == national

        # The international form of the same number is the same person.
        international = "+88" + national
        clash = svc.doctor.post("/api/v1/doctors", headers=headers(OWNER),
                                json={"name": f"Dr. Intl {uniq('doc')}",
                                      "mobile": international})
        assert clash.status_code == 409, clash.text

    def test_unparseable_mobile_is_refused(self, svc):
        for bad in ("0123456789", "0171111", "not-a-number", ""):
            refused = svc.doctor.post(
                "/api/v1/doctors", headers=headers(OWNER),
                json={"name": f"Dr. Bad {uniq('doc')}", "mobile": bad})
            assert refused.status_code == 422, (bad, refused.text)

    def test_duplicate_mobile_is_per_organization(self, svc):
        national = _mobile()
        _create_doctor(svc, mobile=national)
        duplicate = svc.doctor.post(
            "/api/v1/doctors", headers=headers(OWNER),
            json={"name": f"Dr. Dup {uniq('doc')}", "mobile": national})
        assert duplicate.status_code == 409, duplicate.text

        # Another tenant may register the same person under the same number:
        # doctor records are facility-local (BR §9).
        allowed = svc.doctor.post(
            "/api/v1/doctors", headers=headers(FOREIGN),
            json={"name": f"Dr. Elsewhere {uniq('doc')}", "mobile": national})
        assert allowed.status_code == 201, allowed.text

    def test_photo_lifecycle(self, svc):
        doctor = _create_doctor(svc)
        assert doctor["has_photo"] is False

        uploaded = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(OWNER),
            json={"photo_base64": f"data:image/png;base64,{PNG_BASE64}",
                  "mime_type": "image/png"})
        assert uploaded.status_code == 200, uploaded.text
        assert uploaded.json()["has_photo"] is True

        served = svc.doctor.get(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(DESK))
        assert served.status_code == 200, served.text
        assert served.json()["photo_base64"] == PNG_BASE64
        assert served.json()["mime_type"] == "image/png"

        # The list must not inline the image, only the flag.
        listed = svc.doctor.get(
            f"/api/v1/doctors?q={doctor['mobile']}",
            headers=headers(OWNER)).json()
        row = [d for d in listed["items"] if d["id"] == doctor["id"]][0]
        assert row["has_photo"] is True
        assert "photo_base64" not in row

        deleted = svc.doctor.delete(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(OWNER))
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["has_photo"] is False
        assert svc.doctor.get(
            f"/api/v1/doctors/{doctor['id']}/photo",
            headers=headers(OWNER)).status_code == 404

    def test_photo_content_is_checked_not_just_the_label(self, svc):
        doctor = _create_doctor(svc)
        # A PDF renamed to .png is refused on its leading bytes.
        payload = base64_of(b"%PDF-1.7 not an image")
        mismatch = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(OWNER),
            json={"photo_base64": payload, "mime_type": "image/png"})
        assert mismatch.status_code == 422, mismatch.text

        unsupported = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(OWNER),
            json={"photo_base64": PNG_BASE64, "mime_type": "image/svg+xml"})
        assert unsupported.status_code == 422, unsupported.text

        too_big = base64_of(b"\x89PNG\r\n\x1a\n" + b"\x00" * (301 * 1024))
        oversized = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(OWNER),
            json={"photo_base64": too_big, "mime_type": "image/png"})
        assert oversized.status_code == 413, oversized.text


    def test_branch_assignments_keep_exactly_one_primary(self, svc):
        doctor = _create_doctor(svc, branches=(BR, BR2))
        primary = svc.doctor.patch(
            f"/api/v1/doctors/{doctor['id']}", headers=headers(OWNER),
            json={"primary_branch_id": BR2})
        assert primary.status_code == 200, primary.text
        assert primary.json()["primary_branch_id"] == BR2

        br_assignment = [a for a in primary.json()["branches"]
                         if a["branch_id"] == BR][0]
        promoted = svc.doctor.patch(
            f"/api/v1/doctors/{doctor['id']}/branches/{br_assignment['id']}",
            headers=headers(OWNER), json={"is_primary": True})
        assert promoted.status_code == 200, promoted.text
        after = svc.doctor.get(
            f"/api/v1/doctors/{doctor['id']}", headers=headers(OWNER)).json()
        assert after["primary_branch_id"] == BR
        assert [a["branch_id"] for a in after["branches"]
                if a["is_primary"]] == [BR]

    def test_retired_assignment_is_reactivated_not_duplicated(self, svc):
        doctor = _create_doctor(svc, branches=(BR, BR2))
        br2 = [a for a in doctor["branches"] if a["branch_id"] == BR2][0]
        retired = svc.doctor.delete(
            f"/api/v1/doctors/{doctor['id']}/branches/{br2['id']}",
            headers=headers(OWNER))
        assert retired.status_code == 200, retired.text
        assert retired.json()["status"] == "inactive"

        # The row survives, so the chamber it carried is not lost: re-adding
        # the branch flips the same row back to active.
        readded = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/branches", headers=headers(OWNER),
            json={"branch_id": BR2})
        assert readded.status_code == 201, readded.text
        assert readded.json()["id"] == br2["id"]
        assert readded.json()["status"] == "active"

        again = svc.doctor.get(
            f"/api/v1/doctors/{doctor['id']}/branches",
            headers=headers(OWNER)).json()
        assert [a["id"] for a in again["items"]].count(br2["id"]) == 1

    def test_assignment_rejects_a_chamber_from_another_branch(self, svc):
        doctor = _create_doctor(svc)
        foreign_room = _create_room(svc, branch_id=BR2)
        crossed = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/branches", headers=headers(OWNER),
            json={"branch_id": BR, "room_id": foreign_room["id"]})
        assert crossed.status_code == 422, crossed.text


    def test_bmdc_verification_transitions(self, svc):
        doctor = _create_doctor(svc, registration_number=f"BMDC-{uniq('reg')}")
        url = f"/api/v1/doctors/{doctor['id']}/verification"

        pending = svc.doctor.post(url, headers=headers(OWNER),
                                  json={"status": "pending_verification"})
        assert pending.status_code == 200, pending.text
        assert pending.json()["bmdc_verification_status"] == (
            "pending_verification")
        assert pending.json()["bmdc_verified_at"] == ""

        verified = svc.doctor.post(url, headers=headers(OWNER),
                                   json={"status": "verified", "note": "checked"})
        assert verified.status_code == 200, verified.text
        assert verified.json()["bmdc_verification_status"] == "verified"
        assert verified.json()["bmdc_verified_at"]

        # A verification is not silently revocable back to unverified.
        reset = svc.doctor.post(url, headers=headers(OWNER),
                                json={"status": "unverified"})
        assert reset.status_code == 422, reset.text

        rejected = svc.doctor.post(url, headers=headers(OWNER),
                                   json={"status": "rejected",
                                         "note": "number withdrawn"})
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["bmdc_verification_status"] == "rejected"
        assert rejected.json()["bmdc_verified_at"] == ""

        # A rejected registration cannot then be activated.
        svc.doctor.patch(f"/api/v1/doctors/{doctor['id']}",
                         headers=headers(OWNER), json={"status": "inactive"})
        blocked = svc.doctor.patch(
            f"/api/v1/doctors/{doctor['id']}", headers=headers(OWNER),
            json={"status": "active"})
        assert blocked.status_code == 422, blocked.text

    def test_verification_requires_a_registration_number(self, svc):
        doctor = _create_doctor(svc)
        refused = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/verification",
            headers=headers(OWNER), json={"status": "pending_verification"})
        assert refused.status_code == 422, refused.text

    def test_registration_policy_blocks_future_activations_only(self, svc):
        policy = f"/api/v1/orgs/{ORG}/registration-policy"
        try:
            set_required = svc.doctor.patch(
                policy, headers=headers(OWNER), json={"bmdc_required": True})
            assert set_required.status_code == 200, set_required.text

            without_number = svc.doctor.post(
                "/api/v1/doctors", headers=headers(OWNER),
                json={"name": f"Dr. NoBmdc {uniq('doc')}",
                      "mobile": _mobile()})
            assert without_number.status_code == 422, without_number.text

            with_number = _create_doctor(
                svc, registration_number=f"BMDC-{uniq('reg')}")
            assert with_number["status"] == "active"

            # Verification, when demanded, is a separate switch.
            svc.doctor.patch(policy, headers=headers(OWNER),
                             json={"bmdc_verification_required": True})
            unverified = svc.doctor.post(
                "/api/v1/doctors", headers=headers(OWNER),
                json={"name": f"Dr. Unverified {uniq('doc')}",
                      "mobile": _mobile(),
                      "registration_number": f"BMDC-{uniq('reg')}"})
            assert unverified.status_code == 422, unverified.text

            # Tightening the policy does not deactivate the existing doctor.
            still_active = svc.doctor.get(
                f"/api/v1/doctors/{with_number['id']}",
                headers=headers(OWNER)).json()
            assert still_active["status"] == "active"
        finally:
            svc.doctor.patch(policy, headers=headers(OWNER),
                             json={"bmdc_required": False,
                                   "bmdc_verification_required": False})

    def test_receptionist_cannot_manage_doctor_records(self, svc):
        doctor = _create_doctor(svc)
        created = svc.doctor.post(
            "/api/v1/doctors", headers=headers(DESK),
            json={"name": f"Dr. Desk {uniq('doc')}", "mobile": _mobile()})
        assert created.status_code == 403, created.text
        photo = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/photo", headers=headers(DESK),
            json={"photo_base64": PNG_BASE64, "mime_type": "image/png"})
        assert photo.status_code == 403, photo.text
        assignment = svc.doctor.post(
            f"/api/v1/doctors/{doctor['id']}/branches", headers=headers(DESK),
            json={"branch_id": BR2})
        assert assignment.status_code == 403, assignment.text

    def test_another_tenants_doctor_is_a_404(self, svc):
        foreign = svc.doctor.post(
            "/api/v1/doctors", headers=headers(FOREIGN),
            json={"name": f"Dr. Foreign {uniq('doc')}", "mobile": _mobile()})
        assert foreign.status_code == 201, foreign.text
        hidden = svc.doctor.get(f"/api/v1/doctors/{foreign.json()['id']}",
                                headers=headers(OWNER))
        assert hidden.status_code == 404, hidden.text
        assert "Foreign" not in hidden.text



# ---------------------------------------------------------------------------
# Schedule sessions: the weekday/window/chamber a booking resolves against
# ---------------------------------------------------------------------------

class TestScheduleSessions:
    def test_session_carries_its_chamber_and_projects_into_the_schedule(
            self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)

        created = _create_session(svc, schedule["id"], room_id=room["id"],
                                  start="09:00", end="12:00")
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["doctor_id"] == doctor["id"]
        assert body["branch_id"] == BR
        assert body["day_of_week"] == WEEKDAY
        assert body["room_id"] == room["id"]
        assert body["room_name"] == room["name"]
        assert body["floor_name"] == floor["name"]
        assert body["department_name"] == department["name"]
        assert body["slot_duration_minutes"] == 15
        assert body["status"] == "active"

        # ``schedule.slot_templates`` is a projection of the sessions, so the
        # existing calendar and available-slots endpoints keep working.
        projected = svc.scheduling.get(
            f"/api/v1/schedules/{schedule['id']}",
            headers=headers(OWNER)).json()
        templates = projected["slot_templates"]
        assert [t["session_id"] for t in templates] == [body["id"]]
        assert templates[0]["room_id"] == room["id"]

        slots = svc.scheduling.get(
            f"/api/v1/schedules/{schedule['id']}/available-slots",
            params={"date_str": BOOKING_DATE}, headers=headers(OWNER))
        assert slots.status_code == 200, slots.text
        # 09:00-12:00 in 15-minute slots.
        assert len(slots.json()["slots"]) == 12

    def test_doctor_double_booking_is_refused(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)
        assert _create_session(svc, schedule["id"], room_id=room["id"],
                               start="09:00", end="12:00").status_code == 201

        overlapping = _create_session(svc, schedule["id"], room_id=room["id"],
                                      start="11:00", end="13:00")
        assert overlapping.status_code == 409, overlapping.text
        assert "already holds" in overlapping.text

        same_start = _create_session(svc, schedule["id"], room_id=room["id"],
                                     start="09:00", end="10:00")
        assert same_start.status_code == 409, same_start.text

        # Touching windows are not an overlap; a second weekday is fine.
        assert _create_session(svc, schedule["id"], room_id=room["id"],
                               start="12:00", end="13:00").status_code == 201
        assert _create_session(svc, schedule["id"], room_id=room["id"],
                               day=(WEEKDAY + 1) % 7, start="09:00",
                               end="12:00").status_code == 201

    def test_a_chamber_cannot_hold_two_doctors(self, svc):
        first = _create_doctor(svc)
        second = _create_doctor(svc)
        floor, department, room = _chamber(svc)
        first_schedule = _create_schedule(svc, first["id"])
        second_schedule = _create_schedule(svc, second["id"])
        assert _create_session(svc, first_schedule["id"], room_id=room["id"],
                               start="09:00", end="12:00").status_code == 201

        clash = _create_session(svc, second_schedule["id"],
                                room_id=room["id"], start="10:00", end="11:00")
        assert clash.status_code == 409, clash.text
        assert "chamber" in clash.text

        other_room = _create_room(svc, floor_id=floor["id"],
                                  department_id=department["id"])
        assert _create_session(svc, second_schedule["id"],
                               room_id=other_room["id"], start="10:00",
                               end="11:00").status_code == 201


    def test_session_requires_an_active_branch_assignment(self, svc):
        unassigned = _create_doctor(svc, branches=())
        schedule = _create_schedule(svc, unassigned["id"])
        refused = _create_session(svc, schedule["id"])
        assert refused.status_code == 422, refused.text
        assert "not assigned" in refused.text

        elsewhere = _create_doctor(svc, branches=(BR2,))
        other_schedule = _create_schedule(svc, elsewhere["id"])
        refused = _create_session(svc, other_schedule["id"])
        assert refused.status_code == 422, refused.text

    def test_retired_chamber_releases_only_with_its_sessions(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)
        session = _create_session(svc, schedule["id"], room_id=room["id"])
        assert session.status_code == 201, session.text

        blocked = svc.organization.delete(
            f"/api/v1/rooms/{room['id']}", headers=headers(OWNER))
        assert blocked.status_code == 409, blocked.text
        assert "session" in blocked.text.lower()

        retired = svc.scheduling.delete(
            f"/api/v1/sessions/{session.json()['id']}", headers=headers(OWNER))
        assert retired.status_code == 200, retired.text
        assert retired.json()["status"] == "inactive"

        assert svc.organization.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=headers(OWNER)).status_code == 200

        # A retired chamber can no longer be booked into a session.
        refused = _create_session(svc, schedule["id"], room_id=room["id"],
                                  start="14:00", end="15:00")
        assert refused.status_code == 422, refused.text
        assert "retired" in refused.text

    def test_session_window_and_day_are_validated(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        backwards = _create_session(svc, schedule["id"], start="12:00",
                                    end="12:00")
        assert backwards.status_code == 422, backwards.text
        bad_day = _create_session(svc, schedule["id"], day=7)
        assert bad_day.status_code == 422, bad_day.text
        bad_time = _create_session(svc, schedule["id"], start="9am")
        assert bad_time.status_code == 422, bad_time.text

    def test_cross_tenant_schedule_is_a_404(self, svc):
        foreign_doctor = svc.doctor.post(
            "/api/v1/doctors", headers=headers(FOREIGN),
            json={"name": f"Dr. ForeignSched {uniq('doc')}",
                  "mobile": _mobile(), "branch_ids": [OTHER_BR]})
        assert foreign_doctor.status_code == 201, foreign_doctor.text
        foreign_schedule = svc.scheduling.post(
            "/api/v1/schedules", headers=headers(FOREIGN),
            json={"doctor_id": foreign_doctor.json()["id"],
                  "organization_id": OTHER_ORG, "branch_id": OTHER_BR})
        assert foreign_schedule.status_code == 201, foreign_schedule.text

        hidden = svc.scheduling.get(
            f"/api/v1/schedules/{foreign_schedule.json()['id']}/sessions",
            headers=headers(OWNER))
        assert hidden.status_code == 404, hidden.text

    def test_receptionist_reads_sessions_but_cannot_manage_them(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        session = _create_session(svc, schedule["id"])
        assert session.status_code == 201, session.text

        readable = svc.scheduling.get(
            f"/api/v1/branches/{BR}/sessions", headers=headers(DESK))
        assert readable.status_code == 200, readable.text

        desk = svc.scheduling.post(
            f"/api/v1/schedules/{schedule['id']}/sessions",
            headers=headers(DESK),
            json={"day_of_week": WEEKDAY, "start_time": "17:00",
                  "end_time": "18:00"})
        assert desk.status_code == 403, desk.text
        assert svc.scheduling.delete(
            f"/api/v1/sessions/{session.json()['id']}",
            headers=headers(DESK)).status_code == 403



# ---------------------------------------------------------------------------
# Appointment location snapshot — the chamber is copied, never re-derived
# ---------------------------------------------------------------------------

def _book(svc, *, doctor_id, start="09:30", date=BOOKING_DATE, who=DESK,
          patient_id=PATIENT):
    return svc.appointment.post(
        "/api/v1/appointments", headers=headers(who),
        json={"patient_id": patient_id, "doctor_id": doctor_id,
              "appointment_date": date, "start_time": start,
              "booking_source": "reception"})


class TestAppointmentLocation:
    def test_booking_snapshots_the_resolved_chamber(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)
        session = _create_session(svc, schedule["id"], room_id=room["id"],
                                  start="09:00", end="12:00")
        assert session.status_code == 201, session.text

        booked = _book(svc, doctor_id=doctor["id"], start="09:30")
        assert booked.status_code == 201, booked.text
        appt = booked.json()
        assert appt["session_id"] == session.json()["id"]
        assert appt["room_id"] == room["id"]
        assert appt["room_name"] == room["name"]
        assert appt["floor_name"] == floor["name"]
        assert appt["department_name"] == department["name"]
        assert appt["location_label"] == (
            f"{floor['name']} / {department['name']} / {room['name']}")
        # The branch follows the resolved session, not the caller's default.
        assert appt["branch_id"] == BR
        assert appt["status"] == "BOOKED"

        # Reading it back yields the same snapshot.
        fetched = svc.appointment.get(
            f"/api/v1/appointments/{appt['id']}", headers=headers(OWNER))
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["location_label"] == appt["location_label"]

    def test_booking_outside_every_session_is_refused(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)
        assert _create_session(svc, schedule["id"], room_id=room["id"],
                               start="09:00", end="12:00").status_code == 201

        refused = _book(svc, doctor_id=doctor["id"], start="15:00")
        assert refused.status_code == 422, refused.text
        assert "session" in refused.text.lower()

        # The boundary belongs to the session, the minute past it does not.
        assert _book(svc, doctor_id=doctor["id"],
                     start="12:00").status_code == 422
        assert _book(svc, doctor_id=doctor["id"],
                     start="11:59").status_code == 201

    def test_doctor_without_sessions_books_with_no_chamber(self, svc):
        """Pre-feature behaviour is kept: no session, no chamber, no refusal."""
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        booked = _book(svc, doctor_id=doctor["id"], start="08:15")
        assert booked.status_code == 201, booked.text
        appt = booked.json()
        assert appt["schedule_id"] == schedule["id"]
        assert appt["session_id"] == ""
        assert appt["room_name"] == ""
        assert appt["location_label"] == ""

    def test_snapshot_survives_later_facility_reorganisation(self, svc):
        doctor = _create_doctor(svc)
        schedule = _create_schedule(svc, doctor["id"])
        floor, department, room = _chamber(svc)
        assert _create_session(svc, schedule["id"], room_id=room["id"],
                               start="09:00", end="12:00").status_code == 201
        appt = _book(svc, doctor_id=doctor["id"], start="09:30").json()
        assert appt["room_name"] == room["name"]

        renamed = f"Renamed {uniq('room')}"
        patched = svc.organization.patch(
            f"/api/v1/rooms/{room['id']}", headers=headers(OWNER),
            json={"name": renamed})
        assert patched.status_code == 200, patched.text
        assert patched.json()["name"] == renamed

        # The live facility tree moved on ...
        live = svc.scheduling.get(
            f"/api/v1/schedules/{schedule['id']}/sessions",
            headers=headers(OWNER)).json()
        assert live[0]["room_name"] == renamed

        # ... but the booked slip still names the room the patient was sent to.
        reread = svc.appointment.get(
            f"/api/v1/appointments/{appt['id']}", headers=headers(OWNER)).json()
        assert reread["room_name"] == room["name"]
        assert reread["location_label"] == appt["location_label"]


    def test_walk_in_takes_todays_chamber_and_degrades_without_one(self, svc):
        # A walk-in is registered for the operational "today", so the session it
        # can land in is keyed on the wall clock's weekday.
        day = datetime.now().weekday()

        with_chamber = _create_doctor(svc)
        schedule = _create_schedule(svc, with_chamber["id"])
        floor, department, room = _chamber(svc)
        session = _create_session(svc, schedule["id"], room_id=room["id"],
                                  day=day, start="00:00", end="23:59")
        assert session.status_code == 201, session.text

        walk_in = svc.appointment.post(
            "/api/v1/appointments/walk-in", headers=headers(DESK),
            json={"patient_id": PATIENT, "doctor_id": with_chamber["id"]})
        assert walk_in.status_code == 201, walk_in.text
        body = walk_in.json()
        assert body["appointment_type"] == "walk_in"
        assert body["session_id"] == session.json()["id"]
        assert body["room_name"] == room["name"]
        assert body["location_label"] == (
            f"{floor['name']} / {department['name']} / {room['name']}")

        # A doctor with no session today is still registered — just unchambered.
        without = _create_doctor(svc)
        _create_schedule(svc, without["id"])
        degraded = svc.appointment.post(
            "/api/v1/appointments/walk-in", headers=headers(DESK),
            json={"patient_id": PATIENT, "doctor_id": without["id"]})
        assert degraded.status_code == 201, degraded.text
        assert degraded.json()["session_id"] == ""
        assert degraded.json()["location_label"] == ""

    def test_bookings_are_invisible_across_tenants(self, svc):
        foreign_patient = f"facility-doctor-foreign-patient-{uniq('p')}"
        ensure_patient(foreign_patient, OTHER_ORG, name="Foreign Patient",
                       mobile=_mobile())
        foreign_doctor = svc.doctor.post(
            "/api/v1/doctors", headers=headers(FOREIGN),
            json={"name": f"Dr. ForeignBook {uniq('doc')}",
                  "mobile": _mobile(), "branch_ids": [OTHER_BR]})
        assert foreign_doctor.status_code == 201, foreign_doctor.text

        booked = _book(svc, doctor_id=foreign_doctor.json()["id"],
                       start="10:00", who=FOREIGN, patient_id=foreign_patient)
        assert booked.status_code == 201, booked.text
        assert booked.json()["organization_id"] == OTHER_ORG

        hidden = svc.appointment.get(
            f"/api/v1/appointments/{booked.json()['id']}",
            headers=headers(OWNER))
        assert hidden.status_code == 404, hidden.text

