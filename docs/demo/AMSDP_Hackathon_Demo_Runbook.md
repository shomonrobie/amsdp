# AMSDP Hackathon Demo Runbook

> **Milestone:** AMSDP-M7-HRR-2026-11-08 (M7 — Hackathon Readiness & Release Hardening)
> **Product:** AMSDP — Appointment Management System for Doctors & Patients
> **Version:** 1.0 · **Date:** 2026-11-08
> **Status:** Verified (see M7 report `docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md`)

---

## 1. System prerequisites

| Requirement | Minimum |
|---|---|
| CPU / RAM | 4+ cores, 16 GB RAM (development host used 4 GB VRAM / 16 GB RAM) |
| Docker | Docker Engine 24+ with `docker compose` v2 plugin |
| OS | Linux (Ubuntu 22.04+ verified) |
| Free host ports | `3100`, `8110–8117`, `5433` (AMSDP dev/demo); do **not** use `3000`, `5432` |
| Tooling | `git`; host `psql`/`pg_dump` optional (scripts use container clients) |

The Dev stack and Demo stack use the same host ports and must **not run simultaneously**.

---

## 2. Environment configuration

Configuration is environment-based (no application secrets in source):

| Variable | Purpose | Default (dev) |
|---|---|---|
| `AMSDP_DATABASE_URL` | SQLAlchemy DB URL used by every backend service | `postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp` — the password comes from `.env` |
| `AMSDP_JWT_SECRET` | HS256 JWT signing secret | dev fallback only; a real secret is required when `AMSDP_ENV != development` |
| `POSTGRES_DB` | Database created by the `db` container | `amsdp` (demo override: `amsdp_demo`) |

Credential-handling convention: demo passwords are read from the gitignored `.env`
(`AMSDP_DEMO_PASSWORD_<USERNAME>`) by `backend/seed/seed_demo.py` (dev/demo accounts).
They are not production credentials and are never written into application source files
or committed.

---

## 3. Docker Compose startup & shutdown

```bash
cd amsdp

# ---- Development stack (existing database amsdp, volume amsdp_pg_data) ----
docker compose -p amsdp up -d --build          # start
docker compose -p amsdp down                   # stop (data preserved)

# ---- Isolated demo stack (database amsdp_demo, volume amsdp_demo_pg_data) ----
docker compose -p amsdp -f docker-compose.yml down      # dev must be stopped first
_tools/init_demo_env.sh                                # one-shot demo init + start
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down  # stop demo
docker compose -p amsdp up -d --build          # resume development
```

The demo project is fully isolated by `docker-compose.demo.yml`: it overrides the `db`
service to `POSTGRES_DB=amsdp_demo` with its own volume `amsdp_demo_pg_data`, and points
every backend service at `amsdp_demo`. **The development database and volume are never
touched by the demo project.**

---

## 4. Database initialization & demo seeding

```bash
# Manual equivalent of _tools/init_demo_env.sh (demo stack must be up for db only)
cd backend
set -a; . ../.env; set +a                           # POSTGRES_PASSWORD + demo passwords
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo" \
  python -m alembic upgrade head                    # apply all migrations
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo" \
  python seed/seed_demo.py                          # idempotent seed
```

The seed is **idempotent** (re-runnable) and **self-refreshing**: re-running it on the
morning of the demo re-dates the seeded appointments/queue entries to that day's date
(demo-owned rows only, identified by `created_by='demo-seed'` / `added_by='demo-seed'`).

Seeded demo data: 1 hospital org (Uposhak Hospital), 2 branches, 6 staff (one per role),
5 doctors with schedules, 10 patients, 7 appointments across statuses, 2 queue entries.

---

## 5. Demo accounts & role mapping

All demo accounts belong to organisation **demo-org-001 / Uposhak Hospital**.

| Persona | Username | Password (from seed script) | Role | Demonstrable workflows |
|---|---|---|---|---|
| Receptionist | `receptionist` | see `backend/seed/seed_demo.py` | receptionist | register patient, search, book, check-in, walk-in, reorder queue |
| Doctor | `doctor` | see seed script | doctor | view queue, start/complete consultation (linked to Dr. Kamal Hossain) |
| Organisation Admin | `org_admin` | see seed script | org_admin | dashboard, audit review, branch switching, staff/org administration |
| Super Admin | `admin` | see seed script | super_admin | cross-org demo |
| Branch Admin | `br_admin` | see seed script | branch_admin | branch-scoped ops |
| Assistant | `assistant` | see seed script | assistant | read-only patient/appointment/queue view |

> Passwords are deliberately not reproduced in this runbook; they are defined once in
> `backend/seed/seed_demo.py` (and printed by the seed runner). This keeps credentials
> out of documentation and matches the existing dev/demo credential approach.

---

## 6. Access addresses & health checks

| Component | Address |
|---|---|
| Frontend (UI) | http://localhost:3100 |
| Identity | http://localhost:8110 |
| Organization | http://localhost:8111 |
| Patient | http://localhost:8112 |
| Doctor | http://localhost:8113 |
| Scheduling | http://localhost:8114 |
| Appointment | http://localhost:8115 |
| Queueing | http://localhost:8116 |
| Audit | http://localhost:8117 |
| PostgreSQL | localhost:5433 |

```bash
set -a; . .env; set +a                      # exports the demo passwords from .env
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3100/          # expect 200
curl -s -X POST http://localhost:8110/api/v1/staff/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"receptionist\",\"password\":\"$AMSDP_DEMO_PASSWORD_RECEPTIONIST\"}"                    # expect token JSON
docker compose -p amsdp_demo ps                                          # all services Up
```

(Demo passwords are never written here: they come from the gitignored `.env`
(`AMSDP_DEMO_PASSWORD_<USERNAME>`), which `_tools/init_demo_env.sh` and
`backend/seed/seed_demo.py` read. `.env.example` lists the key names.)

---

## 7. Step-by-step demo workflows

### Receptionist — register, book, check-in, walk-in, reorder

1. **Log in** as `receptionist` (Bangla/English toggle in the header). → Dashboard shows today's counts.
2. **Register a patient** → *Patients* → *Register*: name, mobile, sex. → Patient appears in list/search.
3. **Search an existing patient** → use the search box (e.g. `Jamila`) → expected: row match with mobile.
4. **Select doctor & branch** → header Branch selector shows the receptionist's branch (only one
   branch → no cross-branch switching possible; backend enforces it independently).
5. **Check availability** → *Schedules* → open a schedule → bookable slots for today.
6. **Book an appointment** → *Appointments* → patient, doctor, date, time → save.
   → Row status `BOOKED`; queue token assigned.
7. **Capacity enforcement** → keep booking the same doctor+slot until full → UI shows
   "capacity exceeded" (422); no over-booking.
8. **Register a walk-in** → *Queue* → *Walk-in* → patient + placement policy → queue entry + token.
9. **Check in an appointment** → *Queue* → *Check-in* → appointment → status `CHECKED_IN` + queue entry.
10. **Reorder the queue** → ↑/↓ buttons → positions update, position history recorded.
11. **Verify** on the Audit page (`queue.*`, `appointment.*` events) and the doctor's queue.

### Doctor — queue & consultation

1. **Log in** as `doctor` (staff ↔ doctor profile linked to Dr. Kamal Hossain).
2. Open **Queue** → doctor's own queue is pre-selected via the link; otherwise choose manually.
3. **Call next** → `Start` on the first `waiting` entry → status `in_consultation`.
4. **Complete** → status `completed`; appointment becomes `COMPLETED`; dashboard/audit updated.
   Only doctor + admin roles may start/complete consultations; receptionist is denied.

### Organisation Administrator — dashboard, audit, branch switch

1. **Log in** as `org_admin` → Dashboard shows live org totals.
2. **Switch branch** in the header (Branch 1 / Branch 2) → dashboard re-filters to that branch,
   and the Audit page follows the active branch.
3. **Review audit** → *Audit* lists events with actor/role/entity/before/after/reason/timestamp;
   filter by action/entity or search. Visit *Staff*, *Org*, *Branches* to manage.
4. **Verify isolation** → a receptionist token reading another branch's dashboard gets `403`;
   the branch selector never offers an unauthorized branch.

### Security & reliability spot-checks (for judges)

| Check | How | Expected |
|---|---|---|
| Unauthenticated API | `curl` any `/api/v1/**` without token | `401` |
| Expired / invalid token | tampered token | `401` |
| Receptionist cannot consult | attempt queue consultation action | `403` + recorded denial |
| Cross-org access | org A token on org B data | `403`/`404`, no data leak |
| Persistence | book, restart stack | row survives restart |
| Token uniqueness | 20 concurrent enqueues | 20 unique tokens |

---

## 8. Backup and restore

```bash
# Backup dev database (safe while running)
_tools/pg_backup.sh backups                      # writes backups/amsdp_dev_<ts>.sql.gz

# Verify a backup by restoring into an isolated throwaway database
_tools/pg_restore_test.sh backups/amsdp_dev_<ts>.sql.gz   # prints RESTORE VERIFIED, drops test DB

# Manual restore into a fresh named database (NEVER over the dev DB):
set -a; . .env; set +a                      # POSTGRES_PASSWORD from .env
gunzip -c backups/amsdp_dev_<ts>.sql.gz | \
  docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" amsdp-db-1 \
  psql -U amsdp -d <new_database_name>
```

Recovery precautions: backups use the version-matched `pg_dump` inside the Postgres 16
container; always restore into an empty/new database; the restore-test helper never
touches the development database.

---

## 9. Common errors & recovery

| Symptom | Cause | Recovery |
|---|---|---|
| `Address already in use` for 8110/3100/5433 | dev + demo running at once | stop the other project (`docker compose -p amsdp down`) |
| Login `401 invalid credentials` | wrong seed / password drift | re-run `seed_demo.py` (idempotent) |
| Dashboard empty on demo day | seeded appointments dated older than today | re-run `seed_demo.py`; demo-seeded rows re-date to today |
| `SET transaction_timeout` on restore | host `pg_dump` newer than server | use `_tools/pg_backup.sh` (container pg_dump) |
| Services restarted but data missing | wrong project/DB targeted | check `AMSDP_DATABASE_URL` + project name (`docker compose ps`) |

---

## 10. Pre-demo checklist

- [ ] Dev stack stopped, demo stack up: `docker compose -p amsdp_demo ps` all `Up`
- [ ] `_tools/init_demo_env.sh` executed on demo morning (dates refreshed)
- [ ] Frontend http://localhost:3100 loads (HTTP 200) and shows the language toggle
- [ ] Receptionist/Doctor/Org Admin logins all work
- [ ] Demo DB is isolated: `docker exec amsdp_demo-db-1 psql -U amsdp -d amsdp_demo -c '\l'`
      (only `amsdp_demo` etc.)
- [ ] Backup taken (`_tools/pg_backup.sh`) and restore-test passed
- [ ] Queue pre-seeded for doctor demo (T-DR002-001 waiting)

## 11. Post-demo cleanup (never affects development data)

```bash
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down   # stop demo
# Optional: discard the demo volume entirely for a next clean demo
docker volume rm amsdp_demo_amsdp_demo_pg_data                                        # demo data only
# Resume development
docker compose -p amsdp up -d --build
```

Development data lives on volume `amsdp_pg_data` and is untouched by every step above.

---

*Runbook verified against the M7 rehearsal; evidence in `AMSDP_M7_Hackathon_Readiness_Report.md`.*