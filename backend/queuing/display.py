"""AMSDP Digital Queue Display System (DQDS) — M9-C.

Public, read-only queue display for waiting-room TVs/monitors.

Security (Gate 1):
- No auth required (public display).
- Path-scoped by org+branch; unknown *or non-active* → 404 (non-disclosing).
- Rate-limited at 30 req/min/IP (separate from PQT's 10/min), emitting
  X-RateLimit-Limit / X-RateLimit-Remaining / X-RateLimit-Reset and, on
  refusal, Retry-After (never a bare 429).
- Cache: "public, max-age=10" on board data; "no-store" on 404/429 so a
  shared cache cannot pin an error response.
- Zero patient PII: only doctor name, token number, and counts.
"""
import json, time
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends, Response
from sqlalchemy import or_

from common.database import SessionFactory
from common.models import Organization, Branch, QueueEntry, Doctor

router = APIRouter(prefix="/api/v1/queue/display", tags=["dqds"])

# ---------------------------------------------------------------------------
# Rate limiting (in-process sliding window, separate from PQT)
# A durable shared limiter remains deferred to M9-F (M9 report §18.10).
# ---------------------------------------------------------------------------
_DQDS_RATE: dict[str, list[float]] = {}
_DQDS_RATE_LIMIT = 30          # requests
_DQDS_RATE_WINDOW = 60.0       # seconds
_DQDS_PRUNE_EVERY = 512        # requests between stale-bucket sweeps
_dqds_seen = 0

# Board data is short-lived but publicly cacheable; error responses never are.
_PUBLIC_CACHE = {"Cache-Control": "public, max-age=10"}
_ERROR_HEADERS = {"Cache-Control": "no-store"}


def _rate_headers(remaining: int, reset_epoch: int) -> dict:
    """Rate-limit headers required on every response the limiter touches."""
    return {
        "X-RateLimit-Limit": str(_DQDS_RATE_LIMIT),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset_epoch),
    }


def _prune_rate_state(now: float) -> None:
    """Drop buckets whose window has fully expired (bounds memory)."""
    stale = [ip for ip, ts in _DQDS_RATE.items()
             if not ts or now - ts[-1] >= _DQDS_RATE_WINDOW]
    for ip in stale:
        _DQDS_RATE.pop(ip, None)


def _dqds_rate_limit(request: Request) -> dict:
    """Sliding-window limiter; returns the rate headers for the response."""
    global _dqds_seen
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    _dqds_seen += 1
    if _dqds_seen % _DQDS_PRUNE_EVERY == 0:
        _prune_rate_state(now)
    ts = [t for t in _DQDS_RATE.get(ip, ()) if now - t < _DQDS_RATE_WINDOW]
    if len(ts) >= _DQDS_RATE_LIMIT:
        _DQDS_RATE[ip] = ts
        # Seconds until the oldest request leaves the window.
        retry_after = max(1, int(_DQDS_RATE_WINDOW - (now - ts[0])) + 1)
        headers = _rate_headers(0, int(time.time()) + retry_after)
        headers["Retry-After"] = str(retry_after)
        headers.update(_ERROR_HEADERS)
        raise HTTPException(429, "too many requests", headers=headers)
    ts.append(now)
    _DQDS_RATE[ip] = ts
    return _rate_headers(_DQDS_RATE_LIMIT - len(ts),
                         int(time.time()) + int(_DQDS_RATE_WINDOW) + 1)


# Queue statuses that are "active" for the display board.
# completed / cancelled / no_show are terminal and never counted.
_ACTIVE = ("waiting", "called", "in_consultation", "skipped")

# Statuses that represent a patient still awaiting (or being called into) service.
_WAITING = ("waiting", "called", "skipped")


def _active(col):
    """True when a tenant/roster row may feed a public display.

    NULL status is treated as active: such rows predate suspension support and
    were never explicitly disabled, so hiding them would be a silent outage.
    """
    return or_(col == "active", col.is_(None))


def _not_found():
    """Non-disclosing 404 shared by every failed resolution path.

    Unknown org, unknown branch and a branch belonging to another organization
    are indistinguishable to the caller (never 403). Error responses are
    uncacheable so a later fix is not masked by a shared cache.
    """
    return HTTPException(404, "not found", headers=dict(_ERROR_HEADERS))


def _org_branch_or_404(session, org_code: str, branch_code: str):
    """Resolve an active org + its own active branch, or raise 404."""
    org = session.query(Organization).filter(
        Organization.code == org_code, _active(Organization.status)).first()
    if not org:
        raise _not_found()
    branch = session.query(Branch).filter(
        Branch.organization_id == org.id,
        Branch.code == branch_code,
        _active(Branch.status)).first()
    if not branch:
        raise _not_found()
    return org, branch


# ---------------------------------------------------------------------------
# Public DQDS endpoint
# ---------------------------------------------------------------------------

@router.get("/{org_code}/{branch_code}")
def get_queue_display(org_code: str, branch_code: str,
                      rate_headers: dict = Depends(_dqds_rate_limit)):
    """Public queue display for a single branch.

    Returns doctor-wise queue summary with currently-serving token and
    waiting count. Zero patient PII.
    """
    session = SessionFactory()
    try:
        org, branch = _org_branch_or_404(session, org_code, branch_code)
        today = date.today()

        # Active entries for this org+branch+today only. The doctor join is
        # constrained to the same organization so a mis-joined queue entry can
        # never publish another tenant's doctor name.
        rows = session.query(QueueEntry, Doctor).join(
            Doctor, QueueEntry.doctor_id == Doctor.id
        ).filter(
            QueueEntry.organization_id == org.id,
            QueueEntry.branch_id == branch.id,
            QueueEntry.date == today,
            QueueEntry.status.in_(_ACTIVE),
            Doctor.organization_id == org.id,
            _active(Doctor.status),
        ).order_by(Doctor.name, QueueEntry.position).all()

        # Aggregate per doctor. Rows arrive ordered by (doctor name, position),
        # so the first entry of each status group is the lowest queue position.
        buckets: dict[str, dict] = {}
        for qe, doc in rows:
            b = buckets.setdefault(doc.id, {
                "doctor_name": doc.name or "",
                "patients_waiting": 0,
                "called": None,
                "in_consultation": None,
            })
            if qe.status in _WAITING:
                b["patients_waiting"] += 1
            # "Currently serving" prefers an in-consultation patient, else the
            # lowest-position called patient.
            if qe.status == "in_consultation":
                if b["in_consultation"] is None:
                    b["in_consultation"] = qe.token
            elif qe.status == "called" and b["called"] is None:
                b["called"] = qe.token

        # Public schema: an explicit allow-list, hand-built. Internal
        # aggregation state is never reachable from this structure.
        doctors_out = [
            {
                "doctor_name": b["doctor_name"],
                "currently_serving": b["in_consultation"] or b["called"],
                "patients_waiting": b["patients_waiting"],
            }
            for b in buckets.values()
        ]

        now_utc = datetime.now(timezone.utc).isoformat()
        body = json.dumps({
            "organization": {"name": org.name, "code": org.code},
            "branch": {"name": branch.name, "code": branch.code},
            "doctors": doctors_out,
            "updated_at": now_utc,
        })

        return Response(
            content=body,
            media_type="application/json",
            headers={**_PUBLIC_CACHE, **rate_headers},
        )
    except HTTPException:
        raise
    finally:
        session.close()
