# AMSDP — QUE-006 Trial Merge: D-4 and D-6 Decision Closure, V1.0

**Date:** 2026-11-23 · **Branch:** `trial/que006-windows-ubuntu-merge` (HEAD `41ac51a`, `MERGE_HEAD` `2fc007a`, unchanged) · **Status:** **D-4** and **D-6** are decided by the Product Owner and now implemented and testable; the frontend suite is green (`355/355`) and the production build compiles. **Nothing was committed, pushed, migrated, deployed, rebuilt or restarted.** Audible behaviour is still **NOT VERIFIED** (blocker **B-8**).

This report continues `docs/implementation/AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md` (hereafter **V2.0**) on the *same* uncommitted trial merge. It supersedes only that report's rows that record **D-4** and **D-6** as open (V2.0 §11, §12, §13, §15); everything else it says still stands.

---

## 1. Executive summary

* **D-4 — rooms are announced.** The decision is: a room is spoken whenever one is *configured* for the queue entry, and the approved room-less sentence is spoken when it is not. The code already produced the four approved sentences after INT-3/INT-3b; this task makes the decision explicit and pins it, adds the two tests that hold it, and records in the source why no facility-level room switch exists to consult (the announcement configuration stores the language and the voice packs only — `backend/organization/announcement_config.py`).
* **D-6 — one playback vocabulary.** `completed` and `interrupted` are the only words for a finished and a stopped sentence. The pre-merge spellings (`spoken`, `cancelled`, `error`, `unsupported`) were **removed, not aliased**: a transport that still answers one of them is reported as `failed(status_<word>)` by the controller, so a stale engine can never be recorded as a delivered announcement. `PLAYBACK.CANCELLED` was **renamed** to `PLAYBACK.INTERRUPTED` rather than joined by a new member, so the prerecorded engine, the controller, the delivery classifier and the announcement panel now speak exactly the server's reportable outcome set.
* **The nine failing tests are gone, and no test was weakened to get there.** The full frontend suite is **355 tests, 355 pass, 0 fail, 0 skipped** (`EXIT=0`), up from V2.0's `344/353`; the nine former failures were assertions that the controller still said `spoken`/`cancelled`, and the six announcement files that carried them now assert the approved words. Two further tests were added for D-4 (`queue-announcement-room.test.mjs`, 12 → 14).
* **`npm run build`** compiles: `✓ Compiled successfully`, static/dynamic routes unchanged, `EXIT=0`.
* **No behaviour was invented for the decision.** D-4 adds no configuration key and no new payload field: the sentence is chosen from `room_name`, which the backend already serializes and both announcement paths already read. D-6 adds no outcome word: the server's reportable set (`completed`, `failed`, `blocked`, `interrupted`, `skipped_busy`, `skipped_duplicate`) is untouched.
* **Still not a deliverable.** Nothing audible has been heard (**B-8**); **B-5**'s pre-existing test defects are untouched; **D-3**, **D-5** and **D-7** remain open and were deliberately not touched; **B-10** was deliberately not tightened.

---

## 2. The decisions as recorded

| ID | Question (V2.0 §11) | Decision | Date |
|---|---|---|---|
| **D-4** | Are rooms announced at all? | **Yes, when one is configured.** A queue entry that carries a room (`room_name`, the appointment's booking-time snapshot) is announced with the approved *with room* sentence; an entry without one uses the approved *room-less* sentence. No new switch, no new field, no invented room. | 2026-11-22 |
| **D-6** | Outcome vocabulary: `completed`/`interrupted` (Ubuntu/W-series) or `spoken`/`cancelled` (pre-merge frontend)? | **`completed` / `interrupted`.** One vocabulary for playback outcomes; the pre-merge spellings are removed rather than accepted as aliases. | 2026-11-22 |

Both decisions had been carried as **PO DECISION REQUIRED** since the integration report. Neither changes an approved business rule; both resolve an inconsistency between two lineages of the same feature (QUE-006).

---

## 3. D-4 — implementation

### 3.1 What "configured" means, verified rather than assumed

| Question | Answer | Evidence |
|---|---|---|
| Is there a facility setting that turns room announcements on or off? | **No.** The announcement configuration stores the language and the per-language voice packs only. | `backend/organization/announcement_config.py` — `AnnouncementPlatformConfig` (`language`, `voice_packs`), `CONFIG_KEY = "announcement"`; a search for a room key across that surface returns nothing |
| Where does a room come from? | The appointment's booking-time snapshot, serialized by the queue API as `room_name` | `backend/queuing/main.py::_entry_to_dict`; both frontend paths read `room: entry.room_name` |
| What happens when an entry has no room? | The approved room-less sentence is spoken | `frontend/lib/announcements/content.js` `TEMPLATES[lang].noRoom`; asserted in §3.4 |
| Is any other room-shaped field spoken? | **No.** `room_id`, `location_label` and `room_source` are internal or display values and never reach a sentence | new test `D-4 only room_name is a room` |

So the payload is the single input and the two approved sentences are the only possible outputs. That is what the decision describes, and it is what the code does — with no configuration surface invented for it.

### 3.2 The four approved sentences, as spoken

| Language | Configured room `305` | No room |
|---|---|---|
| English | `Token number 4, please proceed to Room 305.` | `Token number 4, please come to the front.` |
| Bangla | `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |

The token is spoken as its trailing serial only (`T-3F2A9C-004` → `4`), in the language's own digits; the room's digits are localised the same way (INT-3b), while `fields.room` keeps the payload's own ASCII value so segment resolution is unaffected.

### 3.3 What changed in the tree

| File | Change |
|---|---|
| `frontend/lib/announcements/content.js` | Header comment now records D-4: that a configured room is announced, what "configured" means, that no facility switch exists, and how `fields.template` / `fields.derived` report the variant used. **No behaviour change** — the templates and the choice between them are unchanged. |
| `frontend/pages/queue.js` | Comment updated: D-4 is decided, so `room: entry.room_name` is the decision implemented rather than a line awaiting one. **No behaviour change.** |
| `frontend/tests/queue-announcement-room.test.mjs` | Header records the decision; **two tests added** (§3.4). |

Nothing else was needed: V2.0's INT-3 fix (the automatic path reads `room_name`) and INT-3b (Bangla room digits) had already made all four sentences reachable from real code, and the existing tests already pinned their exact wording.

### 3.4 The tests that now hold D-4

| Test | What it pins |
|---|---|
| `D-4 the approved variant that was used is reported, not inferred` | For both languages: a room yields `fields.template === 'with_room'`, `hasRoom === true`, `derived === false`; no room yields `'no_room'`, `hasRoom === false`, `derived === true`. A caller never has to parse the sentence. |
| `D-4 only room_name is a room: an id, a label or a source alone speaks the room-less sentence` | With `room_name` empty and `room_id` / `location_label` / `room_source` populated, the room-less sentence is spoken, playback receives `room: ''`, and no `305` appears in the text — an internal identifier or a display label cannot leak into speech. |

Together with the twelve INT-3 tests (`automatic`/`operator`, English/Bangla, with room, empty room, missing field, null field, stale `room` placeholder, the four exact sentences), the file is **14 tests, all passing** (§6).

---

## 4. D-6 — implementation

### 4.1 The vocabulary

| Pre-merge spelling | Approved word (D-6) | Removed from |
|---|---|---|
| `spoken` | `completed` | speech engine, controller, delivery classifier |
| `cancelled` | `interrupted` | speech engine error codes, prerecorded `PLAYBACK`, controller, delivery classifier |
| `error` | `failed` (+ `reason`) | speech engine |
| `unsupported` | `unavailable` | speech engine `OUTCOME`, panel's no-controller fallback |

`PLAYBACK.CANCELLED` was **renamed** to `PLAYBACK.INTERRUPTED` rather than kept beside it, so the prerecorded engine and the controller export the same member names and no caller can mix the two.

### 4.2 Removal, not aliasing — and the consequence, stated plainly

The transport boundary in `frontend/lib/announcements/controller.js` accepts exactly the six words the rest of the system uses:

```
completed · interrupted · failed · blocked · busy · unavailable
```

Anything else is normalised to `{ status: 'failed', reason: 'status_<word>' }`, so an engine that still answers `spoken` is recorded as an honest failure rather than being silently promoted to a delivered announcement. `frontend/lib/announcements/delivery.js` no longer maps `spoken`/`cancelled`; its `default` branch records `failed` / `status_<word>` for any unknown word. A real prerecorded failure keeps its own reason (`missing_asset`, `playback_failed`) — it is not routed through the transport normaliser, because it is already in the approved vocabulary.

### 4.3 What is *not* a playback outcome (checked so the sweep does not over-reach)

| Occurrence | Why it stays | Where |
|---|---|---|
| `reason: 'cancelled'` on an interrupted playback | A **cause**, not a status: the outcome is `interrupted`, the reason says who stopped it | `prerecorded-audio.js`, `speech-synthesis.js` |
| `CANCELLED_CODES = ['canceled', 'cancelled', 'interrupted']` | DOM `SpeechSynthesisErrorEvent` codes, mapped to `interrupted` | `speech-synthesis.js` |
| `CAPABILITY.UNSUPPORTED = 'unsupported'` | A **capability** — what the browser/pack can do, not what happened | `speech-synthesis.js`, panel badge logic |
| Queue entry status `cancelled` | A different domain (queue status), untouched | `pages/queue.js`, `pages/notifications.js` |
| `outcomeRequest(..., 'spoken') → null`, `'spoken' → failed/status_spoken` | Tests that *prove* the word is refused | `tests/queue-announcement-delivery.test.mjs` |

### 4.4 What changed in the tree

| File | Change |
|---|---|
| `frontend/lib/announcements/speech-synthesis.js` | `OUTCOME` keeps six members; a D-6 comment records that the pre-merge spellings were removed, not aliased. A cancelled utterance resolves `interrupted` with `reason: 'cancelled'`. |
| `frontend/lib/announcements/controller.js` | `TRANSPORT_STATUS` is the six-word map; `normaliseTransport` reports an unknown word as `failed(status_<word>)`; comment records D-6. |
| `frontend/lib/announcements/delivery.js` | Classifier accepts only the approved words; unknown words fall to `default` → `failed` / `status_<word>`. |
| `frontend/lib/announcements/prerecorded-audio.js` | `PLAYBACK.CANCELLED` **renamed** to `PLAYBACK.INTERRUPTED`; header records interruption vs cancellation. |
| `frontend/components/queue/QueueAnnouncements.js` | `outcomeLabel` maps `completed` → "spoken", `interrupted` → failed playback; the no-controller fallbacks in `announce()`/`activate()` resolve `{ status: 'unavailable' }` instead of `{ status: 'unsupported' }`. |
| `frontend/tests/queue-announcement-{controller,w2-integration,speech,prerecorded,delivery,room}.test.mjs` | Assertions moved to the approved vocabulary; the nine former failures now assert `completed`/`interrupted` directly. |

### 4.5 Blast radius

| Surface | Effect |
|---|---|
| Persisted `outcome` strings | **None in content.** The delivery classifier already translated to the server's set (`completed`, `failed`, `blocked`, `interrupted`, `skipped_busy`, `skipped_duplicate` — `backend/queuing/announcements.py::OUTCOMES`). What changed is the *transport* vocabulary in front of it, which is now the same set. |
| Server contract | **Unchanged.** No backend file was edited by this task; `OUTCOMES` still rejects any other word with `422 unknown announcement outcome`. |
| Operator UI | The mapping is unchanged in effect (`completed` reads "last announcement spoken", `interrupted` reads as a failed playback). |
| Audit trail | **No row is written differently for the same event**; a stale transport word would now be recorded as `failed(status_spoken)` rather than delivered — stricter, never looser. |
| Queue operations | Untouched — announcing is still fire-and-forget and the page never awaits playback (AC-7 test still passes). |



---

## 5. Repository-wide vocabulary sweep (D-6, evidence)

The sweep was run across `frontend/lib`, `frontend/components`, `frontend/pages` and `frontend/tests`:

| Pattern | Result |
|---|---|
| `OUTCOME.SPOKEN`, `OUTCOME.CANCELLED`, `OUTCOME.ERROR`, `OUTCOME.UNSUPPORTED`, `OUTCOME.NO_VOICE`, `OUTCOME.PENDING`, `PLAYBACK.CANCELLED` | **no matches** — the alias members no longer exist as references |
| `status: 'unsupported'` | **one occurrence, and it is a capability, not an outcome**: the controller test's fake adapter returns `capability() → { status: 'unsupported' }` for an engine that does not exist, which is `CAPABILITY.UNSUPPORTED`. The UI path's no-controller *outcome* fallbacks are `{ status: 'unavailable' }`. |
| `'spoken'`, `'cancelled'` | **only** the deliberate occurrences listed in §4.3: causes (`reason: 'cancelled'`), DOM error codes, queue statuses, and the delivery tests that assert the word is *refused* |

No occurrence of a pre-merge *outcome* word remains in product code.

---

## 6. Test and build evidence

All commands were run in `/home/shomonrobie/amsdp/frontend` on the working tree described in §7. Logs are in `/tmp/que006_trial/` (`Y3`, `Z4`, `Z5`, `Z6`, `Z7`).

| Run | Command | Result |
|---|---|---|
| The six announcement suites (D-6) | `node --test tests/queue-announcement-{controller,w2-integration,speech,prerecorded,delivery,room}.test.mjs` | **98 tests, 98 pass, 0 fail** (`EXIT=0`) |
| The room suite after the D-4 tests were added | `node --test tests/queue-announcement-room.test.mjs` | **14 tests, 14 pass, 0 fail** (`EXIT=0`) |
| Full frontend suite | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs` (what `npm test` runs) | **355 tests, 355 pass, 0 fail, 0 skipped** (`EXIT=0`) |
| Production build | `npm run build` | `✓ Compiled successfully`, 15 routes as before, `EXIT=0` |

**What this proves and what it does not.** The vocabulary and the room decision are **TESTED** against the real modules (the controller, the announcer, the delivery classifier and the prerecorded player are exercised with fake transports, exactly as the browser wires them). When the D-4 tests were first written, one of them failed on a wrong expectation of the author's (`undefined` vs `''` for a deleted `room_name`) and was corrected by pinning the field that the backend actually sends — the code was not changed to make a test pass.

Nothing here is **VERIFIED** in the `.clinerules` §7 sense: no browser was served, no speaker was listened to, and no claim/outcome round trip was made against a running service. **B-8 remains open.**

---

## 7. Git state and preservation

| Item | Value |
|---|---|
| Branch | `trial/que006-windows-ubuntu-merge` (unchanged) |
| `HEAD` / `MERGE_HEAD` | `41ac51a0aea6a4462d3e2356cd5f3e58da57b326` / `2fc007a3f7a96639c3df36341c6081cee4d24a48` (unchanged) |
| Merge commit / push / deploy / migration / rebuild | **none** — none was run |
| Files edited by this task | `frontend/lib/announcements/{speech-synthesis,controller,delivery,prerecorded-audio}.js`, `frontend/components/queue/QueueAnnouncements.js`, `frontend/lib/announcements/content.js`, `frontend/pages/queue.js`, `frontend/tests/queue-announcement-{controller,delivery,prerecorded,room,speech,w2-integration}.test.mjs` |
| Backend | **untouched** by this task (no backend file appears in the diff below) |
| Staged working tree | **181 staged entries** against `41ac51a` (166 additions, 15 modifications, 0 deletions) — V2.0's 178 plus this task's three new/changed paths (the new report, and the two files that had been left unstaged) |
| Unstaged / untracked | **0 / 0** after re-staging — the index and the working tree are identical |

### 7.1 Preservation exports (additive — nothing overwritten)

V2.0's artefacts (`10_…`, `11_…`, `12_…`) predate this task, so the *current* resolved tree was exported beside them in `/home/shomonrobie/amsdp_preservation_20261122/`:

| Artefact | Contents |
|---|---|
| `13_trial-merge-d4-d6-resolved.patch` | `git diff --cached --binary HEAD` over all 181 staged entries; **verified `git apply --check --binary` against a pristine `41ac51a` worktree → `PATCH_APPLIES`** |
| `14_trial-merge-d4-d6-files.tar.gz` | the same files as a tarball — **181 members**, matching the staged count |
| `15_final-digests-d4-d6.txt` | SHA-256 of both artefacts, the staged/unstaged counts and the exact Git state |

No earlier artefact was deleted, renamed or rewritten.


---

## 8. What this closes, and what it does not

| ID | State after this task |
|---|---|
| **D-4** | **CLOSED** — decided 2026-11-22 and implemented: a configured room is spoken; otherwise the approved room-less sentence. Pinned by 14 tests in `queue-announcement-room.test.mjs`. |
| **D-6** | **CLOSED** — decided 2026-11-22 and implemented: `completed`/`interrupted` are the only playback words; the pre-merge spellings are removed and an unknown transport word is recorded as `failed(status_<word>)`. The nine former frontend failures are gone. |
| **B-2** (D-6 vocabulary collision) | **CLOSED** as a consequence of D-6 — the suite is green. |
| **B-8** (no browser/speaker/two-terminal evidence) | **OPEN** — untouched, and it is now the only high-severity blocker between this tree and a merge commit. |
| **B-5** (pre-existing test defects: doctor fixture collisions, queuing `NameError`, `:0`/`:1` expectations) | **OPEN** — not attempted; changing them means editing tests to fit the code, which needs its own authorisation. |
| **B-7** (the merge lives in the index only) | **Mitigated** — re-exported as `13_`/`14_`/`15_`. |
| **B-10** (manifest checksum precedence in `validate_pack_upload`) | **Deliberately unchanged** — tightening validation is a behaviour change outside this task. |
| **D-3** (F3 dedupe store integration) | **OPEN** — untouched. |
| **D-5** (index revision numbering) | **OPEN** — this report is registered in the trial-merge annex, citing no revision number. |
| **D-7** (does an operator repeat create its own delivery record) | **OPEN** — untouched; the operator path still claims nothing, as merged. |
| **O-2** (facility enable/disable and language configuration storage) | **OPEN** — and this task adds **no** room setting to that surface, deliberately: D-4 needs none. |

**Acceptance:** this report is **IMPLEMENTED** and **TESTED**, **NOT VERIFIED** (no audible evidence) and **NOT ACCEPTED**. The minimum bar that remains is B-8's browser/audio checklist on a parallel stack, then a re-run of both suites and the build against the final state.


---

## 9. Governance and skill compliance (`.clinerules` §6)

**Documents read before planning:** `docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation, §12 step 3), `docs/implementation/AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md` (the state to continue, including its §11 decision table and §13 evidence table), the QUE-006 plan of record it cites, and the code paths themselves (`content.js`, `controller.js`, `delivery.js`, `prerecorded-audio.js`, `speech-synthesis.js`, `call-announcer.js`, `pages/queue.js`, `QueueAnnouncements.js`, `backend/queuing/announcements.py`, `backend/organization/announcement_config.py`). Routing rows applied: *Frontend UI*, *Queue / scheduling / workflow transitions*, *Audit / data integrity* and *Documentation* (§11/§12).

**Skills:** **none installed** in this workspace (`.clinerules` §5). None was used, claimed or invented; governance documents were applied directly. Installing a new skill would have needed owner approval and none was attempted.

**Non-negotiables honoured, with evidence:**

* *No silent product decision* — both decisions are the Product Owner's, recorded in §2 before implementation; nothing was decided here.
* *Never claim an unverified capability* — §6 separates TESTED from NOT VERIFIED, and B-8 stays open.
* *Server-side authorization, tenant isolation, audit append-only, forward-only migrations* — no backend file, no migration, no permission and no schema was touched by this task (§7).
* *No secrets* — no credential or token appears in this report or in the code changes.
* *No destructive Git, no commit, push, deploy, live migration, rebuild or restart* — §7; the only Git writes were `git add` of this task's own edits, needed to keep the staged set consistent with the working tree.
* *Documentation policy (§11/§12)* — this report is written under `docs/implementation/`, collision-checked before creation, and registered in the index annex in the same task. Nothing was moved, renamed or deleted, so no migration-manifest entry is required.

**Deviations, declared:**

1. **D-6 was implemented by removal, not by alias.** The decision named the approved words but not the mechanism; accepting both spellings would have left the ambiguity the decision exists to end, and would have let a stale engine be recorded as delivered. The stricter reading is recorded here so it can be reversed knowingly.
2. **Two comments changed without a behaviour change** (`content.js` header, `pages/queue.js`). They were the code's own record of D-4 as *undecided*; leaving them would have left the tree asserting an open question.
3. **This is a new report rather than an edit of V2.0**, so V2.0 stays an accurate record of the state before the decisions. V2.0 gains one pointer line at its top; its §11/§12/§13/§15 rows are superseded by §8 here.

**Report location:** `docs/implementation/AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md`.

---

## 10. Reproducing this verification

```bash
cd /home/shomonrobie/amsdp/frontend

# the two decisions, at unit level
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/queue-announcement-room.test.mjs

# the six announcement suites (D-6)
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test \
  tests/queue-announcement-controller.test.mjs \
  tests/queue-announcement-w2-integration.test.mjs \
  tests/queue-announcement-speech.test.mjs \
  tests/queue-announcement-prerecorded.test.mjs \
  tests/queue-announcement-delivery.test.mjs \
  tests/queue-announcement-room.test.mjs

# the whole suite and the build
npm test
npm run build

# the sweep (must print nothing)
grep -rn "OUTCOME.SPOKEN\|OUTCOME.CANCELLED\|OUTCOME.ERROR\|OUTCOME.UNSUPPORTED\|PLAYBACK.CANCELLED" lib components pages tests
```

Expected: `14/14`, `98/98`, `355/355` and `✓ Compiled successfully`; the sweep prints nothing.

**Nothing further was done:** no commit, no push, no deployment, no live migration, no rebuild or restart, and no declaration that the trial merge is accepted.

