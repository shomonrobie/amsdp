# QUE-006 W2 - Queue Announcement Integration (implementation and verification report)

**Assignment ID:** `AMSDP-QUE-006-W2-QUEUE-INTEGRATION`
**Report date:** 2026-11-21 (recovery and re-verification session)
**Work performed:** 2026-11-21, earlier session
**Depends on:** W1 prerecorded playback engine (IMPLEMENTED AND TESTED)
**Repository:** HEAD `37cf3d1` plus the uncommitted QUE-006 work described in section 2
**Status:** **PARTIALLY IMPLEMENTED.** The integration path exists, is reachable from the code and is
unit-tested, but the *automatic* trigger has **no user-facing control to fire it**: no page in the
product issues a queue `call`, so the approved event cannot occur through the UI. That gap is Product
Owner decision **POD-12 (QOP-001)**, and no button was invented.

---

## 0. Provenance of this report (read this first)

The Product Owner reported this document missing after an unexpected power loss, under the name
`QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md`.

| Fact | Evidence |
|---|---|
| The requested filename did **not** exist | `Get-ChildItem docs/implementation/QUE-006_*` before this task |
| An equivalent report **did** exist as `QUE-006_W2_QUEUE_INTEGRATION_REPORT.md` (9,159 B, written 2026-11-21 08:33) | file listing |
| The work **was** on disk and complete for what it claims: `queue-transitions.js`, controller changes, page seam, panel changes, 15 new tests | `git status` and the diff stat (`pages/queue.js` +38/-?, `QueueAnnouncements.js` +71, `controller.js` +120) |
| No interrupted-write artefacts existed | directory listing; consistent timestamps |

Nothing was lost except the exact filename. This report **supersedes** the earlier
`..._REPORT.md` for naming purposes; that file stays byte-unchanged on disk as the historical record
(`.clinerules` section 11).

**Everything below was re-derived in this session.** Where the earlier report's wording could be read
as stronger than the code supports, this report states the narrower fact (see WL-4, WL-5, WL-6).

---

## 1. Scope and deliverable

Per the master plan (section 4, row W2), W2 delivers:

> Prerecorded strategy in the controller; fire-and-forget announce on the `call` action and the
> operator button; no awaiting, no duplicate.

with `POD-12` explicitly named as the gate for a `call` **UI** control. The assignment's W2 also asks
for verification of: which event triggers, whether announcements are automatic, whether audio can
affect queue operations, completion vs start, duplicate handling and event identity, error and
interruption handling, and announcement audit records.

## 2. Files changed by W2

| File | Change | Verified in this session |
|---|---|---|
| `frontend/lib/announcements/controller.js` | Accepts `player` and an explicit `strategy`; prerecorded is the default when a player is supplied; `playPrerecorded()` maps engine outcomes; transport-aware capability; `activate()` primes instead of speaking; `cancel()` reaches the player; `refresh()`; state reports `transport`, `packId`, `packVersion`. | lines 50-61 (strategy), 82-96 (capability follows the pack), 180-202 (outcome mapping), 213-245 (activate), 260-304 (announce + dedupe), 372-376 (cancel) |
| `frontend/lib/announcements/queue-transitions.js` | **New**, 39 lines. Pure rule: which entries *just became* `called`. | whole file read; `before !== undefined` seeding semantics noted in WL-5 |
| `frontend/pages/queue.js` | `announceEntry` (operator, `source: 'operator'`, `userGesture: true`), `announceOnCall` (event, fire-and-forget), a transition effect over `entries`, and the panel mounted at line 218. | lines 52-56, 58-94, 113-122, 218, 236-239 |
| `frontend/components/queue/QueueAnnouncements.js` | Builds the player over the installed catalogue (`/audio/manifest.json`), resolves the pack through W3's precedence resolver, keeps the speech adapter as the documented alternative, and renders capability honestly. | lines 42-105 (hook), 155-202 (render) |
| `frontend/lib/i18n.js` | Three bilingual keys: `announceLastFailed`, `announcePackMissing`, `announcePackHint`. | lines 110-112 (bn), 222-224 (en) |
| `frontend/tests/queue-announcement-w2-integration.test.mjs` | **New**, 15 tests. | test-name list extracted; all pass |

No queue endpoint, schema, permission, audit rule or wording was changed by W2.

## 3. What actually triggers an announcement

This is the part where a report can easily overstate reality, so the chain is stated explicitly. An
automatic announcement requires **four** links, and only three of them exist:

| # | Link | State |
|---|---|---|
| A | The queue entry transitions `waiting -> called` **on the server**. | **IMPLEMENTED server-side.** `PATCH /api/v1/queue/{entry_id}` with `action: "call"` is allowed from `waiting` (`backend/queuing/main.py:381`), gated on `queue.manage` (`main.py:401-402`), audited as `queue.call` (`main.py:442-447`). |
| B | A UI control issues that `call`. | **ABSENT.** Searched the whole `frontend/` tree: the only occurrence of the string `'call'` as an action is the payload inside the W2 seam itself (`pages/queue.js:87`). The row controls are `start_consultation` (L233), `complete_consultation` (L234), `cancel` (L235), `announce` (L236-239), missed-turn (L240-243) and recover (L244-247). **POD-12 / QOP-001 open.** |
| C | A client observes the transition and calls `announceOnCall`. | **IMPLEMENTED.** `trackCalledTransitions()` (pure, 39 lines) plus the effect at `pages/queue.js:113-122`. |
| D | The page is unlocked, so the browser will actually make sound. | **IMPLEMENTED but operator-dependent.** The panel's *Enable audio* button primes with the catalogue's 300 ms silent clip (`controller.js:213-231`). Without that gesture the first attempt resolves `failed('blocked')` and is **not** retried until a fresh gesture (`controller.js:287-290`). |

Because link B is missing, **the automatic path cannot be exercised through the product UI today**.
What *is* reachable through the UI is the **operator** announcement: the `announce` button on a row
whose status is already `called` (`pages/queue.js:236-239`), which calls `announceEntry()` with
`source: 'operator'` and `userGesture: true`. That button can only be used after someone has moved an
entry into `called` by some other route (an API call, or another client).

### 3.1 Two further constraints found by reading the page (not stated in the earlier report)

| # | Finding | Consequence |
|---|---|---|
| WL-5 | **There is no polling on the queue page.** `pages/queue.js` contains no `setInterval` and no `setTimeout`; `loadQueue()` runs on mount, on a `doctor`/`date` change (L111) and after a local action. | A `call` issued **on another terminal** is announced on this terminal **only when this page reloads its queue**. Even after POD-12 lands, "automatic" means "observed at the next queue refresh", not "instant". |
| WL-6 | The transition rule seeds itself on first observation: `if (before !== undefined && ...)` (`queue-transitions.js:33`). | An entry that is **new** in a refresh and already `called` (created and called between two refreshes, or called by another operator) is **never announced**. This is deliberate - it prevents announcing the whole existing queue on page load - but it also means "called elsewhere, then noticed here" is silent. |

Both are honest design consequences, not bugs in the code as written. They are recorded because a
reader must not expect behaviour the code does not have.

## 4. Requirement-by-requirement status

| Assignment requirement (W2) | Status | Evidence / limitation |
|---|---|---|
| Announcement occurs automatically on the approved queue-call event | **PARTIALLY IMPLEMENTED (BLOCKED on POD-12)** | Wiring exists and is tested (`trackCalledTransitions` + effect at `pages/queue.js:113-122`). The event itself is unreachable in the UI (section 3, link B). Not a seam misdescribed as an integration: the seam is real, the trigger is missing. |
| Receptionist and doctor workflows can trigger queue calls as authorised | **BLOCKED (POD-12)** | Server permission already exists: `call` requires `queue.manage` (`main.py:401-402`), which `receptionist` holds; `doctor` reaches `call` only where granted `queue.manage`. No UI control exists to use it. |
| Playback does not block the queue transaction | **IMPLEMENTED + TESTED** | `announceOnCall` is never awaited; the static test strips comments and fails on any `await` in the seam; `doAction` (`pages/queue.js:124-129`) contains no audio reference; the server commits and audits **before** any client announcement (`main.py:442-448`). |
| Audio failure cannot reverse or block a successful queue call | **IMPLEMENTED + TESTED** | Every engine outcome is converted to a status object (`controller.js:180-202`); `play()` never rejects (`prerecorded-audio.js:243-284`); `announce()` never rejects. The queue response is already sent before audio is attempted. |
| Duplicate events do not produce duplicate announcements | **IMPLEMENTED + TESTED, per client only** | Two guards: the transition tracker (an unchanged `called` is not an event) and the controller's event key + 5 s window (`controller.js:277-285`). **Not** cross-client: see WL-4. |
| Stable event identity | **PARTIALLY IMPLEMENTED** | `announcementEventKey()` yields `event:<id>` when given, else `entry:<entryId>:<action>:<revision>` (`content.js:153-165`). The page passes `queueEntryId` and `action: 'call'` but **no `revision`**, so the key is `entry:<id>:call:0` for every call of that entry. Recalls of the same entry therefore share one key; only the 5 s window separates them. Roadmap section 8.3 AC-2 wants a server-supplied id and cross-page suppression - not implemented (POD-8 territory, not invented). |
| Playback completion distinguished from playback start | **IMPLEMENTED + TESTED** | `completed -> spoken` happens only from the engine's final-clip `ended` (`controller.js:190-192`), proven end-to-end by test 11. Nothing maps a resolved promise to success. |
| Error and interruption handling | **IMPLEMENTED + TESTED** | Outcomes surfaced in the panel (`announceLastFailed`, i18n L110/L222); `blocked` sets activation state and suppresses retries until a gesture; `busy`/`cancelled` pass through unchanged. |
| Announcement audit records | **NOT IMPLEMENTED** | Zero occurrences of `announcement` in any `backend/**/*.py` file (mechanical count this session: **0**). The queue **action** is audited (`queue.call`), but nothing records that an announcement was played or failed. This is roadmap section 8.3 AC-3 and POD-4; nothing was added. |
| No patient or doctor identity announced | **IMPLEMENTED + TESTED** | The seam passes `token` and `room` only; `buildAnnouncement()` reads nothing else; `content.js` has no doctor slot (doctor-name-removal report). |
| Actual tests and browser evidence | **TESTED only** | 15 W2 tests pass (section 5). **No browser run** (section 6). |

## 5. Test evidence - exact commands and results (run in this session)

```
cd e:\amsdp\frontend
node --version
  -> v24.12.0

node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test ^
  tests/queue-announcement-content.test.mjs tests/queue-announcement-controller.test.mjs ^
  tests/queue-announcement-speech.test.mjs tests/queue-announcement-segments.test.mjs ^
  tests/queue-announcement-prerecorded.test.mjs tests/queue-announcement-voice-packs.test.mjs ^
  tests/queue-announcement-w2-integration.test.mjs tests/queue-announcements-boundary.test.mjs
```

Result: **98 tests, 97 pass, 0 fail, 1 skipped**, exit 0. The single skip is the JSX compile check
(`queue-announcements-boundary.test.mjs:31`, `next/dist/build/swc unavailable in this install`).

Adding the agent suite (`scripts/que-006-agent/tests/installer.test.mjs`, 10/10) gives the programme
figure **108 tests, 107 pass, 0 fail, 1 skipped**.

The 15 W2 tests, as declared in `queue-announcement-w2-integration.test.mjs`:

1. prerecorded is the default transport when a player is supplied
2. a playback failure is reported, never thrown, never spoken
3. busy and cancelled are passed through unchanged
4. a blocked browser is not hammered without a fresh gesture
5. `activate()` unlocks by priming the pack, not by speaking
6. `activate()` with no silent clip grants nothing
7. an explicit speech strategy keeps the browser mechanism
8. asking for prerecorded without a player is refused
9. capability follows the pack, not the browser voice list
10. `cancel()` reaches the player
11. end to end: `spoken` is reported only when the final clip ends
12. only a transition into `called` is announced
13. transitions survive entries leaving and returning to the list
14. the transition rule tolerates junk
15. the queue page wires the call seam and never awaits it

Test 15 is the static assertion that satisfies "playback does not block the queue": it reads
`pages/queue.js`, strips comments, and fails if the seam contains an `await`.

### 5.1 Regression population

The four pre-existing announcement suites still pass unchanged: **53 tests, 52 pass, 0 fail,
1 skipped** (same skip as above). The full `frontend/tests` population is **270 tests, 266 pass,
2 fail, 2 skipped**; the two failures are pre-existing and unrelated
(`banglanamesense-dataset.test.mjs` pinned checksum; `calendar-render.test.mjs` Windows `E:` ESM URL),
in files this programme has never touched. Full detail is in the W1 report, section 4.

## 6. Browser / runtime verification evidence

**None. Explicitly absent.** No browser was opened against `/queue`, no announcement was triggered
through the panel, no audio was heard, and no autoplay refusal was observed. The W2 claims rest on:

- the code paths cited by file:line above;
- 15 unit tests driving a fake `Audio` element;
- one static test that reads `pages/queue.js` as text.

The boundary suite's JSX compile check **skipped** (`frontend/node_modules` absent, no
`next/dist/build/swc`), so the W2 edits to `pages/queue.js` and `QueueAnnouncements.js` are
**not compiler-verified**. Before the page may be called deployable, `npm install && npm run build`
must run in `frontend/` and the result recorded. That has not happened.

## 7. Known limitations and unresolved dependencies

| # | Limitation | Owner / next step |
|---|---|---|
| WL-1 | **No `call` control exists anywhere in the UI**, so the automatic trigger cannot fire through the product. | POD-12. Wiring is ready; the button is a separate, cheap change (no schema change). |
| WL-2 | Automatic announcements need an **unlocked page**. The first attempt on a fresh page resolves `failed('blocked')` and is not retried without a gesture. No silent-autoplay trick was added. | Operator enables audio once per page (panel button). |
| WL-3 | **No server-side announcement record.** The queue action is audited; the announcement is not. | POD-4 / roadmap 8.3 AC-3. |
| WL-4 | **Cross-client duplicates are possible.** Dedupe state is per browser tab (tracker + 5 s window). Two open `/queue` pages for the same doctor will each announce the same call. Roadmap 8.3 AC-2's server-supplied event id is not implemented. | Not invented; needs a server event identity (POD-8). |
| WL-5 | **No polling**: a call made on another terminal is only announced here after this page reloads its queue. | Design consequence of the current page; needs a refresh strategy decision. |
| WL-6 | An entry that is **new and already `called`** on a refresh is never announced (seeder semantics). | Design consequence; changing it would risk announcing the whole queue on load. |
| WL-7 | Announcement **language comes from the operator's interface locale** (`QueueAnnouncements.js:49`), not from facility configuration. | W3's server half (blocked: no `pytest`/`fastapi`/`sqlalchemy` on this host). |
| WL-8 | No room is passed (`entry.room` is always `undefined`; `queue_entries` has no room column), so only the no-room sentence can occur. | POD-2 (W4). |

## 8. Deviations from the master assignment

| # | Deviation | Reason |
|---|---|---|
| DEV-1 | Report filename: the assignment's `..._IMPLEMENTATION_REPORT.md` vs the master plan's `QUE-006_W<n>_<NAME>_REPORT.md` convention used by the earlier session. | One file cannot satisfy both. This report adopts the assignment's name; the earlier file is preserved unchanged. |
| DEV-2 | The automatic trigger was **not** made reachable by adding a `call` button. | The assignment forbids inventing the POD-12 decision; the button is explicitly QUE-001 work under owner control. |
| DEV-3 | No announcement audit event was written when audio completes. | Doing so would invent POD-4's payload and linkage, and requires a backend host. Recorded as WL-3. |

## 9. Repository state and preservation statement

- HEAD `37cf3d1`; **no commit, push, deploy, reset, clean, stash or revert** performed.
- Pre-existing modifications (9 tracked files) and untracked work (26 entries) were preserved exactly;
  W2's files were read, not rewritten, in this session.
- The only files created by this task are this report, the W1 report and the index revision.
- No queue endpoint, schema, permission, audit rule, audio asset or wording was changed.

## 10. Conclusion

**W2 is PARTIALLY IMPLEMENTED and must not be described as a completed automatic integration.**

- The client half is implemented and tested: a `waiting -> called` transition is detected once, the
  announcement is fire-and-forget, failure cannot reach the queue, and completion is distinguished
  from start.
- The trigger is **unreachable in the product** because no control issues a queue `call` (POD-12).
- Event identity is per-client (`entry:<id>:call:0`), so cross-page duplication and recall
  distinction remain open (WL-4).
- There is **no announcement audit record** (WL-3) and **no browser evidence** of any of it.

The cheapest next demonstrable step is a `call` button gated on the existing server permission
`queue.manage`. It needs no schema change and makes `announceOnCall` reachable - but only after the
Product Owner decides POD-12.

---

## 11. Governance and skill compliance (`.clinerules` section 6)

- **Domains routed (section 4):** frontend UI/components and pages (`saas-frontend-ux.md` as adapted);
  queue/workflow transitions (Business Rules Parts V-VII); audit expectations (Part X) reviewed for
  WL-3 and deliberately not implemented.
- **Documents read this session:** the docs index, `QUE-006_MASTER_IMPLEMENTATION_PLAN.md` (W2 row and
  DR-3/DR-4/DR-5), roadmap sections 8.1 and 8.3, the earlier W2 report, and the code cited above.
  **Numbering discrepancy, recorded:** the roadmap's section 8.2 ("facility announcement
  configuration") and 8.3 ("non-blocking queue/audio integration") are **not** the assignment's W2 and
  W3. The assignment's W2 maps to roadmap 8.3's client-side requirements, of which AC-2 (server event
  identity) and AC-3 (server-side announcement audit) are unimplemented here and stated as such.
- **Skills:** none installed (section 5) - **none claimed**.
- **Non-negotiables honoured (section 3):** the UI is not treated as the authorisation boundary (the
  `call` permission stays server-side, and no grant was moved into the client); no secret logged; no
  patient or doctor identity in the payload; no audit trail rewritten or fabricated.
- **Evidence standard (section 7):** TESTED is claimed only where the named test passes in this tree;
  browser behaviour is explicitly unclaimed.
- **Report location (section 11):** `docs/implementation/`. No migration, so no manifest entry.
- **Index:** registered as Revision 46 of `docs/governance/AMSDP_Docs_Index_V1.0.md`.
