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

Multi-display (MP-35 … MP-46, specification MD-01 … MD-19):

- ``?display=<code>`` selects one configured board for this branch.  The
  branch-wide board with no parameter keeps its historic payload exactly.
- Scope is filtered **in SQL**: ``doctors`` (explicit membership),
  ``department`` and ``room`` (through ``doctor_branches.room_id``).  An empty
  scope is an empty board, never "all doctors" — a configuration mistake must
  not widen a public feed.
- A display row is trusted only after its organization matches the branch in
  the URL, so a mis-typed row cannot publish another tenant's queue.
- Unknown **and disabled** displays raise the same 404 body and headers as an
  unknown branch.  A request for a disabled display writes one throttled
  ``queue.display.disabled_requested`` audit row; an unknown code writes none,
  because an anonymous probe must not write unbounded rows into an append-only
  trail (MD-19).
- ``show_room`` / ``show_estimated_wait`` / ``show_waiting_count`` are applied
  while the body is built: a field the facility switched off is **absent** from
  the raw response, not hidden in CSS (MD-17).
- A configured board carries ``board_version`` and a weak ``ETag``; an
  ``If-None-Match`` revalidation answers ``304`` with no body (MD-15).
- The public router is GET-only; a state-changing verb gets ``405`` with
  ``Allow: GET`` and ``no-store`` (MD-18).  No board response sets a cookie.

"""
import hashlib, json, math, os, time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends, Response
from sqlalchemy import or_

from common.audit import record_audit
from common.database import SessionFactory
from common.models import (Organization, Branch, QueueEntry, Doctor,
                           DoctorBranch, FacilityRoom, QueueDisplay,
                           QueueDisplayDoctor)
from common.timeutil import facility_zone, operational_today

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


def _bucket_key(request: Request) -> str:
    """The limiter bucket: one per client **and** display (MD-10).

    Keying by client address alone would put a branch's six screens in one
    30/min bucket — six polls every ten seconds is 36/min, so the sixth screen
    would be throttled while nobody was abusing anything.  Keying by display as
    well gives each configured screen its own fair share, and an unknown code
    only ever consumes its own bucket.  A durable, cross-process limiter is
    still GAP-20 / MP-25.
    """
    ip = request.client.host if request.client else "unknown"
    display = (request.query_params.get("display") or "").strip().lower()
    return f"{ip}|{display}"


def _dqds_rate_limit(request: Request) -> dict:
    """Sliding-window limiter; returns the rate headers for the response."""
    global _dqds_seen
    ip = _bucket_key(request)
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
# Display resolution and scope (MP-36, MP-37, MP-41 / MD-02 … MD-09, MD-14)
# ---------------------------------------------------------------------------

#: One ``queue.display.disabled_requested`` row per display per five minutes
#: (MD-19).  In-process, like the request limiter: the durable cross-process
#: limiter is GAP-20 / MP-25, and this throttle exists only to stop an
#: unauthenticated probe from amplifying rows into an append-only trail.
_DISABLED_NOTE_WINDOW = 300.0
_DISABLED_NOTED: dict[str, float] = {}


def _note_disabled_request(session, display) -> None:
    """Record a throttled request for a *disabled* display, never blocking it.

    An unknown code produces no row at all — the caller cannot tell an unknown
    code from a disabled one, and auditing the unknown case would let anyone
    write unbounded rows.  A disabled display is a real row, so the event can be
    attributed to its organization and branch without trusting the request.

    The audit write must never turn a public 404 into a 500: if it fails, the
    request still gets its non-disclosing answer.
    """
    now = time.monotonic()
    last = _DISABLED_NOTED.get(display.id)
    if last is not None and now - last < _DISABLED_NOTE_WINDOW:
        return
    _DISABLED_NOTED[display.id] = now
    try:
        record_audit(session, service="queuing",
                     org_id=display.organization_id,
                     action="queue.display.disabled_requested",
                     target_type="queue_display", target_id=display.id,
                     actor_id="anonymous", actor_role="public",
                     branch_id=display.branch_id,
                     after={"code": display.code, "status": "disabled"})
        session.commit()
    except Exception:                      # pragma: no cover - defensive
        session.rollback()


def _display_or_404(session, org, branch, code: str):
    """Resolve this branch's display by code, or raise the shared 404.

    Resolution is branch-scoped *and* organization-checked: a row whose
    organization does not match the branch cannot publish, so a mis-typed or
    copied row is a configuration error rather than a cross-tenant leak.
    """
    display = session.query(QueueDisplay).filter(
        QueueDisplay.code == code,
        QueueDisplay.branch_id == branch.id,
        QueueDisplay.organization_id == org.id,
    ).first()
    if display is None:
        raise _not_found()
    if (display.status or "active") != "active":
        _note_disabled_request(session, display)
        raise _not_found()
    return display


def _scope_predicate(session, org, branch, display, column=None):
    """A SQL predicate limiting rows to the display's scope.

    Returns ``None`` for the branch-wide board.  Every non-branch scope returns
    a predicate, including an **empty** one: ``IN (SELECT … )`` over no rows
    selects no doctors, which is the specified empty state.  Returning ``None``
    for an empty scope would silently publish the whole branch.

    ``column`` selects what is compared: ``Doctor.id`` for the board query and
    ``QueueEntry.doctor_id`` for the completed-consultation query.  Passing the
    doctor column into a ``queue_entries`` query would cross-join the two tables
    and multiply every sample — the exact fabrication the estimate marker is
    meant to prevent.
    """
    target = Doctor.id if column is None else column
    scope = (display.scope_type or "branch")
    if scope == "branch":
        return None
    if scope == "doctors":
        return target.in_(
            session.query(QueueDisplayDoctor.doctor_id).filter(
                QueueDisplayDoctor.display_id == display.id))
    # department / room both resolve through the doctor's chamber at this branch
    assigned = session.query(DoctorBranch.doctor_id).filter(
        DoctorBranch.branch_id == branch.id,
        DoctorBranch.room_id.isnot(None),
        _active(DoctorBranch.status))
    if scope == "room":
        assigned = assigned.filter(DoctorBranch.room_id == display.room_id)
    else:
        assigned = assigned.join(
            FacilityRoom, FacilityRoom.id == DoctorBranch.room_id).filter(
                FacilityRoom.organization_id == org.id,
                FacilityRoom.department_id == display.department_id)
    return target.in_(assigned)




#: Facility-wide fallback service time when a doctor has too few samples to
#: measure (specification E.5, MD-13).
_DEFAULT_SERVICE_MINUTES = 10


def _room_labels(session, org, branch) -> dict[str, str]:
    """``doctor_id -> room name`` for this branch, read as facility information.

    The room is a *label*, not a queue column: ``queue_entries`` is unchanged.
    A doctor with no chamber assignment simply has no entry and renders ``—``.
    """
    rows = session.query(DoctorBranch.doctor_id, FacilityRoom.name).join(
        FacilityRoom, FacilityRoom.id == DoctorBranch.room_id).filter(
            DoctorBranch.branch_id == branch.id,
            FacilityRoom.organization_id == org.id,
            _active(DoctorBranch.status)).all()
    return {doctor_id: name for doctor_id, name in rows if name}


def _as_datetime(value):
    """Parse a ``status_history`` timestamp, which is stored as an ISO string."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _consultation_minutes(history):
    """Minutes between this entry's last ``in_consultation`` and ``completed``."""
    started = finished = None
    for event in history or []:
        if not isinstance(event, dict):
            continue
        status = event.get("to")
        at = _as_datetime(event.get("at"))
        if at is None:
            continue
        if status == "in_consultation":
            started, finished = at, None
        elif status == "completed" and started is not None:
            finished = at
    if started is None or finished is None:
        return None
    minutes = (finished - started).total_seconds() / 60.0
    return minutes if minutes > 0 else None


def _measured_service_minutes(session, org, branch, today, scope) -> dict[str, float]:
    """Mean completed-consultation minutes per doctor for today, when n ≥ 3.

    Built from ``queue_entries.status_history`` of *completed* entries for this
    organization, branch and day — never from a patient record.  A doctor with
    fewer than three completed consultations is absent from the map, so the
    caller uses the facility default instead of inventing a measurement.
    """
    query = session.query(QueueEntry).filter(
        QueueEntry.organization_id == org.id,
        QueueEntry.branch_id == branch.id,
        QueueEntry.date == today,
        QueueEntry.status == "completed")
    if scope is not None:
        query = query.filter(scope)
    samples: dict[str, list[float]] = {}
    for entry in query.all():
        minutes = _consultation_minutes(entry.status_history)
        if minutes is not None:
            samples.setdefault(entry.doctor_id, []).append(minutes)
    return {doctor_id: sum(values) / len(values)
            for doctor_id, values in samples.items() if len(values) >= 3}


def _default_service_minutes() -> int:
    """``AMSDP_AVG_SERVICE_MINUTES``, floored at 1; 10 when unset or invalid."""
    raw = os.environ.get("AMSDP_AVG_SERVICE_MINUTES", "")
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        value = _DEFAULT_SERVICE_MINUTES
    return max(1, value)


def _board_version(projection) -> str:
    """A hash of the published projection **only**.

    ``updated_at`` is deliberately excluded: a version that changed every
    request would defeat revalidation and make every screen re-render on every
    poll (specification RMD-8).
    """
    canonical = json.dumps(projection, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def _etag_matches(header: str | None, etag: str) -> bool:
    """Weak comparison of an ``If-None-Match`` header against our ``ETag``."""
    if not header:
        return False
    opaque = etag[2:] if etag.startswith("W/") else etag
    for candidate in header.split(","):
        candidate = candidate.strip()
        if candidate == "*":
            return True
        if candidate.startswith("W/"):
            candidate = candidate[2:]
        if candidate == opaque:
            return True
    return False


# ---------------------------------------------------------------------------
# Public DQDS endpoint
# ---------------------------------------------------------------------------

@router.get("/{org_code}/{branch_code}")
def get_queue_display(org_code: str, branch_code: str, request: Request,
                      rate_headers: dict = Depends(_dqds_rate_limit)):
    """Public queue display for a single branch, or one configured display.

    Returns doctor-wise queue summary with currently-serving token and waiting
    count. Zero patient PII.  ``?display=<code>`` narrows the board to that
    display's configured scope; without it the payload is exactly what it was
    before multi-display existed (specification 5.2 — the historic contract,
    including its 404/429/cache behaviour, is unchanged).

    Display codes are stored lower-case; the query parameter is normalised the
    same way, and the write path (MP-39) refuses anything else.
    """
    session = SessionFactory()
    try:
        org, branch = _org_branch_or_404(session, org_code, branch_code)
        # Facility-local day (BR §8), never the server's date: the board must
        # roll over at the facility's midnight, not the container's. The org
        # comes from the path and is already tenant-validated, so the zone
        # lookup stays inside this tenant.
        today = operational_today(session, org.id)

        display_code = (request.query_params.get("display") or "").strip().lower()
        display = (_display_or_404(session, org, branch, display_code)
                   if display_code else None)
        scope = _scope_predicate(session, org, branch, display) if display else None

        # Active entries for this org+branch+today only. The doctor join is
        # constrained to the same organization so a mis-joined queue entry can
        # never publish another tenant's doctor name.
        query = session.query(QueueEntry, Doctor).join(
            Doctor, QueueEntry.doctor_id == Doctor.id
        ).filter(
            QueueEntry.organization_id == org.id,
            QueueEntry.branch_id == branch.id,
            QueueEntry.date == today,
            QueueEntry.status.in_(_ACTIVE),
            Doctor.organization_id == org.id,
            _active(Doctor.status),
        )
        if scope is not None:
            query = query.filter(scope)
        rows = query.order_by(Doctor.name, QueueEntry.position).all()

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
        if display is None:
            # The historic board, unchanged: same keys, same values, same
            # headers.  New fields appear only on a configured display so that
            # nine years of signage and every existing test keep their contract.
            doctors_out = [
                {
                    "doctor_name": b["doctor_name"],
                    "currently_serving": b["in_consultation"] or b["called"],
                    "patients_waiting": b["patients_waiting"],
                }
                for b in buckets.values()
            ]
            body = json.dumps({
                "organization": {"name": org.name, "code": org.code},
                "branch": {"name": branch.name, "code": branch.code},
                "doctors": doctors_out,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            return Response(
                content=body,
                media_type="application/json",
                headers={**_PUBLIC_CACHE, **rate_headers},
            )

        # ---- configured display (MD-15, MD-17) ---------------------------
        # ``False`` is the only value that suppresses; NULL/absent defaults to
        # published, because a row written before a policy existed never said
        # "off".
        show_room = display.show_room is not False
        show_wait = display.show_estimated_wait is not False
        show_count = display.show_waiting_count is not False

        rooms = _room_labels(session, org, branch) if show_room else {}
        # Completed consultations are filtered by ``QueueEntry.doctor_id``, not
        # by the board's ``Doctor.id`` predicate (which would cross-join).
        completed_scope = (_scope_predicate(session, org, branch, display,
                                            column=QueueEntry.doctor_id)
                           if display is not None else None)
        measured = _measured_service_minutes(session, org, branch, today,
                                             completed_scope)
        default_minutes = _default_service_minutes()

        doctors_out = []
        for doc_id, b in buckets.items():
            row = {
                "doctor_name": b["doctor_name"],
                "currently_serving": b["in_consultation"] or b["called"],
            }
            # A field the facility switched off is absent from the body, never
            # merely hidden by the page: the UI is not the safety boundary.
            if show_count:
                row["patients_waiting"] = b["patients_waiting"]
            if show_room:
                row["room_name"] = rooms.get(doc_id)
            if show_wait:
                sample = measured.get(doc_id)
                row["estimated_wait_minutes"] = (
                    max(1, math.ceil(sample)) if sample is not None
                    else default_minutes)
                row["estimate"] = True
            doctors_out.append(row)

        meta = {
            "code": display.code,
            "name": display.name,
            "language": display.language or "bn",
            "scope_type": display.scope_type or "branch",
            "footer_text": display.footer_text or "",
        }
        timezone_name = getattr(facility_zone(session, org.id), "key", "") or ""
        operational_date = today.isoformat()
        # The version hashes the *projection* only; ``updated_at`` is excluded so
        # an idle board revalidates instead of re-rendering every ten seconds.
        version = _board_version({"operational_date": operational_date,
                                  "display": meta, "doctors": doctors_out})
        etag = f'W/"{version}"'
        headers = {**_PUBLIC_CACHE, **rate_headers, "ETag": etag}

        if _etag_matches(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers=headers)

        body = json.dumps({
            "organization": {"name": org.name, "code": org.code},
            "branch": {"name": branch.name, "code": branch.code},
            "display": meta,
            "doctors": doctors_out,
            "board_version": version,
            "operational_date": operational_date,
            "timezone": timezone_name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        return Response(content=body, media_type="application/json",
                        headers=headers)
    except HTTPException:
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Read-only public surface (MP-46 / MD-18, MD-19)
# ---------------------------------------------------------------------------

@router.api_route("/{org_code}/{branch_code}",
                  methods=["POST", "PUT", "PATCH", "DELETE"],
                  include_in_schema=False)
def board_is_read_only(org_code: str, branch_code: str):
    """A public display URL never accepts a state-changing verb.

    Registered explicitly rather than relying on the framework's default 405 so
    that the answer is identical for all four verbs, carries ``Allow: GET``
    (which verbs *are* permitted) and ``no-store`` (an error must never be
    cached), and so a future contributor cannot add a write handler to this
    router without deleting this guard first.

    Nothing is audited here: the caller is anonymous, and an anonymous probe
    must not be able to write rows into an append-only trail (MD-19).
    """
    raise HTTPException(405, "method not allowed",
                        headers={"Allow": "GET", **_ERROR_HEADERS})

