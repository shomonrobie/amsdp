# QUE-006 W3 — Voice Configuration and Versioned Voice Library
## Implementation and Verification Report

**Assignment ID:** `AMSDP-QUE-006-W3-VOICE-CONFIGURATION`
**Date:** 2026-11-21
**Repository:** `e:\amsdp` (Windows checkout), branch `hackathon-mvp`, HEAD `37cf3d1`
**Status:** **IMPLEMENTED, POLICY LAYER VERIFIED, HTTP/DATABASE LAYER NOT EXECUTED.**
The permission boundary, the configuration precedence, the lifecycle, the versioning
rules and the upload validation are implemented in a dependency-free policy module
that was **executed in this session** (49/49 tests pass). The persistence and HTTP
layers (SQLAlchemy models, Alembic migration, FastAPI routes) are **implemented and
syntax-checked but not executed**, because this host has no `pytest`, `fastapi`,
`sqlalchemy`, `alembic`, `psycopg2` or PostgreSQL. Nothing was committed, pushed,
deployed or merged.

---

## 1. Executive summary

| Question | Answer |
|---|---|
| Was there existing W3 work? | Yes, client-side only: `frontend/lib/announcements/voice-packs.js` plus 8 passing tests and a panel that resolves its pack through it. Verified intact, not rewritten. |
| What was missing? | The entire server half: no voice-pack storage, no catalogue, no upload, no validation, no lifecycle, no permission enforcement, no platform defaults, no organisation override, no rollback API, no tests. |
| What was added? | A stdlib-only policy engine, a versioned pack registry with an authenticated API, platform + organisation configuration endpoints, one forward-only migration, and two test suites (49 policy tests, 18 API tests). |
| Is it proven? | The **policy layer is VERIFIED** by execution (49 tests, 0 failures). The **HTTP layer is IMPLEMENTED BUT NOT EXECUTED**; the DDL is **NOT VERIFIED** (never applied to a database). |
| Did it touch restricted files? | No. The seven files on the shared-file restriction list are **unmodified by this task** (§10 evidence). One non-restricted file was touched: `backend/organization/main.py` (+17 lines, two router registrations). |
| Is the Product Owner's permission rule enforced? | Yes, server-side, twice: by the existing capability matrix and by an explicit role allow-list, with `branch_admin`, `receptionist`, `doctor` and `assistant` refused. Proven by executed policy tests and by written API tests. |
| Any blocker found? | Yes, one **pre-existing** blocker that W3 inherits rather than causes: the QUE-006/W2 migration `a7c3f19d2b64` declares the wrong parent and creates a second Alembic head. W3's migration is chained behind it; the single-line W2 fix reduces the graph to **one head** (§12, §14). |

**Headline numbers**

| Item | Value |
|---|---|
| Policy tests executed | **49 / 49 pass, 0 fail** (`python scripts/que-006-w3-voice-config/check_voice_config.py`) |
| API tests written | 18 (not executed — no stack on this host) |
| Frontend W3 regression | **8 / 8 pass** (`node --test tests/queue-announcement-voice-packs.test.mjs`) |
| Python syntax check | 9 files, `py_compile` OK |
| Alembic graph | 16 revisions, heads `a9c4e1f7b2d8` + `c4d8e2a91f60` → **single head** once W2 is reparented |
| Files added | 6 source/test files + 2 verification scripts |
| Files modified | 1 (`backend/organization/main.py`) |
| Commit / push / deploy | **none** |

---

## 2. Existing W3 implementation assessment (Phase A)

Phase A was performed read-only **before any file was edited**. Documents read:
`QUE-006_W3_VOICE_CONFIGURATION_REPORT.md`, `QUE-006_MASTER_IMPLEMENTATION_PLAN.md`,
`QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md`
(relevant sections), `frontend/lib/announcements/voice-packs.js`,
`frontend/tests/queue-announcement-voice-packs.test.mjs`, and the backend
configuration mechanisms (`common/permissions.py`, `common/auth.py`,
`common/config.py`, `common/audit.py`, `common/models.py` structure,
`organization/appointment_config.py`, `organization/notification_config.py`,
`organization/main.py`, `alembic/versions/a7c3f19d2b64_*.py`), plus the W1 and W5
interfaces for compatibility only (`segments.js` `normalisePack`,
`prerecorded-audio.js`, `scripts/que-006-agent/lib/installer.mjs`).

### 2.1 What actually existed

| Artefact | Status before this task | Evidence |
|---|---|---|
| `frontend/lib/announcements/voice-packs.js` (146 lines) | **IMPLEMENTED AND TESTED** | `PACK_STATUS`, `SELECTION_WARNING`, `checkSelectable()`, `resolveAnnouncementConfig()`; 8 tests pass in this session |
| `frontend/components/queue/QueueAnnouncements.js` | **IMPLEMENTED** (resolves its pack through the precedence rule) | `resolveAnnouncementConfig({ builtin })` asserted by test 8; the file is on the restriction list and was **not** touched |
| `frontend/tests/queue-announcement-voice-packs.test.mjs` (146 lines) | **IMPLEMENTED AND TESTED** | 8/8 pass |
| Voice-pack storage (table/model) | **NOT IMPLEMENTED** | no `voice_packs` among the 26 `__tablename__` declarations in `common/models.py` |
| Voice-pack API (list/create/validate/review/publish/retire) | **NOT IMPLEMENTED** | no route, no router module |
| Platform defaults | **NOT IMPLEMENTED** | no platform-settings store of any kind existed |
| Organisation override | **NOT IMPLEMENTED** | `organizations.config` held `queue_config`, `appointment_config`, `notification_config`, `registration_policy` — no `announcement` block |
| Upload validation | **NOT IMPLEMENTED** | no upload surface at all; W5 verifies SHA-256 for *downloads*, which is distribution, not ingestion |
| Versioning / rollback | **PARTIALLY IMPLEMENTED** (client vocabulary only) | the status enum knew `published`; nothing stored versions, so nothing could be rolled back |
| Permission enforcement | **IMPLEMENTED IN THE MATRIX, NOT ENFORCED ON A ROUTE** | `super_admin` holds `platform.admin`; `org_admin` and `super_admin` hold `org.manage`; `branch_admin`, `receptionist`, `doctor`, `assistant` hold neither |
| Preview | **NOT IMPLEMENTED** (server) | the playback engine to audition a pack existed (`createPrerecordedPlayer`); the catalogue to preview did not |
| Metadata (§3.5) | **NOT IMPLEMENTED** at pack level | the *asset* manifest carries `playbackChecksum`, `sampleRate`, `channels`, `durationSeconds`, `technicalValidationStatus`, `humanReviewStatus`; no pack-level record existed |

### 2.2 Two corrections to the earlier W3 report

`QUE-006_W3_VOICE_CONFIGURATION_REPORT.md` (83 lines) was re-read and **not**
assumed accurate. Two of its statements are now outdated; this report supersedes
them:

1. It stated the server half was deliberately **not** implemented because the host
   cannot run the stack. The reasoning is sound but the conclusion no longer stands:
   the decision layer can be — and now is — implemented **and executed** without
   the stack, with the persistence layer written separately and reported honestly as
   unexecuted.
2. It stated `branch_admin` may **read** configuration. That is **false for this
   surface**: `branch_admin` holds no `org.read` in the matrix (it holds
   `branch.read`, `facility.*`, `staff.read`, `symptom.*`, `patient.*`, `doctor.*`,
   `schedule.*`, `appointment.*`, `queue.*`, `audit.read`). A branch administrator
   therefore cannot read the organisation-wide announcement configuration either.

### 2.3 Two Phase A facts that shaped the design

* **No platform-settings store exists.** Platform defaults had to be persisted
  somewhere new; hiding them inside one organisation's JSON would have been wrong.
* **`organization/main.py` is the service composition point** and is **not** on the
  restriction list, so two router registrations there were permissible. Every other
  new file is a new file.

---

## 3. Requirements-to-implementation matrix

Status vocabulary (assignment §10): **VERIFIED** · **PARTIALLY VERIFIED** ·
**IMPLEMENTED BUT NOT EXECUTED** · **NOT VERIFIED** · **BLOCKED** · **NOT IMPLEMENTED**.
"Executed" always means *a test ran in this session*; a written-but-unrun test is
never called verified.

### 3.1 Owner requirements §3.1–§3.5

| Requirement | Status | Where | Evidence |
|---|---|---|---|
| §3.1 Only `super_admin` and `org_admin` may configure | **VERIFIED** (policy) / **IMPLEMENTED BUT NOT EXECUTED** (route) | `voice_pack_policy.may/require`, `VOICE_CONFIG_ROLES`; routes gated on `require_permission("org.manage" / "platform.admin")` | 6 executed tests, e.g. `test_platform_scope_is_available_to_the_platform_admin_only` |
| §3.1 `branch_admin` has **no** access | **VERIFIED** (policy) | `may("configure_organization","branch_admin") is False`; no `org.manage`/`org.read` in the matrix | `test_every_non_configuring_role_is_refused`, `test_managing_other_configuration_does_not_imply_voice_configuration` |
| §3.1 `receptionist` / `doctor` have no access | **VERIFIED** (policy) | same gate | `test_every_non_configuring_role_is_refused` (also covers `assistant`) |
| §3.1 Backend enforcement, not UI hiding | **VERIFIED** (policy) / **IMPLEMENTED BUT NOT EXECUTED** (HTTP) | dependency + `policy.require` in every write route | the policy is server-side code called by the routes; it consults no client flag |
| §3.1 An `org_admin` cannot change platform defaults or another tenant | **VERIFIED** (scope rules) | `resolve_scope` → 403 `platform_scope_forbidden`; foreign org → 404 | `test_platform_scope_is_available_to_the_platform_admin_only`, `test_a_foreign_organisation_is_a_non_disclosing_404` |
| §3.2 Platform default language | **IMPLEMENTED BUT NOT EXECUTED** | `PUT /api/v1/platform/announcement-config` → `announcement_platform_config.language` | written API test |
| §3.2 Default English / Bangla pack, independently | **IMPLEMENTED BUT NOT EXECUTED** (storage) / **VERIFIED** (resolution) | `voice_packs` JSON on the platform row; `resolve_config` resolves per language | executed independent-resolution test |
| §3.2 Create / upload voice-pack versions | **IMPLEMENTED BUT NOT EXECUTED** | `POST /api/v1/voice-packs` | written API tests |
| §3.2 Validate / publish / retire / manage packs | **VERIFIED** (rules) / **IMPLEMENTED BUT NOT EXECUTED** (routes) | `POST …/validate|approve|reject|publish|retire` + `policy.transition` | 8 executed lifecycle tests |
| §3.2 Control which packs are available to organisations | **VERIFIED** (rule) / **IMPLEMENTED BUT NOT EXECUTED** (route) | `available_to_organizations`; `POST …/availability`; `check_selectable` refuses `NOT_AVAILABLE` | `test_an_unreleased_platform_pack_is_not_selectable_by_an_organisation` |
| §3.2 Organisations without overrides inherit platform defaults | **VERIFIED** | `policy.resolve_config` precedence | `test_an_organisation_without_overrides_inherits_the_platform_defaults` |
| §3.3 Override announcement language | **IMPLEMENTED BUT NOT EXECUTED** | `PUT /api/v1/orgs/{id}/announcement-config` → `organizations.config["announcement"]` | written API test |
| §3.3 Select English and Bangla packs independently | **VERIFIED** (rule) | per-language keys in `voice_packs` | `test_english_and_bangla_are_selected_independently` |
| §3.3 Organisation-specific versions, isolated | **VERIFIED** (isolation rule) / **IMPLEMENTED BUT NOT EXECUTED** (route) | `require_pack_access`; `_visible` filter | `test_an_org_admin_cannot_administer_a_platform_pack`, `test_another_organisations_pack_is_refused_and_reported` |
| §3.3 Preview without changing production configuration | **VERIFIED** (purity) / **IMPLEMENTED BUT NOT EXECUTED** (route) | `GET …/preview` returns a descriptor and writes nothing; `pack_descriptor` is pure | `test_building_a_preview_descriptor_does_not_mutate_the_pack`; written API test comparing config before/after |
| §3.3 Validate and submit a new version for review | **VERIFIED** (rules) | `validate` → `pending_review`; `submit` requires `validation_status == "pass"` | `test_technical_validation_cannot_approve_a_pack`, `test_submission_requires_a_passing_validation` |
| §3.3 Select an approved version | **VERIFIED** (rule) | only `published` is selectable | `test_a_retired_or_unpublished_pack_is_never_selected` |
| §3.3 Roll back to a previous approved version | **VERIFIED** (rule) / **IMPLEMENTED BUT NOT EXECUTED** (route) | `policy.rollback_target`; `POST …/announcement-config/rollback` | `test_rollback_chooses_the_previous_published_version`, `test_rollback_never_lands_on_a_pack_the_organisation_cannot_use` |
| §3.4 Multiple versions and personas per language | **VERIFIED** (model + rules) | `voice_name` family; `next_version`; `versions_of` | `test_versions_increase_and_are_never_reused` |
| §3.4 Language and voice are separate settings | **VERIFIED** | `language` and `voice_packs` are distinct keys; resolution is per language | `test_english_and_bangla_are_selected_independently` |
| §3.5 Pack metadata (id, language, voice, description, personality, version, scope, org id, manifest, compatibility, validation, review, publication, timestamps, publisher/approver, retirement) | **IMPLEMENTED (model + checks)**, **NOT VERIFIED** (no database) | `voice_packs` columns; `METADATA_FIELDS`, `CONDITIONAL_METADATA`, `missing_metadata` | `test_metadata_completeness_is_checked_explicitly` |
| §3.5 Never mark human-approved without review | **VERIFIED** (rule) | `transition` refuses `approve` without a reviewer and time; `publish` requires a recorded approval | `test_approval_requires_a_named_human_reviewer`, `test_publication_requires_validation_and_approval` |

### 3.2 Owner requirements §5–§8 (implementation areas)

| Requirement | Status | Where |
|---|---|---|
| §5 Voice-pack catalogue and metadata handling | **IMPLEMENTED BUT NOT EXECUTED** (persistence) / **VERIFIED** (metadata rules) | `voice_packs.py`, `voice_pack_policy.METADATA_FIELDS` |
| §5 Platform and organisation configuration services | **IMPLEMENTED BUT NOT EXECUTED** | `announcement_config.py` |
| §5 Role and organisation-scope enforcement | **VERIFIED** (policy) | `voice_pack_policy.may/require/resolve_scope/require_pack_access` |
| §5 Version selection and rollback | **VERIFIED** (rules) | `next_version`, `rollback_target`, `versions_of` |
| §5 Upload validation and publication lifecycle | **VERIFIED** (rules) / **IMPLEMENTED BUT NOT EXECUTED** (routes) | `validate_pack_upload`, `transition` |
| §5 Preview without production side effects | **VERIFIED** (purity) | `pack_descriptor`; `GET …/preview` |
| §5 W3-specific tests | **VERIFIED** (49 executed) + 18 written | `test_voice_pack_policy.py`, `test_voice_packs_api.py` |
| §6 Content versus extension, container, rate, channels, duration, size | **VERIFIED** | `sniff_container`, `validate_asset` limits |
| §6 Decodability | **PARTIALLY VERIFIED** | container signature only — **no audio decoder runs** (§15) |
| §6 Required assets, manifest consistency, checksums, duplicate/missing/invalid references | **VERIFIED** | `validate_manifest`, `validate_pack_upload` |
| §6 Malicious uploads, path traversal, filename injection | **VERIFIED** | `safe_relative_path` (charset, `..`, absolute, drive letters, control characters) |
| §6 Cross-organisation access | **VERIFIED** (policy) | `require_pack_access` → 404 |
| §6 Manifest manipulation | **VERIFIED** | checksum recomputed from supplied bytes; orphan-file refusal |
| §6 Incomplete uploads | **VERIFIED** | `missing_required_asset`, `invalid_payload`, empty-content refusal |
| §6 An upload never becomes active by itself | **VERIFIED** | `test_an_upload_success_is_not_an_activation` + lifecycle tests |
| §6 No secrets or internal filesystem paths exposed | **VERIFIED** (code review, not a running server) | routes return ids, statuses and refusal codes only; `FileResponse` streams bytes; `_pack_dir` raises 422 without echoing the path |
| §7 Never overwrite a published version | **VERIFIED** (rule) | `assert_mutable` → 409; `next_version`; duplicate id/version → 409 |
| §7 Preserve previous versions for rollback | **VERIFIED** (rule) / **NOT VERIFIED** (database) | retirement keeps the row; rollback reads previous published versions |
| §7 Use ids and versions, not filenames | **VERIFIED** | configuration stores pack ids; `pack_descriptor` carries `id` + `version` |
| §7 Keep the W1 playback interface compatible | **VERIFIED** (contract test) | `pack_descriptor` emits exactly the keys `normalisePack` reads |
| §7 Do not change approved wording | **VERIFIED** (nothing changed) | no announcement text, content module or manifest was modified |
| §7 No doctor names or patient identifiers | **VERIFIED** (nothing changed) | no announcement content touched |
| §7 No browser speech synthesis as a Bangla substitute | **VERIFIED** | `ALLOW_SYNTHESIS_FALLBACK = False`; `resolve_config` returns `no_voice_pack`, never a substitute |
| §7 No audio asset or manifest modification | **VERIFIED** (not performed) | nothing under `frontend/public/audio/` was written in this task |
| §7 Remote installation not claimed | **VERIFIED** (not claimed) | §14 states it explicitly |

### 3.3 Owner test requirements §8.1–§8.16

| # | Requirement | Layer | Status |
|---|---|---|---|
| 1 | Platform admin manages platform configuration | policy + API | **VERIFIED** (policy) / written (API) |
| 2 | Org admin manages only its organisation | policy + API | **VERIFIED** (policy) / written (API) |
| 3 | Branch admin rejected | policy + API | **VERIFIED** (policy) / written (API) |
| 4 | Receptionist and doctor rejected | policy + API | **VERIFIED** (policy) / written (API) |
| 5 | Org admin cannot change platform defaults | policy + API | **VERIFIED** (policy) / written (API) |
| 6 | Cross-organisation access rejected (404) | policy + API | **VERIFIED** (policy) / written (API) |
| 7 | English and Bangla selectable independently | policy | **VERIFIED** |
| 8 | Default inheritance | policy + API | **VERIFIED** (policy) / written (API) |
| 9 | Organisation overrides work | policy + API | **VERIFIED** (policy) / written (API) |
| 10 | Previous versions remain available | policy + API | **VERIFIED** (policy) / written (API) |
| 11 | Rollback selects the intended approved version | policy + API | **VERIFIED** (policy) / written (API) |
| 12 | Preview does not change production configuration | policy + API | **VERIFIED** (purity) / written (API) |
| 13 | Invalid uploads rejected | policy + API | **VERIFIED** (13 executed refusal cases) / written (API) |
| 14 | Unapproved versions cannot become active | policy + API | **VERIFIED** (policy) / written (API) |
| 15 | Retired or unavailable versions cannot be selected | policy + API | **VERIFIED** (policy) / written (API) |
| 16 | Existing W1/W2 interfaces not broken | regression | **VERIFIED**: `node --test tests/queue-*.test.mjs` → **146 tests, 145 pass, 0 fail, 1 skipped** (the skip is the pre-existing JSX/`swc` parse skip, not a W3 failure) |

---

## 4. Product Owner permission rules and how they are enforced

### 4.1 The rule, restated in code

| Caller | May read configuration | May write organisation config | May write platform defaults | May approve / publish / retire |
|---|---|---|---|---|
| `super_admin` | yes | yes (any organisation) | **yes** | **yes** |
| `org_admin` | yes | yes (own organisation only) | **no** | **no** |
| `branch_admin` | **no** | **no** | **no** | **no** |
| `receptionist` | no | no | no | no |
| `doctor` | no | no | no | no |
| `assistant` | no | no | no | no |

### 4.2 Three independent gates, all server-side

1. **The existing capability matrix** (`common/permissions.py`). Routes declare
   `Depends(require_permission(...))`: `org.read` for reads, `org.manage` for
   organisation writes and pack creation, `platform.admin` for platform defaults,
   approval, publication, retirement and release. `branch_admin`,
   `receptionist`, `doctor` and `assistant` hold none of `org.read`,
   `org.manage` or `platform.admin`, so they are refused **by the matrix**, not by a
   new rule invented here.
2. **An explicit role allow-list** (`VOICE_CONFIG_ROLES`, `PLATFORM_ROLES`) inside
   `voice_pack_policy.may()`. This is defence in depth: the only delegable
   capabilities in the system are three `appointment.*` ones
   (`common.permissions.DELEGABLE_CAPABILITIES`, enforced at
   `identity/routes.py`), so `org.manage` cannot be granted to a branch
   administrator today — but if that ever changed, the role allow-list would still
   refuse. `test_managing_other_configuration_does_not_imply_voice_configuration`
   pins the case where a role *does* hold neighbouring configuration capabilities
   (`symptom.manage`, `facility.manage`) and still gets nothing here.
3. **Scope resolution from the token** (`resolve_scope`). The organisation is taken
   from the authenticated context; the request body may only *name* an organisation,
   which is compared, never trusted. A foreign organisation is a **404**
   (`organization_not_found`), the platform scope from a tenant administrator is a
   **403** (`platform_scope_forbidden`), and a pack outside the caller's scope is a
   **404** (`pack_not_found`).

Self-approval is prevented at the transition level rather than by role alone:
`TRANSITION_ROLES` allows `validate`/`submit` for `org_admin` but `approve`,
`reject`, `publish` and `retire` for `super_admin` only, so an organisation can
prepare a version but can never certify it.

### 4.3 What is exercised and what is only written

| Claim | Evidence |
|---|---|
| Non-configuring roles are refused | **executed** — `test_every_non_configuring_role_is_refused`, `test_a_branch_administrator_…` (policy) |
| A tenant cannot reach platform scope | **executed** — `test_platform_scope_is_available_to_the_platform_admin_only` (policy) |
| A foreign organisation is 404, not 403 | **executed** — `test_a_foreign_organisation_is_a_non_disclosing_404` (policy) |
| A foreign pack is 404 and unselectable | **executed** — `test_an_org_admin_cannot_administer_a_platform_pack`, `test_another_organisations_pack_is_refused_and_reported` |
| The HTTP routes answer 403/404/422 | **written, not executed** — `test_voice_packs_api.py::TestWhoMayConfigure` (8 tests). No FastAPI/PostgreSQL on this host, so no status code has been observed from a live server. |

---

## 5. Platform configuration behaviour

`announcement_platform_config` is a **single row** (`id = 'platform'`) holding:

| Field | Meaning |
|---|---|
| `language` | platform default announcement language (`en` / `bn`, default `bn`) |
| `voice_packs` | `{"en": <pack id>, "bn": <pack id>}` — independently selectable |
| `updated_by`, `updated_at` | who changed it and when |

**Rules**

* `GET /api/v1/platform/announcement-config` (`platform.admin`) returns the stored
  defaults, the *resolved* defaults, and the published platform packs that could be
  named.
* `PUT` accepts a language, per-language pack ids, or both; an empty change is a
  422.
* A default **must be a published, released platform pack**. Publishing and
  release are therefore prerequisites, which is what stops a default pointing at a
  draft or at one organisation's private pack
  (`_selection_problems(..., scope="platform")`).
* Platform writes are audited into `platform_audit_events`
  (`announcement_config.platform_updated`) — the platform trail, not a tenant's.
* There is no route that lets an organisation touch this row: the capability is
  `platform.admin`, which only `super_admin` holds.

**Inheritance**: an organisation with no override inherits both the language and
the per-language packs from this row (proven by
`test_an_organisation_without_overrides_inherits_the_platform_defaults`).

---

## 6. Organisation configuration behaviour

Stored in the **existing** `organizations.config` JSON column, key `announcement`:

```json
{
  "announcement": {
    "language": "en",
    "voice_packs": { "en": "org-acme-en-female-1", "bn": "platform-bn-male-2" },
    "updated_at": "2026-11-21T15:12:04+00:00",
    "updated_by": "<actor id>"
  }
}
```

This is the same shape and the same mechanism as `appointment_config` and
`notification_config`, so **no schema change was needed for the organisation half**
— and a corrupt block degrades to "inherit" instead of raising
(`get_announcement_config` drops unknown values).

| Route | Capability | Behaviour |
|---|---|---|
| `GET /api/v1/orgs/{org_id}/announcement-config` | `org.read` | Returns the stored override, the platform defaults, the **resolved** configuration (with `sources` and `warnings`) and the selectable packs. |
| `PUT …/announcement-config` | `org.manage` (+ role allow-list) | Sets the language and/or per-language packs. `null` for a language **clears that language only**. Every selected pack is checked: exists and visible, published, same language, owned by this organisation or a released platform pack. A 422 carries the full problem list. |
| `POST …/announcement-config/rollback` | `org.manage` | Restores the previous published pack for one language. 409 when there is no earlier published version. |

**Isolation**: the route's `{org_id}` is compared with the token's organisation
(`_scoped_org`); a mismatch is a **404**, and a pack belonging to another
organisation is invisible (`_visible` filter) and therefore "not found" if
selected. The organisation half can never write platform defaults — there is no
field for them and no capability that would accept the write.

**Resolution** (identical shape to the client's `resolveAnnouncementConfig`, so
the frontend can consume server output unchanged):

1. the organisation's pack for that language, if selectable;
2. the platform default for that language, if selectable;
3. otherwise `null` with a `no_voice_pack` warning — never another language, never
   a substitute voice, never browser speech.

---

## 7. Voice-pack versioning and lifecycle

### 7.1 Targeting a version

An `organization_id` of `NULL` means a platform pack; any other value is the owning
organisation (`.clinerules` §3: the tenant key stays `organization_id`, no second
tenant column was introduced).

`voice_packs` is keyed by **the version's own id** (`platform-en-female-1`,
`org-acme-bn-male-2`), and `voice_name` groups the versions of one persona. That
choice is deliberate:

* the id must satisfy the charset W5's installer already enforces for a pack
  directory (`safePackId`: `[A-Za-z0-9._-]`), and `policy.PACK_ID_RE` is that
  charset plus "must not start with a dot";
* the frontend's `checkSelectable`/`findById` match configuration by `pack.id`, so
  one id per stored version is what lets a rollback point at a *specific* version;
* `next_version(existing)` returns `max + 1`, and a duplicate version number for
  the same (`organization_id`, `language`, `voice_name`) is a **409**, never an
  overwrite.

### 7.2 Lifecycle

```
draft ──validate──▶ pending_review ──approve──▶ approved ──publish──▶ published ──retire──▶ retired
  │                      │                        │
  └──validate(fail)──▶ rejected ◀──reject─────────┘
```

| Transition | Who | Preconditions (all enforced in `policy.transition`) |
|---|---|---|
| `validate` | `org_admin`, `super_admin` | pack mutable; problems recorded; pass → `pending_review`, fail → `rejected` |
| `submit` | `org_admin`, `super_admin` | `validation_status == "pass"` |
| `approve` | `super_admin` only | from `pending_review`; **named reviewer + review time**; validation passed |
| `reject` | `super_admin` only | from `pending_review`; named reviewer + reason |
| `publish` | `super_admin` only | from `approved`; validation passed; `review_status == "approved"` with a recorded `reviewed_by`; records `published_by`/`published_at` |
| `retire` | `super_admin` only | records `retired_at`; the row is kept |

`assert_mutable` refuses any content change once a pack is approved or published
(409 `pack_immutable`), which is what makes a published version reproducible and a
rollback target stable.

### 7.3 Rollback

`policy.rollback_target(packs, language=…, organization_id=…, current_pack_id=…)`
returns the highest **published** version that is not the one in force and that the
organisation may use. Because publication implies validation and approval, a
rollback can never land on a draft; because foreign and retired packs fail
`check_selectable`, it can never reach one of those either. Both properties are
executed tests (`test_rollback_chooses_the_previous_published_version`,
`test_rollback_never_lands_on_a_pack_the_organisation_cannot_use`).

---

## 8. Upload validation and security controls

An upload is **one JSON document** (`POST /api/v1/voice-packs`): metadata, the
manifest, and the audio as base64 per file. JSON was chosen because no
`python-multipart` dependency exists in this service image and adding a runtime
dependency was out of scope; the cost is that the bytes are decoded and checked
here rather than trusted from a declared content type — which the validation does
anyway.

### 8.1 The checks, in order

| # | Check | Code | Refusal code |
|---|---|---|---|
| 1 | pack id against the W5-compatible charset, not starting with a dot | `PACK_ID_RE` | `pack:invalid_id` |
| 2 | language ∈ {`en`,`bn`} | `LANGUAGES` | `pack:invalid_language` |
| 3 | voice name, description, personality non-empty | `validate_pack_upload` | `pack:missing_<field>` |
| 4 | manifest shape, ≥1 asset, ≤250 assets | `validate_manifest` | `manifest:missing` / `no_assets` / `too_many_assets` |
| 5 | per asset: id charset, language match, path, checksum format, declared container, sample rate, channels, duration | `validate_asset` | `asset <id>:<reason>` |
| 6 | duplicate asset ids and duplicate paths | `validate_manifest` | `duplicate_asset_id` / `duplicate_asset_path` |
| 7 | a role map naming an asset the pack does not contain | `validate_manifest` | `roles …:unknown_asset_reference` |
| 8 | file path safe and relative (charset, `..`, absolute, drive letter, backslash, NUL, empty segments) | `safe_relative_path` | `file:path_traversal` / `file:invalid_path` |
| 9 | base64 decodes and is non-empty | `decode_payload` | `invalid_payload` / `empty_payload` |
| 10 | **real** container from the first bytes (RIFF/WAVE, ID3/MPEG frame sync, `ftyp`) versus the extension | `sniff_container` | `unrecognised_container` / `extension_mismatch` / `unsupported_extension` |
| 11 | per-asset and per-pack size ceilings | `MAX_ASSET_BYTES`, `MAX_PACK_BYTES` | `asset_too_large` / `pack:too_large` |
| 12 | SHA-256 of the bytes against the declared/manifest checksum | `sha256_hex` | `checksum_mismatch` |
| 13 | no file the manifest does not describe | `validate_pack_upload` | `orphan_asset` |
| 14 | every `required: true` asset actually uploaded | `validate_pack_upload` | `missing_required_asset` |

Limits actually enforced: 8 MiB per asset, 64 MiB per pack, 250 assets, 8–48 kHz,
1 or 2 channels, 0.05–60 s per asset, pack id ≤ 80 characters, path segments
≤ 64 characters.

### 8.2 Security properties worth stating explicitly

* **Path traversal and filename injection** are refused by charset and structure,
  then again by comparing the *resolved* filesystem path against the pack root
  (`_pack_dir`, `_write_assets`, and the asset route). Two independent checks,
  because a stored manifest is untrusted on the way out as well as in.
* **Manifest manipulation** is defeated by recomputing SHA-256 from the received
  bytes: a manifest cannot describe different audio than was uploaded, and a file
  the manifest does not mention is refused.
* **Ordering**: nothing is written until the whole payload validates. A rejected
  upload leaves no row, no directory and no audit entry claiming success.
* **Non-disclosure**: refusal bodies carry codes, never filesystem paths; the asset
  route streams bytes with `FileResponse` and never reveals a location; a pack the
  caller may not see is a 404, not a 403.
* **No secret handling at all**: the endpoint takes no credentials and returns no
  tokens; the storage root comes from `AMSDP_VOICE_PACK_ROOT`
  (default `backend/var/voice-packs`), never from the request.

### 8.3 What is *not* verified

* **Decodability is container-level only.** No audio decoder runs, so a WAV with a
  valid header and truncated PCM frames would pass. A production implementation
  should decode or probe each asset before publication; that needs an audio
  toolchain this host does not have. Repeated in §15.
* The upload, write and read-back paths have **never been executed**: no database,
  no object storage, no running service. The *rules* are executed; the *plumbing*
  is not.

---

## 9. API and data model changes

### 9.1 Schema — one forward-only migration (`c4d8e2a91f60`)

| Table | Ownership | Purpose |
|---|---|---|
| `voice_packs` | **new** | one row per pack **version**; a platform pack when `organization_id` is `NULL` |
| `announcement_platform_config` | **new** | single row (`id='platform'`) holding the platform defaults |

`voice_packs` columns: `id` (PK), `organization_id` (FK → `organizations.id`,
nullable), `language`, `voice_name`, `description`, `personality`, `version`,
`status`, `base_path`, `manifest` (JSON), `manifest_checksum`, `compatibility`
(JSON), `available_to_organizations`, `validation_status`, `validation_problems`
(JSON), `validated_at`, `review_status`, `reviewed_by`, `reviewed_at`,
`review_note`, `published_by`, `published_at`, `retired_at`, `created_by`,
`created_at`, `updated_at`; unique on (`organization_id`, `language`,
`voice_name`, `version`); indexes on (`organization_id`, `language`) and
(`status`).

Nothing existing was altered: no column was added to `organizations`,
`queue_entries`, `audit_events` or any other table, and the organisation override
reuses the existing `organizations.config` JSON column. The migration is therefore
**two additive tables and two indexes**.

Idempotency: every table and index is created only when absent
(`inspector.has_table`, `inspector.get_indexes`), matching the house pattern in
`a7c3f19d2b64`. `downgrade()` drops exactly what `upgrade()` creates.

### 9.2 Routes

| Method | Path | Capability | Purpose |
|---|---|---|---|
| GET | `/api/v1/voice-packs` | `org.read` | library metadata visible to the caller |
| POST | `/api/v1/voice-packs` | `org.manage` + role gate | upload a new version (validated before anything is written) |
| GET | `/api/v1/voice-packs/{id}/manifest` | `queue.view` | authenticated catalogue — never a public URL |
| GET | `/api/v1/voice-packs/{id}/preview` | `org.read` | audition descriptor, **no** side effects |
| GET | `/api/v1/voice-packs/{id}/assets/{path}` | `queue.view` | one asset; path re-validated and must be declared in the manifest |
| POST | `/api/v1/voice-packs/{id}/validate` | `org.manage` | re-run technical validation |
| POST | `/api/v1/voice-packs/{id}/submit` | `org.manage` | submit for review |
| POST | `/api/v1/voice-packs/{id}/approve` | `platform.admin` | human approval; reviewer taken from the token |
| POST | `/api/v1/voice-packs/{id}/reject` | `platform.admin` | human rejection with reason |
| POST | `/api/v1/voice-packs/{id}/publish` | `platform.admin` | make selectable |
| POST | `/api/v1/voice-packs/{id}/retire` | `platform.admin` | remove from selection, keep the row |
| POST | `/api/v1/voice-packs/{id}/availability` | `platform.admin` | release or withhold a platform pack |
| GET / PUT | `/api/v1/platform/announcement-config` | `platform.admin` | platform defaults |
| GET / PUT | `/api/v1/orgs/{org_id}/announcement-config` | `org.read` / `org.manage` | organisation override |
| POST | `/api/v1/orgs/{org_id}/announcement-config/rollback` | `org.manage` | restore the previous published version |

**Why `queue.view` on the audio routes**: playback must work for a receptionist,
who holds `queue.*` but not `org.read`. The catalogue and the bytes are therefore
gated on the queue capability, while *configuration* stays on `org.read` /
`org.manage`. An unpublished pack's bytes are additionally restricted to callers
who may administer it (`_may_stream`), so previewing is possible without exposing a
draft to the terminals.

### 9.3 Audit

| Event | Trail |
|---|---|
| `voice_pack.created` `.validated` `.submitted` `.approved` `.rejected` `.published` `.retired` `.availability_changed` | `audit_events` for an organisation pack, `platform_audit_events` for a platform pack |
| `announcement_config.updated` `.rolled_back` | `audit_events`, with the organisation and the before/after block |
| `announcement_config.platform_updated` | `platform_audit_events` |

Both trails are append-only; nothing in this work updates or deletes an audit row.

---

## 10. Files changed and reasons

### 10.1 Added

| File | Lines | Why |
|---|---|---|
| `backend/organization/voice_pack_policy.py` | 781 | The decision layer: permission gate, scope resolution, selectability, precedence, lifecycle transitions, versioning/rollback, metadata checks, upload validation, descriptors. **Stdlib only**, so it can be executed on a host without the stack. |
| `backend/organization/voice_packs.py` | 583 | `VoicePack` model + the pack API (list, upload, validate/submit/approve/reject/publish/retire/availability, manifest, preview, asset streaming) and the storage writer. |
| `backend/organization/announcement_config.py` | 386 | `AnnouncementPlatformConfig` model + platform defaults and organisation override/rollback routes. |
| `backend/alembic/versions/c4d8e2a91f60_add_voice_packs_and_platform_config.py` | 116 | Forward-only, idempotent migration for the two new tables. |
| `backend/organization/tests/test_voice_pack_policy.py` | 519 | 49 tests over the policy layer (runnable with or without pytest). |
| `backend/organization/tests/test_voice_packs_api.py` | 379 | 18 API tests: the denied-API matrix, inheritance, rollback, preview purity, upload refusals. |
| `scripts/que-006-w3-voice-config/check_voice_config.py` | 56 | Dependency-free runner for the policy suite (the executed evidence). |
| `scripts/que-006-w3-voice-config/check_migration_graph.py` | 89 | Read-only Alembic revision-graph checker (no alembic on this host). |

### 10.2 Modified — exactly one file

| File | Change | Why it was permissible |
|---|---|---|
| `backend/organization/main.py` | **+17 lines**: two `try/except ImportError` + `include_router` blocks, alongside the existing `notification_config` / `appointment_config` / `facility` registrations | The service composition point is not on the shared-file restriction list, and a router that is never mounted is not reachable. No existing route, model, schema or handler was touched. |

### 10.3 The seven restricted files were not modified by this task

| Restricted file | Evidence it was untouched |
|---|---|
| `backend/queuing/main.py` | last write `11:36`, before this session's first edit (`15:31`) |
| `backend/common/models.py` | last write `11:35` |
| `frontend/pages/queue.js` | last write `11:45` |
| `frontend/components/queue/QueueAnnouncements.js` | last write `12:06` |
| `frontend/lib/i18n.js` | last write `11:45` |
| `frontend/lib/announcements/content.js` | last write **2026-11-20** `14:21` |
| `frontend/lib/announcements/controller.js` | last write `08:03` |

Those files **do** appear in `git status` as modified — by the earlier
W1/W2/POD-12/W4 work, not by this task. The only file this task edited carries a
later timestamp (`15:31`) than all of them, and no W3 change required reaching into
any of them: the model went into a new module, the configuration pattern was copied
rather than the shared config module edited, and no UI change was needed because
`voice-packs.js` and `QueueAnnouncements.js` already resolve through the precedence
rule.

### 10.4 Not touched at all

`frontend/public/audio/**` (no asset, no manifest), `docs/governance/AMSDP_Docs_Index_V1.0.md`
(see the deviation in Appendix A), `.gitignore`, `docker-compose.yml`, every
`requirements.txt`, and every file named in assignment §9's exclusion list.

---

## 11. Tests executed and exact results

### 11.1 Executed in this session

**Command 1 — the policy suite (the primary evidence)**

```
python scripts/que-006-w3-voice-config/check_voice_config.py
```

```
49 tests, 49 pass, 0 fail
```

What those 49 tests cover, grouped:

| Group | Tests | What is proven |
|---|---|---|
| Permissions and scope | 9 | platform scope is `super_admin`-only; `org_admin` limited to its own organisation; foreign organisation 404; `branch_admin`/`receptionist`/`doctor`/`assistant` refused; platform packs not administrable by a tenant; neighbouring configuration capabilities (`symptom.manage`, `facility.manage`) do not imply voice configuration |
| Selection and precedence | 10 | independent `en`/`bn`; platform inheritance; organisation override; foreign pack refused and reported; unpublished/retired unselectable; unreleased platform pack unselectable; language mismatch is a refusal; documented default language |
| Versioning and rollback | 4 | versions increase and are never reused; rollback picks the previous published version; rollback cannot land on foreign/retired |
| Lifecycle and human review | 12 | upload ≠ activation; validation cannot approve; failing validation rejects; `org_admin` cannot approve its own pack; approval needs a named reviewer; publication needs validation **and** approval; draft cannot be published directly; submission needs a passing validation; published versions are immutable; retirement keeps the row; metadata completeness |
| Upload validation | 10 | well-formed upload passes; traversal (`../`, `/etc/…`, `C:/…`, backslashes); extension/container mismatch; non-audio payload; checksum mismatch; invalid base64; missing required asset; orphan file; duplicate id/path; wrong-language asset; unusable pack id; incomplete metadata; oversized asset; hostile input never raises |
| Compatibility | 4 | descriptor matches the W1 `normalisePack` contract; preview descriptor does not mutate the pack; browser speech is never a substitute; client and server share one refusal vocabulary |

**Command 2 — frontend regression (queue suites; unchanged by this task)**

```
cd frontend && node --test tests/queue-*.test.mjs
```

```
ℹ tests 146
ℹ pass 145
ℹ fail 0
ℹ skipped 1
```

The single skip is the pre-existing JSX/`swc` parse skip in
`queue-announcements-boundary.test.mjs`, not a W3 failure.

**Command 3 — the W3 client suite alone**

```
cd frontend && node --test tests/queue-announcement-voice-packs.test.mjs
```

```
ℹ tests 8
ℹ pass 8
ℹ fail 0
```

**Command 4 — syntax check of everything added**

```
python -m py_compile backend/organization/voice_pack_policy.py \
  backend/organization/voice_packs.py backend/organization/announcement_config.py \
  backend/organization/tests/test_voice_pack_policy.py \
  backend/organization/tests/test_voice_packs_api.py \
  backend/alembic/versions/c4d8e2a91f60_add_voice_packs_and_platform_config.py \
  backend/organization/main.py scripts/que-006-w3-voice-config/check_voice_config.py
```

```
PY_COMPILE OK
```

**Command 5 — migration graph**

```
python scripts/que-006-w3-voice-config/check_migration_graph.py
```

```
16 revisions in backend/alembic/versions
heads: a9c4e1f7b2d8, c4d8e2a91f60
  a9c4e1f7b2d8 <- b3d7e91f6a24 <- …
  c4d8e2a91f60 <- a7c3f19d2b64 <- f8a2b3c4d5e6 <- …
if a7c3f19d2b64 is reparented to a9c4e1f7b2d8, heads: c4d8e2a91f60  <-- single head
```

### 11.2 Written but **not** executed

| Suite | Tests | Why not executed |
|---|---|---|
| `backend/organization/tests/test_voice_packs_api.py` | **18** | needs `pytest`, `fastapi`, `sqlalchemy`, `psycopg2`, `httpx` and PostgreSQL — none present (`importlib.util.find_spec` returns `None` for every one) |

Those 18 are the tests that would observe real status codes (403/404/409/422), real
audit rows and real files on disk. **No status code in this report comes from a live
server.**

### 11.3 One correction made during self-review

The written API test `test_nothing_becomes_active_without_validation_review_and_publication`
originally called `validate` and then `submit`. That is not a legal sequence: both
transitions end in `pending_review`, so the second is an `invalid_transition` (409).
The **rules were right and the test was wrong**; the test now submits the pack
directly (its upload already passed technical validation) and the constraint is
pinned by a new executed policy test,
`test_validation_and_submission_are_alternatives_not_a_sequence`. Recorded here
because a report that hides its own corrections is not evidence.

### 11.4 Not executed, not written

* Migration `upgrade`/`downgrade` against a database.
* Any HTTP call.
* Any browser, device or two-terminal run.
* The existing backend suite (`backend/tests/**`, `backend/*/tests/**`) — same
  dependency requirements, and this task did not run it.

---

## 12. Build results

| Build step | Result |
|---|---|
| Python syntax (`py_compile`, 9 files) | **OK** |
| Frontend build (`npm run build`) | **not run** — no frontend source was changed by this task, so a build would prove nothing about W3 and would spend the time; the frontend suites were run instead |
| Docker image build | **not run** |
| `alembic upgrade head` | **not run** — no alembic, no PostgreSQL; and it would refuse anyway while the pre-existing W2 double head stands (§11.1 command 5) |
| Dependency install | **not attempted** — installing FastAPI/SQLAlchemy/psycopg2/Alembic/pytest is a state-changing act on the owner's machine and was not authorised by the assignment |

---

## 13. Browser / runtime verification status

| Verification | Status | Note |
|---|---|---|
| Voice configuration screen in a browser | **NOT VERIFIED** | no admin UI exists for W3 and no browser was driven. This task implemented the API and the policy, not a screen. |
| Pack selection applied to a live queue announcement | **NOT VERIFIED** | needs the running stack, a published pack and a terminal |
| Preview auditioning real audio in a browser | **NOT VERIFIED** | the preview *descriptor* contract is verified; nobody has listened to a preview |
| Two-terminal announcement after a configuration change | **NOT VERIFIED** | W2's two-terminal verification is still outstanding, and W3 cannot substitute for it |
| Upload an audio pack end to end | **NOT VERIFIED** | the validation rules are executed; the route, the write and the read-back are not |
| W1 playback unchanged | **PARTIALLY VERIFIED** | the descriptor contract test passes and the 146-test frontend queue suite still passes; nothing was played on a device |

**No browser or device claim is made anywhere in this report.**

---

## 14. Remaining blockers and dependencies

### 14.1 One blocker inherited from W2 (not caused by this task)

`backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py`
declares `down_revision = 'f8a2b3c4d5e6'`, but the true head is the merge revision
`a9c4e1f7b2d8` (`down_revision = ('b3d7e91f6a24', 'f8a2b3c4d5e6')`). Two heads
exist, so `alembic upgrade head` refuses to run.

Verified counterfactual (§11.1 command 5): changing that single line to
`'a9c4e1f7b2d8'` leaves **exactly one head — `c4d8e2a91f60`**, this task's
migration. Therefore:

* W3's migration does **not** add an independent branch; it extends the W2 chain;
* fixing W2 fixes W3's DDL chain as a side effect;
* if W2's revision is abandoned instead, `c4d8e2a91f60`'s `down_revision` must
  change to `'a9c4e1f7b2d8'` — the migration docstring says so.

**The fix was not applied.** W2 is outside this task's scope, and silently editing
another workstream's migration is precisely the unreported change the governance
rules forbid.

### 14.2 Dependencies

| Dependency | Effect on W3 |
|---|---|
| **W1 playback engine** | Compatible: `pack_descriptor` emits what `normalisePack` reads. W1's own browser/device verification is still outstanding. |
| **W2 queue integration** | W3 supplies the configuration W2 will read, but nothing wires the resolver into the queue page — that would have meant editing `frontend/pages/queue.js` and `QueueAnnouncements.js`, both restricted. **W3 currently changes nothing about what the terminals play.** |
| **POD-12 call control** | Untouched. The `queue.view` gate on the audio routes grants nothing beyond what the queue already needs. |
| **W4 room support** | Untouched; Ubuntu's uncommitted room work is unaffected and no queue payload shape was changed. |
| **W5 remote installation** | W3 provides the pack identity, version and checksums W5 needs, and the pack id charset deliberately matches W5's `safePackId`. **Remote installation remains NOT IMPLEMENTED and is not claimed here.** |
| **W6 asset cleanup** | Untouched; no asset moved or deleted. |
| A working backend stack | Required before any of the API layer can be called VERIFIED. |

### 14.3 What the owner must decide next

1. **Join W3 to the terminals**: a follow-up may edit `QueueAnnouncements.js`
   (restricted) so the panel resolves from the server payload. Without it the
   feature is configurable but not audible.
2. **Approve the W2 migration reparent** (one line) so the chain has a single head.
3. **Confirm who may read the configuration screen.** Today it is `org.read`, which
   excludes `branch_admin` — that follows the owner's §3.1 rule, but it also means a
   branch administrator cannot see which voice is in force.
4. **Confirm the release default**: a published platform pack is invisible to
   tenants until explicitly released (`available_to_organizations = false`).

---

## 15. Explicit limitations

1. **The HTTP, persistence and storage layers have never run.** Every 200/201/403/
   404/409/422 expectation in this report is written, not observed.
2. **The migration has never been applied.** Column types are asserted by reading
   the code and comparing it with `a7c3f19d2b64`'s style; no database has seen this
   DDL, so a type mismatch (e.g. `sa.false()` on the target PostgreSQL version)
   would only surface at first `upgrade`.
3. **No audio decoder.** Validation proves container, extension match, sizes and
   checksums; it cannot prove the audio plays. Truncated or silent PCM inside a
   valid WAV header would pass.
4. **No UI.** There is no screen to upload, review, publish or select a pack;
   everything is API-only. The existing panel still resolves through the built-in
   pack.
5. **No wiring into the queue.** As of this task, configuring a voice pack changes
   nothing that a patient hears.
6. **The upload format is base64 JSON**, a compromise forced by the absence of
   `python-multipart`. It is validated strictly, but it is not a streaming upload
   and it inflates payloads by ~33 %; a real deployment should move to multipart or
   a presigned object store.
7. **Assets are written to a local filesystem path** (`AMSDP_VOICE_PACK_ROOT`), not
   object storage. A multi-instance deployment would need shared storage.
8. **`next_version` is computed in Python, not by the database.** Two concurrent
   uploads of the same persona could race; the unique constraint would then reject
   one with an integrity error rather than a clean 409. Acceptable for a
   single-instance demo, not for production.
9. **Approval is a single platform role.** There is no four-eyes rule and no
   composer/reviewer separation beyond `super_admin`.
10. **`available_to_organizations` defaults to `false`** for platform packs, so a
    freshly published platform pack is invisible to tenants until released. That is
    deliberate, but it is a behavioural decision the owner should confirm.
11. **The organisation-side audit assertion is weak.** The written API test checks
    that platform events exist but only that organisation events are not `None`,
    because the trail is shared across tests and must not be reset. It would be
    tightened with a baseline counter, as `test_appointment_config.py` does.
12. **`get_announcement_config` silently drops malformed values.** Deliberate (a
    corrupt block must not 500 the queue page), but it means a bad write is
    invisible in the configuration screen; only the audit trail shows the stored
    shape.
13. **No `common/config.py` helper was added.** The announcement-config readers live
    in `organization/announcement_config.py` because only that module uses them; if
    a second service ever needs them, they should move to the shared module in a
    deliberate, reviewed edit.

---

## 16. Confirmation of no commit, push, deployment or merge

* `git status --short` shows the same tracked files modified as before this task,
  plus the new files listed in §10.1. `HEAD` is still `37cf3d1` on
  `hackathon-mvp`.
* **No** `git add`, `git commit`, `git push`, `git merge`, `git rebase`,
  `git reset`, `git stash`, `git checkout` or `git clean` was run. `git add -A` was
  never used.
* **No** service was started, **no** container built, **no** migration applied and
  **no** deployment attempted.
* **No** existing modified or untracked file was reverted, deleted or rewritten.
* The only writes were: the eight files in §10.1, the 17 added lines in
  `backend/organization/main.py`, and this report. `__pycache__` directories created
  by the syntax check were removed afterwards, leaving the tree otherwise as it was
  found.

**Post-report note.** Everything above describes the state at the time of writing and
stays true as a record. The Product Owner subsequently instructed that the work be
committed and pushed, so the W3 files now appear in a commit on this branch. Nothing
in the technical findings, the unexecuted tests, the migration-head defect or the
pending decisions changes because of that: a commit is not a verification, and the
evidence classification in §1 still stands.

---

## Appendix A — Governance and skill compliance (`.clinerules` §6)

**Domains routed (`.clinerules` §4)**

| Domain | Governing documents applied | How |
|---|---|---|
| Authentication, RBAC, permissions | `saas-auth-and-authorisation.md` (as adapted in the governance assessment §3), Business Rules §7–§8, `backend/common/permissions.py`, `backend/common/auth.py` | used the **existing** capability matrix rather than inventing capabilities; added an explicit role allow-list on top; denied-API tests written for every non-configuring role |
| Multi-tenant data, org/branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–§6, `common/auth.py` scope helpers | tenant key stays `organization_id`; scope derived from the token; foreign organisation is a non-disclosing 404; no second tenant column introduced |
| Database schema, migrations, integrity | `saas-multitenant-data.md` §4–§5, `saas-cicd-workflow.md` §3 (adapted), Alembic chain, `common/models.py` | one forward-only, idempotent migration; two additive tables; no existing column touched; the chain-head defect reported, not hidden |
| Backend API / service endpoints | `saas-application-security.md` (adapted), Business Rules Part II | new routers follow the `appointment_config` / `notification_config` pattern: scoped `{org_id}`, audited writes, 404 for foreign tenants |
| Audit, data integrity, reporting | `saas-observability.md` (adapted: redaction, denial recording), `common/audit.py`, Business Rules Part X | tenant events → `audit_events`, platform events → `platform_audit_events`, append-only, before/after recorded |
| Frontend UI | not applicable | no frontend file was changed |

**Skills:** **none installed** in this workspace (`.clinerules` §5; verified: no
`.clinerules/skills/`, `.claude/skills/` or repository `skills/` directory). No skill
was used and **none is claimed**. The knowledge artefacts used are the product and
implementation documents listed in §2.

**Non-negotiables (§3), checked one by one**

| Rule | Compliance |
|---|---|
| No secrets or credentials logged or exposed | none read, logged or returned; the storage root comes from the environment; no `.env` opened |
| The UI is never the safety boundary | every rule is server-side; the client's `checkSelectable` is a UX convenience and the server repeats it |
| Access enforced server-side, org from the token | `resolve_scope` / `_scoped_org` compare against the token; the payload may only *name* an organisation |
| Cross-tenant access fails closed with 404 | `organization_not_found` / `pack_not_found`; 403 is reserved for "your role lacks the capability" |
| Tenant key is `organization_id` | yes; `voice_packs.organization_id` is the only tenant column |
| Audit append-only | no update or delete path exists; tests never delete audit rows |
| Denials recorded | `install_denial_audit(app, "organization")` already covers every 403/404/422 in this service; the new routes inherit it |
| Forward-only idempotent migrations | yes: inspector-guarded, with a `downgrade()` |
| Never claim unverified capability | §3, §11 and §13 separate executed from written throughout |
| Do not use a discovery merely because it exists | no new dependency, no new capability, no table beyond what the requirement needed |

**Evidence standard (§7):** IMPLEMENTED — the code exists and is reachable through
the mounted router. TESTED — 49 policy tests and the frontend suites pass **in this
tree**. VERIFIED — policy claims are confirmed by executed tests; API and DDL claims
are **not** verified. ACCEPTED — nothing; awaiting the Product Owner.

**Deviations and exceptions**

1. **`docs/governance/AMSDP_Docs_Index_V1.0.md` was not updated.** §12 obliges an
   index entry for a new document; assignment §9 forbids changing documents. The
   obligation is **owed** and recorded here rather than silently skipped: one line
   registering
   `docs/implementation/QUE-006_W3_VOICE_CONFIGURATION_IMPLEMENTATION_AND_VERIFICATION_REPORT.md`
   should be added when document edits are permitted again.
2. **`backend/organization/main.py` was modified.** Not on the restriction list, but
   it is a shared composition point; the change is 17 added lines, additive only, and
   documented in §10.2.
3. **A new table for platform defaults was introduced.** The alternative was to store
   platform configuration inside a tenant's JSON blob, which would have been a
   correctness defect rather than a simplification.
4. **`.clinerules` §9's "write code only" boundary was read as "do not start services
   or install dependencies".** The two verification scripts were run because the
   assignment explicitly requires executed evidence (§8), and neither writes to the
   repository.

---

## Appendix B — Exact commands used for the evidence in this report

```
python scripts/que-006-w3-voice-config/check_voice_config.py
cd frontend; node --test tests/queue-*.test.mjs
cd frontend; node --test tests/queue-announcement-voice-packs.test.mjs
python -m py_compile backend/organization/voice_pack_policy.py \
    backend/organization/voice_packs.py backend/organization/announcement_config.py \
    backend/organization/tests/test_voice_pack_policy.py \
    backend/organization/tests/test_voice_packs_api.py \
    backend/alembic/versions/c4d8e2a91f60_add_voice_packs_and_platform_config.py \
    backend/organization/main.py scripts/que-006-w3-voice-config/check_voice_config.py
python scripts/que-006-w3-voice-config/check_migration_graph.py
python -c "import importlib.util as u; [print(m, bool(u.find_spec(m))) for m in ['fastapi','pytest','sqlalchemy','psycopg2','alembic','pydantic','httpx']]"
git status --short
git --no-pager diff --stat backend/organization/main.py
```

`find_spec` in this session returned `False` for `fastapi`, `pytest`, `sqlalchemy`,
`psycopg2`, `alembic`, `pydantic` and `httpx` — the reason the API suite and the
migration are reported as unexecuted rather than passed.

**Where this report was written:** `docs/implementation/`, per `.clinerules` §11 (the
subject is a QUE-006 workstream implementation and verification). No document was
migrated, so no migration-manifest entry is owed.
