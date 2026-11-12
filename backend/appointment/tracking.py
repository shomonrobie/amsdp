"""AMSDP Personal Queue Tracking (PQT) — M9-B.

Appointment-service endpoints: token issuance, revocation, tracking data, QR.
"""
import hashlib, hmac, json, os, secrets, time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from common.database import SessionFactory
from common.models import TrackingToken, Appointment, Patient, Doctor, Branch, QueueEntry
from common.auth import AuthContext, require_permission
from common.audit import record_audit
from common.tracking_tokens import token_hash, generate_raw_token, revoke_for_appointment

router = APIRouter(prefix="/api/v1", tags=["pqt"])

# ---------------------------------------------------------------------------
# Rate limiting (in-process sliding window; DB-backed bucket deferred to M9-F)
# ---------------------------------------------------------------------------
_RATE: dict[str, list[float]] = {}
_RATE_LIMIT = 10          # requests
_RATE_WINDOW = 60.0       # seconds


def _rate_limited(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    ts = [t for t in _RATE.get(ip, []) if now - t < _RATE_WINDOW]
    if len(ts) >= _RATE_LIMIT:
        raise HTTPException(429, "too many requests")
    ts.append(now)
    _RATE[ip] = ts


_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, private, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


class TrackingCreateResponse(BaseModel):
    tracking_url: str
    token_prefix: str
    created: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _tracking_url(raw_token: str) -> str:
    base = os.environ.get("AMSDP_PUBLIC_BASE_URL", "").rstrip("/")
    if not base:
        base = "http://localhost:3100"
    return f"{base}/track/{raw_token}"


@router.post("/appointments/{appointment_id}/tracking-token", status_code=201)
def issue_tracking_token(
    appointment_id: str,
    auth: AuthContext = Depends(require_permission("appointment.modify")),
):
    """Generate and issue a tracking token for an appointment (staff action).

    The raw token is returned exactly once. If an active token already exists
    we cannot re-expose it, so we return 409. A revoked/expired token can be
    replaced with a fresh one.
    """
    session = SessionFactory()
    try:
        appt = session.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id,
        ).first()
        if not appt:
            raise HTTPException(404, "appointment not found")

        existing = session.query(TrackingToken).filter(
            TrackingToken.appointment_id == appointment_id).first()
        if existing and existing.status == "active":
            raise HTTPException(409, "tracking token already issued")

        raw, thash, prefix = generate_raw_token()
        row = TrackingToken(
            id=str(secrets.token_hex(16)),
            appointment_id=appointment_id,
            token_hash=thash,
            token_prefix=prefix,
            status="active",
            eligible_at=datetime.now(timezone.utc),
        )
        if existing:  # replace revoked/expired
            session.delete(existing)
        session.add(row)
        record_audit(session, service="appointment", org_id=appt.organization_id,
            action="pqt.token_issued", target_type="appointment", target_id=appt.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=appt.branch_id or "",
            after={"token_prefix": prefix})
        session.commit()
        return TrackingCreateResponse(
            tracking_url=_tracking_url(raw),
            token_prefix=prefix,
            created=True,
        ).dict()
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/appointments/{appointment_id}/tracking-token/revoke")
def revoke_tracking_token(
    appointment_id: str,
    auth: AuthContext = Depends(require_permission("appointment.modify")),
):
    """Staff action: manually revoke an appointment's tracking token."""
    session = SessionFactory()
    try:
        appt = session.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.organization_id == auth.organization_id,
        ).first()
        if not appt:
            raise HTTPException(404, "appointment not found")
        row = revoke_for_appointment(session, appointment_id)
        if not row:
            raise HTTPException(404, "no active tracking token")
        record_audit(session, service="appointment", org_id=appt.organization_id,
            action="pqt.token_revoked", target_type="appointment", target_id=appt.id,
            actor_id=auth.user_id, actor_role=auth.role, branch_id=appt.branch_id or "",
            reason="manual staff revocation")
        session.commit()
        return {"revoked": True}
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/track/{token}", dependencies=[Depends(_rate_limited)])
def get_tracking(token: str):
    """Public PQT page data. 404 for unknown AND revoked tokens (indistinguishable)."""
    if not token or len(token) < 32:
        raise HTTPException(404, "not found")
    session = SessionFactory()
    try:
        row = session.query(TrackingToken).filter(
            TrackingToken.token_hash == token_hash(token)).first()
        if not row or row.status != "active":
            raise HTTPException(404, "not found")

        appt = session.query(Appointment).filter(Appointment.id == row.appointment_id).first()
        if not appt:
            raise HTTPException(404, "not found")

        doctor = session.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        branch = session.query(Branch).filter(Branch.id == appt.branch_id).first()

        q = session.query(QueueEntry).filter(
            QueueEntry.organization_id == appt.organization_id,
            QueueEntry.doctor_id == appt.doctor_id,
            QueueEntry.branch_id == appt.branch_id,
            QueueEntry.date == appt.appointment_date,
            QueueEntry.status.in_(["waiting", "called", "in_consultation", "skipped"]),
        ).order_by(QueueEntry.position).all()

        target = next((e for e in q if e.appointment_id == appt.id), None)
        serving = next((e for e in q if e.status in ("in_consultation", "called")), None) \
            or (q[0] if q else None)
        patients_ahead = 0
        my_position = target.position if target else None
        if target:
            patients_ahead = sum(
                1 for e in q
                if e.position < target.position and e.status in ("waiting", "called"))

        avg_mins = int(os.environ.get("AMSDP_AVG_SERVICE_MINUTES", "10"))
        estimated_wait_min = patients_ahead * avg_mins if target else None

        from fastapi.responses import Response
        body = json.dumps({
            "appointment": {
                "id": appt.id,
                "date": str(appt.appointment_date),
                "start_time": appt.start_time or "",
                "status": appt.status,
                "token_number": appt.token_number or "",
            },
            "doctor": {"name": doctor.name if doctor else appt.doctor_id},
            "branch": {"name": branch.name if branch else appt.branch_id},
            "queue": {
                "currently_serving": serving.token if serving else None,
                "my_token": target.token if target else None,
                "my_position": my_position,
                "patients_ahead": patients_ahead,
                "estimated_wait_min": estimated_wait_min,
            },
            "privacy": "This page shows only your appointment.",
        })
        return Response(content=body, media_type="application/json",
                        headers=dict(_NO_CACHE_HEADERS))
    except HTTPException:
        raise
    finally:
        session.close()


@router.get("/track/{token}/qr")
def tracking_qr(token: str):
    """QR code image of the tracking URL (public, token-gated)."""
    if not token or len(token) < 32:
        raise HTTPException(404, "not found")
    session = SessionFactory()
    try:
        row = session.query(TrackingToken).filter(
            TrackingToken.token_hash == token_hash(token)).first()
        if not row or row.status != "active":
            raise HTTPException(404, "not found")
        from fastapi.responses import Response
        from qrcode import QRCode
        from qrcode.constants import ERROR_CORRECT_M
        import io
        qr = QRCode(version=1, error_correction=ERROR_CORRECT_M, box_size=8, border=2)
        qr.add_data(_tracking_url(token))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png",
                        headers=dict(_NO_CACHE_HEADERS))
    except HTTPException:
        raise
    finally:
        session.close()