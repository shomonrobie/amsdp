# QUE-006 W1 - Prerecorded Playback Engine (implementation and verification report)

**Assignment ID:** `AMSDP-QUE-006-W1-PRERECORDED-PLAYBACK-ENGINE`
**Report date:** 2026-11-21 (recovery and re-verification session)
**Work performed:** 2026-11-21, earlier session
**Repository:** HEAD `37cf3d1` plus the uncommitted QUE-006 work described in section 2
**Machine:** Windows, Node `v24.12.0`, `frontend/node_modules` **not installed**
**Status:** **IMPLEMENTED AND TESTED** for roadmap section 8.1 AC-1 ... AC-8. **NOT browser-verified**
and therefore **not product-verified**. See sections 6 and 7 for the exact boundary of the claim.

---

## 0. Provenance of this report (read this first)

The Product Owner reported that this document was missing after an unexpected power loss, under
the name `QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_IMPLEMENTATION_REPORT.md`.

What the repository actually contained at recovery time:

| Fact | Evidence |
|---|---|
| The requested filename did **not** exist | `Get-ChildItem docs/implementation/QUE-006_*` before this task |
| An equivalent report **did** exist as `QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_REPORT.md` (9,364 B, written 2026-11-21 08:33) | file listing |
| The work itself **was** on disk: `segments.js` (8,343 B), `prerecorded-audio.js` (13,374 B) and two new test files | `git status` (`?? frontend/lib/announcements/segments.js`, `?? frontend/lib/announcements/prerecorded-audio.js`, `?? frontend/tests/queue-announcement-segments.test.mjs`, `?? frontend/tests/queue-announcement-prerecorded.test.mjs`) |
| No interrupted-write artefacts existed (no `.tmp`, no partial files; every QUE-006 file carried a consistent timestamp) | directory listing |

So nothing was lost except the exact filename. This report **supersedes** the earlier
`..._REPORT.md` for naming purposes. That earlier file is **left byte-unchanged on disk** as the
historical record; it is not deleted, renamed or rewritten (`.clinerules` section 11). Both files are
now registered in the documentation index.

**Every claim below was re-derived in this session from the code and from a fresh test run.** The
earlier report's numbers were re-checked, not copied. One earlier statement was found overstated and
is corrected in section 5 (NM-1).

---

## 1. Scope and deliverable

The assignment's W1 deliverable, as fixed by the master plan (`QUE-006_MASTER_IMPLEMENTATION_PLAN.md`,
section 4 row W1) and by decision record DR-9, is:

> Segment resolution plus a prerecorded player, pack-driven, framework-free, verified against
> roadmap section 8.1 **AC-1 ... AC-8** (preserved verbatim).

Nothing else. W1 must not change wording, assets, the manifest, queue logic, permissions or schema
(roadmap section 8.1 "Must not change"). No with-room end-to-end path may be claimed while POD-2 is
open.

## 2. Files inspected or added

### 2.1 Added by W1 (all still untracked, unmodified since the earlier session)

| File | Bytes | Lines | Purpose |
|---|---:|---:|---|
| `frontend/lib/announcements/segments.js` | 8,343 | 203 | Pure resolution of a `{token, room}` payload into the ordered clips of one pack. No DOM, no `Audio`, no timers, no `fetch`. |
| `frontend/lib/announcements/prerecorded-audio.js` | 13,374 | 384 | The transport: one `Audio` element at a time, sequential clips, completion from the final `ended`, injectable audio factory and timers. |
| `frontend/tests/queue-announcement-segments.test.mjs` | 7,508 | - | 7 tests: AC-1 80-case matrix, AC-3 pre-flight, AC-6 path shape, TF-1 pack versioning, refusals, helpers. |
| `frontend/tests/queue-announcement-prerecorded.test.mjs` | 14,641 | - | 15 tests: AC-2 ... AC-7 against a fake `Audio` element and fake timers. |

### 2.2 Read, not modified, by W1

| File | What was verified in it |
|---|---|
| `frontend/lib/announcements/content.js` (165 lines) | `TEMPLATES` are the only wording source; `buildAnnouncement()` reads **only** `token` and `room` (lines 112-142); `announcementEventKey()` returns `entry:<id>:<action>:<revision>` (lines 153-165); serial extraction caps at 9 digits and refuses UUID/hex (lines 86-97). Byte-unchanged by W1. |
| `frontend/public/audio/manifest.json` | Schema `AMSDP-QUE-006-audio-assets/2.0`, `version 2.0`, **28 assets**; every one of the 28 `playbackFile` paths exists on disk (checked mechanically this session: `missing on disk: 0`); `en.phrase.room-suffix` is `contentStatus: intentional-pause`, `durationSeconds: 0.3`. |
| `frontend/lib/announcements/controller.js` | W2's file; W1 supplies the player it drives. Read to confirm W1 did not duplicate the controller's decisions. |

No audio file, manifest entry, template, schema, permission or queue rule was touched by W1.

## 3. Implementation status, element by element

The classification vocabulary is the assignment's: IMPLEMENTED, TESTED, VERIFIED (a second,
independent artefact confirms it), PARTIALLY IMPLEMENTED, NOT IMPLEMENTED, BLOCKED.

| W1 element (assignment / roadmap) | Status | Where it lives | What the evidence actually shows |
|---|---|---|---|
| Manifest-driven asset resolution | IMPLEMENTED + TESTED | `segments.js:148-202` | Asset **ids** (`en.phrase.token-number`, `bn.digit.4`, ...) are resolved through the pack's own manifest and `basePath`; file names are never parsed. |
| Correct English and Bangla segment composition | IMPLEMENTED + TESTED | `segments.js:44-57`, `119-177` | Role table per language; Bangla digits are normalised to ASCII for id lookup, then spoken from the Bangla clips. |
| Agreement with the approved announcement wording (AC-1) | TESTED (internal agreement) | `queue-announcement-segments.test.mjs` | 80 combinations = 2 languages x 8 tokens x 5 room values, comparing the resolved clip text against `buildAnnouncement()` output. See NM-1 for what this does and does not prove about the *recorded* audio. |
| Playback completion only after the final segment ends (AC-2) | IMPLEMENTED + TESTED, **not verified in a browser** | `prerecorded-audio.js:209-236` | `run()` returns `completed` only after the loop finishes; the loop returns early on any non-`completed` step. A resolved promise is never treated as success. |
| Interrupted playback handling | IMPLEMENTED + TESTED | `prerecorded-audio.js:183-194` | `pause`/`abort` that we did not ask for resolve `failed('interrupted')`; our own `cancel()` resolves `cancelled`. |
| Missing asset handling (AC-3) | IMPLEMENTED + TESTED | `segments.js:179-186`, `prerecorded-audio.js:252-261` | Missing ids are collected **before** playback; the test asserts the audio factory was never called. |
| Corrupt asset handling (AC-4) | IMPLEMENTED + TESTED, **not verified with a real corrupt file** | `prerecorded-audio.js:62-69`, `185-186` | `MediaError` codes map to `decode_error` / `network_error` / `unsupported_source`; the player is reusable afterwards (`playing` is reset in `finally`). |
| No automatic speech-synthesis fallback | IMPLEMENTED + TESTED | `segments.js` refusals; `controller.js:57-61` | Refusals are explicit reasons. `strategy: 'prerecorded'` without a player **throws** rather than downgrading. Speech is reachable only when a caller explicitly asks for it. |
| Busy / overlap handling (AC-5) | IMPLEMENTED + TESTED | `prerecorded-audio.js:243-250` | A second `play()` while `playing` resolves `busy`; nothing is queued and nothing overlaps. |
| Offline behaviour / network independence (AC-6) | IMPLEMENTED + TESTED as "no fetch issued" | `prerecorded-audio.js` (no network API anywhere), `segments.js:73-79` | A `fetch` spy asserts zero calls. This is **not** a disconnected-network test (section 6). |
| Queue operations do not await playback (AC-7) | IMPLEMENTED + TESTED (static) | `pages/queue.js:83-122`; test in the prerecorded suite | The static test strips comments and fails on any `await` in the seam. The queue write path (`doAction`, `pages/queue.js:124-129`) contains no audio reference. |
| Unit tests and their results (AC-8) | TESTED | see section 4 | Reproduced this session, not asserted. |
| Pack boundary sits under the engine (a new voice = new data, not new code) | IMPLEMENTED + TESTED | `segments.js:82-112`; TF-1 test | A second pack version resolves through the same code path. |

### 3.1 The one non-speech segment is a gap, not a clip

`en.phrase.room-suffix` is 300 ms of silence (`intentional-pause`). The engine converts it into a timed
segment carrying the catalogue's own duration (`segments.js:123-136`) and waits it out
(`prerecorded-audio.js:215-222`). No other inter-clip gap is invented anywhere: POD-3 (pause policy)
is still an open owner decision, and inventing a gap would pre-empt it.

## 4. Test evidence - exact commands and results (run in this session)

Working directory `e:\amsdp\frontend` unless stated otherwise.

```
node --version
  -> v24.12.0
```

**W1 suites alone:**

```
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test ^
  tests/queue-announcement-segments.test.mjs tests/queue-announcement-prerecorded.test.mjs
```

Result: **22 tests, 22 pass, 0 fail, 0 skipped** (7 + 15), exit 0.

**The four pre-existing announcement suites (AC-8's "existing 53 tests"):**

```
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test ^
  tests/queue-announcement-content.test.mjs tests/queue-announcement-controller.test.mjs ^
  tests/queue-announcement-speech.test.mjs tests/queue-announcements-boundary.test.mjs
```

Result: **53 tests, 52 pass, 0 fail, 1 skipped**, exit 0. The single skip is
`queue-announcements-boundary.test.mjs:31` - *"the queue page and the announcement panel compile as
JSX"* - skipped with `next/dist/build/swc unavailable in this install`.

**All eight announcement suites:**

```
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test ^
  tests/queue-announcement-content.test.mjs tests/queue-announcement-controller.test.mjs ^
  tests/queue-announcement-speech.test.mjs tests/queue-announcement-segments.test.mjs ^
  tests/queue-announcement-prerecorded.test.mjs tests/queue-announcement-voice-packs.test.mjs ^
  tests/queue-announcement-w2-integration.test.mjs tests/queue-announcements-boundary.test.mjs
```

Result: **98 tests, 97 pass, 0 fail, 1 skipped**, exit 0.

**The `npm test` population (all of `frontend/tests`):**

```
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs
```

Result: **270 tests, 266 pass, 2 fail, 2 skipped**, exit 1. Both failures are **pre-existing and
unrelated to QUE-006**, in files this programme has never modified:

| Failing suite | Reason |
|---|---|
| `tests/banglanamesense-dataset.test.mjs:60` | pinned dataset SHA-256 no longer matches the tracked dataset (`6f69a0ef...` vs expected `ac037c24...`) |
| `tests/calendar-render.test.mjs:1` | Node on Windows refuses the test's `E:`-absolute module URL (`ERR_UNSUPPORTED_ESM_URL_SCHEME`) |

Neither file appears in `git status`, so neither was changed by this programme. They are recorded
here because a reader running `npm test` **will** see two red suites and must not attribute them to
W1.

### 4.1 Asset existence check (mechanical)

```
$m = Get-Content frontend\public\audio\manifest.json -Raw | ConvertFrom-Json
foreach ($a in $m.assets) { Test-Path (Join-Path 'frontend\public\audio' $a.playbackFile) }
```

Result: **28 `playbackFile` entries, 0 missing on disk.** The catalogue the engine resolves against is
complete as shipped.

## 5. Corrections and honest notes

| # | Note |
|---|---|
| NM-1 | **What AC-1 does and does not prove.** The 80-case test compares the *resolved clip text* against `buildAnnouncement()` output, i.e. it proves the engine composes the same sentence the wording contract defines - not that the recorded WAV/MP3 content says it. The link to the approved wording runs through the manifest's own `spokenText`, which was authored from the approved templates. Verified this session by reading the manifest: `en.phrase.token-number` = `"Token number "`, `en.phrase.proceed-to-room` = `", please proceed to Room "`, and the Bangla phrases carry the approved Bangla clauses. That is a data-level check, **not** a listening check - see D-5. |
| NM-2 | **A real wording deviation exists in the recorded English draft, and it was not "fixed".** The manifest's `en.phrase.no-room` is `" please come to the front."` with **no leading comma**, so the assembled sentence reads "Token number 4 please come to the front." where the approved template has a comma. Punctuation is inaudible and the recording is authoritative for the approved DRAFT (DR-1); nothing was re-recorded or re-worded. POD-9 remains open. |
| NM-3 | **The earlier report's "90 tests" figure was a snapshot of a smaller test population** (taken before the voice-pack suite existed). Re-derived now: eight announcement suites = 98 tests; with the installer agent = 108. The earlier number is not wrong about what it measured, but it must not be quoted as the current figure. |
| NM-4 | **A room with no digits is refused** (`unspeakable_room`) rather than spelled letter by letter, and **no token/room bound was invented** (tokens keep `content.js`'s 9-digit rule; rooms are unbounded digit runs until POD-1 decides). |
| NM-5 | **With-room playback is unit-tested only.** The production with-room path is unreachable until POD-2 names a room source, because `queue_entries` has no room column (see the W4 report). |

## 6. Browser / runtime verification evidence

**None. Explicitly absent.** No browser was launched, no device was driven, no audio was heard, no
real `ended` event fired, no real autoplay refusal was observed, and no real corrupt file was fed to a
decoder. Everything in section 3 marked TESTED was proven against a **fake `Audio` element and fake
timers**.

What the fake-element tests can and cannot prove:

| Can prove | Cannot prove |
|---|---|
| The module's own logic maps events to outcomes correctly | That a real browser fires `ended` where the fake does |
| No network call is issued by the engine | That playback works with the network physically disconnected |
| Nothing is reported as success before the final clip ends | That the audio is audible on the target hardware, at the right volume, or intelligible |
| A `MediaError` code produces `decode_error` | That a genuinely corrupt file produces that code |

The isolated preview harness under `scripts/que-006-audio/preview/` exists but was **not** used here,
and it is not product verification either (its own report says so).

## 7. Known defects and unresolved dependencies

| # | Item | Effect | Owner |
|---|---|---|---|
| D-1 | No browser or device verification | The audible product behaviour is unproven | W7 / Product Owner |
| D-2 | Room source undecided (POD-2) | The with-room sentence cannot be produced in the product | Product Owner |
| D-3 | Room number range undecided (POD-1) | Engine refuses non-digit rooms; no bound assumed | Product Owner |
| D-4 | Pause policy undecided (POD-3) | Only the catalogue's own 300 ms silent clip is honoured | Product Owner |
| D-5 | Pronunciation review open (O-3) | Recordings are accepted as DRAFT, unlistened-to by the owner | Product Owner |
| D-6 | `frontend/node_modules` absent | JSX not compiler-verified; `npm install && npm run build` not run | next session |

## 8. Deviations from the master assignment

| # | Deviation | Reason |
|---|---|---|
| DEV-1 | The filename required by the assignment (`..._IMPLEMENTATION_REPORT.md`) was not the one the earlier session used (`..._REPORT.md`, which followed the master plan section 5 step 6 convention `QUE-006_W<n>_<NAME>_REPORT.md`). | The master plan's own naming rule conflicted with the assignment's. One file cannot satisfy both, so this report adopts the assignment's name and preserves the other as history. The conflict is recorded for the Product Owner. |
| DEV-2 | No additional "interrupted mid-clip" test beyond the `pause` / `abort` cases already present | The existing 15-test suite covers both non-completion paths; a duplicate test would add no evidence. |
| DEV-3 | The "no network" assertion lives at engine level, not page level | The page legitimately fetches `/audio/manifest.json` once; the *engine* is the offline-critical part. |

Nothing in the assignment's W1 scope was skipped silently. The with-room sub-item is blocked for the
stated reason, and the engine still implements and unit-tests it, exactly as roadmap section 8.1
requires.

## 9. Repository state and preservation statement

Verified in this session:

- HEAD is `37cf3d1`; **no commit, push, deploy, reset, clean, stash or revert** was performed.
- Before this task `git status --porcelain` showed 9 modified tracked files and 26 untracked entries,
  all belonging to earlier QUE-006 sessions. **All were preserved untouched.**
- W1's four files remain **untracked** (`??`), exactly as the earlier session left them; this session
  read their bytes and wrote none.
- The only files this task created are this report and the W2 report - documentation only. The
  documentation index was updated to register them (Revision 46).
- No audio asset, manifest entry, `content.js` template, schema, migration, permission or queue rule
  was modified. `content.js` appears as modified in `git status`, but that change belongs to the
  earlier doctor-name-removal / OD-3 work and was preserved byte-for-byte; W1 did not edit it.

## 10. Conclusion

**W1 is complete as a unit-level deliverable against roadmap section 8.1 AC-1 ... AC-8,** with one
criterion (AC-1's link to the *recorded* wording) proven at data level only, and one blocked sub-item
(with-room end-to-end) blocked by an open owner decision.

**W1 is not verified as a product behaviour.** Calling prerecorded announcements "working" in the
product requires a browser run with the installed catalogue, a real autoplay gesture, a real `ended`
event and a human listening check. None of those has happened, and this report does not claim them.

---

## 11. Governance and skill compliance (`.clinerules` section 6)

- **Domains routed (section 4):** frontend modules and tests (`saas-frontend-ux.md` as adapted in the
  governance assessment); queue/workflow behaviour (Business Rules Parts V-VII) for AC-7.
- **Documents read this session:** `docs/governance/AMSDP_Docs_Index_V1.0.md` (index + Revision 45),
  `QUE-006_MASTER_IMPLEMENTATION_PLAN.md` (decision register DR-1 ... DR-10 and the W1 row),
  `QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md` section 8.1 (read
  verbatim at lines 678-704), the earlier W1 report, and the code listed in section 2.
- **Skills:** none installed in this workspace (section 5) - **none claimed**. Governance documents
  were used instead, as section 4 requires when a domain's skill slot is empty.
- **Non-negotiables honoured (section 3):** no secret logged or quoted; tenant key untouched; no
  schema, permission or audit change; nothing claimed as verified that only a fake element proved; no
  test, gate, CI result or skill invented.
- **Evidence standard (section 7):** IMPLEMENTED = code reachable (cited by file:line); TESTED = named
  tests passing **in this tree, in this session** (section 4); VERIFIED = deliberately withheld where
  no second independent artefact exists.
- **Report location (section 11):** `docs/implementation/` - the subject-matching existing folder. No
  migration was performed, so no manifest entry is owed.
- **Index:** registered as Revision 46 of `docs/governance/AMSDP_Docs_Index_V1.0.md`.


