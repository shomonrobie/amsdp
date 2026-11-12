"""Durable, worker-shared login throttling.

Sequence 4 finding SEQ4-THROTTLE-D1: the limiter added in Sequence 4 kept its
buckets in a module-level ``dict`` inside ``identity/main.py``.  That made it
per-process — with N uvicorn workers an attacker got N × the allowance, and a
restart cleared every bucket — so it was ineffective against the replica layouts
the deployment plan allows (M8 §5.2).

The counters now live in the ``login_attempts`` table (``common.models``), i.e.
in the PostgreSQL instance every service already uses.  Nothing new is
deployed, the state is shared by all workers and replicas, and it survives a
restart.  M8 §10 asks for exactly this ("a DB-backed route-dependency limiter on
``/api/v1/staff/login``").

Design rules (unchanged from Sequence 4 — they are what makes it usable):

* Keyed on **(client IP, username)**, not on either alone: one noisy user cannot
  lock out a shared office NAT, and one attacker IP cannot spray every account
  unnoticed.
* **No account lockout.**  Locking an account on failed attempts turns this
  control into a denial-of-service tool against a known username.  We only slow
  the attacker down and keep answering ``401`` until the window is saturated,
  then ``429`` with ``Retry-After``.
* A **successful login clears the bucket**, so a legitimate user recovers
  immediately instead of waiting out the window.
* The window is a *sliding* window over stored attempt timestamps, not a fixed
  counter, so it cannot be gamed by bursting at a bucket boundary.

Concurrency: ``pg_advisory_xact_lock(hashtext(key))`` serialises the
count-then-insert for one bucket across processes, so the limit stays exact
under load instead of degrading to roughly N×.  Two different buckets share a
lock only on a 32-bit hash collision, which merely serialises two logins.

Failure handling: these rows are operational, not audit, data.  If the database
rejects the throttle query the caller logs a warning and lets the attempt
proceed — authentication itself queries the same database, so a broken database
cannot become an authentication bypass.

Usage::

    from common.login_throttle import record_attempt, clear_bucket

    record_attempt(session, client_ip, username)   # raises HTTPException(429)
    ...
    clear_bucket(session, client_ip, username)     # on success
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import text

from .models import LoginAttempt

logger = logging.getLogger(__name__)

#: Defaults match the Sequence 4 behaviour (20 attempts / 60 s per bucket).
DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_MAX_ATTEMPTS = 20

#: Attempts older than this are pruned on every limiter call, so an abandoned
#: bucket cannot grow the table without bound.  Ten windows is far beyond any
#: window that has to be honoured, and the range delete is index-covered.
PRUNE_AFTER_SECONDS = 600.0

#: Separator for the advisory-lock key.  A NUL byte is illegal in a PostgreSQL
#: text value, so the ASCII unit separator is used instead; it cannot appear in
#: an IP address.
_KEY_SEP = "\x1f"


def default_window_seconds() -> float:
    """Window length, overridable with ``AMSDP_LOGIN_WINDOW_SECONDS``."""
    try:
        return max(1.0, float(os.environ.get("AMSDP_LOGIN_WINDOW_SECONDS",
                                             DEFAULT_WINDOW_SECONDS)))
    except (TypeError, ValueError):
        return DEFAULT_WINDOW_SECONDS


def default_max_attempts() -> int:
    """Attempts allowed per window, ``AMSDP_LOGIN_MAX_ATTEMPTS`` (default 20)."""
    try:
        return max(1, int(os.environ.get("AMSDP_LOGIN_MAX_ATTEMPTS",
                                         DEFAULT_MAX_ATTEMPTS)))
    except (TypeError, ValueError):
        return DEFAULT_MAX_ATTEMPTS


def bucket_key(client_ip: str, username: str) -> tuple[str, str]:
    """The (ip, username) pair a bucket is counted against.

    The username is capped and case-folded so an oversized body cannot grow the
    key and ``Admin`` cannot buy a second bucket from ``admin``.
    """
    ip = (client_ip or "unknown")[:45]
    return (ip, (username or "")[:120].lower())


def _lock_bucket(session, ip: str, username: str) -> None:
    """Serialise this bucket's count-then-insert across connections.

    PostgreSQL-only: the product runs on PostgreSQL everywhere (``psycopg2`` is
    the only driver in every service image).  On another dialect the limiter
    still counts correctly; it only loses exactness under simultaneous attempts,
    which is why the serialisation is a database lock rather than Python code.
    """
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"),
                    {"k": f"{ip}{_KEY_SEP}{username}"})


def record_attempt(session, client_ip: str, username: str, *,
                   max_attempts: int | None = None,
                   window_seconds: float | None = None,
                   now: datetime | None = None) -> int:
    """Record one attempt; raise ``HTTPException(429)`` when the bucket is full.

    Returns the number of attempts now recorded inside the window *including*
    this one.  The caller owns the session; this function commits, because the
    attempt must be durable even when the credential check that follows fails.
    """
    maximum = default_max_attempts() if max_attempts is None else int(max_attempts)
    window = (default_window_seconds() if window_seconds is None
              else float(window_seconds))
    moment = now or datetime.now(timezone.utc)
    ip, user = bucket_key(client_ip, username)

    _lock_bucket(session, ip, user)

    # Global prune first: bounded table, one index-covered DELETE.
    session.query(LoginAttempt).filter(
        LoginAttempt.attempted_at < moment - timedelta(seconds=PRUNE_AFTER_SECONDS),
    ).delete(synchronize_session=False)

    in_window = session.query(LoginAttempt).filter(
        LoginAttempt.client_ip == ip,
        LoginAttempt.username == user,
        LoginAttempt.attempted_at >= moment - timedelta(seconds=window),
    ).order_by(LoginAttempt.attempted_at).all()

    if len(in_window) >= maximum:
        oldest = in_window[0].attempted_at
        session.commit()          # persist the prune; nothing to add
        retry_after = max(1, int(
            (oldest + timedelta(seconds=window) - moment).total_seconds()) + 1)
        raise HTTPException(
            429,
            "too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )

    session.add(LoginAttempt(client_ip=ip, username=user, attempted_at=moment))
    session.commit()
    return len(in_window) + 1


def clear_bucket(session, client_ip: str, username: str) -> int:
    """Forget a bucket — called on a successful login."""
    ip, user = bucket_key(client_ip, username)
    removed = session.query(LoginAttempt).filter(
        LoginAttempt.client_ip == ip,
        LoginAttempt.username == user,
    ).delete(synchronize_session=False)
    session.commit()
    return removed


def reset(session, client_ip: str | None = None,
          username: str | None = None) -> int:
    """Delete stored attempts (all of them, or one bucket).  Test/admin hook.

    This is not an audit operation: the table holds rate-limit state only, so
    dropping rows neither rewrites nor hides the append-only ``audit_events``
    trail.
    """
    query = session.query(LoginAttempt)
    if client_ip is not None:
        query = query.filter(LoginAttempt.client_ip == (client_ip or "unknown")[:45])
    if username is not None:
        query = query.filter(
            LoginAttempt.username == (username or "")[:120].lower())
    removed = query.delete(synchronize_session=False)
    session.commit()
    return removed
