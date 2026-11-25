"""One definition of a blocked period — shared by scheduling and appointment.

BR §15 makes a blocked date/period part of the schedule, and the MVP acceptance
requires that it *cannot be booked*.  Two services therefore have to agree on
what "this booking falls inside the block" means: ``scheduling`` publishes the
available slots and ``appointment`` accepts or refuses the booking.  If each
decided for itself, a blocked 10:00 hour could be published as free and still be
refused (or worse, published as free and accepted).

Pure functions only: no database, no FastAPI, no policy, no audit.  Callers keep
their own authorization and transaction rules, exactly like
:mod:`common.slots`.

**Degrade, never raise.**  A row whose stored window cannot be read (a legacy or
hand-edited ``"9:00"``) must not turn ``available-slots`` into a 500 — the same
rule :mod:`common.slots` follows for templates (F-14).  The direction of the
degradation is *closed*: an unreadable window covers the whole day, so the
failure mode is "refused a slot that might have been free", never "booked into a
block".
"""

from typing import Optional

from common.slots import MIN_SLOT_DURATION, to_minutes

#: The statuses a block row may hold.  ``cancelled`` is a terminal record, not a
#: delete: the row and its audit events are history (``.clinerules`` §3).
BLOCK_STATUSES = ("active", "cancelled")

#: Kinds returned by :func:`normalise_window`.
WHOLE_DAY = "whole_day"
WINDOW = "window"
MALFORMED = "malformed"


def normalise_window(start_time, end_time):
    """Classify a block's stored time window.

    Returns ``(kind, start_minutes, end_minutes)`` where *kind* is one of
    :data:`WHOLE_DAY` (no window — the whole day is blocked), :data:`WINDOW`
    (a usable ``start < end`` window, minutes since midnight) or
    :data:`MALFORMED` (half a window, an unreadable clock value, or an inverted
    window).  Never raises.
    """
    has_start = bool((start_time or "").strip())
    has_end = bool((end_time or "").strip())
    if not has_start and not has_end:
        return (WHOLE_DAY, None, None)
    start = to_minutes(start_time)
    end = to_minutes(end_time)
    if start is None or end is None or end <= start:
        return (MALFORMED, None, None)
    return (WINDOW, start, end)


def window_label(start_time, end_time) -> str:
    """A human/audit label for the stored window: ``all day`` or ``09:00–11:00``."""
    kind, _, _ = normalise_window(start_time, end_time)
    if kind == WINDOW:
        return f"{start_time}–{end_time}"
    if kind == MALFORMED:
        return "all day (unreadable window)"
    return "all day"


def covers_date(block, day) -> bool:
    """True when *day* falls inside the block's inclusive date range."""
    if day is None:
        return False
    try:
        return block.start_date <= day <= block.end_date
    except TypeError:            # a row with a non-date value cannot be trusted
        return True


def covers(block, day, start_time=None, end_time=None) -> bool:
    """True when a booking at *day* / *start_time*–*end_time* is blocked.

    A whole-day block covers everything on its dates.  A partial block covers a
    booking that **overlaps** its window (``start < block_end and end >
    block_start``), so touching windows — a booking ending exactly when the block
    begins — are not blocked.

    Two documented fail-closed cases: a block whose window cannot be read covers
    the whole day, and a booking with **no time** on a partially blocked day is
    refused (there is no way to prove it falls outside the blocked hours).
    """
    if not covers_date(block, day):
        return False
    kind, block_start, block_end = normalise_window(
        getattr(block, "start_time", None), getattr(block, "end_time", None))
    if kind != WINDOW:
        return True
    booking_start = to_minutes(start_time)
    if booking_start is None:
        return True
    booking_end = to_minutes(end_time)
    if booking_end is None:
        booking_end = booking_start + MIN_SLOT_DURATION
    return booking_start < block_end and booking_end > block_start


def first_covering(blocks, day, start_time=None, end_time=None) -> Optional[object]:
    """The first block from *blocks* that covers the booking, or ``None``."""
    for block in blocks or ():
        if covers(block, day, start_time, end_time):
            return block
    return None
