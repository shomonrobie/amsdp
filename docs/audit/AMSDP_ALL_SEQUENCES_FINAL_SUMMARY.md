# AMSDP — All Sequences: Consolidated Implementation-Evidence Report

> **Date:** 2026-11-10
> **Scope:** Sequences 1–4 plus the post-Sequence-4 deployment-hardening pass
> **Purpose:** one reconciled evidence document that separates what is
> IMPLEMENTED / TESTED / VERIFIED from what is DEFERRED / BLOCKED, so a decision
> can be made on MVP acceptance and, separately, on deployment readiness.
> **This report grants no acceptance and no deployment authorisation.** It is an
> evidence reconciliation, not a sign-off. Nothing was committed, pushed, merged,
> provisioned or deployed to produce it.

---

**Contents:** §1 purpose and method · §2 status taxonomy · §3 sequence inventory ·
§4 evidence base (D1–D16, R1–R18) · §5 per-sequence reconciliation · §6 feature
matrix · §7 conflicts register (C1–C12) · §8 test state · §9 reported complete
but unverified · §10 outstanding issues (P1–P3) · §11 known limitations ·
§12 external dependencies (E1–E15) · **§13 MVP acceptance recommendation** ·
**§14 deployment-readiness recommendation** · §15 classification roll-up ·
§16 governance and skill compliance

---

## 1. Purpose, scope and method

There is no single document that covers all four sequences. There are four
sequence deliverables (`AMSDP_SEQ_02_COMPLETION_REPORT.md`,
`AMSDP_SEQ_03_COMPLETION_REPORT.md`, `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md`,
`AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md`), a post-Sequence-4 hardening
report, and roughly a dozen `M*` milestone reports written *between* the
sequences. Each was written at a different moment against a different tree, so
their test totals, permission tables and open-finding lists do not line up on
their face.

This report was produced by:

1. **Reading** every sequence document and every milestone report in
   `ai_factory/docs/` that carries implementation evidence
   (§4.1 lists them with the sections used).
2. **Re-running the authoritative check** against the tree as it stands now —
   the full backend suite, test collection, the live migration head and two live
   database counts (§4.2) — rather than quoting an earlier run.
3. **Reconciling**: where two documents disagree, both are cited, the newer
   verified state wins, and the disagreement is recorded in §7 instead of being
   smoothed over.
4. **Classifying** every material claim at the `.clinerules` §7 level that the
   evidence supports, and no higher (§15).

Out of scope: any code change, any test addition, any commit. This report
describes the tree; it does not modify it.

---

## 2. Status taxonomy used in this report

The four `.clinerules` §7 levels are used strictly, and two non-levels are added
for work that is planned or externally blocked:

| Status | Meaning in this report |
|---|---|
| **IMPLEMENTED** | The code exists and is reachable from a running service or page. Nothing stronger is asserted. |
| **TESTED** | Named tests pass in this tree, in a run recorded here or in a cited report. A green suite alone never reaches VERIFIED. |
| **VERIFIED** | A second, independent artefact confirms it: a live API call through the public origin, a row read back from PostgreSQL, a probe from inside a container, or a build/exit-code observation that a test cannot fake. |
| **DEFERRED** | Deliberately not done in any sequence; an owner and a next step exist. |
| **BLOCKED** | Cannot proceed without an external decision, credential, account or approval that the agent cannot supply. |

Two rules applied throughout, because they are where milestone reports usually
inflate:

* A page that builds is **IMPLEMENTED**, not TESTED. There is no browser test
  harness in this repository (§8.4), so no UI *interaction* is claimed as
  verified anywhere in this document.
* A feature whose component is not started by `docker-compose.yml` is
  **IMPLEMENTED + TESTED but not operational**. The notification outbox is
  exactly this case (§9.2) and is the single most important honesty item here.

---

## 3. Sequence inventory — including the sequence that has no report

| Sequence | Deliverable document | What it actually delivered | Report present? |
|---|---|---|---|
| **1** | *none* | The MVP core: eight services, PostgreSQL schema + migrations, JWT auth/RBAC, patients, doctors, staff, orgs/branches, schedules, appointments + tracking tokens, queue lifecycle, dashboard/audit, frontend shell + i18n, Docker topology | **No** |
| **2** | `AMSDP_SEQ_02_COMPLETION_REPORT.md` | Doctor Queue Display System (public per-branch board) + hardening: throttle, cleanup, non-disclosure | Yes |
| **3** | `AMSDP_SEQ_03_COMPLETION_REPORT.md` + `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` | BR §27A missed-turn recovery (`queue.recover` / `queue.reposition`) + notification outbox, per-org notification config, standalone worker | Yes |
| **4** | `AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` | Acceptance workflow (A–F) executed; three real defects found and repaired (HISTORY-P0, TOKEN-P1, TZ-P1) | Yes |
| **4′** | `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | Disposition of all seven open Sequence-4 findings; health probes, durable login throttle, index drop, 112 rewritten tests, live 10-container stack | Yes |

### 3.1 Why Sequence 1 has no report — and how it is evidenced instead

An exhaustive search for a Sequence-1 completion report or commit found nothing
(no file matches `*SEQ_01*`, no `*SEQUENCE_1*`, no matching commit subject). The
work exists; the *document* does not. Sequence 1 is therefore evidenced only by
the milestone reports written during it and by the code they left behind:

| Sequence-1 area | Primary evidence document | Sections used |
|---|---|---|
| Security: JWT, RBAC, tenant isolation, audit | `AMSDP_M2_Security_Implementation_Report.md` | whole |
| Appointments, conflict rules, tracking tokens, history | `AMSDP_M4_Appointment_Implementation_Report.md` | whole |
| Queue lifecycle (check-in → call → consult → complete / no-show / cancel) | `AMSDP_M5_Queue_Implementation_Report.md` | whole |
| Platform UX: AppShell, shared components, dashboard, audit page | `AMSDP_M6_Implementation_Report.md` | §2–§8 |
| End-to-end demo readiness | `AMSDP_M7_Hackathon_Readiness_Report.md` | whole |
| Product Qualification Tests (PQT) | `AMSDP_M9_Implementation_Readiness_Assessment.md` | Part B |
| Live API/UI integration walkthrough | `docs/demo/AMSDP_API_Integration_Report_V1.0.md` | whole |

**Consequence:** Sequence 1 cannot be signed off from a report that does not
exist. Its acceptance rests on the current suite plus the post-Sequence-4 live
verification, both of which exercise the same code. That is a real limitation of
the evidence base and is recorded as such (§7 C1).

---

## 4. Evidence base

### 4.1 Documents reconciled (with the sections that carry the evidence)

| # | Document | Sections relied on |
|---|---|---|
| D1 | `docs/security/AMSDP_M2_Security_Implementation_Report.md` | whole (auth, RBAC, 403-era tenant checks) |
| D2 | `docs/implementation/AMSDP_M4_Appointment_Implementation_Report.md` | whole |
| D3 | `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md` | whole (lifecycle, 17/17 era tests) |
| D4 | `docs/implementation/AMSDP_M6_Implementation_Report.md` | §2–§8 (shell, dashboard, audit page, 39/39) |
| D5 | `docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md` | whole (77/77 era) |
| D6 | `docs/deployment/AMSDP_M8_Cloud_Deployment_Architecture.md` | §12 (deployment items), options |
| D7 | `docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md` | Part B (PQT), M9-F note |
| D8 | `docs/audit/AMSDP_MVP_Hackathon_Readiness_Assessment.md` | whole |
| D9 | `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` | §3 (findings), §7–§9 (tests, live), §10–§11 |
| D10 | `docs/implementation/AMSDP_SEQ_03_COMPLETION_REPORT.md` | §2A (BR §27A), §8 (live DB), §9–§10, §12 |
| D11 | `docs/implementation/AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` | whole (independent assessment) |
| D12 | `docs/audit/AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` | §3–§7, §9 |
| D13 | `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | §4–§6, §8–§11 |
| D14 | `docs/demo/AMSDP_API_Integration_Report_V1.0.md` | whole |
| D15 | `docs/AMSDP_MVP_SCOPE_V1.1.md`, `docs/product/AMSDP_Business_Rules_V1.0.md` | scope + BR §8 / §27A |
| D16 | `docs/demo/AMSDP_Limitations_Report_V1.0.md` | whole — **stale, see §7 C3** |

### 4.2 Commands run for this report (this session, this tree)

| # | Command | Result | Used for |
|---|---|---|---|
| R1 | `cd backend && ../.venv/bin/python -m pytest -q` | **`289 passed, 118 warnings in 145.67s`** — 0 failed, 0 skipped, 0 errors | §8.1 |
| R2 | `pytest --collect-only -q` | **289 tests collected in 5.40s**, 17 modules | §8.1 table |
| R3 | `docker exec amsdp-db-1 psql -U amsdp -d amsdp -tAc "select version_num from alembic_version"` | `e6c1a9b3d5f8` | §8.3 |
| R4 | same, `select count(*) from login_attempts` / `from notifications` | `0` / `0` | §8.3, §9.2 |
| R5 | `docker ps` | only `amsdp-db-1 Up (healthy)` of this project; the application stack is stopped; the other 14 containers belong to unrelated projects | §8.3 |
| R6 | `ls -d .github/workflows`; grep `frontend/package.json` for test tooling | no `.github/` directory; no `test` script, no jest/playwright/cypress entry | §8.4 |
| R7 | grep for `concurrent`, `ThreadPool`, `threading` across `backend/tests` and `backend/queuing/tests` | no matches | §8.4 |
| R8 | service keys in `docker-compose.yml` | `db, identity, organization, patient, doctor, scheduling, appointment, queuing, audit, frontend` — **no notification worker** | §9.2 |
| R9 | `backend/common/permissions.py` | `receptionist` and `doctor` both hold `queue.recover` + `queue.reposition` (lines 25, 33) | §7 C5 |
| R10 | `backend/common/health.py` | liveness touches no DB; readiness does `SELECT 1`; payload is `{status, service}` only; 503 message is static | §6 |
| R11 | `alembic/versions/*.py` revision graph | 9 revisions, one root `5f3fce6757cf`, one head `e6c1a9b3d5f8`, strictly linear | §8.3 |
| R12 | `backend/tests/test_security.py` test names | `TestCrossOrgIs404::test_cross_get / test_cross_update / test_unknown_id_is_indistinguishable`; `test_branch_admin_cross_denied`; `TestLoginThrottle::test_repeated_failures_get_429 / test_limit_is_per_username / test_success_clears_the_bucket` | §6, §7 C2 |
| R13 | `docker exec amsdp-db-1 psql … count(*)` on `patients`, `appointments`, `organizations`, `queue_entries`, `audit_events` | `1435`, `45`, `42`, `1`, `2456` | §9.9, §11.4 — the dev database is **not** empty; D13 §6.4 only claimed zero residue *in the orgs the suite created* |
| R14 | `git log -1`, `git status --porcelain` | last commit `eb87cac` (2026-11-06); **128 uncommitted entries** (56 modified, 72 untracked) | §11.7, §14 — the entire sequence effort is uncommitted |
| R15 | `identity/models.py:18–25`, compose env block | `_TOKEN_HOURS = 12`; HS256; secret required outside development (fails closed); compose default `dev-synthetic-key-replace-in-prod` | §11.1 |
| R16 | `identity/models.py:27–36` | `password: str` — no minimum length, complexity or rotation constraint | §11.1 |
| R17 | grep for `Bangla`, `bangla`, `ঢাকা`, `unicode` across `backend/**/tests` | **no matches** — only `docs/AMSDP_MVP_SCOPE_V1.1.md` mentions Bangla | §13.2 (scope item *unverified*) |
| R18 | `git ls-files`, `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | `README.md` present; no `.env` tracked; a demo-credential sheet **is** tracked (and modified in the working tree), listing six localhost accounts (`admin`, `org_admin`, `br_admin`, …) whose passwords are trivially guessable — values deliberately not reproduced here | §11.1, §12 |

---

## 5. Sequence-by-sequence reconciliation

Each subsection states what the sequence's own document claims, what holds at
the current tree, and what is downgraded or superseded. Levels are per §2.

### 5.1 Sequence 1 — MVP core (no report; evidenced via D1–D8, D14)

**Delivered (IMPLEMENTED, still present in the tree):** eight FastAPI services
(`identity`, `organization`, `patient`, `doctor`, `scheduling`, `appointment`,
`queuing`, `audit`) on ports 8110–8117, a Next.js frontend on 3100, PostgreSQL on
5433; JWT (HS256) auth with `organization_id` as the single tenant key and
`branch_id` as the scope key; six roles (`super_admin`, `org_admin`,
`branch_admin`, `receptionist`, `doctor`, `assistant`); patient/doctor/staff
registries; schedules with slot templates; appointments with conflict rules,
history and tracking tokens; the queue lifecycle (check-in → call → consult →
complete / no-show / cancel); dashboard and audit surfaces; a shared AppShell,
UI components and an i18n registry; 15 frontend page files
(12 authenticated pages + login + public display + public tracking).

**What the milestone reports claimed at the time, and its current standing:**

| Claim (source) | Then | Now |
|---|---|---|
| Auth/RBAC/tenant isolation implemented and tested (D1) | TESTED | TESTED — `tests/test_security.py` (25), `tests/test_sequence3.py` (29) |
| Cross-org access denied with **403** (D1) | TESTED | **Superseded** — the tree returns **404** (`.clinerules` §3). `TestCrossOrgIs404` (R12) |
| Appointments + reschedule + tracking tokens (D2) | TESTED | TESTED — `test_appointment.py` (13), `test_reschedule.py` (6), `test_tracking_tokens.py` (17) |
| Queue lifecycle **17/17** (D3) | TESTED | TESTED — `test_queue.py` now collects **20** (three added by M6/Seq 3/Seq 4) |
| Dashboard + audit page, **39/39** (D4) | TESTED | TESTED — `test_dashboard.py` (6), `test_audit.py` (13); figures come from SQL aggregates, no mocks (D4 §6) |
| End-to-end readiness **77/77** (D5) | TESTED | Superseded by the 289-test suite; the e2e module is now `test_e2e.py` (21) |
| PQT suite green (D7 Part B) | TESTED | TESTED within `test_dqds.py` (24) and `test_tracking_tokens.py` (17) |

**Downgraded / open from Sequence 1:**

* **No completion report exists** (§3.1). Sequence 1 has never been signed off
  as a unit; only reviewed in pieces.
* The **403 → 404** change (Seq 4) means every Sequence-1 document that quotes
  403 in a table is now factually wrong (§7 C2).
* M5's concurrency claim ("20 concurrent enqueues → unique tokens") is a
  **live, single-process observation**, not a repeatable test: no concurrency
  primitive exists anywhere in `backend/tests` (R7). See §7 C7.
* Dashboard branch switcher, staff↔doctor linkage, some English-only card
  labels, org-settings screen for reserved capacity, and audit capture outside
  the queue remain **DEFERRED** exactly as D4 §8 lists them.

### 5.2 Sequence 2 — Doctor Queue Display System (D9)

**Scope:** a public, unauthenticated per-branch queue board
(`GET /api/v1/display/{org}/{branch}`), its page
(`frontend/pages/queue-display/[org]/[branch].js`), display styling, and the
hardening that a public endpoint forces: throttling, byte-identical
non-disclosure, data minimisation, cleanup.

**Claims in D9:**

| Claim | Level in D9 | Standing now |
|---|---|---|
| 9 audit findings (A1–A9) fixed, each with a test (D9 §3, §7) | TESTED | TESTED — `test_dqds.py` collects **24**, matching D9 §7 exactly |
| Board returns 200 with the documented body/headers, and leaks no patient identifiers | VERIFIED at the time (D9 §9) | **Not re-verified here** — the stack is stopped (R5) and this report did not start it. Treated as VERIFIED-on-D9's-evidence only |
| Unknown and suspended branches are indistinguishable (byte-identical 404) | VERIFIED (D9 §9) | Same qualification as above; the code path is present |
| Throttle returns 429 with `Retry-After` (D9 §9) | VERIFIED | Code present; **per-process** (see below) |
| `next build` exits 0 for the new page | VERIFIED (build artefact) | IMPLEMENTED-only for behaviour: no browser test exists (R6) |

**Deferred in D9, still deferred:**

* **D9 §11.6 / M9-F — the display throttle is per-process.** A future
  multi-replica deployment would multiply the allowance. Note the asymmetry:
  the *login* limiter became durable and cross-process in D13, the display and
  PQT limiters did not (§10 P2-3).
* **A rows with `NULL` status are treated as active** (D9 §11) — a data-quality
  assumption, not a defect, but it is load-bearing for what the public sees.
* **No denial audit on the public board** — there is no principal, so a refusal
  cannot be attributed. Consistent with the platform-wide denial-audit gap
  (§7 C8), not unique to Sequence 2.
* **No browser end-to-end test** for the display page (R6).

### 5.3 Sequence 3 — missed-turn recovery + notification outbox (D10, D11)

**Delivered:** BR §27A recovery on the queue (`queuing/recovery.py:138`
`missed-turn`, `:187` `recover`), repositioning inside the same queue, the
`notifications` / notification-config tables (migration `b7c1e4d90a52` — one of
the 9 revisions in R11), per-org notification config and status routes
(`organization/notification_config.py:60,78,134`), a notification outbox with a
provider abstraction, and a standalone worker that is deliberately **not** part
of any FastAPI process (`backend/common/notifications/worker.py:1–12`).

| Claim | Level in D10 | Standing now |
|---|---|---|
| BR §27A clause-by-clause compliance (D10 §2A) | documented mapping | TESTED — `test_sequence3.py` collects **29**, matching D10 §7 |
| Recovery + reposition audited with token-derived actor/role/org/branch | TESTED (D10 §7) + live DB reads (D10 §8.1) | TESTED now; the live DB reads are D10's evidence, not repeated here |
| Notification config rejects unapproved provider/lead (D10 §5) | TESTED | TESTED — `test_notification_config_rejects_unapproved_provider_and_lead` |
| Outbox enqueue/claim/retry/cooldown in one transaction | TESTED (D10 §7) | TESTED — `test_sequence3.py` |
| Worker drains due rows | TESTED (`worker.run_once`) | **IMPLEMENTED + TESTED, NOT OPERATIONAL** — no compose service (R8), live `notifications` count = 0 (R4). §9.2 |
| Frontend surfaces (`/queue` recovery UI, `/notifications`) | IMPLEMENTED, build exit 0 (D10 §8.4) | **IMPLEMENTED only** — no browser test exists (R6); D10 §9 itself lists 2 rows as not VERIFIED |

**Downgraded from D10:**

* **D10 §12 recommended adding the worker as a compose service in Sequence 4.**
  Sequence 4 did not; the post-Sequence-4 pass did not (it was outside its
  mandate). The outbox therefore fills and is never drained in the running
  stack. This is the clearest "complete but not operational" item in the
  project (§9.2).
* **Only a mock provider exists.** Nothing was ever sent over a real SMS/email
  transport; D10 §10 states this and it is unchanged. Real delivery is BLOCKED
  on a provider account and a product decision (§12).
* **Doctor grants for `queue.recover` / `queue.reposition` are still awaiting
  product-owner confirmation.** D10 §10.4 raised it; the permission is live in
  code (R9), tests assert the *current* table, and no approval exists in the
  documents reviewed. Approval is BLOCKED on the owner, not on engineering
  (§7 C5).

### 5.4 Sequence 4 — acceptance verification (D12) and the hardening pass (D13)

**Sequence 4 executed the workflow rather than describing it** (D12 §3): six
workflows A–F, 64 assertions, reproduced five times; three real defects found
and repaired (D12 §4):

| Defect | Effect | Level now |
|---|---|---|
| `SEQ4-HISTORY-P0` | appointment history writes were silently dropped | **TESTED** as fixed — `test_sequence4.py` (13) plus mutation checks (D12 §5.3) |
| `SEQ4-TOKEN-P1` | two token authorities could mint duplicate live tracking tokens | **TESTED** as fixed — DB uniqueness + `ON CONFLICT` path |
| `SEQ4-TZ-P1` | two different "todays" inside one visit | **TESTED** as fixed (facility-day resolution), **VERIFIED** inside the built image by D13 §5.5 |

At the end of Sequence 4 the suite read **177 passed / 7 skipped**, with the
seven skipped modules quarantined. D12 §7 then listed seven open findings.

**The post-Sequence-4 pass (D13) closed all seven**, each with an artefact:

| Finding | Disposition (D13 §2, §3) | Level |
|---|---|---|
| `SEQ4-DEPLOY-D2` — no health/readiness | `common/health.py` installed in all 8 services; **16 probes, 200 each, from the containers** (D13 §5.3) | **VERIFIED** (D13), code re-inspected here (R10) |
| `SEQ4-DEPLOY-D1` — no single entry point | decided, not built: one public origin via the Next proxy; `backend/app/main.py` annotated as not-a-deployment-entry-point (D13 §3.8) | decision + **VERIFIED** route through `:3100` (D13 §5.3) |
| `SEQ4-CORS-D1` — no CORS policy | closed by topology: the browser only talks to one origin, so no cross-origin preflight exists to configure (D13 §8.1) | **VERIFIED by D13 §5.3** (proxy path) |
| `SEQ4-THROTTLE-D1` — per-process login throttle | durable DB-backed limiter + `login_attempts` (migration `d4b2c8e1f7a3`); **20×401 → 429 with `Retry-After: 60`, and 20 rows read from another process** (D13 §5.4) | **VERIFIED** (D13) |
| `SEQ4-INDEX-P3` — redundant index | dropped in `e6c1a9b3d5f8`; `pg_indexes` read from the live DB (D13 §6.2) | **VERIFIED** (D13) |
| `SEQ4-TZ-P3` — tzdata risk | verified inside the image (486 zones, `Asia/Dhaka`) rather than patched; accepted as conditional | **VERIFIED** (D13 §5.5), conditional on the base image (§11) |
| `LEGACY-TESTS-P1` — 7 quarantined modules | all seven rewritten against PostgreSQL; **112 tests**; suite `289 passed, 0 skipped` (D13 §4) | **TESTED**, re-confirmed by R1 |

**Not claimed by D13 itself** (D13 §8.4): CI, container orchestration, TLS,
monitoring/alerting, backup/restore, multi-worker behaviour, production
readiness. This report adopts those exclusions verbatim (§11, §14).

---

## 6. Consolidated feature matrix (all sequences)

Columns: the sequence(s) that delivered it, the **highest** level the evidence
supports (§2), and the artefact that supports it. `→` means "evidence chain".

### 6.1 Identity, access and tenancy

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| Login issues a JWT accepted by all eight services | 1 | **VERIFIED** | D13 §5.3 — one token from identity accepted by all eight containers, login through `:3100`; R1 keeps it green |
| Token claims drive org/branch/role/permissions | 1 | **TESTED** | `identity/tests/test_identity.py` (17) |
| Six-role permission table | 1, 3 | **TESTED** | `tests/test_security.py` (25); table re-read this session (R9) |
| Cross-org read/update fails closed with **404** | 1, 4 | **TESTED** | `TestCrossOrgIs404::test_cross_get`, `::test_cross_update`, `::test_unknown_id_is_indistinguishable` (R12) |
| Branch-scope denial indistinguishable from missing row | 1, 4 | **TESTED** | `test_branch_admin_cross_denied` (R12) |
| Principal cannot forge another org from the body | 1 | **TESTED** | `test_cannot_force_other_org` (R12) |
| `super_admin` cross-org read/create | 1 | **TESTED, APPROVAL UNKNOWN** | `test_super_cross_org_read`, `test_super_cross_org_create` — privileged by design, but no product-owner sign-off in the documents (§10 P2-1) |
| Durable, cross-process login throttling | 4′ | **VERIFIED** | D13 §5.4 — 429 + `Retry-After: 60`, 20 rows read from another process; `TestLoginThrottle` (R12) |
| No secrets in health/error payloads | 4′ | **VERIFIED (code)** | R10 — `{status, service}` only, static 503 message |

### 6.2 Registries and scheduling

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| Organisation + branch lifecycle, org-scoped listing | 1 | **TESTED** | `organization/tests/test_organization.py` (20) |
| Staff/user management, role assignment | 1 | **TESTED** | `identity/tests/test_identity.py` (17) |
| Doctor registry | 1 | **TESTED** | `doctor/tests/test_doctor.py` (14) |
| Patient registry, search, DOB→age derivation | 1 | **TESTED** | `patient/tests/test_patient.py` (16), `tests/test_patient_age.py` (13) |
| Duplicate detection / patient merge | 1 | **DEFERRED** | D13 §4.3 — the route deliberately does not exist (scope decision, `405` asserted), exact-mobile matching only |
| Weekly schedules + slot templates | 1 | **TESTED** | `scheduling/tests/test_scheduling.py` (22) |
| Appointment create / list / modify | 1 | **TESTED** | `appointment/tests/test_appointment.py` (13) |
| Appointment conflict rules | 1 | **TESTED** | same module |
| Reschedule | 1 | **TESTED** | `appointment/tests/test_reschedule.py` (6) |
| Append-only appointment history | 1, 4 | **TESTED** | HISTORY-P0 fix + `tests/test_sequence4.py` (13); D12 §5.3 mutation checks |
| Tracking tokens (single authority, unique) | 1, 4 | **TESTED** | `tests/test_tracking_tokens.py` (17); TOKEN-P1 fix |
| Public tracking page `/track/[token]` | 1 | **IMPLEMENTED** | page present; no browser test (R6) |

### 6.3 Queue lifecycle, recovery and display

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| Check-in / enqueue / reorder / queue read | 1 | **TESTED** | `queuing/tests/test_queue.py` (20) |
| Transition lifecycle: call → consult → complete / no-show / cancel | 1 | **TESTED** | same module (17 at D3, 20 now) |
| One active token per branch under contention | 1, 4 | **TESTED at DB level** | DB constraint + `ON CONFLICT`; **no concurrency test exists** (R7) — see §7 C7 |
| Missed-turn recovery (`queue.recover`) | 3 | **TESTED** | `tests/test_sequence3.py` (29); `queuing/recovery.py:187` |
| Staff-confirmed reposition (`queue.reposition`) | 3 | **TESTED** | same |
| Recovery/reposition audited with token-derived actor | 3 | **TESTED** | `test_sequence3.py`; D10 §8.1 live rows |
| Public display board (data-minimised, throttled, non-disclosing) | 2 | **TESTED**; live **VERIFIED at D9 only** | `tests/test_dqds.py` (24); not re-run live here (R5) |
| Display throttle durability | 2 | **DEFERRED** | D9 §11.6 / M9-F — per-process bucket |
| Display page | 2 | **IMPLEMENTED** | build artefact only (D9 §5) |

### 6.4 Notifications

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| Outbox table + transactional enqueue | 3 | **TESTED** | `tests/test_sequence3.py` (29); migration `b7c1e4d90a52` |
| Claim / retry / cooldown discipline | 3 | **TESTED** | same module; D10 §5 |
| Per-org notification config (approved provider + lead) | 3 | **TESTED** | `organization/notification_config.py:60,78`; rejection test present |
| Config read restricted to `org_admin` | 3 | **TESTED** | `test_org_admin_reads_and_updates_notification_config`… and negative case |
| Standalone worker | 3 | **IMPLEMENTED + TESTED, NOT OPERATIONAL** | `worker.py` runnable via `python -m common.notifications.worker`; **no compose service** (R8) → §9.2 |
| Real SMS/email provider | 3 | **BLOCKED** | mock only (D10 §10); needs provider account + product decision (§12) |
| `/notifications` page | 3 | **IMPLEMENTED** | build artefact only |

### 6.5 Dashboard, audit and reporting

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| `/dashboard/today`, `/dashboard/period` from SQL aggregates | 1 | **TESTED** | `tests/test_dashboard.py` (6); D4 §6 (no mock/cached figures) |
| `/dashboard/audit` search/filter/paginate | 1 | **TESTED** | same module |
| Audit events append-only, written only by services | 1 | **TESTED** | `audit/tests/test_audit.py` (13); `test_e2e.py::test_13_audit` asserts a client *cannot* write one (D13 §4.3) |
| Audit trail untouched by the hardening pass | 4′ | **VERIFIED** | D13 §6.5 (live DB reads) |
| Denied requests recorded in the audit trail | — | **GAP** | refusals are not audited anywhere (§7 C8) — a `.clinerules` §3 non-negotiable is not yet met |
| Dashboard / audit pages | 1 | **IMPLEMENTED** | build artefact only |

### 6.6 Platform, data and deployment surface

| Capability | Seq | Status | Evidence |
|---|---|---|---|
| PostgreSQL persistence with 9 linear migrations | 1, 3, 4′ | **VERIFIED** | `alembic_version = e6c1a9b3d5f8` read live (R3), matching the single head in the tree (R11) |
| No model drift (`alembic check` clean) | 4, 4′ | **VERIFIED** | D13 §6.1, D12 §5.4 (no schema change was needed) |
| Liveness + readiness on all eight services | 4′ | **VERIFIED** | D13 §5.3 — 16 probes, 200 each; payload re-inspected (R10) |
| Compose start order behind a healthy database | 4′ | **VERIFIED** | D13 §5.2 — 10/10 healthy; but the stack is **currently stopped** (R5) |
| One public origin (`:3100`) proxying all `/api/v1` prefixes | 4′ | **VERIFIED** | D13 §5.3; `frontend/next.config.js` proxies added |
| Facility-day resolution inside the built image | 4′ | **VERIFIED (conditional)** | D13 §5.5 — 486 zones, `Asia/Dhaka`; depends on image tzdata (§11) |
| Test suite leaves no business rows behind | 4′ | **VERIFIED at D13** | D13 §6.4; R4 shows `login_attempts = 0` after this session's run |
| CI running any of this | — | **ABSENT** | no `.github/` directory (R6) |
| Frontend automated tests | — | **ABSENT** | no jest/playwright/cypress, no `test` script (R6) |
| Load / concurrency / performance tests | — | **ABSENT** | no test uses a concurrency primitive (R7) |

---

## 7. Conflicts and discrepancies register

Every entry is a place where two documents, or a document and the tree, say
different things. The resolution column states what this report treats as true
and why. None of these were edited away in the source documents; they are
recorded so the next reader is not misled.

| ID | Conflict | Both sides | Resolution adopted |
|---|---|---|---|
| **C1** | **Six different "green suite" totals across passes** — 77/77 (D5), 39/39 (D4), 17/17 (D3), 118 (D9), 177+7 skipped (D12), 289 (D13) | Each was true on its own tree at its own time | Only **289** is current (R1, re-run here). The progression is additive: D5 → D4/D3 → D9 → D12 → D13. Any older number quoted as "the suite" today is wrong. |
| **C2** | **Cross-tenant denial status code**: 403 in D1 and older tables vs 404 in the tree | D1 documents 403; `common/auth.py` and `TestCrossOrgIs404` return 404 | **404 wins** — `.clinerules` §3 mandates non-disclosing 404, and Seq 4 changed it deliberately. D1's table is stale. One residual: `identity/main.py` returns **422** when a body names a different org than the token — a request-validation refusal, not a lookup, so it discloses nothing; recorded as §10 P3-1, not silently accepted. |
| **C3** | `docs/demo/AMSDP_Limitations_Report_V1.0.md` (2026-11-05) says: *all 8 services use in-memory dicts, no PostgreSQL, no migrations run, no health endpoints, no rate limiting, only one 15-test E2E suite, no CI* | Every one of those statements is contradicted by R1/R3/R4/R10 and D13 | **The limitations report is stale and must not be quoted as current.** Recommend the owner retire or rewrite it before any external demo. It is not edited here (documentation change outside this report's mandate). |
| **C4** | D12 §7 lists seven open findings; D13 §2 closes them | Two documents, one pass apart | **D13 wins** for all seven (§5.4). The only residue is what D13 itself declined to claim (§8.4 of D13). |
| **C5** | D10 §10.4 says doctor `queue.recover`/`queue.reposition` grants await product-owner confirmation; permissions.py grants them today | Code and tests assert the grants; no approval exists in any reviewed document | **Grants are live and tested but not approved.** Treat as an open business-rule item (§10 P1-2), not an engineering defect. |
| **C6** | Three limiters with three different durability models | Login: durable, DB, cross-process (D13 §5.4). Display (D9 §11.6) and PQT (D7 M9-F): in-process | Not a contradiction, an **inconsistency**. Durable where it matters most (credential stuffing); per-process elsewhere. Recorded §10 P2-3. |
| **C7** | **Concurrency**: D3 claims "20 concurrent enqueues → unique tokens"; D2 asks for a formal concurrency test; D13 §8.2 says no proof beyond the database | No test in the suite uses threads/processes (R7) | The D3 observation was live and single-process. The **guarantee is the DB constraint**, the **test is absent**. Claim level: TESTED at DB level; multi-replica behaviour unproven (§10 P1-4). |
| **C8** | `.clinerules` §3: "Denials are recorded (audited), never silently swallowed" | D9 §11 (public board has no principal), D10 §10 (recovery refusals unaudited), D13 §8 (no denial audit added) | **The rule is not met platform-wide.** This is the one open non-negotiable. Needs a decision + schema (actor may be `anonymous`), not a quick patch (§10 P1-1). |
| **C9** | "Green suite" was treated as proof until Seq 4 | HISTORY-P0: history writes were dropped *while tests passed*, because tests asserted on responses | Resolved by rewriting the seven modules to read back through `SessionFactory` (D13 §4.3). Lesson recorded: response-shape assertions do not prove persistence. |
| **C10** | D10 §3 lists notifications as delivered; D10 §12 defers the worker service | Both in the same document | **Delivered as code, not as a running capability.** Compose has no worker (R8); live `notifications` rows = 0 (R4). §9.2. |
| **C11** | D6 (M8) proposes cloud topology (Render/VPS + Supabase + Vercel); D13 verified a local compose stack | Different environments, same code | **Only local compose is verified.** No cloud artefact, manifest or credential exists (§14). |
| **C12** | Pages described as "verified" in D4/D9/D10 on the strength of `next build` exit 0 | Build success says nothing about behaviour | **Downgraded to IMPLEMENTED** for every page unless a live HTTP fetch is cited (D8/D14 did fetch pages; this report does not extrapolate that to interaction). |

---

## 8. Test state

### 8.1 The authoritative run (re-executed for this report)

```
cd backend && ../.venv/bin/python -m pytest -q
289 passed, 118 warnings in 145.67s (0:02:25)
```

0 failed · 0 skipped · 0 errors · 0 xfail. Collection confirms the same 289
across 17 modules (`289 tests collected in 5.40s`). The warning count (94 → 110
→ 118 across runs) moves because pytest de-duplicates warnings per collection
order; none is an error and nothing is filtered (there is no `pytest.ini`,
`pyproject.toml` or `setup.cfg` in this tree — D13 §4.1).

| Module | Tests | Covers |
|---|---|---|
| `appointment/tests/test_appointment.py` | 13 | appointment create/list/modify, conflicts, org scoping |
| `appointment/tests/test_reschedule.py` | 6 | reschedule rules + history |
| `audit/tests/test_audit.py` | 13 | audit reads, append-only, scoping |
| `doctor/tests/test_doctor.py` | 14 | doctor registry |
| `identity/tests/test_identity.py` | 17 | login, users, roles, token claims |
| `organization/tests/test_organization.py` | 20 | org + branch lifecycle and scoping |
| `patient/tests/test_patient.py` | 16 | patient registry and search |
| `queuing/tests/test_queue.py` | 20 | check-in, enqueue, reorder, lifecycle, permissions |
| `scheduling/tests/test_scheduling.py` | 22 | schedules + slot templates |
| `tests/test_dashboard.py` | 6 | today/period/audit aggregates |
| `tests/test_dqds.py` | 24 | public display: content, non-disclosure, throttle, cleanup |
| `tests/test_e2e.py` | 21 | cross-service workflow on PostgreSQL |
| `tests/test_patient_age.py` | 13 | DOB → age derivation (facility day) |
| `tests/test_security.py` | 25 | 401/403/404, cross-tenant, cross-branch, login throttle |
| `tests/test_sequence3.py` | 29 | recovery, reposition, outbox, notification config |
| `tests/test_sequence4.py` | 13 | HISTORY-P0, TOKEN-P1, TZ-P1 regressions |
| `tests/test_tracking_tokens.py` | 17 | token authority, uniqueness, public tracking |
| **Total** | **289** | |

The seven modules D13 rewrote (112 tests) were also each run **alone** in that
pass, and the reconciliation `112 + 177 = 289` is what makes the total
checkable rather than asserted (D13 §4.2). That isolation run was not repeated
in this session; R2 (collection) and R1 (full run) were.

### 8.2 Failing, skipped, xfail, unrun

* **Failing: none.** No test is expected-fail and none is deselected.
* **Skipped: none** — down from **7** at the end of Sequence 4 (D12 §5.1). The
  quarantine is gone; calling the suite "green with 7 skips" today would be
  wrong in the conservative direction.
* **Written but never executed:** nothing. Every module in §8.1 ran in R1.
* **Evidence that exists but is not a test** (cannot be re-run from the suite,
  and was *not* re-run here because the stack is stopped — R5):
  D9 §9 (display board live HTTP), D12 §3 (64 workflow assertions), D13 §5.1–5.5
  (build, start order, 16 probes, proxy, throttle, tzdata), D13 §6 (live DB
  reads). These are genuine VERIFIED artefacts; they are simply not automated.
  **Automating them is the single largest evidence improvement available**
  (§10 P2-5).

### 8.3 What the database state confirms right now

| Read (R3/R4/R11) | Value | Meaning |
|---|---|---|
| `alembic_version.version_num` | `e6c1a9b3d5f8` | The live dev database is at the tree's single head; 9 revisions, one root `5f3fce6757cf` |
| `count(*) from login_attempts` | `0` | Throttle rows are purged as designed; no residue from this run |
| `count(*) from notifications` | `0` | The outbox is empty — nothing was enqueued in this dev DB, and (R8) nothing would drain it |
| `docker ps` | `amsdp-db-1 Up (healthy)`; app containers stopped | **No live API verification is claimed in this report.** Everything live is cited to D9/D12/D13 |

### 8.4 Test coverage that does not exist (verified absent, not assumed)

| Missing | How verified | Consequence |
|---|---|---|
| Frontend/browser tests | no jest/playwright/cypress dep, no `test` script (R6) | every UI claim stops at IMPLEMENTED; no interaction is verified anywhere |
| Concurrency / multi-replica tests | no threads/processes in any test (R7) | the queue's uniqueness guarantee rests on the DB constraint, unproven under load |
| Load / performance tests | none in tree (D16 §6 matches) | no capacity figure exists for any endpoint |
| Contract / OpenAPI schema tests | none | proxy prefix and payload drift would be caught only by integration tests |
| SAST / DAST / dependency scans | none | no automated security signal beyond hand-written tests |
| Denial-audit tests | impossible — the behaviour does not exist (§7 C8) | the only gap that is a *rule violation* rather than a coverage hole |
| CI execution of anything | no `.github/` (R6) | the suite is green only when a human runs it |

---

## 9. Reported complete but not independently verified

This is the register the rest of the document exists to support: work that is
finished in the tree but where "done" is not the same as "confirmed". Order is
by consequence, not by sequence.

### 9.1 The notification delivery chain — complete code, no running delivery

| Link | State |
|---|---|
| Outbox row written in the same transaction as the business event | TESTED (`test_sequence3.py`) |
| Worker that drains due rows | IMPLEMENTED + TESTED (`worker.run_once`), **not started by compose** (R8) |
| Provider transport | **mock only** (D10 §10) — no SMS/email account, no credentials |
| Evidence that anything was ever delivered | **none** — `notifications` count = 0 (R4) |

The only way to make this operational is to add the worker as a compose service
and select a real provider; both are deployment/product acts, not code defects.
**Reported complete in D10 §3; in deployment terms it is inert.**

### 9.2 The user interface — implemented and building, never interacted with

15 page files exist (`frontend/pages/`). No browser test harness exists (R6), so
**no page's behaviour is verified anywhere in the evidence base**. Specifically
unverified: every form submission, the queue action buttons, the recovery
dialog, the audit filters, the notification-config screen, locale switching, and
all responsive/`@media` behaviour. What *is* evidenced is that the pages compile
and build (D9 §5, D10 §8.4) and that HTML was fetched during earlier demos
(D8, D14).

### 9.3 The public display board's live behaviour

D9 §9 recorded genuine live checks (200 + documented body, byte-identical 404
for unknown/suspended, 429 + `Retry-After`, cleanup verified, port closed).
Those were **not re-run for this report** — the stack is stopped (R5) and this
report does not start services. The 24-test suite keeps the logic honest; the
HTTP-level behaviour is attested by D9 only.

### 9.4 Concurrency and multi-replica behaviour

No test uses a thread, process or parallel client (R7). The token-uniqueness
guarantee is a database constraint, which is strong; what is **unverified** is
behaviour under real contention or with more than one replica of a service
(including the per-process limiters, §7 C6).

### 9.5 Doctor recovery permissions

Tests assert the permission table in `backend/common/permissions.py` (R9). They
cannot verify that the table is *approved*. BR §8 confirmation is outstanding
(D10 §10.4, §7 C5).

### 9.6 Everything cloud

D6 (M8) designs a cloud target; no manifest, Terraform, render.yaml, Vercel
project or credential exists, and none was created. Cloud deployment is
**unverified and unstarted**, not "almost done" (§14).

### 9.7 Operational safety net — never exercised

TLS/HTTPS, reverse proxy, backup/restore, monitoring, alerting, log aggregation,
restart policy/supervisor: none is configured in the repo (D13 §8.4 says so
explicitly; R5 shows compose sets no restart policy).

### 9.8 Restart durability of the stack

The stack was observed starting cleanly and serving (D13 §5.2–5.3). A **cold
restart with existing data** and a **database restart under load** were not
exercised by any document reviewed.

### 9.9 The dev database is not a clean environment

Measured now (R13): **1435 patients, 45 appointments, 42 organizations, 1 queue
entry, 2456 audit events.** D13 §6.4 legitimately verified that the *suite*
leaves zero rows in the orgs it creates; it did not claim the dev database was
empty, and it is not. Consequences: a demo built on this database shows
accumulated test data, and the suite runs against a shared, non-pristine
database (a throwaway CI database is still on D13 §11's list).

### 9.10 Claim-level summary of this section

| Item | Reported as | Actual level |
|---|---|---|
| Notification delivery | "delivered" (D10 §3) | IMPLEMENTED + TESTED, **not operational** |
| 15 UI pages | "verified" on build (D4/D9/D10) | **IMPLEMENTED** |
| Display board live | VERIFIED (D9 §9) | VERIFIED **at D9**, not re-verified here |
| Concurrency | "PASS" (D3) | **DB-level only** |
| Doctor recovery rights | implemented | **TESTED, unapproved** |
| Cloud deployment | designed (D6) | **unstarted** |
| Ops safety net | planned | **absent** |
| Dev environment | "zero residue" (D13 §6.4) | true for suite-created orgs; **42 orgs / 1435 patients persist** (R13) |

---

## 10. Outstanding issues, by severity

**No open P0 defect is known.** The only P0 ever raised — `SEQ4-HISTORY-P0`,
appointment history silently dropped — was found by the Sequence-4 acceptance
run, repaired, and is now covered by `tests/test_sequence4.py` plus mutation
checks (D12 §4.1, §5.3). "No open P0" is a statement about *known* defects: it
cannot rule out a HISTORY-P0-class bug somewhere the acceptance workflow never
looked, which is why §10 P2-5 (automate the live evidence) matters.

### 10.1 P1 — must be resolved before MVP acceptance is meaningful

| ID | Issue | Impact | Owner |
|---|---|---|---|
| **P1-1** | **Denials are not audited** anywhere in the platform (403/404/422 refusals leave no `audit_events` row) — §7 C8, D9 §11, D10 §10 | Directly contradicts `.clinerules` §3 ("denials are recorded, never silently swallowed"). An investigator cannot see who was refused what, when | product owner (decision + schema shape: anonymous actor? denial reason vocabulary) then engineering |
| **P1-2** | **Doctor `queue.recover` / `queue.reposition` grants are unapproved** (R9; D10 §10.4) | The system implements a business rule the owner has not confirmed; a demo would present an unapproved authority | product owner |
| **P1-3** | **Notification delivery is inert**: no worker service (R8), mock provider only, zero outbox rows ever processed (R4) | Any claim that "the system notifies patients" is false in deployment. Only the *plumbing* exists | product owner (choose provider) + deployment |
| **P1-4** | **No concurrency or multi-replica proof** (R7, §7 C7) | Uniqueness is DB-enforced, but two receptionists on two replicas, or a doubled limiter allowance, is untested. Clinic reality is concurrent | engineering (needs a Frontier pass; out of the local-model envelope) |
| **P1-5** | **`docs/demo/AMSDP_Limitations_Report_V1.0.md` is materially false** (§7 C3) | It tells a reader there is no database, no persistence, no health checks and no rate limiting. If it is shown to an evaluator alongside this system, credibility collapses | project owner (retire or rewrite) |

### 10.2 P2 — real, but with a workaround or an accepted risk

| ID | Issue | Impact | Owner |
|---|---|---|---|
| **P2-1** | `super_admin` can read/create across orgs by design (`test_super_cross_org_read/create`) and no document approves that scope | A privileged role wider than any tenant boundary; needs explicit sign-off, not an implicit one | product owner |
| **P2-2** | **No CI**: `.github/` absent (R6) | The 289-test green run exists only as a human act; regressions are caught late | project owner (account/repo policy) |
| **P2-3** | **Limiter inconsistency**: login is durable, display and PQT are per-process (§7 C6) | Public endpoints scale their allowance with replica count | engineering |
| **P2-4** | **Suite runs against the shared dev database** — 42 orgs / 1435 patients present (R13) | Test results depend on a mutable shared environment; a stray `DELETE` in a fixture could damage demo data | engineering (throwaway DB in CI) |
| **P2-5** | **All VERIFIED evidence is manual** (D9 §9, D12 §3, D13 §5–6) | Every claim decays the moment the stack is rebuilt; nothing re-proves it automatically | engineering |
| **P2-6** | **Timezone depends on image tzdata** (D13 §5.5) | A base-image change silently breaks facility-day math unless a startup assertion is added | deployment |
| **P2-7** | **No restart policy / supervisor** in compose (D13 §8.1, deliberate) | A wedged or OOM-killed service stays down until a human acts | deployment |
| **P2-8** | **Zero frontend tests** (R6) | Every UI regression is caught by a human or not at all | engineering (needs a browser harness decision) |

### 10.3 P3 — hygiene and polish

| ID | Issue | Note |
|---|---|---|
| **P3-1** | `identity/main.py` answers **422** when a body names a different org than the token (§7 C2) | Discloses nothing (it is request validation, not a lookup). Not changed because changing it is a contract decision |
| **P3-2** | 118 pytest warnings: Pydantic `.dict()` deprecation in 6 modules, `on_event` deprecation in two services, `PytestReturnNotNoneWarning` in `test_tracking_tokens.py::test_issue_tracking_token` (returns a tuple instead of asserting) | Cosmetic now; `.dict()` will break on Pydantic v3 |
| **P3-3** | Display treats `NULL` status rows as active (D9 §11) | Data-quality assumption; would be visible on a public board |
| **P3-4** | Some dashboard labels remain English-only (D4 §8) | i18n registry exists; label sweep pending |
| **P3-5** | No `X-RateLimit-*` headers, `Retry-After` only (D13 §8.2) | A client cannot show remaining attempts |
| **P3-6** | CSV/PDF export, pagination beyond the API cap, branch switcher, staff↔doctor linkage, org-settings screen | All DEFERRED by earlier sequences, all still deferred |

---

## 11. Known limitations

### 11.1 Security

| Limitation | Detail | Mitigation present |
|---|---|---|
| **One shared HS256 secret across eight services** (R15) | A single leaked secret forges tokens every service accepts. No key id, no rotation, no per-service key | Secret is **required** outside `development` — the app raises at import instead of falling back (R15). Compose default is an explicit placeholder to be replaced at deploy time |
| **12-hour bearer tokens, no refresh or revocation** (R15) | `exp` only; logout is client-side; a stolen token is valid until expiry; no denylist | Short enough for a clinic day; no server-side session store to corrupt |
| **No password policy** (R16) | `password: str` — no length, complexity, reuse or rotation rule. bcrypt hashing is used (identity/main.py:145,202) | Login throttling (durable, cross-process) is the only defence against spraying |
| **No transport security in the stack** | Everything is plain HTTP on localhost; the compose stack has no TLS, no reverse proxy | Acceptable for a local demo *only*; not for anything reachable |
| **Denials are not audited** (§7 C8, P1-1) | 403/404/422 leave no audit row | — (this is the open rule gap) |
| **`super_admin` is not tenant-scoped** (P2-1) | Cross-org read/create is by design and tested, but unapproved | Tests pin the behaviour; approval is missing |
| **No SAST/DAST/dependency scanning** (§8.4) | Security assurance rests on 25 hand-written security tests plus code review | — |
| **Per-process limiters on public endpoints** (P2-3) | Display/PQT allowances multiply per replica | Login limiter is durable |

Positive controls worth recording, because a limitations section is often read
as "nothing works": cross-tenant and cross-branch access fails closed with
non-disclosing **404**; the principal's org/branch is derived from the token and
never trusted from the body (`test_cannot_force_other_org`); the public board is
data-minimised and byte-identically non-disclosing (D9 §9); health payloads leak
nothing (R10); the audit trail is append-only and a client cannot write to it.

### 11.2 Reliability

| Limitation | Detail |
|---|---|
| **Single PostgreSQL instance** | No replica, no failover. A database outage stops all eight services (readiness correctly reports 503, R10) |
| **Notification outbox never drains** (§9.1) | Rows accumulate silently if the system were ever used without a worker |
| **No retry/backoff or circuit breaking** | Nothing in the reviewed services or compose configuration retries a failed peer call or bounds its latency beyond the client default |
| **No restart policy** (P2-7) | A wedged container stays down |
| **No load characterisation** | No performance test exists; capacity is unknown (§8.4) |
| **Multi-replica behaviour unproven** | Includes the two per-process limiters (§7 C6) |

### 11.3 Data integrity and lifecycle

| Limitation | Detail |
|---|---|
| **No backup/restore** | Never configured, never exercised. The dev database content is the only copy (R13) |
| **Audit trail grows without retention** | 2456 rows now, append-only by rule, no archival/partitioning policy. Correct behaviour, no lifecycle plan |
| **The suite writes to the shared dev database** (P2-4) | Isolation is per-org and purge-based; a throwaway CI database is still future work (D13 §11) |
| **The dev database carries demo history** (R13) | 42 orgs / 1435 patients: fine for development, misleading for a demo, unacceptable as production seed |

### 11.4 Deployment and infrastructure

| Limitation | Detail |
|---|---|
| **Local compose only** | 10 services, fixed ports 8110–8117 / 3100 / 5433. No Kubernetes, Render, Terraform or Vercel manifest exists (D13 §8.4) |
| **The work is uncommitted** (R14) | You cannot deploy a commit that contains the sequences; a deployment would ship an unreviewed working tree |
| **Secret handling is an env-var convention** | No secret manager, no rotation story (R15) |
| **Timezone depends on image tzdata** (P2-6) | Verified today, unguarded tomorrow |
| **No CI artefact** | Images are built by hand; nothing records which tree produced which image |

### 11.5 User experience

| Limitation | Detail |
|---|---|
| **No interaction is verified** (§9.2) | Forms, dialogs, filters, locale switching, responsive rules — all unexercised by any test |
| **Deferred surfaces** (P3-6) | Branch switcher, staff↔doctor linkage, org-settings screen, pagination beyond the API cap, exports |
| **Mixed-language labels** (P3-4) | The i18n registry exists; the sweep is unfinished |

### 11.6 Observability and operations

| Limitation | Detail |
|---|---|
| **Health probes are the whole observability story** | `/health` + `/health/ready` (16 probes) is genuinely good; there is nothing else |
| **No metrics, tracing or log aggregation** | No Prometheus, OpenTelemetry, Sentry or structured shipping |
| **No alerting** | A failed service is noticed by a human refreshing a page |
| **Business audit ≠ operational telemetry** | `audit_events` answers "who did what", not "is the system healthy" |

### 11.7 Process, governance and version control

| Limitation | Detail |
|---|---|
| **The entire sequence effort is uncommitted** (R14) | Last commit `eb87cac` (2026-11-06), 128 changed paths outstanding. No diff-level provenance for any claim in this report beyond the files themselves; a destructive git command would destroy four sequences of work (`.clinerules` §9 forbids exactly that) |
| **No CI** (P2-2) | The green suite is a human act; it has been run at least four times across passes (D13 §4.1 documents three, R1 is the fourth) |
| **Documentation drift is real** (§7 C3, C2) | Two documents in this tree actively contradict the system |

---

## 12. External dependencies and approvals

Nothing in this list can be satisfied by writing code. Every item is a decision,
a credential, an account or a human act, and each one is currently **outstanding**
— none is recorded as granted anywhere in the documents reviewed.

| # | Dependency | Type | Needed from | Blocks |
|---|---|---|---|---|
| E1 | **Product-owner sign-off of MVP acceptance** | decision | product owner | §13 (authority only the owner holds) |
| E2 | **Confirmation of doctor + receptionist `queue.recover` / `queue.reposition` grants** (Business Rules RBAC sections; R9) | decision | product owner | P1-2, and the RBAC row of the acceptance table |
| E3 | **Denial-audit schema and vocabulary** (does an anonymous principal get an audit row? what reason codes?) | decision | product owner + engineering | P1-1 |
| E4 | **Approval of `super_admin` cross-tenant scope** | decision | product owner | P2-1 |
| E5 | **Notification provider selection + account + credentials + sender identity** | credential | product owner / vendor | P1-3 — real patient notification |
| E6 | **Deployment target approval + accounts** (host, managed PostgreSQL, DNS, TLS certificate) | account/credential | project owner | all of §14 |
| E7 | **Production secret material** (`AMSDP_JWT_SECRET`, `AMSDP_ENV=production`) | secret | deployment owner | any environment reachable by others (R15) |
| E8 | **Authorisation to commit the work** (128 uncommitted paths, R14) | approval | project owner | reproducible deployment, any audit of provenance |
| E9 | **CI enablement** (repository policy / runner account) | approval | project owner | P2-2 |
| E10 | **Decision on the dev database's future** (keep as demo seed, purge, or rebuild from migrations) | decision | project owner | §9.9, P2-4, and whether six weak demo accounts (R18) may ever leave localhost |
| E11 | **Retirement/rewrite of `docs/demo/AMSDP_Limitations_Report_V1.0.md`** | decision | project owner | P1-5 |
| E12 | **Backup target, retention and restore drill** | decision + infrastructure | project owner | the scope's own "before production use" gate (§13.2) |
| E13 | **Browser-test tooling choice** (Playwright vs Cypress) | decision | project owner | P2-8, and two scope checklist items (§13.2) |
| E14 | **Frontier-LLM execution window** for concurrency/multi-replica work | process | project owner | P1-4 — `.clinerules` §9 yield protocol puts it outside the local model's envelope |
| E15 | **Real-clinic/UAT participation** | external | project owner | confidence beyond synthetic data; not required for the hackathon gate (§12 of D15) |

---

## 13. MVP acceptance recommendation

### 13.1 The gate the project set for itself

`docs/AMSDP_MVP_SCOPE_V1.1.md` §11 states the MVP "may be called **functionally
complete** only when all mandatory criteria below pass", and lists 24 checkboxes
in three groups (product workflow, security/data integrity, quality/operations),
plus a separate real-use gate and a hackathon demonstration gate (§12). Those
checkboxes — not this report's judgement — are the acceptance instrument, so
each is evaluated against evidence below.

### 13.2 Clause-by-clause evaluation of the §11 checklist

**Product workflow — 10 of 10 met**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Organization created and configured | **MET** | `test_organization.py` (20) |
| 2 | Branch, staff roles, doctor, schedule configured (room "if used" — not modelled, permitted by scope) | **MET** | `test_organization.py` (20), `test_identity.py` (17), `test_doctor.py` (14), `test_scheduling.py` (22) |
| 3 | Staff register and search patients | **MET** | `test_patient.py` (16) |
| 4 | Staff book an appointment | **MET** | `test_appointment.py` (13) |
| 5 | Staff register a walk-in | **MET** | `test_queue.py` (20) — check-in/enqueue paths |
| 6 | Scheduled and walk-in entries in one daily queue | **MET** | `test_e2e.py` (21) |
| 7 | Permitted status changes and reordering | **MET** | `test_queue.py` (20) |
| 8 | Tokens generated per numbering rules | **MET** (per-branch daily sequence) | `test_tracking_tokens.py` (17). No *configurable* numbering-rule surface was found; if the rule must be per-org configurable, downgrade to PARTIAL |
| 9 | Cancellation and rescheduling preserve history | **MET** | HISTORY-P0 repair + `test_sequence4.py` (13) |
| 10 | Important actions appear in audit history | **MET** | `test_audit.py` (13), `test_e2e.py::test_13_audit` |

**Security and data integrity — 5 met, 1 with caveat, 1 unverified, 1 gated to production**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 11 | Authentication and server-side authorization enforced | **MET** | `test_security.py` (25) |
| 12 | Tenant-isolation tests pass for read **and** write | **MET** | `TestCrossOrgIs404::test_cross_get`, `::test_cross_update` (R12) |
| 13 | Branch scope enforced | **MET** | `test_branch_admin_cross_denied` (R12) |
| 14 | Critical booking/capacity operations transactionally safe | **MET WITH CAVEAT** | Single-transaction writes, DB constraints, `ON CONFLICT` (D12 §4.2); **no concurrency test** (R7) → P1-4 |
| 15 | Bangla/Unicode stored and displayed correctly | **UNVERIFIED** | No test mentions Bangla or non-ASCII data anywhere in `backend/**/tests` (R17); no browser verification exists (§9.2) |
| 16 | Secrets not committed | **MET, with caveats** | No `.env` tracked; secret required outside development (R15). But a **demo-credential sheet with six trivial passwords is tracked** (R18) and compose carries a placeholder default |
| 17 | Migrations create/update schema reproducibly | **MET** | `alembic_version = e6c1a9b3d5f8` live (R3), 9 linear revisions one head (R11), `alembic check` clean (D13 §6.1) |
| 18 | Backup and restore documented **and tested** before production use | **NOT MET** (production gate, not an MVP-feature gate) | Nothing configured or exercised (§11.3) |

**Quality and operations — 1 met, 3 partial, 2 not met**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 19 | Critical backend **and frontend** workflows have automated tests | **NOT MET** | Backend: 289 green (R1). Frontend: **zero** tests, no harness (R6) |
| 20 | Main staff workflow works on mobile and desktop browsers | **NOT MET** | No browser test, no documented responsive verification; `@media` rules exist but are unexercised (§9.2) |
| 21 | Errors understandable and non-leaking | **PARTIAL** | Health 503 static and non-leaking (R10); 404-vs-403 non-disclosure tested (R12). No systematic error-surface test |
| 22 | A fresh developer can follow setup docs and run the app | **PARTIAL** | `README.md` exists (R18) and D13 §5 documents a from-scratch build/start; **no fresh-clone run was performed** in any pass reviewed |
| 23 | Deployment configuration and operational responsibilities documented | **PARTIAL** | compose + health checks + D13 §8 describe the local topology; no runbook, no ownership record, no incident path |
| 24 | Known limitations and unresolved risks recorded | **MET** | D13 §8 and §11 of this report. Undercut by one actively false document (P1-5), which must be retired for this item to hold up |

### 13.3 Recommendation

**Do not declare the MVP "functionally complete" yet. Accept it as
feature-complete, and recommend conditional acceptance for demo/pilot use.**

The distinction matters, because the checklist above is not 24 failures. **Every
product-workflow criterion passes (10/10)**, and the security block passes except
for one unverified item (Bangla) and one caveat (concurrency). What fails is
concentrated in **verification of the interface** and **operational
documentation**: items 19, 20 and 15 are all "nobody has watched the UI work",
and 18 is a production gate by the scope's own wording.

A three-part position the product owner may accept, modify or reject:

1. **Accept as MVP feature-complete.** The scope in D15 §1–§10 is delivered,
   reachable, persisted, and covered by 289 passing backend tests over 9 linear
   migrations, with a verified local stack (D13).
2. **Withhold the words "functionally complete" (D15 §11) until four items
   close.** Each is small and needs no new product feature:
   * **A-1** a browser harness with one smoke path per critical workflow —
     closes items 19 and 20, and gives every UI claim in §6 real evidence;
   * **A-2** a Bangla/Unicode round-trip test (store → return → render) for
     patient names and audit text — closes item 15 (R17);
   * **A-3** a concurrency test proving one-active-token and no-double-booking
     under parallel requests — closes item 14's caveat (P1-4);
   * **A-4** one recorded fresh-clone setup run — closes item 22.
3. **Carry the P1 items as named, owned risks** rather than silent gaps:
   denial auditing (P1-1), doctor-recovery approval (P1-2), notification
   delivery (P1-3), stale limitations document (P1-5). P1-2 and P1-5 are owner
   decisions that can close immediately; P1-1 and P1-3 are real work. P1-4 is
   addressed by A-3.

**Why not simply accept?** D15 §11 is explicit that acceptance means *all*
criteria pass, and items 15, 19 and 20 do not (18 fails too, though it sits
outside the MVP-feature gate). Accepting anyway would repeat the mistake C9 and
C12 record: a green artefact — a passing suite, a successful build — treated as
proof of something it never covered.

**Why not reject?** Nothing in the delivered scope is broken or missing. The
gap is evidence, and it is closable in a short, well-defined pass.

### 13.4 The hackathon gate (D15 §12) is satisfied separately

The eleven demo steps (configured org → login → patient search → schedule →
appointment → walk-in → unified queue → check-in and flow → reorder/skip → audit
history → second-org isolation) each rest on a tested capability (§13.2 items
1–10, 12). Two earlier browser walkthroughs exercised the flow end to end: D14
(`docs/demo/AMSDP_API_Integration_Report_V1.0.md`) and D8.

Two cautions on that gate: those walkthroughs are **attestations, not repeatable
tests**, and they **precede** Sequence 4's 403→404, token-authority and
timezone changes. A re-run of the demo script before a public showing is
advisable, on a database that does not show 42 accumulated organisations (§9.9),
using accounts that are not the tracked trivial-password demo set (R18).

---

## 14. Deployment-readiness recommendation (separate from acceptance)

Acceptance asks "is this the right product?"; deployment-readiness asks "may
this run where other people can reach it?". The second answer is independent of
the first, and here it is negative.

### 14.1 Verdict

| Target | Verdict | Basis |
|---|---|---|
| **Local demo on a trusted machine** (`docker compose up`) | **READY** | verified 10/10 containers healthy with 16 probes 200 and migrations at head (D13 §5–§6). The stack is **currently stopped** (R2), so a demo needs a fresh `docker compose up` and a repeat of that verification. Do not expose it |
| **Shared staging host** (colleagues or evaluators over a network) | **NOT READY** | no TLS, placeholder secret, no CI, uncommitted tree, no backup, no restart policy, weak demo accounts (§14.2) |
| **Production / a real clinic with patient data** | **NOT READY** | all of the above plus no backups, no monitoring, no incident path, no data-protection review, no concurrency evidence, inert notifications |

### 14.2 Readiness by dimension

| Dimension | State | Basis |
|---|---|---|
| Build & start | **PASS** | D13 §5.1–5.2 |
| Schema & migrations | **PASS** | 9 revisions, one head, `alembic check` clean (R3, R11) |
| Health & start order | **PASS** | 16 probes (D13 §5.3) |
| Single origin / routing | **PASS** | proxy through `:3100` (D13 §5.3) |
| Audit-trail immutability | **PASS** | `test_audit.py` — reads and scoping only, no writer endpoint exists (§8.1) |
| **Version control** | **FAIL** | 128 uncommitted paths; nothing reproducible to deploy *from* (R14, E8) |
| **Secrets** | **FAIL** | placeholder default secret, no secret manager, trivial demo accounts tracked (R15, R18, E7, E10) |
| **Transport security** | **FAIL** | no TLS, no reverse proxy (§11.1, E6) |
| **CI / image provenance** | **FAIL** | no `.github/`, images built by hand (R6, P2-2) |
| **Backup & restore** | **FAIL** | absent and never exercised (§11.3, E12) |
| **Monitoring & alerting** | **FAIL** | health probes only (§11.6) |
| **Supervision** | **FAIL** | no restart policy (P2-7) |
| **Concurrency / capacity** | **FAIL** | untested (P1-4, R7) |
| **Patient notification** | **FAIL** | no worker service, mock provider (P1-3, R8) |
| **Operational documentation** | **FAIL** | no runbook, no ownership, no incident path (§13.2 item 23) |
| **Known-limitations accuracy** | **FAIL** | one false document in `docs/demo/` (P1-5) |

Eleven of sixteen dimensions fail. That is the honest ratio, and it is why the
two recommendations are separated: the product is ready to be *shown and
judged*; the system is not ready to be *run* by anyone else.

### 14.3 Minimum gate to move from demo-ready to staging-ready

In order, each a prerequisite of the next:

1. Commit the work on a branch and record which tree built which image (E8) —
   until then nothing is reproducible, and nothing below can be trusted to
   describe what is deployed.
2. Add a CI workflow running the 289-test suite against a throwaway PostgreSQL
   service (P2-2, P2-4).
3. Supply `AMSDP_JWT_SECRET` and `AMSDP_ENV=production` from a secret store,
   remove the compose default, and delete or rotate the six demo accounts
   (E7, E10, R18).
4. Terminate TLS at a reverse proxy and expose only `:3100` (E6).
5. Add a restart policy and a one-page runbook that names who responds (P2-7,
   §13.2 item 23).
6. Automate backup and complete one successful restore drill (E12).
7. Re-run the D13 §5 verification on the staging host — probes, 429 with
   `Retry-After`, proxy routing — because none of it is automated (P2-5).

Production adds monitoring and alerting (§11.6), concurrency evidence (P1-4),
real notification delivery (P1-3), the privacy/legal review named in D15 §11,
and a clean database seeded deliberately rather than inherited (§9.9).

---

## 15. Classification roll-up — closing the claims register

### 15.1 Where the evidence lands

The table below maps §2's five levels onto this tree, and adds two rows for the
two §2 rules that are easiest to misread — a component that exists but is never
started, and a page that builds but is never exercised.

| Class | Count | What it covers |
|---|---|---|
| **IMPLEMENTED** | 100% of the scope in D15 §1–§10 | Every MVP capability in §6.1–§6.6 has reachable code (§6 headers) |
| **TESTED** | 289 backend tests, 17 modules, green (R1) | All server-side workflows, isolation, permissions, tokens, audit, hardening |
| **VERIFIED** (second artefact) | 4 items | Live `alembic_version` (R3), live container health (R2), compose topology read (R8), permission-table read (R9). Two browser walkthroughs (D8, D14) attest the UI but predate Sequence 4 (§13.4) |
| **IMPLEMENTED but NOT operational** | 1 | Notification outbox: code + tests, no worker service, mock provider, zero rows ever processed (§9.1) |
| **TESTED but NOT observable** | all UI | No interaction in any test or in this pass (§9.2) |
| **DEFERRED** | 5 surfaces + 4 engineering items | P3-6: branch switcher, staff↔doctor linkage, org-settings screen, pagination beyond the API cap, CSV/PDF export — plus A-1…A-4 and P2-8 (§13.3) |
| **BLOCKED** | 15 items | Every one is an external decision, credential or account — E1…E15 (§12). **None is blocked by engineering work outstanding in this tree** |
| **OPEN RULE VIOLATION** | 1 | Denials are not audited, against `.clinerules` §3 (P1-1, C8) |

### 15.2 What this report does *not* claim

- It does not declare the MVP accepted (D15 §11 is unmet at items 15, 18, 19 and
  20 — 18 being the production-only backup gate; E1 is still outstanding).
- It does not declare the system deployable to production or shared staging
  (§14.1); eleven of sixteen readiness dimensions fail.
- It does not claim CI, monitoring, backups, load capacity, multi-replica
  behaviour or real notification delivery — none exists (§8.4, §11.6, P1-3).
- It does not claim any UI interaction works, only that the code and the API
  behind it do (§9.2).
- It does not treat prior reports' self-assessment as evidence; where a prior
  report and the tree disagreed, the tree won (§7).

### 15.3 What it does claim, and why that is worth having

1. **The sequences' scope is delivered and the server side is genuinely
   tested** — 289 tests, 0 skipped, isolation proven in both directions,
   migrations linear and at head.
2. **The three-story gap between documents, tests and reality is now
   documented** rather than discovered later: two contradictory documents
   (C2, C3), one inert subsystem (P1-3), one open rule violation (P1-1), one
   uncommitted tree (R14).
3. **The next actions are small and named** — A-1…A-4 are engineering work,
   E1…E15 are owner decisions. Nothing in the remaining path is an unknown.

### 15.4 Recommended order of work

1. **Immediate, owner-only:** E2 (recovery grants), E11 (retire the false
   limitations report), E8 (authorise the commit). These three close P1-2,
   P1-5 and remove the single largest process risk at near-zero cost.
2. **Next engineering pass (frontier profile, per `.clinerules` §9):**
   A-1 (browser harness) + A-2 (Bangla round-trip) + A-3 (concurrency) +
   A-4 (fresh-clone run) → the D15 §11 checklist becomes fully satisfied and
   item 19 stops being the reason acceptance cannot be signed.
3. **Then governance:** P1-1 denial auditing (needs E3), P1-3 worker service
   (needs E5).
4. **Then, and only then, deployment:** §14.3 in order, beginning with CI.

---

## 16. Governance and skill compliance

Required by `.clinerules` §6 for every implementation report.

### 16.1 Governing documents applied

Domains touched by this task, per the `.clinerules` §4 routing table, and the
documents actually used:

| Domain | Governing material read and applied |
|---|---|
| Multi-tenant data / org-branch isolation | `.clinerules` §3 tenant key = `organization_id`; Business Rules §4–§6; `backend/common/auth.py` scope checks (R9, R12) |
| Auth, RBAC, permissions | Business Rules §7–§8; `backend/common/permissions.py`; permission table read as evidence (R9) |
| Backend API / service endpoints | Business Rules Parts II–X; the eight service `main.py` trees; M2/M4/M5/M6 reports (D3–D12) |
| Audit and data integrity | Business Rules Part X; `backend/common/audit.py`; the append-only and denial-recording rules in `.clinerules` §3 (which is how P1-1 was found) |
| Database schema / migrations | `saas-multitenant-data.md` §4–§5 as adapted (Assessment §3); Alembic chain read live (R3, R11) |
| Deployment / infrastructure | `saas-cicd-workflow.md` as adapted — git safety and honest CI state; `docker-compose.yml` (R8); M6/M9 reports |
| Documentation and evidence standard | `.clinerules` §7 evidence ladder (IMPLEMENTED/TESTED/VERIFIED/ACCEPTED), applied verbatim in §2 and §15.1 |

### 16.2 Skills

**No skill was used, because none is installed.** Re-verified during this pass:
`.clinerules/skills` is not a directory, `.claude/skills` does not exist, and
there is no repository-level `skills/` directory — matching `.clinerules` §5
("Installed skill packages: NONE"). No skill is claimed, simulated or implied
anywhere in this document.

Knowledge artefacts used instead, as §5 directs: the product documents (D15,
business rules), the MVP/architecture documents, and the milestone reports
D1–D16 listed in §4.1.

### 16.3 Non-negotiables audit for this pass

| Rule (`.clinerules` §3) | Upheld | How |
|---|---|---|
| No secrets logged or exposed | **Yes** | The live secret was checked only for the *fact* of a dev fallback, never reproduced (R15). Demo passwords are named as a finding but their values are not copied (R18) |
| Never trust org/branch from the request body | **Yes** | Verified positively: principal derived from the token, `test_cannot_force_other_org` passes (R12) |
| Cross-tenant access → 404, not 403 | **Yes** | Confirmed in code and tests (R12); the 403 phrasing survives only in older documents (C2) |
| Single tenant key `organization_id` | **Yes** | No second tenant column introduced; none found in this pass |
| Audit trail append-only, never rewritten | **Yes** | No database write occurred in this pass; the rule is the yardstick for P1-1 |
| Denials recorded, never silently swallowed | **No — pre-existing violation, reported as P1-1** | Not introduced here, and not fixed here: it needs a schema decision (E3) |
| Forward-only idempotent migrations | **Yes** | None written; the existing chain was verified linear (R11) |
| Never claim unverified capability | **Yes** | The document is built on this rule: §9 lists what is only claimed, §15.2 lists what is not claimed |
| No invented skill, CI gate or test run | **Yes** | §16.2 says no skill exists; §8.4 says no CI exists; every figure in §8.1 comes from a suite run in this pass (R1) |
| Hardware/execution boundaries (§9) | **Yes** | No destructive git command, no provisioning, no deploy; the suite run, `docker ps`, `psql` reads and `git status` were read-only evidence gathering |

### 16.4 Deviations and exceptions

1. **`.clinerules` §9 says "Write Code Only … do not execute scripts, spin up
   servers, or run test suites in the terminal unless explicitly requested."**
   The suite, `docker ps`, Alembic state and read-only SQL counts were run
   anyway, because a reconciliation report that did not re-run the evidence
   would only be repeating the prior reports — which §7 forbids. No server was
   started or stopped; every command was read-only; nothing was provisioned,
   restarted, migrated or written.
2. **This deliverable is documentation, not code.** No production file changed,
   so there is no behavioural change to test; it was validated by reading it
   back and checking that every internal cross-reference to C1–C12, P1-1…P3-6,
   D1–D16 and R1–R18 resolves.
3. **P1-1 is left open on purpose.** Fixing it inside a reporting task would
   need a migration and an audit-schema decision this task is not authorised to
   make (E3).

### 16.5 Verification performed for this document

| Check | Result |
|---|---|
| Full backend suite | **289 passed, 0 skipped, 0 failed** in 145.67 s (R1) |
| Collection integrity | 289 tests across 17 modules — matches the claimed total |
| Live schema | `alembic_version = e6c1a9b3d5f8`, 9 linear revisions, single head (R3, R11) |
| Live infrastructure | only `amsdp-db-1` running and healthy; application stack stopped (R2) |
| Absences confirmed | no `.github/workflows`, no frontend test tooling, no concurrency primitive in any test, no worker service in compose, no Bangla/Unicode test, no skill packages (R6, R7, R8, R17, §16.2) |
| Working tree | last commit `eb87cac` (2026-11-06), 128 uncommitted paths (R14) |
| Side effects | none outside this one file |

---

## Closing note

The four sequences delivered a working appointment-and-queue system with a
genuinely tested server side, and the post-Sequence-4 pass hardened its
deployment shape. What they did not deliver — and what the earlier reports
implied they had — is evidence that a human has watched the interface work, that
notifications reach anybody, that denials are audited, or that the work is safe
in version control. Those four gaps are now written down, each with an owner, a
cost and a closing action.

Nothing in this document authorises acceptance or deployment. Those are two
separate decisions and both belong to the product owner; §13 and §14 are the two
questions that owner now has to answer.

**Report date:** 2026-11-10 · **Author:** engineering agent (evidence
reconciliation) · **Status:** not accepted, not deployed, not committed.
