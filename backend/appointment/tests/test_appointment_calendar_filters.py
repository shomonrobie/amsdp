"""Calendar search/filter/scope behaviour — AMSDP-CALENDAR-FILTER-01.

These tests exist because the previous suite proved the wrong thing: the frontend
tests passed while the defect was live, and the backend list tests passed while the
**grid** applied neither the search nor the branch scope (diagnosis report
``docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md`` F-3, F-4, O-AC).
So every case here drives the real routes against PostgreSQL and asserts on the
records that come back, not on the shape of the request the UI builds.

The three reads must agree — they are three presentations of one question:

* ``GET /api/v1/appointments``          Week/Day grid
* ``GET /api/v1/appointments/list``     paged List view
* ``GET /api/v1/appointments/matches``  the date index for out-of-window matches

Coverage map (owner decisions D-1 branch scope, D-2 search spans all dates):

* grid: search by name / mobile digits / token / id; status, doctor, window;
  unknown status is 422, never an empty page;
* scope: receptionist confined to the token's branch, a foreign ``branch_id`` is a
  non-disclosing 404, a branch-scoped token without a branch is 403, org_admin and
  super_admin see the organization and may narrow, another tenant is invisible;
* match index: counts and dates across every authorized date, no patient data,
  ``near`` ordering, cap + ``truncated``, same filters and scope as the grid;
* agreement: the same query returns the same ids from the grid and the list.

Fixtures use their own organization and purge only their own business rows, so the
module can run against the shared development database.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_patient, ensure_user,
                               headers, load_app, purge_org)
from common.models import Appointment

ORG = "cal-flt-org"
BR = "cal-flt-br"
BR2 = "cal-flt-br2"
OTHER_ORG = "cal-flt-other-org"
OTHER_BR = "cal-flt-other-br"
DOC_A = "cal-flt-doc-a"
DOC_B = "cal-flt-doc-b"
PAT_A = "cal-flt-pat-a"
PAT_B = "cal-flt-pat-b"
PAT_BN = "cal-flt-pat-bn"
PAT_FOREIGN = "cal-flt-pat-foreign"

RECP = "cal_flt_recp"          # receptionist, BR
RECP_BR2 = "cal_flt_recp2"     # receptionist, BR2
ORGADM = "cal_flt_orgadm"      # org_admin, no branch
BRADM = "cal_flt_bradm"        # branch_admin, BR
DOCUSER = "cal_flt_doc"        # doctor, BR
ASST = "cal_flt_asst"          # assistant, BR
SUPER = "cal_flt_super"        # super_admin
NOBRANCH = "cal_flt_nobranch"  # receptionist with no branch on the token
OTHER_RECP = "cal_flt_other_recp"

DAY = "2032-03-10"
DAY2 = "2032-03-11"
FAR = "2032-06-20"


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
    ensure_doctor(DOC_A, ORG, name="Dr. Rafiq Islam", mobile="01700003001")
    ensure_doctor(DOC_B, ORG, name="Dr. Nusrat Jahan", mobile="01700003002")
    ensure_patient(PAT_A, ORG, name="Karim Uddin", mobile="01712220001")
    ensure_patient(PAT_B, ORG, name="Shila Rani", mobile="01712220002")
    ensure_patient(PAT_BN, ORG, name="নাসরিন আক্তার", mobile="01712220003")
    ensure_patient(PAT_FOREIGN, OTHER_ORG, name="Foreign Patient",
                   mobile="01799990001")
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(RECP_BR2, "receptionist", ORG, BR2)
    ensure_user(ORGADM, "org_admin", ORG, None)
    ensure_user(BRADM, "branch_admin", ORG, BR)
    ensure_user(DOCUSER, "doctor", ORG, BR)
    ensure_user(ASST, "assistant", ORG, BR)
    ensure_user(SUPER, "super_admin", ORG, None)
    ensure_user(NOBRANCH, "receptionist", ORG, None)
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


def _insert_many(specs):
    """Insert several appointments in one transaction; returns their ids.

    ``spec`` keys: ``day`` (required), ``token`` (required, unique per day) and
    optional ``org``/``branch``/``patient``/``doctor``/``start``/``status``.
    """
    ids = []
    with db_session() as s:
        for spec in specs:
            status = spec.get("status", "BOOKED")
            appt = Appointment(
                organization_id=spec.get("org", ORG),
                branch_id=spec.get("branch", BR),
                patient_id=spec.get("patient", PAT_A),
                doctor_id=spec.get("doctor", DOC_A),
                appointment_date=date.fromisoformat(spec["day"]),
                start_time=spec.get("start", "09:00"),
                status=status,
                token_number=spec["token"],
                status_history=[{"status": status}],
            )
            s.add(appt)
            ids.append(appt.id)
        s.commit()
    return ids


def _grid(client, user=RECP, **params):
    """The Week/Day read."""
    return client.get("/api/v1/appointments", headers=headers(user),
                      params=params)


def _list(client, user=RECP, **params):
    """The paged List read."""
    return client.get("/api/v1/appointments/list", headers=headers(user),
                      params=params)


def _matches(client, user=RECP, **params):
    """The match date index."""
    return client.get("/api/v1/appointments/matches", headers=headers(user),
                      params=params)


def _list_ids(response):
    """Record ids of a paged ``/appointments/list`` response."""
    return sorted(item["id"] for item in response.json()["items"])


def _ids(response):
    return sorted(item["id"] for item in response.json())



class TestGridSearchAndFilters:
    """``GET /api/v1/appointments`` answers the toolbar, not just the date.

    Before AMSDP-CALENDAR-FILTER-01 this route took no ``q`` at all: the search box
    changed the List view and left the Week/Day grid showing the whole week
    (diagnosis F-3).  Each test below would have failed against that code.
    """

    def test_search_by_patient_name_narrows_the_visible_week(self, client):
        karim = _insert(patient=PAT_A, start="09:00")
        _insert(patient=PAT_B, start="09:30")
        assert len(_grid(client, date_from=DAY, date_to=DAY).json()) == 2
        body = _grid(client, q="Karim", date_from=DAY, date_to=DAY).json()
        assert [item["id"] for item in body] == [karim]
        assert body[0]["patient_name"] == "Karim Uddin"

    def test_search_matches_a_bangla_name(self, client):
        bn = _insert(patient=PAT_BN, start="10:00")
        _insert(patient=PAT_A, start="10:30")
        assert _ids(_grid(client, q="নাসরিন", date_from=DAY, date_to=DAY)) == [bn]
        # A substring in the middle of the name matches too.
        assert _ids(_grid(client, q="আক্তার", date_from=DAY, date_to=DAY)) == [bn]

    def test_search_by_mobile_ignores_the_punctuation(self, client):
        shila = _insert(patient=PAT_B, start="11:00")
        _insert(patient=PAT_A, start="11:30")
        assert _ids(_grid(client, q="017-1222-0002", date_from=DAY,
                          date_to=DAY)) == [shila]
        # A shorter digit run is a substring, so a receptionist can type the tail.
        assert _ids(_grid(client, q="0002", date_from=DAY, date_to=DAY)) == [shila]

    def test_search_matches_the_token_and_the_appointment_id(self, client):
        row = _insert(start="12:00", token="A-42")
        _insert(start="12:30", token="B-43")
        assert _ids(_grid(client, q="A-42", date_from=DAY, date_to=DAY)) == [row]
        assert _ids(_grid(client, q=row, date_from=DAY, date_to=DAY)) == [row]

    def test_status_filter_applies_to_the_grid(self, client):
        _insert(status="BOOKED", start="09:00")
        cancelled = _insert(status="CANCELLED", start="09:30")
        assert _ids(_grid(client, status="CANCELLED", date_from=DAY,
                          date_to=DAY)) == [cancelled]
        assert len(_grid(client, date_from=DAY, date_to=DAY).json()) == 2

    def test_doctor_filter_applies_to_the_grid(self, client):
        mine = _insert(doctor=DOC_A, start="09:00")
        _insert(doctor=DOC_B, start="09:30")
        assert _ids(_grid(client, doctor_id=DOC_A, date_from=DAY,
                          date_to=DAY)) == [mine]

    def test_unknown_status_is_rejected_not_treated_as_no_matches(self, client):
        _insert(status="CHECKED_IN")
        # A label or a lower-case value is not a lifecycle value (diagnosis O-AB).
        assert _grid(client, status="Checked In").status_code == 422
        assert _grid(client, status="checked_in").status_code == 422
        assert _grid(client, status="CHECKED_IN").status_code == 200

    def test_a_malformed_date_is_rejected_not_ignored(self, client):
        _insert()
        # Silently ignoring ``date`` used to return the whole week for a typo.
        assert _grid(client, date="10-03-2032").status_code == 422
        assert _grid(client, date_from="nope").status_code == 422

    def test_filters_combine_without_replacing_each_other(self, client):
        want = _insert(patient=PAT_A, doctor=DOC_A, status="BOOKED", start="09:00")
        _insert(patient=PAT_A, doctor=DOC_A, status="CANCELLED", start="09:30")
        _insert(patient=PAT_B, doctor=DOC_A, status="BOOKED", start="10:00")
        _insert(patient=PAT_A, doctor=DOC_B, status="BOOKED", start="10:30")
        _insert(patient=PAT_A, doctor=DOC_A, status="BOOKED", day=FAR)
        body = _grid(client, q="Karim", doctor_id=DOC_A, status="BOOKED",
                     date_from=DAY, date_to=DAY).json()
        assert _ids(_grid(client, q="Karim", doctor_id=DOC_A, status="BOOKED",
                          date_from=DAY, date_to=DAY)) == [want]
        assert body[0]["start_time"] == "09:00"

    def test_rows_carry_the_names_the_cards_show(self, client):
        _insert(patient=PAT_A, doctor=DOC_A)
        item = _grid(client, date_from=DAY, date_to=DAY).json()[0]
        assert item["patient_name"] == "Karim Uddin"
        assert item["patient_mobile"] == "01712220001"
        assert item["doctor_name"] == "Dr. Rafiq Islam"
        assert item["branch_name"] == BR
        # The grid payload is the appointment payload: nothing was re-invented.
        assert item["status"] == "BOOKED" and "location_label" in item


class TestBranchScopeIsTheTokensBusiness:
    """D-1: the token decides what may be read; the query may only narrow it.

    The calendar used to trust the branch picker: the grid carried no branch
    predicate at all, so a receptionist at one branch saw every branch's day
    (diagnosis F-4).  These cases pin the server-side rule from ``.clinerules`` §3 —
    the principal's branch is derived from the token, cross-branch access fails
    closed and non-disclosingly, and the UI is never the boundary.
    """

    def test_receptionist_sees_only_its_own_branch(self, client):
        mine = _insert(branch=BR, start="09:00")
        _insert(branch=BR2, start="09:00")
        _insert(org=OTHER_ORG, branch=OTHER_BR, patient=PAT_FOREIGN,
                start="09:00")
        assert _ids(_grid(client, RECP, date_from=DAY, date_to=DAY)) == [mine]
        assert _list_ids(_list(client, RECP, date_from=DAY, date_to=DAY)) == [mine]
        assert _matches(client, RECP, date_from=DAY,
                        date_to=DAY).json()["total"] == 1

    def test_receptionist_at_the_other_branch_sees_only_its_own(self, client):
        _insert(branch=BR, start="09:00")
        other = _insert(branch=BR2, start="09:00")
        assert _ids(_grid(client, RECP_BR2, date_from=DAY, date_to=DAY)) == [other]

    def test_naming_another_branch_is_a_non_disclosing_404(self, client):
        _insert(branch=BR2, start="09:00")
        for call in (_grid, _list, _matches):
            response = call(client, RECP, branch_id=BR2)
            # 404, never 403: the answer must not confirm that BR2 exists or holds
            # anything (``.clinerules`` §3).
            assert response.status_code == 404, call.__name__
            assert BR2 not in response.text

    def test_guessing_a_foreign_tenant_branch_is_also_a_404(self, client):
        for call in (_grid, _list, _matches):
            assert call(client, RECP, branch_id=OTHER_BR).status_code == 404

    def test_naming_your_own_branch_narrows_nothing_away(self, client):
        mine = _insert(branch=BR, start="09:00")
        response = _grid(client, RECP, branch_id=BR, date_from=DAY, date_to=DAY)
        assert response.status_code == 200
        assert _ids(response) == [mine]

    def test_org_admin_sees_every_branch_and_may_narrow(self, client):
        _insert(branch=BR, start="09:00")
        only_br2 = _insert(branch=BR2, start="09:00")
        assert len(_grid(client, ORGADM, date_from=DAY, date_to=DAY).json()) == 2
        assert _ids(_grid(client, ORGADM, branch_id=BR2, date_from=DAY,
                          date_to=DAY)) == [only_br2]

    def test_super_admin_sees_the_organization_but_not_another_tenant(self, client):
        _insert(branch=BR, start="09:00")
        _insert(branch=BR2, start="09:00")
        _insert(org=OTHER_ORG, branch=OTHER_BR, patient=PAT_FOREIGN,
                start="09:00")
        assert len(_grid(client, SUPER, date_from=DAY, date_to=DAY).json()) == 2

    def test_branch_admin_is_confined_like_a_receptionist(self, client):
        mine = _insert(branch=BR, start="09:00")
        _insert(branch=BR2, start="09:00")
        assert _ids(_grid(client, BRADM, date_from=DAY, date_to=DAY)) == [mine]
        assert _grid(client, BRADM, branch_id=BR2).status_code == 404

    def test_a_branch_scoped_token_without_a_branch_is_refused(self, client):
        _insert(branch=BR, start="09:00")
        # It can read no appointments at all; saying so is honest, unlike
        # returning an empty week that looks like "nothing booked today".
        for call in (_grid, _list, _matches):
            assert call(client, NOBRANCH, date_from=DAY,
                        date_to=DAY).status_code == 403, call.__name__

    def test_the_reads_require_a_principal(self, client):
        for url in ("/api/v1/appointments", "/api/v1/appointments/list",
                    "/api/v1/appointments/matches"):
            assert client.get(url).status_code == 401

    def test_the_counts_never_leak_the_other_branch(self, client):
        _insert(branch=BR, start="09:00")
        _insert(branch=BR2, start="09:00")
        assert _matches(client, RECP, date_from=DAY, date_to=DAY).json()["total"] == 1
        # The organization-wide reader is the one who may see both.
        assert _matches(client, ORGADM, date_from=DAY,
                        date_to=DAY).json()["total"] == 2



class TestMatchIndexSpansAllAuthorizedDates:
    """D-2: a search reaches every authorized date, not just the visible week.

    The Week/Day grid can only hold one window, so a match three months away is
    invisible there.  Saying nothing was the defect (diagnosis F-5); loading the
    organization's history into the browser to filter it client-side would trade a
    UX bug for a data-exposure and performance bug.  The answer is a counts-only
    date index, and these cases pin both halves of that sentence: it *does* reach
    every date, and it *never* carries a record.
    """

    def test_the_index_counts_matches_on_every_date(self, client):
        _insert(day=DAY, start="09:00")
        _insert(day=DAY2, start="09:00")
        _insert(day=FAR, start="09:00")
        body = _matches(client, RECP, q="Karim").json()
        assert body["total"] == 3
        assert [entry["date"] for entry in body["dates"]] == [DAY, DAY2, FAR]
        assert [entry["count"] for entry in body["dates"]] == [1, 1, 1]
        assert body["truncated"] is False

    def test_matches_on_the_same_day_are_counted_together(self, client):
        _insert(day=DAY, start="09:00")
        _insert(day=DAY, start="09:30")
        _insert(day=FAR, start="09:00")
        body = _matches(client, RECP, q="Karim").json()
        assert body["total"] == 3
        assert body["dates"] == [{"date": DAY, "count": 2},
                                 {"date": FAR, "count": 1}]

    def test_the_index_carries_counts_and_dates_but_no_record(self, client):
        _insert(patient=PAT_A, day=FAR)
        response = _matches(client, RECP, q="Karim")
        body = response.json()
        assert set(body) == {"total", "dates", "truncated"}
        assert all(set(entry) == {"date", "count"} for entry in body["dates"])
        # Neither the patient's name nor the number travels in the index.
        assert "Karim" not in response.text
        assert "01712220001" not in response.text

    def test_near_orders_the_dates_by_distance_from_the_calendar(self, client):
        _insert(day=DAY, start="09:00")            # one day before DAY2
        _insert(day=DAY2, start="09:00")           # the day on screen
        _insert(day=FAR, start="09:00")            # months away
        body = _matches(client, RECP, q="Karim", near=DAY2).json()
        assert [entry["date"] for entry in body["dates"]] == [DAY2, DAY, FAR]

    def test_the_index_applies_the_same_filters_as_the_grid(self, client):
        cancelled = _insert(patient=PAT_A, status="CANCELLED", day=FAR)
        _insert(patient=PAT_A, status="BOOKED", day=FAR)
        _insert(patient=PAT_B, status="CANCELLED", day=FAR, doctor=DOC_B)
        body = _matches(client, RECP, q="Karim", status="CANCELLED").json()
        assert body["total"] == 1
        assert body["dates"] == [{"date": FAR, "count": 1}]
        assert _ids(_grid(client, RECP, q="Karim", status="CANCELLED",
                          date_from=FAR, date_to=FAR)) == [cancelled]
        assert _matches(client, RECP, q="Karim", doctor_id=DOC_A,
                        status="CANCELLED").json()["total"] == 1

    def test_an_unknown_status_is_rejected_here_too(self, client):
        _insert(day=FAR)
        assert _matches(client, RECP, status="Checked In").status_code == 422

    def test_the_date_list_is_capped_and_says_so(self, client):
        # MATCH_DATE_LIMIT (120) distinct dates: the total stays exact, the list
        # stops at the cap and ``truncated`` admits it, so one search can never
        # become an unbounded dump of the organization's history.
        start = date(2033, 1, 1)
        _insert_many([{"day": str(start + timedelta(days=offset)),
                       "token": f"CAP-{offset:03d}", "start": "10:00",
                       "patient": PAT_B}
                      for offset in range(121)])
        body = _matches(client, RECP, q="Shila", near=str(start)).json()
        assert body["total"] == 121
        assert len(body["dates"]) == 120
        assert body["truncated"] is True
        # The cap keeps the dates closest to the calendar, not the oldest.
        assert body["dates"][0]["date"] == str(start)



class TestTheThreeReadsAgree:
    """The grid and the list are two presentations of one predicate set (F-3).

    These are the regression tests for the *divergence*, not for one route: before
    the fix the same search could return four rows in the List view and the whole
    week in the grid, and both suites were green because each tested its own route
    against its own expectations.
    """

    def _mixed_rows(self):
        return _insert_many([
            {"day": DAY, "start": "09:00", "token": "MX-1", "patient": PAT_A},
            {"day": DAY, "start": "09:30", "token": "MX-2", "patient": PAT_B},
            {"day": DAY2, "start": "10:00", "token": "MX-3", "patient": PAT_A,
             "status": "CANCELLED"},
            {"day": DAY2, "start": "10:30", "token": "MX-4", "patient": PAT_A,
             "doctor": DOC_B},
            {"day": FAR, "start": "11:00", "token": "MX-5", "patient": PAT_A},
            {"day": FAR, "start": "11:30", "token": "MX-6", "branch": BR2},
        ])

    def test_the_same_query_returns_the_same_rows(self, client):
        self._mixed_rows()
        window = {"date_from": DAY, "date_to": FAR}
        queries = [
            {},
            {"q": "Karim"},
            {"q": "Karim", "status": "BOOKED"},
            {"q": "Karim", "doctor_id": DOC_A},
            {"q": "01712220001"},
            {"status": "CANCELLED"},
        ]
        for params in queries:
            grid_ids = _ids(_grid(client, RECP, **window, **params))
            page = _list(client, RECP, **window, limit=100, **params).json()
            assert sorted(item["id"] for item in page["items"]) == grid_ids, params
            assert page["total"] == len(grid_ids), params

    def test_the_index_total_equals_the_unpaged_list_total(self, client):
        self._mixed_rows()
        for params in ({"q": "Karim"}, {"q": "Shila"}, {"status": "BOOKED"}, {}):
            indexed = _matches(client, RECP, near=DAY, **params).json()["total"]
            listed = _list(client, RECP, limit=100, **params).json()["total"]
            assert indexed == listed, params

    def test_a_search_that_matches_nothing_is_empty_everywhere(self, client):
        self._mixed_rows()
        assert _grid(client, RECP, q="Nobody At All").json() == []
        assert _list(client, RECP, q="Nobody At All").json()["total"] == 0
        body = _matches(client, RECP, q="Nobody At All").json()
        assert body == {"total": 0, "dates": [], "truncated": False}

    def test_a_like_metacharacter_is_a_literal_not_a_wildcard(self, client):
        # A patient whose name contains "%" must not turn the search box into a
        # wildcard: ``%`` typed alone matches that name, not every patient.
        #
        # The window is stated explicitly because the grid read no longer
        # defaults to "everything" (gap-analysis F-17): a bare request is
        # answered for today ± 180 days, and these fixtures live in 2032.
        pct = ensure_patient("cal-flt-pat-pct", ORG, name="Shila 100% Rani",
                             mobile="01712220009")
        row = _insert(patient=pct, start="12:00", token="PCT-1")
        _insert(patient=PAT_A, start="12:30", token="PCT-2")
        window = {"date_from": DAY, "date_to": DAY}
        assert _ids(_grid(client, RECP, q="%", **window)) == [row]
        assert _ids(_grid(client, RECP, q="100%", **window)) == [row]
        assert len(_grid(client, RECP, **window).json()) == 2

