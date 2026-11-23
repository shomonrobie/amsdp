# QUE-006 W2 — Pre-Commit Review and Repository Reconciliation Assessment

| Field | Value |
|---|---|
| Report | `docs/implementation/QUE-006_W2_PRE_COMMIT_REVIEW_REPORT.md` |
| Date | 2026-11-21 |
| Host | Windows checkout, `E:\amsdp` |
| Branch / HEAD | `hackathon-mvp` @ `37cf3d1e9db76834044afd48fa5729463a26ec47` |
| Task class | Inspection and reporting only (Phase A–G of the owner's instruction) |
| Changes made by this task | **One new file — this report.** No source, test, document, manifest, migration or audio asset was edited, staged, committed, pushed, pulled, merged or deleted |
| Headline verdict | **NOT READY for a W2 commit as the tree stands** — one migration defect (second Alembic head), four mixed-workstream files, and a room divergence that is *not* a Windows regression |

Status vocabulary used throughout: **VERIFIED** (executed on this host, output
observed), **PARTIALLY VERIFIED** (part executed, part inferred), **NOT
VERIFIED** (no execution possible here), **BLOCKED** (cannot proceed without an
unavailable dependency), **NOT APPLICABLE**. Every claim below is tagged with
the evidence that produced it; anything inferred from a document rather than
from execution is marked *assumption*.

---

## 1. Executive summary

1. **The suspected `main.py` room regression does not exist in this checkout.**
   The working-tree diff of `backend/queuing/main.py` against `HEAD` is
   **+22 / −0 lines** — pure addition. There is no deleted line, so no room
   serialization was removed. The reason is simpler and more serious:
   **this checkout never contained the room work at all.**
   `backend/common/locations.py` does not exist (recursive search of the whole
   tree: 0 hits), and `room_payload`, `_rooms_for`, `_room_for_entry`,
   `room_source` have **0 matches** in the working tree *and* **0 matches in
   `HEAD`**. The Ubuntu room implementation is local to the Ubuntu machine and
   has never been committed or pushed to `origin`. *(VERIFIED — Phase A/C
   commands, §4.)*
2. **Consequence for reconciliation:** this is not a "restore deleted code"
   task. It is a "Ubuntu is ahead, uncommitted; Windows is the committed
   baseline plus W2" task. Applying the Windows `main.py` on Ubuntu would
   destroy the Ubuntu room code — the opposite of the risk first suspected.
   The merge must be done **on Ubuntu, by adding the 22 W2 lines into the Ubuntu
   file**, never by copying the Windows file over it. *(§12.)*
3. **A genuine commit blocker was found that was not previously reported:**
   the new migration declares `down_revision = 'f8a2b3c4d5e6'`, but
   `f8a2b3c4d5e6` is **not** the head of the chain. The head is
   `a9c4e1f7b2d8`, a merge revision whose parents are
   `('b3d7e91f6a24', 'f8a2b3c4d5e6')`. Today the chain has **one head**;
   adding `a7c3f19d2b64` off `f8a2b3c4d5e6` produces **two heads**, and
   `alembic upgrade head` becomes ambiguous. The fix is one line
   (`down_revision = 'a9c4e1f7b2d8'`), but it has **not** been applied — this
   task may not edit code, and the file must not be committed as-is.
   *(VERIFIED statically — 15 revision files parsed, DAG computed, §7.)*
4. **Scope reality:** of 164 working-tree entries (12 modified, 152 untracked),
   only **12** are W2-specific: 11 are safe to name in a W2 commit, and the
   twelfth is the migration (HOLD, §7). The remainder is QUE-006 W1 prerecorded
   playback, W3 voice packs, W5 remote installation, POD-12 call control, the
   audio catalogue/asset work and 18 milestone documents.
5. **Four files are mixed-workstream** and cannot be committed as "W2" without
   either bundling other workstreams or editing them: `frontend/pages/queue.js`
   (W2 + POD-12), `frontend/components/queue/QueueAnnouncements.js`
   (W2 + W1), `frontend/lib/i18n.js` (W2 + W1/W3 + POD-12),
   `backend/queuing/tests/test_queue.py` (18 W2 tests + 2 POD-12 tests).
6. **`queue.js` already consumes `entry.room`** while noting *"No queue endpoint
   returns a room yet; omitted rather than invented"* (`frontend/pages/queue.js`
   lines 78–80). The frontend seam for room data therefore already exists; the
   Ubuntu room payload will light it up with no frontend change. *(VERIFIED —
   file read.)*
7. **Evidence actually produced in this session:** 146 frontend queue tests
   (145 pass, 0 fail, 1 environment skip) and 13/13 call-event identity tests —
   the latter being *every* `test_` function in
   `backend/queuing/tests/test_queue_events.py`, executed through a plain
   interpreter. Backend route tests, the migration and any browser runtime
   observation remain **BLOCKED** on this host (§8).
8. **Recommendation:** do **not** commit yet. Reparent the migration, decide the
   mixed-file split, then commit W2 in the eleven-file scope of §9 — and treat
   `backend/queuing/main.py` as HOLD until the Ubuntu reconciliation in §12 is
   agreed, because committing the Windows file makes it canonical and the next
   merge is where Ubuntu's room code would be lost.

---

## 2. Repository state (Phase A)

| Item | Observed value | Status |
|---|---|---|
| Current branch | `hackathon-mvp` | VERIFIED |
| HEAD commit | `37cf3d1e9db76834044afd48fa5729463a26ec47` — `docs(governance): register the Q1-Q5 and QUE-006 documents and correct two counts` | VERIFIED |
| Upstream | `origin/hackathon-mvp`, tracking reported as `## hackathon-mvp...origin/hackathon-mvp` with **no** `[ahead n]` / `[behind n]` marker | VERIFIED (in sync with the last recorded remote state; the remote was **not** contacted) |
| Remote `origin` | fetch `https://github.com/shomonrobie/amsdp/`, push `https://github.com/shomonrobie/amsdp/` | PARTIALLY VERIFIED — owner/repo match the documented workspace (`/home/shomonrobie/amsdp`); identity was not re-confirmed, because fetching was forbidden |
| Branches present | local `hackathon-mvp`; remote refs `origin/HEAD -> origin/main`, `origin/hackathon-mvp`, `origin/main` | VERIFIED |
| Tags / stashes | none / none | VERIFIED |
| Working tree | **dirty** — 12 modified, 152 untracked (164 entries with `-uall`) | VERIFIED |
| Last five commits | `37cf3d1`, `03d9252`, `3cacede`, `66e545e`, `e67327e` | VERIFIED |

The five preceding commits establish the context: `e67327e` added browser
speech synthesis (the seam W2 replaces), `66e545e` added appointment Q1–Q5
(including the merge migration `a9c4e1f7b2d8`), and the three `docs(...)`
commits registered the QUE-006 document series. **No QUE-006 code beyond
`e67327e` has ever been committed** — every workstream W1–W6 exists only as
working-tree changes.

### Modified files and diff size

| File | +/− | Note |
|---|---|---|
| `.gitignore` | +4 / −0 | ignores `/frontend/.audio-originals-backup/` |
| `backend/common/models.py` | +58 / −0 | one new class `QueueAnnouncementDelivery` |
| `backend/queuing/main.py` | +22 / −0 | W2 imports, router registration, 3 new dict keys |
| `backend/queuing/tests/test_queue.py` | +339 / −1 | 20 new test methods + 7 helpers |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | +488 / −9 | Revision 48 block + many registrations |
| `frontend/components/queue/QueueAnnouncements.js` | +88 / −11 | W2 delivery UI **and** W1 audio wiring |
| `frontend/lib/announcements/content.js` | +19 / −17 | doctor-name removal / template rework |
| `frontend/lib/announcements/controller.js` | +109 / −11 | prerecorded-playback path (W1) |
| `frontend/lib/i18n.js` | +12 / −2 | captions for W1, W2, W3 and POD-12 |
| `frontend/pages/queue.js` | +139 / −8 | W2 announcer + refresher, POD-12 call gate |
| `frontend/tests/queue-announcement-content.test.mjs` | +82 / −27 | content/template assertions |
| `frontend/tests/queue-announcement-controller.test.mjs` | +0 / −1 | one assertion removed |

**Total: 12 files, 1360 insertions, 87 deletions**, of which the W2-specific
share visible on its own is `models.py` (+58), `test_queue.py` (18 of 20 tests)
and `main.py` (+22).

---

## 3. Full pending-file inventory (Phase B)

164 entries = 12 modified + 152 untracked. Every entry is accounted for below;
the 72 audio files and the 43 script files are aggregated into two rows and
counted explicitly, because each is a homogeneous group that no W2 commit
should absorb wholesale. (The inventory was taken before this report existed;
this report is the next untracked entry — `git status` now shows 165.)

### 3.1 QUE-006 W2 — announcement reliability (12 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `backend/queuing/events.py` | ?? (new, 96 lines) | W2 | Pure derivation of `qce:<entry>:<index>` from `status_history` | none (stdlib only) | **INCLUDE** |
| `backend/queuing/announcements.py` | ?? (new, 272 lines) | W2 | Claim + outcome endpoints, audit, scope checks | `events.py`, `models.py`, migration | **INCLUDE** (runtime depends on the migration — §7) |
| `backend/queuing/tests/test_queue_events.py` | ?? (new, 13 tests) | W2 | Identity properties, no database needed | `events.py` | **INCLUDE** — executed 13/13 here |
| `backend/common/models.py` | M (+58) | W2 | `QueueAnnouncementDelivery` model only | migration mirrors it | **INCLUDE** — one additive block |
| `backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py` | ?? (new, 95 lines) | W2 | Creates the delivery table | **wrong parent** (§7) | **HOLD** — creates a second Alembic head |
| `frontend/lib/announcements/delivery.js` | ?? (new, 195 lines) | W2 | Claim/play/report protocol client | `call-announcer.js` | **INCLUDE** |
| `frontend/lib/announcements/call-announcer.js` | ?? (new, 180 lines) | W2 | Never-throwing claim → play → report | `delivery.js` | **INCLUDE** |
| `frontend/lib/announcements/queue-transitions.js` | ?? (new) | W2 | Which entries just became `called` (header: “QUE-006 / W2”) | pure | **INCLUDE** |
| `frontend/lib/queue/queue-refresh.js` | ?? (new, 142 lines) | W2 | 20 s non-destructive refresher | pure | **INCLUDE** |
| `frontend/tests/queue-announcement-delivery.test.mjs` | ?? (new, 18 tests) | W2 | Claim/dedupe/outcome behaviour | `delivery.js` | **INCLUDE** — 18/18 here |
| `frontend/tests/queue-refresh-safety.test.mjs` | ?? (new, 8 tests) | W2 | Refresher safety properties | `queue-refresh.js` | **INCLUDE** — 8/8 here |
| `frontend/tests/queue-announcement-w2-integration.test.mjs` | ?? (new, 19 tests) | W2 | Ordering, two-terminal ownership, page wiring | real controller + announcer | **INCLUDE** — 19/19 here |

**11 INCLUDE + 1 HOLD.** Nothing else in the tree is W2-earned.

### 3.2 QUE-006 W1 — prerecorded playback (6 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `frontend/lib/announcements/prerecorded-audio.js` | ?? (new) | W1 | Clip playback layer | `public/audio/**` | **EXCLUDE** |
| `frontend/lib/announcements/segments.js` | ?? (new) | W1 | Composed clip sequencing | `prerecorded-audio.js` | **EXCLUDE** |
| `frontend/lib/announcements/controller.js` | M (+109 / −11) | W1 | Prerecorded path in the controller (22 added lines mention `prerecorded`, **0** mention `delivery`/`claim`) | W1 modules | **EXCLUDE** |
| `frontend/tests/queue-announcement-prerecorded.test.mjs` | ?? (new) | W1 | Prerecorded tests | W1 modules | **EXCLUDE** |
| `frontend/tests/queue-announcement-segments.test.mjs` | ?? (new) | W1 | Segment tests | W1 modules | **EXCLUDE** |
| `frontend/tests/queue-announcement-controller.test.mjs` | M (−1) | W1 | One assertion dropped with the controller change | — | **EXCLUDE** |

### 3.3 QUE-006 POD-12 — call control (2 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `frontend/lib/queue/queue-call.js` | ?? (new) | POD-12 | `createCallGate` / `isCallable` / `performCall` | `queue.manage` capability | **EXCLUDE from W2** — but it is a *build dependency of `pages/queue.js`* (§11) |
| `frontend/tests/queue-call-control.test.mjs` | ?? (new, 18 tests) | POD-12 | Call-gate tests | `queue-call.js` | **EXCLUDE** |

### 3.4 QUE-006 W3 — voice configuration (2 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `frontend/lib/announcements/voice-packs.js` | ?? (new) | W3 | Voice-pack catalogue/client | `public/audio/manifest.json` | **EXCLUDE** |
| `frontend/tests/queue-announcement-voice-packs.test.mjs` | ?? (new) | W3 | Voice-pack tests | `voice-packs.js` | **EXCLUDE** |

### 3.5 QUE-006 W5 — remote installation (3 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `scripts/que-006-agent/agent.mjs` | ?? | W5 | Installation agent CLI | `lib/installer.mjs` | **EXCLUDE** |
| `scripts/que-006-agent/lib/installer.mjs` | ?? | W5 | Installer logic | — | **EXCLUDE** |
| `scripts/que-006-agent/tests/installer.test.mjs` | ?? | W5 | Installer tests | `installer.mjs` | **EXCLUDE** |

### 3.6 Audio catalogue, assets and tooling (43 untracked scripts + 72 binaries)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `scripts/que-006-audio/**` — 30 untracked (8 top-level, 9 in `.work/`, 13 in `lib/`) | ?? | audio catalogue | Generation, standardisation and validation tooling | TTS providers / env credentials | **EXCLUDE** — and `.work/` (tool state JSON, `validate.mjs.superseded-draft`, a master WAV) should not be committed at all |
| `scripts/que-006-audio/preview/**` — 9 untracked | ?? | audio review | Human-review page; `generated/` is covered by its own nested `.gitignore` | — | **EXCLUDE** |
| `scripts/que-006-w2-reliability/check_call_event_identity.py` | ?? | **W2 tooling** | Runs the 13 identity tests without pytest | `queuing/events.py` | **REVIEW** — belongs with W2 in spirit, but it is tooling |
| `frontend/public/audio/**` — 72 untracked (43 `bn/`, 28 `en/`, 1 `manifest.json`; 4,788,625 bytes) | ?? | assets | The clips W1/W2 actually play | read at `QueueAnnouncements.js:68` | **EXCLUDE from W2** — separate owner decision: **0 audio files are tracked today** (`git ls-files frontend/public` = 0) |
| `frontend/lib/announcements/content.js` | M (+19 / −17) | doctor-name removal | Template / `buildAnnouncement` rework | content tests | **EXCLUDE** |
| `frontend/tests/queue-announcement-content.test.mjs` | M (+82 / −27) | doctor-name removal | Matching assertions | `content.js` | **EXCLUDE** |
| `.gitignore` | M (+4) | assets | Ignores `/frontend/.audio-originals-backup/` | — | **EXCLUDE** from W2 (harmless, but a different workstream) |

### 3.7 Documentation (18 new reports + 1 modified index)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | M (+488 / −9) | docs (all) | Revision 48 block and registrations for every QUE-006 document | — | **EXCLUDE from a code commit**; ship as its own docs commit |
| `docs/implementation/QUE-006_MASTER_IMPLEMENTATION_PLAN.md` | ?? | docs | Plan | — | **EXCLUDE** (docs commit) |
| `docs/implementation/QUE-006_POD-12_QUEUE_CALL_CONTROL_IMPLEMENTATION_REPORT.md` | ?? | docs (POD-12) | Report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_IMPLEMENTATION_REPORT.md` | ?? | docs (W1) | Report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_REPORT.md` | ?? | docs (W1) | **Second** W1 report — two exist | — | **HOLD** — duplicate/version question is an owner decision |
| `docs/implementation/QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md` | ?? | docs (W2) | Earlier W2 report | — | **EXCLUDE** from code |
| `docs/implementation/QUE-006_W2_QUEUE_INTEGRATION_REPORT.md` | ?? | docs (W2) | **Third** W2 report | — | **HOLD** — needs an owner ruling on which W2 report is current |
| `docs/implementation/QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md` | ?? | docs (W2) | Documents the files in §3.1 | — | **REVIEW** — accurate, ends at PARTIALLY IMPLEMENTED; this report is its successor |
| `docs/implementation/QUE-006_W3_VOICE_CONFIGURATION_REPORT.md` | ?? | docs (W3) | Report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_W4_ROOM_SUPPORT_REPORT.md` | ?? | docs (W4) | Report; see §5 — it records that rooms are **absent** from the queue API | — | **EXCLUDE** |
| `docs/implementation/QUE-006_W5_REMOTE_INSTALLATION_REPORT.md` | ?? | docs (W5) | Report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_W6_ASSET_DEPENDENCY_REPORT.md` | ?? | docs (W6) | Report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` | ?? | docs (audio) | Catalogue | — | **EXCLUDE** |
| `docs/implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` | ?? | docs (audio) | Standardisation report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md` | ?? | docs (audio) | Provider report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` | ?? | docs (audio) | Doctor-name removal report | — | **EXCLUDE** |
| `docs/implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` | ?? | docs (audio) | Human-verification preparation | — | **EXCLUDE** |
| `docs/implementation/QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md` | ?? | docs | Roadmap | — | **EXCLUDE** |
| `docs/implementation/QUE-006_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | ?? | docs | “Final” report written before W2 was complete | — | **HOLD** — the title overstates what §8 can prove |

### 3.8 Mixed-purpose or dependency-uncertain (6 files)

| File | Git status | Workstream | Purpose | Dependencies | Commit recommendation |
|---|---|---|---|---|---|
| `backend/queuing/main.py` | M (+22 / −0) | **W2 + room divergence** | 3 imports/router registration + 3 response keys | `events.py`, `announcements.py` | **HOLD** — §§4, 5, 11: the change itself is correct, but committing it makes a room-less file canonical |
| `frontend/pages/queue.js` | M (+139 / −8) | **W2 + POD-12** | announcer, refresher, call gate | `queue-call.js` (**POD-12**, untracked) | **REVIEW/HOLD** — cannot build without the POD-12 module |
| `frontend/components/queue/QueueAnnouncements.js` | M (+88 / −11) | **W2 + W1** | delivery UI + audio wiring (added lines: 8 `delivery`, 3 `claim`, 6 `prerecorded`) | W1 modules | **REVIEW** |
| `frontend/lib/i18n.js` | M (+12 / −2) | **W1 + W2 + W3 + POD-12** | captions — `announceElsewhere` is W2, `callNext`/`startConsult` are POD-12, `announcePackMissing`/`announcePackHint` are W1/W3 | — | **REVIEW** |
| `backend/queuing/tests/test_queue.py` | M (+339 / −1) | **W2 + POD-12** | 18 W2 tests + 2 POD-12 tests (`test_receptionist_can_call_a_waiting_entry`, `test_doctor_cannot_call_without_queue_manage`) + 7 helpers | route deps | **REVIEW** — cannot be split without editing |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | M (+488 / −9) | **docs (all)** | see §3.7 | — | **REVIEW** |

**Unknown or unattributable: none.** Every untracked file carries either a
header naming its workstream or a filename that ties it to one.

---

## 4. `main.py` comparison (Phase C)

### 4.1 Method and a statement about the Ubuntu file

The Windows file was compared with its committed baseline using
`git diff backend/queuing/main.py` and `git show HEAD:backend/queuing/main.py`.
**The Ubuntu file was not available in this checkout** and was not transmitted,
so every statement below about "Ubuntu's version" derives from the Product
Owner's description plus this repository's own
`docs/implementation/QUE-006_W4_ROOM_SUPPORT_REPORT.md` — it is *documented
evidence about the workspace*, not a byte-level diff. That limitation is the
most important caveat in this report and is repeated in §5.

### 4.2 The complete Windows diff — 3 hunks, 22 lines, zero deletions

| # | Location | Change | Assessment |
|---|---|---|---|
| 1 | after the recovery router registration (~line 44) | `from .events import current_call_event` + `from .announcements import router as announcements_router`, both with a relative-import fallback, then `app.include_router(announcements_router)` | Correct placeholder: it follows the file's existing `try/except ImportError` convention, appears after every pre-existing router, and registers a router with prefix `/api/v1/queue`, which collides with no existing route (§4.5) |
| 2 | `_entry_to_dict` head | `event = current_call_event(e.id, e.status_history)` | Reads the persisted history; no new column, no new query |
| 3 | `_entry_to_dict` body | `"call_event_id"`, `"call_event_at"`, `"call_count"` | Additive keys; `""`/`""`/`0` for an entry never called |

There is **no hunk that removes anything**, so the diffstat `22 ++++` with no
`-` is itself the proof that this edit deleted no room code. A stray blank line
was added after `_entry_to_dict` (cosmetic).

### 4.3 Room support — checklist against the working tree and against `HEAD`

| Item | In Windows working tree | In `HEAD` | In this checkout at all | Verdict |
|---|---|---|---|---|
| `common.locations` module | absent | absent | **absent** — `locations.py` found nowhere (recursive search, 0 hits) | NOT APPLICABLE here |
| `common.locations.room_payload` | 0 matches | 0 matches | 0 matches | NOT APPLICABLE here |
| `_rooms_for()` | 0 matches | 0 matches | 0 matches | NOT APPLICABLE here |
| `_room_for_entry()` | 0 matches | 0 matches | 0 matches | NOT APPLICABLE here |
| Room snapshot serialization | 0 matches | 0 matches | 0 matches | NOT APPLICABLE here |
| `room_id` / `room_name` / `location_label` / `room_source` in queue code | 0 matches in `backend/` | 0 matches | 0 matches | NOT APPLICABLE here |
| Room resolution in queue listing / history / action responses | none | none | none | **absent by design, in both revisions** |
| Room data model (unrelated, committed) | `FacilityRoom` (`facility_rooms`), `schedule_sessions.room_id`, `appointments.room_id` present in `common/models.py` | same | same | VERIFIED — rooms exist as *facility* data, not as *queue* data |

**Regression verdict: NO REGRESSION FOUND — and none could have been introduced
by this diff.** The Windows edit is additive; the room functionality attributed
to Ubuntu has never existed in this checkout in any revision. The divergence is
therefore *Ubuntu ahead of the committed baseline*, not *Windows having removed
work*. (VERIFIED for every row above by direct search; the Ubuntu-side claim is
the Product Owner's statement.)

The one piece of in-tree corroboration is the report the W4 workstream left
here, `docs/implementation/QUE-006_W4_ROOM_SUPPORT_REPORT.md`, line 14 of which
states: *“`queue_entries` has **no** room column and no room in its response —
`backend/common/models.py:854-884`; `backend/queuing/main.py:_entry_to_dict`.”*
That is the Windows view of W4: a **gap**, not an implementation.

### 4.4 Existing queue functionality — preservation

Because `git diff` reports **three hunks in two locations**, every other byte of
the file is identical to `HEAD`. That is the strongest available preservation
argument, and it is mechanical rather than interpretive:

| Pre-existing capability | Route / location in the file | Touched by the W2 diff? | State |
|---|---|---|---|
| Queue listing | `GET /api/v1/queue` (line 141) | only through `_entry_to_dict` (3 added keys) | unchanged, additive keys only |
| Appointment check-in | `POST /api/v1/queue/check-in` (191) | no | byte-identical to `HEAD` |
| Walk-in enqueue | `POST /api/v1/queue/enqueue` (316) | no | byte-identical |
| Queue transition / `call` | `PATCH /api/v1/queue/{entry_id}` (417) | no | byte-identical |
| Reordering | `POST /api/v1/queue/reorder` (496) | no | byte-identical |
| Queue history | `GET /api/v1/queue/history` (569) | no | byte-identical |
| Permission enforcement (`queue.manage`, `queue.consult`) | inside each route | no | byte-identical; **no new capability invented** |
| Organisation / branch isolation | `_scoped_entry_or_404` and its callers | no | byte-identical; foreign ids still 404 |
| Existing audit records | `record_audit(..., action=f"queue.{data.action}", ...)` at line 464 — yields `queue.call` for a call; plus `queue.checkin` (284), `queue.enqueue` (372), `queue.reorder` (540) | no | byte-identical; still one `queue.call` per successful call |
| Notification hooks | `_notify(...)` (line 59) and its five call sites | no | byte-identical |

### 4.5 W2 integration — checklist

| Item | Present | Evidence |
|---|---|---|
| `current_call_event` import | yes | hunk 1, with the file's usual relative-import fallback |
| Announcement router registration | yes | `app.include_router(announcements_router)` |
| Server-generated `call_event_id` | yes | `qce:<entry_id>:<history index>`, derived in `_entry_to_dict` |
| `call_event_at` | yes | the same history record's `at` |
| `call_count` | yes | number of `call` events in the history |
| Status-history serialization unchanged | yes | `"status_history": e.status_history or []` is an untouched line |
| Route collisions with the six existing routes | **none** | new paths are `POST /api/v1/queue/{entry_id}/announcement` and `POST /api/v1/queue/announcements/{delivery_id}/outcome`; the only pre-existing dynamic route is `PATCH /api/v1/queue/{entry_id}` — different method *and* different segment count, so no shadowing, and the two announcement routes differ in segment count from each other |
| Compatibility with the delivery API | yes | `announcements.py` recomputes the same id from the same history before accepting a claim, so the published key and the validated key cannot drift |

The three new keys are **additive** to a dict literal, which cannot break a
consumer that ignores unknown keys. These routes declare no response schema
(they return plain dicts), so no Pydantic model had to be widened.

**`main.py` verdict: the Windows change is correct and self-consistent
(PARTIALLY VERIFIED — read line by line, route table enumerated; no backend
execution is possible on this host). It is nevertheless classified HOLD in §11
for the reconciliation reason in §5, not for any defect in the change itself.**

---

## 5. Room functionality regression assessment

### 5.1 Finding

**No room regression was found, and none is attributable to the Windows
working tree.** The reasoning is a chain of five verified observations:

1. `backend/common/locations.py` does not exist anywhere in this checkout — a
   recursive filename search over the whole tree returns nothing.
2. The token `room_payload` occurs zero times in the working tree **and** zero
   times in `HEAD` (`git grep room_payload HEAD` → no files).
3. `_rooms_for`, `_room_for_entry` and `room_source` occur zero times in
   `backend/`.
4. The working-tree diff of `main.py` deletes nothing (22 insertions, 0
   deletions), so it cannot have removed pre-existing code of any kind.
5. The W4 report that lives in this checkout describes the room feature as
   **missing**, not as present-and-working: *“`queue_entries` has no room
   column and no room in its response”*
   (`docs/implementation/QUE-006_W4_ROOM_SUPPORT_REPORT.md:14`).

So the premise "Windows removed room snapshot serialization from `main.py`"
cannot be reproduced against this repository. The premise that *is*
reproducible is: **Ubuntu carries uncommitted room work that `origin` does not
have.** The two checkouts are not "one correct, one regressed"; they are
"committed baseline + W2" versus "committed baseline + room work, uncommitted".

### 5.2 What this means for the frontend — a forward dependency, not a break

`frontend/pages/queue.js` (working tree, lines 76–80) already forwards room data
to the announcer:

```js
eventId: entry.call_event_id,
token: entry.token,
// Doctor name removed from announcements (QUE-006 doctor-name removal).
// No queue endpoint returns a room yet; omitted rather than invented.
room: entry.room,
```

The comment is an accurate admission by the W2 author: the field is passed
through, is `undefined` today, and is harmless because the announcement builder
omits an absent room. Once the Ubuntu backend publishes a room, an announcement
can name it **without any frontend change** — provided the published key is
`room` (or the page is adjusted to read `room_name` / `location_label`).
**That key-naming detail is unresolved and must be settled during
reconciliation** (§12, item 4).

### 5.3 The real reconciliation risk

`_entry_to_dict` is the function W2 edits. It is also the function any
room-serialization work must edit, because it is the single serializer for every
queue entry the API returns. The textual overlap is three lines wide but
semantically central: whichever version of `_entry_to_dict` lands last wins, and
a careless merge drops either the call-event keys or the room keys **silently** —
no test on either side would fail, because neither side's tests know about the
other's keys. The Ubuntu file additionally carries module-level helpers
(`room_payload`, `_rooms_for`, `_room_for_entry`, per the owner's description)
that the Windows file does not have at all, so a whole-file overwrite in either
direction destroys work.

That is why `main.py` is **HOLD** rather than INCLUDE: not because the change is
wrong, but because committing it establishes a canonical upstream file without
the room keys, and the next merge from the Ubuntu branch is exactly where the
room code would vanish without leaving a conflict marker.

### 5.4 What the W4 report says is still missing on the Windows side

Beyond `main.py`, the W4 gap on this checkout includes, at minimum: no room
column on `queue_entries`; no room in the queue response; and no
`common/locations.py`. Those are **Ubuntu-side deliverables**, and they are
therefore a **prerequisite of any "queue responses contain both room metadata
and call-event metadata" acceptance criterion** (§12). This report does not
attempt to design that work.

---

## 6. W2 dependency review (Phase D)

Read in full this session: `backend/queuing/events.py` (117 lines),
`backend/queuing/announcements.py` (316 lines),
`backend/alembic/versions/a7c3f19d2b64_…py` (95 lines), the
`QueueAnnouncementDelivery` block of `backend/common/models.py`, and the frontend
modules of §3.1. `backend/queuing/tests/test_queue.py` was inspected by test
name only — it is **not executable** here (§8).

### 6.1 Event identity

| Question | Answer | Evidence / status |
|---|---|---|
| How are call events identified? | `qce:<entry_id>:<index>`, where `<index>` is the position of the `{"action":"call","to":"called"}` record inside `status_history` | `events.py:78-80` — VERIFIED (read) |
| Does identity derive from persisted state? | Yes, exclusively from `QueueEntry.status_history`, which the `call` branch of `PATCH /api/v1/queue/{entry_id}` appends inside the same transaction as the status change | `events.py:1-37`; that code is untouched by the diff — VERIFIED (read) |
| Are repeated calls distinguished? | Yes — a legitimate recall appends a second record, so a different index and a different id | `test_recall_gets_a_new_event_id` — **executed, passed** |
| Is it stable across browser refreshes? | Yes — nothing in the derivation uses a browser clock, a local counter or the audit table; a reload re-reads the same row | `test_read_is_repeatable_for_same_history` — **executed, passed** |
| What if the history is missing? | Empty list → `current_call_event` returns `None` → `call_event_id=""`, `call_event_at=""`, `call_count=0`, no exception | `test_no_history_has_no_event` — **executed, passed** |
| What if the history is malformed? | Tolerated per element: non-list history, non-dict element, non-string `at`. Bad records are skipped, never raised | `test_malformed_history_is_tolerated`, `test_tuple_history_is_accepted` — **executed, passed** |
| What if the id would exceed the column? | `MAX_EVENT_ID_LENGTH = 120`; an over-long candidate yields `None` instead of a truncated id | `events.py:97-98` — VERIFIED (read); the guard itself is **not executed** (`pragma: no cover`) |
| Are ids unique across entries? | Yes — the entry id is part of the string | `test_ids_are_distinct_across_entries` — **executed, passed** |
| Can a duplicate HTTP call create a second event? | No — `called` is not a source status for `call`, so the route answers 422 before appending | `test_duplicate_call_request_creates_no_second_event` — **written, NOT executed** (needs route + DB) |
| A stale or invented id? | `is_current_call_event` compares against the entry's latest event; the claim endpoint answers 409 | `test_is_current_event_rejects_stale_and_invented_ids` — **executed, passed** |

**Limitation to record:** the identity is an **array index**, so it is only as
stable as the append-only guarantee on `status_history`. Any future compaction,
truncation or re-ordering of that column would silently shift every derived id.
No such operation exists today; it is a property to protect, not a defect.
Likewise, `call_count` counts calls *present in the history*, which equals
lifetime calls only while the history is never pruned.

### 6.2 Delivery claims

| Question | Answer | Evidence / status |
|---|---|---|
| Are duplicate claims prevented by a database constraint? | Yes — `call_event_id` is `UNIQUE` in the model (`unique=True`) and in the migration, which names it `queue_announcement_deliveries_call_event_id_key` — the name PostgreSQL would itself generate, so ORM expectations and DDL agree | model + migration read — VERIFIED (static); the constraint has **never been created on this host** |
| Are concurrent requests safe? | One statement: `INSERT … ON CONFLICT (call_event_id) DO NOTHING RETURNING id`. The loser gets no row and is answered `claimed: false, reason: "duplicate_event"`. No advisory lock, no read-then-write race | `_CLAIM_SQL` at `announcements.py:85-95`, used at 259–286 — VERIFIED (read), **not executed** |
| Is claim ownership enforced? | Yes — `requested_by = auth.user_id`, `requested_by_role = auth.role`; organisation and branch come from the **entry row**, never from the request body | `announcements.py:259-272` — VERIFIED (read) |
| Is organisation/branch scope enforced? | Yes — `_scoped_entry` filters on `auth.organization_id`, then `branch_accessible` (125), then `can_access_doctor` for doctor/assistant (127); all three answer **404**, non-disclosing | `announcements.py:115-131` — VERIFIED (read) |
| Are stale events rejected? | Yes, twice over: the entry must still be `called` (252) and the id must equal `current_call_event(...)` (255); otherwise 409 | `announcements.py:252-256` — VERIFIED (read) |
| Is the transaction atomic? | Yes — insert and the `queue.announcement.requested` audit row share one session and one commit; `rollback` on any exception; `close()` in `finally` | `announcements.py:247-316` — VERIFIED (read) |
| Does a claim touch the queue row? | No — it reads the entry and writes only its own table, in its own short transaction | same — VERIFIED (read) |

**Accepted limitation (recorded, not a blocker):** because the claim requires
the entry to still be `called`, a terminal slow enough to arrive after the entry
moved to `in_consultation` receives **409 and announces nothing**. That is the
intended trade-off — announcing a patient who has already entered the room is
worse than silence — but a late terminal therefore leaves **no persisted record
of the miss**: there is no `skipped_stale` outcome. Listed in §13 as a follow-up.

### 6.3 Delivery outcomes

| Question | Answer | Evidence / status |
|---|---|---|
| Are completed / interrupted / failed / duplicate distinguished? | Yes — `requested`, `completed`, `failed`, `blocked`, `interrupted`, `skipped_busy`, `skipped_duplicate`, with `SILENT_OUTCOMES = (blocked, skipped_busy, skipped_duplicate)` | `announcements.py:66-83` — VERIFIED (read) |
| Can a client report `requested`? | No — it is absent from `OUTCOMES`; only the claim sets it, so “asked for” can never be confused with “heard” | `announcements.py:75-83` — VERIFIED (read) |
| Does success mean completed playback rather than playback start? | Yes — `completed` is reported only after the **final** clip fires `ended`; a started-but-unfinished announcement resolves `interrupted` or `failed` | `announcements.py:32-34`; `frontend/lib/announcements/delivery.js:13-15` — VERIFIED (read) |
| Can a settled outcome be rewritten? | No — a different outcome is refused 409 (197); the identical outcome is idempotent (194) and adds no second audit row | `announcements.py:194-198` — VERIFIED (read) |
| Can a delivery failure affect queue status? | No — this module performs no queue write, and its errors occur after the queue call has already committed | VERIFIED (read); `test_announcement_failure_cannot_block_the_queue` is written but **NOT executed** |

### 6.4 Audit

| Question | Answer | Evidence / status |
|---|---|---|
| Are queue calls and announcement outcomes audited separately? | Yes — the queue call keeps its existing `queue.call` record (untouched by the diff); the announcement adds `queue.announcement.requested` (`announcements.py:290-301`) and `queue.announcement.<outcome>` (`announcements.py:200-219`) | VERIFIED (read) |
| Target of the delivery audit? | `target_type="queue_call_event"`, `target_id=<call_event_id>` — links the announcement to the call without duplicating the queue-entry record | VERIFIED (read) |
| Do audit rows carry unnecessary patient or clinical data? | **No.** The `after` payload is `status`, `queue_entry_id`, `language`, `voice_pack_id`, `voice_pack_version`, `transport`. No patient name, phone, doctor name or clinical field, and no token | VERIFIED (read) |
| Is the trail append-only? | Yes — no audit row is updated or deleted, and the delivery row is never deleted either; `record_audit` is the helper the rest of the service already uses | VERIFIED (read) |
| Are denials recorded? | **Yes, by the service-wide mechanism, not by this module.** `install_denial_audit(app, "queuing")` (`main.py:28`) is an ASGI middleware covering `DENIAL_STATUSES = {403, 404, 422}` (`common/denial_audit.py:59`), so a refused claim is audited even though `announcements.py` itself raises before writing a row | VERIFIED (read) |
| Which refusals are **not** audited? | `409` is deliberately outside `DENIAL_STATUSES`: a duplicate claim, a stale event and a settled outcome leave no audit row (the loser is told in its response). This is the existing service convention, not a W2 invention | VERIFIED (read); recorded in §13 |

### 6.5 Permissions

| Question | Answer | Evidence / status |
|---|---|---|
| Are existing capabilities enforced? | Yes — `ANNOUNCE_CAPABILITIES = ("queue.manage", "queue.consult")` (line 64) through `_require_announce` → `check_granted(cap, auth.role, granted)` (108–112) | VERIFIED (read) |
| Was a new permission introduced? | **No** — no new capability string, no new grant, no doctor-specific permission; `announcements.py` defines no capability of its own | VERIFIED (read); `test_claim_requires_no_new_permission` written, **NOT executed** |
| Is a doctor or assistant confined to their own queue? | Yes — `auth.can_access_doctor(entry.doctor_id)` on claim (127) and on outcome (191), mirroring `main.queue_action` (RBAC-R3) | VERIFIED (read) |
| Is organisation/branch isolation preserved? | Yes — foreign organisation, foreign branch and foreign doctor all answer 404 with identical wording | VERIFIED (read) |
| Is scope ever read from the request body? | No — scope comes from the stored entry / stored delivery row; only `event_id`, `language`, `voice_pack_id`, `voice_pack_version`, `transport`, `outcome` and `reason` are read from bodies | `announcements.py:142-160` — VERIFIED (read) |

### 6.6 Frontend delivery and announcement integration

| Module | Role | W2-only? | Status |
|---|---|---|---|
| `frontend/lib/announcements/delivery.js` (195 lines) | Protocol client: `DELIVERY_OUTCOME`/`OUTCOME_VALUES` mirroring the server, claim and report calls, silent skip on 404/409/422 | yes | 18/18 tests pass |
| `frontend/lib/announcements/call-announcer.js` (180 lines) | Claim → play → report; never throws; a lost claim stays silent | yes | covered by the W2 integration suite (19/19) |
| `frontend/lib/announcements/queue-transitions.js` | Pure `called`-transition detection (its header names W2) | yes | covered by the W2 integration suite |
| `frontend/lib/queue/queue-refresh.js` (142 lines) | 20 s refresher, hidden-tab suppression, coalescing, non-fatal errors, `stop()` on unmount | yes | 8/8 tests pass |
| `frontend/components/queue/QueueAnnouncements.js` | Surfaces delivery state (`announceElsewhere`, …) **and** W1 audio wiring | **no — mixed** | tests pass; commit class REVIEW (§3.8) |
| `frontend/pages/queue.js` | Wires announcer + refresher **and** the POD-12 call gate | **no — mixed** | 19/19 integration tests pass |

---

## 7. Migration compatibility assessment

### 7.1 What the migration declares

| Field | Value |
|---|---|
| `revision` | `a7c3f19d2b64` |
| `down_revision` | `f8a2b3c4d5e6` (single string) |
| `branch_labels` / `depends_on` | `None` / `None` |
| Creates | `queue_announcement_deliveries` (15 columns) + `idx_queue_announcement_entry` + `idx_queue_announcement_org_time` |
| Idempotent | Yes — `inspector.has_table()` and `get_indexes()` guards make a second run a no-op |
| Touches existing objects | No — no `alter_column`, no `drop`, no data migration |
| Downgrade | Drops the two indexes if present, then the table; guarded by `has_table` |

### 7.2 The chain — and the defect

Fifteen revision files exist. Parsing every `revision` / `down_revision` pair
gives this shape (⇒ = points at its parent):

```
5f3fce6757cf (base)
  ⇒ ccf34da72c1b ⇒ c7d3601e2486 ⇒ 9d8a1f2b3c4d ⇒ 3c8e5d0a9b2f ⇒ a1f2b3c4d5e6
      ⇒ b7c1e4d90a52 ⇒ d4b2c8e1f7a3 ⇒ e6c1a9b3d5f8
          ⇒ f7d2b4c6e8a1 ⇒ b3d7e91f6a24 ─┐
          ⇒ f8a1b2c3d4e5 ⇒ f8a2b3c4d5e6 ─┴⇒ a9c4e1f7b2d8   (merge, single head)
                                              ⇒ a7c3f19d2b64  ← NEW, WRONG PARENT
```

| Fact | Value | Status |
|---|---|---|
| Head **before** this change | `a9c4e1f7b2d8` — a merge revision with `down_revision = ('b3d7e91f6a24', 'f8a2b3c4d5e6')` | VERIFIED (file parsed; both parents tracked at `HEAD`) |
| Parent declared by the new migration | `f8a2b3c4d5e6` — an **ancestor** of the head, not the head | VERIFIED |
| Heads **after** this change | **two** — `a9c4e1f7b2d8` and `a7c3f19d2b64` | VERIFIED (DAG recomputed) |
| Consequence | `alembic upgrade head` no longer resolves: Alembic refuses when multiple heads exist and requires `heads`, a branch label, or a merge revision | VERIFIED by construction (Alembic semantics); not executed — `alembic` is not installed here |
| Does the W2 work depend on anything in `a9c4e1f7b2d8`? | No — that revision adds `slot_allocations`, `staff_capability_grants` and appointment-type changes, none of which the delivery table references | VERIFIED (read) |

**This is a genuine commit blocker introduced by W2, and it is not mentioned in
`QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md`.** The upgrade path on a fresh
database would work if a human typed the revision explicitly; the documented,
automatable path (`upgrade head`) would not.

### 7.3 Remedies (proposed, not applied)

| Option | Change | Consequence |
|---|---|---|
| **A (preferred)** | `down_revision = 'a9c4e1f7b2d8'` | Chain becomes linear again, single head, no data dependency violated, `upgrade head` works |
| B | Set `down_revision = ('f8a2b3c4d5e6',)` and add a merge revision on top | Two extra revisions for no benefit |
| C | Ship as-is and document `alembic upgrade a7c3f19d2b64` | Keeps the defect in the chain; every future migration inherits the ambiguity |

Option A is the only one that restores the single-head invariant. **It requires a
one-line edit to a file this task is forbidden to modify**, so it is a
recommendation for the owner.

**Ordering note for Ubuntu:** if the Ubuntu database has already been upgraded to
`a9c4e1f7b2d8`, a W2 migration parented on `f8a2b3c4d5e6` would be applied from a
position *ahead* of its own parent — Alembic's branch logic then treats it as a
sibling head. This is exactly the multi-head failure in production form, and it
is one more reason to reparent before the migration ever reaches a real database.

### 7.4 Model ↔ migration agreement

| Check | Result |
|---|---|
| Column count | 15 in the model, 15 in the migration — same set, same order |
| Types | `String`/`String(120)`/`String(8)`/`String(80)`/`String(20)`/`String(24)`/`Integer`/`DateTime(timezone=True)` all match |
| Nullability | `id`, `organization_id`, `queue_entry_id`, `call_event_id`, `language`, `voice_pack_id`, `voice_pack_version`, `transport`, `requested_by`, `requested_at`, `status`, `outcome_reason` NOT NULL in both; `branch_id`, `requested_by_role`, `outcome_at` nullable in both |
| Server defaults | `''` for the four string defaults, `'0'` for the version, `'requested'` for status — identical |
| Primary key | `id` in both |
| Foreign keys | `organizations.id`, `branches.id`, `queue_entries.id` — all present in both |
| Unique constraint | model `unique=True` on `call_event_id`; migration `UniqueConstraint('call_event_id', name='queue_announcement_deliveries_call_event_id_key')` — the same name PostgreSQL would generate, so a `create_all`-built database and an Alembic-built database agree |
| Indexes | `idx_queue_announcement_entry(queue_entry_id)`, `idx_queue_announcement_org_time(organization_id, requested_at)` in both; no redundant index on `call_event_id` (documented in the model) |
| `__service__` | `"queuing"` in the model; `alembic/env.py` imports `common.models` wholesale, so no per-service registry needs updating |

**Model ↔ migration verdict: VERIFIED (static).** The only artefact that could
contradict this is a live `\d queue_announcement_deliveries`, which no host here
can produce.

### 7.5 Unique-constraint semantics vs. intended dedupe

`ON CONFLICT (call_event_id)` needs a **unique index on that column alone** —
which the constraint provides. A composite constraint (`queue_entry_id,
call_event_id`) would *also* have allowed two terminals on the same event to both
insert only if their `queue_entry_id` differed, which is impossible for one
event, so the single-column constraint is the correct and minimal choice. It
also matches the precedent cited in the model docstring (`Notification.dedup_key`).

**Migration verdict overall: BLOCKED** — correct in content, incompatible in
parentage. Not committed until §7.3 option A is applied.

---

## 8. Test and build evidence (Phase E)

Every row below states *who* produced the result. Nothing in the "documented"
rows was re-run by this task, and nothing is claimed beyond what was observed.

### 8.1 Executed in this session

| Command | Result | Notes |
|---|---|---|
| `node --test tests/queue-*.test.mjs` (cwd `frontend`, 11 suites) | **146 tests, 145 pass, 0 fail, 1 skipped**, 0.42 s | Full output captured to `%TEMP%\pcr-queue.txt` and read back; nothing in the repository was written |
| `python scripts/que-006-w2-reliability/check_call_event_identity.py` | **13 tests, 13 pass, 0 fail**, exit 0 | This script runs **every** `test_*` in `backend/queuing/tests/test_queue_events.py` — the file contains exactly 13, so the backend identity suite ran in full through a plain interpreter |
| Working-tree integrity re-check after the runs | `git status --short -uall` → **164** entries, unchanged; no `.pyc` or `__pycache__` in status (`__pycache__/` is in `.gitignore` line 2) | Confirms the tests were non-destructive |

The single skip is environmental and pre-existing:
`frontend/tests/queue-announcements-boundary.test.mjs:31-32` skips
*“the queue page and the announcement panel compile as JSX”* when
`next/dist/build/swc` is unavailable in the install. It is not a W2 failure.

The eleven suites that ran: `queue-announcement-content`,
`queue-announcement-controller`, `queue-announcement-delivery`,
`queue-announcement-prerecorded`, `queue-announcement-segments`,
`queue-announcement-speech`, `queue-announcement-voice-packs`,
`queue-announcement-w2-integration`, `queue-announcements-boundary`,
`queue-call-control`, `queue-refresh-safety`.

### 8.2 Documented in an existing report, **not** re-run here

Source: `docs/implementation/QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md`.

| Claim in that report | Value | Re-verified this session? |
|---|---|---|
| `queue-announcement-delivery` | 18/18 | Yes — inside the 146-test run |
| `queue-refresh-safety` | 8/8 | Yes — inside the 146-test run |
| `queue-announcement-w2-integration` | 19/19 | Yes — inside the 146-test run |
| `queue-call-control` | 18/18 | Yes — inside the 146-test run |
| Whole tree `npm test` | 318 tests, 314 pass, 2 fail (`banglanamesense` checksum, `calendar-render` Windows ESM URL), 2 skip | **No** — not re-run |
| `npm run build` | exit 0, “Compiled successfully”, `/queue` 15.3 kB | **No** — not re-run |
| `check_call_event_identity.py` | 13/13 | Yes — re-run, 13/13 |
| `py_compile` of `announcements.py`, `events.py`, `main.py` | exit 0 | **No** — not re-run; `py_compile` writes `__pycache__`, so it was deliberately avoided this session. Syntax was instead confirmed by reading the files and by the successful import-free execution of `check_call_event_identity.py`, which imports `queuing.events` |

### 8.3 Not executed — and why

| Item | Status | Reason |
|---|---|---|
| `backend/queuing/tests/test_queue.py` (20 new tests, 18 of them W2) | **BLOCKED** | Import probe: `fastapi`, `pytest`, `sqlalchemy`, `psycopg2`, `alembic` are all **missing** from this interpreter; and no PostgreSQL instance exists here |
| `backend/queuing/tests/test_queue_events.py` **via pytest** | NOT APPLICABLE | pytest absent — but its 13 tests ran via the identity script (§8.1) |
| Migration upgrade / downgrade | **BLOCKED** | No `alembic`, no database, and applying migrations is forbidden by this task's constraints |
| `npm test` (whole tree) | NOT RUN | Non-destructive but unnecessary: the queue suites it would cover were already run directly |
| `npm run build` | NOT RUN | Writes `.next/`; the task forbids creating build artefacts, and the previous run's result is documented |
| Browser runtime observation | **NOT VERIFIED** | No server, no database, no browser session in this task |
| Two-terminal dedupe observation | **NOT VERIFIED** | Same reason — this is precisely the acceptance criterion that remains unproven (§13) |
| Any test against a production database | NOT APPLICABLE | Forbidden and unnecessary |

### 8.4 Summary of the evidence position

| Layer | Position |
|---|---|
| Frontend W2 code | **TESTED** — 145 passing assertions across 11 suites, including 45 that are W2-specific |
| Backend identity logic (`events.py`) | **TESTED** — 13/13, the module's complete test set |
| Backend routes, claims, audit, permissions | **IMPLEMENTED only** — read line by line; zero execution |
| Migration | **IMPLEMENTED only** — and statically **BLOCKED** by the head defect |
| Cross-terminal behaviour | **NOT VERIFIED** — neither terminal has ever spoken to the other |
| Persisted audit row | **NOT VERIFIED** — the table does not exist on this host |

---

## 9. Commit inclusion list (Recommendation A)

A dedicated W2 commit can safely contain **eleven files** — the W2 module layer
plus its tests — because none of them imports the mixed files of §11. The
committed tree would still build: `frontend/pages/queue.js` stays at its `HEAD`
version, which imports none of the new modules. Wiring the page is a *later*
commit that can then bring POD-12 in deliberately.

| # | Path | Why it belongs |
|---|---|---|
| 1 | `backend/queuing/events.py` | Identity derivation, pure, tested 13/13 |
| 2 | `backend/queuing/announcements.py` | Claim + outcome endpoints, no new permission |
| 3 | `backend/queuing/tests/test_queue_events.py` | The 13 executed tests |
| 4 | `backend/common/models.py` | **Only** the `QueueAnnouncementDelivery` block — the file has no other pending change (diff verified: +58, one hunk) |
| 5 | `frontend/lib/announcements/delivery.js` | Protocol client |
| 6 | `frontend/lib/announcements/call-announcer.js` | Claim → play → report |
| 7 | `frontend/lib/announcements/queue-transitions.js` | `called`-transition detection |
| 8 | `frontend/lib/queue/queue-refresh.js` | Non-destructive refresher |
| 9 | `frontend/tests/queue-announcement-delivery.test.mjs` | 18 tests |
| 10 | `frontend/tests/queue-refresh-safety.test.mjs` | 8 tests |
| 11 | `frontend/tests/queue-announcement-w2-integration.test.mjs` | 19 tests |

Optional twelfth, at the owner's discretion:
`scripts/que-006-w2-reliability/check_call_event_identity.py` — the harness that
made the backend identity suite runnable without pytest. It is tooling, so it is
not in the list above; it is harmless to include.

**Not included even though it is W2:** the migration
`backend/alembic/versions/a7c3f19d2b64_…py` — see §11. Committing the eleven
files without it leaves `announcements.py` unable to run against a real database,
which is acceptable *only* because the endpoints are not wired into any committed
page yet. If the owner prefers an atomic W2 commit, the migration's parent must
be fixed first (§7.3 A) and all twelve files go in together — **that is the
recommendation for the commit that actually ships W2.**

**Suggested message (atomic variant, 12 files):**

```
feat(queue): server-owned call-event identity and cross-terminal announcement claim (QUE-006 W2)

- qce:<entry>:<history index> derived from persisted status_history
- UNIQUE(call_event_id) claim via INSERT ... ON CONFLICT DO NOTHING
- requested/completed/failed/blocked/interrupted/skipped_* outcomes
- queue.announcement.* audit rows; no new capability
- alembic a7c3f19d2b64 reparented onto a9c4e1f7b2d8
```

**Before staging, re-run:** `node --test tests/queue-*.test.mjs` (expect
146/145/0/1) and `check_call_event_identity.py` (expect 13/13).

---

## 10. Exclusion list (Recommendation B)

Nothing below may be part of a W2 commit.

**QUE-006 W1 — prerecorded playback**

- `frontend/lib/announcements/prerecorded-audio.js`
- `frontend/lib/announcements/segments.js`
- `frontend/lib/announcements/controller.js`
- `frontend/tests/queue-announcement-prerecorded.test.mjs`
- `frontend/tests/queue-announcement-segments.test.mjs`
- `frontend/tests/queue-announcement-controller.test.mjs`

**QUE-006 POD-12 — call control**

- `frontend/lib/queue/queue-call.js`
- `frontend/tests/queue-call-control.test.mjs`

**QUE-006 W3 — voice configuration**

- `frontend/lib/announcements/voice-packs.js`
- `frontend/tests/queue-announcement-voice-packs.test.mjs`

**QUE-006 W5 — remote installation**

- `scripts/que-006-agent/agent.mjs`
- `scripts/que-006-agent/lib/installer.mjs`
- `scripts/que-006-agent/tests/installer.test.mjs`

**Audio catalogue, tooling and assets**

- all 39 untracked files under `scripts/que-006-audio/**` — including `.work/`,
  which holds tool state (`state.json`, `standardisation.json`, `validate.json`,
  `last-run.json`), a superseded draft and a master WAV, and **must not be
  committed under any message**
- `frontend/public/audio/**` — 72 binary files, 4.79 MB. `git ls-files
  frontend/public` returns **0**, so no audio has ever been versioned; committing
  it needs its own decision (size, licence, LFS policy)
- `frontend/lib/announcements/content.js` — doctor-name removal
- `frontend/tests/queue-announcement-content.test.mjs`
- `.gitignore` — the `.audio-originals-backup/` rule

**Documentation**

- `docs/governance/AMSDP_Docs_Index_V1.0.md`
- all 18 untracked `docs/implementation/QUE-006_*.md` files

Documentation is not a code dependency; bundling it makes the W2 commit
unreviewable and mixes five workstreams into one diff.

---

## 11. Hold list (Recommendation C)

| File | Why it is held | What unblocks it |
|---|---|---|
| `backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py` | `down_revision = 'f8a2b3c4d5e6'` is not the head; committing it creates **two heads** (§7.2) | One-line reparent to `a9c4e1f7b2d8`, then `alembic heads` must print exactly one revision |
| `backend/queuing/main.py` | Contains **no regression** (+22/−0) but is the file where room work and W2 collide (§5.3); committing it makes a room-less `_entry_to_dict` canonical | Agree the §12 order: land the Ubuntu room version first and re-apply the 22 W2 lines on top, **or** land W2 first and guarantee the Ubuntu room patch is rebased onto it |
| `frontend/pages/queue.js` | Imports `../lib/queue/queue-call` (**POD-12**) plus the W2 modules. Committing it alone breaks the build; committing it with `queue-call.js` pulls POD-12 in | Decide whether POD-12 ships with W2 (then add `queue-call.js` + its test) or split the page change |
| `frontend/components/queue/QueueAnnouncements.js` | Mixed: W2 delivery state **and** W1 prerecorded wiring in one file | Accept a deliberately mixed W2+W1 commit, or extract the W2 hunks first (an edit — out of scope here) |
| `frontend/lib/i18n.js` | Captions for W1, W2, W3 and POD-12 in 14 added lines | Same choice as above; `announceElsewhere` cannot be separated without editing |
| `backend/queuing/tests/test_queue.py` | 18 W2 tests + 2 POD-12 tests + 7 helpers, **unexecuted** on this host | Include with W2 only once the backend test environment exists; otherwise it ships as untested code |
| `docs/implementation/QUE-006_W2_QUEUE_INTEGRATION_REPORT.md`, `…_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md`, `…_W2_RELIABILITY_COMPLETION_REPORT.md`, `…_W1_PRERECORDED_PLAYBACK_ENGINE_REPORT.md`, `…_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | Four W2-era reports and two W1-era reports exist; “FINAL” claims a completeness §8 cannot confirm | Owner ruling on which document is current per workstream |

---

## 12. Ubuntu reconciliation plan (Phase G)

**Guiding rule: the Ubuntu file is the base; the Windows hunks are the patch.
Never overwrite in either direction.** The Windows file is the committed
baseline plus 22 lines; the Ubuntu file is the committed baseline plus the room
work (and possibly nothing of W2). Only the union is correct.

### 12.1 Proposed merged `main.py` — change summary (no file produced here)

| Step | Action on the Ubuntu file | Constraint |
|---|---|---|
| 1 | Keep the file as-is: room helpers, `room_payload` usage, `_rooms_for()`, `_room_for_entry()`, room resolution in listing/history/action responses | Nothing in the room code is touched, renamed or reordered |
| 2 | Add the two relative-import fallbacks for `events` and `announcements`, then `app.include_router(announcements_router)` **after** the last existing `include_router` call | Same pattern as `display` and `recovery`; `install_denial_audit(app, "queuing")` at line 28 must stay the first installer |
| 3 | At the top of `_entry_to_dict`, add `event = current_call_event(e.id, e.status_history)` | Pure read of `status_history`; no new query, no new column |
| 4 | In the returned dict, add `"call_event_id"`, `"call_event_at"`, `"call_count"` with the `(event or {})` defaults, **as siblings of the room keys**, never nested inside them | The page reads `entry.call_event_id` (`frontend/pages/queue.js:76`), so the key must stay top-level |
| 5 | Leave `"status_history": e.status_history or []` exactly as it is | Every derived id depends on that serialization verbatim |
| 6 | Leave listing, check-in, enqueue, `PATCH`, reorder, history, permissions, isolation, `queue.call` audit and notification hooks untouched | The Windows diff never touched them either |

The result is a `_entry_to_dict` that returns room metadata **and** call-event
metadata, in a module that carries both helper sets. **This is a plan, not a
patch:** no merged file was generated and `main.py` was not modified.

### 12.2 Additional files Ubuntu must receive

| Path | Notes |
|---|---|
| `backend/queuing/events.py` | Whole file; pure, no Ubuntu-specific coupling |
| `backend/queuing/announcements.py` | Whole file; imports `common.database`, `common.models`, `common.auth`, `common.permissions`, `common.audit` — all present on Ubuntu |
| `backend/common/models.py` | **Add the `QueueAnnouncementDelivery` class only.** Do not replace the file: Ubuntu's copy may carry its own additions |
| `backend/alembic/versions/<new revision>_add_queue_announcement_deliveries.py` | **Create it on Ubuntu** (`alembic revision -m "add queue announcement deliveries"`) so `down_revision` is Ubuntu's actual head; do not use the Windows copy blind (§12.3) |
| `backend/queuing/tests/test_queue_events.py` | 13 tests, runnable without pytest via the identity script |
| `backend/queuing/tests/test_queue.py` (W2 tests only) | 18 W2 tests + helpers; the 2 POD-12 tests belong to that workstream |
| `frontend/lib/announcements/delivery.js`, `call-announcer.js`, `queue-transitions.js` | Whole files |
| `frontend/lib/queue/queue-refresh.js` | Whole file |
| `frontend/tests/queue-announcement-delivery.test.mjs`, `queue-refresh-safety.test.mjs`, `queue-announcement-w2-integration.test.mjs` | 45 tests |
| `frontend/pages/queue.js`, `frontend/components/queue/QueueAnnouncements.js`, `frontend/lib/i18n.js` | **Hunks only** — merge into Ubuntu's versions, which may already carry room UI and prerecorded playback |
| `scripts/que-006-w2-reliability/check_call_event_identity.py` | Optional tooling; makes the identity suite runnable without pytest |

Windows needs nothing from Ubuntu except, eventually, the room work itself — and
if that lands on Windows, `backend/common/locations.py` must travel with it (the
Windows tree has no such module).

### 12.3 Dependency and migration ordering

1. **Determine Ubuntu's real head first:** run `alembic heads` on Ubuntu. If the
   room work added a revision, the head is *not* `a9c4e1f7b2d8`, and the W2
   migration must be parented on whatever Ubuntu reports.
2. **Fix the head invariant on Windows too** (§7.3 A: `down_revision =
   'a9c4e1f7b2d8'`) so the two lineages agree and a later merge does not produce
   a third head.
3. **Create the table before any claim can succeed.** `announcements.py` writes to
   `queue_announcement_deliveries`; without the migration every claim fails and
   the frontend silently skips — a failure that presents as “no audio”, not as a
   schema error.
4. **Frontend order:** `delivery.js` → `call-announcer.js` → `queue.js` wiring.
5. **Verification order:** (a) `alembic heads` prints one revision; (b)
   `alembic upgrade head` succeeds on a disposable database; (c) `queue.call`
   still appends exactly one history record; (d) a queue entry's response carries
   **both** room keys and `call_event_id`; (e) two browsers on one entry produce
   exactly one `requested` row and one audible announcement; (f) the row reaches
   `completed` only after the clip ends.

### 12.4 Acceptance gates still to be proven anywhere

| Gate | How it is proven | Status today |
|---|---|---|
| Identity survives a refresh | Reload a page showing a `called` entry; `call_event_id` unchanged | NOT VERIFIED |
| Second terminal is refused | Claim from terminal B returns `200 {claimed: false, reason: "duplicate_event"}` | NOT VERIFIED |
| Exactly one delivery row | `SELECT count(*) … WHERE call_event_id = …` → 1 | NOT VERIFIED |
| Outcome persisted | Row reaches `completed`, `outcome_at` set, `queue.announcement.completed` audited | NOT VERIFIED |
| Room metadata present | Queue response carries room keys alongside `call_event_id` | NOT VERIFIED — the room keys do not exist on this checkout at all |

---

## 13. Outstanding risks

| # | Risk | Severity | Evidence | Mitigation |
|---|---|---|---|---|
| 1 | **Second Alembic head.** Committing `a7c3f19d2b64` as written makes `alembic upgrade head` ambiguous on every deployment that uses the documented path | **High** — breaks automation | §7.2 | Reparent to `a9c4e1f7b2d8` (§7.3 A) |
| 2 | **Backend entirely unexecuted.** Claims, the dedupe constraint, audit rows, 403/404 scope and 409 paths are read, never run | **High** — W2's core promise is unproven | §8.3 | Provision fastapi/sqlalchemy/psycopg2/pytest + PostgreSQL; run `test_queue.py` |
| 3 | **Cross-terminal dedupe never observed.** No two-terminal session exists in any evidence | **High** — the headline acceptance criterion | §8.3, §12.4 | Two browsers, one entry, count the rows |
| 4 | **Room/W2 collision in `_entry_to_dict`.** A careless merge silently drops one side's keys; neither side's tests would fail | **High** | §5.3 | Merge on Ubuntu (§12.1) and assert both key sets in one response test |
| 5 | **Room key naming unresolved.** `queue.js` reads `entry.room`; Ubuntu may publish `room_name`/`location_label` | Medium | §5.2 | Settle the contract during reconciliation |
| 6 | **Mixed files cannot be split without editing** (`queue.js`, `QueueAnnouncements.js`, `i18n.js`, `test_queue.py`) | Medium | §3.8, §11 | Owner decides: bundle or extract |
| 7 | **Audio assets unversioned.** `git ls-files frontend/public` = 0, so a clone from `origin` has no clips and every announcement degrades to silence | Medium (W1-adjacent) | §3.6 | Separate decision on committing 4.79 MB of audio |
| 8 | **`scripts/que-006-audio/.work/` is not gitignored** and holds state JSON, a superseded draft and a master WAV — one `git add -A` publishes tool state | Medium | §3.6 (`check-ignore` output) | Add an ignore rule, or never use `git add -A` in this tree |
| 9 | **409 refusals are not audited.** A duplicate or stale claim leaves no row; only 403/404/422 are recorded service-wide | Low–Medium | §6.4 | Accept as convention, or add `skipped_stale` later |
| 10 | **Identity is index-based.** Any truncation or re-ordering of `status_history` would silently shift every id | Low (design property) | §6.1 | Keep the column append-only; assert it in a test |
| 11 | **164 entries in one working tree.** A single `git add -A` would commit five workstreams, 4.79 MB of audio and ~15.6 MB of script artefacts | High (process) | §3 | Stage by explicit pathspec only |
| 12 | **Report sprawl.** Four W2-era and two W1-era reports; the “FINAL” title claims a completeness the tree does not demonstrate | Low | §11 | Owner ruling on the current document |

---

## 14. Final recommendation

**Do not commit the working tree as it stands.** Three actions are required
first, in this order:

1. **Fix the migration parent** (§7.3 A) — one line. Without it, W2 cannot be
   deployed by the documented path, here or on Ubuntu.
2. **Decide the fate of the four mixed files** (`backend/queuing/main.py`,
   `frontend/pages/queue.js`, `frontend/components/queue/QueueAnnouncements.js`,
   `frontend/lib/i18n.js`) plus `backend/queuing/tests/test_queue.py`. Two
   coherent choices:
   * **Atomic W2 + POD-12 + W1** — accept a multi-workstream commit and say so in
     the message. Fastest, least honest about scope.
   * **Module-layer W2 now, wiring later** — commit the eleven files of §9, then
     land the page/panel/i18n changes together with POD-12. Slower; every commit
     is reviewable.
3. **Settle the Ubuntu direction** (§12) before `main.py` is committed anywhere,
   because whichever version lands first becomes the base the other must rebase
   onto.

**Never** stage with `git add -A` in this tree (risk 11), and **never** copy either
`main.py` over the other.

### 14.1 Status by deliverable

| Deliverable | Status | Basis |
|---|---|---|
| Server-owned event identity | **VERIFIED (logic) / PARTIALLY VERIFIED (integration)** | 13/13 executed; route publication read, not run |
| Cross-terminal dedupe | **NOT VERIFIED** | constraint read; never exercised |
| Persisted audit of outcomes | **NOT VERIFIED** | code read; table never created |
| Safe refresh | **TESTED** | 8/8 |
| Frontend claim/announce/report | **TESTED** | 45 W2 assertions |
| Migration | **BLOCKED** | wrong parent |
| Room support on Windows | **NOT APPLICABLE** — absent by design, never present | §4.3, §5.1 |
| Room regression caused by W2 | **NONE FOUND** — not possible; the diff is additive | §4.2, §5.1 |
| Repository ready for commit | **NO** | §14 items 1–3 |

### 14.2 What this task did **not** do

No source file, test, document, manifest, migration or audio asset was modified;
nothing was staged, committed, pushed, pulled, merged, rebased, cherry-picked,
reset, stashed, cleaned or deleted; no formatter or auto-fix was run; no migration
was applied or downgraded; no database schema was touched; no service was
started; no environment variable or credential was changed or read. The only
write is this report.

---

## Appendix A — Governance and skill compliance

| §4 domain row | Document applied | How it was followed |
|---|---|---|
| Documentation: reading project docs, writing reports, placement | `docs/governance/AMSDP_Docs_Index_V1.0.md` (read), §11/§12 output-location rules | Report written under `docs/implementation/`; destination collision checked (file did not exist); no existing document overwritten |
| Database schema, migrations, indexes | `saas-multitenant-data.md` §4–5 (adapted), Alembic chain, `backend/common/models.py` | Migration inspected statically against the full 15-revision DAG and against the model; **not applied** |
| Authentication, RBAC, permissions | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `common/permissions.py` | Claim capability set confirmed unchanged; no new permission introduced |
| Multi-tenant isolation | `saas-multitenant-data.md` (adapted), `common/auth.py` scope checks | Verified organisation/branch/doctor scoping answers 404 and never reads scope from a body |
| Backend API | `saas-application-security.md` (adapted) | Reviewed endpoints, atomicity, idempotency and the denial-audit middleware |
| Frontend UI | `saas-frontend-ux.md` (as adapted in the governance assessment) | Reviewed module seams only; no UI change proposed |

**Skills: none installed, none used.** There is no `.clinerules/skills/`,
`.claude/skills/` or repo `skills/` directory in this workspace, so the governance
documents above were the only governing material. No skill was claimed.

**Deviations recorded:**

1. **Documentation index not updated.** `.clinerules` §12 normally obliges an
   index revision for every new document; this task explicitly forbids modifying
   documentation, so `AMSDP_Docs_Index_V1.0.md` was **not** touched. Registering
   this report is an owed action for the owner once it is approved.
2. **`py_compile` and `npm run build` not re-run** (both write files —
   `__pycache__`, `.next/`), because the task forbids creating files. The previous
   run's results are quoted as *documented*, never as re-executed.
3. **The Ubuntu `main.py` was not available**, so the room comparison rests on the
   owner's description plus this repository's W4 report. Every such statement is
   labelled as documented evidence rather than a byte-level diff (§4.1, §5.1).

---

## Appendix B — Commands executed (all read-only)

```
git branch --show-current ; git status --short ; git status -sb ; git rev-parse HEAD
git log -5 --oneline --decorate ; git remote -v ; git branch -a ; git tag ; git stash list
git diff --stat ; git status --short -uall          (164 entries)
git diff -- backend/queuing/main.py ; git diff -- backend/common/models.py ; git diff -- .gitignore
git show HEAD:backend/queuing/main.py | Select-String '<room tokens>'
git grep room_payload HEAD ; git ls-files backend/alembic/versions ; git ls-files frontend/public
git check-ignore -v <5 paths> ; git cat-file -e HEAD:<2 migrations>
<15 revision files parsed for revision / down_revision>   → DAG and heads computed
python -c "import fastapi | pytest | sqlalchemy | psycopg2 | alembic"   → all MISSING
node --test tests/queue-*.test.mjs                                     → 146 / 145 pass / 0 fail / 1 skip
python scripts/que-006-w2-reliability/check_call_event_identity.py      → 13 / 13
```

No write command other than the creation of this report was executed.

---

*End of report.*
