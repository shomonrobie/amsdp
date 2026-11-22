# QUE-006 W3 — Language and Voice Configuration (implementation report)

**Assignment ID:** `AMSDP-QUE-006-W3-VOICE-CONFIGURATION`
**Date:** 2026-11-21
**Status:** **PARTIALLY IMPLEMENTED.** The configuration **decision layer** (precedence, organisation
isolation, selectability) is implemented and verified. The **server-side voice-pack domain** (storage,
upload, validation, approval, publication, permissions, admin UI) is **NOT IMPLEMENTED**, because this
host cannot run or test the backend stack — see §2. Shipping it unverified would break the evidence
standard, so it was specified instead of guessed.

---

## 1. What is implemented and verified

| File | Status | Purpose |
|---|---|---|
| `frontend/lib/announcements/voice-packs.js` | new, 168 lines | Pack lifecycle vocabulary, `checkSelectable()`, `resolveAnnouncementConfig()` — the precedence model of assignment §8.2 |
| `frontend/components/queue/QueueAnnouncements.js` | edited | Resolves its pack through `resolveAnnouncementConfig({ builtin })` instead of hardcoding it, so an organisation override needs configuration only |
| `frontend/tests/queue-announcement-voice-packs.test.mjs` | new, 8 tests | Precedence, cross-organisation refusal, unpublished refusal, language mismatch, distinct "missing pack" vs "missing catalogue" facts, language fallback, and the panel wiring |

### 1.1 Precedence as implemented

| Step | Rule | Reported as |
|---|---|---|
| 1 | organisation's pack for that language — **if** published, same language, and owned by that organisation or the platform | `sources[lang] = 'organization'` |
| 2 | platform default for that language | `'platform'` |
| 3 | built-in draft pack (the shipped catalogue) | `'builtin'` |
| 4 | nothing | `'none'` + warning `no_voice_pack` |

Refusals are reported, never silently downgraded: `pack_not_found`, `pack_not_published`,
`pack_language_mismatch`, `pack_foreign_organization`, `no_voice_pack`. A refusal falls through to the
next step **and says so**, which is what §8.2's "report unavailable voice packs clearly" requires.

### 1.2 Organisation isolation, proven (client half)

`checkSelectable()` refuses a pack whose `organizationId` is not the caller's, and the test asserts the
other organisation's pack is **not** used while the refusal is reported. This is the client half of
DR-8; the server half must repeat it — a client rule alone is not an access control (`.clinerules` §3).

## 2. Why the server half is not implemented

| Fact | Evidence |
|---|---|
| No test runner | `python -m pytest --version` → *No module named pytest* |
| No application stack | `python -c "import fastapi, sqlalchemy"` → `ModuleNotFoundError` |
| Therefore | a SQLAlchemy model, an Alembic migration, a FastAPI router and its permission tests could be **written but not executed**: no migration run, no route call, no denied-API test. The assignment forbids claiming that (§10, §13). |

Nothing was added to `backend/` on that basis: no model, no migration, no route. A half-applied schema
change is worse than none, and `.clinerules` §3 requires every schema change to ship as a tested,
forward-only migration.

### 2.1 The contract to implement next (unchanged from the master plan §3)

- **Table `voice_packs`** — `id`, `organization_id` (NULL = platform), `language`, `voice_name`,
  `description`, `personality`, `version`, `status`, `base_path`, `manifest` (JSON), `manifest_checksum`,
  `compatibility` (JSON), `validation_status`, `validation_problems`, `review_status`, `created_*`,
  `approved_*`, `published_*`, `retired_at`. Unique on (`organization_id`, `language`, `voice_name`,
  `version`). Immutable once `published`.
- **Organisation settings** — `organizations.config["announcement"] = {language, voice_packs:{en,bn},
  updated_at, updated_by}`. **No migration** needed: the column already exists (TF-5).
- **Routes** — `GET/PUT /api/v1/orgs/{org_id}/announcement-config`, `GET /api/v1/voice-packs`,
  `POST /api/v1/voice-packs`, `…/{id}/validate|submit|approve|publish|retire`,
  `GET /api/v1/voice-packs/{id}/manifest` (authenticated; organisation packs are never public URLs).
- **Permissions (DR-3)** — reads on `org.read`; organisation writes on `org.manage`; platform defaults,
  approval and publication on `platform.admin`. `branch_admin` holds neither, so it is excluded **by the
  existing matrix**, not by a new rule (TF-6). Denied-API tests for `branch_admin`, `receptionist`,
  `doctor`, `assistant` and a foreign `org_admin` are the acceptance gate.
- **Audit** — one event per language change and per pack transition, with actor, scope, version and
  timestamp (assignment §8.4).

## 3. Status per assignment §4 item

| §4 requirement | Status |
|---|---|
| 4.1 platform defaults, upload, versioning, preview, publish/retire, availability controls | **NOT IMPLEMENTED** (server) — model/route contract in §2.1 |
| 4.2 organisation language + voice selection, isolation | **PARTIALLY IMPLEMENTED** — selection and isolation rules verified client-side; no server storage |
| 4.3 language and voice are separate settings | **IMPLEMENTED AND VERIFIED** — precedence resolves per language independently; the language is reported separately from the packs |
| 4.4 voice-pack data model | **SPECIFIED, NOT IMPLEMENTED** |
| 4.5 versioning and lifecycle | **IMPLEMENTED (vocabulary + selectability) / NOT IMPLEMENTED (persistence)** — only `published` is selectable; every other status is refused with a reason |
| 4.6 secure upload and validation | **NOT IMPLEMENTED** — the *installer* (W5) verifies SHA-256 and refuses path traversal for downloaded catalogues; that is distribution, not upload |
| 4.7 preview | **NOT IMPLEMENTED** — needs the server catalogue. The preview *engine* exists already: `createPrerecordedPlayer().play()` over any pack descriptor |
| Permission enforcement (frontend / API / logic / database) | **FRONTEND: not applicable yet** (no admin UI) · **API/logic/database: NOT IMPLEMENTED** — the existing matrix already satisfies the role mapping, but no route exists to test |

## 4. Test evidence

`frontend/tests/queue-announcement-voice-packs.test.mjs` — **8/8 pass**: organisation override wins ·
platform default when unset · foreign-organisation pack refused and reported · unpublished/retired not
selectable · language mismatch is a refusal not a reroute · missing pack vs missing catalogue are
distinct · invalid language falls back to platform then `bn` · the panel resolves through the
precedence rule.

Announcement battery after W3: **98 tests, 97 pass, 0 fail, 1 skipped**.

## 5. Governance and skill compliance (`.clinerules` §6)

- **Domains (§4):** Authentication/RBAC + multi-tenant isolation → `saas-auth-and-authorisation.md` and
  `saas-multitenant-data.md` as adapted. Applied: tenant key stays `organization_id`; isolation is an
  ownership check, not a hidden button; the role mapping uses the **existing** matrix rather than
  inventing capabilities.
- **Skills:** none installed (§5) — none claimed.
- **Non-negotiables (§3):** no second tenant column; cross-organisation access fails closed and
  non-disclosing; no credentials in code; no schema change was made, so no untested migration exists.
- **Deviations:** the server half is **not** implemented — the largest gap in the programme, and it is
  stated as such in the final report.
