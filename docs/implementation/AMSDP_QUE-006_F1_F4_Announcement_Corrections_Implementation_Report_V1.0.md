# AMSDP QUE-006 — F1–F4 Announcement Corrections Implementation Report

| Item | Value |
|---|---|
| Document | `docs/implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md` |
| Version | 1.0 |
| Date | 2026-11-20 |
| Task | Implement the four findings **F1–F4** of the QUE-006 local-audio plan: the English wording, terminal-outcome honesty, the bounded per-event dedupe store, and the room snapshot on the queue payload |
| Plan of record | `docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md` (§3.1 F1, §3.2 F2, §3.3 F3, §3.4 F4, §6.2/§6.3 wording, §8.2 outcome vocabulary) |
| Predecessor report | `docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md` (the OD-1 mechanism this task corrects) |
| Branch / HEAD | `hackathon-mvp` @ `cd2f9ecdf51b363105214e3ffd504d3adc151ada` (`docs: add AMSDP website content and copywriting proposal`, 2026-11-20 15:03 +0600 — a documentation commit made outside this task). This task staged, committed and pushed **nothing** |
| Location rule applied | `.clinerules` §11 — subject subfolder `docs/implementation/`; destination collision checked against the directory listing first, so nothing was overwritten |
| Feature dispositions | Unchanged. QUE-006 remains **KEEP** / AMSDP Core per the owner MVP scope lock (2026-11-17). This report changes no scope |
| Evidence status | **IMPLEMENTED** and **TESTED** (§8). **NOT VERIFIED** — no browser, device or audible-playback run was performed, so no "the announcement is heard" claim is made (§9). **NOT ACCEPTED** — acceptance is a Product Owner act |
| Skills | **None installed** (`.clinerules` §5). Governance documents applied directly (§7) |

---

## 1. Scope

In scope — the four corrections the plan specifies, and nothing else:

| Finding | Defect the plan records | Correction shipped here |
|---|---|---|
| **F1** | The English sentence omits the approved **"please proceed to"**, and the honorific is hard-coded in the template, so a name already starting "Dr." is spoken twice | One approved template per language, honorific owned by the segment builder and applied exactly once |
| **F2** | `spoken` was reported when the browser reported `start`, i.e. *begun*, not *finished*; a browser that dies mid-utterance was recorded as a delivered call | The six-word terminal vocabulary of plan §8.2; `completed` is emitted **only** on `end` |
| **F3** | One slot remembered a single event key, consumed *before* the attempt, with no notion of what happened to it — so an intervening event un-suppressed an earlier one and a refusal was remembered as announced | A bounded, clock-injected, per-event store whose `state` decides suppression, written *after* the outcome |
| **F4** | No queue payload carried a room, so the approved sentence lost its room clause and the operator could not tell which room the patient would be sent to | Four additive room fields on the queue payload, resolved from the **appointment booking snapshot** in one query per page; the queue page forwards `room_name` to the announcer |

Out of scope and deliberately untouched: the local audio-asset catalogue (plan §5/§7, Stage B/C), the service worker, external TTS, facility configuration storage (OD-2), the server-side announcement event and audit (ANN-002/ANN-008), recall (QOP-003), the missing `call` UI action (QOP-001), schema and migrations. No Alembic migration is part of this task, because no column shape changes: the room fields are derived at read time from columns that already exist on `appointments`.

---

## 2. What was built

| File | Change | Purpose |
|---|---|---|
| `frontend/lib/announcements/content.js` | **modified** | F1 wording; `doctorSegment` / `doctorNameWithoutHonorific` (honorific exactly once); `roomNumberForSpeech` (numeric rooms only); `SKIP_REASON` vocabulary; the Bangla room-less sentence is structurally `null` and refused with `no_room` |
| `frontend/lib/announcements/speech-synthesis.js` | **modified** | F2: `OUTCOME` → `completed / failed / interrupted / blocked / busy / unavailable`; `completed` only on `end`; `start` is progress; no `start` ⇒ `blocked`; legacy names kept as aliases |
| `frontend/lib/announcements/dedupe.js` | **new** | F3: the bounded per-event store (`attempting / completed / failed / interrupted / blocked / exhausted`), injected clock, no timers, deterministic eviction, exponential backoff |
| `frontend/lib/announcements/controller.js` | **modified** | F3 wiring: `shouldSuppress` → `begin` → speak → `settle`; `release()` for `busy` / `unavailable` / `skipped`; one automatic recovery attempt after an operator gesture |
| `frontend/pages/queue.js` | **modified** | F4 wiring: the announcer receives `room: entry.room_name` — the room the payload carries — instead of the stale `entry.room` placeholder |
| `backend/common/locations.py` | **new** | One definition of how a location snapshot reads: `location_label()` and `room_payload()`; no database access |
| `backend/queuing/main.py` | **modified** | `_entry_to_dict(e, room=None)` additive room fields; `_rooms_for()` batch resolution; `_room_for_entry()` for single-entry responses; wired into the page, the call/check-in responses and history |
| `backend/queuing/recovery.py` | **modified** | `_entry_payload(session, entry)` so a recovered entry reports the same room as before the recovery |
| `backend/appointment/main.py` | **modified** | `_location_label()` delegates to `common.locations` — the appointment slip and the announcement cannot disagree |
| `frontend/tests/queue-announcement-content.test.mjs` | **modified** | 14 tests — the approved sentences verbatim, honorific once, room rules, token-serial rule, PII boundary |
| `frontend/tests/queue-announcement-speech.test.mjs` | **modified** | 19 tests — voice choice, silence ≠ success, overlap, cancellation, cleanup |
| `frontend/tests/queue-announcement-controller.test.mjs` | **modified** | 21 tests — facility switch, suppression, retry, activation, busy, observability |
| `frontend/tests/queue-announcement-dedupe.test.mjs` | **new** | 13 tests — the store in isolation: TTL, backoff, exhaustion, eviction, no-text rule |
| `frontend/tests/queue-announcements-boundary.test.mjs` | **modified** | 6 tests — JSX compile, bilingual captions, one announcer, "announcing is not a queue action", and the room the payload carries |
| `backend/tests/test_queue_room_snapshot.py` | **new** | 15 tests — the pure helpers, the additive serializer and the real queue service end to end |

No library, dependency, endpoint path, permission, role or migration was added.

---

## 3. F1 — the approved wording, verbatim

`content.js` is still the only place wording is assembled. The templates now carry exactly the sentences plan §6.2/§6.3 records as the ones the content tests must assert:

| Language | With a room | Without a room |
|---|---|---|
| English | `Token number 4, Dr. Rahim Uddin, please proceed to Room 305.` | `Token number 4, Dr. Rahim Uddin, please proceed.` |
| Bangla | `টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।` | **Not approved** (plan §18 D-11 / O-3) — refused, `reason: 'no_room'` |

Three deliberate decisions, each with a test:

- **The honorific belongs to the segment builder, not the template.** `doctorSegment()` strips one or more leading `Dr.` / `Doctor` / `ডা.` / `ডাক্তার` (bounded to three passes, never a `while (true)` in an audio path) and re-adds it once, so `'Dr. Rahim Uddin'` and `'Rahim Uddin'` both speak `Dr. Rahim Uddin` — never `Dr. Dr.`.
- **A room is announced as a number or not at all.** `roomNumberForSpeech()` accepts 1–4 ASCII digits after digit normalisation and returns `null` for anything else (`'Cabin A'`, `'Room 305'`). A non-numeric room degrades to the room-less sentence and reports `room_not_announceable`; speaking a plausible-but-wrong room is worse than speaking none.
- **The Bangla room-less template is `null`, not a string.** The refusal is therefore structural: no caller can accidentally speak a sentence that ends "…আসুন।" with no destination, and the content tests assert the refusal as the contract.

The token rule is unchanged and re-asserted: only the trailing serial is spoken (`T-3F2A9C-004 → 4`), Bangla speaks Bangla digits, and a UUID / 32-hex / digit-free token is refused with `unspeakable_token`.

---

## 4. F2 — "completed" means finished, not started

`OUTCOME` now has exactly the six terminal words of plan §8.2, and every engine reports the same six:

| Outcome | Emitted when | Proof |
|---|---|---|
| `completed` | the utterance's `end` event fired | the only value the store treats as "announced" |
| `failed` | synthesis began but did not finish, or the engine threw | `reason: 'no_end_event'`, `'speak_threw'`, `'adapter_threw'`, `'utterance_failed'`, `'empty_text'` |
| `interrupted` | cancelled by us, by the page or by the browser | `reason: 'cancelled'` |
| `blocked` | refused before it began: autoplay policy, no device, or no `start` | `reason: 'no_start_event'` |
| `busy` | another utterance is in progress | `replace: true` cancels the first instead |
| `unavailable` | the engine cannot serve this language/voice, or is disposed | `reason: 'unsupported'`, `'voice_unavailable'`, `'voices_not_loaded'`, `'disposed'` |

`start` is a progress event and never resolves the promise; a browser that begins an utterance and then dies settles as `failed` with `no_end_event` instead of being counted as a delivered call. The pre-§8.2 names (`spoken`, `cancelled`, `no_voice`, `unsupported`, `pending_voices`, `error`) are retained as aliases mapping onto those six, so nothing that reads them starts believing a new word means the old thing.

Language honesty is unchanged and re-tested: Bangla text is never read by an English voice — the outcome is `unavailable` with `reason: 'voice_unavailable'`, and a same-language voice from another region is reported as a marked fallback.

---

## 5. F3 — the bounded per-event dedupe store

`frontend/lib/announcements/dedupe.js` replaces the controller's single `lastEventKey` / `lastEventAt` slot. One record per event key; `state` is the only source of truth for "was it announced?".

| State | Suppression | Written by |
|---|---|---|
| `attempting` | yes — an overlapping delivery of the same event must not start a second attempt | `begin()`, before speaking |
| `completed` | yes, for `completedTtlMs` (10 min default) | `settle()` on `completed` only |
| `failed` / `interrupted` | yes — the retry backoff (`retryDelayMs`, 5 s → 30 s) gates the next attempt, and the record itself expires at `failureTtlMs` (60 s) | `settle()` |
| `blocked` | yes, for `blockedTtlMs` (10 min), but an operator gesture clears it | `settle()` on `blocked`, plus the controller's one-shot `blockedRetry` |
| `exhausted` | yes, until the record expires at `failureTtlMs` (60 s) — the budget (`maxAttempts` 3) is spent, and even an operator gesture cannot exceed it; once the 60 s pass, the key is forgotten and a later re-delivery starts a **fresh** budget (asserted: `being interrupted counts as an attempt, like a failure`) | `settle()` |
| *(released)* | no — `busy` / `unavailable` / `skipped` leave the event announcable | `release()` |

What the three F3.3 defects now cost:

1. **An intervening event no longer forgets an earlier one.** Records are keyed per event, so a re-delivery of `A` after `B` is still suppressed inside `A`'s window (`one event's memory does not erase another's`).
2. **A refused attempt is no longer remembered as announced.** The key is reserved with `begin()` and only *settled* after a terminal outcome; a `busy`/`unavailable` result calls `release()`, so nothing unheard is ever recorded as heard (`nothing heard means nothing remembered`, `an unheard event is not remembered: busy and unavailable both retry`).
3. **What happened to an event is observable.** `failed` / `interrupted` retry on a backoff and then `exhausted`; the controller's outcome object carries the status and a normalised reason, and the panel shows why nothing was heard.

Engineering constraints, all asserted:

- **No timers.** Expiry is evaluated on read and swept on write — a kiosk page is never kept awake by a `setInterval`. The only timers on this path live in the adapter, which owns its own watchdogs (`start` timeout ⇒ `blocked / no_start_event`; post-`start` timeout ⇒ `failed / no_end_event`), so an `attempting` key cannot outlive a real playback attempt: the adapter's promise always settles, and the controller settles or releases on every branch.
- **Injected clock** (`now`), so every TTL test is deterministic.
- **Bounded memory**: `maxKeys` 512, deterministic eviction that never evicts an in-flight `attempting` record.
- **No spoken text, no patient field** in a record — event key, state, counts, timestamps and a normalised reason only (`a record carries no spoken text and no patient field`).
- **Suppression is scoped to `source === 'event'`**: an operator repeat is deliberate and always plays (`suppression is scoped to events: an operator repeat is never blocked`).
- **`dedupeWindowMs` is kept as a compatibility knob** that sets all three TTLs and zeroes the backoff, so `dedupeWindowMs: 0` still means "remember nothing" for callers and tests written against the old option; `options.dedupe` overrides it explicitly.

Storage is per browser tab by design. Cross-tab / cross-client suppression needs the server-side event contract (ANN-002/ANN-005) and is **not** claimed here.

---

## 6. F4 — the room on the queue payload

### 6.1 The backend contract (additive, backward compatible)

`_entry_to_dict(e, room=None)` gains four fields and keeps every existing one:

| Field | Content | When empty |
|---|---|---|
| `room_id` | the snapshotted room id | no snapshot, or the snapshot has no room |
| `room_name` | the snapshot's room name — **the only field the announcement speaks** | as above |
| `location_label` | the human-facing label, e.g. `2nd Floor / Cardiology / 204` | as above |
| `room_source` | `appointment_snapshot` only when a room name exists, else `''` | as above |

- **The snapshot is the booking-time truth**, read from `appointments.room_*` — never `schedule_sessions` or `doctor_branches`. A patient is not sent to the doctor's *current* chamber (plan A-10).
- **One query per page, not one per row.** `_rooms_for(session, entries)` resolves the whole page with a single `Appointment` query filtered by both `id IN (…)` and `organization_id IN (…)`, the same pattern the existing patient/doctor name maps use; `_room_for_entry()` serves single-entry responses. The tenant filter lives in the query, so the room read cannot cross an organisation even if an appointment id were forged (`.clinerules` §3).
- **Wired everywhere a queue entry leaves the service**: the queue page, the call/check-in response and `queue_history`, plus `recovery._entry_payload(session, entry)` so a recovered entry announces the same room it would have announced before the recovery.
- **`_location_label()` in `appointment/main.py` now delegates to `common.locations.location_label()`**, so the printed slip and the spoken sentence cannot drift apart.
- **`_entry_to_dict`'s new parameter is optional and defaults to `None`.** Every pre-existing caller keeps working unchanged; the additive change is asserted by `test_entry_dict_without_a_room_keeps_four_empty_room_fields`.

### 6.2 The frontend wiring

`frontend/pages/queue.js` used to pass `room: entry.room` — a placeholder for a field no endpoint returned. It now passes `room: entry.room_name`, the field the payload actually carries, and a boundary test asserts both the new read and the absence of the stale placeholder. With an empty `room_name` (walk-ins, or a snapshot with no room), `buildAnnouncement` takes the approved room-less branch — English says "please proceed", Bangla refuses with `no_room` rather than speaking an unfinished sentence.

The announcement still sends **no HTTP request** and cannot change queue state (`announcing is not a queue action`).

---

## 7. Governance and skill compliance (`.clinerules` §6)

| Domain (§4 routing table) | Documents read and applied | Evidence in this task |
|---|---|---|
| Frontend UI / components / pages | `saas-frontend-ux.md` (as adapted, Assessment §3), `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`, `frontend/lib/i18n.js` conventions | `queue.js` keeps its existing structure and action idioms; the only change is the field the announcer is handed. No new component, no new caption, no styling change |
| Backend API / services | `saas-application-security.md` (adapted), Business Rules Parts II–X | Additive serializer fields; no endpoint path, verb or permission changed; `room_name` is announcement-safe metadata (token/doctor/room only, A-6) |
| Multi-tenant isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–§6, `backend/common/auth.py` scope checks | `_rooms_for` filters by `organization_id IN (…)` **inside** the query; `_room_for_entry` filters by `organization_id ==`; no new tenant key is introduced, `organization_id` remains the only one |
| Authentication / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–§8 | Untouched. The room fields do not widen what a principal can read: they ride on entries the caller has already been authorised to see |
| Queue / scheduling / transitions | Business Rules Parts V–VII, `saas-api-throttling.md` (concurrency, adapted) | The queue transition code is unchanged; the room is attached to the response the transition already returned |
| Audit / data integrity | `saas-observability.md` (adapted, redaction), `backend/common/audit.py`, Business Rules Part X | No audit event was added, removed or rewritten. The announce path is client-side and records nothing server-side; the panel logs no spoken text (§5) |
| Database schema / migrations | `saas-multitenant-data.md` §4–§5, Alembic chain | No schema change and therefore **no migration**: the fields are derived from existing `appointments` columns. The migration chain is untouched |
| Documentation placement | `.clinerules` §11/§12, this index | Report written to `docs/implementation/`; destination collision checked; index updated in the same task |

**Skills: none installed.** `.clinerules` §5 records that no `.clinerules/skills/`, `.claude/skills/` or repository `skills/` package exists, so no skill was selected, invoked or claimed. The governance documents above were applied directly, which is the §5 fallback for every row of the §4 table.

**Non-negotiables checked one by one (§3):**

| Non-negotiable | How this task satisfies it |
|---|---|
| No secret, token, JWT or credential logged or exposed | The dedupe record stores an event key and a state — never the sentence, never a patient field. No credential was read, printed or written |
| The UI is never the safety boundary | Authorisation still happens server-side on the existing endpoints; the announcement is decoration on a list that is already scoped |
| Principal's org/branch from the token, never the body | No endpoint signature changed; the room read is additionally filtered by the entry's own `organization_id` |
| Cross-tenant access fails closed with 404 | Behaviour unchanged; the room query cannot return another organisation's appointment |
| `organization_id` is the only tenant key | No second tenant column was introduced |
| Audit trail append-only | Not touched |
| Denials audited | Not touched (no new denial path) |
| Forward-only idempotent migration for schema change | No schema change was made |
| No unverified capability claimed | §9 states exactly what was not run; no playback claim is made |

---

## 8. Tests and evidence

### 8.1 Commands run in this task, with their real output

| # | Command | Result |
|---|---|---|
| 1 | `cd frontend && node --test --test-reporter=spec tests/queue-announcement-dedupe.test.mjs tests/queue-announcement-controller.test.mjs tests/queue-announcement-content.test.mjs tests/queue-announcement-speech.test.mjs tests/queue-announcements-boundary.test.mjs` | **72 tests, 72 pass, 0 fail**, exit `0` (first run, before the boundary test added in §6.2) |
| 2 | The same five-file command **re-run after the `queue.js` room wiring** | **73 tests, 73 pass, 0 fail**, exit `0` |
| 3 | `cd frontend && node --test tests/queue-announcements-boundary.test.mjs` (alone, after the wiring change) | **6 tests, 6 pass, 0 fail**, exit `0` |
| 4 | `cd frontend && npm test` (whole frontend suite, after the wiring change) | **253 tests, 253 pass, 0 fail**, exit `0` |
| 5 | `pytest tests/test_queue_room_snapshot.py` (against the `.env` database via the local script that exports `AMSDP_DATABASE_URL` without printing it) | **15 passed, 3 warnings**, exit `0`, 12.49 s |
| 6 | Full backend suite `pytest -q` with the new file present | **464 passed, 24 warnings**, 604.54 s |

Per-file frontend counts: content **14**, speech **19**, controller **21**, dedupe **13**, boundary **6** = **73**.

### 8.2 Backend test inventory — `tests/test_queue_room_snapshot.py` (15)

| Group | Tests |
|---|---|
| Pure helpers | `test_location_label_names_the_chamber_snapshot`, `test_location_label_omits_parts_the_clinic_does_not_model`, `test_location_label_of_no_snapshot_is_empty`, `test_no_room_is_the_empty_answer_and_clears_every_field`, `test_room_payload_without_a_room_name_is_not_announceable`, `test_room_payload_names_the_booking_snapshot_as_its_source` |
| Serializer (additive) | `test_entry_dict_without_a_room_keeps_four_empty_room_fields`, `test_entry_dict_carries_the_resolved_room` |
| End to end over the real service | `test_queue_page_announces_the_snapshotted_chamber`, `test_walk_in_entry_announces_without_a_room`, `test_enqueue_endpoint_reports_no_room_for_a_walk_in`, `test_each_entry_on_one_page_keeps_its_own_room`, `test_a_page_of_entries_costs_one_appointments_query`, `test_recovery_payload_reports_the_same_room`, `test_queue_page_never_leaks_another_branch` |

`test_a_page_of_entries_costs_one_appointments_query` is the N+1 guard: it counts the `Appointment` queries issued for a page and asserts a fixed number independent of page size. `test_queue_page_never_leaks_another_branch` is the isolation guard.

### 8.3 Evidence grade (`.clinerules` §7)

| Statement | Grade | Basis |
|---|---|---|
| The four corrections exist and are reachable in the tree | **IMPLEMENTED** | §2 file list, `git diff` and `git status` |
| The named tests pass in this tree | **TESTED** | §8.1 rows 1–6, with pass counts and exit codes |
| `_entry_to_dict`'s additive change breaks no existing caller | **TESTED** | full backend suite 464 passed, including every pre-existing queue and recovery test |
| The queue page passes the payload's room to the announcer | **TESTED** | `the page announces the room the payload carries` (source-contract test) |
| A patient in a real browser hears the correct sentence | **NOT VERIFIED** | no browser, device, speaker or headless run was performed (§9) |
| The owner accepts the behaviour | **NOT ACCEPTED** | acceptance is a Product Owner act |

---

## 9. What is *not* verified, and why it matters

1. **No audio was heard.** Nothing here ran a browser, a speaker, a device or a headless page with a real `speechSynthesis` engine. Every claim about the *mechanism* rests on unit tests that drive a fake engine. This is exactly the gate plan A-13 (and the MVP Feature Catalogue) sets before implementation may be described as producing audio: it is **not** passed.
2. **The browser's own refusal behaviour was not observed.** `blocked` / `no_start_event` / `no_end_event` are modelled and unit-tested; which real browser reports which sequence on which platform is unmeasured.
3. **Voice availability was not measured on a target machine.** Whether a Bangla voice exists on the hospital's actual hardware decides whether Bangla announcements play or report `voice_unavailable`. Nothing here proves a Bangla voice is installed anywhere.
4. **The room snapshot's real data was exercised through seeded fixtures, not the production dataset.** The end-to-end tests create their own organisation, doctor, appointment and queue entry.
5. **No human listened to a Bangla sentence** for pronunciation or intelligibility; that is plan D-17 / O-4 territory and requires a native-speaker gate.

---

## 10. Open items

| # | Item | Owner / route |
|---|---|---|
| O-1 | **The Bangla room-less sentence is unapproved** (plan O-3 / D-11). Until the owner approves wording, a Bangla announcement for an entry with no room is *refused* (`no_room`) — audible silence is the deliberate choice over an unfinished sentence | Product Owner |
| O-2 | **The dedupe TTLs and retry budget are an engineering recommendation** (10 min / 60 s / 10 min, 3 attempts, 5 s→30 s backoff, `maxKeys` 512). They are defaults in code, not owner-ratified values (plan O-5 / D-8) | Product Owner |
| O-3 | **Facility configuration is not stored** (OD-2 residual): enable/disable and language are still controller options, not persisted settings, so nothing today lets an `org_admin` actually configure them | Product Owner decision, then a backend task |
| O-4 | **No server-side announcement event or audit** (ANN-002 / ANN-008 / plan O-8). A tab reload loses the memory, and no operator can prove after the fact that a call was announced | Product Owner decision, then a backend task |
| O-5 | **Walk-in room capture does not exist** (plan option R2). `room_source: 'walk_in_capture'` is reserved and never written; a walk-in announces room-less | Future task |
| O-6 | **Cross-tab / multi-screen suppression is not implemented** (per-tab store). Two duty desks can each announce the same event | Needs ANN-002 |
| O-7 | **The local audio-asset catalogue (plan Stages B/C) is not built.** The browser engine is currently the only engine, which plan A-4 permits as an *optional alternative* only | Future stage |
| O-8 | **Recall (QOP-003) and the `call` UI action (QOP-001) are untouched.** Announcement is not recall: it replays a `called` entry and never re-calls a patient in queue state | Product backlog |
| O-9 | **Two records still describe QUE-006 as unstarted, and neither was edited here.** `docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` (line 44, the scope-lock paragraph) says its "implementation and verification status remain independent of this scope approval (NOT STARTED / NOT TESTED, no TTS provider or audio code)" — true when written, and now stale for the *mechanism* only, not for the audio claim. The product catalogue's ten acceptance boxes (`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`, QUE-006) remain **unchecked, correctly**, because criterion 10 requires browser/runtime audio verification and that gate is still unmet (§9). Neither document is owner-controlled, but both belong to other workstreams; updating them is that workstream's act, not a side effect of this report | Product Owner / catalogue workstream |
| O-10 | **`.gitignore`'s `+.aider*` line is not this task's change.** It appeared in the working tree from a separate editor session; it was left in place and is *not* claimed here | Whoever owns that change |

---

## 11. Working tree and documentation state

- **Nothing was staged, committed or pushed** by this task. `git diff --cached` is empty.
- Uncommitted paths belonging to this workstream: **nine** source files (five frontend: `content.js`, `speech-synthesis.js`, `dedupe.js`, `controller.js`, `pages/queue.js`; four backend: `common/locations.py`, `queuing/main.py`, `queuing/recovery.py`, `appointment/main.py`) and **six** test files (five frontend, one backend). Four of those files are new and untracked: `frontend/lib/announcements/dedupe.js`, `backend/common/locations.py`, `frontend/tests/queue-announcement-dedupe.test.mjs`, `backend/tests/test_queue_room_snapshot.py`.
- Untracked paths that are **not** this task's product code: `docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md` (the plan of record, registered in the documentation index by the same task that wrote this report), `docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md` (uncertain-ownership file in a folder outside `.clinerules` §11 — left in place, reported not migrated) and the `.aider*` ignore line (O-10).
- **Index registration.** This report and the plan of record are registered in `docs/governance/AMSDP_Docs_Index_V1.0.md` under its own revision. An unindexed document is an incomplete task (§12).
- **This report is not a scope or disposition change.** QUE-006 remains KEEP / AMSDP Core, and the feature's acceptance is untouched by anything written here.
