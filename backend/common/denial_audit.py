"""Denied-request auditing shared by every backend service (owner decision Q-2).

``.clinerules`` §3 requires that denials are *recorded*, never silently
swallowed, and §4 routes denial auditing to the shared audit subsystem.  Before
this module a 403/404/422 left no trace at all: ``common.audit`` was only ever
called by the service that performed an action, so a probe that was *refused*
was invisible in the trail.

How it works
------------
``install_denial_audit(app, service)`` wraps the service's ASGI app in
:class:`DenialAuditMiddleware`.  Recording therefore happens for **every**
response the service produces, whether the denial came from a permission
dependency (``require_permission``), from an endpoint raising ``HTTPException``,
from the tenant gate (``require_org_access``), or from request validation
(422).  There is exactly **one** recording site, so a denial can never be logged
twice by overlapping middleware and exception handlers (Q-2 §10: no duplicate
audit events).

Recorded statuses: ``403``, ``404``, ``422``.

Why 401 is recorded only to the log
-----------------------------------
``audit_events.organization_id`` is ``NOT NULL`` with a foreign key to
``organizations`` (``common/models.py``) and the trail is read per tenant
(``audit/main.py``).  A 401 means there is no *verified* identity: there is no
organization to attribute the row to.  Attribution is never guessed from an
unverified JWT — honouring unverified claims would let an anonymous caller write
rows into another tenant's audit trail, which is a cross-tenant integrity
attack.  Unauthenticated denials are therefore written to the
``amsdp.denial_audit`` log stream instead of the database.  That is an explicit,
documented exclusion, not a silent omission.

Safety properties
-----------------
* The row is written **after** the response has been sent, so nothing in the
  audit path can turn a denial into a success or change the response (Q-2 §11).
* Only the method, a redacted path, the status, the verified actor/org/branch
  claims of the token and an optional ``X-Request-ID`` are stored.  Bearer
  tokens, passwords, query strings and opaque entity identifiers are never
  written (Q-2 §8).
* The write runs in a worker thread and swallows its own failures, so a database
  problem cannot break a request that has already been answered.
"""

import logging
import re

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from .audit import record_audit
from .auth import decode_token
from .database import SessionFactory

logger = logging.getLogger("amsdp.denial_audit")

#: Response statuses that represent a denial and are persisted (Q-2).
DENIAL_STATUSES = frozenset({403, 404, 422})

#: Denials with no verified tenant: recorded on the log stream, never in the
#: table (``audit_events.organization_id`` is NOT NULL — see the module docstring).
LOGGED_ONLY_STATUSES = frozenset({401})

#: Audit action name for a denied request.
DENIAL_ACTION = "request.denied"

#: Response header a route sets — through ``HTTPException(headers=...)`` — when
#: it has **already** written its own domain-specific denial row (MP-46 uses it
#: for ``queue.display.denied``).  The middleware strips the header before the
#: response reaches the client and skips the generic row, so one denial stays one
#: row (Q-2 §10).  A route that sets it without writing a row would lose the
#: record, which is why the display module only sets it after a successful
#: commit and omits it when the write failed — the denial then falls back to the
#: generic row.
DOMAIN_DENIAL_HEADER = "x-amsdp-denial-audit"

#: A path segment long enough to be a token, uuid or other opaque identifier.
_OPAQUE_SEGMENT = re.compile(r"^[A-Za-z0-9_.~%+-]{20,}$")

_MAX_PATH = 200


def safe_path(path: str) -> str:
    """Return *path* with opaque (token-like) segments redacted.

    Tracking links and entity ids travel in the path.  Writing them into the
    audit trail would copy one tenant's identifiers into a security record that
    outlives the request (Q-2 §8), so any segment that looks like a token, uuid
    or long id is replaced by ``{redacted}``.  The shape of the endpoint — what a
    denial investigation needs — is preserved.
    """
    parts = [_OPAQUE_SEGMENT.sub("{redacted}", part)
             for part in (path or "/").split("/")]
    return ("/".join(parts) or "/")[:_MAX_PATH]


def _header(scope, name: bytes) -> bytes:
    for key, value in scope.get("headers") or []:
        if key.lower() == name:
            return value
    return b""


def _verified_claims(scope) -> dict:
    """Claims of a **verified** bearer token, or ``{}``.

    ``decode_token`` checks the signature and the expiry, so only claims the
    platform itself issued are ever used for attribution.  Nothing about the
    token itself is returned or logged.
    """
    raw = _header(scope, b"authorization").decode("latin-1").strip()
    if not raw.lower().startswith("bearer "):
        return {}
    try:
        claims = decode_token(raw[7:].strip())
    except HTTPException:
        return {}
    except Exception:                                    # pragma: no cover
        return {}
    return claims if isinstance(claims, dict) else {}


def _request_id(scope) -> str:
    return _header(scope, b"x-request-id").decode("latin-1").strip()[:64]


def denial_record(service: str, scope, status: int) -> dict | None:
    """Build the audit payload for one denied request.

    Returns ``None`` when the request cannot be attributed to a tenant (no
    verified token): such a denial goes to the log instead of the database.
    A pure function — it reads the ASGI scope only, which keeps the payload
    trivially testable.
    """
    claims = _verified_claims(scope)
    org_id = (claims.get("org") or "").strip()
    if not org_id:
        return None
    method = (scope.get("method") or "GET").upper()
    path = safe_path(scope.get("path") or "/")
    after = {"status": status}
    request_id = _request_id(scope)
    if request_id:
        after["request_id"] = request_id
    return {
        "service": service,
        "org_id": org_id,
        "branch_id": claims.get("branch") or "",
        "action": DENIAL_ACTION,
        "target_type": "http_request",
        "target_id": f"{method} {path}",
        "actor_id": claims.get("sub") or "",
        "actor_role": claims.get("role") or "",
        "after": after,
        "reason": f"denied status={status}",
    }


def log_denial(service: str, scope, status: int) -> None:
    """Record one denial that cannot be attributed to a tenant, on the log.

    Also used by :func:`record_denial` when a 403/404/422 arrives without a
    verifiable token: the exclusion is always visible somewhere.
    """
    logger.warning(
        "denied request without tenant context: service=%s %s %s status=%s",
        service, (scope.get("method") or "?").upper(),
        safe_path(scope.get("path") or "/"), status)


def record_denial(service: str, scope, status: int) -> None:
    """Persist (or log) one denied request.  Never raises."""
    payload = denial_record(service, scope, status)
    if payload is None:
        log_denial(service, scope, status)
        return
    session = SessionFactory()
    try:
        record_audit(session, **payload)
        session.commit()
    except Exception:
        session.rollback()
        logger.warning(
            "denial audit row could not be written: %s status=%s",
            payload["target_id"], status)
    finally:
        session.close()


class DenialAuditMiddleware:
    """ASGI middleware: persist every 403/404/422 response (Q-2)."""

    def __init__(self, app, service: str):
        self.app = app
        self.service = service

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        status = {"code": 0}
        domain_recorded = {"flag": False}

        async def _send(message):
            if message.get("type") == "http.response.start":
                status["code"] = int(message.get("status") or 0)
                headers = message.get("headers") or []
                marker = DOMAIN_DENIAL_HEADER.encode("latin-1")
                if any(key.lower() == marker for key, _ in headers):
                    # The route already wrote a domain-specific denial row; drop
                    # the marker (it is internal) and do not duplicate it below.
                    domain_recorded["flag"] = True
                    message = dict(message)
                    message["headers"] = [(k, v) for k, v in headers
                                          if k.lower() != marker]
            await send(message)

        await self.app(scope, receive, _send)

        code = status["code"]
        if code in DENIAL_STATUSES and not domain_recorded["flag"]:
            try:
                await run_in_threadpool(record_denial, self.service, scope, code)
            except Exception:                            # pragma: no cover
                logger.warning("denial audit hook failed", exc_info=True)
        elif code in LOGGED_ONLY_STATUSES:
            log_denial(self.service, scope, code)


def install_denial_audit(app, service: str) -> None:
    """Register :class:`DenialAuditMiddleware` on *app* for *service*.

    One call per service, next to ``install_health``, so every backend app —
    including ones added later — records denials the same way.
    """
    app.add_middleware(DenialAuditMiddleware, service=service)
