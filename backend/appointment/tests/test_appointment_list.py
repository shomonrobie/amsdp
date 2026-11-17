"""Administrative appointment list — ``GET /api/v1/appointments/list``.

AMSDP-CALENDAR-UX-01 §11 added a *paged, searched, sorted* read path for the
calendar's List view, because paginating an unpaged endpoint in the browser means
downloading the organization's whole appointment history.  These tests drive the
real service against PostgreSQL and read the assertions back through
``SessionFactory``.

The authorization cases are the point of the module, not an afterthought:

* another tenant's appointments are invisible even when their id is guessed;
* a branch-scoped token cannot widen its own scope through ``branch_id``, and
  asking for a foreign branch answers **404**, not 403 (non-disclosing);
* the response is capped at 100 rows whatever the caller asks for.

Every test uses its own organization and purges only its own business rows, so it
can run against the shared development database.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment

ORG = "cal-list-org"
BR = "cal-list-br"
BR2 = "cal-list-br2"
OTHER_ORG = "cal-list-other-org"
OTHER_BR = "cal-list-other-br"
DOC_A = "cal-list-doc-a"
DOC_B = "cal-list-doc-b"
PAT_A = "cal-list-pat-a"
PAT_B = "cal-list-pat-b"
PAT_BN = "cal-list-pat-bn"
PAT_FOREIGN = "cal-list-pat-foreign"
RECP = "cal_list_recp"
RECP2 = "cal_list_recp2"
ORGADM = "cal_list_orgadm"
OTHER_RECP = "cal_list_other_recp"

DAY = "2031-05-12"
DAY2 = "2031-05-13"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("appointment"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_doctor(DOC_A, ORG, name="Dr. Fatima Begum", mobile="01700002001")
    ensure_doctor(DOC_B, ORG, name="Dr. Abdul Karim", mobile="01700002002")
    ensure_patient(PAT_A, ORG, name="Momena Begum", mobile="01711110001")
    ensure_patient(PAT_B, ORG, name="Sultana Akter", mobile="01711110002")
    ensure_patient(PAT_BN, ORG, name="রহিম উদ্দিন", mobile="01711110003")
    ensure_patient(PAT_FOREIGN, OTHER_ORG, name="Foreign Patient",
                   mobile="01799990001")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(RECP2, "receptionist", ORG, BR2)
    ensure_user(ORGADM, "org_admin", ORG, None)
    ensure_user(OTHER_RECP, "receptionist", OTHER_ORG, OTHER_BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _insert(*, org=ORG, branch=BR, patient=PAT_A, doctor=DOC_A, day=DAY,
            start="09:00", status="BOOKED", token=None):
    """One real appointment row, written through the service's own engine."""
    with db_session() as s:
        appt = Appointment(
            organization_id=org, branch_id=branch, patient_id=patient,
            doctor_id=doctor, appointment_date=date.fromisoformat(day),
            start_time=start, status=status,
            token_number=token or ("T-" + start.replace(":", "")),
            status_history=[{"status": status}],
        )
        s.add(appt)
        s.commit()
        return appt.id


def _get(client, user=RECP, **params):
    return client.get("/api/v1/appointments/list", headers=headers(user),
                      params=params)


class TestEnvelopeAndPaging:
    def test_page_envelope_reports_the_matching_total(self, client):
        _insert(day=DAY, start="09:00")
        _insert(day=DAY, start="09:30")
        _insert(day=DAY2, start="10:00")

        body = _get(client, limit=2).json()
        assert body["total"] == 3
        assert body["limit"] == 2
        assert body["page"] == 1
        assert body["pages"] == 2
        assert len(body["items"]) == 2

        second = _get(client, limit=2, page=2).json()
        assert len(second["items"]) == 1
        assert second["page"] == 2

    def test_pages_never_overlap_and_cover_every_row(self, client):
        for minute in ("09:00", "09:30", "10:00", "10:30", "11:00"):
            _insert(start=minute)
        seen = []
        for page in (1, 2, 3):
            seen += [a["id"] for a in _get(client, limit=2, page=page).json()["items"]]
        assert len(seen) == 5
        assert len(set(seen)) == 5

    def test_empty_result_is_an_empty_page_not_an_error(self, client):
        body = _get(client).json()
        assert body == {"items": [], "total": 0, "page": 1, "limit": 25,
                        "pages": 0}

    def test_limit_is_capped_at_one_hundred(self, client):
        # The cap is the difference between a page and an unbounded dump.
        assert _get(client, limit=101).status_code == 422
        assert _get(client, limit=0).status_code == 422
        assert _get(client, page=0).status_code == 422
        for size in (25, 50, 100):
            assert _get(client, limit=size).status_code == 200

    def test_rows_carry_the_names_the_list_view_shows(self, client):
        _insert()
        item = _get(client).json()["items"][0]
        assert item["patient_name"] == "Momena Begum"
        assert item["patient_mobile"] == "01711110001"
        assert item["doctor_name"] == "Dr. Fatima Begum"
        assert item["branch_name"] == BR
        # The grid payload is reused, not re-invented: location snapshot included.
        assert "location_label" in item and "status" in item


class TestSearch:
    def test_search_by_patient_name(self, client):
        _insert(patient=PAT_A)
        _insert(patient=PAT_B, start="10:00")
        body = _get(client, q="momena").json()
        assert body["total"] == 1
        assert body["items"][0]["patient_name"] == "Momena Begum"

    def test_search_is_case_insensitive_and_partial(self, client):
        _insert(patient=PAT_A)
        assert _get(client, q="MOMENA").json()["total"] == 1
        assert _get(client, q="Beg").json()["total"] == 1

    def test_search_finds_a_bangla_name_and_part_of_it(self, client):
        """Bangla has no case, so ILIKE on UTF-8 is exactly the intended match.

        The desk types what the patient says — sometimes the first name, sometimes
        only the middle of it — so a substring inside the word must match too.
        """
        _insert(patient=PAT_BN, start="12:00")
        assert _get(client, q="রহিম").json()["total"] == 1
        assert _get(client, q="উদ্দিন").json()["total"] == 1
        assert _get(client, q="হিম উ").json()["total"] == 1
        # A Bangla term that is not there stays not-there: no fuzzy widening.
        assert _get(client, q="করিম").json()["total"] == 0

    def test_search_by_mobile_ignores_punctuation(self, client):
        _insert(patient=PAT_A)
        assert _get(client, q="01711110001").json()["total"] == 1
        assert _get(client, q="017-1111-0001").json()["total"] == 1
        assert _get(client, q="1111000").json()["total"] == 1
        assert _get(client, q="01711110009").json()["total"] == 0

    def test_search_by_appointment_id(self, client):
        appt_id = _insert()
        body = _get(client, q=appt_id).json()
        assert body["total"] == 1
        assert body["items"][0]["id"] == appt_id

    def test_search_by_token_number(self, client):
        _insert(start="11:30", token="T-1130")
        assert _get(client, q="T-1130").json()["total"] == 1

    def test_search_wildcards_are_literal(self, client):
        # '%' must not become "match everything".
        _insert()
        assert _get(client, q="%").json()["total"] == 0

    def test_search_never_crosses_the_tenant_boundary(self, client):
        foreign = _insert(org=OTHER_ORG, branch=OTHER_BR, patient=PAT_FOREIGN,
                          doctor=DOC_A, day=DAY)
        # RECP must not find it by id, name or mobile.
        assert _get(client, q=foreign).json()["total"] == 0
        assert _get(client, q="Foreign").json()["total"] == 0
        assert _get(client, q="01799990001").json()["total"] == 0
        assert _get(client).json()["total"] == 0


class TestFiltersAndSorting:
    def test_filters_combine_without_losing_each_other(self, client):
        _insert(doctor=DOC_A, status="BOOKED", day=DAY, start="09:00")
        _insert(doctor=DOC_A, status="CANCELLED", day=DAY, start="09:30")
        _insert(doctor=DOC_B, status="BOOKED", day=DAY, start="10:00")
        _insert(doctor=DOC_A, status="BOOKED", day="2031-06-01", start="09:00")

        assert _get(client, doctor_id=DOC_A).json()["total"] == 3
        assert _get(client, status="CANCELLED").json()["total"] == 1
        both = _get(client, doctor_id=DOC_A, status="BOOKED").json()
        assert both["total"] == 2
        windowed = _get(client, doctor_id=DOC_A, status="BOOKED",
                        date_from=DAY, date_to=DAY).json()
        assert windowed["total"] == 1
        assert windowed["items"][0]["start_time"] == "09:00"

    def test_status_filter_uses_the_lifecycle_value_verbatim(self, client):
        _insert(status="CHECKED_IN")
        # A label ("Checked In") is a presentation concern, not a filter value.
        assert _get(client, status="CHECKED_IN").json()["total"] == 1
        # AMSDP-CALENDAR-FILTER-01 (diagnosis F-6): an unknown status is now a
        # 422, not an empty page.  Answering "0 results" for a value the UI cannot
        # produce hides the bug behind a plausible-looking empty table, and it let
        # the grid and the list disagree about what "no matches" meant.
        assert _get(client, status="Checked In").status_code == 422
        assert _get(client, status="checked_in").status_code == 422
        assert _get(client, status="").status_code == 200

    def test_default_order_is_newest_first_then_chronological(self, client):
        _insert(day=DAY, start="10:00")
        _insert(day=DAY2, start="09:00")
        _insert(day=DAY, start="09:00")
        items = _get(client).json()["items"]
        assert [(a["appointment_date"], a["start_time"]) for a in items] == [
            (DAY2, "09:00"), (DAY, "09:00"), (DAY, "10:00")]

    def test_sort_by_patient_supports_both_orders(self, client):
        _insert(patient=PAT_A, start="09:00")
        _insert(patient=PAT_B, start="09:30")
        asc = [a["patient_name"] for a in
               _get(client, sort="patient", order="asc").json()["items"]]
        desc = [a["patient_name"] for a in
                _get(client, sort="patient", order="desc").json()["items"]]
        assert asc == ["Momena Begum", "Sultana Akter"]
        assert desc == ["Sultana Akter", "Momena Begum"]

    def test_sort_by_doctor_branch_and_status_are_supported(self, client):
        _insert(doctor=DOC_B, status="BOOKED", start="09:00")
        _insert(doctor=DOC_A, status="CANCELLED", start="09:30")
        doctors = [a["doctor_name"] for a in
                   _get(client, sort="doctor", order="asc").json()["items"]]
        assert doctors == ["Dr. Abdul Karim", "Dr. Fatima Begum"]
        statuses = [a["status"] for a in
                    _get(client, sort="status", order="asc").json()["items"]]
        assert statuses == ["BOOKED", "CANCELLED"]
        assert _get(client, sort="branch").status_code == 200

    def test_unknown_sort_or_order_is_rejected(self, client):
        # A typo must fail loudly instead of returning a differently ordered page
        # while the UI claims the requested sort.
        assert _get(client, sort="mobile").status_code == 422
        assert _get(client, sort="patient", order="sideways").status_code == 422

    def test_malformed_dates_are_rejected_not_ignored(self, client):
        assert _get(client, date_from="12-05-2031").status_code == 422
        assert _get(client, date_to="2031-13-01").status_code == 422


class TestAuthorization:
    def test_route_requires_an_authenticated_caller(self, client):
        assert client.get("/api/v1/appointments/list").status_code == 401

    def test_branch_scoped_token_only_sees_its_own_branch(self, client):
        _insert(branch=BR)
        _insert(branch=BR2, start="10:00")
        body = _get(client, user=RECP).json()
        assert body["total"] == 1
        assert body["items"][0]["branch_id"] == BR

        # The other branch's receptionist sees exactly the other appointment.
        other = _get(client, user=RECP2).json()
        assert other["total"] == 1
        assert other["items"][0]["branch_id"] == BR2

    def test_asking_for_a_foreign_branch_is_a_non_disclosing_404(self, client):
        _insert(branch=BR2)
        r = _get(client, user=RECP, branch_id=BR2)
        assert r.status_code == 404
        # Its own branch is fine to name explicitly.
        assert _get(client, user=RECP, branch_id=BR).status_code == 200

    def test_org_admin_sees_all_branches_and_may_narrow(self, client):
        _insert(branch=BR)
        _insert(branch=BR2, start="10:00")
        assert _get(client, user=ORGADM).json()["total"] == 2
        narrowed = _get(client, user=ORGADM, branch_id=BR2).json()
        assert narrowed["total"] == 1
        assert narrowed["items"][0]["branch_id"] == BR2

    def test_another_tenant_sees_none_of_our_rows(self, client):
        _insert()
        assert _get(client, user=OTHER_RECP).json()["total"] == 0

    def test_a_denied_cross_branch_probe_is_written_to_the_audit_trail(self, client):
        """`.clinerules` §3 — denials are recorded, never silently swallowed."""
        import time

        from common.models import AuditEvent

        _insert(branch=BR2)
        assert _get(client, user=RECP, branch_id=BR2).status_code == 404

        # The denial row is written off the response path (Q-2), so poll briefly
        # instead of assuming the worker thread has already committed.
        deadline = time.time() + 5
        found = False
        while time.time() < deadline and not found:
            with db_session() as s:
                found = s.query(AuditEvent).filter(
                    AuditEvent.organization_id == ORG,
                    AuditEvent.target_type == "http_request",
                    AuditEvent.target_id == "GET /api/v1/appointments/list",
                ).count() > 0
            if not found:
                time.sleep(0.1)
        assert found, "the cross-branch 404 left no audit row"

