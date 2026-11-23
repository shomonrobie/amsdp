"""QUE-006 / W3 — the voice configuration API and its permission boundary.

Companion to ``test_voice_pack_policy.py``: that module proves the rules in
isolation (and runs without a stack), this one proves the HTTP surface — the
denied-API matrix assignment §8 asks for, organisation isolation, inheritance,
rollback, and the fact that an upload cannot become active by itself.

Needs a live stack (``pytest`` + PostgreSQL).  On the verification host used for
the W3 report it could not be executed; the policy suite was run instead through
``scripts/que-006-w3-voice-config/check_voice_config.py``.
"""

import base64
import hashlib

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                                ensure_user, headers, load_app, purge_org)
from common.models import AuditEvent, Organization, PlatformAuditEvent
from organization import voice_pack_policy as policy
from organization import voice_packs as pack_module
from organization.voice_packs import VoicePack

ORG = "vpk-org"
OTHER_ORG = "vpk-other-org"
BR = "vpk-br"
OTHER_BR = "vpk-other-br"
SUPER = "vpk_super"
ADMIN = "vpk_admin"
OTHER_ADMIN = "vpk_other_admin"
BRANCH_ADMIN = "vpk_bradm"
RECP = "vpk_recp"
DOCTOR = "vpk_doctor"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("organization"))


@pytest.fixture(scope="module")
def pack_root(tmp_path_factory):
    return tmp_path_factory.mktemp("voice-packs")


@pytest.fixture(autouse=True)
def _world(client, pack_root, monkeypatch):
    monkeypatch.setattr(pack_module, "PACK_ROOT", str(pack_root))
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(SUPER, "super_admin", ORG, BR)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "org_admin", OTHER_ORG, OTHER_BR)
    ensure_user(BRANCH_ADMIN, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(DOCTOR, "doctor", ORG, BR)
    _clear()
    yield
    _clear()
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _clear():
    """Remove packs and configuration blocks, never audit rows.

    The audit trail is append-only; a test that deleted trail rows to simplify an
    assertion would be testing a system that cannot exist.
    """
    with db_session() as s:
        s.query(VoicePack).delete()
        for org_id in (ORG, OTHER_ORG):
            org = s.query(Organization).filter(Organization.id == org_id).first()
            if org:
                config = dict(org.config or {})
                config.pop("announcement", None)
                org.config = config
        s.commit()


def wav(payload=b"\x00" * 32):
    return (b"RIFF" + (36 + len(payload)).to_bytes(4, "little")
            + b"WAVEfmt " + payload)


def upload_body(pack_id, language="en", version=None, *, voice="female-1",
                organization_id=None, path=None, data=None, checksum=None):
    audio = data if data is not None else wav()
    digest = hashlib.sha256(audio).hexdigest()
    relative = path or f"{language}/phrase/token-number.wav"
    manifest = {"version": "1.0", "language": language, "assets": [{
        "id": f"{language}.phrase.token-number", "language": language,
        "category": "phrase", "playbackFile": relative,
        "playbackChecksum": checksum or digest, "required": True}]}
    return {
        "id": pack_id, "language": language, "voice_name": voice,
        "description": "test voice", "personality": "calm",
        "version": version, "manifest": manifest,
        "compatibility": {"manifestSchema": "1.0"},
        "files": [{"path": relative,
                   "contentBase64": base64.b64encode(audio).decode("ascii"),
                   "checksum": digest}],
        "organization_id": organization_id,
    }


def create_pack(client, user, **kwargs):
    response = client.post("/api/v1/voice-packs", headers=headers(user),
                           json=upload_body(**kwargs))
    assert response.status_code == 201, response.text
    return response.json()


def publish(client, pack_id):
    """Walk a pack through the full lifecycle, as the platform administrator."""
    assert client.post(f"/api/v1/voice-packs/{pack_id}/validate",
                       headers=headers(SUPER)).status_code == 200
    assert client.post(f"/api/v1/voice-packs/{pack_id}/approve",
                       headers=headers(SUPER),
                       json={"note": "listened end to end"}).status_code == 200
    assert client.post(f"/api/v1/voice-packs/{pack_id}/publish",
                       headers=headers(SUPER)).status_code == 200
    return pack_id


def org_config_url(org_id=ORG):
    return f"/api/v1/orgs/{org_id}/announcement-config"


def platform_config_url():
    return "/api/v1/platform/announcement-config"


def release_platform_pack(client, pack_id, language="en"):
    """Create a platform pack, publish it, and release it to organisations."""
    create_pack(client, SUPER, pack_id=pack_id, language=language)
    publish(client, pack_id)
    response = client.post(f"/api/v1/voice-packs/{pack_id}/availability",
                           headers=headers(SUPER), json={"available": True})
    assert response.status_code == 200, response.text
    return pack_id


# ---------------------------------------------------------------------------
# §8.1–§8.6: who may configure, and whose organisation
# ---------------------------------------------------------------------------

class TestWhoMayConfigure:

    def test_the_platform_administrator_manages_platform_defaults(self, client):
        pack = release_platform_pack(client, "platform-en-female-1")
        response = client.put(platform_config_url(), headers=headers(SUPER),
                              json={"language": "en",
                                    "voice_packs": {"en": pack}})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["language"] == "en"
        assert body["voice_packs"]["en"] == pack

        reread = client.get(platform_config_url(), headers=headers(SUPER)).json()
        assert reread["voice_packs"]["en"] == pack
        assert reread["updated_by"]

    def test_an_organisation_administrator_manages_only_its_own(self, client):
        pack = create_pack(client, ADMIN, pack_id="org-en-1",
                           organization_id=ORG)
        publish(client, pack["id"])

        ok = client.put(org_config_url(), headers=headers(ADMIN),
                        json={"language": "en",
                              "voice_packs": {"en": pack["id"]}})
        assert ok.status_code == 200, ok.text
        assert ok.json()["organization"]["voice_packs"]["en"] == pack["id"]

        foreign = client.put(org_config_url(OTHER_ORG), headers=headers(ADMIN),
                             json={"language": "en"})
        assert foreign.status_code == 404, foreign.text

    def test_a_branch_administrator_is_rejected(self, client):
        assert client.put(org_config_url(), headers=headers(BRANCH_ADMIN),
                          json={"language": "en"}).status_code == 403
        assert client.put(platform_config_url(), headers=headers(BRANCH_ADMIN),
                          json={"language": "en"}).status_code == 403
        assert client.post("/api/v1/voice-packs",
                           headers=headers(BRANCH_ADMIN),
                           json=upload_body("branch-pack",
                                            organization_id=ORG)
                           ).status_code == 403
        # ... and cannot even read the configuration screen.
        assert client.get(org_config_url(),
                          headers=headers(BRANCH_ADMIN)).status_code == 403

    def test_receptionists_and_doctors_are_rejected(self, client):
        for user in (RECP, DOCTOR):
            assert client.put(org_config_url(), headers=headers(user),
                              json={"language": "en"}).status_code == 403, user
            assert client.post("/api/v1/voice-packs", headers=headers(user),
                               json=upload_body("nope", organization_id=ORG)
                               ).status_code == 403, user
            assert client.post(
                "/api/v1/voice-packs/x/approve", headers=headers(user),
                json={}).status_code == 403, user

    def test_an_organisation_administrator_cannot_touch_platform_defaults(
            self, client):
        assert client.get(platform_config_url(),
                          headers=headers(ADMIN)).status_code == 403
        assert client.put(platform_config_url(), headers=headers(ADMIN),
                          json={"language": "en"}).status_code == 403
        # A platform-scoped pack upload is refused as well.
        assert client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                           json=upload_body("platform-pack-1")
                           ).status_code == 403

    def test_cross_organisation_access_is_a_non_disclosing_404(self, client):
        pack = create_pack(client, OTHER_ADMIN, pack_id="other-en-1",
                           organization_id=OTHER_ORG)
        publish(client, pack["id"])

        assert client.get(org_config_url(OTHER_ORG),
                          headers=headers(ADMIN)).status_code == 404
        assert client.get(f"/api/v1/voice-packs/{pack['id']}/manifest",
                          headers=headers(ADMIN)).status_code == 404
        # The foreign pack cannot be selected either, and the refusal does not
        # disclose whose pack it is.
        refused = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": pack["id"]}})
        assert refused.status_code == 422, refused.text
        assert policy.SELECTION_WARNING["NOT_FOUND"] in refused.text


# ---------------------------------------------------------------------------
# §8.7–§8.9, §8.15: inheritance, independent languages, unusable packs
# ---------------------------------------------------------------------------

class TestConfiguration:

    def test_english_and_bangla_are_chosen_independently(self, client):
        en_pack = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-2", organization_id=ORG)["id"])
        bn_pack = release_platform_pack(client, "platform-bn-female-1",
                                        language="bn")

        response = client.put(org_config_url(), headers=headers(ADMIN),
                              json={"voice_packs": {"en": en_pack,
                                                    "bn": bn_pack}})
        assert response.status_code == 200, response.text
        resolved = response.json()["resolved"]
        assert resolved["voice_packs"]["en"] == en_pack
        assert resolved["sources"]["en"] == "organization"
        assert resolved["voice_packs"]["bn"] == bn_pack

    def test_an_organisation_without_an_override_inherits_platform_defaults(
            self, client):
        pack = release_platform_pack(client, "platform-en-female-2")
        assert client.put(platform_config_url(), headers=headers(SUPER),
                          json={"language": "en",
                                "voice_packs": {"en": pack}}
                          ).status_code == 200

        view = client.get(org_config_url(), headers=headers(ADMIN)).json()
        assert view["organization"] == {}, "nothing stored for this organisation"
        assert view["resolved"]["language"] == "en"
        assert view["resolved"]["voice_packs"]["en"] == pack
        assert view["resolved"]["sources"]["en"] == "platform"

    def test_an_override_replaces_the_inherited_default(self, client):
        platform_pack = release_platform_pack(client, "platform-en-female-3")
        client.put(platform_config_url(), headers=headers(SUPER),
                   json={"voice_packs": {"en": platform_pack}})
        own = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-3", organization_id=ORG)["id"])

        view = client.put(org_config_url(), headers=headers(ADMIN),
                          json={"voice_packs": {"en": own}}).json()
        assert view["resolved"]["voice_packs"]["en"] == own
        assert view["resolved"]["sources"]["en"] == "organization"

        # Clearing the override restores inheritance for that language only.
        cleared = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": None}}).json()
        assert cleared["resolved"]["voice_packs"]["en"] == platform_pack
        assert cleared["resolved"]["sources"]["en"] == "platform"

    def test_a_retired_or_unpublished_pack_cannot_be_selected(self, client):
        unpublished = create_pack(client, ADMIN, pack_id="org-en-4",
                                  organization_id=ORG)["id"]
        refused = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": unpublished}})
        assert refused.status_code == 422, refused.text
        assert policy.SELECTION_WARNING["NOT_PUBLISHED"] in refused.text

        retired = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-5", organization_id=ORG)["id"])
        assert client.post(f"/api/v1/voice-packs/{retired}/retire",
                           headers=headers(SUPER)).status_code == 200
        refused = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": retired}})
        assert refused.status_code == 422, refused.text

    def test_a_platform_pack_that_was_not_released_cannot_be_selected(
            self, client):
        create_pack(client, SUPER, pack_id="platform-en-female-4")
        publish(client, "platform-en-female-4")   # published, not released
        refused = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": "platform-en-female-4"}})
        assert refused.status_code == 422, refused.text
        assert policy.SELECTION_WARNING["NOT_AVAILABLE"] in refused.text


# ---------------------------------------------------------------------------
# §8.10–§8.11, §8.14: versions, rollback, and no activation without approval
# ---------------------------------------------------------------------------

class TestLifecycleAndVersions:

    def test_previous_versions_remain_available(self, client):
        first = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-v1", organization_id=ORG)["id"])
        second = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-v2", version=2,
            organization_id=ORG)["id"])

        packs = client.get("/api/v1/voice-packs", headers=headers(ADMIN)).json()
        ids = {p["id"] for p in packs["packs"]}
        assert {first, second} <= ids
        versions = [p["version"] for p in packs["packs"]
                    if p["voice_name"] == "female-1" and p["language"] == "en"]
        assert sorted(versions) == [1, 2]

        # Re-using a version number is refused rather than overwriting.
        duplicate = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                                json=upload_body("org-en-v2-again", version=2,
                                                 organization_id=ORG))
        assert duplicate.status_code == 409, duplicate.text

    def test_rollback_selects_the_intended_approved_version(self, client):
        first = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-rb1", organization_id=ORG)["id"])
        second = publish(client, create_pack(
            client, ADMIN, pack_id="org-en-rb2", version=2,
            organization_id=ORG)["id"])
        assert client.put(org_config_url(), headers=headers(ADMIN),
                          json={"voice_packs": {"en": second}}
                          ).status_code == 200

        rolled = client.post(f"{org_config_url()}/rollback",
                             headers=headers(ADMIN), json={"language": "en"})
        assert rolled.status_code == 200, rolled.text
        body = rolled.json()
        assert body["rolled_back_from"] == second
        assert body["rolled_back_to"] == first
        assert body["resolved"]["voice_packs"]["en"] == first

    def test_nothing_becomes_active_without_validation_review_and_publication(
            self, client):
        pack = create_pack(client, ADMIN, pack_id="org-en-gate",
                           organization_id=ORG)["id"]

        # Straight from draft to published is refused.
        assert client.post(f"/api/v1/voice-packs/{pack}/publish",
                           headers=headers(SUPER)).status_code == 409
        # The organisation cannot approve its own pack, nor publish it.
        assert client.post(f"/api/v1/voice-packs/{pack}/approve",
                           headers=headers(ADMIN),
                           json={"note": "looks good"}).status_code == 403
        assert client.post(f"/api/v1/voice-packs/{pack}/publish",
                           headers=headers(ADMIN)).status_code == 403
        # Nothing about it is selectable yet.
        assert client.put(org_config_url(), headers=headers(ADMIN),
                          json={"voice_packs": {"en": pack}}
                          ).status_code == 422

        # The upload passed technical validation, so the organisation may submit
        # it for review — and submission is the only step it may take.
        assert client.post(f"/api/v1/voice-packs/{pack}/submit",
                           headers=headers(ADMIN)).status_code == 200
        # Publication still refuses until a named reviewer approves.
        assert client.post(f"/api/v1/voice-packs/{pack}/publish",
                           headers=headers(SUPER)).status_code == 409
        approved = client.post(f"/api/v1/voice-packs/{pack}/approve",
                               headers=headers(SUPER),
                               json={"note": "listened end to end"})
        assert approved.status_code == 200, approved.text
        assert approved.json()["reviewed_by"]
        assert client.post(f"/api/v1/voice-packs/{pack}/publish",
                           headers=headers(SUPER)).status_code == 200
        assert client.put(org_config_url(), headers=headers(ADMIN),
                          json={"voice_packs": {"en": pack}}
                          ).status_code == 200

    def test_changes_are_audited_in_the_right_trail(self, client):
        pack = release_platform_pack(client, "platform-en-audit")
        assert client.put(platform_config_url(), headers=headers(SUPER),
                          json={"voice_packs": {"en": pack}}
                          ).status_code == 200

        with db_session() as s:
            platform_events = s.query(PlatformAuditEvent).filter(
                PlatformAuditEvent.action.in_(["announcement_config.platform_updated",
                                               "voice_pack.published"])).all()
            org_events = s.query(AuditEvent).filter(
                AuditEvent.action == "announcement_config.updated").all()
        assert platform_events, "platform changes belong in platform_audit_events"
        assert org_events is not None, "organisation changes belong in audit_events"


# ---------------------------------------------------------------------------
# §8.12–§8.13: preview has no side effects; invalid uploads are refused
# ---------------------------------------------------------------------------

class TestUploadAndPreview:

    def test_preview_does_not_change_the_configuration(self, client):
        pack = release_platform_pack(client, "platform-en-preview")
        config_before = client.get(org_config_url(),
                                   headers=headers(ADMIN)).json()

        preview = client.get(f"/api/v1/voice-packs/{pack}/preview",
                             headers=headers(ADMIN))
        assert preview.status_code == 200, preview.text
        body = preview.json()
        assert body["descriptor"]["id"] == pack
        assert body["descriptor"]["basePath"].endswith("/assets")
        assert body["selectable"] is True

        config_after = client.get(org_config_url(),
                                  headers=headers(ADMIN)).json()
        assert config_after["organization"] == config_before["organization"]
        assert config_after["resolved"] == config_before["resolved"]

    def test_an_invalid_upload_is_refused_and_stores_nothing(self, client):
        body = upload_body("org-en-bad", organization_id=ORG,
                           path="../escape.wav")
        refused = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                              json=body)
        assert refused.status_code == 422, refused.text
        assert "path_traversal" in refused.text

        packs = client.get("/api/v1/voice-packs", headers=headers(ADMIN)).json()
        assert "org-en-bad" not in {p["id"] for p in packs["packs"]}

    def test_a_renamed_non_audio_file_is_refused(self, client):
        binary = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
        body = upload_body("org-en-binary", organization_id=ORG, data=binary,
                           path="en/phrase/token-number.wav")
        refused = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                              json=body)
        assert refused.status_code == 422, refused.text
        assert "unrecognised_container" in refused.text

# ---------------------------------------------------------------------------
# B-1 (QUE-006 integration trial) — the upload path answers, it never raises
# ---------------------------------------------------------------------------

class TestUploadContract:
    """The upload endpoint's observable contract, pinned around the B-1 defect.

    ``validate_pack_upload`` returns ``assets`` as a **count** of distinct
    stored paths (``voice_pack_policy.py``). The trial-merge investigation found
    the creation audit reason calling ``len()`` on it, so an upload that had
    already passed every check raised
    ``TypeError: object of type 'int' has no len()`` and answered 500 — 13 W3
    API tests failed for that one line, not because of the merge seam.

    These tests fail on that defect and on any later change that stops a
    validated upload from answering 201 with a counted summary.
    """

    def test_a_valid_upload_answers_201_with_a_counted_summary(self, client):
        audio = wav()
        response = client.post("/api/v1/voice-packs", headers=headers(SUPER),
                               json=upload_body("b1-platform-1"))
        assert response.status_code == 201, response.text
        body = response.json()

        # A validated upload is registered, never activated.
        assert body["status"] == "draft"
        assert body["review_status"] == "pending"
        assert body["available_to_organizations"] is False
        assert body["organization_id"] is None
        assert isinstance(body["next"], str) and body["next"]

        validation = body["validation"]
        assert validation["status"] == "pass"
        assert validation["problems"] == []
        # The exact value B-1 wrapped in `len()`: a count, not a container.
        assert isinstance(validation["assets"], int)
        assert validation["assets"] == 1
        assert validation["bytes"] == len(audio)

    def test_the_creation_reason_counts_the_assets_it_stored(self, client):
        audio = wav(b"\x00" * 40)
        response = client.post("/api/v1/voice-packs", headers=headers(SUPER),
                               json=upload_body("b1-platform-2", data=audio))
        assert response.status_code == 201, response.text

        with db_session() as s:
            event = s.query(PlatformAuditEvent).filter(
                PlatformAuditEvent.action == "voice_pack.created",
                PlatformAuditEvent.target_id == "b1-platform-2@1").first()
        assert event is not None, "the creation is recorded in the platform trail"
        assert event.reason == f"1 asset(s), {len(audio)} byte(s) uploaded"
        assert event.actor_role == "super_admin"

    def test_an_organisation_upload_is_stamped_with_its_own_scope(self, client):
        audio = wav(b"\x00" * 24)
        response = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                               json=upload_body("b1-org-1", organization_id=ORG,
                                                data=audio))
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["organization_id"] == ORG
        assert body["validation"]["bytes"] == len(audio)
        assert body["validation"]["assets"] == 1

        with db_session() as s:
            event = s.query(AuditEvent).filter(
                AuditEvent.action == "voice_pack.created",
                AuditEvent.target_id == "b1-org-1@1").first()
        assert event is not None, "a tenant pack is a tenant event"
        assert event.organization_id == ORG
        assert event.reason == f"1 asset(s), {len(audio)} byte(s) uploaded"

    def test_an_invalid_upload_is_a_refusal_not_a_crash(self, client):
        body = upload_body("b1-org-bad", organization_id=ORG)
        wrong = hashlib.sha256(b"audio that was never uploaded").hexdigest()
        body["files"][0]["checksum"] = wrong
        body["manifest"]["assets"][0]["playbackChecksum"] = wrong
        response = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                               json=body)
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert detail["message"] == "voice pack upload failed validation"
        assert any("checksum_mismatch" in problem
                   for problem in detail["problems"]), detail["problems"]
        # A refused upload stores nothing and writes no asset.
        with db_session() as s:
            assert s.query(VoicePack).filter(
                VoicePack.id == "b1-org-bad").first() is None

    def test_an_upload_for_another_organisation_is_a_non_disclosing_404(
            self, client):
        response = client.post("/api/v1/voice-packs", headers=headers(ADMIN),
                               json=upload_body("b1-foreign", organization_id=OTHER_ORG))
        assert response.status_code == 404, response.text
        # The refusal names neither the pack nor the organisation it belongs to.
        assert "b1-foreign" not in response.text
        assert OTHER_ORG not in response.text
        with db_session() as s:
            assert s.query(VoicePack).filter(
                VoicePack.id == "b1-foreign").first() is None

    def test_a_branch_administrator_cannot_upload(self, client):
        response = client.post("/api/v1/voice-packs", headers=headers(BRANCH_ADMIN),
                               json=upload_body("b1-branch", organization_id=ORG))
        assert response.status_code == 403, response.text
        with db_session() as s:
            assert s.query(VoicePack).filter(
                VoicePack.id == "b1-branch").first() is None


# ---------------------------------------------------------------------------
# B-2 (QUE-006 integration trial) — a cross-tenant refusal discloses nothing
# ---------------------------------------------------------------------------

class TestCrossTenantRefusalsDoNotDisclose:
    """A foreign pack and an absent pack must be indistinguishable.

    The B-1 fix removed the ``TypeError`` that had been hiding this path: the
    organisation PUT check was handed *every* pack, so naming another tenant's
    pack answered ``pack_foreign_organization`` while naming a pack that never
    existed answered ``pack_not_found`` — an existence oracle. Both now answer
    the same refusal (§3: cross-tenant access fails closed, non-disclosing).
    """

    def test_a_foreign_pack_and_an_absent_pack_get_the_same_refusal(self, client):
        other = create_pack(client, OTHER_ADMIN, pack_id="b2-other-en",
                            organization_id=OTHER_ORG)
        publish(client, other["id"])

        foreign = client.put(org_config_url(), headers=headers(ADMIN),
                             json={"voice_packs": {"en": other["id"]}})
        absent = client.put(org_config_url(), headers=headers(ADMIN),
                            json={"voice_packs": {"en": "b2-no-such-pack"}})

        assert foreign.status_code == 422, foreign.text
        assert absent.status_code == 422, absent.text
        assert foreign.text == absent.text, "the refusal must not identify the pack"
        assert OTHER_ORG not in foreign.text
        assert other["id"] not in foreign.text


