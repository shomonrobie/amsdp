# AMSDP Demo Credential Sheet — V1.0

> **Date:** 2026-11-05  
> **Purpose:** Demo accounts for AMSDP MVP, one per RBAC role.  
> **Login URL:** http://localhost:3100/  
> **API Base:** http://localhost:8110 (Identity Service)

---

## All Accounts

| # | Role | Username | Password | Display Name | Organization | Branch |
|---|------|----------|----------|--------------|--------------|--------|
| 1 | **super_admin** | admin | *rotated — see `AMSDP_DEMO_PASSWORD_ADMIN` in `.env`* | Super Admin | org1 | br1 |
| 2 | **org_admin** | org_admin | org123 | Org Admin | org1 | br1 |
| 3 | **branch_admin** | br_admin | br123 | Branch Admin | org1 | br1 |
| 4 | **receptionist** | receptionist | rec123 | Receptionist | org1 | br1 |
| 5 | **doctor** | doctor | doc123 | Doctor User | org1 | br1 |
| 6 | **assistant** | assistant | ast123 | Assistant | org1 | br1 |

> **Rotated 2026-11-11, re-verified 2026-11-12 (finding B-12).** The `super_admin` password is
> deliberately no longer printed here: its earlier value had been published in tracked source files,
> so it was rotated in the running demo database and the new value now lives only in the gitignored
> `.env` (`AMSDP_DEMO_PASSWORD_ADMIN`). This sheet stays the single documented place for the local
> dev/demo seed accounts below — no other file in the tree repeats their passwords; the runtime
> source is always `.env` (key names in `.env.example`).

---

## Quick-Start

1. Open http://localhost:3100/ in a browser.
2. Enter **Username** `admin` and the super-admin password from `.env`
   (`AMSDP_DEMO_PASSWORD_ADMIN` — never committed; see `.env.example`).
3. Click **Login** — you will be redirected to the Dashboard.
4. Use the navigation bar to explore Patients, Doctors, Schedules, Appointments, and Queue.

---

## Role Capabilities (RBAC Summary)

| Role | Permissions |
|------|-------------|
| **super_admin** | Everything (`*`) |
| **org_admin** | Org/branch/staff management, all patient/doctor/schedule/appointment/queue ops, audit read |
| **branch_admin** | Branch/staff read, all patient/doctor/schedule/appointment/queue ops, audit read |
| **receptionist** | Patient CRUD, appointment CRUD, queue view/reorder |
| **doctor** | Patient read/search, schedule read, appointment read, queue view |
| **assistant** | Patient read/search, appointment read, queue view |

*Full permission matrix in `backend/identity/permissions.py` (BR §8).*

---

## Demo Data Pre-Loaded

- **Organization:** `UPH-001` (Uposhak Hospital) — *requires POST to `/api/v1/orgs`*
- **Branch:** `BR-UPH-001` (Main Branch) — *requires POST via organization service*
- **Sample Patients, Doctors, Schedules, Appointments, Queue entries** — *created via API calls during E2E test suite*

> **Note:** The in-memory stores are reset when containers restart. Use the E2E test (see below) to re-seed.

## Re-Seed Data (if needed)

```bash
cd /home/shomonrobie/amsdp
python -m pytest backend/tests/test_e2e.py -v
```

This creates org → branch → doctor → patient → staff → login → schedule → appointment → queue → audit entries.