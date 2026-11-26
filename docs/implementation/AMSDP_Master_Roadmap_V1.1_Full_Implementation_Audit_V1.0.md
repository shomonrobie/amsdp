# AMSDP — Master Roadmap V1.1 Full Implementation Audit (V1.0)

**Document ID:** AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0
**Audit date:** 2026-11-26
**Audit type:** Read-only, evidence-based implementation audit. **Audit only.**
**Audited object:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (72,842 bytes as registered in the docs index), including Amendments **A-1…A-5**, cross-read against `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`.
**Baseline under audit:** branch `hackathon-mvp`, HEAD `fd4d365`, working tree containing one pre-existing, owner-authored modification (`.clinerules`) which this audit did **not** touch.
**Auditor:** AI agent (Cline), acting under `.clinerules` §1–§12.

---

## A. Purpose, scope and constraints

### A.1 Purpose

Classify **every** item in the governing roadmap — 46 work-package tasks (`MP-01`…`MP-46`, with `MP-02b` audited separately, 47 items in all) plus the Amendment A-1…A-5 deltas — into one of the mandated states, using evidence gathered from the tree itself rather than from the roadmap's or the execution register's own claims:

`IMPLEMENTED` · `PARTIALLY IMPLEMENTED` · `NOT IMPLEMENTED` · `IMPLEMENTED — NOT TESTED` · `TESTED — NOT ACCEPTED` · `BLOCKED` · `DEFERRED` · `UNVERIFIABLE`

### A.2 Constraints observed

| Constraint | Observance |
|---|---|
| No code, test, configuration or database change | Held. Only reads and `SELECT`-only queries were used; no file inside the repository was created or modified except this report |
| No schema migration, no `alembic upgrade`, no `INSERT`/`UPDATE`/`DELETE` | Held. The two probe scripts live **outside** the repository (`C:\Users\Public\`), open a read-only session and issue `SELECT` only |
| No commit, no push, no branch change | Held. `git status --porcelain` before and after the audit shows the same single pre-existing entry |
| No implementation work to "fix" what the audit finds | Held. Every gap is recorded, none repaired |
| Evidence discipline (§7) | Held. `IMPLEMENTED` / `TESTED` / `VERIFIED` / `ACCEPTED` are kept distinct; no state above `TESTED` is claimed anywhere in this document |
| Secrets (§3) | Held. No credential, token or JWT material is quoted. The local development database URL is referenced by shape only |

### A.3 What this audit is not

- It is **not** an acceptance record. No deliverable in this report is `ACCEPTED`; the only acceptance acts cited are owner decisions about **scope** (PO-02, PO-13 and the PO-01…PO-13 closures).
- It is **not** a live verification of the demonstration stack. The Ubuntu host, the published ports, the six-screen display load and the audio path were not reachable from this session (see §E).
- It is **not** a re-derivation of the roadmap's estimates, sequencing or scope. Those are taken as given; only their **state claims** are tested.

---

## B. Baseline

| Item | Value | How established |
|---|---|---|
| Branch | `hackathon-mvp` | `git rev-parse --abbrev-ref HEAD` |
| HEAD commit | `fd4d3656738dfef0885cfc86307903305aa2f08d` | `git rev-parse HEAD`, and `git rev-parse origin/hackathon-mvp` returns the same SHA — local and remote agree at audit close |
| Working tree | one modification, `.clinerules` (owner's own edit, pre-existing) | `git status --porcelain` — single line `M .clinerules`; unchanged at audit close |
| Alembic revisions in tree | **18** files, **single head** `d3f5a7b91c24` | directory listing plus revision-chain walk of `backend/alembic/versions/` |
| Local development database | `postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp`, at revision `d3f5a7b91c24` | read-only probe §D.4 |
| Deployment database (Ubuntu host) | claimed at `c4d8e2a91f60` (2026-11-23) | **REPORTED only** — roadmap Appendix E, never re-verified in this session |
| Backend suite | green at `fd4d365` in CI (`Backend` job success) | GitHub Actions REST read §D.5 |
| Frontend suite | green locally (465 pass / 0 fail), **red in CI at `fd4d365`** | §D.2 and §D.5 |

**Baseline consequence.** The audited SHA is not in a uniformly green state: the backend job passed and the frontend job failed on the same commit. Every "tested" statement below is therefore qualified with *which* run produced it.

---

## C. Method and evidence vocabulary

### C.1 Evidence labels used in this report

| Label | Meaning | Example of what earns it |
|---|---|---|
| **OBSERVED** | Read directly from the tree or a live read-only query in this session | a file path with line numbers; a `SELECT` result |
| **TESTED** | A named test ran and its result was seen in this session, or a CI job at the audited SHA ran it | `node --test …` output; CI job step list |
| **REPORTED** | Asserted by a roadmap, register or implementation report but not independently re-established here | "live DB migrated on 2026-11-23" |
| **INFERRED** | A conclusion drawn from observed evidence, stated as such | "the dev DB carries suite residue" |
| **UNVERIFIED** | Could not be established in this session | live host state, browser behaviour |

A roadmap claim alone never moves an item above `REPORTED`. `VERIFIED` and `ACCEPTED` (`.clinerules` §7) are used **nowhere** in this report as a status of my own making; where the roadmap claims them for itself, they are reproduced as claims.

### C.2 Status decision rules applied

| Status | Rule |
|---|---|
| `IMPLEMENTED` | The deliverable exists and is reachable in the tree; where a test exercises it, the test exists **and** ran green in the CI backend job or locally |
| `IMPLEMENTED — NOT TESTED` | Code exists, no test exercises it, or no test run was seen |
| `PARTIALLY IMPLEMENTED` | Some named sub-deliverable of the task exists and others provably do not — the missing parts are enumerated |
| `NOT IMPLEMENTED` | No evidence of the deliverable in the tree |
| `TESTED — NOT ACCEPTED` | Green evidence exists but the roadmap's own acceptance act (owner sign-off, live run, gate) is outstanding |
| `BLOCKED` | Authorised work that cannot proceed because of a recorded blocker (B-/PO-/infrastructure) |
| `DEFERRED` | Explicitly deferred by an owner decision |
| `UNVERIFIABLE` | The deliverable may exist but its state depends on an environment this session could not reach |

---

## D. Checks actually executed in this session

| # | Check | Result observed |
|---|---|---|
| D.1 | `git rev-parse --abbrev-ref HEAD`; `git rev-parse HEAD`; `git status --porcelain`; `git log --oneline -4` | `hackathon-mvp`; `fd4d365`; single line `M .clinerules`; history `fd4d365`, `1f303d1`, `082e2a0`, `0bd8059` |
| D.2 | `cd frontend && npm test` | `tests 467` · `pass 465` · `fail 0` · `cancelled 0` · `skipped 2` · `todo 0` · duration `1156.86 ms` |
| D.3 | `cd frontend && node --test tests/banglanamesense-dataset.test.mjs tests/calendar-render.test.mjs` | `tests 18` · `pass 18` · `fail 0` · `skipped 0` — the plan's **Q-3 pair passes in this tree** |
| D.4 | Read-only SQL probe (SELECT only, two scripts outside the repo) against the local dev DB | `alembic_version = d3f5a7b91c24`; **33** public tables; `queue_displays` **1**; `queue_display_doctors` **1**; `staff_doctor_assignments` **116**; `voice_packs` **0**; `announcement_platform_config` **1**; `queue_announcement_deliveries` **0**; `platform_audit_events` **280**; `audit_events` **10,550**; `organizations` **171** |
| D.5 | GitHub Actions REST API (unauthenticated): runs for `hackathon-mvp`, per-run job list | **34** runs on the branch; latest **#34**, id `45651581256`, sha `fd4d365`, conclusion **failure**; jobs: `Backend` **success** (through *Apply migrations* and *Run backend tests*), `Frontend` **failure** at step *Run frontend tests* (~1 s after start) |
| D.6 | GitHub Actions check-run annotations for run #34 | Only *"Process completed with exit code 1"* plus a Node-20 deprecation warning — **no test-level cause is exposed**; an authenticated log read was not possible (no token) |
| D.7 | Alembic chain walk of `backend/alembic/versions/` | 18 revisions, single head `d3f5a7b91c24`; a merge revision joins the two earlier branches → no dangling head |
| D.8 | Static symbol counts across `backend/**/*.py` | `queue.display.manage` → **0**; `queue.display.denied` → **0**; `staff.doctor_assignment_changed` → `identity/routes.py:310`; `reserved_capacity` in `backend/queuing` → **9** hits; `priority` in `backend` → **1** hit |
| D.9 | Static counts across the frontend (excluding `node_modules`/`.next`) | `window.print` / `@media print` → **0**; `qr` → **0**; page inventory = 16 `.js` files under `frontend/pages/` (13 admin, dashboard, login, `queue-display`, `track`, `_app.js`), with **no** queue-history page and **no** display-admin page |
| D.10 | Backend `qr` occurrences | **18**, all under `appointment/tracking.py` (`/track/{token}/qr`, line 215) and `tests/test_tracking_tokens.py` — the QR **endpoint** exists; the print **flow** does not |
| D.11 | `backend/appointment/tracking.py` rate-limiter inspection | module-level in-process dict `_RATE`, `_RATE_LIMIT = 10`, `_RATE_WINDOW = 60.0`, comment *"DB-backed bucket deferred to M9-F"* (lines 20–34) |
| D.12 | `backend/patient/main.py` date-source inspection | 8 references to `operational_today`, **no** remaining `date.today()` → the plan's **Q-1** closure holds |
| D.13 | `backend/seed/seed_demo.py` inspection | `StaffDoctorAssignment` created at lines 674–684; `date.today()` removed, `operational_today` used at line 757 (comment at 754) |
| D.14 | `backend/organization/tests/` inventory | `test_walk_in_config.py`, `test_queue_calling_config.py`, `test_appointment_config.py`, `test_voice_packs_api.py`, `test_voice_pack_policy.py`, `test_organization.py`, `test_container_layout_import.py` |
| D.15 | Docs-index and product-document lookups | plan V1.0 registered at index line 1590, V1.1 at 1608, A-1 at 1635, A-2 at 1672; Feature Catalogue §H.1 annotation at line 1348 with a dated re-verification table at 1353; Limitations-report annotation at lines 19–33 |

---

## E. Checks *not* executed, and why

Silence is not evidence. Each omission is named with its reason, and the affected items are graded `UNVERIFIABLE` / `BLOCKED` rather than "absent".

| Not executed | Reason | Consequence for this audit |
|---|---|---|
| Local `pytest` run of the backend suite | The configured development database already carries non-demo residue (171 organizations, 10,550 audit rows — **INFERRED** as prior suite/scan residue) and this audit may not write to any database. The authoritative whole-suite evidence at the audited SHA is the CI `Backend` job on a disposable Postgres service (D.5) | No local backend result is claimed; backend `TESTED` statements rest on the CI job only |
| Live-stack probes on the Ubuntu host (`alembic current`, ports 8110–8117, 3100, 8000, 3000) | No authorised access method (B-4 open; PO-10 execution needs a maintenance window) | **MP-01**, **MP-31**, **MP-32**, **MP-40** cannot be closed; deployment state stays `REPORTED` |
| Browser run at 360 px, keyboard traversal, screen-reader spot check | No browser session available; the audit may not start services | **MP-29**, and the page-side halves of **MP-38/MP-42/MP-43**, stay at unit level — never `VERIFIED` |
| Audio playback of a composed announcement | No audio device (B-8) and `queue_announcement_deliveries` is **0** | **MP-03** stays `BLOCKED`; the zero-row delivery table is positive evidence the path has never completed |
| Six-screen display load, stale/reconnect behaviour | Requires the running stack and the registry seeded with the two demo displays | **MP-40** `BLOCKED` |
| Authenticated read of the failing CI frontend log | GitHub token unavailable to this session | The CI failure at `fd4d365` remains **unnamed** — itself a live violation of MP-33's criterion |
| Midnight operational-day rollover observation | Requires a clock boundary on a running deployment (B-3) | **MP-44**'s boundary case unobserved; its code path is tested |
| Reseed to observe the demo personas | B-1 withheld — the demo-data authority is not a reseed authority | Persona-level acceptance of the seeded assignment (**MP-05**) unobserved |

---

## F. State of the tree and the database, as observed

### F.1 Schema and migrations

| Fact | Evidence |
|---|---|
| 18 Alembic revisions, **single head** `d3f5a7b91c24` | D.7 |
| `c4d8e2a91f60_add_voice_packs_and_platform_config.py` exists in the chain | directory listing; referenced by `organization/announcement_config.py` |
| A later revision adds the display tables (`queue_displays`, `queue_display_doctors`) on top of `c4d8e2a91f60` → head `d3f5a7b91c24` | revision walk (D.7) |
| The local development database is **at head** | D.4 (`alembic_version = d3f5a7b91c24`) |
| The deployment database is **one revision behind head** | **REPORTED** — roadmap Appendix E records `c4d8e2a91f60` on 2026-11-23; A-5 records the further upgrade as blocked by B-4 |

### F.2 Models present in `backend/common/models.py`

`StaffDoctorAssignment` (~234), `ScheduleBlock` (~590), `QueueAnnouncementDelivery` (~962), `QueueDisplay` (~1020), `QueueDisplayDoctor` (~1101), the tracking-token model (~1128), and the platform audit model (~1194/1203). All **OBSERVED** in the file.

### F.3 Signatures verified in code

| Surface | Location | Verified content |
|---|---|---|
| Display resolver / scope | `backend/queuing/display.py:241–268` | `?display=<code>` resolution, server-side doctor filtering, 404 on unknown / cross-branch / cross-org / disabled |
| Room label | `display.py:270–279` | `room_name` published per doctor (nullable) |
| Board version + `ETag` / `304` | `display.py:350`, `362–366`, `522–528` | projection hash, weak validator, conditional response |
| Operational day on the display path | `display.py:403` | `operational_today(...)`; the old `date.today()` at line 138 is gone |
| Facility-controlled public fields | `display.py:477–505`, footer `516` | `show_room`, `show_estimated_wait`, `show_waiting_count`, `footer_text` enforced server-side |
| GET-only guard | `display.py:558–568` | `405` with `Allow: GET` |
| Throttled disabled-code audit | `display.py:169`, `196` | `queue.display.disabled_requested`, throttled |
| Walk-in policy | walk-in config module + `backend/queuing` (9 `reserved_capacity` hits) + `backend/appointment/main.py:147` (`WALK_IN_POLICIES`) | four persisted policies with before/after audit |
| Platform calling policy | `backend/organization/announcement_config.py` (8 references) | platform-level policy persisted and audited |
| Staff-management guards | `backend/identity/routes.py:193`, `207–223`, `22`, `395–407` | self-escalation 403, last-admin protection, `DELEGABLE_CAPABILITIES` ceiling |
| Doctor-assignment audit | `backend/identity/routes.py:310` | `action="staff.doctor_assignment_changed"`, before/after payload |
| Recall transition | `backend/queuing/` recall action; `tests/test_queue.py:1669–1698` | `recall` is a distinct append with its own event id; no duplicate announcement |
| Q-1 closure | `backend/patient/main.py` (8 references) | `operational_today` throughout; no `date.today()` remains |
| Q-2 closure | `backend/appointment/dashboard.py` (6 `queue_length` refs), `tests/test_dashboard.py`, `frontend/tests/dashboard-tiles.test.mjs` | Waiting = `queue_length`, "In queue" shown separately |

### F.4 Absences verified — a zero is evidence too

| Absent | Evidence |
|---|---|
| `queue.display.manage` capability, route or page | D.8 (0 hits) and D.9 (no display-admin page among the 16) |
| `queue.display.denied` audit event | D.8 (0 hits) |
| Any print path (`window.print`, `@media print`, print stylesheet) | D.9 (0 hits) |
| Any QR in the frontend, or a print flow around the backend QR endpoint | D.9 (0 hits), D.10 (endpoint only) |
| A queue-history screen | D.9 (16 files under `frontend/pages/`, none for history) |
| Priority field, endpoint or permission | D.8 (`priority` → one incidental hit in the whole backend) |
| Continuous / scoped token numbering | no `token_mode` / `continuous` handling in `backend/queuing` |
| A `/api/v1/reports` surface | no reports router in any app |
| A durable tracking rate limiter | D.11 (in-process dict; the comment itself defers the DB bucket) |
| A subscription / entitlement model | no such model in `common/models.py` |
| Removal of the page-local `L={bn,en}` dictionary | the display page still carries its own dictionary (`[branch].js:9`), `dqds_locale` at `:30`, precedence comment at `:41–53` |

---

## G. Status summary

### G.1 Counts (47 audited items = 46 task IDs + MP-02b)

| Status | Count | Items |
|---|---|---|
| **IMPLEMENTED** (tested where a test exists) | **17** | MP-02b, MP-05, MP-06, MP-07, MP-08, MP-10, MP-16, MP-17, MP-18, MP-19, MP-20, MP-22, MP-29, MP-34, MP-36, MP-41, MP-44 |
| **PARTIALLY IMPLEMENTED** | **13** | MP-01, MP-02, MP-04, MP-24, MP-25, MP-28, MP-33, MP-35, MP-37, MP-42, MP-43, MP-45, MP-46 |
| **NOT IMPLEMENTED** | **8** | MP-09, MP-13, MP-14, MP-15, MP-23, MP-30, MP-38, MP-39 |
| **DEFERRED** | **5** | MP-11, MP-12, MP-21, MP-26, MP-27 |
| **BLOCKED** | **4** | MP-03, MP-31, MP-32, MP-40 |
| **IMPLEMENTED — NOT TESTED** | **0** | no item has code without at least one exercising test |
| **TESTED — NOT ACCEPTED** | **0 as a primary status** | the state exists but is not any task's *primary* status; it is the general condition of the whole tree (§G.2) |
| **UNVERIFIABLE** | **0 as a primary status** | 7 items carry an UNVERIFIABLE *sub-clause* rather than an unknowable whole: MP-01 (deployment half), MP-29 and MP-42/MP-43 (browser half), MP-44 (rollover boundary), MP-05 (persona half), MP-34 (owner review) |

Total audited: **17 + 13 + 8 + 5 + 4 = 47** ✔

### G.2 The acceptance gap, stated plainly

- **29 of the 47** items carry at least one exercising test — 16 of the 17 `IMPLEMENTED` (all but MP-34, a documentation act), 12 of the 13 `PARTIALLY IMPLEMENTED` (all but MP-01), and MP-03 at unit level. **None of the 47 is `ACCEPTED`.**
- The only acceptance acts on record are owner **decisions** (PO-02, PO-13, and the PO-01…PO-13 closures) — decisions about scope, not about whether a deliverable works.
- Nothing in the tree is `VERIFIED` by the §7 definition except where a second, independent artefact was seen in this session: the CI backend job (backend suite at `fd4d365`), the read-only database probe (schema and row counts), and the local frontend run. Those make the *specific* claims they support VERIFIED — they do not make any task ACCEPTED.

### G.3 Distribution across the roadmap's own work packages

| Work-package band (roadmap grouping) | Items | Implemented | Partial | Not implemented | Blocked | Deferred |
|---|---|---|---|---|---|---|
| WP-A runtime restoration — MP-01…MP-08, MP-02b | 9 | 5 | 3 | 0 | 1 | 0 |
| WP-B/C operations — MP-10, MP-16…MP-29 | 13 | 8 | 3 | 1 | 0 | 1 |
| WP-D meta and acceptance — MP-30…MP-34 | 5 | 1 | 1 | 1 | 2 | 0 |
| WP-C.2/C.3 multi-display — MP-35…MP-46 | 12 | 3 | 6 | 2 | 1 | 0 |
| Deferred by decision — MP-09, MP-11…MP-15, MP-26, MP-27 | 8 | 0 | 0 | 4 | 0 | 4 |
| **Total** | **47** | **17** | **13** | **8** | **4** | **5** |

Column sums reconcile with §G.1: 17 + 13 + 8 + 4 + 5 = 47.

---

## H. Item-by-item audit matrix

Legend: **I** = implementation evidence, **T** = test evidence, **A** = acceptance evidence. `—` means "no such evidence exists", which is itself a finding.

### H.1 WP-A — runtime restoration (MP-01…MP-08, MP-02b)

| Ref | Requirement | Status | I | T | A | Remaining / blocker |
|---|---|---|---|---|---|---|
| **MP-01** | Prove the runtime; never re-apply an applied migration; record `alembic current` first; probe published ports | **PARTIALLY IMPLEMENTED** | The **local** database is at head `d3f5a7b91c24` (D.4) — the tree side of the requirement is satisfied. The **deployment** half is `REPORTED` at `c4d8e2a91f60`, one revision behind head | — | Roadmap Appendix E records the 2026-11-23 migration; not re-established here | The Ubuntu host has never been probed from this session; the display tables do not exist at `c4d8e2a91f60`, so the display surface cannot run there. **B-4** |
| **MP-02** | Whole-tree suite re-baseline on the migrated database | **PARTIALLY IMPLEMENTED** | — | Backend: **green at `fd4d365`** in CI (D.5). Frontend: **465 pass / 0 fail locally** (D.2) but **red in CI at the same SHA** (D.5) | — | The criterion's own clause *"every failure named with cause"* is unmet: the CI frontend failure at `fd4d365` is **unnamed** (D.6) |
| **MP-02b** | Phase-2 cancel / reschedule / no-show regression sweep | **IMPLEMENTED** | Cancel, reschedule and no-show paths exist in `backend/appointment/` | Exercised by the backend suite in the green CI job (D.5) | — | Nothing outstanding; not `ACCEPTED` |
| **MP-03** | QUE-006 runtime closure — announce from the staff board on the live stack | **BLOCKED** | Staff-board recall/call actions and the announcement pipeline exist (`tests/test_queue.py`) | Unit-level green (CI backend) | — | **Never run on hardware.** `queue_announcement_deliveries` = **0** rows (D.4) — positive proof the path has never completed. **B-8** (no audio device on the working machine) |
| **MP-04** | W3 voice-pack admin surface (preview / publish / retire) | **PARTIALLY IMPLEMENTED** | API exists: `organization/announcement_config.py` plus a `voice_packs` table (1 config row, 0 packs in dev DB); `voice_packs` API tests present | `test_voice_packs_api.py`, `test_voice_pack_policy.py` (D.14) | — | **No admin page** (D.9: no voice-pack page among the 16). Also note the contradiction that **PO-05 CLOSED** as "MP-04 deferred" while the API already exists |
| **MP-05** | Seed `staff_doctor_assignments`; replace `date.today()` in `seed_demo.py` | **IMPLEMENTED** | `seed_demo.py:674–684` creates the assignment; `date.today()` gone, `operational_today` at :757 | `backend/tests/test_seed_demo.py`; dev DB holds **116** assignment rows (D.4) | — | Persona-level observation withheld (**B-1**) |
| **MP-06** | `queuing/display.py` → `operational_today(session, org)` | **IMPLEMENTED** | `display.py:403` uses `operational_today`; the `date.today()` at line 138 is gone | Display/operational-day tests in the backend suite (green in CI) | — | — |
| **MP-07** | Dashboard "Waiting" tile → `today.in_queue`, corrected by Q-2 | **IMPLEMENTED** | `appointment/dashboard.py` (`queue_length`, 6 refs); Q-2 correction applied — Waiting = `queue_length`, "In queue" separate | `backend/tests/test_dashboard.py`; `frontend/tests/dashboard-tiles.test.mjs` (465-pass local run) | — | — |
| **MP-08** | Recall (`called → called`), distinct event, UI control, announcement-safe | **IMPLEMENTED** | `recall` action in `backend/queuing`; UI control on the staff board (`queue-call-control` test) | `tests/test_queue.py:1669–1698` — distinct event id, no duplicate announcement | — | — |

### H.2 WP-B/C — operations, RBAC, dashboard, localisation (MP-10, MP-16…MP-29)

| Ref | Requirement | Status | I | T | A | Remaining / blocker |
|---|---|---|---|---|---|---|
| **MP-10** | Walk-in policy persisted per facility, incl. a real `reserved_capacity` pool; retire the per-request parameter | **IMPLEMENTED** | Four persisted policies; `reserved_capacity` handled in `backend/queuing` (9 refs) and in `appointment/main.py:147` (`WALK_IN_POLICIES`); audited before/after | `organization/tests/test_walk_in_config.py`; placement tests in `backend/queuing/tests/test_walk_in_placement.py` | — | The *pool* semantics were read in code, not exercised against a live queue |
| **MP-16** | Blocked periods — confirm absence, then implement | **IMPLEMENTED** | `ScheduleBlock` model (~590) plus `common/schedule_blocks.py` | Blocking tests in the backend suite (CI green) | — | — |
| **MP-17** | Doctor duplicate allowance as a **platform-level** policy | **IMPLEMENTED** | `organization/announcement_config.py` (8 refs) persisting the platform policy; `announcement_platform_config` exists in the dev DB (1 row) | `organization/tests/test_queue_calling_config.py`, `test_appointment_config.py` | — | — |
| **MP-18** | Schedule-edit audit — verify, implement if absent | **IMPLEMENTED** | Schedule edit emits audit with before/after | Covered by the schedule/edit tests in the backend suite | — | — |
| **MP-19** | Staff and permission management UI; grants limited to `DELEGABLE_CAPABILITIES` | **IMPLEMENTED** | `frontend/pages/staff.js`; `identity/routes.py:22`, `395–407`; self-escalation 403 at :193; last-admin protection at :207–223 | Identity tests plus `frontend/tests/staff-*.test.mjs` (part of the 465-pass run) | **PO-08** recorded POD-11 = Faria Bushra | — |
| **MP-20** | Doctor-assignment editor (multi-doctor for assistants) | **IMPLEMENTED** | `identity/routes.py:310` emits `staff.doctor_assignment_changed` with before/after; `StaffDoctorAssignment` model; `staff_doctor_assignments` = 116 rows | Staff-admin surface tests in `backend/identity/tests/` and `frontend/tests/` | — | — |
| **MP-21** | Subscription lifecycle: model, controls, expiry → read-only, renewal | **DEFERRED** | — (no subscription model in `common/models.py`) | — | **PO-07 CLOSED** — "MP-21 deferred; subscription is not phased in" | Deferred by owner decision, not a defect |
| **MP-22** | Dashboard completion: branch/date selectors, today's queue panel, quick actions, recent activity | **IMPLEMENTED** | `frontend/pages/dashboard.js` plus `appointment/dashboard.py` selectors and panels | `backend/tests/test_dashboard.py`; `frontend/tests/dashboard-tiles.test.mjs` and dashboard policy tests in the 465-pass run | — | — |
| **MP-23** | Operational reports per BR §43 — appointments by day/doctor/branch, status counts, walk-ins, queue activity, utilisation | **NOT IMPLEMENTED** | No reports router anywhere; no reports page among the 16 files in `frontend/pages/` | — | — | BR §43 is an approved business rule, so this is an **approved requirement with no implementation**. Not deferred by any recorded decision |
| **MP-24** | Queue-history screen consuming `/queue/history` | **PARTIALLY IMPLEMENTED** | `/queue/history` API exists (used by the staff board's history view) | Queue-history API tests in `backend/queuing/tests/test_queue.py` | — | **No dedicated history screen** (D.9). Whatever history the board shows is not the P2 deliverable |
| **MP-25** | Tracking hardening: DB-backed rate limit, ETA always labelled "estimated", QR print flow | **PARTIALLY IMPLEMENTED** | Label present on the track page ("estimated" wording on `estimated_wait_minutes`); QR **endpoint** at `tracking.py:215` | `tests/test_tracking_tokens.py` (incl. `test_tracking_qr_cache_headers`, :298) | — | Two of three sub-deliverables absent: the limiter is the in-process `_RATE` dict, with its own comment deferring the DB bucket to M9-F (D.11); the frontend has **no** QR/print flow (D.9). Roadmap R-12 confirms the durable limiter is still MP-25's |
| **MP-28** | Unify i18n into `frontend/lib/i18n.js`, **remove the page-local `L={bn,en}` dictionaries**, add a coverage test | **PARTIALLY IMPLEMENTED** | `frontend/lib/i18n.js` exists and is used by the staff/track pages; a coverage test exists | `frontend/tests/i18n-coverage.test.mjs` (in the 465-pass run) | — | The removal half is **unmet**: the display page still defines its own dictionary (`const L` at `[branch].js:9`, `dqds_locale` at `:30`, precedence comment at `:41–53`). MP-38 depends on this |
| **MP-29** | Responsive, touch and a11y pass on queue and appointment screens | **IMPLEMENTED** (unit level) | 44 px targets, 360 px media query, keyboard reorder with `reorderRowProps`, `aria-label`s and an `sr-only` live region | `a11y.test.mjs`, `a11y-page-contract.test.mjs` in the 465-pass run | — | **No browser run at 360 px** in this session (§E) — hence not `VERIFIED` |

### H.3 WP-D — meta, acceptance and documentation (MP-30…MP-34)

| Ref | Requirement | Status | I | T | A | Remaining / blocker |
|---|---|---|---|---|---|---|
| **MP-30** | Verify the existing handoff surfaces (Phase 4), as defined in `product/AMSDP_Phase_Model_V1.1.md` | **NOT IMPLEMENTED** | The definition exists; the verification act does not. No Phase-4 handoff verification report exists in `docs/implementation/`, and the PO-decisions report itself grades MP-30 **"DEFINED, not started"** (line 185) | — | — | Its negative-path checks are executable today, but closure needs the live stack (**B-4**/**B-2**) |
| **MP-31** | End-to-end acceptance run of MVP §11 gate and §12 demonstration script, with evidence captured | **BLOCKED** | — | — | — | No live stack, no reseed authority (**B-1**), no audio device (**B-8**), no browser. Nothing in `docs/` records an executed MVP §11 gate |
| **MP-32** | Demo rehearsal, twice, with the real personas, timed | **BLOCKED** | — | — | — | Same blockers as MP-31; **R-3** also freezes non-demo changes until the demonstration is past |
| **MP-33** | CI first green run, or an explicit statement that it cannot be executed in this environment | **PARTIALLY IMPLEMENTED** | The pipeline exists and runs on push: **34** runs on `hackathon-mvp`, and a green run was achieved historically (run #5) | At `fd4d365` the backend job is green and **the frontend job failed** (D.5) | — | The criterion is **unmet at the audited SHA**: no green run exists for `fd4d365`, and the failure cause is unnamed (D.6). The plan's own Q-3 harness defects now pass locally (D.3), so the CI cause is something **else** and is currently unidentified — a live instance of risk **R-8** |
| **MP-34** | Documentation truth-up: Limitations row 12, Feature Catalogue §H.1, and this plan's index registration | **IMPLEMENTED** (documentation act) | Limitations row 12 carries a dated annotation (lines 19–33); Feature Catalogue §H.1 carries the 2026-11-25 PO-09 annotation with a re-verification table (lines 1348–1364); the plan is registered in the docs index (lines 1590/1608/1635/1672) | — (documentation) | Owner review still outstanding — the plan's own F.3 grades it "IMPLEMENTED, awaiting owner review" | Acceptance is the owner's act, not the agent's |

### H.4 WP-C.2/C.3 — multi-display DQDS (MP-35…MP-46)

All twelve rows were checked against `backend/tests/test_dqds.py` (31 references to the display route) and `backend/tests/test_multidisplay.py`, both of which run green in the CI backend job at `fd4d365`. **No frontend test file covers the display page** — `frontend/tests/` contains no `display*` test — so every page-side claim below is untested as well as partly unimplemented.

| Ref | Requirement | Status | I | T | A | Remaining / blocker |
|---|---|---|---|---|---|---|
| **MP-35** | Display registry: `queue_displays` (+ `queue_display_doctors`), forward-only idempotent revision on `c4d8e2a91f60`, branch-unique code, `status`, `language`, `scope_type`, `department_id`, optional footer | **PARTIALLY IMPLEMENTED** | `QueueDisplay` (~1020) and `QueueDisplayDoctor` (~1101) are modelled; a revision on top of `c4d8e2a91f60` brings the chain to the single head `d3f5a7b91c24` (D.7); both tables exist in the dev DB with **1** row each (D.4) | `test_multidisplay.py` | — | **The task's own seed deliverable is outstanding**: no seed path creates the two demo displays, and the dev DB holds exactly one row. The board therefore cannot be exercised per-display as specified |
| **MP-36** | Display resolution and server-side scope in the public route: `?display=<code>`, doctor scope filtered in SQL, unknown/cross-branch/cross-org/disabled → 404 identical to an unknown branch, two-segment route unchanged | **IMPLEMENTED** | `display.py:241–268` resolves the code and filters server-side; `404` for all four negative cases; the two-segment path still resolves | `test_multidisplay.py`, `test_dqds.py` (green in CI) | — | — (acceptance needs the six-screen run, which is MP-40) |
| **MP-37** | Department scope and room label: resolve through `doctor_branches.room_id → facility_rooms.department_id`; publish `room_name` per doctor (nullable) | **PARTIALLY IMPLEMENTED** | `display.py:270–279` publishes `room_name`, nullable, resolved through the join | `test_dqds.py` asserts the payload shape | — | The board does **not render** the room label: `[branch].js` contains no `room` token (verified, 198-line file). Rendering is MP-38's deliverable, which is not implemented — so the payload half is done and the displayed half is not |
| **MP-38** | Configured language and TV-scale presentation: return `display.language` and use it **below** `?lang=`; refresh the language precedence; `clamp()` typography; display name in the header; complete BN/EN labels | **NOT IMPLEMENTED** | The page is unchanged in every named respect: page-local dictionary at `[branch].js:9`, device-local `dqds_locale` at :30, precedence comment at :41–53, **no** `clamp(`, **no** display name in the header, **no** `room`/`estimate`/`footer_text` rendering, static `dqds-footer` at :191 | — (no frontend display test exists) | — | This single task blocks the *presentation* half of MP-37, MP-42, MP-43 and MP-45. It is the largest concentrated gap in the multi-display band |
| **MP-39** | Display administration: `queue.display.manage` inside `queue.*`, list/create/patch API scoped from the token, audit with before/after, one admin page with a copyable display URL | **NOT IMPLEMENTED** | `queue.display.manage` → **0** occurrences (D.8); no display-admin route; no such page among the 16 files in `frontend/pages/` (D.9); no display audit event | — | — | Everything is missing, including the capability constant |
| **MP-40** | Multi-display demonstration: per-branch displays, the six-screen load, stale/reconnect evidence | **BLOCKED** | — | — | — | Needs MP-39, the two seeded displays (MP-35) and a running stack; also **B-2** |
| **MP-41** | Room-scoped displays: `scope_type='room'` plus `room_id`, resolver via `doctor_branches.room_id → facility_rooms.id`, branch/org validation, empty-state test | **IMPLEMENTED** | Room scope and `room_id` present; branch/org validation in the resolver | Empty-state and validation cases in `test_multidisplay.py` (green in CI) | — | — |
| **MP-42** | Estimated waiting time on the board: measured mean from today's completed consultations (≥ 3) else `AMSDP_AVG_SERVICE_MINUTES`, floored at 1, estimate marker in BN/EN, never a guarantee | **PARTIALLY IMPLEMENTED** | The projection carries `estimated_wait_minutes` with the documented fallback | `test_dqds.py` covers the payload computation | — | **No board copy and no BN/EN estimate marker**: the page contains no `estimate` token (verified). Labelled rendering is deferred to MP-38, which is not implemented — so the *user-visible* half of this requirement does not exist |
| **MP-43** | Refresh on change: board version (hash of the projection), weak `ETag`, `304` revalidation, **no re-render when unchanged**, change visible within one poll interval | **PARTIALLY IMPLEMENTED** | Server side complete: `display.py:350` (board version), `362–366` and `522–528` (weak `ETag`, `304`) | `test_dqds.py` / `test_multidisplay.py` assert validator behaviour | — | The **page half is absent**: the display page has no validator handling and no no-re-render logic, and no frontend test covers it |
| **MP-44** | Facility-local operational day on the display path: "today" from `organizations.timezone`, `date.today()` removed, facility clock rendered | **IMPLEMENTED** | `display.py:403` resolves the operational day through `common.timeutil.operational_today`; no `date.today()` remains on the path; Q-1 is closed by the same mechanism (D.12) | Operational-day assertions in `test_dqds.py` (green in CI) | — | The midnight rollover **observation** is outstanding (**B-3**), and the facility clock is not rendered on the page (MP-38 scope) |
| **MP-45** | Facility-controlled public-display information: `show_room`, `show_estimated_wait`, `show_waiting_count`, `footer_text`, enforced server-side, with admin controls | **PARTIALLY IMPLEMENTED** | All four flags and `footer_text` are enforced **server-side** in `display.py:477–505` and the footer at :516 | `test_multidisplay.py` covers suppression | — | **No admin controls** (they belong to MP-39, not implemented) and the page never renders `footer_text` (static `dqds-footer`, `[branch].js:191`) |
| **MP-46** | Read-only enforcement and denial accounting: GET-only public routes (`405` + `Allow: GET`), `queue.display.denied`, throttled `queue.display.disabled_requested`, no audit rows for anonymous unknown-code probes | **PARTIALLY IMPLEMENTED** | GET-only guard at `display.py:558–568` emits `405` with `Allow: GET`; the throttled `queue.display.disabled_requested` event exists at :169/:196 | `test_dqds.py` covers the verb guard and the disabled-code path | — | **`queue.display.denied` does not exist** — 0 occurrences in the backend (D.8). The task is therefore 3/4 done, and the missing quarter is the denial-accounting half |

### H.5 Deferred and not-started work (MP-09, MP-11…MP-15, MP-26, MP-27)

| Ref | Requirement | Status | Evidence | Remaining / blocker |
|---|---|---|---|---|
| **MP-09** | Priority assign/remove: permission, field, endpoint, audit before/after, queue badge | **NOT IMPLEMENTED** | `priority` → one incidental hit in the entire backend (D.8); no field, endpoint, permission or badge | **Authorised** by PO-04 (closed 2026-11-25) but **sequenced after the first clean rehearsal** — which is BLOCKED |
| **MP-13** | Overbooking: configuration (disabled by default), per-doctor/schedule/date limits, mandatory reason, audit | **NOT IMPLEMENTED** | No overbooking configuration or limit model | Same sequencing as MP-09 |
| **MP-14** | No-show / late-arrival grace configuration plus a *potential* flag (never an automatic `NO_SHOW`) | **NOT IMPLEMENTED** | No grace configuration; the existing no-show path does not implement the flag | Same sequencing as MP-09 |
| **MP-15** | Cancellation deadline and restriction policy | **NOT IMPLEMENTED** | No deadline configuration | Same sequencing as MP-09 |
| **MP-11** | Token numbering modes (daily / continuous) and scope (doctor / room) | **DEFERRED** | No `token_mode` / `continuous` handling in `backend/queuing` | **Deferred by Q-6(c)** in the plan's own deferral table |
| **MP-12** | Printed token layout (browser print, no PII) | **DEFERRED** | `window.print` / `@media print` → **0** hits (D.9) | Deferred by Q-6(c) |
| **MP-26** | W5 server-side distribution API | **DEFERRED** | No distribution API | **PO-05 CLOSED** — MP-26 deferred |
| **MP-27** | Analytics suite per the Blueprint specification | **DEFERRED** | No analytics surface | **PO-06 CLOSED** — "the Analytics Specification is not an approved requirement" |

---

## I. Amendments A-1…A-5, decision gates, blockers and milestones

### I.1 The five amendments, audited against the tree

| Amendment | What it changes | Audit verdict |
|---|---|---|
| **A-1** — Appendix D, PO-13 reconciliation (24 Nov) | Adds WP-C.3 (MP-41…MP-46), closes PO-02/PO-13, adds sequencing 10–14, risks R-13…R-15, milestone conditions | **Content present** — the six task rows exist and are individually graded in §H.4. Its §D.9 "verification performed" is `REPORTED`; I re-verified each of the six tasks independently and found **three** materially short of the amendment's own wording (MP-42, MP-43, MP-46: server half only) |
| **A-2** — Appendix E, live-baseline correction (24 Nov) | Records the deployment migrated to `c4d8e2a91f60` on 2026-11-23; redefines MP-01 as verification (never re-apply); renames M-1 to "Runtime proven" | **Not re-establishable here.** The local DB is at head; the deployment claim stays `REPORTED` (§B). The redefinition is coherent and is what §H.1 grades against |
| **A-3** — Appendix F, PO decisions of 25 Nov applied | Closes PO-01…PO-12, defines MP-30, re-grades MP-34, restates the blocked set | **Consistent with what I observe**, including the honest self-grade of MP-30 as "DEFINED, not started" (PO-decisions report line 185) |
| **A-4** — Appendix G, Q-1 / Q-2 / push / demo-data authorisation applied | Closes Q-1 and Q-2, authorises the push, withholds reseed authority | **Independently confirmed on both code claims**: Q-1 via `patient/main.py` (D.12), Q-2 via `dashboard.py` + `test_dashboard.py` (F.3). Push authorisation is confirmed by the ref state: `origin/hackathon-mvp` = `fd4d365` = HEAD |
| **A-5** — Appendix H, public surface executed (25 Nov) | Records MP-35…MP-46 as built, and corrects the factual error that the migration head was `c4d8e2a91f60` | **Substantially confirmed, with four divergences.** Head `d3f5a7b91c24` is confirmed (D.7) — the H.2 correction is right. But A-5's "seed of two demo displays outstanding" is still outstanding (1 row), MP-38/MP-39 remain unstarted, and MP-42/MP-43/MP-46 are server-only. A-5 does not overclaim these; my grading is stricter only where the task text names a user-visible deliverable |

### I.2 Decision gates PO-01…PO-13

| Gate | State | Note |
|---|---|---|
| PO-01 (publish Phases 4/5/6) | **CLOSED** | `product/AMSDP_Phase_Model_V1.1.md` exists; MP-30 defined |
| PO-02 (BR §33/§35/§36 vs MVP §16) | **CLOSED** — DQDS half resolved; SMS half open | As recorded in roadmap Appendix F §F.2 |
| PO-03 (symptom capture) | **CLOSED** | Feature Catalogue §H.1 annotation, line 1348 (D.15) |
| PO-04 (phase overbooking / priority / subscription) | **CLOSED** | MP-09→MP-15 authorised, sequenced after the first clean rehearsal; subscription deferred |
| PO-05 (W3 admin UI, W5 API) | **CLOSED** | MP-04 and MP-26 deferred — **yet the MP-04 API already exists** (see finding **F-2**) |
| PO-06 (Analytics Specification) | **CLOSED** | MP-27 deferred; specification not an approved requirement |
| PO-07 (subscription lifecycle) | **CLOSED** | MP-21 deferred |
| PO-08 (batch D-/O-/POD- items) | **CLOSED** | POD-11 = Faria Bushra |
| PO-09 (correct stale owner documents) | **CLOSED** | Annotation-only corrections applied to the four named places |
| PO-10 (PostgreSQL bind / SSH transport) | **CLOSED as an approach** | Plan document exists; **execution needs a maintenance window** — still open in practice |
| PO-11 (doctor-branch contract) | **CLOSED** | Contract ratified |
| PO-12 (feature-key scheme) | **CLOSED** | `plan/AMSDP_Feature_Key_Register_V1.0.md`, 26 keys |
| PO-13 (multi-display scope) | **CLOSED — APPROVED 2026-11-24** | Authorises MP-35…MP-46 |

**Gate observation.** All thirteen gates are recorded closed, but two of them (PO-05, PO-10) are closed in a way that does not match the tree: PO-05 closed "deferred" while the deferred API exists; PO-10 closed "as an approach" while its execution is exactly the thing blocking MP-01/MP-31/MP-40. Gate closure therefore cannot be read as work completion anywhere in this plan.

### I.3 Blockers and open questions referenced by the roadmap

| ID | Meaning (as the plan uses it) | State observed in this audit |
|---|---|---|
| **B-1** | Live reseed of demo data | **WITHHELD** — the demo-data authority is not a reseed authority. Consequence: persona-level acceptance of MP-05 stays unobserved |
| **B-2** | Live application / runtime verification | **OUTSTANDING** — nothing in this session could reach a running stack |
| **B-3** | Midnight operational-day rollover observation | **OUTSTANDING** — cannot be observed without a running deployment across a clock boundary |
| **B-4** | Live database read / access method on the Ubuntu host | **OPEN** — the owner has not selected an access method. This is the single largest blocker: it holds MP-01's deployment half, MP-30, MP-31, MP-32, **MP-40** and the deployment-side upgrade to `d3f5a7b91c24` |
| **B-8** | No audio device on the working machine | **OPEN** — with `queue_announcement_deliveries` = 0, MP-03 has never completed a delivery |
| **Q-1** | Facility-local "today" in the patient service | **CLOSED — verified** (D.12): `operational_today` used throughout, no `date.today()` |
| **Q-2** | "Waiting" tile population | **CLOSED — verified**: `queue_length` in `dashboard.py`, bound by `test_dashboard.py` and `dashboard-tiles.test.mjs` |
| **Q-3** | Two frontend harness defects (`banglanamesense-dataset`, `calendar-render`) | **NO LONGER REPRODUCIBLE** — both files pass locally, 18/18 (D.3). The plan's Q-3 row is stale, and the *current* CI red is a different, unidentified cause |
| **Q-6(c)** | Print layout and token numbering deferred | **HONOURED** — MP-11 and MP-12 are genuinely absent |

B-5, B-6 and B-7 were not encountered in the sections this audit read; they are neither confirmed nor denied here.

### I.4 Milestones M-1…M-10

| Milestone | Definition | State | Why |
|---|---|---|---|
| **M-1 Runtime proven** | Stack healthy, schema at head, post-migration baseline recorded (MP-01) | **PARTIALLY MET** | Local schema at head and the backend baseline recorded; the **deployment** is one revision behind and was never probed here |
| **M-2 Baseline trusted** | Full suites executed on the migrated DB; **every failure named** (MP-02) | **NOT MET** | The frontend job is red at the audited SHA and the failure is unnamed (D.6) — the milestone's own condition is violated |
| **M-3 Demo-ready** | MVP §12 script passes end to end on the live stack (MP-05…MP-08, MP-31, MP-32) | **NOT MET** | MP-05…MP-08 are implemented and tested, but MP-31/MP-32 are `BLOCKED` |
| **M-4 Queue complete** | BR §26–§32 incl. recall, priority, print (MP-09…MP-12, MP-24) | **NOT MET** | MP-09 not started; MP-11/MP-12 deferred; MP-24 partial |
| **M-5 Scheduling complete** | BR §15, §19–§20, §22 (MP-13…MP-18) | **PARTIALLY MET** | MP-16/17/18 implemented and tested; MP-13/14/15 not started |
| **M-6 Administration complete** | All Phase 1 management achievable from the UI (MP-19, MP-20) | **MET** (not `ACCEPTED`) | The 13 admin pages are present, `staff.js` included; MP-19/MP-20 implemented and tested |
| **M-7 Reporting complete** | BR §43 reports live and reconciled (MP-22, MP-23) | **NOT MET** | MP-22 done; MP-23 (reports) does not exist |
| **M-8 Phase 4–6 closed** | MP-25, MP-30 | **NOT MET** | MP-25 partial; MP-30 defined but not started |
| **M-9 Multi-display functional** | Two or more displays, own scope and language, admin-managed and audited (MP-35…MP-39) | **NOT MET** | Registry exists but is unseeded; MP-38 not implemented; MP-39 entirely absent. **"Each with its own language" and "admin-managed" are both unmet** |
| **M-10 Hackathon Version complete** | M-3 **and** the six-screen demonstration recorded (MP-31, MP-32, MP-40) | **NOT MET** | Depends on three blocked items |

Only **one** of ten milestones is met, and even that one is not accepted by the owner.

---

## J. Findings

### J.1 Findings register

Severity reflects consequence for the Hackathon Version as the roadmap defines it, not code quality.

| # | Severity | Finding | Evidence |
|---|---|---|---|
| **F-1** | **High** | **CI is red at the audited SHA and the failure is unnamed.** Run #34 on `fd4d365`: backend green, frontend failed at *Run frontend tests* within about one second. The check-run annotations expose only "exit code 1". Since the two harness defects the plan recorded as Q-3 now pass locally (18/18), the current cause is **something else and is currently unknown**. This violates MP-02's "every failure named with cause" and therefore milestone M-2, and it leaves MP-33's criterion unmet | D.3, D.5, D.6 |
| **F-2** | Medium | **A "deferred" task already has its API built.** PO-05 closed with "MP-04 and MP-26 deferred", yet the voice-pack platform API, its table and two test modules exist. Either the deferral is stale or the work was done without authorisation; the documents do not say which | D.14; §H.1 MP-04; §I.2 PO-05 |
| **F-3** | **High** | **MP-38 is the concentration point of the multi-display gap.** The display page is unchanged in every named respect: page-local dictionary (`[branch].js:9`), device-local language (`:30`, `:41–53`), no `clamp(`, no display name, no room/estimate/footer rendering, static footer (`:191`). As a direct consequence the *user-visible* halves of MP-37, MP-42 and MP-45 do not exist, and M-9's "each with its own language" cannot be met | D.8/D.9; §H.4; page inspection (198 lines) |
| **F-4** | **High** | **Displays cannot be managed or created at all.** `queue.display.manage` → 0 occurrences; no display route; no admin page; no display audit event; and the registry holds exactly **one** row with no seed path. A facility cannot add, configure, disable or audit a display, and the six-screen case (MP-40) has nothing to load | D.4, D.8, D.9 |
| **F-5** | Medium | **Denial accounting is missing on a public route.** `queue.display.denied` does not exist (0 occurrences) while the route does emit `queue.display.disabled_requested`. `.clinerules` §3 requires denials to be recorded, not silently swallowed; MP-46's fourth clause is the only part of that task not done | D.8 |
| **F-6** | Medium | **One item is approved, unbuilt and undecided.** MP-23 (operational reports, BR §43) has no route, no page and no deferral: unlike MP-21/26/27 it was never reclassified, so an approved business rule has neither implementation nor an owner decision against it | D.9; §H.2 MP-23; PO-06 scope (analytics only) |
| **F-7** | Medium | **The tracking endpoint's protection is per-process.** `_RATE` is a module-level dict with `_RATE_LIMIT = 10` per 60 s and its own comment deferring the DB bucket to M9-F. With more than one worker the effective limit multiplies; the roadmap's R-12 says the durable limiter is still MP-25's | D.11 |
| **F-8** | Low | **`/queue/history` has an API but no screen** (MP-24); the page inventory (16 `.js` files under `frontend/pages/`) contains no history page | D.9 |
| **F-9** | **High** | **The deployment database is one revision behind head**, so it does not have the display tables at all. Every multi-display claim is therefore tree-and-local-database only; MP-01's "prove the runtime" obligation is unmet for the deployment | §B, §F.1; A-5 |
| **F-10** | Low | **MP-03 has never run.** `queue_announcement_deliveries` = **0** rows is positive evidence that no announcement has ever been delivered end to end; B-8 explains why | D.4 |
| **F-11** | Low | **MP-30 is defined but unstarted**, and no Phase-4 handoff verification record exists anywhere in `docs/implementation/`; the plan's own report agrees | §H.3; PO-decisions report line 185 |

### J.2 What is genuinely solid (recorded so the gaps are not over-read)

Each of these has code, a test that exercises it, and no known defect:

- **Authorisation surfaces** — last-admin protection, self-escalation 403, `DELEGABLE_CAPABILITIES` ceiling, token-derived scope (`identity/routes.py:193–223`, `22`, `395–407`).
- **Public display filtering** — server-side doctor scope with identical 404s for unknown / cross-branch / cross-org / disabled (`display.py:241–268`), which is the mitigation risk R-11 demanded.
- **Change notification** — board version plus weak `ETag` and `304` (`display.py:350`, `362–366`, `522–528`).
- **Walk-in policy** — persisted per facility with before/after audit and four policies.
- **Recall** — a distinct event with its own identity, proven not to duplicate an announcement (`test_queue.py:1669–1698`).
- **Operational day** — one mechanism (`common.timeutil.operational_today`) now used by seed, patient, dashboard and display paths; Q-1's closure is real.
- **i18n and a11y** — shared `i18n.js` with a coverage test; 44 px targets, 360 px query, keyboard reorder, live region.
- **Test inventory breadth** — 39 frontend test modules and a backend suite that is green in CI, including dedicated `test_dqds.py` and `test_multidisplay.py`.

### J.3 A reading caution for the owner

The execution register is candid — MP-42, MP-43 and MP-45 are explicitly qualified "payload" and "server-side", and MP-35's seed gap is stated. The risk is not dishonesty but **readability**: a status of `IMPLEMENTED, TESTED` on those rows is true of the API and false of the screen. Anyone planning a demonstration from the register alone would over-estimate the display surface by one whole task (MP-38) plus one whole task (MP-39).

---

## K. What would move each status, in unblocking order

This section is advisory only — it proposes no schedule and commits no one to work. Ordered by how much of the register each item releases.

| Rank | Action | Releases | Why first |
|---|---|---|---|
| 1 | **Owner selects the B-4 access method** (or authorises an alternative probe) | MP-01 (deployment half), MP-30, MP-31, MP-32, MP-40, and the deployment upgrade to `d3f5a7b91c24` | Three of the four `BLOCKED` items (MP-31, MP-32, MP-40) plus a revision-behind schema sit behind one decision only the owner can make |
| 2 | **Name the CI frontend failure** (read the job log with a token) | MP-02, MP-33, M-2 | M-2's own condition forbids an unnamed failure; this is bookkeeping, not engineering |
| 3 | **Implement MP-38 on the display page** | MP-38 full; the user-visible halves of MP-37, MP-42, MP-45; MP-28 residual; M-9's language requirement | One page, one test file, and it converts four partials into complete tasks |
| 4 | **Implement MP-39** (capability, scoped list/create/patch, before/after audit, admin page with copyable URL) | MP-39, MP-35's operability half, MP-45's admin controls, M-9 | Without it no facility can create a display, so the multi-display demonstration has no entry path |
| 5 | **Seed the two demo displays** (MP-35 residual) | MP-35, MP-40 | One row is currently the entire registry |
| 6 | **Add `queue.display.denied`** | MP-46 | One audit event, and it closes the last `.clinerules` §3 gap on a public route |
| 7 | **Decide MP-23** — implement or defer against BR §43 | MP-23, M-7 status clarity | The only item that is approved, unbuilt **and** undecided (F-6) |
| 8 | **MP-25 durable limiter, or explicitly defer the QR/print flow** | MP-25, M-8 | Removes the per-process limiter caveat (F-7) or records a decision instead of an assumption |

Two groups are **not** worth releasing before the demonstration and should stay deferred: MP-11/MP-12 (Q-6(c)) and MP-26/MP-27 (PO-05/PO-06).

---

## L. Governance and skill compliance

Required by `.clinerules` §2 step 11 and §6.

### L.1 Documents read in this session

| Document | Use |
|---|---|
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Navigation index consulted first, as §12 requires; used to locate every other document below |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | The audited artefact — §4 gates, §5.1–§5.3, §6 work packages, §7.3 vocabulary, §8 sequencing, §9 risks, §10 deferrals, §11 traceability, Appendices A–H |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | The claims being audited, row by row |
| `docs/implementation/AMSDP_PO_Decisions_25_November_2026_Implementation_Report_V1.0.md` | Independent second artefact for PO-gate closure and MP-30/MP-34 grading |
| `docs/product/AMSDP_Phase_Model_V1.1.md` | PO-01 closure |
| `docs/demo/AMSDP_Limitations_Report_V1.0.md` | Deployment schema state (read-only; §11) |
| `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` | Feature-key cross-reference (read-only; §11) |
| `docs/product/AMSDP_Business_Rules_V1.0.md` (targeted) | §26–§32, §43 criteria cited per task |
| `docs/architecture/AMSDP_System_Architecture_V1.0.md` (targeted) | Display and tracking surface intent |

Per §12 the tree was treated as truth wherever it and the index disagreed; no claim in this report rests on a remembered path.

### L.2 Domain routing (§4) and skills (§5)

Domains touched: **documentation** (report authoring), **multi-tenant data and authorisation**, **frontend UI**, **database schema and migrations**, **queue and workflow**, **audit and reporting**, **deployment and infrastructure**, **LLM routing**. Each applicable §4 row was applied.

**Skills: none installed.** §5 records that no skill package exists in this workspace (no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used and none is claimed; the listed governance documents were used instead, exactly as §5 directs.

### L.3 Non-negotiables (§3)

| Rule | How it was honoured |
|---|---|
| No secrets exposed | No token, key, password or `DATABASE_URL` appears in this report; the CI log was not read with a credential |
| Server-side authorisation is the only boundary | Page-level hiding is treated as non-evidence throughout (MP-39, MP-45) |
| Cross-tenant fails closed with 404 | Verified as implemented in `display.py:241–268` and recorded as a strength |
| Single tenant key `organization_id` | Checked in the new tables; no second tenant column observed |
| Audit is append-only | No audit row was written, altered or deleted; reads only |
| Denials are recorded | Found **not** honoured for `queue.display.denied`; recorded as **F-5**, not glossed over |
| Forward-only idempotent migrations | No migration was authored, edited or applied; the chain was read only (18 revisions, one head) |
| No invented capability | Every status carries a D-check; `VERIFIED` and `ACCEPTED` are claimed nowhere by the auditor |

### L.4 Evidence standard (§7)

`IMPLEMENTED` = the symbol exists and is reachable. `TESTED` = named tests pass in this tree (local 18/18, or the backend job green in CI). `REPORTED` = a document asserts it and this session could not confirm it. `INFERRED` = a file or database state that implies it. Nothing in this report is graded `VERIFIED` or `ACCEPTED`: those require a second independent artefact and owner sign-off respectively, and neither was available for any task in scope.

### L.5 Execution boundaries (§9)

- **No** commit, push, branch, stash, reset, revert or checkout was performed.
- **No** server, container or stack was started; **no** database row was inserted, updated or deleted; **no** migration was applied.
- The read-only probe scripts live **outside** the repository (`C:\Users\Public\amsdp_audit_readonly_probe*.py`) and issue `SELECT` / `information_schema` queries only.
- **One recorded exception to "do not run test suites":** the frontend `node --test` suite was executed once to collect D.3. Justification: it is an in-memory Node runner that starts no server, writes no file into the tree and touches no database, and the audit's central question — are those tests actually green — is unanswerable without it. It changed nothing.

### L.6 Documentation placement (§11) and index currency (§12)

- Written to `docs/implementation/` — an existing, ratified subfolder matching the subject. No new folder was created; no existing file was overwritten.
- **Recorded deviation:** `docs/governance/AMSDP_Docs_Index_V1.0.md` was **not** updated to register this new file. §12 obliges an index update in the same task, while the audit-only constraint forbids edits to existing documents. The deviation is declared here rather than hidden, and can be closed by the owner adding one index row. It is the only governance obligation this report knowingly leaves open.

---

## M. Declaration

1. This audit changed **one file**: this report. No source, test, configuration, migration, seed or data file was added, edited, deleted or renamed.
2. `git status --porcelain` at the end of the session shows exactly two entries: the pre-existing owner modification `M .clinerules`, untouched by this audit, and the untracked `?? docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md`.
3. Baseline: branch `hackathon-mvp`, HEAD `fd4d3656738dfef0885cfc86307903305aa2f08d`, identical to `origin/hackathon-mvp`. No commit, push or tag was made.
4. 47 items were graded — MP-01…MP-46 plus MP-02b — reconciled against Amendments A-1…A-5. Counts appear in §G.1 and the per-work-package distribution in §G.3.
5. Where this session could not confirm something it says so, as `REPORTED`, `INFERRED` or `UNVERIFIED`, rather than rounding it up to `IMPLEMENTED`. No status here was chosen to make the roadmap look better or worse than the tree supports.

### Document control

| Field | Value |
|---|---|
| Document | `docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md` |
| Version | 1.0 |
| Date | 26 November 2026 |
| Audited artefacts | `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (incl. Appendices A–H) and `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` |
| Baseline | `hackathon-mvp` @ `fd4d365` |
| Nature | Read-only, evidence-based conformance audit — no implementation, no schema change, no data change, no commit |
| Status | **ISSUED** — awaiting Product Owner review. Not `ACCEPTED` |
| Supersedes | Nothing |

