"""Operational date/time helpers.

AMSDP Business Rules §8: operational dates and times follow the *facility's*
configured time zone, while stored timestamps are UTC.

The facility zone is ``organizations.timezone`` (the column Sequence 3's
notification planner already formats against) when the caller can supply a
session and the organization id.  Without them — background helpers, tests,
module-level defaults — it falls back to ``AMSDP_FACILITY_TZ`` and then to
``DEFAULT_TZ``, so the answer never depends on the container's ``TZ`` setting.

Use :func:`operational_today` for anything a human would call "today" (queue day,
appointment day, dashboard day) and :func:`utc_timestamp` for audit/history
timestamps.  Do not mix the two: a service that derives "today" from UTC while
another uses the facility zone files the same visit under two different days
whenever the facility is east of UTC and it is after local midnight (finding
SEQ4-TZ-P1).
"""

import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

#: Facility zone used when neither the organization nor ``AMSDP_FACILITY_TZ``
#: supplies one (matches ``organizations.timezone``'s default).
DEFAULT_TZ = "Asia/Dhaka"


def facility_zone(session=None, organization_id=None) -> ZoneInfo:
    """The time zone of the facility that owns the request.

    ``session``/``organization_id`` are optional: when both are given the
    organization's own ``timezone`` wins.  An unreadable or unknown zone name
    falls back to ``AMSDP_FACILITY_TZ`` and then to :data:`DEFAULT_TZ` rather
    than raising, because a bad column value must not take the queue down.
    """
    name = None
    if session is not None and organization_id:
        try:
            from common.models import Organization
            org = session.query(Organization).filter(
                Organization.id == organization_id).first()
            name = getattr(org, "timezone", None) if org is not None else None
        except Exception:                      # pragma: no cover - defensive
            name = None
    for candidate in (name, os.environ.get("AMSDP_FACILITY_TZ"), DEFAULT_TZ):
        if not candidate:
            continue
        try:
            return ZoneInfo(candidate)
        except Exception:
            continue
    # No tzdata at all (a slim image without zoneinfo): fall back to the process
    # zone rather than failing the request — the date is still a real local date.
    return datetime.now().astimezone().tzinfo or timezone.utc


def operational_today(session=None, organization_id=None) -> date:
    """The facility-local date for that organization — never the UTC date."""
    return datetime.now(facility_zone(session, organization_id)).date()


def utc_timestamp() -> str:
    """A UTC ISO timestamp, as stored in ``*_history`` columns."""
    return str(datetime.now(timezone.utc))
