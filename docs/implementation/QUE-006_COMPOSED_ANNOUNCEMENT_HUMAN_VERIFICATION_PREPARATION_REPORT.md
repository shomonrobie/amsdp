# QUE-006 — Composed Announcement Human-Verification Preparation Report

**Status:** preparation complete; **nothing approved, nothing accepted, no human listening verdict exists.**
**Date:** 2026-11-21
**Tooling:** `scripts/que-006-audio/preview/` (new, isolated; no product code changed by this work)
**Owner action required:** listen to the 20 samples and fill `review-template.csv` (§7, §11)

---

## 1. Purpose and scope

The 28 catalogue clips are delivered and format-standardised (see
`QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md`), but the product does not
assemble or play them yet, and no human has judged whether a *composed*
announcement — token digits + phrase + room digits, with the intended order and
junctions — sounds acceptable in English or Bangla. Every asset in
`manifest.json` is still `humanReviewStatus: pending`.

This report covers the isolated tooling built so that the Product Owner can make
that judgement with real audio, in a browser, without touching the product:

1. **20 composed WAV samples** — byte-for-byte concatenations of the delivered
   clips covering 5 token/room cases × 4 announcement patterns (English and
   Bangla).
2. **A reviewer page** — a loopback-only static server that renders the 20
   samples with captions produced by the product's own wording module, a clip
   timeline per sample, and a live composer for arbitrary token/room input.
3. **A review record** — a CSV (and mirrored Markdown) with one row per sample
   and blank verdict fields, so a pass/fail decision can be recorded per sample
   and attributed to a named asset.
4. **A browser verification harness** — a headless Chrome run that proves the
   page actually renders, plays and refuses what it says it does.

In scope: producing the audio, presenting it, recording the human verdict,
proving the presentation works. Out of scope: approving pronunciation, changing
any clip, wiring playback into the product, and defining the room-number range.

### Evidence levels used in this report (§7 of the core rules)

| Term | Meaning here |
|---|---|
| IMPLEMENTED | The file exists and is reachable/executable in this tree |
| TESTED | A named script or check was run in this session with the result quoted |
| VERIFIED | A second, independent artefact confirms it — **not achieved for audio quality**, which needs ears |
| ACCEPTED | Signed by the Product Owner — **not claimed anywhere** |

---

## 2. What was built, and how it works

```
scripts/que-006-audio/preview/
  compose-wav.mjs            generator: 20 composed WAVs + samples.json + data.json + clip-analysis.json
  compose.mjs                pure planning module: wording (via product content.js), clip order, junction pauses
  server.mjs                 loopback static server with five fixed read-only roots and method/route guards
  index.html / preview.css   reviewer page (no framework, no build step, no external requests)
  preview.js                  page logic: renders rows, plays samples, live composer, timeline, review columns
  make-review-template.mjs   writes review-template.csv + review-template.md from samples.json
  check-page.mjs             headless-Chrome harness over the DevTools protocol (12 checks)
  generated/                 build output, git-ignored except .gitignore itself
    samples/                 20 composed WAVs (14.15 MB)
    samples.json             per-sample manifest: segments, pauses, frames, SHA-256, decode result
    clip-analysis.json       measured speech bounds and trailing silence for all 28 clips
    data.json                page payload: contract, assets, samples, templates, pause options
    review-template.csv/.md  the review record
    source-baseline.json     SHA-256 of the 72 catalogue/manifest files, before and after composition
```

Two design decisions carry the weight:

* **No audio processing.** There is no ffmpeg step and no re-encode. The
  generator copies the PCM data chunks of the delivered WAVs into a new
  44.1 kHz/16-bit/mono file and re-hashes the result (§4). What the reviewer
  hears is the delivered clips, in order, nothing else.
* **No hard-coded wording.** `compose.mjs` imports the product's
  `frontend/lib/announcements/content.js` and the reviewer page imports the same
  module in the browser (`/announcements/content.js`). If the approved wording
  changes, the samples' captions and the composer's captions change with it; the
  page cannot drift from the product silently.

---

## 3. Isolation — what this touches, and what it does not

| Item | Treatment |
|---|---|
| `frontend/lib/announcements/content.js` | **Imported, never modified.** Read at build time by the generator and at page load by the browser |
| `frontend/public/audio/**` (28 clips + `manifest.json`) | **Read-only.** The server maps `/audio/` to this directory; the generator hashes all 72 catalogue/manifest files before and after the run and asserts equality (`source-baseline.json`) |
| Any human-review flag | **Untouched.** The page and the generator cannot change `humanReviewStatus`; every asset stays `pending` |
| Database / backend / migrations | **Not involved.** No connection, no schema change, no Alembic revision |
| Writes | Confined to `scripts/que-006-audio/preview/generated/` |
| Git | No commit, no push, no staging, no rebase in this work; no existing file was deleted or rewritten |

The server binds `127.0.0.1` only, serves four fixed path prefixes, refuses every
method except `GET`/`HEAD`, and refuses dotfiles. §9 records the observed
responses, including the refused traversal attempts.

`generated/.gitignore` contains `*` plus `!.gitignore`, so the 14.15 MB of
composed audio and the JSON payloads stay out of the repository while the
directory itself remains tracked.

---

## 4. The 20 samples — method, and the proof that the method held

Run: `node scripts/que-006-audio/preview/compose-wav.mjs`
Result (recorded in `samples.json`, `generatedAt 2026-11-21T05:31:27.766Z`):

| Property | Recorded value |
|---|---|
| Cases × variants | 5 × 4 = **20 samples** |
| Output contract | WAV format 1, **44.1 kHz, mono, 16-bit PCM**, matching `manifest.json` |
| Total output | **14,832,466 bytes** (14.15 MB) |
| Copied PCM ranges | **120 of 120 identical** to their source range |
| Decode verification | **20 of 20** samples decoded and cross-checked against their own frame counts |
| Wording checks | **20 of 20 match** `buildAnnouncement()` (0 mismatches) |
| Catalogue integrity | 72 files hashed before/after — **catalogueUnchanged: true** |
| Manifest snapshot | `manifestSha256 = f4a10872fc1324fa32058a76803b9edb762d8d7a7846f484c46c3369257a328c` |
| Junction pause | `DEFAULT_PAUSE_MS = 0` — **no pause is inserted in the delivered samples** |


Why zero junction pause is correct here, and not an omission: every delivered
clip still carries its own trailing room tone (§6), so a scheduled pause would
add a *second* silence. The rule implemented in `compose.mjs` is "a pause is
added before every clip except the first and before bound suffix clips
(`room-locative`, `room-suffix`, `no-room`), which are always butted directly".
The composer on the page exposes 0/50/100/150/200/300 ms so the owner can hear
what a deliberate junction pause *would* sound like — but the 20 samples
themselves are the unpaused baseline.

The wording check is a live comparison, not a transcription: the generator
spawns a child process that imports the product's `content.js`, renders
`buildAnnouncement()` for each sample's case, and compares that string with the
caption written into `samples.json`. Templates seen at composition time:

* English, with room — `Token number {number}, please proceed to Room {room}.`
* English, without room — `Token number {number}, please come to the front.`
* Bangla, with room — `টোকেন নম্বর {number}, কক্ষ {room}-এ আসুন।`
* Bangla, without room — `টোকেন নম্বর {number}, অনুগ্রহ করে সামনে আসুন।`

Regeneration is deterministic: an unchanged input produces byte-identical output
(`reusedOnThisRun` is recorded per sample), and `source-baseline.json` fails the
run if the catalogue moved underneath it.

---

## 5. Sample inventory

| Sample | Lang | Pattern | Token | Room | Duration | Clips | SHA-256 (12) |
|---|---|---|---:|---:|---:|---:|---|
| S01-en-with-room-T4-R305 | en | English, with room | 4 | 305 | 6.439 s | 7 | caac035fcba6 |
| S02-en-no-room-T4 | en | English, without room | 4 | - | 3.396 s | 3 | fa01bac97b6c |
| S03-bn-with-room-T4-R305 | bn | Bangla, with room | 4 | 305 | 12.740 s | 7 | 30c55c3ac5a4 |
| S04-bn-no-room-T4 | bn | Bangla, without room | 4 | - | 6.090 s | 3 | 2664e2ae8ad0 |
| S05-en-with-room-T12-R305 | en | English, with room | 12 | 305 | 6.804 s | 8 | 4df632da5299 |
| S06-en-no-room-T12 | en | English, without room | 12 | - | 3.762 s | 4 | 4cc46bb659a9 |
| S07-bn-with-room-T12-R305 | bn | Bangla, with room | 12 | 305 | 14.560 s | 8 | 322185e3d541 |
| S08-bn-no-room-T12 | bn | Bangla, without room | 12 | - | 7.910 s | 4 | 4731496df7b4 |
| S09-en-with-room-T11-R303 | en | English, with room | 11 | 303 | 6.961 s | 8 | 3fbdc6a3870a |
| S10-en-no-room-T11 | en | English, without room | 11 | - | 3.840 s | 4 | 62a4fb010694 |
| S11-bn-with-room-T11-R303 | bn | Bangla, with room | 11 | 303 | 14.560 s | 8 | d9b34abf436b |
| S12-bn-no-room-T11 | bn | Bangla, without room | 11 | - | 7.910 s | 4 | 235af5f5cd89 |
| S13-en-with-room-T20-R100 | en | English, with room | 20 | 100 | 6.883 s | 8 | ce0866a657ce |
| S14-en-no-room-T20 | en | English, without room | 20 | - | 3.918 s | 4 | 21cb5ae9a734 |
| S15-bn-with-room-T20-R100 | bn | Bangla, with room | 20 | 100 | 14.560 s | 8 | 539c715e9c22 |
| S16-bn-no-room-T20 | bn | Bangla, without room | 20 | - | 7.910 s | 4 | 342d07523c96 |
| S17-en-with-room-T999-R999 | en | English, with room | 999 | 999 | 8.581 s | 9 | dad2b495e6c0 |
| S18-en-no-room-T999 | en | English, without room | 999 | - | 5.224 s | 5 | 16bcffa1e4e8 |
| S19-bn-with-room-T999-R999 | bn | Bangla, with room | 999 | 999 | 16.380 s | 9 | b495efb86d16 |
| S20-bn-no-room-T999 | bn | Bangla, without room | 999 | - | 9.730 s | 5 | d00708b7ad60 |

The five cases (T4/R305, T12/R305, T11/R303, T20/R100, T999/R999) exercise
single-digit, two-digit, three-digit and leading-vowel token shapes plus the
maximum recommended room number. Bangla samples run roughly twice as long as
their English counterparts for the same clip count — that is §6, not a defect in
the composer.


---

## 6. What the measurement found in the delivered clips

`clip-analysis.json` measures speech bounds at 2 % of each clip's peak
(≈ −34 dBFS relative) for all 28 assets. **Nothing was trimmed** — the numbers
exist so the owner can judge whether the trailing silence is acceptable.

| Language | Clips | Tail silence range | Mean tail | Clips with > 0.5 s tail |
|---|---:|---|---:|---:|
| English | 14 | 0.014 – 0.331 s | 0.204 s | 0 |
| Bangla | 14 | **0.874 – 1.388 s** | **1.260 s** | **14 of 14** |

Consequences, stated plainly:

* **Every Bangla clip ends with at least 0.874 s of near-silence**, and one
  reaches 1.388 s. In a 7-clip Bangla announcement that is roughly 8–9 s of
  silence distributed between words, which is why S03 is 12.740 s where S01 is
  6.439 s. Whether that sounds like "a calm announcement" or "a broken
  announcement" is exactly the judgement the owner has to make by ear. It was
  reported, not fixed: trimming would alter the delivered files and invalidate
  their checksums and manifest.
* **`en.phrase.room-suffix` is a punctuation-only asset** (`"."`) and measures as
  silent — that is correct, not a missing recording. The page marks it so a
  reviewer does not report "no sound at the end of the room number" as a defect.
* Total trailing silence across the catalogue: **2.85 s (English)** and
  **17.64 s (Bangla)** — useful when deciding whether to re-cut the Bangla set.

---

## 7. The review record

`node scripts/que-006-audio/preview/make-review-template.mjs` writes two files
from `samples.json`, both linked from the page:

* `generated/review-template.csv` — **1 header + 20 rows × 23 columns**,
  UTF-8 with BOM so Excel opens the Bangla columns correctly.
* `generated/review-template.md` — the same table plus a column guide, for
  reading without a spreadsheet.

Columns, in order: `sample_number, sample_id, language, announcement_type,
token, room, expected_text, duration_seconds, sha256_12, segment_count` — all
pre-filled from the generator, none typed by hand — followed by the blank
verdict fields: `verdict`, `intelligibility_1_5`, `pronunciation_1_5`,
`natural_prosody_1_5`, `digit_clarity_1_5`, `room_clarity_1_5`,
`junction_pause_ok`, `audible_artefacts`, `observations`, `defect_severity`,
`follow_up_action`, `reviewer`, `review_date`.

A blank row is not a pass: the page and the template both say so. `verdict`
accepts pass / fail / unsure; a `fail` is only actionable when
`follow_up_action` names the asset (the page's per-sample timeline gives the
exact `assetId` at every position, e.g. `bn.digit.7` or
`bn.phrase.room-locative`).

---

## 8. Browser verification harness — 12 checks, all passing

Run: `node scripts/que-006-audio/preview/server.mjs --port 8623` in one terminal,
then `node scripts/que-006-audio/preview/check-page.mjs --port 8623 --page-port 9342`.
Any free port pair works; the two `--port` values must match.

The harness is a small DevTools-protocol client over Node's built-in WebSocket
(no Puppeteer, no Playwright, no new dependency). It launches headless Chrome
against a throwaway profile, opens `about:blank` first and then navigates, so an
exception thrown *during page load* is still captured.

Observed run — **Chrome 158.0.8127.36, Node v24.12.0, exit code 0**:

| § | Check | Observed result |
|---|---|---|
| 11.1 | Page loads and renders every sample row | **20 of 20 rows** |
| 11.2 | Sample ids render in the generated order | 20 ids in `samples.json` order |
| 11.3 | Every caption equals the approved wording | 20 captions compared with `samples.json` |
| 11.4 | Every row has a play button | 20 of 20 |
| 11.5 | Language filter hides exactly the other language | 10 Bangla rows shown, 20 restored |
| 11.6 | An English sample plays to completion | 7,439 ms wall time for the 6.439 s file, status `S01-en-with-room-T4-R305 finished — 6.439 s played, Token number 4, please proceed to Room 305.` |
| 11.7 | A Bangla sample plays to completion at full length | 12,878 ms wall time for 12.740 s, status `S03-bn-with-room-T4-R305 finished — 12.740 s played, টোকেন নম্বর ৪, কক্ষ 305-এ আসুন।` |
| 11.8 | The review-record table mirrors the CSV header | 23 rows rendered from a 23-column header |
| 11.9 | An internal identifier is refused, never spoken | `Cannot announce this: the product refuses the input with "unspeakable_token"…` |
| 11.10 | A non-numeric room shows the wording but schedules no audio | Caption `Token number 7, please proceed to Room ICU-2.` + `No audio can be composed: room "ICU-2" contains "I", which is not a digit…`, 0 timeline entries, status unchanged |
| 11.11 | A hand-made announcement composes and plays to completion | 7,530 ms, 8 clips, 7.404 s played, `Token number 12, please proceed to Room 305. — Composed announcement finished` |
| 11.12 | No uncaught exception and no console error | Console clean for the whole session |

Two details worth noting, because they are the failure modes this harness exists
to catch:

* **11.10 asserts *no* scheduling, not a disabled button.** The first version of
  the check asserted that the Play button was disabled after a refused room; it
  is not disabled, and that is the correct behaviour — the button stays live so
  the reviewer can fix the input and press Play again. The assertion was wrong,
  not the page, and was corrected to assert zero timeline entries.
* **11.12 catches load-time exceptions.** A blank-page run earlier in the work was
  caused by an exception thrown before any check could run; the about:blank →
  navigate sequence plus the console/exception collector is what makes that
  visible instead of appearing as "0 rows".

Exit codes: `0` all checks passed, `1` at least one failed, `2` the harness could
not run (no Chrome/Edge, or nothing is serving the page — in which case the
report must say the page is *not* verified). A run that prints `SKIPPED` is not
evidence.


---

## 9. The server — what it serves and what it refuses

`server.mjs` binds `127.0.0.1` and maps exactly five prefixes:

| Prefix | Directory | Contents |
|---|---|---|
| `/` | `scripts/que-006-audio/preview/` | the page, CSS, JS |
| `/announcements/` | `frontend/lib/announcements/` | the approved wording module (read-only) |
| `/audio/` | `frontend/public/audio/` | the 28 delivered clips (read-only) |
| `/samples/` | `preview/generated/samples/` | the 20 composed WAVs |
| `/generated/` | `preview/generated/` | JSON payloads, review templates |

Probed in this session with a fresh server on a fresh port:

| Request | Response |
|---|---|
| `GET /` | 200 (7,628 bytes) |
| `GET /preview.css` | 200 (7,478 bytes) |
| `GET /preview.js` | 200 |
| `GET /generated/data.json` | 200 (44,562 bytes) |
| `GET /generated/review-template.csv` | 200 (3,266 bytes) |
| `GET /samples/S01-en-with-room-T4-R305.wav` | 200, `audio/wav` |
| `GET /audio/en/phrase/token-number.wav` | 200, `audio/wav` |
| `GET /.gitignore` | 404 (dotfile refused) |
| `GET /nope.txt` | 404 |
| `GET /..%2f..%2fpackage.json` | 404 |
| `GET /%2e%2e/%2e%2e/package.json` | 404 |
| `GET /generated/..%2f..%2fpackage.json` | 404 |
| `GET //etc/passwd` | 404 |
| `GET /C:/Windows/win.ini` | 404 |
| `GET /preview.js%00.css` | 400 (NUL byte refused) |
| `POST /`, `PUT /`, `DELETE /` | 405 |

`GET /server.mjs` returns 200 because the server's own source sits inside the
served review root. That is a deliberate trade — the tool is loopback-only,
read-only and contains no secret (it never reads a key or `.env`) — recorded here
so nobody mistakes it for an oversight.

---

## 10. What this does not prove

1. **Audio quality.** No human has listened. The harness proves the page plays
   the right bytes for the right duration; it cannot judge intelligibility,
   pronunciation, prosody or whether the Bangla trailing silence sounds natural.
2. **Product integration.** The application does not play these clips. This page
   composes audio itself; the product playback path remains unimplemented.
3. **Real hardware.** Playback ran through this machine's default output, headless
   with `--mute-audio` in the harness. Clinic speakers, volume and background
   noise are untested.
4. **Loudness.** No normalisation and no level check; levels are whatever the
   delivered clips carry (peaks recorded in `clip-analysis.json`).
5. **Approval.** Nothing here changes `humanReviewStatus`, and no sentence in this
   report should be read as approving a clip.
6. **A second environment.** Chrome 158 on Windows only; Firefox was not
   exercised, Edge is supported as a fallback by the harness but was not run.

---

## 11. Open items for the owner

| # | Item | Why it matters | Suggested decision |
|---|---|---|---|
| O-1 | **Bangla trailing silence (0.874–1.388 s per clip)** | Roughly doubles Bangla announcement length; may read as dead air on clinic hardware | Listen to S03/S07/S19 and decide: acceptable, or re-cut the Bangla set |
| O-2 | **Room-number range is undefined** | The catalogue records "1–999" as a *recommendation awaiting approval*; there is no rule to enforce | Approve 1–999, or state the real range. Until then the composer guards at 9 digits and refuses longer input rather than inventing a limit |
| O-3 | **Junction pause policy** | The delivered samples use 0 ms (the clips' own tails already provide the gap). A fixed pause would change every file | Confirm "0 ms, rely on the recorded tails", or pick a pause and regenerate |
| O-4 | **`en.phrase.no-room` catalogue cell** (from the generation report) | Still a declared override awaiting a decision | Decide before the wording is frozen |
| O-5 | **Reviewer assignment** | A blank template is not a review | Name the reviewer(s) and the date; Bangla must be judged by a Bangla speaker |
| O-6 | **A post-review action** | If samples fail, the tooling can regenerate with a different provider or pause, but regeneration invalidates hashes and the review | Decide the policy now: re-review after any clip change |


---

## 12. Governance and skill compliance

| Requirement | How it was met |
|---|---|
| §2 automatic routing — documentation read first | `docs/governance/AMSDP_Docs_Index_V1.0.md` consulted; the QUE-006 generation, format-standardisation and catalogue documents read for the clip facts; `frontend/lib/announcements/content.js` and `frontend/public/audio/manifest.json` read as the source of truth for wording and asset facts |
| §4 domain rows applied | *Frontend UI* (page, a11y: skip link, table caption, `aria-live` status, labelled controls) + *Queue/workflow* (announcement composition rules) + *Infrastructure* (loopback-only static server, no product service started or altered) + *Documentation* (§11 placement, §12 index registration) |
| §3 non-negotiables | No secret read, logged or exposed; no auth/RBAC path touched; no tenant or branch logic involved; no audit event created or altered; no schema change; nothing claimed that was not run. The page states plainly that it is not an approval mechanism |
| §5 skills registry | **No skill package is installed** in this workspace (verified: no `.clinerules/skills/`, `.claude/skills/` or repo `skills/`). Governance documents were used instead; **no skill usage is claimed** |
| §6 compliance reporting | This section |
| §7 evidence standard | Every claim above carries a file, a command or an observed output; audio quality is explicitly left at TESTED — never VERIFIED or ACCEPTED |
| §9 execution boundaries | No destructive git command; no commit, push or stage; no server or browser process left running (no listener on 8617–8623 and no `node` process remain, checked after the final run); the headless Chrome profile is deleted by the harness on exit (`fs.rmSync(PROFILE_DIR)` in `check-page.mjs`, and `preview/generated/.chrome-profile` is absent) |
| §11 documentation placement | This report is written to `docs/implementation/` and registered in `docs/governance/AMSDP_Docs_Index_V1.0.md` in the same task; no existing document was overwritten, moved or deleted |
| §12 documentation reading | Paths cited in this report were opened in this session; the index was updated rather than assumed |

**Deviation recorded, in full.** The three page files were written in this work
tree and were found mis-assembled when re-checked. `index.html` carried the
`</table></section>` closers of the samples table *after* `</html>` instead of in
place — the browser hoisted them, so the page rendered 20 rows and every check
passed, but the document was not well-formed and the first "tag balance" check
missed it because it counted tags rather than their order. `preview.js` had four
function tails appended at end of file and was repaired. Both were then verified
properly: `index.html` now has 5/5 `section`, 2/2 `table`, 2/2 `tbody`, 2/2
`thead`, 13/13 `div`, 1/1 `form`, 1/1 `main`, 1/1 `html` open/close pairs, no
content after `</html>`, and is UTF-8 without a BOM (7,628 bytes); `node --check`
is clean on all five `.mjs` files; and `check-page.mjs` was **re-run in Chrome
after the repair** — 12/12, exit 0 (§8 figures are from that post-repair run).
`preview.css`, `server.mjs`, `compose.mjs`, `compose-wav.mjs` and
`make-review-template.mjs` were checked the same way and needed nothing. No
product file was affected at any point.

---

## 13. Artefacts, reproduction and integrity

### Artefacts

| Path | Size | Role |
|---|---:|---|
| `scripts/que-006-audio/preview/compose-wav.mjs` | 31.8 KB | generator |
| `scripts/que-006-audio/preview/compose.mjs` | 9.0 KB | planning module (wording + clip order + pauses) |
| `scripts/que-006-audio/preview/preview.js` | 21.9 KB | page logic |
| `scripts/que-006-audio/preview/index.html` | 7.5 KB | page markup |
| `scripts/que-006-audio/preview/preview.css` | 7.3 KB | page styles |
| `scripts/que-006-audio/preview/server.mjs` | 7.1 KB | loopback static server |
| `scripts/que-006-audio/preview/make-review-template.mjs` | 9.2 KB | review record writer |
| `scripts/que-006-audio/preview/check-page.mjs` | 21.0 KB | browser verification harness |
| `scripts/que-006-audio/preview/generated/samples/` | 14.15 MB, 20 files | the 20 composed WAVs (git-ignored) |
| `scripts/que-006-audio/preview/generated/samples.json` | 100.1 KB | per-sample manifest |
| `scripts/que-006-audio/preview/generated/clip-analysis.json` | 16.9 KB | measured speech bounds and tails |
| `scripts/que-006-audio/preview/generated/data.json` | 43.5 KB | page payload |
| `scripts/que-006-audio/preview/generated/review-template.csv` | 3.2 KB | the review record |
| `scripts/que-006-audio/preview/generated/review-template.md` | 3.2 KB | readable mirror + column guide |
| `scripts/que-006-audio/preview/generated/source-baseline.json` | 7.0 KB | catalogue hashes before/after |
| `docs/implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` | this file | the report |

### Reproduction

```bash
# 1. build the samples and the page payload (idempotent; --force to rebuild)
node scripts/que-006-audio/preview/compose-wav.mjs

# 2. write the review record
node scripts/que-006-audio/preview/make-review-template.mjs

# 3. serve the review page on loopback only
node scripts/que-006-audio/preview/server.mjs --port 8617

# 4. in a second terminal: prove the page works (exit 0 = 12/12)
node scripts/que-006-audio/preview/check-page.mjs --port 8617 --page-port 9341
```

### Integrity statement

* No commit, no push, no staging, no branch or history change was made.
* No file outside `scripts/que-006-audio/preview/`, `scripts/que-006-audio/README.md`
  (a new *Human review preparation — `preview/`* section added; nothing removed or
  rewritten) and this report's two documentation locations — `docs/implementation/`
  (this file) and `docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 43 and one
  table row) — was created or modified by this work; the working tree still contains
  the pre-existing QUE-006 modifications to `frontend/` and the root `.gitignore`
  entry for `frontend/.audio-originals-backup/` that belong to the earlier
  generation/standardisation tasks, untouched by this one.
* `frontend/public/audio/` and `manifest.json` are byte-identical to their state
  before composition, as recorded in `source-baseline.json`
  (`catalogueUnchanged: true`, 72 files hashed).
* Every asset in `manifest.json` remains `humanReviewStatus: pending`.

**Bottom line:** the audio and the tooling to judge it are ready. The judgement
itself has not been made, and this report does not make it.

