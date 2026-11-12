"""Tests for the Doctor Service — BR §9.

**Rewritten for Sequence 4 finding LEGACY-TESTS-P1.**  The quarantined module
imported ``doctor.main._doctors_db`` — an in-memory dict that no longer exists —
and passed ``organization_id`` in the request body, which the service now ignores
by design (the tenant comes from the token).  This version authenticates real
staff users and asserts against PostgreSQL.

Doctors are *business* rows of an organization, so they are purged before each
test and re-created through the API: the counts below are exact rather than
"at least one", which is what makes the tenant-isolation assertions meaningful.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org, uniq)
from common.models import Doctor

ORG = "legacy-doc-org"
BR = "legacy-doc-br"
OTHER_ORG = "legacy-doc-other-org"
OTHER_BR = "legacy-doc-other-br"
ADMIN = "legacy_doc_admin"
OTHER_ADMIN = "legacy_doc_other_admin"
RECP = "legacy_doc_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("doctor"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "branch_admin", OTHER_ORG, OTHER_BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    yield
    # Teardown: no business rows left behind; reference rows stay (audit).
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _create(client, name="Dr. Rahman", mobile="01711111111", **extra):
    body = {"name": name, "mobile": mobile}
    body.update(extra)
    return client.post("/api/v1/doctors", headers=headers(ADMIN), json=body)


class TestDoctorCreate:
    def test_create_doctor(self, client):
        r = _create(client, name="Dr. Rahman", speciality="Cardiology")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Dr. Rahman"
        assert body["speciality"] == "Cardiology"
        # Tenant identity is derived from the token, never from the body.
        assert body["organization_id"] == ORG
        assert body["status"] == "active"
        with db_session() as s:
            row = s.query(Doctor).filter(Doctor.id == body["id"]).first()
            assert row is not None and row.name == "Dr. Rahman"

    def test_create_without_name_and_mobile_422(self, client):
        r = _create(client, name="", mobile="")
        assert r.status_code == 422
        with db_session() as s:
            assert s.query(Doctor).filter(
                Doctor.organization_id == ORG, Doctor.name == "").count() == 0

    def test_branch_assignment_is_limited_to_the_owning_org(self, client):
        """A foreign branch id is dropped, never linked across tenants."""
        r = _create(client, branch_ids=[BR, OTHER_BR])
        assert r.status_code == 201, r.text
        assert r.json()["branch_ids"] == [BR]

    def test_receptionist_cannot_create_a_doctor(self, client):
        r = client.post("/api/v1/doctors", headers=headers(RECP),
                        json={"name": "Dr. No", "mobile": "01799999999"})
        assert r.status_code == 403

    def test_create_requires_authentication(self, client):
        r = client.post("/api/v1/doctors",
                        json={"name": "Dr. No", "mobile": "01799999999"})
        assert r.status_code == 401


class TestDoctorSearch:
    def test_search_is_scoped_to_the_callers_org(self, client):
        """Each token's list contains its own doctors and no foreign ones.

        Doctors are reference rows the audit trail points at, so they are never
        deleted between tests; the assertions therefore scope themselves to names
        created here instead of to a total count.
        """
        tag = uniq("scope")
        mine_name = f"Dr. Mine {tag}"
        theirs_name = f"Dr. Theirs {tag}"
        assert _create(client, name=mine_name,
                       mobile="01711111111").status_code == 201
        r = client.post("/api/v1/doctors", headers=headers(OTHER_ADMIN),
                        json={"name": theirs_name, "mobile": "01733333333"})
        assert r.status_code == 201, r.text

        mine = client.get("/api/v1/doctors", headers=headers(ADMIN)).json()
        assert {d["organization_id"] for d in mine["items"]} == {ORG}
        assert mine_name in {d["name"] for d in mine["items"]}
        assert theirs_name not in {d["name"] for d in mine["items"]}

        theirs = client.get("/api/v1/doctors",
                            headers=headers(OTHER_ADMIN)).json()
        assert {d["organization_id"] for d in theirs["items"]} == {OTHER_ORG}
        assert theirs_name in {d["name"] for d in theirs["items"]}
        assert mine_name not in {d["name"] for d in theirs["items"]}

    def test_search_by_name_and_speciality(self, client):
        tag = uniq("filter")
        speciality = f"Neurology {tag}"
        _create(client, name=f"Dr. Karim {tag}", speciality="Cardiology",
                mobile="01711111111")
        _create(client, name=f"Dr. Salma {tag}", speciality=speciality,
                mobile="01722222222")
        by_name = client.get("/api/v1/doctors", params={"q": f"Karim {tag}"},
                             headers=headers(ADMIN)).json()
        assert by_name["total"] == 1
        assert by_name["items"][0]["name"] == f"Dr. Karim {tag}"
        by_speciality = client.get("/api/v1/doctors",
                                   params={"speciality": speciality},
                                   headers=headers(ADMIN)).json()
        assert [d["name"] for d in by_speciality["items"]] == [
            f"Dr. Salma {tag}"]

    def test_search_by_branch_filters_unassigned_doctors(self, client):
        tag = uniq("branch")
        branchful = f"Dr. Branchful {tag}"
        branchless = f"Dr. Branchless {tag}"
        _create(client, name=branchful, branch_ids=[BR], mobile="01711111111")
        _create(client, name=branchless, mobile="01722222222")
        r = client.get("/api/v1/doctors", params={"branch_id": BR},
                       headers=headers(ADMIN))
        names = {d["name"] for d in r.json()["items"]}
        assert branchful in names
        assert branchless not in names


class TestDoctorReadUpdate:
    def test_get_doctor(self, client):
        doc_id = _create(client, name="Dr. X").json()["id"]
        r = client.get(f"/api/v1/doctors/{doc_id}", headers=headers(ADMIN))
        assert r.status_code == 200
        assert r.json()["name"] == "Dr. X"

    def test_get_missing_doctor_404(self, client):
        r = client.get("/api/v1/doctors/nonexistent", headers=headers(ADMIN))
        assert r.status_code == 404

    def test_foreign_tenant_doctor_is_a_404(self, client):
        doc_id = _create(client).json()["id"]
        r = client.get(f"/api/v1/doctors/{doc_id}",
                       headers=headers(OTHER_ADMIN))
        assert r.status_code == 404

    def test_update_doctor(self, client):
        doc_id = _create(client, name="Dr. Old").json()["id"]
        r = client.patch(f"/api/v1/doctors/{doc_id}", headers=headers(ADMIN),
                         json={"name": "Dr. Updated",
                               "speciality": "Neurology"})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Dr. Updated"
        assert r.json()["speciality"] == "Neurology"
        with db_session() as s:
            row = s.query(Doctor).filter(Doctor.id == doc_id).first()
            assert (row.name, row.speciality) == ("Dr. Updated", "Neurology")

    def test_update_replaces_branch_assignments(self, client):
        doc_id = _create(client, branch_ids=[BR]).json()["id"]
        r = client.patch(f"/api/v1/doctors/{doc_id}", headers=headers(ADMIN),
                         json={"branch_ids": []})
        assert r.status_code == 200, r.text
        assert r.json()["branch_ids"] == []

    def test_foreign_tenant_doctor_cannot_be_updated(self, client):
        doc_id = _create(client).json()["id"]
        r = client.patch(f"/api/v1/doctors/{doc_id}",
                         headers=headers(OTHER_ADMIN),
                         json={"name": "Hijacked"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Doctor).filter(
                Doctor.id == doc_id).first().name == "Dr. Rahman"
