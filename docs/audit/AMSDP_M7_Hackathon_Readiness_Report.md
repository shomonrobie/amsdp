# AMSDP M7 Hackathon Readiness Report

> **Milestone ID:** AMSDP-M7-HRR-2026-11-08
> **Milestone Name:** M7 — Hackathon Readiness & Release Hardening
> **Status:** EXECUTED — CONDITIONAL GO (see §17)
> **Date:** 2026-11-08
> **Product:** AMSDP — Appointment Management System for Doctors & Patients

## 1. Executive summary

M7 delivered and verified the hackathon-critical hardening workstreams plus regression
hardening:

1. **Isolated clean demo environment** (B0) — dedicated demo database `amsdp_demo` on a
   dedicated Docker volume, initialized reproducibly by `_tools/init_demo_env.sh`
   (verified live: logins, dashboard, queue, audit all served from demo data; development
   data untouched).
2. **Backup & restore** (B1) — container-version-matched `pg_dump` backup + a real restore
   test into an isolated throwaway database (dev and demo both verified; dev DB never used
   as a restore target).
3. **Demo runbook** (B2) — `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`.
4. **Bangla/English localization** (B3) — label sweep across dashboard, queue, and audit;
   existing language toggle preserved; production build green (no layout breakage).
5. **Branch switching + access control** (B4) — backend `/api/v1/me/branches` scoping,
   server-side `require_branch_access` enforcement on dashboard/audit endpoints, frontend
   branch selector, branch-filtered dashboard/audit.
6. **Audit coverage** (B5) — transactional persistent audit for appointment
   create/status-change/cancel/reschedule/transfer/walk-in, organization and branch
   create/update, and staff create/update.
7. **Staff↔doctor linkage** (B6) — optional nullable `staff_users.doctor_id` FK with
   same-org validation (migration + tests).
8. **Rehearsal** (B7) — 32/32 live workflow checks on the isolated demo stack, plus
   20-concurrent-enqueue token uniqueness, persistence-across-restart, and clean demo logs.

Automated regression: **77/77 tests pass** (patient-age 13, identity 17, security 21,
dashboard 6, queue 20). The security and identity test suites were repaired from
destructive delete-all fixtures to idempotent upserts, and a pre-existing circular-import
bug in the Identity service (which hid the staff routes from import/test contexts) was
fixed.

**Independent findings fixed along the way:** org_admin could not list staff (`staff.read`
missing from the RBAC matrix); duplicate usernames returned HTTP 500 instead of a client
error; queue UI offered check-in for appointments in non-check-in-able states.

## 2. Milestone ID and scope

| Item | Value |
|---|---|
| Milestone ID | AMSDP-M7-HRR-2026-11-08 |
| Mode | Incremental implementation + verification + evidence-based reporting |
| Personas | Receptionist, Doctor, Organization Administrator (per §1 mission) |
| Out of scope | New product features, excluded EMR/portal/billing features, AILI changes, commits/pushes |

## 3. Baseline findings (verified at start)

- Stack was running on the documented ports (3100, 8110–8117, 5433); unrelated processes
  (3000/5432 and third-party containers) untouched.
- Dev database `amsdp` contained demo data **mixed with test artifacts**: 6 orgs,
  7 branches, 9 staff, 145 patients (matches the readiness assessment).
- No demo database, no backup/restore mechanism, no runbook.
- `test_e2e.py` is **stale**: it references `_users_db`/`_orgs_db` in-memory stores removed
  by the M1/M3 PostgreSQL conversions; it has not been part of the green regression since
  then and is superseded by live rehearsal evidence (see §15).
- `tests/test_security.py` and `identity/tests/test_identity.py` fixtures **deleted the
  whole `staff_users` table on every run** (destroying demo accounts); restoration and
  fixture repair were required.

## 4. Work completed by workstream

### M7-B0 — Isolated clean demo environment ✅
- `docker-compose.demo.yml` overrides the `db` service to `POSTGRES_DB=amsdp_demo` on a
  dedicated volume `amsdp_demo_pg_data`, and points every backend at `amsdp_demo`.
- `_tools/init_demo_env.sh` automates: stop demo → start demo db → alembic upgrade →
  idempotent seed → start stack → health checks (executed, ran clean; log
  `/tmp/demo_init3.txt`).
- Enhanced `backend/seed/seed_demo.py`: 2 branches, 5 doctors, schedules, 10 patients,
  7 appointments (multi-status), 2 queue entries; idempotent and self-refreshing (re-seed
  on demo morning re-dates demo-owned rows to today).
- Isolation verified: demo DB has 1 org / 2 branches / 6 staff / 5 doctors / 10 patients /
  5 schedules / 7 appointments; dev DB untouched after demo runs.

### M7-B1 — Database backup and restore ✅
- `_tools/pg_backup.sh` — container-matched `pg_dump` (fixes a host-version
  `SET transaction_timeout` incompatibility found during the work), parameterized by
  container/dbname.
- `_tools/pg_restore_test.sh` — restores into an isolated `amsdp_restore_test` database,
  verifies schema, essential counts, alembic head, SQLAlchemy connectivity, then drops the
  temp DB. Dev DB is never a restore target.
- Verified for BOTH dev (`amsdp`) and demo (`amsdp_demo`): restore → 12 tables, matching
  counts, connectivity OK (see §10).

### M7-B2 — Demo runbook ✅
`docs/demo/AMSDP_Hackathon_Demo_Runbook.md` — prerequisites, configuration, compose
startup/shutdown, DB init + seeding, account/role map, addresses + health checks,
step-by-step persona workflows with expected results, backup/restore, common errors,
pre-demo checklist, post-demo cleanup that never affects development data.

### M7-B3 — Bangla and English localization ✅
- Added ~35 dictionary keys (branch selector, dashboard cards, audit column headers, queue
  statuses/actions, modal labels) in `frontend/lib/i18n.js`.
- Swept `dashboard.js`, `audit.js`, `queue.js`; placeholders/buttons now render `t(...)`.
- Next.js production build green; existing toggle preserved.

### M7-B4 — Branch switching and access control ✅
- Backend: `GET /api/v1/me/branches` (org_admin/super_admin → all org branches;
  branch-scoped roles → their token branch only). Dashboard `/today`, `/period`, `/audit`
  now enforce `require_branch_access(branch_id)` server-side.
- Frontend: header branch selector (fetches `/api/v1/me/branches`, saves selection in
  session); dashboard/audit re-fetch with `branch_id`.
- Patients remain org-scoped (not branch-assigned); appointment branch association preserved.

### M7-B5 — Audit coverage ✅
- Transactional `record_audit` calls (same session/commit) added in: appointment
  (created, walk_in_created, status_change covering cancel/check-in/no-show, rescheduled,
  transferred), organization (created/updated org + branch), identity (staff
  created/updated).
- Audit payload now includes `organization_id` for admin clarity.
- Verified live: booking + cancellation produced `appointment.created` and
  `appointment.status_change` (CANCELLED with reason/actor/org/branch/role); audit endpoint
  returns only the caller org's events.

### M7-B6 — Staff↔doctor linkage ✅ (minimal, safe)
- Migration `9d8a1f2b3c4d_add_staff_doctor_link`: nullable `staff_users.doctor_id` FK.
- Identity create/update accept optional `doctor_id`, validated same-organization
  (unknown/cross-org → 422). Not every staff member is a doctor; manual doctor selection
  remains the fallback. Demo doctor staff linked to Dr. Kamal Hossain.
- 4 new automated tests.

### M7-B7 — Final regression and demo rehearsal ✅
- Live rehearsal on the isolated demo stack: 32/32 checks (§8); reliability probes 6/6
  (§8); final automated regression 64/64 (§7).

### M7-B8 — Patient age and optional date of birth ✅
- Optional `date_of_birth` kept optional (never mandatory; privacy rule applied). Added a
  nullable `age` (reported age, 0–150) column via migration
  `3c8e5d0a9b2f_add_patient_age` — forward-only, idempotent.
- Backend schema/validation (`patient/main.py`): `PatientCreate`/`PatientUpdate` accept
  optional `date_of_birth` (YYYY-MM-DD, must not be future) and optional `age` (0–150);
  responses expose `age` (reported, raw), `age_from_dob` (server-computed), and
  `age_source` (`'dob' | 'reported' | ''`).
- Authoritative rule: when DOB is present, `age_from_dob` is authoritative
  (`age_source='dob'`); a manually entered age is never treated as authoritative then.
  When DOB is absent, the reported age is shown (`age_source='reported'`). **A DOB is
  never inferred or fabricated from a reported age.**
- Frontend (`patients.js`): optional DOB + Reported-Age inputs in registration and an Age
  column that shows `age_from_dob (age from DOB)` vs `reported age`; Bangla/English via the
  page's locale dict; registration works with both, DOB only, age only, or neither.
- Demo seed: some demo patients now carry a DOB or a reported age for realism.
- Tests: new `backend/tests/test_patient_age.py` (13 tests) — all four registration
  combinations, birthday-boundary computation, validation rejections, edit behaviour
  (DOB becomes authoritative when added; reported age resurfaces if DOB cleared), and
  legacy-record compatibility.
- Live verification (`/tmp/age_live_out.txt`): 16/16 — both/DOB-only/age-only/neither
  register (201); computed age correct (1980-04-12 → 46); no fabricated DOB; future DOB and
  out-of-range age rejected (422); listing carries the new fields.

## 5. Files created or modified

**Created:** `docker-compose.demo.yml`, `_tools/init_demo_env.sh`, `_tools/pg_backup.sh`,
`_tools/pg_restore_test.sh`,
`backend/alembic/versions/9d8a1f2b3c4d_add_staff_doctor_link.py`,
`backend/alembic/versions/3c8e5d0a9b2f_add_patient_age.py`,
`backend/tests/test_patient_age.py`, `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`.

**Modified:** `backend/seed/seed_demo.py`, `backend/common/models.py`,
`backend/common/permissions.py`, `backend/patient/main.py`,
`backend/identity/{main,routes,models}.py`,
`backend/appointment/{main,dashboard}.py`, `backend/organization/main.py`,
`frontend/lib/i18n.js`, `frontend/lib/auth.js`, `frontend/components/AppShell.js`,
`frontend/pages/{dashboard,audit,queue,patients}.js`, `frontend/next.config.js`,
`frontend/styles/global.css`, `backend/tests/test_security.py`,
`backend/identity/tests/test_identity.py`.

## 6. Database and migration changes

| Change | Migration | Status |
|---|---|---|
| `staff_users.doctor_id` nullable FK → `doctors.id` (M7-B6) | `9d8a1f2b3c4d_add_staff_doctor_link` | Applied to dev + demo DBs, forward-only + idempotent; alembic head `9d8a1f2b3c4d` |
| `patients.age` nullable INT = reported age (M7-B8) | `3c8e5d0a9b2f_add_patient_age` | Applied to dev DB; applied to demo on next `init_demo_env.sh`; head `3c8e5d0a9b2f` |

`date_of_birth` remains the existing optional `String(20)` column; never mandatory. The
demo database `amsdp_demo` (dedicated volume) is migrated through the full chain by
`_tools/init_demo_env.sh`. **The development database was preserved** (never
deleted/reset/truncated; only additive demo seed + forward migrations).

## 7. Tests executed and exact results

| Suite | Result | Notes |
|---|---|---|
| `tests/test_patient_age.py` | **13 passed** | M7-B8 age/DOB suite (four combos, computation, validation, edit, back-compat) |
| `identity/tests/test_identity.py` | **17 passed** | incl. new doctor-link suite (4) |
| `tests/test_security.py` | **21 passed** | ALLOW+DENY matrix; fixtures non-destructive |
| `tests/test_dashboard.py` | **6 passed** | real-Aggregates |
| `queuing/tests/test_queue.py` | **20 passed** | incl. concurrency + negative perms |
| **Total automated** | **77 passed** | final run: `77 passed in 15.73s` (log `/tmp/full_reg_m7b8.txt`) |
| `tests/test_e2e.py` | **not run (stale)** | legacy in-memory artifact; superseded by live rehearsal (§3/§15) |
| Frontend build | `next build` green | 12 routes generated; patients page rebuilt with age/DOB |

Automation note: the identity/security suites were repaired to be **idempotent and
non-destructive** (upsert fixtures + unique usernames) and no longer delete demo accounts;
duplicate-username creates now return HTTP 422 rather than 500.

## 8. End-to-end workflow evidence

All checks executed against the **isolated demo stack** (`docker compose -p amsdp_demo`),
log `/tmp/rehearsal_final.txt`. Each API result was cross-checked against resulting DB state
where material.

**Rehearsal — 32/32 PASS**

| Area | Checks (all PASS) |
|---|---|
| Logins | all 6 canonical roles |
| Receptionist | search patients (n=10), register patient (201), book appointment (201), second booking within capacity (201), walk-in (201), BOOKED→CONFIRMED (200), check-in creates queue entry, queue reorder (200 + persisted), receptionist CAN enqueue walk-in (201) |
| Doctor | sees linked queue (demo-dr-002, T-DR002-001 waiting), start consultation (200), complete consultation (200), **DB-verified** queue `status=completed` |
| Security / RBAC | receptionist DENIED consultation (403), assistant DENIED appointment create (403), assistant CAN read patients (200), unauthenticated (401), invalid token (401) |
| Org admin | dashboard branch 1 (total=9), dashboard branch 2 (200), sees 2 branches for switching, receptionist sees 1, **receptionist cross-branch dashboard DENIED (403)** |
| Audit | includes `appointment.created`, includes `queue.*` events, all events org-scoped to demo-org-001 |

**Reliability — 6/6 PASS** (`/tmp/reliability_out.txt`, `/tmp/persist_demo_out.txt`):
20 concurrent enqueues → all 201 with **20 unique queue tokens**; queue listing shows 20;
persistence probe appointment `994d915c-…` **survived restart** of appointment/queue/identity;
dashboard totals intact (11 before/after restart).

**Demo logs:** zero `ERROR`/`Traceback` lines across the rehearsal (`/tmp/demo_logs.txt`).

## 9. Security and tenant-isolation evidence

- RBAC ALLOW + DENY matrix: 21 security tests + live denials (receptionist consult 403,
  assistant book 403, cross-branch dashboard 403).
- Tenant isolation: audit returns only the caller's `organization_id`; staff reads are
  org-scoped; cross-org creates rejected.
- Branch isolation: server-side `require_branch_access` on dashboard; `/me/branches` role
  scoping; patients remain org-scoped.
- Token edge cases: unauthenticated 401, invalid token 401; inactive users rejected (test).
- No secrets logged; JWT secret handling unchanged; dev-only credential approach preserved
  (seeds are not production credentials, never committed with a real secret).

## 10. Backup and restore verification

| Run | Result |
|---|---|
| Dev backup (`amsdp_dev_20261108-173701.sql.gz`) + restore test | 12 tables; orgs=6, branches=7, staff=9, patients=145, appts=6, audit=20; alembic `c7d3601e2486`; SQLAlchemy probe OK; temp DB dropped |
| Demo backup (`amsdp_amsdp_demo_20261108-191145.sql.gz`) + restore test | 12 tables; orgs=1, branches=2, staff=6, patients=11, appts=11, audit=29; alembic `9d8a1f2b3c4d`; probe OK; temp DB dropped |

Both restores targeted the isolated `amsdp_restore_test` database only; the development
database was never written to by the restore tooling.

## 11. Demo environment instructions

Refer to `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`. Key commands:

```bash
_tools/init_demo_env.sh                                    # fresh demo stack (dev must be down)
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down   # stop demo
docker compose -p amsdp up -d --build                      # resume dev
```

## 12. Known limitations and unresolved defects

| # | Limitation | Impact | Owned by |
|---|---|---|---|
| 1 | `tests/test_e2e.py` stale (in-memory legacy) — not part of green regression | Cosmetic; live rehearsal covers e2e | future cleanup |
| 2 | Reserved-capacity configuration has no org-settings UI (opt-in, default off) | Deferred per readiness assessment | future milestone |
| 3 | Some secondary screens still have hardcoded English labels (orgs/staff/schedules/doctors/patients) | Minor inconsistency on non-critical screens | future i18n sweep |
| 4 | Queue UI check-in list now shows only `CONFIRMED` appointments (aligned with BR §18) | None (backend always authoritative) | — |
| 5 | Dev database accumulates additive test artifacts from suites | Demo order-of-magnitude; demo DB is isolated and clean | documented |
| 6 | Demo and dev stacks cannot run simultaneously (shared host ports) | Runbook documents stop/start routine | by design |

## 13. Governance and applicable agent-rules compliance

- **Routing (.clinerules §2/§4):** task parsed across Database/migrations · Docker/infra ·
  Backend API · Multi-tenant isolation · Auth/RBAC · Dashboard · Queue/scheduling · Audit ·
  Frontend UX/i18n rows; governing documents applied as adapted in the governance assessment §3.
- **saas-multitenant-data (adapted):** demo DB forward-only-migrated and isolated; tenant key
  remains `organization_id` (no second tenant column); demo/dev isolation verified; the
  staff↔doctor FK shipped as a forward-only idempotent Alembic migration.
- **saas-application-security / saas-auth-and-authorisation (adapted):** branch authorization
  enforced server-side; tenant from principal only; cross-branch 403/404; UI is not the
  boundary (branch selector is presentation only); RBAC matrix extended minimally (org_admin
  `staff.read`); ALLOW+DENY paths tested.
- **saas-observability (adapted):** audit writes transactional + append-only; denials recorded;
  no secrets logged; audit search surface verified.
- **saas-frontend-ux (adapted):** no second design system; states preserved; i18n without layout
  breakage.
- **saas-cicd-workflow (adapted):** no CI claims invented; git untouched (no commits/pushes);
  no destructive git; uncommitted milestone work preserved.
- **Non-negotiables (.clinerules §3):** dev DB never deleted/reset/truncated; 3000/5432 and
  unrelated processes untouched; ports preserved; AILI unmodified; nothing committed/pushed.

## 14. Skills discovered and actually used

- **No skill packages are installed** in this workspace (verified in the governance
  integration). No skill was claimed or used; all work followed the governance documents.
- Knowledge artefacts used: `.clinerules`, `AMSDP_Engineering_Governance_Assessment.md`,
  `AMSDP_Skill_Routing_Architecture.md`, Business Rules, M4/M5/M6 reports, readiness
  assessment, and the adapted agent-rules.

## 15. Deviations from the authorization and reasons

1. **`tests/test_e2e.py` not run** — it references removed in-memory stores; rewritten e2e
   coverage was unnecessary because the authorization itself mandates a live rehearsal with
   DB-state verification, which was executed and passed (32/32). Stale artifact documented
   (§12) rather than rewritten to avoid duplicate maintenance.
2. **Staff↔doctor linkage implemented (not deferred)** — the minimal optional FK approach
   carried low risk and was completed with migration + tests. No business rule changed;
   manual doctor selection remains the fallback, satisfying the authorization's safety
   conditions.
3. **Demo DB isolated via a dedicated volume** — the authorization preferred "a separate
   Docker volume"; implemented exactly that (`db` override with `amsdp_demo_pg_data`).
   Demo and dev data remain fully isolated (verified).
4. **Test-fixture repairs** (destructive delete-all → idempotent upsert; duplicate-username
   422; Router refactor) — pre-existing defects that endangered data; fixed as quality
   hardening under the regression mandate, not as new product scope.

## 16. Remaining risks

- **Low:** reserved-capacity org-settings UI absent; secondary-screen labels not all localized.
- **Low:** dev DB grows with additive test artifacts (mitigated by the isolated demo DB).
- **Low:** host platform specifics (Docker compose v2, Linux) assumed; verified on this host.
- **None critical:** core receptionist → doctor → admin workflows, isolation, persistence,
  concurrency, audit, backup/restore, and demo environment all verified.

## 17. Final recommendation

**CONDITIONAL GO.**

All GO criteria are met: clean isolated demo environment; backup and restore both verified;
runbook complete; critical receptionist/doctor/administrator workflows pass end-to-end
(32/32); security and tenant/branch isolation pass; operational audit coverage verified;
localization usable across the critical demo workflows; the application starts reliably via
the documented procedure; no critical/high defect remains.

Conditional items (non-blocking, listed in §12): reserved-capacity UI, secondary-screen i18n,
and stale-e2e cleanup remain for future milestones.

---

## Governance and Skill Compliance

- **Applicable governance documents (routed):** saas-multitenant-data, saas-application-security,
  saas-auth-and-authorisation, saas-observability, saas-frontend-ux, saas-cicd-workflow (all as
  adapted in the governance assessment), plus Business Rules and `.clinerules`.
- **Selected skills:** none installed; resolved to the listed governance documents (reported per
  `.clinerules` §5), never claimed as used.
- **Evidence instructions were followed:** non-negotiable preservation rules held (ports, dev
  data, unrelated processes, AILI); ALLOW+DENY and cross-branch/org denials verified; audit
  writes transactional; no skill/CI capability fabricated; git untouched.
- **Tests and verification performed:** 77/77 automated (incl. new patient-age 13); 32/32 +
  6/6 live demo checks; M7-B8 live registration/computation 16/16; backup + restore verified
  for dev and demo; frontend production build green.
- **Deviations or exceptions:** §15 above (stale e2e documented; linkage implemented; test-fixture
  repairs; demo volume approach).
- **Skills unavailable or not applicable:** all skill slots — none installed; `emissions-provenance`
  and `saas-ai-provider-registry` not applicable to AMSDP.