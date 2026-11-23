"""QUE-006 / W3 — voice configuration and voice-pack policy (server side).

This module is the *decision layer* for language and voice configuration.  It is
deliberately free of FastAPI, SQLAlchemy and filesystem access so that the rules
themselves can be executed and proven; the HTTP surface
(:mod:`organization.announcement_config`, :mod:`organization.voice_packs`)
translates between this layer and the database.

Owner decisions implemented here (assignment §3):

§3.1 **Who may configure**
    ``super_admin`` (platform-wide) and ``org_admin`` (own organisation only).
    ``branch_admin``, ``receptionist``, ``doctor`` and ``assistant`` hold no
    voice-configuration authority.  The role matrix already denies them, because
    only the platform administrator holds ``platform.admin`` and only the two
    administrator roles hold ``org.manage`` — but the gate is restated here as
    well (:data:`VOICE_CONFIG_ROLES`) so a future delegable capability cannot
    widen it silently.  A client-side rule is not an access control; this is the
    server half.

§3.2 **Platform configuration** — platform default language, the default English
    and Bangla packs (selected independently), pack creation, validation,
    publication, retirement, and which published packs organisations may use.

§3.3 **Organisation configuration** — language override, independent per-language
    pack selection among available packs, its own pack versions (draft, submit
    for review), selection of an approved version, and rollback.

§3.4 **Voice library** — several versions and personas per language; language and
    voice are separate settings, and English and Bangla resolve independently.

§3.5 **Metadata** — :data:`METADATA_FIELDS` and :func:`missing_metadata` make the
    required fields explicit instead of implicit in a table definition.

Nothing here may mark a pack human-approved: :func:`transition` refuses
``approve``/``publish`` unless a reviewer identity and review time are supplied
(assignment §3.5, "Do not mark a voice pack as human-approved without actual
human review").

The status vocabulary and the refusal reasons follow the words the frontend
already uses (``frontend/lib/announcements/voice-packs.js``), so both halves of
the system refuse the same things for the same reasons.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from typing import Any, Iterable, Mapping, Sequence

from common.permissions import check as permission_check

# ---------------------------------------------------------------------------
# Roles and capabilities (assignment §3.1)
# ---------------------------------------------------------------------------

#: The only roles that may change language or voice configuration.
VOICE_CONFIG_ROLES: tuple[str, ...] = ("super_admin", "org_admin")

#: The only role that may change platform defaults, approve or publish.
PLATFORM_ROLES: tuple[str, ...] = ("super_admin",)

CAPABILITY_READ = "org.read"
CAPABILITY_ORG_WRITE = "org.manage"
CAPABILITY_PLATFORM = "platform.admin"

#: The capability each operation is gated on, resolved through the existing
#: matrix rather than by inventing a new one.
ACTION_CAPABILITY: dict[str, str] = {
    "read": CAPABILITY_READ,
    "configure_organization": CAPABILITY_ORG_WRITE,
    "manage_pack": CAPABILITY_ORG_WRITE,
    "configure_platform": CAPABILITY_PLATFORM,
    "approve_pack": CAPABILITY_PLATFORM,
    "publish_pack": CAPABILITY_PLATFORM,
    "retire_pack": CAPABILITY_PLATFORM,
    "control_availability": CAPABILITY_PLATFORM,
}

LANGUAGES: tuple[str, ...] = ("bn", "en")
DEFAULT_LANGUAGE = "bn"

# ---------------------------------------------------------------------------
# Lifecycle (assignment §3.2, §3.3, §3.5)
# ---------------------------------------------------------------------------

PACK_STATUS = {
    "DRAFT": "draft",
    "VALIDATING": "validating",
    "PENDING_REVIEW": "pending_review",
    "APPROVED": "approved",
    "PUBLISHED": "published",
    "RETIRED": "retired",
    "REJECTED": "rejected",
}

STATUSES: tuple[str, ...] = tuple(PACK_STATUS.values())

#: Only a published pack may be selected for production use.
SELECTABLE_STATUS = PACK_STATUS["PUBLISHED"]

#: Statuses in which a pack's content may still be replaced.
MUTABLE_STATUSES: tuple[str, ...] = (
    PACK_STATUS["DRAFT"], PACK_STATUS["REJECTED"],
    PACK_STATUS["VALIDATING"], PACK_STATUS["PENDING_REVIEW"],
)

VALIDATION_STATUSES: tuple[str, ...] = ("unvalidated", "pass", "fail")
REVIEW_STATUSES: tuple[str, ...] = ("pending", "approved", "rejected")

#: ``action -> (allowed source statuses, resulting status)``.
TRANSITIONS: dict[str, tuple[tuple[str, ...], str]] = {
    # Technical validation is a machine step; it never grants approval.
    "validate": (
        (PACK_STATUS["DRAFT"], PACK_STATUS["REJECTED"],
         PACK_STATUS["VALIDATING"]),
        PACK_STATUS["PENDING_REVIEW"],
    ),
    # An organisation submits its own validated version for human review.
    "submit": (
        (PACK_STATUS["DRAFT"], PACK_STATUS["REJECTED"]),
        PACK_STATUS["PENDING_REVIEW"],
    ),
    # Human review, recorded with a named reviewer — never inferred.
    "approve": ((PACK_STATUS["PENDING_REVIEW"],), PACK_STATUS["APPROVED"]),
    "reject": ((PACK_STATUS["PENDING_REVIEW"],), PACK_STATUS["REJECTED"]),
    # Publication makes a version selectable.  It is irreversible except by
    # retirement, which is what keeps a published version reproducible.
    "publish": ((PACK_STATUS["APPROVED"],), PACK_STATUS["PUBLISHED"]),
    "retire": (
        (PACK_STATUS["PUBLISHED"], PACK_STATUS["APPROVED"],
         PACK_STATUS["PENDING_REVIEW"], PACK_STATUS["REJECTED"]),
        PACK_STATUS["RETIRED"],
    ),
}

#: Which roles may drive each transition.  ``org_admin`` may validate and submit
#: its own pack but can never approve or publish one: self-approval is exactly
#: what "do not mark a pack human-approved without review" forbids.
TRANSITION_ROLES: dict[str, tuple[str, ...]] = {
    "validate": ("super_admin", "org_admin"),
    "submit": ("super_admin", "org_admin"),
    "approve": PLATFORM_ROLES,
    "reject": PLATFORM_ROLES,
    "publish": PLATFORM_ROLES,
    "retire": PLATFORM_ROLES,
}

#: The interface never substitutes browser speech synthesis for a missing
#: prerecorded pack (assignment §7).  It is a constant, not a flag, so no
#: configuration value can turn it on by accident.
ALLOW_SYNTHESIS_FALLBACK = False


class PolicyError(Exception):
    """A refusal carrying an HTTP-shaped status, raised instead of guessing.

    ``status`` follows the project contract: 403 when the role lacks the
    capability, **404** for a foreign organisation (non-disclosing), 409 for a
    conflict with the pack's current state, 422 for an invalid payload.
    """

    def __init__(self, detail: str, status: int = 422, code: str = ""):
        super().__init__(detail)
        self.detail = detail
        self.status = status
        self.code = code or detail


# ---------------------------------------------------------------------------
# Permission and scope decisions
# ---------------------------------------------------------------------------

def may(action: str, role: str) -> bool:
    """May *role* perform *action*?

    Two gates, both must pass: the explicit voice-configuration role list
    (assignment §3.1) and the existing capability matrix.  Stating both means a
    hand-written capability grant can never widen voice configuration, and the
    role list alone is not the access control either.
    """
    if action in ("read", "preview"):
        # Reading configuration is ordinary organization reading; a branch
        # administrator may read, which is not configuration authority.
        return permission_check(CAPABILITY_READ, role)
    if action in ("configure_platform", "approve_pack", "publish_pack",
                  "retire_pack", "control_availability"):
        return (role in PLATFORM_ROLES
                and permission_check(CAPABILITY_PLATFORM, role))
    if role not in VOICE_CONFIG_ROLES:
        return False
    capability = ACTION_CAPABILITY.get(action)
    return True if capability is None else permission_check(capability, role)


def require(action: str, role: str) -> None:
    """Raise a 403 unless *role* may perform *action*."""
    if not may(action, role):
        raise PolicyError("insufficient permissions", status=403,
                          code="forbidden")


def resolve_scope(role: str, caller_organization_id: str | None,
                  requested_organization_id: str | None) -> dict[str, Any]:
    """Which configuration scope is being addressed?

    Returns ``{"scope": "platform", "organization_id": None}`` or
    ``{"scope": "organization", "organization_id": <id>}``.

    A foreign organisation is a **non-disclosing 404** (``.clinerules`` §3
    forbids 403 there), and the organisation is always derived from the
    authenticated caller — never trusted from the payload.
    """
    if requested_organization_id in (None, "", "platform"):
        if role not in PLATFORM_ROLES:
            # Asking for the platform scope is asking to change everyone's
            # defaults; a tenant administrator is refused.
            raise PolicyError("platform configuration is not available",
                              status=403, code="platform_scope_forbidden")
        return {"scope": "platform", "organization_id": None}

    if caller_organization_id == requested_organization_id:
        return {"scope": "organization",
                "organization_id": requested_organization_id}
    if role in PLATFORM_ROLES:
        return {"scope": "organization",
                "organization_id": requested_organization_id}
    raise PolicyError("not found", status=404, code="organization_not_found")


def require_pack_access(*, pack_organization_id: str | None, role: str,
                        caller_organization_id: str | None) -> None:
    """May *role* administer a pack owned by *pack_organization_id*?

    Platform packs are administered by the platform administrator only (an
    organisation may *use* an available platform pack — that is a selection
    decision, checked by :func:`check_selectable`).  An organisation's pack is
    reachable by that organisation and by the platform administrator, by nobody
    else, and the refusal is a non-disclosing 404.
    """
    if pack_organization_id is None:
        if role not in PLATFORM_ROLES:
            raise PolicyError("not found", status=404, code="pack_not_found")
        return
    if role in PLATFORM_ROLES:
        return
    if caller_organization_id != pack_organization_id:
        raise PolicyError("not found", status=404, code="pack_not_found")


# ---------------------------------------------------------------------------
# Selectability — the server half of the frontend precedence model
# ---------------------------------------------------------------------------

SELECTION_WARNING = {
    "NOT_FOUND": "pack_not_found",
    "NOT_PUBLISHED": "pack_not_published",
    "LANGUAGE_MISMATCH": "pack_language_mismatch",
    "FOREIGN_ORGANIZATION": "pack_foreign_organization",
    "NOT_AVAILABLE": "pack_not_available",
    "NO_PACK": "no_voice_pack",
}

#: Refusals only the server can decide, because only the server knows the
#: availability flag.  The UI never needs to understand them — by the time a pack
#: reaches the client it has already passed this check — but a client that shows
#: a warning list must not be surprised by them either.
SERVER_ONLY_WARNING: tuple[str, ...] = (SELECTION_WARNING["NOT_AVAILABLE"],)


def pack_owner(pack: Mapping[str, Any]) -> str | None:
    """Owning organisation of *pack*, or ``None`` for a platform pack."""
    return pack.get("organization_id") or pack.get("organizationId") or None


def check_selectable(pack: Mapping[str, Any] | None, language: str,
                     organization_id: str | None) -> tuple[bool, str | None]:
    """Is *pack* usable by *organization_id* for *language*?

    Mirrors ``checkSelectable`` in ``frontend/lib/announcements/voice-packs.js``
    so the two halves cannot disagree, and adds the platform availability flag
    the client cannot be trusted to enforce: a platform pack the administrator
    has not released to organisations is not selectable by one.
    """
    if not pack:
        return False, SELECTION_WARNING["NOT_FOUND"]
    if pack.get("language") != language:
        return False, SELECTION_WARNING["LANGUAGE_MISMATCH"]
    if pack.get("status") != SELECTABLE_STATUS:
        return False, SELECTION_WARNING["NOT_PUBLISHED"]
    owner = pack_owner(pack)
    if owner and owner != organization_id:
        return False, SELECTION_WARNING["FOREIGN_ORGANIZATION"]
    if owner is None and not pack.get("available_to_organizations", False):
        # Published but withheld from tenants.  The platform administrator's own
        # defaults may still name it; an organisation may not.
        return False, SELECTION_WARNING["NOT_AVAILABLE"]
    return True, None


def index_packs(packs: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """``id -> pack`` for the packs a caller may see."""
    return {p["id"]: p for p in packs
            if isinstance(p, Mapping) and isinstance(p.get("id"), str) and p.get("id")}


def configured_pack_id(config: Mapping[str, Any] | None,
                       language: str) -> str | None:
    """The pack id *config* names for *language*, or ``None``.

    Language selection and voice selection are separate settings, so this reads
    one language's pack without looking at the other's (assignment §3.4).
    """
    block = (config or {}).get("voice_packs") or {}
    value = block.get(language) if isinstance(block, Mapping) else None
    return value if isinstance(value, str) and value else None


def resolve_config(platform_config: Mapping[str, Any] | None,
                   organization_config: Mapping[str, Any] | None,
                   packs: Sequence[Mapping[str, Any]],
                   organization_id: str | None) -> dict[str, Any]:
    """Resolve the configuration in force for one organisation.

    Precedence (assignment §3.2 "organisations without overrides inherit platform
    defaults", §3.3 overrides, §3.4 independent languages):

    1. the organisation's pack for that language, if selectable;
    2. the platform default for that language, if selectable;
    3. nothing — ``no_voice_pack`` — never a different language, never a
       different persona, and never browser speech (assignment §7).

    The shape is the JSON the frontend already consumes
    (``{language, voice_packs, sources, warnings}``), so
    ``resolveAnnouncementConfig`` can be fed server output without translation.
    Every step down is reported, so the UI can say which pack is in force and why
    a configured one was refused.
    """
    org = organization_config or {}
    platform = platform_config or {}
    index = index_packs(packs)

    language = org.get("language") if org.get("language") in LANGUAGES else None
    if language is None:
        language = (platform.get("language")
                    if platform.get("language") in LANGUAGES else DEFAULT_LANGUAGE)

    resolved: dict[str, str | None] = {}
    sources: dict[str, str] = {}
    warnings: list[dict[str, str]] = []

    for lang in LANGUAGES:
        chosen: str | None = None
        source = "none"
        for label, config in (("organization", org), ("platform", platform)):
            candidate_id = configured_pack_id(config, lang)
            if not candidate_id:
                continue
            candidate = index.get(candidate_id)
            if candidate is None:
                warnings.append({"language": lang, "source": label,
                                 "reason": SELECTION_WARNING["NOT_FOUND"]})
                continue
            ok, reason = check_selectable(candidate, lang, organization_id)
            if not ok:
                warnings.append({"language": lang, "source": label,
                                 "reason": reason
                                 or SELECTION_WARNING["NOT_PUBLISHED"]})
                continue
            chosen = candidate_id
            source = label
            break
        resolved[lang] = chosen
        sources[lang] = source
        if chosen is None:
            warnings.append({"language": lang, "source": "builtin",
                             "reason": SELECTION_WARNING["NO_PACK"]})

    return {"language": language, "voice_packs": resolved,
            "sources": sources, "warnings": warnings}


# ---------------------------------------------------------------------------
# Versioning and rollback (assignment §3.3 / §7)
# ---------------------------------------------------------------------------

def next_version(existing_versions: Iterable[Any]) -> int:
    """The next free version number for one pack family.

    Versions start at 1 and only ever increase: a published version is never
    overwritten (assignment §7), so re-uploading content means a new row, not an
    edit of the old one.
    """
    numbers = [int(v) for v in (existing_versions or ())
               if isinstance(v, int) or (isinstance(v, str) and v.isdigit())]
    return (max(numbers) + 1) if numbers else 1


def rollback_target(packs: Sequence[Mapping[str, Any]], *, language: str,
                    organization_id: str | None,
                    current_pack_id: str | None) -> Mapping[str, Any] | None:
    """The version to restore for *language*, or ``None``.

    "Roll back to a previous approved version" (assignment §3.3) means the
    highest published version that is not the one in force.  Published implies
    validated and approved, so rollback can never land on an unapproved draft.
    Only packs the organisation may actually use are considered — a rollback is
    not a way to reach a pack that selection would refuse.
    """
    candidates = []
    for pack in packs:
        if not isinstance(pack, Mapping) or pack.get("id") == current_pack_id:
            continue
        ok, _reason = check_selectable(pack, language, organization_id)
        if not ok:
            continue
        candidates.append(pack)
    if not candidates:
        return None
    return max(candidates, key=lambda p: (int(p.get("version") or 0),
                                          str(p.get("id") or "")))


def versions_of(packs: Sequence[Mapping[str, Any]], *, language: str,
                family: str) -> list[Mapping[str, Any]]:
    """Every version of one pack family for one language, newest first.

    A family is identified by voice name (plus scope, which the caller filters),
    not by id, because each version is its own row with its own id.
    """
    selected = [p for p in packs
                if isinstance(p, Mapping)
                and p.get("language") == language
                and p.get("voice_name") == family]
    return sorted(selected, key=lambda p: int(p.get("version") or 0),
                  reverse=True)


# ---------------------------------------------------------------------------
# Lifecycle transitions (assignment §3.2 / §3.5)
# ---------------------------------------------------------------------------

def assert_mutable(pack: Mapping[str, Any]) -> None:
    """Refuse to change the content of a version that is already approved.

    A published version must stay reproducible: configuration names an id and a
    version, and re-writing either would silently change what a facility hears.
    """
    if pack.get("status") not in MUTABLE_STATUSES:
        raise PolicyError(
            "pack version is immutable once approved or published; create a new "
            "version instead", status=409, code="pack_immutable")


def transition(pack: Mapping[str, Any], action: str, *, role: str,
               actor_id: str = "", now: str = "",
               problems: Sequence[str] | None = None,
               reviewer_id: str = "", review_note: str = "") -> dict[str, Any]:
    """Apply *action* to *pack* and return the fields to persist.

    The rules that matter, all of them refusals rather than silent corrections:

    * only :data:`TRANSITION_ROLES` may drive the action, so an organisation
      administrator can never approve or publish its own pack;
    * the source status must be one the transition allows;
    * ``approve``/``reject`` require a named reviewer and review time — a pack is
      never marked human-approved because an upload succeeded;
    * ``publish`` additionally requires a *passing* technical validation and a
      recorded approval;
    * ``retire`` is the only way to take a published version out of selection,
      and it keeps the row.
    """
    allowed_roles = TRANSITION_ROLES.get(action)
    if not allowed_roles:
        raise PolicyError(f"unknown action {action!r}", status=422,
                          code="unknown_action")
    if role not in allowed_roles:
        raise PolicyError("insufficient permissions", status=403,
                          code="forbidden")

    current = pack.get("status")
    sources, target = TRANSITIONS[action]
    if current not in sources:
        raise PolicyError(
            f"action {action!r} is not valid from status {current!r}",
            status=409, code="invalid_transition")

    updates: dict[str, Any] = {"status": target}

    if action == "validate":
        failing = list(problems or ())
        updates["validation_status"] = "fail" if failing else "pass"
        updates["validation_problems"] = failing
        if failing:
            updates["status"] = PACK_STATUS["REJECTED"]
        else:
            updates["validated_at"] = now

    if action == "submit" and pack.get("validation_status") != "pass":
        # Submitting an unvalidated or failing pack wastes a reviewer's time and
        # is refused rather than queued.
        raise PolicyError("pack must pass technical validation before review",
                          status=409, code="validation_required")

    if action in ("approve", "reject"):
        if not reviewer_id or not now:
            raise PolicyError(
                "a named reviewer and review time are required; a pack is never "
                "approved automatically", status=422,
                code="human_review_required")
        updates["review_status"] = ("approved" if action == "approve"
                                    else "rejected")
        updates["reviewed_by"] = reviewer_id
        updates["reviewed_at"] = now
        updates["review_note"] = review_note

    if action == "approve" and pack.get("validation_status") != "pass":
        raise PolicyError("pack must pass technical validation before approval",
                          status=409, code="validation_required")

    if action == "publish":
        if pack.get("validation_status") != "pass":
            raise PolicyError(
                "pack must pass technical validation before publication",
                status=409, code="validation_required")
        if pack.get("review_status") != "approved" or not pack.get("reviewed_by"):
            raise PolicyError(
                "pack must be approved by a named reviewer before publication",
                status=409, code="approval_required")
        updates["published_at"] = now
        updates["published_by"] = actor_id

    if action == "retire":
        updates["retired_at"] = now

    return updates


# ---------------------------------------------------------------------------
# Metadata completeness (assignment §3.5)
# ---------------------------------------------------------------------------

#: Every field the voice library must carry, and why it is asked for.  Listing
#: them here keeps the API contract and the table honest: a field that is
#: "supported" but never checked tends to be the one that is missing.
METADATA_FIELDS: tuple[tuple[str, str], ...] = (
    ("id", "unique voice-pack id, also the W5 install directory name"),
    ("language", "en or bn — language and voice are separate settings"),
    ("voice_name", "the persona, e.g. male-1 / female-1"),
    ("description", "what the voice sounds like, for the selector"),
    ("personality", "character the pack was voiced for"),
    ("version", "integer, never reused, never overwritten"),
    ("organization_id", "NULL for a platform pack, else the owning tenant"),
    ("manifest", "asset catalogue: ids, files, checksums, formats"),
    ("compatibility", "manifest schema version and player contract"),
    ("validation_status", "unvalidated / pass / fail"),
    ("review_status", "pending / approved / rejected"),
    ("status", "draft .. published .. retired"),
    ("created_at", "creation timestamp"),
    ("updated_at", "last update timestamp"),
)

#: Fields that only become required once a state is reached, so that a draft may
#: exist without pretending it was reviewed.
CONDITIONAL_METADATA: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("reviewed_by", "review_status", ("approved",)),
    ("reviewed_at", "review_status", ("approved",)),
    ("published_by", "status", (PACK_STATUS["PUBLISHED"],)),
    ("published_at", "status", (PACK_STATUS["PUBLISHED"],)),
    ("retired_at", "status", (PACK_STATUS["RETIRED"],)),
)


def missing_metadata(pack: Mapping[str, Any]) -> list[str]:
    """Names of required metadata fields that are absent or empty.

    Used when a version is validated and when it is submitted, so an incomplete
    pack fails *before* a human is asked to review it.  ``0`` is a valid version
    only in the sense that it means "not set", so it is reported as missing.
    """
    missing = [name for name, _why in METADATA_FIELDS
               if pack.get(name) in (None, "", [], {}, 0)]
    review = pack.get("review_status")
    status = pack.get("status")
    for name, condition_field, wanted in CONDITIONAL_METADATA:
        current = review if condition_field == "review_status" else status
        if current in wanted and pack.get(name) in (None, "", [], {}):
            missing.append(name)
    return missing


# ---------------------------------------------------------------------------
# Upload validation and security (assignment §6)
# ---------------------------------------------------------------------------

#: A pack id is also a directory name on the facility PC (W5 keeps the packs
#: under ``<root>/packs/<packId>/``), so it is restricted to the charset the
#: installer already enforces — ``scripts/que-006-agent/lib/installer.mjs``
#: ``safePackId`` — and additionally may not begin with a dot.
PACK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
CHECKSUM_RE = re.compile(r"^[0-9a-f]{64}$")

#: Path segments allowed in a manifest asset path.  Deliberately narrow: a
#: manifest is untrusted input that later becomes a filesystem path, so anything
#: that could escape a base directory is refused at the door rather than sanitised
#: afterwards.
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_PACK_BYTES = 64 * 1024 * 1024
MAX_PACK_ASSETS = 250
MIN_SAMPLE_RATE = 8000
MAX_SAMPLE_RATE = 48000
ALLOWED_CHANNELS = (1, 2)
MIN_ASSET_SECONDS = 0.05
MAX_ASSET_SECONDS = 60.0

#: Containers the player can decode.  Anything else is refused rather than left
#: to the browser to discover.
SUPPORTED_CONTAINERS: tuple[str, ...] = ("wav", "mp3", "m4a")

EXTENSION_CONTAINER = {"wav": "wav", "mp3": "mp3", "m4a": "m4a", "mp4": "m4a"}


def safe_relative_path(path: Any, *, what: str = "path") -> str:
    """Validate a manifest-relative path and return it unchanged.

    Refuses (``PolicyError`` 422) anything that is not a plain relative path:
    absolute paths, drive letters, backslashes, ``..`` segments, empty segments,
    control characters, and segments outside :data:`SAFE_SEGMENT_RE`.  A stored
    path is later joined onto a pack root, so this is the check that makes path
    traversal impossible rather than merely unlikely.
    """
    if not isinstance(path, str) or not path or len(path) > 200:
        raise PolicyError(f"invalid {what}", status=422, code="invalid_path")
    if path.startswith("/") or "\\" in path or ":" in path or "\x00" in path:
        raise PolicyError(f"unsafe {what}", status=422, code="path_traversal")
    segments = path.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        raise PolicyError(f"unsafe {what}", status=422, code="path_traversal")
    if any(not SAFE_SEGMENT_RE.match(segment) for segment in segments):
        raise PolicyError(f"unsafe {what}", status=422, code="path_traversal")
    return path


def sniff_container(data: bytes) -> str | None:
    """Identify the real container from the first bytes, not from the name.

    Filename extensions are attacker-controlled; the container signature is what
    the decoder will actually see.  ``None`` means "not a container this server
    accepts", which includes OGG and every non-audio payload.
    """
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12:
        return None
    head = bytes(data[:12])
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[4:8] == b"ftyp":
        return "m4a"
    if head[:3] == b"ID3":
        return "mp3"
    if head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
        return "mp3"
    return None


def sha256_hex(data: bytes) -> str:
    """SHA-256 of *data*, lowercase hex — the same form the manifest uses."""
    return hashlib.sha256(data).hexdigest()


def decode_payload(value: Any) -> bytes | None:
    """Decode a base64 upload payload, or ``None`` when it is not base64.

    Uploads arrive as JSON so that no multipart dependency is added to the
    service image; the cost is that the bytes must be decoded and checked here
    rather than trusted from a declared content type.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None


def _number(value: Any) -> float | None:
    """A finite float, or ``None`` — booleans and strings are not numbers here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def validate_asset(asset: Mapping[str, Any], *, language: str) -> list[str]:
    """Structural problems with one manifest asset, as short codes.

    Only describes the asset; uniqueness across the manifest and the presence of
    the actual bytes are checked by :func:`validate_manifest` and
    :func:`validate_pack_upload`, because those need the whole upload.
    """
    problems: list[str] = []
    asset_id = asset.get("id")
    if not isinstance(asset_id, str) or not ASSET_ID_RE.match(asset_id):
        return ["asset:invalid_id"]

    if asset.get("language") != language:
        problems.append(f"asset {asset_id}:language_mismatch")

    path = asset.get("playbackFile")
    try:
        safe_relative_path(path, what="playbackFile")
    except PolicyError as error:
        problems.append(f"asset {asset_id}:{error.code}")

    checksum = asset.get("playbackChecksum")
    if checksum is not None and (not isinstance(checksum, str)
                                 or not CHECKSUM_RE.match(checksum.lower())):
        problems.append(f"asset {asset_id}:invalid_checksum")

    container = asset.get("playbackFormat") or asset.get("container")
    if isinstance(container, str) and container:
        declared = container.split("/")[0].split(";")[0].lower()
        if declared not in SUPPORTED_CONTAINERS:
            problems.append(f"asset {asset_id}:unsupported_container")

    rate = _number(asset.get("sampleRate"))
    if rate is not None and not MIN_SAMPLE_RATE <= rate <= MAX_SAMPLE_RATE:
        problems.append(f"asset {asset_id}:sample_rate_out_of_range")

    channels = _number(asset.get("channels"))
    if channels is not None and int(channels) not in ALLOWED_CHANNELS:
        problems.append(f"asset {asset_id}:channel_count_unsupported")

    duration = _number(asset.get("durationSeconds"))
    if duration is not None and not MIN_ASSET_SECONDS <= duration <= MAX_ASSET_SECONDS:
        problems.append(f"asset {asset_id}:duration_out_of_range")

    return problems


def validate_manifest(manifest: Mapping[str, Any] | None, *,
                      language: str) -> list[str]:
    """Manifest-level problems: shape, uniqueness, references, declared assets."""
    if not isinstance(manifest, Mapping):
        return ["manifest:missing"]
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        return ["manifest:no_assets"]
    if len(assets) > MAX_PACK_ASSETS:
        return ["manifest:too_many_assets"]

    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()

    for asset in assets:
        if not isinstance(asset, Mapping):
            problems.append("manifest:asset_not_object")
            continue
        problems.extend(validate_asset(asset, language=language))
        asset_id = asset.get("id")
        if isinstance(asset_id, str):
            if asset_id in seen_ids:
                problems.append(f"asset {asset_id}:duplicate_asset_id")
            seen_ids.add(asset_id)
        path = asset.get("playbackFile")
        if isinstance(path, str):
            if path in seen_paths:
                problems.append(f"asset {asset_id}:duplicate_asset_path")
            seen_paths.add(path)

    # A role map that names an asset the pack does not contain would fail on the
    # terminal at announcement time, which is the worst possible moment.
    roles = manifest.get("roles")
    if isinstance(roles, Mapping):
        for lang, ids in roles.items():
            if not isinstance(ids, (list, tuple)):
                continue
            for asset_id in ids:
                if isinstance(asset_id, str) and asset_id not in seen_ids:
                    problems.append(f"roles {lang}:unknown_asset_reference:{asset_id}")

    return problems


def _manifest_assets(manifest: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    assets = (manifest or {}).get("assets") if isinstance(manifest, Mapping) else None
    return ([a for a in assets if isinstance(a, Mapping)]
            if isinstance(assets, list) else [])


def validate_pack_upload(upload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a whole voice-pack upload without touching the database.

    Returns ``{"ok", "problems", "assets", "bytes", "checksums"}``.  It never
    raises on hostile input: every refusal becomes a problem code, so the caller
    can answer 422 with a complete list instead of stopping at the first fault.

    What is actually checked (assignment §6):

    * the pack id and every manifest path against a strict charset, so a path can
      never escape the pack root (path traversal, filename injection);
    * the real container from the file's own bytes versus the declared extension,
      so a renamed executable is not accepted as ``.mp3``;
    * decodability of the declared payload (base64), a per-asset and per-pack
      size ceiling, and non-empty content;
    * SHA-256 of every file against **both** the file entry's own checksum and
      the manifest's checksum, so neither a mistyped upload nor a manifest that
      describes different audio than was uploaded can pass (B-10);
    * duplicate and orphan references: a file the manifest does not mention, a
      required asset that was not uploaded, a duplicate id or duplicate path;
    * the metadata required before a human is asked to review the pack.

    A successful validation says nothing about *activation*: the pack stays
    ``draft`` and cannot be selected until it has passed validation, been
    approved by a named reviewer and been published (assignment §6, §7).
    """
    problems: list[str] = []
    source = upload if isinstance(upload, Mapping) else {}

    pack_id = source.get("id")
    if not isinstance(pack_id, str) or not PACK_ID_RE.match(pack_id):
        problems.append("pack:invalid_id")

    language = source.get("language")
    if language not in LANGUAGES:
        problems.append("pack:invalid_language")
        language = None

    for name in ("voice_name", "description", "personality"):
        if not isinstance(source.get(name), str) or not source.get(name).strip():
            problems.append(f"pack:missing_{name}")

    manifest = source.get("manifest")
    if language:
        problems.extend(validate_manifest(manifest, language=language))
    assets = _manifest_assets(manifest)
    manifest_paths = {a.get("playbackFile") for a in assets
                      if isinstance(a.get("playbackFile"), str)}
    manifest_checksums = {a.get("playbackFile"): a.get("playbackChecksum")
                          for a in assets}

    files = source.get("files")
    if files is None:
        files = []
    if not isinstance(files, list):
        problems.append("files:not_a_list")
        files = []

    seen: dict[str, str] = {}
    paths_seen: set[str] = set()
    total_bytes = 0
    for entry in files:
        if not isinstance(entry, Mapping):
            problems.append("file:not_an_object")
            continue
        try:
            path = safe_relative_path(entry.get("path"), what="file path")
        except PolicyError as error:
            problems.append(f"file:{error.code}")
            continue
        if path in paths_seen:
            problems.append(f"file {path}:duplicate_file")
            continue
        paths_seen.add(path)

        data = decode_payload(entry.get("contentBase64"))
        if data is None:
            problems.append(f"file {path}:invalid_payload")
            continue
        if not data:
            problems.append(f"file {path}:empty_payload")
            continue
        if len(data) > MAX_ASSET_BYTES:
            problems.append(f"file {path}:asset_too_large")
            continue
        total_bytes += len(data)

        container = sniff_container(data)
        if container is None:
            problems.append(f"file {path}:unrecognised_container")
            continue
        extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        expected = EXTENSION_CONTAINER.get(extension)
        if expected is None:
            problems.append(f"file {path}:unsupported_extension")
        elif expected != container:
            # The bytes are the truth: a .mp3 that is really a WAV is refused
            # rather than relabelled.
            problems.append(f"file {path}:extension_mismatch")

        actual = sha256_hex(data)
        # Both declarations are checked (B-10).  A file entry's own `checksum`
        # says "this is the audio I meant to upload"; the manifest's
        # `playbackChecksum` says "this is the audio a reviewer approved".
        # Accepting one *or* the other let a self-consistent file entry carry
        # bytes that the approved manifest never described.
        declared = entry.get("checksum")
        if declared and str(declared).strip().lower() != actual:
            problems.append(f"file {path}:checksum_mismatch")
        approved = manifest_checksums.get(path)
        if approved and str(approved).strip().lower() != actual:
            problems.append(f"file {path}:manifest_checksum_mismatch")
        seen[path] = actual

        if manifest_paths and path not in manifest_paths:
            problems.append(f"file {path}:orphan_asset")

    for asset in assets:
        if asset.get("required") is True:
            path = asset.get("playbackFile")
            if isinstance(path, str) and path not in paths_seen:
                problems.append(f"asset {asset.get('id')}:missing_required_asset")

    if total_bytes > MAX_PACK_BYTES:
        problems.append("pack:too_large")

    unique = list(dict.fromkeys(problems))
    return {"ok": not unique, "problems": unique,
            "assets": len(seen), "bytes": total_bytes,
            "checksums": seen}


def pack_descriptor(pack: Mapping[str, Any],
                    base_path: str | None = None) -> dict[str, Any]:
    """The descriptor W1's player and W5's installer already understand.

    ``normalisePack`` in ``frontend/lib/announcements/segments.js`` reads exactly
    these keys, so a server pack reaches the existing playback engine without the
    engine changing (assignment §7: keep the W1 interface compatible).
    ``basePath`` points at the authenticated asset route unless the pack declares
    one — organisation packs are never public URLs.
    """
    manifest = pack.get("manifest")
    manifest = manifest if isinstance(manifest, Mapping) else {}
    pack_id = pack.get("id") or ""
    owner = pack_owner(pack)
    return {
        "id": pack_id,
        "language": pack.get("language") or "",
        "version": int(pack.get("version") or 0),
        "scope": "organization" if owner else "platform",
        "organizationId": owner,
        "basePath": (base_path or pack.get("base_path")
                     or f"/api/v1/voice-packs/{pack_id}/assets"),
        "status": pack.get("status") or PACK_STATUS["DRAFT"],
        "roles": manifest.get("roles"),
        "manifest": manifest,
        "assets": _manifest_assets(manifest),
    }
