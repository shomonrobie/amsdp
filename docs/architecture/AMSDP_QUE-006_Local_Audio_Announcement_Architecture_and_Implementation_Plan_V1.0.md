# AMSDP QUE-006 — Local Audio Announcement Architecture and Implementation Plan V1.0

| Field | Value |
|---|---|
| Document ID | AMSDP-QUE-006-LOCAL-AUDIO-ARCH-001 |
| Task ID | AMSDP-QUE-006-LOCAL-AUDIO-DESIGN-01 |
| Task mode | READ-ONLY — architecture, source inspection and technical design |
| Status | DESIGN ONLY. No finding in this document is fixed, tested, verified or accepted |
| Branch / HEAD inspected | `hackathon-mvp` @ `37cf3d1e9db76834044afd48fa5729463a26ec47` |
| Working tree during inspection | clean (0 modified, 0 untracked, no stashes) |
| Date | 2026-11-20 |
| Evidence rule | Every claim about current behaviour cites `file:line` at the HEAD above. Runtime, browser and device behaviour is explicitly marked as **not performed** |

**How to read this document.** Section 18 separates what the Product Owner has approved from what this
document merely recommends. Unless a statement appears in the "owner-approved" column of §18, it is an
engineering recommendation that requires approval before implementation.

---

## 1. Executive summary

### 1.1 What the owner has decided

QUE-006's delivery mechanism is being replaced as the *primary* path. The approved direction is:

- **Primary:** locally stored, pre-recorded Bangla and English audio clips, **assembled dynamically at
  playback time** from reusable phrase recordings plus number recordings/components.
- Doctor-specific recordings may be used where they exist.
- Local playback must work **without internet connectivity** once assets are installed.
- External TTS is an **optional** fallback, never a mandatory dependency.
- Browser-native speech synthesis may remain an **optional alternative** but must not be the primary
  Bangla mechanism.
- **Queue operations must never depend on audio success.**
- Patient identity and clinical information must never be announced.

### 1.2 Why this direction is technically justified — not just preferred

The OD-1 mechanism (Web Speech API) cannot *guarantee* Bangla. Voices are supplied by the device's
operating system, so a Windows kiosk, an Android TV and an iPad each have a different — or absent —
Bangla voice. The Phase 3 gap analysis already recorded this as the decisive risk
(`docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md:913`, finding ANN-003). The current implementation handles the
absence honestly (it refuses rather than reading Bangla with an English voice —
`frontend/lib/announcements/speech-synthesis.js:18-20, 132-138`), but "honest refusal" is not a
shippable announcement feature. **Recorded clips are the only mechanism that can guarantee Bangla
quality, offline, on an unknown device.**

### 1.3 What exists today (verified at source, not from reports)

OD-1 is implemented and unit-tested in the tree at `37cf3d1`:

| Layer | Location | State |
|---|---|---|
| Wording | `frontend/lib/announcements/content.js` (163 lines) | Implemented; pure, unit-tested |
| Browser adapter | `frontend/lib/announcements/speech-synthesis.js` (379 lines) | Implemented; unit-tested against a fake engine |
| Controller | `frontend/lib/announcements/controller.js` (286 lines) | Implemented; unit-tested |
| Operator surface | `frontend/components/queue/QueueAnnouncements.js` (149 lines) | Implemented; boundary-tested |
| Trigger | `frontend/pages/queue.js:57-66, 202` | Manual button on `called` rows only |
| Tests | 4 files, 49 tests | Present; **not run in this task** |

The 49 announcement tests comprise 11 content tests, 15 controller tests, 18 adapter tests and 5
boundary tests. The wider frontend suite was reported green (229/229) by the preceding
commit-verification session against this exact tree; **this read-only task executed no tests** and
claims no coverage.

### 1.4 The four findings, stated once

| # | Finding | Source-level status | Severity |
|---|---|---|---|
| F1 | English wording omits the approved "please proceed to" | **CONFIRMED** — `content.js:36`, `content.js:18`, OD-1 report `:84`, tests `queue-announcement-content.test.mjs:37,43` all encode the shorter sentence | HIGH (patient-facing content is not the approved sentence) |
| F2 | Playback reported successful before it finishes | **CONFIRMED** — `speech-synthesis.js:256-267` resolves on `onstart`; `onend` (`:268-276`) is a no-op because `settle()` is already resolved (`:244-248`); `OUTCOME.SPOKEN` is documented as "speech started" (`:33`); the UI claims "played" (`i18n.js:216`) | HIGH (a failed utterance is presented as delivered) |
| F3 | Duplicate suppression remembers only the most recent event | **CONFIRMED** — single `lastEventKey`/`lastEventAt` pair (`controller.js:62-63`), checked and *overwritten* at `:195-202`; the key is consumed **before** the attempt, so `needs_activation` (`:204-207`) and adapter errors (`:213`) leave a failed event marked announced | HIGH (interleaving defeats suppression; failures are remembered as successes) |
| F4 | Room information is unavailable | **CONFIRMED** — `_entry_to_dict` (`backend/queuing/main.py:82-92`) emits no room; `frontend/pages/queue.js:64-65` passes `entry.room`, always `undefined`; `content.js:117-119` therefore always takes the room-less branch and sets `derived: true` | HIGH (the approved sentence cannot be spoken in full) |

None of these is a regression introduced by a recent commit; they are the committed state of OD-1.

### 1.5 The architectural conclusion

OD-1 got two of its three layers right and is missing the third. The durable shape is:

1. **Composition** — turn a queue event into an ordered list of *phrase units* (pure, language-specific,
   patient-free). Today `content.js` produces a single *sentence string*; for local audio the unit must
   be a plan, and the sentence becomes a *script* the recordings must match.
2. **Renderer** — turn a plan into sound. Today one renderer is bound to Web Speech. It must become an
   interface with three implementations: `local-audio` (primary), `speech-synthesis` (optional),
   `external-tts` (optional fallback).
3. **Controller** — decide *whether* and *when*, and record what happened. This exists, but its
   duplicate store is one slot deep and its success definition is wrong.

Everything in §§4–9 follows from that split, so the four corrections are not throwaway work when local
audio lands.

### 1.6 What this task did not do

No application code, test, migration, configuration, existing documentation or governance file was
modified. No database record was created. No dependency was installed. Nothing was staged, committed or
pushed. One new document (this one) was created.

### 1.7 Ratified QUE-006 acceptance baseline (already on record)

The MVP Feature Catalogue is a Product-Owner-approved document (decision log entry, 2026-11-17) and it
already fixes QUE-006's acceptance criteria. This design is bound to them, so they are quoted here and
traced in §16.6:

| # | Ratified criterion (`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md:544-559`, `:1108-1118`) | Design response |
|---|---|---|
| C1 | Bangla announcement produced for a call event when Bangla is configured | §5, §6.3, Stage D |
| C2 | English announcement produced for a call event when English is configured | §5, §6.2, Stage C |
| C3 | Announcement language configurable per facility | §12.1 `announcementLanguage` |
| C4 | Announcements can be enabled/disabled per facility | §12.1 `announcementsEnabled` |
| C5 | Announcements triggered by appropriate queue events (e.g. patient called) | §8, and see the correction below |
| C6 | No duplicate or conflicting announcements for the same queue event | §3.3 F3 (this finding is a **ratified-criterion breach**) |
| C7 | Voice-output failure does not fail or interrupt the queue call | §4.6 step 6, §8.3 |
| C8 | Only authorized roles (org/branch admin) may configure announcements | §12.3 — **partially answers OD-2** |
| C9 | Spoken announcements contain no unnecessary PII (no patient name/mobile) | §11.1 |
| C10 | Actual audio output verified at browser/runtime before implementation is claimed | §16.4, §16.5 |

**Two corrections this inspection forces on the design, made rather than silently carried:**

1. **Trigger.** C5 plus the catalogue's role statement ("`receptionist`, `doctor` trigger announcements via
   the queue call action", `:546-548`) means an announcement on the call event is the **approved**
   behaviour. This document's earlier working assumption — manual-play only — is therefore *not* the
   approved default; the design carries `announcementTrigger: 'auto_on_call'` as the default with manual
   play/replay as an operator affordance (§12.1, §13.3, §18 A-12).
2. **Configuration ownership.** C8 assigns enable/disable and language to `super_admin` / `org_admin` /
   `branch_admin`, i.e. the **facility** — so OD-2 is answered for the two settings the catalogue names.
   It remains genuinely open only for the *additional* knobs this design introduces (engine preference,
   external-TTS spend, catalogue install) and for *where* the surface lives (§12.3).

Neither correction changes the four findings; both change what "approved" means, which is exactly the
distinction §18 exists to keep.

---

## 2. Current OD-1 implementation assessment

### 2.1 Component map (verified at `37cf3d1`)

| Component | Lines | Responsibility as built | Assessment for the local-audio direction |
|---|---|---|---|
| `lib/announcements/content.js` | 163 | Approved string templates, event key, read-aloud token serial, Bangla digit conversion | **Reusable core, wrong unit.** The PII allow-list (`:85-87`: only `token`, `doctorName`, `room` are read) and the token-serial rule (`spokenTokenNumber`, `:96-124`) are exactly right and must survive. The output unit must change from "one sentence" to "an ordered plan of phrase ids"; the sentence becomes the recording script. |
| `lib/announcements/speech-synthesis.js` | 379 | Web Speech adapter: voice selection, language honesty, one-at-a-time, start timeout, cancel/dispose | **Becomes one of three renderers.** Voice selection (`pickVoice`, `:63-119`) stays, demoted. The completion contract (`:244-276`) must be fixed (§3.2), because the new engines need the *same* contract. |
| `lib/announcements/controller.js` | 286 | Facility switch, dedupe, activation, single-in-flight, observable last outcome | **Reusable shell, two defects at its heart** — dedupe (§3.3) and treating `spoken` as success (§3.2). It is engine-agnostic already (`:45-47` requires only an object with `speak`), which is why the renderer seam can be introduced without a rewrite. |
| `components/queue/QueueAnnouncements.js` | 149 | Panel: enable/activate, language switch, announce-last, live "now speaking", outcome caption | **Retain.** Only the vocabulary changes (`needs_activation`, `blocked`, `spoken` → `completed`, `failed`, `interrupted`, plus asset/engine status). |
| `pages/queue.js` | 57-66, 202 | Manual "Announce" control; passes `token`, `doctorName`, `room: entry.room` | **Retain the manual control**; the room argument is dead today (§3.4) and the trigger set may widen in Stage D. |
| `lib/i18n.js` | `queue.announce*` keys | Bilingual captions incl. `announceLastSpoken: 'played'` (`:216`) | Captions must be re-derived from the new outcome taxonomy. |
| Tests | 49 | Content/adapter/controller/boundary | 5 assertions encode defective behaviour and must change (§14.4). |

### 2.2 What OD-1 got right and the new architecture must not lose

1. **The patient can never be named.** `buildAnnouncement` reads exactly three fields (`content.js:85-103`
   destructures nothing else) and `announcementPayloadFromQueueEntry` ignores everything except those
   fields (`:127-138`). Test `patient identity cannot reach the spoken text` asserts the sentence is
   identical with `patientName`, `mobile`, `notes` present.
2. **An internal identifier is never read aloud.** A real token is `T-<doctor-fragment>-<serial>`
   (`backend/common/queue_tokens.py:20-22`); only the trailing serial is spoken, and a UUID-shaped or
   digitless token refuses with `unspeakable_token` (`content.js:96-124`).
3. **No silent language substitution.** Bangla text without a Bangla voice refuses (`no_voice`), never
   falls back to English (`speech-synthesis.js:132-138`). This rule must be inherited by *every* new
   renderer and by the external-TTS path.
4. **Audio is not on the queue path.** `announceEntry` is fire-and-forget (`queue.js:57-66`); no queue
   action awaits or inspects it. Criterion 7 of §6.1 is satisfied by construction and must stay that way.
5. **The renderer is injected.** `createAnnouncementController({adapter})` (`controller.js:45-47`) means
   the local-audio engine can be introduced behind the existing seam.

### 2.3 What is structurally absent (and is what this design adds)

| Missing capability | Consequence today |
|---|---|
| Any audio asset, manifest, cache or installation step | Nothing can be spoken offline; `frontend/public/` is **empty** and there is no service worker, manifest or PWA config anywhere in the tree |
| A renderer interface (start/complete/fail) | Completion cannot be observed; only one engine can exist |
| A phrase/plan level for composition | Number and room variation is impossible without re-recording whole sentences |
| An announcement event contract (ANN-002) | The only trigger is an operator button; the DQDS has no path to announce |
| Any announcement configuration | Enable/language/engine are component props only (`QueueAnnouncements.js:33-35`), not facility settings — enable/disable and language are **ratified as facility settings** (`MVP_Feature_Catalogue…:548`), so their absence is a gap, not a design choice; engine/TTS ownership remains open (OD-2 residual) |
| Any announcement attempt observability (ANN-008) | The panel shows the last attempt; nothing is logged or audited server-side |
| Room on the queue payload (F4) | The approved sentence is always truncated by one segment |

---

## 3. The four findings and their remediation specifications

Each finding is stated in the same shape: **claim → source-level evidence → affected components → required
correction (testable) → test changes → acceptance criteria → dependencies**. Nothing in this section is
implemented.

### 3.1 Finding F1 — the English announcement does not match the approved wording

#### F1.1 Approved wording (owner)

> "Token number [number], Dr. [doctor's name], please proceed to Room [room number]."

#### F1.2 What the code says

| Evidence | Content |
|---|---|
| `content.js:36` | `withRoom: 'Token number {number}, Dr. {doctor}, Room {room}.'` |
| `content.js:18` | A comment recording the same sentence as `en.withRoom` "OD-3" |
| `content.js:37` | `noRoom: 'Token number {number}, Dr. {doctor}.'` |
| OD-1 report `:84` | The same short sentence, presented as the approved OD-3 template |
| `queue-announcement-content.test.mjs:37` | `assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, Room 305.')` |
| `queue-announcement-content.test.mjs:43` | Asserts `TEMPLATES.en.withRoom` equals the short sentence |

The phrase **"please proceed to"** appears nowhere in the repository. The sentence is two comma-joined
noun phrases with a terminal full stop: it announces a room but never instructs the patient to go there.
The defect is recorded consistently (comment, code, report, test), which is why it survived — the suite
tests that the string has not drifted *from itself*, not that it matches the owner's sentence.

#### F1.3 Affected components

`frontend/lib/announcements/content.js` (templates, `buildAnnouncement`), the content test file, the OD-1
report's §4 table, the operator panel's spoken-text preview, and — critically — **the future recording
script**: with local audio the English phrase clips must be recorded to match this exact sentence, so
re-recording cost is attached to getting the wording right *first*.

#### F1.4 Required correction — English

1. `TEMPLATES.en.withRoom` becomes
   `'Token number {number}, Dr. {doctor}, please proceed to Room {room}.'`
2. The room-less variant must **keep the instruction and drop only the destination**. Engineering
   proposal (requires approval, §18 O-3): `'Token number {number}, Dr. {doctor}, please proceed.'`
3. The doctor-less variants must not fabricate a name and must not leave a dangling "Dr." or a double
   comma. Engineering proposal (requires approval, §18 O-2/O-3):
   - `'Token number {number}, please proceed to Room {room}.'`
   - `'Token number {number}, please proceed.'`
4. Variant selection is by **availability and configuration**, never by guesswork: the plan builder emits
   `segments: ['token_number', 'doctor', 'proceed_to', 'room']` minus absent segments, and the renderer
   speaks exactly those segments. A missing room or doctor removes a segment; it never inserts a
   placeholder, the word "null", or an empty clip.
5. Punctuation stays `, ` between segments and `.` at the end; `Room` is capitalised; `Dr.` keeps its
   period because it is spoken as an abbreviation ("doctor").
6. **Honorific duplication must be fixed in the same change.** `doctor.name` is free text
   (`backend/common/models.py`, `Doctor.name`), and `content.js:121-124` prefixes a literal `Dr. `; a name
   stored as "Dr. A. Rahman" is spoken "Dr. Dr. A. Rahman", and the current test *asserts* that output
   (`queue-announcement-content.test.mjs:112-113`). Correction: strip a leading honorific before prefixing
   — `Dr`, `Dr.`, `ডা.`, `ডাঃ`, `Doctor` — case-insensitively, then prefix once. With local audio this
   matters twice over, because a doctor's own recording already contains the honorific and the
   composition must not prepend the `doctor_prefix` clip when a doctor clip exists.

#### F1.5 Bangla must be documented separately, not inferred

The Bangla sentence is **not a translation** of the English one and must be approved as its own artefact.

| Evidence | Content |
|---|---|
| `content.js:32` | `withRoom: 'টোকেন নম্বর {number}, ডা. {doctor}, কক্ষ {room}-এ আসুন।'` |
| `content.js:33` | `noRoom: 'টোকেন নম্বর {number}, ডা. {doctor}, আসুন।'` |
| `content.js:77-92` | `toBanglaDigits`, so a Bangla voice reads `৩০৫` rather than three Latin glyphs |

Segment-by-segment meaning — for the recording script, not a legal translation:

| Segment | Bangla | Function | Note |
|---|---|---|---|
| token | `টোকেন নম্বর` + number | "token number" | `টোকেন` is a loanword and is what patients in a Bangladeshi OPD actually hear; an alternative pure-Bangla form (`ক্রম সংখ্যা`) would be a *different, unapproved* wording |
| doctor | `ডা.` + name | honorific + clinician | In Bangla the honorific is `ডা.` (abbreviation of `ডাক্তার`); it is attached to the name, not spoken as a separate word in fast speech |
| destination | `কক্ষ {room}-এ` | "to room {room}" | The locative suffix `-এ` is **glued to the number**, which is the structural reason a Bangla sentence cannot be assembled by concatenating "কক্ষ" + a bare number clip: the number must be recorded in the locative frame, or the suffix must be a separate clip |
| instruction | `আসুন` | "please come" | Sentence-final polite imperative. `আসুন` is the functional equivalent of "please proceed to", but they are not word-for-word interchangeable — which is exactly why the Bangla string needs its own approval |

The `-এ` suffix is the most important constraint on the Bangla clip catalogue (§5.2): a room number must
exist in **two recorded forms** — citation form for display, locative form for speech — or the
composition must slot a locative-frame phrase clip (`কক্ষ …-এ আসুন`) with the number inserted where `-এ`
attaches. Recommendation: three units, `কক্ষ` / number-in-locative-form / `-এ আসুন`, accepting a bounded
set of room values per facility rather than attempting Bangla morphology at runtime.

#### F1.6 Test changes required by F1

| Test | Change |
|---|---|
| `content:32-39` "the approved English template is spoken exactly as OD-3 records it" | Expect `'Token number 4, Dr. Rahim Uddin, please proceed to Room 305.'` |
| `content:41-44` "the templates themselves carry the approved punctuation" | Both `TEMPLATES.en.*` assertions change |
| `content:46-56` "with no room assigned the room clause is dropped" | Expect the approved room-less variant (currently `'Token number 4, Dr. Rahim Uddin.'`); keep the blank-room case (`room: '   '`) |
| `content:85-102` "patient identity cannot reach the spoken text" | Expected string changes; the leak assertions do not |
| `content:111-114` "free text is whitespace-collapsed" | Must now assert **no duplicated honorific**: `'  Dr.  A.   Rahman '` → `'Token number 7, Dr. A. Rahman, please proceed.'`, not `'Dr. Dr. …'` |
| `content:20-30` Bangla template | Unchanged only if the owner ratifies the current Bangla string; otherwise it changes with the approval |
| New | Variant-matrix test: four combinations (doctor × room) each produce a complete, grammatical, honorific-once sentence, and no variant contains `undefined`, `null`, `''` or a double space |

#### F1.7 Acceptance criteria

1. The spoken English sentence equals the owner's sentence verbatim when both doctor and room exist.
2. With no room, the sentence still contains an instruction and no placeholder.
3. With no doctor name, no dangling honorific and no double comma.
4. A doctor name already carrying an honorific is spoken once, not twice.
5. The Bangla sentence is recorded in §5.2's script as an independently approved artefact.
6. All assertions above are unit tests; **no claim of audibility** until a device playback test (§16.4).

#### F1.8 Dependencies

OD-3 wording approval (the room-less and doctor-less variants are **not** currently approved), F4 (room
availability decides which variant is reachable), Stage A.

### 3.2 Finding F2 — playback is reported as successful before it finishes

#### F2.1 Claim

The adapter settles its promise on the **start** event, so a start is treated as delivery. The controller
and operator panel therefore believe an announcement was made when only its first syllable was scheduled.

#### F2.2 Source-level evidence

| Evidence | Content |
|---|---|
| `speech-synthesis.js:33` | `SPOKEN: 'spoken', // the browser reported that speech started` — the outcome is defined as *started* |
| `speech-synthesis.js:244-248` | `const settle = (result) => { if (resolved) return; resolved = true; resolve(result); … }` — the **first** settle wins |
| `speech-synthesis.js:256-267` | `utterance.onstart = () => { … settle({ status: OUTCOME.SPOKEN, … }) }` — therefore `onstart` **is** the success path |
| `speech-synthesis.js:268-276` | `utterance.onend = () => settle({ status: OUTCOME.SPOKEN, … })` — a **no-op**, because `resolved` is already true |
| `speech-synthesis.js:277-289` | `onerror` → `BLOCKED` for `not-allowed`, `CANCELLED` for `canceled`, `ERROR` otherwise |
| `speech-synthesis.js:125` | `startTimeoutMs` defaults to 1500 ms — the only watchdog is a *start* watchdog |
| `speech-synthesis.js:290-300` | Timeout → `{ status: BLOCKED, reason: 'no_start_event' }` |
| `controller.js:209-216` | `result = await adapter.speak(...)` then `record(...)` |
| `controller.js:50-53` | `appliesActivation(...)` grants activation for `SPOKEN` — a *started* utterance proves the gesture worked (defensible) but is conflated with delivery (not defensible) |
| `frontend/lib/i18n.js:216` | `announceLastSpoken: 'played'` — the operator is told it played |
| `…speech.test.mjs:54-55` | The fake engine fires `onstart()` **then** `onend()` synchronously, so no test distinguishes the two |
| `…speech.test.mjs:120-131` | "speaking … reports spoken" asserts `status === SPOKEN` immediately after `await speak(...)` |

There is **no test** anywhere in which `onstart` fires and `onend` never does.

#### F2.3 Consequence chain

`onstart` → `settle(SPOKEN)` → controller records `spoken` → activation granted → panel renders "played"
→ an operator whose screen is muted, or whose utterance was cut off by navigation, or whose engine
stalled after the first word, is told the patient was called. Nothing anywhere distinguishes attempted
from delivered.

#### F2.4 Required correction — one contract for all renderers

A renderer is a function from a *plan* to a *terminal outcome*. **Start is an event, not an outcome.**

| Outcome | Meaning | Produced when |
|---|---|---|
| `started` | audio has begun (informational, **not terminal**) | engine start / first clip `playing` |
| `completed` | playback reached its natural end | speech `onend`; last clip `ended` |
| `failed` | the engine reported an error before completion | speech `onerror` (non-cancel); media `error` with decode/format/network cause |
| `interrupted` | playback began, then stopped for a reason other than our own cancel | speech `interrupted`; media `abort`/`stalled` after start; page unload |
| `cancelled` | **we** stopped it (supersede, dispose, engine switch) | our own `cancel()` path |
| `blocked` | the browser refused to start | `play()` rejection `NotAllowedError`; speech `not-allowed`; start watchdog expiry |
| `busy` | another announcement is in flight | controller-side, before the engine |
| `unavailable` | capability absent (no engine, no assets) | capability probe |
| `skipped` | content or assets could not be resolved | unspeakable token, missing clip, unknown language |
| `duplicate` | suppressed because this event already completed | dedupe store (§3.3) |

**Contract (renderer-agnostic).** `speak(plan | text, options)` resolves **exactly once**, only on a
**terminal** outcome:

```js
// Terminal result shape — identical for every renderer
{
  status: 'completed' | 'failed' | 'interrupted' | 'cancelled' | 'blocked' | 'unavailable' | 'skipped',
  reason: string | null,        // normalized engine code: 'ended' | 'decode_error' | 'not-allowed' | …
  engine: 'local-audio' | 'speech-synthesis' | 'external-tts',
  language: 'bn' | 'en',
  requestedAt: number,          // ms, injected monotonic clock
  startedAt: number | null,
  endedAt: number,
  durationMs: number,           // endedAt - (startedAt ?? requestedAt)
  clipCount: number,            // local audio; 1 for speech
  segments: string[]            // phrase units actually spoken
}
```

Non-terminal progress is published out-of-band — an `onstart`/`onclip` callback or an observable state
field — never by resolving the promise. `speak()` **never rejects**; a throwing engine becomes
`{status:'failed', reason:'engine_threw'}` (already correct in OD-1 and to be retained,
`controller.js:213-216`).

**Mandatory behaviours under the new contract**

1. `onstart` without a terminal event within a **bounded watchdog** → `failed`, `reason:'no_end_event'`
   (watchdog = declared duration + margin, or the existing 1500 ms start watchdog when no start is seen).
   OD-1's `no_start_event` → `blocked` mapping is retained.
2. `onend` without `onstart` → `completed`, `reason:'start_event_missing'` (several Chromium builds skip
   `onstart`); it is **not** `blocked`, because audio demonstrably ran to the end.
3. Web Speech error-code normalisation:

| `SpeechSynthesisErrorEvent.error` | Terminal outcome |
|---|---|
| `canceled` | `cancelled` if we cancelled, else `interrupted` |
| `interrupted` | `interrupted` |
| `not-allowed` | `blocked` (reason `not-allowed`) |
| `audio-busy` | `busy` |
| `synthesis-failed`, `synthesis-unavailable`, `language-unavailable`, `voice-unavailable` | `failed` |
| `network` | `failed` (reason `network`) |
| anything else | `failed` |

4. On dispose or supersede the in-flight promise settles `cancelled` **before** `dispose()` returns, so no
   attempt is leaked (`speech-synthesis.js` already cancels; only the label changes).

#### F2.5 Equivalent completion semantics for the local audio engine

The local engine plays a **sequence** of short clips, so "completed" has a stronger meaning: *every* clip
in the plan reached its natural end and no clip was skipped. The mapping from `HTMLAudioElement` /
Web Audio events:

| Engine event / condition | Outcome | Reason |
|---|---|---|
| first clip `playing` | `started` (informational) | — |
| every clip `ended`, in order | `completed` | `ended` |
| `error` with `MediaError.code === MEDIA_ERR_DECODE` | `failed` | `decode_error` (corrupt asset — §7.5) |
| `error` with `MEDIA_ERR_SRC_NOT_SUPPORTED` | `failed` | `format_unsupported` |
| `error` with `MEDIA_ERR_NETWORK` | `failed` | `asset_unreachable` (offline and not cached) |
| `error` with `MEDIA_ERR_ABORTED` while we cancelled | `cancelled` | `aborted` |
| `error` with `MEDIA_ERR_ABORTED` while we did not | `interrupted` | `aborted_externally` |
| `play()` rejects `NotAllowedError` | `blocked` | `not-allowed` (autoplay policy) |
| `play()` rejects `NotSupportedError` | `failed` | `format_unsupported` |
| `stalled`/`suspend` after start beyond watchdog | `interrupted` | `stalled` |
| declared duration + margin elapses without `ended` | `failed` | `no_end_event` |
| a resolved clip id has no asset | `skipped` | `asset_missing` (whole plan refusals: never a partial sentence is a *decision* — see §8.4) |

Two rules make this testable without real audio:

1. Duration is **declared** by the manifest per clip, so the watchdog is deterministic and the sequence
   length is known before playback starts.
2. The engine receives an injected `createAudio(url)` factory and `timers`, exactly as the speech adapter
   receives `synth`/`timers` (`speech-synthesis.js:110-126`). A fake audio element can therefore emit
   `playing`/`ended`/`error` in any order in a unit test.

**Sequence rule (decision, needs no owner input):** a plan is spoken *in full or not at all*. If any clip
in the plan is missing or corrupt, the engine must **not** speak a partial sentence (a token number with
no room is a different, approved variant — a sentence missing its middle is not). It returns `skipped`
with the missing ids and the controller records it as a failed attempt.

#### F2.6 How the controller receives and records these outcomes

`record()` (`controller.js:32-50` region) is extended, not replaced:

```js
// last = { status, reason, language, engine, eventKey, source,
//          requestedAt, startedAt, endedAt, durationMs, clipCount, segments }
```

| Terminal outcome | `last` shown to the operator | Dedupe effect | Retry |
|---|---|---|---|
| `completed` | "Announced" | key marked **completed** | none |
| `failed` | "Audio failed — check sound" + reason | key stays **attempted** (releasable) | bounded (§3.3) |
| `interrupted` | "Interrupted" | releasable, single automatic retry | 1 |
| `cancelled` | "Replaced" (no alarm) | neither completed nor failed | none |
| `blocked` | "Sound is blocked — tap to enable" | releasable; **no** retry until a gesture | on activation |
| `busy` | "Busy — retried" | releasable | 1 automatic, then drop |
| `unavailable` / `skipped` | "Cannot announce (reason)" | releasable | none |

Activation (`ACTIVATION.GRANTED`) may still be inferred from `started`, because the gesture demonstrably
produced audio; **success** is inferred only from `completed`. These are two different flags in `state`,
not one status string.

#### F2.7 Test changes required by F2

| Test | Change |
|---|---|
| `speech.test.mjs:120-131` "…reports spoken" | Split into: `onstart` → promise still pending, `last.phase === 'started'`; then `onend` → `completed` |
| `speech.test.mjs:148-160` "silence is not success" | Retained; `no_start_event` still maps to `blocked` |
| `speech.test.mjs:171-179` "a cancelled utterance is reported as cancelled" | Retained, plus a new case: cancel **after** start (currently impossible to express, because the promise already resolved) |
| New | `onstart` then `onerror('synthesis-failed')` → `failed`, not `completed` |
| New | `onstart` then nothing → watchdog → `failed`, `reason:'no_end_event'` |
| New | `onend` without `onstart` → `completed`, `reason:'start_event_missing'` |
| New | `onerror('audio-busy')` → `busy`; `language-unavailable` → `failed` |
| New (local engine) | full sequence `ended` → `completed` with `clipCount === plan.length` |
| New (local engine) | corrupt clip mid-sequence → `skipped`, **nothing after it plays**, `segments` lists only what played |
| `controller.test.mjs:74-116` (dedupe group) | Re-expressed against attempt states (§3.3) |
| `controller.test.mjs:181-197` "outcomes are observable without leaking the spoken text" | Extended: the record must carry `engine`, `durationMs` and no spoken text |

#### F2.8 Acceptance criteria

1. No code path resolves a successful outcome on a start event.
2. `completed` is reachable only from a terminal engine event.
3. `failed`, `interrupted`, `cancelled` and `blocked` are distinguishable in both the adapter result and
   the controller record.
4. A never-ending playback is bounded by a watchdog and reported `failed`.
5. The operator caption never says "played" for anything other than `completed`.
6. Unit tests above pass; **audibility remains unverified** until §16.4.

#### F2.9 Dependencies

None on the owner. It is a prerequisite for F3 (success vs attempt) and for the local engine (Stage C),
because both need one outcome vocabulary.

### 3.3 Finding F3 — duplicate suppression remembers only the most recent event

#### F3.1 Claim

Suppression is a **single slot**: one event key, one timestamp, consumed *before* the announcement is
attempted. Two consequences — an earlier event is re-announced after any intervening event, and a
failed/blocked announcement stays marked as though it had been announced.

#### F3.2 Source-level evidence

| Evidence | Content |
|---|---|
| `controller.js:32` | `const DEFAULT_DEDUPE_WINDOW_MS = 5000;` |
| `controller.js:62-63` | `let lastEventKey = null; let lastEventAt = 0;` — one key, one timestamp |
| `controller.js:195-202` | check, then **overwrite** the slot, then fall through to playback |
| `controller.js:204-207` | `return record({ status: 'needs_activation' }, …)` — returns **after** the key was consumed |
| `controller.js:211` | `result = await adapter.speak(...)` — nothing rolls the key back on failure |
| `controller.js:213-216` | errors become `record({status:'error'})`; the slot still holds the key |

The block verbatim (`controller.js:195-202`):

```js
if (source === 'event' && key) {
  const at = now();
  if (lastEventKey === key && (at - lastEventAt) < dedupeWindowMs) {
    return record({ status: 'duplicate' }, content, input, source, lang);
  }
  lastEventKey = key;
  lastEventAt = at;
}
```

#### F3.3 Three distinct defects

1. **Single-slot memory loses history.** Trace with the default 5 s window: `call(A)` announced at `t=0`
   and completes; `call(B)` announced at `t=2s` (slot now holds `B`); a duplicate delivery of `call(A)`
   arrives at `t=3s`. The comparison is against `B`, so **`A` is announced a second time** — inside the
   very window meant to suppress it. Any interleaved event defeats suppression for everything except the
   immediately preceding one.
2. **The key is consumed before the attempt.** A `needs_activation` refusal (`:206`) or an adapter error
   (`:213`) leaves the key in the slot, so the *next* legitimate delivery of the same event is suppressed:
   a failed announcement is remembered as if it had succeeded and the patient is never called.
3. **No distinction between attempt and delivery.** The store records *that a key was seen*, not *what
   happened*, so retry, exhaustion and operator-visible failure have no representation. F2's
   `completed`/`failed` split is a prerequisite for fixing this.

The window is also a *time* window only: two different events inside it are both announced (correct), and
the same event outside it is announced again (correct only if the re-delivery delay is truly bounded —
which is why the window must exceed the plausible re-delivery delay, and why a genuine recall must be a
*different* event key).

#### F3.4 Required correction — a bounded, event-keyed deduplication store

Replace the two scalars with a `Map` keyed by the announcement event key
(`content.js:140-155` `announcementEventKey`, which already yields `entry:<id>:<action>:<revision>` or
`event:<id>`). Because the key contains the action **and** the revision, a recall is a *different* event
and is never suppressed by its own preceding call — the store need not reason about intent.

```js
// One record per event key. state is the only source of truth for "was it announced?"
{
  key,            // entry:<queueEntryId>:<action>:<revision>  |  event:<eventId>
  state,          // 'attempting' | 'completed' | 'failed' | 'blocked' | 'interrupted' | 'exhausted'
  attempts,       // terminal attempts, not counting 'attempting'
  firstAttemptAt,
  lastAttemptAt,
  completedAt,    // set only when state === 'completed'
  expiresAt,      // completedTtlMs after completedAt, or failureTtlMs after lastAttemptAt
  lastReason      // normalized reason from F2 (never the spoken text)
}
```

**Policy (engineering recommendation — the numbers require owner ratification, §18 O-5):**

| State | Duplicate delivery of the same key | Expiry |
|---|---|---|
| `attempting` | queued behind the in-flight attempt (`busy`), never overlapped | attempt watchdog (F2.5) |
| `completed` | **suppressed** with `duplicate` | `completedTtlMs`, default **10 minutes** |
| `failed` / `interrupted` | retry allowed once `minRetryIntervalMs` elapsed, up to `maxAttempts` (default 3), then `exhausted` | `failureTtlMs`, default 60 s |
| `blocked` | suppressed **until activation is granted**, then one automatic retry | `blockedTtlMs`, default 10 minutes |
| `exhausted` | suppressed; surfaced as "cannot announce — use Recall" | `failureTtlMs` |

- **Why 10 minutes for `completed`** (up from 5 s): a re-delivery can arrive after a page refresh, a
  Realtime/WebSocket reconnect or a poll retry — all of which can exceed 5 s. Ten minutes also covers an
  operator who re-sends after seeing a stale board. A *genuine* re-call is a `recall` action with a new
  revision, i.e. a new key, so a long window never blocks legitimate repetition.
- **Memory bound:** `maxKeys` default **512**, lazy sweep on each insert (expired entries dropped) plus
  deterministic eviction when full: `completed` first (earliest `expiresAt`), then oldest
  `lastAttemptAt`. `attempting` is never evicted. 512 keys is a few tens of KB.
- **Retry backoff:** `minRetryIntervalMs = min(5000 * 2 ** (attempts - 1), 30000)`; never a tight loop.
- **Cancelled** (superseded) attempts do **not** count as attempts and set no expiry — the newer event is
  the one that should be heard.
- **Operator announcements** (`source: 'operator'`) continue to bypass suppression (correct today; test
  `an operator repeat is deliberate and bypasses suppression` must stay green) but are still recorded for
  observability.
- **Clock injection is mandatory** so tests are deterministic — `now()` is already an option on the
  factory; the store must not call `Date.now()` directly.
- **No timers.** Expiry is evaluated on read and swept on write; a background timer would keep a kiosk
  page awake and add a failure mode to a screen that runs for a whole shift.

#### F3.5 How the principles carry into the local-audio architecture

1. The store stays in the **controller**, not the renderer, so switching engine never changes duplicate
   behaviour (the current engine-agnostic seam at `controller.js:45-47` is what makes this cheap).
2. The store is only accurate if the renderer reports **terminal** outcomes (F2). A renderer that resolves
   at start would mark an event `completed` before anything was heard — the two findings are coupled.
3. When a fallback engine takes over a failed attempt (Stage E), it must update the **same** record
   (`attempting` → `completed`), never create a second record: a fallback must not be able to announce the
   same event twice.
4. The store is per-client. Cross-client suppression (ANN-005: a second display in the same waiting room)
   needs the server-side event contract (ANN-002) and is explicitly **out of scope** here.

#### F3.6 Test changes required by F3

| Test | Change |
|---|---|
| `controller:74-85` "the same queue event is spoken once" | Retained (single-event case) |
| `controller:86-97` "…announced again after the suppression window" | Window is now 10 min for `completed`; advance the injected clock accordingly |
| `controller:98-107` "a different event is never suppressed" | Retained |
| `controller:108-116` operator bypass | Retained |
| New | **Interleaved replay:** A completed, B announced, A delivered again inside the window → `duplicate`, `calls.speak.length === 2` |
| New | **Failure is releasable:** adapter returns `failed`; the same key delivered again after `minRetryIntervalMs` is spoken; after 3 attempts → `exhausted` and suppressed |
| New | **Blocked waits for a gesture:** `blocked` → same key re-delivered before activation is `duplicate`/suppressed; after `activate()` it is spoken once |
| New | **Bounded memory:** insert 600 distinct keys; the store never exceeds 512 and `completed` entries are evicted before `attempting` |
| New | **Expiry sweep:** an entry past `expiresAt` no longer suppresses |
| New | **Cancelled is not an attempt:** superseded key can be re-announced immediately |

#### F3.7 Acceptance criteria

1. An earlier event re-delivered after an intervening event is suppressed inside the window.
2. A failed or blocked announcement is never permanently marked as announced.
3. Retry is bounded, spaced and observable; exhaustion is surfaced to the operator.
4. The store is bounded in memory and needs no background timer.
5. All of the above are unit tests over an injected clock.

#### F3.8 Dependencies

F2 (terminal outcomes), ANN-002 (stable event identity across clients, for Stage D+), Stage A.

### 3.4 Finding F4 — room information is unavailable to the announcement

#### F4.1 Claim

No queue payload carries a room, so the approved sentence can never be spoken in full. The frontend already
passes `room: entry.room` — a property that does not exist on any queue response — and the content module
therefore always takes its room-less branch and marks the result `derived: true`.

#### F4.2 The complete data path, hop by hop

| Hop | Evidence | Room present? |
|---|---|---|
| `QueueEntry` model | `backend/common/models.py:854-884`; `appointment_id` at `:866` (nullable); `patient_id`, `doctor_id`, `branch_id`, `date`, `position`, `token`, `status` | **No room column at all** |
| Serializer | `backend/queuing/main.py:82-92` `_entry_to_dict` | No room field |
| Queue list | `backend/queuing/main.py:137-151` adds `patient_name`, `doctor_name` from a batch map | No room |
| Action responses | `_entry_to_dict` reused at `main.py:269` (check-in), `:361`, `:456`, `:583` | No room |
| Check-in write | `main.py:230-238` creates the entry with `appointment_id=appt.id` and copies **nothing** about location | Room exists upstream, is not carried |
| Enqueue write | `main.py:293` (`enqueue_patient`) sets `appointment_id=None` | **Walk-ins have no room source whatsoever** |
| Frontend trigger | `frontend/pages/queue.js:64-65`: `// No queue endpoint returns a room yet; omitted rather than invented.` then `room: entry.room` | `undefined`, always |
| Content | `content.js:117-119` — no room ⇒ `noRoom` template, `fields.derived = true` (`:104-106`) | Clause dropped |
| Operator panel | `QueueAnnouncements.js:71-76` preview shows the room-less sentence | — |

#### F4.3 Where the authoritative room actually lives

| Candidate source | Evidence | Verdict |
|---|---|---|
| **Appointment location snapshot** — `appointments.room_id`, `room_name`, `floor_name`, `department_name`, `.location_source` | `backend/common/models.py:616-630`; the model comment at `:621-624` states these are "a snapshot of the location at booking time … rewriting the current one would lose where the patient was actually told to go" | **AUTHORITATIVE for an appointment-backed queue entry** |
| Serialized snapshot | `_location_label(a)` `backend/appointment/main.py:238-241`; `_appt_to_dict` emits `room_id`, `room_name` at `:278` | Already exposed on the appointment API |
| Live schedule session room | `ScheduleSession.room` `models.py:555-570`; `DoctorBranch.room` `:439-440` | **MUST NOT be used.** This is *current* schedule truth; using it would silently rewrite where an already-queued patient was told to go — exactly the business rule the snapshot exists to prevent |
| Branch/chamber master data | facility/room tables via `room_in_branch()` (`backend/doctor/profile.py:254-266`) | Only for *validating a newly chosen* room, never for deriving an existing one |

**Business rule (restated, and it governs this whole section):** an existing queue entry's room is the room
the patient was told at booking/check-in. It is never re-derived from the doctor's current schedule,
current chamber, or the branch's current room list.

#### F4.4 Required correction — two options, recommended in sequence

**Option R1 — read-through (no migration; recommended for Stage A).**
The queue serializer resolves the room from the queue entry's **appointment snapshot**:

```python
# backend/queuing/main.py — _entry_to_dict gains an optional, resolved room
def _entry_to_dict(e, room=None):
    ...  # unchanged fields
    "room_id": (room or {}).get("room_id") or "",
    "room_name": (room or {}).get("room_name") or "",
    "location_label": (room or {}).get("label") or "",
    "room_source": (room or {}).get("source") or "",   # 'appointment_snapshot' | 'walk_in_capture' | ''
```

Callers (`get_queue` `:137-151`, `:269`, `:361`, `:456`, `:583`) pass a room resolved **in one batch**,
not per row:

```python
# one query for the whole page, mirroring the existing pnames/dnames batch pattern
rooms = {a.id: {"room_id": a.room_id, "room_name": a.room_name,
                "label": _location_label(a), "source": "appointment_snapshot"}
         for a in session.query(Appointment)
             .filter(Appointment.id.in_(appt_ids)).all()}
```

`_location_label` is reused from `backend/appointment/main.py:238-241` (or moved to a shared helper) so the
queue and the appointment API cannot disagree about how a location reads.

- Appointment-backed entries get a room. Walk-ins (`appointment_id is NULL`) get `room_source: ''` and
  announce the room-less variant — honest, and identical to today's output, but now explicit.
- Additive and backward compatible: three string fields plus one provenance field; no client breaks.

**Option R2 — snapshot onto the queue entry (migration; recommended for Stage B/A2).**
Add to `queue_entries`: `room_id String(36) NULL`, `room_name String(120) NULL`,
`location_source String(32) NULL` (reusing the naming already in `appointments`), then:

1. `check_in_appointment` (`main.py:230-238`) **copies** the appointment snapshot onto the entry at creation
   (`room_id=appt.room_id`, `room_name=appt.room_name`, `location_source='appointment_snapshot'`) — a copy,
   never a re-derivation, so the queue keeps its own immutable record of where the patient was sent.
2. `enqueue_patient` (`main.py:284-300`) accepts an optional `room_id`; when supplied it is validated with
   `room_in_branch(...)` (org + branch + active) and the name is copied in with `location_source='walk_in_capture'`.
   When omitted, the entry announces the room-less variant.
3. Backfill for existing rows: `UPDATE queue_entries SET room_* = (SELECT room_* FROM appointments WHERE
   id = queue_entries.appointment_id)` for appointment-backed rows only. **The backfill reads the
   appointment snapshot, never `schedule_sessions`.** Pre-existing walk-ins stay `NULL`.
4. `_entry_to_dict` then reads the entry's own columns, so all five call sites get the room for free.

R2 is the better long-term contract (the queue entry becomes its own evidence record; walk-ins can be
announced with a room; the serializer stops depending on a nullable FK). R1 is the cheaper way to make the
approved sentence speakable this cycle. **They are not mutually exclusive**: ship R1 now, R2 as a later
migration whose read path supersedes R1's join.

#### F4.5 Frontend contract

```js
// frontend/pages/queue.js — replace the dead 'entry.room'
room: entry.room_name,          // '' when the appointment had no room
roomSource: entry.room_source,  // 'appointment_snapshot' | 'walk_in_capture' | ''
```

`buildAnnouncement` keeps its rules (`content.js:106-124`): a blank or whitespace-only room is *no room*
(`:119`) and `fields.derived` records the shortened sentence. The plan builder (§4.3) emits the `room`
segment only when `hasRoom`.

#### F4.6 Behaviour when no room was assigned

1. Announce the **approved room-less variant** (§3.1 F1.4 variant 2) — never "Room", never "Room 0", never
   a silently substituted current chamber.
2. Record `reason: 'no_room'` on the attempt (observable, §8.6) and show it in the panel caption so the
   operator knows why the sentence is shorter.
3. Surface it at the source: the queue row/panel indicates "no room on this appointment", so the front desk
   can fix the appointment rather than wonder why the announcement is incomplete.

#### F4.7 Authorization and privacy boundaries

- The room rides inside the **existing** queue authorization: `get_queue` and the action routes already
  enforce organization scoping, `branch_accessible(auth, …)` and doctor/assistant assignment
  (`main.py:120-160`, `:190-230`, `:330-360`). No new endpoint is introduced, so no new gate has to be
  invented — the safest possible outcome for a tenant-scoped field.
- A room is facility information, not patient information: adding it to the staff queue payload widens no
  PII surface, and the announcement payload gains no new identifier (§11.2).
- **The public DQDS board is a different surface with its own decision** (DQD-002 / OD-4). Nothing here
  authorises showing a room on the public display; the PQV decision governs that
  (`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md:57-67`: "token numbers and operational state").
- `appointment_id` stays server-side: the announcement payload must not carry it — it is not needed to
  speak, and it would put an internal identifier into client logs.

#### F4.8 Acceptance criteria

1. A queue entry created from an appointment whose snapshot is Room 305 announces Room 305.
2. Changing the doctor's current schedule/chamber room to 401 afterwards does **not** change that entry's
   announcement (**the historical-correctness test**, §16.1 item 6).
3. An appointment booked with no room announces the room-less variant with `reason: 'no_room'`.
4. A walk-in announces the room-less variant until room capture exists (R1), or its captured room (R2).
5. A foreign organization's queue request still receives the same 404/403 as today; no room leaks.
6. Batch resolution: `get_queue` for N entries issues a constant number of queries (no N+1).

#### F4.9 Dependencies

R1: nothing beyond Stage A. R2: a migration, `room_in_branch` reuse, and a walk-in room-capture UI decision
(which rooms an operator may pick is a small UX decision, not an owner policy). Announcing a room also
depends on the Bangla locative clip strategy (§5.2).

#### F4.10 What this finding does *not* require

No change to `QueueEntry`'s identity or to the position/reorder logic. No change to the public tracking
page. No change to appointment booking. The only writes are (R2) three nullable columns and their
population at two already-existing creation points.

---

## 4. Proposed local audio architecture

### 4.1 The three layers

```
                 queue event (call / recall / operator)
                                │
                                ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 1. COMPOSITION  lib/announcements/plan.js   (pure, no DOM)    │
  │    event + language + available fields  →  AnnouncementPlan   │
  │    { language, eventKey, segments[], clipIds[], gapsMs[],     │
  │      text (script, for preview/tests), hasRoom, hasDoctor }   │
  └──────────────────────────────────────────────────────────────┘
                                │  same plan, three possible renderers
             ┌──────────────────┼───────────────────────────┐
             ▼                  ▼                           ▼
   ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
   │ local-audio      │ │ speech-synthesis │ │ external-tts (optional) │
   │ PRIMARY          │ │ OPTIONAL ALT     │ │ OPTIONAL FALLBACK       │
   │ clips + manifest │ │ Web Speech API   │ │ backend proxy           │
   └──────────────────┘ └──────────────────┘ └────────────────────────┘
             └──────────────────┼───────────────────────────┘
                                ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ 3. CONTROLLER  lib/announcements/controller.js               │
  │    dedupe store (F3) · single in-flight · activation ·       │
  │    retry/backoff · last outcome (F2) · engine selection      │
  └──────────────────────────────────────────────────────────────┘
                                │
                                ▼
        operator panel status · optional attempt log (ANN-008)
```

The **renderer contract** is the seam that makes this work:

```js
{
  id: 'local-audio' | 'speech-synthesis' | 'external-tts',
  isSupported(),                 // synchronous capability probe
  capability({ language }),      // { status, detail } for the panel
  prepare(plan),                 // optional: verify assets/credentials before playing
  async speak(planOrText, opts), // resolves once, terminal outcome only (F2.4)
  cancel(reason),                // settles an in-flight attempt as 'cancelled'
  isSpeaking(),
  dispose()
}
```

`controller.js:45-47` already accepts an injected adapter with `speak`, so the interface is additive:
`speech-synthesis.js` is wrapped, not rewritten, and keeps its voice-selection tests.

### 4.2 Composition plan — the new unit

```js
// English, doctor and room present, token serial 4, room 305
{
  language: 'en', eventKey: 'entry:qe-1:call:2',
  segments: ['token_number', 'doctor', 'proceed_to', 'room'],
  clipIds: ['en/phrase/token_number', 'en/num/4',
            'en/phrase/doctor_prefix', 'en/doctor/<doctorId>|en/name_fallback',
            'en/phrase/please_proceed_to', 'en/phrase/room', 'en/num/305'],
  gapsMs: [0, 120, 160, 0, 140, 120, 0],
  text: 'Token number 4, Dr. Rahim Uddin, please proceed to Room 305.',
  hasRoom: true, hasDoctor: true
}
```

The Bangla plan has the same shape with `segments: ['token_number','doctor','room_locative','come']` and
`clipIds: ['bn/phrase/token_number','bn/num/4','bn/phrase/doctor_prefix','bn/phrase/kokho',
'bn/room_loc/305','bn/phrase/ase_asun']`.

A plan is **declarative**: it names clips, not sounds, so it is unit-testable with no audio, renderable by
any engine, and diffable when the catalogue version changes. `text` exists for the operator preview, the
content tests and the external-TTS fallback — the local engine never reads it.

### 4.3 Composition rules

1. **Segment order is fixed per language**: `token_number → doctor → proceed_to → room` (en);
   `token_number → doctor → kokho → room_locative → ase_asun` (bn).
2. **Absent optional field ⇒ absent segment.** No placeholder clip, no silence where a word should be.
3. **Doctor clip precedence:** a per-doctor recording (`bn/doctor/<id>`) replaces the
   `doctor_prefix + name` pair entirely; failing that, a per-doctor recorded-name entry (§5.4); failing
   that, the segment is omitted if configuration permits (§18 O-2).
4. **Numbers are never digit-concatenated** (§6).
5. **Refusal beats fabrication:** an unspeakable token yields `skipped/unspeakable_token`, an unknown
   language `skipped/unsupported_language` (existing behaviour, retained).
6. **Only allow-listed fields can reach a plan**: `token`, `doctorName`/`doctorId`, `room` (§11.2).

### 4.4 Engine selection policy (default, per language)

| Language | Primary | Permitted alternates | Never |
|---|---|---|---|
| `bn` | `local-audio` | `external-tts` **only if** the facility enabled it *and* its Bangla voice passed the listening test (§10.3) | browser `speech-synthesis` as an automatic substitute; any automatic language switch |
| `en` | `local-audio` | `speech-synthesis` (a local `en-*` voice), then `external-tts` if enabled | a network voice when a local voice exists (OD-1 rule retained) |

Selection is **explicit and observable**: the panel states which engine spoke, and a fallback is presented
as a fallback (OD-1's honesty rule at `speech-synthesis.js:128-131`, generalised to engines).

### 4.5 Proposed file layout

| Path | Status | Purpose |
|---|---|---|
| `lib/announcements/content.js` | **modified** | wording (F1), event key (retained), token serial (retained) |
| `lib/announcements/plan.js` | **new** | composition: event + fields → plan (§4.2) |
| `lib/announcements/engine.js` | **new** | renderer interface + selection policy (§4.1, §4.4) |
| `lib/announcements/local-audio.js` | **new** | clip sequencer, manifest resolution, watchdog (F2.5) |
| `lib/announcements/assets.js` | **new** | manifest load, integrity check, cache probe, install (§7) |
| `lib/announcements/dedupe.js` | **new** | bounded event store (F3.4) |
| `lib/announcements/controller.js` | **modified** | outcome recording (F2.6), store wiring, engine selection |
| `lib/announcements/speech-synthesis.js` | **modified** | terminal-outcome contract (F2.4); voice logic retained |
| `components/queue/QueueAnnouncements.js` | **modified** | outcome vocabulary, asset/engine status, install action |
| `pages/queue.js` | **modified** | room field (F4.5), optional trigger widening (Stage D) |
| `public/audio/announcements/**` | **new assets** | clips + `manifest.json` (§7.2) |
| `public/sw.js` | **new** | cache-first asset service worker (§7.3) |

`frontend/public/` is currently **empty** and there is no service worker or web-app manifest anywhere in
the tree (verified), so the asset layer is purely additive.

### 4.6 Event flow for a call (as designed, not implemented)

1. Operator presses Call (today: `queue.js:202`) → `POST /api/v1/queue/{id}/action {action:'call'}`.
2. The queue route performs the transition and audit **without touching audio** (`main.py:400-470`). It
   responds 200 with the entry.
3. The frontend, holding the response (or a future server event, ANN-002), builds
   `{queueEntryId, action:'call', revision, token, doctorName, room}`.
4. `controller.announce({source:'event'})` → dedupe store (§F3.4) → plan (§4.2) → engine (§4.4).
5. The terminal outcome updates the panel and, if enabled, an attempt log (ANN-008).
6. **Nothing in steps 3–5 can change, delay or roll back step 2.** The call is committed before audio is
   considered; a total audio failure leaves the call standing and visible on every board.

---

## 5. Audio asset catalogue

### 5.1 Fixed phrase clips

Every phrase clip is recorded **once per language per voice**, scripted exactly, and reused for ever. Ids
are stable; the catalogue version bumps when a recording is replaced.

**English (`en-GB`)** — recorded mid-sentence, so no falling sentence-final intonation:

| id | Script | Notes |
|---|---|---|
| `en/phrase/token_number` | "Token number" | spoken with a slight comma pause after |
| `en/phrase/doctor_prefix` | "Doctor" | the abbreviation "Dr." is *spoken* "Doctor"; do not record "D-R" |
| `en/phrase/please_proceed_to` | "please proceed to" | **the phrase missing today** (F1) |
| `en/phrase/room` | "Room" | `en-GB` pronunciation |
| `en/phrase/please_proceed` | "please proceed" | room-less variant (§18 O-3) |
| `en/phrase/attention` | "Attention please" | optional pre-roll for a noisy waiting room |
| `en/phrase/repeat` | "I repeat" | optional pre-roll on the first retry |

**Bangla (`bn-BD`)** — a **separate script**, not a translation of the English:

| id | Script | Notes |
|---|---|---|
| `bn/phrase/token_number` | "টোকেন নম্বর" | loanword, as patients hear it (§3.1 F1.5) |
| `bn/phrase/doctor_prefix` | "ডাক্তার" / "ডা." | record the full "ডাক্তার" for clarity, let the join be shortened by the gap, or record both and choose by config |
| `bn/phrase/kokho` | "কক্ষ" | "room"; must be followed by a **locative** number (§5.2) |
| `bn/phrase/room_frame` | "কক্ষ …-এ আসুন" | the frame alternative to `kokho` + locative number (§5.2) |
| `bn/phrase/ase_asun` | "আসুন" | polite imperative; the functional equivalent of "please proceed" |
| `bn/phrase/ase_asun_roomless` | "আসুন" (room-less variant) | identical audio, separate id so the two variants can diverge without re-cutting `ase_asun` |

### 5.2 The Bangla locative constraint (the catalogue's hardest problem)

In Bangla the destination is `কক্ষ ৩০৫-এ` — the locative suffix `-এ` **attaches to the number**. A bare
cardinal clip ("তিনশ পাঁচ") followed by a separate "-এ" clip is intelligible but sounds broken, and a
cardinal inserted before `কক্ষ …-এ আসুন` is ungrammatical ("কক্ষ তিনশ পাঁচ-এ আসুন" instead of
"কক্ষ ৩০৫-এ আসুন").

Two workable strategies:

| Strategy | How | Cost | Recommendation |
|---|---|---|---|
| **A. Locative room recordings** | Record each room number in locative form (`bn/room_loc/305` = "৩০৫-এ") for the facility's actual room set | One clip per room per facility; a facility with 40 rooms needs 40 clips | **Recommended** — rooms are a bounded, slowly-changing set, and this is the only option that always sounds right |
| **B. Frame clip** | Record `কক্ষ …-এ আসুন` with the number gap in the middle; the number clip is inserted in citation form | One frame clip + the normal number clips; sounds slightly formal, and only works because the frame carries the suffix | Acceptable interim, requires listening approval |

**Token numbers** are unaffected: they are announced in citation form ("টোকেন নম্বর ৪") and always use the
number clips of §5.3. The result is that a Bangla plan may draw a token number and a room number from two
different clip families — which is precisely why the plan (§4.2) is a list of clip ids, not a sentence.

### 5.3 Number recordings

The unit of a number is a **spoken word group**, never a digit.

**English** — `en/num/0` … `en/num/19` (20 clips), `en/num/20,30,…,90` (8 clips), `en/num/hundred`,
`en/num/thousand`, `en/num/oh` (for "oh-five" style rooms if the facility prefers it — off by default).

- 21–99 compose as *tens + unit* ("twenty" + "one"), with a **reduced gap** (~60 ms) and no re-recording of
  every value.
- Hundreds compose as *unit + "hundred" + unit* ("three hundred" + "five"). **`en-GB` includes "and"**
  ("three hundred and five"), so a `en/num/and` clip is required if the facility's locale is `en-GB` and the
  script is the British form. This is a one-line config choice (`hundredsStyle: 'with_and' | 'without_and'`),
  but the *clips* for both must exist.
- Above 999: not expected for token serials or room numbers; the plan falls back to `skipped/range` rather
  than speaking a plausible-sounding wrong number (§6.4).

**Bangla** — `bn/num/0` … `bn/num/99` (100 clips), `bn/num/100,200,…,900` (9 clips), `bn/num/thousand`.

- Bangla cardinals below 100 are largely **irregular** (একুশ, বাইশ, ত্রিশ …), so composition below 100 is
  not credible and must not be attempted: record 0–99.
- 101–999 compose as *hundreds + remainder* ("তিনশ" + "পাঁচ"), which is correct and natural.

### 5.4 Doctor-name recordings (optional)

| Aspect | Design |
|---|---|
| Per-doctor clip | `bn/doctor/<doctorId>` and `en/doctor/<doctorId>` — the **full spoken name including the honorific**, because a recording of a real clinician saying their name naturally includes it. When present, `doctor_prefix` is **not** played (§4.3 rule 3). |
| Who records | The doctor (a self-recorded clip is both cheapest and most respectful of pronunciation), captured through a staff-accessible "record my name" action on the doctor profile. |
| Consent | A doctor-name recording is staff personal data. It is opt-in, revocable, and its presence is recorded. Deleting the clip reverts to the prefix+name fallback. |
| Fallback order | (1) doctor clip, (2) per-doctor transliteration entry in a pronunciation table (`doctor_pronunciation`), (3) omit the segment if config permits, (4) otherwise refuse with `skipped/doctor_name_not_announceable`. |
| Why a pronunciation table matters | `Doctor.name` is free text and may be Latin-script ("Rahim Uddin") while the Bangla plan needs Bangla words. Speaking Latin text with a Bangla voice produces nonsense, which is why OD-1's `missing_doctor_name` refusal exists and why an explicit transliteration is the honest fix. |
| Volume | A doctor clip is concatenated with other clips, so it must be recorded to the **same loudness standard** (§5.7) or the announcement will jolt. |

### 5.5 Pauses and transitions

| Element | Design |
|---|---|
| Silence between segments | Explicit `gapsMs` in the plan (typical 120–180 ms; ~60 ms inside a composed number), scheduled by the engine, **not** baked into each clip (baked-in silence cannot be varied and drifts with codec padding) |
| Lead-in | 150 ms before the first clip so the first syllable is never clipped by a device that is waking its audio path |
| Tail | 300 ms of silence after the last clip before the next event may start; also prevents two announcements from running together |
| Optional pre-roll | `en/phrase/attention` / `bn/phrase/attention` for a noisy room; config, off by default |
| Repeat marker | `repeat` clip on a retried attempt so a patient hearing it twice knows it is deliberate |

### 5.6 Pronunciation variants

| Variant | Why | How it is selected |
|---|---|---|
| `hundredsStyle` | `en-GB` "three hundred **and** five" vs `en-US` "three hundred five" | facility language locale (config), never per-call |
| `roomWord` | "Room" vs "Cabin"/"Chamber" — a Bangladeshi facility may prefer "কেবিন" in Bangla | facility config; both clips shipped |
| `doctorHonorific` | "ডাক্তার" (full) vs "ডা." (clipped) in Bangla | facility config; both clips shipped |
| `tokenWord` | "টোকেন" vs "ক্রম" | **not shipped** until the wording is approved; adding an unapproved synonym is a wording change, not a pronunciation variant |
| Per-doctor name | §5.4 | per-doctor data |
| Digits as words | "three oh five" vs "three hundred five" for rooms | `roomReadAs: 'number' | 'digits'`, default `number`; `digits` needs `en/num/oh` and is discouraged |

Every variant is a **separate clip id plus a config key**, so the engine never guesses and the catalogue
version records exactly which variants exist.

### 5.7 Recording production standard

1. One voice per language per facility (voice talent chosen by the facility; Bangla must be a native
   `bn-BD` speaker). Mixing voices mid-sentence is a defect, not a feature.
2. Master: 48 kHz / 24-bit WAV, single microphone, consistent distance, no music, no reverb, no compression.
3. Delivery: mono, trimmed to ±10 ms of the first/last phoneme, normalised to a consistent loudness
   (≈ −16 LUFS integrated, peak ≤ −1 dBTP) so segments do not jolt.
4. Phrase clips are read **mid-sentence** (no sentence-final falling tone) except the final `আসুন` /
   "please proceed" clip which carries the sentence ending.
5. Numbers are read in isolation, evenly paced; the same speaker reads every value in one session.
6. Reject-and-re-record criteria: clipping, plosive pops, room echo, audible breath before the phrase,
   inconsistent pace, or a Bangla number read with an Indian/Bangladeshi regional accent mismatch to the
   rest of the set.
7. Every accepted clip is checksummed into the manifest (§7.2); a re-record changes the version.

### 5.8 Recorded vs composed — the summary table

| Spoken element | Recorded | Composed at playback |
|---|---|---|
| Phrase words ("Token number", "please proceed to", "Room", "টোকেন নম্বর", "কক্ষ", "আসুন") | ✔ | — |
| Token serial 1–999 | ✔ (word groups) | ✔ above 19 depending on language (§5.3) |
| Room number | ✔ (citation and, for Bangla, locative form) | ✔ digits/word-group composition |
| Doctor name | ✔ (per doctor, optional) | fallback via transliteration table + name clips, else omitted |
| Pauses | — | ✔ explicit gaps |
| Order of segments | — | ✔ fixed per language |

---

## 6. Number and sentence composition

### 6.1 Number → clip-id list (pure function)

```js
// lib/announcements/plan.js
numberClips(0, 'en')      → ['en/num/0']
numberClips(4, 'en')      → ['en/num/4']
numberClips(17, 'en')     → ['en/num/17']
numberClips(21, 'en')     → ['en/num/20', 'en/num/1']            // 60 ms gap
numberClips(305, 'en-GB') → ['en/num/3', 'en/num/hundred', 'en/num/and', 'en/num/5']
numberClips(305, 'en-US') → ['en/num/3', 'en/num/hundred', 'en/num/5']
numberClips(17, 'bn')     → ['bn/num/17']                        // no decomposition < 100
numberClips(305, 'bn')    → ['bn/num/300', 'bn/num/5']
numberClips(1000, 'bn')   → ['bn/num/thousand']
```

Rules:

1. Accept only what is **recorded**; anything else is `skipped/range` (§6.4 rule 4).
2. No leading zeros are spoken; `0007` and `7` both speak "seven" (the serial is an integer, not a string —
   `content.js:44-48` already coerces and rejects non-integers).
3. Negative, fractional or non-finite values are refused (`skipped/invalid_number`), never rounded.
4. The function is deterministic and total: the same input always yields the same clip list, which is what
   makes the catalogue test (§16.1 item 3) meaningful.

### 6.2 Sentence composition, English

```
segment 1  token_number        "Token number"        always
segment 2  number(tokenSerial) e.g. "four"           always
segment 3  doctor_prefix + name (or doctor clip)     only if hasDoctor
segment 4  please_proceed_to   "please proceed to"   variant 1 only
segment 5  room + number(room) "Room" "three oh five" variant 1 only
segment 6  please_proceed      "please proceed"      variant 2 only (room-less)
final punctuation/intonation comes from the last recorded clip, so variant 1 must end on the room number
and variant 2 on the "please proceed" clip.
```

Resulting sentences (the exact strings the content tests must assert):

| Case | Sentence |
|---|---|
| doctor + room | `Token number 4, Dr. Rahim Uddin, please proceed to Room 305.` |
| doctor, no room | `Token number 4, Dr. Rahim Uddin, please proceed.` |
| no doctor, room | `Token number 4, please proceed to Room 305.` |
| neither | `Token number 4, please proceed.` |

### 6.3 Sentence composition, Bangla

```
segment 1  bn/phrase/token_number     "টোকেন নম্বর"
segment 2  number(tokenSerial)
segment 3  bn/phrase/doctor_prefix + name, or doctor clip     only if hasDoctor
segment 4  bn/phrase/kokho            "কক্ষ"
segment 5  bn/room_loc/<roomId>       "৩০৫-এ"  (strategy A, §5.2)
segment 6  bn/phrase/ase_asun         "আসুন"
```

Room-less Bangla is not a drop-in: "টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, আসুন।" reads as "…, come", so the
room-less Bangla sentence needs an approved alternative text (e.g. "কাউন্টারে আসুন" — "come to the
counter") which is **not currently approved** and is raised as §18 O-3.

### 6.4 Edge cases and their outcomes

| Input | Outcome | Why |
|---|---|---|
| token serial 0 | speaks "zero"/"শূন্য" | 0 is recorded; a serial of 0 is odd but not invalid |
| token serial unparseable / negative | `skipped/unspeakable_token` | existing behaviour (`content.js:44-48`) retained |
| token serial > catalogue range | `skipped/range` | never speak a plausible-but-wrong number |
| room `''` / whitespace | room-less variant, `reason: 'no_room'` | F4.6 |
| room non-numeric ("Cabin A") | room-less variant **plus** `reason: 'room_not_announceable'` — or a recorded `room_named/<slug>` clip if the facility provides one | speaking "Cabin A" needs a recording, not a guess |
| doctor name in Latin script with a Bangla plan | fallback chain (§5.4), else omit or refuse per config | a Bangla voice reading Latin letters is unintelligible |
| doctor name already starting "Dr." | **strip the honorific before joining** | fixes the live `Dr. Dr.` duplication (§3.1 F1.6) |
| doctor name absent | omit segment (variant without doctor) | existing `missing_doctor_name` refusal becomes a *skip* only if config says so; default keeps refusing (§18 O-2) |
| language not `en`/`bn` | `skipped/unsupported_language` | existing behaviour retained |
| two languages enabled | the facility's `announcementLanguage` decides; never both in one plan | avoid doubling an already-noisy room |

---

## 7. Asset format, storage, manifest and caching

### 7.1 Encoding format

| Aspect | Decision | Reason |
|---|---|---|
| Primary codec | **Opus, mono, 32 kbps, in WebM** (`.webm`) | Speech at 32 kbps mono Opus is transparent for this use and halves the download of MP3. Supported by Chrome, Edge and Firefox, which is the realistic browser class of a queue desk or waiting-room display. |
| Fallback codec | **MP3, mono, 64 kbps** (`.mp3`) | Needed for Safari-family browsers and older installed displays, plus any device whose media stack refuses `audio/webm`. Chosen at runtime by `canPlayType`, not by user-agent sniffing. |
| Rejected | WAV delivery | 10–20× the bytes for no audible benefit; forces a slow first install and a cache-pressure problem on exactly the devices with the least storage |
| Rejected | Streaming/segmented (HLS/DASH) | Latency and per-clip failure modes for a 1-second sound |
| Sample rate | 48 kHz for Opus, 44.1 kHz for MP3 | Codec-native rates; no resampling at play time |
| Channels | Mono | A waiting-room announcement is mono; stereo doubles cost for nothing |

**Size budget** (Opus figures; MP3 fallback roughly doubles):

| Family | Count (typical facility) | Bytes each | Total |
|---|---|---|---|
| Phrase clips per language | 7–8 × 2 | ~5 KB | ~70 KB |
| Number clips `en` (0–19, tens, hundred, thousand, and, oh) | 32 | ~4 KB | ~130 KB |
| Number clips `bn` (0–99, hundreds, thousand) | 110 | ~4 KB | ~440 KB |
| Locative room clips `bn` (40 rooms) | 40 | ~4 KB | ~160 KB |
| Doctor clips (50 doctors, optional) | 50 | ~6 KB | ~300 KB |
| **Total, both languages, Opus** | | | **≈ 1.1 MB** |
| **Total with MP3 fallback shipped alongside** | | | **≈ 2.2 MB** |

That budget is deliberately small enough to precache on a tablet, survive a browser cache eviction, and
download over a slow clinic connection during an install step rather than during a call.

### 7.2 Manifest

One generated file, the only thing the client needs before it can play anything:

```json
{
  "manifestVersion": "2026-11-20.1",
  "catalogueVersion": "bn-1.0.0/en-1.0.0",
  "generatedAt": "2026-11-20T09:00:00Z",
  "languages": ["en", "bn"],
  "gapDefaults": { "sentence": 150, "withinNumber": 60, "leadIn": 150, "tail": 300 },
  "variants": { "en": { "hundredsStyle": "with_and", "roomReadAs": "number" },
                "bn": { "roomWord": "kokho" } },
  "clips": {
    "en/phrase/please_proceed_to": {
      "text": "please proceed to",
      "durationMs": 1180,
      "sources": [
        { "type": "audio/webm; codecs=opus", "src": "en/phrase/please_proceed_to.webm", "bytes": 5240, "sha256": "…" },
        { "type": "audio/mpeg",               "src": "en/phrase/please_proceed_to.mp3",  "bytes": 9800, "sha256": "…" }
      ]
    },
    "bn/room_loc/305": {
      "text": "৩০৫-এ", "roomId": "…uuid…", "durationMs": 900,
      "sources": [ { "type": "audio/webm; codecs=opus", "src": "bn/room_loc/305.webm", "bytes": 3900, "sha256": "…" } ]
    }
  }
}
```

Rules:

1. The manifest is **the contract**. A clip id that is not in the manifest does not exist; the plan builder
   must therefore be validated against the manifest in tests (§16.1 item 3), which is what stops a
   composition rule from silently referencing a clip nobody recorded.
2. `durationMs` lets the engine compute an expected duration and set a sensible watchdog before playing
   anything (§F2.5), instead of a single global timeout.
3. `sha256` per source makes the install verifiable (§7.5) and makes a mid-flight asset swap detectable.
4. Room clips carry `roomId` as well as the path, so a renamed room (305 → "Consultation 4") does not
   orphan its locative clip: the id still resolves, only the display name changed.
5. The manifest is generated by a build/ops script from the recorded files — it is never hand-edited, and
   it is committed alongside the clips so a checkout is playable without a build step.

### 7.3 Delivery and offline caching (the DQDS is the hard case)

A **queue desk operator page** is online by definition (it drives the queue API). A **waiting-room display**
is not: it may be a small PC behind a clinic router on a flaky link. Both must speak reliably.

| Layer | Design |
|---|---|
| Static hosting | Assets are ordinary files under `public/audio/announcements/`, served by the existing frontend host with long-lived immutable caching (`Cache-Control: public, max-age=31536000, immutable`) and a content-hashed or versioned directory (`/audio/announcements/v1.0.0/…`). A catalogue change is a new directory, so no cache invalidation is needed. |
| Service worker | A small cache-first service worker (`public/sw.js`) precaches the manifest plus all clips for the facility's enabled languages during an explicit **Install audio** action, and serves them cache-first afterwards. Scope is limited to `/audio/announcements/`; it does not touch API responses, documents or other app routes. |
| Why not app-shell PWA | The task asks for offline **audio**, not an offline application. Precaching the whole app would create a stale-UI class of bug (an operator on an old bundle) that is far worse than the problem it solves. The worker is asset-scoped and additive. |
| Install affordance | The announcements panel shows **Audio assets: 0 / 212 clips (0 KB / 1.1 MB) → Install**. After install: **Ready (offline-capable, catalogue bn-1.0.0/en-1.0.0)**. If not installed, the panel says **Not installed — announcements will attempt to stream each clip** (§7.4). |
| No service worker available | Assets still play from the HTTP cache after first use; the panel reports `offline: false` and the design degrades honestly rather than claiming readiness. |
| Cache probe | `assets.js` verifies presence with `caches.match(...)` for the manifest and a sample of clips (not all 212 — a 10-clip sample plus a byte-length check), so `capability()` is a real probe, not an assumption. |
| Storage pressure | On `QuotaExceededError`, install stops, reports how many clips landed and what is missing, and keeps stream-on-demand working. Audio is the first thing evicted under pressure, so the panel re-probes on every mount and after any `completed`/`failed` streak. |

### 7.4 Stream-on-demand (installed = false)

When a clip is not cached, the engine plays it from the network with `preload="auto"` and a per-clip timeout
derived from `durationMs`. This works on a desk with a good link and is exactly the wrong thing to rely on
in a waiting room, which is why the panel distinguishes the two states plainly.

### 7.5 Integrity and verification

1. During install, each downloaded clip's bytes are hashed and compared to the manifest `sha256`; a mismatch
   marks the clip `corrupt`, is not cached, and is reported.
2. At play time the engine does not re-hash (too slow); it relies on the cache having been verified at
   install, and treats a decode/`error` event as `failed` with `reason: 'decode'`, invalidating that clip in
   `assets.js` so the next install repairs it.
3. `Audio assets` version mismatch (cached catalogue ≠ manifest catalogue) triggers a repair prompt rather
   than silent mixing of two recordings.

### 7.6 Failure modes and their declared behaviour

| Failure | Behaviour |
|---|---|
| No service worker / private browsing | Stream-on-demand only; panel shows `offline: false` |
| Assets partially installed | Announcements still attempt; a missing clip yields `failed/missing_clip` **mid-sentence** — so the engine prefers to skip a plan whose clips are not all present and report `blocked/assets_incomplete`, rather than speaking half a sentence |
| Device has no audio output / muted | `play()` rejects or `AudioContext` is suspended → `failed/output`; the panel says "no audio output detected" and the operator still sees the call on screen |
| Browser blocks autoplay | The queue page is a user-gesture-driven tool; the first call click counts as a gesture. If a display page ever plays without a gesture, it must be activated once via a visible **Enable announcements** button (never a silent retry loop) |
| Tab backgrounded / throttled | Timers throttle; the engine uses audio-media events, not `setInterval`, for sequencing, so throttling shifts nothing |
| Network dies mid-install | Install is resumable: it skips clips already verified, so a retry continues rather than restarting 1.1 MB |

---

## 8. Playback engine and event flow

### 8.1 The local engine (`local-audio.js`)

```js
const engine = createLocalAudioEngine({ assets, now, createAudio /* injectable for tests */ });

engine.speak(plan, { signal })
// 1. resolve every clipId in plan.clipIds against the manifest
//    - any unresolvable clip  → resolve({ status:'blocked', reason:'assets_incomplete' })  [never partial speech]
// 2. expectedMs = Σ durationMs + Σ gapsMs + leadIn + tail
// 3. arm watchdog(expectedMs * 1.6 + 2000)
// 4. for each clip: new Audio(src) → play() → await 'ended'  (or 'error')
//    - `ended` on the LAST clip           → resolve({ status:'completed' })
//    - 'error' / play() rejection         → resolve({ status:'failed', reason })   (no retry inside the engine)
//    - watchdog expiry                    → resolve({ status:'failed', reason:'watchdog' })
//    - signal abort / cancel()            → pause + resolve({ status:'interrupted' })
```

Hard rules:

1. **`completed` is emitted only after the last clip ends.** Nothing else can produce it — that is the
   structural fix for F2 (§3.2), and it is enforced by making the engine the only place that returns it.
2. **No partial sentences.** A missing clip blocks the whole plan; speaking "Token number 4, Dr. Rahim
   Uddin, please" is worse than silence because staff will assume the room was announced.
3. **No internal retry.** Retry belongs to the controller (§8.4), which knows about attempt counts,
   backoff and whether the operator has since called someone else.
4. **Sequencing is event-driven**, using the audio element's own `ended`/`error` events and a single
   watchdog timer. No `setInterval` polling loop.
5. **One `Audio` object per clip, reused from a small pool** (max 3), and explicitly `pause()`d + `src=''`
   on completion so a device does not hold dozens of media elements open.
6. **Injectable clock and `createAudio`** so the whole engine can be unit-tested in Node with fake audio
   elements (§16.1 item 4) without any real sound.

### 8.2 Terminal outcomes (shared vocabulary, all engines)

```js
{ status: 'completed' | 'failed' | 'interrupted' | 'cancelled' | 'blocked' |
          'busy' | 'unavailable' | 'skipped' | 'duplicate',
  reason: null | 'no_output' | 'decode' | 'missing_clip' | 'watchdog' | 'network'
        | 'not_activated' | 'no_room' | 'room_not_announceable' | 'unspeakable_token'
        | 'range' | 'invalid_number' | 'unsupported_language' | 'assets_incomplete'
        | 'user_muted' | 'voice_unavailable',
  engine: 'local-audio' | 'speech-synthesis' | 'external-tts',
  language: 'en' | 'bn',
  attempt: 1,
  eventKey, startedAt, endedAt, durationMs, expectedMs }
```

`'started'` is **not** in this list — it is not an outcome. It may be emitted as a *progress* event
(`onProgress({ phase:'speaking' })`) but the controller's `lastOutcome` only ever holds a terminal value
(F2.6).

### 8.3 Single in-flight, activation and ordering

1. At most one attempt is in flight. A new event during speech either (a) queued if it is a different
   patient and the current clip set has ≤ 1 clip left, or (b) rejected as `busy` — **default: `busy`**, and
   the panel shows "called while another announcement was playing" so the operator can recall.
   *Rationale:* overlapping announcements in a waiting room are unintelligible, and silently queueing three
   stale calls is worse than a visible miss.
2. The queue is bounded at 1 pending (not an unbounded FIFO): a 40-person backlog must never become a
   three-minute announcement lag.
3. Activation is a one-time, user-gesture-driven unlock shared by all engines (`speech-synthesis.js:150-160`
   already has the browser-TTS equivalent); for `local-audio` the unlock is simply the first successful
   `play()` inside a gesture, and a blocked autoplay becomes `failed/not_activated`, never a silent no-op.
4. `cancel()` is called on: leaving the queue page, disabling announcements, switching language, changing
   the selected entry, and before a newer attempt for the same event.

### 8.4 Retry and backoff (F2.7 + F3.5)

| Attempt | Delay before | Gap after failure |
|---|---|---|
| 1 | 0 | 2 s |
| 2 | 2 s | 4 s |
| 3 | 6 s | — (give up, `failed`) |

Retries are **only** for `failed` (transient) outcomes. `skipped`, `blocked`, `cancelled`, `interrupted`,
`duplicate` and `unavailable` are never retried: retrying them cannot succeed and would double-announce.
Each retry increments `attempt` in the store and is visible in the panel ("retrying 2 of 3").

### 8.5 Event identity across engines

The `eventKey` from `content.js:60-80` (`entry:<queueEntryId>:<action>:<revision>`) is the identity for all
three engines and for the dedupe store, so a fallback from `local-audio` to `external-tts` is the *same*
event, not a second announcement.

### 8.6 Observability fields the panel shows

| Field | Meaning |
|---|---|
| Engine + language | which renderer spoke, in which language |
| Last outcome | terminal status + reason, humanised ("Played", "Failed — no audio output", "Skipped — no room on this appointment") |
| Attempt | `1`, `2 of 3`, `gave up` |
| Assets | `Ready (offline)`, `Streaming`, `Not installed`, `Corrupt clip: bn/num/7` |
| Voice (browser TTS only) | the selected voice, and whether it is a network voice |
| Timing | started/ended, `durationMs` vs `expectedMs` (a wild divergence is a symptom) |

---

## 9. Room data-flow correction (as designed)

### 9.1 The corrected path

```
appointment booking
   └── Appointment.room_id / room_name / location_source      (models.py:616-630, write-once snapshot)
            │
            ├─────────────────────────────► GET /api/v1/appointment/...   (already serialised, main.py:278)
            │                                        └── appointment UI shows the booked room
            │
            └── check-in  (backend/queuing/main.py:230-238)
                     └── QueueEntry  (+ room_id/room_name/location_source when R2 lands)
                              │
                              └── GET /api/v1/queue/...  (main.py:82-92 serializer)
                                       ├── room_name / room_id / location_label / room_source   [R1 join | R2 column]
                                       └── pages/queue.js:64-65  room: entry.room_name
                                                └── plan.js → 'room' segment → local-audio
```

### 9.2 Source-of-truth table

| Source | Status | May be announced? |
|---|---|---|
| `Appointment.room_id` / `room_name` set at booking | **authoritative snapshot** | ✔ yes — this is the record of where the patient was told to go |
| `QueueEntry.room_*` copied at check-in (R2) | **authoritative copy of the snapshot** | ✔ yes |
| Room captured at walk-in registration (R2) | **authoritative capture** | ✔ yes |
| `ScheduleSession.room` (doctor's *current* schedule) | mutable, changes through the day | ✘ **never** — announcing it tells a patient a room their appointment never named, and silently rewrites history |
| `DoctorBranch.room` / branch default room | mutable default | ✘ never as an announcement substitute; at most a booking-time default that ends up in the snapshot |
| Free-text notes / operator memory | unmodelled | ✘ never |

### 9.3 Why the "current schedule" shortcut is forbidden

1. **It is wrong for the patient.** A token issued for Room 305 is the token the patient is holding. If the
   doctor was moved to 401 after check-in, announcing 401 sends the patient to a room that the board, the
   printed slip and the receptionist's screen do not agree on.
2. **It is wrong over time.** Re-announcing the same token later in the day would produce a different room
   for the same event, so the audio would contradict the persisted queue history — a provenance violation of
   exactly the kind the platform rules forbid for emissions, applied to a queue.
3. **It couples two moving subsystems.** `schedule_sessions` is edited by roster/attendance flows; queue
   announcements must not become a second, invisible reader of live schedule state whose failures surface
   as a patient in the wrong room.
4. **Correction belongs upstream.** If the room genuinely changed, the correct action is to change the
   appointment (which is an audited, visible rewrite) and then re-call the patient — a deliberate operator
   act, not an audio side-effect.

### 9.4 Cases and their announcements

| Case | Announcement | Operator-visible state |
|---|---|---|
| Appointment with room | full sentence | normal |
| Appointment without room | room-less variant | "no room on this appointment" hint on the row |
| Walk-in (R1) | room-less variant | same hint, "walk-in" badge |
| Walk-in with captured room (R2) | full sentence with the captured room | normal |
| Room renamed after check-in | the snapshot name (R2 keeps the copied name) | the mismatch is visible in the appointment history |

---

## 10. External TTS (optional fallback only)

### 10.1 Position in the design

External TTS is a **fallback**, never the primary mechanism, and never a silent substitute for missing
assets. It exists to cover: (a) an English name or room that has no recording, (b) a facility that has not
recorded Bangla assets yet, and (c) a future language. It is the only engine that requires the network and
the only one that sends text off the device, which is why every use of it is visible in the panel.

### 10.2 Backend proxy, not a browser key

```
frontend  →  POST /api/v1/announcements/tts      (staff auth, queue-scoped)
             body: { language, text, voice? }
          ←  200 audio/mpeg | 200 { audioUrl (short-lived) } | 4xx refusal
backend   →  provider API with a server-side credential
```

Rules (all mandatory):

1. **The provider credential never reaches the browser.** No key in `VITE_*`, no key in `public/`.
2. The endpoint is **staff-authenticated and organization-scoped** using the same dependencies as the queue
   routes (`main.py:120-160`); it is not a public synthesis service.
3. The endpoint accepts **only the announcement text shape** (allow-listed fields, ≤ 400 characters,
   `language ∈ {en, bn}`). It must not become a general "speak anything" proxy — that would be an
   abuse path and an exfiltration path.
4. Rate-limited per organization through the existing limiter dependency (route dependency, **not**
   `RateLimitMiddleware`, which must stay unregistered), and refusal is 429 with headers.
5. Never log the request text at info level alongside identifiers; log `language`, `chars`, `outcome`.
6. Any API key, token or signed URL returned by a provider stays server-side; the browser receives audio
   bytes or a short-lived URL that is not logged.

### 10.3 Quality gate (a hard prerequisite, not a nicety)

A Bangla TTS voice must pass an **explicit listening test by a native speaker** on the actual script
patterns (token numbers, "কক্ষ …-এ আসুন", doctor names) before it may be enabled for Bangla. Generic
provider Bangla voices frequently mispronounce locative forms and Latin-script doctor names; an
unintelligible announcement in a waiting room is a worse patient experience than a bell. Until the gate is
passed, `external-tts` for `bn` is **disabled by configuration**, and the panel says so.

### 10.4 Caching synthesised audio

Synthesised audio for a **fixed** text (phrase, number, room name) is effectively an asset. The design
therefore caches provider output as assets when it is stable:

1. On first synthesis of a text that has no clip, the backend stores the audio as a facility-scoped asset
   with a content hash, and the manifest gains a `tts/<hash>` entry.
2. Subsequent plays use the cached asset through `local-audio`, so repeated announcements cost nothing and
   work offline — the fallback gradually becomes the primary locally, which is the intended direction.
3. Cached TTS audio is subject to the same integrity/versioning rules (§7.5) and is never treated as a
   substitute for a professionally recorded clip: `source: 'tts'` is recorded in the manifest so an audit
   can tell a synthetic room name from a recorded one.

### 10.5 Cost and dependency controls

| Control | Design |
|---|---|
| Off by default | `externalTts.enabled = false` until a facility opts in |
| Budget guard | the endpoint counts characters per organization per day; exceeding the cap returns `blocked/quota` and the panel says "fallback voice unavailable — using recordings only" |
| Provider outage | a non-2xx or timeout returns `blocked/provider_unavailable`; the controller does **not** fall back to browser TTS for Bangla |
| Language coverage | a provider voice that does not support `bn` is not eligible; capability is checked server-side, not assumed |

---

## 11. Security, privacy and consent

### 11.1 What an announcement may contain

Allow-list, enforced at plan construction (`plan.js`) and re-checked at the panel:

| Allowed | Not allowed |
|---|---|
| token serial (an integer, not a name) | patient name, initials, phone, date of birth, national id, address |
| doctor display name (staff data) | diagnosis, department-inferred condition, test name, prescription, bill amount |
| room name (facility data) | appointment reason, notes, any free text field |
| event action ("called", "recall") | internal queue ids, appointment ids, organization ids, DB uuids |

The design's whole domain is deliberately the same surface the PQV decision already permits on a public
board — token number and operational state — so that **an announcement broadcast into a waiting room can
never say anything the public display may not show** (§11.5).

### 11.2 Payload hygiene

1. `plan.js` copies only `token`, `doctorName`/`doctorId`, `room` out of the queue entry — a
   destructuring-by-allow-list, so adding a field to the API response cannot leak into audio by accident.
2. The attempt log (if enabled) stores the plan's **clip ids and text of the recorded segments**, never the
   whole queue entry.
3. No `appointment_id`, `organization_id`, `patient` object or auth token is put in `plan`, in the panel
   state, or in `localStorage`.
4. Nothing about an announcement is written to the URL (no token or room in query strings or fragments), so
   screen-shares, bookmarks and browser history do not become patient-flow records.

### 11.3 Consent, notice and the public surface

1. A waiting-room announcement is public speech in a physical space. The facility is responsible for
   notice that announcements are made; CarbonTally's job is to make it impossible for the content to exceed
   the allow-list.
2. The same rule that governs the DQDS board applies: a token serial plus a room is not an identity, but
   **combining** it with a visible position in a queue can be re-identifying in a small waiting room. The PQV
   decision (`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md:57-67`) already records that judgement;
   this document does not widen it, and OD-4 remains the place to change it.
3. Doctor-name announcements are staff data. They are announceable because a patient must know whom they
   are seeing; a doctor may opt out (config), in which case the segment is omitted and the announcement
   still works.

### 11.4 Asset and manifest trust

| Risk | Control |
|---|---|
| Someone replaces a clip | `sha256` per source in the manifest, verified at install; a mismatch is reported and not cached |
| Someone edits the manifest | The manifest is served from the same origin as the app; a tampered manifest can only reference same-origin paths (validated) and its clips still fail hash checks |
| A clip path escapes the directory | Path values are validated against `^[a-z0-9/_-]+$` and resolved relative to the announcements root only |
| Cross-tenant audio | Assets are per-facility directories; a facility's manifest never references another facility's doctor clips. Doctor clips are keyed by doctor id, and the manifest only lists doctors visible to that facility |

### 11.5 Boundaries this document does **not** move

1. **The UI is not the security boundary.** The queue API's authorization is unchanged and remains the only
   thing that decides whether a staff member may see an entry; audio merely reads what the API already
   returned.
2. **The DQDS public display is a separate authorization decision** (OD-4 / PQV). Nothing here grants it.
3. **PE / consultant / customer isolation is untouched** — no new endpoint, no new query scope, no RLS
   change (R2 adds nullable columns to an already tenant-scoped table and inherits its policies).
4. **No audio content is ever derived from a document, extraction or emissions record.** The announcement
   path has no contact with the processing pipeline.
5. **`RateLimitMiddleware` stays unregistered**; the TTS endpoint uses the route-dependency limiter, and its
   refusal is 429 with headers (§10.2 item 4).
6. **No compliance claim.** Speaking a token number is not a medical-device, accessibility-certification or
   regulatory assurance, and nothing in the panel copy may imply one.

---

## 12. Configuration ownership (OD-2 partially answered, partly open)

### 12.1 The keys the design requires

| Key | Type / default | Effect | Safe to change at runtime? |
|---|---|---|---|
| `announcementLanguage` | `'bn' \| 'en'` — no default assumed | which language the facility announces in | yes (takes effect on the next event) |
| `announcementsEnabled` | boolean, default `false` | master switch; audio is always opt-in | yes |
| `announcementTrigger` | `'auto_on_call' \| 'manual'`, default **`'auto_on_call'`** (ratified criterion C5) | manual remains an operator affordance (play/replay) in both modes | yes |
| `announcementEngine` | `'local_audio' \| 'browser_tts' \| 'external_tts'` with `local_audio` primary | which renderer is preferred | yes |
| `externalTts.enabled` | boolean, default `false` | enables the network fallback (§10) | yes |
| `externalTts.dailyCharBudget` | integer | abuse/cost guard | yes |
| `hundredsStyle` | `'with_and' \| 'without_and'` | English hundreds wording (§5.3) | yes |
| `roomWord` | `'room' \| 'cabin'` (bn: `kokho` / `kebin`) | room noun | yes |
| `doctorHonorific` | `'full' \| 'short'` (bn) | "ডাক্তার" vs "ডা." | yes |
| `roomReadAs` | `'number' \| 'digits'` | "three hundred five" vs "three oh five" | yes |
| `announceDoctorName` | boolean, default `true` | omit the doctor segment (privacy / speed) | yes |
| `repeatOnRecall` | boolean, default `true` | play the `repeat` pre-roll on a recall | yes |
| `assetBaseUrl` | string | where the catalogue is served (only needed if assets move to a CDN) | yes |

### 12.2 What is *not* configuration

- The allow-list of announceable fields (§11.1) — policy, not preference.
- The "never use the current schedule room" rule (§9.3) — correctness, not preference.
- The terminal outcome vocabulary (§8.2) — a contract between modules.
- The retry ceilings and the dedupe TTL (F3.4) — engineering safety limits; exposing them invites a facility
  to configure a double-announcement.

### 12.3 OD-2 — what the record already answers, and what it does not

OD-2 was carried into this task as **unresolved**: who owns announcement configuration — the facility
(customer admin), the processing entity that operates the front desk, or CarbonTally internal staff.

Source inspection changes that status. The approved MVP Feature Catalogue already states, for QUE-006:

> "**Expected user roles:** `super_admin`, `org_admin`, `branch_admin` (configure enable/disable and
> announcement language); `receptionist`, `doctor` (trigger announcements via the queue call action)"
> — `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md:548`

and, as an acceptance criterion:

> "Only authorized roles (org/branch admin) may configure announcements." — same file `:1116`

**Therefore, by ratified product record:**

| Question | Status |
|---|---|
| Who may enable/disable announcements? | **Answered** — `org_admin`, `branch_admin` (and `super_admin`), i.e. the facility |
| Who may choose the language? | **Answered** — the same facility roles |
| Who triggers an announcement? | **Answered** — `receptionist`/`doctor` via the queue call action |
| Who owns the **engine preference** (`local_audio` / `browser_tts` / `external_tts`)? | **Open** — not named in the catalogue |
| Who owns **external-TTS spend** (switch + budget)? | **Open** — commercial question, not addressed |
| Who **installs/updates the asset catalogue**, and where is that surface? | **Open** — engineering/ops question, not addressed |
| Which *surface* holds the facility settings (org settings vs branch settings vs a new page)? | **Open** — an implementation/placement decision, not a policy one |

So OD-2 should be re-scoped rather than left as a blanket blocker: **the policy question is answered for the
two settings that matter most, and remains open for the three knobs this design adds.** That narrowing is
reported in the completion report as a correction to the task brief, not invented.

### 12.4 Consequence for the design

1. **No new ownership model is invented.** Enable/disable and language are read and written through the
   facility settings path the catalogue already presumes, with `org_admin`/`branch_admin`/`super_admin`
   authorization per the existing capability model (the UI is not the boundary; the write is authorized
   server-side).
2. **The three open knobs are not exposed until decided.** `announcementEngine`, `externalTts.*` and the
   install action ship **disabled/absent** while their ownership is open. In particular, external TTS stays
   off (`§18 D-13`), and the install action is offered to whoever operates the display device as a
   *device-level* action, not a policy setting — installing audio on a screen changes nothing about the
   facility's configuration.
3. **One accessor, one place to move.** All reads go through `announcementConfig` in the frontend and a
   single server-side settings read, so the surface can be relocated (org vs branch vs admin plane) without
   touching the engine, the plan builder or any test.
4. **Language has no engineering default.** If a facility has no configured language, the feature does not
   guess: it stays silent with `blocked/not_configured` and the panel says "announcement language not
   configured" — guessing `bn` or `en` on a patient's behalf is a product decision this document will not
   make (§18 O-9).

---

## 13. Impact assessment

### 13.1 Code impact by module

| Module | Impact | Notes |
|---|---|---|
| `lib/announcements/content.js` | **medium** — wording (F1), honorific normalisation | its existing tests must change (§3.1 F1.4) |
| `lib/announcements/controller.js` | **medium** — outcome vocabulary, store wiring, engine selection | dedupe structure replaced (F3) |
| `lib/announcements/speech-synthesis.js` | **medium** — terminal outcomes | voice selection and pause logic retained |
| `lib/announcements/plan.js`, `engine.js`, `local-audio.js`, `assets.js`, `dedupe.js` | **new** | ~5 focused modules, each unit-testable |
| `components/queue/QueueAnnouncements.js` | **medium** — outcomes, engine/asset status, install action | the operator-facing surface of all four findings |
| `pages/queue.js` | **small** — room field | one property, one mapping |
| `backend/queuing/main.py` | **small (R1) / medium (R2)** | serializer + batched room resolution; R2 adds creation-time copy |
| `backend/appointment/main.py` | **none (R1)** — reuse `_location_label` | possibly a shared helper extraction |
| `backend/**/tts` route | **new**, optional, Stage E | gated on §10.3 |
| `public/audio/announcements/**`, `public/sw.js` | **new** | assets are data, not code |

### 13.2 Test impact

- Existing announcement tests: **49** (11 content, 15 controller, 18 speech-synthesis, 5 boundary).
- Tests that **must change** because they encode defective behaviour: the content tests that assert the
  missing-phrase string (`queue-announcement-content.test.mjs:37,43`) and the honorific-duplication
  assertion (`:112-113`); the controller's single-slot dedupe tests (F3.4); the speech tests that assert
  `SPOKEN` on `onstart` (F2.6).
- New test families: plan/composition, catalogue coverage, local engine, dedupe store, assets/manifest,
  queue API room fields.

### 13.3 Operator and workflow impact

1. **No new duty is created.** Announcements remain opt-in and audio failure never blocks a call
   (§4.6 step 6). The queue does not depend on audio in any direction.
2. The panel becomes more informative (engine, assets, attempts) — which is a small cognitive cost for a
   large diagnostic gain, and it is progressive: collapsed by default, expanded on demand.
3. **The trigger becomes event-driven, as ratified.** Criterion C5 requires announcements on the queue call
   event, so the manual button (`queue.js:57-66, 202`) becomes an affordance alongside automatic
   announcement rather than the only trigger. That *is* a change to the desk's working behaviour — the room
   will now speak on every call wherever announcements are enabled — and it needs a runbook line and a
   training note, not a new product decision. A manual-only facility mode is not approved (§18 D-14).

### 13.4 Infrastructure and operational impact

| Area | Impact |
|---|---|
| Storage | ~1–2 MB per facility language set in the frontend host; + facility-scoped cached TTS audio if enabled |
| Network | an install-time download per display device; then zero per announcement |
| Backend | R1: one extra batched query per queue page. R2: a migration. Stage E: a new authenticated endpoint |
| Support | new failure vocabulary in the panel; the runbook must explain "Not installed", "Corrupt clip", "No audio output" |
| Browsers | Chrome/Edge/Firefox primary; Safari needs the MP3 fallback and is verified on device (§16.5) |

### 13.5 Contract impact

1. **Additive only** on `GET /api/v1/queue/...` (three string fields + one provenance field, R1).
2. No removal of any existing field; `entry.room` was never populated, so no consumer loses anything.
3. The new TTS endpoint is new and optional; it must appear in the OpenAPI schema before use (§16.3).

---

## 14. Migration and compatibility

### 14.1 From today's browser-TTS-only implementation

| Step | Change | Compatibility |
|---|---|---|
| M1 | Introduce the renderer interface; wrap `speech-synthesis.js` unchanged behind it | zero behaviour change; all 18 speech tests still pass |
| M2 | Introduce the plan (§4.2) and have the wrapper accept a plan's `text` | zero behaviour change; plan is derived from today's `buildAnnouncement` output |
| M3 | Add `local-audio` as an engine; keep browser TTS available | selected only when assets are installed; otherwise today's path |
| M4 | Replace the single-slot dedupe with the bounded store | **behaviour change**: retries of a previously succeeded event become possible when TTL expires; tests change by design |
| M5 | Terminal-outcome reporting | **behaviour change**: the panel may now say "failed" where it used to say "played" — this is the point of F2 |
| M6 | Room field end-to-end | additive; plans without a room are unchanged |

### 14.2 Database migration (R2 only)

- Three nullable columns on `queue_entries` (`room_id`, `room_name`, `location_source`) + one backfill
  statement + no index (the queue is already filtered by organization/branch/status and the room is display
  data, not a filter key).
- Down-migration: drop the three columns; nothing else references them, and the serializer degrades to R1's
  join semantics (so an R2 rollback does not break announcements).
- No RLS change: the table's existing policies cover the new columns automatically. A test must prove a
  foreign organization still cannot read them (§16.3).
- Existing rows: appointment-backed entries backfilled from `Appointment`; walk-ins left `NULL` (honest
  absence, not a guess).

### 14.3 Asset versioning and rollback

1. Clips live in a versioned directory (`v1.0.0/`); the manifest names the catalogue version.
2. Rolling back a bad recording is redeploying the previous directory plus its manifest — no client change.
3. A cached old catalogue keeps working offline until the device reinstalls; the panel compares cached version
   to manifest version and offers **Update audio** rather than mixing them (§7.5 item 3).
4. Because the plan is derived from the manifest-validated id space, an old cached catalogue that lacks a new
   clip id yields `blocked/assets_incomplete`, never a wrong sound.

### 14.4 Behavioural compatibility the staff will notice

| Today | After | Mitigation |
|---|---|---|
| "Played" as soon as speech starts | "Played" only when it finished; "Failed" if it did not | this is the fix, but the runbook and the release note must say it plainly, or staff will report a "regression" |
| English sentence missing "please proceed to" | the approved sentence | release note: the sentence changed on purpose |
| "Dr. Dr. Rahim Uddin" | "Dr. Rahim Uddin" | release note |
| A second call for the same patient says nothing, ever | says nothing within the window, then works again | release note: the window is 10 minutes (F3.4) |
| No room spoken | room spoken when the appointment had one | release note |
| Audio needs no install | audio must be installed once for offline use | the panel's install affordance and the runbook step |

### 14.5 Legacy behaviour deliberately retained

1. `eventKey` shape and the `source: 'event' | 'manual'` distinction (`controller.js:113-118`).
2. Manual announcement bypassing the event dedupe (§F3.3 rule 3).
3. Browser-TTS pause halving and voice preference (`speech-synthesis.js:180-240`).
4. Refusal states (`missing_doctor_name`, `unsupported_language`, `unspeakable_token`) — narrowed only where
   §6.4 says so, never silently dropped.
5. The announcements feature remains entirely optional and quarantined from queue operations.

---

## 15. Staged implementation plan

Ordering principle: **correctness before capability, capability before convenience.** Every stage is
independently shippable and independently abandonable; nothing later is required to make earlier work
correct.

### Stage A — Truthfulness of what exists today (highest value, no new assets)

| Item | Detail |
|---|---|
| Scope | F1 wording + honorific normalisation; F2 terminal outcomes for the *existing* browser-TTS path; F3 bounded dedupe store; F4 **R1** room read-through; the ratified event trigger (C5) — announce on `called`, wired **after** the dedupe fix so it cannot double-announce |
| Why first | today the product reports success it has not achieved and cannot speak the approved sentence; these are defects in shipped behaviour, independent of any new audio architecture |
| Deliverables | `content.js` wording; `controller.js` outcome recording + store; `speech-synthesis.js` terminal contract; `_entry_to_dict` room fields + batched resolution; `QueueAnnouncements.js` honest status |
| Exit criteria | content/controller/speech tests updated and green; a stopped mid-sentence synthesis reports `failed`; a failed event is retried and eventually succeeds; a queue entry shows its appointment room; foreign-organization denial unchanged |
| Not included | no clips, no service worker, no config UI, no backend endpoint |
| Risk | low — behaviour changes are visible but strictly more honest |

### Stage B — Composition core (pure logic, no recordings)

| Item | Detail |
|---|---|
| Scope | `plan.js`, `engine.js` renderer interface, manifest schema + validator, catalogue coverage test |
| Deliverables | plan builder with en/bn segment rules (§4.3, §6.2–6.3), number→clip-id function (§6.1), manifest schema and a `validateManifest()` used by both tests and `assets.js` |
| Exit criteria | golden plan tests for all 8 field combinations × 2 languages; every clip id referenced by any plan exists in the *declared* catalogue (the test fails if `plan.js` invents an id) |
| Depends on | Stage A (event keys and outcome vocabulary) |
| Risk | low — pure functions |

### Stage C — Local audio delivery (English first)

| Item | Detail |
|---|---|
| Scope | `local-audio.js` (sequencer, watchdog, cancellation), `assets.js` (install, verify, probe), `public/sw.js`, install UI, English catalogue recorded |
| Deliverables | working English announcements from local clips, offline-capable after install; `blocked/assets_incomplete` instead of partial sentences |
| Exit criteria | a real browser plays a full sentence with no network after install; killing the network mid-install resumes; a corrupted clip is reported and repaired; watchdog fires on a stalled element |
| Depends on | Stage B; a recorded English catalogue and its manifest |
| Risk | medium — first real audio device behaviour; mitigated by the injectable audio factory for tests |

### Stage D — Bangla catalogue and locative rooms

| Item | Detail |
|---|---|
| Scope | Bangla phrase/number inventory (§5.1, §5.3), locative room clips or frame clip (§5.2), doctor-name recordings (§5.4) |
| Deliverables | Bangla announcements, native-speaker sign-off per clip, recorded-name workflow |
| Exit criteria | listening sign-off on all four field combinations including a room-less Bangla sentence under the approved wording (§18 O-3); locative rooms sound natural to a native speaker; the English and Bangla event triggers behave identically (C5) |
| Depends on | Stage C; language approval; recording sessions |
| Risk | high on wording, not on engineering — the Bangla room-less form is an open question |

### Stage E — External TTS fallback (optional)

| Item | Detail |
|---|---|
| Scope | backend proxy route, credential handling, allow-list enforcement, rate limit, budget guard, cached synthesis as assets |
| Deliverables | `/api/v1/announcements/tts` in OpenAPI, authenticated and organization-scoped; synthesis cached to the asset catalogue |
| Exit criteria | (§10.3) native-speaker listening gate passed for `bn`; a non-staff caller is refused; over-budget returns a clear refusal; 429 carries headers; no key or URL in the browser or logs |
| Depends on | Stage C (asset caching), an owner decision on cost (§18 O-4) |
| Risk | medium — network dependency and cost; strictly a fallback |

### Stage F — Hardening and operations

| Item | Detail |
|---|---|
| Scope | optional attempt log (ANN-008), runbook, panel polish, R2 migration, device-matrix verification (§16.5) |
| Deliverables | operator runbook (install, corrupt clip, no output, quota), attempt log if approved, `queue_entries` room columns if R2 is chosen |
| Exit criteria | full device matrix verified; runbook reviewed by whoever operates the desk |
| Depends on | Stage C/D in real use |
| Risk | low |

---

## 16. Test and verification strategy

### 16.0 The fifteen areas and the layer that proves each

| # | Area | Unit | API | Browser | Physical device |
|---|---|---|---|---|---|
| 1 | Wording / approved sentence | ✔ | — | ✔ (panel preview text) | — |
| 2 | Number composition | ✔ | — | — | — |
| 3 | Catalogue coverage & manifest integrity | ✔ (+ build check) | — | ✔ (install verifies hashes) | — |
| 4 | Plan composition (segments, gaps, variants) | ✔ | — | — | — |
| 5 | Local engine sequencing / watchdog / cancel | ✔ (fake audio) | — | ✔ (real audio) | ✔ |
| 6 | Browser-TTS terminal outcomes | ✔ (stubbed speechSynthesis) | — | ✔ | — |
| 7 | Dedupe store & retry/backoff | ✔ (injected clock) | — | — | — |
| 8 | Controller state machine & engine selection | ✔ | — | ✔ | — |
| 9 | Queue API room fields | — | ✔ (TestClient) | ✔ | — |
| 10 | Authorization boundaries (cross-org, cross-branch) | — | ✔ | — | — |
| 11 | Asset install / caching / repair | ✔ (manifest logic) | — | ✔ | ✔ (cache eviction) |
| 12 | Offline behaviour | — | — | ✔ (DevTools offline) | ✔ (unplugged link) |
| 13 | Accessibility & operator UX | — | — | ✔ (axe + keyboard) | — |
| 14 | Responsive viewports | — | — | ✔ (390→1920) | ✔ (real screens) |
| 15 | Room acoustics & intelligibility | — | — | — | ✔ **only here** |

Area 15 is called out deliberately: no automated test can prove that a sentence is intelligible in a noisy
waiting room. Claiming "announcements verified" without a physical listening check would be exactly the
false-completion the project rules forbid.

### 16.1 Unit layer (Node, no audio, no DOM)

1. **Wording** — all four English sentences of §6.2 and the Bangla sentences of §6.3 exactly; the
   release-blocking assertion is that `please proceed to` is present, and that a name supplied as
   "Dr. Rahim Uddin" never produces "Dr. Dr.".
2. **Wording regressions** — the two defective assertions at `queue-announcement-content.test.mjs:37,43` and
   `:112-113` are **rewritten**, not deleted, so the fix is visible in the diff.
3. **Number composition** — every case in §6.1, plus 0, 10, 11, 19, 20, 21, 99, 100, 101, 110, 999 and the
   refusal cases in §6.4; Bangla below 100 must never decompose.
4. **Catalogue coverage** — for a fixture catalogue, every clip id a plan can produce exists; a deliberately
   missing clip id fails the test with the offending id named. This is the guard that stops a composition
   rule from referencing a recording nobody made.
5. **Manifest validation** — missing `sha256`, non-`^[a-z0-9/_-]+$` path, duplicate id, unknown mime type,
   absent `durationMs` are each rejected.
6. **Plan composition** — 8 field combinations × 2 languages; `gapsMs` length equals `clipIds` length;
   absent field ⇒ absent segment; room-less English uses the room-less variant.
7. **Local engine** — with an injected fake `createAudio`: normal completion; element `error` mid-sequence ⇒
   `failed/decode` with no further clips played; watchdog expiry ⇒ `failed/watchdog` and all elements released;
   `cancel()` mid-sequence ⇒ `interrupted`; missing clip ⇒ `blocked/assets_incomplete` and **nothing played**.
8. **Browser-TTS contract** — `onstart` alone never yields `completed`; `onend` yields `completed`; `onerror`
   yields `failed`; `speechSynthesis.cancel()` yields `interrupted`; a voice list appearing late still
   selects a local voice.
9. **Dedupe store** — duplicate within TTL ⇒ `duplicate`; different revision ⇒ allowed; manual source ⇒
   always allowed; TTL expiry ⇒ allowed; store bounded at `maxKeys` with oldest-completed eviction; failed
   event retried to `maxAttempts` then terminal; exponential delays computed from the injected clock (no real
   sleep); no timers left behind (`clock.pendingTimers() === 0`).
10. **Controller** — single in-flight ⇒ second event `busy`; engine fallback preserves `eventKey`; a
    fallback is reported as a fallback, not as a second announcement.

### 16.2 API layer (pytest + TestClient)

1. Queue payload contains `room_name`, `room_id`, `location_label`, `room_source` for an
   appointment-backed entry, populated from the **appointment snapshot**.
2. The historical-correctness test: create the entry, then change the doctor's schedule room, then re-read —
   the announcement room is unchanged (§16.1 item 6 of F4.8).
3. Appointment with no room ⇒ empty room fields + `room_source` empty, not `"null"`, not the branch default.
4. Walk-in ⇒ empty room fields; with R2, a captured room round-trips and an invalid room id is rejected with
   4xx (not a 500).
5. **Authorization, both directions**: same-organization staff allowed; a staff member of another
   organization gets the same 403/404 as any other entry today; a branch the user cannot access is refused;
   no room value appears in any denial body.
6. Query count: `get_queue` for a page of N entries issues a constant number of statements (no N+1) — assert
   with a statement counter.
7. TTS route (Stage E): unauthenticated ⇒ 401/403; other-organization ⇒ refused; oversized text ⇒ 422;
   over budget ⇒ documented refusal; rate limit ⇒ 429 **with** `X-RateLimit-*` headers; `RateLimitMiddleware`
   is still absent from the app's middleware stack.

### 16.3 Contract layer

1. The queue response schema change is additive and reflected in the OpenAPI document; a snapshot test
   records the four new fields so a future removal is a test failure.
2. The TTS endpoint (if built) appears in `/openapi.json` before any frontend code uses it — no invented
   route may be called from the panel.
3. No existing field is renamed or removed; the queue response diff must contain only additions.

### 16.4 Browser layer (real browser, Playwright or manual protocol)

1. **Local playback** — install assets, play a call, assert the panel reaches `completed` **and** that the
   audio actually produced output (listen + assert `durationMs` ≈ `expectedMs`); a panel saying "played" over
   silence is the F2 defect returning.
2. **Interruption** — cancel mid-announcement, assert `interrupted` and no trailing clip.
3. **Watchdog** — stub a media element that never fires `ended`, assert `failed/watchdog` within the bound.
4. **Offline** — DevTools *Offline* after install, play again, assert `completed`; then hard-reload and play,
   asserting the service worker still serves from cache.
5. **Corrupt clip** — replace a cached clip's bytes, replay, assert `failed/decode` and a repair prompt.
6. **Partial install** — interrupt install at 40 %, reconnect, assert the resume continues instead of
   restarting.
7. **No audio output** — mute/select a null sink where possible, assert `failed/output` and visible copy.
8. **Autoplay policy** — a fresh page with no gesture must show **Enable announcements**, and the first
   click must unlock playback; assert there is no silent retry loop.
9. **Room absent** — an entry with no room announces the room-less variant and shows `reason: 'no_room'`.
10. **Dedupe** — two rapid calls for the same token say nothing the second time and clearly report
    `duplicate`; a manual announcement still plays.
11. **Language switch** — after switching language, no clip from the previous language plays (assert the
    plan's `language`).
12. **Accessibility** — keyboard-only operation of the panel; `aria-live` announces the status change
    without stealing focus; axe scan clean on the panel; contrast of the status chips ≥ 4.5:1.
13. **Responsive** — panel and status text usable at 1920×1080, 1440×900, 1280×800, 1024×768, 768×1024,
    430×932, 390×844, 375×812 with no horizontal overflow.
14. **Console hygiene** — no unhandled promise rejections, no autoplay warnings storm, no errors on a normal
    successful announcement.

### 16.5 Physical device layer (the only place area 15 can be signed off)

| Check | Method |
|---|---|
| Intelligibility at 5–8 m with realistic ambient noise | listen from the waiting area, at the intended volume, with people talking |
| Bangla naturalness (locative rooms, numbers 21–99, doctor names) | native-speaker listener signs off per clip family |
| Device matrix | at least one Chrome/Edge PC, one Firefox, one Safari/iPad (exercises the MP3 fallback), one low-end Android tablet |
| Cold start | power-cycle the display device, confirm the announcement works without a manual install (assets persisted) |
| Cache eviction | fill browser storage to evict audio, confirm the panel re-probes and offers re-install rather than failing silently mid-sentence |
| Volume/level consistency between clips | listen for jolts between a recorded phrase and a recorded number |
| Dual-device race | two operator screens on the same branch calling at once — confirm no interleaved audio and no double announcement |

### 16.6 Ratified-criteria traceability

Each ratified QUE-006 acceptance criterion (§1.7) mapped to the test that would prove it, and to its status
today. "Not met today" is a statement about the code at `37cf3d1`, not about this document.

| # | Criterion | Proven by | Status today |
|---|---|---|---|
| C1 | Bangla announcement on a call event | §16.4 item 1 + §16.5 native-speaker sign-off | **Not met** — no Bangla audio path exists; browser TTS refuses when no Bangla voice is present |
| C2 | English announcement on a call event | §16.4 item 1 | Partially met — browser TTS only, and the sentence is the wrong sentence (F1) |
| C3 | Language configurable per facility | §16.2 item 1 equivalent for settings; UI test §16.4 item 11 | **Not met** — no configuration storage inspected in the announcement path |
| C4 | Enable/disable per facility | same | **Not met** — the panel's switch is not a facility setting |
| C5 | Triggered by appropriate queue events | §16.4 item 10, §16.1 item 10 | **Not met** — trigger is a manual button on `called` rows only (`queue.js:57-66, 202`) |
| C6 | No duplicate/conflicting announcements for one event | §16.1 item 9, §16.4 item 10 | **Breached** — F3: one-slot store, and failures are remembered as successes |
| C7 | Voice failure does not fail the queue call | §16.2 (call succeeds with audio stubbed to fail) | Met in structure — the call is committed server-side before audio; needs an explicit regression test |
| C8 | Only org/branch admin may configure | §16.2 item 7 pattern, applied to the settings write | Not applicable yet (no settings write exists) |
| C9 | No unnecessary PII | §16.1 item 11 (extra payload fields cannot change the plan), §16.4 item 1 | Met by construction in `content.js`, but the allow-list becomes explicit only in `plan.js` |
| C10 | Audio output verified at browser/runtime | §16.4, §16.5 | **Not done** — no browser or device verification exists for OD-1 |

Two consequences worth stating plainly: **C6 is the criterion F3 breaches**, which raises F3 from "design
smell" to "ratified acceptance criterion unmet"; and **C10 means no announcement implementation may be
reported as implemented-and-verified until a browser and a physical device have been listened to.**

### 16.7 What this plan explicitly does **not** claim

1. No tests were executed for this document. The counts quoted (49 existing) are read from the suite, not
   re-run.
2. Browser and device verification are **planned**, not performed.
3. Passing every row above proves the announcement system behaves as specified; it does not prove the queue
   itself is correct, nor that a patient reached the right room.

---

## 17. Risks, dependencies and open questions

### 17.1 Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | Recorded catalogue is not produced, so the architecture has no sound to play | medium | high (feature blocked) | Stage A/B deliver value with no assets; Stage C is gated on a signed-off recording session, not on code |
| R-2 | Bangla locative rooms sound wrong | medium | medium (credibility) | locative clip strategy (§5.2 A) + native-speaker sign-off per room |
| R-3 | Wording approval of the room-less Bangla sentence is never given | medium | low (room-less Bangla stays silent-with-reason) | explicit `reason: 'no_room'`; English unaffected |
| R-4 | Staff read "Failed" as a regression | medium | low | release note + runbook (§14.4) |
| R-5 | Asset install never happens on the real display device | medium | medium | install affordance + cache probe + honest "Streaming" state |
| R-6 | Doctor-name recordings raise consent/HR questions | medium | low (feature optional) | opt-in, revocable, omit segment if absent |
| R-7 | External TTS is enabled without the quality gate | low | high (unintelligible public speech) | disabled by default; gate in §10.3; config ownership question §18 D-2 |
| R-8 | Announcements are wired to a public board beyond the PQV decision | low | high (privacy) | §11.5; OD-4 remains the deciding record |
| R-9 | Retry logic double-announces | low | medium (confusing, not harmful) | per-event store keyed store, exponential backoff, `maxAttempts` 3, no retry for non-transient outcomes |
| R-10 | Device audio stack behaves differently than stubbed tests suggest | medium | medium | injected-audio unit tests **and** real-browser + physical-device verification before acceptance |
| R-11 | A future field is added to the queue payload and leaks into audio | low | high (privacy) | allow-list construction in `plan.js` (§11.2) + a test that a payload with extra fields produces an unchanged plan |

### 17.2 Dependencies

| Dependency | Needed by | Status |
|---|---|---|
| Approved English wording | Stage A | the sentence with "please proceed to" is quoted in this document; confirm at Stage A |
| Bangla wording approval (incl. room-less) | Stage D | **open** (§18 O-3) |
| Recording talent and studio time | Stage C/D | not started |
| Native-speaker reviewer | Stage D | not arranged |
| OD-2 configuration ownership | any settings surface | **partially answered** — enable/disable + language are facility-owned per `MVP_Feature_Catalogue…:548, :1116`; engine/TTS-spend/install ownership still open (§12.3) |
| Facility's room list (ids + names) for locative clips | Stage D | available from master data |
| Device matrix availability (incl. Safari/iPad) | Stage F | not arranged |
| External-TTS provider + budget | Stage E | **open** (§18 O-4) |

### 17.3 Open questions, each with a proposed default (not a decision)

| # | Question | Proposed default if unanswered | Consequence of the default |
|---|---|---|---|
| O-1 | May a facility choose **manual-only** announcements instead of announce-on-call? | announce on the call event (ratified criterion C5), with manual play/replay always available; no manual-only mode until approved | facilities that prefer silence on call have only the master switch, which is coarser |
| O-2 | May the doctor segment be omitted (privacy / a doctor's opt-out / no recording)? | omit only when the facility has said so; otherwise refuse with `missing_doctor_name` (today's behaviour) | no silent wording change |
| O-3 | What is the approved room-less Bangla sentence? | speak nothing in Bangla when there is no room, with `reason: 'no_room'` | Bangla room-less calls are silent but honest |
| O-4 | Is external TTS approved commercially (per-character cost) and by whom? | disabled | fallback unavailable; recordings only |
| O-5 | Which Bangla dialect/voice, and who owns the recordings? | facility-chosen, CarbonTally-released catalogue | catalogue ownership stays with the platform |
| O-6 | Should walk-ins capture a room at registration (R2)? | no capture in Stage A; room-less variant | walk-in announcements lack a room until R2 |
| O-7 | Where are assets hosted (frontend host vs CDN)? | frontend host, versioned directory | a later CDN move is a config change (`assetBaseUrl`) |
| O-8 | Are announcement attempts logged server-side (ANN-008)? | client-side panel only | no new table; weaker audit of "was the patient called audibly" |
| O-9 | Language per facility or per branch? | per facility — **ratified** (C3); open sub-question: may a branch override its facility? | a bilingual facility cannot mix languages per desk |
| O-10 | May the DQDS public board show rooms? | unchanged — **not** granted here | public display shows token + state only (OD-4) |

---

## 18. Owner-approved versus engineering recommendation

This section exists so no reader mistakes a design choice for a product decision. It is the **only** place
in this document where the two are separated; everything above describes the design, and everything below
assigns authority.

### 18.1 Owner-approved (given for this task, implemented as specified)

| # | Approved item | Where it lands |
|---|---|---|
| A-1 | Primary announcements use **locally stored pre-recorded Bangla/English clips assembled at playback time** (phrase + number recordings) | §4, §5, §6 |
| A-2 | Announcements are **offline-capable after install** | §7.3 |
| A-3 | **External TTS is an optional fallback**, not the primary mechanism | §10, §4.4 |
| A-4 | **Browser speech synthesis is an optional alternative only** — never the assumed primary, never an automatic Bangla substitute | §4.4, §8.2 |
| A-5 | **Queue operations never depend on audio**; audio failure cannot block, delay or roll back a call | §4.6 step 6, §8.3 |
| A-6 | **No patient identity or clinical information is announced** — token, doctor, room, action only | §11.1 |
| A-7 | The English sentence must include **"please proceed to"** (F1) | §3.1, §6.2 |
| A-8 | Success must mean **the announcement completed**, not started (F2) | §3.2, §8.1 rule 1 |
| A-9 | Deduplication must not become a **permanent** block on a legitimate repeat (F3) | §3.3 F3.4 |
| A-10 | The room announced is the **appointment snapshot**, never the current schedule (F4) | §3.4, §9 |
| A-11 | This work modifies no existing repository file (design task only) | completion report |
| A-12 | Ratified by the approved MVP Feature Catalogue for QUE-006: announcement **enable/disable and language are facility-owned settings**, configurable only by `super_admin`/`org_admin`/`branch_admin`; announcements are **triggered by the queue call event**; `receptionist`/`doctor` trigger them | §12.1, §12.3, §13.3 (`MVP_Feature_Catalogue…:546-559`, `:1109-1118`) |
| A-13 | Ratified: **actual audio output must be verified at browser/runtime before implementation is claimed** | §16.4, §16.5, §16.6 (same file `:1118`) |

### 18.2 Engineering recommendation (proposed here; requires approval before implementation where marked)

| # | Recommendation | Marked |
|---|---|---|
| D-1 | Stage ordering A→B→C→D→E→F, with Stage A shipping independently | propose |
| D-2 | Configuration ownership: **ratified** for enable/disable and language (facility, per A-12). Still open — and therefore not exposed — for **engine preference, external-TTS spend, and catalogue install** | **DECISION REQUIRED, narrowed (OD-2 residual)** |
| D-3 | Announcement content stays within the PQV public-display permission set, so audio can never exceed what a public board may show | propose |
| D-4 | Room data path: R1 (read-through join) first, R2 (snapshot columns + walk-in capture) later; never `ScheduleSession.room` | propose |
| D-5 | Opus/WebM primary with MP3 fallback, versioned asset directories, manifest with `sha256` | propose |
| D-6 | Asset-scoped service worker only (no app-shell PWA), explicit install action | propose |
| D-7 | Terminal outcome vocabulary `completed/failed/interrupted/cancelled/blocked/busy/unavailable/skipped/duplicate`; `started` is a progress event, never an outcome | propose |
| D-8 | Dedupe store: per-event key, 10-minute completed TTL, `maxKeys` 512, `maxAttempts` 3, exponential backoff, injected clock, no timers | propose |
| D-9 | Bangla numbers 0–99 recorded whole (no composition below 100 because the cardinals are irregular) | propose |
| D-10 | Bangla rooms use **locative recordings** per room rather than a suffix clip | propose |
| D-11 | Bangla room-less announcement needs new approved wording; until then, silence with `reason: 'no_room'` | **DECISION REQUIRED (O-3)** |
| D-12 | Doctor-name recordings are opt-in per doctor; the honorific is stripped before joining a name | **DECISION REQUIRED on consent policy (O-2/O-5)** |
| D-13 | External TTS enabled only after a native-speaker listening gate, with a per-organization daily character budget | **DECISION REQUIRED (O-4)** |
| D-14 | Announcement trigger: **announce on the queue call event** (ratified C5), with manual play/replay as an operator affordance; a manual-only facility mode is not approved | **ratified in part; residual DECISION on manual-only mode (O-1)** |
| D-15 | No server-side announcement attempt log unless ANN-008 is approved; client-side panel state only | **DECISION REQUIRED (O-8)** |
| D-16 | TTS synthesis cached as facility assets, so a fallback becomes local on second use | propose |
| D-17 | Physical-device listening verification is a release gate for Stage C/D acceptance | propose |

### 18.3 What is *not* decided by this document

1. **OD-2 (residual)** — engine preference, TTS spend and catalogue-install ownership are open (§12.3). The
   enable/disable + language ownership is *not* open: it is ratified (A-12).
2. **O-1…O-10** — each has a proposed default that is safe (does less, claims less), but a default is not an
   approval; O-9's "per facility" part is ratified (C3) while a branch override is not.
3. **OD-4 / DQD-002** (public board room visibility) — untouched.
4. **Bangla wording** beyond the quoted segment structure in §6.3 — the room-less sentence and any wording
   variant needs owner approval.
5. **Commercial terms** for any external TTS provider.
6. **Any compliance, accessibility-certification or medical-device claim** — none is made, and none may be
   inferred from this design.

---

## Appendix A — Source evidence index

All paths are relative to the repository root; all line numbers are as inspected at
**branch `hackathon-mvp`, HEAD `37cf3d1e9db76834044afd48fa5729463a26ec47`** (clean working tree, 0
modified, 0 untracked, no stashes). Line numbers drift with later commits; the quoted behaviour, not the
number, is the claim.

### A.1 F1 — wording

| Evidence | Location |
|---|---|
| Defective sentence template, missing "please proceed to" | `frontend/lib/announcements/content.js:36` |
| Sentence assembly and derived-field flags | `frontend/lib/announcements/content.js:106-124` |
| Blind `"Dr. "` prefix (source of the `Dr. Dr.` defect) | `frontend/lib/announcements/content.js:121-124` |
| Tests asserting the defective sentence | `frontend/tests/queue-announcement-content.test.mjs:37,43` |
| Test asserting duplicated honorific output | `frontend/tests/queue-announcement-content.test.mjs:112-113` |

### A.2 F2 — success reported on start

| Evidence | Location |
|---|---|
| `SPOKEN` defined (meaning "started") | `frontend/lib/announcements/speech-synthesis.js:33` |
| `onstart` settles `SPOKEN` | `frontend/lib/announcements/speech-synthesis.js:256-267` |
| `onend` is a no-op (never recorded) | `frontend/lib/announcements/speech-synthesis.js:268-276` |
| Operator-facing copy says "played" | `frontend/lib/announcements/speech-synthesis.js:216` |
| Honest-degradation precedent to generalise | `frontend/lib/announcements/speech-synthesis.js:128-131` |
| Activation / user-gesture handling | `frontend/lib/announcements/speech-synthesis.js:150-160` |
| Pause-halving and voice preference (retained) | `frontend/lib/announcements/speech-synthesis.js:180-240` |

### A.3 F3 — single-slot deduplication

| Evidence | Location |
|---|---|
| One `lastEventKey` / `lastEventAt` pair | `frontend/lib/announcements/controller.js:62-63` |
| Event key marked before the attempt | `frontend/lib/announcements/controller.js:195-202` |
| Failure paths leave the key marked | `frontend/lib/announcements/controller.js:204-207`, `:213` |
| Injected adapter seam (interface can be added additively) | `frontend/lib/announcements/controller.js:45-47` |
| `source: 'event' \| 'manual'` distinction (retained) | `frontend/lib/announcements/controller.js:113-118` |
| Event key construction (retained identity) | `frontend/lib/announcements/content.js:60-80` |

### A.4 F4 — room unavailable

| Evidence | Location |
|---|---|
| Queue serializer emits no room | `backend/queuing/main.py:82-92` |
| Frontend reads the non-existent `entry.room` | `frontend/pages/queue.js:64-65` |
| Queue authz / org+branch scoping | `backend/queuing/main.py:120-160`, `:190-230`, `:330-360` |
| `get_queue` and its serializer call sites | `backend/queuing/main.py:137-151`, `:269`, `:361`, `:456`, `:583` |
| Check-in creates the entry | `backend/queuing/main.py:230-238` |
| Walk-in creation (`appointment_id = NULL`) | `backend/queuing/main.py:284-300` (walk-in at `:293`) |
| Actions audit without audio | `backend/queuing/main.py:400-470` |
| **Authoritative** appointment room snapshot | `backend/appointment/models.py:616-630` (`room_id`, `room_name`, `location_source`) |
| Location label helper (reuse) | `backend/appointment/main.py:238-241` |
| Appointment API already serialises the snapshot | `backend/appointment/main.py:278` |
| Public-display permission set (not widened here) | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md:57-67` |

### A.5 Environment facts

| Fact | How verified |
|---|---|
| `frontend/public/` is empty; no service worker, no web-app manifest, no PWA anywhere | directory listing + repository-wide search |
| No `Audio` / `AudioContext` / media-element usage exists today | repository-wide search |
| `frontend/pages/queue-display/` exists (a dedicated display surface is already present) | directory listing |
| Announcement test suite: 49 tests (11 content, 15 controller, 18 speech, 5 boundary) | test file inventory (**read, not run**) |

### A.6 Ratified product record consulted

| Evidence | Location |
|---|---|
| Decision-log entry (approved 2026-11-17) | `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md:542` |
| QUE-006 module: description, expected roles, expected behaviour | same file `:544-559` |
| QUE-006 acceptance criteria (the ten criteria quoted in §1.7) | same file `:1108-1118` |
| Earlier Phase 3 gap analysis recording the Bangla-voice risk (ANN-003) | `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md:907-913` |

These lines are quoted, not paraphrased, in §1.7. They change two things this design had been treating as
open (trigger, and enable/language ownership); §1.7 records the correction explicitly rather than absorbing
it silently.

---

## Document control

| Field | Value |
|---|---|
| Document | AMSDP-QUE-006 Local Audio Announcement Architecture and Implementation Plan |
| Version | 1.0 |
| Task | AMSDP-QUE-006-LOCAL-AUDIO-DESIGN-01 (read-only design) |
| Branch / HEAD | `hackathon-mvp` / `37cf3d1e9db76834044afd48fa5729463a26ec47` |
| Repository changes made | **none** — this document is the only artefact |
| Tests run | **none** (design task) |
| Verification performed | source inspection only; no browser, device or runtime verification |
| Related documents | `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` (ratified acceptance baseline, §1.7); `docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md`; `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` |
| Supersedes | nothing — OD-1's implementation record remains the description of what is deployed today |
| Status of this design | proposed; implementation gated on §18.2 decisions where marked |

### Version history

| Version | Change |
|---|---|
| 1.0 | First issue: OD-1 assessment, four finding remediations, local audio architecture, catalogue, composition, storage/caching, engine, room data path, optional TTS, security, configuration ownership, impacts, migration, staged plan, test strategy. Also records the ratified QUE-006 acceptance baseline (§1.7) and traces the ten criteria to tests (§16.6); on that evidence, the announcement trigger and the facility ownership of enable/disable + language are **ratified, not proposed**, and OD-2 is narrowed accordingly |

---

*End of document.*
