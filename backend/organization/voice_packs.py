"""QUE-006 / W3 — the versioned voice-pack registry (storage and API).

The rules live in :mod:`organization.voice_pack_policy`, which is dependency-free
and unit-tested; this module is the thin layer that persists packs, writes their
assets and exposes them over HTTP.  Keeping the two apart is deliberate: the
policy answers "may this happen?", so it can be proven without a database, and
the router only decides *where* to store the answer.

Owner decisions implemented here (assignment §3.2, §3.3, §7):

* a **platform** pack (``organization_id`` NULL) is created, validated, approved,
  published, retired and released to tenants by ``super_admin`` only;
* an **organisation** pack belongs to one organisation and is reachable by that
  organisation and the platform administrator; anyone else gets a non-disclosing
  404;
* a version is **never overwritten** once approved or published — new content is
  a new row with the next version number, so a rollback target always exists;
* nothing becomes selectable because an upload succeeded: publication needs a
  passing technical validation *and* a named human reviewer;
* ``available_to_organizations`` is the platform's control over which published
  packs a tenant may choose; a withheld platform pack is invisible to tenants;
* assets are written under ``AMSDP_VOICE_PACK_ROOT`` (default
  ``backend/var/voice-packs``) at a path validated by the policy layer, and are
  served back only through an authenticated route — an organisation pack is never
  a public URL, and no filesystem path is ever returned to a client.
"""

import os
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        JSON, String, Text, UniqueConstraint)

from common.audit import record_audit, record_platform_audit
from common.auth import AuthContext, require_permission
from common.database import Base, SessionFactory

# TRIAL MERGE / acceptance-readiness (2026-11-23): the container layout is the runtime truth.
# `organization/Dockerfile` copies `organization/` into `/app` and runs `uvicorn main:app`, so
# `main.py` is a *top-level* module there: an unguarded relative import (`from . import x`) raises
# "attempted relative import with no known parent package" at start-up and the whole organisation
# service — including this W3 API — never comes up. `main.py` has always guarded its own router
# imports (`try: from .x import … / except ImportError: from x import …`); this module now does
# the same. Behaviour, routes and payloads are unchanged: only the import spelling differs
# between the package layout (tests) and the flat layout (the image).
try:                                     # package layout: `organization.main` (tests)
    from . import voice_pack_policy as policy
except ImportError:                      # flat layout: `uvicorn main:app` in the image
    import voice_pack_policy as policy

router = APIRouter(prefix="/api/v1/voice-packs", tags=["voice-packs"])

#: Where uploaded pack assets live.  Outside the web root on purpose: an
#: organisation's audio must not be reachable by guessing a static URL.
PACK_ROOT = os.environ.get("AMSDP_VOICE_PACK_ROOT") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "var", "voice-packs")


class VoicePack(Base):
    """One version of one voice persona, platform-wide or per organisation.

    The primary key is the version's own identifier (``platform-en-female-1``),
    which is also the directory name used for its assets and the ``packId`` the
    W5 installer receives.  ``voice_name`` groups the versions of one persona so
    ``next_version`` can never reuse a number.
    """

    __tablename__ = "voice_packs"
    __service__ = "organization"

    id = Column(String(80), primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"),
                             nullable=True)
    language = Column(String(8), nullable=False)
    voice_name = Column(String(80), nullable=False)
    description = Column(Text, default="")
    personality = Column(String(80), default="")
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="draft")
    base_path = Column(String(200), default="")
    manifest = Column(JSON, default=dict)
    manifest_checksum = Column(String(64), default="")
    compatibility = Column(JSON, default=dict)
    available_to_organizations = Column(Boolean, nullable=False, default=False)
    validation_status = Column(String(16), nullable=False, default="unvalidated")
    validation_problems = Column(JSON, default=list)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    review_status = Column(String(16), nullable=False, default="pending")
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, default="")
    published_by = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "language", "voice_name", "version",
                         name="voice_packs_scope_language_voice_version_key"),
        Index("idx_voice_packs_scope_language", "organization_id", "language"),
        Index("idx_voice_packs_status", "status"),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, datetime) else (value or "")


def _row(pack: VoicePack) -> dict[str, Any]:
    """The stored row as the plain dict the policy layer reads."""
    return {
        "id": pack.id,
        "organization_id": pack.organization_id,
        "language": pack.language,
        "voice_name": pack.voice_name,
        "description": pack.description or "",
        "personality": pack.personality or "",
        "version": pack.version,
        "status": pack.status,
        "base_path": pack.base_path or "",
        "manifest": pack.manifest or {},
        "compatibility": pack.compatibility or {},
        "available_to_organizations": bool(pack.available_to_organizations),
        "validation_status": pack.validation_status,
        "validation_problems": list(pack.validation_problems or []),
        "review_status": pack.review_status,
        "reviewed_by": pack.reviewed_by,
        "reviewed_at": _iso(pack.reviewed_at),
        "published_by": pack.published_by,
        "published_at": _iso(pack.published_at),
        "retired_at": _iso(pack.retired_at),
        "created_at": _iso(pack.created_at),
        "updated_at": _iso(pack.updated_at),
    }


def _apply(pack: VoicePack, updates: dict[str, Any]) -> None:
    """Persist a policy decision on the row, converting timestamps back."""
    for key, value in updates.items():
        if key.endswith("_at") and isinstance(value, str) and value:
            value = datetime.fromisoformat(value)
        setattr(pack, key, value)
    pack.updated_at = datetime.now(timezone.utc)


def _refuse(error: policy.PolicyError) -> None:
    """Translate a policy refusal into the project's HTTP contract."""
    raise HTTPException(error.status, error.detail)


def _pack_or_404(session, pack_id: str) -> VoicePack:
    pack = session.query(VoicePack).filter(VoicePack.id == pack_id).first()
    if pack is None:
        raise HTTPException(404, "voice pack not found")
    return pack


def _visible(pack: VoicePack, auth: AuthContext) -> bool:
    """May this caller see the pack at all?

    Platform packs are visible to tenants only when they have been released to
    organisations; an organisation pack only to its organisation and the platform
    administrator.  A caller who may not see a pack is told it does not exist.
    """
    if auth.role in policy.PLATFORM_ROLES:
        return True
    if pack.organization_id is None:
        return bool(pack.available_to_organizations)
    return pack.organization_id == auth.organization_id


def _visible_or_404(pack: VoicePack, auth: AuthContext) -> VoicePack:
    if not _visible(pack, auth):
        raise HTTPException(404, "voice pack not found")
    return pack


def _audit(session, pack: VoicePack, action: str, auth: AuthContext,
           before: dict | None = None, after: dict | None = None,
           reason: str = "") -> None:
    """Record one event, in the trail that matches the pack's scope.

    A tenant pack is a tenant event (``audit_events``, organization_id set); a
    platform pack is a platform event (``platform_audit_events``).  ``.clinerules``
    §3: denials and changes are recorded, and the trail is append-only.
    """
    target = f"{pack.id}@{pack.version}"
    if pack.organization_id:
        record_audit(session, service="organization", org_id=pack.organization_id,
                     action=action, target_type="voice_pack", target_id=target,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after, reason=reason)
    else:
        record_platform_audit(session, service="organization", action=action,
                             target_type="voice_pack", target_id=target,
                             actor_id=auth.user_id, actor_role=auth.role,
                             before=before, after=after, reason=reason)


def _pack_dir(pack_id: str) -> str:
    """Absolute directory for *pack_id*, refusing anything that could escape.

    The id has already been through :func:`policy.safe_relative_path`'s sibling
    check, but the resolved path is compared against the root as well: two
    independent checks are cheaper than one traversal.
    """
    if not policy.PACK_ID_RE.match(pack_id or ""):
        raise HTTPException(422, "invalid voice pack id")
    root = os.path.realpath(PACK_ROOT)
    target = os.path.realpath(os.path.join(root, pack_id))
    if target != root and not target.startswith(root + os.sep):
        raise HTTPException(422, "invalid voice pack id")
    return target


def _write_assets(pack_id: str, files: List[dict[str, str]]) -> int:
    """Write validated asset bytes; returns the number of files written.

    Only called after :func:`policy.validate_pack_upload` has accepted the
    payload, so every path and every byte has already been checked.  The directory
    is the pack version's own, so a write cannot land on another version's assets.
    """
    directory = _pack_dir(pack_id)
    written = 0
    for entry in files:
        data = policy.decode_payload(entry.get("contentBase64"))
        if data is None:
            continue
        relative = policy.safe_relative_path(entry.get("path"), what="file path")
        target = os.path.realpath(os.path.join(directory, *relative.split("/")))
        if not target.startswith(os.path.realpath(directory) + os.sep):
            raise HTTPException(422, "unsafe asset path")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(data)
        written += 1
    return written


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class AssetPayload(BaseModel):
    path: str
    contentBase64: str
    checksum: Optional[str] = None


class VoicePackUpload(BaseModel):
    """A complete pack version: metadata, manifest and the audio it describes.

    ``organization_id`` is only ever *compared* with the caller's organization —
    it never selects it (``.clinerules`` §3).  Omitted means the platform scope,
    which only ``super_admin`` may address.
    """

    id: str
    language: str
    voice_name: str
    description: str = ""
    personality: str = ""
    version: Optional[int] = None
    manifest: dict = Field(default_factory=dict)
    compatibility: dict = Field(default_factory=dict)
    files: List[AssetPayload] = Field(default_factory=list)
    organization_id: Optional[str] = None


class ReviewDecision(BaseModel):
    note: str = ""


class AvailabilityChange(BaseModel):
    available: bool


def _scope_of(auth: AuthContext, requested: Optional[str]) -> Optional[str]:
    """The organization id a write applies to; ``None`` for the platform scope."""
    try:
        scope = policy.resolve_scope(auth.role, auth.organization_id, requested)
    except policy.PolicyError as error:
        _refuse(error)
    return scope["organization_id"]


def _summary(pack: VoicePack) -> dict[str, Any]:
    """The metadata a selector needs; the manifest is fetched separately."""
    row = _row(pack)
    return {key: row[key] for key in (
        "id", "organization_id", "language", "voice_name", "description",
        "personality", "version", "status", "available_to_organizations",
        "validation_status", "review_status", "reviewed_by", "reviewed_at",
        "published_by", "published_at", "retired_at", "created_at", "updated_at")}


def _may_stream(pack: VoicePack, auth: AuthContext) -> bool:
    """May this caller fetch the *audio* of this pack?

    Playback needs the assets, so the gate is the queue capability rather than the
    configuration one — a receptionist must be able to play a published pack
    without being able to change it.  A pack that is not published is streamed
    only to a caller who may administer it, which is what makes previewing an
    unreleased version possible without exposing it to the terminals.
    """
    if not _visible(pack, auth):
        return False
    if pack.status == policy.SELECTABLE_STATUS:
        return True
    return auth.role in policy.VOICE_CONFIG_ROLES


# ---------------------------------------------------------------------------
# Reading the library
# ---------------------------------------------------------------------------

@router.get("")
def list_voice_packs(
        language: Optional[str] = None,
        status: Optional[str] = None,
        auth: AuthContext = Depends(require_permission("org.read"))):
    """Every pack this caller may see, as configuration metadata.

    A tenant sees its own packs in every status, plus the platform packs released
    to organisations.  A branch administrator holds no ``org.read`` in the matrix,
    so this configuration surface is closed to it: voice settings are
    organization-wide.
    """
    session = SessionFactory()
    try:
        query = session.query(VoicePack)
        if auth.role not in policy.PLATFORM_ROLES:
            own = VoicePack.organization_id == auth.organization_id
            released = ((VoicePack.organization_id.is_(None))
                        & (VoicePack.available_to_organizations.is_(True)))
            query = query.filter(own | released)
        if language:
            query = query.filter(VoicePack.language == language)
        if status:
            query = query.filter(VoicePack.status == status)
        rows = query.order_by(VoicePack.language, VoicePack.voice_name,
                              VoicePack.version.desc()).all()
        return {"packs": [_summary(pack) for pack in rows]}
    finally:
        session.close()


@router.get("/{pack_id}/manifest")
def get_pack_manifest(pack_id: str,
                      auth: AuthContext = Depends(require_permission("queue.view"))):
    """The asset catalogue of one pack version, authenticated.

    Organisation packs are never public URLs, so the catalogue is served here
    rather than from the static tree.
    """
    session = SessionFactory()
    try:
        pack = _pack_or_404(session, pack_id)
        if not _may_stream(pack, auth):
            raise HTTPException(404, "voice pack not found")
        return {"id": pack.id, "language": pack.language,
                "version": pack.version, "status": pack.status,
                "manifest": pack.manifest or {},
                "manifest_checksum": pack.manifest_checksum or ""}
    finally:
        session.close()


@router.get("/{pack_id}/preview")
def preview_pack(pack_id: str,
                 auth: AuthContext = Depends(require_permission("org.read"))):
    """Describe a pack for auditioning **without changing any configuration**.

    Read-only by construction: nothing is written, no status changes and the
    production configuration is untouched (assignment §3.3).
    """
    session = SessionFactory()
    try:
        pack = _visible_or_404(_pack_or_404(session, pack_id), auth)
        row = _row(pack)
        return {
            "descriptor": policy.pack_descriptor(row),
            "problems": policy.validate_manifest(row["manifest"],
                                                language=row["language"]),
            "status": row["status"],
            "selectable": policy.check_selectable(row, row["language"],
                                                  auth.organization_id)[0],
        }
    finally:
        session.close()


@router.get("/{pack_id}/assets/{asset_path:path}")
def get_pack_asset(pack_id: str, asset_path: str,
                   auth: AuthContext = Depends(require_permission("queue.view"))):
    """Serve one asset file of one pack version.

    The path is re-validated on the way out — a stored manifest is untrusted input
    — and it must be one this pack's manifest actually declares.  A refusal is a
    404: there is no directory listing to fall back on and no filesystem path is
    ever returned to the caller.
    """
    session = SessionFactory()
    try:
        pack = _pack_or_404(session, pack_id)
        if not _may_stream(pack, auth):
            raise HTTPException(404, "voice pack not found")
        declared = {a.get("playbackFile")
                    for a in (pack.manifest or {}).get("assets", [])
                    if isinstance(a, dict)}
        if asset_path not in declared:
            raise HTTPException(404, "asset not found")
        try:
            relative = policy.safe_relative_path(asset_path, what="asset path")
        except policy.PolicyError:
            raise HTTPException(404, "asset not found")
        directory = _pack_dir(pack.id)
        target = os.path.realpath(os.path.join(directory, *relative.split("/")))
        if not target.startswith(os.path.realpath(directory) + os.sep):
            raise HTTPException(404, "asset not found")
        if not os.path.isfile(target):
            raise HTTPException(404, "asset not found")
        return FileResponse(target)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Creating a version (upload)
# ---------------------------------------------------------------------------

def _manifest_checksum(manifest: Any) -> str:
    """A stable digest of the manifest as stored, for change detection."""
    import json
    return policy.sha256_hex(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8"))


@router.post("", status_code=201)
def create_voice_pack(data: VoicePackUpload,
                      auth: AuthContext = Depends(require_permission("org.manage"))):
    """Register one new pack version from an uploaded manifest and its assets.

    Order matters and is the whole point of the endpoint:

    1. scope is resolved from the token (a foreign organisation is a 404, the
       platform scope is refused to a tenant administrator);
    2. *everything* is validated before a byte is written — path traversal, real
       container versus extension, checksums, orphans, duplicates, missing
       required assets, metadata;
    3. only then is the row created, deliberately as ``draft``: an upload that
       validated is not published, approved or selectable, and a publication
       still needs a human reviewer (assignment §6).
    """
    policy.require("manage_pack", auth.role)
    organization_id = _scope_of(auth, data.organization_id)

    payload = data.model_dump()
    result = policy.validate_pack_upload(payload)
    if not result["ok"]:
        # 422 with the complete list: an upload is corrected in one round, not
        # one fault per attempt.
        raise HTTPException(422, {"message": "voice pack upload failed validation",
                                  "problems": result["problems"]})

    session = SessionFactory()
    try:
        if session.query(VoicePack).filter(VoicePack.id == data.id).first():
            raise HTTPException(409, "voice pack version already exists")

        family = session.query(VoicePack).filter(
            VoicePack.organization_id == organization_id,
            VoicePack.language == data.language,
            VoicePack.voice_name == data.voice_name).all()
        version = data.version or policy.next_version([p.version for p in family])
        if any(p.version == version for p in family):
            raise HTTPException(
                409, "this version number is already used for this voice; a "
                     "published version is never overwritten")

        problems = sorted(set(policy.validate_manifest(data.manifest,
                                                       language=data.language)))
        _write_assets(data.id, [f.model_dump() for f in data.files])

        pack = VoicePack(
            id=data.id, organization_id=organization_id,
            language=data.language, voice_name=data.voice_name,
            description=data.description, personality=data.personality,
            version=version, status=policy.PACK_STATUS["DRAFT"],
            manifest=data.manifest,
            manifest_checksum=_manifest_checksum(data.manifest),
            compatibility=data.compatibility or {},
            available_to_organizations=False,
            validation_status="fail" if problems else "pass",
            validation_problems=problems,
            review_status="pending",
            created_by=auth.user_id)
        session.add(pack)
        session.flush()
        # B-1 (QUE-006 integration trial): `validate_pack_upload` reports
        # ``assets`` as a *count* of distinct stored paths, not as a list — see
        # its return value. Wrapping it in ``len()`` raised
        # ``TypeError: object of type 'int' has no len()`` on every upload that
        # had already passed validation, which turned the 201 into a 500 and
        # failed 13 W3 API tests. The count is read directly here and below, so
        # the response body and the audit reason describe the same upload.
        _audit(session, pack, "voice_pack.created", auth,
               after=_summary(pack),
               reason=f"{result['assets']} asset(s), "
                      f"{result['bytes']} byte(s) uploaded")
        session.commit()
        body = _summary(pack)
        body["validation"] = {"status": pack.validation_status,
                              "problems": problems,
                              "assets": result["assets"],
                              "bytes": result["bytes"]}
        body["next"] = "validate, submit for review, then approval and publication"
        return body
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Moving a version through its lifecycle
# ---------------------------------------------------------------------------

#: Audit action for each lifecycle step.  The names read as past-tense facts in
#: the trail, which is what makes it reviewable without cross-referencing code.
AUDIT_ACTION = {
    "validate": "voice_pack.validated",
    "submit": "voice_pack.submitted",
    "approve": "voice_pack.approved",
    "reject": "voice_pack.rejected",
    "publish": "voice_pack.published",
    "retire": "voice_pack.retired",
}


def _file_problems(pack: VoicePack) -> list[str]:
    """Required assets whose bytes are not actually on disk.

    Validation is repeated from stored state rather than trusted from upload time:
    a file can be missing because a copy failed or because someone removed it, and
    a pack that announces half its phrases is worse than one that refuses to
    publish.
    """
    problems: list[str] = []
    directory = _pack_dir(pack.id)
    for asset in (pack.manifest or {}).get("assets", []):
        if not isinstance(asset, dict) or asset.get("required") is not True:
            continue
        path = asset.get("playbackFile")
        if not isinstance(path, str) or not path:
            continue
        target = os.path.join(directory, *path.split("/"))
        if not os.path.isfile(target):
            problems.append(f"asset {asset.get('id')}:missing_file")
    return problems


def _run_transition(pack_id: str, action: str, auth: AuthContext, *,
                    note: str = "", reviewer_id: str = "") -> dict[str, Any]:
    """Apply one lifecycle step, audit it, and return the resulting summary."""
    session = SessionFactory()
    try:
        pack = _pack_or_404(session, pack_id)
        try:
            policy.require_pack_access(
                pack_organization_id=pack.organization_id, role=auth.role,
                caller_organization_id=auth.organization_id)
            row = _row(pack)
            problems = None
            if action == "validate":
                problems = (policy.validate_manifest(row["manifest"],
                                                     language=row["language"])
                            + _file_problems(pack))
            updates = policy.transition(
                row, action, role=auth.role, actor_id=auth.user_id, now=_now(),
                problems=problems, reviewer_id=reviewer_id, review_note=note)
        except policy.PolicyError as error:
            _refuse(error)

        before = _summary(pack)
        _apply(pack, updates)
        _audit(session, pack, AUDIT_ACTION[action], auth, before=before,
               after=_summary(pack), reason=note)
        session.commit()
        body = _summary(pack)
        body["validation_problems"] = list(pack.validation_problems or [])
        return body
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{pack_id}/validate")
def validate_pack(pack_id: str,
                  auth: AuthContext = Depends(require_permission("org.manage"))):
    """Re-run technical validation from the stored manifest and the stored files.

    Machine validation never grants approval: a passing result moves the version
    to ``pending_review``, a failing one marks it ``rejected`` and keeps the
    reasons on the row.
    """
    return _run_transition(pack_id, "validate", auth)


@router.post("/{pack_id}/submit")
def submit_pack(pack_id: str,
                auth: AuthContext = Depends(require_permission("org.manage"))):
    """Submit a validated organisation version for human review."""
    return _run_transition(pack_id, "submit", auth)


@router.post("/{pack_id}/approve")
def approve_pack(pack_id: str, decision: ReviewDecision,
                 auth: AuthContext = Depends(require_permission("platform.admin"))):
    """Record a human approval, naming the reviewer.

    Only the platform administrator may approve, so an organisation can never mark
    its own pack human-reviewed — the one thing assignment §3.5 forbids outright.
    The reviewer identity comes from the token, never from the payload.
    """
    return _run_transition(pack_id, "approve", auth, note=decision.note,
                           reviewer_id=auth.user_id)


@router.post("/{pack_id}/reject")
def reject_pack(pack_id: str, decision: ReviewDecision,
                auth: AuthContext = Depends(require_permission("platform.admin"))):
    """Record a human rejection with its reason."""
    return _run_transition(pack_id, "reject", auth, note=decision.note,
                           reviewer_id=auth.user_id)


@router.post("/{pack_id}/publish")
def publish_pack(pack_id: str,
                 auth: AuthContext = Depends(require_permission("platform.admin"))):
    """Publish an approved version, which is what makes it selectable."""
    return _run_transition(pack_id, "publish", auth)


@router.post("/{pack_id}/retire")
def retire_pack(pack_id: str,
                auth: AuthContext = Depends(require_permission("platform.admin"))):
    """Retire a version: it stops being selectable and its row is kept.

    Retiring deletes nothing — a facility that already installed the pack keeps
    working, and the rollback history stays intact.
    """
    return _run_transition(pack_id, "retire", auth)


@router.post("/{pack_id}/availability")
def set_availability(pack_id: str, change: AvailabilityChange,
                     auth: AuthContext = Depends(
                         require_permission("platform.admin"))):
    """Release or withhold a published **platform** pack for organisations.

    This is the platform's control over which packs a tenant may select
    (assignment §3.2).  An organisation's own pack is always available to it, so
    the flag is only meaningful — and only accepted — for a platform pack.
    """
    session = SessionFactory()
    try:
        pack = _pack_or_404(session, pack_id)
        if pack.organization_id is not None:
            raise HTTPException(
                409, "availability applies to platform packs only; an "
                     "organisation's pack is available to that organisation")
        if change.available and pack.status != policy.SELECTABLE_STATUS:
            raise HTTPException(
                409, "only a published pack can be released to organisations")
        before = _summary(pack)
        pack.available_to_organizations = bool(change.available)
        _apply(pack, {})
        _audit(session, pack, "voice_pack.availability_changed", auth,
               before=before, after=_summary(pack))
        session.commit()
        return _summary(pack)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
