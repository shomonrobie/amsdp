# AMSDP — Phase 3.0 Queue Operations, DQDS and QUE-006
## Gap Analysis

| Item | Value |
|---|---|
| Document | `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` |
| Version | 1.0 |
| Date | 2026-11-19 |
| Task ID | `AMSDP-PHASE-3-GAP-ANALYSIS` |
| Task type | **READ-ONLY DISCOVERY AND GAP ANALYSIS** — implementation authorization NOT granted |
| Status | **ANALYSIS.** No source file, test, migration, configuration, database row or existing document was modified. One new file was created: this document. |
| Branch / HEAD inspected | `hackathon-mvp` @ `6b7ef4d27edbf820bfcafc25a9c789235337823d` (`fix(appointment): reliability remediation F-01…F-19 of the gap analysis`, 2026-11-19 16:29 +0600) |
| Working tree at start | 35 modified files + 12 untracked files, all pre-existing (Phase 2 appointment remediation, owner decisions Q1–Q5, operational RBAC follow-up, QUE-006 documentation). Left exactly as found. |
| Scope | Queue service (`backend/queuing/`), queue UI (`frontend/pages/queue.js`), DQDS (`backend/queuing/display.py`, `frontend/pages/queue-display/[org]/[branch].js`), QUE-006 (no implementation), and the queue↔appointment↔notification seams |
| Out of scope | PQT tracking page behaviour except where a queue transition revokes a tracking token; SaaS subscription planes; deployment/Docker changes; Business Rules or MVP Scope edits |
| Governing sources | `.clinerules`; `docs/governance/AMSDP_Docs_Index_V1.0.md`; `docs/product/AMSDP_Business_Rules_V1.0.md`; `docs/product/AMSDP_MVP_SCOPE_V1.0.md`; `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`; `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`; `docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md` |
| Location rule applied | `.clinerules` §11 — subject subfolder `docs/audit/`; collision checked first (`ls` on the exact path returned “No such file or directory”), so nothing was overwritten |
| Feature dispositions | Unchanged. QUE-001…QUE-006 and DQDS-001 remain **KEEP** per the Product Owner MVP scope lock (2026-11-17); QUE-006 remains **AMSDP Core** |
| Acceptance | **Not claimed for any feature.** ACCEPTED is a Product Owner act and this document does not perform it. |

---

## Section 1 — Executive Summary

### 1.1 Overall Phase 3 readiness

**Phase 3 is not complete, but it is not a greenfield build either.** Queue Operations is a real, database-backed, tenant-scoped service with an atomic token allocator, an audited state machine, a missed-turn recovery module, and 58 queue tests plus 24 DQDS tests in the tree. The DQDS board is implemented, public, non-disclosing on failure, and rate-limited. Those are substantial assets and none of them should be rebuilt.

Three things stand between the current tree and the Phase 3 outcome the task defines
(*appointment/walk-in → check-in → token → queue management → public display → audible announcement → consultation*):

1. **The `call` step has no user interface and, for a doctor, no permission.** The queue API supports `waiting → called`, and the end-to-end tests exercise it over HTTP, but no frontend surface sends `action: "call"` (grepped: zero occurrences of `'call'` in `frontend/`). A receptionist therefore cannot call a patient from the product, and a doctor — who does not hold `queue.manage` — cannot call at all. `called` is nevertheless the state the public board prefers to advertise and the state QUE-006 is specified to announce, so the last two links of the patient journey are unreachable from the product rather than merely unimplemented.
2. **There is no recall, anywhere.** `_TRANSITIONS` (`backend/queuing/main.py:380-388`) permits `call` from `waiting` and `skipped` only; a `called` entry cannot be called again, and no `recall` string exists in the backend or the frontend. QUE-004's brief and QUE-006's recall requirement both depend on it.
3. **QUE-006 does not exist in any form.** No TTS provider, no `speechSynthesis` call, no announcement service, no configuration key, no event, no test, no browser run. `grep -rniE 'speechSynthesis|announce|tts|voice'` over `backend/`, `frontend/` and `docker-compose.yml` returns only unrelated accessibility comments, a symptom-catalogue entry (`hoarse_voice`) and a compiled JS chunk. The catalogue's `NOT STARTED / NOT TESTED` status is accurate.

**Verdict:** Phase 3 needs a remediation-and-completion programme, not a rewrite. **No CRITICAL finding was substantiated** — tenant isolation, branch scoping, doctor ownership and public-board privacy all fail closed in the code that exists and are covered by tests. The blocking work is functional completeness (call/recall in the UI, QUE-006), DQDS fidelity (facility-local day, room information, TV presentation), and testing hygiene.

### 1.2 Existing implementation strengths (do not rebuild)

| Strength | Evidence |
|---|---|
| Atomic daily token allocation under concurrency | `backend/common/queue_tokens.py:38-56` — one `INSERT … ON CONFLICT (doctor_id, date) DO UPDATE … RETURNING`; the rationale (SEQ4-TOKEN-P1: two live entries sharing a token) is in the module docstring |
| Server-enforced branch scope on every queue route | `get_queue` (`main.py:119-160`), check-in (`main.py:169-283`), enqueue (`main.py:294-372`), actions (`main.py:104-117`, `395-467`), history (`main.py:547-585`); tests `TestQueueBranchAuthorization`, `TestQueueEnqueueBranchOwnership`, `TestQueueHistoryBranchAuth` |
| Doctor/assistant ownership fails closed | `auth.can_access_doctor()` on every doctor-scoped route; tests `TestQueueDoctorAssistantOwnership`, `TestQueueMultiDoctorAssignments`, `TestQueueMissingDoctorAssignment` |
| Recovery preserves identity (token, appointment, patient) instead of cancel-and-rebook | `backend/queuing/recovery.py:1-18, 192-281`; tests `test_recover_renumbers_queue_and_keeps_token`, `test_missed_turn_marks_skipped_and_preserves_identity` |
| Every queue mutation writes an audit event | `record_audit(...)` in check-in, enqueue, every action, reorder, missed-turn and recovery; test `test_queue_ops_write_audit_events`; e2e `test_16_the_audit_trail_records_the_workflow` |
| Denials are audited, not swallowed | `install_denial_audit(app, "queuing")` (`main.py:26-28`) |
| DQDS is privacy-minimal and non-disclosing | explicit allow-list payload (`display.py:174-197`); unknown org ≡ unknown branch ≡ foreign branch → identical 404 (`_not_found`, `display.py:98-106`); tests `test_dqds_no_pii`, `test_dqds_cross_org_doctor_name_never_leaks`, `test_dqds_not_found_is_non_disclosing_and_uncacheable` |
| Display resilience and a11y in the board page | stale-while-error with a localized strip, `aria-live="polite"`, not-found and retry states (`queue-display/[org]/[branch].js:80-231`) |

### 1.3 Major gaps

| # | Gap | Where |
|---|---|---|
| G-1 | `call` is API-only; the page exposes ↑/↓, Start, Cancel, Missed turn, Recover — no Call | `frontend/pages/queue.js:173-186` |
| G-2 | Doctors hold `queue.consult`/`queue.recover`/`queue.reposition` but **not** `queue.manage`/`queue.reorder`, so a solo chamber cannot call, cancel or reorder | `backend/common/permissions.py:104-123`; `main.py:400-403` |
| G-3 | No recall action or state transition | `main.py:380-393`; no `recall` anywhere in `backend/` or `frontend/` |
| G-4 | QUE-006 is entirely absent | repository-wide grep; catalogue `NOT STARTED` |
| G-5 | DQDS scopes “today” with `date.today()` (server zone) while the platform uses the facility zone | `display.py:138` vs `common/timeutil.py:59-61` |
| G-6 | No room/chamber in the DQDS payload or the queue data model | `common/models.py:854-873` (`QueueEntry` has `branch_id`, `doctor_id`, no room); `display.py:176-183` |
| G-7 | Token numbering is hardcoded (daily serial per doctor, `T-<doctor-id-prefix>-NNN`); BR §31's continuous mode and room scope do not exist | `common/queue_tokens.py:33-56`; `QueueSequence` PK `(doctor_id, date)` |
| G-8 | The queue page never refreshes itself | `frontend/pages/queue.js:50-65, 157` |
| G-9 | No automated concurrency proof for token allocation or duplicate check-in; duplicate check-in is check-then-insert with no constraint behind it | `main.py:202-213`; `test_unique_daily_tokens` is sequential |
| G-10 | The queue test suite deletes **all** `queue_entries` rows in an autouse fixture, so it is unsafe against a live/demo database | `backend/queuing/tests/test_queue.py:95-100` |

### 1.4 Critical/high risks

| Risk | Severity | Why |
|---|---|---|
| A patient can be called only through an API client | HIGH | The core Phase 3 action is unreachable for receptionists in the shipped UI and impossible for a doctor, so DQDS and any announcement have no product-side trigger |
| A solo doctor cannot run their own queue | HIGH | Scenario A (individual doctor's chamber) is a stated AMSDP operating model; today the doctor can start and complete a consultation but cannot call, cancel or reorder |
| “Recall” does not exist | HIGH | Real waiting rooms need it when a patient did not hear; QUE-006 lists recall as an announcement event |
| QUE-006 missing end-to-end | HIGH | Owner-approved Core capability with zero implementation — not a “test coverage gap” |
| DQDS shows the wrong day's queue for part of every day | HIGH | Between 00:00 and 05:59 Asia/Dhaka the container's UTC date is still “yesterday”, so the board advertises yesterday's active tokens and hides today's check-ins |
| Duplicate tokens for one appointment under a race | MEDIUM | No unique constraint on `queue_entries.appointment_id` and no row lock; two concurrent requests can both pass the “already queued” check |
| Cross-branch position rewriting in recovery | MEDIUM | `_active_queue()` scopes org+doctor+date but not branch, then `_renumber()` writes positions and audit rows for those entries |
| Running the queue tests on this host destroys demo queue state | MEDIUM | The `clean_queue` autouse fixture deletes the whole table |

### 1.5 Browser-verification status

| Surface | Browser verified? | Evidence |
|---|---|---|
| DQDS board page | **BROWSER UNVERIFIED** | `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` §11.5 records that no browser/E2E harness exists in this repo and that the page is covered only by `next build` and endpoint tests; §9's live verification used `curl` against uvicorn, not a browser |
| Queue operator page (`/queue`) | **BROWSER UNVERIFIED** | No browser run is recorded anywhere in the tree, and no frontend test covers `pages/queue.js` (the 16 files in `frontend/tests/` are library unit tests) |
| QUE-006 announcement playback | **BROWSER UNVERIFIED — and unimplemented** | Nothing to verify |
| Audio/autoplay behaviour on a TV device | **UNVERIFIED and undesigned** | No audio code; no device/browser matrix recorded |

No feature in this document is ACCEPTED.

---

## Section 2 — Scope and Governance

### 2.1 Documents consulted in this session (all read from disk, not from memory)

| Document | What was taken from it |
|---|---|
| `.clinerules` | Precedence (§1), routing (§4), non-negotiables (§3), evidence standard (§7), execution boundaries (§9), documentation location (§11) and reading (§12) rules |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Navigation to every document below; Revision 33 snapshot (**90** documents on disk, **88** registered; open item O-3) |
| `docs/product/AMSDP_Business_Rules_V1.0.md` | §24–§29 (walk-ins, unified queue, manual queue management, priority, daily board), §30–§33 (token generation, numbering modes/scope, printed tokens, DQDS FINALIZED DIRECTION), §40–§42 (audit, minimisation, security), §52–§54 (queue/token and display acceptance criteria) |
| `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` | QUE-001…QUE-006 and DQDS-001 entries (description, roles, expected behaviour, acceptance criteria, dependencies, recorded status), §E.6/§E.13 checklists, §F.4 status summary, §F.1/F.2 labels |
| `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | §A–§G (public DQDS: token-only, org/branch-scoped, P0), §H classification, §J (notifications), §K (missed-turn recovery “NOT APPROVED FOR MVP” as written) |
| `docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md` | The twelve fields of the QUE-006 catalogue entry, the ten acceptance criteria, the Core-classification evidence and the `NOT STARTED / NOT TESTED` record |
| `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md` | Endpoint/permission table, lifecycle diagram, token UPSERT rationale, the 17-test / live-e2e / 20-concurrent claims, and the report's own “remaining gaps” |
| `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` | DQDS audit findings A1–A9, backend/UI hardening, the 24 tests, §9 live `curl` verification, §10 evidence table, §11 deviations (limiter per-process, idle doctors omitted, only serving token published, own i18n map, **no browser harness**) |
| `backend/tests/test_sequence3.py` (26 tests) | Missed-turn/recovery contract and the notification hooks a queue change re-plans |
| Source of truth for behaviour | `backend/queuing/main.py` (585 lines), `display.py` (201), `recovery.py` (282), `common/queue_tokens.py`, `common/permissions.py`, `common/timeutil.py`, `common/notifications/config.py`, `common/models.py` (`QueueEntry` 854-873, `QueueSequence`), `frontend/pages/queue.js` (262), `frontend/pages/queue-display/[org]/[branch].js`, `frontend/lib/auth.js` (`can()`), `frontend/styles/global.css` (`.dqds-*`) |

No document named by the task brief was missing. **The catalogue is authoritative for this analysis but its QUE-001…QUE-005 status rows are stale** — see §3.6 and QOP-019.

### 2.2 Approved decisions applied (not re-opened)

| Decision | Status used here |
|---|---|
| QUE-001…QUE-005, DQDS-001 and QUE-006 are all **KEEP** (MVP scope lock, 2026-11-17) | Applied. No disposition in this document changes |
| QUE-006 is **AMSDP Core**, configurable per facility, not a Connect feature and not a future module | Applied; treated as in-scope Phase 3 work (ANN findings), not deferred |
| Appointment and queue are separate lifecycles: an appointment is not “in the queue” until check-in | Applied; the analysis follows the actual transition (`BOOKED/AWAITING_CONFIRMATION/CONFIRMED/CHECKED_IN → IN_QUEUE`) |
| Organization = tenant; branch = location; server-side authorization; cross-tenant/cross-branch = 404 | Applied as the standard every finding is measured against |
| DQDS is public, token-only, org+branch path-scoped, zero PII, no auth | Applied |
| Facility configuration belongs on `organizations.config` (existing mechanism, e.g. `notification_config`, `appointment_config`) | Applied — QUE-006 configuration is assessed against this mechanism rather than a new framework |
| Missed-turn recovery and repositioning are implemented product behaviour (BR §27A, `recovery.py`) | Applied **with the contradiction recorded in §2.4** |

### 2.3 Scope boundaries

In scope: queue creation/token/sequencing, lifecycle and transitions, ordering and recovery, role/branch/doctor authorization, appointment↔queue integration, DQDS function/security/presentation/reliability, QUE-006 (events, speech, content, configuration, duplicate suppression, browser audio constraints, tests), and the A–E integration scenarios.

Out of scope: appointment booking rules and capacity (covered by `AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` and its remediation report); PQT tracking page internals beyond the revocation call; SMS/WhatsApp delivery mechanics; Docker/CI; subscription entitlements; UI restyling beyond what a finding requires.

### 2.4 Documented contradictions found (reported, not silently resolved)

| # | Contradiction | Sources | Consequence |
|---|---|---|---|
| C-1 | DQDS scope: BR §33 requires multi-doctor/**multi-room** display, per-display configuration, configurable display language and estimated wait, and calls itself “later-phase”; the catalogue's DQDS-001 requires only a doctor-wise token board and records `IMPLEMENTED / TESTED`; PQV §B calls DQDS **MVP/P0** with “multi-display configuration part of the same” scope | `AMSDP_Business_Rules_V1.0.md:740-770`; `AMSDP_MVP_Feature_Catalogue…:886-915`; `AMSDP_PQV_…:57-70, 160` | Which document defines Phase 3 DQDS acceptance? Recorded as **OD-4** |
| C-2 | Missed-turn recovery: PQV §H classifies it `NOT APPROVED FOR MVP`; the code implements it, the catalogue's QUE-004 includes “recover”, and BR §27 is “FINALIZED” for manual queue management | `AMSDP_PQV_…:165`; `recovery.py`; catalogue `:482-511` | Whether the shipped recovery module is approved scope is recorded as **OD-6** |
| C-3 | Queue action API: catalogue documents `POST /api/v1/queue/action`; the tree exposes `PATCH /api/v1/queue/{entry_id}` with an `action` field | catalogue `:489`; `main.py:395` | Documentation drift — QOP-019 |
| C-4 | Check-in permission: catalogue says `queue.checkin`; the tree requires `appointment.check_in` (owner decision Q3) | catalogue `:370`; `main.py:169-171` | Documentation drift — QOP-019 |
| C-5 | Branch/ownership defects: catalogue F.4 lists R-01…R-04 as open (`PARTIALLY IMPLEMENTED`); the working tree contains the P0-1…P0-5, RBAC-R1/R3 and C1/C2 fixes with dedicated tests | catalogue `:1251-1255, 1334-1338`; `main.py` inline comments | Catalogue understates the tree — QOP-019 |

`.clinerules` §1 requires a conflict to be reported rather than silently resolved; C-1, C-2 and C-4 affect business behaviour or scope and are therefore raised as owner decisions in Section 12, not decided here.

---

## Section 3 — Current Implementation Inventory

### 3.1 Queue backend (`backend/queuing/`, 1,068 lines of service code)

| Route | Method | Authorization | Behaviour |
|---|---|---|---|
| `/api/v1/queue` | GET | any authenticated (`get_current_user`) + `can_access_doctor` for doctor/assistant | Active entries for one doctor/date, optionally branch-filtered; joins patient and doctor names |
| `/api/v1/queue/check-in` | POST | `appointment.check_in` | Appointment → queue entry (`entry_source="appointment"`), token allocated, appointment advanced to `IN_QUEUE`, notification hooks fired after commit |
| `/api/v1/queue/enqueue` | POST | `queue.checkin` | Walk-in/extra entry; `entry_source ∈ {walk_in, extra, appointment}`; branch validated against token scope |
| `/api/v1/queue/{entry_id}` | PATCH | `queue.consult` (start/complete consultation) else `queue.manage` | State machine with an explicit transition table; audit event per action |
| `/api/v1/queue/{entry_id}/missed-turn` | POST | `queue.recover` | `waiting`/`called` → `skipped`, identity preserved |
| `/api/v1/queue/{entry_id}/recover` | POST | `queue.recover` (+`queue.reposition` for an override) | `skipped` → `waiting` at end of queue or at a reasoned position; renumbers the queue |
| `/api/v1/queue/reorder` | POST | `queue.reorder` | Bulk order change, homogeneity check, position history per moved entry |
| `/api/v1/queue/history` | GET | any authenticated + `can_access_doctor` for doctor/assistant | All statuses for a doctor/date; branch validated |
| `/api/v1/queue/display/{org_code}/{branch_code}` | GET | **public** | DQDS board; 30 req/min/IP; `public, max-age=10` |

State model (`main.py:70, 380-393`):

```
ACTIVE_STATUSES = waiting | called | in_consultation | skipped

waiting         → call | start_consultation | cancel | mark_no_show
called          → start_consultation | cancel | mark_no_show
in_consultation → complete_consultation
skipped         → call | reinsert | start_consultation | cancel
completed | cancelled | no_show → (terminal)
```

Token model (`common/queue_tokens.py`, `QueueSequence`): one daily counter per `(doctor_id, date)`, allocated by a single atomic UPSERT; the display token is `T-<first 6 chars of doctor_id uppercased>-<serial:03d>`; the queue position defaults to the serial (`main.py:229, 339`) and is rewritten to `1..N` by reorder and recovery.

### 3.2 Queue frontend (`frontend/pages/queue.js`, 262 lines)

- Doctor selector, date input, Search button; table columns: `#` (position), token, patient, source, status, actions.
- Actions rendered: ↑/↓ (`canManage`), Start (`canConsult` + `waiting`), Complete (`canConsult` + `in_consultation`), Cancel (`canManage` + `waiting`), Missed turn (`canRecover` + `waiting|called`), Recover (`canRecover` + `skipped`).
- Modals: Check-in (appointments filtered to `CONFIRMED`), Walk-in (patient + policy), Missed turn (`ConfirmDialog` with reason), Recover (mode/position/reason), Cancel (reason required).
- Data loading: `loadQueue()` on mount, on doctor/date change, and after any action. **No timer, no polling, no websocket** (`grep setInterval` on the page returns nothing).
- Capability gating mirrors the backend matrix through `frontend/lib/auth.js:can()` — a second copy of the permission table (`auth.js:21-36`), which must be kept in step with `common/permissions.py`.

### 3.3 DQDS backend (`backend/queuing/display.py`) and page

| Aspect | Actual implementation |
|---|---|
| Data source | `QueueEntry ⋈ Doctor` for one org+branch, `QueueEntry.date == date.today()`, `status IN (waiting, called, in_consultation, skipped)`, doctor `active`/NULL, ordered by doctor name then position |
| Response | `{organization:{name,code}, branch:{name,code}, doctors:[{doctor_name, currently_serving, patients_waiting}], updated_at}` — a hand-built allow-list, no ids, no patient data |
| Serving token | `in_consultation` preferred, else the lowest-position `called`; `skipped` counts as waiting, never as serving |
| Transport | HTTP polling, 10 s (`REFRESH_MS`), matching `Cache-Control: public, max-age=10` |
| Rate limiting | In-process sliding window, 30/60 s per `request.client.host`, `X-RateLimit-*` on success, `Retry-After` + `no-store` on 429 |
| Failure modes | Unknown/inactive org or branch → identical `404 {"detail":"not found"}` with `no-store`; transport failure → stale-while-error strip on the page |
| Language | Display-local `bn`/`en` string map inside the page; precedence `?lang=` → `localStorage['dqds_locale']` → staff `sessionStorage['locale']` → `bn` |
| Presentation | Card `max-width:960px`; token `1.4rem` (~22 px); doctor name `1rem`; single column below 640 px, two-row flex above |
| Tests | `backend/tests/test_dqds.py` — 24 tests (PII, isolation, non-disclosure, cache, limiter headers, inactive tenant/branch/doctor, serving preference, tracking-material absence) |

### 3.4 QUE-006 inventory

| Element | Present? | Evidence |
|---|---|---|
| Announcement event emitted on call | **No** | `queue_action` calls `record_audit`, `_notify("on_queue_changed", …)` and `revoke_for_appointment`; no announcement hook, no event id |
| Queue-event transport (stream/SSE/WS/queue) | **No** | Only HTTP request/response and the SMS/WhatsApp outbox |
| Speech synthesis (browser or server) | **No** | Repository grep for `speechSynthesis`, `SpeechSynthesisUtterance`, `tts`, `text-to-speech`, `announce` → no product hits |
| TTS provider / audio assets | **No** | No provider config, no media directory, no dependency in `backend/requirements*.txt` or `frontend/package.json` |
| Facility configuration key | **No** | `organizations.config` is used for `notification_config` and `appointment_config` only |
| Configuration UI | **No** | No page, no control |
| Announcement content template | **No** | Only catalogue prose |
| Duplicate suppression / ordering / retry | **No** | Nothing to suppress |
| Audio-permission/autoplay handling | **No** | No audio code |
| Tests | **No** | No announcement test anywhere |
| Catalogue status | `NOT STARTED` / `NOT TESTED` | `AMSDP_MVP_Feature_Catalogue…:577-581, 1266` |

### 3.5 Event and configuration architecture that QUE-006 would use

| Asset | State | Relevance |
|---|---|---|
| `_notify(event, *args)` best-effort hook pattern | Implemented and used by every queue mutation (`main.py:47-57`, `recovery.py:60-66`) | The established way to add a **non-blocking** side effect; a hook that never raises is exactly the “announcement failure must not fail the call” contract, but the current hooks are synchronous and delivery-less |
| Notification outbox (`common/notifications/`) | Implemented for `whatsapp`/`sms` only (`config.py:66`, `CHANNELS`) | Durable, retry-aware, deduped rows with a worker; a server-side announcement transport could reuse the outbox shape, but the channel list is closed |
| `organizations.config` JSON + `appointment_config` router | Implemented (`backend/organization/appointment_config.py`) | The template for `queue_announcement_config`: org-scoped route, `org.read`/`org.manage`, before/after audit, non-disclosing 404 for a foreign org |
| `organizations.locale` (default `bn`), `organizations.timezone` (default `Asia/Dhaka`) | Implemented (`common/models.py:38-39`) | Facility-level language and operational day already exist as columns |
| `common/timeutil.operational_today()` | Implemented and used by enqueue | The correct source for “today”; DQDS does not use it (DQD-001) |

### 3.6 Documentation drift and test inventory (summary; full inventory in Section 10)

The catalogue's QUE-001…QUE-005 rows and F.4 summary describe a tree that no longer exists: `POST /api/v1/queue/action` is now `PATCH /api/v1/queue/{entry_id}`; check-in requires `appointment.check_in`; R-01…R-04 are fixed and tested (P0-1…P0-5, RBAC-R1/R3, C1/C2). The current status of the queue features is therefore **better** than the catalogue records — but the catalogue is the artefact the Product Owner signs, so it must be reconciled before acceptance (QOP-019, Stage 3.4).

Test inventory in the tree: `backend/queuing/tests/test_queue.py` (58 tests in 13 classes), `backend/tests/test_dqds.py` (24), `backend/tests/test_sequence3.py` (26 — recovery + notification hooks), `backend/tests/test_sequence4.py` (13 — token/check-in seams), `backend/tests/test_e2e.py` (21 — cross-service lifecycle incl. `call`), `backend/tests/test_security.py` (25), `frontend/tests/*.test.mjs` (16 files, none for `pages/queue.js` or the DQDS page).

---

## Section 4 — Queue Operations Findings (QUE-001 … QUE-005)

Severity per task §10: **CRITICAL** = security/privacy exposure, cross-tenant leakage, queue corruption or an unsafe core operation; **HIGH** = a core queue workflow cannot reliably do what it must; **MEDIUM** = important function/configuration/integration/recovery issue; **LOW** = usability/presentation.

### QOP-001 — The `call` action has no user interface

| Field | Value |
|---|---|
| Feature | QUE-004 (queue call) |
| Finding | QOP-001 |
| Severity | HIGH — the first half of the documented Phase 3 journey (`queue action → public display → announcement`) has no product-side trigger |
| Expected | A receptionist (or another authorized operator) selects a waiting patient and calls them; the entry becomes `called`, the board advertises it, and (once QUE-006 exists) the announcement fires |
| Actual | `queue.js` renders ↑/↓, Start, Complete, Cancel, Missed turn and Recover only. `doAction()` is invoked with `start_consultation`, `complete_consultation` and `cancel`; nothing in `frontend/` sends `action: "call"` (grep returns zero hits) |
| Evidence | `frontend/pages/queue.js:105-135, 173-186`; `backend/queuing/main.py:395-467` (API supports `call`); `main.py:380-393` |
| Tests | `backend/tests/test_e2e.py:275` (`test_14_queue_lifecycle_completes_the_visit`), `backend/tests/test_sequence4.py:124` — the action is tested **over HTTP only** |
| Test status | TESTED at API level; **no** test or code path exercises it through the UI |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None — server-side authorization is unaffected by a missing button |
| Remediation | Add a Call action (visible for `waiting` when the operator holds the capability) that PATCHes `{action:"call"}` and refreshes the row from the response |
| Dependencies | QOP-002 must be settled at the same time, otherwise the button is hidden for the solo-doctor model |
| Acceptance | A receptionist can move `waiting → called` from `/queue`, the response is `200`, an audit event `queue.call` exists, and the DQDS board shows the token as serving within one poll (≤10 s) |

### QOP-002 — A doctor cannot operate their own queue

| Field | Value |
|---|---|
| Feature | QUE-004, QUE-005 (and Scenario A) |
| Finding | QOP-002 |
| Severity | HIGH — the individual-doctor-chamber operating model cannot complete a queue cycle |
| Expected | In a chamber without reception staff, the doctor calls the next patient, can reorder a short queue, and can cancel a no-show |
| Actual | `doctor` holds `queue.view`, `queue.consult`, `queue.recover`, `queue.reposition` — **not** `queue.manage`, not `queue.reorder`, not `queue.checkin`. `call`/`cancel`/`mark_no_show`/`reinsert` all require `queue.manage` (`main.py:401-403`), so a doctor receives `403`; `reorder` requires `queue.reorder` (`main.py:476`). The frontend mirrors this (`auth.js:32-35`), so no button appears either |
| Evidence | `backend/common/permissions.py:104-123`; `frontend/lib/auth.js:32-35`; `main.py:400-403, 476` |
| Tests | `test_doctor_can_start_consultation`, `test_receptionist_cannot_start_consultation`, `test_rbac_r3_doctor_can_consult_own_entry`, `test_doctor_may_confirm_and_recover_within_their_queue` — the positive capability set is tested; the absence of `queue.manage` for doctors is not asserted anywhere |
| Test status | TESTED (current behaviour) — the gap is encoded, not flagged |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | Widening doctor authority must stay constrained by `can_access_doctor` (already enforced on every route) and must not confer `appointment.modify` |
| Remediation | Prefer a narrow `queue.call` capability over granting the broad `queue.manage` (which also allows cancel/no-show), and mirror it in `lib/auth.js` |
| Dependencies | OD-5; frontend capability mirror; audit action naming |
| Acceptance | A doctor can call a patient in their own queue, cannot do so in another doctor's queue (404), and gains no ability to cancel/reschedule an appointment |

### QOP-003 — Recall does not exist

| Field | Value |
|---|---|
| Feature | QUE-004; QUE-006 (recall event) |
| Finding | QOP-003 |
| Severity | HIGH — a normal waiting-room event (“the patient did not hear”) has no supported action, and QUE-006 is specified to announce recalls |
| Expected | A `called` patient can be called again without changing status or token; the action is audited and announceable |
| Actual | `called` permits only `start_consultation`, `cancel`, `mark_no_show`. There is no `recall` action, route, capability, audit action or transition (`grep -rni recall backend frontend --include=*.py --include=*.js` → no product hits) |
| Evidence | `main.py:380-393`; `main.py:374-377` (`QueueAction.action` enum comment) |
| Tests | None — no test names recall anywhere |
| Test status | NOT TESTED (nothing to test) |
| Browser status | NOT APPLICABLE (no surface) |
| Privacy/security | A recall must not create a second live entry; identity stays on the same row |
| Remediation | Add `recall` to the `called` transition set as an idempotent, state-preserving action (status stays `called`, history gains `{action:"recall"}`), audit it as `queue.recall`, and surface it beside the called row |
| Dependencies | OD-5 (semantics), ANN-002 (event identity for dedupe) |
| Acceptance | Recalling a `called` entry returns `200`, status remains `called`, `status_history` gains a `recall` entry, `queue.recall` appears in the audit trail, and two recalls cannot produce two overlapping announcements |

### QOP-004 — Duplicate check-in is a check-then-insert with no constraint behind it

| Field | Value |
|---|---|
| Feature | QUE-001 (appointment check-in) |
| Finding | QOP-004 |
| Severity | MEDIUM — needs concurrent requests to trigger, but then produces two live entries with two tokens for one appointment |
| Expected | One appointment yields at most one active queue entry, guaranteed by the database rather than by a read |
| Actual | `check_in_appointment` queries for an active entry, then inserts. `queue_entries` has no unique constraint on `appointment_id` (only `idx_queue_doctor_date` and `idx_queue_org`) and the initial migration creates none (`backend/alembic/versions/5f3fce6757cf_initial_schema.py` is the only migration touching `queue_entries`) |
| Evidence | `backend/queuing/main.py:202-213`; `backend/common/models.py:854-873`; alembic chain |
| Tests | `test_duplicate_check_in_rejected` (sequential), `test_13_double_check_in_is_rejected` (e2e, sequential) |
| Test status | TESTED for the sequential case only; the race is untested |
| Browser status | N/A |
| Privacy/security | Two tokens for one patient on a public board is a patient-identification hazard (the same class as SEQ4-TOKEN-P1) |
| Remediation | Add a partial unique index on `queue_entries(appointment_id)` where `status IN ('waiting','called','in_consultation','skipped')`, or take a `FOR UPDATE` lock on the appointment row; return `422` on the constraint violation. Forward-only Alembic migration |
| Dependencies | Pre-existing data must be de-duplicated first (a migration precondition, not a data rewrite by the agent) |
| Acceptance | Two concurrent `POST /queue/check-in` calls for one appointment produce exactly one `201` and one `422`; a second active entry is impossible at the database level; a regression test drives the race with `ThreadPoolExecutor` |

### QOP-005 — Enqueue can create an “appointment” entry with no appointment, and can queue one patient twice

| Field | Value |
|---|---|
| Feature | QUE-002 (walk-in enqueue) |
| Finding | QOP-005 |
| Severity | MEDIUM — data integrity: the entry's provenance can be wrong and duplicates are possible |
| Expected | `entry_source="appointment"` implies an `appointment_id`; the queue holds one active entry per patient/doctor/day |
| Actual | `entry_source` is accepted from `{walk_in, extra, appointment}`, but the route always inserts `appointment_id=None`; no check rejects a second active entry for the same `patient_id`+`doctor_id`+`date` |
| Evidence | `backend/queuing/main.py:284-300, 335-350` |
| Tests | `TestWalkInPolicies` (4 policies + invalid policy), `TestQueueEnqueueBranchOwnership` (7) — none covers provenance or duplicate patients |
| Test status | TESTED for policy/branch behaviour; the integrity gaps are untested |
| Browser status | N/A |
| Privacy/security | A duplicate live entry means two tokens for one person; a mislabelled source corrupts operational reporting |
| Remediation | Restrict `entry_source` to `{walk_in, extra}` on this route (an appointment entry must come from check-in), and reject or explicitly document a second active entry for the same patient/doctor/day |
| Dependencies | QOP-004's constraint work should be designed together |
| Acceptance | Posting `entry_source="appointment"` returns `422`; a second enqueue for the same patient/doctor/day is either refused with a clear code or recorded as an intentional `extra`; both behaviours are tested |

### QOP-006 — Reorder accepts an empty reason and does not require `queue.reposition`

| Field | Value |
|---|---|
| Feature | QUE-005, QUE-004 |
| Finding | QOP-006 |
| Severity | MEDIUM — audit quality: BR §27.2 requires previous/new position, actor, timestamp **and reason where required**; the catalogue requires a written reason for a reposition |
| Expected | A manual reorder carries a justification, and a position override is gated on `queue.reposition` |
| Actual | `QueueReorder.reason` defaults to `""` and is written into the audit row verbatim; the route depends only on `queue.reorder`. Recovery *does* enforce both (reason required for an override, `queue.reposition` checked) — the two paths disagree |
| Evidence | `main.py:469-476, 505-533` vs `recovery.py:192-227` |
| Tests | `test_reorder_preserves_token`, `test_p0_5_reorder_rejects_mixed_branch`, `test_p0_5_reorder_same_branch_succeeds` — none asserts a required reason |
| Test status | TESTED for ordering behaviour only |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None; weakens the audit defensibility of queue order changes |
| Remediation | Require a non-empty reason for reorder (422 otherwise), and require `queue.reposition` in addition to `queue.reorder` when a move crosses another entry — or record explicitly that reorder is a distinct, reason-optional capability (BR §27 wording) |
| Dependencies | Documentation wording or a simple code rule; the frontend already collects a reason for recovery only |
| Acceptance | `POST /queue/reorder` without a reason returns `422`; a reasoned reorder records `reason` and before/after positions for every moved entry; a caller without `queue.reposition` cannot perform a position override |

### QOP-007 — Recovery renumbers entries belonging to another branch

| Field | Value |
|---|---|
| Feature | QUE-004 (recover/reposition) |
| Finding | QOP-007 |
| Severity | MEDIUM — cross-branch mutation of queue bookkeeping by a branch-scoped actor |
| Expected | A branch-scoped operator affects only their own branch's queue |
| Actual | `_scoped_entry` correctly checks the *acted-on* entry's branch, but `_active_queue()` selects every active entry for the doctor/date **without a branch filter**, and `_renumber()` then writes `position`, `position_history` and a `queue.reposition` audit event for those rows. A doctor working at two branches on one day has both branches' entries renumbered by a receptionist at one of them |
| Evidence | `recovery.py:78-95` (entry scope) vs `recovery.py:97-110` (`_active_queue`) and `113-140` (`_renumber`) |
| Tests | `test_recovery_cross_branch_and_cross_org_are_404` — covers the acted-on entry only, not the neighbours |
| Test status | TESTED for the entry; the neighbour scope is untested |
| Privacy/security | No disclosure; an unauthorized write to another branch's rows, and audit events attributed under the wrong branch context |
| Remediation | Add `QueueEntry.branch_id == entry.branch_id` to `_active_queue()`, and add a two-branch regression test |
| Dependencies | QOP-008 (position semantics) should be decided first |
| Acceptance | Recovering an entry at branch A leaves branch B's positions and audit trail untouched; the test seeds both branches and asserts it |

### QOP-008 — Token serial doubles as queue position, and ordering has no tie-break

| Field | Value |
|---|---|
| Feature | QUE-001, QUE-002, QUE-003, QUE-005 |
| Finding | QOP-008 |
| Severity | MEDIUM — display order can be ambiguous and `#` in the UI is not a queue rank |
| Expected | Position is a dense, unique queue order; the token is a separate, stable label (BR §27.6: position, appointment status, appointment time and token are separate concepts) |
| Actual | `pos = seq` on both insert paths, so positions are the token serial (gappy after cancellations) until a reorder/recovery rewrites 1..N; `staff_placement` accepts any caller-supplied position with no uniqueness check, so two live entries can share a position; `get_queue` orders by `position` only, with no `created_at` tie-break (unlike `_active_queue` in recovery) |
| Evidence | `main.py:229, 339`; `main.py:119-160`; `recovery.py:97-110` |
| Tests | `test_staff_placement`, `test_unique_daily_tokens`, `test_reorder_preserves_token` — none asserts position uniqueness or stable ordering under ties |
| Test status | TESTED for creation/order basics only |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Keep `position` dense and unique per queue context (allocate `max(position)+1`; reject or normalise a duplicate `staff_placement`) and order by `(position, created_at)` everywhere |
| Dependencies | QOP-009 shares the same decision surface |
| Acceptance | Two live entries never share a position; API order equals UI order under any tie; a test asserts uniqueness after enqueue/reorder/recover sequences |

### QOP-009 — Token numbering is hardcoded; BR §31 modes and scope do not exist

| Field | Value |
|---|---|
| Feature | QUE-001, QUE-002 |
| Finding | QOP-009 |
| Severity | MEDIUM — BR §31 (FINALIZED), §52 and §56 require a configurable numbering mode (daily/continuous) and scope (doctor or room); one mode and one scope exist |
| Expected | Daily serial by default, continuous serial available, numbering per doctor **or per room**, token unique within its scope, history preserved across resets |
| Actual | One counter per `(doctor_id, date)`; format fixed as `T-<doctor-id-prefix>-<NNN>`; no continuous mode, no room scope, no configuration key, no UI. The M5 report lists “token numbering config (doctor vs room) not surfaced in UI — Low”, but the backend capability does not exist either |
| Evidence | `common/queue_tokens.py:33-56`; `common/models.py` (`QueueSequence` PK); `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md` §11 |
| Tests | `test_unique_daily_tokens` |
| Test status | TESTED for daily uniqueness only |
| Browser status | N/A |
| Privacy/security | The token embeds part of the doctor's UUID — an internal identifier on a public board, and an unspeakable string for QUE-006 (DQD-011, ANN-007) |
| Remediation | Introduce `queue_numbering_config` on `organizations.config` (mode, scope, prefix, width), extend `QueueSequence` to a scope key and keep the daily default; decide scope under OD-7 |
| Dependencies | OD-7; a forward-only migration if the sequence key changes |
| Acceptance | A facility can select daily or continuous numbering and doctor or room scope; tokens remain unique within scope; existing tokens are never renumbered; both modes are tested |

### QOP-010 — The queue page never refreshes itself

| Field | Value |
|---|---|
| Feature | QUE-003 (queue view), task §5.3 (displayed order vs authoritative order) |
| Finding | QOP-010 |
| Severity | MEDIUM — two operators at one desk can act on a stale list; the displayed order is only authoritative at load time |
| Expected | The operator's list reflects the backend's current order (poll or push) without a manual action |
| Actual | `loadQueue()` runs on mount, on doctor/date change and after a local action. There is no interval, no SSE/websocket, and no “last updated” indicator. A patient queued by another operator, or a call made on another device, is invisible until Search is pressed |
| Evidence | `frontend/pages/queue.js:50-65, 157`; no `setInterval`/`EventSource`/`WebSocket` in the page |
| Tests | None (no frontend test covers this page) |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Poll `GET /api/v1/queue` on a short interval (10–15 s, matching DQDS's cache window) with an in-flight guard and a visible “last updated”; move to push only if a transport is introduced for QUE-006 |
| Dependencies | Shares a transport decision with ANN-002 |
| Acceptance | A change made by another operator appears within one interval without user action; the poll pauses when the tab is hidden; no duplicate actions from overlapping requests |

### QOP-011 — Queue history has an endpoint but no screen

| Field | Value |
|---|---|
| Feature | QUE-003 / QUE-004 (history and audit visibility) |
| Finding | QOP-011 |
| Severity | MEDIUM — operators and supervisors cannot see completed/cancelled/skipped entries, so “what happened to token 004?” is answerable only through the audit log or a database read |
| Expected | An authorized operator can view a doctor/day queue including terminal entries and their history |
| Actual | `GET /api/v1/queue/history` is implemented with branch and doctor scoping, and `grep 'queue/history' frontend/` returns nothing — no page calls it |
| Evidence | `main.py:547-585`; frontend grep |
| Tests | `TestQueueHistoryBranchAuth` (7 tests) covers the endpoint |
| Test status | TESTED (backend only) |
| Browser status | NOT IMPLEMENTED in the UI, therefore unverifiable |
| Privacy/security | The endpoint is correctly scoped; a future screen must keep patient names behind `queue.view` + branch/doctor scope |
| Remediation | Add a history view/toggle on `/queue` (same doctor/date filters) that reads `/api/v1/queue/history` |
| Dependencies | None |
| Acceptance | An operator can list terminal entries for their queue, cross-branch history returns 404, and the view is read-only |

### QOP-012 — The queue test suite wipes the whole queue table

| Field | Value |
|---|---|
| Feature | Test hygiene (affects every QUE feature) |
| Finding | QOP-012 |
| Severity | MEDIUM — the suite cannot be run on a host whose database holds real or demo queue data; this is why this analysis did not execute it (§10.3) |
| Expected | A test suite purges only the rows it created (the pattern `purge_org()` in `backend/tests/amsdp_test_support.py:309-366` already establishes) |
| Actual | `@pytest.fixture(autouse=True) def clean_queue()` runs `session.query(QueueEntry).delete()` before every test — a table-wide delete in whatever database `AMSDP_DATABASE_URL` points at |
| Evidence | `backend/queuing/tests/test_queue.py:95-100` |
| Tests | The suite itself (58 tests) |
| Test status | TESTED (that it passes) but **unsafe to execute against a populated database** |
| Browser status | N/A |
| Privacy/security | A destructive test default is a data-loss hazard on any shared environment |
| Remediation | Scope the fixture to the suite's own org (`m5-org`) or to ids created by the test, and refuse to run if `AMSDP_DATABASE_URL` looks like a shared/demo database |
| Dependencies | None |
| Acceptance | Running the suite leaves every row outside its own fixture org intact; a guard fails fast when pointed at a non-test database |

### QOP-013 — No automated concurrency evidence for queue writes

| Field | Value |
|---|---|
| Feature | QUE-001, QUE-002 |
| Finding | QOP-013 |
| Severity | MEDIUM — the token allocator is the one place where a race corrupts patient identity, and no test proves it |
| Expected | A test drives N simultaneous check-ins/enqueues and asserts N distinct tokens and positions (the pattern `ThreadPoolExecutor` already used in `backend/appointment/tests/test_capacity_integrity.py:214` and `test_appointment_reliability.py:171`) |
| Actual | `test_unique_daily_tokens` creates entries sequentially. The “20 concurrent enqueues → 20 unique tokens” claim lives only in `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md` §8 (a live run, not a test) |
| Evidence | `backend/queuing/tests/test_queue.py` (no `Thread`/`concurrent` import — verified by grep across `backend/**/test_*.py`); M5 report §8 |
| Tests | `test_unique_daily_tokens` |
| Test status | TEST COVERAGE GAP |
| Browser status | N/A |
| Privacy/security | Duplicate tokens are a patient-identification hazard on the public board |
| Remediation | Add `ThreadPoolExecutor` tests for (a) concurrent enqueue → unique tokens, (b) concurrent check-in of one appointment → one entry (ties to QOP-004), (c) concurrent reorder → deterministic final order |
| Dependencies | QOP-004 |
| Acceptance | Each concurrency test fails against the current duplicate-check-in code and passes after the fix |

### QOP-014 — The queue page opens on the UTC date

| Field | Value |
|---|---|
| Feature | QUE-003 (usability) |
| Finding | QOP-014 |
| Severity | LOW — wrong default, easily corrected by the operator, but it contradicts the platform's own rule |
| Expected | The page defaults to the facility-local date (`operational_today()` semantics, BR §8) |
| Actual | `React.useState(new Date().toISOString().slice(0, 10))` — the browser's UTC date. Between 00:00 and 05:59 Asia/Dhaka this is “yesterday” for an operator in Dhaka |
| Evidence | `frontend/pages/queue.js:26`; contrast `backend/common/timeutil.py:1-18` (finding SEQ4-TZ-P1) |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Derive the default from the organization's timezone (the facility context is already fetched elsewhere in the app) or from a server-provided “today” |
| Dependencies | A facility/timezone source on the frontend (currently only `getActiveBranch()`) |
| Acceptance | At 01:00 Asia/Dhaka the page opens on the local date and lists that day's entries |

### QOP-015 — The check-in modal hides appointments the API would accept

| Field | Value |
|---|---|
| Feature | QUE-001 |
| Finding | QOP-015 |
| Severity | LOW — a desk can still check in via `/appointments`, but the queue page (the daily board) cannot |
| Expected | The queue page offers every appointment the server will accept for check-in |
| Actual | The modal filters to `status === 'CONFIRMED'`; the API accepts `BOOKED`, `AWAITING_CONFIRMATION`, `CONFIRMED` and idempotent `CHECKED_IN`. A `BOOKED` appointment is therefore invisible in the queue page's picker and yields “no options” |
| Evidence | `frontend/pages/queue.js:137, 200`; `main.py:75, 231-238` |
| Tests | None for the filter; `test_check_in_creates_entry` uses a `CONFIRMED` fixture |
| Test status | TEST COVERAGE GAP |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Filter on the same set the server accepts (ideally from a server field), and show patient name + slot rather than an id substring |
| Dependencies | None |
| Acceptance | An appointment in any check-in-able state appears in the modal; one in a terminal/post-queue state does not |

### QOP-016 — Two overlapping recovery paths with different rules

| Field | Value |
|---|---|
| Feature | QUE-004 |
| Finding | QOP-016 |
| Severity | LOW — behaviour is correct in both paths, but the semantics and audit vocabulary diverge with no recorded rationale |
| Expected | One documented way to bring a skipped patient back |
| Actual | `PATCH /queue/{id} {action:"reinsert"}` (`queue.manage`) and `POST /queue/{id}/recover` (`queue.recover`) both move `skipped → waiting`; the first does not renumber, does not require a reason and audits `queue.reinsert`; the second renumbers, can require a reason and audits `queue.recover`. The UI exposes only Recover |
| Evidence | `main.py:380-393, 395-467`; `recovery.py:192-281`; `queue.js:182-186` |
| Tests | `test_recover_renumbers_queue_and_keeps_token` (recover); no test for `reinsert` |
| Test status | TESTED for one path only |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Remove `reinsert` from the public action set (or document it as an administrative escape hatch) so the recovery module is the single authority |
| Dependencies | QOP-007 |
| Acceptance | Exactly one supported path from `skipped` to `waiting`, covered by a test, with one audit action name |

### QOP-017 — Queue actions are not constrained to the operational day

| Field | Value |
|---|---|
| Feature | QUE-004 |
| Finding | QOP-017 |
| Severity | LOW — a stale entry from a previous day can still be called or completed, extending a queue nobody is serving |
| Expected | State transitions apply to today's queue (or an explicitly selected day with a documented purpose) |
| Actual | `queue_action` and the recovery routes load the entry by id and status only; `entry.date` is never compared with `operational_today()`. The UI defaults to today but the API accepts any date's entry |
| Evidence | `main.py:395-467`; `recovery.py:143-281` |
| Tests | None covers a stale date |
| Test status | TEST COVERAGE GAP |
| Browser status | N/A |
| Privacy/security | None |
| Remediation | Reject transitively-served actions on entries whose date is not the facility's operational day (422 with a clear message), unless the request explicitly targets a historical day under an administrative capability |
| Dependencies | QOP-010 (a refreshed list would also surface stale rows) |
| Acceptance | Acting on yesterday's `waiting` entry returns `422`; the rule is tested and named |

### QOP-018 — `queue_history` closes its session twice

| Field | Value |
|---|---|
| Feature | QUE-003 (code hygiene) |
| Finding | QOP-018 |
| Severity | LOW — no functional impact (`Session.close()` is idempotent), but it indicates an unreviewed edit in a security-sensitive file |
| Expected | One `finally: session.close()` per handler, as in every other route |
| Actual | `finally: session.close()` appears twice at the end of `queue_history` |
| Evidence | `backend/queuing/main.py:584-585` |
| Tests | `TestQueueHistoryBranchAuth` still passes |
| Test status | TESTED (green despite the defect) |
| Browser status | N/A |
| Privacy/security | None directly; a double-close in a handler that mixes audit and queue data invites copy-paste of the mistake |
| Remediation | Delete the duplicate line |
| Dependencies | None |
| Acceptance | One close per handler; a lint rule or review checklist prevents recurrence |

### QOP-019 — The catalogue's queue rows no longer describe the tree

| Field | Value |
|---|---|
| Feature | QUE-001…QUE-005 (documentation accuracy) |
| Finding | QOP-019 |
| Severity | MEDIUM — the artefact the Product Owner signs understates the implementation and names a non-existent endpoint and permission |
| Expected | Catalogue status rows and API references match the working tree |
| Actual | (a) `POST /api/v1/queue/action` is documented; the route is `PATCH /api/v1/queue/{entry_id}`. (b) Check-in is documented as requiring `queue.checkin`; it requires `appointment.check_in` (owner decision Q3). (c) QUE-001…QUE-005 are recorded `PARTIALLY IMPLEMENTED` with R-01…R-04 open, while the tree contains the P0-1…P0-5 and RBAC-R1/R3/C1/C2 fixes plus 38 dedicated branch/ownership tests |
| Evidence | `AMSDP_MVP_Feature_Catalogue…:386-390, 415-419, 443-447, 489-511, 536-540, 1251-1255, 1334-1338`; `main.py` inline comments `P0-1`, `P0-2`, `P0-3`, `P0-5`, `RBAC-R1`, `RBAC-R3`, `C1`, `C2` |
| Tests | The tests that prove the fixes: `TestQueueBranchAuthorization` (8), `TestQueueEnqueueBranchOwnership` (7), `TestQueueDoctorAssistantOwnership` (6), `TestQueueHistoryBranchAuth` (7), `TestQueueMissingDoctorAssignment` (3), `TestQueueRecoveryDoctorAuth`, `TestQueueMultiDoctorAssignments` (6) |
| Test status | TESTED |
| Browser status | N/A |
| Privacy/security | None; a stale document can cause a future agent to “fix” what is already fixed, or to trust a permission that no longer gates the route |
| Remediation | Reconcile the catalogue rows (endpoint, permission, status, known gaps) in one documentation task, and record it in the docs index |
| Dependencies | Owner review of the wording; no code change |
| Acceptance | Every statement in QUE-001…QUE-005 matches the tree, and the F.4 row for each feature is accurate at the commit being accepted |

---

## Section 5 — DQDS Findings (DQDS-001)

Finding identifiers use the prefix **DQD-** deliberately: `DQDS-001` is the feature ID, and reusing it for findings would make the register ambiguous.

### 5.1 DQDS-001 acceptance matrix (catalogue's five criteria)

| Criterion | Verdict | Evidence |
|---|---|---|
| Returns board data for a valid org+branch | PASS (API) | `test_dqds_active_queue`, `test_dqds_empty_queue`; SEQ_02 §9 live `200` |
| 404 for unknown or non-active org/branch, never 403 | PASS | `test_dqds_unknown_org_404`, `test_dqds_unknown_branch_404`, `test_dqds_cross_org_404`, `test_dqds_inactive_org_404`, `test_dqds_inactive_branch_404`, `test_dqds_not_found_is_non_disclosing_and_uncacheable`; live §9 |
| Rate-limit headers present on responses | **PARTIAL** | Present on `200` and `429`; a `404` raised by `_not_found()` carries only `Cache-Control: no-store` because the limiter's headers are attached to the returned response, not to the exception |
| No patient PII in the response | PASS | `test_dqds_no_pii`, `test_dqds_no_internal_helpers_leak`, `test_dqds_never_returns_tracking_material`; payload is an explicit allow-list |
| Only active statuses shown (`waiting`, `called`, `in_consultation`, `skipped`) | PASS | `_ACTIVE` (`display.py:83`); `test_dqds_non_active_excluded`, `test_dqds_idle_doctor_not_listed` |

So DQDS-001 as *written in the catalogue* is essentially satisfied. The findings below are against the **Business Rules §33** definition of DQDS (C-1 / OD-4) and against the operational requirements in the task brief — a television in a waiting room, in Bangla, showing which room to go to, on the right day.

### DQD-001 — The board's “today” is the server's date, not the facility's

| Field | Value |
|---|---|
| Feature | DQDS-001; BR §33.5; BR §8 |
| Finding | DQD-001 |
| Severity | HIGH — for six hours of every Dhaka day the public board shows the **previous** day's queue |
| Expected | The board's day is the facility-local operational day, as everywhere else in the platform (`operational_today(session, org.id)`) |
| Actual | `today = date.today()` inside `get_queue_display` — the container's local date. The queuing container runs with the host/UTC default; at 00:00–05:59 Asia/Dhaka the UTC date is still the previous day, so entries filed under the local day are invisible and yesterday's still-active entries are advertised |
| Evidence | `backend/queuing/display.py:138`; `backend/common/timeutil.py:1-18, 59-61`; contrast `main.py:222` (`operational_today`) for enqueue |
| Tests | `test_dqds_timezone_today_only` asserts only that a `TODAY + 1` row is excluded, using the same `date.today()` baseline, so it cannot detect the defect |
| Test status | TEST PASSES — and is blind to the bug (a false-negative test) |
| Browser status | BROWSER UNVERIFIED (no browser run at either side of local midnight) |
| Privacy/security | The board leaks continuity of yesterday's queue state (tokens and counts) into a new day; no PII, but operationally misleading in a waiting room |
| Remediation | Replace `date.today()` with `operational_today(session, org.id)` after the org is resolved, and add a test that injects a fixed clock/zone and asserts the boundary |
| Dependencies | None; `timeutil` already exists |
| Acceptance | With the process in UTC and the facility in Asia/Dhaka, a 01:00 local request returns the local day's entries; a regression test proves today ≠ UTC-date at that boundary |

### DQD-002 — The board cannot show a room, because a queue entry has no room

| Field | Value |
|---|---|
| Feature | DQDS-001; BR §33.1, §33.7, §33.9; PQV §B (“one or more doctors/rooms”) |
| Finding | DQD-002 |
| Severity | HIGH — a token without a destination does not complete the waiting-room task in a multi-room facility |
| Expected | The board shows the serving token **and** where to go (room/chamber), and supports several rooms per branch |
| Actual | `QueueEntry` carries `branch_id` and `doctor_id` only; schedules have `room_id` (`common/models.py:555`), the queue does not. The payload has `doctor_name`, `currently_serving`, `patients_waiting`; the page renders no room. There is no way to derive the room at the queue level without a new association |
| Evidence | `common/models.py:854-873`; `display.py:176-183`; `queue-display/[org]/[branch].js:183-201` |
| Tests | `test_dqds_active_queue` asserts the exact payload keys — a room field would currently fail that test |
| Test status | TESTED for the current shape |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | Room is facility information, not patient data; adding it does not widen PII exposure |
| Remediation | Add a room association at check-in (from the appointment's schedule session, or a facility default) and publish `room_name` in the allow-list; the migration must be forward-only and nullable for historic rows |
| Dependencies | OD-4 (scope) and QOP-009 (room-scoped numbering) touch the same model change; coordinate them into one migration |
| Acceptance | A board for a two-room branch shows each serving token with its room; a queue entry with no room renders “—” and does not break the layout; the DQDS payload still contains no PII |

### DQD-003 — One board per branch; no display configuration or registry

| Field | Value |
|---|---|
| Feature | BR §33.2, §33.3 (multiple displays per branch, each configured for rooms/doctors/queues); PQV §B (multi-display “part of the same scope”) |
| Finding | DQD-003 |
| Severity | MEDIUM — a large hospital with per-floor screens cannot configure them; the catalogue's DQDS-001 does not require it, so this is scope-dependent (OD-4) |
| Expected | A facility can register displays and choose which doctors/rooms each shows |
| Actual | The only public route is `/queue-display/{org}/{branch}` → one board showing every active doctor in the branch. There is no display entity, no filter parameters (`doctor_id`, `room_id`), no configuration, no naming, no revocation |
| Evidence | `display.py:127-201`; `queue-display/[org]/[branch].js` (no query parameters except `?lang=`) |
| Tests | None (no multi-display concept to test) |
| Test status | NOT IMPLEMENTED |
| Browser status | N/A |
| Privacy/security | A per-display filter must remain server-side (a client-side filter would ship the whole branch's data to a public URL) |
| Remediation | Introduce a display configuration (id, label, org, branch, doctor/room filter) stored on `organizations.config` or a table, and accept a display id in the public route; keep the current branch-wide route as the default display |
| Dependencies | OD-4; DQD-002 (room filter needs rooms) |
| Acceptance | Two displays in one branch can show different doctor/room subsets without either receiving data outside its filter |

### DQD-004 — Presentation is app-scale, not television-scale

| Field | Value |
|---|---|
| Feature | BR §33.6 (“large readable typography suitable for television/waiting areas”), §33.8 (current token + relevant doctor/room information) |
| Finding | DQD-004 |
| Severity | MEDIUM — the board is legible on a laptop, marginal at 3 m on a TV |
| Expected | Token and doctor/room readable from the far side of a waiting room; a layout that uses the screen |
| Actual | `.dqds-card { max-width:960px }`, `.dqds-token { font-size:1.4rem }` (~22 px), `.dqds-doc-name { 1rem }`, `.dqds-label { 0.72rem }`. The layout is a white card on a dark page, capped at 960 px regardless of viewport |
| Evidence | `frontend/styles/global.css:91-124` |
| Tests | None (no visual or snapshot test) |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED at any distance/resolution |
| Privacy/security | None |
| Remediation | Add a TV-scale mode (viewport-driven `clamp()` sizes, full-height rows, high-contrast token block) and verify at 1920×1080 and 1366×768 on a real screen |
| Dependencies | DQD-002 (room column) and DQD-008 (next-token list) change the layout — design them together |
| Acceptance | At 1920×1080 the serving token is readable at ≥5 m; long doctor names wrap or truncate without overlapping the token; a screenshot at both resolutions is recorded as verification evidence |

### DQD-005 — No estimated waiting time or countdown

| Field | Value |
|---|---|
| Feature | BR §33.8, §33.9, §53 (“countdown is labelled as an estimate”) |
| Finding | DQD-005 |
| Severity | MEDIUM — a required display element is absent; the capability to compute it already exists |
| Expected | The board may show an estimated reporting/waiting time, explicitly labelled an estimate, never a guaranteed consultation time |
| Actual | The payload has `patients_waiting` only. `common/notifications/hooks.py:96-124` already implements `expected_visit_time()` and `plan_reminder_time()` with the documented “estimate” semantics, but the DQDS does not use them |
| Evidence | `display.py:176-190`; `common/notifications/hooks.py:96-124` |
| Tests | `test_queue_change_replans_pending_reminder` covers the estimator for notifications only |
| Test status | TEST COVERAGE GAP for DQDS |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | An estimate is aggregate; it must not be derived from another patient's identity |
| Remediation | Publish a per-doctor estimated wait (average service minutes × waiting count, facility-configurable) with an explicit “estimate” label, reusing the existing estimator |
| Dependencies | OD-4 (whether this is Phase 3 or later); `AMSDP_AVG_SERVICE_MINUTES` already exists |
| Acceptance | The board shows “~N min (estimate)” per doctor; the label is present in both languages; the value never claims a guaranteed time |

### DQD-006 — Display language is a per-TV setting, not a facility setting

| Field | Value |
|---|---|
| Feature | BR §33.4 (“display language configurable as Bangla or English”), §53 |
| Finding | DQD-006 |
| Severity | MEDIUM — the requirement is facility configuration; the implementation is a browser preference |
| Expected | The facility (or the display's configuration) determines the board's language; a display does not silently switch because someone pressed a button or because a staff session had a different locale |
| Actual | `?lang=` query → `localStorage['dqds_locale']` → `sessionStorage['locale']` (staff preview) → `'bn'`. Nothing is read from the organization, and the toggle writes only to that device |
| Evidence | `queue-display/[org]/[branch].js:31-84, 152-156`; `display.py` returns no language field; `organizations.locale` exists (`common/models.py:38`) and is unused here |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Add a display language preference to the display/facility configuration and return it from the board endpoint; keep `?lang=` as an operator override with documented precedence |
| Dependencies | OD-4; DQD-003 (per-display configuration) shares the storage decision |
| Acceptance | Two displays in one branch can be configured to different languages without touching the device; clearing browser storage does not change the board's language; `?lang=` still overrides for a preview |

### DQD-007 — The limiter is per-process and blind to a proxy

| Field | Value |
|---|---|
| Feature | DQDS-001 (rate limiting), task §6.2 |
| Finding | DQD-007 |
| Severity | MEDIUM — the control is a DoS brake, but it degrades silently in the deployment shape AMSDP is heading for |
| Expected | 30 req/min per client across the deployment, keyed on a trustworthy client identity |
| Actual | `_DQDS_RATE` is a module-level dict, so N uvicorn workers/replicas allow N×30; the key is `request.client.host`, which behind any reverse proxy or facility NAT is either the proxy's address (all displays share one bucket) or an untrusted forwarded value (if later added without a trusted-proxy rule) |
| Evidence | `display.py:30-78`; acknowledged in SEQ_02 §11.1 and the catalogue's known-gaps cell |
| Tests | `test_dqds_rate_limit`, `test_dqds_rate_limit_headers` |
| Test status | TESTED for the single-process case |
| Browser status | N/A |
| Privacy/security | A public endpoint whose only brake can be bypassed by scale-out; over-limiting a NAT would blank the board for a whole facility |
| Remediation | Move to a shared limiter (Redis/Postgres token bucket) before more than one worker, and key on a configured trusted client address or a per-display identifier |
| Dependencies | DQD-003 (display identities would make keying natural) |
| Acceptance | The limit holds across two worker processes; a documented proxy configuration yields one bucket per real client |

### DQD-008 — Only the serving token is published; there is no “next” information

| Field | Value |
|---|---|
| Feature | BR §33.1 (“current queue/token information for multiple doctors and rooms”) |
| Finding | DQD-008 |
| Severity | MEDIUM — waiting patients cannot tell how close they are, and the board cannot show a short “up next” strip |
| Expected | Current token plus, at the facility's discretion, the next few tokens |
| Actual | Queued tokens are never published (a deliberate privacy decision, SEQ_02 §11.3/M9 §15.3); only `currently_serving` and a count |
| Evidence | `display.py:156-183`; SEQ_02 §11.2–§11.3 |
| Tests | `test_dqds_serving_prefers_in_consultation`, `test_dqds_skipped_never_shown_as_serving`, `test_dqds_no_pii` |
| Test status | TESTED (as designed) |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | Showing a *sequence* of tokens is not PII (no names), but a facility that is the only one operating could infer individuals; the decision must be explicit and configurable, not implicit |
| Remediation | Add a facility-configurable “show next N tokens” option (default off) and document the privacy reasoning; keep names out of the payload unconditionally |
| Dependencies | OD-4 |
| Acceptance | With the option off, the payload is unchanged; with it on, up to N upcoming tokens appear with no patient data |

### DQD-009 — Nothing in the product opens, registers or disables a display

| Field | Value |
|---|---|
| Feature | DQDS-001 (operability), BR §33.2 |
| Finding | DQD-009 |
| Severity | MEDIUM — a facility cannot find or manage its board without knowing the URL shape; a leaked or retired screen cannot be switched off |
| Expected | An administrator can see the display URL (and ideally a QR/link), copy it to the TV, and disable a display |
| Actual | `grep -rn 'queue-display' frontend --include=*.js` finds the page's own route parser and nothing else — no navigation entry, no link from the queue page, no settings screen, no enable/disable. Disabling the whole branch (`Branch.status`) is the only way to kill a board, and that also breaks staff operations |
| Evidence | `frontend/components/AppShell.js` (no DQDS entry); frontend grep |
| Tests | None |
| Test status | NOT IMPLEMENTED |
| Browser status | N/A |
| Privacy/security | No revocation path for a public URL |
| Remediation | Add a “Displays” panel (org/branch admin) showing the board URL, a copy/QR affordance and an enable/disable toggle; add a link from `/queue` |
| Dependencies | DQD-003 (a display entity is the natural place for enable/disable) |
| Acceptance | An admin can open settings, copy the URL, open it in a new tab, and disable it; a disabled display returns the same non-disclosing 404 |

### DQD-010 — `404` responses carry no rate-limit headers

| Field | Value |
|---|---|
| Feature | DQDS-001 acceptance (“rate-limit headers present on responses”) |
| Finding | DQD-010 |
| Severity | LOW — the acceptance criterion is arguably unmet for error responses; no functional loss |
| Expected | Every response the limiter touches is signalled, so a monitoring probe can reason about refusal |
| Actual | `_rate_headers()` values are merged only into the `200` `Response`; `_not_found()` raises `HTTPException` with `Cache-Control: no-store` alone |
| Evidence | `display.py:41-47, 96-106, 193-197` |
| Tests | `test_dqds_not_found_is_non_disclosing_and_uncacheable` asserts `no-store`, not the absence of rate headers |
| Test status | TESTED (current behaviour is asserted) |
| Browser status | N/A |
| Privacy/security | None |
| Remediation | Attach the limiter headers to the 404 path too (or amend the criterion to say which responses must carry them) |
| Dependencies | None |
| Acceptance | A 404 carries `X-RateLimit-*` and stays byte-identical across the three not-found causes |

### DQD-011 — The public token embeds part of the doctor's internal id

| Field | Value |
|---|---|
| Feature | DQDS-001 (no internal identifiers), QUE-006 (speakable token) |
| Finding | DQD-011 |
| Severity | LOW — no personal data is revealed, but an internal key fragment is broadcast on a public surface and the string is not human- or speech-friendly |
| Expected | A public token is a short, facility-configurable, speakable label (e.g. `A-014`); internal ids stay internal |
| Actual | `token_for()` returns `T-<doctor_id[:6] upper>-<serial:03d>`; the doctor id is a UUID, so the board shows strings such as `T-3F2A9C-001` |
| Evidence | `common/queue_tokens.py:33-35`; DQDS payload `currently_serving` |
| Tests | `test_check_in_creates_entry` asserts `token.startswith("T-")`; nothing asserts the absence of id material |
| Test status | TESTED for format, not for disclosure |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | A stable fragment of a primary key on a public board; low sensitivity, but it contradicts the “no internal identifiers” principle in task §6.2 |
| Remediation | Make the token prefix a facility setting (or a doctor-level short code) with a safe default, and never derive it from the primary key; coordinate with QOP-009 |
| Dependencies | OD-7; ANN-007 (announcement wording) |
| Acceptance | Tokens contain no database identifier; a facility can set a prefix; printed and displayed tokens still match (BR §31.6) |

### DQD-012 — The board keeps a private copy of the bilingual strings

| Field | Value |
|---|---|
| Feature | L10N-001 consistency; DQDS |
| Finding | DQD-012 |
| Severity | LOW — deliberate and documented (SEQ_02 §5, §11.4), but it is a second source of truth for Bangla/English wording |
| Expected | One place defines user-visible strings, or the duplication is justified per string |
| Actual | `const L = { bn: {...}, en: {...} }` inside the page, with keys (`tl`, `lq`, `er`, `ee`, `og`, `br`, `dr`, `now`, `wt`, `noq`, `none`, `up`, `nf`, `nf2`, `nt`, `sv`, `off`) that do not exist in `lib/i18n.js` |
| Evidence | `queue-display/[org]/[branch].js:43-62`; `frontend/lib/i18n.js` (no `dqds` namespace) |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED (the Bangla render has never been checked in a browser) |
| Privacy/security | None |
| Remediation | Either move the strings into `lib/i18n.js` under a `dqds` namespace or record the exception in the L10N note so the next change cannot half-translate the board |
| Dependencies | DQD-006 (language source) |
| Acceptance | Every board string exists in both languages in one authoritative location; a missing key fails a test rather than rendering a raw key |

### DQD-013 — No frontend or browser test touches the board

| Field | Value |
|---|---|
| Feature | DQDS-001 verification |
| Finding | DQD-013 |
| Severity | MEDIUM — the endpoint is well tested; the page that a facility actually puts on a wall is not |
| Expected | At least a rendering test for the five states (loading, ready, empty, not-found, stale) and a recorded browser run |
| Actual | `frontend/tests/` contains 16 pure-Node tests for library modules; none imports `pages/queue-display/[org]/[branch].js`. SEQ_02 §11.5 states there is no browser/E2E harness in the repo and that the page is covered only by `next build` + endpoint tests |
| Evidence | `frontend/tests/` listing; `frontend/package.json` (`node --test tests/*.test.mjs`); SEQ_02 §10–§11 |
| Tests | None |
| Test status | NO TEST COVERAGE for the page |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | A regression that accidentally rendered a patient name would not be caught by any test on the page |
| Remediation | Add page-level tests by extracting the state machine/data mapping into a testable module (the page currently mixes route parsing, polling and rendering), and perform one recorded browser run per resolution |
| Dependencies | DQD-004 (layout work will touch the same code) |
| Acceptance | A failing endpoint or a 404 produces a visible, localized state in a test; a browser screenshot set is attached to the DQDS completion report |

### DQD-014 — A public board URL cannot be revoked

| Field | Value |
|---|---|
| Feature | DQDS-001 (privacy), task §6.2 |
| Finding | DQD-014 |
| Severity | LOW — the data is deliberately public and token-only, so the exposure is bounded; the *control* is missing |
| Expected | A facility can rotate or revoke a board address (or at least disable it) if a link is shared outside the premises |
| Actual | The address is `/{org_code}/{branch_code}` — stable, guessable within an org, and identical for every board of that branch. There is no display secret, no rotation, and no disable (DQD-009) |
| Evidence | `display.py:108-121, 127-201`; `Organization.code`, `Branch.code` are stable identifiers |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | N/A |
| Privacy/security | Bounded: the worst case is that an outsider sees doctor names, token numbers and counts for one branch. Acceptable only as an explicit, recorded decision |
| Remediation | Record the acceptance decision (OD) and, when displays are introduced (DQD-003), give each display a revocable identifier |
| Dependencies | OD-4; DQD-003 |
| Acceptance | Either the owner records that a stable public URL is acceptable, or displays get identifiers that can be disabled |

---

## Section 6 — QUE-006 Findings (Intelligent Queue Voice Announcements, Bangla/English)

### 6.1 QUE-006 acceptance matrix (the catalogue's ten criteria)

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Bangla announcement produced for a call event when Bangla is configured | **NOT MET** | No speech code, no configuration, no call event hook |
| 2 | English announcement produced for a call event when English is configured | **NOT MET** | As above |
| 3 | Announcement language configurable per facility | **NOT MET** | No configuration key |
| 4 | Announcements can be enabled/disabled per facility | **NOT MET** | No configuration key |
| 5 | Announcements triggered by appropriate queue events | **NOT MET** | `call` exists as an API action but nothing observes it (and it is not reachable from the UI — QOP-001) |
| 6 | No duplicate or conflicting announcements for the same event | **NOT MET** | Nothing exists to suppress; no event identity |
| 7 | Voice-output failure does not fail or interrupt the queue call | **VACUOUSLY TRUE** | No audio is attempted, so nothing can fail — but the property is undesigned, not proven |
| 8 | Only authorized roles (org/branch admin) may configure announcements | **NOT MET** | No configuration surface; the branch-level authority question is also unresolved (OD-2) |
| 9 | Spoken announcements contain no unnecessary patient PII | **NOT MET (undesigned)** | No template exists to review; the token and doctor name are the intended content |
| 10 | Actual audio output verified at browser/runtime before implementation is claimed | **NOT MET** | No browser audio run has ever been recorded |

Ten of ten acceptance criteria are unmet. This is not a coverage gap: the feature does not exist.

### ANN-001 — No announcement capability of any kind

| Field | Value |
|---|---|
| Feature | QUE-006 |
| Finding | ANN-001 |
| Severity | HIGH — the only Phase 3 capability with zero implementation; owner-approved Core scope |
| Expected | A call event can produce an audible Bangla or English announcement inside the facility, when the facility has enabled it |
| Actual | No TTS call, no audio asset, no provider, no announcement service, no event, no configuration, no UI, no test. A repository grep for `speechSynthesis`, `SpeechSynthesisUtterance`, `announce`, `text-to-speech`, `tts` and `voice` over `backend/`, `frontend/` and `docker-compose.yml` returns only accessibility comments, a symptom name and a compiled chunk |
| Evidence | repository grep; `AMSDP_MVP_Feature_Catalogue…:544-581, 1266`; `AMSDP_QUE-006_…_Catalogue_Addition_V1.0.md` §4 |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED (nothing to play) |
| Privacy/security | No exposure today; the design must forbid patient names/mobiles in the spoken text |
| Remediation | Implement Stages 3.3 in full (see Section 11) |
| Dependencies | QOP-001 (a reachable call action), ANN-002 (event), ANN-004 (config), OD-1 (delivery mechanism) |
| Acceptance | Criteria 1–10 in §6.1, each with named evidence |

### ANN-002 — There is no announcement event contract

| Field | Value |
|---|---|
| Feature | QUE-006 (trigger, duplicate prevention, ordering) |
| Finding | ANN-002 |
| Severity | HIGH — without an event identity, duplicate suppression, retry and ordering cannot be specified, let alone implemented |
| Expected | A queue action emits an event with a stable id (e.g. `queue_entry_id` + action + revision), a monotonic ordering key, and enough payload (org, branch, doctor, room, token, language) for a consumer to announce exactly once |
| Actual | `queue_action` performs the transition, writes an audit row and calls `_notify("on_queue_changed", org, doctor, date, reason)`. There is no event id, no payload contract, no consumer, and the only durable transport is the SMS/WhatsApp outbox (`CHANNELS = ("whatsapp","sms")`) |
| Evidence | `main.py:395-467, 47-57`; `common/notifications/config.py:66`; `common/notifications/hooks.py:234-310` |
| Tests | `test_queue_ops_write_audit_events` proves the audit side only |
| Test status | NOT TESTED for any event contract |
| Browser status | N/A |
| Privacy/security | An event carrying patient identity would be a privacy defect; the contract must carry only token, doctor and room |
| Remediation | Define a queue-event contract (`queue.called`, `queue.recalled`, `queue.skipped`) with an idempotency key, emitted after commit, and a consumer that dedupes on that key |
| Dependencies | OD-1 (transport), QOP-003 (recall must exist to be announced) |
| Acceptance | Replaying the same event twice produces one announcement; two rapid calls produce two announcements in order; the payload contains no PII (assert it in a test) |

### ANN-003 — No Bangla/English speech strategy, and voice availability is unproven

| Field | Value |
|---|---|
| Feature | QUE-006 (criteria 1–2, 10) |
| Finding | ANN-003 |
| Severity | HIGH — the requirement is specifically Bangla **and** English audio; the mechanism that can deliver Bangla reliably in a Bangladeshi waiting room has not been chosen or tested |
| Expected | A decided mechanism (browser `speechSynthesis`, a configured TTS provider, or pre-generated audio), a documented Bangla/English voice path, and a recorded playback test on the target device |
| Actual | No mechanism. Nothing in the tree selects, configures or probes a voice; no document in `docs/` records a device/voice matrix; no browser run exists |
| Evidence | repository grep; `docs/implementation/AMSDP_QUE-006_…_Catalogue_Addition_V1.0.md` §11 (“TTS provider selection … future work”) |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED — and, critically, **Bangla voice availability cannot be assumed**. Web Speech voices are supplied by the OS/browser; a desktop Chrome install without a Bangla TTS engine has no `bn-BD` voice, and an Android TV/ChromeOS device may differ from a Windows kiosk. This must be measured per target device, not assumed |
| Privacy/security | A server-side provider would send the announcement text (token, doctor name) to a third party — the contract must exclude patient identity and the provider must be an approved dependency |
| Remediation | Decide the mechanism under OD-1; then build a capability probe (`speechSynthesis.getVoices()` matching `bn`/`en`) with an explicit, visible fallback (English-only, or a non-audio board prompt) and record a playback test per device class |
| Dependencies | OD-1, OD-3 (wording) |
| Acceptance | A written device/voice matrix exists; Bangla playback is demonstrated (video/screenshot + operator attestation) on the actual deployment device; the fallback path is demonstrated when no Bangla voice is present |

### ANN-004 — No configuration surface, and the branch-level authority question is open

| Field | Value |
|---|---|
| Feature | QUE-006 (criteria 3, 4, 8) |
| Finding | ANN-004 |
| Severity | HIGH — enable/disable and language are acceptance criteria, and the existing configuration mechanism is not used |
| Expected | `organizations.config["queue_announcement_config"]` (enabled, language, events, content toggles, volume/repeat policy) with a GET/PUT route modelled on `appointment_config`, audited with before/after, non-disclosing 404 for a foreign org, and an authorized role set |
| Actual | No key, no route, no UI, no audit. `organizations.config` holds only `notification_config` and `appointment_config` |
| Evidence | `backend/organization/appointment_config.py` (the pattern); `common/notifications/config.py` (the JSON shape); `organizations.config` column |
| Tests | `test_org_admin_reads_and_updates_notification_config`, `test_branch_admin_cannot_read_notification_config`, `test_cross_org_notification_config_is_non_disclosing_404` — the pattern is already tested for notifications, not for announcements |
| Test status | NOT IMPLEMENTED |
| Browser status | N/A |
| Privacy/security | Configuration must be server-authorized (`org.read`/`org.manage`); the existing notification precedent denies `branch_admin`, which conflicts with the catalogue's “`branch_admin` (configure)” expectation — a genuine ownership question (OD-2) |
| Remediation | Add the config key + route + validation + audit, reusing the appointment-config shape; resolve branch-level authority under OD-2 |
| Dependencies | OD-2 |
| Acceptance | An org admin can enable announcements, choose Bangla/English and choose events; the change is audited with before/after; an unauthorized role is refused server-side; a foreign org gets 404 |

### ANN-005 — No duplicate, ordering, retry or playback-state design

| Field | Value |
|---|---|
| Feature | QUE-006 (criterion 6; task §7.5) |
| Finding | ANN-005 |
| Severity | HIGH — “no duplicate or conflicting announcements” is an acceptance criterion, and none of the concurrency shapes that produce duplicates has a designed answer |
| Expected | A specified answer for: rapid successive calls, recall, two operators on one doctor, several doctors announcing simultaneously, browser refresh, reconnection, repeated delivery of the same event, delayed delivery, and a second announcement arriving while one is playing |
| Actual | No queue for playback, no in-progress guard, no dedupe key, no priority, no coalescing rule, no cancellation of a superseded announcement |
| Evidence | No audio code exists; the only comparable design in the tree is the notification outbox's cooldown (`COOLDOWN_MINUTES`, `common/notifications/config.py:70-71`), which is per appointment+channel and not per queue event |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Specify and implement a single-consumer announcement queue keyed by event id, with: skip-if-same-event, queue-if-different (FIFO), coalesce-bursts-per-token (optional), and drop-on-superseded (recall replaces the earlier call for the same entry) |
| Dependencies | ANN-002 (event identity), QOP-003 (recall) |
| Acceptance | A burst of the same event produces one announcement; two different calls produce two, in order; a recall for entry X does not interrupt an announcement for entry Y mid-sentence unless the policy says so (and then it is tested) |

### ANN-006 — Autoplay, permissions and “audio disabled” are undesigned

| Field | Value |
|---|---|
| Feature | QUE-006 (criterion 7; task §7.6) |
| Finding | ANN-006 |
| Severity | MEDIUM — the queue is safe today only because no audio is attempted; once audio exists, the failure modes must not reach the queue path or the operator |
| Expected | A display/announcement client that unlocks audio on a user gesture, survives a muted TV or a missing voice, reports “audio off” to the operator, and never blocks or fails a queue action |
| Actual | No audio element, no unlock gesture, no muted-state indicator, no permission flow. Browser autoplay policies and audio-permission denial are unaddressed |
| Evidence | No audio code; DQDS page has no audio affordance |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | None |
| Remediation | Design the announcement client so the queue never awaits it: server writes the event; the client announces best-effort; the operator sees an “audio disabled/unavailable” badge with a one-click enable; queue actions are unchanged either way |
| Dependencies | OD-1 (mechanism determines where this lives) |
| Acceptance | With audio blocked, `call` still returns `200`, the board still updates, and the operator sees a visible audio-off state; the failure is logged |

### ANN-007 — Content, wording and pronunciation are unspecified

| Field | Value |
|---|---|
| Feature | QUE-006 (criterion 9; task §7.3) |
| Finding | ANN-007 |
| Severity | MEDIUM — the announcement text is the product surface the patient hears; today there is no approved wording and the token itself is not speakable |
| Expected | An approved Bangla and English template (token + doctor + room where configured), an approved pronunciation convention for tokens and doctor names, and an explicit prohibition on patient name/mobile/clinical detail |
| Actual | The catalogue states the content intent; no template, no wording approval, no Bangla transliteration of doctor names, no speakable token. Doctor names are free text (`Doctor.name`), and the existing `BanglaNameSense` work covers **patient** names only |
| Evidence | `AMSDP_MVP_Feature_Catalogue…:558-570`; `doc.name` free text; `frontend/lib/bangla-name-sense/` scope |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | The template must guarantee no PII; the current token format (`T-3F2A9C-001`) would be read out character by character |
| Remediation | Obtain approved wording (OD-3), define a read-aloud token form (numeric serial with the facility prefix), and decide whether doctor names are spoken as written or via a per-doctor pronunciation field |
| Dependencies | OD-3; QOP-009 / DQD-011 (token format) |
| Acceptance | The exact Bangla and English strings are recorded and approved; a playback test demonstrates the token is intelligible; no template field can carry patient identity |

### ANN-008 — Announcement attempts and failures are not observable

| Field | Value |
|---|---|
| Feature | QUE-006 (task §7.6 “visible or logged”), BR §40 |
| Finding | ANN-008 |
| Severity | MEDIUM — a facility whose announcements silently stopped would have no way to know |
| Expected | Each announcement attempt (event id, language, outcome, duration, failure reason) is observable — an audit event and/or a structured log line — without recording patient identity |
| Actual | The queue action is audited (`queue.call`), but nothing records whether an announcement was attempted, played, blocked or failed. The audit trail is append-only and persistent (correct), and the queue service installs token redaction and denial auditing, so the mechanism exists to record this safely |
| Evidence | `main.py:44-57, 395-467`; `common/audit.py` usage; no announcement audit action exists |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | N/A |
| Privacy/security | Any log/audit record must contain the token and doctor only — never the patient |
| Remediation | Emit `queue.announcement.played` / `.failed` / `.skipped` with the event id and reason; surface a “last announcement” indicator to the operator |
| Dependencies | ANN-002 |
| Acceptance | A blocked-autoplay run leaves a retrievable record; a successful run leaves one too; neither contains PII |

### ANN-009 — No test or verification plan exists for QUE-006

| Field | Value |
|---|---|
| Feature | QUE-006 |
| Finding | ANN-009 |
| Severity | MEDIUM — the ten acceptance criteria have no test mapping, so “done” cannot be demonstrated when work starts |
| Expected | Named tests for: Bangla playback, English playback, token pronunciation, doctor/room content, recall, disabled configuration, duplicate prevention, concurrent events, audio failure, autoplay restriction |
| Actual | Zero tests of any kind; the catalogue records `NOT TESTED`; no verification plan exists in any document |
| Evidence | `AMSDP_MVP_Feature_Catalogue…:579`; repository test inventory |
| Tests | None |
| Test status | NOT TESTED |
| Browser status | BROWSER UNVERIFIED |
| Privacy/security | A privacy test for the spoken payload is part of the missing plan |
| Remediation | Write the test map in Stage 3.3 before implementation (unit tests for the config/event/dedupe logic, plus a recorded browser playback matrix) |
| Dependencies | ANN-002, ANN-004 |
| Acceptance | Every acceptance criterion maps to a named test or a recorded browser step; the map is reviewed before coding starts |

### ANN-010 — Volume, repeat and voice selection are undefined

| Field | Value |
|---|---|
| Feature | QUE-006 (task §7.4) |
| Finding | ANN-010 |
| Severity | LOW — optional configuration, but the catalogue calls the capability configurable, so the boundary must be stated |
| Expected | An explicit statement of what is configurable (volume, repeat count, voice) and what is out of scope, with a safe default |
| Actual | Nothing is specified. The catalogue requires enable/disable and language only; volume/repeat appear in the task brief as “if supported by the product requirements” |
| Evidence | `AMSDP_MVP_Feature_Catalogue…:550-571` |
| Tests | None |
| Test status | N/A |
| Browser status | N/A |
| Privacy/security | None |
| Remediation | Record the boundary in the QUE-006 implementation report; default volume to the device's own level, repeat once at most, and no voice selection in Phase 3 |
| Dependencies | OD-1, OD-3 |
| Acceptance | The Phase 3 scope statement lists exactly which knobs exist; nothing else is claimed |

---

## Section 7 — Security, Authorization and Privacy

This section answers a different question from Sections 4–6: not “is the feature complete?” but “can the feature that exists be trusted, and what would the missing parts have to preserve?” Every row was checked against the code, not the documentation.

| Aspect | Verdict | Evidence | Residual risk |
|---|---|---|---|
| Tenant isolation (queue) | **SOUND** | Every query filters `QueueEntry.organization_id == auth.organization_id`; `_scoped_entry_or_404` (`main.py:104-117`) and `_scoped_entry` (`recovery.py:78-95`) both join on org; tests `test_cross_org_entry_not_found`, `test_rbac_r1_org_admin_cannot_enqueue_foreign_org_branch`, `test_c1_org_admin_other_org_branch_denied`, `test_recovery_cross_branch_and_cross_org_are_404` | None found |
| Cross-tenant response semantics | **SOUND** | A foreign or missing row is `404` in every path (`_scoped_entry_or_404`, `_scoped_entry`, `branch_accessible`); no queue route returns `403` for a scope failure. (`recovery.py:112-114` returns `403` for a *permission* shortfall — `queue.reposition` — which is a capability decision, not a tenant decision, and matches BR §54) | The 403-on-permission vs 404-on-scope split should stay documented so a future edit does not convert one into the other |
| Branch isolation (queue) | **SOUND, one exception** | List (`main.py:129-142`), check-in (`main.py:189-206`), enqueue (`main.py:311-324`), action (`main.py:110-116`), history (`main.py:565-581`), reorder homogeneity (`main.py:472-496`) | **QOP-007**: `_active_queue()` in the recovery path is org+doctor+date, not branch, so a recovery renumbers another branch's rows |
| Doctor ownership | **SOUND** | `auth.can_access_doctor(doctor_id)` on list, history, check-in, enqueue, every action and recovery; fails closed when `auth.doctor_id` is unset (`TestQueueMissingDoctorAssignment`) | QOP-002 will widen *action* capability; the ownership check must remain the outer gate |
| Assistant assignments (multi-doctor) | **SOUND** | `staff_doctor_assignments` is authoritative; tests `test_assistant_assigned_to_multiple_doctors`, `test_assistant_cannot_access_unassigned_doctor`, `test_assignment_revocation_denies_access`, `test_revoked_legacy_doctor_id_does_not_restore_access`, `test_assistant_cannot_recover_or_confirm_missed_turn` | An assistant can check in (owner decision Q3) but cannot progress the queue; this is a workflow gap (INT-002), not a security gap |
| Receptionist access | **SOUND** | `queue.view/reorder/checkin/manage/recover/reposition` (`permissions.py:82-103`), branch-limited by token; `test_p0_*`, `TestQueueEnqueueBranchOwnership` | Holding both `queue.checkin` and `appointment.check_in` means the desk can create and advance a visit; that is the intended front-desk role |
| Public DQDS exposure | **SOUND (bounded)** | Allow-list payload; no ids; no patient data; inactive/unknown/cross-org indistinguishable; `test_dqds_no_pii`, `test_dqds_no_internal_helpers_leak`, `test_dqds_never_returns_tracking_material`, `test_dqds_cross_org_doctor_name_never_leaks` | Token strings embed a doctor-id fragment (DQD-011); the URL is stable and unrevocable (DQD-014); the limiter can be multiplied by scale-out (DQD-007) |
| Public DQDS and PII | **SOUND** | Response is `{organization, branch, doctors[{doctor_name, currently_serving, patients_waiting}], updated_at}` — no patient name, mobile, id, note or clinical field can be reached because they are never selected | A future “next tokens” or room addition must keep the allow-list discipline (DQD-002/DQD-008 acceptance) |
| Announcement privacy | **NOT APPLICABLE YET — design constraint** | No announcement code exists | ANN-007 requires an approved template with no patient identity; ANN-002 requires the event payload to exclude patient fields |
| Audit coverage (queue) | **SOUND** | `record_audit` on check-in, enqueue, each action, reorder, missed-turn and every renumber; `test_queue_ops_write_audit_events`; e2e `test_16` asserts `queue.checkin`, `queue.call`, `queue.start_consultation`, `queue.complete_consultation` | Reorder can record an empty reason (QOP-006); no announcement audit exists (ANN-008) |
| Denial recording | **SOUND** | `install_denial_audit(app, "queuing")` writes every 403/404/422 answered by the service; `install_token_redaction()` on startup | Every 404 produced by QOP-005/QOP-007's fixes must keep this behaviour |
| Public-board denial logging | **BY DESIGN, NONE** | `display.py` writes no audit event (SEQ_02 §11.6): there is no authenticated principal and no org derived from a token | If per-org abuse telemetry is required, it belongs to the limiter work (DQD-007) |
| Secrets | **NO EXPOSURE** | No TTS provider, no credentials, no key material in the queue or DQDS code paths | A future provider integration must follow the notification pattern (status-only reporting, credentials from environment, never in `organizations.config`) |

**Conclusion.** Nothing in the implemented queue/DQDS code weakens tenant isolation, branch scope, doctor ownership or public-board privacy. The two security-adjacent defects found are a *write-scope* defect (QOP-007) and an *identifier-hygiene* issue (DQD-011); neither is CRITICAL. The Phase 3 additions must inherit the same pattern: derive scope from the token, fail closed, return 404, audit the denial.

---

## Section 8 — Integration Findings

Target chain: **appointment/walk-in → check-in → queue token → queue action → DQDS update → audible announcement**.

### 8.1 Scenario verdicts

| Scenario | Verdict | Reasoning |
|---|---|---|
| **A — Individual doctor's chamber** (doctor alone) | **DEFECT CONFIRMED** (INT-001) | The doctor can check in their own patient (`appointment.check_in`, owner decision Q3) and start/complete a consultation, but cannot call (no `queue.manage`, no UI control), cannot recall, cannot reorder, and there is no announcement. The queue cycle cannot be completed by the person the model is built for |
| **B — Hospital with receptionist and assistants** | **PARTIALLY IMPLEMENTED** (INT-002) | The receptionist can check in, enqueue, reorder, cancel and complete the desk side — except the `call` action, which has no UI. The assistant can check in for assigned doctors but cannot progress the queue at all. Multiple doctor queues operate independently and are correctly scoped. The public board is correct per branch/branch |
| **C — Multiple branches** | **IMPLEMENTED — TEST COVERAGE GAP + one defect** (INT-003) | Branch scope is enforced and tested on every route (38 branch/ownership tests); DQDS is branch-path-scoped and cross-tenant 404s. But recovery renumbers across branches (QOP-007), and the DQDS day window is wrong for six hours a day (DQD-001), which is a branch-level operational failure |
| **D — Concurrent operations** | **PARTIALLY IMPLEMENTED — TEST COVERAGE GAP** (INT-004) | Token allocation is genuinely atomic (single UPSERT). Duplicate check-in has a race window (QOP-004). No automated concurrency test exists (QOP-013). DQDS reflects committed state, but only at 10 s granularity, and the queue page does not refresh at all (QOP-010) |
| **E — Audio failure** | **NOT IMPLEMENTED** (INT-005) | There is no audio to fail. “The queue continues” is true only because the capability is absent; the property is not designed or proven |

### INT-001 — Scenario A cannot complete the queue cycle

| Field | Value |
|---|---|
| Finding | INT-001 |
| Severity | HIGH |
| Expected | A solo doctor checks in, calls, consults, completes and recalls a patient, with the board updating and (when enabled) an announcement playing |
| Actual | Check-in and consultation work; call, recall, reorder and cancel do not (QOP-001, QOP-002, QOP-003); the announcement does not exist (ANN-001) |
| Evidence | `permissions.py:104-123`; `queue.js:173-186`; `main.py:400-403` |
| Status | DEFECT CONFIRMED |
| Remediation | QOP-001 + QOP-002 (+ QOP-003 for recall) close the functional part; QUE-006 closes the audible part |
| Dependencies | OD-5 (capability design) |
| Acceptance | The five-step journey in a single-operator chamber is executed end-to-end in a browser and recorded |

### INT-002 — Scenario B: the assistant is read-only for the queue

| Field | Value |
|---|---|
| Finding | INT-002 |
| Severity | MEDIUM |
| Expected | An assistant manages the assigned doctor's queue (call, skip, recover) as the doctor's delegate, subject to assignment scope |
| Actual | The assistant holds `queue.view` and `appointment.check_in` only; call/skip/recover/reorder are all refused. The queue page therefore shows them a table with no actions except the check-in modal (gated on `queue.manage`, so not even that) |
| Evidence | `permissions.py:123-135`; `auth.js:36`; `queue.js:144, 173-186` |
| Status | PARTIALLY IMPLEMENTED |
| Remediation | Decide whether the assistant is a queue operator (then grant the queue capabilities the facility permits, always behind `can_access_doctor`) or purely a check-in clerk (then say so in BR §7.5 and hide the empty action column) |
| Dependencies | OD-5 |
| Acceptance | The chosen model is stated in the Business Rules and enforced by tests; the UI matches it |

### INT-003 — Scenario C: branch correctness holds, with two exceptions

| Field | Value |
|---|---|
| Finding | INT-003 |
| Severity | MEDIUM |
| Expected | Branch A's queue never affects Branch B's bookkeeping; the board shows the right branch and the right day |
| Actual | Read/write scoping is correct on the queue routes, but recovery renumbers the doctor's entries across all branches (QOP-007), and the board's day is UTC-derived (DQD-001). A doctor working at two branches is the exact case that exposes both |
| Evidence | `recovery.py:97-110`; `display.py:138`; `TestQueueBranchAuthorization`, `test_dqds_other_org_isolation` |
| Status | IMPLEMENTED — TEST COVERAGE GAP (plus the two defects above) |
| Remediation | QOP-007 and DQD-001, each with a two-branch/clock-boundary test |
| Dependencies | None |
| Acceptance | A recovery at branch A leaves branch B untouched; at 01:00 Dhaka the board lists the local day |

### INT-004 — Scenario D: atomic tokens, a duplicate-check-in race, and no concurrency test

| Field | Value |
|---|---|
| Finding | INT-004 |
| Severity | MEDIUM |
| Expected | Concurrent operators cannot produce duplicate tokens or duplicate entries; the board converges on the committed state |
| Actual | Token allocation is atomic and correct. Duplicate check-in is check-then-insert with no constraint (QOP-004). No concurrency test exists (QOP-013). The board converges, but within 10 s and only for the correct day (DQD-001) |
| Evidence | `queue_tokens.py:38-56`; `main.py:202-213`; test inventory |
| Status | PARTIALLY IMPLEMENTED — TEST COVERAGE GAP |
| Remediation | QOP-004 (constraint/lock) + QOP-013 (tests) |
| Dependencies | QOP-004 |
| Acceptance | Two concurrent check-ins of one appointment yield one entry; N concurrent enqueues yield N unique tokens; both proven by a test, not a manual run |

### INT-005 — Scenario E: there is no audio path to degrade

| Field | Value |
|---|---|
| Finding | INT-005 |
| Severity | HIGH |
| Expected | With audio blocked or a Bangla voice missing, the call succeeds, the board updates, the failure is visible/logged, and the operator continues |
| Actual | No audio client exists, so the scenario cannot be exercised. The catalogue's criterion 7 (“failure does not interrupt the queue”) is satisfied only vacuously |
| Evidence | Repository grep; §6.1 row 7 |
| Status | NOT IMPLEMENTED |
| Remediation | ANN-006 design + ANN-008 observability, implemented in Stage 3.3, then verified by a blocked-audio browser run |
| Dependencies | ANN-001, OD-1 |
| Acceptance | A browser run with autoplay blocked shows: `call` 200, board updates, visible audio-off state, log entry, no operator error |

### INT-006 — Nothing tests the chain end-to-end across services and the board

| Field | Value |
|---|---|
| Finding | INT-006 |
| Severity | MEDIUM |
| Expected | At least one test proves that a check-in followed by a call changes what the public board serves, and that a recall/complete does the same |
| Actual | `test_e2e.py` exercises appointment → check-in → call → start → complete through the services and asserts the audit trail; `test_dqds.py` seeds queue rows directly. No test drives the projection from a real queue action to a board response, and no browser test exists for any of it |
| Evidence | `backend/tests/test_e2e.py:255-330`; `backend/tests/test_dqds.py` seeding helpers |
| Status | IMPLEMENTED — TEST COVERAGE GAP |
| Remediation | Add an integration test that performs the queue action over HTTP and then reads the board endpoint; add one recorded browser run for the operator page and one for the board |
| Dependencies | DQD-013 (page testability) |
| Acceptance | The test fails if the board stops reflecting a call; the browser run is attached as verification evidence |

---

## Section 9 — Consolidated Findings Register

| ID | Severity | Status | One-line finding | Stage |
|---|---|---|---|---|
| QOP-001 | HIGH | DEFECT CONFIRMED | `call` has no UI control | 3.1 |
| QOP-002 | HIGH | DEFECT CONFIRMED | A doctor cannot call/cancel/reorder their own queue | 3.1 |
| QOP-003 | HIGH | NOT IMPLEMENTED | No recall action or transition | 3.1 |
| QOP-004 | MEDIUM | DEFECT CONFIRMED | Duplicate check-in race (no constraint behind the check) | 3.1 |
| QOP-005 | MEDIUM | DEFECT CONFIRMED | Enqueue can fake `appointment` provenance; no duplicate-patient guard | 3.1 |
| QOP-006 | MEDIUM | DEFECT CONFIRMED | Reorder accepts an empty reason; reposition permission not required | 3.1 |
| QOP-007 | MEDIUM | DEFECT CONFIRMED | Recovery renumbers another branch's entries | 3.1 |
| QOP-008 | MEDIUM | PARTIALLY IMPLEMENTED | Position conflated with token serial; duplicate positions possible; no tie-break | 3.1 |
| QOP-009 | MEDIUM | PARTIALLY IMPLEMENTED | Token numbering hardcoded (no continuous mode, no room scope) | 3.1 |
| QOP-010 | MEDIUM | NOT IMPLEMENTED | Queue page never refreshes | 3.1 |
| QOP-011 | MEDIUM | PARTIALLY IMPLEMENTED | Queue history endpoint has no UI | 3.1 |
| QOP-012 | MEDIUM | DEFECT CONFIRMED | Test suite deletes the whole `queue_entries` table | 3.1 |
| QOP-013 | MEDIUM | TEST COVERAGE GAP | No automated concurrency test | 3.1 |
| QOP-014 | LOW | DEFECT CONFIRMED | Queue page opens on the UTC date | 3.1 |
| QOP-015 | LOW | TEST COVERAGE GAP | Check-in modal hides check-in-able appointments | 3.1 |
| QOP-016 | LOW | PARTIALLY IMPLEMENTED | Two overlapping recovery paths | 3.1 |
| QOP-017 | LOW | TEST COVERAGE GAP | Actions not constrained to the operational day | 3.1 |
| QOP-018 | LOW | DEFECT CONFIRMED | Duplicate `session.close()` in `queue_history` | 3.1 |
| QOP-019 | MEDIUM | DEFECT CONFIRMED | Catalogue's queue rows no longer match the tree | 3.4 |
| DQD-001 | HIGH | DEFECT CONFIRMED | Board's day is the server's date, not the facility's | 3.2 |
| DQD-002 | HIGH | NOT IMPLEMENTED | No room information anywhere in the queue/board | 3.2 |
| DQD-003 | MEDIUM | NOT IMPLEMENTED | No display configuration or multi-display support | 3.2 |
| DQD-004 | MEDIUM | PARTIALLY IMPLEMENTED | Presentation is app-scale, not TV-scale | 3.2 |
| DQD-005 | MEDIUM | NOT IMPLEMENTED | No estimated wait/countdown | 3.2 |
| DQD-006 | MEDIUM | PARTIALLY IMPLEMENTED | Display language is a per-TV preference, not facility config | 3.2 |
| DQD-007 | MEDIUM | PARTIALLY IMPLEMENTED | Limiter is per-process and proxy-blind | 3.2 |
| DQD-008 | MEDIUM | PARTIALLY IMPLEMENTED | Only the serving token is published; no “next up” | 3.2 |
| DQD-009 | MEDIUM | NOT IMPLEMENTED | No way to open, register or disable a display | 3.2 |
| DQD-010 | LOW | PARTIALLY IMPLEMENTED | 404 responses omit rate-limit headers | 3.2 |
| DQD-011 | LOW | DEFECT CONFIRMED | Public token embeds a doctor-id fragment | 3.2 |
| DQD-012 | LOW | DEFECT CONFIRMED | DQDS keeps a private bilingual string map | 3.2 |
| DQD-013 | MEDIUM | TEST COVERAGE GAP | No frontend/browser test for the board | 3.2 |
| DQD-014 | LOW | DEFECT CONFIRMED | Public board URL cannot be revoked | 3.2 |
| ANN-001 | HIGH | NOT IMPLEMENTED | No announcement capability at all | 3.3 |
| ANN-002 | HIGH | NOT IMPLEMENTED | No announcement event contract | 3.3 |
| ANN-003 | HIGH | NOT IMPLEMENTED | No Bangla/English speech strategy; voice availability unproven | 3.3 |
| ANN-004 | HIGH | NOT IMPLEMENTED | No announcement configuration; branch authority open | 3.3 |
| ANN-005 | HIGH | NOT IMPLEMENTED | No duplicate/ordering/playback-state design | 3.3 |
| ANN-006 | MEDIUM | NOT IMPLEMENTED | Autoplay/permission/audio-off undesigned | 3.3 |
| ANN-007 | MEDIUM | NOT IMPLEMENTED | Content, wording and pronunciation unspecified | 3.3 |
| ANN-008 | MEDIUM | NOT IMPLEMENTED | No observability for announcement attempts/failures | 3.3 |
| ANN-009 | MEDIUM | TEST COVERAGE GAP | No test or verification plan for QUE-006 | 3.3 |
| ANN-010 | LOW | NOT IMPLEMENTED | Volume/repeat/voice boundary undefined | 3.3 |
| INT-001 | HIGH | DEFECT CONFIRMED | Scenario A cannot complete the queue cycle | 3.1/3.3 |
| INT-002 | MEDIUM | PARTIALLY IMPLEMENTED | Assistant is read-only for the queue | 3.1 |
| INT-003 | MEDIUM | TEST COVERAGE GAP | Branch correctness holds except QOP-007/DQD-001 | 3.1/3.2 |
| INT-004 | MEDIUM | PARTIALLY IMPLEMENTED | Duplicate-check-in race; no concurrency test | 3.1 |
| INT-005 | HIGH | NOT IMPLEMENTED | Scenario E unexercisable (no audio path) | 3.3 |
| INT-006 | MEDIUM | TEST COVERAGE GAP | No cross-service/browser test of action → board | 3.4 |

### 9.1 Severity roll-up

| Workstream | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---:|---:|---:|---:|---:|
| Queue Operations (QOP) | 0 | 3 | 11 | 5 | 19 |
| DQDS (DQD) | 0 | 2 | 8 | 4 | 14 |
| QUE-006 (ANN) | 0 | 5 | 4 | 1 | 10 |
| Integration (INT) | 0 | 2 | 4 | 0 | 6 |
| **Total** | **0** | **12** | **27** | **10** | **49** |

No finding was escalated to CRITICAL. Per task §10 that rating is reserved for a security/privacy exposure, cross-tenant leakage, queue corruption, or a defect that makes core queue operations unsafe; the two candidates (QOP-007, QOP-004) are bounded — a cross-branch bookkeeping write with no disclosure, and a race that requires simultaneous requests — so both are MEDIUM with their rationale stated in place.

---

## Section 10 — Test and Verification Inventory

### 10.1 What exists in the tree

| Suite | Tests | What it proves | Notes |
|---|---:|---|---|
| `backend/queuing/tests/test_queue.py` | 58 (13 classes) | Check-in, duplicate rejection, four walk-in policies, token uniqueness, reorder, lifecycle, invalid transitions, role authorization, cross-org 404, persistence across reopen, audit writes, P0-1…P0-5 branch scope, RBAC-R1 enqueue ownership, RBAC-R3 doctor/assistant ownership, C1 history branch auth, C2 recovery ownership, C3 missing assignment, multi-doctor assignments | **Destructive fixture** (QOP-012); no concurrency test (QOP-013); no recall test |
| `backend/tests/test_dqds.py` | 24 | Board payload, empty queue, non-disclosure, cross-org isolation, PII absence, rate limiting + headers, cache headers, inactive org/branch/doctor, serving preference, tracking-material absence, internal-helper absence | Self-scoped purge (`_ensure()` deletes only its own orgs) |
| `backend/tests/test_sequence3.py` | 26 | Missed-turn idempotence, recovery renumbering, override reason, cross-branch/org 404, assistant refusal, notification hooks, outbox behaviour | The recovery contract is genuinely tested |
| `backend/tests/test_sequence4.py` | 13 | Cross-service token/check-in seams, `call` over HTTP | — |
| `backend/tests/test_e2e.py` | 21 | appointment → check-in → call → start → complete, audit trail composition, tenant-scoped audit feed | Service-level, not browser |
| `backend/tests/test_security.py` | 25 | Cross-cutting authorization/redaction checks | — |
| `frontend/tests/*.test.mjs` | 16 files | Calendar, booking feedback, Bangla name sense, symptom picker, dialog focus, facility/doctor | **None covers `pages/queue.js` or the DQDS page** (DQD-013) |

### 10.2 Documented prior evidence (not produced by this session)

| Claim | Where it is recorded |
|---|---|
| Queue suite 17/17 pass; live Docker e2e 14/14; 20 concurrent enqueues → 20 unique tokens; persistence across container restart | `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md` §8 |
| DQDS 24/24 pass; 118-test regression pass; `next build` exit 0; live `curl` verification of 200/404/429, headers and suspend/restore; no browser harness | `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` §7, §9, §10, §11 |
| Full backend suite `318 passed, 183 warnings in 624.05s` on this working tree (2026-11-19) | `docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md` |

### 10.3 What this session ran — and what it deliberately did not

**No test was executed in this session.** That is a deliberate read-only decision, not an omission:

1. The task (§4) forbids modifying the database, and this repository's suites write to it.
2. `backend/queuing/tests/test_queue.py:95-100` runs `session.query(QueueEntry).delete()` in an autouse fixture, i.e. it would delete every queue entry in the database this stack uses — including the demo data the docs index records.
3. `pytest --collect-only` was rejected too: importing `test_queue.py` executes module-level `_ensure_org()`, which commits.

Consequently every test-status statement in this document is **documentary or code-read**, and is labelled as such. To promote any finding to VERIFIED, the exact commands are:

```
# after QOP-012 is fixed (fixture scoped, guard added)
cd backend && AMSDP_DATABASE_URL=<test-db> ../.venv/bin/python -m pytest \
    queuing/tests/test_queue.py tests/test_dqds.py tests/test_sequence3.py tests/test_sequence4.py -q

# cross-service lifecycle (needs the stack up)
cd backend && ../.venv/bin/python -m pytest tests/test_e2e.py -q

# frontend library tests (no database)
cd frontend && npm test
```

Browser verification remains manual: there is no browser harness in this repository (SEQ_02 §11.5), so `BROWSER UNVERIFIED` can only be cleared by a recorded run.

### 10.4 Verification inventory by requirement (what does not exist)

| Required verification (task §7.7, §10) | Exists? |
|---|---|
| Bangla playback | No |
| English playback | No |
| Token pronunciation | No |
| Doctor/room announcement content | No |
| Recall announcement | No (recall does not exist) |
| Disabled-configuration behaviour | No |
| Duplicate prevention | No |
| Concurrent events | No |
| Audio failure | No |
| Browser autoplay restriction | No |
| DQDS rendered in a browser (any language, any resolution) | No |
| Queue operator page exercised in a browser | No |
| Concurrent token allocation as a test | No (live claim only) |
| Duplicate check-in under a race | No |
| Action → board projection across services | No |

---

## Section 11 — Implementation Roadmap

The prescribed order (3.1 Queue → 3.2 DQDS → 3.3 QUE-006 → 3.4 Integration) is kept, and the source evidence supports it: QUE-006's only approved trigger is the queue call action, which today has neither a UI control nor a doctor capability, and a DQDS board that shows the wrong day would make any announcement's effect unverifiable. **One exception is recommended:** the three decisions that block design (OD-1, OD-4, OD-5) should be answered **before** Stage 3.1 starts, because OD-5 changes the capability matrix 3.1 modifies, and OD-4 determines how much of Stage 3.2 is in scope.

### Stage 3.1 — Queue Operations remediation

| Element | Content |
|---|---|
| Findings covered | QOP-001…QOP-018 (QOP-019 belongs to 3.4), INT-001, INT-002, INT-003, INT-004 |
| Exact work | 1. Add a **Call** control and a **Recall** control to `/queue`, and add the recall transition + `queue.recall` audit action server-side. 2. Resolve the doctor/assistant capability model (OD-5) and apply it to `common/permissions.py`, `frontend/lib/auth.js` and the tests. 3. Add the duplicate-active-entry guarantee for check-in (partial unique index or row lock) as a forward-only Alembic migration. 4. Restrict `entry_source` on enqueue and add a duplicate-patient rule. 5. Require a reason for reorder and `queue.reposition` for an override. 6. Add the branch filter to `_active_queue()`. 7. Make `position` dense/unique per queue and order by `(position, created_at)`. 8. Implement configurable numbering (subject to OD-7). 9. Poll the queue list and show “last updated”. 10. Add a history view. 11. Fix the test fixture and add concurrency tests. 12. Fix the UTC default date, the check-in modal filter, the operational-day guard and the duplicate `close()` |
| Dependencies | OD-5 (capability model), OD-7 (numbering), a test database or a scoped fixture before any suite is executed |
| Risks | The migration touching `queue_entries` must be idempotent and must not renumber historic tokens; widening doctor capabilities could over-grant unless expressed as a narrow capability; changing `position` semantics can break the DQDS ordering assumption — hence the shared `(position, created_at)` rule |
| Acceptance | A receptionist and a doctor (own queue only) can check in → call → recall → skip → recover → start → complete entirely from the UI; two concurrent check-ins of one appointment yield one entry; the queue order is unique and stable; every action is audited with a reason where required |
| Required tests | New: `test_recall_preserves_status_and_audits`, `test_doctor_can_call_own_entry_and_not_another`, `test_concurrent_check_in_creates_one_entry`, `test_concurrent_enqueue_unique_tokens`, `test_reorder_requires_reason`, `test_recovery_does_not_touch_other_branch`, `test_position_unique_after_recovery`, `test_enqueue_rejects_appointment_source`, `test_queue_action_rejects_previous_day`, `test_queue_fixture_scoped` (guard). Existing: all 58 queue tests, `test_sequence3`, `test_sequence4`, `test_e2e` |
| Browser verification | One recorded run on `/queue` as receptionist and as doctor: call, recall, skip, recover, reorder, check-in, walk-in, history; confirm a second browser sees the change within one poll |

### Stage 3.2 — DQDS completion

| Element | Content |
|---|---|
| Findings covered | DQD-001…DQD-014, INT-003 (board half) |
| Exact work | 1. Use the facility-local operational day. 2. Add room to the queue entry and publish `room_name`. 3. Add the display configuration/registry with an optional per-display doctor/room filter and an enable/disable state (per OD-4). 4. TV-scale layout with a documented resolution target. 5. Estimated wait with an explicit “estimate” label. 6. Read the language from the display/facility configuration. 7. Durable limiter and a trusted client-address rule. 8. Optional “next N tokens” (default off). 9. A Displays panel with URL/QR and enable/disable. 10. Rate-limit headers on 404. 11. Speakable, facility-configurable token prefix. 12. Consolidate the i18n strings. 13. Make the page testable and add state tests |
| Dependencies | OD-4 (scope), Stage 3.1's position/room model change, and the same migration window (coordinate DQD-002 with QOP-009) |
| Risks | Room association for historic rows is unknown — the column must be nullable and the board must degrade to “—”; a per-display filter must be server-side; a durable limiter introduces a new runtime dependency (choose Redis only if it is already acceptable to the owner) |
| Acceptance | At 01:00 Asia/Dhaka the board shows the local day; a two-room branch shows rooms; two displays can show different subsets; a TV at 1920×1080 is readable at 5 m; the language comes from configuration; a disabled display is a non-disclosing 404 |
| Required tests | `test_dqds_uses_facility_local_day`, `test_dqds_publishes_room_without_pii`, `test_dqds_display_filter_is_server_side`, `test_dqds_display_disabled_404`, `test_dqds_rate_limit_headers_on_404`, `test_dqds_payload_has_no_internal_ids`; frontend state tests for loading/ready/empty/notfound/stale |
| Browser verification | Recorded runs at 1920×1080 and 1366×768 in both languages, including a simulated network drop (stale strip) and recovery |

### Stage 3.3 — QUE-006 implementation

| Element | Content |
|---|---|
| Findings covered | ANN-001…ANN-010, INT-001 (audio half), INT-005 |
| Exact work | 1. Decide and document the delivery mechanism (OD-1). 2. Define the queue-event contract with an idempotency key and emit it after commit. 3. Add `queue_announcement_config` to `organizations.config` with a route, validation, before/after audit and server-side authorization. 4. Build the announcement consumer: dedupe, FIFO, supersede-on-recall, retry, and a single in-progress announcement. 5. Implement Bangla and English playback with a voice-availability probe and a visible fallback. 6. Approve and implement the templates (OD-3), including a speakable token form. 7. Add audio-unlock and audio-off affordances that never block the queue. 8. Audit/log attempts and failures without PII. 9. Write the acceptance-test map before coding |
| Dependencies | Stage 3.1 (a reachable call action + recall), OD-1, OD-2, OD-3; optionally DQD-002/room if the announcement is to include the room |
| Risks | Bangla voice availability varies by device — the single largest delivery risk; a server-side TTS provider adds a data-sharing dependency and latency; autoplay policy can block the first announcement after a refresh; over-eager dedupe can drop a legitimate recall |
| Acceptance | With announcements enabled and Bangla configured, a call produces an intelligible Bangla announcement containing the token and doctor (and room where configured) and no patient data; the same with English; a disabled facility produces none; a repeated event produces one; a recall re-announces that entry; a blocked or missing voice leaves the queue fully functional with a visible error |
| Required tests | `test_announcement_event_has_idempotency_key`, `test_announcement_payload_has_no_pii`, `test_announcement_disabled_by_default`, `test_announcement_dedupe_same_event`, `test_announcement_orders_two_calls`, `test_announcement_superseded_by_recall`, `test_announcement_config_requires_admin_and_is_audited`, `test_announcement_failure_does_not_fail_call`; plus the browser playback matrix |
| Browser verification | Playback evidence for Bangla and English on the actual deployment device class, an autoplay-blocked run, a missing-Bangla-voice run, and a “two calls in two seconds” run |

### Stage 3.4 — Integration and acceptance

| Element | Content |
|---|---|
| Findings covered | INT-001…INT-006, QOP-019 |
| Exact work | 1. Cross-service test: HTTP queue action → board projection. 2. Scenario A–E browser runs, recorded. 3. Reconcile the catalogue rows for QUE-001…QUE-006 and DQDS-001 (endpoint, permission, status, known gaps) and refresh §F.4. 4. Register this document and any new report in `docs/governance/AMSDP_Docs_Index_V1.0.md`. 5. Produce the Phase 3 completion report with the governance-and-skill compliance section |
| Dependencies | Stages 3.1–3.3 complete |
| Risks | Documentation reconciliation can drift again if it is not done at the acceptance commit; a browser run on a development machine is not the same as the facility device — the device class must be stated |
| Acceptance | Every finding in Section 9 is closed or explicitly carried with an owner decision reference; the five scenarios have recorded evidence; the catalogue matches the tree; the owner accepts (or refuses) each feature |
| Required tests | `test_call_projects_to_board`, `test_recall_projects_to_board`, `test_complete_removes_from_board`; the full backend and frontend suites run against a scoped test database |
| Browser verification | Scenario A (solo doctor), B (desk + assistant), C (two branches), D (two operators, same queue), E (audio blocked) — each recorded with the exact steps and outcome |

**Suggested sequencing inside 3.1** (highest user value first, smallest blast radius first): QOP-001 + QOP-002 + QOP-003 (the journey), then QOP-004/QOP-005 (integrity), then QOP-007/QOP-008/QOP-006 (correctness and audit), then QOP-012/QOP-013 (testability), then the LOW items.

---

## Section 12 — Owner Decisions

Only decisions that the approved documents do **not** already settle are listed. Matters the Business Rules or the MVP scope lock already answer (walk-in policies, tenant scope, public-board privacy, appointment/queue separation, KEEP/DEFER dispositions) are **not** reopened here.

### OD-1 — How should announcements be produced and played?

| Field | Content |
|---|---|
| Question | Which delivery mechanism does QUE-006 use: (a) the browser's `speechSynthesis` on a display device, (b) a server-side TTS provider producing audio, or (c) pre-generated audio clips? |
| Why it matters | Every ANN finding's design depends on it: where configuration lives, where dedupe runs, how failures are observed, whether an external provider receives any text, and — decisively — whether Bangla can be guaranteed on the facility's device |
| Choices | **(a) Browser speech** — no provider, no cost, no data leaves the facility; but voices come from the device OS, Bangla may be missing, autoplay needs a user gesture, and there is no central control. **(b) Server TTS** — consistent Bangla on any speaker; but adds a paid external dependency, latency, a data-sharing contract (token + doctor name only) and audio caching. **(c) Pre-generated clips** — deterministic and offline-friendly for numerals/phrases; but cannot say a doctor's name without a large clip library |
| Recommendation | Start with **(a) plus a measured device matrix**, because it is the only option that ships without a new external dependency, and add a **server-side clip/numeral fallback** only if the measured Bangla quality on the target device is unacceptable. Record the measurement before choosing |
| If deferred | QUE-006 cannot start; Stage 3.3 slips entirely; the queue and board can still be completed (Stages 3.1–3.2) |

### OD-2 — Who owns announcement configuration, and at what level?

| Field | Content |
|---|---|
| Question | Is announcement enable/disable and language an **organization** setting, a **branch** setting, or a **display** setting — and may a `branch_admin` change it? |
| Why it matters | The catalogue lists `branch_admin` among the configuring roles, but the existing notification-config precedent denies `branch_admin` (it requires `org.read`/`org.manage`, which `branch_admin` does not hold). Choosing wrongly either blocks branch managers or widens authority without a decision |
| Choices | (1) Organization only, `org_admin`+ (mirrors `notification_config`). (2) Organization default with a per-branch override, `branch_admin` allowed to override. (3) Per-display only |
| Recommendation | **(2)**: an organization default (enable, language, events) with an optional branch override, because facilities with one loud waiting room and one quiet chamber need different behaviour; grant the override on an explicit capability rather than by widening `branch_admin`'s whole namespace |
| If deferred | ANN-004 cannot be implemented; a temporary org-only configuration would have to be migrated later |

### OD-3 — What exactly is announced, and how is a token pronounced?

| Field | Content |
|---|---|
| Question | Approve the Bangla and English announcement wording, the fields it may contain (token, doctor, room), and the read-aloud form of a token |
| Why it matters | The current token (`T-3F2A9C-001`) is not speakable and embeds an id fragment (DQD-011); a template that includes a patient name would breach the privacy criterion; Bangla doctor-name pronunciation is unaddressed |
| Choices | (1) Token + doctor name, with the token read as its numeric serial. (2) Token + doctor + room. (3) Token only. Plus: whether doctor names are read as written or from an optional per-doctor pronunciation field |
| Recommendation | **(2)** with the token read as “number N” under the facility's configured prefix, and an optional per-doctor Bangla pronunciation field — it matches what a patient in a corridor actually needs, and keeps every field non-PII |
| If deferred | ANN-007 blocks the template; a provisional wording would have to be re-recorded and re-tested |

### OD-4 — Which DQDS definition governs Phase 3 acceptance?

| Field | Content |
|---|---|
| Question | Is Phase 3 DQDS acceptance the catalogue's DQDS-001 (doctor-wise token board, no auth, no PII, rate-limited) or BR §33's fuller system (multiple displays per branch, per-display doctor/room configuration, facility-configured language, estimated wait, search result “current queue information”)? |
| Why it matters | The two readings differ by roughly eight findings (DQD-002, 003, 005, 006, 008, 009, 013, 014). Accepting the catalogue definition closes DQDS-001 today and defers the rest; accepting BR §33 makes Stage 3.2 a substantive build |
| Choices | (1) Catalogue definition for Phase 3; BR §33 items become later-phase (and BR §33's own “later-phase” sentence is honoured). (2) BR §33 definition, with multi-display in Phase 3. (3) A middle position: facility-local day + room + TV layout + configured language now; multi-display and estimates later |
| Recommendation | **(3)** — the first three are what make a board usable on a wall in a real facility, while multi-display and estimates need facilities to tell us their layouts |
| If deferred | Stage 3.2 cannot be scoped; DQD-003/DQD-005/DQD-008/DQD-009 stay in limbo and the register cannot be closed |

### OD-5 — What may a doctor and an assistant do to a queue?

| Field | Content |
|---|---|
| Question | Confirm the queue capability model: may a `doctor` call/recall/reorder (and cancel) their own queue, and may an `assistant` operate the assigned doctor's queue? |
| Why it matters | This is INT-001/INT-002/QOP-002 all at once. Today a solo doctor can start a consultation but cannot call the patient; an assistant can check in but cannot progress the queue. The answer changes `common/permissions.py`, the frontend mirror, and the tests that encode the current behaviour |
| Choices | (1) Keep as-is; the desk always calls (breaks Scenario A). (2) Grant doctors a new narrow `queue.call`/`queue.recall` capability for their own queue only. (3) Grant doctors `queue.manage` for their own queue. (4) Also grant assistants the queue-operator set for assigned doctors |
| Recommendation | **(2) plus (4)**: a narrow call/recall capability for doctors, and an explicit assistant queue-operator capability — never the broad `queue.manage`, and always behind `can_access_doctor`, so a solo chamber works without handing doctors appointment-modify authority |
| If deferred | Stage 3.1 cannot add the Call button safely (it would be hidden for the very role that needs it), and Scenario A stays broken |

### OD-6 — Is missed-turn recovery approved MVP scope?

| Field | Content |
|---|---|
| Question | Confirm that the implemented missed-turn/recovery/reposition behaviour (`recovery.py`, BR §27, catalogue QUE-004) is approved scope, given that PQV §H classifies “Missed-Turn Recovery & Queue Repositioning” as **NOT APPROVED FOR MVP** |
| Why it matters | `.clinerules` §1 requires a documented conflict to be surfaced. The code, the catalogue and BR §27 treat it as shipped behaviour; one approved decision document says otherwise. Acceptance of QUE-004 depends on which is authoritative |
| Choices | (1) Recovery is approved MVP behaviour; PQV §H is superseded (record the supersession). (2) Recovery is a later-phase capability and should be hidden behind a setting until approved. (3) Recovery is approved but the *automatic* variants are not |
| Recommendation | **(1)** — it is implemented, tested (26 tests), audited and it preserves token identity, which is safer than the cancel-and-rebook alternative; record the PQV §H supersession so the conflict cannot resurface |
| If deferred | QUE-004 acceptance is ambiguous; a future agent may remove working, tested behaviour on the strength of the older clause |

### OD-7 — Is configurable token numbering in Phase 3 scope?

| Field | Content |
|---|---|
| Question | BR §31 (FINALIZED) promises daily **and** continuous numbering, scoped per doctor **or room**, configurable per facility. The implementation has one mode (daily) and one scope (doctor). Is the configuration part of Phase 3, or is the current behaviour the accepted MVP reading? |
| Why it matters | It shares a data-model change with the room work (DQD-002) and the speakable token (OD-3/DQD-011); doing it later means two migrations over `queue_sequences` instead of one |
| Choices | (1) Phase 3: implement mode + scope + prefix configuration. (2) Accept daily-per-doctor as the MVP behaviour and record a Business Rules amendment (owner edit, not an agent edit). (3) Implement only the prefix/format configuration now, modes later |
| Recommendation | **(3)** now and **(1)** in the DQDS stage — the prefix/format is needed for audio (OD-3) and public hygiene (DQD-011), while continuous numbering has no current consumer |
| If deferred | QOP-009 and DQD-011 stay open; BR §31's promise remains unimplemented and must be documented as such |

---

## Section 13 — Overall Readiness and Recommendation

**Is Phase 3 ready for implementation? Yes — Stage 3.1 is ready to start now. Is Phase 3 ready for acceptance? No, and it is not close.**

What is ready:

- The queue service is a sound foundation: tenant/branch/doctor scoping is enforced and tested on every route, token allocation is atomic, every mutation is audited, and recovery preserves identity. Nothing in Section 7 required a security remediation.
- The DQDS endpoint satisfies its catalogue contract (four of five criteria fully, one partially) and its privacy posture is defensible in the code, not merely in a document.
- The work is enumerable: 49 findings, 12 HIGH, **none CRITICAL**, and every HIGH has a named remediation and acceptance test in Section 11.

What is not ready:

- The Phase 3 journey cannot be walked by the product's own users: the call step has no UI, a doctor cannot perform it at all, recall does not exist, and the announcement does not exist.
- The public board is wrong for six hours of every Dhaka day and cannot say which room to go to.
- Nothing in the queue/DQDS surface has been browser-verified, and the queue suite cannot currently be run against a populated database.

Recommendation, one line per consumer:

| For | Recommendation |
|---|---|
| The Product Owner | Rule on **OD-1, OD-4 and OD-5 before authorising Stage 3.1** (they change the capability matrix and the scope of the next stage), and on OD-2/OD-3 before Stage 3.3. OD-6 and OD-7 are documentation-level decisions that can be taken at any time |
| The implementation agent | Start Stage 3.1 with QOP-001/QOP-002/QOP-003; do not edit `frontend/lib/auth.js` or `common/permissions.py` until OD-5 is answered; fix QOP-012 before running any suite |
| The acceptance reviewer | Do not accept QUE-004, QUE-006 or DQDS-001 against the current tree; at most QUE-001/QUE-002/QUE-003 after Stage 3.1 plus browser verification |

**Top five implementation priorities**

1. **QOP-001 + QOP-002 + QOP-003** — make call and recall real for the receptionist and the solo doctor. Without this, every later stage adds capability no user can reach.
2. **QOP-004 + QOP-005 + QOP-013** — close the duplicate-entry race at the database level and prove token integrity with a concurrency test.
3. **DQD-001 + DQD-002** — the right day and the right room on the public board; these two decide whether a waiting-room television is usable at all.
4. **ANN-001…ANN-005** — the QUE-006 spine (event, configuration, playback, dedupe), after OD-1/OD-2/OD-3 are answered.
5. **QOP-012 + DQD-013 + INT-006** — make the work provable: a non-destructive fixture, page-level tests, and one cross-service test from queue action to board.

None of these requires rebuilding what exists. All five are additive or corrective, and each has a named acceptance test in Section 11.

---

## Appendix A — Evidence index

Every `file:line` cited in this document, with what it establishes.

| Reference | Establishes |
|---|---|
| `backend/queuing/main.py:26-28` | Denial auditing installed for the queue service |
| `backend/queuing/main.py:44-57` | Best-effort `_notify` hook pattern (never raises) |
| `backend/queuing/main.py:70, 75` | `ACTIVE_STATUSES`; `CHECKIN_SOURCES` (owner decision Q3 lifecycle) |
| `backend/queuing/main.py:104-117` | `_scoped_entry_or_404` — org **and** branch scope, 404 |
| `backend/queuing/main.py:119-160` | `GET /queue` branch/doctor scoping and ordering |
| `backend/queuing/main.py:169-283` | Check-in: permission, state validation, duplicate check, branch from the appointment |
| `backend/queuing/main.py:202-213` | Duplicate check-in is check-then-insert (QOP-004) |
| `backend/queuing/main.py:229, 339` | `position = token serial` (QOP-008) |
| `backend/queuing/main.py:284-300, 335-350` | Enqueue provenance/duplicate gaps (QOP-005) |
| `backend/queuing/main.py:374-393` | Action enum and transition tables (no recall) (QOP-003) |
| `backend/queuing/main.py:395-467` | Action route: permission split, doctor ownership, audit, notifications |
| `backend/queuing/main.py:469-533` | Reorder: optional reason, homogeneity check (QOP-006) |
| `backend/queuing/main.py:547-585` | History endpoint and branch validation; double `close()` (QOP-018) |
| `backend/queuing/recovery.py:78-140` | Recovery scope, `_active_queue` (no branch filter), `_renumber` (QOP-007) |
| `backend/queuing/recovery.py:143-281` | Missed-turn and recover contracts (reason, `queue.reposition`, audit) |
| `backend/queuing/display.py:30-78` | In-process limiter and headers (DQD-007) |
| `backend/queuing/display.py:98-121` | Non-disclosing 404 resolver |
| `backend/queuing/display.py:127-201` | Board query (`date.today()`, no room, allow-list payload) (DQD-001/DQD-002) |
| `backend/common/queue_tokens.py:33-56` | Token format and atomic UPSERT (QOP-009, DQD-011) |
| `backend/common/permissions.py:82-135` | Receptionist / doctor / assistant capability sets (QOP-002, INT-002) |
| `backend/common/timeutil.py:1-75` | Facility-local operational day — the rule DQDS breaks |
| `backend/common/models.py:854-873` | `QueueEntry` columns (no room, no unique appointment constraint) |
| `backend/common/notifications/config.py:66-71` | Closed channel list; cooldown (ANN-002, ANN-005) |
| `backend/organization/appointment_config.py` | The configuration-route pattern ANN-004 should copy |
| `backend/queuing/tests/test_queue.py:95-100` | Table-wide delete fixture (QOP-012) |
| `frontend/pages/queue.js:26` | UTC default date (QOP-014) |
| `frontend/pages/queue.js:137, 200` | `CONFIRMED`-only check-in picker (QOP-015) |
| `frontend/pages/queue.js:173-186` | Rendered actions — no Call (QOP-001) |
| `frontend/lib/auth.js:21-36` | Frontend capability mirror (must track OD-5) |
| `frontend/pages/queue-display/[org]/[branch].js:31-84, 152-156` | Display language precedence (DQD-006) |
| `frontend/styles/global.css:91-124` | DQDS presentation sizes (DQD-004) |
| `AMSDP_MVP_Feature_Catalogue…:363-581, 886-915, 1078-1118, 1185-1192, 1237-1266` | The acceptance criteria and recorded statuses this analysis measures against |
| `AMSDP_Business_Rules_V1.0.md:581-770, 1023-1043, 1079-1098` | Queue/DQDS business rules and configurability requirements |
| `AMSDP_PQV_…_Decision_V1.0.md:57-70, 160-165` | DQDS P0 classification; recovery “NOT APPROVED” clause (C-1, C-2, OD-4, OD-6) |
| `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` §9–§11 | DQDS live evidence and its stated limitations (no browser harness, per-process limiter, serving-token-only) |

---

## Appendix B — Governance and skill compliance

### B.1 Documents read before acting (`.clinerules` §2 step 3, §12)

`.clinerules`; `docs/governance/AMSDP_Docs_Index_V1.0.md`; `docs/product/AMSDP_Business_Rules_V1.0.md` (§24–§33, §40–§42, §52–§56); `docs/product/AMSDP_MVP_SCOPE_V1.0.md` (as cited by the catalogue); `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`; `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`; `docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`; `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md`; `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md`. Sources of truth for behaviour were read in full or in the relevant ranges: `backend/queuing/main.py`, `display.py`, `recovery.py`, `common/queue_tokens.py`, `common/permissions.py`, `common/timeutil.py`, `common/notifications/config.py`, `common/models.py`, `frontend/pages/queue.js`, `frontend/pages/queue-display/[org]/[branch].js`, `frontend/lib/auth.js`, `frontend/styles/global.css`, and the queue/DQDS/recovery/e2e test inventories.

### B.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5 Skills Registry: NONE — re-verified: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used or claimed; the AMSDP governance documents were applied directly, per §5's fallback instruction.

### B.3 Non-negotiables (§3) — how each was honoured

| Rule | How it was honoured |
|---|---|
| No secrets logged or exposed | No credential, token or key was read, printed or written; `.env` was never opened and nothing from `docs/demo/AMSDP_Demo_Credentials_V1.0.md` was used or quoted |
| UI is never the safety boundary | Every finding is stated against server-side enforcement; QOP-001's missing button is explicitly *not* treated as authorization |
| Server-side authorization; org/branch from the token | The analysis measures the code against this rule and reports one violation of the *write* scope (QOP-007) |
| Cross-tenant/branch fails closed with 404 | Confirmed by code and tests; the single `403` (a permission shortfall) is distinguished from a scope failure |
| `organization_id` is the only tenant key | No second tenant column is proposed anywhere in this document |
| Audit is append-only and persistent | No audit row was written, deleted or rewritten; suggested new audit actions are additive names |
| Denials are recorded | Noted as implemented (`install_denial_audit`); no proposal would bypass it |
| Schema changes ship as forward-only idempotent migrations | Every migration this document asks for (QOP-004, QOP-009, DQD-002/003) is described as forward-only; none was created |
| Never claim an unverified capability | Section 10 states plainly that no test was executed and why; every status is labelled TESTED / CODE-READ / NOT TESTED with its evidence |
| Do not use a tool or library merely because it is available | No new library or provider is proposed as a dependency; no skill was invoked |

### B.4 Read-only compliance (task §4, §13)

| Requirement | Result |
|---|---|
| No source files changed | **Confirmed** — `git diff --stat` before and after are identical: 35 files, 1,868 insertions(+), 154 deletions(−) |
| No existing documents changed | **Confirmed** — the five `M docs/…` entries are the pre-existing modifications from earlier work, left byte-identical |
| No migrations created | **Confirmed** |
| No database changes | **Confirmed** — no SQL was executed and no test suite was run (§10.3) |
| No pre-existing modified file altered | **Confirmed** |
| No untracked file deleted | **Confirmed** — the 12 pre-existing untracked files are unchanged; the new document is the 13th |
| Nothing staged, no commit, no push | **Confirmed** — `git status --short` shows `??` for the new file and no staged entries |
| **Before** | `hackathon-mvp` @ `6b7ef4d`; 35 `M`, 12 `??` |
| **After** | `hackathon-mvp` @ `6b7ef4d`; 35 `M`, 13 `??` — the only delta is this document |
| Only permitted new artefact | `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` |

### B.5 Documentation placement (§11) and index (§12)

- Written under `docs/audit/` — the subject subfolder for audit and gap-analysis records — with the filename `AMSDP_<Topic>_<Version>.md`.
- The destination filename was checked before writing; it did not exist, so nothing was overwritten and no historical version was disturbed.
- `.clinerules` §12 obliges an index update **when a document is created**. This task is explicitly read-only for existing documents (task §12: “Do not modify the Docs Index during this read-only task … record the proposed registration row for owner review”), so the index was **not** edited and the proposed row is supplied in Appendix C for the owner to apply. This is a deliberate, stated deviation, recorded here rather than hidden.

### B.6 Deviations and limitations

1. **No tests executed** (§10.3) — the repository's queue suite deletes the whole `queue_entries` table and the task forbids database modification.
2. **No browser verification** — the repository has no browser harness (SEQ_02 §11.5) and a browser run was outside a read-only task.
3. **Docs index not updated** (B.5) — the row is proposed, not applied.
4. **Line references are to the working tree at `6b7ef4d` plus local modifications**, not to the committed HEAD; a later commit that shifts lines will date them, while the paths and function names remain stable anchors.
5. **The catalogue's status rows are stale** (QOP-019). They were not “fixed” because they are a measurement artefact under owner review; the discrepancy is reported instead.

---

## Appendix C — Proposed Docs Index registration row (for owner review, not applied)

`.clinerules` §12 requires a created document to be registered in `docs/governance/AMSDP_Docs_Index_V1.0.md`. Because this task is read-only for existing documents, the row below is **proposed** for the `## audit/` table (columns `File | Size | Read when | Owner`), with the size measured at the time of writing:

```markdown
| `AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` | 149,752 | **Before any Phase 3 queue, DQDS or QUE-006 work, or before accepting QUE-004/QUE-005/QUE-006/DQDS-001** — 49 findings (12 HIGH, 0 CRITICAL) across Queue Operations (QOP-001…019), DQDS (DQD-001…014), QUE-006 (ANN-001…010) and integration (INT-001…006) with `file:line` evidence, the A–E scenario verdicts, the test inventory and why no suite was run, the four-stage roadmap, and owner decisions OD-1…OD-7 (announcement mechanism, configuration ownership, wording, DQDS scope, doctor/assistant queue capability, recovery scope, token numbering) | — |
```

The accompanying revision note would read: snapshot **91** on disk / **89** registered; open item **O-3** unchanged (the two documents still unregistered by their own workstreams).

---

*End of document.*



































