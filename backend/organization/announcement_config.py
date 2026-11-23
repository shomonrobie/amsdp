"""QUE-006 / W3 — language and voice configuration (platform and organisation).

Two scopes, one surface, and a strict boundary between them:

``/api/v1/platform/announcement-config``
    the platform defaults — announcement language and the default English and
    Bangla packs.  ``platform.admin`` only, i.e. ``super_admin``.  Stored in
    ``announcement_platform_config`` because no platform-settings store existed.

``/api/v1/orgs/{org_id}/announcement-config``
    one organisation's override.  Read with ``org.read``, written with
    ``org.manage``; a foreign ``org_id`` is a **non-disclosing 404**, and the
    organisation is always the one in the token.  Stored in the existing
    ``organizations.config["announcement"]`` block — the same pattern as
    ``appointment_config`` and ``notification_config``, so this half needs no
    schema change.

An organisation without overrides inherits the platform defaults, and language and
voice are separate settings chosen independently per language (assignment §3.2–
§3.4).  Every write is validated against the pack registry through
:mod:`organization.voice_pack_policy`, so a configuration cannot name a pack that
is unpublished, of the wrong language, owned by another organisation, or withheld
by the platform — and the refusal says which of those it was.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, JSON, String

from common.audit import record_audit, record_platform_audit
from common.auth import AuthContext, require_permission
from common.database import Base, SessionFactory
from common.models import Organization

# TRIAL MERGE / acceptance-readiness (2026-11-23): same dual-layout rule as `voice_packs.py`.
# The image runs `uvicorn main:app` with this directory as `/app`, where `announcement_config`
# and `voice_packs` are top-level modules; the test harness imports them as
# `organization.announcement_config`. An unguarded relative import therefore crashed the
# service at start-up in the container while every unit test still passed. Both spellings are
# now accepted; nothing else changes.
try:                                     # package layout: `organization.main` (tests)
    from . import voice_pack_policy as policy
    from .voice_packs import VoicePack, _row as _pack_row
except ImportError:                      # flat layout: `uvicorn main:app` in the image
    import voice_pack_policy as policy
    from voice_packs import VoicePack, _row as _pack_row

router = APIRouter(tags=["announcement-config"])

CONFIG_KEY = "announcement"
PLATFORM_ROW_ID = "platform"


class AnnouncementPlatformConfig(Base):
    """The platform's announcement defaults — one row, id ``platform``.

    ``organizations.config`` holds tenant configuration, and a platform default is
    not tenant configuration: it applies to every organisation that has no
    override.  A single-row table keeps that distinction visible instead of
    hiding a platform setting inside some organisation's JSON.
    """

    __tablename__ = "announcement_platform_config"
    __service__ = "organization"

    id = Column(String(20), primary_key=True, default=PLATFORM_ROW_ID)
    language = Column(String(8), nullable=False, default=policy.DEFAULT_LANGUAGE)
    voice_packs = Column(JSON, default=dict)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refuse(error: policy.PolicyError) -> None:
    raise HTTPException(error.status, error.detail)


def _scoped_org(auth: AuthContext, org_id: str) -> str:
    """Non-disclosing tenant gate: a foreign organization is 404, not 403."""
    if auth.role in policy.PLATFORM_ROLES or auth.organization_id == org_id:
        return org_id
    raise HTTPException(404, "organization not found")


def _org_or_404(session, org_id: str) -> Organization:
    org = session.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        raise HTTPException(404, "organization not found")
    return org


def get_announcement_config(org_config: Any) -> Dict[str, Any]:
    """Read the ``announcement`` block of an organisation's config.

    Malformed values are dropped rather than raising: a corrupt configuration
    block must never make the queue page answer 500.
    """
    block = (org_config or {}).get(CONFIG_KEY)
    if not isinstance(block, dict):
        return {}
    result: Dict[str, Any] = {}
    if block.get("language") in policy.LANGUAGES:
        result["language"] = block["language"]
    packs = block.get("voice_packs")
    if isinstance(packs, dict):
        result["voice_packs"] = {
            lang: value for lang, value in packs.items()
            if lang in policy.LANGUAGES and isinstance(value, str) and value}
    for key in ("updated_at", "updated_by"):
        if isinstance(block.get(key), str):
            result[key] = block[key]
    return result


def _platform_view(session) -> Dict[str, Any]:
    row = session.query(AnnouncementPlatformConfig).filter(
        AnnouncementPlatformConfig.id == PLATFORM_ROW_ID).first()
    if row is None:
        return {"language": policy.DEFAULT_LANGUAGE, "voice_packs": {},
                "updated_at": "", "updated_by": "",
                "inherited": True}
    return {"language": row.language,
            "voice_packs": dict(row.voice_packs or {}),
            "updated_at": row.updated_at.isoformat() if row.updated_at else "",
            "updated_by": row.updated_by or "",
            "inherited": False}


class VoiceConfigUpdate(BaseModel):
    """A configuration change: a language, per-language pack ids, or both.

    ``None`` for a language clears the override for that language — English and
    Bangla are chosen independently, so clearing one must not disturb the other.
    """

    language: Optional[str] = None
    voice_packs: Optional[Dict[str, Optional[str]]] = None


class RollbackRequest(BaseModel):
    language: str


def _selection_problems(packs: List[Dict[str, Any]],
                        updates: VoiceConfigUpdate, *, scope: str,
                        organization_id: Optional[str]) -> List[str]:
    """Every reason the requested pack selection is not allowed, in one pass."""
    problems: List[str] = []
    if updates.language is not None and updates.language not in policy.LANGUAGES:
        problems.append(f"language: unsupported ({updates.language})")

    index = policy.index_packs(packs)
    for language, pack_id in (updates.voice_packs or {}).items():
        if language not in policy.LANGUAGES:
            problems.append(f"{language}: unsupported language")
            continue
        if pack_id in (None, ""):
            continue                      # clearing an override is always allowed
        pack = index.get(pack_id)
        if pack is None:
            # The pack is either absent or not visible to this caller; both are
            # "not found", so visibility cannot be probed by guesswork.
            problems.append(f"{language}: {policy.SELECTION_WARNING['NOT_FOUND']}")
            continue
        if scope == "platform":
            # A platform default must be a *platform* pack that has been published
            # and released, because it becomes the default for every tenant that
            # has no override.
            if pack.get("status") != policy.SELECTABLE_STATUS:
                problems.append(f"{language}: "
                                f"{policy.SELECTION_WARNING['NOT_PUBLISHED']}")
            elif policy.pack_owner(pack) is not None:
                problems.append(f"{language}: a platform default must be a "
                                "platform pack, not an organisation's")
            elif not pack.get("available_to_organizations"):
                problems.append(f"{language}: "
                                f"{policy.SELECTION_WARNING['NOT_AVAILABLE']}")
            continue
        ok, reason = policy.check_selectable(pack, language, organization_id)
        if not ok:
            problems.append(f"{language}: {reason}")
    return problems


def _require_any_change(updates: VoiceConfigUpdate) -> None:
    if updates.language is None and updates.voice_packs is None:
        raise HTTPException(422, "no changes supplied")


# ---------------------------------------------------------------------------
# Platform defaults (§3.2)
# ---------------------------------------------------------------------------

@router.get("/api/v1/platform/announcement-config")
def get_platform_config(auth: AuthContext = Depends(
        require_permission("platform.admin"))):
    """The platform defaults in force, and the packs they may name."""
    session = SessionFactory()
    try:
        view = _platform_view(session)
        packs = [_pack_row(pack) for pack in session.query(VoicePack).all()]
        view["resolved"] = policy.resolve_config(view, {}, packs, None)
        view["available_packs"] = [
            {"id": p["id"], "language": p["language"],
             "voice_name": p["voice_name"], "version": p["version"],
             "status": p["status"],
             "available_to_organizations": bool(p.get("available_to_organizations"))}
            for p in packs
            if p.get("status") == policy.SELECTABLE_STATUS
            and policy.pack_owner(p) is None]
        return view
    finally:
        session.close()


@router.put("/api/v1/platform/announcement-config")
def update_platform_config(updates: VoiceConfigUpdate,
                           auth: AuthContext = Depends(
                               require_permission("platform.admin"))):
    """Change the platform default language and/or its default voice packs.

    Only ``super_admin`` reaches this route, and only a published, released
    platform pack may be a default: a default is an inherit-for-everyone decision,
    so it cannot point at a draft or at one organisation's private pack.
    """
    policy.require("configure_platform", auth.role)
    _require_any_change(updates)

    session = SessionFactory()
    try:
        packs = [_pack_row(pack) for pack in session.query(VoicePack).all()]
        problems = _selection_problems(packs, updates, scope="platform",
                                       organization_id=None)
        if problems:
            raise HTTPException(422, {"message": "invalid platform configuration",
                                      "problems": problems})

        row = session.query(AnnouncementPlatformConfig).filter(
            AnnouncementPlatformConfig.id == PLATFORM_ROW_ID).first()
        if row is None:
            row = AnnouncementPlatformConfig(id=PLATFORM_ROW_ID,
                                             language=policy.DEFAULT_LANGUAGE,
                                             voice_packs={})
            session.add(row)
        before = {"language": row.language,
                  "voice_packs": dict(row.voice_packs or {})}
        if updates.language is not None:
            row.language = updates.language
        if updates.voice_packs is not None:
            merged = dict(row.voice_packs or {})
            for language, pack_id in updates.voice_packs.items():
                if pack_id in (None, ""):
                    merged.pop(language, None)
                else:
                    merged[language] = pack_id
            row.voice_packs = merged
        row.updated_by = auth.user_id
        row.updated_at = datetime.now(timezone.utc)
        after = {"language": row.language,
                 "voice_packs": dict(row.voice_packs or {})}
        record_platform_audit(session, service="organization",
                              action="announcement_config.platform_updated",
                              target_type="platform_announcement_config",
                              target_id=PLATFORM_ROW_ID, actor_id=auth.user_id,
                              actor_role=auth.role, before=before, after=after,
                              reason="platform announcement defaults")
        session.commit()
        return _platform_view(session)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Organisation configuration (§3.3)
# ---------------------------------------------------------------------------

def _visible_pack_rows(session, auth: AuthContext) -> List[Dict[str, Any]]:
    """The voice packs this caller may see, as plain rows.

    A tenant sees its own packs plus the platform packs that have been released
    to organisations; a platform administrator sees everything.  A foreign
    organisation's pack is therefore *absent* rather than present-and-refused,
    which is what keeps a cross-tenant selection from disclosing that the pack
    exists at all (``.clinerules`` §3: cross-tenant access fails closed and does
    not disclose).  ``_selection_problems`` turns an absent pack into
    ``pack_not_found`` for exactly that reason.
    """
    query = session.query(VoicePack)
    if auth.role not in policy.PLATFORM_ROLES:
        own = VoicePack.organization_id == auth.organization_id
        released = ((VoicePack.organization_id.is_(None))
                    & (VoicePack.available_to_organizations.is_(True)))
        query = query.filter(own | released)
    return [_pack_row(pack) for pack in query.all()]


def _selection_pack_rows(session, auth: AuthContext) -> List[Dict[str, Any]]:
    """The packs a configuration may *name*, as plain rows.

    This is deliberately wider than :func:`_visible_pack_rows`, which is the
    screen's list. A selection must be able to explain a refusal the client
    cannot: an **unreleased platform pack** is present here so it can answer
    ``pack_not_available`` — the platform catalogue is not tenant data, and
    hiding it would turn an actionable refusal into a misleading "not found".

    Another organisation's pack is still excluded: a tenant's pack that this
    caller may not read is indistinguishable from a pack that does not exist
    (``pack_not_found``), so the endpoint discloses nothing about other tenants
    (``.clinerules`` §3: cross-tenant access fails closed, non-disclosing).
    """
    query = session.query(VoicePack)
    if auth.role not in policy.PLATFORM_ROLES:
        query = query.filter(
            (VoicePack.organization_id == auth.organization_id)
            | VoicePack.organization_id.is_(None))
    return [_pack_row(pack) for pack in query.all()]


def _organization_view(session, org: Organization,
                       auth: AuthContext) -> Dict[str, Any]:
    """Everything the configuration screen needs, in one read.

    ``resolved`` is the same precedence the announcement runtime uses, so the
    screen shows what is *in force* rather than what is merely stored.
    """
    platform = _platform_view(session)
    org_block = get_announcement_config(org.config)

    packs = _visible_pack_rows(session, auth)

    return {
        "organization_id": org.id,
        "organization": org_block,
        "platform": {"language": platform["language"],
                     "voice_packs": platform["voice_packs"]},
        "resolved": policy.resolve_config(platform, org_block, packs, org.id),
        "available_packs": [
            {"id": p["id"], "language": p["language"],
             "voice_name": p["voice_name"], "version": p["version"],
             "status": p["status"],
             "scope": "organization" if policy.pack_owner(p) else "platform",
             "selectable": policy.check_selectable(
                 p, p["language"], org.id)[0]}
            for p in packs],
    }


@router.get("/api/v1/orgs/{org_id}/announcement-config")
def get_organization_config(org_id: str,
                            auth: AuthContext = Depends(
                                require_permission("org.read"))):
    """The organisation's override, the platform defaults, and the result."""
    _scoped_org(auth, org_id)
    session = SessionFactory()
    try:
        return _organization_view(session, _org_or_404(session, org_id), auth)
    finally:
        session.close()


@router.put("/api/v1/orgs/{org_id}/announcement-config")
def update_organization_config(org_id: str, updates: VoiceConfigUpdate,
                               auth: AuthContext = Depends(
                                   require_permission("org.manage"))):
    """Change this organisation's language and/or voice packs.

    Every selection is checked against the packs this organisation may actually
    use: published, right language, its own or a released platform pack.  The
    platform defaults are **not** writable here — that scope has its own route and
    its own capability — so an organisation administrator cannot change what other
    tenants inherit.
    """
    _scoped_org(auth, org_id)
    policy.require("configure_organization", auth.role)
    _require_any_change(updates)

    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        # B-2 (QUE-006 integration trial): this used to pass *every* pack to the
        # selection check, so naming another organisation's pack answered
        # `pack_foreign_organization` — which confirms the pack exists and who
        # owns it. A foreign tenant pack is now absent (→ `pack_not_found`),
        # while an unreleased platform pack still answers `pack_not_available`.
        visible = _selection_pack_rows(session, auth)
        problems = _selection_problems(visible, updates, scope="organization",
                                       organization_id=org_id)
        if problems:
            raise HTTPException(422,
                                {"message": "invalid announcement configuration",
                                 "problems": problems})

        before = get_announcement_config(org.config)
        block = dict(before)
        if updates.language is not None:
            block["language"] = updates.language
        if updates.voice_packs is not None:
            merged = dict(block.get("voice_packs") or {})
            for language, pack_id in updates.voice_packs.items():
                if pack_id in (None, ""):
                    merged.pop(language, None)
                else:
                    merged[language] = pack_id
            block["voice_packs"] = merged
        block["updated_at"] = _now()
        block["updated_by"] = auth.user_id

        config = dict(org.config or {})
        config[CONFIG_KEY] = block
        org.config = config

        after = get_announcement_config(config)
        record_audit(session, service="organization", org_id=org_id,
                     action="announcement_config.updated",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason="announcement language / voice packs")
        session.commit()
        return _organization_view(session, org, auth)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/api/v1/orgs/{org_id}/announcement-config/rollback")
def rollback_organization_config(org_id: str, request: RollbackRequest,
                                 auth: AuthContext = Depends(
                                     require_permission("org.manage"))):
    """Restore the previous published pack for one language.

    Only a published — therefore validated and approved — version is a rollback
    target, and only one this organisation may use, so a rollback cannot be used
    to reach a draft or another tenant's pack.  Previous versions are never
    deleted, which is what makes this possible at all (assignment §7).
    """
    _scoped_org(auth, org_id)
    policy.require("configure_organization", auth.role)
    if request.language not in policy.LANGUAGES:
        raise HTTPException(422, f"unsupported language {request.language!r}")

    session = SessionFactory()
    try:
        org = _org_or_404(session, org_id)
        platform = _platform_view(session)
        before = get_announcement_config(org.config)
        packs = [_pack_row(pack) for pack in session.query(VoicePack).all()]

        resolved = policy.resolve_config(platform, before, packs, org_id)
        current_id = ((before.get("voice_packs") or {}).get(request.language)
                      or resolved["voice_packs"].get(request.language))
        target = policy.rollback_target(packs, language=request.language,
                                        organization_id=org_id,
                                        current_pack_id=current_id)
        if target is None:
            raise HTTPException(
                409, f"no earlier published {request.language} pack is available")

        block = dict(before)
        merged = dict(block.get("voice_packs") or {})
        merged[request.language] = target["id"]
        block["voice_packs"] = merged
        block["updated_at"] = _now()
        block["updated_by"] = auth.user_id

        config = dict(org.config or {})
        config[CONFIG_KEY] = block
        org.config = config

        after = get_announcement_config(config)
        record_audit(session, service="organization", org_id=org_id,
                     action="announcement_config.rolled_back",
                     target_type="organization", target_id=org_id,
                     actor_id=auth.user_id, actor_role=auth.role,
                     before=before, after=after,
                     reason=f"rollback {request.language} from "
                            f"{current_id or 'inherited'} to {target['id']}")
        session.commit()
        view = _organization_view(session, org, auth)
        view["rolled_back_from"] = current_id
        view["rolled_back_to"] = target["id"]
        return view
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
