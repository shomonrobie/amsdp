# QUE-006 — Final Implementation and Verification Report

**Assignment:** `AMSDP-QUE-006-MASTER-IMPLEMENTATION`
**Date:** 2026-11-21
**Repository:** HEAD `37cf3d1` plus this programme's uncommitted work (nothing committed, pushed or deployed)
**Overall status:** **NOT IMPLEMENTATION COMPLETE.** Two of the seven workstreams are complete at unit
level (W1, W5-agent), two are partial (W2, W3), one is blocked by an owner decision (W4), one is a
delivered analysis (W6), and one — this report — is the integrated assessment (W7). The blockers are
**decisions and environment**, not effort: POD-2, POD-7, POD-12, and a host that cannot run the backend
stack.

---

## 1. Executive summary

| What changed | Effect |
|---|---|
| A prerecorded playback engine (`segments.js`, `prerecorded-audio.js`) | The queue page can now speak the approved sentences from installed clips, in both languages, with or without a room, reporting completion only when the last clip ends |
| The controller learned a transport (`prerecorded` by default, `speech` only by explicit configuration) | Browser speech is no longer the mechanism; it is the documented alternative |
| A queue-call transition rule (`queue-transitions.js`) plus a page seam | A `waiting → called` change is announced exactly once, fire-and-forget, and never awaited |
| A configuration precedence resolver (`voice-packs.js`) | Organisation override → platform default → built-in draft → nothing, with every refusal reported |
| A facility agent (`scripts/que-006-agent/`) | Verified download, atomic install, rollback, recovery and offline use — tested against a stub server |
| Five reports plus this one | Every claim above is traceable to a named test |

**What did not change.** The approved wording, all 72 audio files, the manifest, the queue's state machine,
the database schema, and every permission. The draft voice remains the accepted draft (DR-1).

## 2. Product Owner decisions implemented

| Decision | Where implemented | Evidence |
|---|---|---|
| DR-1 draft frozen, no re-recording | nothing written to `frontend/public/audio/**` or `content.js` templates | `git status` shows no audio/manifest modification |
| DR-2 approved wording, no doctor/patient identity | `content.js` untouched; segments are proven **against** it | AC-1 test, 80 combinations |
| DR-3 configuration roles (`super_admin` platform, `org_admin` own org, others none) | client selectability + the existing `org.manage` / `platform.admin` matrix; **server routes not implemented** | `queue-announcement-voice-packs.test.mjs`; W3 §2 |
| DR-4 prerecorded primary, speech optional, never an automatic Bangla fallback | `controller.js` transport, `QueueAnnouncements.js` pack wiring | W2 tests 1, 7, 8, 9 |
| DR-5 queue never waits, success only after completion | engine `completed` from final `ended`; static "no await" tests | AC-2, AC-7, W2 test 11 and 15 |
| DR-6 remote installation architecture | `scripts/que-006-agent/` | 10 installer tests |
| DR-7 configurable English **and** Bangla voice library | pack descriptor + per-language selection; **storage/upload/approval not implemented** | `voice-packs.js` + tests; W3 §3 |
| DR-8 organisation isolation | `checkSelectable()` refuses a foreign pack; **server enforcement not implemented** | W3 test 3 |

## 3. Final architecture (as built)

```
queue page (operator)
  └─ useQueueAnnouncements()                       components/queue/QueueAnnouncements.js
       ├─ createPrerecordedPlayer({packProvider})  lib/announcements/prerecorded-audio.js
       │     └─ resolveSegments({token,room},pack) lib/announcements/segments.js
       │           └─ buildAnnouncement()          lib/announcements/content.js   (approved wording)
       ├─ createSpeechSynthesisAdapter()           lib/announcements/speech-synthesis.js (alternative)
       └─ createAnnouncementController({adapter, player, strategy})
             ├─ dedupe (event key, 5 s) · overlap (busy) · activation (gesture)
             └─ outcomes: spoken | failed(reason) | busy | cancelled | duplicate | needs_activation

call transition                                    lib/announcements/queue-transitions.js
  └─ announceOnCall()  (fire-and-forget)           pages/queue.js
```

The pack is data (`id, language, version, scope, basePath, manifest`). A new English or Bangla voice, or a
new version of either, needs a manifest and a base path — **no code change** (W1 test `TF-1`).

## 4. The seven workstreams, with honest status

| W | Assignment ID | Status | Verified | Not verified / blocked |
|---|---|---|---|---|
| **W1** | `…-W1-PRERECORDED-PLAYBACK-ENGINE` | **IMPLEMENTED AND VERIFIED** (unit) | AC-1…AC-8, 22 tests | browser playback, real decode, real offline |
| **W2** | `…-W2-QUEUE-INTEGRATION` | **PARTIALLY IMPLEMENTED** | transport, transitions, non-blocking, failure independence, 15 tests | the `call` **control** does not exist (POD-12), so automatic triggering is unreachable in the UI; no browser run |
| **W3** | `…-W3-VOICE-CONFIGURATION` | **PARTIALLY IMPLEMENTED** | precedence, isolation, selectability, 8 tests | **server-side domain, migration, upload, approval, admin UI — NOT IMPLEMENTED** (host cannot run the backend) |
| **W4** | `…-W4-ROOM-SUPPORT` | **BLOCKED — REQUIRES PRODUCT OWNER DECISION** | the room analysis and the engine's room support | the data source (POD-2) and the range (POD-1) are undecided; no schema change was made |
| **W5** | `…-W5-REMOTE-INSTALLATION` | **PARTIALLY IMPLEMENTED** | installer + agent, 10 tests | distribution API and entitlement enforcement (server, W3); no facility PC; no service wrapper |
| **W6** | `…-W6-ASSET-CLEANUP` | **DEFERRED BY PRODUCT OWNER** (POD-7) | full dependency report; 15 unreferenced files confirmed | no file moved or deleted — deliberately |
| **W7** | `…-W7-INTEGRATED-VERIFICATION` | **THIS REPORT** | suites re-run, counts recorded | no browser, no device, no network disconnection, no real server |

## 5. Integrated test results (re-run for this report)

```
cd frontend && node --test tests/queue-announcement-{content,controller,speech,segments,prerecorded,
  w2-integration,voice-packs}.test.mjs tests/queue-announcements-boundary.test.mjs
  → tests 98 · pass 97 · fail 0 · skipped 1

node --test scripts/que-006-agent/tests/installer.test.mjs
  → tests 10 · pass 10 · fail 0
```

**Total: 108 tests · 107 pass · 0 fail · 1 skipped** (Node v24.12.0, Windows).

The 53 pre-existing announcement tests are unchanged and still pass; the 55 new tests are this
programme's. The one skip is the JSX-compile check, which skips itself when
`next/dist/build/swc` is unavailable in the install.

**That skip matters and is not glossed over:** `frontend/node_modules` is absent in this workspace, so the
edits to `pages/queue.js` and `components/queue/QueueAnnouncements.js` are **not compiler-verified**. Their
logic is covered by the static tests, but `next build` was never run. `npm install && npm run build` is a
prerequisite before this page can be called deployable.

**Pre-existing failures elsewhere in `frontend/tests` are not attributable to this programme** and were
left untouched: `calendar-render.test.mjs` (Node on Windows rejects the test's `E:`-absolute module URL)
and `banglanamesense-dataset.test.mjs` (pinned dataset checksum differs from the tracked dataset).

### 5.1 Announcement-behaviour matrix (assignment §W7)

| Case | Covered by | Result |
|---|---|---|
| English with room | AC-1 matrix (`room: 5 / 101 / ৩`) | verified (segment level) |
| English without room | AC-1 matrix + AC-2/AC-5/end-to-end | verified |
| Bangla with room | AC-1 matrix + AC-6 offline playback | verified |
| Bangla without room | AC-1 matrix | verified |
| Single-digit token | AC-1 (`7`, `১`) | verified |
| Multi-digit token | AC-1 (`012`, `240`, `999`) | verified |
| Repeated digits | AC-1 (`11`) | verified |
| Zero-containing numbers | AC-1 (`101`, `012`), plus the zero clip in the digit-id test | verified |
| Room-number composition | AC-1 + the intentional-pause test | verified |

### 5.2 Voice library, permissions, operations, installation

| Area | Status |
|---|---|
| Platform default selection / organisation override / language and voice switching / multiple versions | **verified at the resolution level** (8 tests); **no persistence** (W3 server half missing) |
| Voice-pack upload, validation, approval workflow, organisation isolation in storage | **NOT IMPLEMENTED** |
| Permissions for `super_admin`, `org_admin`, `branch_admin`, receptionist, doctor | **client-side rules only**; denied-API tests **cannot run** without the backend stack → **NOT VERIFIED** |
| Offline playback, missing assets, corrupt assets, interruption, repeated calls, duplicate events, playback failure, queue independence | **verified at unit level** (fake audio element); **browser/refresh behaviours NOT verified** |
| New catalogue installation, version update, failed download, invalid checksum, interrupted install, rollback, offline | **verified for the agent** (10 tests) against a stub server; **not on a facility PC** |

## 6. Database and API changes

**None.** No migration was written, applied or reverted, and no API route was added. Two reasons, both
recorded in the workstream reports:

1. the intended changes (a `voice_packs` table, queue-entry room fields) depend on decisions POD-2 and the
   W3 server scope;
2. this host has no `pytest`, `fastapi` or `sqlalchemy`, so a migration could not be applied or tested —
   `.clinerules` §3 forbids shipping an unverified schema change.

The exact contract to implement is in `QUE-006_MASTER_IMPLEMENTATION_PLAN.md` §3 and
`QUE-006_W3_VOICE_CONFIGURATION_REPORT.md` §2.1.

## 7. Migration and rollback instructions (for what was actually shipped)

**Files added (no migration, no schema):**

- `frontend/lib/announcements/{segments,prerecorded-audio,queue-transitions,voice-packs}.js`
- `frontend/tests/queue-announcement-{segments,prerecorded,w2-integration,voice-packs}.test.mjs`
- `scripts/que-006-agent/{agent.mjs,lib/installer.mjs,tests/installer.test.mjs}`
- this programme's reports in `docs/implementation/`

**Files modified:** `controller.js`, `QueueAnnouncements.js`, `pages/queue.js`, `lib/i18n.js` (three
bilingual keys).

**Rollback (all reversible without a database):**

1. *Transport only:* pass `strategy: 'speech'` to `createAnnouncementController` in
   `QueueAnnouncements.js` — restores the pre-W2 browser-speech behaviour with no other change.
2. *Full frontend rollback:* `git revert` the four modified frontend files and delete the four new library
   files and their tests. Nothing else depends on them.
3. *Agent rollback:* stop running the CLI; the installed catalogues are plain directories under
   `AMSDP_VOICE_ROOT` and can be deleted at will. `node scripts/que-006-agent/agent.mjs --rollback <packId>`
   returns to the previous catalogue without touching the server.
4. *Do not* use `git reset --hard`, `git clean -fd` or `git stash` — the tree carries pre-existing
   uncommitted work (`.clinerules` §9).

## 8. Browser, device and offline verification — not performed

Stated plainly, because the assignment forbids the opposite:

| Claim | Made? | Why |
|---|---|---|
| Audible playback in a browser | **No** | no browser was driven; the engine is proven against a fake `Audio` element |
| Correct pronunciation of any clip | **No** | O-3 (named human reviewer) is open and all 28 assets are `humanReviewStatus: pending` |
| Device-level loudspeaker behaviour | **No** | no device available |
| Offline operation | **Partially** — *no network call is issued during playback* is proven; surviving a disconnected network was not exercised |
| Autoplay refusal | **Partially** — a rejected `play()` maps to `failed('blocked')` and the UI asks for a gesture; not observed in a real browser |

What the tests **do** prove is the logic that decides these things — which is the part that was wrong in the
shipped draft, where `start` was treated as evidence that a sentence had been spoken.

## 9. Known limitations

| # | Limitation | Owner of the fix |
|---|---|---|
| KL-1 | No voice-pack storage, upload, validation, approval, publication or admin UI | W3 (needs a backend-capable host) |
| KL-2 | No server-side enforcement of pack entitlement; the agent's pack list is a hint | W3 |
| KL-3 | No `call` control, so the automatic announcement is unreachable in the UI | QUE-001 / POD-12 |
| KL-4 | Automatic announcements require an operator gesture to unlock audio (browser policy) | product decision; documented, not worked around |
| KL-5 | No server-side announcement record (played/failed/skipped) | POD-4 |
| KL-6 | With-room announcements cannot be exercised end-to-end | POD-2 |
| KL-7 | The panel uses the operator's interface locale as the announcement language | OD-2 / W3 |
| KL-8 | No compatibility refusal of an incompatible pack (agent) | W3 metadata |
| KL-9 | No retry for a single failed clip; the sentence fails and reports why | by design; POD-3 may revisit |
| KL-10 | No Windows service wrapper for the agent | deployment work |

## 10. Outstanding Product Owner decisions

| ID | Decision | Blocks |
|---|---|---|
| **POD-2** | Room source: booking snapshot (`appointments.room_name`), live doctor chamber, or a queue-entry snapshot at call time — and may a room change mid-queue? | W4, with-room end-to-end |
| **POD-1** | Maximum token and room range | validation bounds |
| **POD-3** | Inter-clip pause policy (currently only the catalogue's own 300 ms) | audible pacing |
| **POD-4** | Is a server-side announcement record required? | announcement audit |
| **POD-7** | May the 15 unreferenced files leave the served tree? | W6 cleanup |
| **POD-8** | Trailing-silence policy | pacing refinement |
| **POD-9** | `en.phrase.no-room` comma discrepancy | wording sign-off |
| **POD-12** | Authorise the queue `call` UI | W2 end-to-end and every "announced on call" demonstration |
| **O-3** | Name a pronunciation reviewer per language | any claim of pronunciation approval |
| **O-2** | Trailing silence vs playback compensation | pacing refinement |

POD-5 is **closed by DR-3** (organisation scope, not per-branch). Still open from assignment §4: which voice
personality becomes the platform default, and whether a new recording may replace the accepted draft.
Neither was decided here.

## 11. Final acceptance readiness

| Question | Answer |
|---|---|
| Is the prerecorded engine ready for review? | **Yes** — AC-1…AC-8 verified at unit level; ready for a human listening pass |
| Is QUE-006 implementation complete? | **No.** Part 13's conditions are not met: no browser/device verification, no voice-pack administration, no room data, no distribution API, no denied-API permission tests |
| Is anything claiming more than it has? | No. Every verified line cites a test that passes in this tree; every unverified line says so |
| Smallest next increment with real value? | **POD-12 + a `call` button** — turns existing machinery into a demonstrable product behaviour with no schema change |
| Biggest missing piece? | **W3's server half** — without it, "configurable voice library" is a resolution rule, not a feature |
| What must not happen before the owner decides? | Re-record, trim, rename or delete assets, add schema, publish a pack, or claim pronunciation/sound quality |

### 11.1 Technical completion versus Product Owner acceptance

- **Technical completion:** W1 and the W5 agent are technically complete and unit-verified. W2 and W3 are
  sound but incomplete by scope. Nothing is `ACCEPTED`.
- **Product Owner acceptance** additionally requires (a) the human listening pass (O-3), (b) POD-2/POD-12 so
  the two headline behaviours are reachable, (c) W3's server half so a voice can actually be chosen, and
  (d) a browser/device session in a facility-like setup.

## 12. Files changed in this programme

**Added (11):** `frontend/lib/announcements/{segments,prerecorded-audio,queue-transitions,voice-packs}.js`;
`frontend/tests/queue-announcement-{segments,prerecorded,w2-integration,voice-packs}.test.mjs`;
`scripts/que-006-agent/agent.mjs`, `scripts/que-006-agent/lib/installer.mjs`,
`scripts/que-006-agent/tests/installer.test.mjs`.

**Modified (4):** `frontend/lib/announcements/controller.js`,
`frontend/components/queue/QueueAnnouncements.js`, `frontend/pages/queue.js`, `frontend/lib/i18n.js`.

**Documentation added (8):** the master plan, the six workstream reports and this report, all in
`docs/implementation/`.

**Documentation index (Revision 45), verified rather than assumed:** all eight documents are registered
in `docs/governance/AMSDP_Docs_Index_V1.0.md` with a *Read when* column and a byte figure re-checked
against disk (14 QUE-006 rows, 0 stale). The registered-row count was re-derived mechanically in this
session — **103 rows whose first cell is a backticked `.md` path, resolving to 103 distinct files, none
duplicated** — against **106** documents on disk, so the residual gap is **3**, and those three are named:
`AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
`AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` and
`AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md` (the pre-existing O-3/O-4 gap, not
created here). Two **pre-existing** byte figures that disagreed with the tree were corrected while doing
this — `QUE-006_AUDIO_GENERATION_CATALOGUE.md` (15,234 → 17,144 B) and
`QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` (18,432 → 11,809 B) — with
their prose descriptions checked and left as their authors wrote them.

**Not touched:** every audio file, the manifest, `content.js` wording, `backend/**`, migrations, permissions,
`docker-compose.yml`, and the pre-existing uncommitted work in the tree.

## 13. Governance and skill compliance (`.clinerules` §6)

- **Routing (§4):** frontend UI/UX · queue/workflow · database/schema (decided **not** to change) ·
  audit/reporting · deployment · multi-tenant isolation. Each report names the documents it applied.
- **Skills:** **none installed** in this workspace (§5) and **none claimed**. Governance documents were used
  instead, as the routing table requires.
- **Non-negotiables (§3):** no secret logged or exposed (the agent token is never printed); the tenant key
  stays `organization_id`; cross-tenant access fails closed; the UI is not presented as an authorisation
  boundary (the missing server half is stated, not faked); the audit trail is untouched; no schema change
  without a tested migration; no capability claimed that is not verified.
- **Evidence standard (§7):** IMPLEMENTED, VERIFIED, BLOCKED, DEFERRED and NOT IMPLEMENTED are used exactly
  as defined; nothing is `ACCEPTED`.
- **Repository safety (assignment §11):** HEAD recorded, `git status` inspected before and after, no commit,
  push, deploy, reset, clean or revert, and no pre-existing modification overwritten.
- **Report location (`.clinerules` §11):** `docs/implementation/`, the subject-matching existing folder; the
  documentation index is updated in the same task.
