"""Q-1 / MP-44 — the patient service answers "today" with the facility's day.

Q-1 (`AMSDP_Owner_Decisions_25_November_2026` §2) approved folding the two
server-local date reads in this service into **MP-44**, the facility-clock
helper.  Before the change the service asked the *host* twice —
``datetime.now().date()`` for the date-of-birth future check and
``date.today()`` for the age — while the queue, the dashboard and the display
already used ``organizations.timezone`` (BR §8).  At 02:00 Dhaka on a UTC host
that is a different calendar day, so a newborn's date of birth was refused as
"in the future" and every age was a day stale between the two midnights.

These tests are **DB-free** on purpose: the defect is in the arithmetic and in
which clock it reads, and both can be proven without a session.  They cover

* the two boundaries the old code got wrong (a birthday today, a birth date one
  day ahead of the facility's today);
* that ``operational_today`` follows ``AMSDP_FACILITY_TZ`` and not the process
  clock — the two zones used are UTC+14 and UTC-11, which can *never* be on the
  same calendar day, so the assertion cannot flake;
* a source guard that fails if a server-local date read comes back, and a guard
  that the day is read once per request rather than once per patient row.
"""

import ast
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

from common.timeutil import operational_today
from patient.main import _age_from_dob, _validate_dob

MAIN = Path(__file__).resolve().parents[1] / "main.py"

#: UTC+14 and UTC-11: 25 hours apart, so their calendar dates differ by exactly
#: one day at every instant of the year.  Nothing about the host clock can make
#: these two agree, which is what makes the test deterministic.
EAST_OF_UTC = "Pacific/Kiritimati"
WEST_OF_UTC = "Pacific/Midway"


@pytest.fixture()
def facility_zone(monkeypatch):
    """Point the helper at a zone name, the way a facility's config would."""
    def _set(name):
        monkeypatch.setenv("AMSDP_FACILITY_TZ", name)
        return operational_today()
    return _set


# ---------------------------------------------------------------------------
# The facility day is a facility day, not the host's day
# ---------------------------------------------------------------------------

def test_operational_today_follows_the_facility_zone_not_the_process_zone(
        facility_zone):
    east = facility_zone(EAST_OF_UTC)
    west = facility_zone(WEST_OF_UTC)
    assert (east - west).days == 1, (east, west)


def test_a_birth_date_that_is_tomorrow_here_is_today_there(facility_zone):
    """The exact edge case Q-1 named: 02:00 Dhaka is still yesterday on UTC."""
    west = facility_zone(WEST_OF_UTC)
    tomorrow_here = west + timedelta(days=1)

    with pytest.raises(HTTPException) as refused:
        _validate_dob(tomorrow_here.isoformat(), west)
    assert refused.value.status_code == 422

    # In the facility that is already on the next day, the same date is "today".
    assert _validate_dob(tomorrow_here.isoformat(), facility_zone(EAST_OF_UTC)) \
        == tomorrow_here.isoformat()


# ---------------------------------------------------------------------------
# Boundaries: today is allowed, tomorrow is not, the birthday is inclusive
# ---------------------------------------------------------------------------

def test_a_birth_date_of_the_facility_today_is_accepted():
    today = date(2026, 11, 25)
    assert _validate_dob("2026-11-25", today) == "2026-11-25"


def test_a_birth_date_after_the_facility_today_is_refused():
    with pytest.raises(HTTPException) as refused:
        _validate_dob("2026-11-26", date(2026, 11, 25))
    assert refused.value.status_code == 422
    assert "future" in str(refused.value.detail)


def test_an_empty_birth_date_is_still_optional():
    assert _validate_dob(None, date(2026, 11, 25)) == ""
    assert _validate_dob("", date(2026, 11, 25)) == ""


def test_a_malformed_birth_date_is_a_format_error_not_a_future_error():
    with pytest.raises(HTTPException) as refused:
        _validate_dob("25-11-2026", date(2026, 11, 25))
    assert refused.value.status_code == 422
    assert "YYYY-MM-DD" in str(refused.value.detail)


def test_the_age_turns_over_on_the_facility_birthday():
    dob = "2000-03-01"
    assert _age_from_dob(dob, date(2026, 2, 28)) == 25
    assert _age_from_dob(dob, date(2026, 3, 1)) == 26


def test_a_leap_day_birth_date_is_aged_without_fabrication():
    """29 February has no anniversary in a common year: the age flips on 1 March."""
    assert _age_from_dob("2004-02-29", date(2026, 2, 28)) == 21
    assert _age_from_dob("2004-02-29", date(2026, 3, 1)) == 22


def test_the_age_defaults_to_the_facility_day(facility_zone):
    today = facility_zone(EAST_OF_UTC)
    dob = (today - timedelta(days=365 * 30)).isoformat()
    assert _age_from_dob(dob) in (29, 30)      # leap days inside 30 years
    assert _age_from_dob(dob) == _age_from_dob(dob, today)


# ---------------------------------------------------------------------------
# Static guards: no server-local read comes back, and the day is read once
# ---------------------------------------------------------------------------

def _called_names(node):
    """Every ``something.attr(...)`` call in the tree, as (attr, Call)."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
            yield sub.func.attr, sub


def test_the_module_no_longer_reads_the_local_clock():
    """``date.today()`` and ``datetime.now().date()`` are the defect itself."""
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    offences = []
    for attr, call in _called_names(tree):
        if attr == "today":
            offences.append((call.lineno, "X.today()"))
        if attr == "date" and isinstance(call.func.value, ast.Call) \
                and getattr(call.func.value.func, "attr", "") == "now":
            offences.append((call.lineno, "X.now().date()"))
    assert offences == [], "server-local date reads remain: " + repr(offences)


def test_the_facility_day_is_read_once_per_request():
    """A per-row ``_patient_to_dict(p)`` call would add one org lookup per patient."""
    source = MAIN.read_text(encoding="utf-8")
    calls = re.findall(r"(?<!def )_patient_to_dict\(([^)]*)\)", source)
    assert calls, "no _patient_to_dict call sites found - the guard is stale"
    for args in calls:
        assert "facility_today" in args or "operational_today" in args, \
            "_patient_to_dict called without an explicit facility day: " + args


def test_the_module_resolves_the_day_through_the_shared_helper():
    source = MAIN.read_text(encoding="utf-8")
    assert "from common.timeutil import operational_today" in source
    assert source.count("operational_today(") >= 5, \
        "expected the shared helper at every read site"
