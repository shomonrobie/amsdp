# QUE-006 — Voice Announcement: Future Refactoring Plan and Production Implementation Roadmap

**Task ID:** `AMSDP-QUE-006-VOICE-ROADMAP`
**Date:** 2026-11-21
**Status:** planning and inspection deliverable — **nothing implemented, nothing refactored, nothing approved by this document**
**Owner decision recorded here:** the current Voice Announcement output is accepted as an **approved DRAFT** (§2)
**Scope of this task:** documentation and code inspection only. No production code, no audio asset, no manifest, no schema, no permission and no queue logic was changed. `git status` evidence is in §13.

---

## 1. Executive summary

QUE-006 — *Intelligent Queue Voice Announcements (Bangla/English)* — is a core MVP capability
(`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`, line 544) whose
acceptance checklist has ten items and **zero checkboxes ticked**. The tree today contains two
disconnected halves of the capability, plus a third piece that is neither half:

| Half | What exists | What it is not |
|---|---|---|
| **A. Speaking path (live)** | A browser `speechSynthesis` announcement mechanism — wording (`content.js`), decisions (`controller.js`), browser seam (`speech-synthesis.js`), operator panel (`QueueAnnouncements.js`), wired into `frontend/pages/queue.js`. 4 test files, **53 tests, 52 pass, 1 skipped, 0 fail** (run in this task, §5.9). | Never heard on a real device. Reports `spoken` when the browser fires `start`, **not** when playback completes. Triggered only by a human clicking a per-row button, on an entry that is *already* `called`. |
| **B. Recorded audio (dormant)** | 28 catalogue recordings as WAV masters + MP3 playback files, delivered and format-standardised; `frontend/public/audio/manifest.json` (schema `AMSDP-QUE-006-audio-assets/2.0`, 28/28 technical pass, 0 human-approved); three validators that pass; an isolated preview harness that composes 20 announceable samples byte-for-byte and plays them in Chrome (**12/12 checks, exit 0**). | **No runtime consumer.** No component reads `manifest.json`; `playable.integratedWithApplication` is `false`; there is no prerecorded playback engine. Producing assets is not playing them. |
| **C. Production plumbing** | Nothing. | No `call` action in the UI, no server announcement event, no facility announcement configuration, no announcement audit event, no room on the queue payload, and no remote catalogue-installation agent anywhere in the tree or in `docs/`. |

The Product Owner has now accepted the current English and Bangla output as an **approved DRAFT**
(§2). That decision does three things: it freezes the wording and the recordings, it removes any
obligation to re-record or re-engineer the voice now, and it explicitly does **not** constitute
audio-quality, pronunciation or production acceptance. The refactoring work is therefore deferred
to a separately authorised exercise (§6), and the acceptance criteria in the feature catalogue stay
unticked.

**What remains to finish QUE-006 is not voice work — it is integration work.** Six workstreams,
classified with evidence in §5 and sequenced in §9:

| # | Workstream | Status (evidence-based) |
|---|---|---|
| W1 | Production prerecorded playback integration (O-6) | **NOT IMPLEMENTED** |
| W2 | Facility-level configuration + permission enforcement | **NOT IMPLEMENTED** (client-only, in-memory, interface-locale language) |
| W3 | Non-blocking queue integration | **PARTIALLY IMPLEMENTED** — the contract holds in code, but it is not wired to a queue event and never exercised against a real failure |
| W4 | Remote catalogue installation (local agent) | **NOT IMPLEMENTED** — approved architecture, zero artefacts |
| W5 | Asset distribution and cleanup (O-7) | **REQUIRES PRODUCT OWNER DECISION** |
| W6 | Operational verification (browser/device/offline) | **NOT IMPLEMENTED** — no browser or device playback evidence exists for the product |

Three prerequisites sit *inside* W1/W3 and are the reason the naive order does not hold: the queue
`call` action has **no user interface** (gap analysis QOP-001), a queue entry carries **no room**
(`backend/common/models.py:854` — `QueueEntry` has no room column), and the existing adapter reports
**start**, not completion. §9 explains the corrected sequence and why.

**Recommended single next task:** the manifest-driven prerecorded playback engine as an isolated,
unit-testable frontend module with a fake audio element — no queue page change, no configuration, no
schema change (§14). Everything else in the roadmap depends on it existing.

---

## 2. Product Owner decision — the current output is an approved DRAFT

### 2.1 The decision, as recorded

> **The current Voice Announcement output is accepted as DRAFT.**

### 2.2 What the decision means (binding interpretation for all downstream work)

1. The **current English and Bangla announcement output** — the 28 catalogue recordings as delivered
   and format-standardised, and the current composition rules that assemble them — is the **working
   draft**. It is accepted, not rejected.
2. The **existing recordings and the current composition are retained**. No re-recording, no
   re-generation, no trimming, no normalisation, no replacement, no deletion.
3. **No immediate voice redesign, re-recording or refactoring is required** or authorised by this
   decision, and none is performed by this task.
4. Future voice improvements — pronunciation, accent, clarity, pacing — are handled through a
   **separately planned refactoring exercise** (§6), which requires its own authorisation.
5. The draft acceptance is **not** final audio-quality acceptance, **not** pronunciation acceptance,
   and **not** production acceptance. `humanReviewStatus` stays `pending` on all 28 assets; the ten
   acceptance criteria in the feature catalogue stay unticked.
6. The **approved announcement wording does not change**: Bangla and English templates in
   `frontend/lib/announcements/content.js:34-43` remain authoritative, with no doctor name, no
   honourific and no patient identity.
7. Nothing in this report should be read as approving, verifying or accepting a clip, a voice, a
   pronunciation or the playback path.

### 2.3 What remains true alongside the draft acceptance

The draft being accepted does **not** make the capability delivered. The following statements from
the existing QUE-006 document set still hold verbatim after this decision:

- `manifest.json` says of itself: `playable.integratedWithApplication: false`, and
  *"These files and this manifest are prepared for a prerecorded-audio engine that does not exist
  yet."*
- `QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` §12: *"QUE-006 prerecorded-audio playback is NOT
  implemented, NOT integrated, and NOT accepted."*
- `AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md` §11: *"Bangla audio
  output is NOT VERIFIED. English audio output is NOT VERIFIED."*
- The feature catalogue records QUE-006 as `NOT STARTED` / `NOT TESTED` (lines 577–581 and 1266) with
  a note that the status cells are now stale and need an owner edit — they remain owner-controlled
  and unedited here.

The combination is coherent and must be preserved in every later report: **the sound is accepted as
a draft; the product capability is not built.**

### 2.4 Document set — how this report relates to the existing QUE-006 documents

This is the **planning layer**. It aggregates and cites the evidence documents; it does not restate
them, and it does not supersede any of them.

| Document | Role | Relationship |
|---|---|---|
| `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` (QUE-006, lines 544–581) | Owner-controlled requirement and acceptance checklist | **Authoritative.** Ten criteria; none ticked; status cells stale and owner-only |
| `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` (§3.4, §3.5, §4, ANN-001…ANN-010) | Finding register | Source of finding IDs (ANN-*, QOP-*) used here |
| `docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md` | Record of the browser speech mechanism (OD-1) | Evidence for §3 and §5; its O-1…O-10 remain open except where noted |
| `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` | The 28-asset catalogue: text, filenames, formats, ranges | Evidence for §4 and §6 |
| `docs/implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md` | Generation tooling, providers, blocked runs, disclosed incidents | Evidence for §6.5 |
| `docs/implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` | Doctor-name removal + catalogue creation | Evidence for §3.2 (no doctor identity) |
| `docs/implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` | Format standardisation, manifest v2.0, validators, decisions D-1…D-5, open items O-1…O-7 | Evidence for §4 and §12 |
| `docs/implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` | The 20 composed samples, reviewer page, headless harness | Evidence for §4.4; **the only place real audio was played** |
| **This document** | Future-refactoring plan + remaining production roadmap + status classification | Planning; creates no new technical evidence |

---

## 3. Current implementation architecture (as inspected, not as remembered)

### 3.1 The speaking path, end to end

```
 OPERATOR (queue page)                     BROWSER                                DEVICE
 ─────────────────────                     ───────                                ──────
 queue row, status === 'called'
   [ Announce ] button ──┐
                         │  announce(entry, {source:'operator', userGesture:true})
                         ▼
        frontend/pages/queue.js  announceEntry()   (lines 57-69)
        payload: { queueEntryId, action:'announce', token, room }
                         │      NOTE: `room` is always undefined — QueueEntry has no room
                         │      column and no queue endpoint returns one (models.py:854-882)
                         ▼
        controller.announce(payload, opts)          lib/announcements/controller.js:177-217
                         │
        ┌────────────────┼──────────────────────────────────────────────┐
        │ 1 enabled?  no → status 'disabled' (nothing attempted)        │
        │ 2 adapter.isSupported()?  no → 'unsupported'                  │
        │ 3 buildAnnouncement(payload, lang) → 'skipped' + reason       │  content.js:112-142
        │ 4 duplicate? same event key inside 5 000 ms → 'duplicate'     │
        │ 5 activation BLOCKED and no gesture → 'needs_activation'      │
        └────────────────┬──────────────────────────────────────────────┘
                         ▼
           adapter.speak(text, {language})      lib/announcements/speech-synthesis.js
                         │  pickVoice(list,'bn'|'en') — requested language or nothing
                         │  one utterance at a time; second call → 'busy'
                         ▼
        window.speechSynthesis.speak(utterance)
                         │
      onstart  → resolve 'spoken'      (START, not completion — see §3.4)
      onerror  → 'error' | 'cancelled' | 'blocked' by error code
      no start within startTimeoutMs → 'blocked', reason 'no_start_event'
```

The panel (`frontend/components/queue/QueueAnnouncements.js`) renders only the controller's state
and forwards one click; it renders nothing until mounted so server-side rendering cannot mismatch
the browser's voice list.

### 3.2 Module responsibilities and the exact contracts

| File | Lines | Owns | Deliberately does **not** own |
|---|---|---|---|
| `frontend/lib/announcements/content.js` | 165 | The only place wording is assembled. `TEMPLATES` (bn/en × with-room/no-room), `spokenTokenNumber()` (trailing digit group, leading zeros stripped, UUID/32-hex refused, >9 digits refused), `toBanglaDigits()`, `announcementEventKey()`, `PATIENT_FIELDS` (declared never-read list) | Voice, timing, transport, persistence |
| `frontend/lib/announcements/controller.js` | 286 | Facility switch (in-memory), duplicate suppression (5 s window, event key), overlap suppression (`busy`), activation state (`unknown`/`granted`/`blocked`), last outcome, UI subscription | Server events, facility configuration storage, announcement audit, cross-client ordering |
| `frontend/lib/announcements/speech-synthesis.js` | 379 | The single seam over `window.speechSynthesis`: capability (`unsupported`/`pending_voices`/`ready`/`no_voice`), voice selection with **no language substitution**, one utterance at a time, refusal detection by missing `start`, `never throws / never rejects` | Prerecorded audio, caching, offline behaviour |
| `frontend/components/queue/QueueAnnouncements.js` | 149 | Rendering: status badge, "Enable audio" button, last-outcome line with the spoken text | Any decision |
| `frontend/pages/queue.js` | 262+ | `canAnnounce = can('queue.manage') \|\| can('queue.consult')`; one controller per page; the per-row button | Queue transitions — announcing is not a queue action (pinned by a test) |

Privacy contract, verified by tests: the spoken payload is built from **two** fields only — the token
serial and an optional room. `doctorName` is no longer passed at all
(`QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md`), the templates contain no
doctor slot, and patient fields are never read, so they cannot leak by accident.

### 3.3 Wiring into the queue page — what is actually reachable

| Product requirement | Reachable today? | Evidence |
|---|---|---|
| Announce when a patient is **called** (`waiting → called`) | **No.** There is no `call` control in any page: `doAction()` is invoked only with `start_consultation`, `complete_consultation`, `cancel`, plus the recovery/missed-turn routes. | `frontend/pages/queue.js:197-198, 284`; gap analysis QOP-001 (*"zero occurrences of `'call'` in `frontend/`"*) |
| Announce from the operator's `Announce` button | **Yes** — but only on rows already in `called` | `frontend/pages/queue.js:200-203` |
| Announce automatically on a server event | **No.** No announcement event, no transport, no subscription | gap analysis §3.4 (event: No; transport: No); OD-1 report O-3 |
| Announce with a room number | **No.** `room: entry.room` is `undefined` everywhere; the with-room branch is unreachable in production and has only ever run in unit tests and in the isolated preview harness | `backend/common/models.py:854-882`; `content.js:121-127` |
| Announce in the facility's configured language | **No.** The controller uses the operator's interface locale — `language: getLocale() === 'en' ? 'en' : 'bn'` | `frontend/components/queue/QueueAnnouncements.js:43-48` (*"The facility language setting (OD-2) does not exist yet"*) |
| Announce from a kiosk/TV (public display) | **No.** The panel is an operator surface on the authenticated queue page | `frontend/pages/queue-display/` carries no announcement code |

### 3.4 A correctness detail that matters for acceptance: *start* is not *completion*

`speech-synthesis.js` resolves `OUTCOME.SPOKEN` from the utterance's `start` event and treats a
missing `start` as `blocked`. That is the right decision for **detecting refusals** and is documented
as such. It is **not** evidence that a sentence finished. The QUE-006 requirement is "playback
success only after completed playback"; the prerecorded engine (W1) must therefore resolve
completion from `ended`, and this adapter's `spoken` must never be presented as completion evidence.
That is a design constraint on the roadmap, not a defect in the shipped code.

### 3.5 Server side: the seams that exist, and the ones that do not

| Seam | State | File |
|---|---|---|
| Queue `call` action (`waiting → called`), gated on `queue.manage` | **Implemented, tested over HTTP**, but unreachable from the UI | `backend/queuing/main.py:396-404` |
| Best-effort non-blocking side-effect hook, `_notify(event, *args)` — never raises, opens its own session | **Implemented**, used by every queue mutation; the established place for a non-blocking announcement side effect | `backend/queuing/main.py:47-57` |
| Durable outbox with dedup/retry (`common/notifications/`) | **Implemented for `whatsapp`/`sms` only**; the channel list is closed, so it cannot carry an announcement today | gap analysis §3.5 |
| Org-scoped configuration JSON + audited config router (`organizations.config`, `appointment_config.py`, `notification_config.py`) | **Implemented** — the exact template an announcement config route should follow | `backend/common/config.py`, `backend/organization/appointment_config.py:30-116`, `backend/organization/notification_config.py` |
| Facility identity columns (`organizations.locale` default `bn`, `timezone`) | **Implemented** — a facility language column already exists, but nothing reads it for announcements | `backend/common/models.py:38-39` |
| Room data on a queue entry or queue response | **Absent** — no column, no field, no endpoint | `backend/common/models.py:854-882` |
| Announcement audit events (`queue.announcement.played/.failed/.skipped`) | **Absent** | OD-1 report O-3 |
| Remote catalogue installation agent (poll, download, verify, atomic install, rollback, status) | **Absent everywhere** — no code, no route, no client, and no design document in `docs/` | searched: `local agent`, `remote installation`, `voice agent`, `updater`, `installation`, `poll_` → zero product hits |

---

## 4. Current audio catalogue and asset status

### 4.1 What is delivered

| Fact | Value | Source |
|---|---|---|
| Catalogue document | `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` (V1.0, 17,144 bytes), 28 assets | file |
| Manifest | `frontend/public/audio/manifest.json`, 53,888 bytes | file |
| Manifest schema | `AMSDP-QUE-006-audio-assets/2.0`, `version: 2.0` | manifest |
| Generated at | `2026-11-21T04:36:51.499Z` | manifest |
| Assets | **28** — 8 phrase assets (4 en, 4 bn incl. `bn.phrase.room-locative`) + 20 digit assets (0–9 × en, bn) | manifest |
| Delivery formats | master `wav/pcm_s16le/44100Hz/mono/16-bit`; playback `mp3/44100Hz/mono/128kbps/cbr` | manifest `formats` |
| Summary | `total 28, masterPresent 28, playbackPresent 28, technicalPass 28, technicalMissing 0, technicalFail 0, contentIssues 0, humanApproved 0, humanPending 28, complete true` | manifest `summary` |
| Playback readiness block | `readyForPlaybackEngine: true`, `integratedWithApplication: **false**`, `humanReviewOutstanding: true` | manifest `playable` |
| Composition rules | digits spoken individually, no separators, Bangla locative appended after room digits | catalogue §3.3 |
| Ranges | token serial ≤ 9 digits (code); **recommended** 1–999 for tokens and rooms — **not approved** | catalogue §3.2 |

The `playable.readyForPlaybackEngine` flag is `true` now, whereas the format-standardisation report
recorded `false`. The change is explained: it flipped when the missing Bangla locative clip was
supplied and the catalogue reached 28/28 (index Revision 42; standardisation report §17). It says the
**assets** are ready for an engine — not that an engine exists, which is why
`integratedWithApplication` remains `false`.

### 4.2 What is on disk versus what the manifest references

Mechanical count of `frontend/public/audio/` in this task:

| Measure | Value |
|---|---|
| Files on disk | **72** |
| Files referenced by the manifest (`masterFile` + `playbackFile`, 28 × 2) | **56** |
| Manifest itself | 1 |
| **Unreferenced files** | **15** |

The 15 unreferenced files are the retained originals and one mislabelled placeholder — exactly the
set decision D-3 kept and open item O-7 asks the owner about:

```
bn/number/digit-0.m4a … bn/number/digit-9.m4a      (10 files — original Bangla sources)
bn/phrase/token-number.m4a
bn/phrase/room-prefix.m4a
bn/phrase/no-room.m4a
bn/phrase/room-locative.mpeg                        (the supplied Bangla recording, byte-preserved)
bn/phrase/room-suffix.wav                           (an English-silence copy under a Bangla name)
```

`en/phrase/room-suffix.wav` **is** referenced (it is the intentional-pause asset, `contentStatus:
intentional-pause`, 0.300 s) — the Bangla-named namesake is the mislabelled copy and is not.

### 4.3 Provenance, immutability and the serving tree

- Every one of the 29 pre-standardisation originals is preserved byte-for-byte under
  `frontend/.audio-originals-backup/` with a record (`ORIGINALS.json`, 29 entries, each re-verified)
  — standardisation report §2 and §17.3.
- That backup directory is **git-ignored** (`/frontend/.audio-originals-backup/` in `.gitignore`) so
  ~1 MB of binary recordings stay on disk as evidence without entering the repository (decision D-5).
- English playback files are the **original MP3s, byte-identical**, not re-encodes of the masters
  (decision D-2), so no second lossy generation exists.
- Per-asset SHA-256 for master and playback is in the manifest (`masterChecksum`, `playbackChecksum`)
  and is what any future installer must verify.
- The assets sit in the **publicly served** frontend tree (`frontend/public/audio/`), so today they
  are reachable by URL from a running frontend even though nothing uses them. That is the fact O-7 is
  about, and W5 must not change it without the owner's decision.

### 4.4 Validation and the only real playback that has happened

| Activity | Result | Where |
|---|---|---|
| `validate-audio-assets.mjs` | exit 0 — 28/28 pass, 56 checksums verified, 29 preserved originals re-verified, CBR frame spread 0.3 kbps | standardisation report §6, §17.5 |
| `validate.mjs` | exit 0 — 28/28 | same |
| `rebuild-audio-manifest.mjs --check` | exit 0 — "manifest is current" | same |
| Isolated preview: 20 composed samples, reviewer page, headless-Chrome harness | **12/12 checks, exit 0**; byte-level PCM concatenation with per-sample SHA-256; `source-baseline.json` proves 72 catalogue/manifest files unchanged | `QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` |
| Human listening review of the 28 clips | **Not performed** — no reviewer named, no verdict recorded; `review-template.csv` is blank | same report; standardisation report §10 |
| Playback by the product itself | **Never** — no consumer of the manifest exists | manifest `playable`; `grep audio/manifest` over `frontend/**/*.js` → no hits |

**Read this honestly:** technical validation proves the files are well-formed, correctly named,
correctly encoded and unmodified. It proves nothing about how they sound, and the composed-sample
harness proves the *composition arithmetic and the browser can play local WAVs* — not that the
product announces queue calls.

---

## 5. Current implementation status by workstream

### 5.1 Status vocabulary and how it was applied

Exactly one status per feature, from the seven permitted values, applied strictly:

- **IMPLEMENTED AND VERIFIED** — code exists, is reachable, and a *second independent artefact*
  confirms it (a validator run, a harness run, a re-run with different tooling). Not used for anything
  a human has never heard.
- **IMPLEMENTED BUT NOT VERIFIED** — code exists and its tests pass, but nothing independent confirms
  it in the real environment (a browser, a device, a live queue call).
- **PARTIALLY IMPLEMENTED** — some of the requirement exists; the remainder is named.
- **NOT IMPLEMENTED** — no code, or code that cannot satisfy the requirement.
- **BLOCKED** — cannot be built until something else exists (a decision, a schema field, another
  workstream).
- **REQUIRES PRODUCT OWNER DECISION** — engineering is ready; the product question is open.
- **DEFERRED BY PRODUCT OWNER** — explicitly postponed by an owner decision.

Code existing is never treated as evidence that a feature works.

### 5.2 Master status table (rows 1–18)

| # | Feature / requirement | Status | Evidence anchor |
|---|---|---|---|
| 1 | Approved announcement wording (bn/en, with-room/no-room) | IMPLEMENTED BUT NOT VERIFIED | `content.js:34-43`; tests pin exact strings; never spoken on a device |
| 2 | Token-number composition (trailing serial, leading zeros, UUID refusal) | IMPLEMENTED BUT NOT VERIFIED | `content.js:86-97`; content tests; no production token announced |
| 3 | Room-number composition in production | **BLOCKED** | `QueueEntry` has no room (`models.py:854`); needs a room source + payload change |
| 4 | Bangla digit conversion (`৪` not "four") | IMPLEMENTED BUT NOT VERIFIED | `content.js:59-61`; tested; not heard |
| 5 | Browser speech-synthesis adapter (OD-1) | IMPLEMENTED BUT NOT VERIFIED | `speech-synthesis.js`; speech tests; OD-1 report §11 |
| 6 | Language honesty — never substitute an English voice for Bangla | IMPLEMENTED BUT NOT VERIFIED | `pickVoice()` → `null` → `no_voice`; speech tests; no device matrix |
| 7 | Operator announcement surface on the queue page | IMPLEMENTED BUT NOT VERIFIED | `QueueAnnouncements.js`, `queue.js:200-203`; boundary tests; JSX compile test **skipped** |
| 8 | Announcement triggered by the queue `call` event | **NOT IMPLEMENTED** | no UI call action (QOP-001); no event; no subscription |
| 9 | Queue `call` action on the server | IMPLEMENTED BUT NOT VERIFIED | `backend/queuing/main.py:396-404`; backend tests documented, not re-run here |
| 10 | Duplicate-event suppression | PARTIALLY IMPLEMENTED | single-client 5 s window (`controller.js:194-202`); no server event id, no cross-client guarantee |
| 11 | Overlap suppression (one announcement at a time) | IMPLEMENTED BUT NOT VERIFIED | `busy` outcome; tested; not heard |
| 12 | Autoplay/activation handling and visible "audio off" | IMPLEMENTED BUT NOT VERIFIED | `ACTIVATION`, `startTimeoutMs` refusal path; not exercised on a kiosk/TV |
| 13 | Audio failure never blocks a queue operation | IMPLEMENTED BUT NOT VERIFIED | `speak()` never throws; `announceEntry` is fire-and-forget; no forced-failure test on device |
| 14 | Playback success reported only after **completion** | **NOT IMPLEMENTED** | adapter resolves on `start` (§3.4); requires the prerecorded engine |
| 15 | Prerecorded playback engine (O-6) | **NOT IMPLEMENTED** | no consumer of `manifest.json`; `integratedWithApplication: false` |
| 16 | Manifest-driven loading, sequencing, missing/corrupt handling | **NOT IMPLEMENTED** | no code |
| 17 | Offline playback after installation | **NOT IMPLEMENTED** | no engine, no service worker, no local installation |
| 18 | Facility announcement enable/disable (persisted, facility-scoped) | **NOT IMPLEMENTED** | `enabled` is an in-memory controller flag; no config key anywhere |

### 5.2 Master status table (rows 19–35, continued)

| # | Feature / requirement | Status | Evidence anchor |
|---|---|---|---|
| 19 | Facility announcement language (persisted, facility-scoped) | PARTIALLY IMPLEMENTED | interface locale used (`QueueAnnouncements.js:47`); `organizations.locale` exists but is not read for announcements |
| 20 | Announcement configuration API + audit | **NOT IMPLEMENTED** | no route; `appointment_config.py` is the ready template |
| 21 | Permission enforcement for announcement configuration | **NOT IMPLEMENTED** | nothing to enforce; and `branch_admin` **cannot** reach an org-config route (§5.4) |
| 22 | Announcement played/failed/skipped audit events | **NOT IMPLEMENTED** | OD-1 O-3 |
| 23 | Audio asset catalogue, manifest, checksums, validators | **IMPLEMENTED AND VERIFIED** (technical only) | §4.4: three validators exit 0, manifest read-back, preview harness 12/12 — **not** pronunciation approval |
| 24 | Human listening review of the 28 clips | **NOT IMPLEMENTED** | no reviewer, blank template, `humanPending 28` |
| 25 | Isolated composition preview tooling (20 samples + harness) | **IMPLEMENTED AND VERIFIED** | preparation report; 12/12 in Chrome |
| 26 | Remote catalogue installation agent (poll/download/verify/install/rollback/status) | **NOT IMPLEMENTED** | zero artefacts in code and docs |
| 27 | Catalogue version discovery + compatibility check on the client | **NOT IMPLEMENTED** | manifest has `version`/`schema`; nothing reads them |
| 28 | Asset distribution / cleanup of the 15 unreferenced files (O-7) | **REQUIRES PRODUCT OWNER DECISION** | §4.2 |
| 29 | Bangla ~1 s trailing silence | **REQUIRES PRODUCT OWNER DECISION** | measured 0.874–1.388 s per clip; reported, not trimmed |
| 30 | Inter-clip junction pause policy | **REQUIRES PRODUCT OWNER DECISION** | measured 0 ms at junctions |
| 31 | Token/room supported range (1–999) | **REQUIRES PRODUCT OWNER DECISION** | catalogue §3.2 recommendation, unapproved |
| 32 | `en.phrase.no-room` leading-comma wording | **REQUIRES PRODUCT OWNER DECISION** | recorded with the comma; catalogue cell omits it |
| 33 | Voice/provider selection for any future re-recording | **REQUIRES PRODUCT OWNER DECISION** | Gemini + ElevenLabs both implemented; neither chosen as "the" voice |
| 34 | Voice redesign / re-recording / pronunciation refinement | **DEFERRED BY PRODUCT OWNER** | §2: draft accepted; refactoring separately authorised |
| 35 | Doctor-name / honourific in the spoken payload | IMPLEMENTED AND VERIFIED (removed) | no doctor slot in the templates; removal report; tests assert absence |

Rows 1–35 are the honest picture: **three** are independently verified (technical asset integrity; the
isolated preview; the removal of doctor identity), **ten** are implemented but unheard, **two** are
partly implemented, **twelve** are not implemented at all, **one** is blocked by missing data, and
**six** await a Product Owner decision.

### 5.3 W1 — Production prerecorded playback integration (O-6)

**Status: NOT IMPLEMENTED.**

| Aspect | Finding |
|---|---|
| Files that would be the seam | none exists; `frontend/lib/announcements/` contains only the speech-synthesis path |
| Existing functions | none — no audio module, no `HTMLAudioElement`, no `new Audio(` anywhere in `frontend/` (grep: 0 hits) |
| Tests | none |
| Missing | asset loading by manifest id; per-language phrase/digit sequencing; number composition from clips; completion reporting from `ended`; error handling; missing/corrupt asset handling; overlap prevention across a whole announcement; offline operation |
| Evidence | `manifest.json` `playable.integratedWithApplication: false`; no consumer of `audio/manifest.json`; standardisation report §12 |

Two hard dependencies make this bigger than "write an audio element":

1. **The composition target is implemented in text, not in clips.** `buildAnnouncement()` returns a
   *string*. A prerecorded engine needs the *asset sequence* (`token-number`, digits…, `room-prefix`,
   digits…, `room-locative`) for the same event, and must agree with the approved wording. If the
   sequence rules are re-implemented, they can drift from `content.js`; the engine must derive them
   from a single source and tests must prove the two agree.
2. **A room does not exist in the data** (§3.5), so only the no-room path can be exercised in
   production until a room source is approved and carried on the payload.

### 5.4 W2 — Facility-level configuration

**Status: NOT IMPLEMENTED** (language: PARTIALLY IMPLEMENTED, by accident of the interface locale).

| Requirement | State | Evidence |
|---|---|---|
| Persisted enable/disable per facility | absent | no announcement key in `backend/common/config.py` (which has `queue_config`, `appointment_config`, `registration_policy` only); no column in `models.py` |
| Persisted language per facility | absent (`organizations.locale` exists, unused for announcements) | `models.py:39`; `QueueAnnouncements.js:43-48` |
| Configuration API | absent | `organization/main.py` (`org.manage`), `facility.py` (facility tree), `appointment_config.py`, `notification_config.py` — no announcement route |
| Configuration UI | absent | `frontend/pages/` has `orgs.js`, `branches.js`, `facilities.js`, `notifications.js` — no announcement settings surface |
| Permission model | **the approved boundary is not reachable as designed** | see below |

The template for the missing feature already exists, audited and tenant-gated:
`backend/organization/appointment_config.py` (GET `org.read`, PUT `org.manage`, `_scoped_org()` →
non-disclosing 404, `record_audit` before/after, plus a `common/config.py` accessor whose defaults
never raise on malformed JSON). `frontend/pages/notifications.js` is the matching UI pattern.

**The permission problem, stated precisely.** The approved boundary is *`super_admin`, `org_admin`
and `branch_admin` may configure*; *receptionist* and *doctor* may trigger but must not configure.
In `backend/common/permissions.py`:

| Role | `org.manage` | `facility.manage` | `queue.manage` | `queue.consult` |
|---|---|---|---|---|
| `super_admin` | yes (wildcard) | yes | yes | yes |
| `org_admin` | yes | yes | yes (`queue.*`) | yes |
| `branch_admin` | **no** | yes | yes (`queue.*`) | yes |
| `receptionist` | no | no | yes | no |
| `doctor` | no | no | no | yes |

An org-config route gated on `org.manage` (the `appointment_config` / `notification_config`
precedent) would therefore **exclude `branch_admin`**, violating the approved boundary; gating on
`facility.manage` includes `branch_admin` but is *branch*-flavoured while `organizations.config` is
*organization*-scoped. Either the setting is stored per branch (new column/table + forward-only
migration) and gated on `facility.manage`, or a narrow new capability is added. **This is a Product
Owner decision, not an engineering preference** (§12, POD-5) — and it must be settled before the
route is written. The OD-1 report already flagged the same tension (its O-2: *"the catalogue names
`branch_admin`; the notification precedent denies it"*).

### 5.5 W3 — Non-blocking queue integration

**Status: PARTIALLY IMPLEMENTED.** The *contract* is right and tested; the *integration* does not exist.

| Requirement | State | Evidence |
|---|---|---|
| Queue call does not wait for audio | satisfied by construction — `announceEntry()` is never awaited and `doAction()` never touches audio | `queue.js:57-69, 88-93`; boundary test *"announcing is not a queue action"* |
| Audio failure cannot fail a queue operation | satisfied by construction — `speak()` never throws or rejects; the controller catches adapter throws | `speech-synthesis.js` header contract; `controller.js:209-216` |
| No duplicate announcements for one event | single-client only | 5 s window + event key; no server event id |
| Playback success/failure reported accurately | **not satisfied** | success is reported at `start`, not completion (§3.4); nothing is recorded server-side |
| Audio state never confused with queue state | satisfied in the current design (there is no server audio state at all) | no announcement rows in any table |
| Announcement attached to an actual call event | **absent** | no call UI, no event, no subscription |
| Recovery after interrupted playback | **absent** | nothing to recover |

The operational requirement — *audio must never block the queue* — is therefore honoured
*architecturally* but **not yet proven**, because nothing has ever been wired to a queue transition.
`_notify(event, *args)` (`backend/queuing/main.py:47-57`) is the established never-raising place to hang
a server-side announcement side effect, and reusing it is the low-risk path.

### 5.6 W4 — Remote catalogue installation (approved local-agent architecture)

**Status: NOT IMPLEMENTED — and not merely unfinished: nothing of it exists.**

Searches run in this task, across `backend/`, `frontend/`, `scripts/` and `docs/`:

| Pattern | Product hits |
|---|---|
| `local agent`, `remote installation`, `voice agent` | **0** (in `docs/`, 0) |
| `updater`, `installation`, `poll_` | **0** |
| audio catalogue download / version discovery endpoint | **0** |
| any client that reads `audio/manifest.json` | **0** |

The architecture the Product Owner approved is: *a local agent on the facility PC polls the central
server over a secure outbound connection, downloads and verifies approved catalogues, installs them
atomically, keeps the previous catalogue for rollback, and reports installation/update status.* Not
one of those elements exists — not the agent, not the server-side catalogue registry, not the version
endpoint, not the status reporting, not the rollback store. There is not even a design document for
it in `docs/`; this report records the requirement, and §8 W4 records what would have to be built.

**Constraint recorded:** this approved architecture must not be replaced by an unrelated update
mechanism (a CDN pull, a git-based deploy, a shared network folder) without explicit Product Owner
approval. In particular, the existing static serving of `frontend/public/audio/` is **not** the
installation mechanism and must not be treated as one.

### 5.7 W5 — Audio asset distribution and cleanup (O-7)

**Status: REQUIRES PRODUCT OWNER DECISION.**

| Question the owner must answer | Engineering position |
|---|---|
| May the 13 Bangla `.m4a` sources, `bn/phrase/room-locative.mpeg` and the mislabelled `bn/phrase/room-suffix.wav` be removed from `frontend/public/audio/`? | They are **unreferenced by the manifest** (§4.2) and ~424 KB of dead weight in a **publicly served** tree. The `.mpeg` is the only Bangla locative source and its byte-preserved copy lives in the git-ignored backup — removing it from the served tree does not destroy it, but the owner should confirm that reasoning |
| Should any of them be retained as provenance inside the served tree? | Retaining them keeps an unambiguous audit trail; it also means unauthenticated users can download raw voice sources |
| Should the mislabelled `bn/phrase/room-suffix.wav` be renamed? | **No** — renaming would make a missing recording indistinguishable from a present one (standardisation decision D-1). Delete-by-decision or leave, never rename |

**Nothing is deleted, moved or renamed in this task.** The cleanup, when authorised, must be a
forward-only, reversible operation with a checksum manifest, executed in its own task.

### 5.8 W6 — Operational verification

**Status: NOT IMPLEMENTED.** No browser, device or offline test of the *product* exists.

What has been proven and what has not:

| Claim | Proven? | By what |
|---|---|---|
| The composition arithmetic is correct (clip order, digit count, Bangla digits, locative) | **Yes**, offline | 20 composed samples with per-sample SHA-256; preparation report |
| A browser can play those composed WAVs and report completion | **Yes**, in the preview harness only | headless Chrome run, 12/12, exit 0 |
| The product announces a queue call in Bangla | **No** | no call event, no playback engine |
| The product announces a queue call in English | **No** | same |
| Bangla voice availability on the target kiosk/TV | **No** — no device/voice matrix | OD-1 report §11 |
| Autoplay refusal handling on the target device | **No** — only against a fake engine | OD-1 report §11 |
| Offline playback after installation | **No** — nothing installs, nothing caches | this report |
| Audio failure does not disturb a live queue | **No** — never forced in a running system | §5.5 |

The preview harness is the *pattern* to reuse for W6 (raw DevTools protocol over the built-in
WebSocket, no new dependency, exit code 2 when unverifiable), but it composes files on disk; it does
not drive the application.

### 5.9 Test evidence gathered in this task

Run, with the project's own command shape (`frontend/package.json` `test` script):

```
cd frontend
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test \
  tests/queue-announcement-content.test.mjs \
  tests/queue-announcement-controller.test.mjs \
  tests/queue-announcement-speech.test.mjs \
  tests/queue-announcements-boundary.test.mjs
```

| Metric | Result |
|---|---|
| Tests | **53** |
| Passed | **52** |
| Failed | **0** |
| Skipped | **1** — *"the queue page and the announcement panel compile as JSX"* (`next/dist/build/swc unavailable in this install`) |
| Duration | 531.56 ms |

Interpretation, stated carefully: the wording, the decisions and the browser seam are covered by
passing tests. The one skipped test is the only evidence that would prove the **page** still compiles
with these changes, and it is skipped in this environment. That is another reason feature 7 in §5.2
is *not verified*, and it is why W6 must include one real page load in a browser before any acceptance
claim.

Backend queue tests (`backend/queuing/tests/test_queue.py`, `backend/tests/test_e2e.py`) were **not
re-run in this task**: they need the composed environment, and this task must not start services.
Their existence and scope are documented in the gap analysis §3.6; their results are not claimed here.

---

## 6. Future voice refactoring plan (only if the Product Owner later authorises it)

> **This section is a plan, not work.** The draft is accepted (§2); nothing here is started, and none
> of it may begin without a separate authorisation naming the scope.

A refactoring exercise has one advantage the current work does not: there is now a **complete,
validated, checksummed baseline** to compare against. Any change must be provably a change, and any
regression must be provably reversible.

### 6.1 Voice recording improvements

| Concern | What would change | How it stays safe |
|---|---|---|
| Pronunciation corrections | Re-record individual assets only (`en.digit.*`, `bn.phrase.*`), never a whole set for one word | Asset-level versioning: the manifest already carries per-asset SHA-256 and `humanReviewStatus`; a re-recorded clip gets a new checksum and a fresh `pending` review |
| English accent | The catalogue asks for *clear, natural British English* (§4.1); a change of accent is a **product** decision | Accent recorded as an explicit catalogue field before generation, so a reviewer knows what was intended |
| Bangladeshi Bangla pronunciation | Native/fluent speaker review is the only acceptance path (O-3 today) | Review verdicts recorded per asset; a clip with no verdict cannot be switched on |
| Clarity and consistency | One voice per language across all assets; no mixing within a phrase | Catalogue records the voice id per asset; validation refuses a catalogue where one language uses two voices |
| Recording quality | Master stays `wav/pcm_s16le/44100Hz/mono/16-bit`; nothing normalised in place | The three validators are the gate; a re-record that fails them never reaches the manifest |
| Volume consistency | Measured per asset today (`mean_volume`/`max_volume` in manifest notes); a spread threshold would turn "consistent" into a check | Add a loudness-spread check to `validate-audio-assets.mjs` (a code change → its own task) |
| Phrase and digit replacement | Any single asset replaceable without touching its neighbours | The `.audio-originals-backup` + `ORIGINALS.json` pattern is already proven (§4.3) |
| Provenance and version tracking | Each run is described in the generation report; a machine-readable `generation.json` per catalogue version would make it durable | Catalogue `version` + manifest `generatedAt` + per-asset checksums are the minimum; a per-asset `sourceProvider` closes the gap |

**Non-negotiable for any re-record:** the approved wording does not change. A re-record is a new
performance of the same words, never new words.

### 6.2 Audio timing and composition

| Concern | Current measured state | What a refactor would address |
|---|---|---|
| **Trailing silence** | Bangla clips carry **0.874–1.388 s** (mean 1.260 s; **14 of 14** over 0.5 s). English carries 0.014–0.331 s (mean 0.204 s) | Equalise the perceived inter-clip gap across languages. Either trim in a **separate approved pass** (destructive; needs the owner's O-2 decision) or compensate at playback time (non-destructive, but must be identical in every player) |
| **Inter-clip pause** | Measured **0 ms** at junctions in the composed samples | A designed junction pause (e.g. 60–120 ms) applied by the engine, not baked into files, so it is tunable without re-recording |
| Leading silence | Small, per clip, no declared policy | One declared policy instead of per-clip accident |
| Number composition | Digits concatenated directly, no separators (§3.3 of the catalogue) | Optional short gap between digits for intelligibility at distance — an engine parameter |
| Bangla locative | `-এ আসুন।` appended after the room digits (1.820 s asset) | Confirm the joint sounds natural under the new junction policy |
| Consistency across languages | English mean gap 0.204 s vs Bangla 1.260 s — **the two languages do not sound the same today** | This is the largest audible difference a refactor should remove |

Any trimming is a **separate, owner-approved, reversible pass** with before/after checksums and a
preserved original — never an in-place edit of the accepted draft.

### 6.3 Audio engine improvements

The engine is the part that does not exist yet (§5.3). When it is built — **before** any voice
refactor, because a refactor needs something to play through — it must provide:

| Requirement | Design consequence |
|---|---|
| Prerecorded audio as the **primary** mechanism | The engine is the default path; browser `speechSynthesis` becomes an explicitly configured alternative, never an automatic fallback |
| No silent Bangla substitution | If a Bangla asset is missing or unplayable the outcome is a reported failure (`no_asset`), never an English voice reading Bangla |
| Offline operation after installation | Assets resolve from the installed catalogue on disk; no network fetch per announcement |
| Asset loading and caching | Preload the small working set (phrases + 10 digits per language); verify checksums on install unconditionally, and on load where cheap |
| Playback sequencing | One ordered segment list per announcement; a second announcement is refused (`busy`) or queued by one declared policy — the same policy everywhere |
| Completion and error reporting | Success resolves on the **last segment's `ended`**; failure resolves with a reason (`missing_asset`, `decode_error`, `blocked`, `interrupted`). Never on `start` (§3.4) |
| Missing or corrupted asset | Detectable before the first sound: a manifest check at start-up plus a per-play error path. The announcement degrades to "not announced"; the queue never degrades |
| Prevention of overlap | A single owner of the audio element per page, exactly as `controller.js` already does for speech |
| Recovery from interruption | A cancelled or interrupted announcement leaves no stuck state: the engine is reusable on the next event and the operator sees the failure |

### 6.4 Catalogue and version management

| Concern | Position |
|---|---|
| Schema evolution | `manifest.schema` is `AMSDP-QUE-006-audio-assets/2.0`; a new field must not break a v2 reader. Additive-only within a major version; a breaking change bumps the major and needs an engine release that understands both |
| Manifest validation | Already strong (three validators). Add a schema assertion in the **engine's** start-up path so a bad catalogue fails closed before it speaks |
| Asset checksums | Per-asset `masterChecksum`/`playbackChecksum` exist; the installer verifies playback files, the engine may verify what it preloads |
| Version compatibility | The manifest carries `version` and `schema`; the engine must declare the range it supports and refuse anything else with a visible reason — never a silent partial play |
| Update and rollback | Keep the previous catalogue directory intact and switch by atomic swap; rollback = switch back. This is W4's contract and the same contract for a voice refactor |
| Backward compatibility | A catalogue that drops an asset id must not break the engine; missing ids are reported, never invented |
| Migrating older assets | English MP3s are originals, Bangla masters derived from `.mpeg`/`.m4a`; a migration must carry `playbackDerivation` forward so provenance is never lost (defect 5 in the standardisation report) |

### 6.5 Future voice-generation workflow (the existing approved approach)

The tooling already exists and is the sanctioned route: `scripts/que-006-audio/` — `generate.mjs`
(provider `gemini` by default, `elevenlabs` selectable), `standardise-audio.mjs`,
`validate-audio-assets.mjs`, `validate.mjs`, `rebuild-audio-manifest.mjs`, with `catalogue.mjs` as the
single source of asset ids, text and filenames.

Rules a future generation run must obey:

1. **Credential handling.** The key stays in an environment variable — `GEMINI_API_KEY` for Gemini;
   `ELEVEN_LABS_API_KEY` or `ELEVENLABS_API_KEY` for ElevenLabs (`scripts/que-006-audio/lib/env.mjs:39-40`).
   It is **never** written into source, a catalogue, a report, a log or a commit message. `lib/env.mjs`
   also rejects implausible key shapes, so a mis-pasted value fails loudly instead of producing a 401
   that reads like a model error.
2. **Outbound calls are explicit.** Generation contacts an external TTS provider; it happens only in a
   task that authorises it, never as a side effect of a build, a test or a validation run.
3. **Order of operations.** `generate.mjs` → `standardise-audio.mjs` (in-place conversion is safe
   because it writes a temp file and renames) → `validate-audio-assets.mjs` (strict) →
   `rebuild-audio-manifest.mjs` → `validate.mjs`. Originals are preserved before any conversion, and
   the backup record never absorbs the tool's own outputs (defect 3 in the standardisation report).
4. **Never overwrite the accepted draft.** A new generation writes a **new catalogue version** beside
   the draft; promotion to "the" catalogue is a separate, owner-authorised act.

No external TTS call was made in this task, and none may be made as part of it.

### 6.6 Refactoring risks and the phased strategy

| Risk | Why it is real here | Mitigation |
|---|---|---|
| Changing the accepted draft by accident | The draft is now the reference copy; an in-place trim or re-encode silently destroys the accepted sound | Work on a copy, never in place; before/after SHA-256 of all 28 assets; the accepted catalogue is read-only during a refactor |
| Incorrect number composition | Digits are the only number building blocks; a wrong digit, a dropped clip or a stripped leading zero changes what a patient hears | One composition source; golden-sample tests per language (`1`, `7`, `12`, `101`, `999`); byte-level comparison with the existing 20 composed samples |
| Language-specific pronunciation defects | English and Bangla are reviewed by different ears; a "fix" in one can regress the other | Per-language review records; no bulk re-generation across both languages in one step |
| Breaking offline operation | A refactor that fetches per announcement looks fine online and fails in a chamber with no internet | Offline test with the network disabled after installation, as an acceptance condition; no runtime fetch in the engine |
| Catalogue incompatibility | Engine and catalogue are updated independently once W4 exists | Declared supported `schema`/`version` range; refuse rather than degrade; install-time compatibility check |
| Queue operations becoming dependent on audio | One `await` on playback in a queue handler would couple a clinical workflow to a loudspeaker | The `_notify` hook pattern; a static test that no queue handler references the audio engine; a forced-failure test |
| Incomplete rollback | A half-copied catalogue is worse than the old one | Atomic swap; previous version retained; rollback exercised in a test, not merely documented |

**Phased strategy** — each phase separately authorised, each with its own exit evidence:

| Phase | Content | Prerequisites | Testing | Rollback |
|---|---|---|---|---|
| **P0** | Freeze and label the accepted draft: tag the catalogue version, snapshot all 28 checksums | Nothing | Checksum re-verification | Not needed (read-only) |
| **P1** | Timing pass: measure and *report* leading/trailing/junction silences per asset; propose a policy | P0; owner decisions O-2/O-3 | Measurement report only, no file modified | Not needed |
| **P2** | Non-destructive timing normalisation at playback (junction gap as an engine parameter) | P1; the W1 engine exists | Composed-sample A/B with checksums; both languages | Remove the parameter |
| **P3** | Targeted re-records for defective assets only | Owner approval naming the assets; provider key in the environment | Full validator chain + human review per asset | Restore the preserved original from the backup record |
| **P4** | Promotion of a new catalogue version | P2/P3 complete; review verdicts recorded | Full validator chain, preview harness, offline check | Switch back to the previous catalogue directory |

Voice refactoring must **never** precede the playback engine: without an engine there is nothing to
compare against and the phase would be unverifiable.

---

## 7. Technical debt and known limitations

| # | Debt / limitation | Impact | Where it lives | Disposition |
|---|---|---|---|---|
| TD-1 | Two composition paths would exist if W1 re-implements wording rules | Wording drift between spoken text and played clips — the highest-risk defect in the capability | `content.js` vs the future engine | Design W1 to derive segments from one source; test the agreement |
| TD-2 | Success is reported at `start`, not completion | An announcement cut off mid-sentence reports success | `speech-synthesis.js` | W1 reports on `ended`; the speech adapter's `spoken` is documented as "started" |
| TD-3 | Announcement language = operator interface locale | An English-UI receptionist in a Bangla facility speaks English | `QueueAnnouncements.js:47` | W2 |
| TD-4 | Enable/disable is per browser tab, not per facility | A refresh re-enables; two operators can disagree | `controller.js` (`enabled` in memory) | W2 |
| TD-5 | No server-side announcement record | Cannot answer "was the patient called audibly at 10:42?" | nothing exists | W2/W3 audit events |
| TD-6 | Bangla clips carry ~1.26 s mean trailing silence | Long uneven gaps; Bangla and English announcements do not sound alike | the 28 assets | O-2 (owner) → phases P1/P2 |
| TD-7 | Junction pause is 0 ms by measurement | Clips butt together; digits can run into the next word | composition policy | Owner policy (POD-3) → engine parameter |
| TD-8 | Room composition is unreachable | Two of the four approved template variants can never be used in production | `QueueEntry` schema | BLOCKED → POD-2 |
| TD-9 | 15 unreferenced files in a publicly served tree | Dead weight; raw voice sources publicly downloadable | `frontend/public/audio/` | O-7 (owner) |
| TD-10 | Preview tooling is not the product | A reviewer may mistake the harness's green run for product verification | `scripts/que-006-audio/preview/` | Keep the distinction explicit in every report (as here) |
| TD-11 | `next/dist/build/swc` unavailable in this install | The JSX compile test skips, so page compilation is unproven here | test environment | W6 loads the real page; investigate separately |
| TD-12 | No device/voice matrix | Bangla may have no voice at all on the target machine (speech path) | deployment environment | W6 acceptance condition |
| TD-13 | Feature-catalogue status cells are stale (owner-controlled) | The signed artefact understates what exists and overstates what QUE-006 delivers | `AMSDP_MVP_Feature_Catalogue…:577-581, 1266` | Owner edit; not editable here |
| TD-14 | `call` action has no UI | The core journey "call the next patient" is unreachable, so an announcement trigger built today would have nothing to fire on | `frontend/pages/queue.js` | Prerequisite inside W1/W3 (§9) |

---

## 8. Remaining production implementation roadmap

Each workstream states its **deliverable**, its **acceptance criteria**, and what must **not** change.
This is the contract for the tasks that follow; none of it is started here.

### 8.1 W1 — Prerecorded playback engine and its integration into the announcement path

**Deliverable.** A framework-free module (proposed `frontend/lib/announcements/prerecorded-audio.js`
with a `segments.js` companion) that, given the *same* payload `content.js` already accepts, resolves
the ordered asset ids for the language, plays them through one `Audio` element, and reports
`completed` / `failed(reason)` / `busy` / `cancelled`. A controller-level strategy chooses
`prerecorded` (default) or `speech` (explicitly configured), never switching silently.

**Acceptance criteria.**

1. Segment resolution agrees with `buildAnnouncement()` for every case the content tests cover:
   with-room/no-room, single digit, multi-digit, Bangla digits, token serial extraction. Proven by a
   test that compares the segment list against the approved text — not by inspection.
2. Success resolves only after the final segment's `ended`; a synthetic cut-off resolves
   `failed('interrupted')`.
3. A missing asset id resolves `failed('missing_asset')` **before** any sound and never falls back to
   speech synthesis.
4. A corrupt/undecodable file resolves `failed('decode_error')`, and the engine stays usable.
5. A second announcement while one is playing resolves `busy` (no overlap).
6. No network fetch when the catalogue is installed (offline test).
7. No queue handler awaits the engine; a static test asserts the queue page never awaits playback.
8. The existing 53 frontend tests still pass; new tests drive a fake audio element (no browser needed).

**Must not change.** Wording, assets, manifest, queue logic, permissions, schema.

**Blocked sub-item.** The with-room path cannot be exercised end-to-end until POD-2 resolves the room
source; the engine must still implement and unit-test it.

### 8.2 W2 — Facility announcement configuration and permission enforcement

**Deliverable.** Persisted `enabled` + `language` per facility, an audited configuration route and a
configuration surface, following `appointment_config.py` + `pages/notifications.js`.

**Acceptance criteria.**

1. `GET` returns the effective settings plus `updated_at`/`updated_by`; a foreign facility is a
   **non-disclosing 404**, never 403.
2. `PUT`/`PATCH` is audited with before/after values; denials are audited too.
3. Only `super_admin`, `org_admin`, `branch_admin` can write; `receptionist`/`doctor` are refused on
   write and see a read-only or no view.
4. The configuration is facility-scoped in the sense the owner chose (POD-5) — an org-level block or a
   per-branch row — and the migration is forward-only and idempotent.
5. Malformed stored configuration falls back to safe defaults (default enablement is POD-6) without
   raising.
6. The queue page reads the setting once per load and never derives language from the interface locale.
7. Backend tests cover: admin write, receptionist/doctor refusal, cross-tenant 404, malformed config.

### 8.3 W3 — Non-blocking queue/audio integration and failure handling

**Deliverable.** The announcement attached to the queue `call` event without ever entering its
critical path, with accurate outcome reporting and duplicate suppression that survives a refresh.

**Acceptance criteria.**

1. A `call` transition completes and responds **whether or not** audio plays; a forced audio failure
   (asset removed / device muted / engine throwing) leaves the queue response unchanged.
2. The announcement carries a stable event identity (a server-supplied id, or `entry:action:revision`)
   so two pages do not double-announce one call, and a recall is announceable as its own event.
3. `played` / `failed` / `skipped` outcomes are recorded server-side as append-only audit events with
   no patient identity.
4. A queue action never fails because of an audit-write or audio problem (best-effort, like `_notify`).
5. A test proves audio state cannot influence queue state: no announcement row is joined into a queue
   query, and no queue handler imports the engine.

### 8.4 W4 — Remote catalogue installation (approved local-agent architecture)

**Deliverable.** The approved architecture, built as approved: local agent → secure outbound poll →
version discovery → download → checksum verification → atomic install → previous version retained →
status reporting → offline operation on the last good catalogue.

**Acceptance criteria.**

1. The agent authenticates outbound only; no inbound port is opened on the facility PC.
2. Catalogue discovery returns a version plus a checksum manifest; the agent installs only a catalogue
   whose playback checksums verify.
3. Installation is atomic: a failure at any point leaves the previous catalogue intact and usable.
4. Rollback to the previous version is a single operation, exercised in a test.
5. Status (installed version, last check, last result, errors) is reportable and visible to an admin.
6. A download interrupted by a network failure is recoverable without manual cleanup.
7. With the network down, playback works from the last installed catalogue.
8. **No alternative update mechanism is introduced**; static serving of `frontend/public/audio/` stops
   being the transport of record for a facility installation.

### 8.5 W5 — Asset distribution and cleanup (O-7)

**Deliverable.** An owner-approved disposition for the 15 unreferenced files, executed as its own
reversible task with a checksum manifest.

**Acceptance criteria.** Owner decision recorded; manifest references unchanged; validators still exit
0; preserved originals still verified; `git status` shows only the intended deletions/moves; nothing
the manifest references is touched.

### 8.6 W6 — Operational verification

**Deliverable.** Evidence, not assertions: a browser/device/offline matrix with recorded results.

**Acceptance criteria.** Every row of §10 has an artefact (harness output, log, screenshot, recorded
run). Until then, no report may describe QUE-006 as verified or accepted.

---

## 9. Recommended implementation sequence and dependencies

### 9.1 The proposed order, evaluated

The task proposed: (1) approve the refactoring report, (2) prerecorded playback (O-6), (3) facility
configuration, (4) non-blocking queue integration, (5) remote installation, (6) asset cleanup,
(7) integrated verification, (8) final report.

**That order is sound, and this report adopts it with three evidence-based amendments.** The
amendments do not reorder the workstreams; they insert prerequisites that the repository shows are
missing and that would otherwise make steps 4 and 7 unverifiable.

### 9.2 Amendments and their evidence

**A1 — Split step 2 into "engine module" and "engine wired to an event."**
The engine can be built, tested and reviewed with no queue change at all (a fake audio element, a
payload, an expected segment list). Wiring it to a queue transition, by contrast, depends on an event
that does not exist (§5.5). Splitting lets the largest, riskiest piece start immediately after
approval while the event contract is still being agreed.

*Evidence:* `frontend/lib/announcements/` is framework-free by design and the existing tests drive
fakes, so an isolated engine is consistent with the established pattern; no announcement event exists
anywhere (§3.5).

**A2 — Insert the queue `call` action UI as a prerequisite of step 4 (not as part of QUE-006's own
scope decision).**
Today a patient cannot be *called* from the product at all (QOP-001). An announcement attached to
`call` would fire only if something triggers `call`. Two consequences: (a) acceptance criterion
"announcements triggered by appropriate queue events" is untestable in the UI without it; (b) the
journey in the feature catalogue ("patient called to consultation") is unreachable. This is QUE-001
work, so it needs its own authorisation — but it must be sequenced here or step 7 will stall.

*Evidence:* `frontend/pages/queue.js` never sends `action: 'call'` (grep); `backend/queuing/main.py:396-404`
supports it; gap analysis QOP-001 and OD-1 report O-7 say the same thing.

**A3 — Pull a single browser smoke test forward to immediately after step 4, instead of leaving all
verification at step 7.**
The current tree has one skipped test which is the only compile evidence for the page (TD-11) and
zero device evidence (TD-12). Discovering at step 7 that the page does not run in a browser would
invalidate steps 2–5 retrospectively.

*Evidence:* §5.9 (1 skipped test), OD-1 report §11 (no device verification).

**A4 (scope warning, not a reorder) — step 6 (cleanup) must come after step 5 (remote installation).**
Once W4 exists, the "served tree" stops being the installation transport; deciding what is served
before that decision is made risks approving a cleanup that W4 immediately makes obsolete.

### 9.3 Dependency graph

```
 (1) Owner approves this report + POD-1…POD-6 answered
      │
      ├─────────────► A2  queue `call` action UI (QUE-001, own authorisation)
      │                    │
 (2a) W1 engine module (isolated, fake audio) ──┐    │
      │                                        │    │
 (3)  W2 facility config + permissions ◄───────┘    │
      │  (needs POD-5 storage/permission decision)  │
      ▼                                             ▼
 (4)  W3 wire the engine to the call event + audit + event identity ◄─── A2
      │
      ├──► A3  one browser smoke test (page loads, a call announces audibly)
      │
 (5)  W4 remote catalogue installation (agent + registry + atomic swap + rollback)
      │
 (6)  W5 asset cleanup (after W4, per A4; needs POD-7/O-7)
      │
 (7)  W6 full browser/device/offline matrix (needs POD-2 for the with-room rows)
      │
 (8)  QUE-006 implementation + acceptance report (owner signs; catalogue boxes ticked by the owner)
```

### 9.4 What each step is blocked by

| Step | Blocked by | Blocking type |
|---|---|---|
| 1 | Nothing | Owner act |
| 2a (engine) | Approval of this report; POD-1 (ranges) for validation bounds only | Owner, then engineering |
| 2b (wire to event) | A2 (call UI) or a server-side event contract; POD-2 for with-room | Engineering + owner |
| 3 (config) | **POD-5** (org-level vs per-branch storage, and which capability gates it); POD-6 (default enablement) | **Owner decision — cannot be engineered around** |
| 4 (integration) | 2b, 3; POD-4 (whether a server audit record is required for acceptance) | Engineering + owner |
| 5 (remote install) | 4 stable; a server-side catalogue registry design | Engineering |
| 6 (cleanup) | 5; **POD-7** (O-7 disposition) | Owner |
| 7 (verification) | 4, 5; **POD-2** (room), a named human reviewer (O-3) | Engineering + owner |
| 8 (final report) | 7; owner acceptance of the audio itself | Owner |

### 9.5 What may run in parallel

- W1's engine module and W2's configuration **backend** are independent: one is frontend-only and
  touches no server code; the other is server-only.
- The preview/review track (human listening, O-3) is independent of every workstream and should run in
  parallel from day one, because it is the only thing that can ever close the pronunciation question.
- W4's design work (registry shape, agent contract) can start once W3's event identity is settled,
  even before the agent is written.

### 9.6 Sequencing rule that must not be broken

**Do not build the remote installer before the engine exists.** An installer with nothing to install
for cannot be verified, and its rollback semantics would be invented rather than tested. Equally, **do
not run a voice refactor (§6) before the engine exists** — a refactor needs a playback path to be
compared through. Both constraints are restatements of the same dependency: *the engine is the hinge.*

---

## 10. Testing and verification requirements

Every row must eventually carry a real artefact. "Code exists" and "unit tests pass" are not
verification (`.clinerules` §7).

| ID | Requirement | Test method | Evidence that would satisfy it | Current state |
|---|---|---|---|---|
| V-01 | English prerecorded announcement, no room | Play through the product; compare with the approved text | Recorded run + clip list | **Not possible yet** (no engine) |
| V-02 | Bangla prerecorded announcement, no room | Same | Same | **Not possible yet** |
| V-03 | With-room announcement, both languages | Same, with a room on the payload | Same | **Blocked** (no room data, POD-2) |
| V-04 | Single-digit token (`1`…`9`) | Deterministic case in the preview harness **and** in the product | Harness output + product run | Harness: yes; product: no |
| V-05 | Multi-digit token (`10`, `101`, `999`) | Same | Same | Harness: yes; product: no |
| V-06 | Room-number composition | Same | Same | **Blocked** |
| V-07 | Offline playback after installation | Disable the network, announce | Log + recorded run | **No engine, nothing installs** |
| V-08 | Missing asset handling | Remove one file from the installed catalogue; announce | `failed('missing_asset')`, no sound, no fallback | **No engine** |
| V-09 | Corrupt asset handling | Truncate a file; announce | `failed('decode_error')`, engine reusable | **No engine** |
| V-10 | Completion reporting | Cut playback short; observe the outcome | `failed('interrupted')`, not `completed` | **Unimplemented** (§3.4) |
| V-11 | Non-blocking queue operation | Force audio failure during a call | Queue response identical to the no-audio case | **Unimplemented** (§5.5) |
| V-12 | Duplicate suppression across two clients | Two browsers on one queue, one call | One announcement | **Single-client only** |
| V-13 | Facility enable/disable | Configure off, then call | No audio, and the UI says so | **Unimplemented** |
| V-14 | Facility language | Configure bn then en, then call | Correct language each time, no substitution | **Unimplemented** |
| V-15 | Configuration permissions | Receptionist and doctor attempt to write | Refused; denial audited; admins succeed | **Unimplemented** |
| V-16 | Cross-tenant configuration access | Foreign `org_id` | Non-disclosing **404** | **Unimplemented** |
| V-17 | Remote installation + rollback | Install v2, roll back to v1 | Status report + played output from v1 | **Unimplemented** |
| V-18 | Autoplay refusal on the target device | Real kiosk/TV with a blocked policy | Visible "audio off", no exception, queue unaffected | **Only against a fake engine** |
| V-19 | Bangla voice availability on the target device | Enumerate voices on the device | Documented matrix | **Absent** (TD-12) |
| V-20 | Page actually compiles and runs | `next build` + browser load | Build log + page load | **Skipped in this install** (TD-11) |
| V-21 | Human listening review of the 28 clips | Named reviewer, per-asset verdicts | Filled `review-template.csv` | **Not performed** (O-3) |

Minimum bar before any "QUE-006 delivered" claim: **V-01, V-02, V-04, V-05, V-11, V-13, V-14, V-15,
V-20** green, plus V-03/V-06 resolved by decision or accepted as blocked, plus V-18/V-19 on the real
device. V-07, V-08, V-09 and V-17 are required before any facility install.

---

## 11. Risks and rollback strategy

### 11.1 Delivery risks

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-1 | The draft audio is modified by accident during later work | Low | High — the accepted sound is lost | Read-only treatment of the 28 assets + manifest; checksum gate in every task report | Engineering |
| R-2 | Two composition paths drift (text vs clips) | **High** if not designed against | High — the product says one thing, the clips another | One source of truth; agreement test (§8.1 AC-1) | Engineering |
| R-3 | Queue operations become coupled to audio | Medium | High — a clinical workflow stalls on a loudspeaker | `_notify` best-effort pattern; no `await` in handlers; static test | Engineering |
| R-4 | Silent fallback to speech synthesis for Bangla | Medium | High — a wrong-language announcement in a clinic | Explicitly no fallback; `no_asset` outcome; test | Engineering |
| R-5 | Facility-config permission boundary wrong (`branch_admin` excluded) | **High** if built on the existing precedent | Medium — approved behaviour not delivered | POD-5 decided **before** the route is written | Owner |
| R-6 | Bangla trailing silence makes announcements feel broken | Medium | Medium — perceived quality, not correctness | Owner timing decision (O-2); engine-side junction control | Owner |
| R-7 | Remote installer ships without a tested rollback | Medium | High — a bad catalogue at a facility with no way back | Atomic swap + previous version retained; rollback test as AC | Engineering |
| R-8 | "Verified" claimed from a green unit suite | **High** (observed pattern) | High — false acceptance | §7 evidence standard; §10 artefact requirement | Governance |
| R-9 | An agent edits an owner-controlled catalogue status | Low | High — a signed artefact corrupted | §11 read-only list; owner edits only | Governance |
| R-10 | Cleanup (O-7) deletes a file something later needs | Low | Medium | Sequenced after W4; reversible with a checksum manifest; owner approval | Owner |

### 11.2 Rollback strategy

| Change type | Rollback |
|---|---|
| Frontend code (engine, controller wiring) | Revert the commit; the speech path and the assets are untouched, so the product returns to its current behaviour |
| Facility configuration rows/columns | Forward-only migration; rollback is a **new** migration that drops the added column/table — settings are additive and default-safe, so a revert restores prior behaviour |
| Audio catalogue version | Atomic directory swap back to the retained previous version; checksums verified before and after |
| Asset cleanup (O-7) | Restore from the preserved originals (`frontend/.audio-originals-backup`, verified) — which is why the cleanup must not touch the backup |
| Voice refactor | A new catalogue version beside the draft; the accepted draft is never overwritten, so rollback is "keep using the draft" (§6.6) |
| Remote installation at a facility | Agent-initiated rollback to the retained previous catalogue, reported as an installation status event |

**Non-negotiable:** no rollback may require destroying the audit trail, the preserved originals or the
accepted draft. If a proposed rollback would, it is not an acceptable plan.

---

## 12. Product Owner decisions

### 12.1 Decisions already taken and preserved (not re-opened here)

| ID | Decision | Where recorded | Preserved by this report |
|---|---|---|---|
| OD-1 | Browser speech synthesis is the delivery mechanism for the current announcement path | OD-1 implementation report | §3 |
| OD-2 | Facility enable/disable + language configuration is intended to live in facility configuration | OD-1 report O-2 | §5.4, §8.2 |
| OD-3 | Approved wording, both languages, no doctor name, no honourific, no patient identity | `content.js`, doctor-name removal report | §2.2, §3.2 |
| — | Current output accepted as **DRAFT**; recordings retained; no re-recording | this task's assignment | §2 |
| — | Prerecorded local audio is the **primary** playback approach | catalogue + manifest `playable` | §5.3, §8.1 |
| — | Offline operation after installation | approved architecture | §8.4 |
| — | Browser speech synthesis is an **optional** alternative only; no automatic Bangla substitution | OD-1, `speech-synthesis.js` | §6.3, R-4 |
| — | Audio must never block a queue operation; success only after completed playback | feature catalogue QUE-006 | §5.5, §8.3 |
| — | Configuration boundary: `super_admin`, `org_admin`, `branch_admin` configure; `receptionist`, `doctor` trigger only | feature catalogue QUE-006 | §5.4 |
| — | Remote installation architecture: local agent, outbound poll, verified download, atomic install, rollback, status | assignment §3E | §5.6, §8.4 |
| — | Token/room ranges, trailing-silence policy, inter-clip pause policy, pronunciation approval, source-asset removal and any change to the accepted draft remain **owner decisions** | assignment §8 | §12.2 |

### 12.2 Decisions still required

| ID | Decision needed | Blocks | Recommendation (not a decision) | Status |
|---|---|---|---|---|
| **POD-1** | Maximum token-number and room-number range | Validation bounds in the engine; the catalogue's 1–999 is unapproved | Adopt 1–999 for tokens and rooms as an operational limit; a token serial is already capped at 9 digits in code | Open |
| **POD-2** | Where a room number comes from (doctor's room, appointment room, branch room assignment?) and whether it may change mid-queue | With-room announcements (V-03, V-06); a payload change and possibly a migration | Room on the **queue entry**, snapshotted at call time from the branch room assigned to the doctor for that session | Open (**blocks an acceptance criterion**) |
| **POD-3** | Inter-clip pause policy (junction gap, digit gap, leading gap) | Engine timing; "natural-sounding" acceptance | 0 ms today; adopt a tunable engine-side gap (e.g. 60–120 ms) rather than baking it into files | Open |
| **POD-4** | Whether a server-side announcement record (played/failed/skipped) is required for acceptance | W3 audit events | Required — without it, "announcements were made" is unproven and un-auditable | Open |
| **POD-5** | Storage scope and capability for announcement configuration: org-level (`organizations.config`, `org.manage`) or per-branch (new row/column, `facility.manage`) | W2 — **cannot be engineered around** (§5.4) | Per-branch storage gated on `facility.manage`, because the approved boundary includes `branch_admin` and a branch is the facility that hears the announcement | Open (**blocks W2**) |
| **POD-6** | Default enablement for a facility that has never configured announcements | W2 defaults | Disabled until configured — the catalogue says announcements are "not forced on every facility", and an unexpected loudspeaker in a clinic is worse than silence | Open |
| **POD-7** | O-7 disposition: may the 15 unreferenced files (13 `.m4a`, the `.mpeg`, the mislabelled `room-suffix.wav`) be removed from the served tree? | W5 | Remove the `.m4a`/`.mpeg` from the **served** tree (they remain in the preserved backup); decide the mislabelled `room-suffix.wav` explicitly; never rename it | Open |
| **POD-8** | O-2 trailing-silence policy: trim in a separate approved pass, compensate at playback, or accept as-is | §6 phases P1/P2; audible pacing | Compensate at playback (non-destructive) now; revisit trimming only if the compensated result is unsatisfactory | Open |
| **POD-9** | O-4: `en.phrase.no-room` was recorded with a leading comma; the catalogue cell omits it | Wording sign-off | Treat the recorded clip as authoritative for the draft; do not re-record for punctuation alone | Open |
| **POD-10** | O-5: which provider/voice is "the" product voice for any future generation | Any re-record | Record whatever produced the accepted draft as the reference voice; choose nothing new | Open |
| **POD-11** | O-3: name a reviewer (native/fluent for Bangla) and the re-review policy when a clip changes | V-21; any pronunciation claim | One named reviewer per language; any changed clip returns to `pending` and must be re-reviewed before use | Open |
| **POD-12** | Authorisation for the queue `call` UI (QUE-001 work) — in or out of QUE-006's critical path | §9 A2; V-11 and the "triggered by queue events" criterion | In — without it the capability cannot be verified through the product | Open |

Nothing here pre-empts any decision. Where a recommendation appears it is labelled as such and
carries no authority.

---

## 13. File-level evidence and verification of this task

### 13.1 Files inspected (evidence for every claim above)

| File | What it proves |
|---|---|
| `frontend/lib/announcements/content.js` (165 lines) | Wording, token-number rules, event key, no-PII contract |
| `frontend/lib/announcements/controller.js` (286 lines) | Enable switch, dedupe window, busy, activation states |
| `frontend/lib/announcements/speech-synthesis.js` (379 lines) | Voice selection, no substitution, start-vs-completion semantics |
| `frontend/components/queue/QueueAnnouncements.js` (149 lines) | Operator surface; language from interface locale |
| `frontend/pages/queue.js` (262+ lines) | Wiring, `canAnnounce`, per-row button, no `call` action |
| `frontend/tests/queue-announcement-{content,controller,speech}.test.mjs`, `queue-announcements-boundary.test.mjs` | The 53 tests: 52 pass, 1 skipped |
| `frontend/public/audio/manifest.json` (53,888 bytes) | 28 assets, checksums, `integratedWithApplication: false`, 0 human-approved |
| `frontend/public/audio/**` (72 files) | 56 referenced, 15 unreferenced (§4.2) |
| `backend/common/models.py` (`QueueEntry` 854-882; `Organization` 31-45) | No room field; `locale`/`config` exist |
| `backend/common/config.py` | Config accessor pattern (`queue_config`, `appointment_config`, `registration_policy`) |
| `backend/organization/appointment_config.py` (116 lines) | The audited config-route template |
| `backend/organization/notification_config.py` | Sibling config surface (`org.manage`) |
| `backend/organization/facility.py` | Facility tree routes (`facility.read`/`facility.manage`) |
| `backend/common/permissions.py` | Who holds `org.manage`, `facility.manage`, `queue.*` |
| `backend/queuing/main.py` (47-57 `_notify`; 396-404 queue actions) | Non-blocking hook; `call` gated on `queue.manage` |
| `scripts/que-006-audio/**` (27 files) | Generation, standardisation, validation, preview tooling |
| `scripts/que-006-audio/lib/env.mjs` | Provider → environment-variable key mapping |
| `docs/product/AMSDP_MVP_Feature_Catalogue…` (544-581, 976, 1266) | Ten acceptance criteria, none ticked; stale status |
| `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` (§3.4-3.6, QOP-001, ANN-001…010) | Finding register |
| `docs/implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` (§12, §14-15, §17) | O-1…O-7, decisions D-1…D-5, validators |
| `docs/implementation/AMSDP_QUE-006_OD-1_…_V1.0.md` (§11-13) | Not-verified statement; O-1…O-10 |
| `docs/implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` | The 20 samples, harness, 12/12 |
| `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` (§2-3) | Assets, ranges, composition rules |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Navigation; updated by this task (Revision 44) |

### 13.2 Commands run and their results

| Check | Result |
|---|---|
| `git status --porcelain` | HEAD `37cf3d1`. Modified: `.gitignore`, `docs/governance/AMSDP_Docs_Index_V1.0.md`, `frontend/lib/announcements/content.js`, `frontend/pages/queue.js`, `frontend/tests/queue-announcement-content.test.mjs`, `frontend/tests/queue-announcement-controller.test.mjs` — **all pre-existing except the index edit made by this task** |
| Untracked | Six QUE-006 reports (five pre-existing + **this one**), `frontend/public/`, `scripts/` — the QUE-006 work is **not committed**; that is the pre-existing state and it was preserved |
| Frontend announcement tests | 53 tests, **52 pass, 0 fail, 1 skipped**, 531.56 ms |
| Mechanically counted audio files | 72 files, 56 referenced, 15 unreferenced |
| Manifest read-back | 28 assets; `complete: true`; `humanApproved: 0`; `integratedWithApplication: false` |
| Repository-wide searches | no announcement config key, no audio consumer, no local agent, no service worker, no `HTMLAudioElement` |

### 13.3 Strict-scope confirmation

| Restriction | Status |
|---|---|
| No voice engine refactor | Not touched |
| No announcement wording change | Not touched — `content.js` unchanged by this task |
| No production announcement or queue logic change | Not touched |
| No recording changed, regenerated, trimmed or normalised | Not touched — all 56 manifest-referenced files and all 15 originals untouched |
| No manifest or catalogue change | Not touched |
| No audio file deleted or moved | Not touched |
| No facility settings or permissions changed | Not touched |
| No playback integration implemented | Not touched |
| No remote installation agent implemented | Not touched |
| No schema or API change | Not touched |
| No commit, push or deploy | None performed |
| Pre-existing local modifications and untracked files preserved | Yes (§13.2) |
| Existing reports not overwritten | Yes — one new file created; the index was updated additively |

---

## 14. Final status, handoff and the recommended next task

### 14.1 Final status of this task

| Aspect | Result |
|---|---|
| Deliverable | **Created** — `docs/implementation/QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md` |
| Documentation index | Updated (Revision 44, one new row, snapshot counts corrected) |
| Production code | **Untouched** |
| Audio assets / manifest | **Untouched** |
| Schema / API / permissions / queue logic | **Untouched** |
| Commit / push / deploy | **None** |
| Evidence level reached for QUE-006 | **PARTIALLY IMPLEMENTED and NOT VERIFIED** — unchanged by this task |

### 14.2 What is already implemented and verified

- The 28-asset audio catalogue: masters + playback files, per-asset SHA-256, manifest schema 2.0,
  three validators exiting 0, 29 preserved originals re-verified. **Verified technically** (not
  pronunciation).
- The isolated composed-sample preview: 20 samples, reviewer page, headless-Chrome harness 12/12 in a
  real browser. **Verified.**
- Doctor-name/honourific removal from the spoken payload. **Verified** by tests that assert absence.

### 14.3 What is implemented but not verified

- The browser speech-synthesis announcement path in full: wording, controller decisions, voice
  selection, panel, queue-page wiring. 52 of 53 tests pass; the 53rd (JSX compile) is skipped; nothing
  has been heard on a device.

### 14.4 What remains to be implemented

W1 prerecorded playback engine · W2 facility configuration + permission enforcement · W3 queue-event
integration, event identity and announcement audit · W4 remote catalogue installation agent · W6
operational verification. W5 awaits a decision.

### 14.5 What requires Product Owner decisions

POD-1 … POD-12 (§12.2). Two block work outright: **POD-5** (configuration scope and capability) and
**POD-2** (room source, which blocks an acceptance criterion). POD-7 (asset removal), POD-3 (pause
policy) and POD-8 (trailing silence) shape the quality of the delivered result.

### 14.6 Recommended next task (not started)

**Task ID (proposed):** `AMSDP-QUE-006-W1-PRERECORDED-PLAYBACK-ENGINE`
**Scope:** one isolated, framework-free frontend module plus tests. **No** queue page change, **no**
configuration, **no** schema change, **no** asset change.

| Element | Detail |
|---|---|
| Deliverable | `frontend/lib/announcements/prerecorded-audio.js` (+ `segments.js`), driven by `frontend/public/audio/manifest.json`; reports `completed`, `failed(reason)`, `busy`, `cancelled` |
| Depends on | Owner approval of this report; POD-1 for the validation bound only (the module can be built with the bound injected) |
| Must not touch | wording, assets, manifest, queue logic, permissions, schema, the speech path |
| Test approach | `node --test` with a fake `Audio` element, following the existing announcement test conventions (no new dependency) |
| Acceptance criteria | §8.1, AC-1 … AC-8 |
| Exit evidence | Test-run output (pass counts) + a segment-list/module description in the implementation report; explicitly **not** a claim of audible verification |
| Why first | Every other workstream needs it: configuration without an engine configures nothing, integration without an engine wires nothing, installation without an engine installs nothing, and verification without an engine can only verify speech synthesis |

**Do not begin this task in this assignment.** It waits for explicit authorisation.

### 14.7 Handoff summary

**Implemented and verified:** the audio catalogue and its technical integrity; the isolated preview
harness; the removal of doctor identity from announcements.
**Implemented, not verified:** the browser speech-synthesis announcement path, end to end in unit tests
only.
**Not implemented:** prerecorded playback, facility configuration, queue-event integration and audit,
remote installation, operator-facing verification.
**Awaiting the owner:** twelve decisions (§12.2), plus the human listening review (O-3).
**Draft status:** the current English and Bangla output remains the **accepted draft** — unchanged by
this task, and not promoted to production acceptance by anything written here.

### 14.8 Governance and skill compliance (`.clinerules` §6)

| Requirement | How it was met |
|---|---|
| Documents read before acting (§2 step 3, §12) | `docs/governance/AMSDP_Docs_Index_V1.0.md` (index, read first), the QUE-006 document set (catalogue, OD-1 report, generation report, standardisation report, doctor-name removal report, preparation report), the gap analysis, the feature catalogue QUE-006 section, `.clinerules` |
| Routing applied (§4) | Rows used: *Backend API*, *Multi-tenant data*, *Database schema* (examined, not changed), *Queue/scheduling/workflow*, *Audit*, *Documentation*, *LLM/AI tooling* (generation workflow) |
| Skills | **None installed** (§5) — no `.clinerules/skills/`, no skill packages. The governance documents were used instead, and no skill usage is claimed |
| Non-negotiables (§3) | No secret written or quoted; no authorisation weakened; no second tenant key proposed; audit trail untouched; no schema change; no capability claimed that is not verified |
| Evidence standard (§7) | Every status carries a file path, a test result or a command result; IMPLEMENTED ≠ VERIFIED is stated wherever it matters; the one skipped test and the absent device evidence are disclosed |
| Execution boundaries (§9) | No server started; no suite spawned beyond the announcement unit tests; no destructive git operation; no commit |
| Documentation output location (§11) | Written under `docs/implementation/` — an existing subfolder — with no filename collision (the name did not previously exist); no other folder used; index updated in the same task |
| Documentation reading (§12) | Index read first; every cited document was opened in this session; the ~320 KB UI/UX blueprint was not loaded, and no large document was pasted into the conversation |
| Owner-controlled documents | Read only (feature catalogue, business rules, MVP scope, architecture); the stale QUE-006 status cells were **reported, not edited** |
| Verification performed | 53 announcement tests run (52 pass / 1 skip); `git status` captured; audio tree counted; manifest read back; repository searches for the missing seams |

**Deviations and open items:** none in scope. The only judgement calls are the sequencing amendments
A1–A4 (§9), which are recommendations awaiting approval, and the §5.2 labels for features that are
partly present — each is stated with its reason rather than rounded up.

---

*End of report. Nothing in this document authorises implementation.*
