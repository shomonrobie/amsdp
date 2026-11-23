"""QUE-006 / W2 — pure tests for the server-generated queue call event id.

These tests need no database, no FastAPI and no fixtures: ``queuing.events`` is
a pure reading of ``QueueEntry.status_history``. That matters here because the
W2 verification host has no PostgreSQL and no ``pytest``; the same functions are
also executed by ``scripts/que-006-w2-reliability/check_call_event_identity.py``,
which runs every ``test_*`` in this module through a plain interpreter.

Do not weaken these assertions to make a database test pass: the database tests
in ``test_queue.py`` prove the *route* appends a history record, while these
prove the *identity derived from that record* is stable, unique and replay-safe.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from queuing.events import (  # noqa: E402
    MAX_EVENT_ID_LENGTH,
    call_events,
    current_call_event,
    event_id_for_index,
    is_current_call_event,
)

ENTRY = "8f14e45f-ceea-467a-9f0e-1c2b3a4d5e6f"


def _call(at="2026-11-21T09:00:00+00:00", frm="waiting"):
    return {"from": frm, "to": "called", "action": "call",
            "actor": "u-1", "reason": "", "at": at}


def _history_with_two_calls():
    return [
        _call("2026-11-21T09:00:00+00:00"),
        {"from": "called", "to": "skipped", "action": "mark_missed_turn",
         "actor": "u-2", "reason": "", "at": "2026-11-21T09:10:00+00:00"},
        _call("2026-11-21T09:12:00+00:00", frm="skipped"),
    ]


def test_no_history_has_no_event():
    assert call_events(None) == []
    assert call_events([]) == []
    assert current_call_event(ENTRY, None) is None


def test_first_call_is_index_zero():
    event = current_call_event(ENTRY, [_call()])
    assert event is not None
    assert event["call_event_id"] == "qce:" + ENTRY + ":0"
    assert event["call_event_at"] == "2026-11-21T09:00:00+00:00"
    assert event["call_count"] == 1


def test_recall_gets_a_new_event_id():
    """A legitimate recall must not reuse the first call's identity."""
    first = current_call_event(ENTRY, [_call()])
    second = current_call_event(ENTRY, _history_with_two_calls())
    assert second["call_event_id"] != first["call_event_id"]
    assert second["call_event_id"] == "qce:" + ENTRY + ":2"
    assert second["call_count"] == 2
    assert second["call_event_at"] == "2026-11-21T09:12:00+00:00"


def test_read_is_repeatable_for_same_history():
    """A refresh, a retry or a delayed response must not change the identity."""
    history = [_call(), {"from": "called", "to": "cancelled", "action": "cancel",
                         "actor": "u-1", "reason": "left", "at": "2026-11-21T09:02:00+00:00"}]
    ids = {current_call_event(ENTRY, list(history))["call_event_id"] for _ in range(5)}
    assert ids == {"qce:" + ENTRY + ":0"}


def test_non_call_records_are_ignored():
    history = [
        {"from": "waiting", "to": "in_consultation", "action": "start_consultation",
         "actor": "u-1", "reason": "", "at": "2026-11-21T09:00:00+00:00"},
        {"from": "waiting", "to": "cancelled", "action": "cancel",
         "actor": "u-1", "reason": "left", "at": "2026-11-21T09:01:00+00:00"},
        {"from": "waiting", "to": "no_show", "action": "mark_no_show",
         "actor": "u-1", "reason": "", "at": "2026-11-21T09:02:00+00:00"},
    ]
    assert call_events(history) == []
    assert current_call_event(ENTRY, history) is None


def test_call_that_did_not_end_in_called_is_not_an_event():
    """Defensive: only a transition *into* `called` is a call event."""
    history = [{"from": "waiting", "to": "skipped", "action": "call",
                "actor": "u-1", "reason": "", "at": "2026-11-21T09:00:00+00:00"}]
    assert current_call_event(ENTRY, history) is None



def test_malformed_history_is_tolerated():
    history = [
        None,
        "not-a-record",
        42,
        {},
        {"action": "call"},
        {"action": "call", "to": "called"},
        {"action": "call", "to": "called", "at": 1234},
    ]
    events = call_events(history)
    assert [e["index"] for e in events] == [5, 6]
    assert [e["at"] for e in events] == ["", ""]
    event = current_call_event(ENTRY, history)
    assert event["call_event_id"] == "qce:" + ENTRY + ":6"


def test_tuple_history_is_accepted():
    assert current_call_event(ENTRY, (_call(),))["call_event_id"] == "qce:" + ENTRY + ":0"


def test_missing_entry_id_yields_no_event():
    assert current_call_event("", [_call()]) is None
    assert current_call_event(None, [_call()]) is None
    assert current_call_event("   ", [_call()]) is None


def test_event_id_is_short_enough_for_the_wire():
    history = [_call()] * 400
    event = current_call_event(ENTRY, history)
    assert len(event["call_event_id"]) <= MAX_EVENT_ID_LENGTH
    assert event["call_event_id"].endswith(":399")


def test_event_id_helper_matches_derivation():
    derived = current_call_event(ENTRY, [_call(), _call(), _call(), _call()])
    assert event_id_for_index(ENTRY, 3) == derived["call_event_id"]


def test_is_current_event_rejects_stale_and_invented_ids():
    history = _history_with_two_calls()
    assert is_current_call_event(ENTRY, history, "qce:" + ENTRY + ":2") is True
    assert is_current_call_event(ENTRY, history, "qce:" + ENTRY + ":0") is False
    assert is_current_call_event(ENTRY, history, "qce:" + ENTRY + ":9") is False
    assert is_current_call_event(ENTRY, history, "recall-1") is False
    assert is_current_call_event(ENTRY, history, "") is False
    assert is_current_call_event(ENTRY, history, None) is False


def test_ids_are_distinct_across_entries():
    """Two entries called at the same instant must not collide."""
    other = "11111111-2222-3333-4444-555555555555"
    a = current_call_event(ENTRY, [_call()])
    b = current_call_event(other, [_call()])
    assert a["call_event_id"] != b["call_event_id"]
