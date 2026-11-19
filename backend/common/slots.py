"""One definition of a booking slot — shared by scheduling and appointment.

BR §23.3/§23.9 make the slot template the definition of a slot: a window with a
duration and a capacity.  Three readers used to interpret that definition on
their own (gap-analysis finding F-16): the calendar grid expanded templates in
the browser, ``GET /schedules/{id}/available-slots`` expanded them again, and
``create_appointment`` matched the requested minute against them a third way.
This module is the single arithmetic they share, so a given minute belongs to
exactly one slot everywhere — which is also what makes the capacity guard (F-03)
count the same bucket the availability read publishes.

Pure functions only: no database, no FastAPI, no policy.  Every caller keeps its
own authorization rules and transaction boundaries.

Times are ``HH:MM`` zero-padded strings, because that is what
``schedules.slot_templates`` stores and what lexicographic comparison already
relies on throughout the two services.
"""

import re
from typing import Optional

#: ``HH:MM`` in 24-hour form.  Zero-padded, so string order is time order.
HHMM_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)$"
HHMM = re.compile(HHMM_PATTERN)

#: Fallbacks for a template that omits a field.  Deliberately the same numbers
#: the two services already used, so nothing changes for a well-formed row.
DEFAULT_SLOT_DURATION = 15
DEFAULT_CAPACITY = 1

#: A slot shorter than this is a configuration accident, not a consultation.
MIN_SLOT_DURATION = 5

#: Ceiling on the slots one template may expand to: a 24-hour template at the
#: minimum duration is 288, so this only stops a corrupt row from running away.
MAX_SLOTS_PER_TEMPLATE = 500


def is_hhmm(value) -> bool:
    """True when *value* is a zero-padded ``HH:MM`` clock time."""
    return isinstance(value, str) and bool(HHMM.match(value))


def to_minutes(value) -> Optional[int]:
    """Minutes since midnight, or ``None`` when *value* is not ``HH:MM``.

    Returning ``None`` (rather than raising) is deliberate: a stored template
    written before validation existed must degrade to "this template publishes
    nothing", not turn a read endpoint into a 500.
    """
    if not is_hhmm(value):
        return None
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(total: int) -> str:
    """``HH:MM`` for *total* minutes (values past midnight are not expected)."""
    hours, minutes = divmod(int(total), 60)
    return f"{hours:02d}:{minutes:02d}"


def normalise_template(template) -> Optional[dict]:
    """The usable form of a stored template, or ``None`` if it cannot be one.

    A template is usable when its window parses, runs forwards, and its
    duration and capacity are positive numbers.  Anything else is skipped by
    every reader instead of raising.
    """
    if not isinstance(template, dict):
        return None
    start = to_minutes(template.get("start_time"))
    end = to_minutes(template.get("end_time"))
    if start is None or end is None or end <= start:
        return None
    try:
        duration = int(template.get("slot_duration_minutes") or DEFAULT_SLOT_DURATION)
        capacity = int(template.get("max_patients") or DEFAULT_CAPACITY)
        day = template.get("day_of_week")
        day = None if day is None else int(day)
    except (TypeError, ValueError):
        return None
    if duration < MIN_SLOT_DURATION or capacity < 1:
        return None
    if day is not None and not 0 <= day <= 6:
        return None
    return {
        "day_of_week": day,
        "start_time": to_hhmm(start),
        "end_time": to_hhmm(end),
        "slot_duration_minutes": duration,
        "max_patients": capacity,
    }


def templates_for_day(templates, weekday: int) -> list:
    """Normalised templates that publish hours on *weekday* (0 = Monday).

    This is the weekday filter every reader must apply.  The availability read
    used to skip it (F-15), so a Monday-only doctor advertised free slots on a
    Wednesday; the write path matched minutes without it too, so the same
    booking was accepted on a day the doctor never works.

    A template with no ``day_of_week`` is treated as applying to every day:
    rows written before the field was validated behave that way today, and
    silently closing a doctor's published hours is the worse failure.
    """
    out = []
    for template in templates or []:
        normal = normalise_template(template)
        if normal is None:
            continue
        if normal["day_of_week"] is not None and normal["day_of_week"] != weekday:
            continue
        out.append(normal)
    return out


def slot_starts(template) -> list:
    """``[(start, end), …]`` for every slot a template publishes.

    Empty when the template is unusable, which is what keeps a corrupt row from
    reaching ``range()`` and raising inside a read endpoint (F-14).
    """
    normal = normalise_template(template)
    if normal is None:
        return []
    start = to_minutes(normal["start_time"])
    end = to_minutes(normal["end_time"])
    step = normal["slot_duration_minutes"]
    out = []
    for cursor in range(start, end, step):
        if len(out) >= MAX_SLOTS_PER_TEMPLATE:
            break
        out.append((to_hhmm(cursor), to_hhmm(min(cursor + step, end))))
    return out


def slot_window(template, start_time) -> Optional[tuple]:
    """The ``(start, end)`` window of the slot inside *template* holding *start_time*.

    ``None`` when the template is unusable or does not cover the time.  This is
    the arithmetic that makes a booking at 09:07 the *same* slot as 09:00 rather
    than a slot of its own (F-03).
    """
    normal = normalise_template(template)
    at = to_minutes(start_time)
    if normal is None or at is None:
        return None
    start = to_minutes(normal["start_time"])
    end = to_minutes(normal["end_time"])
    if not start <= at < end:
        return None
    step = normal["slot_duration_minutes"]
    window_start = start + ((at - start) // step) * step
    return (to_hhmm(window_start), to_hhmm(min(window_start + step, end)))


def covering_template(templates, start_time) -> Optional[dict]:
    """The first normalised template whose window contains *start_time*."""
    for template in templates or []:
        if slot_window(template, start_time) is not None:
            return normalise_template(template)
    return None


def slot_for(templates, start_time) -> Optional[dict]:
    """``{start_time, end_time, max_patients}`` for the slot holding *start_time*.

    ``None`` when no template covers the time — the caller decides whether that
    is a refusal or the unconfigured-day fallback.
    """
    normal = covering_template(templates, start_time)
    if normal is None:
        return None
    window = slot_window(normal, start_time)
    return {
        "start_time": window[0],
        "end_time": window[1],
        "max_patients": normal["max_patients"],
    }
