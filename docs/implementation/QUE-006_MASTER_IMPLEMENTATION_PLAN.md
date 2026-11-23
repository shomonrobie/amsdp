# QUE-006 — Master Implementation Plan (Voice Announcement Programme)

**Assignment ID:** `AMSDP-QUE-006-MASTER-IMPLEMENTATION`
**Date:** 2026-11-21
**Status:** planning gate for the seven-workstream programme. This document authorises nothing by itself; it records the inspected baseline, the decision register and the planned change set for each workstream.
**Scope of this task's first step:** documentation plus read-only repository inspection. No production code is changed by this document.

---

## 1. Inspected baseline (verified in this session, not remembered)

| Fact | Value | How verified |
|---|---|---|
| Repository HEAD | `37cf3d1` | `git rev-parse --short HEAD` |
| Modified tracked files (pre-existing, preserved) | `.gitignore`, `docs/governance/AMSDP_Docs_Index_V1.0.md`, `frontend/lib/announcements/content.js`, `frontend/pages/queue.js`, `frontend/tests/queue-announcement-content.test.mjs`, `frontend/tests/queue-announcement-controller.test.mjs` | `git status --porcelain` |
| Untracked, pre-existing | 5 QUE-006 reports + the roadmap, `frontend/public/`, `scripts/` | `git status --porcelain` |
| Announcement modules | `content.js` (165), `controller.js` (286), `speech-synthesis.js` (379), `QueueAnnouncements.js` (149) | file sizes/reads |
| Announcement tests | 4 files, **53 tests** (`npm test` → 52 pass, 1 skipped) | run in this session |
| Audio served tree | `frontend/public/audio/`: 72 files — 28 `.mp3`, 29 `.wav`, 13 `.m4a`, 1 `.mpeg`, 1 `manifest.json`; 6 directories | `Get-ChildItem -Recurse` |
| Manifest | `AMSDP-QUE-006-audio-assets/2.0`, `version 2.0`, **28 assets**, 28 master + 28 playback present, 28 technical pass | `ConvertFrom-Json` |
| Asset id scheme | `en.phrase.{token-number,proceed-to-room,room-suffix,no-room}`, `en.digit.0..9`, `bn.phrase.{token-number,room-prefix,room-locative,no-room}`, `bn.digit.0..9` | manifest `id` values |
| Queue entry model | `queue_entries` — **no room column** (`models.py:854-884`) | read |
| Queue `call` action | implemented server-side, gated on `queue.manage` (`queuing/main.py:396-404`); no UI control anywhere | read |
| Non-blocking side-effect seam | `_notify(event, *args)` — never raises, own session (`queuing/main.py:47-57`) | read |
| Org config pattern | `organizations.config` JSON + audited router (`appointment_config.py`, `notification_config.py`, `common/config.py`) | read |
| Permissions | `super_admin` holds `platform.admin`, `platform.cross_org`, `org.manage`; `org_admin` holds `org.manage`; **`branch_admin` does not hold `org.manage`** (`permissions.py:37-134`) | read |
| Alembic | `backend/alembic/versions/` — 14 revisions | listing |
| Backend test layout | `backend/tests` + per-service `tests` packages (8) | listing |
| Remote installation | **zero artefacts** in code or docs | searched earlier in the roadmap task |

### 1.1 One correction to the earlier roadmap, made by this plan

The roadmap described the configuration boundary as `super_admin` / `org_admin` / `branch_admin`
(the feature-catalogue wording). **The Product Owner's assignment (§3.4) states `branch_admin` has
no configuration access.** That resolves POD-5's permission ambiguity in favour of the *organisation*
scope, not the per-branch scope the roadmap recommended:

- storage: `organizations.config["announcement"]` (existing JSON column, no migration), plus a new
  `voice_packs` table for versioned packs;
- gate: `org.manage` for organisation writes, `platform.admin` for platform defaults and publication;
- `branch_admin` therefore has **no** configuration access *by construction*, because it holds neither
  capability. This must still be proven by denied-API tests, not by absence of a button.

This is recorded as **decision register entry DR-3** and supersedes roadmap POD-5's recommendation.
The roadmap is not rewritten; this plan is the newer artefact.

---

## 2. Decision register

Statuses: **APPROVED** (Product Owner, binding) · **APPROVED-REC** (owner approved the recommendation,
not a fresh decision) · **OPEN** (owner decision required) · **DEFERRED** (owner postponed) ·
**TECHNICAL** (implementation finding, no business authority).

### 2.1 Approved (binding on this programme)

| ID | Decision | Source | Consequence for implementation |
|---|---|---|---|
| DR-1 | Current output is an **approved DRAFT**; recordings and wording preserved; no re-recording, no voice refactor without approval | Assignment §3.1 | No asset, manifest entry or template may be rewritten. A new voice is a **new pack version**, never an edit. |
| DR-2 | Approved wording (en/bn × with-room/no-room) exactly as in `content.js`; no doctor name/honorific, no patient identity, no clinical data | Assignment §3.2 | `TEMPLATES` stay byte-identical. Segment resolution must **agree** with them, proven by test. |
| DR-3 | `super_admin` platform-wide · `org_admin` own organisation · `branch_admin`, receptionist, doctor — **none** | Assignment §3.4 | Enforced on `org.manage` / `platform.admin`; denied-API tests required, not UI hiding. |
| DR-4 | Prerecorded local audio is primary; browser speech is an optional alternative only; **never** an automatic Bangla fallback | Assignment §3.3 | Engine defaults to prerecorded; speech only when explicitly configured. |
| DR-5 | Queue operations never wait for audio; success only after playback **completes**; playback failure never fails a queue operation | Assignment §3.3, §8.5 | Engine reports `completed` from `ended`; queuing calls it fire-and-forget. |
| DR-6 | Remote installation: local agent, outbound poll, verified download, atomic install, previous version retained, rollback, status, offline | Assignment §3.5 | W5 implements exactly this; no inbound access to facility PCs. |
| DR-7 | Configurable English **and** Bangla voice library, multiple versions, personality metadata, preview, publish/retire, org isolation | Assignment §4 | New `voice_packs` domain (platform + organisation scope), versioned, immutable once published. |
| DR-8 | Organisation overrides platform default; no cross-org change; no platform-default change by `org_admin`; org uploads isolated by `organization_id` | Assignment §4.2 | Precedence resolver + scoped routes + storage isolation. |

### 2.2 Approved recommendations carried in (not new decisions)

| ID | Item | Effect |
|---|---|---|
| DR-9 | The roadmap's `AMSDP-QUE-006-W1-PRERECORDED-PLAYBACK-ENGINE` scope and **§8.1 AC-1…AC-8** are the W1 acceptance criteria, preserved verbatim | W1 gate |
| DR-10 | Doctor identity removal (already implemented and tested) stays | No template may regain a doctor slot |

### 2.3 Open — each blocks only the feature named

| ID | Decision | Blocks | Workaround until decided |
|---|---|---|---|
| POD-1 | Maximum token/room range | Validation bounds | No new bound invented. Tokens keep `content.js`'s existing 9-digit rule; rooms are unbounded digit runs. |
| POD-2 | Source of a room number | W4 with-room announcements end-to-end | Engine + resolution unit-tested for rooms; **no schema change**, no invented field. |
| POD-3 | Inter-clip pause policy | Natural-sounding pacing | No gap invented: only the catalogue's own 300 ms intentional-pause asset is honoured (0 ms elsewhere). |
| POD-4 | Server-side announcement record required? | Announcement audit events | None added in W1/W2 beyond the existing queue audit; re-raised in W7. |
| POD-7 | Removal of 15 unreferenced files from the served tree | W6 deletions | W6 produces a dependency report only; **no file deleted or moved**. |
| POD-8 | Trailing-silence policy | Audible pacing refinement | Nothing trimmed, nothing compensated at playback. |
| POD-9 | `en.phrase.no-room` comma discrepancy | Wording sign-off | Recorded clip untouched; comma is punctuation and inaudible; documented as **TF-2**. |
| POD-12 | Queue `call` UI authorisation | W2 end-to-end trigger | Announcement fires on the existing `call` action and on the operator button; no `call` control invented in W2. |

`O-3` (named human reviewer) and `O-2` stay open: nothing in this programme claims pronunciation
approval, and every existing asset keeps `humanReviewStatus: pending`.

### 2.4 Technical findings from this inspection

| ID | Finding | Where |
|---|---|---|
| **TF-1** | Asset ids encode language + role only, so a new voice pack is a new **manifest + base path**, not new code | `manifest.json` ids |
| **TF-2** | `en.phrase.no-room` clip is `" please come to the front."` (no comma); the template has `"Token number {n}, please come…"`. Punctuation only — inaudible | manifest `spokenText` vs `content.js` |
| **TF-3** | `en.phrase.room-suffix` is 300 ms of silence, `contentStatus: intentional-pause`; the manifest's own note says an engine must *insert a pause, not speak it* | manifest asset notes |
| **TF-4** | `en.digit.N` clips speak the **word** ("five"); `bn.digit.N` speak the **Bangla glyph** ("৫"). A text comparison must normalise number words or it fails for the wrong reason | manifest `spokenText` |
| **TF-5** | `organizations.config` is already JSON and `organizations.locale` already exists → organisation announcement settings need **no migration**; only voice packs do | `models.py:31-44` |
| **TF-6** | `branch_admin` holds `facility.manage` but not `org.manage`, so the old per-branch plan could not satisfy DR-3 without a new capability; the organisation scope can | `permissions.py:72-76` |
| **TF-7** | The queuing service has no outbound event channel (no websocket/SSE), so "automatic on call" must be driven by the client that performs the call | `queuing/main.py` |

---

## 3. Voice-library architecture (approved before W1, per assignment §4)

### 3.1 Why the pack boundary goes *under* the engine, not around it

The engine must never learn a file name. It receives a **pack descriptor**:

```js
{
  id: 'platform.en.male.v1',        // stable identity, never reused
  language: 'en',                    // 'en' | 'bn'
  version: 1,                        // immutable once published
  scope: 'platform' | 'organization',
  organizationId: null | '<org id>',
  basePath: '/audio/packs/platform-en-male-v1',
  manifest: { schema: '…', assets: [ … ] },
  status: 'published',
  checksum: '<manifest sha-256>',
}
```

Resolution (`segments.js`) reads **asset ids** (`en.phrase.token-number`, `bn.digit.4`, …) from that
manifest and builds `basePath + playbackFile`. A second English voice, a second Bangla voice or
version 2 of either therefore needs **no code change at all** — which is exactly what assignment §4.1
items 4–9 and §4.5 require, and what W1 requirement 12 ("without hardcoded filenames") means.

The existing catalogue is registered as `platform.en.v1` / `platform.bn.v1` by describing it as data,
**not** by moving or rewriting any file (DR-1). `frontend/public/audio/` stays the served tree.

### 3.2 Data model (new table, one migration)

`voice_packs` (new, `backend/common/models.py`, service `organization`):

| Column | Type | Notes |
|---|---|---|
| `id` | String PK | e.g. `vp_…` |
| `organization_id` | FK `organizations.id`, nullable | `NULL` = platform pack; never a second tenant column |
| `language` | String(10) | `'en'` / `'bn'`, validated against `ANNOUNCEMENT_LANGUAGES` |
| `voice_name` | String(120) | human label, e.g. "Male Voice" |
| `description` | Text | free text |
| `personality` | String(40) | `male` / `female` / `neutral` / free label — metadata only |
| `version` | Integer | unique with (`organization_id`, `language`, `voice_name`, `version`) |
| `status` | String(20) | `draft`,`validating`,`pending_review`,`approved`,`published`,`retired`,`rejected` |
| `base_path` | String(300) | serving path of the pack's assets |
| `manifest` | JSON | the pack's own manifest document |
| `manifest_checksum` | String(64) | sha-256 of the canonical manifest JSON |
| `compatibility` | JSON | `{schema, languages, sampleRate, channels, formats}` |
| `validation_status` | String(20), `validation_problems` | JSON list |
| `review_status` | String(20) | `pending` until a named human review (O-3) |
| `created_at`, `created_by`, `approved_at`, `approved_by`, `published_at`, `published_by`, `retired_at` | | audit trail of the lifecycle |

Immutable once `published`: an update to a published row is refused (**409**), the only mutating
transitions are `published → retired`. New content = new row = new version.

`organizations.config["announcement"]` (existing JSON column, **no migration**) holds:

```json
{"language": "bn", "voice_packs": {"en": "vp_…", "bn": "vp_…"}, "updated_at": "…", "updated_by": "…"}
```

Platform defaults live in a platform-scope row of the same shape, stored in the existing
`config` JSON of a reserved platform record rather than a second table (see W3 report for the exact
placement decision and why no schema was added for it).

### 3.3 Precedence (assignment §8.2, made explicit)

1. organisation override for that language, **if it names a pack that is `published` and compatible**;
2. otherwise the platform default for that language;
3. otherwise the built-in draft pack (`platform.en.v1` / `platform.bn.v1`);
4. otherwise — no fallback at all: the engine reports `failed('no_voice_pack')`. It never switches
   language, never switches personality and never substitutes browser speech for Bangla.

Every step down is reported in the resolved descriptor (`source: 'organization' | 'platform' |
'builtin'`) so the UI can say which is in force. No undocumented fallback exists.

### 3.4 API surface (new, org-scoped, audited)

| Method & path | Permission | Purpose |
|---|---|---|
| `GET /api/v1/announcement-config` | `org.read` | resolved config + which packs are in force + available packs |
| `PUT /api/v1/orgs/{org_id}/announcement-config` | `org.manage` | language + per-language pack ids; foreign org → **404** |
| `GET /api/v1/voice-packs?language=&scope=` | `org.read` | available packs (platform published + own org's) |
| `POST /api/v1/voice-packs` | `org.manage` (org scope) / `platform.admin` (platform scope) | create a draft version from an uploaded manifest |
| `POST /api/v1/voice-packs/{id}/validate` | same | re-run validation, record problems |
| `POST /api/v1/voice-packs/{id}/submit` | same | `draft → pending_review` |
| `POST /api/v1/voice-packs/{id}/approve` | `platform.admin` | `pending_review → approved` (a human review must be recorded) |
| `POST /api/v1/voice-packs/{id}/publish` | `platform.admin` | `approved → published`, marks previous version of the same voice `retired` |
| `POST /api/v1/voice-packs/{id}/retire` | `platform.admin`/owner | `→ retired`, never destroyed |
| `GET /api/v1/voice-packs/{id}/manifest` | `org.read` (owner/platform only) | authenticated download; org packs are **never** public URLs |

`branch_admin`, `receptionist`, `doctor`, `assistant` receive **403** (or 404 on a foreign id) from
every mutating route; tests must call the routes directly with those roles.

---

## 4. Workstream plan (sequential, phase-gated)

| # | Workstream / assignment ID | Deliverable | Files (planned) | Depends on | Exit gate |
|---|---|---|---|---|---|
| **W1** | `AMSDP-QUE-006-W1-PRERECORDED-PLAYBACK-ENGINE` | Segment resolution + prerecorded player, pack-driven | `frontend/lib/announcements/segments.js`, `prerecorded-audio.js`, 2 new test files | DR-1, DR-2, DR-4, DR-5, DR-9 | roadmap §8.1 **AC-1…AC-8** |
| **W2** | `AMSDP-QUE-006-W2-QUEUE-INTEGRATION` | Prerecorded strategy in the controller; fire-and-forget announce on the `call` action and the operator button; no awaiting, no duplicate | `controller.js`, `pages/queue.js`, `QueueAnnouncements.js`, tests | W1; POD-12 for a `call` **UI** | queue ops unaffected with audio failing; duplicate suppressed |
| **W3** | `AMSDP-QUE-006-W3-VOICE-CONFIGURATION` | Voice-pack domain, config precedence, permissions, admin UI | `models.py`, new migration, `backend/organization/voice_packs.py`, `announcement_config.py`, `common/config.py`, `permissions.py` (no new capability needed), frontend admin page | W1 (pack descriptor), DR-3/7/8 | denied-API tests for all five roles |
| **W4** | `AMSDP-QUE-006-W4-ROOM-SUPPORT` | Room transport end-to-end | `models.py`/migration **only if** POD-2 is decided | **POD-2 OPEN** | blocked; engine part already covered by W1 |
| **W5** | `AMSDP-QUE-006-W5-REMOTE-INSTALLATION` | Local agent (outbound poll, verified download, atomic install, rollback, status) + distribution API | new `scripts/que-006-agent/` or `local_agent/`, distribution routes in W3's router | W3 (pack identity + checksums), DR-6 | install/update/rollback/offline scenarios |
| **W6** | `AMSDP-QUE-006-W6-ASSET-CLEANUP` | Dependency report only | `docs/implementation/` report | **POD-7 OPEN** | no file moved or deleted |
| **W7** | `AMSDP-QUE-006-W7-INTEGRATED-VERIFICATION` | Cross-workstream matrix, browser/offline evidence, consolidated report | `QUE-006_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | W1–W6 | honest status per row; no unverified claim |

### 4.1 Ordering consequence of this inspection

W1 → W3 → W2 is the technically correct order, because W2 wires a *configured* strategy into the queue
page and W3 is what makes a strategy configurable. W2 is nevertheless executed **after W1 as the
assignment orders it**, using the built-in pack, and simply re-reads its config source in W3. That
keeps the assignment's sequence while avoiding a rewrite: the W2 integration point takes the pack from
one resolver function whose source W3 later changes from "built-in" to "server config".

W4 stays blocked (POD-2). W6 produces a report only (POD-7). W5's distribution half needs W3's pack
identity, so W5 follows W3.

### 4.2 Risks and their mitigations

| Risk | Mitigation |
|---|---|
| A second audio engine duplicates the speech adapter's rules | The controller keeps the *decisions* (dedupe, overlap, activation); the engine is a transport only. |
| Browser autoplay refusal looks like success | `completed` only from the final `ended`; `play()` rejection → `blocked`; never inferred from a resolved promise. |
| Queue regressions | No queue handler awaits playback; a static test asserts it (roadmap AC-7). |
| Migration risk on existing data | One additive table, no column changes; upgrade/downgrade both provided and tested. |
| Silent language/personality substitution | Precedence returns an explicit source or `no_voice_pack`; never a substitute. |
| Existing draft recordings touched | W1/W3 read the manifest and never write it; no asset is created, moved or re-encoded. |

---

## 5. Phase-gate protocol for every workstream

1. **Inspect** — read the exact files, record line numbers used.
2. **Plan** — the row in §4 plus a per-workstream plan in its report.
3. **Implement** — only that workstream's files.
4. **Test** — unit + regression; `cd frontend && npm test` for frontend, `pytest` for backend.
5. **Verify** — acceptance criteria table with criterion → test name → result.
6. **Report** — `docs/implementation/QUE-006_W<n>_<NAME>_REPORT.md`, with the `.clinerules` §6
   compliance section.
7. **Regression** — re-run the previous workstreams' suites; record the counts.
8. **Proceed** — only when every non-blocked criterion is VERIFIED.

Status vocabulary is the assignment's seven-value set. Nothing is marked complete on the strength of
a green suite alone; VERIFIED requires a second artefact (test output captured in the report, or a
live call/browser run).
