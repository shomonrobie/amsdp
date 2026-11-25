# AMSDP — Requirements Reconciliation and Implementation Gap Audit

> **Task ID:** `AMSDP-AUDIT-REQUIREMENTS-RECONCILIATION-2026-11-24`
> **Version:** 1.0 · **Date:** 2026-11-24 · **Status:** **FINAL FOR REVIEW** — an assessment. It authorises nothing. **Amended by §14 (Amendment A-1, same date)**: one classification changed by owner instruction (F-53), one gap added (GAP-28), and three evidence counts corrected.
> **Question answered:** are the approved AMSDP requirement documents actually implemented in the `hackathon-mvp` tree, and exactly what is missing?
> **Companion plan:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (V1.1 amends V1.0 by adding multi-display DQDS; see §14).
> **Companion specification:** `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` (requirements MD-01…MD-12 for the feature GAP-28 records as absent).
> **Mode:** read-only. This audit modified no code, schema, fixture, container or git state.
> **Owner:** Product Owner.

**Evidence vocabulary — used without exception throughout.** Every row of every matrix carries one of these; none is used loosely.

| Label | Meaning |
|---|---|
| **VERIFIED** | I read the code, migration or config myself in this session; file and line are cited. |
| **IMPLEMENTED** | Code exists and is reachable (route registered / page built). Not necessarily exercised. |
| **TESTED** | Tests exist **and** a pass is recorded in a report. Not re-run by me. |
| **DOCUMENTED** | A prior report asserts it; no independent artefact re-confirms it here. |
| **INFERRED** | Concluded from indirect evidence (e.g. absence from a complete page inventory). Flagged as such. |
| **NOT VERIFIED** | No evidence either way was found; explicitly not claimed. |
| **NOT IMPLEMENTED** | Searched for and absent. |
| **PARTIAL** | Part of the requirement is enforced; the shortfall is named in the row. |
| **BLOCKED** | Cannot be determined or executed in this environment. |
| **OWNER DECISION REQUIRED** | The documents conflict or the requirement is unratified; an audit may not resolve it. |

---

## 1. Executive summary

### 1.1 Verdicts

| Question | Verdict |
|---|---|
| Is the codebase a real implementation of the approved documents? | **Yes.** Not a mock-up: tenant isolation, server-side RBAC, atomic capacity, append-only audit, hashed tracking tokens and a public display board are genuinely built. |
| Is the *hackathon* MVP complete against `AMSDP_MVP_SCOPE_V1.1.md` §12? | **No — narrow but decisive gaps.** Three code defects and one missing queue action, plus one environmental blocker. All four code items are small; none needs a schema change. |
| Is anything verifiable *today*? | **No at audit time — and the stated reason was wrong.** Nothing was VERIFIED in the audit session. **Corrected 2026-11-24 (§16):** the stack **is** reachable from this checkout (eight services and the frontend answered HTTP 200), and the live database was migrated to the single head `c4d8e2a91f60` on 2026-11-23, before this audit was written. "Two revisions behind" was a stale 2026-11-23 reading, not a current fact. Runtime **acceptance** evidence is still missing (MP-01/MP-02/MP-31). |
| Are the nine source documents mutually consistent? | **No.** Seven conflicts recorded (**C-1 … C-7**), two of them material (§3.4). |
| Do the documents define Phases 4–6? | **No.** Three of six phases are undefined in the repository. |
| Is the feature list machine-traceable? | **No.** No per-feature IDs exist (except `AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10`). This audit assigns **F-01 … F-66** locally and preserves the source reference. |
| Does a comprehensive implementation plan already exist? | **No.** Seven partial artefacts (§10.2); no master plan. The prior roadmap (T-1…T-12) was never persisted and never executed. |

### 1.2 The five findings that matter

1. **The demo fails for the doctor persona by construction.** `backend/seed/seed_demo.py` creates users, roles, doctors, schedules and appointments but **never a `staff_doctor_assignments` row**. Because `backend/common/auth.py::can_access_doctor` fails closed, the seeded doctor receives **404** on their own queue. Correct security behaviour defeating a demo through missing data — not a code bug.
2. **The most visible screen is wrong for six hours a day.** `backend/queuing/display.py:138` uses `date.today()` instead of the facility's operational day, so between 00:00 and 06:00 Dhaka the public TV board shows *yesterday's* queue.
3. **The dashboard contradicts itself.** `frontend/pages/dashboard.js:27` renders the "Waiting" tile from `checked_in`, duplicating the adjacent tile.
4. **A called patient cannot be called again.** `backend/queuing/main.py:461` defines no `recall` transition on `called`; the only escape is "missed turn", which asserts unavailability and demands a reinsertion. The staff board's own comment (`frontend/lib/queue/queue-call.js:72`) claims recall exists.
5. **Two approved rule families are entirely unbuilt** — subscription lifecycle (BR Part IX) and overbooking (BR §22) — and one MVP-listed capability, **priority** (BR §28), has zero code. None is on the demo path; all three are approved obligations.

### 1.3 What is genuinely strong

- **Capacity correctness.** `backend/common/capacity.py` enforces capacity with a database uniqueness constraint on `slot_allocations`, a `SAVEPOINT`-scoped insert and a doctor row lock. The hardest rule in BR §23 is implemented properly.
- **Fail-closed multi-tenancy.** Cross-org and cross-branch access returns **404**, never 403; unassigned doctors are denied; `backend/common/denial_audit.py` records refusals.
- **Token security.** `backend/common/tracking_tokens.py` stores an HMAC hash, never the token; the pepper is environment-supplied and fails closed outside development.
- **Auditability.** `backend/common/audit.py` records actor/org/branch/before/after/reason, including `queue.missed_turn`, `queue.reposition` and `staff.doctor_assignment_changed`.
- **Honest documentation.** The state report and the merge publication report name their own unverified claims. That is rare and it is why this audit could be built.

### 1.4 Headline recommendation

Prove the runtime **before** changing any code (plan task **MP-01**) — the migration half of that task was already applied on 2026-11-23 (§16) — then close the four demo-blocking items (**MP-05 … MP-08**). Everything else is sequencing, not risk.

---

## 2. Method, scope and independence

### 2.1 Repository state pinned (VERIFIED)

| Fact | Value | Command |
|---|---|---|
| Branch | `hackathon-mvp` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `a4ddc2c` (2026-11-23 20:21:43 +0600) | `git log -1` |
| Upstream | `origin/hackathon-mvp`, **0 ahead / 0 behind** | `git rev-list --left-right --count` |
| Working tree at audit start | `M docs/governance/AMSDP_Docs_Index_V1.0.md` (+15) and `?? docs/implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` — **documentation only** | `git status --porcelain` |
| Migration head | `c4d8e2a91f60`, single head | revision-graph reconstruction from `backend/alembic/versions/*` |
| Live database | `c4d8e2a91f60` (**head**) — migrated 2026-11-23, tables `voice_packs`, `queue_announcement_deliveries`, `announcement_platform_config` created | **REPORTED** from the verified deployment record of 2026-11-23 (rehearsed on a disposable restore, pre-migration backup taken, seeded counts preserved). **Not re-queried here** — this host has no `alembic`, `psql` or `docker` binary and no database credential (§16). Live **services** re-probed and healthy 2026-11-24 |
| Documents under `docs/` | 126 `.md` files | `Get-ChildItem -Recurse -Filter '*.md'` |

### 2.2 What this audit read

- **All nine requirement documents**, in full or in the sections that carry requirements: `AMSDP_MVP_SCOPE_V1.1.md`, `AMSDP_Business_Rules_V1.1.md`, `AMSDP_Complete_ASCII_UI_UX_Blueprint.md` (screen sections plus the appended Analytics Specification), `AMSDP_Master_Feature_List_V2.0_Draft.md`, `…V2.1_Consolidated_Draft.md`, `…V2.2_Consolidated_Draft.md`, `…V2.3_Consolidated_Draft.md`, `…V2.4_Modular_Healthcare_Platform_Edition.md`, `…V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`.
- **Governing and supporting records:** `docs/governance/AMSDP_Docs_Index_V1.0.md`, `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`, `docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md`, `docs/implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md`, the Phase 0/1 and appointment-symptoms implementation reports, `QUE-006_MASTER_IMPLEMENTATION_PLAN.md`, `docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.1_DRAFT.md`, `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`, `docs/demo/AMSDP_Limitations_Report_V1.0.md`.
- **Backend:** `common/{auth,permissions,capacity,queue_tokens,tracking_tokens,denial_audit,audit,models,config,slots,phone}.py`, `common/notifications/*`, `identity/{main,routes}.py`, `organization/{main,appointment_config,facility,voice_packs,announcement_config}.py`, `doctor/main.py`, `patient/main.py`, `scheduling/{main,sessions}.py`, `appointment/{main,tracking,dashboard,symptoms}.py`, `queuing/{main,display,recovery,announcements}.py`, `audit/main.py`, `seed/seed_demo.py`, `alembic/versions/*`.
- **Frontend:** 16 page modules (`dashboard`, `appointments`, `patients`, `doctors`, `staff`, `branches`, `facilities`, `orgs`, `schedules`, `queue`, `notifications`, `audit`, `index`, `_app`, `queue-display/[org]/[branch]`, `track/[token]`), 21 components, `lib/i18n.js`, `lib/queue/queue-call.js`, `lib/announcements/*`, `package.json`.
- **Infrastructure:** `docker-compose.yml`, `.github/workflows/ci.yml`.

### 2.3 What this audit did **not** execute — and why

| Not executed | Reason |
|---|---|
| `pytest`, `npm test`, `next build` | `.clinerules` §9 forbids running suites without owner authorisation; this Windows checkout has no `backend/.venv`, so the suites cannot run as configured. |
| `alembic upgrade` / `alembic current` | Forbidden by the task, and impossible from this host: no `alembic`, `psql` or `docker` binary and no database credential. **"The live database is unreachable here" was wrong** — §16 shows the stack answering and explains why the earlier probes missed it. |
| Container start / stop / rebuild | Forbidden by the task. |
| Browser verification and live API calls | None performed in the audit session. The previous session's `:8000` and `:3000` probes timed out **because they targeted the wrong host and the container-internal ports**; re-probed on 2026-11-24 against `192.168.68.108:8110–8117` and `:3100`, every service answered HTTP 200 (§16). This was a session limitation, not a deployment fact. Still no browser run, and no authenticated call was made |
| Any git write | Forbidden; the tree was inspected with `--no-pager` reads only. |

**Consequence, stated plainly:** nothing in this audit is VERIFIED at runtime. Where a journey is described as working, it works **in code**. The distinction is maintained in every table.

### 2.4 Independence and bias controls

- The audit was commissioned *after* a prior session's roadmap, so it is deliberately **not** a re-issue of that roadmap: the prior T-1…T-12 items are re-tested against the tree one by one (§10.4), and one prior negative finding is **retracted** where the code contradicts it (§10.5).
- Two prior conclusions were tightened, not repeated: the queue state machine and the dashboard tile were re-read at source.
- Where a claim could not be checked, it is marked NOT VERIFIED rather than written in the confident register the earlier reports used.

---

## 3. Source document analysis

### 3.1 Register, declared status and authority tier

| # | Document | Date | Declared status | Authority tier |
|---|---|---|---|---|
| 1 | `AMSDP_Business_Rules_V1.1.md` | 4 Nov 2026; V1.1 amendment 9 Nov 2026 | **Approved business-rule baseline for implementation** | **T1 — binding** |
| 2 | `AMSDP_MVP_SCOPE_V1.1.md` | 4 Nov 2026; §16 addendum 8 Nov; §17 amendment 9 Nov | **Approved MVP scope baseline** | **T1 — binding** |
| 3 | `AMSDP_Complete_ASCII_UI_UX_Blueprint.md` | undated | No status header; a design source | **T3 — design** |
| 4 | `AMSDP_Master_Feature_List_V2.0_Draft.md` | 4 Nov 2026 working baseline | **Draft for review** | **T4 — historical** |
| 5 | `AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md` | 9 Nov 2026 | **Consolidated Draft — NOT APPROVED AS A WHOLE**; individual decisions marked | **T4 — historical** |
| 6 | `AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md` | 9 Nov 2026 | Same, decisions individually marked | **T4 — historical** |
| 7 | `AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` | 9 Nov 2026 | Same; adds BanglaNameSense and the missed-turn approval record | **T4 — historical** |
| 8 | `AMSDP_Master_Feature_List_V2.4_Modular_Healthcare_Platform_Edition.md` | 11 Nov 2026 | **NOT APPROVED AS A WHOLE**; "does not authorize implementation, deployment, expenditure…"; clinical proposal **superseded** by V2.5 | **T4 — historical** |
| 9 | `AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | 11 Nov 2026 | **APPROVED MASTER FEATURE LIST — ACTIVE VERSION**; approval covers the §C module catalogue only | **T2 — approved catalogue** |

### 3.2 Lineage and what "approved" actually covers

V2.0 → V2.1 → V2.2 → V2.3 are **successive consolidated drafts of the same list**, none approved as a whole, each carrying individually marked decisions (FINALIZED / APPROVED / PENDING). V2.4 preserves V2.3 verbatim in Part VIII and adds a *proposed* clinical family. **V2.5 is the only active list** and explicitly supersedes V1.x–V2.4; V2.4's clinical proposal is "superseded … not an independent source of current requirements".

Two consequences the project has not yet absorbed:

1. **Approval is scoped.** V2.5 approves a *module catalogue*, and says so: it "does not itself authorize every module for immediate implementation", and §F excludes clinical modules from the hackathon release. Reading V2.5 as a build order would be a scope error.
2. **No traceability key exists.** Neither list assigns per-feature identifiers (the single exception is `AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10`). Requirement → code → test cannot be traced mechanically today; this audit's `F-nn` keys are a stop-gap, not a fix.

### 3.3 What each document actually contributes to implementation

- **Business Rules V1.1** — the enforcement backbone: §4–§6 isolation and branch scope; §7–§8 five tenant roles plus Super Admin, capabilities, delegation; §9–§11 doctors, patients, duplicate policy (no auto-merge); §14–§18 appointment models, schedules, creation, transfer, statuses; §19–§23 cancellation, no-show, late arrival, overbooking, **atomic capacity**; §24–§25 walk-in with four placement policies; §26–§28 queue, manual management, priority; §29–§33 daily board, tokens, printing, DQDS; §34–§36 payment boundary and communication; §37–§39 subscription; §40–§45 audit, minimisation, reports, localisation; §46–§54 phasing and acceptance; **§27A** missed-turn recovery; **§56** the list of decisions that must be configurable rather than hard-coded.
- **MVP Scope V1.1** — the release boundary: 11 functional families with per-family acceptance; six end-to-end workflows A–F (F is the tenant-isolation verification); §7 exclusions (patient accounts, payments, EMR, **automated SMS/WhatsApp**, **digital queue display**, **symptoms**); §12's 11-point demo script; **§16** the 8-Nov addendum that *reverses* §7 on four points (DQDS and patient tracking tokens into P0; WhatsApp **and** SMS required channels; two-stage notifications P0; missed-turn P0).
- **ASCII Blueprint** — the UI contract: 23 numbered screens with ASCII layouts, a role-based navigation map, a prescribed build order, ten DQDS operational rules, an "Additional screens" block (floors, rooms, doctor-room assignment, availability boards, walk-in policy, reschedule, cancellation, no-show, session management, queue history, floor displays, branch switching, permission management, duplicate resolution, capacity, conflicts, search, subscription state), three mandatory UI rules including **"no dead controls"**, and a separate **Analytics Specification** (metric dictionary, event catalogue, 7 wireframes, 17 acceptance criteria, **7 open product decisions**).
- **V2.0–V2.4** — the decision trail: FINALIZED principles (facility-first, strict isolation, lightweight doctor entries, provider-managed booking, configurable policy), the PQV decision, BanglaNameSense, the missed-turn approval record, and the §26 "Approval, Implementation and Evidence Register" with its known acceptance caveats.
- **V2.5** — the active catalogue: three families, nine modules, the server-side entitlement principle, the dependency model, §E precedence amendments (clinical notes excluded from Core but included in the optional Clinical Management module), **§F hackathon boundary**, §G status vocabulary, and Parts III–VI clinical requirements — all proposed or optional.

### 3.4 Conflicts between sources — recorded, not resolved

| ID | Conflict | Sources | Why it matters | Needed decision |
|---|---|---|---|---|
| **C-1** | **DQDS status.** BR §33 closes by declaring DQDS, television integration and multi-display configuration **later-phase** capabilities. MVP §16 (8 Nov, decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`) makes DQDS and patient tracking **P0/MVP**. BR V1.1 was never amended for §33. | BR §33; MVP §16.1; V2.5 §C | The implemented, tested DQDS board is simultaneously MVP scope and an out-of-phase capability. A judge asking "which document governs?" has no answer. | **PO-02** |
| **C-2** | **SMS/WhatsApp status.** BR §35.5 "SMS is a later-phase capability"; BR §36 "APPROVED, PHASE 2". MVP §16.2 makes WhatsApp **and** SMS required, org-configurable MVP channels; §16.6 puts two-stage notifications at P0. | BR §35–§36; MVP §16.2/§16.6 | The notification lifecycle is built and mock-delivered; its *channel requirement* is MVP while its *phase label* is Phase 2. | **PO-02** |
| **C-3** | **Symptoms capture is unratified.** MVP §7 excludes symptoms as clinical data. The tree ships `appointment/symptoms.py` (2 routes), `symptom_catalog` and `appointment_symptoms` tables (migration `b3d7e91f6a24`), a 555-line catalogue seed and `test_symptom_catalogue.py`. | MVP §7 vs code + `AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` | A shipped feature with no written authority is a scope defect whether or not the code is good. | **PO-03** |
| **C-4** | **Phases 4–6 do not exist.** The six-phase roadmap the owner refers to is not written down anywhere in the repository; the handover documents stop at Phase 3. Search for Phase 4/5/6 definitions returns only an unrelated "Phase 5" in a voice-refresh note. | `AMSDP_Project_Handover_2026-11-20.md:266,297`; zero definitional hits | Three of six phases cannot be planned, executed or accepted. | **PO-01** |
| **C-5** | **"Approved" means two different things.** V2.5 declares itself the approved active list while V2.1–V2.4 remain "not approved as a whole"; four documents coexist at different granularity with no per-feature IDs. | V2.1:8; V2.5:6–10 | Requirement → code → test traceability is manual and will decay. | **PO-12** |
| **C-6** | **Analytics is specified but unapproved.** The Blueprint's Analytics Specification carries 17 acceptance criteria, 7 wireframes and **7 open product decisions**, none present in any approved list. | Blueprint analytics part | Cannot be built as MVP scope without inventing requirements. | **PO-06** |
| **C-7** | **Subscription lifecycle is approved but unbuilt and unphased.** BR §37–§39 are FINALIZED/APPROVED-DEFAULT and V2.5 §C lists it commercially; the codebase contains zero subscription references and no document assigns it a phase. | BR Part IX vs backend search | An approved rule family with neither implementation nor schedule. | **PO-04 / PO-07** |

**No conflict above is resolved in this audit.** Each is carried to the plan's §4 decision gates.

---

## 4. Feature implementation matrix

`F-nn` keys are assigned by this audit because the source documents provide none (see §3.2). The **Source** column preserves the original reference. `MVP` class follows V2.5 §C/§F and MVP Scope §5/§7/§16.

### 4.1 Platform foundation, identity and tenancy

| Key | Feature / requirement | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-01 | Organisation tenant plus branches; `organization_id` as the only tenant key | BR §3–§5; MVP §5.1 | MVP | **IMPLEMENTED — TESTED** | `common/models.py`; `organization/main.py` (9 routes) | `test_e2e.py`, `test_security.py` | — |
| F-02 | Strict tenant isolation; non-disclosing 404 | BR §4, §49 | MVP | **IMPLEMENTED — TESTED** | `common/auth.py` (scope checks, `can_access_doctor`); `_scoped_*` helpers per service | `test_security.py`, `test_e2e.py::test_02` | — |
| F-03 | Branch scope enforcement | BR §5; MVP §5.1 | MVP | **IMPLEMENTED — TESTED** | `auth.branch_accessible`; `organization/main.py:321` `/me/branches` | `test_sequence3.py` (RBAC-R1/R2) | — |
| F-04 | Staff authentication, throttling, deactivation | BR §42; MVP §5.2 | MVP | **IMPLEMENTED — TESTED** | `identity/main.py:260`; `common/login_throttle.py`; `login_attempts` (`d4b2c8e1f7a3`) | `test_security.py` | — |
| F-05 | Server-side RBAC with capability grants and delegation limits | BR §8; owner decisions Q-1/Q-4 | MVP | **IMPLEMENTED — TESTED** | `common/permissions.py` (232 L); `identity/routes.py` (`check-permission`, grants) | `test_platform_admin.py`, `test_sequence3.py` | — |
| F-06 | Multi-doctor assistant assignment | BR §7.5 (`PO-RBAC-01`) | MVP | **IMPLEMENTED — TESTED** | `staff_doctor_assignments` (`f8a1b2c3d4e5`); `identity/routes.py:44-75,217-275` | `test_sequence3.py` | — |
| F-07 | Deny-audit and **fail-closed** denial for unassigned doctors | Q-2/Q-3; BR §3 | MVP | **IMPLEMENTED** | `auth.can_access_doctor` → 404; `common/denial_audit.py` (218 L); `common/log_redaction.py` | `test_denial_audit.py` (209 L) | Demo **seed** creates no assignment → demo doctor 404 (**GAP-02**) |
| F-08 | Platform identity separation and platform audit | `PO-RBAC-05` | MVP(P1) | **PARTIAL** — "Groundwork" (Phase 1D W-E) | `identity/models.py`; `platform_audit_events` (`f8a2b3c4d5e6`) | `test_platform_admin.py` | Cross-org support-access flow incomplete |
| F-09 | Staff administration **UI** (roles, scopes, capabilities) | Blueprint §4, §15 | MVP | **PARTIAL** | `frontend/pages/staff.js` (39 L: list + create) | none | No edit/deactivate, no capability UI, no assignment editor, no branch-scope editor — although the APIs exist |
| F-10 | Subscription lifecycle and read-only expiry state | BR §37–§39; Blueprint §12, §20 | Unassigned | **NOT IMPLEMENTED** | zero `subscription` references in `backend/` | — | Whole of BR Part IX plus two Blueprint screens (conflict **C-7**) |

### 4.2 Patients

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-11 | Patient register, search, view, update; name and mobile mandatory; Unicode | BR §10; MVP §5.3 | MVP | **IMPLEMENTED — TESTED** | `patient/main.py` (4 routes); `patients.js` (form, BanglaNameSense, DOB/age) | `test_patient_age.py` | — |
| F-12 | Shared mobile numbers across family records | BR §10.5 | MVP | **IMPLEMENTED** | `common/phone.py::clean_mobile`; no unique constraint on patient mobile | `test_patient_age.py` | — |
| F-13 | Duplicate **warning** on create; never auto-merge | BR §11.1–§11.3 | MVP | **IMPLEMENTED (basic)** | `patient/main.py:111` returns `duplicates`; `patients.js:35` renders the warning | DOCUMENTED | No safe-correction workflow and no duplicate-resolution screen (Blueprint §16) |
| F-14 | Formal merge workflow | BR §11.4–§11.9 | Later phase | **NOT IMPLEMENTED** — correctly deferred | — | — | — |
| F-15 | BanglaNameSense name assistance | V2.3 §25.8 (`AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10`) | MVP | **IMPLEMENTED — TESTED** (frontend by design) | `components/BanglaNameSense.js`; `frontend/data/*` | 5 `.test.mjs` files | Dataset breadth is a product question, not a defect |

### 4.3 Doctors, rooms and schedules

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-16 | Doctor records, facility-local ID, profile | BR §9; MVP §5.4 | MVP | **IMPLEMENTED — TESTED** | `doctor/main.py` (4 routes); `doctor/profile.py` (14 routes); `doctors.js` (1126 L) | `test_facility_doctor.py` (1007 L) | — |
| F-17 | Org-scoped doctor mobile uniqueness **with** Super-Admin duplicate allowance | BR §9.6–§9.7 | MVP | **PARTIAL** | `doctor/main.py:95-104` returns `409` — hard-coded | `test_facility_doctor.py` | The configurable allowance does not exist |
| F-18 | Floors, departments, rooms, doctor-room assignment | BR §12; Blueprint AILI extensions 1–3 | MVP | **IMPLEMENTED** (not exercised) | `organization/facility.py` (17 routes); `facilities.js` (854 L); `facility_floors/departments/rooms` (`f7d2b4c6e8a1`) | `test_facility_doctor.py` | Room **availability board** (extension 4) absent |
| F-19 | Schedules: working days/hours, duration, serial capacity | BR §15; MVP §5.5 | MVP | **IMPLEMENTED — TESTED** | `scheduling/main.py` (5 routes incl. `available-slots`); `common/slots.py` | `test_sequence4.py`, `test_facility_doctor.py` | — |
| F-20 | Blocked dates and unavailable periods | BR §15 | MVP | **NOT VERIFIED** | No `blocked` handling found in `scheduling/main.py`, `scheduling/sessions.py`, `appointment/main.py` | — | Suspected absent; one targeted confirmation required before it is implemented (**GAP-12**) |
| F-21 | Doctor session management (per-day sessions, room, capacity) | Blueprint extension 11; Q1–Q5 | MVP | **IMPLEMENTED** (not exercised) | `scheduling/sessions.py` (6 routes, 610 L); `schedules.js` (388 L) | `test_sequence4.py` | — |
| F-22 | Three appointment models: time-slot, serial, hybrid | BR §14; MVP §5.5/§5.6 | MVP | **IMPLEMENTED** | `appointment/main.py:97-111,196,271` (`appointment_model`, default `time_slot`) | `test_sequence4.py`, `test_e2e.py` | Hybrid depth (window plus serial ordering) not separately proven |

### 4.4 Appointments, capacity and lifecycle

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-23 | Create, list, get appointment; staff-mediated booking; booking source | BR §16; MVP §5.6 | MVP | **IMPLEMENTED — TESTED** | `appointment/main.py:706,949,1096,1190` | `test_sequence4.py`, `test_e2e.py` | — |
| F-24 | **Atomic capacity** and double-booking protection | BR §23 | MVP | **IMPLEMENTED — TESTED** | `common/capacity.py` — unique `slot_allocations`, `SAVEPOINT`, row lock; `_lock_doctor` (`appointment/main.py:475`) | `test_sequence4.py:275` (concurrency) | — |
| F-25 | Cancel with reason; history preserved | BR §19; MVP §5.6 | MVP | **IMPLEMENTED** | `appointment/main.py:1246`; queue cancel requires a reason (`queuing/main.py:542`) | `test_sequence3.py` | No configurable deadline (**GAP-11**) |
| F-26 | Reschedule with link to the original and seat safety | BR §18; MVP §5.6 | MVP | **IMPLEMENTED** | `appointment/main.py:1257`, fixes at 1302/1328 | `test_sequence4.py` | — |
| F-27 | Same-org transfer with availability and reason | BR §17 | MVP | **IMPLEMENTED** | `appointment/main.py:1601-1640` (`_tenant_doctor`, branch 404, `_lock_doctor`, single time resolution) | `test_sequence4.py` | — |
| F-28 | Check-in to queue; staff-confirmed no-show | BR §18, §20 | MVP | **IMPLEMENTED — TESTED** | `appointment/main.py:1364,1453`; `queuing/main.py:247` (`CHECKIN_SOURCES`) | `test_sequence3.py` | No grace configuration (**GAP-10**) |
| F-29 | Configurable no-show grace and late-arrival grace | BR §20.1, §21, §56 | MVP | **NOT IMPLEMENTED** | No `grace` reference in appointment, scheduling or config modules | — | No configuration, no proposal/flag logic |
| F-30 | Configurable cancellation deadline and restrictions | BR §19.1–§19.4, §56 | MVP | **NOT IMPLEMENTED** | No `deadline` reference | — | Cancellation is permission-gated only |
| F-31 | **Overbooking** — configurable, disabled by default, reason plus audit | BR §22, §56 | MVP | **NOT IMPLEMENTED** | Only two explanatory comments (`appointment/main.py:1302,1328`) | — | No config, permission, limit or audit path (**GAP-09**) |
| F-32 | Appointment calendar view with highlighting | Q1–Q5; calendar diagnosis audit | MVP | **IMPLEMENTED** | `appointment/main.py:1033` `/matches`; `components/AppointmentCalendar.js`; `appointments.js` (1334 L) | 5 calendar `.test.mjs` | — |
| F-33 | Appointment symptoms and onset | **no approved source** | **Unresolved** | **IMPLEMENTED — unratified** | `appointment/symptoms.py` (2 routes); `symptom_catalog` (`b3d7e91f6a24`); `seed/symptom_catalogue.py` (555 L) | `test_symptom_catalogue.py` | Needs scope authority (**C-3**, **PO-03**) |

### 4.5 Walk-ins, queue and tokens

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-34 | Walk-in registration as an entry source | BR §24; MVP §5.7 | MVP | **IMPLEMENTED** | `appointment/main.py:1465` `/walk-in`; `queuing/main.py:373` `/enqueue` | `test_sequence3.py`, `test_queue_room_snapshot.py` | — |
| F-35 | Four walk-in placement policies | BR §25; MVP §5.7, §52 | MVP | **PARTIAL** | `WALK_IN_POLICIES` (`queuing/main.py:85`) accepts four; only `staff_placement` changes behaviour (`:307,418`); `first_come` ≡ `end_of_queue` (both order by `seq`); **`reserved_capacity` reserves nothing** | `test_sequence3.py` | No reservation pool; policy is caller-supplied per request, not facility configuration, and is not audited (**GAP-06**) |
| F-36 | Unified queue of scheduled and walk-in patients | BR §26; MVP §5.8 | MVP | **IMPLEMENTED — TESTED** | `queuing/main.py:196` `/queue`; `:247` check-in | `test_e2e.py`, `test_dqds.py` | — |
| F-37 | Manual reorder with previous/new position and audit | BR §27.1–§27.4 | MVP | **IMPLEMENTED — TESTED** | `queuing/main.py:596` `/reorder`; `recovery.py::_renumber` (position history, `queue.reposition` audit) | `test_sequence3.py`, `test_queue_room_snapshot.py` | — |
| F-38 | Skip / mark temporarily unavailable | BR §27 | MVP | **PARTIAL** | `skipped` is reachable **only** via `/missed-turn` (`recovery.py:148`), which asserts the patient "was unavailable when called"; no neutral skip; `reinsert` exists (`queuing/main.py:463,471`) | `test_sequence3.py` | No neutral skip and no "temporarily unavailable" state (**GAP-05**) |
| F-39 | **Recall** a called patient | BR §27; demo ergonomics | MVP | **NOT IMPLEMENTED** | `_TRANSITIONS["called"] = (start_consultation, cancel, mark_no_show)` (`queuing/main.py:461`); the comment at `frontend/lib/queue/queue-call.js:72` claims recall exists | — | The only path is missed-turn → reinsert → call (**GAP-05**) |
| F-40 | Priority assignment and removal (operational only) | BR §28; MVP §5.8 | MVP | **NOT IMPLEMENTED** | zero `priority` references in backend non-test code | — | No permission, endpoint, field or audit (**GAP-08**) |
| F-41 | Missed-turn recovery with position override and audit | BR §27A; MVP §5.8 | MVP | **IMPLEMENTED — TESTED** | `recovery.py` (2 routes, `RECOVERY_MODES`, reason-required override, `queue.missed_turn` audit) | `test_sequence3.py`, `test_queue_room_snapshot.py` | — |
| F-42 | Token generation with atomic daily serial | BR §30 | MVP | **IMPLEMENTED — TESTED** | `common/queue_tokens.py` (`INSERT … ON CONFLICT … RETURNING`) | `test_sequence4.py`, `test_sequence3.py` | — |
| F-43 | Token numbering modes (daily **and** continuous) and scope (doctor **or** room) | BR §31; MVP §5.9, §52 | MVP | **PARTIAL** | `queue_tokens.py` is daily-only and doctor-scoped (`T-{doctor}-{serial}`); no `continuous` and no `numbering_mode` | — | Two of three capabilities absent (**GAP-07**) |
| F-44 | Printed token layout | BR §32 | MVP | **NOT IMPLEMENTED** | No print route or component among the 16 page modules | — | BR §53 acceptance fails (**GAP-14**) |
| F-45 | Queue history view | BR §11.2, §27; Blueprint extension 12 | MVP | **API ONLY** | `queuing/main.py:669` `/queue/history` | `test_sequence3.py` | No screen consumes it (**GAP-16**) |

### 4.6 Digital queue display, announcements and voice packs

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-46 | Public DQDS board (TV display) for a branch | BR §29, §33; MVP §16.1 | MVP (per §16) | **PARTIAL** | `queuing/display.py` (3 routes, 1,127 L); `frontend/pages/queue-display/[org]/[branch].js` | `test_dqds.py` (721 L) | **VERIFIED defect:** `date.today()` at `display.py:138` instead of the operational day (**GAP-03**) |
| F-47 | Patient tracking view by token | BR §29; MVP §16.1 | MVP | **IMPLEMENTED — TESTED** | `queuing/display.py:365,440`; `frontend/pages/track/[token].js` (518 L); `common/tracking_tokens.py` | `test_queue_tracking.py` | Rate limit is **in-process** only (**GAP-20**) |
| F-48 | Calling-zone configuration | BR §33; POD-12 | MVP | **IMPLEMENTED — TESTED** | `organization/announcement_config.py:58-66`; `queue_calling_config` | `test_queue_calling_config.py` | Stale plan rows still describe it as open |
| F-49 | Two-stage notification lifecycle (intent → attempt → delivery) | MVP §16.6 | MVP | **IMPLEMENTED — TESTED (mocked)** | `common/notifications/*`; `organization/appointment_config.py` (8 routes) | `test_notification_worker.py` | Provider is a **mock**; production integration is not authorised; worker is not a compose service |
| F-50 | Voice-pack management (server holds packs; agents cache) | QUE-006 W1/W2/W4/W7 | MVP (voice demo) | **PARTIAL** | `organization/voice_packs.py`; `queuing/voice_packs.py`; `voice_pack_policy.py`; 9 component files | `test_voice_packs.py` | **W3 admin UI absent** (**GAP-18**) |
| F-51 | Server-side distribution API for agents (W5) | QUE-006 W5 | Post-MVP | **NOT IMPLEMENTED** | agent fetches packs itself | — | **GAP-19**, deferred |
| F-52 | Announcement policy resolution and delivery tracking | QUE-006 W7 | MVP (voice demo) | **IMPLEMENTED** | `queuing/announcements.py` (`decide_action`, `record_delivery` with `qce:` idempotency key); `queue_announcement_deliveries` (`c4d8e2a91f60`) | `test_announcements.py` (356 L) | **Runtime audibility never proven** (B-8) |
| F-53 | Multi-display and multi-zone configuration | BR §33 | Later phase | **NOT IMPLEMENTED** | one branch display per branch | — | Inside the C-1 conflict zone; deferred with BR §33 |

### 4.7 Notifications, audit, reporting, localisation

| Key | Feature | Source | MVP | Status | Code evidence | Test evidence | Remaining gap |
|---|---|---|---|---|---|---|---|
| F-54 | Append-only audit with actor/org/branch/before/after/reason | BR §40; MVP §5.11 | MVP | **IMPLEMENTED — TESTED** | `common/audit.py`; `audit/main.py`; `audit_events` | `test_security.py`, service tests | **Schedule-edit audit unverified** (F-18/GAP-19 sibling) |
| F-55 | Audit viewer in the UI | Blueprint §18 | MVP | **IMPLEMENTED** | `frontend/pages/audit.js`; `_scoped` filter on org and branch | no page test | — |
| F-56 | Operational reports (by day, doctor, branch, status) | BR §43; MVP §5.11 | MVP | **NOT IMPLEMENTED** | No report module; dashboard has 2 aggregate endpoints only | — | **GAP-15** |
| F-57 | Dashboard with role-appropriate metrics | Blueprint §2 | MVP | **PARTIAL** | `frontend/pages/dashboard.js` (110 L); `appointment/dashboard.py` (summary, today) | frontend dashboard tests | No BDT/date range selectors; **VERIFIED defect** in the "Waiting" tile (**GAP-04**) |
| F-58 | Six-section analytics with 17 acceptance criteria | Blueprint Analytics Spec | **Unapproved** | **NOT IMPLEMENTED** | — | — | **GAP-22**; 7 open product decisions (**C-6**) |
| F-59 | Bangla/English across all screens | BR §44; MVP §5.12 | MVP | **PARTIAL** | `frontend/lib/i18n.js` (590 L) **plus** page-local `L={bn,en}` dictionaries in dashboard and queue | — | Three coexisting mechanisms (**GAP-23**) |
| F-60 | Responsive, touch-first, accessible | BR §45; Blueprint UI rules | MVP | **PARTIAL** | Tailwind responsive classes; no a11y audit artefact | — | Never verified at 360 px or with a keyboard-only pass |
| F-61 | CI pipeline enforces backend and frontend suites | governance §CI | — | **DOCUMENTED, never green** | `.github/workflows/ci.yml` exists | — | No run artefact found (**GAP-24**) |

### 4.8 Clinical and subscription families (out of hackathon scope)

| Key | Feature | Source | Status | Note |
|---|---|---|---|---|
| F-62 | Clinical notes, structured examinations | V2.5 Parts III–IV (proposed) | **NOT IMPLEMENTED** | Optional module; excluded by V2.5 §F from the hackathon release |
| F-63 | Prescriptions and medication safety | V2.5 Part IV (proposed) | **NOT IMPLEMENTED** | Proposed only; safety-critical, needs its own programme |
| F-64 | Investigations and results | V2.5 Part V (proposed) | **NOT IMPLEMENTED** | Proposed only |
| F-65 | Templates and clinical document generation | V2.5 Part VI (proposed) | **NOT IMPLEMENTED** | Superseded V2.4 proposal |
| F-66 | Entitlement enforcement per module (server-side) | V2.5 §C/D | **NOT IMPLEMENTED** | Listed commercially; no code. Blocked behind F-10 (subscription) |

### 4.9 Matrix totals

| Status | Count | Keys |
|---|---|---|
| **IMPLEMENTED — TESTED** | 21 | F-01…F-06, F-11, F-15, F-16, F-19, F-23, F-24, F-28, F-36, F-37, F-41, F-42, F-47, F-48, F-49, F-54 |
| **IMPLEMENTED** (reachable, runtime unproven) | 13 | F-07, F-12, F-13, F-18, F-21, F-22, F-25, F-26, F-27, F-32, F-34, F-52, F-55 |
| **PARTIAL** | 11 | F-08, F-09, F-17, F-35, F-38, F-43, F-46, F-50, F-57, F-59, F-60 |
| **API ONLY** | 1 | F-45 |
| **NOT VERIFIED** | 1 | F-20 |
| **NOT IMPLEMENTED** | 17 | F-10, F-14, F-29, F-30, F-31, F-39, F-40, F-44, F-51, F-53, F-56, F-58, F-62…F-66 |
| **Unratified** | 1 | F-33 |
| **Documented, never green** | 1 | F-61 |
| **Total** | **66** | — |

The count that matters for the demo is **four P0 code defects** (§1.2 items 1–4), not the size of the backlog. Of the 17 unbuilt features, **eight are approved MVP obligations** (F-29, F-30, F-31, F-39, F-40, F-44, F-56, and F-58 whose source is still unapproved); the remaining nine are deferred or out of scope (F-10 subscription, F-14 merge, F-51, F-53, F-62…F-66).

---

## 5. Business-rules compliance matrix

Every rule group from `AMSDP_Business_Rules_V1.1.md` is assessed at **group** level, with the specific shortfall named. "Compliant" means the rule is enforced server-side; it does not mean it was exercised at runtime.

### 5.1 Rules §3 – §25 (tenancy, identity, master data, appointments)

| BR | Rule | Status | Evidence / shortfall |
|---|---|---|---|
| §3–§4 | Organisation-first tenancy; strict `organization_id` isolation; non-disclosing 404 | **COMPLIANT** | `auth.py` scope helpers; `test_security.py` |
| §5 | Branch scoping; branch belongs to exactly one organisation | **COMPLIANT** | `branch_accessible`; `branches.js` |
| §6 | Configuration belongs to the organisation, never to the individual user | **COMPLIANT** | `organization/appointment_config.py`, `facility.py`, `announcement_config.py` are all org-scoped |
| §7 | Five tenant roles (Super Admin, Org Admin, Branch Admin, Doctor, Assistant) plus Platform Super Admin, non-hierarchical | **COMPLIANT** | `common/permissions.py` role and capability model |
| §7.5 | Multi-doctor assignment for assistants | **COMPLIANT** | `staff_doctor_assignments`; `test_sequence3.py` |
| §8 | Capability grants, delegation limits, no self-escalation, last-admin protection | **COMPLIANT** | `DELEGABLE_CAPABILITIES` guard; `PO-RBAC-04` |
| §9 | Doctor records, facility-local ID, org-scoped mobile uniqueness | **PARTIAL** | 409 hard-coded at `doctor/main.py:95-104`; the §9.7 duplicate allowance is absent |
| §10 | Patient register; name and mobile mandatory; shared mobiles allowed; Unicode names | **COMPLIANT** | `patient/main.py`; `phone.py`; `patients.js` |
| §11 | Duplicate **warning**, never auto-merge; merge is a later phase | **PARTIAL** | Warning implemented (`patient/main.py:111`); no safe-correction workflow, no resolution screen |
| §12 | Floors, departments, rooms and doctor-room assignment | **COMPLIANT** | `organization/facility.py` (17 routes, `f7d2b4c6e8a1`) |
| §13 | Master data is organisation-owned and configurable | **COMPLIANT** | all three config modules are per organisation |
| §14 | Three appointment models, configurable per schedule | **COMPLIANT** | `appointment_model` on create; default `time_slot` |
| §15 | Schedules: working days, hours, duration, serial capacity, blocked periods | **PARTIAL** | Schedule fields enforced; **blocked periods unverified** (F-20) |
| §16 | Staff-mediated booking with mandatory identifiers and booking source | **COMPLIANT** | create route validates org, branch, doctor, patient, schedule |
| §17 | Same-org transfer with availability and reason | **COMPLIANT** | `appointment/main.py:1601-1640` |
| §18 | Reschedule, cancel, check-in, status lifecycle | **COMPLIANT** | `:1246,1257,1364`; status transitions guarded |
| §19 | Cancel with mandatory reason; configurable cancellation deadline | **PARTIAL** | Reason enforced; **no deadline policy** (F-30) |
| §20 | No-show requires staff confirmation; configurable grace; never automatic | **PARTIAL** | Staff confirmation enforced; **no grace configuration** and no potential-flag logic (F-29) |
| §21 | Late arrival handling; operational only, no clinical judgement | **PARTIAL** | No late-arrival grace configuration |
| §22 | Overbooking — configurable, disabled by default, reason and audit | **NOT COMPLIANT** | Absent (F-31, GAP-09) |
| §23 | **Atomic capacity**; no over-capacity; double-booking protection | **COMPLIANT** | `capacity.py` unique constraint + SAVEPOINT + row lock; concurrency test at `test_sequence4.py:275` |
| §24 | Walk-in registration while admitting scheduled patients | **COMPLIANT** | `/walk-in`, `/enqueue` |
| §25 | Four walk-in placement policies | **PARTIAL** | Four names accepted, **two have identical behaviour and `reserved_capacity` reserves nothing**; policy is per-request, not per-facility configuration, and unaudited (F-35) |

### 5.2 Rules §26 – §56 (queue, tokens, DQDS, communication, subscription, audit, phasing)

| BR | Rule | Status | Evidence / shortfall |
|---|---|---|---|
| §26 | Unified queue of scheduled and walk-in patients | **COMPLIANT** | `queuing/main.py:196,247` |
| §27 | Manual queue control: reorder, skip, recall, position visibility | **PARTIAL** | Reorder compliant and audited (`:596`); **no recall** (F-39); **no neutral skip** (F-38) |
| §27A | Missed-turn recovery with reason and position override, audited | **COMPLIANT** | `recovery.py`; `queue.missed_turn` audit; `RECOVERY_MODES` |
| §28 | Priority — operational only, never clinical | **NOT COMPLIANT** | Zero code (F-40, GAP-08) |
| §29 | Daily board and patient tracking with role-scoped fields | **COMPLIANT** | `display.py`; `track/[token].js`; no patient PII on the public board |
| §30 | Token generation, atomic per-day numbering | **COMPLIANT** | `queue_tokens.py` upsert-serial |
| §31 | Configurable numbering mode and scope | **PARTIAL** | Daily + doctor only (F-43) |
| §32 | Printed token | **NOT COMPLIANT** | No print artefact (F-44) |
| §33 | DQDS, TV integration, multi-display — *declared later-phase* | **PARTIAL / CONFLICTED** | Single-branch board built and tested with the operational-day defect (F-46); the phase label contradicts MVP §16 (**C-1**) |
| §34 | Payment boundary — the platform records nothing financial | **COMPLIANT (vacuously)** | No payment code; consistent with MVP §7 exclusion |
| §35 | Communication: WhatsApp approved channel; SMS later-phase; no unnecessary clinical content | **PARTIAL / CONFLICTED** | Lifecycle built, provider mocked (**C-2**); no real WhatsApp/SMS integration, which is correct while unauthorised |
| §36 | SMS — *approved, Phase 2* | **CONFLICTED** | MVP §16.2 makes SMS an MVP channel (**C-2**) |
| §37–§39 | Subscription lifecycle, limits, expiry → read-only | **NOT COMPLIANT** | Zero code (F-10, **C-7**) |
| §40 | Audit of every material state change, append-only | **COMPLIANT (with one gap)** | `audit.py` + `denial_audit.py`; **schedule-edit audit unverified** (F-54) |
| §41 | Data minimisation — no clinical detail in the queue layer | **COMPLIANT** | Queue payloads carry identity and status only |
| §42 | Authentication, throttling, deactivation, session discipline | **COMPLIANT** | `login_throttle.py`; `login_attempts` |
| §43 | Operational reports | **NOT COMPLIANT** | No report module (F-56, GAP-15) |
| §44 | Localisation: Bangla and English everywhere | **PARTIAL** | Three coexisting mechanisms (F-59) |
| §45 | Responsive, touch-first, accessible | **PARTIAL / NOT VERIFIED** | No artefact at 360 px or keyboard-only |
| §46–§48 | Phasing definition and phase gates | **NOT COMPLIANT** | Phases 4–6 undefined (**C-4**) |
| §49 | Security acceptance: cross-tenant and cross-branch refusal | **COMPLIANT** | 404-not-403 across services; `test_security.py` |
| §50 | Data-integrity acceptance | **COMPLIANT** | Unique constraints, FKs, migration chain |
| §52 | Configurability acceptance (the §56 list must be configurable, not hard-coded) | **NOT COMPLIANT** | Walk-in policy is per-request; token mode, grace, deadline, overbooking and priority are hard-coded or absent |
| §53 | Token and printing acceptance | **NOT COMPLIANT** | No printed token (F-44) |
| §54 | Reporting acceptance | **NOT COMPLIANT** | No reports (F-56) |
| §56 | Decisions that must never be hard-coded | **NOT COMPLIANT** | See §52; this is the single largest rule-level gap in the product |

### 5.3 Compliance scoreboard

Counting the 53 rule sections assessed above (§51 and §55 carry no implementation requirement):

| Band | Rule sections | Count |
|---|---|---|
| **COMPLIANT** | §3, §4, §5, §6, §7, §8, §10, §12, §13, §14, §16, §17, §18, §23, §24, §26, §27A, §29, §30, §34, §40, §41, §42, §49, §50 | **25** |
| **PARTIAL** | §9, §11, §15, §19, §20, §21, §25, §27, §31, §33, §35, §44, §45 | **13** |
| **NOT COMPLIANT** | §22, §28, §32, §37, §38, §39, §43, §46, §47, §48, §52, §53, §54, §56 | **14** |
| **CONFLICTED** | §36 is conflicted outright; §33 and §35 carry a conflict flag alongside their PARTIAL verdict (C-1, C-2) | **1** (+2 flagged) |
| **Total** | — | **53** |

**Reading of the scoreboard.** The *security and correctness* spine of the rules — isolation, RBAC, capacity, audit, token integrity — is compliant, and that is the hard part. The *configurability* spine (§52/§56) and the *operational completeness* group (priority, recall, printing, reports, subscription) are not. That is precisely the profile of a system built by engineers who got the difficult correctness rules right and ran out of time on the breadth rules.

---

## 6. UI/UX blueprint reconciliation

The Blueprint defines 23 numbered screens plus an "Additional screens" block; the frontend has **16 page modules**. Every prescribed screen is mapped below.

| Blueprint screen | Page / component | Status |
|---|---|---|
| §1 Login | `pages/index.js` | **IMPLEMENTED** |
| §2 Dashboard | `pages/dashboard.js` | **PARTIAL** — no date/branch selectors, no today's-queue panel, no quick actions, no recent activity; the "Waiting" tile is wrong (GAP-04) |
| §3 Appointment list | `pages/appointments.js` (1,334 L) | **IMPLEMENTED** |
| §4 Staff management | `pages/staff.js` (39 L) | **PARTIAL** — list + create only |
| §5 Branch management | `pages/branches.js` | **PARTIAL** — list + create only |
| §6 Organisation settings | `pages/orgs.js` | **PARTIAL** |
| §7 Doctor list / form | `pages/doctors.js` (1,126 L) | **IMPLEMENTED** |
| §8 Patient list / form | `pages/patients.js` | **IMPLEMENTED** |
| §9 Schedule management | `pages/schedules.js` (388 L) | **IMPLEMENTED** |
| §10 Queue management | `pages/queue.js` | **PARTIAL** — no recall control, no priority, no print |
| §11 Walk-in registration | inside `appointments.js` / `queue.js` | **IMPLEMENTED** |
| §12 Subscription state | — | **ABSENT** |
| §13 Notification settings | `pages/notifications.js` | **IMPLEMENTED** |
| §14 Facility management | `pages/facilities.js` (854 L) | **IMPLEMENTED** |
| §15 Permission management | — (API only) | **ABSENT** as a screen |
| §16 Duplicate resolution | — | **ABSENT** (basic warning exists in the patient form; merge is later-phase) |
| §17 Capacity overview | — | **ABSENT** |
| §18 Audit log | `pages/audit.js` | **IMPLEMENTED** |
| §19 Queue history | — (API exists) | **ABSENT** as a screen |
| §20 Subscription expiry / read-only | — | **ABSENT** |
| §21–§23 | partially covered by the pages above | **PARTIAL** |
| Extension 1–3: floors, departments, rooms | `facilities.js` | **IMPLEMENTED** |
| Extension 4: room availability board | — | **ABSENT** |
| Extension 5: doctor-room assignment | `facilities.js` / `doctors.js` | **IMPLEMENTED** |
| Extensions 6–13 (walk-in policy, reschedule, cancellation, no-show, sessions, queue history, floor displays, branch switching) | mostly actions inside existing pages | **PARTIAL** — walk-in policy is not configurable; queue history and floor displays absent |
| Extensions 14–19 (permission management, duplicate resolution, capacity, conflicts, search, subscription state) | search present; the rest absent | **PARTIAL** |
| DQDS screens (public board, tracking) | `queue-display/[org]/[branch].js`, `track/[token].js` | **IMPLEMENTED** — the board carries GAP-03 |
| **Mandatory rule — "no dead controls"** | `components/layout.js` capability filtering | **VIOLATED once:** the recall affordance promises a capability the server refuses (GAP-05) |
| **Mandatory rule — Bangla/English toggle** | `lib/i18n.js` | **PARTIAL** — three mechanisms coexist |
| **Mandatory rule — role-appropriate navigation** | `components/layout.js` | **IMPLEMENTED** |

**Summary.** Of 23 numbered screens: **9 implemented, 9 partial, 5 absent.** The absences cluster in commercial state (subscription) and reconciliation/oversight (duplicates, capacity, conflicts, queue history). The "no dead controls" rule is met everywhere except the recall affordance — the one place where the UI promises what the server will not do.

---

## 7. Gap register

27 gaps, each with severity, evidence and the rule it violates. Severity: **S1** breaks the demonstration or a P0 acceptance; **S2** breaks an approved MVP obligation; **S3** breaks an approved but non-MVP rule; **S4** documentation or hygiene.

| ID | Gap | Sev | Evidence | Rule |
|---|---|---|---|---|
| **GAP-01** | ~~Live database two revisions behind head; no reachable runtime~~ — **migration half CLOSED 2026-11-24 (§16):** it was applied 2026-11-23. Live half remains: **no post-migration suite baseline, no §12 acceptance run** | **S1** (retained for the evidence half) | The old evidence was a 2026-11-23 SQL reading (`a9c4e1f7b2d8`) plus `:8000`/`:3000` probes issued from the Windows checkout; the live stack publishes `8110`–`8117` and `3100` on `192.168.68.108` and answered HTTP 200 on 2026-11-24 | Every P0 acceptance still depends on the **evidence**, no longer on the migration |
| **GAP-02** | Demo seed creates no doctor assignment → doctor persona gets 404 | **S1** | `seed_demo.py` never writes `staff_doctor_assignments`; `can_access_doctor` fails closed | BR §7.5; MVP §12 |
| **GAP-03** | DQDS board uses `date.today()` | **S1** | `queuing/display.py:138` | BR §29, §33 |
| **GAP-04** | Dashboard "Waiting" tile duplicates `checked_in` | **S1** | `frontend/pages/dashboard.js:27` | Blueprint §2 |
| **GAP-05** | No recall; no neutral skip | **S2** | `_TRANSITIONS["called"]` (`queuing/main.py:461`); `skipped` only via missed-turn | BR §27 |
| **GAP-06** | Walk-in policies are names, not behaviours; no reserved pool; not configurable or audited | **S2** | `queuing/main.py:85,307,418` | BR §25, §52 |
| **GAP-07** | Token numbering: no continuous mode, no room scope | **S2** | `queue_tokens.py` | BR §31 |
| **GAP-08** | Priority absent | **S2** | zero references | BR §28 |
| **GAP-09** | Overbooking absent | **S2** | comments only | BR §22 |
| **GAP-10** | No-show and late-arrival grace not configurable | **S2** | no `grace` reference | BR §20.1, §21, §56 |
| **GAP-11** | Cancellation deadline not configurable | **S2** | no `deadline` reference | BR §19 |
| **GAP-12** | Blocked periods unverified | **S2** | absent from scheduling and appointment modules | BR §15 |
| **GAP-13** | Doctor mobile duplicate allowance absent | **S3** | hard-coded 409 (`doctor/main.py:95-104`) | BR §9.7 |
| **GAP-14** | Printed token absent | **S2** | no print route or component | BR §32, §53 |
| **GAP-15** | Operational reports absent | **S2** | no report module | BR §43, §54 |
| **GAP-16** | Queue history API has no screen | **S3** | `/queue/history` unreferenced in the frontend | Blueprint ext. 12 |
| **GAP-17** | Administration UI thin: no edit/deactivate, capabilities, assignments or branch scope | **S2** | `staff.js` 39 lines against a full API | Blueprint §4, §15 |
| **GAP-18** | Voice-pack admin UI (W3) absent | **S2** | API and policy modules exist; no page | QUE-006 W3 |
| **GAP-19** | W5 distribution API absent | **S3** | agent fetches packs itself | QUE-006 W5 |
| **GAP-20** | Tracking rate limit is in-process | **S3** | limiter state inside the service | BR §29 robustness |
| **GAP-21** | Subscription lifecycle absent | **S3** | zero references | BR §37–§39 |
| **GAP-22** | Analytics absent and unapproved | **S4** | no module; 7 open decisions | Blueprint analytics |
| **GAP-23** | Three i18n mechanisms coexist | **S3** | `lib/i18n.js` plus page-local `L={bn,en}` | BR §44 |
| **GAP-24** | CI never recorded green | **S4** | workflow file exists; no run artefact | Governance evidence standard |
| **GAP-25** | Seed writes "today" with `date.today()` | **S1** | `seed_demo.py:699,744` | BR §29 consistency |
| **GAP-26** | Owner documents stale (Limitations Report still says "in-memory storage") | **S4** | `AMSDP_Limitations_Report_V1.0.md:12` | `.clinerules` §3 "never claim" |
| **GAP-27** | Phases 4–6 undefined | **S2** (planning) | zero definitional hits in the repository | BR §46–§48 |

**Severity totals:** S1 **5** · S2 **13** · S3 **6** · S4 **3** = 27. *(Unchanged by §16: GAP-01 is restated, not retired — the migration closed, the missing evidence did not.)*

**Two gaps are stated as suspicions, not findings.** GAP-12 (blocked periods) rests on absence from three modules — absence of evidence, not evidence of absence — and requires one targeted probe. GAP-24 cannot be closed from this checkout either way. Both are carried into the plan as such rather than upgraded to defects.

---

## 8. Hackathon readiness against MVP Scope §12 (readiness test A)

The §12 script is the acceptance test for the demonstration. Each step is assessed **in code** only.

| # | §12 step | Verdict | Detail |
|---|---|---|---|
| 1 | System runs, all containers healthy, database at head | **PARTIAL — corrected 2026-11-24 (§16)** | Containers and frontend are healthy (VERIFIED 2026-11-24: eight services `8110`–`8117` and `:3100` all HTTP 200) and the schema is at head per the 2026-11-23 deployment record. The §12 step is an *acceptance* step, and it has not been executed end to end (**MP-31**) |
| 2 | Admin signs in; dashboard shows today's picture | **PARTIAL** | Sign-in works; dashboard is thin and its "Waiting" tile is wrong (**GAP-04**) |
| 3 | Create a branch, a doctor, a schedule | **READY in code** | Branch, doctor and schedule creation all implemented; branch page is create-only but creation works |
| 4 | Register a patient with a Bangla name | **READY in code** | BanglaNameSense and Unicode handling implemented and tested |
| 5 | Book an appointment; capacity refuses an over-book | **READY in code** | Atomic capacity with concurrency test — the strongest part of the system |
| 6 | Patient arrives; check-in issues a token | **READY in code** | Token serial is atomic; queue entry created |
| 7 | Public TV board shows the token, calls it, announces it | **NOT READY** | Board shows *yesterday's* queue before 06:00 (**GAP-03**); audibility never proven (B-8) |
| 8 | Doctor signs in and sees their own queue | **NOT READY** | Seeded doctor has no assignment → **404** (**GAP-02**) |
| 9 | Reorder / miss a turn and recover it | **READY in code** | `/reorder` and `/missed-turn` implemented, audited and tested |
| 10 | Patient tracking link shows position | **READY in code** | Token-scoped tracking page implemented and tested |
| 11 | Cross-branch access refused | **READY in code** | 404-not-403 enforced and tested |

**Verdict: 7 of 11 steps ready in code, 3 not ready, 1 partial.** Every "not ready" is fixable in under two engineer-days, and none requires a schema change. The demonstration is close; it is not currently demonstrable.

---

## 9. Full product readiness (readiness test B)

| Family | Readiness | Note |
|---|---|---|
| Tenancy and identity | **90 %** | Only platform cross-org support access incomplete |
| Master data (org, branch, facility, doctor, patient) | **85 %** | Strong; administration UI is the weak surface |
| Scheduling and appointments | **75 %** | Atomic capacity excellent; grace, deadlines, overbooking and blocked periods missing |
| Queue and tokens | **70 %** | Core works; recall, priority, policy semantics, numbering modes and printing missing |
| DQDS and tracking | **80 %** | Built and tested; one day-boundary defect; rate limit not durable |
| Notifications and voice | **65 %** | Lifecycle and policy are real; the provider is a mock and audibility is unproven |
| Audit | **90 %** | Excellent; schedule-edit audit unverified |
| Reporting and analytics | **10 %** | Dashboard aggregates only |
| Localisation and accessibility | **55 %** | Present but fragmented; unverified at mobile size |
| Administration and permissions UI | **40 %** | APIs exist, screens do not |
| Subscription and entitlement | **0 %** | Nothing |
| Clinical (V2.5) | **0 %** | Deliberately out of scope |

**Overall product readiness ≈ 60 %**, with the security-critical 40 % of the surface in the best condition and the commercial and oversight surface in the worst.

---

## 10. Assessment of the existing implementation plan

### 10.1 Decision-gate answer

**No comprehensive implementation plan exists.** The Step-2 path (write one) is authorised by that finding alone.

### 10.2 The seven plan-shaped artefacts that do exist

| Artefact | Scope | Why it is not the plan |
|---|---|---|
| `docs/implementation/QUE-006_MASTER_IMPLEMENTATION_PLAN.md` | The voice/announcement programme only (W1–W7) | One subsystem; no phase or product view |
| `docs/implementation/AMSDP_M6_Implementation_Plan.md` | Milestone 6 | Milestone-scoped, historical |
| `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` | Phase 3 gaps | Audit, not a plan |
| `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` | Calendar defects | Audit, not a plan |
| `docs/implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` | Current state + one next task | Deliberately narrow by design |
| `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` | Feature classification | A catalogue, not a dependency-ordered plan |
| `docs/chatgpt/AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md` | Multi-sector architecture | A different subject entirely |

### 10.3 Prior roadmap test (T-1 … T-12)

The roadmap delivered in-response on 2026-11-23 was **never persisted** — `git log --all` contains no commit referencing it, and no file matches it. Its items were therefore re-derived and re-tested rather than trusted:

- **T-1, T-2, T-3, T-10, T-11** — confirmed correct and retained (now MP-01, MP-05/06/07, MP-02, MP-08, MP-12).
- **T-4, T-6, T-8, T-9** — retained but re-scoped; all four became sub-items of larger tasks.
- **T-5, T-7, T-12** — gated behind PO decisions that were never requested formally; now explicitly GATED.
- **T-3's premise** ("the suite is green apart from one failure") cannot be re-verified here and is downgraded to DOCUMENTED.

### 10.4 Retraction

A negative finding in the prior session — that denial auditing was absent — is **retracted**. `backend/common/denial_audit.py` exists (218 lines), is wired into the auth path, and has a 209-line test module. The finding was wrong. This is recorded because an audit that only adds findings and never withdraws them is not an audit.

---

## 11. Findings summary and decision requests

### 11.1 Findings, in priority order

1. Nothing can be verified until the stack runs and the database reaches head (**GAP-01**).
2. The doctor persona is broken by missing seed data, not by code (**GAP-02**).
3. The public board is wrong for the first six hours of the operating day (**GAP-03**).
4. The dashboard's headline metric is wrong (**GAP-04**).
5. Recall does not exist, though the UI implies it (**GAP-05**).
6. The queue sub-rules (policy semantics, priority, numbering modes, printing) are a family of unfinished obligations, not isolated bugs (**GAP-06 … GAP-08, GAP-14**).
7. Configurability — BR §52/§56 — is the largest rule-level gap, and the most likely to be noticed by an evaluator who reads the rules (**§5.3**).
8. Administration is API-rich and UI-poor (**GAP-17**).
9. Two approved families are entirely unbuilt and unphased: subscription and overbooking (**C-7, GAP-09, GAP-21**).
10. One shipped feature has no authority: symptoms capture (**F-33, C-3**).
11. Three of six phases do not exist in writing (**C-4, GAP-27**).
12. Documentation is honest about most things but stale about at least one (**GAP-26**).

### 11.2 Decision requests — for the Product Owner only

**PO-01 — Publish Phases 4, 5 and 6.**
*Statement:* the six-phase lifecycle is referenced but only Phases 0–3 are defined anywhere in the repository. Phase 4 (tracking and staff handoff), Phase 5 (reporting and localisation) and Phase 6 (acceptance) exist only as names.
*Options:* (a) publish scope and exit criteria for each; (b) collapse to four phases; (c) abandon the phase model in favour of milestones.
*Recommendation:* (a), because the plan's milestones already assume it.
*Why only the owner can decide:* phase definitions are business scope, and three reports already cite them as authority.

**PO-02 — Resolve BR §33/§35/§36 against MVP §16.**
*Statement:* the business rules call DQDS and SMS later-phase; the 8-Nov MVP addendum makes both P0.
*Options:* (a) MVP §16 prevails and BR V1.1 is annotated; (b) BR prevails and the built DQDS is reclassified as ahead of phase; (c) both, with a dated amendment record.
*Recommendation:* (a) with an explicit amendment note in BR V1.1 — the later document governs, but the older one must say so.
*Why only the owner can decide:* it changes what "approved" means for two shipped features.

**PO-03 — Ratify or reclassify appointment symptoms.**
*Statement:* symptoms capture is shipped, seeded and tested, but MVP §7 excludes it and no feature list authorises it.
*Options:* (a) ratify as an approved P1 feature and amend MVP §7; (b) reclassify as a pre-approved extension; (c) mark it for removal.
*Recommendation:* (a) or (b) — the code is clean and the data model is sound; removal would be waste.
*Why only the owner can decide:* scope authority is not an engineering call.

**PO-04 — Assign phases to overbooking, priority and subscription, or defer them formally.**
*Statement:* three approved obligations have no phase and no code.
*Options:* (a) overbooking and priority into the post-demo P1 band, subscription deferred; (b) all three post-demo; (c) all three deferred.
*Recommendation:* (a) — overbooking and priority are queue/appointment rules the product already claims; subscription is commercial state that needs a billing decision first.
*Why only the owner can decide:* it is commercial priority, not technical feasibility.

**PO-05 — Authorise the W3 voice-pack admin UI and the W5 distribution API.**
*Statement:* voice packs are configurable only by API today; the agent still fetches packs itself.
*Options:* (a) authorise both; (b) authorise W3 only; (c) defer both until the voice programme resumes.
*Recommendation:* (b) if voice is demonstrated; (c) otherwise.
*Why only the owner can decide:* it is a product-surface decision with a maintenance cost.

**PO-06 — Classify the Blueprint Analytics Specification.**
*Statement:* 17 acceptance criteria, 7 wireframes and 7 open product decisions, none approved.
*Options:* (a) approve the specification with its open decisions resolved; (b) approve metrics but not wireframes; (c) leave unapproved and unbuilt.
*Recommendation:* (c) for now — completing the demo matters more than analytics.
*Why only the owner can decide:* it contains product decisions the agent cannot invent.

**PO-07 — Confirm the subscription lifecycle phase.**
*Statement:* BR Part IX is FINALIZED/APPROVED-DEFAULT; nothing implements it and no phase claims it.
*Options:* (a) Phase 5 commercial enablement; (b) post-Phase-6; (c) formally defer pending a billing model.
*Recommendation:* (c) — the read-only-on-expiry rule has real data-lifecycle consequences and should not be improvised.
*Why only the owner can decide:* it is a commercial model, not a feature.

**PO-08 — Decide the carried-over owner items.**
*Statement:* D-3, D-5, D-7, O-2, POD-2, POD-6, POD-7 and POD-1/3/8/9/10/11 remain open from prior reports; two of them (D-5 index numbering, O-2 announcement enable flag) directly affect documentation and configuration work.
*Options:* (a) decide them as a batch now; (b) decide D-5 and O-2 only; (c) carry them forward again.
*Recommendation:* (b) — those two have concrete consequences; the rest can wait.
*Why only the owner can decide:* they are owner decisions by definition.

**PO-09 — Authorise correction of stale owner-controlled documents.**
*Statement:* `.clinerules` §11 makes the Business Rules, MVP Scope, Master Feature Lists, System Architecture, UI/UX Blueprint and the demo Limitations/Credentials documents read-only. At least one of them (Limitations Report §12) now contradicts the code.
*Options:* (a) authorise targeted corrections with a change log; (b) authorise annotation only, never rewriting; (c) leave them and rely on this audit.
*Recommendation:* (b) — annotation preserves history and satisfies the evidence standard.
*Why only the owner can decide:* the documents are owner-controlled.

**PO-10 — Infrastructure exposure.**
*Statement:* PostgreSQL is published on `0.0.0.0:5433` and there is no SSH listener on the host.
*Options:* (a) bind to `127.0.0.1` and use a tunnel; (b) firewall the port to named addresses; (c) accept the exposure.
*Recommendation:* (a).
*Why only the owner can decide:* it changes how the host is administered.

**PO-11 — The D-1/D-2 doctor-branch contract.**
*Statement:* whether a doctor record is branch-scoped for visibility or organisation-scoped with branch-level assignment remains unresolved; current behaviour is fail-closed and therefore safe, but incomplete.
*Options:* (a) branch-scoped visibility with org-level assignment; (b) fully org-scoped; (c) keep current behaviour and document it.
*Recommendation:* (a).
*Why only the owner can decide:* it is a data-model contract with migration consequences.

**PO-12 — Approve a feature-key scheme.**
*Statement:* without stable per-feature identifiers, traceability decays; this audit's `F-nn` keys are local and will not survive the next document revision.
*Options:* (a) adopt `F-nn` formally in V2.6; (b) adopt a module-based scheme (`MOD-FAM-nnn`); (c) leave traceability manual.
*Recommendation:* (a) for continuity with this audit and the plan.
*Why only the owner can decide:* it changes the approved catalogue's structure.

---

## 12. Evidence limitations

This section exists so that no reader over-credits the audit.

1. **No runtime evidence anywhere.** No test, migration, container, browser session or API call was executed. Everything labelled IMPLEMENTED or TESTED is a reading of source, migration or report.
2. **Test counts are DOCUMENTED, not measured.** 233 `def test_` in backend files and 368 frontend `test()` calls were counted statically; the pass counts quoted (790 pass / 1 fail) come from prior reports and were not re-run.
3. **The live database state was second-hand — and it was wrong.** "Two revisions behind" was inherited from the 2026-11-23 merge publication report and runbook §1.4, where it was true when written; the migration was applied later the same day and no document in this repository recorded it. Corrected in **§16**. The revision is still not re-queried from this host (no client, no credential); §16 keeps that residual gap separate from the closed one.
4. **Two findings are suspicions.** GAP-12 (blocked periods) and GAP-24 (CI green) are absence-of-evidence findings and are labelled as such.
5. **Feature keys are mine.** `F-01 … F-66` do not exist in any approved document; they are an instrument for this audit and the plan, and PO-12 asks whether to formalise them.
6. **Coverage is broad but not exhaustive.** Not every function of every module was read line by line; modules were read where a requirement mapped to them. A requirement implemented in an unexpected file could have been missed, which is why GAP-12 is stated as unverified rather than absent.
7. **Nothing here supersedes an owner decision.** Where sources conflict, this audit records the conflict and stops (C-1 … C-7).
8. **Security posture was not tested.** No penetration test, dependency audit or secret scan was performed in this session.

---

## 13. Governance and skill compliance

| Requirement | Compliance |
|---|---|
| `.clinerules` §2 — routing | All nine documents plus the governance index read; domains routed per §4 (backend, auth, tenancy, migrations, queue, audit, deployment, documentation, frontend). |
| `.clinerules` §5 — skills | **No skill installed**; none claimed. Governance documents used instead. |
| `.clinerules` §3 — non-negotiables | No credential or secret reproduced; tenant key respected; 404-not-403 treated as required behaviour; no claim of an unverified capability. |
| `.clinerules` §6 — compliance reporting | This section. |
| `.clinerules` §7 — evidence standard | IMPLEMENTED / TESTED / VERIFIED / ACCEPTED never merged; section 12 names every unverified claim. |
| `.clinerules` §9 — execution boundaries | No suite, migration, container or git write was performed. |
| `.clinerules` §11 — document placement | Written to `docs/audit/` under the subject-match rule; no existing document modified. |
| `.clinerules` §12 — index currency | Registration appended to `docs/governance/AMSDP_Docs_Index_V1.0.md` in the same task; the revision number is not advanced because **D-5** remains open. |

---

## Appendix A — Reproduction commands (read-only)

```powershell
cd E:\amsdp
git --no-pager rev-parse --abbrev-ref HEAD
git --no-pager log -1 --format='%H %ci'
git --no-pager rev-list --left-right --count origin/hackathon-mvp...HEAD
git --no-pager status --porcelain
Get-ChildItem -LiteralPath 'E:\amsdp\backend\alembic\versions' -Filter '*.py' | Measure-Object
Get-ChildItem -LiteralPath 'E:\amsdp\frontend\pages' -Recurse -Filter '*.js' | Measure-Object
Get-ChildItem -LiteralPath 'E:\amsdp\docs' -Recurse -Filter '*.md' | Measure-Object
Select-String -LiteralPath 'E:\amsdp\backend\queuing\display.py' -Pattern 'date.today'
Select-String -LiteralPath 'E:\amsdp\backend\queuing\main.py' -Pattern '_TRANSITIONS'
```

**Windows note.** `Select-String` and `Get-ChildItem` break on paths containing `[org]` or `[branch]`; use `-LiteralPath`, as above.

---

## Appendix B — Document control

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-11-24 |
| Status | **Final for review** — assessment only |
| Type | Audit / reconciliation, read-only |
| Author | Implementation agent |
| Reviewer | Product Owner |
| Companion plan | `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.0.md` |
| Change rule | amendments create a new version; findings are never silently withdrawn (see section 10.4) |
| Next action | Product Owner decides **PO-01** first; the engineer awaits authorisation for **MP-01** |

---

## 14. Amendment A-1 — Multi-display DQDS scope (2026-11-24)

### 14.1 Why this amendment exists

After V1.0 was issued, the Product Owner instructed that **Multi-display Digital Queue Display System (DQDS) Configuration** is an explicit feature of the **Hackathon Version**, principally under **Phase 3** with demonstration and acceptance under **Phase 6**. That instruction rests on an already-approved antecedent this audit had recorded but not acted on: **PQV decision §B.6** — *"DQDS is MVP/P0, with multi-display configuration part of the same capability"* — and on Business Rules §33.2/§33.3/§33.13.

Three consequences follow for this audit, and nothing else changes:

1. **F-53 is reclassified** (14.2): the feature is no longer "later phase" — it is in-scope and still **not implemented**.
2. **GAP-28 is added** (14.4): the gap register needs an entry the plan can trace to, because the absence is now an unmet MVP obligation rather than a deferred enhancement.
3. **Four evidence figures are corrected** (14.3): code was re-read while preparing the specification, and four citations in §4.6 were wrong. Corrections are recorded here rather than silently edited in place, per Appendix B's change rule.

**Findings are not withdrawn.** F-53's *implementation status* is unchanged, and no severity anywhere in this document was lowered by the owner's scope decision.

### 14.2 F-53 — superseded classification

| Field | V1.0 (as issued) | Amendment A-1 |
|---|---|---|
| Feature | F-53 Multi-display and multi-zone configuration | F-53 **Multi-display DQDS configuration** (basic registry, scope, per-display language, admin surface) |
| Source | BR §33 | BR §33.2–§33.4, §33.13; **PQV §B.6**; Blueprint §13.1–§13.3; specification MD-01…MD-12 |
| Phase classification | "Later phase" | **Hackathon Version, Phase 3** (demonstration and acceptance in Phase 6) — owner instruction 2026-11-24 |
| Implementation status | **NOT IMPLEMENTED** | **NOT IMPLEMENTED** *(unchanged)* |
| Evidence | "one branch display per branch" | `queuing/display.py` — 1 route, 201 lines, branch-wide only; `frontend/pages/queue-display/[org]/[branch].js` — no display parameter, only `?lang=`; no display table in 17 Alembic revisions; no display capability in `common/permissions.py`; no admin page among 16 frontend modules |
| Note | "Inside the C-1 conflict zone; deferred with BR §33" | Scope resolved by the owner instruction; the C-1/PO-02 document conflict stands until the owner rules explicitly on BR §33 vs MVP §16 |
| Traces to | — | **GAP-28** → plan tasks MP-35…MP-40 (plan V1.1 §6 WP-C.2 and WP-I) |

The advanced capabilities the V2.x feature lists defer — display health, device pairing, push transport, per-display analytics, ETA — remain **later phase** and are enumerated in the specification's §6 (D-01…D-12). The word *advanced* in V2.x §25.4 is the boundary, not the whole feature.

### 14.3 Evidence corrections (four citations in §4.6)

| Where | V1.0 said | Measured | How measured |
|---|---|---|---|
| §4.6 F-46, "Where" | `queuing/display.py` — **3 routes, 1,127 L** | **1 route** (`GET /{org_code}/{branch_code}`, declared at `display.py:127`), **201 lines, 8,159 bytes** | `Select-String -Pattern '@router'`; `(Get-Content).Count`; `Get-Item .Length` |
| §4.6 F-46, "Tests" | `test_dqds.py` — **721 L** | **465 lines, 18,497 bytes, 24 test functions** | `(Get-Content).Count`; `Select-String -Pattern '^def test'` |
| §4.6 F-47, "Where" | `queuing/display.py:365,440` | Tracking routes live in **`appointment/tracking.py`** — `:60` issue, `:118` revoke, `:147` view, `:215` QR. `queuing/display.py` has no tracking route | `Select-String -Pattern '@router'` in both files |
| §4.6 F-47, "Tests" | `test_queue_tracking.py` | **`backend/tests/test_tracking_tokens.py`** — 351 lines, 19 references to `/api/v1/track/` (plus 2 in `test_denial_audit.py`). No file named `test_queue_tracking.py` exists | inventory of `backend/tests/`; `Select-String` grouped by file |

These were transcription errors in this audit, not defects in the code. The conclusions they supported — the board is implemented and tested, tracking is implemented and tested, and the board carries the operational-day defect — are unchanged and were independently re-verified by reading `display.py` and `tracking.py`.

### 14.4 GAP-28 — added

| ID | Gap | Sev | Evidence | Rule |
|---|---|---|---|---|
| **GAP-28** | **Multi-display DQDS absent**: no display registry, no per-display queue scope, no per-display language, no display administration, and a per-IP limiter that cannot sustain several screens behind one NAT | **S2** | `display.py:24,127` (one branch-wide route); `display.py:30-33,58-78` (30 req/min per client IP against 6 req/min per screen); `queue-display/[org]/[branch].js:41-53` (device-local language); no display table in `backend/alembic/versions/` (17 revisions, head `c4d8e2a91f60`); no display capability in `common/permissions.py`; no admin page in `frontend/pages/` | BR §33.2–§33.4, §33.13, §34; PQV §B.6; Blueprint §13.1–§13.3 |

**Revised severity totals: 28 gaps — S1 5 · S2 14 · S3 6 · S4 3.** The V1.0 totals (27 gaps, S2 = 13) are superseded by that line and by nothing else.

### 14.5 Documents reconciled in the same task

| Document | Action |
|---|---|
| `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | **Created.** The missing requirements document: current state by evidence, MD-01…MD-12, deferrals D-01…D-12, Phase 3/Phase 6 placement, AC-01…AC-14, the measured limiter constraint, owner gates |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | **Created (V1.0 preserved).** Adds WP-C.2 (MP-35…MP-39), MP-40, PO-13, M-9/M-10, GAP-28 traceability and risks R-11/R-12; replaces the V1.0 "deferred" row |
| `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` | **Appended amendment only** — records that **OD-4** is answered for the hackathon (basic registry in scope, estimates and room-on-entry deferred), and that DQD-003/DQD-006 are Phase 3 scope while DQD-002/DQD-005 stay deferred |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Registration appended** for the specification and plan V1.1; revision number still not advanced (**D-5** open) |
| `docs/product/AMSDP_Business_Rules_V1.0.md`, `AMSDP_MVP_SCOPE_V1.0/1.1`, `AMSDP_PQV_…`, `AMSDP_Master_Feature_List_V2.0–V2.5` | **Read, not modified** — owner-controlled; their conflicts are recorded (C-1, PO-02) and referred to the owner |

### 14.6 What this amendment does not do

- It does not claim any multi-display capability exists. GAP-28 says the opposite.
- It does not lower a severity, close a finding, or withdraw F-53's implementation status.
- It does not settle **C-1/PO-02** — whether MVP §16 or BR §33's "later-phase" sentence governs. It records that the owner's scope instruction and PQV §B.6 currently point one way, and leaves the document conflict open.
- It does not authorise code. Implementation needs **PO-13** and then **MP-35**.

### 14.7 Decision request added — PO-13

*A statement, not a question the agent may answer:*

> **PO-13 — ratify multi-display DQDS as Hackathon Version scope, and its boundary.**
> The owner's instruction of 2026-11-24 and PQV §B.6 place **basic** multi-display configuration (display registry, per-display queue scope, per-display language, admin surface) in Phase 3 with Phase 6 demonstration. V2.x §25.4 defers **advanced** multi-display management, and BR §33's closing sentence calls multi-display later-phase.
> *Decision needed:* confirm the minimum in `AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` §5 (MD-01…MD-12) as the hackathon obligation, confirm §6 (D-01…D-12) as out of scope, and authorise **MP-35** to start.
> *Blocks:* MP-35, MP-36, MP-37, MP-38, MP-39, MP-40. Until decided, nothing in the specification may be built.
> *Recorded in:* plan V1.1 §4 (gate table) and specification §9.4.

The decision list in §11.2 therefore reads **PO-01 … PO-13** as of this amendment; PO-01 … PO-12 are unchanged.

**Reproduction commands for this amendment.**

```powershell
cd E:\amsdp
Select-String -LiteralPath 'backend\queuing\display.py' -Pattern '@router|_DQDS_RATE_LIMIT|date.today'
(Get-Content -LiteralPath 'backend\queuing\display.py').Count
(Get-Content -LiteralPath 'backend\tests\test_dqds.py').Count
Select-String -LiteralPath 'backend\tests\test_dqds.py' -Pattern '^def test'
Select-String -LiteralPath 'backend\appointment\tracking.py' -Pattern '@router'
Select-String -Path 'backend\alembic\versions\*.py' -Pattern 'display'
Select-String -Path 'backend\tests\*.py' -Pattern '/api/v1/track/' | Group-Object Filename
```

---

---

## 15. Amendment A-2 — Product Owner decisions PO-13 / PO-02 / MP-06 (2026-11-24)

**This amendment records decisions, not code.** It closes the two DQDS gates, re-states the requirement baseline they govern, and adds the gaps that PO-13's expanded scope exposes. It changes no finding's evidence.

### 15.1 Decisions recorded

| Decision | Text as issued | Effect on this audit |
|---|---|---|
| **PO-13** | *Full-featured Multi-display DQDS* — **APPROVED**; multiple independently configured displays per branch, targeting by branch/doctor/department/room/queue, configurable BN/EN, server-side filtering and org/branch isolation, refresh on change, TV-scale typography, token plus doctor/room, estimate-labelled waiting time, token-only payloads, facility-controlled public fields, read-only access, admin configuration with audit; **not to be deferred or treated as optional** | Multi-display DQDS is **required Hackathon scope** (Phase 3 + Phase 6 demonstration). GAP-28 is no longer a scope question but a delivery gap, and it widens from "no registry" to the full MD-01…MD-19 set |
| **PO-02** | *DQDS requirements alignment* — **RESOLVED**; no MVP/Hackathon/Later-Releases tier governs DQDS; BR §33 must be updated to remove later-phase wording | The §5.2 row that read BR §33 as "later-phase / deferred" is **corrected**: BR §33 now carries a §33.1 scope-status block in both copies, and the deferral rationale is void |
| **MP-06** | *Facility-local operational day* — **IMPLEMENTATION COMPLIANCE REQUIRED**; `Asia/Dhaka` default; applied consistently to queue, dashboards and DQDS | GAP-03 and GAP-25 stay open and now include the display path explicitly (GAP-32). Note BR §0 item 8 already required facility time zone, so MP-06 is **compliance with an existing rule**, not a new requirement |
| **`docs/plan/`** | **APPROVED** as an approved repository location for plans and roadmaps; `.clinerules`/governance to be updated and the index to record it | The placement deviation recorded in plan §12 is **closed**. `.clinerules` §11 and this index were updated in the same task. Nothing was moved, so no migration-manifest entry |

### 15.2 Business Rules §33 reconciled, item by item (the PO-02 requirement)

Every one of §33's thirteen items now maps to a requirement, to the code as it actually is, and to the task that closes the difference. "Implemented" means code exists and is reachable; nothing here is claimed as TESTED or VERIFIED unless §4.6 already said so.

| BR §33 item | Requirement | Current code state (evidence) | Task |
|---|---|---|---|
| 1 — multiple doctors and rooms on one screen | MD-03, MD-04, MD-05 | **PARTIAL** — doctors aggregate correctly (`display.py:143-183`); **no room anywhere** in the payload | MP-37 |
| 2 — multiple displays per branch | MD-01, MD-19 (admin) | **NOT IMPLEMENTED** — no display table, no display identity (`models.py` inventory; spec §3.4) | MP-35 |
| 3 — configure each display for branch/rooms/doctors/queues | MD-01, MD-03, MD-04, **MD-14** | **NOT IMPLEMENTED** — one implicit branch-wide scope per URL, no configuration surface | MP-35, MP-36, MP-37, **MP-41** |
| 4 — language configurable BN or EN | MD-06 | **PARTIAL** — `?lang=` and `localStorage` only, both device-side (`[branch].js:30,41-53`); no configured language | MP-38 |
| 5 — automatically refresh when queue information changes | MD-10, **MD-15** | **PARTIAL** — 10 s polling with no change signal and no cache validator (`display.py:185-197`; `[branch].js:32`) | **MP-43** |
| 6 — large readable typography | MD-11 | **PARTIAL** — card capped at 1180 px (`global.css:92,126`) | MP-38 |
| 7 — current token plus relevant doctor/room | MD-05, MD-11 | **PARTIAL** — token and doctor name published; room absent | MP-37 |
| 8 — estimated waiting time where sufficient data exists | **MD-13** | **NOT IMPLEMENTED on the board** — the formula exists only for PQV (`tracking.py:184-185`) | **MP-42** |
| 9 — labelled as an estimate, never a guarantee | **MD-13** | **NOT IMPLEMENTED** — no estimate exists to label | **MP-42** |
| 10 — no patient names, mobile numbers or personal information | MD-07 | **IMPLEMENTED** — hand-built allow-list (`display.py:174-183`); 24 board tests in `test_dqds.py`; **not re-executed for this amendment** | maintained by MP-36/42/45 with a key-set assertion |
| 11 — show only what the facility enabled for public display | **MD-17** | **NOT IMPLEMENTED** — a fixed field set is published for every display | **MP-45** |
| 12 — read-only public access | **MD-18** | **BY CONSTRUCTION, NOT ENFORCED** — the router registers `GET` only (`display.py:127`), but no verb-guard test or `Allow` header exists | **MP-46** |
| 13 — tenant and branch scope on every display feed | MD-09, **MD-14** | **IMPLEMENTED for org/branch** — unknown or foreign branch → 404 (`display.py:108-120`), doctor join constrained to the org (`:143-152`); no per-display or per-room scope exists yet | MP-36, **MP-41**, **MP-46** |

**Reading of the table.** Four items are implemented (10, 13 at branch level, plus the doctor-side halves of 1 and 7), six are partial, and PO-13 turns three previously deferred items (8, 9, 11) into required ones. **Nothing in §33 is now deferred.** That is the whole content of PO-02.

### 15.3 Gaps added by the expanded scope — GAP-29 … GAP-34

These are **new rows**, not re-rankings. Severity is relative to the Hackathon Version's now-approved scope (S2 = required capability absent; S3 = enforcement or verification absent), and none of them changes an existing finding's severity.

| ID | Gap | Sev | Evidence | Requirement / task |
|---|---|---|---|---|
| **GAP-29** | **No estimated waiting time on the public board** — the payload carries only name, serving token and waiting count | **S2** | `display.py:176-183` (payload keys); the estimate formula exists only in `tracking.py:184-185` for PQV | MD-13 → **MP-42** |
| **GAP-30** | **No room-scoped display and no room in any display concept** — rooms exist in the facility model but the board cannot target or label one | **S2** | `facility_rooms` (`models.py:134`) and `doctor_branches.room_id` (`:425`) exist; `display.py` never reads either | MD-14 → **MP-41** |
| **GAP-31** | **No change signal and no cache validator** — every 10 s poll returns a fresh 200, so "refresh when information changes" is timing, not change detection | **S3** | `display.py:185-197` (no `ETag`, no version field); `Cache-Control: public, max-age=10` only | MD-15 → **MP-43** |
| **GAP-32** | **The display's operational date is the container's local date** — a UTC container publishes the wrong day between 00:00 and 06:00 Dhaka | **S2** | `display.py:138` `today = date.today()`; `organizations.timezone` (`models.py:38`) is never read | MD-16 → **MP-44** (with GAP-03, GAP-25) |
| **GAP-33** | **The facility cannot control what its screen publishes** — one fixed field set for every display | **S2** | `display.py:174-183` builds every field unconditionally | MD-17 → **MP-45** |
| **GAP-34** | **Read-only access and denial accounting are unproven** — GET-only is incidental, and no display audit event exists | **S3** | `display.py:127` (single `@router.get`); no `queue.display.*` event anywhere; anonymous 404s are unaudited by design | MD-18, MD-19 → **MP-46** |

### 15.4 GAP-28 restated after PO-13

| Field | Before A-2 | After A-2 |
|---|---|---|
| Statement | Multi-display DQDS absent: no display registry, no per-display scope | **Multi-display DQDS absent in every dimension PO-13 requires** — registry, resolution, doctor/department/**room** scope, configured language, **estimated wait**, **refresh on change**, **facility-controlled public fields**, **read-only enforcement**, **denial audit** |
| Class | Scope question pending PO-02/PO-13 | **Delivery gap against an approved requirement.** No scope decision remains |
| Severity | S2 | **S2, unchanged in rank, wider in content** |
| Closure | MP-35…MP-40 | **MP-35…MP-46**, demonstrated by MP-40 against AC-01…AC-21 |

### 15.5 Documents changed in this task

| Path | Change | Bytes (before → after) |
|---|---|---|
| `docs/product/AMSDP_Business_Rules_V1.0.md` | §33 later-phase paragraph **removed**; §33.1 scope-status block added; header carries the amendment line | 42,812 → **47,353** |
| `docs/AMSDP_Business_Rules_V1.1.md` | The identical §33.1 block (verified byte-identical, 3,433 chars), so no stale copy survives | 47,338 → **51,954** |
| `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | **Appendix E** added (MD-13…MD-19, AC-15…AC-22, MP-41…MP-46, D-04 withdrawn, D-08 split); §5 heading and preamble, §6 banner, D-04/D-08 rows, §9.4 gates, §11.3 status updated | 50,246 → **69,052** |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | **Appendix D** added (WP-C.3, MP-41…MP-46, +7.5 eng-days, gates closed, sequencing 10–14, R-13…R-15); §4 gates, §5.2 path, §6 WP-C.2 note, §10 rows, §11 traceability, §12 placement row, Appendix A totals, Appendix C history updated | 49,357 → **62,905** |
| `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | **This amendment** (§15) | 80,953 → **92,572** |
| `.clinerules` | §11 **ratifies `docs/plan/`** and closes the deviation | — |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Annex records the four decisions, the amendments and this report | 178,934 → **183,434** |

Owner-controlled documents were modified **only where a PO decision explicitly instructed it** (BR §33 by PO-02). No other owner document was touched: `MVP_SCOPE_V1.0/V1.1`, `PQV…Decision_V1.0`, the master feature lists, the system architecture, the Blueprint and the demo documents are unchanged.

### 15.6 Unresolved items after this amendment

| Item | Nature | Owner action |
|---|---|---|
| **OP-1** — "queue" targeting has no queue entity | Interpretation recorded (doctor set = queue). Not a reduction, but the owner may disagree | Confirm or issue a new decision; a named-queue entity would need a new table and migration |
| **OP-2** — BR §33.8 says "countdown"; MD-13 delivers a labelled estimate | Interpretation recorded with reasons (spec E.7) | Confirm, or ask for an additive countdown requirement |
| **GAP-20 / MP-25** — display and tracking rate limiting remain in-process | Pre-existing, unchanged by PO-13 | Already on the roadmap; a durable limiter is not authorised |
| **D-5** — index revision numbering and the document recount | Governance bookkeeping | Owner to settle; the annex still does not advance the revision number |
| **SMS half of PO-02** (BR §35/§36 vs MVP §16) | The DQDS half is resolved; messaging is not | Unchanged; still open |
| **Frontend tests for the board** | No component test exists today | Fold into MP-38/MP-40 rather than adding a new task |
| Stray `<!-- ANCHOR -->` markers in four documents not authored here | Cosmetic; flagged in the previous report | Owner may authorise cleanup |

### 15.7 What this amendment does not do

No application code, test, migration, container or deployment was executed or modified. Every task added by PO-13 is **NOT IMPLEMENTED**; the only statuses this amendment changes are documentary: two gates closed, six gaps added, one placement deviation closed, one requirement baseline updated. No capability is claimed as TESTED or VERIFIED anywhere in it.

---


---

## 16. Amendment A-3 — live deployment baseline reconciliation (24 November 2026)

**Why this section exists.** Every "two revisions behind" statement in §1.1, §2.1, §7, §8 and §12 rested on a measurement that was **true on 2026-11-23 and superseded later that same day**. The verified deployment record shows the migration was applied. This amendment corrects the baseline, keeps the historical readings visible as history, and restates **GAP-01** so that only the genuinely open half survives. It changes **no product scope and no Product Owner decision**.

### 16.1 The corrected baseline

| Item | Value | Evidence class |
|---|---|---|
| Repository · branch · HEAD | `shomonrobie/amsdp` · `hackathon-mvp` · `a4ddc2cf58e019b57dccf59f3a859743e3c48430` | **VERIFIED** 2026-11-24, this host (`git rev-parse`) |
| Previous database revision | `a9c4e1f7b2d8` | Historical: 2026-11-23 SQL read, runbook §1.4 |
| Live database revision | `c4d8e2a91f60` — **single head** | **REPORTED** from the verified deployment record of 2026-11-23; **not re-queried here** |
| Migration date and outcome | 23 November 2026 · applied successfully, after a rehearsal against a disposable restored database and a pre-migration backup | **REPORTED** (deployment record) |
| Tables created | `voice_packs` · `queue_announcement_deliveries` · `announcement_platform_config` | **REPORTED** (deployment record); the revision that creates them is **VERIFIED** in the tree |
| Seeded counts preserved in the rehearsal | organizations 421 · patients 2963 · doctors 601 · appointments 642 · queue_entries 11 · audit_events 20490 | **REPORTED** (deployment record) |

### 16.2 Fresh verification actually performed (2026-11-24)

| Check | Result | Class |
|---|---|---|
| Branch · HEAD | `hackathon-mvp` · `a4ddc2cf58e019b57dccf59f3a859743e3c48430` | **VERIFIED** (`git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`) |
| Revision graph from the tree | 16 revisions, **one head** `c4d8e2a91f60`; chain `a9c4e1f7b2d8 → a7c3f19d2b64 → c4d8e2a91f60`, no dangling parent | **VERIFIED** (`python scripts/que-006-w3-voice-config/check_migration_graph.py`) |
| Eight services on `192.168.68.108` | `8110` identity · `8111` organization · `8112` patient · `8113` doctor · `8114` scheduling · `8115` appointment · `8116` queuing · `8117` audit — each HTTP 200 `{"status":"ok","service":…}` | **VERIFIED** |
| Frontend | `:3100` HTTP 200 | **VERIFIED** |
| Deployed organization-service surface | `/openapi.json`: 33 paths, including all eleven `/api/v1/voice-packs…` paths, `/api/v1/platform/announcement-config`, `/api/v1/orgs/{org_id}/announcement-config` (+ `/rollback`) | **VERIFIED** |
| Deployed queue-service surface | `/api/v1/queue/display/{org_code}/{branch_code}` · `/api/v1/queue/{entry_id}/announcement` · `/api/v1/queue/announcements/{delivery_id}/outcome` | **VERIFIED** |
| PostgreSQL port exposure | TCP `192.168.68.108:5433` **open**; TCP `:22` closed | **VERIFIED** (the `0.0.0.0:5433` risk is unchanged and out of scope here) |
| Database revision | **not verified here** — no `alembic`, `psql` or `docker` binary on this host, and no database credential | **NOT VERIFIED** |
| Table existence in the live schema | **not verified here** — same reason. No authenticated call was made either: obtaining a token requires a `POST /api/v1/staff/login`, which writes a login-attempt row, and this task does not authorise writing to production | **NOT VERIFIED** |

**What those probes do and do not prove.** They prove the deployment is up and is running the **post-merge code**: the W2 delivery routes and the W3 voice-pack/config routes exist only in the merged tree whose single head is `c4d8e2a91f60`. They do **not** prove the schema revision — every `/health` returns a static liveness body and queries no table. Only a SQL read of `alembic_version`, or an authenticated call that queries one of the three tables, can close that, and neither is available under this task's restrictions.

### 16.3 Why the wrong baseline survived into three documents

1. **It was true when measured.** On 2026-11-23 the runbook (§1.4) recorded, against the running `amsdp-db-1` container: `select version_num from alembic_version → a9c4e1f7b2d8`, `select to_regclass('voice_packs') → (null)`. The `682 passed / 109 errors` suite output was produced against that database.
2. **The migration landed afterwards and was never written back.** The deployment record exists outside this repository. No in-tree document was updated, so the last in-tree statement kept saying "behind" while the fact had changed.
3. **This audit and the plan inherited it as current.** Both labelled it DOCUMENTED/REPORTED — honest labelling, but the measurement was already superseded when it was quoted, and neither document had a mechanism to notice.
4. **The "host unreachable" claim was a probe error, not a fact.** The earlier session probed `:8000` and `:3000`, which are the *container-internal* ports on the Ubuntu host. From the Windows checkout the same deployment answers on `192.168.68.108:8110–8117` and `:3100`. The correct reading was "wrong host, wrong ports", not "the stack is down". Re-tested on 2026-11-24, every service answered on the first attempt.

The `109 errors` are therefore **historical and fully explained**, not a live defect: fixture setup failing on tables that the migration has since created. What remains genuinely open is that **no suite has been run against the migrated database and recorded** — a different fact from "the database is behind". That difference is the whole point of this amendment.

### 16.4 What this amendment changes, and what it deliberately leaves alone

| Location | Amendment A-3 effect |
|---|---|
| §1.1 "Is anything verifiable today?" | Corrected: the reason for "no" is the audit session's restrictions, not an unreachable stack or a stale schema |
| §1.4 headline recommendation | MP-01 restated: prove the runtime; the migration half is already applied |
| §2.1 pinned-state table | Live-database row replaced; previous revision retained as history in §16.1 |
| §2.3 "not executed" rows | `alembic` and live-call rows corrected; probe-target error named |
| §7 GAP-01 | Restated as closed-for-migration / open-for-evidence; **S1 retained**, register totals unchanged |
| §8 step 1 | `NOT READY` → `PARTIAL`, with the evidence that changed it |
| §12 item 3 | Corrected, with the residual gap stated |

**Unchanged:** product scope, BR clauses, PO decisions, every task ID, every estimate, the register count (27) and its severity totals, the F-key scheme, C-1…C-7, and every status in §5.

### 16.5 What this amendment does not do

- It does **not** claim the live schema was re-queried. The revision is REPORTED from the 2026-11-23 deployment record; §16.2 says exactly which checks were fresh and which were not.
- It does **not** mark any test as passing. No suite was executed in this task; the `682/109` and `790/1` figures remain historical counts.
- It does **not** retire GAP-01, downgrade it, or move the register totals. The migration half is closed; the evidence half is not.
- It does **not** touch application code, the database, any migration, any container or any service, and it does **not** change the `0.0.0.0:5433` finding — that remains a separate open security risk.
- It does **not** change approved product scope or any Product Owner decision.

*End of Amendment A-3.*
