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

import itertools
import uuid

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org, uniq)
from common.models import Doctor, DoctorBranch

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


_MOBILE_SENTINEL = object()
_MOBILE_SEQ = itertools.count(1)
#: A per-process random base, so two runs against the same database cannot collide
#: either (the doctor rows are reference data and are never purged).
_MOBILE_BASE = int(uuid.uuid4().int % 900000) * 1000


def _next_mobile() -> str:
    """A canonical, unique BD mobile number for one doctor creation.

    ``create_doctor`` enforces one doctor per (organization, mobile) and answers
    409 otherwise, while doctors are reference rows the audit trail points at and
    are deliberately never deleted between tests.  A fixed fixture mobile number
    therefore made every test after the first in a class collide — nine tests
    could not create the doctor they were about.  The number is unique per call
    here; none of the assertions is about the mobile value.
    """
    return f"017{(_MOBILE_BASE + next(_MOBILE_SEQ)) % 100000000:08d}"


def _doctor_count() -> int:
    """How many doctors this organization has right now."""
    with db_session() as s:
        return s.query(Doctor).filter(Doctor.organization_id == ORG).count()


def _create(client, name="Dr. Rahman", mobile=_MOBILE_SENTINEL, **extra):
    body = {"name": name,
            "mobile": _next_mobile() if mobile is _MOBILE_SENTINEL else mobile}
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

    def test_branch_assignment_with_a_foreign_branch_is_a_422(self, client):
        """A foreign branch id is refused, never linked across tenants.

        Owner decision B (2026-11-23) settles the contract the trial merge
        surfaced (**D-1**): the endpoint **rejects** the whole request with
        ``422`` instead of silently dropping the foreign id and answering
        ``201``.  Dropping it made a successful-looking create whose chamber
        assignments were not what the caller asked for; a refusal is the honest
        answer, and it is what the code already did.

        The message must not disclose anything about the other tenant: it says
        the branch is not in *this* organization, and never confirms that the id
        exists elsewhere.  Nothing is written either — no doctor row, no
        ``doctor_branches`` row.
        """
        before = _doctor_count()
        r = _create(client, branch_ids=[BR, OTHER_BR])
        assert r.status_code == 422, r.text
        assert r.json()["detail"] == "branch not found in this organization"
        # Non-disclosing: the refusal is identical whether or not the id exists.
        assert "other" not in r.text.lower()
        assert _doctor_count() == before

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
        assert _create(client, name=mine_name).status_code == 201
        r = client.post("/api/v1/doctors", headers=headers(OTHER_ADMIN),
                        json={"name": theirs_name, "mobile": _next_mobile()})
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
        _create(client, name=f"Dr. Karim {tag}", speciality="Cardiology")
        _create(client, name=f"Dr. Salma {tag}", speciality=speciality)
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
        _create(client, name=branchful, branch_ids=[BR])
        _create(client, name=branchless)
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

    def test_retired_assignment_is_preserved_but_not_serialised(self, client):
        """Owner decision C (2026-11-23) settles **D-2**.

        The response lists only the assignments now in force.  The row itself is
        *retired* (``status = inactive``), never deleted — it carries the chamber
        an appointment was booked into — and re-adding the branch reactivates the
        same row instead of inserting a duplicate.
        """
        doc_id = _create(client, branch_ids=[BR]).json()["id"]
        r = client.patch(f"/api/v1/doctors/{doc_id}", headers=headers(ADMIN),
                         json={"branch_ids": []})
        assert r.status_code == 200, r.text
        assert r.json()["branch_ids"] == []
        assert r.json()["branches"] == []
        assert r.json()["primary_branch_id"] is None

        with db_session() as s:
            rows = s.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == doc_id).all()
            assert len(rows) == 1, "the historical row must survive the update"
            assert rows[0].status == "inactive"
            assert rows[0].is_primary is False

        # A later read agrees with the update, and re-adding reactivates the row.
        assert client.get(f"/api/v1/doctors/{doc_id}",
                          headers=headers(ADMIN)).json()["branch_ids"] == []
        again = client.patch(f"/api/v1/doctors/{doc_id}",
                             headers=headers(ADMIN),
                             json={"branch_ids": [BR]})
        assert again.status_code == 200, again.text
        assert again.json()["branch_ids"] == [BR]
        with db_session() as s:
            rows = s.query(DoctorBranch).filter(
                DoctorBranch.doctor_id == doc_id).all()
            assert len(rows) == 1, "uq_doctor_branch: no duplicate assignment"
            assert rows[0].status == "active"

    def test_foreign_tenant_doctor_cannot_be_updated(self, client):
        doc_id = _create(client).json()["id"]
        r = client.patch(f"/api/v1/doctors/{doc_id}",
                         headers=headers(OTHER_ADMIN),
                         json={"name": "Hijacked"})
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(Doctor).filter(
                Doctor.id == doc_id).first().name == "Dr. Rahman"
