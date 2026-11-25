"""QUE-006 / W2 — server-generated identity for a queue ``call`` event.

Why this exists
---------------
The queue announcement is played by a browser after it observes a
``waiting -> called`` transition. The browser used to invent that identity
itself (``entry:<id>:call:0``), so two issues were unavoidable:

* a recall of the same entry produced the *same* key, and only a 5 second
  window in the client told the two apart;
* two open terminals shared no identity at all, so both announced.

This module derives a stable identity from data the server already persists:
``queue_entries.status_history``. The ``call`` route appends exactly one
``{"action": "call", "to": "called", ...}`` record per successful transition,
inside the same transaction as the status change, with a server timestamp
(``backend/queuing/main.py`` -> ``queue_action``). The append position is a
monotonic, server-generated counter that survives refreshes, restarts and
duplicate responses.

Therefore:

* a successful call gets ``qce:<entry id>:<history index>``;
* a recall is an explicit action of its own (``recall``, ``called -> called``,
  MP-08) and appends its own record -> a different index -> a new id;
* a repeated HTTP request cannot create a second record, because ``called`` is
  not a source status for ``call`` in ``_TRANSITIONS`` (the route answers 422
  before touching the history), so a duplicate request has no new event. Recall
  does not weaken that: it is a separate action an operator must choose, so a
  retried or double-submitted ``call`` still cannot announce twice;
* nothing here depends on a browser clock, a local counter or the audit table.

The module is deliberately pure (standard library only, no SQLAlchemy, no
FastAPI) so the rule can be executed and tested without a database. It is used
by ``_entry_to_dict`` to publish ``call_event_id`` / ``call_event_at`` and by
``backend/queuing/announcements.py`` to validate a claim.

This is not a new table and not a new audit record: it is a *reading* of the
existing status history. See the W2 reliability completion report, sections 3-4.
"""

from __future__ import annotations

#: The action string the queue route records for a call (main.py:508-527).
CALL_ACTION = "call"
#: MP-08: the explicit recall action. A second call for the *same* entry is a
#: different act, so it is a different action string rather than a repeated
#: ``call`` — that is what keeps a duplicated ``call`` request refused (422).
RECALL_ACTION = "recall"
#: Every action that moves an entry into ``called``, and so is a call event.
CALL_ACTIONS = (CALL_ACTION, RECALL_ACTION)
#: The status a successful call moves the entry into.
CALLED_STATUS = "called"
#: Prefix for the derived identity. Kept short: the column contract is 120 chars.
EVENT_ID_PREFIX = "qce"

#: Longest id this module will produce (``qce:`` + uuid + ``:`` + index).
MAX_EVENT_ID_LENGTH = 120


def call_events(history) -> list[dict]:
    """Every completed call transition in *history*, oldest first.

    A call event is a record that moved the entry into ``called`` through
    ``call`` or ``recall`` (MP-08). Both count, because both end in an
    announcement; the ``action`` is kept on the event so a caller can tell a
    first call from a recall without parsing the id.

    Tolerant by design: a malformed or missing history yields an empty list
    rather than an exception, because a queue row must never fail to render
    (or to be authorised) because of one bad history element.
    """
    events: list[dict] = []
    if not isinstance(history, (list, tuple)):
        return events
    for index, item in enumerate(history):
        if not isinstance(item, dict):
            continue
        if item.get("action") not in CALL_ACTIONS:
            continue
        if item.get("to") != CALLED_STATUS:
            continue
        at = item.get("at")
        events.append({
            "index": index,
            "at": at if isinstance(at, str) else "",
            "action": item.get("action"),
            "from": item.get("from") if isinstance(item.get("from"), str) else "",
        })
    return events


def event_id_for_index(entry_id: str, index: int) -> str:
    """The wire identity for the ``call`` recorded at *index* in *entry_id*."""
    return f"{EVENT_ID_PREFIX}:{entry_id}:{int(index)}"


def current_call_event(entry_id, history):
    """The most recent call event of one entry, or ``None``.

    Returns ``{"call_event_id", "call_event_at", "call_index", "call_count"}``.
    ``call_count`` counts every call in the history, so a caller can tell a
    first call from a recall without parsing the id.
    """
    if not isinstance(entry_id, str) or not entry_id.strip():
        return None
    events = call_events(history)
    if not events:
        return None
    last = events[-1]
    candidate = event_id_for_index(entry_id.strip(), last["index"])
    if len(candidate) > MAX_EVENT_ID_LENGTH:      # pragma: no cover - guard only
        return None
    return {
        "call_event_id": candidate,
        "call_event_at": last["at"],
        "call_index": last["index"],
        "call_count": len(events),
    }


def is_current_call_event(entry_id, history, event_id) -> bool:
    """True when *event_id* is exactly the entry's latest call event.

    Used by the announcement claim endpoint: a client may not claim an id that
    is not the entry's current event, so a stale or invented id cannot consume
    the delivery slot of a real call.
    """
    if not isinstance(event_id, str) or not event_id.strip():
        return False
    current = current_call_event(entry_id, history)
    return bool(current) and current["call_event_id"] == event_id.strip()
