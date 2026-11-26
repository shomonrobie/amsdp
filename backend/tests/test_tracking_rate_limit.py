"""MP-25 / GAP-20 — the durable rate-limit budget.

``common.rate_limit.hit`` is the whole mechanism: one ``INSERT … ON CONFLICT DO
UPDATE`` against ``tracking_rate_buckets``.  These tests exercise it against the
real database, because the property that matters — *two callers on two
connections share one budget* — is a property of the statement, not of a dict in
this process.

``now`` is injected in every test so the window boundary is deterministic; no test
sleeps.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.database import SessionFactory
from common.models import TrackingRateBucket
from common.rate_limit import hit

BUCKET = "pqt:test-" + uuid.uuid4().hex[:8]


def _purge(bucket):
    with SessionFactory() as s:
        s.query(TrackingRateBucket).filter(
            TrackingRateBucket.bucket == bucket).delete(synchronize_session=False)
        s.commit()


def _charge(bucket, moment, limit=3, window=60):
    with SessionFactory() as s:
        try:
            allowed, remaining, reset_epoch = hit(
                s, bucket, limit=limit, window_seconds=window, now=moment)
            s.commit()
            return allowed, remaining, reset_epoch
        finally:
            s.close()


def test_the_limit_is_the_number_of_requests_allowed():
    _purge(BUCKET)
    try:
        moment = datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc)
        results = [_charge(BUCKET, moment) for _ in range(5)]
        assert [r[0] for r in results] == [True, True, True, False, False]
        assert [r[1] for r in results] == [2, 1, 0, 0, 0]
        # The reset is the end of the current fixed window, not "now + window".
        assert results[0][2] == int((moment + timedelta(seconds=60)).timestamp())
    finally:
        _purge(BUCKET)


def test_two_connections_share_one_budget():
    """The property the in-process dict could not have."""
    _purge(BUCKET)
    try:
        moment = datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc)
        first = _charge(BUCKET, moment, limit=2)
        second = _charge(BUCKET, moment, limit=2)   # a *separate* session
        third = _charge(BUCKET, moment, limit=2)
        assert [first[0], second[0], third[0]] == [True, True, False], \
            "a second worker must not get its own budget"
    finally:
        _purge(BUCKET)


def test_a_new_window_starts_afresh():
    _purge(BUCKET)
    try:
        start = datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc)
        for _ in range(3):
            _charge(BUCKET, start, limit=3)
        assert _charge(BUCKET, start, limit=3)[0] is False, "the window is full"
        later = start + timedelta(seconds=61)
        allowed, remaining, _ = _charge(BUCKET, later, limit=3)
        assert allowed is True, "a new window admits the caller again"
        assert remaining == 2
    finally:
        _purge(BUCKET)


def test_the_bucket_key_is_clamped_to_the_column_width():
    """A long address must not raise: a limiter may not fail open on a length."""
    long_bucket = ("pqt:" + "9" * 300)
    try:
        allowed, _, _ = _charge(long_bucket, datetime.now(timezone.utc), limit=1)
        assert allowed is True
    finally:
        _purge(("pqt:" + "9" * 300)[:120])


def test_nothing_identifying_is_stored():
    """The row is an address prefix and two numbers — no path, token or query."""
    _purge(BUCKET)
    try:
        _charge(BUCKET, datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc))
        with SessionFactory() as s:
            row = s.query(TrackingRateBucket).filter(
                TrackingRateBucket.bucket == BUCKET).one()
            values = [str(row.bucket), str(row.hits), str(row.window_started_at)]
        for value in values:
            assert "/" not in value, "a path must never be stored in a bucket key"
    finally:
        _purge(BUCKET)
