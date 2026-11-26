"""Durable request budgets shared by the public endpoints (MP-25 / GAP-20).

The in-process sliding window was honest about what it was — a counter in one
worker's memory — and that is exactly why it could not be relied on: the stack
runs several workers, every restart cleared the counters, and a limiter that a
deploy resets is not a limiter.

:func:`hit` keeps the budget in the database instead, in
``tracking_rate_buckets`` (``common.models.TrackingRateBucket``), and allocates
it with **one** statement:

    INSERT … ON CONFLICT (bucket) DO UPDATE SET hits = …, window_started_at = …

PostgreSQL serialises two workers updating the same row, so the count is exact
without an application lock, a Redis instance or a new dependency.  The window is
a fixed interval rather than a sliding one: a fixed window can admit up to twice
the limit across a boundary, which is acceptable for a public read-only page and
is stated here rather than discovered later.

Callers own the session and the commit, so a rate decision can be made inside the
transaction that already exists — and a failure to record the hit must never turn
a page into a 500 (the callers catch and fall back).
"""

from datetime import datetime, timedelta, timezone

import sqlalchemy as sa

#: The one statement that allocates a request.  ``:cutoff`` marks the end of the
#: previous window: a row older than that restarts at 1, a row inside it counts up.
_ALLOCATE = sa.text("""
    INSERT INTO tracking_rate_buckets (bucket, window_started_at, hits)
    VALUES (:bucket, :now, 1)
    ON CONFLICT (bucket) DO UPDATE SET
        hits = CASE
            WHEN tracking_rate_buckets.window_started_at <= :cutoff THEN 1
            ELSE tracking_rate_buckets.hits + 1
        END,
        window_started_at = CASE
            WHEN tracking_rate_buckets.window_started_at <= :cutoff THEN :now
            ELSE tracking_rate_buckets.window_started_at
        END
    RETURNING hits, window_started_at
""")


def hit(session, bucket: str, *, limit: int, window_seconds: int,
        now: datetime | None = None) -> tuple[bool, int, int]:
    """Count one request in *bucket* and report the decision.

    Returns ``(allowed, remaining, reset_epoch)`` where *reset_epoch* is the
    Unix second at which the current window ends.  ``allowed`` is ``hits <=
    limit``, so the limit is the number of requests **permitted**, not the number
    refused.

    The caller commits.  ``now`` exists so a test can pin the window boundary
    without sleeping; production callers never pass it.
    """
    moment = now or datetime.now(timezone.utc)
    cutoff = moment - timedelta(seconds=window_seconds)
    row = session.execute(_ALLOCATE, {
        "bucket": bucket[:120], "now": moment, "cutoff": cutoff,
    }).first()
    used = int(row[0])
    started = row[1]
    if started.tzinfo is None:                    # a naive column read back
        started = started.replace(tzinfo=timezone.utc)
    reset_epoch = int((started + timedelta(seconds=window_seconds)).timestamp())
    return used <= limit, max(0, limit - used), reset_epoch
