"""MP-18 — schedule-edit audit: the decision layer and a source-level guard.

MP-18's acceptance criterion is *"any schedule write produces an audit row with
before/after; no silent schedule mutation remains"*.  The behavioural proof lives
in ``scheduling/tests/test_schedule_audit.py``, which reads ``audit_events`` back
from PostgreSQL and asserts the values (10 tests: schedule created, capacity,
templates, status, generic update; session create, capacity, retire).  That module
**cannot run on this host** — there is no database — so it is recorded as unrun,
not as passing.

What *is* executable here, and is what this module covers:

* the projection-diff helper added for the gap MP-18 found — a session write
  rebuilds ``schedules.slot_templates``, and that schedule mutation had no
  ``schedule.*`` audit row until it was routed through
  :func:`scheduling.sessions.audit_template_projection`;
* a source-level guard that fails if a future write route is added to the
  scheduling service without an audit event, or if anything calls
  ``sync_slot_templates`` outside the audited helper.

The guard is deliberately static.  It cannot prove that an event carries the
right *values* — that is the PostgreSQL tests' job — but it does prove the thing
that regresses silently: a new endpoint that writes and forgets to audit.
"""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from scheduling.sessions import audit_template_projection, windows_map

SCHEDULING = Path(__file__).resolve().parents[1] / "scheduling"
WRITE_METHODS = ("post", "put", "patch", "delete")
#: Calls that satisfy "this route audits".
AUDIT_CALLS = ("record_audit", "audit_template_projection")


# ---------------------------------------------------------------------------
# The projection diff (pure)
# ---------------------------------------------------------------------------

def test_windows_map_keeps_the_canonical_key_and_capacity():
    assert windows_map([{"day_of_week": 0, "start_time": "09:00",
                         "end_time": "10:00", "max_patients": 2}]) == {
        "0 09:00-10:00": 2}


def test_windows_map_drops_a_time_that_is_not_hhmm():
    """``9:00`` is not a stored form: readers skip it, so this map must too."""
    assert windows_map([{"day_of_week": 0, "start_time": "9:00",
                         "end_time": "10:00", "max_patients": 2}]) == {}


def test_windows_map_defaults_capacity_to_one():
    assert windows_map([{"day_of_week": 3, "start_time": "14:00",
                         "end_time": "15:00"}]) == {"3 14:00-15:00": 1}


def test_windows_map_skips_templates_no_reader_could_use():
    """An unusable window is not a window: end before start, or not a dict."""
    assert windows_map([
        {"day_of_week": 0, "start_time": "10:00", "end_time": "09:00"},
        {"day_of_week": 0, "start_time": "noon", "end_time": "13:00"},
        "not a template",
        {"day_of_week": 1, "start_time": "09:00", "end_time": "09:30"},
    ]) == {"1 09:00-09:30": 1}


@pytest.mark.parametrize("empty", [None, [], ()])
def test_windows_map_of_nothing_is_empty(empty):
    assert windows_map(empty) == {}


# ---------------------------------------------------------------------------
# The audited projection write
# ---------------------------------------------------------------------------

class _Schedule:
    def __init__(self, templates, schedule_id="sch-1"):
        self.templates = list(templates)
        self.id = schedule_id
        self.organization_id = "org-1"
        self.branch_id = "br-1"

    @property
    def slot_templates(self):
        return self.templates

    @slot_templates.setter
    def slot_templates(self, value):
        self.templates = list(value)


def _session_row(day=0, start="09:00", end="10:00", capacity=1, sid="sess-1"):
    return SimpleNamespace(id=sid, day_of_week=day, start_time=start,
                           end_time=end, slot_duration_minutes=15,
                           max_patients=capacity, room_id=None)


class _Session:
    """Answers ``query(ScheduleSession).filter(...).all()`` with *rows*."""

    def __init__(self, rows):
        self.rows = rows

    def query(self, model):
        rows = self.rows

        class _Query:
            def filter(self, *criteria):
                return self

            def all(self):
                return rows

        return _Query()


@pytest.fixture
def recorded(monkeypatch):
    """Capture the audit calls the helper makes, without touching a database."""
    calls = []

    def _fake(session, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("scheduling.sessions.record_audit", _fake)
    return calls



def test_a_changed_projection_is_audited_against_the_schedule(recorded):
    """The MP-18 gap: the session write moved the schedule, so the schedule is named."""
    schedule = _Schedule([{"day_of_week": 0, "start_time": "09:00",
                           "end_time": "10:00", "max_patients": 1}])
    auth = SimpleNamespace(user_id="user-1", role="branch_admin")
    rows = [_session_row(day=0, start="09:00", end="10:00", capacity=3)]

    audit_template_projection(_Session(rows), schedule, auth, "session created")

    assert len(recorded) == 1
    event = recorded[0]
    assert event["action"] == "schedule.templates_changed"
    assert event["target_type"] == "schedule"
    assert event["target_id"] == "sch-1"
    assert event["org_id"] == "org-1"
    assert event["branch_id"] == "br-1"
    assert event["actor_id"] == "user-1"
    assert event["before"] == {"windows": {"0 09:00-10:00": 1}}
    assert event["after"] == {"windows": {"0 09:00-10:00": 3}}
    assert event["reason"] == "session created"


def test_an_unchanged_projection_writes_no_schedule_event(recorded):
    """A session edit that does not move the projection must not claim it did."""
    schedule = _Schedule([{"day_of_week": 0, "start_time": "09:00",
                           "end_time": "10:00", "slot_duration_minutes": 15,
                           "max_patients": 1, "session_id": "sess-1",
                           "room_id": None}])
    auth = SimpleNamespace(user_id="user-1", role="branch_admin")
    rows = [_session_row(day=0, start="09:00", end="10:00", capacity=1)]

    audit_template_projection(_Session(rows), schedule, auth, "session updated")

    assert recorded == []


def test_retiring_the_last_session_reports_the_window_disappearing(recorded):
    # The window belongs to the session (`session_id` is what marks a projection
    # entry as session-derived), so retiring the session removes it.
    schedule = _Schedule([{"day_of_week": 0, "start_time": "09:00",
                           "end_time": "10:00", "max_patients": 1,
                           "session_id": "sess-1", "room_id": None}])
    auth = SimpleNamespace(user_id="user-1", role="branch_admin")

    audit_template_projection(_Session([]), schedule, auth, "session retired")

    assert len(recorded) == 1
    assert recorded[0]["before"] == {"windows": {"0 09:00-10:00": 1}}
    assert recorded[0]["after"] == {"windows": {}}


def test_a_declared_window_survives_the_first_session_write(recorded):
    """D-1: the projection is a merge, not a rebuild from sessions.

    ``POST /api/v1/schedules`` declares a doctor's hours with no session yet, so a
    blind rebuild deleted the clinic the first time a session was added — the
    calendar and ``available-slots`` then published fewer hours than the schedule
    stated.  A declared entry carries no ``session_id`` and must survive; a second
    identical projection is not a change and must not be audited again.
    """
    schedule = _Schedule([{"day_of_week": 0, "start_time": "09:00",
                           "end_time": "10:00", "max_patients": 1}])
    auth = SimpleNamespace(user_id="user-1", role="branch_admin")
    rows = [_session_row(day=0, start="11:00", end="12:00", capacity=1)]

    audit_template_projection(_Session(rows), schedule, auth, "session created")

    assert len(recorded) == 1
    assert recorded[0]["after"] == {"windows": {"0 09:00-10:00": 1,
                                               "0 11:00-12:00": 1}}
    recorded.clear()
    audit_template_projection(_Session(rows), schedule, auth, "session updated")
    assert recorded == [], "an identical projection must not be audited twice"


def test_a_declared_window_is_refused_when_the_session_covers_it(recorded):
    """The session's capacity wins; the declared duplicate is dropped, once."""
    schedule = _Schedule([{"day_of_week": 0, "start_time": "09:00",
                           "end_time": "10:00", "max_patients": 1}])
    auth = SimpleNamespace(user_id="user-1", role="branch_admin")
    rows = [_session_row(day=0, start="09:00", end="10:00", capacity=4)]

    audit_template_projection(_Session(rows), schedule, auth, "session created")

    assert len(recorded) == 1
    assert recorded[0]["after"] == {"windows": {"0 09:00-10:00": 4}}
    assert len(schedule.slot_templates) == 1, "the window is published once"



# ---------------------------------------------------------------------------
# The source-level guard: no write route without an audit event
# ---------------------------------------------------------------------------

def _write_route_functions(path: Path):
    """Every function in *path* decorated as a POST/PUT/PATCH/DELETE route."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr in WRITE_METHODS):
                yield node
                break


def _calls(function):
    """``(name, call)`` for each plain-name call inside *function*."""
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            yield node.func.id, node


def _scheduling_sources():
    sources = sorted(SCHEDULING.glob("*.py"))
    assert sources, "the scheduling package must be where this test looks"
    return sources


def test_every_write_route_in_the_scheduling_service_audits_with_after():
    checked, missing = [], []
    for path in _scheduling_sources():
        for function in _write_route_functions(path):
            checked.append(f"{path.name}::{function.name}")
            audits = [call for name, call in _calls(function)
                      if name in AUDIT_CALLS]
            if not audits:
                missing.append(f"{path.name}::{function.name} writes with no audit")
                continue
            # A route that audits through the helper is covered by the helper's
            # own guard below; a direct record_audit must carry the after state.
            direct = [call for name, call in _calls(function)
                      if name == "record_audit"]
            if direct and not any(kw.arg == "after"
                                  for call in direct for kw in call.keywords):
                missing.append(
                    f"{path.name}::{function.name} audits without an 'after'")
    assert checked, "no write routes found — the guard would be vacuous"
    assert not missing, "silent schedule mutations: " + "; ".join(missing)


def test_the_projection_helper_is_the_only_caller_of_sync_slot_templates():
    """Anything else calling it would mutate the schedule without an audit row."""
    offenders = []
    for path in _scheduling_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in [n for n in ast.walk(tree)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for name, _call in _calls(function):
                if (name == "sync_slot_templates"
                        and function.name != "audit_template_projection"):
                    offenders.append(f"{path.name}::{function.name}")
    assert offenders == [], (
        "sync_slot_templates changes schedules.slot_templates; call "
        "audit_template_projection instead: " + ", ".join(offenders))


def test_the_projection_helper_itself_records_before_and_after():
    tree = ast.parse((SCHEDULING / "sessions.py").read_text(encoding="utf-8"))
    helper = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "audit_template_projection")
    keywords = {kw.arg for _name, call in _calls(helper) for kw in call.keywords}
    assert {"before", "after", "action", "target_id"} <= keywords
