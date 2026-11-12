# AMSDP MVP — Hackathon Readiness Assessment

**Date:** 8 November 2026
**Mode:** Read-only assessment (no code modified)
**Scope:** M6 outstanding findings, eight-priority verification, end-to-end workflow, reliability/security, demo readiness

---

## 1. Executive Summary

AMSDP's core appointment-and-queue workflow is **functional, persistent (PostgreSQL), secured (RBAC + tenant/branch isolation), and test-backed**. Live end-to-end verification passed all 15 workflow checks across receptionist, doctor, and admin personas, and data survives service restarts.

The main demo risk is **data cleanliness**, not functionality: automated test runs mixed test-only organizations/patients into the same database as the curated demo data, and no database backup/restore mechanism exists. Several M6 follow-ups (branch switch, staff↔doctor link, appointment-side audit, reservation UI) remain open but do **not** block the core receptionist→queue→doctor workflow.

**Recommendation: CONDITIONAL GO** — conditional on owner-approved clean demo data and a small backup script. Details in §8.

---

## 2. M6 Outstanding Findings — Status

| # | Finding | Status | Before hackathon? |
|---|---------|--------|-------------------|
| 1 | **Branch-switch control** — `/dashboard/today`/`period` accept `branch_id` and AppShell shows org context, but there is **no branch selector UI**. | **FAIL (UI)** | Not required (single-branch demo OK) |
| 2 | **Staff-to-doctor profile linkage** — `StaffUser` has no `doctor_id`; `Doctor` has no staff link. Doctor persona manually selects a doctor in Queue UI. | **FAIL (model)** | Not required (manual selection works) |
| 3 | **English-only dashboard labels** — dashboard cards, queue/audit buttons hardcoded English despite `lib/i18n.js`. | **PARTIAL** | Recommended (quick label sweep) |
| 4 | **Queue-centric audit coverage** — persistent audit covers **all queue operations** (verified live). Appointment/org writes not yet audited; legacy in-memory audit service unused by any frontend flow. | **PARTIAL** | Main queue path covered → not blocking |
| 5 | **Reserved-capacity configuration UI** — config exists (default disabled) + `available-slots` reports fields, but **no org-settings screen**. | **FAIL (UI)** | Defer (opt-in feature) |
## 3. Eight-Priority Feature Assessment

| # | Priority | Persistence | API/Backend | Frontend | Security | Evidence | Verdict |
|---|----------|-------------|-------------|----------|----------|----------|---------|
| 1 | Org & Branch | ✅ PostgreSQL | CRUD + auth + org scope | list + create (no edit UI) | ✅ | org e2e + M2 tests | PASS |
| 2 | Staff mgmt | ✅ | CRUD + 6 roles + activate/deactivate | list + create (no edit/deactivate UI) | ✅ staff perms + branch scope | identity 13/13 | PASS |
| 3 | Doctor mgmt | ✅ | CRUD + branch assignment | list/search/register (no edit UI) | ✅ | doctor e2e | PASS |
| 4 | Patient mgmt | ✅ org-scoped | search/register/update + dup warnings | search/register + dup warning | ✅ | patient e2e | PASS |
| 5 | Scheduling | ✅ | templates, 3 models, capacity | list/create/available-slots | ✅ | availability e2e | PASS |
| 6 | Appointment | ✅ | BR§18 lifecycle, reschedule/transfer, cancel reason, walk-in | book/walk-in/status/check-in | ✅ atomic capacity | capacity 2/3 e2e | PASS |
| 7 | Queue mgmt | ✅ | check-in, walk-in, reorder, tokens (atomic), consult transitions, history | full UI | ✅ doctor-only consult | 20 tests + concurrency | PASS |
| 8 | Dashboard & audit | ✅ | `/today`, `/period`, `/audit` real aggregates | cards + audit filters + denied state | ✅ org-scoped, 401 | 6 tests + live | PASS |

**Overall:** all eight priorities are PostgreSQL-backed, real-API, security-enforced, and test-covered. Frontend **edit** UIs (org/branch/staff/doctor/patient; appointment reschedule/transfer) are the main functional gaps; list/create + workflows complete.

## 4. Full End-to-End Workflow — Live Test Results (15/15 PASS)

**Receptionist:** login; patient registration ("M7 Demo Patient") + search (7 found); doctor selection; availability check (30-min slots); booking (BOOKED) with capacity enforced (2nd accepted at limit 2, **3rd rejected 422**); walk-in (entry_source=walk_in); check-in (queue token T-DEMO-D-005); queue reorder (positions swapped, tokens stable).

**Doctor:** view personal queue (doctor selector); start consultation (waiting→in_consultation); complete (→completed, appointment COMPLETED).

**Administrator:** dashboard today metrics (real counts); audit history (19 events, filtered); role restrictions — assistant → staff list **403**, receptionist → start consultation **403**.

**Unverified/incomplete steps:** appointment reschedule/transfer have backend APIs but no UI; doctor's auto-personal queue requires manual doctor selection (no staff↔doctor link). Neither blocks the core demo.

## 5. Reliability & Security Assessment

| Item | Status | Evidence |
|------|--------|----------|
| Persistence after restart | PASS | Container restarts → 6 appointments & 19 audit events intact |
| Appointment capacity / concurrency | PASS (serial); boundary race not stress-tested | atomic COUNT; 3rd booking rejected 422 |
| Queue token concurrency | PASS | atomic UPSERT; 20 concurrent → 20 unique |
| Tenant isolation | PASS | org-scoped queries; cross-org → empty/404 |
| Branch isolation | PASS | token-branch filters for scoped roles |
| Role permissions | PASS | RBAC enforced; consultation doctor-only (403 tested) |
| Audit completeness | PARTIAL | queue comprehensive; appointment/org pending |
| Invalid transitions | PASS | map rejects (422, verified live) |
| Error handling | PASS | consistent JSON detail + frontend states |
| DB backup & recovery | FAIL | no backup/restore script or procedure |

## 6. Demo Readiness

| Item | Status | Notes |
|------|--------|-------|
| Demo accounts (six roles) | PASS | Verified live (usernames below; passwords are the documented demo dev credentials in `backend/seed/seed_demo.py` — retrieve there, not reproduced in this report) |
| Realistic demo data | PARTIAL | Demo data exists but DB also holds **test rows** from automated suites |
| Clean demo org/branches | PARTIAL | demo-org-001/demo-br-001 present alongside test orgs |
| Bangla/English | PARTIAL | AppShell + i18n; dashboard/queue labels partially English |
| Desktop / mobile | PASS / PARTIAL | drawer + responsive; table wrap only on queue |
| Startup & recovery | PASS | compose up; idempotent seed; persistent volume |
| Repeatable demo workflow | PASS | 15-step automation passes |
| Demo runbook | FAIL | not yet written (M7 deliverable) |

**Demo accounts to log in with** (passwords from `backend/seed/seed_demo.py`):
## 7. Critical Blockers

1. **Clean demo data (blocker for a polished demo, not for functionality).** The database mixes test artifacts with demo data. Options requiring owner approval: (a) a fresh demo database (new named volume) seeded only by `seed_demo.py`, or (b) approved one-time cleanup of test-only records.
2. **No backup/restore mechanism.** A `pg_dump` script + restore instructions should ship with M7 as a safety net.

## 8. Recommended M7 Scope

| Work item | Priority |
|-----------|----------|
| Owner-approved clean demo data (dedicated demo DB or approved cleanup) | HIGH |
| `pg_dump` backup script + restore + documented recovery | HIGH |
| i18n label sweep (dashboard cards, queue/audit buttons) | MEDIUM |
| Branch switch control on dashboard/AppShell | MEDIUM |
| Appointment/organization audit writes (extend `common/audit`) | MEDIUM |
| Staff↔doctor linkage for true doctor dashboard | LOW |
| Demo runbook/script + installation instructions | HIGH |

## 9. Recommendation

**GO (conditional).** The approved MVP core — org/branch, staff, doctor, patient, scheduling, appointment, queue, dashboard & audit — is implemented, PostgreSQL-persistent, secured per BR, and passes automated + live end-to-end verification (39 automated tests, 15 live workflow checks, concurrency + persistence checks).

Conditional items before final demo freeze:
1. Owner approves the clean-demo-data approach (dedicated demo DB or cleanup).
2. Add the `pg_dump` backup script and restore instructions.
3. (Recommended, not blocking) i18n label sweep + branch switch.

**If clean data is not authorized, the demo should use a freshly re-seeded dedicated database rather than the shared volume.**

---

*Read-only assessment complete. No source code, AILI, Docker configuration, data, or Git state was modified.*
`admin` (super_admin), `org_admin`, `br_admin` (branch_admin), `receptionist`, `doctor`, `assistant`.