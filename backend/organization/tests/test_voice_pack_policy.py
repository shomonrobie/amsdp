"""QUE-006 / W3 — the policy engine behind language and voice configuration.

These tests exercise the rules that decide *who* may change voice configuration,
*which* pack is in force, *what* may become selectable, and *what* an upload is
allowed to contain.  They are written as plain functions with no fixtures so that
they run under pytest in CI **and** under the dependency-free checker in this
checkout, where FastAPI/SQLAlchemy/pytest are not installed:

    python scripts/que-006-w3-voice-config/check_voice_config.py

The HTTP surface is covered separately by ``test_voice_packs_api.py``, which needs
a live stack.
"""

import base64
import hashlib

from organization import voice_pack_policy as policy

PUBLISHED = policy.PACK_STATUS["PUBLISHED"]
ORG_A = "org-a"
ORG_B = "org-b"
REVIEWER = "user-platform-reviewer"


def pack(pack_id, language, version=1, *, status=PUBLISHED, owner=None,
         available=True, voice="female-1", **extra):
    """A pack row in the shape the policy layer reads."""
    row = {
        "id": pack_id,
        "language": language,
        "voice_name": voice,
        "version": version,
        "status": status,
        "organization_id": owner,
        "available_to_organizations": available,
        "description": "test voice",
        "personality": "calm",
        "manifest": {"version": "1.0", "assets": []},
        "compatibility": {"manifestSchema": "1.0"},
        "validation_status": "pass",
        "review_status": "approved",
        "reviewed_by": REVIEWER,
        "reviewed_at": "2026-11-21T00:00:00+00:00",
        "published_by": REVIEWER,
        "published_at": "2026-11-21T00:00:00+00:00",
        "created_at": "2026-11-21T00:00:00+00:00",
        "updated_at": "2026-11-21T00:00:00+00:00",
    }
    row.update(extra)
    return row


def raises(call, *, status=None, code=None):
    """Assert that *call* raises :class:`policy.PolicyError` with the given shape."""
    try:
        call()
    except policy.PolicyError as error:
        if status is not None:
            assert error.status == status, (error.status, error.detail)
        if code is not None:
            assert error.code == code, (error.code, error.detail)
        return error
    raise AssertionError("expected a PolicyError, none was raised")


# ---------------------------------------------------------------------------
# 1–6: permissions and organisation scope (assignment §3.1, §9.1–§9.6)
# ---------------------------------------------------------------------------

def test_platform_scope_is_available_to_the_platform_admin_only():
    assert policy.may("configure_platform", "super_admin") is True

    for role in ("org_admin", "branch_admin", "receptionist", "doctor", "assistant"):
        assert policy.may("configure_platform", role) is False, role

    raises(lambda: policy.resolve_scope("org_admin", ORG_A, None),
           status=403, code="platform_scope_forbidden")


def test_an_org_admin_may_configure_only_its_own_organisation():
    assert policy.may("configure_organization", "org_admin") is True
    scope = policy.resolve_scope("org_admin", ORG_A, ORG_A)
    assert scope == {"scope": "organization", "organization_id": ORG_A}


def test_a_foreign_organisation_is_a_non_disclosing_404():
    # The tenant gate derives the organisation from the token, so a payload that
    # names another tenant must not be confirmed to exist.
    raises(lambda: policy.resolve_scope("org_admin", ORG_A, ORG_B),
           status=404, code="organization_not_found")


def test_every_non_configuring_role_is_refused():
    for role in ("branch_admin", "receptionist", "doctor", "assistant"):
        assert policy.may("configure_organization", role) is False, role
        assert policy.may("manage_pack", role) is False, role
        assert policy.may("approve_pack", role) is False, role
        assert policy.may("publish_pack", role) is False, role
        raises(lambda role=role: policy.require("configure_organization", role),
               status=403, code="forbidden")


def test_reading_does_not_become_configuring():
    # Reading configuration follows the ordinary organization-read capability, and
    # configuration authority is never derived from it.  Two facts worth pinning:
    # an organisation administrator may read *and* configure; a branch
    # administrator — who does hold other configuration-like capabilities such as
    # ``facility.manage`` and ``symptom.manage`` — holds no ``org.read`` at all,
    # because the announcement configuration is organization-wide.  So voice
    # configuration is invisible to it as well as unwritable.
    assert policy.may("read", "org_admin") is True
    assert policy.may("read", "branch_admin") is False
    assert policy.may("read", "receptionist") is False
    assert policy.may("configure_organization", "branch_admin") is False


def test_managing_other_configuration_does_not_imply_voice_configuration():
    # A role that may curate symptoms or facilities must still not reach the
    # announcement voice settings; the capability is checked, not inferred.
    from common.permissions import check

    assert check("symptom.manage", "branch_admin") is True
    assert check("facility.manage", "branch_admin") is True
    assert policy.may("configure_organization", "branch_admin") is False


def test_an_org_admin_cannot_administer_a_platform_pack():
    raises(lambda: policy.require_pack_access(
        pack_organization_id=None, role="org_admin", caller_organization_id=ORG_A),
        status=404, code="pack_not_found")
    # ... nor another organisation's pack, and the refusal does not disclose it.
    raises(lambda: policy.require_pack_access(
        pack_organization_id=ORG_B, role="org_admin", caller_organization_id=ORG_A),
        status=404, code="pack_not_found")
    # ... but may reach its own, and the platform admin may reach any.
    policy.require_pack_access(pack_organization_id=ORG_A, role="org_admin",
                               caller_organization_id=ORG_A)
    policy.require_pack_access(pack_organization_id=ORG_B, role="super_admin",
                               caller_organization_id=ORG_A)


def test_the_platform_admin_may_configure_a_tenant_when_support_requires_it():
    scope = policy.resolve_scope("super_admin", ORG_A, ORG_B)
    assert scope["organization_id"] == ORG_B


# ---------------------------------------------------------------------------
# 7–12: inheritance, overrides, independent languages, versioning (§3.2–§3.4)
# ---------------------------------------------------------------------------

def test_english_and_bangla_are_selected_independently():
    packs = [pack("vp_org_en_v1", "en", owner=ORG_A),
             pack("vp_platform_bn_v1", "bn")]
    resolved = policy.resolve_config(
        {"language": "bn", "voice_packs": {"en": "vp_platform_en_v1"}},
        {"language": "en", "voice_packs": {"en": "vp_org_en_v1",
                                           "bn": "vp_platform_bn_v1"}},
        packs, ORG_A)
    assert resolved["language"] == "en", "the organisation language wins"
    assert resolved["voice_packs"]["en"] == "vp_org_en_v1"
    assert resolved["sources"]["en"] == "organization"
    assert resolved["voice_packs"]["bn"] == "vp_platform_bn_v1"
    assert resolved["sources"]["bn"] == "organization"


def test_an_organisation_without_overrides_inherits_the_platform_defaults():
    packs = [pack("vp_platform_en_v2", "en", version=2),
             pack("vp_platform_bn_v3", "bn", version=3)]
    resolved = policy.resolve_config(
        {"language": "bn", "voice_packs": {"en": "vp_platform_en_v2",
                                           "bn": "vp_platform_bn_v3"}},
        {}, packs, ORG_A)
    assert resolved["language"] == "bn"
    assert resolved["sources"] == {"bn": "platform", "en": "platform"}
    assert resolved["voice_packs"]["en"] == "vp_platform_en_v2"
    assert resolved["warnings"] == []


def test_the_organisation_override_wins_over_the_platform_default():
    packs = [pack("vp_platform_en_v1", "en"),
             pack("vp_org_en_v4", "en", version=4, owner=ORG_A, voice="male-2")]
    resolved = policy.resolve_config(
        {"voice_packs": {"en": "vp_platform_en_v1"}},
        {"voice_packs": {"en": "vp_org_en_v4"}},
        packs, ORG_A)
    assert resolved["voice_packs"]["en"] == "vp_org_en_v4"
    assert resolved["sources"]["en"] == "organization"


def test_another_organisations_pack_is_refused_and_reported():
    packs = [pack("vp_org_b_en_v1", "en", owner=ORG_B)]
    resolved = policy.resolve_config(
        {}, {"voice_packs": {"en": "vp_org_b_en_v1"}}, packs, ORG_A)
    assert resolved["voice_packs"]["en"] is None
    assert resolved["sources"]["en"] == "none"
    reasons = [w["reason"] for w in resolved["warnings"]]
    assert policy.SELECTION_WARNING["FOREIGN_ORGANIZATION"] in reasons
    assert policy.SELECTION_WARNING["NO_PACK"] in reasons


def test_a_retired_or_unpublished_pack_is_never_selected():
    for status in ("draft", "validating", "pending_review", "approved",
                   "retired", "rejected"):
        ok, reason = policy.check_selectable(pack("vp_x", "en", status=status),
                                            "en", ORG_A)
        assert ok is False, status
        assert reason == policy.SELECTION_WARNING["NOT_PUBLISHED"], status


def test_an_unreleased_platform_pack_is_not_selectable_by_an_organisation():
    withheld = pack("vp_platform_en_v1", "en", available=False)
    ok, reason = policy.check_selectable(withheld, "en", ORG_A)
    assert ok is False
    assert reason == policy.SELECTION_WARNING["NOT_AVAILABLE"]

    resolved = policy.resolve_config({}, {"voice_packs": {"en": "vp_platform_en_v1"}},
                                     [withheld], ORG_A)
    assert resolved["voice_packs"]["en"] is None


def test_a_language_mismatch_is_a_refusal_not_a_reroute():
    packs = [pack("vp_en", "en")]
    resolved = policy.resolve_config({}, {"voice_packs": {"bn": "vp_en"}}, packs, ORG_A)
    assert resolved["voice_packs"]["bn"] is None
    assert resolved["warnings"][0]["reason"] == policy.SELECTION_WARNING["LANGUAGE_MISMATCH"]


def test_the_default_language_is_documented_not_guessed():
    resolved = policy.resolve_config({"language": "fr"}, {"language": "de"}, [], ORG_A)
    assert resolved["language"] == policy.DEFAULT_LANGUAGE == "bn"


def test_versions_increase_and_are_never_reused():
    assert policy.next_version([]) == 1
    assert policy.next_version([1, 2]) == 3
    assert policy.next_version(["1", "4"]) == 5
    older = pack("vp_a", "en", version=1, owner=ORG_A)
    newer = pack("vp_b", "en", version=2, owner=ORG_A)
    assert [p["version"] for p in policy.versions_of([older, newer], language="en",
                                                     family="female-1")] == [2, 1]


def test_rollback_chooses_the_previous_published_version():
    current = pack("vp_v3", "en", version=3, owner=ORG_A)
    previous = pack("vp_v2", "en", version=2, owner=ORG_A)
    draft = pack("vp_v4", "en", version=4, owner=ORG_A,
                 status=policy.PACK_STATUS["DRAFT"])
    target = policy.rollback_target([current, previous, draft], language="en",
                                    organization_id=ORG_A,
                                    current_pack_id="vp_v3")
    assert target is not None and target["id"] == "vp_v2"


def test_rollback_never_lands_on_a_pack_the_organisation_cannot_use():
    foreign = pack("vp_foreign_v1", "en", version=1, owner=ORG_B)
    retired = pack("vp_retired_v1", "en", version=2, owner=ORG_A,
                   status=policy.PACK_STATUS["RETIRED"])
    assert policy.rollback_target([foreign, retired], language="en",
                                  organization_id=ORG_A,
                                  current_pack_id=None) is None


# ---------------------------------------------------------------------------
# 13–15: lifecycle, human review and immutability (§3.5, §6, §7)
# ---------------------------------------------------------------------------

def test_an_upload_success_is_not_an_activation():
    draft = pack("vp_org_en_v1", "en", owner=ORG_A,
                 status=policy.PACK_STATUS["DRAFT"],
                 validation_status="unvalidated", review_status="pending",
                 reviewed_by=None, reviewed_at=None)
    # Nothing about a draft is selectable, whatever an upload managed to store.
    ok, reason = policy.check_selectable(draft, "en", ORG_A)
    assert ok is False
    assert reason == policy.SELECTION_WARNING["NOT_PUBLISHED"]


def test_technical_validation_cannot_approve_a_pack():
    draft = pack("vp_org_en_v1", "en", owner=ORG_A,
                 status=policy.PACK_STATUS["DRAFT"],
                 validation_status="unvalidated", review_status="pending",
                 reviewed_by=None, reviewed_at=None)
    updates = policy.transition(draft, "validate", role="org_admin",
                                now="2026-11-21T10:00:00+00:00", problems=[])
    assert updates["status"] == policy.PACK_STATUS["PENDING_REVIEW"]
    assert updates["validation_status"] == "pass"
    assert "reviewed_by" not in updates, "validation never records a reviewer"


def test_a_failing_validation_rejects_the_pack():
    draft = pack("vp_org_en_v1", "en", owner=ORG_A,
                 status=policy.PACK_STATUS["DRAFT"],
                 validation_status="unvalidated", review_status="pending",
                 reviewed_by=None, reviewed_at=None)
    updates = policy.transition(draft, "validate", role="org_admin",
                                problems=["file en/x.mp3:checksum_mismatch"])
    assert updates["status"] == policy.PACK_STATUS["REJECTED"]
    assert updates["validation_status"] == "fail"
    assert updates["validation_problems"] == ["file en/x.mp3:checksum_mismatch"]


def test_an_organisation_administrator_cannot_approve_its_own_pack():
    pending = pack("vp_org_en_v1", "en", owner=ORG_A,
                   status=policy.PACK_STATUS["PENDING_REVIEW"],
                   review_status="pending", reviewed_by=None, reviewed_at=None)
    raises(lambda: policy.transition(pending, "approve", role="org_admin",
                                     reviewer_id=REVIEWER,
                                     now="2026-11-21T10:00:00+00:00"),
           status=403, code="forbidden")


def test_approval_requires_a_named_human_reviewer():
    pending = pack("vp_org_en_v1", "en", owner=ORG_A,
                   status=policy.PACK_STATUS["PENDING_REVIEW"],
                   review_status="pending", reviewed_by=None, reviewed_at=None)
    raises(lambda: policy.transition(pending, "approve", role="super_admin"),
           status=422, code="human_review_required")

    updates = policy.transition(pending, "approve", role="super_admin",
                                reviewer_id=REVIEWER,
                                now="2026-11-21T10:00:00+00:00",
                                review_note="listened to all 28 assets")
    assert updates["status"] == policy.PACK_STATUS["APPROVED"]
    assert updates["review_status"] == "approved"
    assert updates["reviewed_by"] == REVIEWER
    assert updates["reviewed_at"] == "2026-11-21T10:00:00+00:00"


def test_publication_requires_validation_and_approval():
    # Not validated yet.
    approved_but_unvalidated = pack("vp_a", "en", owner=ORG_A,
                                    status=policy.PACK_STATUS["APPROVED"],
                                    validation_status="unvalidated")
    raises(lambda: policy.transition(approved_but_unvalidated, "publish",
                                     role="super_admin", actor_id=REVIEWER,
                                     now="2026-11-21T10:00:00+00:00"),
           status=409, code="validation_required")

    # Validated but nobody approved it.
    unreviewed = pack("vp_b", "en", owner=ORG_A,
                      status=policy.PACK_STATUS["APPROVED"],
                      review_status="pending", reviewed_by=None)
    raises(lambda: policy.transition(unreviewed, "publish", role="super_admin",
                                     now="2026-11-21T10:00:00+00:00"),
           status=409, code="approval_required")

    # Correct order succeeds and records who published it.
    approved = pack("vp_c", "en", owner=ORG_A,
                    status=policy.PACK_STATUS["APPROVED"])
    updates = policy.transition(approved, "publish", role="super_admin",
                                actor_id=REVIEWER,
                                now="2026-11-21T11:00:00+00:00")
    assert updates["status"] == PUBLISHED
    assert updates["published_by"] == REVIEWER
    assert updates["published_at"] == "2026-11-21T11:00:00+00:00"


def test_a_draft_cannot_be_published_directly():
    draft = pack("vp_d", "en", owner=ORG_A, status=policy.PACK_STATUS["DRAFT"])
    raises(lambda: policy.transition(draft, "publish", role="super_admin",
                                     now="2026-11-21T11:00:00+00:00"),
           status=409, code="invalid_transition")


def test_submission_requires_a_passing_validation():
    draft = pack("vp_e", "en", owner=ORG_A, status=policy.PACK_STATUS["DRAFT"],
                 validation_status="unvalidated")
    raises(lambda: policy.transition(draft, "submit", role="org_admin"),
           status=409, code="validation_required")

    validated = pack("vp_f", "en", owner=ORG_A,
                     status=policy.PACK_STATUS["DRAFT"], validation_status="pass")
    updates = policy.transition(validated, "submit", role="org_admin")
    assert updates["status"] == policy.PACK_STATUS["PENDING_REVIEW"]


def test_validation_and_submission_are_alternatives_not_a_sequence():
    """Both end in ``pending_review``; only one of them applies to a given pack.

    A pack that validates at upload is submitted straight away; a pack whose
    validation failed can be re-validated later.  Trying to do both is refused, so
    the state machine cannot be driven in a circle by a client.
    """
    validated_at_upload = pack(
        "vp_n", "en", owner=ORG_A, status=policy.PACK_STATUS["DRAFT"],
        validation_status="pass")
    submitted = dict(validated_at_upload)
    submitted.update(policy.transition(validated_at_upload, "submit",
                                       role="org_admin"))
    assert submitted["status"] == policy.PACK_STATUS["PENDING_REVIEW"]

    raises(lambda: policy.transition(submitted, "submit", role="org_admin"),
           status=409, code="invalid_transition")
    raises(lambda: policy.transition(submitted, "validate", role="org_admin",
                                     problems=[]),
           status=409, code="invalid_transition")


def test_a_published_version_is_immutable():
    published = pack("vp_g", "en", owner=ORG_A)
    raises(lambda: policy.assert_mutable(published), status=409,
           code="pack_immutable")
    # A draft may still be replaced.
    policy.assert_mutable(pack("vp_h", "en", status=policy.PACK_STATUS["DRAFT"]))


def test_retirement_keeps_the_row_and_records_when():
    published = pack("vp_i", "en", owner=ORG_A)
    updates = policy.transition(published, "retire", role="super_admin",
                                now="2026-11-21T12:00:00+00:00")
    assert updates["status"] == policy.PACK_STATUS["RETIRED"]
    assert updates["retired_at"] == "2026-11-21T12:00:00+00:00"
    assert "published_at" not in updates, "retirement does not rewrite publication"


def test_metadata_completeness_is_checked_explicitly():
    complete = pack("vp_j", "en", owner=ORG_A)
    assert policy.missing_metadata(complete) == []

    incomplete = pack("vp_k", "en", owner=ORG_A, description="",
                      personality=None, compatibility=None)
    missing = policy.missing_metadata(incomplete)
    for name in ("description", "personality", "compatibility"):
        assert name in missing, name

    # A published pack must say who published it; an approved one who reviewed it.
    published_without_publisher = pack("vp_l", "en", owner=ORG_A,
                                       status=PUBLISHED, published_by=None)
    assert "published_by" in policy.missing_metadata(published_without_publisher)

    approved_without_reviewer = pack("vp_m", "en", owner=ORG_A,
                                     status=policy.PACK_STATUS["APPROVED"],
                                     reviewed_by=None)
    assert "reviewed_by" in policy.missing_metadata(approved_without_reviewer)


# ---------------------------------------------------------------------------
# 16: upload validation and security (assignment §6)
# ---------------------------------------------------------------------------

def wav_bytes(padding=16):
    """A minimal, recognisable RIFF/WAVE payload.

    Only the container signature is inspected — this server runs no audio decoder
    — so the tests assert exactly what the code asserts, and no more.
    """
    return (b"RIFF" + (36 + padding).to_bytes(4, "little")
            + b"WAVEfmt " + b"\x00" * padding)


def asset(asset_id, path, checksum=None, required=True, language="en"):
    return {"id": asset_id, "language": language, "category": "phrase",
            "playbackFile": path, "playbackChecksum": checksum,
            "required": required}


def upload_payload(**overrides):
    data = wav_bytes()
    digest = hashlib.sha256(data).hexdigest()
    payload = {
        "id": "org-acme-en-female-v1",
        "language": "en",
        "voice_name": "female-1",
        "description": "warm female English",
        "personality": "calm",
        "manifest": {"version": "1.0", "language": "en",
                     "assets": [asset("en.phrase.token-number",
                                      "en/phrase/token-number.wav", digest)]},
        "files": [{"path": "en/phrase/token-number.wav",
                   "contentBase64": base64.b64encode(data).decode("ascii"),
                   "checksum": digest}],
    }
    payload.update(overrides)
    return payload


def problems_of(payload):
    return policy.validate_pack_upload(payload)["problems"]


def test_a_well_formed_upload_passes_validation():
    result = policy.validate_pack_upload(upload_payload())
    assert result["ok"] is True, result["problems"]
    assert result["assets"] == 1
    assert result["bytes"] > 0
    assert len(result["checksums"]["en/phrase/token-number.wav"]) == 64


def test_a_path_that_escapes_the_pack_root_is_refused():
    for bad in ("../etc/passwd.mp3", "en/../../secret.mp3", "/etc/passwd.mp3",
                "C:/windows/system32/evil.mp3", "en\\phrase\\x.mp3"):
        payload = upload_payload()
        payload["manifest"]["assets"][0]["playbackFile"] = bad
        payload["files"][0]["path"] = bad
        found = problems_of(payload)
        assert any("path_traversal" in p or "invalid_path" in p for p in found), (bad, found)


def test_a_file_that_is_not_the_format_its_name_claims_is_refused():
    payload = upload_payload()
    payload["files"][0]["path"] = "en/phrase/token-number.mp3"
    payload["manifest"]["assets"][0]["playbackFile"] = "en/phrase/token-number.mp3"
    found = problems_of(payload)
    assert any("extension_mismatch" in p for p in found), found


def test_a_non_audio_payload_is_refused():
    binary = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
    payload = upload_payload()
    payload["files"][0]["contentBase64"] = base64.b64encode(binary).decode("ascii")
    payload["files"][0]["checksum"] = hashlib.sha256(binary).hexdigest()
    payload["manifest"]["assets"][0]["playbackChecksum"] = None
    found = problems_of(payload)
    assert any("unrecognised_container" in p for p in found), found


def test_a_checksum_that_does_not_match_the_bytes_is_refused():
    payload = upload_payload()
    payload["manifest"]["assets"][0]["playbackChecksum"] = "0" * 64
    payload["files"][0]["checksum"] = None
    found = problems_of(payload)
    assert any("checksum_mismatch" in p for p in found), found


def test_invalid_base64_is_refused_rather_than_guessed():
    payload = upload_payload()
    payload["files"][0]["contentBase64"] = "not base64 !!"
    found = problems_of(payload)
    assert any("invalid_payload" in p for p in found), found


def test_a_required_asset_that_was_not_uploaded_is_refused():
    payload = upload_payload()
    payload["files"] = []
    found = problems_of(payload)
    assert any("missing_required_asset" in p for p in found), found


def test_a_file_the_manifest_does_not_mention_is_refused():
    payload = upload_payload()
    extra = wav_bytes()
    payload["files"].append({
        "path": "en/phrase/sneaky.wav",
        "contentBase64": base64.b64encode(extra).decode("ascii")})
    found = problems_of(payload)
    assert any("orphan_asset" in p for p in found), found


def test_duplicate_paths_and_ids_are_refused():
    payload = upload_payload()
    payload["manifest"]["assets"].append(
        asset("en.phrase.token-number", "en/phrase/token-number.wav",
              hashlib.sha256(wav_bytes()).hexdigest()))
    found = problems_of(payload)
    assert any("duplicate_asset_id" in p for p in found), found
    assert any("duplicate_asset_path" in p for p in found), found


def test_a_manifest_asset_in_the_wrong_language_is_refused():
    payload = upload_payload()
    payload["manifest"]["assets"][0]["language"] = "bn"
    found = problems_of(payload)
    assert any("language_mismatch" in p for p in found), found


def test_an_unusable_pack_id_is_refused():
    for bad in ("../org", "org/acme", ".hidden", "", "x" * 100):
        found = problems_of(upload_payload(id=bad))
        assert "pack:invalid_id" in found, (bad, found)


def test_incomplete_metadata_is_refused_before_a_human_sees_the_pack():
    found = problems_of(upload_payload(personality=""))
    assert "pack:missing_personality" in found, found


def test_an_oversized_asset_is_refused():
    payload = upload_payload()
    payload["files"][0]["contentBase64"] = base64.b64encode(
        wav_bytes(policy.MAX_ASSET_BYTES)).decode("ascii")
    payload["manifest"]["assets"][0]["playbackChecksum"] = None
    payload["files"][0]["checksum"] = None
    found = problems_of(payload)
    assert any("asset_too_large" in p for p in found), found


def test_validation_never_raises_on_hostile_input():
    # A validator that throws on malformed input turns a 422 into a 500, which
    # is how upload endpoints leak stack traces and filesystem paths.
    for hostile in (None, {}, {"manifest": None}, {"files": "nope"},
                    {"manifest": {"assets": "nope"}},
                    {"manifest": {"assets": [None, 1, "x"]}},
                    {"id": 5, "language": [], "files": [None, 5]}):
        result = policy.validate_pack_upload(hostile)
        assert isinstance(result["problems"], list) and result["problems"]
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Compatibility with W1/W5 and with the existing frontend vocabulary
# ---------------------------------------------------------------------------

def test_the_descriptor_matches_the_w1_player_contract():
    row = pack("org-acme-en-female-v1", "en", owner=ORG_A, voice="female-1")
    descriptor = policy.pack_descriptor(row)
    for key in ("id", "language", "version", "scope", "organizationId",
                "basePath", "status", "roles", "manifest", "assets"):
        assert key in descriptor, key
    assert descriptor["scope"] == "organization"
    assert descriptor["organizationId"] == ORG_A
    assert descriptor["basePath"] == ("/api/v1/voice-packs/"
                                      "org-acme-en-female-v1/assets")
    # A platform pack reports the platform scope, not an empty organisation.
    platform_pack = policy.pack_descriptor(pack("platform-en-female-v1", "en"))
    assert platform_pack["scope"] == "platform"
    assert platform_pack["organizationId"] is None


def test_building_a_preview_descriptor_does_not_mutate_the_pack():
    # "Preview a voice pack without changing production configuration" (§3.3):
    # the preview is a pure function of the stored row.
    row = pack("vp_preview", "en", owner=ORG_A)
    before = dict(row)
    policy.pack_descriptor(row)
    assert row == before


def test_browser_speech_is_never_a_substitute_for_a_missing_pack():
    assert policy.ALLOW_SYNTHESIS_FALLBACK is False
    resolved = policy.resolve_config({}, {}, [], ORG_A)
    assert resolved["voice_packs"] == {"bn": None, "en": None}
    assert {warning["reason"] for warning in resolved["warnings"]} == {"no_voice_pack"}


def test_the_client_and_server_share_one_vocabulary():
    """The refusal codes the server reports are the ones the UI already knows.

    Read from the frontend module rather than restated, so the two halves cannot
    drift apart without this failing.
    """
    from pathlib import Path

    path = (Path(__file__).resolve().parents[3]
            / "frontend" / "lib" / "announcements" / "voice-packs.js")
    if not path.exists():          # backend-only checkout: nothing to compare
        return
    source = path.read_text(encoding="utf-8")
    client_codes = [code for code in policy.SELECTION_WARNING.values()
                    if code not in policy.SERVER_ONLY_WARNING]
    assert len(client_codes) == len(policy.SELECTION_WARNING) - 1
    for code in client_codes:
        assert code in source, code
    for status in policy.STATUSES:
        assert f"'{status}'" in source, status
    assert "resolveAnnouncementConfig" in source
