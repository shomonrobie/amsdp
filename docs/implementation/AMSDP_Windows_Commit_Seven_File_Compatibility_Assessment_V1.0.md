# AMSDP — Windows Commit `2fc007a` · Seven-File Replacement Compatibility Assessment

> **Task ID:** `AMSDP-WIN7-COMPAT-ASSESSMENT-2026-11-22`
> **Date:** 2026-11-22 · **Mode:** READ-ONLY assessment (no file, database, container or Git state changed)
> **Ubuntu working copy:** `/home/shomonrobie/amsdp`, `HEAD = cd2f9ec` (working tree carries 13 modified / 10 untracked entries — see §0.2)
> **Compared against:** remote commit `2fc007a3f7a96639c3df36341c6081cee4d24a48` ("the Windows commit") fetched file-by-file over HTTPS
> **Verdict:** **NOT SAFE TO REPLACE** — §A

---

## 0. Scope, method and evidence

### 0.1 The exact question

Before the Ubuntu working copy is replaced by the Windows-pushed Git version, could the Git versions of these seven files break AMSDP functionality that works on Ubuntu today?

1. `backend/appointment/main.py`
2. `backend/queuing/main.py`
3. `backend/queuing/recovery.py`
4. `frontend/lib/announcements/content.js`
5. `frontend/lib/announcements/controller.js`
6. `frontend/lib/announcements/speech-synthesis.js`
7. `frontend/pages/queue.js`

### 0.2 Method

1. **Three-way identity check** per file: `git rev-parse HEAD:<path>` (committed Ubuntu), `git hash-object <path>` (Ubuntu working tree), `git hash-object` of the file fetched from commit `2fc007a`. This separates *committed* Ubuntu state from *uncommitted* Ubuntu work — the distinction that decides everything in this report.
2. **Full text diff** of Ubuntu working tree vs the commit, per file (`git diff --no-index`, artefacts in `/tmp/win7/diffs/`).
3. **Import-graph and dependency closure**: every relative/absolute import in the seven commit files resolved against the Ubuntu tree; missing modules enumerated.
4. **Contract analysis**: FastAPI routes, payload keys, Pydantic models, frontend consumers, i18n keys, tests.
5. **Safe runtime experiments (no repository, database or container touched):**
   - executed the Ubuntu frontend announcement suite as-is (baseline);
   - copied `frontend/{lib,tests,components,pages,package.json}` to `/tmp/win7/probe/frontend` (with `node_modules` symlinked read-only), verified the copy reproduced the baseline, then **overlaid only the four commit frontend files** and re-ran the same Ubuntu tests.
6. **AST parse check** of all six Python files (Ubuntu and commit) — syntax is not the failure mode.
7. **Database/migration dependency check by source inspection only** (no DB connection, no migration run): table names, migration filenames and revision chain.

No `git reset`/`checkout`/`clean`/`merge`/`rebase`, no migration, no container restart, no `.env` change. Verified afterwards: `git status --short -uall` = **23** entries — the 13 modified / 9 untracked entries this task inherited (13 modified + 9 untracked = 22) plus this report as the 10th untracked file; nothing inherited was modified except `docs/governance/AMSDP_Docs_Index_V1.0.md`, to which one row and one revision entry were appended (§H.2). `HEAD` = `cd2f9ec`, `git diff --stat` = 13 files / 726 insertions / 154 deletions — unchanged.

### 0.3 The single most important finding, stated first

**Three of the seven files are byte-identical between the Ubuntu *committed* HEAD and the Windows commit.** The Ubuntu functionality this task is worried about is **uncommitted working-tree work** that was never pushed:

| File | Ubuntu HEAD blob | Ubuntu working tree blob | Commit `2fc007a` blob | Relationship |
|---|---|---|---|---|
| `backend/appointment/main.py` | `be76241f96` | `64cdedc36b` | **`be76241f96`** | commit **== Ubuntu HEAD**; Ubuntu work uncommitted |
| `backend/queuing/main.py` | `76bc7da98b` | `b5b2d51883` | `c32d8e810a` | all three differ |
| `backend/queuing/recovery.py` | `a7e7ac93b1` | `434a935d71` | **`a7e7ac93b1`** | commit **== Ubuntu HEAD**; Ubuntu work uncommitted |
| `frontend/lib/announcements/content.js` | `281656e2c7` | `1e0eebd12d` | `efb1f4a13b` | all three differ |
| `frontend/lib/announcements/controller.js` | `72f435dc59` | `5587c3bede` | `1cbed8f2f6` | all three differ |
| `frontend/lib/announcements/speech-synthesis.js` | `ea828280e7` | `ca2f43614b` | **`ea828280e7`** | commit **== Ubuntu HEAD**; Ubuntu work uncommitted |
| `frontend/pages/queue.js` | `857c80b31a` | `e5db74b88d` | `4ddc865205` | all three differ |

Line counts (HEAD / Ubuntu working tree / commit): `1692/1698/1692`, `585/637/607`, `282/287/282`, `163/287/165`, `286/347/384`, `379/431/379`, `288/291/419`.

Consequence: replacing the working copy with the Windows tree discards four distinct bodies of Ubuntu work (QUE-006 **F1**, **F2**, **F3**, **F4**) that exist **only** in the uncommitted working tree — without conflict, without warning, and irreversibly unless the working tree is preserved first.

### 0.4 What the two lineages are

| Lineage | Present in | Content |
|---|---|---|
| **Ubuntu working tree** | uncommitted edits (QUE-006 **F1–F4**, task `AMSDP-QUE-006-F1-F4`, 2026-11-20) | F1 approved Bangla/English wording **with doctor honorific** and **rooms spoken as numbers**; F2 six terminal speech outcomes (only `end` proves delivery); F3 bounded per-event dedupe store; F4 room snapshot (`room_id`/`room_name`/`location_label`/`room_source`) on the queue payload, fed from `appointments.room_*`, announced by `pages/queue.js` |
| **Windows commit** | `2fc007a` on the remote | QUE-006 **W2** server-side call-event identity (`call_event_id`/`call_event_at`/`call_count`), **announcement delivery claim** (`POST /api/v1/queue/{id}/announcement`, `POST /api/v1/queue/announcements/{id}/outcome`) on a **new table**, **doctor name removed** from announcements (OD-3), **room never announced** (`grep room` in the commit's `queuing/main.py` → **zero matches**), new Call button, visibility-aware quiet refresh, prerecorded-audio transport, voice packs, `queue-transitions` transition tracking |

These are **not** two versions of one design; they are two different answers to the same questions ("who is named?", "is a room announced?", "who may announce?", "how is a duplicate detected?"). Replacing one with the other is a **product decision** (OD-3), not a merge.


---

## A. Executive verdict

> ### **NOT SAFE TO REPLACE**

Three independent, decisive reasons — each alone blocks a bare replacement of these seven files:

1. **The commit's backend cannot start on the Ubuntu tree.** `backend/queuing/main.py` (commit) imports `.events` / `events` and `.announcements` / `announcements` unconditionally at module import (`/tmp/win7/target/backend#queuing#main.py:53-63`). Neither `backend/queuing/events.py` nor `backend/queuing/announcements.py` exists on Ubuntu — both are outside the seven files and were never created here. The container is `CMD ["uvicorn", "main:app", ...]` with `COPY queuing/ ./`, so the `except ImportError: from events import ...` fallback is an instant `ModuleNotFoundError` at import: the **queuing service crash-loops**, taking down every queue route, the public display, missed-turn recovery, check-in and the `/api/v1/queue/*` paths the queue page uses. On top of that, the commit's `announcements.py` imports `QueueAnnouncementDelivery` from `common.models`, which does not exist on Ubuntu either.
2. **The commit's frontend cannot build.** `lib/announcements/controller.js` (commit) imports `./prerecorded-audio.js`; `pages/queue.js` (commit) imports `lib/queue/*` (`createQueueRefresher`), `lib/announcements/call-announcer.js` and `lib/announcements/queue-transitions.js`. None of those modules exist on Ubuntu, and `frontend/Dockerfile` runs `npm run build` at image-build time, so the **frontend image build fails**. Proven by execution, not inference — §F.
3. **Even with the missing modules and tables supplied, replacing these seven files deletes four shipped Ubuntu behaviours** (F1 wording + room + doctor honorific, F2 outcome model, F3 dedupe store, F4 room snapshot), removes four keys from the queue payload, and changes the audible Bangla sentence for every patient. The Ubuntu test suite records the loss: two test files fail to load and eight assertions fail (§F).

**What would be safe** is not "these seven files" but the whole commit — its new modules, its two new migrations, a decision on the F1–F4 versus W2/OD-3 lineage, and a rebuild. §G lists that work. Nothing here was implemented.


---

## B. Seven-file comparison

### B.1 `backend/appointment/main.py` (1692 / 1698 / 1692 lines)

**Ubuntu behaviour.** Full appointment lifecycle: create (staff, with location snapshot), read/list, update, cancel, reschedule, no-show, status transitions, availability/capacity, symptoms; `_location_label(a)` builds the human location string. In the **working tree** `_location_label` is a thin delegate to the new untracked module `backend/common/locations.py` (`from common.locations import location_label`, `main.py:24`; body `main.py:247`), which returns the same shape as the previous inline join (`floor · department · room`, skipping empty parts).

**Windows commit behaviour.** `be76241f96` — **byte-identical to Ubuntu `HEAD`**: inline join, no `common/locations.py`, no delegate.

**Functional differences.** None in output. The working tree relocated ~12 lines of pure string formatting into a shared helper; the commit keeps them inline (6 fewer lines).

**Potential breakage.** Replacing this file with the commit version (or a plain `git checkout -- <path>`) silently reverts the F4 refactor and leaves `backend/common/locations.py` **untracked-and-unused** — no import error, no failing test, no visible symptom. That is exactly the class of loss that ships unnoticed (`git status` already shows `?? backend/common/locations.py`).

**Dependencies / migrations.** None. No schema change, no route change, no payload change, no new env var, no new dependency. Both versions address the same `appointments` routes.

**Evidence.** `git rev-parse HEAD:backend/appointment/main.py` = `be76241f96…`; `git hash-object` (working tree) = `64cdedc36b…`; commit blob = `be76241f96…`. Working-tree diff vs commit: **1 hunk, +3/−9**, confined to the import and `_location_label`. `ast.parse` OK on both.

### B.2 `backend/queuing/main.py` (585 / 637 / 607 lines)

**Ubuntu behaviour (working tree, 637).**
- `_entry_to_dict(e, room=None)` publishes the entry **plus four additive room keys**: `room_id`, `room_name`, `location_label`, `room_source`.
- `_rooms_for(session, entries)` batch-resolves appointment location snapshots in **one** query for the page (no N+1), reading `appointments.room_*` — booking-time truth, never `schedule_sessions`/`doctor_branches` (current truth).
- `_room_for_entry(session, entry)` resolves the room for a **single-entry action response**.
- `GET /api/v1/queue` (`main.py:180-207`) attaches `rooms.get(e.appointment_id)` per entry and still adds the `patient_name`/`doctor_name` maps; branch scoping (`branch_accessible`, `is_super_admin`/`is_org_admin` bypass) unchanged.
- Check-in and every queue-action response carry the same four room keys.
- Announcements are entirely **client-side**: no server call-event identity, no claim, no cross-terminal coordination.

**Windows commit behaviour (607).**
- `_entry_to_dict(e)` — **one positional argument** — publishes `call_event_id`, `call_event_at`, `call_count` derived from `status_history` via `events.current_call_event()`; the four room keys are **gone**.
- `_rooms_for` and `_room_for_entry` are **removed**; `grep -n room` over the commit's file returns **nothing**.
- New module-level wiring (lines 53-63): `from .events import current_call_event` and `from .announcements import router as announcements_router` + `app.include_router(announcements_router)` → two new endpoints under `/api/v1/queue` (claim, outcome), each permission-gated by `queue.manage`/`queue.consult` (`ANNOUNCE_CAPABILITIES`, `announcements.py:64`) and scoped org+branch → **404** for a foreign delivery or entry.
- Everything else (check-in, action state machine, tokens, positions, recovery wiring, `install_denial_audit`, health) is unchanged in shape.

**Functional differences.** (a) queue payload loses `room_id`/`room_name`/`location_label`/`room_source`, gains `call_event_id`/`call_event_at`/`call_count`; (b) single-entry action responses lose the room; (c) the page's room query disappears; (d) two new endpoints appear that need a table this environment does not have; (e) the frontend must now speak neither room nor doctor (§B.4, §B.7).

**Potential breakage.** If this file is replaced **alone** (recovery left as the Ubuntu version): `recovery._entry_payload` does `from .main import _entry_to_dict, _room_for_entry`, and `_room_for_entry` no longer exists → `ImportError` in both fallback branches → `POST /api/v1/queue/{id}/missed-turn` and `POST /api/v1/queue/{id}/recover` return **500** instead of recovering a missed turn (BR §27A). Replaced **as a set**, the import failure moves to the missing `events`/`announcements` modules (§A, reason 1).

**Dependencies / migrations.** Requires `backend/queuing/events.py` (pure functions, no DB), `backend/queuing/announcements.py`, `common.models.QueueAnnouncementDelivery`, table `queue_announcement_deliveries` (migration `a7c3f19d2b64`), plus voice-pack tables (`c4d8e2a91f60`). No new Python dependency — the existing `requirements.txt` already covers `text()` + `INSERT … ON CONFLICT`.

**Evidence.** Blob hashes §0.3; `grep -n 'room'` over the commit file → no output; commit `_entry_to_dict` + import block quoted in `/tmp/win7/39_target_qmain.txt`; Ubuntu helpers quoted in `/tmp/win7/40_local_qmain.txt`; route/authorisation inventory in `/tmp/win7/27_routes.txt`.

### B.3 `backend/queuing/recovery.py` (282 / 287 / 282 lines)

**Ubuntu behaviour.** Sequence-3 missed-turn recovery (BR §27A). `_entry_payload(entry, session)` builds the response payload by delegating to `main._entry_to_dict(entry, _room_for_entry(session, entry))` — so a recovery response carries the **same four room keys** as the queue list, taken from the appointment snapshot.

**Windows commit behaviour.** `a7e7ac93b1` — **byte-identical to Ubuntu `HEAD`**: `_entry_payload` calls `main._entry_to_dict(entry)` without a room, because at HEAD time `_entry_to_dict` had no room parameter.

**Functional differences.** None *inside the file*; the difference lives in its callee. It is consistent with the `main.py` of either lineage.

**Potential breakage.** The clearest **pair-coupled** file in the set:
- commit `recovery.py` + Ubuntu `main.py` → works, but every missed-turn/recover response silently loses the room fields (F4 regression, no error).
- Ubuntu `recovery.py` + commit `main.py` → `ImportError: cannot import name '_room_for_entry'` → **HTTP 500** on both recovery endpoints.

**Dependencies / migrations.** None of its own. No schema, no migration, no env var, no dependency. Routes unchanged: `POST /api/v1/queue/{entry_id}/missed-turn`, `POST /api/v1/queue/{entry_id}/recover`.

**Evidence.** Blob hashes §0.3 (HEAD == commit); working-tree diff vs commit = the `_entry_payload` delegation only; `ast.parse` OK on both.

### B.4 `frontend/lib/announcements/content.js` (163 / 287 / 165 lines)

**Ubuntu behaviour (working tree, 287).** The F1 wording engine. Exports 14 symbols, including `DOCTOR_PREFIX`, `SKIP_REASON`, `MAX_ROOM_DIGITS`, `tokenSerial`, `doctorNameWithoutHonorific`, `doctorSegment`, `roomNumberForSpeech`. Templates:

```
bn.withRoom: 'টোকেন নম্বর {number}, {doctor}, কক্ষ {room}-এ আসুন।'   bn.noRoom: null → refuse with reason 'no_room'
en.withRoom: 'Token number {number}, {doctor}, please proceed to Room {room}.'
en.noRoom:   'Token number {number}, {doctor}, please proceed.'
```

`buildAnnouncement` refuses with `missing_doctor_name` when no doctor is supplied, normalises the honorific exactly once (`doctorSegment`), and only speaks a room that is a genuine short number (`roomNumberForSpeech`, ≤ 4 digits) — a room like "3rd floor" degrades to `room_not_announceable` instead of being read aloud.

**Windows commit behaviour (165).** Exports 7 symbols; `DOCTOR_PREFIX`, `SKIP_REASON`, `tokenSerial`, `doctorSegment`, `roomNumberForSpeech` and all honorific handling are **removed**. Templates:

```
bn.withRoom: 'টোকেন নম্বর {number}, কক্ষ {room}-এ আসুন।'   bn.noRoom: 'টোকেন নম্বর {number}, অনুগ্রহ করে সামনে আসুন।'
en.withRoom: 'Token number {number}, please proceed to Room {room}.'
en.noRoom:   'Token number {number}, please come to the front.'
```

No doctor slot, no honorific logic, no room-number validation (raw `cleanText(source.room)`), and the Bangla room-less sentence that is a structural `null` refusal in the Ubuntu version is now written out. `reason` values are inline string literals instead of the shared `SKIP_REASON` vocabulary.

**Functional differences (audible, per patient).**
| Input | Ubuntu working tree | Windows commit |
|---|---|---|
| token 4, room "302", doctor "Dr. Karim" | `টোকেন নম্বর ৪, ডা. করিম, কক্ষ ৩০২-এ আসুন।` | `টোকেন নম্বর ৪, কক্ষ ৩০২-এ আসুন।` (doctor never named) |
| token 4, no room | **refused** (`no_room`) — nothing spoken, reason shown in the panel | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |
| token 4, no doctor | **refused** (`missing_doctor_name`) | spoken normally (doctor not required) |
| room "3rd floor" | `room_not_announceable`, room clause dropped, reason surfaced | room read verbatim as text |

**Potential breakage.** `frontend/tests/queue-announcement-content.test.mjs` imports `DOCTOR_PREFIX` and drives `doctorSegment`/`roomNumberForSpeech`; against the commit's file the **module fails to load** (`SyntaxError: … does not provide an export named 'DOCTOR_PREFIX'`) — the whole file dies, not one assertion. Any other consumer of the removed exports breaks identically.

**Dependencies / migrations.** None: pure JS, no imports, no package change (`frontend/package.json` is **byte-identical** between Ubuntu and the commit). The only coupling is to `controller.js` and the payload key `room` (§B.7).

**Evidence.** `/tmp/win7/diffs/WT_content.diff`; `/tmp/win7/41_exports.txt` (export lists side by side); Ubuntu lines 39-90 and 212-264, commit lines 30-60 and 112-142 read in full; sandbox execution in §F.


### B.5 `frontend/lib/announcements/controller.js` (286 / 347 / 384 lines)

**Ubuntu behaviour (working tree, 347).** Orchestrates one announcement: capability check, content build, **F3 bounded per-event dedupe store** (`./dedupe.js`, `createAnnouncementStore`, `DEDUPE_DEFAULTS`; `store.shouldSuppress` / `begin` / `release`), activation handling, blocked-retry memory, `source: 'event' | 'operator'`, and `record()` outcomes. Imports only `./content.js` and `./speech-synthesis.js`.

**Windows commit behaviour (384).** Imports `./content.js`, `./speech-synthesis.js` **and `./prerecorded-audio.js`** (`PLAYBACK`); the client dedupe store is replaced by **server-side claiming** through `lib/announcements/call-announcer.js` + `queue-transitions.js` (delivery claim, `delivery_id`, outcome reporting), so duplicate suppression is decided by the backend rather than by a browser store.

**Functional differences.** Duplicate suppression moves from a bounded client store to a server claim (`POST /api/v1/queue/{id}/announcement` → 201 claimed / 200 duplicate, `POST /api/v1/queue/announcements/{id}/outcome`); the controller gains a prerecorded-audio transport path; the Ubuntu `dedupe` options (`dedupeWindowMs`, injectable store) no longer exist; announce-time state moves into the server row (`status`, `outcome_reason`) instead of component state.

**Potential breakage.** Any Ubuntu component or test that constructs the controller with a `dedupe`/store option, or asserts client-side suppression, becomes meaningless — and the module **cannot even load** on Ubuntu today: `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '…/lib/announcements/prerecorded-audio.js' imported from '…/lib/announcements/controller.js'` (proven by execution in §F). A partial replacement (controller from the commit, component from Ubuntu) yields a silently weakened behaviour: no store and no claim.

**Dependencies / migrations.** New modules required: `frontend/lib/announcements/prerecorded-audio.js`, `frontend/lib/announcements/call-announcer.js`, `frontend/lib/announcements/queue-transitions.js`, plus `voice-packs.js` and the commit's `frontend/components/queue/QueueAnnouncements.js`. Backend endpoints in §B.2 and the table in §E. **No new npm dependency.**

**Evidence.** `/tmp/win7/diffs/WT_controller.diff`; `/tmp/win7/41_exports.txt`; Ubuntu `announce()` body lines 216-260; sandbox execution in §F.

### B.6 `frontend/lib/announcements/speech-synthesis.js` (379 / 431 / 379 lines)

**Ubuntu behaviour (working tree, 431).** The F2 outcome model — six terminal outcomes where **only the `end` event proves delivery**: `start` is progress, not completion; a cancelled utterance is `interrupted` (not `spoken`); silence is `blocked`; an autoplay refusal is `blocked`; a throwing engine becomes an error **result**, never a rejection; a throwing `getVoices()` is treated as "no voices"; one utterance at a time (`busy`, replace cancels); subscribe/dispose handled.

**Windows commit behaviour.** `ea828280e7` — **byte-identical to Ubuntu `HEAD`**: the older, coarser model (`start` resolves the "spoken" outcome, a cancel resolves a distinct `cancelled` value, an interruption is `OUTCOME.CANCELLED`).

**Functional differences.** Directly opposing semantics on three points:

| Ubuntu F2 | Windows commit |
|---|---|
| `start` → still pending; only `end` → completed | `start` → `OUTCOME.SPOKEN` |
| interruption → outcome `interrupted` | interruption → `OUTCOME.CANCELLED` |
| no speech engine → `unavailable`, not broken | different capability/outcome mapping (test fails) |

**Potential breakage.** `frontend/tests/queue-announcement-speech.test.mjs` fails on **4 assertions** (proven, §F), including the one that says a started-but-never-ended utterance is not a completed announcement. Operationally this is the difference between "the panel says the patient was called" and "the panel says playback was attempted" — a false-success risk in a waiting room, which is exactly why F2 exists.

**Dependencies / migrations.** None: pure JS, no imports, no npm change.

**Evidence.** Blob hashes §0.3 (HEAD == commit); `/tmp/win7/diffs/WT_speech.diff`; `/tmp/win7/41_exports.txt`; sandbox failures in §F.


### B.7 `frontend/pages/queue.js` (288 / 291 / 419 lines)

**Ubuntu behaviour (working tree, 291).** Server-rendered queue page: doctor/branch/date search, entry list, actions (call / serve / complete / no-show / skip / recall), and the announcement panel driven by the **operator gesture**. The announcement body is:

```js
announcements.announce({
  queueEntryId: entry.id,
  action: 'announce',
  token: entry.token,
  doctorName: …,              // resolved from the payload's doctor_name
  room: entry.room_name,      // the room the payload carries (QUE-006 F4)
}, { source: 'operator', userGesture: true });
```

No polling loop, no visibility handling, no automatic announce on transition.

**Windows commit behaviour (419).** Adds: a **Call** button with `call` / `pleaseWait` / `calledNotice` / `callFailed` captions; **visibility-aware quiet refresh** via `lib/queue/*` (`createQueueRefresher`); **transition tracking** (`trackCalledTransitions`) so a patient who *becomes* `called` is announced automatically; a **delivery claim** through `call-announcer.js` (`eventId: entry.call_event_id`); and an announcement body with **no `doctorName`** and **`room: entry.room`**, where `entry.room` is never set by the page — with the comment *"No queue endpoint returns a room yet; omitted rather than invented."*

**Functional differences.** (a) room announcement **removed** — and the stated reason (no endpoint returns a room) is true **only** of the commit's own backend and false against the Ubuntu backend, which does return `room_name`; (b) doctor name removed (OD-3); (c) new server-coordinated auto-announce on transition; (d) a new Call button whose captions do **not** exist in the Ubuntu `frontend/lib/i18n.js` (`call`, `pleaseWait`, `calledNotice`, `callFailed` are all absent there; all four are present in the commit's `i18n.js`, which is **not** one of the seven files); (e) the new modules of §B.5.

**Potential breakage.** With the Ubuntu `i18n.js` the new captions render as missing keys — the Ubuntu boundary test asserts exactly this and fails with `missing dictionary keys: calledNotice, callFailed, call`. With the Ubuntu component (`components/queue/QueueAnnouncements.js`, not among the seven) the `delivery` prop the commit's page passes is ignored, and the mounted panel is not the one the commit's `useQueueAnnouncements()` expects (it imports `voice-packs.js` and `prerecorded-audio.js`). The build fails outright: `lib/queue`, `call-announcer`, `queue-transitions` do not exist (§A, reason 2).

**Dependencies / migrations.** `frontend/lib/queue/*` (refresher), `lib/announcements/call-announcer.js`, `lib/announcements/queue-transitions.js`, an i18n dictionary change, the panel component, and — at runtime — the two new backend endpoints plus the delivery table.

**Evidence.** `/tmp/win7/diffs/WT_queue.diff`; commit `queue.js:118-235`; Ubuntu `queue.js:60-75`; i18n key check (`/tmp/win7/14_i18n_target.txt`); boundary-test failures in §F.


---

## C. Cross-file compatibility

### C.1 Import graph — what each commit file needs that Ubuntu does not have

| Commit file | Import (resolved against the Ubuntu tree) | Present on Ubuntu? |
|---|---|---|
| `backend/queuing/main.py` | `.events` → `backend/queuing/events.py` | **NO** |
| | `.announcements` → `backend/queuing/announcements.py` | **NO** |
| `backend/queuing/announcements.py` (indirect) | `common.models.QueueAnnouncementDelivery` | **NO** (`grep class QueueAnnouncementDelivery backend/common/models.py` → nothing) |
| | `common.permissions.check_granted` | yes (`permissions.py:222`) |
| | `common.auth.*`, `common.audit.record_audit` | yes |
| `backend/queuing/recovery.py` | stdlib + lazy `main._entry_to_dict` | yes — but the **name** `_room_for_entry` disappears with the commit's `main.py` (§B.3) |
| `backend/appointment/main.py` | nothing new | yes |
| `frontend/lib/announcements/content.js` | none | n/a |
| `frontend/lib/announcements/controller.js` | `./prerecorded-audio.js` | **NO** |
| `frontend/lib/announcements/speech-synthesis.js` | none | n/a |
| `frontend/pages/queue.js` | `lib/queue/*` (`createQueueRefresher`), `lib/announcements/call-announcer.js`, `lib/announcements/queue-transitions.js` | **NO** — Ubuntu's `lib/announcements/` holds only `content.js`, `controller.js`, `dedupe.js`, `speech-synthesis.js`, and there is no `lib/queue/` at all |
| commit's `components/queue/QueueAnnouncements.js` (indirect) | `./prerecorded-audio`, `./voice-packs` | **NO** |

Four distinct missing-module classes, each fatal at import/build time.

### C.2 Contract matrix — what changes under a "full commit" replacement

| Contract | Ubuntu today | Commit | Direction |
|---|---|---|---|
| `GET /api/v1/queue` entry keys | +`room_id`, `room_name`, `location_label`, `room_source` | +`call_event_id`, `call_event_at`, `call_count` | **breaking removal** of the room keys |
| Queue-action / check-in responses | room keys present | room keys absent | breaking removal |
| `POST /api/v1/queue/{id}/announcement` | does not exist | claim: 201 + `delivery_id` / 200 `duplicate_event` / 409 not-current / 404 foreign / 403 no capability | new; needs the table |
| `POST /api/v1/queue/announcements/{id}/outcome` | does not exist | settle `completed`/`failed` + audit | new; needs the table |
| `POST /{id}/missed-turn`, `POST /{id}/recover` | work, room included | work, room dropped | behavioural regression (§B.3) |
| Auth / tenancy | org from token, branch filter, 404 non-disclosing | same rules reused by both new endpoints | **no weakening observed** |
| Denial audit | `install_denial_audit(app, "queuing")` | identical | unchanged |
| i18n dictionary | no `call`/`pleaseWait`/`calledNotice`/`callFailed` | all four added | required companion change |
| npm dependencies | — | none added (`package.json` byte-identical) | safe |
| Python dependencies | — | none added (`requirements.txt` unchanged) | safe |

### C.3 Consumers of the affected payload keys

Grepped across `frontend/**` (excluding `node_modules`) and `backend/queuing/display.py`:

- the **only** runtime consumer of the queue payload's `room_name` is `frontend/pages/queue.js:68` (the announcement itself);
- `frontend/lib/facility.js` and `pages/doctors.js` read `room_name` from **doctor/facility** payloads, not the queue — unaffected;
- the public display service (`backend/queuing/display.py`) contains **no** room usage — unaffected;
- the queue payload's `location_label` has **no frontend consumer** (the appointments UI reads `appt.location_label` from the appointments API), so it is announcement-support only.

Net: removing the room keys breaks the room announcement (F4) and the room-snapshot test suite; nothing else consumes them. That narrows the blast radius but does not make the loss acceptable — the room clause is the feature F4 exists for.

### C.4 Mixed-pairing matrix (what happens if only some files are swapped)

| Backend pairing | Result |
|---|---|
| commit `main.py` + Ubuntu `recovery.py` | `ImportError: _room_for_entry` → **500** on missed-turn/recover |
| Ubuntu `main.py` + commit `recovery.py` | runs; room silently dropped from recovery payloads |
| commit `main.py` + commit `recovery.py` (the set) | `ModuleNotFoundError: events` → **queuing container cannot start** |
| commit `appointment/main.py` + anything | runs; F4 location refactor lost, `common/locations.py` orphaned |

| Frontend pairing | Result |
|---|---|
| commit `content.js` + Ubuntu `controller.js` | `controller.js` imports `announcementEventKey`/`buildAnnouncement` (still exported) but the F1 refusal vocabulary is gone → doctor-less, room-less sentences; `content` tests fail to load |
| commit `controller.js` + Ubuntu `content.js` | `ERR_MODULE_NOT_FOUND: prerecorded-audio.js` → panel blank |
| commit `speech-synthesis.js` + Ubuntu `controller.js` | runs, but outcomes regress to "start = spoken" |
| commit `pages/queue.js` + Ubuntu everything else | build fails (`lib/queue`, `call-announcer`, `queue-transitions`); even if those existed, `entry.room`/`entry.doctor_name` handling and the four i18n keys are missing |
| commit `QueueAnnouncements.js` (outside the seven) + Ubuntu lib | `ERR_MODULE_NOT_FOUND: voice-packs.js` |

Every partial combination either fails to load or degrades a behaviour silently. There is no safe subset.


---

## D. Existing Ubuntu functionality at risk

Ranked by consequence. "Silent" = no error is raised, which is the dangerous class.

| # | Ubuntu feature | Source of the feature | Under the commit | Impact |
|---|---|---|---|---|
| D-1 | **Queue service runs at all** | `backend/queuing/main.py` + existing modules | `ModuleNotFoundError: events` at import → container crash-loop | **Outage** of queue, display, recovery, check-in |
| D-2 | **Frontend builds at all** | `npm run build` in `frontend/Dockerfile` | missing `lib/queue/*`, `call-announcer`, `queue-transitions`, `prerecorded-audio` | **No frontend image** |
| D-3 | **Room announced from the appointment snapshot (F4)** | `queuing/main.py` `_rooms_for`/`_room_for_entry`, `recovery.py`, `pages/queue.js` | all four room keys removed; response roomless by design | Patient is called to no room — the feature's whole purpose |
| D-4 | **Doctor name + honorific in the sentence (F1)** | `content.js` `doctorSegment`/`DOCTOR_PREFIX` | removed (OD-3) | Audible product change: `ডা. করিম` disappears |
| D-5 | **Room number spoken only when announceable (F1)** | `content.js` `roomNumberForSpeech`, `MAX_ROOM_DIGITS` | removed; raw text would be spoken | Would read "3rd floor" aloud if a room ever returns |
| D-6 | **Bangla room-less sentence refused rather than half-spoken (F1/O-3)** | `content.js` `bn.noRoom: null` | replaced by a written Bangla sentence | Turns a refusal into speech — a **wording decision**, not a defect fix |
| D-7 | **"Only `end` proves delivery" (F2)** | `speech-synthesis.js` | `start` resolves `spoken` | Panel reports success on an interrupted call — false comfort |
| D-8 | **Bounded client dedupe store (F3)** | `controller.js` + `dedupe.js` | removed, replaced by a server claim that needs a table this DB lacks | Without the table: every claim 500s, so either announcements stop (if wired to the claim) or the dedupe guarantee is gone |
| D-9 | **Missed-turn recovery responses carry the room** | `recovery.py` | room dropped | Recovery shows less than the queue list did |
| D-10 | **`location_label` refactor shared with appointments** | `common/locations.py` (untracked) | orphaned | Dead code, future drift |
| D-11 | **Ubuntu test coverage of all of the above** | `frontend/tests/queue-announcement-*.test.mjs` (4 files), `backend/tests/test_queue_room_snapshot.py` (untracked) | 2 files fail to load, 8 assertions fail, and 1 backend suite has no matching implementation | Green suite becomes red/unrunnable |

### D.1 What the commit *adds* that Ubuntu does not have (the loss is not one-sided)

Honesty requires recording the gains, because a future owner decision may prefer them: server-side call-event identity (dedupe that survives a page reload and multiple terminals), a delivery row that records who announced what and how it ended (auditable), visibility-aware quiet refresh (less polling noise with several terminals open), a Call button as a first-class action, prerecorded-audio transport and voice-pack configuration, and transition-derived announcements (a patient who becomes `called` is announced without an operator press). These are real capabilities; they arrive **instead of**, not **in addition to**, F1–F4 as currently written.

---

## E. Database and deployment risks

### E.1 Schema and migrations

| Item | Ubuntu state | Commit | Risk |
|---|---|---|---|
| `queue_announcement_deliveries` | **absent** — no local migration mentions it (`grep -rl queue_announcement backend/alembic/versions/` → nothing) | created by `a7c3f19d2b64_add_queue_announcement_deliveries.py` | Every claim/outcome call fails `UndefinedTable` (500) until migrated |
| `voice_packs`, platform announcement config | absent | `c4d8e2a91f60_add_voice_packs_and_platform_config.py` | Frontend voice-pack resolution has no server-side backing |
| `common/models.py` | no `QueueAnnouncementDelivery` | model required | `ImportError` in `announcements.py` (§C.1) |
| Migration head | single head (`a9c4e1f7b2d8` newest) | adds `a7c3f19d2b64`, which does **not** descend from `a9c4e1f7b2d8` (it revises the platform-audit chain) | Two heads → `alembic upgrade head` **aborts** ("multiple heads") unless a merge revision is added |
| `call_event_id` / `call_count` | not stored | derived from the existing `status_history` JSON — **no new column** | no schema risk for call-event identity |
| Queue `room_*` | reads existing `appointments.room_*` via `common/locations.py` | not read at all | no schema risk in either direction |

No new environment variable is introduced by any of the seven files or their direct dependencies; no change to `docker-compose.yml`, `requirements.txt`, `package.json`, `package-lock.json` or `alembic.ini` is required by the commit.

### E.2 Docker / runtime

| Risk | Detail |
|---|---|
| Backend image builds, container exits | `queuing/Dockerfile`: `WORKDIR /app`, `COPY queuing/ ./`, `COPY common/ ./common/`, `CMD uvicorn main:app`. `from events import current_call_event` needs `events.py` in the image; without it `main:app` never imports → restart loop → the frontend and the nginx `/api/v1/queue` route lose their backend |
| Frontend image build fails | `frontend/Dockerfile` runs `npm run build` before `CMD npm start`; missing modules abort the build. There is no "runtime-degraded" state |
| Rebuild required | Even a correct replacement requires **both** images to be rebuilt; a code-only swap leaves the running containers on the old code — "the files changed but nothing did" |
| No new infra requirement | No new service, port, volume, broker, scheduler or env var. The commit adds no websocket/SSE channel (`queue-transitions.js` observes transitions client-side) |
| Ubuntu Docker environment | Inspected only (§F); no container was rebuilt or restarted, per the task restriction |


---

## F. Verification results

### F.1 Inspected (read in this session)

The seven Ubuntu files (full, or hunk-complete via `git diff --no-index`), the seven commit files, all seven working-tree-vs-commit diffs (`/tmp/win7/diffs/`), the commit's `backend/queuing/announcements.py` and `backend/queuing/events.py`, `frontend/lib/announcements/{call-announcer.js,queue-transitions.js}`, `frontend/components/queue/QueueAnnouncements.js` (imports/exports), `frontend/lib/i18n.js` (both versions), `backend/common/locations.py`, `backend/common/models.py` (grep), `backend/common/permissions.py` (grep), `backend/conftest.py`, `backend/queuing/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` (queuing/appointment services), `frontend/package.json`, `backend/queuing/requirements.txt`, `backend/alembic/versions/` (grep), `docs/governance/AMSDP_Docs_Index_V1.0.md` (header snapshot, Revisions 35-36).

### F.2 Tested (safe, non-destructive, executed this session)

**Baseline — Ubuntu tree, announcement suite:**

```
cd frontend && node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test \
  tests/queue-announcement-content.test.mjs tests/queue-announcement-controller.test.mjs \
  tests/queue-announcement-speech.test.mjs tests/queue-announcement-dedupe.test.mjs \
  tests/queue-announcements-boundary.test.mjs
→ tests 73 · pass 73 · fail 0
```

**Sandbox control — the same tree copied to `/tmp/win7/probe/frontend` (node_modules symlinked read-only), four of the five test files:**

```
→ tests 60 · pass 60 · fail 0
```

The copy reproduces the baseline exactly, so it is a faithful rig.

**Sandbox overlay — the four commit frontend files copied over the Ubuntu copy, the same Ubuntu tests:**

```
→ tests 27 · pass 19 · fail 8   (only the speech + boundary files reached execution)
   plus 2 test files that died at module load
```

| Failure | Evidence |
|---|---|
| `queue-announcement-content.test.mjs` | `SyntaxError: The requested module '../lib/announcements/content.js' does not provide an export named 'DOCTOR_PREFIX'` — file did not load |
| `queue-announcement-controller.test.mjs` | `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '…/lib/announcements/prerecorded-audio.js' imported from '…/lib/announcements/controller.js'` — file did not load |
| `without a speech engine the adapter is unavailable, not broken` | assertion |
| `speaking sets the language and the chosen voice, and reports completed` | assertion |
| `start is progress, not completion: only \`end\` resolves completed` | `actual 'spoken'` vs `expected undefined` |
| `a cancelled utterance is reported as interrupted, not as spoken` | `actual 'cancelled'` vs `expected undefined` |
| `every caption the announcement boundary asks for is bilingual` | `missing dictionary keys: calledNotice, callFailed, call` |
| `the page announces the room the payload carries` | expected `/room: entry\.room_name/`, actual `room: entry.room` |

Raw outputs: `/tmp/win7/17_baseline_tests.txt`, `/tmp/win7/19_probe_baseline.txt`, `/tmp/win7/20_probe_target.txt`, counts in `/tmp/win7/22_probe_counts.txt`.

**Static checks executed:** `ast.parse` of all six Python files → **OK ×6** (the backend failure is import-level, not syntax); blob comparison across the three states for all seven files (§0.3); `grep`-based import and payload-key resolution (§C); i18n key presence check (§B.7).

### F.3 Verified at runtime

**Nothing.** No container was restarted or rebuilt, no service was called, no page loaded in a browser, no audio played, no database query issued. Therefore "the queuing container crash-loops" and "the frontend image build fails" are **TESTED at the module-resolution level** (executed) and **INSPECTED at the Dockerfile/import level**, but *not* VERIFIED end-to-end in this environment.

### F.4 Not verified — and what each would need

| Not verified | Why / requirement |
|---|---|
| Backend suite against the commit files | `backend/conftest.py` takes the URL from `AMSDP_DATABASE_URL`; unset, it points at the live database. Requires a **separate throwaway database** + `AMSDP_DATABASE_URL=<throwaway>`. Identified, not created. |
| `backend/tests/test_queue_room_snapshot.py` (untracked, 15 tests) | Same DB requirement; and it imports `queuing.main` which, on the commit, has no room fields at all — it cannot pass by construction. |
| Migrations `a7c3f19d2b64`, `c4d8e2a91f60` | Prohibited (no migrations). The multiple-head conclusion is read from the revision files, not executed. |
| Container start-up / image build | Prohibited (no Docker restart or rebuild). |
| Audio playback, autoplay policy, Bangla voice availability | No browser or device run. |
| Two terminals announcing one call | Needs both backends running with the new table — outside the restrictions. |


---

## G. Final recommendation

### G.1 Answer to the question asked

**Replacing these seven files is NOT SAFE.** Not as a set, not as a subset, and not into the current working tree. Three blockers, in the order they would be hit in practice:

1. The `frontend` image build fails and the `queuing` container cannot start (missing modules, §A reasons 1–2).
2. The new delivery endpoints need a table and a model that do not exist here (§E.1), so even a started service returns 500 on any announcement claim.
3. The replacement silently deletes F1–F4 — including the room announcement and the "only `end` proves delivery" outcome model — and the Ubuntu suite goes from 73/73 green to 2 unloadable files plus 8 failed assertions (§F.2).

### G.2 Corrective work required before *any* replacement, in order

| # | Action | Gate |
|---|---|---|
| G-1 | **Preserve the uncommitted Ubuntu work first.** Commit (or at minimum branch/patch) the QUE-006 F1–F4 working-tree state, including the untracked `backend/common/locations.py`, `frontend/lib/announcements/dedupe.js`, `backend/tests/test_queue_room_snapshot.py`, `frontend/tests/queue-announcement-dedupe.test.mjs`. Without this step the four corrections exist nowhere but this disk. | Must precede any pull/replace |
| G-2 | **Owner decision on lineage (business rule, §1.2 precedence):** F1–F4 (doctor + honorific, room spoken as a number, refusal when no approved sentence exists, client dedupe) versus W2/OD-3 (no doctor named, no room announced, server-side claim). This is a product/privacy decision, not an engineering merge, and it changes what patients hear. | Blocks G-3…G-6 |
| G-3 | **Replace as a whole commit, never as seven files.** Fetch `2fc007a` and take its complete file set — at minimum the seven plus `backend/queuing/{events.py,announcements.py}`, `backend/common/models.py`, `frontend/lib/announcements/{prerecorded-audio.js,call-announcer.js,queue-transitions.js,voice-packs.js,delivery.js}`, `frontend/lib/queue/*`, `frontend/components/queue/QueueAnnouncements.js`, `frontend/lib/i18n.js`, and the matching tests. | G-2 |
| G-4 | **Migrations:** add `a7c3f19d2b64` + `c4d8e2a91f60` **and** a merge revision joining them to the current head `a9c4e1f7b2d8` (forward-only, idempotent), rehearsed on a throwaway database first. `alembic upgrade head` must not see two heads. | G-3 |
| G-5 | **Decide what happens to the room under lineage W2:** either re-apply a room snapshot on top of it, or record the room announcement as *intentionally withdrawn* in the business rules. The commit's comment ("No queue endpoint returns a room yet") is true only inside its own tree; unaddressed, the room feature dies by comment. | G-2 |
| G-6 | **Re-baseline the tests, rebuild both images,** then verify: `GET /api/v1/queue` returns the chosen key set; one claim wins and the second terminal reports `duplicate_event`; the panel reaches `completed` only on `end`; missed-turn recovery still answers; the queue page renders in Bengali and English with the new captions. | G-4, G-5 |
| G-7 | **Do not delete** the superseded F1–F4 documents or tests; mark them superseded in the index with a Revision entry, per §11's never-delete rule. | G-6 |

### G.3 What this assessment deliberately did **not** do

No file was modified, moved, renamed, staged, committed or reverted; no `git reset`/`checkout`/`clean`/`merge`/`rebase` was run; no migration was executed; the live PostgreSQL database was never contacted; no container was restarted or rebuilt; no environment file or secret was read into this report. Only this report was created, plus one row and one Revision 37 entry appended to `docs/governance/AMSDP_Docs_Index_V1.0.md` (§H.2).

**Report location:** `docs/implementation/AMSDP_Windows_Commit_Seven_File_Compatibility_Assessment_V1.0.md` (subject folder `implementation/`, per §11; no filename collision existed at creation time).


---

## H. Governance and Skill Compliance

| §4 domain | Governance applied | Evidence in this report |
|---|---|---|
| Backend API / service endpoints | `saas-application-security.md` (adapted) | §B.2, §C.2 — routes, payload contracts; no client-trusted authorisation introduced by the commit |
| Auth / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py` | §C.2 — `queue.manage`/`queue.consult` gate, 404-not-403, no weakening found |
| Multi-tenant isolation | `saas-multitenant-data.md` (adapted), `backend/common/auth.py` scope checks | §B.2, §C.2 — org from token, branch 404, `organization_id` as the only tenant key |
| Database / migrations | `saas-multitenant-data.md` §4–5, Alembic chain | §E.1 — forward-only/idempotent requirement; multiple-head blocker |
| Frontend UI | `saas-frontend-ux.md` (adapted), `frontend/lib/i18n.js` | §B.4–B.7 — bilingual captions, missing keys identified |
| Audit | `saas-observability.md` (adapted), `backend/common/audit.py` | §C.2 — claim/outcome audit events noted, append-only requirement stated |
| Docker / deployment | `saas-cicd-workflow.md` (adapted) | §E.2 — image build/start analysis, honest CI state |
| Documentation | §11, §12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | this file's placement and its index registration (§H.2) |

- **Skills:** none installed in this workspace (verified: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used, claimed or invented; the governance documents above were used instead.
- **Non-negotiables honoured:** no secret, token, credential or JWT material appears in this report; the live PostgreSQL database was never contacted; audit and denial-audit behaviour was compared, not changed; no capability is claimed beyond §F.1–F.4 — the §7 evidence standard is applied explicitly, keeping INSPECTED, TESTED and VERIFIED apart.
- **Execution boundaries honoured (§9):** read-only assessment, no Git state changes, no migrations, no Docker actions, no environment or secret changes. Post-check at the end of the task: `git status --porcelain -uall` = 23 entries (22 carried in + this report), `HEAD = cd2f9ec`, and the 13-file / +726 / −154 diffstat unchanged.
- **Conflicts reported, not resolved (§1):** the F1–F4 and W2/OD-3 lineages contradict each other on what patients hear; this report records both sides and refers the decision to the Product Owner (O-1, O-2) instead of silently adopting either.

### H.1 Open items

| ID | Item | Decision owner |
|---|---|---|
| O-1 | Whether the F1–F4 lineage or the W2/OD-3 lineage is authoritative for announcements (they differ in *what patients hear*) | Product Owner |
| O-2 | Whether the room announcement is re-applied on top of W2 or formally withdrawn from the business rules | Product Owner |
| O-3 | Whether the uncommitted F1–F4 working-tree work is committed **before** any replacement (G-1) — until then it exists nowhere but this disk | Product Owner / engineering |
| O-4 | Whether the two sibling working-tree reports (`implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md`, `implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md`) are adopted into the registered set — they are enumerated as unregistered in the index's Revision 37 and were not acted on here, per §11's uncertain-ownership rule | Index owner |

### H.2 Index registration — applied

Per §12 ("Creating … a document obligates an index update in the same task"), `docs/governance/AMSDP_Docs_Index_V1.0.md` was updated in this task: **one row appended** to the `implementation/` table (immediately after the QUE-006 F1–F4 report's row, its size cell holding the byte count measured with `wc -c` at registration) and **one appended Revision 37 entry** recording the change, with no existing row overwritten, moved or deleted (no migration-manifest entry is due, §11, because nothing moved or renamed). The header snapshot sentence — the historical 2026-11-20 figures — was **not rewritten**; a dated count-check parenthetical was appended after it instead, in the same style Revision 32 used, recording `find docs -name '*.md'` = **98**, **92** registered, **6** unregistered, each of the six named, and the header's own revision date was bumped from 2026-11-20 to 2026-11-22. That file also carries another task's uncommitted Revision 36 edits; this task appended only and touched none of them. The only existing line this task replaced anywhere is that header *revised* date, which is also the only deleted line in the file's uncommitted diff against `HEAD` (verified with `git diff --numstat`); every other change is an addition.


---

## Appendix A — Evidence artefacts and reproduction

All artefacts live outside the repository, under `/tmp/win7/` (nothing was written into the tree except this report and the index row):

| Artefact | Content |
|---|---|
| `01_fetch.txt`, `10_fetch2.txt` | HTTPS fetch log for commit `2fc007a` |
| `02_target_ids.txt`, `03_diffstat.txt`, `04_diffsizes.txt` | commit file inventory and sizes |
| `diffs/WT_*.diff` | the seven working-tree-vs-commit diffs |
| `33_matrix2.txt` | the three-way blob/line matrix (§0.3) |
| `39_target_qmain.txt`, `40_local_qmain.txt` | `_entry_to_dict`, room helpers, commit import wiring |
| `27_routes.txt`, `25_claim.txt` | announcement routes, claim SQL, capability gate |
| `41_exports.txt` | export lists for the four frontend files, both lineages |
| `14_i18n_target.txt`, `16_i18n_local.txt` | i18n key presence, commit vs Ubuntu |
| `17_baseline_tests.txt`, `19_probe_baseline.txt`, `20_probe_target.txt`, `22_probe_counts.txt` | the three test executions of §F.2 |
| `probe/frontend/` | the sandbox copy used for the overlay experiment (`node_modules` symlinked read-only) |

Reproduction of the decisive experiment, without touching the repository:

```bash
mkdir -p /tmp/probe && cd /tmp/probe
cp -r /home/shomonrobie/amsdp/frontend/{lib,tests,components,pages,package.json} .
ln -s /home/shomonrobie/amsdp/frontend/node_modules node_modules
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/queue-announcement-*.test.mjs   # 60/60
cp <commit>/frontend/lib/announcements/{content,controller,speech-synthesis}.js lib/announcements/
cp <commit>/frontend/pages/queue.js pages/
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/queue-announcement-*.test.mjs   # 2 files unloadable, 8 assertion failures
```

The backend equivalent needs a throwaway database plus the commit's `events.py`, `announcements.py` and `QueueAnnouncementDelivery` model; it is described here and was **not** run (§F.4).

---

## Appendix B — Reading guide

| If you want to know… | Read |
|---|---|
| Can I just copy these seven files over? | §G.1 — no. Then §A reasons 1–2 for the two hard blockers |
| Which of the seven differ, and how much? | §0.3 (three-way matrix) and §B.1–B.7 |
| What exactly do patients stop hearing? | §D, rows D-3…D-8 |
| Why do the new endpoints fail even after the service starts? | §E.1 |
| What must happen before a replacement is attempted? | §G.2, gates G-1…G-7 |
| What was actually run, and what was only read? | §F.2 (executed) vs §F.1/§F.3/§F.4 (read / not verified) |

*End of report. Assessment only — no fix was implemented, and no repository, database, container or Git state was modified by this task beyond this document and its index row.*

