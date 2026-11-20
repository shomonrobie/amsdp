# AMSDP QUE-006 / OD-1 — Browser Speech Synthesis Implementation Report

| Item | Value |
|---|---|
| Document | `docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md` |
| Version | 1.0 |
| Date | 2026-11-20 |
| Task | Implement QUE-006 under owner decision **OD-1**: the browser-native Web Speech API (`window.speechSynthesis`), no provider, no outbound call |
| Branch / HEAD | `hackathon-mvp` @ `6b7ef4d27edbf820bfcafc25a9c789235337823d` — unchanged by this task, nothing staged, committed or pushed |
| Working tree at start | 35 modified + 12 untracked paths, all pre-existing (Phase 2 appointment remediation, owner decisions Q1–Q5, operational RBAC follow-up, QUE-006 documentation). All preserved; see §13 |
| Location rule applied | `.clinerules` §11 — subject subfolder `docs/implementation/`; destination collision checked first (`ls` returned “No such file or directory”), so nothing was overwritten |
| Feature dispositions | Unchanged. QUE-006 remains **KEEP** / AMSDP Core per the Product Owner MVP scope lock (2026-11-17) |
| Evidence status | **IMPLEMENTED** and **TESTED** (§10). **NOT VERIFIED** — no browser/device run was performed, so no audible-playback claim is made (§11). **NOT ACCEPTED** — acceptance is a Product Owner act |
| Skills | **None installed** (`.clinerules` §5). Governance documents applied directly |

---

## 1. Scope

In scope: the reusable speech-synthesis adapter, the approved Bangla/English content,
language-aware voice selection, missing-voice and autoplay/activation handling, duplicate
and overlap control, operator-visible state, an operator boundary on `/queue`, and
automated tests — all in `frontend/`.

Out of scope and deliberately untouched: backend code, API contracts, schema,
migrations, role permissions, facility configuration storage (OD-2), the queue event
contract (ANN-002), server-side announcement audit (ANN-008), recall (QOP-003) and the
`call` action's missing UI (QOP-001). Each is recorded as an open item in §12.

---

## 2. What was built

| File | Change | Purpose |
|---|---|---|
| `frontend/lib/announcements/content.js` | **new** | The only place announcement wording is assembled: approved OD-3 templates, the read-aloud token serial, digit conversion, the event key. Pure — no DOM, no timers |
| `frontend/lib/announcements/speech-synthesis.js` | **new** | The single seam over `speechSynthesis`: capability probe, voice selection, `speak()`, cancel, `voiceschanged` subscription, dispose. Never throws, never rejects |
| `frontend/lib/announcements/controller.js` | **new** | The decisions: facility switch, duplicate suppression, one-at-a-time playback, activation state, the observable outcome of the last attempt |
| `frontend/components/queue/QueueAnnouncements.js` | **new** | Thin React shell: capability/activation badge, "Enable audio" gesture, last-announcement line; renders only after mount |
| `frontend/pages/queue.js` | **modified** | Mounts one announcer, renders the panel, offers an **Announce** action on a `called` entry. Queue state, actions and permissions unchanged |
| `frontend/lib/i18n.js` | **modified** | 17 new captions, added to **both** dictionaries (bn + en) |
| `frontend/tests/queue-announcement-content.test.mjs` | **new** | 11 tests — wording, token pronunciation, PII boundary, event keys |
| `frontend/tests/queue-announcement-speech.test.mjs` | **new** | 18 tests — voice choice, silence≠success, overlap, cancellation, cleanup |
| `frontend/tests/queue-announcement-controller.test.mjs` | **new** | 15 tests — switch, dedupe, activation recovery, busy, observability |
| `frontend/tests/queue-announcements-boundary.test.mjs` | **new** | 5 tests — JSX compilation, bilingual captions, "announcing is not a queue action", post-mount rendering |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | **modified** | Revision 34 + this report's row |

No backend file, migration, compose file, endpoint, permission map or product document was
modified. `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` is
Product-Owner-controlled and was **read but not edited** — its QUE-006 status cells
(`NOT STARTED` / `NOT TESTED`, lines 577–581, 976, 1266) are now stale and are a
Product Owner update, not an agent one (§12, O-9).

---

## 3. Mechanism and boundary (OD-1)

The announcement is generated **in the browser** by `window.speechSynthesis`, with no server
call, no provider, no audio asset and no patient-identifying data leaving the page.

Four things are kept strictly separate, as the task requires:

1. **Queue action `call`** — a backend state transition (`waiting|skipped → called`,
   `PATCH /api/v1/queue/{id}`). Untouched by this task.
2. **Queue recall** — does not exist yet (`QOP-003`); nothing here invents it.
3. **QUE-006 audible announcement** — a client-side playback of a `called` entry. It sends
   **no HTTP request** and cannot change queue state; proven by a test (§10).
4. **Outbound telephone calls** — excluded by OD-1 and the catalogue; no telephony code is
   involved.

The operator's queue list is therefore exactly as correct with audio broken, blocked or
absent as it is with audio working. The announcement path never returns a promise the queue
page awaits before rendering, and every failure mode is an outcome object, not an exception.

---

## 4. Content (OD-3)

`lib/announcements/content.js` holds the approved strings verbatim:

| Language | Template (OD-3) |
|---|---|
| Bangla | `টোকেন নম্বর [সংখ্যা], ডা. [ডাক্তারের নাম], কক্ষ [কক্ষ নম্বর]-এ আসুন।` |
| English | `Token number [number], Dr. [doctor name], Room [room].` |

Decisions inside this module, each with a test:

- **The token is never spoken raw.** A real token is `T-<doctor-id fragment>-<serial>`
  (`backend/common/queue_tokens.py:20-22`), so speaking it would read an internal
  identifier aloud. Only the trailing serial is spoken, as a plain number
  (`T-3F2A9C-004 → 4`). A UUID, a 32-hex string or a token with no digits is **refused**
  (`unspeakable_token`) rather than read out.
- **Bangla announcements use Bangla digits** (`৪`, not `4`) so a Bangla voice reads a
  number rather than a glyph name.
- **Patient identity cannot enter the text.** Only three fields are read — `token`,
  `doctorName`, `room`. `patientName`, `patient_id`, `mobile`, `notes` and the rest are
  ignored, and a test asserts the sentence is identical with and without them.
- **A missing doctor name or an unknown language is refused, not guessed.** There is no
  silent fallback to English (or to another language) anywhere in the path.

**Room clause — documented dependency, not an invention (O-1).** No queue endpoint returns a
room: `_entry_to_dict` (`backend/queuing/main.py:82-92`) carries none, and the room lives on
chambers/sessions, not on a queue entry. The approved template's room clause is therefore
**dropped** rather than filled with a guess:

- bn: `টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, আসুন।`
- en: `Token number 4, Dr. Rahim Uddin.`

Both are marked `fields.derived = true`. They are the approved sentence minus one segment,
and they are the variants a facility will actually hear until either (a) the owner approves
the room-less wording, or (b) a room is added to the announcement payload. This is an
**owner decision**, raised as **O-1**.

---

## 5. Voice selection, missing voices and language honesty

| Rule | Behaviour | Test |
|---|---|---|
| A voice must match the language asked for | only `bn` / `bn-*` voices can read Bangla; only `en` / `en-*` can read English | `a voice is only chosen for the language that was asked for` |
| Prefer the primary tag | `bn-BD` before `bn-IN`; `en-GB` before `en-US` | same test + `another region of the same language is a marked fallback` |
| Prefer a local voice | `localService` beats a network voice (a facility's link may be down) | `a local voice is preferred over a network voice` |
| **Never substitute a language** | Bangla text with no Bangla voice → `no_voice`, nothing is spoken | `Bangla without a Bangla voice refuses instead of using English` |
| Distinguish "not loaded yet" from "not installed" | empty voice list → `pending_voices`; a loaded list with no match → `no_voice` | `capability distinguishes "no voices yet" from "no voice for this language"` |
| Voices arrive asynchronously | `voiceschanged` is subscribed and released on dispose | `voice changes are subscribed and unsubscribed cleanly` |
| A broken engine is not a broken page | a throwing `getVoices()`/`speak()` becomes `pending_voices`/`error` | `a throwing getVoices() …`, `a throwing engine becomes an error result` |

The panel shows the fallback explicitly ("No bn-BD voice — using another Bangla voice"), so a
facility is never told Bangla is available when the device is reading it with, say, `bn-IN`,
and Bangla is never silently read through an English voice.

---

## 6. Activation, autoplay and "audio off"

- **Silence is not success.** `speak()` resolves `spoken` only when the engine reports
  `start` (or `end`). If neither arrives within `startTimeoutMs` (1500 ms) the outcome is
  `blocked` (`reason: 'no_start_event'`) and the utterance is cancelled — the browser's
  autoplay refusal, which throws nothing, is therefore detected rather than assumed away.
- **One deliberate gesture unlocks audio.** The panel shows an **Enable audio** button
  whenever the browser supports speech and activation has not been granted. Clicking it
  primes the engine with a silent, language-independent utterance; `spoken` grants
  activation, `blocked` records the refusal (tests: `activating audio is a gesture…`,
  `the priming utterance is silent and needs no voice`).
- **A blocked browser is not hammered.** Once activation is `blocked`, an event-sourced
  announcement returns `needs_activation` **without touching the engine**; only a fresh
  operator click (`userGesture: true`) retries, and success clears the blocked state
  (test: `a blocked browser is not hammered, but a new gesture may recover it`).
- **The operator always sees the state**: `unsupported` / `pending_voices` / `no_voice` /
  blocked / off / on, plus the last outcome and the last spoken sentence. The state is
  rendered in a `role="status"` `aria-live="polite"` region, so a screen-reader user is told
  when audio changes — the announcement itself is not the only feedback channel.
- **No hydration drift.** The queue page is server-rendered and the server cannot know the
  voice list, so the panel renders `null` until mounted (test: `the panel defers browser
  state until after mount`), matching the DQDS page's established pattern.

---

## 7. Duplicate and overlap policy

| Situation | Answer | Where |
|---|---|---|
| The same queue event delivered twice | one announcement. The event key is `event:<id>` or `entry:<queue entry>:<action>:<revision>`; a repeat inside `dedupeWindowMs` (default 5 s) returns `duplicate` **without reaching the engine** | `controller.announce`, tests `the same queue event is spoken once`, `…after the suppression window`, `a different event is never suppressed` |
| A second announcement while one is playing | `busy` — never overlapped. A single-slot policy, no hidden queue | `adapter.speak`, test `one utterance at a time…` |
| A superseded utterance (`replace: true`) | the first resolves `cancelled`, the new one plays | same test |
| The operator wants to say it again | `source: 'operator'` bypasses duplicate suppression, because a repeat is intent, not a duplicate | test `an operator repeat is deliberate and bypasses suppression` |
| Browser refresh / reconnection / two operators / several doctors | **not solved here** — these need the server-side event contract and its idempotency key (ANN-002, O-3) | §12 |
| A recall replacing an earlier call | **not solved here** — recall does not exist yet (QOP-003, O-4) | §12 |

The suppression window is a client-side guard over what the client is told, not a substitute
for server-side idempotency; the report does not claim otherwise.

---

## 8. Observability

Every attempt produces a visible, structured record — outcome, language, event key and
reason — and the operator sees the last one on the panel. The record deliberately contains
**no spoken sentence and no patient data**: a test asserts the exact key set of the log line
(`outcomes are observable without leaking the spoken text`).

This satisfies the *"visible or logged"* half of ANN-008 at the client boundary. The
**server-side** half — a durable `queue.announcement.played/.failed/.skipped` audit event —
requires the queue event contract and is **not implemented** (O-3). No announcement is
therefore recorded in the audit trail today, and this report does not claim it is.

---

## 9. Operator surface

On `/queue` (unchanged filters, table and actions):

- a status card above the table: capability badge, **Enable audio** (only when a gesture is
  needed and the role may trigger), the voice-fallback note, the "no Bangla voice" note and
  the last outcome with the last spoken sentence;
- an **Announce** button in the actions column of a `called` entry, offered to the roles the
  catalogue names as triggers (`queue.manage` — front desk/admin, or `queue.consult` —
  doctor). It is disabled while another queue action is in flight and does not alter
  permissions, statuses or the transition table;
- it is *not* a `call` button. `waiting → called` still has no UI (QOP-001, O-7), so today a
  `called` entry reached through the API is the thing an operator can re-announce. This is a
  deliberate boundary, not an oversight: implementing `call` would be a queue-operations
  change and needs the OD-5 answer.

Facility enable/disable and language selection are **not** in this build (OD-2, O-2). Until
that configuration exists, the client speaks the operator's current interface language and
defaults to Bangla; it never guesses a third option.

---

## 10. Tests and verification performed

**Command** (the project's own frontend suite; no dependency added):

```bash
cd /home/shomonrobie/amsdp/frontend && npm test
# → node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs
```

**Result — ran successfully, in this tree, on 2026-11-20:**

```
ℹ tests 229
ℹ suites 0
ℹ pass 229
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2143.33728
exit=0
```

Baseline before this task was **180** frontend tests; this task adds **49** (11 content +
18 adapter + 15 controller + 5 boundary), and **every pre-existing test still passes**. The
JSX-compilation test in the boundary suite ran rather than skipped, so `next/dist/build/swc`
was available and the new page/component genuinely parse.

**Not run, and why:**

| Suite | Why not run |
|---|---|
| `backend/**` tests | No backend file was touched. Note that `backend/queuing/tests/test_queue.py` carries the destructive fixture recorded as **QOP-012**; it was neither run nor modified |
| `next build` | A browser console from a *different* application was attached to the shared terminal during this task (its bundle path is `static/js/bundle.js`, a create-react-app artefact, not this Next.js frontend), so it is not evidence about this checkout. `next build` was still avoided because it rewrites the shared `.next` directory and a development server may be running against it; compilation was therefore proven with the repository's own SWC JSX test instead. The application was not rebuilt or restarted |
| Browser / device playback | Not performed — see §11 |

**Test map to the acceptance criteria of the task** (no criterion is claimed beyond the
status it earns):

| Criterion | Status | Evidence |
|---|---|---|
| 1. Reusable, isolated adapter | **IMPLEMENTED + TESTED** | `lib/announcements/speech-synthesis.js`; 18 adapter tests; no React or page knowledge in it |
| 2. Language-aware voice selection | **IMPLEMENTED + TESTED** | `pickVoice`; 4 tests |
| 3. Missing voice handled without wrong-language speech | **IMPLEMENTED + TESTED** | `no_voice` / `pending_voices`; 3 tests |
| 4. User-activation / autoplay | **IMPLEMENTED + TESTED** (unit) — **NOT VERIFIED** (device) | activation + `no_start_event` logic; 4 tests |
| 5. Playback cannot block queue operations | **IMPLEMENTED + TESTED** | outcomes never throw; test `announcing is not a queue action`; the panel awaits nothing |
| 6. Duplicate/overlap controlled | **IMPLEMENTED + TESTED** | 6 tests (§7) |
| 7. Content per OD-3, no invented fields | **IMPLEMENTED + TESTED**; one **owner decision open** (O-1, room clause) | 11 content tests |
| 8. Bilingual, approved wording | **IMPLEMENTED + TESTED** | exact-string assertions, both languages |
| 9. Automated tests | **DONE** | 49 new tests, command and result above |
| 10. Honest status reporting | **DONE** | this section and §11 |

---

## 11. Browser / device verification — NOT PERFORMED

No browser was driven and no device was listened to. Therefore:

- **Bangla audio output is NOT VERIFIED.**
- **English audio output is NOT VERIFIED.**
- **Autoplay behaviour on the target kiosk/TV is NOT VERIFIED** (the code detects a refusal;
  that detection has only been proven against a fake engine).
- **Bangla voice availability on the deployment device is NOT VERIFIED** — no device/voice
  matrix exists, which is ANN-003's remaining acceptance condition.

The unit tests prove the decisions and the wiring, not that a human heard a sentence. A
recorded playback run (Bangla configured, English configured, no-Bangla-voice fallback, and a
blocked-autoplay run) is required before QUE-006 may be described as VERIFIED, and the
catalogue's ten acceptance boxes remain unchecked.

---

## 12. Gap-analysis findings — what moved, and what did not

| Finding | Before | After this task |
|---|---|---|
| ANN-001 No announcement capability | NOT IMPLEMENTED | **PARTIALLY IMPLEMENTED** — a browser mechanism exists and is tested, but is not wired to a server queue event (O-3) |
| ANN-002 No announcement event contract | NOT IMPLEMENTED | **UNCHANGED** — the client accepts an optional `eventId` and derives a key, but no server event exists |
| ANN-003 Bangla/English strategy, voice availability unproven | NOT IMPLEMENTED | **PARTIALLY IMPLEMENTED** — strategy and non-substitution implemented and tested; **device voice matrix still absent** (NOT VERIFIED) |
| ANN-004 Configuration surface | NOT IMPLEMENTED | **UNCHANGED** — OD-2 / O-2 |
| ANN-005 Duplicate/ordering/playback state | NOT IMPLEMENTED | **PARTIALLY IMPLEMENTED** — single-client duplicate and overlap control implemented and tested; cross-client ordering, refresh, reconnection and recall remain open (O-3, O-4) |
| ANN-006 Autoplay/permissions/audio-off | NOT IMPLEMENTED | **IMPLEMENTED at the client boundary, NOT VERIFIED on a device** — activation, refusal detection, visible audio-off and a no-audio-blocking path |
| ANN-007 Content, wording, pronunciation | NOT IMPLEMENTED | **PARTIALLY IMPLEMENTED** — approved templates used verbatim; token serial made speakable; room dependency documented (O-1); doctor-name transliteration not implemented (O-8) |
| ANN-008 Observability | NOT IMPLEMENTED | **PARTIALLY IMPLEMENTED** — visible outcome + structured client record with no PII; no server audit event (O-3) |
| ANN-009 No test/verification plan | TEST COVERAGE GAP | **PARTIALLY CLOSED** — 49 tests and the map in §10; the browser playback matrix is still missing (§11) |
| ANN-010 Volume/repeat/voice boundary undefined | NOT IMPLEMENTED | **STATED** — see O-10 |

No finding is claimed closed. "Closed" is not a status this report can confer.

---

## 13. Open items

| ID | Item | Type |
|---|---|---|
| **O-1** | **Room clause.** No queue payload carries a room, so the approved OD-3 template is spoken without it. The room-less variants (bn `…, আসুন।` / en `Token number 4, Dr. Rahim Uddin.`) need Product Owner approval, or a room must be added to the announcement payload | **PO DECISION REQUIRED** |
| **O-2** | Facility enable/disable + language configuration (`organizations.config["queue_announcement_config"]`, OD-2) and its authorization question (the catalogue names `branch_admin`; the notification precedent denies it) | **PO DECISION REQUIRED** |
| **O-3** | Server-side queue event (`queue.called` / `queue.recalled`) with an idempotency key, plus `queue.announcement.played/.failed/.skipped` audit events | Engineering, needs O-4 |
| **O-4** | Recall (`QOP-003`) does not exist, so a recall cannot be announced | Engineering + OD-6 |
| **O-5** | Browser/device verification: Bangla + English playback, blocked autoplay, muted TV, no-Bangla-voice fallback on the real deployment device | Verification |
| **O-6** | `frontend/pages/queue.js` was already modified by another workstream before this task. My edits are additive (one import, one hook, one panel, one button) and that work was preserved; a reviewer should diff it in context | Review note |
| **O-7** | `call` (`waiting → called`) still has no UI (QOP-001). The announcement therefore attaches to an entry that is already `called`; the "call triggers the announcement" journey is not yet reachable from the product | Engineering + OD-5 |
| **O-8** | Doctor-name pronunciation: names are spoken as stored. `BanglaNameSense` covers **patient** names only, so an ASCII doctor name read by a Bangla voice may be mispronounced | **PO DECISION REQUIRED** (ANN-007) |
| **O-9** | The product catalogue still records QUE-006 as `NOT STARTED` / `NOT TESTED` (lines 577–581, 976, 1266). It is Product-Owner-controlled; the status cells are now stale and need an owner edit | Owner |
| **O-10** | Volume, repeat count and voice selection are **out of scope**: volume is the device's own level, one utterance per event, no voice picker. Only enable/disable and language are intended knobs (and even those await O-2) | Scope statement |

---

## 14. Governance and skill compliance (`.clinerules` §6)

**Applicable governance documents, and how they were followed:**

| Document / rule | Application |
|---|---|
| `.clinerules` §1 precedence | Verified runtime state first: branch, HEAD, the queue payload shape, `queue_tokens.py` and the frontend test runner were inspected before any code was written; the catalogue's stale status was reported rather than "fixed" |
| §2 automatic routing | Routed as **Frontend UI** + **Queue/workflow** + **documentation**; read `AMSDP_Docs_Index_V1.0.md`, the QUE-006 gap analysis, the QUE-006 catalogue addition, the product catalogue entry and `frontend/lib/i18n.js` before editing |
| §3 non-negotiables | No secrets logged or exposed; no server-side authorization changed; the UI is not treated as a security boundary (the announcement is a client mechanism with no authority); tenant key, audit trail and migrations untouched; no unverified capability claimed (§11) |
| §4 routing table | `saas-frontend-ux.md` (as adapted) for components/i18n; Business Rules Parts V–VII for the queue boundary; no skill installed, stated here |
| §6 compliance reporting | This section |
| §7 evidence standard | IMPLEMENTED / TESTED / VERIFIED / ACCEPTED used with their defined meanings; nothing is called VERIFIED or ACCEPTED |
| §9 execution boundaries | Only the explicitly requested test suite was executed (§10); no server was started, restarted or rebuilt; no destructive git operation; unrelated work preserved |
| §11 documentation output | Report written under `docs/implementation/`, filename `AMSDP_<Topic>_<Version>.md`, collision checked, no existing document overwritten |
| §12 documentation reading | Index consulted first; only the documents needed were read; every path cited here was opened in this session |

**Skills:** none installed (`.clinerules` §5 — `NONE`). No skill was simulated or claimed.

**Conflicts found:** none between the task, OD-1/OD-3, the catalogue and the code. Two places
where the code and the aspiration differ are recorded rather than silently resolved: the room
clause (O-1) and the missing `call` UI (O-7).

---

## 15. Final state

```
Branch : hackathon-mvp
HEAD   : 6b7ef4d27edbf820bfcafc25a9c789235337823d   (unchanged)
Staged : nothing           Committed: nothing           Pushed: nothing

Added (untracked):
  frontend/lib/announcements/content.js
  frontend/lib/announcements/speech-synthesis.js
  frontend/lib/announcements/controller.js
  frontend/components/queue/QueueAnnouncements.js
  frontend/tests/queue-announcement-content.test.mjs
  frontend/tests/queue-announcement-speech.test.mjs
  frontend/tests/queue-announcement-controller.test.mjs
  frontend/tests/queue-announcements-boundary.test.mjs
  docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md

Modified (only these, by this task):
  frontend/pages/queue.js                     (+ import, hook, panel, Announce action)
  frontend/lib/i18n.js                        (+ 17 captions × 2 languages)
  docs/governance/AMSDP_Docs_Index_V1.0.md    (+ Revision 34, + this report's row)
```

All 35 pre-existing modified files and 12 pre-existing untracked paths are unchanged by this
task. Nothing was staged, committed, pushed, stashed, reset or cleaned.

**Residual limitation, stated plainly:** QUE-006 now has a working, tested, browser-native
announcement mechanism and an operator surface, but it is **not** triggered by a queue event,
**not** configurable per facility, **not** audited server-side, and **not** proven audible on
any device. Those four are the difference between "the mechanism exists" and "the feature
works in a waiting room".

---

## 16. Environment note

The session's working directory was **not** this repository: the agent was launched in
`/home/shomonrobie/ct_93d5cdd`, a different project whose `.clinerules` describe another
application entirely. The task's expected repository was located at `/home/shomonrobie/amsdp`
and verified before any edit — branch `hackathon-mvp`, HEAD
`6b7ef4d27edbf820bfcafc25a9c789235337823d`, matching the task and the gap analysis's recorded
inspection state. All work was done there; nothing in `ct_93d5cdd` was read, modified or
executed against. This is reported rather than assumed away.






