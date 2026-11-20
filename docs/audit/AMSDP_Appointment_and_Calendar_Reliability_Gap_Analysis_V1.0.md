# AMSDP — Appointment and Calendar Reliability
## Phase 2 Gap Analysis (WP-2.1 … WP-2.7)

| Item | Value |
|---|---|
| Document | `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` |
| Version | 1.0 |
| Date | 2026-11-19 |
| Status | **ANALYSIS — read-only.** No product code, test, migration, configuration or governance document was modified. |
| Branch / commit inspected | `hackathon-mvp` @ `6d3acdf` (working tree dirty with the RBAC workstream; left exactly as found) |
| Scope | Appointment service (`backend/appointment/`), scheduling service (`backend/scheduling/`), calendar/scheduling read paths, appointment UI (`frontend/pages/appointments.js`, `frontend/components/AppointmentCalendar.js`, `frontend/lib/calendar/`) |
| Out of scope | Queue/DQDS/PQT behaviour except where an appointment transition hands off to the queue; notifications; Docker; SaaS planes |
| Governing sources | `.clinerules`; `docs/product/AMSDP_Business_Rules_V1.0.md`; `docs/product/AMSDP_MVP_SCOPE_V1.0.md`; `docs/governance/AMSDP_Engineering_Governance_Assessment.md`; `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Location rule applied | `.clinerules` §11 (authoritative docs tree, subject subfolder `docs/audit/`); no collision — the filename did not previously exist |
| Remediation outcome | **All nineteen findings were addressed on 2026-11-19** — see `docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md` (task `AMSDP-APPT-RELIABILITY-01`, `.clinerules` §12 registration: index Revision 32). Seventeen are closed (tested), and two are closed only in part: **F-01** shipped the application-level lock but not the database constraint (owner decision **Q2**), and **F-18** now states the consequence of an outside-session time but does not mark such a booking as unscheduled (**Q1**/**Q3**). This analysis below is unchanged: it remains a `CODE-READ` record of the tree as it was at `6d3acdf`. |

---

## 1. Purpose, scope and method

This document answers one question: **where is the Appointment and Calendar capability of the hackathon MVP unreliable, unsafe, or unproven, and in what order should those gaps be closed?**

It is a *gap analysis*, not an implementation. It contains no patches, no proposed diffs and no schema changes — only findings, evidence, and a four-stage roadmap.

### 1.1 Method

1. Read the governance router (`.clinerules`), the documentation index, the approved Business Rules and the MVP scope.
2. Read the implementation in full for the write paths (`create_appointment`, `update_appointment_status`, `reschedule_appointment`, `transfer_appointment`, `check_in_appointment`, schedule create/update, `available-slots`) and the read paths (`/appointments`, `/appointments/list`, `/appointments/matches`, `/appointments/{id}`) plus their shared predicate module (`appt_filters.py`).
3. Read the calendar UI and its derivation library (`grid.js`, `list.js`, `matches.js`) against the same predicates.
4. Cross-checked the authorization model (`common/auth.py`, `common/permissions.py`) route by route.
5. Cross-checked the persistence contract (`common/models.py`, the Alembic chain) for any constraint that could substitute for application-level enforcement.
6. Inventoried the test corpus for the two services and the frontend, then listed the tests that would have to exist to prove each finding.

### 1.2 Evidence vocabulary (`.clinerules` §7)

| Tag | Meaning |
|---|---|
| IMPLEMENTED | The code exists and is reachable. |
| TESTED | A named test in this tree exercises it. |
| VERIFIED | A second, independent artefact confirms it (live call, DB read, browser run). |
| ACCEPTED | The project owner has signed it. |

**Every finding in this report is `CODE-READ`, not `VERIFIED`.** Each was established by reading the implementation and its callers; none was reproduced against a running PostgreSQL database or a live service. **No test suite was executed** (`.clinerules` §9: suites are not run unless explicitly requested). A `CODE-READ` finding is a statement about what the code *will* do given the stated input — it is strong evidence, but the report does not claim more than that, and §8 lists the exact commands that would promote it.

### 1.3 A note on the work-package identifiers

`WP-2.1` … `WP-2.7` are carried from the Phase 2 programme brief. **They do not occur anywhere in this repository** — a repository-wide search for `WP-2.` returns no match in any document or source file, and the existing backlog (`docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md`) uses its own `P0/P1/P2` and `H0…` numbering. Each package below is therefore **defined by the code it governs**, so the owner can remap the numbering to the brief mechanically without invalidating any finding: the findings stand on their file-and-line citations, not on the grouping.


---

## 2. Baseline — what was inspected

### 2.1 Repository state at inspection

```
branch  : hackathon-mvp
HEAD    : 6d3acdf
dirty   : M backend/common/auth.py
          M backend/identity/main.py
          M backend/identity/routes.py
          M backend/identity/tests/test_identity.py
          M backend/queuing/tests/test_queue.py
          M backend/tests/test_sequence3.py
          M docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md
          M docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md
          ?? docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md
```

These nine entries are the RBAC workstream. **None was touched by this analysis**; the list was captured before work began and re-checked afterwards (§12).

### 2.2 Services and surfaces in scope

| Surface | Source | Role in the capability |
|---|---|---|
| Appointment API | `backend/appointment/main.py` (~1 120 lines) | Create (with capacity), read (grid), paged list, match index, detail, status transition, reschedule, transfer, walk-in, check-in |
| Shared read predicates | `backend/appointment/appt_filters.py` | One predicate set for grid + list + match index (`apply_branch_scope`, `apply_filters`, `row_context`, `match_index`) |
| Scheduling API | `backend/scheduling/main.py` | Schedules (create / list / get / update), `available-slots` |
| Clinic sessions | `backend/scheduling/sessions.py` | Recurring sessions with a chamber, projected into `schedules.slot_templates` |
| Authorization | `backend/common/auth.py`, `backend/common/permissions.py` | `require_permission`, `require_branch_access`, `branch_accessible`, role matrix |
| Persistence | `backend/common/models.py`, `backend/alembic/versions/` | `Appointment` shape and indexes |
| Calendar UI | `frontend/pages/appointments.js` (~1 300 lines) | Week/Day grid, List view, booking dialog, walk-in, cancel, check-in |
| Calendar derivation | `frontend/lib/calendar/{grid,list,matches}.js` | Slot expansion, capacity display, search/filter query building |
| Tests | `backend/appointment/tests/` (5 files, 108 test functions), `backend/scheduling/tests/` (36), `frontend/tests/` (15 `.test.mjs`) | Evidence base for §8 |

### 2.3 Repository documentation that already covers part of this ground

| Document | What it contributes | Relationship to this report |
|---|---|---|
| `docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md` | The F-1…F-7 diagnosis that produced `AMSDP-CALENDAR-FILTER-01` | **Its defects are fixed** — re-checked by reading (see §7.1). Referenced, not repeated. |
| `docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` | The RBAC closeout, including finding **8.3** (line 103): "`PATCH /status`, cancel, reschedule, and check-in look appointments up by org …; branch-scoped callers limited by queue entry branch on mutation", graded **NOT A DEFECT** | **F-08 challenges that row.** The stated mitigation does not hold on these routes: they touch no queue entry. See §6, F-08. |
| `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` | The discovery audit behind the Phase 1 permission matrix | Read; no conflict raised. |
| `docs/product/AMSDP_Business_Rules_V1.0.md` §4, §6, §17, §22, §23, §51 | Binding rules on tenant isolation, shared patient records, transfer, overbooking, capacity and double-booking | The authority for severity throughout §6. |

---

## 3. Executive summary

**The calendar reads are in good shape. The writes are not — and the gaps are narrower, but sharper, than the phase close-outs imply.**

The `AMSDP-CALENDAR-FILTER-01` work closed the read-side defects properly. One predicate module serves the grid, the paged list and the match index, so a filter cannot mean three things in three places (`appt_filters.py:196-221`). Branch confinement on reads is server-side and non-disclosing — a foreign branch gets the same `404` an unknown id gets (`appt_filters.py:181-189`). The display joins are tenant-scoped *inside* the join (`appt_filters.py:214-219`), so a retired or foreign patient/doctor/branch can never leak a name into a row. Slot derivation is one function shared by the dialog and the grid (`grid.js:122-177`), and the browser's "statuses that occupy a slot" set mirrors the server's exactly (`grid.js:30-32` ↔ `appointment/main.py:394-395`).

The risk is concentrated on the write side, in five themes:

1. **Capacity is counted, but never enforced as the rules require.** `create_appointment` counts active rows for one exact `start_time` string (`main.py:389-396`) and inserts afterwards (`:452`) with no row lock and no constraint behind it (`models.py:547,591-595`; `alembic/versions/5f3fce6757cf:128-129`). The comment above that count reads *"Concurrency-safe capacity check"* — it is not. The capacity is read from the template by **range** but counted by **string**, so each distinct minute inside one slot is its own bucket and the slot can hold `max_patients` per distinct time. Reschedule and transfer write a new time and re-check no capacity at all. → **F-01, F-03, F-04, F-11**

2. **A booking need not fall inside a slot the doctor works.** `start_time` is an unvalidated string on the model (`main.py:144-148`). The resolver refuses a time outside every clinic *session* (`:325-328`), which is a real guard — but when the doctor holds no active session that weekday it refuses nothing, and when a session exists but no template covers the minute, capacity silently drops to the template default of 1 (`:407-412`) instead of the configured value. A time of `"banana"` is stored as-is. → **F-02**, and the dialog invites the same shape when a day publishes no slots → **F-18**

3. **Write-path authorization trails the read side, and one route escapes the permission matrix.** `GET /appointments/{id}` and `POST /{id}/check-in` require authentication only (`:731-732`, `:883-885`), and `check-in` calls the transition function *directly*, so that function's `appointment.modify` dependency never runs (`:897`) — a doctor, whose role holds read-only appointment permissions, can check a patient in and create a queue entry. Every mutation loads by `organization_id` and never by branch. `create_appointment` never queries `Doctor` at all, while `transfer_appointment` does (`:400-406` vs `:1062-1064`) — the two routes disagree about whether a request-body id must be resolved. → **F-07 (Critical), F-05, F-06, F-08, F-09, F-10**

4. **One availability question, three different answers.** The grid filters templates by weekday and schedule status but not by effective dates (`grid.js:141-152`); `available-slots` ignores all three (`scheduling/main.py:191-215`); the appointment service's chamber lookup honours weekday and effective dates through clinic sessions (`appointment/main.py:316-329`). Template *contents* are never validated (`scheduling/main.py:32-37`), so malformed stored data reaches `int(...split(':'))` and raises `500` (`:192-197`). Schedule writes are branch- and tenant-checked — better than the appointment writes — but produce no audit row and swallow invalid dates. → **F-12 … F-16**

5. **The surface is polite but under-informed.** The list/grid read accepts an unbounded date range (→ F-17); a day that publishes no slots invites an arbitrary time the server cannot govern (→ F-18); a full slot is disabled showing `booked/capacity` with a capacity-only tooltip and no reason, and a server rejection is appended verbatim, in English, after a translated prefix (→ F-19, `appointments.js:564`). → **F-17, F-18, F-19**

**Tally (19 findings):** 1 Critical, 6 High, 9 Medium, 3 Low.

| Severity | IDs | One-line reason |
|---|---|---|
| Critical | F-07 | `check-in` bypasses `appointment.modify` and writes a queue entry — an authorization bypass, not a UX defect |
| High | F-01, F-03, F-04, F-05, F-06, F-08 | Non-atomic capacity; per-minute capacity buckets; reschedule ignores capacity; unvalidated `doctor_id`; branch assignment outside the actor's scope; org-wide mutation |
| Medium | F-02, F-09 … F-16 | Unvalidated time, detail-read permission gap, unvalidated transfer destination and time, unaudited and unvalidated schedule configuration |
| Low | F-17 … F-19 | Unbounded list window, the no-slot fallback affordance, full-slot and rejection messaging |

**What this means for the demo.** The happy path — search a patient, pick a doctor, pick a published slot, book, see it on the grid, check in, cancel — works, and with the shipped UI a single operator will not see a contradiction: the dialog only offers published slots. What will not survive a determined question is the claim *"capacity is enforced"*: two simultaneous requests, a reschedule into a full slot, or booking 09:01, 09:02, 09:03 into the same 09:00–09:15 slot with `max_patients = 1` all produce states BR §51 forbids. **Stages 1 and 2 of §9 exist to make that claim true before it is demonstrated.**

---

## 4. The seven work packages as the brief defines them

The brief names WP-2.1 … WP-2.7 but does not define them, and no artefact in this repository does — searching `docs/` for `WP-2` returns only the brief's own wording. §5 therefore maps each package to the capability the Business Rules describe, states how far the code satisfies it, and stays reversible: if the owner's package definition differs, the findings keep their IDs and move between packages. The mapping used throughout this analysis is:

| WP | Area | What "reliable" means here | State in this tree |
|---|---|---|---|
| WP-2.1 | Capacity and slot integrity | A slot cannot hold more than its configured capacity except through an authorised, reasoned, audited overbooking; a booking always belongs to a slot the doctor works | **Partial** — capacity is counted, not enforced (F-01, F-03, F-04, F-11), and slot membership is advisory (F-02, F-19) |
| WP-2.2 | Booking integrity | Every entity a booking names is resolved inside the caller's tenant and branch scope before the row is written | **Partial** — no `Doctor` lookup and no branch-scope check on create (F-05, F-06); the arbitrary-time affordance on a day with no slots feeds F-02 (F-18) |
| WP-2.3 | Appointment lifecycle | Transitions are whitelisted, permission-checked, audited, and consistent across routes | **Transitions sound; two doors open** — the whitelist and the audit trail are right, but `check-in` bypasses the permission and every mutation ignores branch scope (F-07 **Critical**, F-08) |
| WP-2.4 | Reschedule, cancellation and transfer | Every re-assignment path re-validates what create validates, and preserves history | **History sound** (original kept, `rescheduled_to` set, symptoms copied, audit written); **validation absent** (F-04, F-10, F-11) |
| WP-2.5 | Scheduling configuration | Configuration is validated at the boundary, audited, and is the single source of truth for availability | **Weakest package** — references are checked (branch, doctor, tenant: `scheduling/main.py:84-95`), contents are not; no audit; three availability derivations (F-12 … F-16) |
| WP-2.6 | Authorization and scope on appointment writes | Every write enforces tenant and branch scope server-side, denials are non-disclosing `404`, and the permission matrix is the only gate | **Partial** — reads are the model, writes are behind (F-05 … F-10); it also inherits the Critical, because `check-in`'s missing dependency is an authorization defect (F-07) |
| WP-2.7 | Calendar UX and error presentation | The screen cannot offer an action the server will refuse without saying why, in the user's language | **Cosmetic gaps** (F-17, F-18, F-19) |

### 4.1 Why WP-2.6 is not a separate stage of work

Five findings sit in WP-2.6 and four of them are the same fix seen from different routes: *resolve every request-body reference through a tenant- and branch-scoped query, then apply the actor's branch scope to the row you loaded.* F-07 is the exception and the more urgent one — it is a single dependency change (`get_current_user` → `require_permission("appointment.modify")`) plus the same check inside the idempotency shortcut. Treating authorization as its own work package would spread one helper across several milestones, which is how the asymmetry between the read and write paths arose in the first place; §9 therefore folds WP-2.6 into **Stage 1**, which touches `appointment/main.py` and calls existing helpers in `common/auth.py` / `common/permissions.py`, and nothing else. WP-2.7 collapses into **Stage 4** for the same reason: its findings depend on Q1's answer and on the empty states Stage 3 introduces.

The packages are therefore presentation, not schedule: **four stages, seven packages**, mapped per stage in §9.

---

## 5. Gap matrix

Class: **DEFECT** = the code contradicts a binding rule or its own stated contract; **GAP** = a required capability is missing; **HARDENING** = correct today by convention only; **POLISH** = UX/consistency. A finding appears under every work package it belongs to; repeated rows carry `*` and are counted once in §5.8.

### 5.1 WP-2.1 Capacity and slot integrity

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-01 | Capacity is count-then-insert: no row lock, no constraint, and the preceding comment calls the count "concurrency-safe". The daily serial is `count(*) + 1` on the same pattern | `appointment/main.py:389-396` → `:452`; `:426-428`; `models.py:547,591-595`; `alembic/versions/5f3fce6757cf:128-129` | DEFECT (BR §23.7, §23.8, §51) | High |
| F-03 | Capacity is taken from the template by **range** but counted by **exact string**, so each distinct time inside one slot is a fresh bucket and a slot can hold `max_patients` per distinct minute | `appointment/main.py:389-396` vs `:407-412` | DEFECT (BR §23.7, §23.9, §51) | High |
| F-04 | Reschedule writes a new `start_time` with no capacity check at all; `_resolve_location` guards the session window, nothing guards the seat | `appointment/main.py:829-847` (`:815-817`, `:829-836`) | DEFECT (BR §22.4-22.6, §23.7) | High |
| F-02 | `start_time` is an unvalidated `str`: no format check, and a booking whose time no template covers silently gets the hard-coded default capacity 1 instead of the configured value; when the doctor holds no active session that weekday, any string is accepted | `appointment/main.py:144-148`, `:299`, `:310-329`, `:400-412` | DEFECT (BR §22.9, §23.4-23.6) | Medium |
| F-11 | Transfer writes `start_time = data.new_start_time` while the chamber was resolved for `data.new_start_time or orig.start_time` — the snapshot can describe a time the row does not carry — and re-checks no capacity | `appointment/main.py:1072-1076` vs `:1081` | DEFECT (BR §17.4, §22.5) | Medium |
| F-19 | A full slot is disabled showing `booked/capacity` with a capacity-only tooltip and no reason; a server rejection is appended verbatim in English | `appointments.js:1022-1032`, `:564`; `grid.js:160-177` | POLISH | Low |

### 5.2 WP-2.2 Booking integrity

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-05 | `create_appointment` never queries `Doctor` — a request-body `doctor_id` is written to the row unvalidated, so an appointment can name a doctor in another tenant. `transfer_appointment` performs exactly this lookup (`:1062-1064`); create does not, and `can_access_doctor` is not called on either path | `appointment/main.py:400-406` vs `:1062-1064`; `common/permissions.py` | DEFECT (BR §4, §22.7; `.clinerules` §3) | High |
| F-06 | The appointment's branch is taken from the resolved clinic/session, else from a schedule that may belong to **another branch of the same org**, else the token branch — and the result is never checked with `branch_accessible`. When the actor's branch has no schedule for that doctor, the resolver falls through to any schedule in the organization | `appointment/main.py:305-314`, `:431-439`; unused helpers `common/auth.py:430-448`; contrast `scheduling/main.py:84-85` | DEFECT (BR §6.3; `.clinerules` §3) | High |
| F-18 | When the chosen day publishes no slots the dialog invites a free-text time (`<input type='time'>`), which is exactly the shape F-02 describes; the grid then has no slot to attach capacity to | `appointments.js:1011-1018`; `grid.js:160-177` | GAP | Low |

### 5.3 WP-2.3 Appointment lifecycle

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-07 | `check-in` is gated on authentication only, and calls `update_appointment_status` **directly**, so the `appointment.modify` dependency that guards `PATCH /{id}/status` never runs. A doctor — appointment read-only — can check a patient in, and the route then creates a queue entry | `appointment/main.py:883-885`, `:891-897`; guard on the equivalent route `:748-750`; `common/permissions.py:96-106` | DEFECT (BR §8, §10; `.clinerules` §3) | **Critical** |
| F-08 | Every mutation loads by `organization_id` only — status, cancel, reschedule, transfer, check-in — so a branch-scoped actor refused a cross-branch *read* can still mutate the same row, and check-in writes a queue entry filed in that branch | `appointment/main.py:249-265`, `:753-755`, `:808-810`, `:909-911`, `:1053-1055` vs `appt_filters.py:181-189` | DEFECT (BR §6.3; `.clinerules` §3) | High |

The lifecycle itself is sound and is the part a fix must not disturb: `VALID_TRANSITIONS` refuses illegal moves (`:244-246`), the transition appends to `status_history` with actor and reason (`:757-761`), writes an audit row before commit (`:763-768`), and revokes tracking tokens when the visit ends (`:769-772`). `cancel` reuses it with a mandatory reason (`:791-797`).

### 5.4 WP-2.4 Reschedule, cancellation and transfer

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-04* | Reschedule re-resolves the chamber but checks no capacity, so a full slot accepts a rescheduled patient | `appointment/main.py:829-836` | DEFECT | High |
| F-11* | The new row stores `data.new_start_time` (may be `None`) while the chamber was resolved for the fallback time; no capacity check | `appointment/main.py:1076` vs `:1081` | DEFECT | Medium |
| F-10 | Transfer's `new_branch_id` is used as a resolver filter and otherwise written verbatim: it is never checked against `Branch` or against `branch_accessible`, so an unknown or out-of-scope branch produces a row no branch-scoped read can return | `appointment/main.py:1074-1077` | DEFECT (BR §6.3, §17.4) | Medium |

What is right here and should stay: the original is never mutated destructively — it moves to `RESCHEDULED`, keeps its history, gains `rescheduled_to`, and its symptoms are copied forward (`:818-826`, `:856`, `:851-854`); both paths audit with before/after; transfer resolves the target doctor inside the tenant (`:1062-1064`).

### 5.5 WP-2.5 Scheduling configuration

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-12 | Schedule create and update write no audit row — `record_audit` is not imported by the scheduling service at all | `scheduling/main.py:96-101`, `:155-166` | GAP (BR Part X) | Medium |
| F-13 | Invalid `effective_from` / `effective_to` are swallowed by a bare `except`: on create the value silently becomes `None`; on update nothing is written and the previous date is kept — both answer `200` | `scheduling/main.py:72-78`, `:158-163` | DEFECT (BR §22.8) | Medium |
| F-14 | `slot_templates` contents are never validated (`HH:MM` shape, start < end, duration > 0, `max_patients` ≥ 1, weekday range, overlap), yet `available-slots` parses them with `map(int, …split(':'))` and `range(…, dur)`: malformed stored data is a `500` | `scheduling/main.py:32-37`, `:192-197` | DEFECT (BR §23.3, §23.9) | Medium |
| F-15 | `available-slots` ignores `day_of_week`, `effective_from`/`effective_to` and `status`, and issues one `count()` query per slot inside the expansion loop | `scheduling/main.py:191-215` (`:200-205`) | DEFECT (BR §23.3, §23.9) | Medium |
| F-16 | Three derivations of "is this slot available" disagree: the grid honours weekday and schedule status but not effective dates; `available-slots` honours none of them; the appointment service honours weekday and effective dates via sessions — so the dialog can offer a slot the server refuses with a `422` | `grid.js:141-152`; `scheduling/main.py:191-215`; `appointment/main.py:301-329` | DEFECT (BR §22.9, §23.3) | Medium |

Credit where it is due and should be preserved: `create_schedule` and `update_schedule` *do* enforce `branch_accessible`, and do resolve `Doctor` and `Branch` inside the tenant (`scheduling/main.py:84-95`, `:151-154`). These are the checks the appointment write paths lack (F-05, F-06) — the same codebase contains both the right pattern and its absence.

### 5.6 WP-2.6 Authorization and scope on appointment writes

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-07* | Permission bypass on `check-in` | `appointment/main.py:883-885`, `:897` | DEFECT | **Critical** |
| F-05* | `doctor_id` never resolved in the tenant on create | `appointment/main.py:400-406` | DEFECT | High |
| F-06* | Branch scope unenforced on create | `appointment/main.py:305-314`, `:431-439` | DEFECT | High |
| F-08* | Mutations org-scoped only | `appointment/main.py:249-265`, `:753-755`, `:808-810`, `:909-911`, `:1053-1055` | DEFECT | High |
| F-09 | `GET /appointments/{id}` requires authentication only — not `appointment.read` — and applies no branch scope, so any authenticated principal can read any appointment's detail in the organization, including the recorded symptoms and onset | `appointment/main.py:731-736` | DEFECT (BR §8; `.clinerules` §3) | Medium |
| F-10* | Transfer destination branch unvalidated | `appointment/main.py:1074-1077` | DEFECT | Medium |

The tenant boundary on **reads** is intact and is the reason F-05 is High rather than Critical: `appointment_rows` scopes every join by `organization_id` (`appt_filters.py:210-221`), so a foreign `doctor_id` renders no name and discloses nothing. What is broken is the write: an id the caller never proved they may name is stored.


### 5.7 WP-2.7 Calendar UX and error presentation

| ID | Gap | Evidence (file:line) | Class | Sev |
|---|---|---|---|---|
| F-17 | `GET /appointments` accepts an unbounded `date_from`/`date_to` pair: no default window, no maximum span, so one request can scan the tenant's whole history | `appointment/main.py:495-503`, `:532-541` | HARDENING | Low |
| F-18* | The no-slot fallback invites a time the server cannot govern | `appointments.js:1011-1018` | GAP | Low |
| F-19* | Full-slot and rejection messaging | `appointments.js:1022-1032`, `:564` | POLISH | Low |

### 5.8 Totals by work package and severity

| WP | Critical | High | Medium | Low | Distinct findings |
|---|---|---|---|---|---|
| WP-2.1 | — | F-01, F-03, F-04 | F-02, F-11 | F-19 | 6 |
| WP-2.2 | — | F-05, F-06 | — | F-18 | 3 |
| WP-2.3 | F-07 | F-08 | — | — | 2 |
| WP-2.4 | — | (F-04) | F-10, (F-11) | — | 3 |
| WP-2.5 | — | — | F-12, F-13, F-14, F-15, F-16 | — | 5 |
| WP-2.6 | (F-07) | (F-05), (F-06), (F-08) | F-09, (F-10) | — | 6 |
| WP-2.7 | — | — | — | F-17, (F-18), (F-19) | 3 |
| **All packages** | **1** | **6** | **9** | **3** | **19** |

Parentheses mark a finding already counted under its primary package. Two readings matter for sequencing: the single Critical (F-07) is a permission-matrix defect rather than a capacity defect, and it is also the cheapest fix in the set — one dependency and one internal call — which is why Stage 1 is short.

---

## 6. The findings, one by one

Every finding below was established by reading the code in this tree at `hackathon-mvp` (`6d3acdf`) and re-read before this document was finalised. **None was proved by execution** — §8 lists the tests that would do that, and Appendix A records where each claim's evidence sits. Where a claim depends on runtime behaviour I say so and mark it as inference rather than fact. Findings are numbered F-01 … F-19 and keep those numbers wherever they are cited.

### F-01 — Capacity is counted, then written, and the comment calls that concurrency-safe

**Severity: High · WP-2.1 · DEFECT**

**What the code does.** `create_appointment` runs one `count()` over the active statuses for `(doctor_id, appointment_date, start_time)` (`appointment/main.py:389-396`), derives `effective_capacity` from the slot template (`:400-418`), refuses with `422` when `existing >= effective_capacity` (`:419-423`), and then constructs and adds the row (`:436-452`). Nothing between the count and the insert holds a lock; nothing in the schema forbids the duplicate.

**Evidence.**
- `appointment/main.py:389` — the literal comment `# Concurrency-safe capacity check:` above a plain `count()`; no `.with_for_update()` anywhere in the function.
- `appointment/main.py:436-452` — the `Appointment(...)` construction and `session.add(appt)`; the row is written after the read, in the same transaction, with no locking read in between.
- `appointment/main.py:426-428` — the daily serial is `count(*) + 1` on the same read-then-write shape, so two concurrent bookings can also collide on `serial_number` and `token_number`.
- `backend/common/models.py:547` — `start_time` is `String(10)`, nullable, no uniqueness pairing.
- `backend/common/models.py:591-595` — the `Appointment` indexes are search/support indexes; none is a partial unique or exclusion constraint on `(doctor_id, appointment_date, start_time)`.
- `backend/alembic/versions/5f3fce6757cf:128-129` — the initial schema creates those same non-unique indexes, and no later revision in the chain adds a capacity constraint.

**Why it matters.** BR §23.7 requires capacity to be validated *atomically at save time* to prevent concurrent overbooking; §23.8 forbids this exact shape and names "transactions, constraints or equivalent concurrency-safe mechanisms" as the requirement; §51 makes it an acceptance criterion. Under the default `READ COMMITTED` isolation two requests both read `existing = 0` for a capacity-1 slot and both proceed. The comment is the damaging part: a reviewer skimming the function reads "concurrency-safe" and stops looking. This is the only finding in the set that a normal demo cannot reveal (§3, "What this means for the demo").

**How to prove it.** Two threads posting to `POST /api/v1/appointments` for the same doctor/date/`start_time` on a capacity-1 slot: both return `201` and the count becomes 2. See T-1 in §8.3. The claim is inference from the isolation level and the absence of a lock; it is falsifiable in one test and should be falsified or confirmed before a fix is designed.

**Direction (not a patch).** Pick one mechanism and make the comment true: a partial unique index for capacity-1 slots plus a `SELECT … FOR UPDATE` on the slot row for capacity-N, or a serialisable transaction with retry. The serial/token allocation at `:426-428` needs the same treatment in the same change, and the choice belongs in the migration so the next reader sees the guarantee where the schema lives.


### F-02 — A booking's time is an unvalidated string, and capacity silently falls back to 1 when no template covers it

**Severity: Medium · WP-2.1 · DEFECT**

**What the code does.** `start_time` is `str | None` on `AppointmentCreate` (`appointment/main.py:144-148`) with no format validation. `_resolve_location` compares it lexicographically against session rows (`:299`, `:324`) and refuses a time inside no session (`:325-328`) — but only when the doctor *has* an active session that weekday (`if covering and slot and not matched`). Capacity is then read by scanning templates for one where `t["start_time"] <= data.start_time < t["end_time"]` (`:407-412`); if none matches, `max_capacity` stays at the hard-coded `1` seeded on `:406`.

**Evidence.** `appointment/main.py:144-148` (the model), `:299` (`slot = start_time or ""`), `:310-329` (the session guard and its `covering` precondition), `:406` (`max_capacity = 1`), `:407-412` (template range match); `scheduling/main.py:32-37` (templates type their times as plain `str`, with no format constraint).

**Why it matters.** Two defects share one cause — the time is never treated as a slot reference. First, a malformed value is stored: with no active session that weekday, `"banana"` returns `201`, is written to a `String(10)` column, and then sorts and buckets unpredictably in every read (`grid.js` sorts by string; `bucketAppointments` keys on the raw value). Second, configuration is not honoured: a doctor with `max_patients = 4` on a 09:00–10:00 template booked at 10:30 — inside the session, outside the template — gets capacity 1, the configured number silently replaced by a constant. BR §22.9 asks for a clear explanation when a booking cannot be granted; here it is granted, on a different capacity from the one configured. The *deliberate* exemption recorded at `:1000-1010` matters to this finding's reading: a walk-in outside a session degrades to "no chamber" by design, so "no chamber" is not itself a defect — but "a scheduled booking with an uninterpretable time" is.

**How to prove it.** `POST /api/v1/appointments` with `start_time = "banana"` for a doctor holding no session on the target weekday → `201`, and the row appears in the dialog's bucket map under the key `"banana"`. See T-2.

**Direction.** Validate `start_time` as `HH:MM` at the model boundary (one `pattern=` on the Pydantic field closes the malformed case), and make the capacity lookup fail loudly rather than defaulting when a session exists but no template covers the minute. A booked time that no configured template describes is a configuration error and should say so.

---

### F-03 — Capacity is granted per distinct minute, not per slot

**Severity: High · WP-2.1 · DEFECT**

**What the code does.** The count filters on exact equality — `Appointment.start_time == data.start_time` (`appointment/main.py:393`) — while the capacity for that booking is read from the template that *contains* the time (`:408`). The guard compares the count of one string against the capacity of one range.

**Evidence.** `appointment/main.py:389-396` (exact-string count) vs `:407-412` (range-based capacity); `scheduling/main.py:197-205` (the same split on the read side: slots are enumerated in `dur`-minute steps, then counted with `start_time == st`).

**Why it matters.** A 09:00–10:00 template with `slot_duration_minutes = 15` and `max_patients = 1` publishes 09:00, 09:15, 09:30, 09:45 — and also accepts 09:01, 09:02, 09:03, each with capacity 1, because each is its own bucket inside the same template range. The arithmetic BR §23.7/§23.9 describe — "a slot's capacity" — is therefore multiplied by the number of distinct times a client chooses to send, without a single concurrent request and without breaking any check the code performs. The grid then renders `4/1` in a slot labelled capacity 1. This is the most easily demonstrated overbooking path in the system: no race, no privileged role, no unusual client — just a time inside the slot that is not the slot's own start.

**How to prove it.** Book 09:00 on a capacity-1 slot, then 09:01, then 09:02 → three `201`s for one slot. See T-3.

**Direction.** Count capacity against the *slot*, not against a string: either normalise `start_time` to a published slot start on write (rejecting or snapping a non-slot time), or count with a range predicate matching the template window. The read side must use the same rule or the badge and the guard will disagree again — F-16's theme arriving through a different door.

---

### F-04 — Reschedule moves a patient into a slot without re-checking capacity

**Severity: High · WP-2.1 · DEFECT**

**What the code does.** `reschedule_appointment` loads the original by `(id, organization_id)` (`appointment/main.py:808-810`), refuses closed statuses (`:811-812`), computes the new day's serial as `count(*) + 1` (`:815-817`), marks the original `RESCHEDULED`, resolves the chamber for the new day/time (`:829-833`), and inserts a new `BOOKED` row (`:837-847`). It never counts how many active appointments already occupy the target slot, and never compares any count against the template's `max_patients`.

**Evidence.** `appointment/main.py:829-847` — resolver call, new-row construction, insert; the only capacity-shaped query in the function is the serial count at `:815-817`, which counts the whole *day*, not a slot. Contrast `create_appointment:389-423`, where the guard exists.

**Why it matters.** The rule the create path implements does not apply to the path most likely to be used when a clinic is full — moving a patient into a slot someone else already holds. BR §22.4-§22.6 make reschedule a first-class booking operation subject to the same capacity rules, and §23.7's atomicity requirement is meaningless if a second write path skips the check altogether. The session-window `422` from `_resolve_location` (`:325-328`) prevents an off-session time but says nothing about seats, so a full 4-seat slot accepts a fifth patient silently and the grid renders `5/4`.

**How to prove it.** Fill a capacity-1 slot through create, then reschedule a second appointment into it → `200` and two active rows in the slot. See T-4.

**Direction.** One capacity guard, called by every path that writes a time: create, reschedule, transfer (F-11), and walk-in where a slot applies. Authorised overbooking needs an explicit parameter, a reason and an audit event (§22.4-22.6); a silent one should not be reachable from any route.

---

### F-05 — A booking can name a doctor the tenant has never resolved

**Severity: High · WP-2.2 / WP-2.6 · DEFECT**

**What the code does.** `doctor_id` arrives in the request body. `create_appointment` validates the patient with an organization filter (`appointment/main.py:376-378`) and the symptoms (`:383-385`), then uses `data.doctor_id` directly — as the capacity filter (`:391`), as the schedule/session lookup key (`:402-405`), and as the value written to the row (`:439`). There is no query against `Doctor` anywhere in the function. `transfer_appointment` does exactly that query before using a new doctor (`:1061-1064`), which is what makes the omission in create a defect rather than a convention.

**Evidence.** `appointment/main.py:400-406` (create: resolver called with the raw body value, no `Doctor` lookup); `:1061-1064` (transfer: `Doctor.id == … AND Doctor.organization_id == auth.organization_id`); `backend/common/permissions.py` (`can_access_doctor`, defined and not called from any appointment write route).

**Why it matters.** `.clinerules` §3 states the non-negotiable plainly: *"the principal's org/branch is derived from the authenticated token, never trusted from the request body."* A foreign `doctor_id` is a request-body value naming an entity outside the tenant, and it is stored. The read side limits the damage — `appointment_rows` scopes every join by `organization_id` (`appt_filters.py:214-219`), so the foreign doctor's name is not disclosed and the row renders its id — but the record is wrong three ways: it violates BR §4's tenant isolation at the write; it makes the appointment unattributable to a real clinician; and it pollutes the per-doctor capacity and serial counts (`:389-396`, `:426-428`) with rows keyed to an id the tenant does not own. A stale tab or a copied payload reaches this state without malice, which is why the check belongs on the server rather than in the dialog.

**How to prove it.** Create an appointment whose `doctor_id` belongs to another organization → `201` today, with no clinician resolved for the row. See T-5. Expected behaviour is the non-disclosing `404` for an unknown id, not `403` and not a descriptive `422` (`.clinerules` §3) — though `transfer` currently answers `422 "target doctor not found"`, so the two routes should be made to agree, on the non-disclosing answer.

**Direction.** Resolve every referenced entity — doctor, branch, department, patient — through a tenant-scoped query before it is used, in one helper that all appointment write routes call, and let an out-of-tenant id be indistinguishable from a missing one.

### F-06 — The appointment's branch is chosen by the resolver, not by the actor's scope

**Severity: High · WP-2.2 / WP-2.6 · DEFECT**

**What the code does.** The branch written to the row is derived, not validated: `branch_for_appt` is the clinic session's branch when one matched, else the resolved schedule's branch, else the token branch (`appointment/main.py:431-435`). The resolver prefers a schedule in the actor's branch (`:305-306`) but **falls through to any schedule in the organization** when none matches (`:310-314`), and the session query applies a branch filter only when the token carries one (`:321-322`). Nowhere does the code call `branch_accessible` on the outcome.

**Evidence.** `appointment/main.py:305-314` (preferred branch, then org-wide fallback), `:321-322` (session filter only when `auth.branch_id`), `:431-439` (derivation and write); the unused helpers `common/auth.py:430-448`; the read-side model `appt_filters.py:181-189`; and the same codebase doing it correctly for schedules at `scheduling/main.py:84-85`.

**Why it matters.** `.clinerules` §3 requires cross-branch access to fail closed, and BR §6.3 permits branch-level restriction of what a user may "view or operate on". The asymmetry is the tell: the same receptionist asking to *read* branch Y is refused non-disclosingly by `apply_branch_scope`, while asking to *write* into branch Y succeeds whenever the doctor has a schedule there and the actor's own branch does not — precisely the situation of a doctor who works at two branches, which is the feature the fallback exists to serve. A write is the more consequential operation, so the weaker check sits on the wrong side. The result is a row the actor cannot then read back.

**How to prove it.** Authenticate as a branch-X receptionist; book a doctor who holds a schedule in branch Y and none in X → `201`, `branch_id = Y`, and the row is invisible in the creator's own list. See T-6.

**Direction.** Derive the branch as now, then require `branch_accessible(auth, branch)` before the insert and answer `404` when it fails — the two lines `create_schedule` already uses. If the intended behaviour is "a receptionist may book into any branch of the organization", that is a Q4 decision and should be written down rather than left as an accident of a fallback loop.

---

### F-07 — `check-in` bypasses the permission that guards every other status change

**Severity: Critical · WP-2.3 / WP-2.6 · DEFECT**

**What the code does.** `PATCH /api/v1/appointments/{id}/status` is declared with `Depends(require_permission("appointment.modify"))` (`appointment/main.py:748-750`). `POST /api/v1/appointments/{id}/check-in` is declared with `Depends(get_current_user)` (`:883-885`), forces `data.status = "CHECKED_IN"` (`:886`), and then calls `r = update_appointment_status(appointment_id, data, auth)` — the *function*, not the route (`:897`). FastAPI resolves dependencies when routing, so calling the function directly runs its body with whatever `auth` object it is handed; the `require_permission("appointment.modify")` dependency is never evaluated. The route then continues in its own session to allocate a token and insert a queue entry (`:919-930`), i.e. a write in another service's table.

**Evidence.** `appointment/main.py:883-885` (`get_current_user`), `:897` (direct call), `:748-750` (the same transition behind `appointment.modify`), `:919-930` (`allocate_daily_token` + `QueueEntry` insert), `backend/common/permissions.py:96-106` (the role matrix: doctors hold appointment *read*, not *modify*).

**Why it matters.** This is the only finding where an authenticated user performs an action their role forbids, and it is the only one rated Critical. The route has two effects, both intended and both write-side: it advances the appointment's state machine and creates a queue entry that the queue board will act on. Idempotency (`:891-895`) does not narrow the hole — it only short-circuits a second check-in of an already-checked-in row. The comment at `:898` says the queue entry is created "with the *same* token authority, history and audit trail as `POST /api/v1/queue/check-in`", which is true and makes the bypass sharper: the platform has a guarded queue check-in and an unguarded one on this route. A doctor can therefore put their own patient into the queue and change the visit's status; whether that is *desirable* for a doctor is a Q4 product question, but as written it is not a decision — it is the absence of a dependency.

**How to prove it.** Authenticate with a role that has `appointment.read` but not `appointment.modify` (the doctor role, `common/permissions.py:96-106`) and `POST /{id}/check-in` → `200`, status `CHECKED_IN`, a `QueueEntry` created, and an audit row whose `actor_role` is the read-only role. See T-7. The expectation to assert is `403` for that role, matching `PATCH /{id}/status`.

**Direction.** Change the dependency to `require_permission("appointment.modify")` and stop the internal call from re-entering the route function — hoist the transition into a helper that takes an already-authorised actor, so a future route cannot call it without having passed a guard. If doctors *should* be able to check in their own patients, express that as a permission granted to the role, not as a route that skips the matrix.

---

### F-08 — Every mutation is tenant-scoped and none is branch-scoped

**Severity: High · WP-2.3 / WP-2.6 · DEFECT**

**What the code does.** Each write route loads its row with one filter: `Appointment.id == …` and `Appointment.organization_id == auth.organization_id` — status (`appointment/main.py:753-755`), reschedule (`:808-810`), check-in's second lookup (`:909-911`), transfer (`:1053-1055`) — and the shared helper `_scoped_appointment` does the same (`:249-265`, docstring: "The appointment if it belongs to the caller's organization, else None"). No route compares the row's `branch_id` to the actor's branch.

**Evidence.** The four loads above; `_scoped_appointment:249-265`; the read-side rule they contradict, `appt_filters.py:181-189` (`apply_branch_scope`: a branch-scoped actor naming another branch gets `404`); `common/auth.py:430-448` (`branch_accessible`, unused here).

**Why it matters.** A branch-scoped receptionist who cannot *see* branch Y's calendar can still cancel its appointments, reschedule them into their own branch, transfer them to another doctor, and check a patient in — and check-in writes a `QueueEntry` whose `branch_id` is the appointment's (`:923`), so the queue board of the other branch changes as a result. `.clinerules` §3 requires cross-branch access to fail closed with `404`; BR §6.3 makes branch restriction a matter of what a user may operate on, not merely what they may view. The pattern is the same asymmetry as F-06: the read path applies a scope the write path never learned.

**A word on the prior record.** An earlier phase report recorded this as not-a-defect, reasoning that a queue or lifecycle guard would stop a cross-branch actor. Reading the code, no mutation consults a queue entry, and the lifecycle whitelist (`:244-246`) knows only statuses. If the owner's position still holds, the reasoning needs an artefact that demonstrates it; otherwise this finding stands and supersedes the earlier entry. Superseding a governance record is an owner act, so it is listed as **Q4** in §11 rather than done here.

**How to prove it.** Token for branch X, appointment in branch Y, same organization: `POST /{id}/cancel` with a reason → `200`; `POST /{id}/check-in` → `200` plus a queue entry in Y. See T-8. Expect `404`.

**Direction.** One scoped loader used by every write route: tenant filter as now, plus `branch_accessible(auth, row.branch_id)` → `404`. It is the same two lines as F-06 and belongs in the same helper.

---

### F-09 — The detail read needs authentication but not permission, and ignores branch scope

**Severity: Medium · WP-2.6 · DEFECT**

**What the code does.** `GET /api/v1/appointments/{id}` is declared with `Depends(get_current_user)` (`appointment/main.py:731-732`), loads by `(id, organization_id)` (`:735-736`), and returns the full row including the recorded symptoms and the onset answer (`:738-739`). The list and grid routes, by contrast, require `appointment.read` and apply `apply_branch_scope` (`:502`, `:528-529`).

**Evidence.** `appointment/main.py:731-739`; contrast `:495-503` and `:528-529`; `appt_filters.py:181-189`.

**Why it matters.** Two gaps in one route. Any authenticated principal — including a role with no appointment permission at all, which the grid route's own docstring says was closed there (`:519-521`) — can read any appointment in the organization by id, and a branch-scoped actor can read a row in another branch. The payload is the sensitive one: symptoms, onset free text, notes, patient id and mobile eligibility. BR §8 ties data access to role; `.clinerules` §3 makes the server the boundary. The route is reachable from the UI's detail panel, so it is exercised routinely and will not look anomalous in a log.

**How to prove it.** With a role holding no appointment permission: `GET /api/v1/appointments/{id}` → `200` today, `403` expected. With a branch-X token and a branch-Y appointment: → `200` today, `404` expected. See T-9.

**Direction.** The same dependency as the list route (`require_permission("appointment.read")`), plus the branch-scoped loader from F-08, and the same answer shape — `404` for anything the caller may not see.

---

### F-10 — A transfer can file the visit into a branch that does not exist

**Severity: Medium · WP-2.4 / WP-2.6 · DEFECT**

**What the code does.** `transfer_appointment` reads `data.new_branch_id` (`appointment/main.py:1074`), passes it to `_resolve_location` as the branch to prefer (`:1072-1076`), and then sets `t_branch = t_clinic.branch_id if t_clinic is not None else data.new_branch_id` (`:1077`) — writing the request-body value verbatim when no clinic matched. It never queries `Branch` and never calls `branch_accessible`, although it queries `Doctor` in the tenant two lines earlier (`:1061-1064`).

**Evidence.** `appointment/main.py:1069-1079` (derivation and the row that receives it); `scheduling/main.py:91-95` (the `Branch` lookup the create-schedule path performs); `common/auth.py:430-448` (`branch_accessible`).

**Why it matters.** An unknown or out-of-scope branch id produces an appointment whose `branch_id` matches no branch: every branch-filtered read excludes it, the join at `appt_filters.py:218-219` yields no branch name, and the visit becomes invisible to the branch that owns it while remaining visible org-wide. That is a data-integrity defect with a security edge — a branch-scoped actor has just written outside their scope. BR §17.4 treats transfer as an intra-organization operation with a defined destination; a destination that does not resolve is not a transfer.

**How to prove it.** Transfer with `new_branch_id` set to a random UUID → `200`, and the new row carries that UUID. With a branch-X token and branch Y as destination → `200`. See T-10.

**Direction.** Resolve `Branch` inside the tenant and check `branch_accessible` before use — the `create_schedule` pattern — and derive `t_branch` from the resolved branch rather than from the body.

---

### F-11 — A transfer resolves a chamber for one time and writes another

**Severity: Medium · WP-2.1 / WP-2.4 · DEFECT**

**What the code does.** The chamber is resolved with a fallback — `start_time=data.new_start_time or orig.start_time` (`appointment/main.py:1076`) — but the row is constructed with `start_time=data.new_start_time` (`:1081`), with no fallback and no capacity check. When the caller omits `new_start_time`, the appointment is stored with `start_time = NULL` while carrying a full chamber snapshot (session, floor, department, room) resolved for the *original* time on the new date (`_apply_location`, `:1087`, `:335-351`).

**Evidence.** `appointment/main.py:1072-1081` (the two different expressions, four lines apart); `:1087` and `:335-351` (the snapshot copied onto the row); contrast reschedule `:833` and `:840`, which use the same `or orig.start_time` expression in both places.

**Why it matters.** The record becomes internally inconsistent: the row says "no time", the chamber says "09:30, Room 3". Every read that buckets by `start_time` (`grid.js:197-215`) files it under the empty key, so the patient does not appear in the slot the room was reserved for — and capacity for that slot never counts them, which quietly compounds F-01/F-03. It is also the sharper half of the transfer problem: reschedule at least repeats the same expression on both lines, so the snapshot and the row cannot disagree. BR §17.4 and §22.5 expect a transfer to preserve the visit's time or to set a new one deliberately; dropping it by omission is neither.

**How to prove it.** Transfer without `new_start_time` → `201`/`200`, the new row's `start_time` is `null`, and the row carries `room_name`/`session_id`. See T-11.

**Direction.** Use one resolved value for both the lookup and the write, and run it through the same slot/capacity guard as create (F-04's helper). If a transfer may legitimately clear the time, that is a state to model explicitly rather than a fallback that misfires.

---

### F-12 — Schedule create and update write no audit row

**Severity: Medium · WP-2.5 · GAP**

**What the code does.** `create_schedule` (`scheduling/main.py:67-105`) and `update_schedule` (`:145-166`) validate the branch, doctor and tenant, write the row, and commit. Neither calls `record_audit`; the module does not import it, so no schedule change is audited anywhere in this service.

**Evidence.** `scheduling/main.py:96-101` (create: construct, add, commit, return) and `:155-166` (update: mutate fields, commit, return); the absence of `record_audit` in the file, against its use in the appointment service (`appointment/main.py:763-768`, `:857-864`, `:1096-1100`).

**Why it matters.** A schedule edit is the change that decides how many patients a day can hold and which hours exist at all — the most consequential configuration in the capability, and the input to every capacity decision in F-01…F-04. BR Part X requires an auditable record of consequential changes, including who changed what and when. Today an over-capacity day can be traced to a template `max_patients` change with no record that it changed, by whom, or from what — and `update_schedule` accepts the whole `slot_templates` array wholesale (`:155-156`), so "from what" is not recoverable from the database afterwards.

**How to prove it.** `PATCH /api/v1/schedules/{id}` changing `max_patients`, then query the audit table for `service == "scheduling"` → no row. See T-12.

**Direction.** Import `record_audit` and emit one event per write with a before/after snapshot of `slot_templates` and the effective window — the appointment service's `appointment.rescheduled` event is the pattern to copy (`:857-864`).

---

### F-13 — Invalid effective dates are swallowed, and the response says nothing

**Severity: Medium · WP-2.5 · DEFECT**

**What the code does.** Both write paths wrap `datetime.strptime(...)` in `try/except: pass`. On create (`scheduling/main.py:72-78`) an unparseable `effective_from`/`effective_to` leaves the local `ef`/`et` at `None`, so the schedule is stored with **no** effective window — which `_date_covered` reads as "always valid". On update (`:158-163`) the assignment is skipped, so the **previous** date survives and the caller's value is silently discarded. Both return the schedule with `200`/`201` as though the value had been accepted.

**Evidence.** `scheduling/main.py:72-78`, `:158-163`; the consumer that interprets `None` as unbounded, `appointment/main.py:277-285` (`_date_covered`).

**Why it matters.** The effective window is what decides whether a schedule applies on a given day (BR §23.3, §23.9), and the two failure modes point in opposite directions: create widens it to infinity, update keeps a value the caller was trying to replace. Neither is reported. A typo in a date — `2026-13-01`, `01/13/2026` — is therefore a silent configuration change, and BR §22.8 asks for a clear explanation whenever a request cannot be honoured. The API's answer is the same status code as success, which is the most expensive kind of wrong.

**How to prove it.** `POST /api/v1/schedules` with `effective_from: "2026-13-01"` → `201`, and the returned `effective_from` is `""`; `PATCH` an existing schedule the same way → `200`, unchanged date. See T-13.

**Direction.** Parse with the existing `except` replaced by a `422` naming the field — the pattern `appointment/main.py:367-368` already uses (`invalid date, use YYYY-MM-DD`). Validation at the model boundary (`Optional[date]` on the Pydantic model) would remove the `try` entirely.

---

### F-14 — Template contents are never validated, and the reader trusts them

**Severity: Medium · WP-2.5 · DEFECT**

**What the code does.** `SlotTemplate` (`scheduling/main.py:32-37`) fixes the *types* — `day_of_week: int`, `start_time: str`, `end_time: str`, `slot_duration_minutes: int = 15`, `max_patients: int = 4` — and validates nothing about the *content*: no `HH:MM` shape, no `start < end`, no `duration > 0`, no `max_patients >= 1`, no weekday range, no overlap check between templates. `available-slots` then consumes the stored dicts directly: `map(int, t["start_time"].split(":"))`, `range(smin, emin, dur)` (`:192-197`).

**Evidence.** `scheduling/main.py:32-37`, `:99` / `:156` (`.dict()` straight into `slot_templates`), `:192-197` (unchecked parse and `range`); `appointment/main.py:340-343` (the appointment service's own template scan, which trusts the same dicts), `:407-412`.

**Why it matters.** Any accepted-but-nonsensical template becomes a runtime failure later, in a different service, at read time: `"9:00"` raises `ValueError` inside `map(int, …)` and the endpoint returns `500`; `slot_duration_minutes: 0` raises inside `range`; `max_patients: 0` makes every slot full and `create_appointment`'s `max(max_capacity - reserved, 1)` silently promotes it to 1 (`:415`). The frontend is more defensive than the backend here — `expandTemplate` returns `[]` for a bad template rather than throwing (`grid.js:122-133`) — which means the same corrupt row can render an empty day in the browser and a `500` on the API. BR §23.3/§23.9 make the template the definition of a slot; a definition that can hold `"9:00"` is not one.

**How to prove it.** `POST /api/v1/schedules` with `slot_templates: [{"day_of_week": 1, "start_time": "9am", "end_time": "12:00", "slot_duration_minutes": 15, "max_patients": 1}]` → `201`; then `GET /api/v1/schedules/{id}/available-slots?date=…` → `500`. See T-14.

**Direction.** Validate in `SlotTemplate` with a field validator (`HH:MM`, `start < end`, `duration >= 5`, `1 <= max_patients`, `0 <= day_of_week <= 6`) so a bad template cannot be stored, and make the reader defensive anyway — a row inserted before the validator existed must degrade to "no slots" rather than `500`.

---

### F-15 — `available-slots` answers a different question from the one its inputs describe

**Severity: Medium · WP-2.5 · DEFECT**

**What the code does.** The endpoint takes a `date` (`scheduling/main.py:188-189`) and then ignores everything about that date except the booking count: the expansion loop iterates every template in the schedule (`:191`) without consulting `t["day_of_week"]`, the schedule's `effective_from`/`effective_to`, or `sched.status`. For each expanded slot it issues a separate `count()` on `Appointment` (`:200-205`), so a 16-slot day is 16 round trips.

**Evidence.** `scheduling/main.py:191-215` (the loop and its per-slot count); the fields that exist and are not read: `day_of_week` (`:33`), the effective window (`:43-44`), `status` (`models.Schedule.status`, default "active"); the frontend doing the weekday filter the server omits, `grid.js:141-152`.

**Why it matters.** The route is named for a date and returns every template regardless of weekday, so asking for a Sunday returns Monday's hours. Whatever consumes it — the dialog's slot list, or a future capacity panel — cannot distinguish "the doctor does not work today" from "the doctor works all day", and BR §23.3/§23.9 make exactly that distinction the point of a template. The N+1 shape compounds it: the cost of the endpoint grows with the number of slots, in the service that every booking screen calls on open.

**How to prove it.** Create a schedule whose only template is `day_of_week: 0` (Monday); request `available-slots` for a Sunday → a full Monday list is returned. See T-15.

**Direction.** One shared availability function: filter templates by weekday, by the effective window and by schedule status, then compute booked counts for the surviving slot starts in **one** grouped query. That function is also the answer to F-16 — the frontend should call or mirror it, not re-derive it.

---

### F-16 — Three sources of truth decide whether a slot exists

**Severity: Medium · WP-2.5 · DEFECT**

**What the code does.** Three derivations disagree, each defensible in isolation:

| Derivation | Weekday | Effective window | Schedule status | Where |
|---|---|---|---|---|
| Grid / dialog slot list | **yes** | no | **yes** | `grid.js:136-152` |
| `available-slots` | no | no | no | `scheduling/main.py:191-215` |
| Appointment chamber resolution | **yes** (via `ScheduleSession.day_of_week`) | **yes** (`_date_covered`) | **yes** (`status == "active"`) | `appointment/main.py:301-329` |

**Evidence.** The three citations above, plus the two different tables they read: templates in `schedules.slot_templates` and sessions in `ScheduleSession` (`appointment/main.py:316-320`).

**Why it matters.** The user-visible consequence is a dead end rather than a wrong record: the grid offers a slot because the weekday and status match, the dialog posts it, and the server refuses with `422 "no clinic session covers this time — book inside the doctor's session window"` (`:325-328`) — a message about a session window the user has no way to see. The opposite also happens: a schedule whose `effective_from` is in the future publishes bookable-looking hours because neither the grid nor `available-slots` filters on effective dates. BR §22.9 requires the UI not to offer what the server will refuse; here the two disagree by construction, not by bug. It is also the reason F-14 and F-15 are worth fixing together: validating templates while three readers interpret them differently fixes nothing.

**How to prove it.** Give a doctor a Monday-only template with `effective_from` set to next month; open the grid on a Monday this month → slots render; book one → `422` about a session window. See T-16.

**Direction.** Name the single authority. The clinic-session model is the richer one and is what the appointment service already enforces, so either project sessions into the published slot list the grid reads, or make `available-slots` the only executor and have the grid display its answer. The staged choice belongs to **Q1** in §11, because it decides which table is the source of truth for "does this slot exist".

---

### F-17 — The calendar read has no window bound

**Severity: Low · WP-2.7 · HARDENING**

**What the code does.** `GET /api/v1/appointments` accepts `date_from` and `date_to` as optional strings (`appointment/main.py:499`) and applies them only when supplied (`apply_filters`, `:532-534`). There is no default window and no maximum span, so a request with neither returns every appointment the caller may read, ordered by date and time (`:539-541`).

**Evidence.** `appointment/main.py:495-503`, `:532-541`; the shared predicate at `appt_filters.py` (which validates the *format* of a supplied date, not the span).

**Why it matters.** This is a load and payload ceiling, not a correctness defect — nothing is exposed that the caller is not entitled to read. But the route is the grid's read and is called on every filter change and poll (`appointments.js:505-514` for the slot picker alone), so an unbounded default is a standing invitation to pull a tenant's entire appointment history into a browser tab. BR §22 tolerates a deliberate, documented default; an accidental unbounded result set is the shape that becomes a performance incident during a demo with a projector on it.

**How to prove it.** Count appointments, request the list with no parameters, compare lengths → equal. See T-17.

**Direction.** Default the window (the grid already thinks in weeks) and refuse a span beyond a stated maximum with `422`, mirroring how `q` is bounded by `SEARCH_MAX_LENGTH` (`:500`).

---

### F-18 — When a day publishes no slots, the dialog offers a free-text time instead

**Severity: Low · WP-2.2 / WP-2.7 · GAP**

**What the code does.** `slotChoices` is built from `slotsForDate` for the selected doctor and date. When it is empty the dialog does not say "this doctor does not work today" and stop: it renders the `noSlots` notice followed by an unrestricted `<input type='time'>` (`appointments.js:1011-1018`), and `saveBooking` posts whatever that picker holds, sliced to five characters (`:539`, `:549`). The server then decides — and with no session that weekday it decides yes (F-02).

**Evidence.** `appointments.js:1011-1018` (the branch), `:534-557` (the submit path, with no client-side check that the time belongs to a slot); the fallback it mirrors, `grid.js:179-192` (`capacityFor` returns `1` when no schedule covers the time, in a comment that cites the server's own `max_capacity = 1`).

**Why it matters.** The fallback is deliberate and documented on both sides — the frontend comment says it matches `create_appointment` — which is why this is a GAP rather than a DEFECT: the two agree. What they agree on is that an unconfigured day is bookable at any minute, with capacity 1, and the user is told nothing about the consequence. A receptionist choosing 10:07 on a day with no schedule gets a confirmed appointment that no slot, no session and no capacity model accounts for. BR §22.9 asks the interface not to offer what the system cannot honour; here the system honours it by having no opinion.

**How to prove it.** Pick a doctor with no schedule for the selected weekday, confirm the notice plus a free time field, book 10:07 → `201`. See T-18.

**Direction.** If a walk-in outside any session is intended (the `:1000-1010` exemption says it is for walk-ins), say so in the dialog and mark the booking as unscheduled so it is visible as such in the grid; do not present an arbitrary-time field as an equivalent to a slot. If it is not intended, remove the fallback and render the empty state.

---

### F-19 — A full slot and a rejected booking do not explain themselves

**Severity: Low · WP-2.1 / WP-2.7 · POLISH**

**What the code does.** A slot at capacity renders as a disabled button whose only explanation is a tooltip reading `capacity: N` and an inline `booked/capacity` count (`appointments.js:1022-1032`). A slot with 3 of 4 taken is visually identical to one with 4 of 4 except for the number, since opacity is the only other signal (`:1026`). When the server refuses a booking, the dialog appends the raw exception text after a translated prefix: `T('bookErr') + ': ' + String(e.message || e)` (`:564`).

**Evidence.** `appointments.js:1022-1032` and `:564`; the messages the server can return on this path — `422 "no clinic session covers this time — book inside the doctor's session window"` (`appointment/main.py:325-328`), `422 "slot is full"` (`:418-421`), `422 "invalid date, use YYYY-MM-DD"` (`:367-368`).

**Why it matters.** These are the two moments the capability has to explain itself, and in both it hands the user either a number without a reason or an untranslated English sentence inside an otherwise Bengali interface. `T('bookErr')` is localised, the server's sentence is not, and the specific `422` about a session window names a concept ("session window") that the booking dialog never displays — so the correction it asks for is not one the user can perform from where they are standing. BR §22.9, and BR Part XI's language requirement, both point at this seam. It is POLISH rather than a defect because nothing is recorded wrongly: the refusal is correct, only unexplained.

**How to prove it.** Fill a slot and read the disabled button's tooltip; then book outside the session window and read the dialog's error line. See T-19.

**Direction.** Map the server's known refusal codes to translated strings with an actionable next step, and show remaining seats as words ("2 left") rather than only as arithmetic. The `status` codes are already distinct enough to key on without exposing internals.

---

### 6.1 The pattern across the nineteen findings

The pattern is narrower than "the appointment module is unfinished". Three sentences cover it:

- **The write path is less careful than the read path.** Reads are tenant- and branch-scoped, deny non-disclosingly and audit the denial; writes check the tenant, sometimes the session window, and neither the branch nor the referenced doctor. Every High finding except F-01 and F-03 is an instance of this asymmetry, and both correct patterns already exist in the tree (`scheduling/main.py:84-95` for entity validation, `appt_filters.py:181-189` for scope) — the work is to apply them, not to invent them.
- **Capacity is a number the system counts and never a rule it enforces.** No lock, no constraint, no reschedule check, and a count that treats each distinct minute as its own slot. That is why the same slot can be shown as full and still accept patients, and it is the finding set most likely to be visible in a demo (F-01, F-03, F-04).
- **Configuration is trusted after it is stored.** Templates are unvalidated on write and parsed without guards on read, effective dates are swallowed, and three readers disagree about whether a slot exists. Fixing the readers without validating the writer, or the reverse, would leave the disagreement in place (F-12 … F-16).

A fourth observation is about reachability rather than cause: **almost none of the High findings needs concurrency to reproduce.** F-03, F-04 and F-11 need only one well-formed request carrying an unusual time; F-05 and F-06 need only an id or a branch the caller does not own; F-08 needs only a token from another branch. Only F-01 requires two simultaneous requests, which is why it is the one finding in the set that a happy-path demonstration can never reveal.

None of this requires a schema change. F-01 is the one finding whose complete fix (a constraint or a locked read) touches the database, and even that has a correct application-level answer first; everything else is a guard, a validator, an audit call or a label. That is why the roadmap in §9 sequences the authorization fixes ahead of the capacity ones: they are the cheapest, they close the only Critical, and none of them depends on a design decision still open in §11.

---

## 7. What is already sound (read and confirmed, not assumed)

Recording these matters as much as the gaps: they are the parts a fix must not break.

### 7.1 The read side, post-`AMSDP-CALENDAR-FILTER-01`

| Property | Evidence |
|---|---|
| One predicate set serves grid, paged list and match index — a filter cannot mean three things | `appt_filters.py:168-300`; the three routes call `apply_branch_scope` + `apply_filters` |
| Branch confinement on reads is server-side and non-disclosing | `appt_filters.py:181-189` (foreign branch → `404`, missing token branch → `403`) |
| The UI's branch picker is cosmetic; the grant is server-side | documented in `appt_filters.py:178-180`; verified by reading the route dependencies |
| Slot derivation is one shared function used by the form and the grid | `grid.js:160-175`, consumed at `appointments.js:505-514` |
| The capacity badge and the backend count the same statuses | `grid.js:30-32` ↔ `appointment/main.py:389-396` |
| Search/filter query building is centralised | `frontend/lib/calendar/matches.js`; `appointments.js` passes state, not ad-hoc params |

### 7.2 Lifecycle

- Transitions are whitelisted in `VALID_TRANSITIONS`; an illegal transition is refused rather than coerced (`appointment/main.py:748-773`).
- Each transition writes an audit event with actor, from-state and to-state (`:460-479` pattern, reused by the transition route).
- Cancellation and no-show route through the same audited transition path, so they are not special cases.

### 7.3 Scheduling

- Schedules and templates are modelled with capacity and effective windows rather than a single daily number (`scheduling/main.py:32-37`) — the shape BR §23.3/§23.9 asks for, even though enforcement is incomplete.
- Clinic sessions project into `schedules.slot_templates`, so there is one representation of a doctor's working day rather than two (`scheduling/sessions.py`).

### 7.4 Completed work this analysis credits

For completeness against the brief's "completed items", these are present and working by reading — they are the parts of the Phase 1/2 programme the appointment capability already has:

| Completed | Where | Note |
|---|---|---|
| Single read-predicate module shared by grid, list and match index (`AMSDP-CALENDAR-FILTER-01`) | `backend/appointment/appt_filters.py` | The largest single improvement to this capability; a filter can no longer diverge per view |
| Server-side branch confinement on reads with non-disclosing `404` | `appt_filters.py:168-189` | The model the write paths should follow |
| Shared slot derivation between the booking form and the grid | `frontend/lib/calendar/grid.js:160-175` | One expansion function, not two |
| Capacity-aware grid badge from the same status set as the backend | `grid.js:30-32` ↔ `appointment/main.py:389-396` | Count agrees; enforcement does not (F-01) |
| Explicit lifecycle state machine with refused illegal transitions | `appointment/main.py:748-773` | Whitelist, not coercion |
| Audited lifecycle transitions (actor, from, to) | `appointment/main.py:460-479` | Pattern reused by cancel / no-show / check-in |
| Reschedule and transfer implemented, with original-assignment history on transfer | `main.py:802-847`, `:1047-1088` | Both need capacity/scope work (F-04, F-10, F-11) |
| Walk-in booking and check-in → queue hand-off | `main.py:883-897` | The only cross-service write in the capability (the reason F-07 matters) |
| Clinic sessions with chambers projected into schedules | `backend/scheduling/sessions.py` | One representation of a doctor's day |
| Bilingual appointment UI with Week/Day/List views and filters | `frontend/pages/appointments.js`, `frontend/lib/i18n.js` | BN/EN dictionaries; capacity label is the one untranslated item (F-19) |
| Permission matrix and token-derived org/branch context | `backend/common/permissions.py`, `common/auth.py` | Exists and is correct — the appointment write routes simply do not call it (§5.6) |
| Substantial test corpus (108 appointment + 36 scheduling test functions; 15 frontend test files) | `backend/appointment/tests/`, `backend/scheduling/tests/`, `frontend/tests/` | Strong on the happy path and read filtering; absent on concurrency and scope boundaries (§8.2) |


---

## 8. Test and evidence gaps

**No test was executed in this session.** The commands below are the ones that *would* produce the evidence; they are listed so the fix stages in §9 can name their own exit criteria. Running them requires a disposable PostgreSQL (`.clinerules` §9 forbids unrequested suite runs, and the suite itself needs the database).

### 8.1 How this tree is tested

| Layer | Where | How to run | Prerequisite |
|---|---|---|---|
| Appointment service | `backend/appointment/tests/` (5 files, ~108 test functions counted by search) | `cd backend && python -m pytest appointment/tests -q` | Active venv; `AMSDP_DATABASE_URL` pointing at a disposable PostgreSQL |
| Scheduling service | `backend/scheduling/tests/` (~36 test functions) | `cd backend && python -m pytest scheduling/tests -q` | as above |
| Cross-service sequences | `backend/tests/` (incl. `test_sequence3.py`, modified by the RBAC workstream) | `cd backend && python -m pytest tests -q` | as above |
| Frontend | `frontend/tests/*.test.mjs` (15 files) | `cd frontend && npm test` | `npm install`; the script is `node --test tests/*.test.mjs` (`frontend/package.json:9`) |

The suite bootstraps through `backend/conftest.py`, which puts the backend root and `backend/tests/` on `sys.path` and takes the database URL from `AMSDP_DATABASE_URL` (`conftest.py:1-15`). No `pytest.ini`, `setup.cfg`, `tox.ini` or `pyproject.toml` was found at the repository root or in `backend/`, so pytest discovery is by convention.

### 8.2 What the corpus does not cover

| Missing coverage | Why it matters here | Findings it leaves unproven |
|---|---|---|
| **No concurrent-request test anywhere** — no `threading`, no `ThreadPoolExecutor`, no parallel client in either service's tests | The atomicity claim is the one thing BR §23.7/§23.8/§51 demand proof of, and nothing exercises it | F-01 |
| **No test books a malformed or non-slot `start_time`** — no `"banana"`, and no minute inside a slot that is not the slot's own start | The unvalidated-time path and the per-minute capacity bucket are untested by construction | F-02, F-03, F-18 |
| **No test books an off-template time** | The "invented bucket" behaviour is untested by construction | F-03 |
| **No test reschedules into a full slot** | Reschedule's capacity silence is untested | F-04 |
| **No test uses a `doctor_id` or `branch_id` from outside scope** | The authorization gaps are invisible to a same-tenant fixture | F-05, F-06, F-09, F-10 |
| **No test asserts the permission used by `check-in`** | A read capability guarding a write is not caught by happy-path tests | F-07 |
| **Branch-scope assertions exist for reads, not for mutations** | Reads are tested against the confinement rule; writes are not | F-08 |
| **No malformed-schedule test** (`slot_templates` shape, invalid dates) | The stored-data-causes-`500` class is unrepresented | F-13, F-14 |
| **No audit assertions on schedule writes** | The absence of an audit row cannot fail a test that never looks | F-12 |
| **No empty/error-state frontend test for "no schedule configured"** | The distinguishing message is not pinned by a test | F-16, F-19 |

### 8.3 The evidence table each fix stage should fill

| Test | Proves | Layer | Exists today? |
|---|---|---|---|
| T-1 | Two parallel bookings cannot exceed capacity | backend (threads) | **No** |
| T-2 | A malformed or non-slot `start_time` is refused (or snapped to a published slot) | backend | **No** |
| T-3 | An off-template `start_time` is refused | backend | **No** |
| T-4 | Reschedule into a full slot is refused or explicitly overbooked | backend | **No** |
| T-5 | A foreign `doctor_id` yields a non-disclosing `404` | backend | **No** |
| T-6 | A foreign `branch_id` on create yields `404` | backend | **No** |
| T-7 | `check-in` requires the modify capability | backend | **No** |
| T-8 | A cross-branch mutation yields `404` | backend | **No** |
| T-9 | A cross-branch detail read yields `404` | backend | Partial (list/grid only) |
| T-10 | An unknown transfer branch yields `404`, not `500` | backend | **No** |
| T-11 | Transfer to a non-existent slot is refused | backend | **No** |
| T-12 | A schedule edit writes an audit row | backend | **No** |
| T-13 | Invalid effective dates are refused with `422` | backend | **No** |
| T-14 | A malformed `slot_templates` value cannot break `available-slots` | backend | **No** |
| T-15 | `available-slots` respects the weekday and effective window | backend | **No** |
| T-16 | A future-effective schedule renders an explained empty state | frontend | **No** |
| T-17 | An over-wide date range is refused | backend | **No** |
| T-18 | A day with no published slots offers no arbitrary-time field, or labels the booking it produces as unscheduled | frontend + backend | **No** |
| T-19 | A capacity rejection shows a localised, specific reason | frontend | **No** |

The pattern is worth stating plainly: **the appointment capability is tested for the happy path and for read-side filtering, and essentially untested for the two things the Business Rules care most about — concurrency and cross-tenant/cross-branch boundaries.** That is a coverage defect, not a code defect, and it is why §9 stage 1 and stage 2 each ship their tests with the fix rather than after it.

---

## 9. Roadmap — four stages

Four stages, not seven. The seven work packages are *areas of concern*; they collapse into four *shippable units* because several packages are closed by the same edit, and because authorization cannot be staged behind anything else.

Each stage is a closed unit: it names its findings, the files it touches, its exit evidence, and what it must not break (drawn from §7).

---

### Stage 1 — Close the door: authorization on the write paths

**Closes:** F-07 (Critical), F-05, F-06, F-08, F-09, F-10 — WP-2.3's Critical and every defect in WP-2.6.
**Touches:** `backend/appointment/main.py` (six route bodies), `backend/common/permissions.py` (one capability, subject to Q3). **No migration. No schema change. No frontend change.**
**Why first:** it is the only stage containing a Critical finding; it is the smallest stage by edit volume because `require_branch_access`, `branch_accessible` and `can_access_doctor` already exist and are already used elsewhere; and every later stage's "this is now safe" claim depends on the actor being correctly confined. Doing capacity work first would leave F-06 open, so a wrong-branch actor could overbook — two defects compounding into one incident.
**Exit evidence:** T-5 … T-10 green; the existing appointment and scheduling suites still green; a cross-branch mutation observed returning `404` (not `403`, not `200`).
**Must not break:** org_admin's legitimate org-wide reach (`branch_accessible` returns `True` for `is_org_admin`/`can_cross_org`, `common/auth.py:445-447`) — §7.1's non-disclosing read behaviour must be preserved exactly, and BR §6.2's "authorized users at different branches … according to permissions" must keep working for the roles meant to have it.
**Risk:** low, bounded to one file plus the matrix; fully revertible.

---

### Stage 2 — Make capacity true: atomicity, slot membership, and the second booking paths

**Closes:** F-01, F-02, F-03, F-04, F-11 — WP-2.1 entirely, and the capacity half of WP-2.4.
**Touches:** one shared capacity/slot-membership validator used by create, walk-in, reschedule and transfer; `backend/appointment/main.py`; **one forward-only, idempotent Alembic migration** (`.clinerules` §3) for whatever concurrency mechanism Q2 selects; tests.
**Why second:** it is the stage the Business Rules speak to most directly (§23.7, §23.8, §51) and the one an audience can break live. It is second rather than first only because it is the larger edit, and because Stage 1 removes the possibility of an *unauthorised* overbooking, leaving Stage 2 to fix the *unvalidated* one.
**Sequencing inside the stage** (this matters if time is short): F-02 and F-03 first — pure validation, no migration, closing the two paths the UI can reach today — then F-04 and F-11 (the second booking paths), then F-01 with its migration. The first three sub-steps are independently shippable; the migration is the largest single item and must not be rushed.
**Exit evidence:** T-1 (threads — the only test that can prove §23.7), T-2, T-3, T-4, T-11 green; `alembic upgrade head` idempotent on both a fresh and a seeded database; a capacity-1 slot demonstrably rejecting the second concurrent booking with a clear message (§22.8).
**Must not break:** the grid badge's agreement with the backend count (§7.1) and the `VALID_TRANSITIONS` lifecycle (§7.2) — an overbooking decision must not become a lifecycle shortcut.
**Depends on:** Q1 (whether an outside-session, arbitrary-time booking is a legitimate model, and what governs its capacity) and Q2 (which concurrency mechanism). Both are owner decisions; neither can be guessed safely.

---

### Stage 3 — Govern the configuration: validation, audit and one availability predicate

**Closes:** F-12, F-13, F-14, F-15, F-16 — WP-2.5 entirely.
**Touches:** `backend/scheduling/main.py` (write validation + audit + a single availability derivation), a shared slot-derivation module consumed by both the endpoint and `frontend/lib/calendar/grid.js`, and the frontend's empty state.
**Why third:** it is the first stage that is *not* about a live-exploitable path — nobody can overbook by editing a schedule — but it is the stage that makes Stage 2's capacity decisions stable, because capacity is read from configuration that is currently unvalidated and unaudited. Doing it before Stage 2 would mean enforcing capacity against data that can be corrupted at will; doing it after means Stage 2's validator can rely on a shape guarantee.
**Exit evidence:** T-12 … T-16 green; a malformed template rejected at the write boundary (`422`) and, if one is inserted directly into the database, `available-slots` degrading to "no slots" rather than `500`; every schedule write producing an audit row with before/after.
**Must not break:** §7.3 — the schedule/session projection must keep one representation of a doctor's day; the grid must keep deriving slots through one function.
**Depends on:** nothing blocking, though Q5 (whether schedule edits must be audited) should be confirmed rather than assumed.

---

### Stage 4 — Polish the surface: bounds, affordances and messages

**Closes:** F-17, F-18, F-19 — WP-2.7 entirely, and the frontend half of WP-2.2's F-18.
**Touches:** `frontend/pages/appointments.js`, `frontend/lib/calendar/grid.js`, `frontend/lib/i18n.js`, and the grid endpoint's range guard in `backend/appointment/main.py`.
**Why last:** these are the only findings that produce neither a wrong record nor an unauthorised action; they produce a bad experience. They are also the findings most likely to be *changed* by Q1's answer (the arbitrary-time fallback, F-18) and by Stage 3's new empty state, so scheduling them last avoids doing the work twice.
**Exit evidence:** T-17, T-18, T-19 green; a capacity rejection read in BN locale states the reason; a schedule with no applicable effective window renders a distinguishable empty state.
**Must not break:** the bilingual dictionaries (both extended together), and the shared derivation from §7.1.

---

### 9.1 What the roadmap deliberately does not include

- **No new service, no new abstraction layer.** Every mechanism Stage 1 needs already exists; Stages 2 and 3 consolidate two existing predicates rather than inventing new ones.
- **No cross-tenant feature work, no notifications, no Docker changes.** Out of scope per §1.
- **No correction of the Phase 0–1 record (F-08).** Superseding a governance document is an owner act; it is listed as Q4 in §11.
- **No estimate in days.** The honest unit here is *edit surface*: Stage 1 = one file + the matrix; Stage 2 = one file + one migration + tests; Stage 3 = two files + one shared module; Stage 4 = three files + one guard.

---

## 10. Recommended order, and the one deviation worth considering

**Recommended: Stage 1 → Stage 2 → Stage 3 → Stage 4.**

The reasoning is not "highest severity first" alone — it is dependency order plus evidence order:

1. **Stage 1 before everything** because it is the only stage that closes a Critical finding, it is the cheapest by edit surface, and it converts "an actor may do anything in the tenant" into "an actor may do what its token allows" — the precondition for every later claim.
2. **Stage 2 before Stage 3** because capacity enforcement is the capability's headline promise and because it needs the configuration shape that Stage 3 will guarantee; shipping Stage 2 second means its validator can be strengthened *once* when Stage 3 lands, rather than being written against unvalidated data and then rewritten.
3. **Stage 3 before Stage 4** because the empty-state and message work in Stage 4 depends on Stage 3's single availability predicate; doing Stage 4 first would mean writing messages for a slot list that is about to change shape.
4. **Stage 4 last** because it is the only stage that changes no data and no authorization decision, so it is the correct thing to defer if capacity is tight — and the correct thing to drop entirely if the demo must ship early, since F-17/F-18/F-19 are Low.

**The one deviation worth considering.** If the demonstration is imminent and only one thing can be fixed, fix **the F-02/F-03 pair inside Stage 2 rather than the whole stage** — pure server-side validation, no migration, no schema risk — and keep Stage 1 for after the demo. That is a deviation this report does not recommend, only names: it trades the only Critical (F-07, an unauthorised lifecycle change plus a queue write) and an unvalidated cross-tenant `doctor_id` (F-05) for a visible capacity guarantee, which inverts the severity order for the sake of the audience. If it is taken, it must be an explicit, recorded owner decision rather than a silent re-prioritisation, and §3 of `.clinerules` (tenant isolation as a non-negotiable) should be cited in that record as the reason the deviation is temporary.

**What must not be reordered.** Stage 2's migration must not land before Stage 1's authorization, and Stage 3's validation must not land before Stage 2's capacity validator exists — otherwise the same work is done twice against a moving target, and each stage's exit evidence would have to be re-proven.

---

## 11. Decisions required from the project owner

These five cannot be resolved by reading the code, because each is a product or platform ruling. **None was guessed in this analysis**; where a finding depends on one, it says so.

| # | Question | Why the code cannot answer it | Findings affected | If unanswered |
|---|---|---|---|---|
| **Q1** | Is a booking outside every clinic session — a walk-in, or a time no template covers — a legitimate booking model? If yes, what governs its capacity: the doctor-day, the nearest session, or nothing? | The two mechanisms disagree. `create_appointment` refuses a time outside a session only when the doctor holds one that weekday (`main.py:325-328`), and falls back to capacity 1 when no template covers the minute (`:407-412`). The UI offers an arbitrary time field on any day that publishes no slots (`appointments.js:1011-1018`) and mirrors the same fallback (`grid.js:179-192`). BR §23.4-§23.6 name slot, serial and hybrid models — not a free one. | F-02, F-18; gates Stage 2 | Stage 2 can refuse an out-of-slot time only by removing an affordance the product may intend |
| **Q2** | Which concurrency mechanism is authoritative: a partial unique index for capacity-1 slots + `FOR UPDATE`, or serialisable transactions with retry? | BR §23.8 permits "transactions, constraints or equivalent". Both satisfy it; the choice determines the migration and its lock behaviour. | F-01; gates Stage 2's migration | The migration cannot be written without inventing an architecture decision |
| **Q3** | Should a doctor be able to check in their own patient, or is check-in a receptionist capability behind `appointment.modify`? | `check-in` reaches the transition function directly (`main.py:897`) from a route with no permission dependency (`:883-885`), while the same transition behind `PATCH /{id}/status` requires `appointment.modify` (`:748-750`); the doctor role holds read-only appointment permissions (`common/permissions.py:96-106`). Whether doctors *should* check in is a matrix decision; that they *can* today is a bypass. | F-07; gates part of Stage 1 | Stage 1 cannot add a permission without knowing which role the workflow belongs to |
| **Q4** | May a branch-scoped actor mutate an appointment belonging to another branch of the same organization? BR §6.3 permits branch-level restriction but does not mandate it; the Phase 1 closeout claimed the restriction already exists (F-08). | The code says yes implicitly; the read paths say no explicitly; the governance record says the question is closed. Only the owner can reconcile the three. | F-06, F-08, F-09, F-10; gates Stage 1 | Stage 1 would impose a confinement policy that is a product choice, not a defect fix |
| **Q5** | Do schedule/capacity configuration writes require an audit event, as appointment mutations do? | `.clinerules` §3 requires audit for changes to governed data; BR §22.2-§22.3 makes capacity governed. The code currently omits it. | F-12; gates part of Stage 3 | Treated as mandatory in this report; confirmation removes the assumption |

**Recommended resolution order:** Q4 and Q3 (they gate Stage 1, the smallest and most urgent stage), then Q1 and Q2 (they gate Stage 2), then Q5 (Stage 3).

---

## 12. Read-only confirmation

**What was created:** exactly one file — this document, `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md`, which did not previously exist (collision checked before writing, per `.clinerules` §11).

**What was modified:** **nothing.** No source file, test, migration, configuration, frontend asset or existing documentation was edited, moved, renamed or deleted. The nine dirty entries listed in §2.1 — the RBAC workstream's eight modified files and one untracked document — were captured before this analysis began and re-checked afterwards; the list is unchanged (verified with `git status --porcelain`, §App. C).

**No state-changing command was run.** Nothing was executed against a database, no service was started or stopped, no migration was applied, no test suite was run, no Git index entry was staged, and no destructive Git operation was used (`.clinerules` §9). The shell commands issued were `git rev-parse`/`git status`, `wc`, `ls`, `grep`/`sed`, `cat` of scratch files, and three `python3 -c` invocations whose only side effect was the in-place removal of stray blank lines at the end of this file (§C.5).

**Scratch files** were written to `/tmp` only — the `git status` captures (`/tmp/status_before.txt`, `/tmp/sb.txt`), the grep/count buffers (`/tmp/pk.txt`, `/tmp/t8b.txt` … `/tmp/wc8b.txt`), and the two splice buffers used to rebuild §3–§6 (`/tmp/new_core.md`, `/tmp/doc_new.md`). None is inside the repository and none is a deliverable. **The only write performed inside the repository was to this file.**

**One governance obligation is deliberately deferred.** `.clinerules` §12 requires that creating a document updates `docs/governance/AMSDP_Docs_Index_V1.0.md` in the same task, and §11 forbids leaving an unindexed document. Because this task was explicitly read-only, **the index was not touched.** The one-line entry below is prepared for the owner (or the next authorised task) to paste into the index's audit section:

```
| `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` | Appointment & Calendar reliability — Phase 2 gap analysis: 19 findings (WP-2.1…2.7), 4-stage roadmap | Read when planning appointment/calendar capacity, slot, booking or scheduling-configuration work; or before re-prioritising the Phase 2 packages |
```

That deferral is recorded here rather than silently skipped, so the index defect is visible and small rather than invisible and permanent.

**Evidence standard for this document (`.clinerules` §7).** Every finding is `CODE-READ`. Nothing in it is `TESTED` or `VERIFIED`, because no test was run and no request was issued. The report says what the code will do, cites where, and names the exact test that would prove it. Where it describes something as *sound* (§7), that too is a reading, not a verification.

---

## Appendix A — Evidence index

Every claim in this report traces to one of these citations.

| Citation | What it establishes | Findings |
|---|---|---|
| `backend/appointment/main.py:144-148` | `start_time` is an optional, unvalidated `str` on `AppointmentCreate` | F-02 |
| `backend/appointment/main.py:376-378` | Patient existence is checked (tenant-scoped) before booking | §7.4 |
| `backend/appointment/main.py:386-423` | The capacity block: count by exact string, capacity by template range, insert afterwards | F-01, F-02, F-03 |
| `backend/appointment/main.py:389-396` | Count-then-insert; `ACTIVE_STATUSES`; no `FOR UPDATE` | F-01 |
| `backend/appointment/main.py:400-412` | `doctor_id` used with no `Doctor` lookup; capacity read from the template covering the time | F-05, F-02 |
| `backend/appointment/main.py:418-423` | Capacity rejection raises `422` | F-01, F-19 |
| `backend/appointment/main.py:431-439` | `branch_id` derived by the resolver and written with no scope check | F-06 |
| `backend/appointment/main.py:440`, `:448-450` | Write/insert after the unlocked read | F-01, F-02 |
| `backend/appointment/main.py:460-479` | Audit-event pattern used by mutations | F-12, §7.2 |
| `backend/appointment/main.py:495-503`, `:528-541` | Grid endpoint's unbounded date window | F-17 |
| `backend/appointment/main.py:731-741` | Detail read: `get_current_user` + `organization_id` only | F-09 |
| `backend/appointment/main.py:748-773` | `VALID_TRANSITIONS` whitelist; `appointment.modify` gate | F-07, §7.2 |
| `backend/appointment/main.py:755` | Status mutation loaded by org only | F-08 |
| `backend/appointment/main.py:802-847` | Reschedule writes time with no capacity check | F-04 |
| `backend/appointment/main.py:883-897` | Check-in depends on `get_current_user` only and calls the transition function directly; writes queue state | F-07, F-08 |
| `backend/appointment/main.py:1047-1088` | Transfer: unvalidated `new_branch_id` and `start_time` | F-10, F-11 |
| `backend/appointment/appt_filters.py:168-189` | Read-path branch confinement; non-disclosing `404`; `403` on missing token branch | F-06, F-08, F-09, §7.1 |
| `backend/appointment/appt_filters.py:196-300` | Row shape joins doctor/branch/patient — the disclosure surface for F-05 | F-05 |
| `backend/common/auth.py:401-425` | `require_branch_access` — documented, correct, unused by appointment writes | F-06, F-08 |
| `backend/common/auth.py:430-448` | `branch_accessible` — org_admin/cross-org pass, everyone else must match | F-06, F-08, §9 |
| `backend/common/permissions.py:96-106` | The doctor role holds appointment `read` only — the role the bypass serves | F-07 |
| `backend/common/models.py:547` | `start_time` is nullable `String(10)` | F-01, F-11 |
| `backend/common/models.py:591-595` | Appointment indexes are non-unique search indexes | F-01 |
| `backend/alembic/versions/5f3fce6757cf:128-129` | Initial schema's non-unique indexes; no capacity constraint anywhere in the chain | F-01 |
| `backend/scheduling/main.py:32-37` | `slot_templates` times typed as plain `str`, no format constraint | F-14, F-02 |
| `backend/scheduling/main.py:67-105` | Schedule create: silent date substitution, no audit, no template validation | F-12, F-13, F-14 |
| `backend/scheduling/main.py:143-170` | Schedule update: same three omissions | F-12, F-13 |
| `backend/scheduling/main.py:171-221` | `available-slots`: no weekday/effective-window test; per-slot count loop | F-15 |
| `backend/scheduling/main.py:191-199` | Template parsing by split/cast — the `500` on malformed data | F-14 |
| `backend/scheduling/sessions.py` | Sessions project into `slot_templates` | §7.3, §7.4 |
| `frontend/lib/calendar/grid.js:30-32` | `ACTIVE_STATUSES` mirrors the backend set | F-19, §7.4 |
| `frontend/lib/calendar/grid.js:122-133` | `expandTemplate` — the client slot strings F-03 depends on | F-03 |
| `frontend/lib/calendar/grid.js:135-152` | Schedule/template selection by weekday only; ignores effective dates | F-16 |
| `frontend/lib/calendar/grid.js:160-175` | `slotsForDate` — shared derivation and the capacity badge | F-03, F-16, F-19, §7.1 |
| `frontend/pages/appointments.js:46-91`, `:92+` | BN and EN dictionaries | F-19 |
| `frontend/pages/appointments.js:1011-1018` | Free-text time field offered when a day publishes no slots | F-18 |
| `frontend/pages/appointments.js:505-514` | Day rows from the grid endpoint; shared derivation consumed | §7.1 |
| `frontend/pages/appointments.js:564` | Server rejection appended verbatim after a translated prefix | F-19 |
| `backend/appointment/main.py:325-328` | Session-window refusal — applied only when the doctor holds an active session that weekday | F-02, F-16 |
| `backend/appointment/main.py:407-412` | Capacity read from the template covering the time; the hard-coded `1` when none matches | F-02, F-03 |
| `backend/appointment/main.py:829-847` | Reschedule writes the new time with no capacity check | F-04 |
| `backend/appointment/main.py:1076` vs `:1081` | Chamber resolved for the fallback time; the row written with the raw field | F-11 |
| `backend/scheduling/main.py:84-95` | Schedule create resolves `Branch` and `Doctor` in the tenant and checks `branch_accessible` — the pattern the appointment writes lack | F-05, F-06 |
| `frontend/lib/calendar/grid.js:179-192` | `capacityFor` falls back to 1 when no schedule covers the time — the client mirror of the server default | F-02, F-18 |

| `frontend/pages/appointments.js:1004-1034` | Slot buttons and availability rendering | F-18, F-19 |
| `frontend/package.json:9` | Frontend test command (`node --test tests/*.test.mjs`) | §8.1 |
| `backend/conftest.py:1-15` | Suite bootstrap; `AMSDP_DATABASE_URL` requirement | §8.1 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:144-160` | §4 strict tenant isolation (FINALIZED) | F-05 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:199-214` | §6 shared patient records; branch-level permissions | F-06, F-09 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:313-315` | §10.8-10.9 shared across branches subject to permissions; never across orgs | F-06, F-09 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:386-397` | §15 schedule configuration; validate at save time | F-04, F-15 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:415-424` | §17 transfer: same org, capacity, reason, history | F-10, F-11 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:548-561` | §22 overbooking: disabled by default; authorised, reasoned, audited | F-04, F-11 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:563-577` | §23 capacity and double-booking protection; atomic at save time | F-01, F-02, F-03 |
| `docs/product/AMSDP_Business_Rules_V1.0.md:1011-1016` | §51 acceptance: concurrent bookings cannot exceed capacity | F-01 |
| `docs/implementation/AMSDP_Phase_0_…_Report_V1.0.md:103` | Finding 8.3 graded NOT A DEFECT on a mitigation the code does not implement | F-08 |
| `.clinerules` §3 | Tenant/branch non-disclosure, audit, migrations, no silent overrides | F-01…F-12 |
| `.clinerules` §7 | Evidence standard — why every finding here is CODE-READ | §1.2, §12 |
| `.clinerules` §9 | Execution boundaries — no unrequested suites, no destructive Git | §1.2, §8, §12 |
| `.clinerules` §11/§12 | Document placement and index obligation; read-before-plan | §12 |

---

## Appendix B — Documents and sources read

**Governance and product**
- `.clinerules` (router; §1 precedence, §3 non-negotiables, §4 routing, §7 evidence, §9 boundaries, §11 placement, §12 reading)
- `docs/governance/AMSDP_Docs_Index_V1.0.md`
- `docs/governance/AMSDP_Engineering_Governance_Assessment.md` (routing detail)
- `docs/product/AMSDP_Business_Rules_V1.0.md` — §4, §6, §10, §15, §17, §19-20, §22, §23, §27, §51
- `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
- `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md`
- `docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md`
- `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md`
- `docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md` (prior diagnosis, defects now fixed)

**Backend**
- `backend/appointment/main.py` (full)
- `backend/appointment/appt_filters.py`
- `backend/appointment/tests/test_appointment.py`, `test_reschedule.py` (+ test inventory for the remaining three files)
- `backend/scheduling/main.py`, `backend/scheduling/sessions.py`
- `backend/common/auth.py`, `backend/common/permissions.py`, `backend/common/models.py`
- `backend/alembic/versions/*` (chain inspection for capacity constraints)
- `backend/conftest.py`

**Frontend**
- `frontend/pages/appointments.js`
- `frontend/components/AppointmentCalendar.js`
- `frontend/lib/calendar/grid.js`
- `frontend/lib/i18n.js`
- `frontend/package.json`
- `frontend/tests/` (inventory)

**Not available during this analysis**
- The knowledge-base/memory tool at `127.0.0.1:8888` returned `ECONNREFUSED` throughout. **No memory-derived claim appears in this document**; every statement rests on a file read in this session. It is recorded here because `.clinerules` §7 requires that evidence be attributed to an artefact that actually existed.

---

## Appendix C — Verification of the read-only claim

### C.1 Repository identity

```
$ git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD
hackathon-mvp
6d3acdf
```

### C.2 Working tree, captured before the analysis began

```
 M backend/common/auth.py
 M backend/identity/main.py
 M backend/identity/routes.py
 M backend/identity/tests/test_identity.py
 M backend/queuing/tests/test_queue.py
 M backend/tests/test_sequence3.py
 M docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md
 M docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md
?? docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md
```

### C.3 Working tree, captured after the report was written

```
 M backend/common/auth.py
 M backend/identity/main.py
 M backend/identity/routes.py
 M backend/identity/tests/test_identity.py
 M backend/queuing/tests/test_queue.py
 M backend/tests/test_sequence3.py
 M docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md
 M docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md
?? docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md
?? docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md
```

### C.4 The diff, and what it proves

```
$ diff <before> <after>
10a9
> ?? docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md
```

*(The two extra leading lines in the raw before-capture were the branch and commit echoed by the same command; the working-tree entries are identical.)*

**One line added. Nothing changed.** No RBAC-workstream file appears as newly modified, no file disappeared, and no content of the nine pre-existing entries was touched. The single new entry is this report.

### C.5 Commands issued during the analysis

| Command | Class | Purpose |
|---|---|---|
| `git rev-parse --abbrev-ref HEAD`, `git rev-parse --short HEAD` | read-only | Record the baseline commit |
| `git status --porcelain` (before, after) | read-only | Prove the tree was left untouched |
| `ls backend/pytest.ini setup.cfg pytest.ini pyproject.toml tox.ini` | read-only | Establish the pytest configuration situation (§8.1) |
| `wc -l`, `sed -n`, `grep -n -A`, `cut`, `cat` on repo files and `/tmp` scratch files | read-only | Evidence gathering and paging |
| `sed -n '1,40p' frontend/package.json` | read-only | Confirm the test script name (§8.1) |
| `python3 -c …` (heading inventory, severity tally, duplicate-line and adjacent-separator sweep) | read-only | Verify this document's own structure after the final editing pass |
| `python3 -c …` (strip trailing blank lines, in place) | **write — to this document only** | Remove the stray blank lines left at EOF by the section splice; no other file was opened for writing |

**Not run, deliberately:** `pytest` (any selection), `npm test`, `alembic upgrade/downgrade`, `docker compose …`, any HTTP request to a running service, any SQL statement. Each is listed as a *future* exit criterion in §8.3 and §9, not as something this analysis performed.

### C.6 What a reviewer should treat as unproven

1. **Every severity rating is a judgement**, informed by the Business Rules and `.clinerules` §3, not a measurement. F-07 is the only Critical because it is an authorization bypass that also writes into another service's table — no reading of the rules makes it a preference. F-05 is High and not Critical because the read-side joins are tenant-scoped, so a foreign `doctor_id` discloses nothing; it would become Critical only if a read path stopped scoping. If the owner rules Q4 differently for branches, F-06/F-08/F-09 downgrade accordingly while F-05 does not move.
2. **No defect here has been observed failing.** Each is a reading of the code. The first task of any fix stage is to convert the relevant row of §8.3 from "No" to a passing test — a finding that cannot be made to fail is a finding that should be withdrawn, and saying so is cheaper than shipping a guess.
3. **Test counts are search counts**, not execution results (§8.1). They describe the size of the corpus, not its health.

---

*End of document — V1.0, 2026-11-19. Read-only analysis; no product code, test, migration or configuration was modified.*

---

## Appendix D — Closure status after `AMSDP-APPT-OWNER-DECISIONS-01` (2026-11-19)

**This appendix supersedes the "two are closed only in part" clause of the front-matter's
*Remediation outcome* row and nothing else.** The analysis above is untouched: it remains a
`CODE-READ` record of the tree at `6d3acdf`, and the front matter's revision history is
deliberately not rewritten. What follows states where each finding stands after the second work
order.

| Finding | Status after the second work order | Evidence |
|---|---|---|
| **F-01** | **CLOSED** — the application lock *and* the database constraint the rules require: `slot_allocations` with `UNIQUE (doctor_id, appointment_date, slot_key, seat_number)` and `UNIQUE (appointment_id)`, claimed under the doctor row lock, released by the single status writer. Historical keys are approximated on backfill; pre-existing overruns are reported, not repaired. | `appointment/tests/test_capacity_integrity.py` (10), migration `a9c4e1f7b2d8` |
| **F-18** | **CLOSED** — the outside-session booking is now a persisted type (`unscheduled`) created only through a reasoned, capability-gated, organization-limited, audited override; a day with no published slots no longer invites an arbitrary time. | `test_appointment.py` override cases, `appointment-booking-feedback.test.mjs` |
| F-03, F-04, F-11 | unchanged — closed by the first work order; the window-based seat count now also charges a mid-window booking to its window (§3.1 of the specification), which strengthens rather than weakens them | first report §4 |
| All other findings (F-02, F-05 … F-10, F-12 … F-17, F-19) | unchanged from the first work order | first report §4 |

**Three further questions this analysis raised are now answered** and were not findings in their
own right: check-in was a side effect of `appointment.modify` (now `appointment.check_in`, own
capability, ownership-narrowed); a doctor working without a receptionist could not register a
walk-in (now may, for their own patients, without gaining `appointment.modify`); and a
central-receptionist had no way to book across branches (now an explicit, branch-scoped,
revocable grant).

Behavioural specification: `docs/architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md`.
Implementation report: `docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md`.

*This appendix is an addition, not a rewrite. No line above it was modified.*

