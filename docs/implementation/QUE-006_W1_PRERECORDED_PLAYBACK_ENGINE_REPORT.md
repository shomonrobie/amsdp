# QUE-006 W1 — Prerecorded Playback Engine (implementation report)

**Assignment ID:** `AMSDP-QUE-006-W1-PRERECORDED-PLAYBACK-ENGINE`
**Date:** 2026-11-21
**Repository:** HEAD `37cf3d1` + the uncommitted work this programme is adding
**Status:** **IMPLEMENTED AND VERIFIED (unit level)** for roadmap §8.1 AC-1…AC-8.
**Not verified:** actual browser playback (see §7). No browser or device was driven.

---

## 1. What was built

| File | Status | Purpose |
|---|---|---|
| `frontend/lib/announcements/segments.js` | new, 202 lines | Pure resolution of an announcement payload into the ordered clips of one voice pack. No DOM, no `Audio`, no timers. |
| `frontend/lib/announcements/prerecorded-audio.js` | new, 377 lines | The player: one `Audio` element at a time, sequential clips, completion from the final `ended`, injectable environment. |
| `frontend/tests/queue-announcement-segments.test.mjs` | new, 7 tests | AC-1 (80-case matrix), AC-3 pre-flight, AC-6 path shape, pack versioning, refusals. |
| `frontend/tests/queue-announcement-prerecorded.test.mjs` | new, 15 tests | AC-2…AC-7 against a fake `Audio` element and fake timers. |

Nothing else was modified by W1. No asset, manifest entry, template, schema, permission or
queue rule was touched.

## 2. Design decisions (and why)

1. **The pack boundary sits under the engine.** A pack is data:
   `{id, language, version, scope, basePath, manifest, roles?}`. Resolution reads *asset ids*
   (`en.phrase.token-number`, `bn.digit.4`, …) and builds `basePath + playbackFile`. A second English
   or Bangla voice, or version 2 of either, is therefore a new manifest + base path with **no code
   change** — proven by the `TF-1` test.
2. **The wording contract stays in `content.js`.** `resolveSegments()` calls `buildAnnouncement()`
   first and refuses the payload for the same reason it would, so a second place can never decide what
   is said. The segment list is then proven against that text (§3, AC-1).
3. **Completion means `ended` on the last clip.** `play()` resolves `completed` only after the loop
   over all segments finishes; every other exit carries a reason. `start`/`play()` returning is never
   treated as success.
4. **Refusal before sound.** A missing asset is detected in resolution, so no `Audio` element is
   created (AC-3 test asserts the factory was never called).
5. **The silent clip is a gap, not a clip.** `en.phrase.room-suffix` is `contentStatus:
   intentional-pause` (300 ms of silence) and the manifest's own note says an engine must insert a
   pause. It becomes a timed segment carrying the catalogue's duration. **No inter-clip gap is
   invented** — POD-3 is still open.
6. **No fetch, ever.** The player never reads the network: the manifest is injected and clips are
   local paths. AC-6 test installs a `fetch` spy and asserts zero calls.
7. **Explicit refusals instead of substitutions.** `unsupported_language`, `unspeakable_token`,
   `unspeakable_room`, `manifest_unavailable`, `missing_asset`, `decode_error`, `interrupted`,
   `network_error`, `unsupported_source`, `blocked`, `audio_unavailable`, `error`. None of them is
   "fall back to speech".

## 3. Acceptance criteria — roadmap §8.1, preserved verbatim

| AC | Criterion (roadmap wording, abbreviated) | Test | Result |
|---|---|---|---|
| AC-1 | Segment resolution agrees with `buildAnnouncement()` for every case; proven by comparing against the approved text, not by inspection | `queue-announcement-segments.test.mjs` → *AC-1 every resolved segment list speaks the approved sentence* (**80 combinations**: 2 languages × 8 tokens × 5 room values), plus *AC-1 the segment order is the catalogue contract* | **PASS** |
| AC-2 | Success resolves only after the final segment's `ended`; a synthetic cut-off resolves `failed('interrupted')` | *AC-2 completed is reported only after the final clip ends*; *AC-2 a cut-off mid-sentence is failed(interrupted)*; *AC-2 an unexpected pause is interrupted*; W2's end-to-end test repeats it through the controller | **PASS** |
| AC-3 | A missing asset resolves `failed('missing_asset')` **before** any sound and never falls back to speech synthesis | *AC-3 a missing asset fails before any audio element exists* (asserts `created.length === 0` and `missing === ['en.digit.7']`) | **PASS** |
| AC-4 | A corrupt/undecodable file resolves `failed('decode_error')` and the engine stays usable | *AC-4 a corrupt clip fails as decode_error and the player stays usable* (the next announcement completes) | **PASS** |
| AC-5 | A second announcement while one is playing resolves `busy` (no overlap) | *AC-5 a second announcement while one plays is busy* (and no second audio element is created) | **PASS** |
| AC-6 | No network fetch when the catalogue is installed | *AC-6 an installed Bangla catalogue plays with no network access* (`fetch` spy: 0 calls); *AC-6 assets resolve to local paths under the pack base path* | **PASS** |
| AC-7 | No queue handler awaits the engine; a static test asserts the queue page never awaits playback | *AC-7 the queue page never awaits playback (static check)* — comments stripped, so only code can break it | **PASS** |
| AC-8 | The existing 53 frontend tests still pass; new tests drive a fake audio element (no browser needed) | Full announcement battery: **90 tests, 89 pass, 0 fail, 1 skipped** (the 4 pre-existing suites contribute 53 = 52 pass + 1 skip) | **PASS** |

## 4. Test evidence (actual output)

```
cd frontend && node --test tests/queue-announcement-{content,controller,speech,segments,prerecorded}.test.mjs \
  tests/queue-announcements-boundary.test.mjs tests/queue-announcement-w2-integration.test.mjs
  tests 90 · pass 89 · fail 0 · skipped 1 · duration_ms 1571
```

W1 alone: `queue-announcement-segments.test.mjs` 7/7 pass; `queue-announcement-prerecorded.test.mjs`
15/15 pass.

Pre-existing failures elsewhere in `frontend/tests` are **not** W1's and were left untouched:
`calendar-render.test.mjs` (Node on Windows refuses the test's `E:`-absolute module URL —
`ERR_UNSUPPORTED_ESM_URL_SCHEME`) and `banglanamesense-dataset.test.mjs` (pinned dataset checksum no
longer matches the tracked dataset). Both files are unmodified in this working tree.

## 5. Deviations and honest notes

| # | Note |
|---|---|
| N-1 | **Clip boundaries are separated by a space** in the returned `spokenText`. Without it, two digit clips read as the word "onezero"; the comparison therefore joins clips with a space and drops whitespace last. Word order and content are compared strictly. |
| N-2 | **TF-2 confirmed by test.** `en.phrase.no-room` is `" please come to the front."` while the template carries a comma. Punctuation is inaudible and the clip is authoritative for the draft (POD-9 still open); nothing was re-recorded. |
| N-3 | **A room with no digits is refused** (`unspeakable_room`) rather than spelled letter by letter. This is a technical refusal to avoid inventing a number format (POD-1/POD-2 open). |
| N-4 | **No token/room bound was invented.** Tokens keep `content.js`'s existing 9-digit rule; rooms are unbounded digit runs until POD-1 decides. |
| N-5 | **With-room playback is unit-tested only.** The production with-room path stays unreachable until POD-2 names a room source, exactly as the roadmap's blocked sub-item says. |

## 6. Regression check

The four pre-existing announcement suites still pass unchanged (53 tests: 52 pass, 1 skipped).

**Correction to an earlier draft of this report:** the boundary suite's JSX-compile check **skipped**
itself, because this workspace has no `frontend/node_modules` (no `next/dist/build/swc`). W1 therefore
did **not** compiler-verify `pages/queue.js` or `QueueAnnouncements.js`; W1 did not modify either file, so
the point is only that no such claim may be made. W2's edits to those two files carry the same caveat,
recorded in its report.

## 7. What is **not** verified by W1

- **No browser ran.** No claim of audible playback, of a real `ended` event, of a real autoplay
  refusal, or of a device hearing anything. Those belong to W7's browser/device verification.
- **No real asset decode.** `decode_error` is proven from a `MediaError` code, not from a corrupt file
  in a browser.
- **Offline is proven as "no fetch issued"**, not by disconnecting a network.

## 8. Governance and skill compliance (`.clinerules` §6)

- **Domain routing (§4):** Frontend UI/components → `saas-frontend-ux.md` as adapted in the governance
  assessment; Queue/workflow → Business Rules Parts V–VII. Applied: no new dependency, framework-free
  modules, injectable environment, existing test conventions (`node --test`, no library added).
- **Skills:** none installed in this workspace (§5). No skill is claimed; governance documents were
  used instead, as §4 requires.
- **Non-negotiables honoured (§3):** no secret logged; tenant key untouched; no schema, permission or
  audit change; no queue logic change; nothing verified was claimed beyond what the tests show.
- **Wording/asset freeze (DR-1/DR-2):** `content.js` templates, the manifest and all 72 audio files are
  byte-unchanged. The engine reads them.
- **Report location (§11):** `docs/implementation/` — subject-matching existing folder.
