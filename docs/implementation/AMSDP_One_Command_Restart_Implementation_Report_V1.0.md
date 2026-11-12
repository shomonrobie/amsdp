# AMSDP — One-Command Restart / Startability Implementation Report

> **Task ID:** `AMSDP-OPS-ONE-COMMAND-RESTART-2026-11-10`
> **Date:** 2026-11-10
> **Site:** `/home/shomonrobie/amsdp`
> **Status:** implementation complete and verified live in this session
> (IMPLEMENTED + TESTED + VERIFIED). Not ACCEPTED — acceptance is the Product
> Owner's act.
> **Where written:** `docs/implementation/` (`.clinerules` §11), see §11.
> **Companion report (separate task, same session):**
> `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md`

---

## 1. Script location and exact commands

**One script, one command:**

```bash
_tools/amsdp_stack.sh            # start or resume the whole application
```

| Task | Exact command |
|---|---|
| Start the full application (all stopped, some running, or all running) | `_tools/amsdp_stack.sh up` (a bare `_tools/amsdp_stack.sh` does the same) |
| Gracefully restart the full application, keeping data | `_tools/amsdp_stack.sh restart` |
| Stop the application, keeping containers and data | `_tools/amsdp_stack.sh stop` |
| Show service state, health and HTTP probes | `_tools/amsdp_stack.sh status` |
| Follow logs (all services, or one) | `_tools/amsdp_stack.sh logs [service]` |
| Rebuild images before starting | `AMSDP_BUILD=1 _tools/amsdp_stack.sh up` |
| Help | `_tools/amsdp_stack.sh help` |

Overrides (all optional): `AMSDP_COMPOSE_PROJECT` (default `amsdp`),
`AMSDP_READY_TIMEOUT` (default `180` s), `AMSDP_HEALTH_INTERVAL` (default `3` s),
`AMSDP_BUILD` (default `0`).

---

## 2. Files created or modified

| File | Change |
|---|---|
| `_tools/amsdp_stack.sh` | **New** executable script (mode `+x`), 263 lines: `up` / `restart` / `stop` / `status` / `logs` / `help` |
| `README.md` | **New section** `### 3. Running the AMSDP stack locally` appended at the end (numbered to follow the existing `### 1.` / `### 2.`): how to start, restart, stop, inspect status and logs, and what to do when startup fails. The Product Owner's existing uncommitted README edits were left untouched (byte-level detail in §8 item 7) |

Not modified: `docker-compose.yml`, `docker-compose.demo.yml`, `frontend/Dockerfile`,
any backend Dockerfile or service, any `.env` file (none exist in the tree), the
database, and every application feature. No new orchestration mechanism and no
deployment platform were introduced — the script drives the existing compose
project.

---

## 3. What the script does (and deliberately does not do)

1. **Guard checks first.** Docker present, compose v2 plugin present, daemon
   reachable; then a *project-conflict* check — the isolated demo project
   (`amsdp_demo`) publishes the same host ports, so the script refuses to start
   with a clear message instead of failing with a port bind error.
2. **Delegates orchestration to compose.** `docker compose -p amsdp up -d`
   (plus `--build` only when `AMSDP_BUILD=1`; missing images are built by compose
   itself). Compose is the single owner of the containers, so running the command
   again cannot create a second instance of anything.
3. **Respects dependencies and health.** `docker-compose.yml` already gates the
   backends on `db: condition: service_healthy` and the frontend on
   `identity: service_healthy`; the script does not re-implement that ordering.
4. **Waits for real readiness, not for "started".** It polls until *all* of:
   `pg_isready` inside the db container, `/health/ready` on each of the eight
   backends (host ports 8110–8117) and HTTP 200 from the frontend on port 3100.
   Only then does it print a status table and exit 0.
5. **Fails loudly.** On timeout it exits **1** and prints: the error, the full
   service state table, the list of failing probes, and the last 25 log lines of
   each failing service, plus the command to investigate further.
6. **Prints status.** A per-service table (state / compose health / live probe)
   and the access addresses.
7. **Never destroys data.** It performs no `down`, never removes a volume, never
   runs migrations, seeds, truncates or resets. `stop` is `docker compose stop`
   (containers and the `amsdp_amsdp_pg_data` volume are kept).
8. **Never prints secrets.** No environment dump, no `docker compose config`
   (which would print the JWT secret and the database URL), no credentials.
9. **Safe to repeat.** `up` on an already-running stack reports `Running` for
   every container and changes nothing.

---

## 4. Services started and health results

Stack (unchanged topology): `db` (PostgreSQL 16) + 8 backends (`identity`,
`organization`, `patient`, `doctor`, `scheduling`, `appointment`, `queuing`,
`audit`) + `frontend`.

Final state after the last `up` (verbatim from the script's own output):

```
==> Service status (compose project: amsdp)
  SERVICE        STATE     HEALTH    PROBE
  db             running   healthy   ok
  identity       running   healthy   ok
  organization   running   healthy   ok
  patient        running   healthy   ok
  doctor         running   healthy   ok
  scheduling     running   healthy   ok
  appointment    running   healthy   ok
  queuing        running   healthy   ok
  audit          running   healthy   ok
  frontend       running   healthy   ok
```

Independent HTTP checks performed outside the script:

```
GET /                        -> 200
GET /patients                -> 200
GET /api/v1/patients (no JWT) -> 401
/health/ready on 8110..8117  -> 200 (all eight services)
```

Container count after repeated `up`/`restart` cycles: **10** (exactly the ten
services, no duplicates).

---

## 5. Access addresses

| What | Address |
|---|---|
| Frontend (only public entry point) | <http://localhost:3100> |
| Backend services | `127.0.0.1:8110–8117` (identity 8110, organization 8111, patient 8112, doctor 8113, scheduling 8114, appointment 8115, queuing 8116, audit 8117); browsers reach them through the frontend proxy `/api/v1/*` |

---

## 6. Tests performed and results

Every scenario below was executed in this session; nothing is projected.

| # | Scenario | Result |
|---:|---|---|
| 1 | **Only the database running** — `_tools/amsdp_stack.sh status` | Correct partial-state report: `db running healthy ok`; the two existing-but-stopped containers shown `exited` / probe `FAILED`; services with no container shown `missing`. No error, no false success |
| 2 | **Cold start from db-only** — `_tools/amsdp_stack.sh up` | All nine missing services created, built and started; `all services ready after 2 probe(s)`; exit 0; 10/10 healthy |
| 3 | **Every service already running** — `_tools/amsdp_stack.sh up` again | Every container reported `Running`; `all services ready after 1 probe(s)`; container count still **10**; exit 0 (idempotent, no duplicates) |
| 4 | **Graceful restart** — `_tools/amsdp_stack.sh restart` | All ten containers restarted in place; `all services ready after 2 probe(s)`; 10/10 healthy; exit 0 |
| 5 | **Stop** — `_tools/amsdp_stack.sh stop` | All ten stopped gracefully (`Exited (0)`); 0 running; containers and volume kept; exit 0 |
| 6 | **Data while stopped** | Database restarted on its own volume and queried: `patients=1435` — the volume survives a full stop |
| 7 | **Failure path** — `AMSDP_READY_TIMEOUT=0 _tools/amsdp_stack.sh up` from a fully stopped stack | **exit 1** with `ERROR: not every service became ready within 0s`, the service-state table (`frontend … starting`), the failing probe (`frontend: http://127.0.0.1:3100/ not reachable`), the last 25 frontend log lines, and `The stack is NOT ready. Investigate with: _tools/amsdp_stack.sh logs <service>`. No misleading success message |
| 8 | **Recovery from a partially started stack** — `_tools/amsdp_stack.sh up` | `all services ready after 1 probe(s)`; 10/10 healthy; exit 0 |
| 9 | **Script syntax** — `bash -n _tools/amsdp_stack.sh` | clean |
| 10 | **Repeatability** — scripts run 6+ times in sequence | Same result each time; never created an extra container |

Readiness probes are the project's own: `pg_isready -U amsdp -d amsdp` inside the
db container, each backend's `/health/ready`, and the frontend root page.

---

## 7. Database preservation evidence

Counts read directly from the PostgreSQL container at four points of the cycle
(before, after two `up`s, after `restart`, and after `stop` → failed start →
`up`): identical every time.

| Table | Baseline (before) | After `up` ×2 | After `restart` | After `stop` + failure + `up` |
|---|---:|---:|---:|---:|
| `patients` | 1,435 | 1,435 | 1,435 | 1,435 |
| `appointments` | 45 | 45 | 45 | 45 |
| `organizations` | 42 | 42 | 42 | 42 |
| `audit_events` | 2,456 | 2,456 | 2,456 | 2,456 |

No migration, seed, truncate, reset or volume operation was performed at any
point. Query used (no password on the command line, connection inside the
container): `docker compose -p amsdp exec -T db psql -U amsdp -d amsdp -tAc "select count(*) from patients"`.

---

## 8. Remaining manual requirements and known limitations

1. **Docker must be running.** The script reports `the docker daemon is not
   reachable` with the fix, but starting Docker itself (`sudo systemctl start
   docker`) is outside the script: it needs root and is environment-specific.
2. **Content changes need a rebuild.** `up` reuses existing images (that is what
   makes it fast and safe); after a Dockerfile or dependency change use
   `AMSDP_BUILD=1 _tools/amsdp_stack.sh up`. Compose rebuilds automatically only
   when an image is missing.
3. **Dev and demo stacks cannot run together** (they publish the same host
   ports). The script detects the situation and tells you the exact command to
   stop the other project, rather than silently binding another port.
4. **No auto-healing / restart policy.** A crashed service is not restarted
   automatically; `_tools/amsdp_stack.sh status` shows it and `up` repairs it.
   Adding compose `restart:` policies was out of scope (it changes runtime
   behaviour of every service).
5. **No cloud, production, CI/CD or deployment work** — explicitly out of scope.
6. **Log rotation** is Docker's default; unbounded log growth on a long-lived
   stack is a known local-development limitation.
7. **`README.md` byte-level note.** The file had no trailing newline at EOF;
   appending a section necessarily adds one. The Product Owner's own uncommitted
   edit (the "Positioning and Patient-Facing Value" block and its reworded
   paragraph) is preserved verbatim — `git diff` shows the same text, only the
   final line terminator changed as an unavoidable consequence of appending.


---

## 9. Acceptance criteria checklist

| # | Criterion (from the task) | Status | Evidence |
|---:|---|---|---|
| 1 | One documented command starts the complete application | **VERIFIED** | `_tools/amsdp_stack.sh up`, documented in `README.md` §3 and §1 here; executed |
| 2 | The command works when all services are stopped | **VERIFIED** | Scenario 2 (db-only start) and scenario 8 (full stop → `up`) |
| 3 | The command works when some or all services are already running | **VERIFIED** | Scenario 3 (all running, no duplicates, 10 containers) and scenario 1/8 (partial) |
| 4 | Backend and frontend become reachable after startup | **VERIFIED** | `/health/ready` 200 on 8110–8117; `GET /` 200 and `GET /patients` 200 on :3100 |
| 5 | PostgreSQL data remains intact across restarts | **VERIFIED** | §7 — identical row counts at four points, including a full stop |
| 6 | A failed service produces a clear error rather than a misleading success message | **VERIFIED** | Scenario 7 — exit 1, named failing probe, log tail, no success banner |
| 7 | Stop and restart procedures are documented and tested | **VERIFIED** | `README.md` §3 table; scenarios 4 and 5 |
| 8 | Existing application tests and functionality remain unaffected | **VERIFIED** | No application code was changed by this task; unauthenticated API still 401 (auth intact); `backend/patient` suite 16/16 green and the frontend `next build` green in the same session (see the BanglaNameSense report §7) |
| 9 | One clear, executable script in a project-level location | **DONE** | `_tools/amsdp_stack.sh` (mode `+x`), same folder as the existing `pg_backup.sh`, `pg_restore_test.sh`, `init_demo_env.sh` |
| 10 | Uses the existing orchestration; no new platform | **DONE** | Only `docker compose -p amsdp up/restart/stop/ps/logs` is called |

---

## 10. Governance and skill compliance

| Requirement | How it was met (`.clinerules`) |
|---|---|
| §2 routing — Docker/deployment/infrastructure row | Read `docker-compose.yml`, `docker-compose.demo.yml`, `frontend/Dockerfile`, `frontend/next.config.js`, `_tools/*.sh`, `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` §3, `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md`; the script reuses the documented compose commands rather than inventing new ones |
| §3 non-negotiables | No secret printed (§3.1 of the script's own description), no schema/tenant/audit change, no authorization change, data never destroyed |
| §4 adapted infrastructure rules (`saas-cicd-workflow.md`: honest state, git safety) | Success is reported only after health probes pass; failure exits non-zero; no git state was touched |
| §5 skills | **No skill package is installed**; none used or claimed |
| §7 evidence standard | Every scenario number in §6 was executed; VERIFIED rows point at an independent artefact (HTTP status codes, SQL counts, exit codes) |
| §9 execution boundaries | The brief required verification of a live restart, so the stack was started/stopped in this session — with the owner's own compose project, on the owner's machine |
| §11 output location | This report is under `docs/`; no AMSDP document was written to `ai_factory/docs/`; the index was updated in the same task |

---

## 11. Deviations and open items

| ID | Item | Resolution |
|---|---|---|
| D-2 | The brief asked to append these results to the BanglaNameSense report | Implemented as this **separate** report so the two tasks stay independently identifiable and each keeps its own checklist; both reports cross-link. If a single combined document is required, it can be produced on request |
| D-6 | `git mv`-style staging is not applicable here; nothing staged | No file was staged, committed, pushed, merged or deployed |
| O-9 | Compose `restart:` policies / health-based auto-healing are not configured | Out of scope for this task; raised as a possible follow-up only |

Nothing was staged, committed, pushed, merged or deployed. All unrelated
uncommitted changes in the tree were preserved; no destructive git command was
run.

| PostgreSQL | container `amsdp-db-1`, host port `5433`, volume `amsdp_amsdp_pg_data` |
