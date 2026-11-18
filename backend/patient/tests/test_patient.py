"""Tests for the Patient Service — BR §10–§11.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined module
imported ``patient.main._patients_db`` (gone) and passed ``organization_id`` in
the body (the service now derives the tenant from the token).

One legacy expectation is deliberately *not* restored: ``POST
/api/v1/patients/merge`` does not exist and must not.  BR §11 note 4 and MVP
scope §"Patient identity" state that a merge workflow is a later-phase
capability; the MVP warns about possible duplicates and never merges silently.
:func:`TestDuplicateHandling.test_no_silent_merge_route` pins that decision, so
re-introducing merge without the approved workflow fails here first.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org)
from common.models import Patient, StaffUser

ORG = "legacy-pat-org"
BR = "legacy-pat-br"
OTHER_ORG = "legacy-pat-other"
OTHER_BR = "legacy-pat-other-br"
RECP = "legacy_pat_recp"
OTHER_RECP = "legacy_pat_other_recp"
ORG_ADMIN = "legacy_pat_org_admin"
BR_ADMIN = "legacy_pat_br_admin"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("patient"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(OTHER_RECP, "receptionist", OTHER_ORG, OTHER_BR)
    ensure_user(ORG_ADMIN, "org_admin", ORG, BR)
    ensure_user(BR_ADMIN, "branch_admin", ORG, BR)
    yield
    # Teardown: no business rows left behind; reference rows stay (audit).
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _register(client, name="Jamila Begum", mobile="01711111111",
              user=RECP, **extra):
    body = {"name": name, "mobile": mobile}
    body.update(extra)
    return client.post("/api/v1/patients", headers=headers(user), json=body)


class TestPatientRegistration:
    def test_register_patient(self, client):
        r = _register(client)
        assert r.status_code == 201, r.text
        patient = r.json()["patient"]
        assert patient["name"] == "Jamila Begum"
        # The tenant comes from the token; the body cannot choose it.
        assert patient["organization_id"] == ORG
        assert r.json()["duplicates"] == []
        with db_session() as s:
            row = s.query(Patient).filter(Patient.id == patient["id"]).first()
            assert row is not None and row.mobile == "01711111111"

    def test_register_without_name_and_mobile_422(self, client):
        r = _register(client, name="", mobile="")
        assert r.status_code == 422
        with db_session() as s:
            assert s.query(Patient).filter(
                Patient.organization_id == ORG).count() == 0

    def test_register_with_date_of_birth_records_dob_as_age_source(self, client):
        patient = _register(client, date_of_birth="1990-05-10").json()["patient"]
        assert patient["age_source"] == "dob"
        assert patient["age_from_dob"] is not None
        assert patient["age_from_dob"] >= 35

    def test_register_rejects_a_future_date_of_birth(self, client):
        r = _register(client, date_of_birth="2999-01-01")
        assert r.status_code == 422


class TestDuplicateHandling:
    def test_duplicate_mobile_warns(self, client):
        first = _register(client, name="A").json()["patient"]
        r = _register(client, name="B")
        assert r.status_code == 201, r.text
        duplicates = r.json()["duplicates"]
        assert len(duplicates) == 1
        assert duplicates[0]["patient_id"] == first["id"]

    def test_cross_org_duplicate_is_not_a_warning(self, client):
        """Duplicate detection is tenant-local: another clinic's patient list
        is never disclosed as 'a duplicate'."""
        _register(client, name="A")
        r = _register(client, name="B", user=OTHER_RECP)
        assert r.status_code == 201, r.text
        assert r.json()["duplicates"] == []

    def test_no_silent_merge_route(self, client):
        """BR §11 / MVP scope: merging is a later-phase workflow, not MVP.

        ``/api/v1/patients/merge`` matches only the read route
        (``GET /api/v1/patients/{patient_id}``), so a POST is refused as a
        method mismatch — no merge handler exists to call.
        """
        r = client.post("/api/v1/patients/merge", headers=headers(RECP), json={
            "primary_patient_id": "a", "duplicate_patient_id": "b",
            "reason": "same person"})
        assert r.status_code == 405


class TestPatientSearch:
    def test_search_by_name(self, client):
        _register(client, name="Jamila Begum", mobile="01711111111")
        _register(client, name="Rahim Molla", mobile="01722222222")
        r = client.get("/api/v1/patients", params={"q": "Jamila"},
                       headers=headers(RECP))
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["name"] == "Jamila Begum"

    def test_search_by_mobile(self, client):
        _register(client, name="Jamila Begum", mobile="01711111111")
        _register(client, name="Rahim Molla", mobile="01722222222")
        r = client.get("/api/v1/patients", params={"q": "0172222"},
                       headers=headers(RECP))
        assert [p["name"] for p in r.json()["items"]] == ["Rahim Molla"]

    def test_search_is_tenant_isolated(self, client):
        _register(client, name="Karim Molla", mobile="01733333333")
        _register(client, name="Karim Other", mobile="01744444444",
                  user=OTHER_RECP)
        mine = client.get("/api/v1/patients", params={"q": "Karim"},
                          headers=headers(RECP)).json()
        assert mine["total"] == 1
        assert mine["items"][0]["name"] == "Karim Molla"
        theirs = client.get("/api/v1/patients", params={"q": "Karim"},
                            headers=headers(OTHER_RECP)).json()
        assert theirs["total"] == 1
        assert theirs["items"][0]["name"] == "Karim Other"

    def test_pagination_metadata(self, client):
        for i in range(3):
            _register(client, name=f"Patient {i}", mobile=f"0170000000{i}")
        r = client.get("/api/v1/patients", params={"limit": 2},
                       headers=headers(RECP))
        assert r.json()["total"] == 3
        assert len(r.json()["items"]) == 2
        assert r.json()["page"] == 1


class TestPatientReadUpdate:
    def test_get_patient(self, client):
        patient_id = _register(client).json()["patient"]["id"]
        r = client.get(f"/api/v1/patients/{patient_id}", headers=headers(RECP))
        assert r.status_code == 200
        assert r.json()["id"] == patient_id

    def test_get_missing_patient_404(self, client):
        r = client.get("/api/v1/patients/nonexistent", headers=headers(RECP))
        assert r.status_code == 404

    def test_foreign_tenant_patient_is_a_404(self, client):
        patient_id = _register(client).json()["patient"]["id"]
        r = client.get(f"/api/v1/patients/{patient_id}",
                       headers=headers(OTHER_RECP))
        assert r.status_code == 404

    def test_update_patient(self, client):
        patient_id = _register(client).json()["patient"]["id"]
        r = client.patch(f"/api/v1/patients/{patient_id}",
                         headers=headers(ORG_ADMIN),
                         json={"name": "Jamila Akter", "address": "Mirpur"})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Jamila Akter"
        assert r.json()["address"] == "Mirpur"
        with db_session() as s:
            assert s.query(Patient).filter(
                Patient.id == patient_id).first().name == "Jamila Akter"

    def test_branch_admin_can_update_patient(self, client):
        patient_id = _register(client).json()["patient"]["id"]
        r = client.patch(f"/api/v1/patients/{patient_id}",
                         headers=headers(BR_ADMIN),
                         json={"name": "Jamila Akter", "address": "Mirpur"})
        assert r.status_code == 200, r.text

    def test_receptionist_cannot_update_patient_403(self, client):
        patient_id = _register(client).json()["patient"]["id"]
        r = client.patch(f"/api/v1/patients/{patient_id}",
                         headers=headers(RECP), json={"name": "Hijacked"})
        assert r.status_code == 403, r.text
        with db_session() as s:
            assert s.query(Patient).filter(
                Patient.id == patient_id).first().name == "Jamila Begum"

    def test_doctor_cannot_update_patient_403(self, client):
        # A doctor has patient.read/search only — never patient.update.
        import uuid, bcrypt
        doc_staff_id = f"pat-doc-upd-staff-{uuid.uuid4().hex[:6]}"
        doc_username = f"pat_doc_upd_{uuid.uuid4().hex[:6]}"
        with db_session() as s:
            pw = bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode()
            s.add(StaffUser(id=doc_staff_id,
                organization_id=ORG, branch_id=BR,
                username=doc_username, password_hash=pw,
                display_name="Dr Upd", role="doctor", status="active"))
            s.commit()
        r = client.patch(f"/api/v1/patients/{_register(client).json()['patient']['id']}",
                         headers=headers(doc_username),
                         json={"name": "Hijacked"})
        assert r.status_code == 403, r.text

    def test_assistant_cannot_update_patient_403(self, client):
        # An assistant has patient.read/search only — never patient.update.
        import uuid, bcrypt
        asst_staff_id = f"pat-ass-upd-staff-{uuid.uuid4().hex[:6]}"
        asst_username = f"pat_ass_upd_{uuid.uuid4().hex[:6]}"
        with db_session() as s:
            pw = bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode()
            s.add(StaffUser(id=asst_staff_id,
                organization_id=ORG, branch_id=BR,
                username=asst_username, password_hash=pw,
                display_name="Asst Upd", role="assistant", status="active"))
            s.commit()
        r = client.patch(f"/api/v1/patients/{_register(client).json()['patient']['id']}",
                         headers=headers(asst_username),
                         json={"name": "Hijacked"})
        assert r.status_code == 403, r.text

    def test_foreign_tenant_patient_cannot_be_updated(self, client):
        # Register the patient as OTHER_RECP (in OTHER_ORG), then try to update
        # as ORG_ADMIN (in ORG) — permission passes but the tenant lookup fails.
        patient_id = _register(client, user=OTHER_RECP).json()["patient"]["id"]
        assert patient_id  # sanity: the patient was created in OTHER_ORG
        r = client.patch(f"/api/v1/patients/{patient_id}",
                         headers=headers(ORG_ADMIN), json={"name": "Hijacked"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Patient).filter(
                Patient.id == patient_id).first().name == "Jamila Begum"
