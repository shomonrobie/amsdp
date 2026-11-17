"""Symptom catalogue + appointment symptom recording — AMSDP-SYMPTOM-01.

Every test drives the real service app against PostgreSQL and reads its
assertions back through ``SessionFactory``, so a green test means the rows are
in the database — not in a dict the test itself populated.  Authentication is
real (``headers()`` mints a JWT from a real ``staff_users`` row), so the tenant
scoping under test is the production one.

What is deliberately *not* tested here: search ranking.  Ranking is a pure
function over the catalogue in the browser
(``frontend/lib/symptom-catalogue``), covered by ``symptom-catalogue-*.test.mjs``
under ``node --test``.  Re-implementing the Bengali normaliser in Python to test
it twice is exactly the second language-sense engine this feature must not have.
"""

import json

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_symptom,
                               ensure_user, headers, load_app, purge_org)
from common.models import (Appointment, AppointmentSymptom, AuditEvent,
                           SymptomCatalog)

ORG = "symptom-org"
BR = "symptom-br"
OTHER_ORG = "symptom-other-org"
DOC = "symptom-doc"
PAT = "symptom-pat"
RECP = "symptom_recp"
ADMIN = "symptom_admin"

DAY = "2032-05-10"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def world(client):
    """A fresh, isolated organization with a small known catalogue."""
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_doctor(DOC, ORG, name="Dr. Symptom", mobile="01700002001")
    ensure_patient(PAT, ORG, name="Symptom Patient", mobile="01700002002")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    catalogue = {
        "headache": ensure_symptom(
            "headache", ORG, name_en="Headache", name_bn="মাথাব্যথা",
            synonyms_en=["head pain"], synonyms_bn=["মাথা ব্যথা"],
            category="neurological", specialty_hints=["medicine"], sort_order=10),
        "cough": ensure_symptom(
            "cough", ORG, name_en="Cough", name_bn="কাশি",
            synonyms_en=["coughing"], synonyms_bn=["শুকনো কাশি"],
            category="respiratory", sort_order=20),
        "chest_pain": ensure_symptom(
            "chest_pain", ORG, name_en="Chest pain", name_bn="বুকে ব্যথা",
            category="cardiovascular", specialty_hints=["cardiology"],
            sort_order=30),
        "retired": ensure_symptom(
            "retired_symptom", ORG, name_en="Retired entry",
            name_bn="বন্ধ এন্ট্রি", status="inactive"),
        # Another tenant's entry — must be invisible and unusable here.
        "foreign": ensure_symptom(
            "foreign_symptom", OTHER_ORG, name_en="Foreign entry"),
    }
    yield catalogue
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _book(client, *, start="09:00", patient=PAT, **extra):
    payload = {"patient_id": patient, "doctor_id": DOC,
               "appointment_date": DAY, "start_time": start}
    payload.update(extra)
    return client.post("/api/v1/appointments", headers=headers(RECP),
                       json=payload)


def _symptom_rows(appointment_id, org=ORG):
    with db_session() as s:
        return (s.query(AppointmentSymptom)
                .filter(AppointmentSymptom.organization_id == org,
                        AppointmentSymptom.appointment_id == appointment_id)
                .order_by(AppointmentSymptom.created_at,
                          AppointmentSymptom.id).all())


def _appointments(org=ORG):
    with db_session() as s:
        return s.query(Appointment).filter(
            Appointment.organization_id == org).all()


class TestCatalogue:
    def test_requires_authentication(self, client):
        assert client.get("/api/v1/symptoms").status_code == 401

    def test_returns_only_this_organizations_active_entries(self, client, world):
        r = client.get("/api/v1/symptoms", headers=headers(RECP))
        assert r.status_code == 200, r.text
        codes = {item["code"] for item in r.json()["items"]}
        assert codes == {"headache", "cough", "chest_pain"}
        assert "foreign_symptom" not in codes, "cross-tenant entry leaked"
        assert "retired_symptom" not in codes, "retired entry offered for booking"

    def test_entry_shape_carries_both_scripts_and_provenance(self, client, world):
        body = client.get("/api/v1/symptoms", headers=headers(RECP)).json()
        headache = next(i for i in body["items"] if i["code"] == "headache")
        assert headache["name_en"] == "Headache"
        assert headache["name_bn"] == "মাথাব্যথা"
        assert headache["synonyms_bn"] == ["মাথা ব্যথা"]
        assert headache["category"] == "neurological"
        assert headache["specialty_hints"] == ["medicine"]
        assert headache["status"] == "active"
        # Provenance travels with the payload: the UI can never claim more than
        # the recorded review state supports.
        assert headache["review_status"] in body["review_status_values"]
        assert body["max_symptoms"] == 20
        assert "Not a diagnosis" in body["disclaimer"]

    def test_inactive_entries_need_manage_permission(self, client, world):
        url = "/api/v1/symptoms?include_inactive=true"
        assert client.get(url, headers=headers(RECP)).status_code == 403
        admin = client.get(url, headers=headers(ADMIN))
        assert admin.status_code == 200, admin.text
        assert "retired_symptom" in {i["code"] for i in admin.json()["items"]}

    def test_onset_options_are_bilingual_and_closed(self, client, world):
        body = client.get("/api/v1/symptoms", headers=headers(RECP)).json()
        options = body["onset_options"]
        assert [o["code"] for o in options] == [
            "TODAY", "YESTERDAY", "FEW_DAYS", "FEW_WEEKS", "OVER_MONTH",
            "LONG_STANDING", "UNKNOWN"]
        for option in options:
            assert option["name_en"] and option["name_bn"]

    def test_onset_options_route_serves_the_same_vocabulary(self, client, world):
        r = client.get("/api/v1/symptoms/onset-options", headers=headers(RECP))
        assert r.status_code == 200
        assert len(r.json()["items"]) == 7


class TestBooking:
    def test_booking_without_symptoms_still_works(self, client, world):
        """The whole feature is optional: a booking with no symptoms is normal."""
        r = _book(client)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["symptoms"] == []
        assert body["symptom_onset"] == ""
        assert body["symptom_onset_note"] == ""
        assert _symptom_rows(body["id"]) == []

    def test_one_catalogue_symptom_is_recorded_with_a_snapshot(
            self, client, world):
        r = _book(client, start="09:05",
                  symptom_ids=[world["headache"]])
        assert r.status_code == 201, r.text
        body = r.json()
        assert len(body["symptoms"]) == 1
        recorded = body["symptoms"][0]
        assert recorded["kind"] == "catalogue"
        assert recorded["symptom_id"] == world["headache"]
        assert recorded["name_en"] == "Headache"
        assert recorded["name_bn"] == "মাথাব্যথা"
        assert recorded["text"] == ""
        rows = _symptom_rows(body["id"])
        assert len(rows) == 1
        assert rows[0].organization_id == ORG
        assert rows[0].recorded_by, "the receptionist who recorded it is kept"

    def test_multiple_symptoms_are_recorded_in_order(self, client, world):
        r = _book(client, start="09:10",
                  symptom_ids=[world["chest_pain"], world["headache"]],
                  symptom_texts=["মাথার পেছনে চাপ অনুভব করছি"])
        assert r.status_code == 201, r.text
        body = r.json()
        assert [s["kind"] for s in body["symptoms"]] == [
            "catalogue", "catalogue", "free_text"]
        assert body["symptoms"][2]["text"] == "মাথার পেছনে চাপ অনুভব করছি"
        assert len(_symptom_rows(body["id"])) == 3

    def test_onset_can_be_recorded_without_any_symptom(self, client, world):
        r = _book(client, start="09:15", symptom_onset="FEW_DAYS",
                  symptom_onset_note="প্রায় চার দিন ধরে")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["symptom_onset"] == "FEW_DAYS"
        assert body["symptom_onset_note"] == "প্রায় চার দিন ধরে"
        assert body["symptoms"] == []

    def test_unknown_onset_answer_is_kept_as_an_answer(self, client, world):
        """``UNKNOWN`` means "asked, could not say" — not "not asked"."""
        body = _book(client, start="09:20", symptom_onset="UNKNOWN").json()
        assert body["symptom_onset"] == "UNKNOWN"
        assert _book(client, start="09:25").json()["symptom_onset"] == ""

    def test_duplicate_catalogue_selection_collapses(self, client, world):
        r = _book(client, start="09:30",
                  symptom_ids=[world["headache"], world["headache"]])
        assert r.status_code == 201, r.text
        assert len(r.json()["symptoms"]) == 1
        assert len(_symptom_rows(r.json()["id"])) == 1

    def test_duplicate_free_text_collapses(self, client, world):
        r = _book(client, start="09:35",
                  symptom_texts=["মাথা ব্যথা", "  মাথা ব্যথা  ", "মাথা   ব্যথা"])
        assert r.status_code == 201, r.text
        rows = _symptom_rows(r.json()["id"])
        assert len(rows) == 1
        assert rows[0].text_reported == "মাথা ব্যথা"


class TestRejections:
    def test_unknown_symptom_id_is_rejected_and_nothing_is_created(
            self, client, world):
        r = _book(client, start="10:00", symptom_ids=["no-such-symptom"])
        assert r.status_code == 422
        assert _appointments() == []

    def test_cross_tenant_symptom_is_indistinguishable_from_unknown(
            self, client, world):
        foreign = _book(client, start="10:05", symptom_ids=[world["foreign"]])
        unknown = _book(client, start="10:10", symptom_ids=["no-such-symptom"])
        assert foreign.status_code == 422 == unknown.status_code
        assert foreign.json()["detail"] == unknown.json()["detail"], (
            "a cross-tenant id must not be distinguishable from an unknown one")
        assert _appointments() == []

    def test_retired_symptom_cannot_be_booked(self, client, world):
        r = _book(client, start="10:15", symptom_ids=[world["retired"]])
        assert r.status_code == 422
        assert _appointments() == []

    def test_unknown_onset_code_is_rejected(self, client, world):
        r = _book(client, start="10:20", symptom_onset="SOMETIME")
        assert r.status_code == 422
        assert _appointments() == []

    def test_too_many_symptoms_are_rejected(self, client, world):
        r = _book(client, start="10:25",
                  symptom_texts=[f"complaint number {i}" for i in range(21)])
        assert r.status_code == 422
        assert "20" in r.json()["detail"]
        assert _appointments() == []

    def test_an_over_long_description_is_rejected(self, client, world):
        r = _book(client, start="10:30", symptom_texts=["ক" * 201])
        assert r.status_code == 422
        assert _appointments() == []


class TestHistory:
    def test_snapshot_survives_a_catalogue_rename(self, client, world):
        body = _book(client, start="11:00", symptom_ids=[world["headache"]]).json()
        with db_session() as s:
            row = s.query(SymptomCatalog).filter(
                SymptomCatalog.id == world["headache"]).first()
            row.name_en = "Headache (renamed)"
            row.name_bn = "মাথাব্যথা (নতুন)"
            s.commit()
        detail = client.get(f"/api/v1/appointments/{body['id']}",
                            headers=headers(RECP)).json()
        assert detail["symptoms"][0]["name_en"] == "Headache", (
            "an existing visit must keep the wording recorded at booking time")
        catalogue = client.get("/api/v1/symptoms", headers=headers(RECP)).json()
        renamed = next(i for i in catalogue["items"] if i["code"] == "headache")
        assert renamed["name_en"] == "Headache (renamed)"

    def test_symptoms_appear_in_the_calendar_list_and_the_detail(
            self, client, world):
        body = _book(client, start="11:05", symptom_ids=[world["cough"]],
                     symptom_onset="TODAY").json()
        listed = client.get(
            f"/api/v1/appointments?date_from={DAY}&date_to={DAY}",
            headers=headers(RECP)).json()
        row = next(a for a in listed if a["id"] == body["id"])
        assert [s["symptom_id"] for s in row["symptoms"]] == [world["cough"]]
        assert row["symptom_onset"] == "TODAY"
        detail = client.get(f"/api/v1/appointments/{body['id']}",
                            headers=headers(RECP)).json()
        assert len(detail["symptoms"]) == 1


class TestOtherBookingPaths:
    def test_walk_in_records_symptoms(self, client, world):
        r = client.post("/api/v1/appointments/walk-in", headers=headers(RECP),
                        json={"patient_id": PAT, "doctor_id": DOC,
                              "symptom_ids": [world["headache"]],
                              "symptom_texts": ["হঠাৎ করে শুরু হয়েছে"],
                              "symptom_onset": "TODAY"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert [s["kind"] for s in body["symptoms"]] == ["catalogue", "free_text"]
        assert body["symptom_onset"] == "TODAY"

    def test_reschedule_carries_the_complaint_forward(self, client, world):
        original = _book(client, start="11:30", symptom_ids=[world["headache"]],
                         symptom_texts=["বিশেষ কিছু"], symptom_onset="FEW_DAYS",
                         symptom_onset_note="সোমবার থেকে").json()
        moved = client.post(
            f"/api/v1/appointments/{original['id']}/reschedule",
            headers=headers(RECP),
            json={"new_date": "2032-05-11", "new_start_time": "09:00",
                  "reason": "patient request"})
        assert moved.status_code == 200, moved.text
        new = moved.json()["new_appointment"]
        assert len(new["symptoms"]) == 2
        assert new["symptom_onset"] == "FEW_DAYS"
        assert new["symptom_onset_note"] == "সোমবার থেকে"
        # The original visit keeps its own record (history is not rewritten).
        assert len(_symptom_rows(original["id"])) == 2
        assert len(_symptom_rows(new["id"])) == 2


class TestAudit:
    def test_audit_keeps_symptom_metadata_but_not_the_patients_words(
            self, client, world):
        """The trail proves what happened without duplicating clinical text.

        ``audit_events`` is append-only and permanent, so it records catalogue
        ids, counts and the onset code — enough to evidence the booking — and
        never copies the patient's free-text description into it.
        """
        words = "খুব অস্বস্তি হচ্ছে, ঠিক করে বলতে পারছি না"
        body = _book(client, start="12:00", symptom_ids=[world["headache"]],
                     symptom_texts=[words], symptom_onset="TODAY").json()
        with db_session() as s:
            event = (s.query(AuditEvent)
                     .filter(AuditEvent.action == "appointment.created",
                             AuditEvent.target_id == body["id"]).first())
        assert event is not None, "booking must be audited"
        after = event.after or {}
        assert after["symptom_count"] == 2
        assert after["symptom_ids"] == [world["headache"]]
        assert after["symptom_text_count"] == 1
        assert after["symptom_onset"] == "TODAY"
        assert words not in json.dumps(after, ensure_ascii=False)

    def test_a_denied_catalogue_read_is_audited(self, client, world):
        """A 403 is recorded, never silently swallowed (``.clinerules`` §3)."""
        client.get("/api/v1/symptoms?include_inactive=true",
                   headers=headers(RECP))
        with db_session() as s:
            event = (s.query(AuditEvent)
                     .filter(AuditEvent.organization_id == ORG,
                             AuditEvent.action == "request.denied")
                     .order_by(AuditEvent.timestamp.desc()).first())
        assert event is not None
        assert event.actor_id




