# QUE-006 / W2 — Queue Announcement Reliability: Completion Report

**Task:** `AMSDP-QUE-006-W2-RELIABILITY`
**Date:** 2026-11-21
**Scope:** make the W2 queue-call announcement reliable end to end — server-owned
event identity, cross-terminal deduplication, a persisted delivery record, and a
queue refresh that cannot silently lose the list. **No queue state machine, no
permission, no template and no audio asset was changed.**
**Verdict:** **PARTIALLY IMPLEMENTED — COMPLETE ON THE FRONTEND, UNEXECUTED ON THE BACKEND.**
The whole frontend suite runs and passes for everything this task touched; the
two backend endpoints and the migration **could not be executed on this host**
(no `fastapi`, `pytest`, `sqlalchemy`, `psycopg2`, no PostgreSQL — see §7). No
browser, no audio device and no second terminal were available, so
cross-terminal deduplication is proven at the contract level only.

> **Honesty statement.** Every count in §6 came from a command run in this
> session; nothing is recalled from an earlier report. Every claim the
> implementation does *not* support is listed in §7 rather than blurred into the
> verdict.

---

## 1. What was wrong before this task

The earlier W2 report (`QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md`)
named five defects and left them open. This task addresses exactly those five:

| # | Defect (as recorded earlier) | Resolution in this task |
|---|---|---|
| 1 | Dedupe was **per browser tab** — two terminals both spoke | The server owns the delivery slot: `queue_announcement_deliveries.call_event_id` is `UNIQUE` and the claim is `INSERT … ON CONFLICT DO NOTHING RETURNING` (§3) |
| 2 | Event identity `entry:<id>:call:0` was **invented by the client** | Identity is derived on the server from the append-only `status_history`: `qce:<entry_id>:<index>` (§3.1) |
| 3 | An entry that arrived already `called` was never announced | The seam announces any *current* call event the terminal has not yet claimed, including one present at load (§4.2) |
| 4 | **No announcement audit record existed** (POD-4) | Three separate facts are audited: `queue.call`, `queue.announcement.requested`, `queue.announcement.<outcome>` (§3.4) |
| 5 | The queue page had **no refresh**, so a terminal could not see a call | A 20 s visible-tab refresher with focus / visibility / online triggers and a quiet path that cannot blank the list (§4.4, §5) |

---

## 2. The design decision that everything else follows from

Three facts are deliberately **separated**, because collapsing any two of them
produces a lie in the audit trail:

| Fact | Who may assert it | What it means |
|---|---|---|
| `queue.call` committed | the server, when the `call` action commits | a token was called — **not** that anything was heard |
| delivery `requested` | the server, when it grants the claim | this terminal won the slot and may speak |
| delivery `completed` | the terminal that holds the claim, after the final clip reported `ended` | the room actually heard it |

A client therefore **cannot** report `requested`: it is created by the claim
(`announcements.py`, claim handler) and never accepted from a request body. A
started-but-unconfirmed announcement resolves `failed`, never `completed`
(`delivery.js` `DELIVERY_OUTCOME`, `outcomeRequest`).

---

## 3. Server side

### 3.1 Identity — `backend/queuing/events.py` (new)

`current_call_event(entry)` walks `status_history` and returns the *n*-th
`→ called` transition as `qce:<entry_id>:<n>` (0-based). The rules it enforces:

* **No history, no event.** An entry without a `called` transition has no id, so
  the browser has nothing to announce.
* **Append-only derivation.** Re-reading the same history yields the same id
  (`test_read_is_repeatable_for_same_history`), which is what makes a repeated
  observation of the same call one event rather than two.
* **A recall is a new event.** A second `→ called` produces a higher index
  (`test_recall_gets_a_new_event_id`), so recalling a token speaks again, while
  a duplicated poll of the first call does not.
* **Staleness is server-decidable.** `is_current_event(entry, event_id)` rejects
  an id that is not the newest transition, which is how the claim answers **409**
  for a stale event instead of trusting the client's clock.
* Malformed history, tuple-shaped history and non-`call` records are tolerated
  rather than raising — a broken audit row must not take the queue down.

### 3.2 The delivery record — `QueueAnnouncementDelivery` + migration `a7c3f19d2b64`

`backend/common/models.py` gains one table; the migration
`add_queue_announcement_deliveries` (`revision = 'a7c3f19d2b64'`,
`down_revision = 'f8a2b3c4d5e6'`) creates it **forward-only and idempotently** —
it inspects the binder first and is a no-op against a database that already has
the table and indexes (§3 non-negotiable: every schema change ships as an
idempotent Alembic migration).

| Column | Why it exists |
|---|---|
| `call_event_id` (`UNIQUE`) | the dedupe key — one row per call event, ever |
| `delivery_id` | what the terminal quotes back when it reports an outcome |
| `queue_entry_id`, `organization_id`, `branch_id` | scope, derived from the entry, never from the body |
| `status` | `requested` → exactly one of the terminal outcomes |
| `voice_pack_id`, `voice_pack_version`, `transport` | answers "which recording announced this" without storing any patient or doctor data |
| `reason`, timestamps | why it settled as it did, and when |

No patient name, phone number, token text or doctor name is stored — identifiers
only. Indexes: `idx_queue_announcement_entry` and `idx_queue_announcement_org_time`.

### 3.3 The two endpoints — `backend/queuing/announcements.py` (new)

`POST /api/v1/queue/{entry_id}/announcement` — claim.
`POST /api/v1/queue/announcements/{delivery_id}/outcome` — report.

| Property | Implementation |
|---|---|
| Atomic dedupe | `INSERT … ON CONFLICT (call_event_id) DO NOTHING RETURNING` — the first terminal wins, everyone else reads the existing row and is told `claimed: false, reason: "duplicate_event"` (200, not an error) |
| Authority | no capability invented: `check_granted` on the two capabilities that already make the panel reachable — `queue.manage` or `queue.consult` |
| Tenant / branch scope | the queue service's existing rule is reused; a foreign or out-of-branch entry answers **404**, never 403 |
| Doctor scope | a doctor or assistant may only claim their own assigned doctor's queue (RBAC-R3), also **404** non-disclosing |
| Stale / wrong-state claims | **409** — "queue entry is not currently called", "announcement event is not the current call", "announcement already resolved as X" |
| Unknown outcome | **422** — the outcome set is closed |
| Isolation | claim and outcome are each their own short transaction; a failure here can never reverse a queue call (V-11) |
| Audit | `record_audit` appends; nothing is deleted or rewritten |

### 3.4 Audit shape (POD-4)

`queue.announcement.requested` is written when the claim is granted, and exactly
one of `queue.announcement.completed` / `.interrupted` / `.failed` /
`.skipped_duplicate` when the terminal reports. The test class
`TestAnnouncementAudit` asserts the two things that matter and would otherwise be
easy to fake: a successful `call` is **not** an announcement, and `requested` is
**not** `completed`. The claim writes no "heard" claim at all.



---

## 4. Frontend

Four modules, each pure enough to test without a browser, plus the page and the
panel that use them.

### 4.1 `lib/announcements/delivery.js` (new) — the decisions, no side effects

`eventIdOf`, `claimRequest`, `outcomeRequest`, `deliveryPath`, `outcomePath`,
`isFreshCallEvent`, `classifyAnnouncement`, and the frozen `DELIVERY_OUTCOME` /
`OUTCOME_VALUES` sets. Nothing here fetches or plays; the file states that in its
own header. `DEFAULT_MAX_EVENT_AGE_MS = 120000` bounds an **automatic**
announcement only: a tab returning from sleep must not read out a call from ten
minutes ago as if it were new. The operator's own "Announce" press is *not*
bounded — a deliberate repeat is a decision, not a notification.

### 4.2 `lib/announcements/call-announcer.js` (new) — claim before play

`createCallAnnouncer({ announce, describe, post, maxEventAgeMs })` returns
`announceCall(entry, opts)`. Order is fixed and is asserted by test:

**claim → play → report.** The claim is made first because the slot is the only
thing that makes a second terminal silent; reporting happens last, because the
outcome is only knowable after the clip ended.

* It **never throws.** Every path returns `{ status, reason, eventId }`; the
  queue page therefore cannot be broken by an audio or network failure.
* **404 / 409 / 422** from the claim are a *silent skip*, not an error surface:
  they mean "this terminal may not announce this event", which the operator
  cannot fix. `skip()` returns `claim_rejected` (or the server's own
  `duplicate_event`).
* **Local dedupe is now only for automatic announcements**
  (`duplicate_local`); the operator's deliberate repeat is claimed and reported
  like any other announcement, so the audit shows a human decision rather than a
  suppressed click.
* `disabled` (panel switched off) and `not_wired` (no announce/post function)
  are distinct reasons, checked after the event-id guard so a missing id is
  reported as `no_event_id`.
* `stale_event` uses the shared age bound; `announce_threw` / `report_failed` /
  `claim_failed` are the three genuine failures, all swallowed at the boundary.

### 4.3 The panel — `components/queue/QueueAnnouncements.js`

The panel accepts `delivery` and renders `deliveryNote(delivery)`: for
`duplicate_event`, `not_owner` or `claim_rejected` it shows one muted sentence —
`announceElsewhere`, translated in both languages (`i18n.js` line 112 Bangla,
line 226 English) — and nothing at all otherwise. It is deliberately **muted,
never an error**: the three reasons all mean "someone else is handling this
call", which is the system working. A stale or already-seen event says nothing.

### 4.4 The page — `pages/queue.js`

| Wiring | Line | Effect |
|---|---|---|
| `createCallAnnouncer({ … })` | 98 | one announcer per page |
| `announceCall(entry, { source: 'event' }).then(setDelivery)` | 126 | the call transition claims, plays, reports, and hands the result to the panel |
| `{ source: 'operator', userGesture: true }` | 82 | the operator's press is marked deliberate |
| `<QueueAnnouncements … delivery={delivery} />` | 307 | the outcome reaches the operator |
| `createQueueRefresher({ refresh: () => loadQueueRef.current({ quiet: true }) })` | 164 | background refresh |
| `const quiet = opts.quiet === true` | 133 | a background refresh never raises the spinner and does not blank the board |

---

## 5. Refresh design and its trade-offs (Phase 5)

`lib/queue/queue-refresh.js`: `createQueueRefresher({ intervalMs, document,
window, refresh, onError })`, default `DEFAULT_REFRESH_INTERVAL_MS = 20000`,
interval disabled when `intervalMs` is 0, and `isStarted()` exposed for tests and
for the page's cleanup.

| Decision | Why | Cost accepted |
|---|---|---|
| **20 s poll, not SSE / WebSocket** | the queue endpoint already exists and is cheap; a push channel would need infrastructure this milestone does not have | a call can be up to 20 s late on an idle terminal. The focus trigger cuts this to ~0 s for the terminal the receptionist is actually looking at |
| **No refresh while the tab is hidden** | polling a hidden tab wakes a laptop for nothing and cannot be heard anyway | a terminal left in a background tab learns of calls only when focused |
| **Coalesced** | interval, `focus`, `visibilitychange` and `online` can fire together; the second request waits for the first | a trigger can be served by a request that started ~1 s earlier |
| **Errors are non-fatal** | one failed refresh must not blank a working board | a persistent failure shows one banner and keeps retrying every 20 s; it is not escalated |
| **Quiet path** | a refresh must not flash the spinner every 20 s, and must not clear the list it failed to reload | the page's error banner is left to the explicit load path |
| **Stopped on unmount** | no timer or listener outlives the page | none — `stop()` clears the interval and all three listeners |

---

## 6. Verification actually performed (this session)

All commands were run on this host; the figures below are the output of those
runs, not restatements of an earlier report.

| # | Command | Result |
|---|---|---|
| 1 | `node --test tests/queue-announcement-delivery.test.mjs` | **18 tests, 18 pass, 0 fail** |
| 2 | `node --test tests/queue-refresh-safety.test.mjs` | **8 tests, 8 pass, 0 fail** |
| 3 | `node --test tests/queue-announcement-w2-integration.test.mjs` | **19 tests, 19 pass, 0 fail** (15 pre-existing + 4 added here) |
| 4 | `node --test tests/queue-call-control.test.mjs` | **18 tests, 18 pass, 0 fail** |
| 5 | eight-file batch (the four above + controller, content, boundary, calendar-integration) | **91 tests, 90 pass, 0 fail, 1 skipped** — the skip is `the queue page and the announcement panel compile as JSX`: *"next/dist/build/swc unavailable in this install"* (pre-existing, unrelated to the changes: the build in #8 is the compiler evidence) |
| 6 | `node --test tests/queue-*.test.mjs` | **146 tests, 145 pass, 0 fail, 1 skipped** (was **116** before this task: +18 delivery, +8 refresh, +4 integration = 30) |
| 7 | `npm test` (whole tree) | **318 tests, 314 pass, 2 fail, 2 skipped** (was **288**; +30 = the same 30). The 2 failures are the **pre-existing, unrelated** ones: `dataset bytes match the hash recorded in DATASET_SOURCE` (Bangla name-sense dataset checksum) and `tests\calendar-render.test.mjs` (Windows `E:` ESM URL) |
| 8 | `npm run build` | **exit 0 — "Compiled successfully"**, `/queue` **15.3 kB** / 134 kB first load (was 13.4 kB before these modules) |
| 9 | `python scripts\que-006-w2-reliability\check_call_event_identity.py` | **13 tests, 13 pass, 0 fail** (exit 0) — the pure identity suite executed *for real*, not imported |
| 10 | `python -m py_compile backend\queuing\announcements.py backend\queuing\events.py backend\queuing\main.py` | **exit 0** |
| 11 | import resolution, read statically | `check_granted` (`common/permissions.py:222`), `AuthContext` (`:147`), `get_current_user` (`:260`), `branch_accessible` (`:482`), `record_audit` (`common/audit.py`), `SessionFactory` (`common/database.py`), `QueueAnnouncementDelivery` / `QueueEntry` (`common/models.py`), `current_call_event` (`queuing/events.py`) — all present |
| 12 | migration chain | `a7c3f19d2b64` ← `f8a2b3c4d5e6`; creates the table only if absent, `UNIQUE(call_event_id)`, two indexes |

Frontend tests are plain `node:test` with `assert`, importing the real modules —
no mocking of the modules under test. The claim/play/report ordering test uses
the **real** controller and the **real** announcer with a fake transport and a
fake audio element, and records the order in which the three actions happen;
that is why "claim before play" is a proven property rather than a comment.

---

## 7. What is **not** verified, and exactly why

| Claim not made | Blocker observed on this host |
|---|---|
| The two endpoints respond as designed against a real database | `python -c "import fastapi"`, `"import pytest"`, `"import psycopg2"`, `"import sqlalchemy"` **all fail** — no FastAPI, no pytest, no SQLAlchemy, no PostgreSQL driver, no database. `backend/queuing/tests/test_queue.py` (which gained **18** W2 tests in `TestQueueCallEventIdentity`, `TestAnnouncementDeliveryClaim`, `TestAnnouncementAudit`) therefore **could not be executed**; it was only compile-checked (#10) |
| The migration applies and rolls back cleanly | same: no database, no Alembic environment to point at one |
| **Two real terminals, one call, one voice** (the defect this task exists for) | no browser, no second device, no network. Proven only at the contract level: the dedupe key is `UNIQUE` in SQL, the insert is `ON CONFLICT DO NOTHING`, and the two-terminal test drives the real announcer twice against a shared claim set |
| A clip was actually **heard** | no audio device; no `jsdom`/`Audio` in the test host, so playback is a fake element that reports `ended` |
| The 20 s refresh observed in a browser | no browser. The refresher is exercised with a fake `setInterval`/`document`/`window` |
| Staleness boundary correctness under real clock skew | the 120 s bound is client-side and tested, but a terminal with a wrong clock can still mislabel an event; the server's **409** on a non-current event is the real guard, and that guard is unexecuted (row 1) |

Consequences recorded honestly: the task's acceptance criteria are met in code
and in the frontend test suite; the backend half is **IMPLEMENTED, not TESTED**,
and nothing in this task is **VERIFIED** in the §7 evidence standard sense
(there is no second independent artefact such as a live API call or a DB read).

> Correct next step on a host with the stack installed:
> `pytest backend/queuing/tests/test_queue.py -k "Announcement or CallEvent" -q`
> then apply the migration and repeat the two-terminal check in two real
> browsers.


---

## 8. Deviations, decisions and things left alone

| # | Item | Decision |
|---|---|---|
| D1 | **No new capability for announcing** | Announcing is not a queue mutation. The claim is gated on `queue.manage` / `queue.consult`, which already make the panel reachable; inventing `queue.announce` would have required a permission change, which this task was explicitly forbidden to make |
| D2 | **Operator repeat is still claimed** | One *call event* has one delivery record; the operator's repeat is not locally suppressed, so pressing the button twice cannot silently do nothing. If another terminal owns the event the panel says so |
| D3 | **`maxAgeMs` renamed `maxEventAgeMs`** | The old name read as "how long the clip is"; it bounds the *event's* age. A wrong-name option would have been copied into the next module |
| D4 | **`automatic` derived from `opts.source !== 'operator'`** | A single source of truth for "is this a deliberate human action", with an explicit boolean override for callers that already know |
| D5 | `enabled === false` → `disabled` skip placed **after** the wiring guard | A page that has not wired the announcer must report `not_wired`, not claim the feature is switched off |
| D6 | The panel's JSX compile check still skips | Pre-existing (`next/dist/build/swc unavailable in this install`). Not fixed here: the fix is an import-specifier change in a test file outside this task's scope, and `npm run build` supplies stronger compiler evidence |
| D7 | Backend tests written but unexecuted | See §7. Writing them was still correct: they encode the contract and run on a host with the stack |
| D8 | No change to the queue state machine, permissions, templates or audio assets | Only one new i18n **key** (`announceElsewhere`) in the two existing dictionaries |

---

## 9. Governance and Skill Compliance

**Applicable governance documents (§4 routing), all read in this task:**

| Domain | Document applied | How it was followed |
|---|---|---|
| Backend API / service endpoints | `saas-application-security.md` (as adapted, Assessment §3), Business Rules Parts II–X | claim/outcome are two narrow endpoints; closed outcome set → 422; no client-supplied scope; no invented capability |
| Authentication / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py` | existing `check_granted` + `can_access_doctor`; no permission added; doctor/assistant scope mirrors `main.queue_action` (RBAC-R3) |
| Multi-tenant / org-branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6, `common/auth.py` | scope derived from the authenticated token; foreign or out-of-branch → **404**, never 403; `organization_id` remains the only tenant key |
| Database schema / migrations | `saas-multitenant-data.md` §4–5, `saas-cicd-workflow.md` §3 (adapted) | forward-only idempotent Alembic revision chained to `f8a2b3c4d5e6`; the unique key enforces dedupe in the database, not in the browser |
| Queue / workflow transitions | Business Rules Parts V–VII, M4/M5 reports | the queue transaction is untouched; claim and outcome are separate short transactions (V-11); `queue.call` is audited separately from the announcement (V-12, POD-4) |
| Frontend UI | `saas-frontend-ux.md` (adapted), shared components, `frontend/lib/i18n.js` | reuses `QueueAnnouncements`; one new bilingual key; the cross-terminal case is a muted note, not an error; no new design-system primitive |
| Audit / integrity | `saas-observability.md` (adapted), `backend/common/audit.py`, Business Rules Part X | append-only `record_audit`; refusals are recorded, not swallowed; no secrets, tokens or patient data in the audit payload |
| Documentation | §11 (writing) and §12 (reading), `AMSDP_Docs_Index_V1.0.md` | this report lives in `docs/implementation/`; the index is updated in the same task (Revision 48); no document moved, so no manifest entry is owed |

**Skills: none applicable.** §5 of the rules states that no skill packages are
installed in this workspace, and a check of `.clinerules/skills/`, `.claude/skills/`
and any repo `skills/` directory found none. No skill was used and none is
claimed. The knowledge artefacts used instead were the QUE-006 product and
architecture documents and the earlier W1 / W2 / POD-12 implementation reports,
cited by filename throughout.

**Non-negotiables confirmed:** no secret, token or JWT material is logged or
exposed; authorization is server-side and fails closed with 404; the tenant key is
still `organization_id` alone; the audit trail is append-only; the schema change
is a forward-only idempotent migration; no capability is claimed that was not
executed — §7 is deliberately longer than §6.

**Tests and verification:** §6 (frontend, executed) and §7 (backend, blocked,
with the exact failing imports quoted).

**Deviations:** §8, items D1–D8. None relaxes §1 precedence or §3 non-negotiables.


---

## 10. Files

**Added (backend)**

| File | Note |
|---|---|
| `backend/queuing/events.py` | call-event identity, pure, no DB |
| `backend/queuing/announcements.py` | claim + outcome router |
| `backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py` | idempotent forward migration |
| `backend/queuing/tests/test_queue_events.py` | 13 pure identity tests |
| `scripts/que-006-w2-reliability/check_call_event_identity.py` | runs those 13 without pytest |

**Modified (backend)** — `backend/common/models.py` (one model),
`backend/queuing/main.py` (router registration), `backend/queuing/tests/test_queue.py`
(+18 W2 tests; delivery rows are cleared in the fixture teardown so the unique key
cannot leak between tests).

**Added (frontend)** — `lib/announcements/delivery.js`,
`lib/announcements/call-announcer.js`, `lib/queue/queue-refresh.js`,
`tests/queue-announcement-delivery.test.mjs`,
`tests/queue-refresh-safety.test.mjs`.

**Modified (frontend)** — `pages/queue.js`,
`components/queue/QueueAnnouncements.js`, `lib/i18n.js`,
`tests/queue-announcement-w2-integration.test.mjs` (+4 tests),
`tests/queue-call-control.test.mjs` (seam assertion),
`tests/queue-announcement-content.test.mjs`,
`tests/queue-announcement-controller.test.mjs`,
`lib/announcements/content.js`, `lib/announcements/controller.js`.

**This document** — `docs/implementation/QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md`.

---

## 11. Rollback

1. `git checkout -- frontend/pages/queue.js frontend/components/queue/QueueAnnouncements.js frontend/lib/i18n.js frontend/lib/announcements/controller.js frontend/lib/announcements/content.js`
2. delete the five new frontend files listed in §10;
3. delete `backend/queuing/announcements.py`, `backend/queuing/events.py`,
   `backend/alembic/versions/a7c3f19d2b64_*.py`,
   `backend/queuing/tests/test_queue_events.py` and `scripts/que-006-w2-reliability/`;
4. `git checkout -- backend/common/models.py backend/queuing/main.py backend/queuing/tests/test_queue.py`;
5. if the migration was applied, `alembic downgrade f8a2b3c4d5e6` — the delivery
   table is the only object it owns.

Nothing was staged, committed, pushed or deployed in this task. HEAD is unchanged.

---

## 12. Verdict

**PARTIALLY IMPLEMENTED.** The five defects this task set out to close are closed
in code, and every frontend claim is backed by a test run and a clean production
build. The deduplication guarantee rests on a database constraint that has not
been executed on this host, and no browser has been opened. W2 therefore moves
from *"the frontend announces, but unreliably and unauditably"* to *"the contract
is implemented and frontend-tested; backend execution and a two-terminal
observation remain outstanding"* — a real advance, and not yet a completion.

| Milestone-level status | State |
|---|---|
| W2 frontend integration | IMPLEMENTED + TESTED (146 queue tests, 145 pass, 1 pre-existing skip) |
| W2 backend claim / outcome / audit | IMPLEMENTED, **NOT TESTED** on this host (§7) |
| W2 cross-terminal dedupe (two real terminals) | **NOT VERIFIED** |
| W2 persisted announcement audit observed in a database | **NOT VERIFIED** |
| W2 production build | **VERIFIED** (`npm run build` exit 0, `/queue` 15.3 kB) |

