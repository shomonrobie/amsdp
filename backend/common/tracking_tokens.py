"""AMSDP shared PQT tracking-token helpers (M9-B).

Used by both the appointment service (issue/lookup) and the queuing service
(transactional revocation on consultation start) so token lifecycle stays
consistent across service boundaries.

Security model (Gate 1):
- Raw token: secrets.token_urlsafe(32) → 256-bit entropy, returned once.
- token_hash = hmac_sha256(raw, pepper).hexdigest()  (UNIQUE index).
- Pepper from env AMSDP_TRACKING_PEPPER; never stored in the database.
- Revoked tokens are never reactivated; unknown/revoked are indistinguishable.
"""
import hashlib, hmac, os, secrets
from datetime import datetime, timezone

from .models import TrackingToken


def tracking_pepper() -> bytes:
    pep = os.environ.get("AMSDP_TRACKING_PEPPER")
    if not pep:
        env = os.environ.get("AMSDP_ENV", "development")
        if env != "development":
            raise RuntimeError("AMSDP_TRACKING_PEPPER must be set outside development.")
        pep = "dev-tracking-pepper-not-for-prod"
    return pep.encode()


def token_hash(raw_token: str) -> str:
    return hmac.new(tracking_pepper(), raw_token.encode(), hashlib.sha256).hexdigest()


def generate_raw_token() -> tuple[str, str, str]:
    """Return (raw_token, token_hash, token_prefix)."""
    raw = secrets.token_urlsafe(32)
    return raw, token_hash(raw), raw[:8]


def revoke_for_appointment(session, appointment_id: str, reason: str = ""):
    """Revoke the active tracking token for an appointment.

    Runs inside the caller's session/transaction so revocation is atomic with
    the lifecycle operation that triggers it.
    """
    row = session.query(TrackingToken).filter(
        TrackingToken.appointment_id == appointment_id,
        TrackingToken.status == "active",
    ).first()
    if row:
        row.status = "revoked"
        row.revoked_at = datetime.now(timezone.utc)
    return row