"""Doctor profile: credentials, photograph, specialities and branch chambers.

AMSDP-FACILITY-DOCTOR-01.  Split out of ``doctor/main.py`` because the doctor
record now carries more than a name and a phone number, and because the rules
below are easier to audit when they live in one place:

* **Canonical mobile numbers.**  Every write path normalises through
  :func:`common.phone.normalize_bd_mobile`, so ``+880 1711-111111`` and
  ``01711111111`` are the same doctor.  An unparseable number is a 422 — the
  service never stores a guess.
* **Registration policy.**  A doctor may always be *recorded*; the
  organization's ``registration_policy`` decides whether that record may be
  *activated* (``bmdc_required``) and whether the number must already be
  *verified* (``bmdc_verification_required``).  Enforcement therefore lives in
  :func:`enforce_activation_policy`, called from every path that can set
  ``status="active"``.
* **Verification is its own axis.**  ``bmdc_verification_status`` answers "is
  this registration checked?"; ``status`` answers "does this doctor work here?".
  Conflating them would make a rejected registration look like a resigned
  doctor and vice versa.
* **One primary branch.**  ``doctor_branches`` has a partial unique index, so
  setting a new primary clears the old one inside the same transaction.

Nothing here trusts a body field for tenancy: the organization always comes from
the authenticated token, and a doctor/branch/speciality outside it is a
non-disclosing 404.
"""

import base64
import binascii
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.audit import record_audit
from common.auth import (
    AuthContext, get_current_user, require_org_access, require_permission,
)
from common.config import (doctor_mobile_must_be_unique,
                           get_doctor_mobile_policy, get_registration_policy,
                           merge_doctor_mobile_policy)
from common.database import SessionFactory
from common.models import (
    Branch, Doctor, DoctorBranch, DoctorSpecialty, FacilityRoom, Organization,
    Specialty,
)
from common.phone import InvalidMobileNumber, normalize_bd_mobile

router = APIRouter()

SERVICE = "doctor"

#: Decoded photograph cap.  The bytes are stored inline in the row, so this is
#: also a row-size cap: 300 KB of JPEG is ~400 KB of base64 text.
PHOTO_MAX_BYTES = 300 * 1024

#: Accepted image types.  ``image/svg+xml`` is deliberately absent: an SVG is a
#: script container, and this photo is rendered straight into an ``<img>``.
PHOTO_MIMES = ("image/jpeg", "image/png", "image/webp")

#: BMDC verification states (see ``Doctor.bmdc_verification_status``).
BMDC_STATUSES = ("unverified", "pending_verification", "verified", "rejected")

#: Permitted verification transitions.  ``verified`` may only be revoked to
#: ``rejected`` (a withdrawn registration), never silently reset to unverified.
BMDC_TRANSITIONS = {
    "unverified": ("pending_verification", "verified", "rejected"),
    "pending_verification": ("verified", "rejected"),
    "verified": ("rejected",),
    "rejected": ("pending_verification", "verified"),
}

#: Assignment states accepted by :class:`BranchAssignmentCreate`.
ASSIGNMENT_STATUSES = ("active", "inactive")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PhotoUpload(BaseModel):
    """Inline photograph body (base64) with its declared MIME type."""
    photo_base64: str
    mime_type: str = "image/jpeg"


class SpecialtyLinkCreate(BaseModel):
    specialty_ids: list[str] = []


class BranchAssignmentCreate(BaseModel):
    branch_id: str
    room_id: Optional[str] = None
    consultation_fee_override: Optional[float] = None
    is_primary: bool = False
    status: str = "active"


class BranchAssignmentUpdate(BaseModel):
    room_id: Optional[str] = None
    consultation_fee_override: Optional[float] = None
    is_primary: Optional[bool] = None
    status: Optional[str] = None


class BmdcVerificationUpdate(BaseModel):
    status: str
    note: str = ""


class RegistrationPolicyUpdate(BaseModel):
    bmdc_required: Optional[bool] = None
    bmdc_verification_required: Optional[bool] = None


class DoctorMobilePolicyUpdate(BaseModel):
    """BR §9.7 — whether an organization tolerates two doctors on one number."""

    allow_duplicate_mobile: Optional[bool] = None


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def doctor_dict(d: Doctor) -> dict:
    """The canonical doctor payload.

    ``branch_ids`` is kept because existing callers (and the booking UI) read
    it; ``branches`` adds the chamber/fee/primary detail that the redesigned
    doctor screen needs.  The photograph itself is never inlined here — a list
    of 50 doctors would otherwise carry 50 images — only ``has_photo``.

    **Only active assignments are part of this contract** (owner decision C,
    2026-11-23).  A retired or legacy ``doctor_branches`` row is *preserved* in
    the database — the row carries the chamber an appointment was booked into,
    so deleting it would orphan that history — but it is not something the
    doctor currently works in, and serialising it made ``PATCH`` with
    ``branch_ids: []`` answer with a branch the caller had just removed.  The
    rows are still there for history and for re-adding a branch (which
    reactivates the existing row); they simply do not appear in the payload.
    """
    all_assignments = list(d.branch_assignments or [])
    assignments = [a for a in all_assignments
                   if (a.status or "active") == "active"]
    assignments.sort(key=lambda a: (not a.is_primary,
                                    a.branch.name if a.branch else ""))
    links = list(d.specialty_links or [])
    links.sort(key=lambda l: (l.specialty.sort_order if l.specialty else 0,
                              l.specialty.name_en if l.specialty else ""))
    primary = next((a for a in assignments if a.is_primary), None)
    return {
        "id": d.id,
        "organization_id": d.organization_id,
        "name": d.name,
        "mobile": d.mobile,
        "speciality": d.speciality or "",
        "qualification": d.qualification or "",
        "registration_number": d.registration_number or "",
        "bmdc_verification_status": (
            d.bmdc_verification_status or "unverified"),
        "bmdc_verified_at": str(d.bmdc_verified_at) if d.bmdc_verified_at else "",
        "has_photo": bool(d.photo_base64),
        "photo_mime": d.photo_mime or "",
        "photo_updated_at": str(d.photo_updated_at) if d.photo_updated_at else "",
        "consultation_fee": d.consultation_fee,
        "locale": d.locale or "bn",
        "status": d.status or "active",
        "branch_ids": [a.branch_id for a in assignments],
        "primary_branch_id": primary.branch_id if primary else None,
        "branches": [{
            "id": a.id,
            "branch_id": a.branch_id,
            "branch_name": a.branch.name if a.branch else "",
            "room_id": a.room_id,
            "room_name": a.room.name if a.room else "",
            "consultation_fee_override": a.consultation_fee_override,
            "is_primary": bool(a.is_primary),
            "status": a.status or "active",
        } for a in assignments],
        "specialty_ids": [l.specialty_id for l in links],
        "specialties": [{
            "id": l.specialty_id,
            "code": l.specialty.code if l.specialty else "",
            "name_en": l.specialty.name_en if l.specialty else "",
            "name_bn": (l.specialty.name_bn or "") if l.specialty else "",
        } for l in links],
        "created_at": str(d.created_at) if d.created_at else "",
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def clean_mobile(value) -> str:
    """Normalise to ``01XXXXXXXXX`` or answer 422 (never store a guess)."""
    try:
        return normalize_bd_mobile(value)
    except InvalidMobileNumber as exc:
        raise HTTPException(422, str(exc))


def _audit(session, auth: AuthContext, action: str, target_id: str,
           org_id: str, branch_id: Optional[str] = None, before=None,
           after=None, reason: str = "") -> None:
    record_audit(session, service=SERVICE, org_id=org_id,
                 action=action, target_type="doctor", target_id=target_id,
                 actor_id=auth.user_id, actor_role=auth.role,
                 branch_id=branch_id or "", before=before, after=after,
                 reason=reason)


def scoped_doctor(session, auth: AuthContext, doctor_id: str) -> Doctor:
    """The doctor row, or a 404.

    A doctor in another organization is indistinguishable from one that does
    not exist — the query is scoped, the caller is never told which.
    """
    doctor = session.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.organization_id == auth.organization_id).first()
    if not doctor:
        raise HTTPException(404, "not found")
    return doctor


def organization_row(session, org_id: str) -> Organization:
    org = session.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(404, "not found")
    return org


def mobile_in_use(session, organization_id: str, mobile: str,
                  exclude_doctor_id: Optional[str] = None) -> Optional[Doctor]:
    """The other doctor in *organization_id* already registered on *mobile*.

    Scoped by organization on purpose: BR §9.8 allows the same number at a
    different facility, so a cross-tenant match is not a duplicate and is never
    looked for.
    """
    query = session.query(Doctor).filter(
        Doctor.organization_id == organization_id,
        Doctor.mobile == mobile)
    if exclude_doctor_id:
        query = query.filter(Doctor.id != exclude_doctor_id)
    return query.first()


def assert_mobile_available(session, org: Optional[Organization],
                            organization_id: str, mobile: str,
                            exclude_doctor_id: Optional[str] = None) -> None:
    """Refuse a second doctor on one number *unless the organization allows it*.

    BR §9.6 makes "one doctor per mobile number" the default **within** the
    organization; BR §9.7 lets a platform administrator lift that per
    organization (``common.config.doctor_mobile_policy``).  ``org`` may be
    ``None`` — a caller that has not loaded the row, or a pre-migration state —
    and the default then applies, so a missing configuration can only ever make
    the check stricter.

    BR §9.8 is unaffected by the switch: the lookup never leaves the tenant, so
    the same number is always free at another facility.
    """
    if not doctor_mobile_must_be_unique(
            org.config if org is not None else None):
        return
    if mobile_in_use(session, organization_id, mobile, exclude_doctor_id):
        raise HTTPException(
            409, "a doctor with this mobile number already exists")


def enforce_activation_policy(session, doctor: Doctor,
                              org: Optional[Organization]) -> None:
    """Refuse to activate a doctor the organization's policy does not allow.

    Called from every path that can set ``status="active"`` — creation,
    update, and branch re-activation — so the rule cannot be bypassed by
    picking a different endpoint.  A **rejected** registration is refused even
    when ``bmdc_required`` is off: the number was checked and found invalid.
    """
    if (doctor.status or "active") != "active":
        return
    if (doctor.bmdc_verification_status or "unverified") == "rejected":
        raise HTTPException(
            422, "cannot activate a doctor whose BMDC registration was rejected")
    policy = get_registration_policy(org.config if org is not None else None)
    if policy["bmdc_required"] and not (doctor.registration_number or "").strip():
        raise HTTPException(
            422, "BMDC registration number is required before this doctor "
                 "can be active (organization registration policy)")
    if (policy["bmdc_verification_required"]
            and (doctor.bmdc_verification_status or "unverified") != "verified"):
        raise HTTPException(
            422, "BMDC registration must be verified before this doctor can be "
                 "active (organization registration policy)")


def _branch_in_org(session, org_id: str, branch_id: str) -> Branch:
    branch = session.query(Branch).filter(
        Branch.id == branch_id,
        Branch.organization_id == org_id).first()
    if not branch:
        raise HTTPException(422, "branch not found in this organization")
    return branch


def room_in_branch(session, org_id: str, branch_id: str,
                   room_id: str) -> FacilityRoom:
    """A chamber must exist, belong to this organization *and* this branch."""
    room = session.query(FacilityRoom).filter(
        FacilityRoom.id == room_id,
        FacilityRoom.organization_id == org_id).first()
    if not room:
        raise HTTPException(422, "room not found in this organization")
    if room.branch_id != branch_id:
        raise HTTPException(422, "room does not belong to this branch")
    if (room.status or "active") != "active":
        raise HTTPException(422, "room is retired; choose an active room")
    return room


def clear_other_primaries(session, doctor_id: str, keep_id: str = None) -> None:
    """Demote every other primary assignment of *doctor_id*."""
    query = session.query(DoctorBranch).filter(
        DoctorBranch.doctor_id == doctor_id,
        DoctorBranch.is_primary.is_(True))
    if keep_id:
        query = query.filter(DoctorBranch.id != keep_id)
    for row in query.all():
        row.is_primary = False


def replace_branch_assignments(session, doctor: Doctor, branch_ids,
                               org_id: str,
                               primary_branch_id: str = None) -> None:
    """Make the doctor's assignments exactly *branch_ids*.

    Rows are **retired, never deleted**: an assignment carries the chamber an
    appointment was booked into, and deleting it would orphan that history.
    Re-adding a branch reactivates its existing row instead of inserting a
    duplicate (``uq_doctor_branch``).
    """
    wanted = []
    for branch_id in (branch_ids or []):
        if branch_id and branch_id not in wanted:
            wanted.append(branch_id)      # a repeated id is not two assignments
    for branch_id in wanted:
        _branch_in_org(session, org_id, branch_id)
    existing = {a.branch_id: a for a in session.query(DoctorBranch).filter(
        DoctorBranch.doctor_id == doctor.id).all()}
    for branch_id in wanted:
        row = existing.get(branch_id)
        if row is None:
            session.add(DoctorBranch(
                doctor_id=doctor.id, branch_id=branch_id, is_primary=False,
                status="active"))
        elif (row.status or "active") != "active":
            row.status = "active"
    for branch_id, row in existing.items():
        if branch_id not in wanted:
            row.status = "inactive"
            row.is_primary = False
    session.flush()
    active = session.query(DoctorBranch).filter(
        DoctorBranch.doctor_id == doctor.id,
        DoctorBranch.status == "active").all()
    active.sort(key=lambda a: a.branch_id)
    target = primary_branch_id if any(
        a.branch_id == primary_branch_id for a in active) else None
    if target is None and active and not any(a.is_primary for a in active):
        target = active[0].branch_id   # deterministic: one primary per doctor
    if target is None:
        # See the reload note at the end of the function.
        session.expire(doctor, ["branch_assignments"])
        return
    # Demote first and flush, or the partial unique index would see two
    # primaries in a single UPDATE batch.
    for row in active:
        if row.is_primary and row.branch_id != target:
            row.is_primary = False
    session.flush()
    for row in active:
        row.is_primary = (row.branch_id == target)
    session.flush()
    # The assignments are written through the session, not through the
    # relationship, and this application's session factory does not expire
    # attributes on commit.  A caller that already serialised the doctor (the
    # ``before`` half of the audit record does) would otherwise keep reading
    # the pre-mutation collection — omitting a branch that was just added.
    session.expire(doctor, ["branch_assignments"])


def set_specialties(session, doctor: Doctor, specialty_ids,
                    org_id: str) -> None:
    """Replace the doctor's structured specialities and refresh the text copy."""
    ids = []
    for specialty_id in (specialty_ids or []):
        if specialty_id and specialty_id not in ids:
            ids.append(specialty_id)
    if ids:
        found = {row.id for row in session.query(Specialty).filter(
            Specialty.id.in_(ids),
            Specialty.organization_id == org_id).all()}
        if len(found) != len(ids):
            raise HTTPException(
                422, "specialty not found in this organization")
    session.query(DoctorSpecialty).filter(
        DoctorSpecialty.doctor_id == doctor.id).delete(synchronize_session=False)
    session.flush()
    for specialty_id in ids:
        session.add(DoctorSpecialty(doctor_id=doctor.id,
                                    specialty_id=specialty_id))
    session.flush()
    sync_speciality_text(session, doctor)
    refresh_specialty_links(session, doctor)


def sync_speciality_text(session, doctor: Doctor) -> None:
    """Mirror the structured specialities into ``doctors.speciality``.

    The free-text column stays authoritative only for doctors that have no
    structured links (legacy rows), so the existing search filter and the
    printed slip keep working without a second query.
    """
    links = session.query(DoctorSpecialty).filter(
        DoctorSpecialty.doctor_id == doctor.id).all()
    names = [l.specialty.name_en for l in links if l.specialty is not None]
    if names:
        doctor.speciality = ", ".join(names)[:100]


def refresh_specialty_links(session, doctor: Doctor) -> None:
    """Reload ``doctor.specialty_links`` from the database.

    Links are written through the session, not through the relationship, and
    this application's session factory does not expire attributes on commit
    (``expire_on_commit=False``).  Without this reload the loaded collection
    would keep answering with the pre-mutation rows — to the response body and
    to the audit record alike.
    """
    session.expire(doctor, ["specialty_links"])


# ---------------------------------------------------------------------------
# Photograph
# ---------------------------------------------------------------------------

#: Leading bytes of the accepted image formats, so a ``.pdf`` renamed to
#: ``.jpg`` (or a script labelled ``image/png``) is refused on content, not only
#: on its declared type.
_PHOTO_MAGIC = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}


def _decode_photo(payload: str, mime: str):
    """Validate an inline photograph and return ``(base64, mime)``."""
    declared = (mime or "").strip().lower()
    data = (payload or "").strip()
    if data.startswith("data:"):
        header, _, data = data.partition(",")
        if ";base64" not in header:
            raise HTTPException(422, "data URL must be base64 encoded")
        inline = header[5:].split(";")[0].strip().lower()
        if inline:
            declared = inline
    if declared not in PHOTO_MIMES:
        raise HTTPException(
            422, "unsupported image type; upload JPEG, PNG or WebP")
    if not data:
        raise HTTPException(422, "photo_base64 is required")
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "photo_base64 is not valid base64")
    if not raw:
        raise HTTPException(422, "photo_base64 is empty")
    if len(raw) > PHOTO_MAX_BYTES:
        raise HTTPException(
            413, f"photo must be at most {PHOTO_MAX_BYTES // 1024} KB")
    if not any(raw.startswith(sig) for sig in _PHOTO_MAGIC[declared]):
        raise HTTPException(
            422, "photo content does not match its declared image type")
    if declared == "image/webp" and raw[8:12] != b"WEBP":
        raise HTTPException(
            422, "photo content does not match its declared image type")
    return base64.b64encode(raw).decode("ascii"), declared


@router.post("/api/v1/doctors/{doctor_id}/photo")
def upload_photo(
    doctor_id: str, data: PhotoUpload,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Replace the doctor's photograph.

    The bytes live in the row (no object store exists here) and are served by
    :func:`get_photo`; they are never echoed back by the doctor list.
    """
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        encoded, mime = _decode_photo(data.photo_base64, data.mime_type)
        doctor.photo_base64 = encoded
        doctor.photo_mime = mime
        doctor.photo_updated_at = datetime.now(timezone.utc)
        _audit(session, auth, "doctor.photo.update", doctor.id,
               doctor.organization_id,
               after={"photo_mime": mime, "photo_bytes": len(encoded)})
        session.commit()
        return {"doctor_id": doctor.id, "has_photo": True,
                "photo_mime": mime,
                "photo_updated_at": str(doctor.photo_updated_at)}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/api/v1/doctors/{doctor_id}/photo")
def get_photo(
    doctor_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    """The photograph as a base64 data payload, for ``<img src=...>``."""
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        if not doctor.photo_base64:
            raise HTTPException(404, "not found")
        return {
            "doctor_id": doctor.id,
            "mime_type": doctor.photo_mime or "image/jpeg",
            "photo_base64": doctor.photo_base64,
            "photo_updated_at": (str(doctor.photo_updated_at)
                                 if doctor.photo_updated_at else ""),
        }
    finally:
        session.close()


@router.delete("/api/v1/doctors/{doctor_id}/photo")
def delete_photo(
    doctor_id: str,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        had = bool(doctor.photo_base64)
        doctor.photo_base64 = None
        doctor.photo_mime = None
        doctor.photo_updated_at = None
        if had:
            _audit(session, auth, "doctor.photo.delete", doctor.id,
                   doctor.organization_id, before={"had_photo": True})
        session.commit()
        return {"doctor_id": doctor.id, "has_photo": False}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Structured specialities
# ---------------------------------------------------------------------------

def _specialty_link_dict(link) -> dict:
    return {
        "id": link.specialty_id,
        "code": link.specialty.code if link.specialty else "",
        "name_en": link.specialty.name_en if link.specialty else "",
        "name_bn": (link.specialty.name_bn or "") if link.specialty else "",
        "sort_order": link.specialty.sort_order if link.specialty else 0,
    }


@router.get("/api/v1/doctors/{doctor_id}/specialties")
def list_specialties(
    doctor_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        items = sorted((_specialty_link_dict(l) for l in doctor.specialty_links),
                       key=lambda s: (s["sort_order"], s["name_en"]))
        return {"items": items, "total": len(items)}
    finally:
        session.close()


@router.post("/api/v1/doctors/{doctor_id}/specialties", status_code=201)
def add_specialties(
    doctor_id: str, data: SpecialtyLinkCreate,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Add one or more structured specialities (an existing link is a no-op)."""
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        wanted = [s for s in (data.specialty_ids or []) if s]
        if not wanted:
            raise HTTPException(422, "specialty_ids is required")
        found = {row.id for row in session.query(Specialty).filter(
            Specialty.id.in_(wanted),
            Specialty.organization_id == doctor.organization_id).all()}
        missing = [s for s in wanted if s not in found]
        if missing:
            raise HTTPException(422, "specialty not found in this organization")
        current = {l.specialty_id for l in doctor.specialty_links}
        added = [s for s in dict.fromkeys(wanted) if s not in current]
        for specialty_id in added:
            session.add(DoctorSpecialty(doctor_id=doctor.id,
                                        specialty_id=specialty_id))
        session.flush()
        sync_speciality_text(session, doctor)
        if added:
            _audit(session, auth, "doctor.specialty.add", doctor.id,
                   doctor.organization_id, after={"specialty_ids": added})
        session.commit()
        refresh_specialty_links(session, doctor)
        items = sorted((_specialty_link_dict(l) for l in doctor.specialty_links),
                       key=lambda s: (s["sort_order"], s["name_en"]))
        return {"items": items, "total": len(items), "added": len(added)}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/doctors/{doctor_id}/specialties/{specialty_id}")
def remove_specialty(
    doctor_id: str, specialty_id: str,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        link = session.query(DoctorSpecialty).filter(
            DoctorSpecialty.doctor_id == doctor.id,
            DoctorSpecialty.specialty_id == specialty_id).first()
        if not link:
            raise HTTPException(404, "not found")
        session.delete(link)
        session.flush()
        sync_speciality_text(session, doctor)
        _audit(session, auth, "doctor.specialty.remove", doctor.id,
               doctor.organization_id, before={"specialty_id": specialty_id})
        session.commit()
        refresh_specialty_links(session, doctor)
        items = sorted((_specialty_link_dict(l) for l in doctor.specialty_links),
                       key=lambda s: (s["sort_order"], s["name_en"]))
        return {"items": items, "total": len(items)}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.put("/api/v1/doctors/{doctor_id}/specialties")
def replace_specialties(
    doctor_id: str, data: SpecialtyLinkCreate,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Set the doctor's specialities to exactly *specialty_ids*."""
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        before = [l.specialty_id for l in doctor.specialty_links]
        set_specialties(session, doctor, data.specialty_ids,
                        doctor.organization_id)
        after = [l.specialty_id for l in doctor.specialty_links]
        if sorted(before) != sorted(after):
            _audit(session, auth, "doctor.specialty.set", doctor.id,
                   doctor.organization_id, before={"specialty_ids": before},
                   after={"specialty_ids": after})
        session.commit()
        items = sorted((_specialty_link_dict(l) for l in doctor.specialty_links),
                       key=lambda s: (s["sort_order"], s["name_en"]))
        return {"items": items, "total": len(items)}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()





# ---------------------------------------------------------------------------
# Branch assignments (multi-branch + default chamber + fee override)
# ---------------------------------------------------------------------------

def assignment_dict(assignment) -> dict:
    return {
        "id": assignment.id,
        "doctor_id": assignment.doctor_id,
        "branch_id": assignment.branch_id,
        "branch_name": assignment.branch.name if assignment.branch else "",
        "room_id": assignment.room_id,
        "room_name": assignment.room.name if assignment.room else "",
        "consultation_fee_override": assignment.consultation_fee_override,
        "is_primary": bool(assignment.is_primary),
        "status": assignment.status or "active",
        "created_at": (str(assignment.created_at)
                       if assignment.created_at else ""),
    }


def _assignment_or_404(session, doctor: Doctor, assignment_id: str):
    assignment = session.query(DoctorBranch).filter(
        DoctorBranch.id == assignment_id,
        DoctorBranch.doctor_id == doctor.id).first()
    if not assignment:
        raise HTTPException(404, "not found")
    return assignment


def promote_primary(session, doctor: Doctor) -> None:
    """Give a doctor with active branches exactly one primary."""
    active = session.query(DoctorBranch).filter(
        DoctorBranch.doctor_id == doctor.id,
        DoctorBranch.status == "active").all()
    active.sort(key=lambda a: a.branch_id)
    if not active or any(a.is_primary for a in active):
        return
    active[0].is_primary = True
    session.flush()


@router.get("/api/v1/doctors/{doctor_id}/branches")
def list_branch_assignments(
    doctor_id: str,
    auth: AuthContext = Depends(get_current_user),
):
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        items = list(doctor_dict(doctor)["branches"])
        return {"items": items, "total": len(items)}
    finally:
        session.close()


@router.post("/api/v1/doctors/{doctor_id}/branches", status_code=201)
def create_branch_assignment(
    doctor_id: str, data: BranchAssignmentCreate,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Assign the doctor to another branch, optionally with a chamber.

    Re-assigning a branch that was previously retired reactivates the original
    row (``uq_doctor_branch`` makes a second row impossible), so the chamber and
    fee override that branch already carried are preserved.
    """
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        if (data.status or "active") not in ASSIGNMENT_STATUSES:
            raise HTTPException(422, "status must be active or inactive")
        branch = _branch_in_org(session, doctor.organization_id, data.branch_id)
        if data.room_id:
            room_in_branch(session, doctor.organization_id, branch.id,
                           data.room_id)
        assignment = session.query(DoctorBranch).filter(
            DoctorBranch.doctor_id == doctor.id,
            DoctorBranch.branch_id == branch.id).first()
        if assignment is not None and (
                assignment.status or "active") == "active":
            raise HTTPException(409, "doctor is already assigned to this branch")
        if assignment is None:
            assignment = DoctorBranch(doctor_id=doctor.id, branch_id=branch.id)
            session.add(assignment)
        assignment.status = data.status or "active"
        if data.room_id is not None:
            assignment.room_id = data.room_id or None
        if data.consultation_fee_override is not None:
            assignment.consultation_fee_override = data.consultation_fee_override
        session.flush()
        if data.is_primary:
            clear_other_primaries(session, doctor.id, keep_id=assignment.id)
            session.flush()
            assignment.is_primary = True
        promote_primary(session, doctor)
        payload = assignment_dict(assignment)
        _audit(session, auth, "doctor.branch.assign", doctor.id,
               doctor.organization_id, branch_id=branch.id, after=payload)
        session.commit()
        return payload
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@router.patch("/api/v1/doctors/{doctor_id}/branches/{assignment_id}")
def update_branch_assignment(
    doctor_id: str, assignment_id: str, data: BranchAssignmentUpdate,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        assignment = _assignment_or_404(session, doctor, assignment_id)
        before = assignment_dict(assignment)
        if data.status is not None:
            if data.status not in ASSIGNMENT_STATUSES:
                raise HTTPException(422, "status must be active or inactive")
            assignment.status = data.status
        if data.room_id is not None:
            if data.room_id:
                room_in_branch(session, doctor.organization_id,
                               assignment.branch_id, data.room_id)
                assignment.room_id = data.room_id
            else:
                assignment.room_id = None
        if data.consultation_fee_override is not None:
            assignment.consultation_fee_override = data.consultation_fee_override
        session.flush()
        if data.is_primary is True:
            clear_other_primaries(session, doctor.id, keep_id=assignment.id)
            session.flush()
            assignment.is_primary = True
        elif data.is_primary is False:
            assignment.is_primary = False
            session.flush()
        if (assignment.status or "active") != "active":
            assignment.is_primary = False
            session.flush()
        promote_primary(session, doctor)
        after = assignment_dict(assignment)
        if before != after:
            _audit(session, auth, "doctor.branch.update", doctor.id,
                   doctor.organization_id, branch_id=assignment.branch_id,
                   before=before, after=after)
        session.commit()
        return after
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.delete("/api/v1/doctors/{doctor_id}/branches/{assignment_id}")
def retire_branch_assignment(
    doctor_id: str, assignment_id: str,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Retire the assignment; the row stays so booking history keeps its link."""
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        assignment = _assignment_or_404(session, doctor, assignment_id)
        before = assignment_dict(assignment)
        assignment.status = "inactive"
        assignment.is_primary = False
        session.flush()
        promote_primary(session, doctor)
        after = assignment_dict(assignment)
        _audit(session, auth, "doctor.branch.retire", doctor.id,
               doctor.organization_id, branch_id=assignment.branch_id,
               before=before, after=after)
        session.commit()
        return after
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# BMDC verification and the organization's registration policy
# ---------------------------------------------------------------------------

@router.post("/api/v1/doctors/{doctor_id}/verification")
def set_verification(
    doctor_id: str, data: BmdcVerificationUpdate,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """Record the outcome of a BMDC registration check.

    This is a *record of a human check*, not an automated lookup: nothing here
    contacts BMDC, so the endpoint demands an explicit status and keeps the
    reason.  ``verified`` stamps ``bmdc_verified_at``; every other target clears
    it, so a stale timestamp can never imply a current verification.
    """
    session = SessionFactory()
    try:
        doctor = scoped_doctor(session, auth, doctor_id)
        target = (data.status or "").strip()
        if target not in BMDC_STATUSES:
            raise HTTPException(
                422, "status must be one of " + ", ".join(BMDC_STATUSES))
        current = doctor.bmdc_verification_status or "unverified"
        if target != current and target not in BMDC_TRANSITIONS.get(current, ()):
            raise HTTPException(
                422, f"cannot move verification from {current} to {target}")
        if target in ("pending_verification", "verified") and not (
                doctor.registration_number or "").strip():
            raise HTTPException(
                422, "record the BMDC registration number before verification")
        before = {"bmdc_verification_status": current,
                  "bmdc_verified_at": (str(doctor.bmdc_verified_at)
                                       if doctor.bmdc_verified_at else "")}
        doctor.bmdc_verification_status = target
        doctor.bmdc_verified_at = (
            datetime.now(timezone.utc) if target == "verified" else None)
        _audit(session, auth, "doctor.verification.update", doctor.id,
               doctor.organization_id, before=before,
               after={"bmdc_verification_status": target},
               reason=(data.note or "").strip())
        session.commit()
        return doctor_dict(doctor)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/api/v1/orgs/{org_id}/registration-policy")
def read_registration_policy(
    org_id: str,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """The organization's doctor registration policy (defaults when unset)."""
    require_org_access(org_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        row = organization_row(session, org_id)
        return {"organization_id": row.id,
                "registration_policy": get_registration_policy(row.config)}
    finally:
        session.close()

@router.patch("/api/v1/orgs/{org_id}/registration-policy")
def update_registration_policy(
    org_id: str, data: RegistrationPolicyUpdate,
    auth: AuthContext = Depends(require_permission("org.manage")),
):
    """Change whether an active doctor must carry (a verified) BMDC number.

    Organization configuration, so it is gated on ``org.manage`` — a branch
    administrator may register doctors but cannot decide this for the tenant.
    Loosening the policy never un-verifies an existing doctor and tightening it
    silently deactivates nobody; it only blocks *future* activations.
    """
    require_org_access(org_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        row = organization_row(session, org_id)
        before = get_registration_policy(row.config)
        after = dict(before)
        if data.bmdc_required is not None:
            after["bmdc_required"] = bool(data.bmdc_required)
        if data.bmdc_verification_required is not None:
            after["bmdc_verification_required"] = bool(
                data.bmdc_verification_required)
        config = dict(row.config or {})
        config["registration_policy"] = after
        row.config = config
        _audit(session, auth, "organization.registration_policy.update",
               row.id, row.id, before=before, after=after)
        session.commit()
        return {"organization_id": row.id, "registration_policy": after}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/api/v1/orgs/{org_id}/doctor-mobile-policy")
def read_doctor_mobile_policy(
    org_id: str,
    auth: AuthContext = Depends(require_permission("doctor.manage")),
):
    """The organization's doctor mobile-number duplicate policy (BR §9.6–§9.7).

    Read access for anyone who may register doctors, because the answer decides
    whether the create form should warn about a repeat number *before* the save
    is attempted; the 409 remains the authority either way.
    """
    require_org_access(org_id, service=SERVICE)(auth)
    session = SessionFactory()
    try:
        row = organization_row(session, org_id)
        return {"organization_id": row.id,
                "doctor_mobile_policy": get_doctor_mobile_policy(row.config)}
    finally:
        session.close()


@router.patch("/api/v1/orgs/{org_id}/doctor-mobile-policy")
def update_doctor_mobile_policy(
    org_id: str, data: DoctorMobilePolicyUpdate,
    auth: AuthContext = Depends(require_permission("org.manage")),
):
    """Allow, or stop allowing, two doctors on one mobile number (BR §9.7).

    **Only a platform administrator may change it.**  BR §9.7 names the Super
    Admin, not the facility — the allowance is a platform-level exception the
    facility is *given*, not one it can grant itself.  That is enforced here
    rather than by omitting the route, because a 403 that says why is more
    useful to an auditor than a 404 that pretends the setting does not exist.
    Withdrawing the allowance is the conservative direction, but it is the same
    switch: one rule is easier to hold than two.

    **Prospective only.**  No doctor row is created, merged or removed; the
    setting decides whether the next colliding write is a 409.  Existing
    duplicates survive a withdrawal because appointments and the append-only
    audit trail point at those rows.
    """
    require_org_access(org_id, service=SERVICE)(auth)
    if not getattr(auth, "is_super_admin", False):
        raise HTTPException(
            403, "only a platform administrator may change the doctor "
                 "mobile-number duplicate policy")
    if data.allow_duplicate_mobile is None:
        raise HTTPException(422, "no changes supplied")
    session = SessionFactory()
    try:
        row = organization_row(session, org_id)
        before = get_doctor_mobile_policy(row.config)
        merged = merge_doctor_mobile_policy(
            row.config, {"allow_duplicate_mobile":
                         bool(data.allow_duplicate_mobile)})
        merged["doctor_mobile_policy"]["updated_at"] = datetime.now(
            timezone.utc).isoformat()
        merged["doctor_mobile_policy"]["updated_by"] = auth.user_id
        row.config = merged
        after = get_doctor_mobile_policy(merged)
        # target_type is "organization": the row that changed is the tenant's
        # configuration, not a doctor.  (The sibling registration-policy route
        # records under "doctor"; this one states what actually moved.)
        record_audit(session, service=SERVICE, org_id=row.id,
                     action="organization.doctor_mobile_policy.update",
                     target_type="organization", target_id=row.id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason="doctor mobile-number duplicate allowance")
        session.commit()
        return {"organization_id": row.id, "doctor_mobile_policy": after}
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
