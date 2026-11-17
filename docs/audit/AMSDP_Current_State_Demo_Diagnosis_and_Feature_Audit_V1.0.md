# AMSDP — Current-State Demo Diagnosis & Feature Audit V1.0

> **Task ID:** `AMSDP-DEMO-DIAGNOSIS-CURRENT-STATE-AUDIT-2026-11-15`
> **Date:** 2026-11-15 · **Branch:** `hackathon-mvp` · **HEAD:** `6bfbec4` (2026-11-14, *docs: add hackathon backlog and reconciliation proposal*)
> **Mode:** read-only diagnosis. **No application code, Compose file, migration, seed or database row was modified.**
> **Report location:** `docs/audit/` (`.clinerules` §11 — audit/acceptance evidence)
> **Scope:** why the hackathon demo does not work, why staff cannot sign in, and an honest
> IMPLEMENTED / TESTED / VERIFIED graded inventory of the feature surface (Parts A–G).

---

## Governance and Skill Compliance (`.clinerules` §6)

| Item | Value |
|---|---|
| Domains routed (§4) | Backend API/service endpoints · Authentication & sessions · Multi-tenant isolation · Database schema/migrations · Docker/deployment/ports · Dashboard · Queue/scheduling · Audit · Documentation |
| Documents read this task | `docs/governance/AMSDP_Docs_Index_V1.0.md` (first, per §12); `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`; `docs/product/AMSDP_MVP_SCOPE_V1.0.md` §5.1–5.11; `.github/workflows/ci.yml`; plus, from the same session, `docs/demo/AMSDP_Limitations_Report_V1.0.md` and `docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md` |
| Skills | **None installed.** Verified again in this task: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/` directory, no Cline skill configuration. The §4 table's *Skill slot* therefore resolved to governance documents in every row, exactly as §5 prescribes. No skill usage is claimed. |
| Non-negotiables honoured (§3) | No secret, token, JWT material, password or hash value is reproduced here — credentials were verified by returning **booleans only**. Cross-tenant behaviour was read, not exercised destructively. No audit row was deleted or rewritten. No schema change was made. Every claim below is tied to a command output or a `path:line` citation (§7). Nothing was restarted, reseeded or reconfigured. |
| Evidence grading (§7) | This report deliberately separates **IMPLEMENTED** (code reachable), **TESTED** (named tests exist in this tree), and **VERIFIED** (an independent artefact confirms it *today*). Because the runtime is down, almost nothing qualifies as **VERIFIED** today — that is stated per row rather than glossed over. |
| Revision 2 — owner correction (same task, 2026-11-15) | The owner stated that AMSDP had been configured to start automatically, that the demo users existed, and that sign-in had worked. Both halves were re-checked against the tree, the host and the database and **both are confirmed**; the verification also **corrected four statements** in Parts A–C (frontend "crash" → skipped in a partial recovery; restart-policy omission → documented deferral; a wrong inference from the audit trail, since login is not audited; and a six-hour journal-clock labelling error). All corrections are itemised in **Part G.3**, with the new evidence in G.4 and F.4 rows 19–26. The diagnosis itself is unchanged and now dated: the break is *after* `2026-11-12T20:46:41Z`. |
| Documents read in revision 2 | `docs/demo/AMSDP_Demo_Credentials_V1.0.md`, `docs/demo/AMSDP_Limitations_Report_V1.0.md` (both owner-controlled → read and cited, **not modified**, §11), `README.md` §3, `_tools/amsdp_stack.sh`, `_tools/init_demo_env.sh`, `backend/seed/seed_demo.py`, `backend/identity/main.py:100-240`, `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md`, `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | |

---

## Part A — Executive summary

**The demo does not work. There are three independent defects; any one of them alone is enough to
break it.**

| # | Defect | State | Consequence for the demo |
|---|---|---|---|
| **D1** | **`amsdp-frontend-1` is not running.** It stopped with **every** other container in a stack-wide shutdown at `2026-11-12T15:30:54Z` (exit `255`) and **was never started again**, while the other nine were restarted on `2026-11-14T15:47:4xZ`. No container declares a restart policy — a **documented, deliberate** deferral, not an oversight (see G.1, correction 2) | Broken | `http://localhost:3100` has **no listener**. The login page does not exist for the browser. This alone makes "staff cannot sign in" literally true. |
| **D2** | **Container↔container TCP on the Docker bridge is dropped host-wide** — every backend service times out reaching the database | Broken | All 8 backend services report `unhealthy`; `/health/ready` never completes; `POST /api/v1/staff/login` **never answers** (verified: no HTTP response in 25 s). Even a healthy frontend could not log in, because its rewrite proxy to `http://identity:8000` crosses the same broken path. |
| **D3** | The **demo stack (`amsdp_demo`) has never been started on this host** — only the dev stack `amsdp` exists, and the demo-owned queue data in that database is **empty** | Broken / drift | The runbook's isolated `amsdp_demo` database, volume and pre-seeded queue (`T-DR002-001 waiting`) do not exist here. A demo run today would use the polluted dev database with **0 queue entries** for `demo-org-001`. |

**What is *not* wrong** — established by direct measurement, so that remediation does not chase
phantoms:

- **The credentials are correct.** All six demo accounts exist, are `active`, sit in
  `demo-org-001 / demo-br-001`, and **every one of the six bcrypt hashes verifies against its
  `AMSDP_DEMO_PASSWORD_<USERNAME>` value in `.env`** (6/6 `True`). There is no password drift.
- **The database is healthy and the schema is current.** `amsdp-db-1` is `healthy`; the
  `alembic_version` is `e6c1a9b3d5f8`, which is the head of the 9-migration forward-only chain.
- **The configuration is correct.** Every service receives
  `AMSDP_DATABASE_URL=postgresql+psycopg2://amsdp:<password>@db:5432/amsdp` — service-name DNS,
  which is the right thing to do inside a Compose network — and DNS resolves
  (`db` → `172.19.0.2`). Both Compose stacks validate: `docker compose config --quiet` returns 0
  for the dev file and for the dev+demo overlay.
- **The login code path is correct** (`backend/identity/main.py:184-219`): throttle → user lookup →
  `bcrypt.checkpw` → status check → JWT. It fails at its **first** database touch, not in logic.

**Latent defect found while auditing (not the current outage, but a demo-showstopper the moment
the stack is fixed)** — **D4:** `frontend/pages/orgs.js` reads `sessionStorage` during render
without a `typeof window` guard (lines 8 and 12) while also declaring
`getServerSideProps` (line 4). The Organizations page therefore throws
`ReferenceError: sessionStorage is not defined` **on the server** and returns a 500 page.
This is not theoretical — it is in the retained container log at `2026-11-11T11:31:32Z`
(`⨯ ReferenceError: sessionStorage is not defined … at b (/app/.next/server/pages/orgs.js:1:1025)`).
It is the **only** page in the app missing that guard; `schedules.js`, `doctors.js`,
`branches.js`, `appointments.js`, `dashboard.js` and `lib/auth.js` all guard correctly.

**Root cause in one sentence:** the Docker daemon restarted on **2026-11-14 21:00 (+06)** and the
host firewall (`ufw` is **active**) is dropping the bridge **forward** path, so containers can no
longer reach each other; the frontend went down in the stack-wide stop of 2026-11-12 and was the one
service **not** brought back in the 2026-11-14 restart (nothing restarts a container on its own —
by design, see G.1); and the demo stack itself was never stood up on this host.

> **Owner correction incorporated (2026-11-15).** The workspace does contain a real, documented
> startability mechanism (`_tools/amsdp_stack.sh`, `README.md` §3, the one-command restart report), the
> six demo accounts **do** exist and **did** authenticate successfully as recently as
> `2026-11-12T20:46:41Z` (= 2026-11-13 02:46 local). Both facts are confirmed in **Part G**, which also
> corrects four statements in Parts A–C. Nothing in Part G weakens the diagnosis: it dates it.

**Repair order (each step gated by the previous):** D2 → D1 → D3 → D4. Detail and exact commands
in Part F.

## Part B — Verified runtime state

### B.1 Containers (project `amsdp` = the **dev** stack)

| Container | Status | Health |
|---|---|---|
| `amsdp-db-1` | Up 14 hours | **healthy** |
| `amsdp-identity-1` | Up 14 hours | **unhealthy** |
| `amsdp-organization-1` | Up 14 hours | **unhealthy** |
| `amsdp-patient-1` | Up 14 hours | **unhealthy** |
| `amsdp-doctor-1` | Up 14 hours | **unhealthy** |
| `amsdp-scheduling-1` | Up 14 hours | **unhealthy** |
| `amsdp-appointment-1` | Up 14 hours | **unhealthy** |
| `amsdp-queuing-1` | Up 14 hours | **unhealthy** |
| `amsdp-audit-1` | Up 14 hours | **unhealthy** |
| `amsdp-frontend-1` | **Exited (255) 2 days ago** | n/a |

`docker compose ls -a` lists exactly two projects on this host: **`amsdp`** (`exited(1), running(9)`)
and **`n8n`**. There is **no `amsdp_demo` project** — the isolated demo stack from the runbook has
not been created here.

Frontend container facts: `ExitCode=255`, `OOMKilled=false`, `RestartCount=0`,
`StartedAt=2026-11-12T07:34:05Z`, `FinishedAt=2026-11-12T15:30:54Z`, `Error=""`.
The last log line is a Node deprecation warning at `07:34:39Z`; **nothing is logged at the moment
of exit**, so the precise terminating signal is not provable from retained logs.

**What the timestamps actually say (refined in Part G.4).** `FinishedAt=15:30:54.655Z` on the
frontend is mirrored, within **94 ms**, by all nine other containers (`15:30:54.56Z … .65Z`), with
`ExitCode=0` on the nine and `255` on the frontend. That is a **simultaneous stack-wide stop**
(daemon stop / host shutdown), **not** a frontend crash. Nine of the ten were started again at
`2026-11-14T15:47:43–50Z`; the frontend's `StartedAt` still reads `07:34:05Z` on 11-12, which proves
**no start has even been attempted** since. So D1 is a *partial recovery that skipped the frontend*,
not a crash loop.

On restart policies: `RestartPolicy.Name=no` for all ten containers, and **neither
`docker-compose.yml` nor `docker-compose.demo.yml` contains a `restart:` key at all** — so no
service can self-heal after a crash or a host reboot. This was **not an oversight**: the deferral is
recorded in `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md:642-643` ("deliberate: a
restart policy is a deployment decision for whatever supervisor…"), in the same report's line 724
table, and in `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` (§8 item 4
"No auto-healing / restart policy", open item O-9). The intended substitute is the **manual**
`_tools/amsdp_stack.sh` — see G.1.

### B.2 Host ports

| Port | Listener | Expected by runbook |
|---|---|---|
| `3100` | **none** | Frontend — *missing* |
| `5433` | yes | PostgreSQL dev |
| `8110`–`8117` | yes (all eight) | identity … audit |

The backend services are *listening*; they simply cannot serve anything that needs the database.

### B.3 Database (dev DB `amsdp`, reached from the host on `127.0.0.1:5433`)

| Fact | Value |
|---|---|
| `alembic_version` | `e6c1a9b3d5f8` = head of `5f3fce6757cf → ccf34da72c1b → c7d3601e2486 → 9d8a1f2b3c4d → 3c8e5d0a9b2f → a1f2b3c4d5e6 → b7c1e4d90a52 → d4b2c8e1f7a3 → e6c1a9b3d5f8` |
| Migration files | 9 (`backend/alembic/versions/`) |
| `staff_users` total | **559** rows |
| `staff_users` in `demo-org-001` | 6 (exactly the six demo accounts) |
| `patients` in `demo-org-001` | **18** (runbook documents 10) |
| `appointments` in `demo-org-001` | **9** (runbook documents 7) |
| `doctors` in `demo-org-001` | 5 |
| `queue_entries` in `demo-org-001` | **0** (runbook requires 2, incl. `T-DR002-001 waiting`) |
| `queue_entries` overall | 4 rows, **all in test orgs**: `dqds-org` 2, `m5-org` 1, `m9b-org` 1 |
| `appointments` overall | `m5-org` 60, `m9b-org` 13, `demo-org-001` 9 |
| `audit_events` | 3,484 rows; latest `2026-11-12 20:46:41Z`; per-day 11-09: 1418, 11-10: 1039, 11-11: 510, 11-12: 517 |
| `schedules` (`demo-org-001`) | 5 |
| `appointments` date range (`demo-org-001`) | `2026-11-11` … `2026-11-12`, **0 dated today (2026-11-15)** |

**The date range is a live demo hazard the runbook itself warns about:** even after the network is
repaired, the dashboard and queue will look empty because the demo appointments are dated
2026-11-11/12. `seed_demo.py` is self-refreshing and re-dates demo-owned rows (`created_by='demo-seed'`)
to the current day — so **it must be re-run on demo morning**, per runbook §4 and the pre-demo
checklist.

Reading: the dev database has been used as a test target (`m5-org`, `m9b-org`, `dqds-org` fixtures)
and the demo seed has been re-run into it more than once (18 ≠ 10 patients). **It is not a clean
demo dataset**, and its queue — the centrepiece of the demo — is empty.

### B.4 Git working tree

Branch `hackathon-mvp`, HEAD `6bfbec4`. Uncommitted: `M frontend/styles/global.css`;
untracked `_tools/` and `docker-compose.demo.yml`. **These were not touched.**

### B.5 Compose level

Both stacks parse and resolve: `dev_config_rc=0`, `demo_config_rc=0`. Dev DSN
`…@db:5432/amsdp`; demo override `…@db:5432/amsdp_demo` with `POSTGRES_DB=amsdp_demo` and volume
`amsdp_amsdp_demo_pg_data`. The demo overlay is well-formed — it has simply never been run here.

## Part C — Root cause: why the demo fails and why sign-in fails

### C.1 Timeline (all timestamps as recorded on this host)

| When | Event | Evidence |
|---|---|---|
| 2026-11-11 09:18Z | identity service process start; `/health/ready` **200** | identity app log |
| 2026-11-11 11:31:32Z | frontend SSR 500 on `/orgs` — `ReferenceError: sessionStorage is not defined` | frontend app log |
| 2026-11-12 07:34:05Z | `amsdp-frontend-1` (re)starts, becomes Ready | container `StartedAt` |
| 2026-11-12 15:28:57Z | **last successful** `/health/ready` 200 (identity) — last proof the DB was reachable | identity app log |
| 2026-11-12 15:30:54Z | **all ten containers stop within 94 ms** — a stack-wide stop (daemon stop / host shutdown), not a crash: `ExitCode=0` on the nine, `255` on the frontend | container `FinishedAt` ×10 |
| 2026-11-12 20:46:41Z | last audit-writing **authenticated** action (`staff.created`, `actor_role=super_admin`, org-1) — proves a valid token existed at 2026-11-13 02:46 local (G.2) | `audit_events` |
| 2026-11-12 21:31+06 | dockerd logs Supabase network endpoint failures (*unrelated* project) | dockerd journal |
| 2026-11-14 12:48:51+06 | `docker.service` stop/restart **#1** | dockerd journal |
| 2026-11-14 12:49:00+06 | dockerd: **"Deleting nftables IPv4 rules" → exit status 1** | dockerd journal |
| 2026-11-14 12:49:03+06 (`06:49:03Z`) | `amsdp-db-1`'s **previous stop** — restart #1 took the stack down; it later ran again before the 11-14 restart below | container `FinishedAt` |
| 2026-11-14 21:00:10+06 | `docker.service` stop/restart **#2** | dockerd journal |
| 2026-11-14 21:00:11+06 | dockerd: **nftables rule deletion fails again, exit status 1** | dockerd journal |
| 2026-11-14 21:00:13+06 | Docker daemon **Started** — this is the runtime boundary of the current outage | dockerd journal |
| 2026-11-14 21:47:43–50+06 (`15:47:4xZ`) | **nine of ten** containers start; **`amsdp-frontend-1` is not among them** — its `StartedAt` is still 11-12, so no start was even attempted | container `StartedAt` |
| since then | only `/health` (liveness) 200s; **no** `/health/ready` success; every service `unhealthy` | identity log + `docker ps` |

> **Clock note (corrected 2026-11-15).** `journalctl` was read without `--utc`, so journal rows are
> **local time (+06)**; container timestamps are **UTC**. The earlier draft suffixed the journal rows
> with `Z`, which made them look six hours later than they are. The two clocks reconcile exactly on
> the DB stop: `12:49:03+06` = `06:49:03Z`. Both were re-checked in this session; the corrected
> container view is in **G.4**.

The daemon restart is the **boundary**: before it the stack was serving (200s on `/health/ready`,
audit rows being written); after it, no container has ever reached the database again. Note that in
that final generation the frontend had already been absent since 2026-11-12, so the 2026-11-14
restart could restore *API* reachability at best — the login page needed a tenth container that
nothing started.

### C.2 The network failure, measured five ways (all on this host, 2026-11-15)

| Probe | From → To | Result |
|---|---|---|
| 1 | `amsdp-identity-1` → `db:5432` (TCP connect) | **`TimeoutError`** — *not* refused |
| 2 | `amsdp-identity-1` → `127.0.0.1:8000` | **CONNECTED** (own loopback, trivially) |
| 3 | `amsdp-audit-1` → `identity:8000` | **`TimeoutError`** |
| 4 | `amsdp-audit-1` → `172.19.0.1:5433` (host gateway, *published* port) | **CONNECTED** |
| 5 | DNS inside container: `db` | resolves to `172.19.0.2` — **name resolution is fine** |

**The signature is decisive:** packets to the *host's published ports* work; packets to *another
container's* IP/port hang until timeout, and never produce a RST. That is a **dropped-forwarded-
packet** profile, not an application, DNS, credential, port-binding or Compose problem. Both
containers are on `amsdp_default` (`172.19.0.0/16`), so this is not a "different networks" mistake
either.

### C.3 Host facts that explain it

| Fact | Value | Meaning |
|---|---|---|
| `net.ipv4.ip_forward` | `1` | kernel forwarding is on — not the cause |
| `net.bridge.bridge-nf-call-iptables` | `1` | bridge traffic **is** subject to netfilter |
| `ufw` | **active** | a host firewall is loaded and is evaluating forwarded traffic |
| `iptables -S` / `nft list ruleset` as this user | **permission denied (needs root)** | the exact offending rule could not be read |
| dockerd at shutdown/start | **fails to delete its nftables IPv4 rules (exit 1)** twice | docker and the host ruleset are fighting over the same tables — the classic ufw/iptables-nft coexist pattern |

**Honest limitation (§7):** the *symptom* is VERIFIED (five independent probes). The *exact*
offending rule is a strong inference, because reading the ruleset requires root and no privileged
command was run. Part F gives the non-destructive root check that closes this gap.

### C.4 The sign-in chain, broken at two of its three hops

```
browser ──1──► localhost:3100 (frontend)         ✗ NO LISTENER  ← D1, certain
                    │
                    └──2──► next rewrites ──► http://identity:8000   ✗ cross-container (D2)
                                      │
                                      └──3──► db:5432 (PostgreSQL)    ✗ cross-container (D2)
```

- **Hop 1 fails outright**: port 3100 has no listener because the container exited on 2026-11-12.
- **Hops 2 and 3 would also fail** once the frontend were restarted, because both cross the bridge.
- **A direct login attempt confirms it end-to-end**: a single controlled
  `POST /api/v1/staff/login` with valid `receptionist` credentials against the *host-published*
  `http://localhost:8110/api/v1/staff/login` returned **HTTP `000` after 25 s** — i.e. the request
  was accepted by the socket and then never answered, exactly as a hung DB connect predicts. The
  same credentials verify correctly in isolation (bcrypt, 6/6), so **the failure is environmental,
  not credential, not authorization, not business-logic.**

### C.5 Why it looks like "credentials don't work"

Three misleading symptoms converge on the same user-visible message:

1. No frontend at all → the operator may be reaching a stale browser tab or the previous demo's
   cached page, and the resulting failure looks like a login rejection.
2. `docker ps` shows the backend services **Up** (they are; their process is alive) while `health`
   says `unhealthy` — easy to read as "the app is up, so my password must be wrong".
3. The audit trail shows no authentication event since `2026-11-12T20:46:41Z` — but **login is not
   audited at all** (`backend/identity/main.py:184-219` writes no audit row on success), so absence
   of rows proves nothing about login attempts. *(Corrected in G.3: my first draft read this absence
   as evidence that no attempt had reached the service. It is not.)* What the audit trail **does**
   prove is that the last successful *audit-writing* authenticated action was at `20:46:41Z`, and
   that the current failure is at the transport layer — `HTTP 000` after 25 s, no TCP answer from
   `identity:8000` (C.2 probe 3) — not a rejection.
4. The demo credential sheet still prints five of the six passwords in plain text
   (`docs/demo/AMSDP_Demo_Credentials_V1.0.md:15-19`) and points the operator at
   `http://localhost:3100` — a URL with no listener today — so "follow the docs and log in" fails
   exactly as written.

## Part D — Feature inventory matrix

**Grading key (§7):** `IMPLEMENTED` = code is reachable (endpoint decorated / page exists);
`TESTED` = named tests exist in this tree (count shown); **no row is `VERIFIED` today** because the
stack cannot serve a request — the last successful authenticated call was 2026-11-12.

Routes counted from the actual decorator map: **64 route declarations** —
`appointment` 17 (`main.py` 10, `tracking.py` 4, `dashboard.py` 3), `organization` 12 (`main.py` 9,
`notification_config.py` 3), `queuing` 9 (`main.py` 6, `recovery.py` 2, `display.py` 1),
`scheduling` 5, `patient` 4, `identity` 7 (`main.py` 3, `routes.py` 4), `doctor` 4, `audit` 2,
gateway `app/main.py` 1, shared `common/health.py` 2 (liveness + readiness) and `common/auth.py` 1.

### D.1 MVP scope §5.1–5.11

| MVP item | Backend evidence | Frontend | Seed / demo data | Grade |
|---|---|---|---|---|
| **§5.1 Organizations & branches** (create/list/get, per-org settings) | `organization/main.py:95,119,133,149` (orgs) + `:181,210,225,241` (branches) + `:274` | `pages/orgs.js` **SSR-broken (D4)**, `pages/branches.js` | 1 org; **3 branches** (runbook documents 2) | IMPLEMENTED; orgs page **BROKEN** |
| **§5.2 Authentication / JWT / RBAC** | `identity/main.py:129` (`/staff/login`), `:184` (verify), `:222` (`/staff/me`); `identity/routes.py:31,49,74,128` (staff admin); `common/permissions.py` | `pages/index.js` (login form), `lib/auth.js` (guard + `h()` helper) | 6 staff users, all roles | IMPLEMENTED · TESTED (`test_identity` 18, `test_security` 25) — **runtime blocked** |
| **§5.3 Patients** (create/list/get/update, Bangla name handling) | `patient/main.py:111,152,174,192` | `pages/patients.js` | 18 patients (expected 10) | IMPLEMENTED · TESTED (`test_patient` 16, `test_patient_age` 13) |
| **§5.4 Doctors** (create/list/get/patch) | `doctor/main.py:57,92,118,136` | `pages/doctors.js` | 5 doctors | IMPLEMENTED · TESTED (`test_doctor` 14) |
| **§5.5 Scheduling** (create/list/patch schedules, availability) | `scheduling/main.py:58,81,93,104,128` | `pages/schedules.js` | schedules for 5 doctors | IMPLEMENTED · TESTED (`test_scheduling` 22) |
| **§5.6 Appointments lifecycle** (book, get, list, status, cancel, reschedule, transfer, no-show) | `appointment/main.py:195,287,308,324,366,377,439,510,522,562` | `pages/appointments.js` | 9 (expected 7) | IMPLEMENTED · TESTED (`test_appointment` 13, `test_reschedule` 6) |
| **§5.7 Walk-in registration** | `appointment/main.py` walk-in POST (in the 10 above) + `queuing/main.py:146` (enqueue) | `pages/appointments.js` (walk-in flow) | none pre-seeded | IMPLEMENTED · TESTED (`test_e2e` 21) |
| **§5.8 Queue management** (today board, status transitions, reorder, recovery, missed turn, display) | `queuing/main.py:108,146,213,294,366,416`; `queuing/recovery.py:138,187`; `queuing/display.py:127` | `pages/queue.js`, `pages/queue-display/` | **0 entries for demo org** — demo centrepiece unpopulated | IMPLEMENTED · TESTED (`test_queue` 20) — **demo data gap** |
| **§5.9 Token issuance** (per-doctor daily sequences, continuous numbering) | `queuing/main.py` enqueue + `queue_sequences` migration `c7d3601e2486`/related | shown on queue + appointment pages | no tokens today | IMPLEMENTED · TESTED |
| **§5.10 Audit trail** (query by org/target, append-only) | `audit/main.py:85,101`; writer `common/audit.py` | `pages/audit.js` (+ `pages/staff.js`) | 3,484 rows, latest 2026-11-12 | IMPLEMENTED · TESTED (`test_audit` 13, `test_denial_audit` 8) |
| **§5.11 Bangla / English i18n, responsive UI** | n/a (client-side) | `lib/i18n.js`, `lib/bangla-name-sense/` (4 test files) | BN/EN strings present | IMPLEMENTED · partial TESTED (matcher only) — **no a11y tests, no page tests** |

### D.2 Capabilities present beyond §5 (hackathon extras)

| Capability | Backend evidence | Frontend | Grade |
|---|---|---|---|
| **Dashboard aggregates** (operational day counts) | `appointment/dashboard.py:17,74,138` | `pages/dashboard.js` | IMPLEMENTED · TESTED (`test_dashboard` 6) |
| **Public tracking tokens (PQV)** — issue/revoke/verify, tokenised public lookup | `appointment/tracking.py:60,117,147,215` | `pages/track/` | IMPLEMENTED · TESTED (`test_tracking_tokens` 17) |
| **Notification configuration** (per-org channel settings) | `organization/notification_config.py:60,78,134` | `pages/notifications.js` | IMPLEMENTED · untested by a dedicated file |
| **Platform admin (super_admin cross-org)** | `common/permissions.py` + platform-admin guards, `identity` staff routes | `pages/staff.js` | IMPLEMENTED · TESTED (`test_platform_admin` 16) |
| **Login throttling** | `identity/main.py:184-219` (pre-check) | n/a | IMPLEMENTED · covered by `test_security` |
| **Data-quality / duplicate detection (DQDS)** | `dqds` logic + migration `a1f2b3c4d5e6` | patients page warning | IMPLEMENTED · TESTED (`test_dqds` 24) |
| **Gateway / per-service health probes** | `app/main.py:20`, `common/health.py:35,39` | n/a | IMPLEMENTED · **failing in this environment** (Part C) |

**Counts:** 64 route declarations · 14 frontend pages/routes (incl. `_app.js`, `api/`,
`queue-display/`, `track/`) · 9 migrations · 19 backend test files / 311 test functions ·
4 frontend test files / matcher-only.

## Part E — Test & CI inventory

### E.1 Backend suite

19 test files, **311 test functions**, all under `backend/` and run by `python -m pytest -q` from
`backend/` with `PYTHONPATH=backend`:

| File | Tests | | File | Tests |
|---|---:|---|---|---:|
| `tests/test_sequence3.py` | 26 | | `tests/test_sequence4.py` | 13 |
| `tests/test_security.py` | 25 | | `tests/test_patient_age.py` | 13 |
| `tests/test_dqds.py` | 24 | | `audit/tests/test_audit.py` | 13 |
| `scheduling/tests/test_scheduling.py` | 22 | | `appointment/tests/test_appointment.py` | 13 |
| `tests/test_e2e.py` | 21 | | `tests/test_denial_audit.py` | 8 |
| `queuing/tests/test_queue.py` | 20 | | `tests/test_dashboard.py` | 6 |
| `organization/tests/test_organization.py` | 20 | | `appointment/tests/test_reschedule.py` | 6 |
| `identity/tests/test_identity.py` | 18 | | | |
| `tests/test_tracking_tokens.py` | 17 | | | |
| `tests/test_platform_admin.py` | 16 | | | |
| `patient/tests/test_patient.py` | 16 | | | |
| `doctor/tests/test_doctor.py` | 14 | | | |

**They are integration tests, not unit tests.** `common/database.py` reads
`AMSDP_DATABASE_URL`, so the suite requires a **live PostgreSQL with the Alembic chain applied** —
it cannot run without one, and it writes rows (that is how the `m5-org` / `m9b-org` / `dqds-org`
fixtures and the 559 staff users in the dev database came to exist).

### E.2 Frontend suite

4 `node:test` files, all under `lib/bangla-name-sense/` (the Bangla name normalisation/matching
component). There is **no** test for any page, any component under `components/`, `lib/auth.js`,
`lib/i18n.js`, or the login flow — and no E2E framework (no Playwright/Cypress dependency in
`frontend/package.json`). Also no lint script. **Consequence: defect D4 (the `/orgs` SSR crash)
could not have been caught by the current test suite, and nothing in CI would catch a regression of
it.**

### E.3 CI pipeline

`.github/workflows/ci.yml` (owner decision Q-5, 2026-11-12) — two independent jobs, triggered on
push to `main`/`hackathon-mvp`, on pull requests, and manually:

- **backend** — `ubuntu-latest`, Python 3.13, `postgres:16-alpine` service published on **5433**
  (the same port the dev stack publishes), `alembic upgrade head` from `backend/`, then
  `python -m pytest -q`. Credentials are CI-only literals on an ephemeral service container.
- **frontend** — Node 22, `npm ci`, `npm run build`, `npm test`.

**Honest status:** the workflow file explicitly records that **the first pipeline run failed**
(`python -m alembic` resolving the `backend/alembic/` namespace package instead of the installed
console script) and was corrected to `alembic upgrade head`. Whether the current `HEAD` is green on
GitHub cannot be established from this host without querying GitHub, so **no green-pipeline claim is
made here** (§7).

### E.4 Tests were deliberately not executed in this audit

Rationale, stated so it is not mistaken for an omission:

1. The suite is **integration-level and destructive by nature** (it inserts orgs/users/appointments
   into whatever `AMSDP_DATABASE_URL` points at). Pointing it at the only reachable database — the
   dev `amsdp` DB that holds the demo data — would have polluted the very dataset under audit.
2. Backend containers cannot reach the DB (Part C), so an in-container run would fail for
   environmental reasons and prove nothing about the code.
3. `.clinerules` §9 forbids running servers/test suites unless the owner asks. This task was
   scoped as read-only diagnosis.

**Therefore every "TESTED" mark in Part D means "named tests exist in this tree", not "tests were
run today".** Any acceptance claim must be re-established after Part F steps 1–3 by running the
suite against a throwaway database (e.g. the CI recipe: `postgres:16-alpine` on 5433, fresh volume).

## Part F — Gaps, prioritised remediation and evidence

### F.1 Remediation plan (destructive steps left to the owner — nothing here was executed)

| Priority | ID | Action | Why | Effort |
|---|---|---|---|---|
| **P0** | R-1 | Restore Docker bridge **forward** traffic on the host (firewall) | Fixes D2 — without it nothing else matters | 10 min, **needs sudo** |
| **P0** | R-2 | Restart the stack and the frontend; confirm `healthy` + port 3100 | Fixes D1 (and proves R-1) | 5 min |
| **P0** | R-3 | Choose **one** database: run the isolated `amsdp_demo` stack per the runbook, or consciously demo on the dev DB | Fixes D3 (`amsdp_demo` never existed here) | 15 min |
| **P0** | R-4 | Seed **and verify the queue** for `demo-org-001` (currently 0 entries) | The demo's centrepiece has no data | 5 min |
| **P1** | R-5 | Fix `frontend/pages/orgs.js` SSR guard | Fixes D4 — `/orgs` currently 500s | 10 min |
| **P1** | R-6 | Add `restart: unless-stopped` to every service in `docker-compose.yml` (and the demo overlay), **or** install the supervisor the hardening report deferred to (a systemd user unit running `_tools/amsdp_stack.sh up` at boot) | Nothing on this host restarts a container: `RestartPolicy=no` ×10. This is how the frontend stayed absent for 3 days. The omission is a **documented deferral** (hardening report `:642-643`, one-command report §8 item 4 / O-9), so R-6 *closes* a known gap rather than correcting an oversight — see G.1 | 15 min |
| **P1** | R-7 | Add `timeout=` + a short-circuit to the `/health/ready` probe, and log the failing dependency | The healthcheck hangs 5 s and reports `unhealthy` with **no diagnostic** — the single biggest obstacle to diagnosing this outage | 20 min |
| **P2** | R-8 | Give the demo its own clean data (18 patients ≠ 10 documented; `m5-org`/`m9b-org`/`dqds-org` test noise visible to `super_admin`) | Judging credibility | 30 min |
| **P2** | R-9 | Add at least one frontend page test / a11y check so SSR-only crashes like D4 can be caught | Prevents a repeat of D4 | 1–2 h |
| **P2** | R-10 | Confirm the CI pipeline is green on `HEAD` | No green claim can be made from this host | 5 min |

### F.2 R-1 — the firewall step, with the read-only root check first

The symptom is proven; the *rule* is not, because reading netfilter state needs root. Run the
diagnostic first (read-only), then the least-invasive candidate repair, verifying after each:

```bash
# --- 1. diagnose (read-only, needs sudo) ---
sudo ufw status verbose                       # is default forward policy DROP / REJECT?
sudo iptables -S FORWARD | head -30           # look for a DROP/REJECT with no docker ACCEPT above it
sudo nft list ruleset | sed -n '/chain FORWARD/,/^\s*}/p'
docker network inspect amsdp_default --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'

# --- 2. candidate repairs, in increasing invasiveness ---
sudo systemctl reload ufw && sudo systemctl restart ufw   # cheapest: make ufw re-insert docker rules
# if still broken, allow routed traffic inside the compose subnet only:
sudo ufw route allow from 172.19.0.0/16 to 172.19.0.0/16
# last resort, temporary (lost on daemon restart), per bridge interface:
sudo iptables -I FORWARD -i br-<id> -o br-<id> -j ACCEPT

# --- 3. verify after EACH attempt (must print OK, not TimeoutError) ---
docker exec amsdp-identity-1 python -c \
  "import socket;socket.create_connection(('db',5432),5);print('OK')"
```

> ⚠️ R-1's repair commands are **standard remedies, not verified in this environment** — the
> offending rule could not be read without root, so treat the fix list as a decision tree, not a
> prescription. The *verification* command above is the gate: do not proceed until it prints `OK`.

### F.3 R-2…R-5 — exact gates

```bash
# R-2: bring everything up, then wait for health (not merely "Up")
docker compose -p amsdp up -d
watch -n2 'docker compose -p amsdp ps --format "table {{.Name}}\t{{.Status}}"'
curl -s -o /dev/null -w 'identity ready=%{http_code}\n' http://localhost:8110/health/ready   # want 200
ss -ltnp | grep -E ':3100'                                                                  # want a listener
curl -s -o /dev/null -w 'frontend=%{http_code}\n' http://localhost:3100/                     # want 200

# R-2 smoke: ONE login with a demo account, token must NOT be echoed
curl -s -o /tmp/login.json -w 'login=%{http_code}\n' -X POST http://localhost:8110/api/v1/staff/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"receptionist\",\"password\":\"$AMSDP_DEMO_PASSWORD_RECEPTIONIST\"}"

# R-3: isolated demo stack (runbook §3) — dev stack down first, per the runbook checklist
docker compose -p amsdp down
_tools/init_demo_env.sh                        # one-shot demo init + start
docker compose -p amsdp_demo ps                # every service Up (and healthy)

# R-4: seed is idempotent and re-dates demo-owned rows to today (created_by/added_by='demo-seed')
cd backend && set -a; . ../.env; set +a
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo" \
  python -m alembic upgrade head
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo" \
  python seed/seed_demo.py
docker exec amsdp_demo-db-1 psql -U amsdp -d amsdp_demo -c \
  "select token, status from queue_entries where organization_id='demo-org-001';"  # expect T-DR002-001 waiting
```

Mandatory because the existing demo rows are **stale-dated** (`2026-11-11`…`2026-11-12`, zero rows
dated today): without a re-seed on demo morning, the dashboard and queue render empty even on a
perfectly healthy stack.

**R-5 (D4) fix, precisely:** the bug is a *render-time* `sessionStorage` read — `T()` at
`frontend/pages/orgs.js:5` already guards it, but `usr()` at line 6 and the header object at line 10
do not, and both execute during SSR because line 4 declares `getServerSideProps`. The minimal,
convention-matching repair is to mirror `lib/auth.js`:

```js
function usr(){ try { if (typeof window === 'undefined') return {}; return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}') } catch(e) { return {} } }
// and inside the component, before any sessionStorage use:
const token = typeof window !== 'undefined' ? sessionStorage.getItem('amsdp_token') : null;
```

**Not applied** — this audit is read-only.

### F.4 Evidence appendix

Every claim above comes from one of these, captured on this host on 2026-11-15. Commands are listed
so the owner can re-run them; outputs are summarised here because `/tmp` is ephemeral.

| # | Command / probe | Result (verbatim where short) |
|---|---|---|
| 1 | `docker ps -a --format …` | 9 backend containers `Up 14 hours` / `(unhealthy)`, `db` `(healthy)`, `amsdp-frontend-1` `Exited (255) 2 days ago` |
| 2 | `docker inspect` on the frontend | `ExitCode=255`, `OOMKilled=false`, `RestartCount=0`, `RestartPolicy.Name=no`, `FinishedAt=2026-11-12T15:30:54Z` |
| 3 | `grep -n 'restart:' docker-compose.yml docker-compose.demo.yml` | **no matches** in either file |
| 4 | `docker compose ls -a` | only `amsdp` (`exited(1), running(9)`) and `n8n` — **no `amsdp_demo`** |
| 5 | `ss -ltn` | `5433`, `8110`–`8117` present; **`3100` absent** |
| 6 | `docker compose config --quiet` (dev, and dev+demo) | `rc=0`, `rc=0` |
| 7 | in-container TCP probes (5 variants) | `db:5432` → `TimeoutError`; `identity:8000` from audit → `TimeoutError`; `172.19.0.1:5433` → CONNECTED; `127.0.0.1:8000` → CONNECTED; `db` resolves to `172.19.0.2` |
| 8 | `POST /api/v1/staff/login` (receptionist, once) | **HTTP `000` after 25 s** — socket accepted, no response |
| 9 | bcrypt verification of all 6 demo accounts vs `.env` | **6/6 `True`** (booleans only; no hash or password printed) |
| 10 | `psql` row counts (dev DB) | demo org: 6 staff, 18 patients, 9 appointments, 5 doctors, **0 queue entries**, 3 branches, 5 schedules; appointments dated 11-11…11-12, 0 today; `queue_entries` 4 rows all in `dqds-org`/`m5-org`/`m9b-org`; `audit_events` 3,484, max `2026-11-12 20:46:41Z`; `staff_users` 559 |
| 11 | `select version_num from alembic_version` | `e6c1a9b3d5f8` = head of the 9-migration chain |
| 12 | container logs (identity) | `/health/ready` 200s through `2026-11-12T15:28:57Z`, then only `/health` liveness |
| 13 | container logs (frontend) | `2026-11-11T11:31:32Z` `ReferenceError: sessionStorage is not defined … /app/.next/server/pages/orgs.js`; last line `07:34:39Z`; nothing at exit |
| 14 | `journalctl -u docker` | `2026-11-14 12:49:00` and `21:00:11` "Deleting nftables IPv4 rules" **exit status 1**; daemon `Started 21:00:13`; Supabase endpoint errors `2026-11-12 21:31` (unrelated project) |
| 15 | `sysctl` / `ufw status` | `ip_forward=1`, `bridge-nf-call-iptables=1`, **ufw active**; `iptables`/`nft` reads denied (non-root) |
| 16 | `grep -c 'def test_' backend -r` | 19 files, **311** test functions (per-file table in Part E) |
| 17 | `ls frontend/pages frontend/lib` | 14 page entries; `lib/` = `auth.js`, `i18n.js`, `bangla-name-sense/` |
| 18 | doc-set reconciliation | `find docs -name '*.md' \| wc -l` = 65 before this report; the index header claims 61 while its body names 64 of the 65 → **stale header count + 1 unregistered file**, see F.6 |
| 19 | `docker inspect` on **all ten** containers (`StartedAt`/`FinishedAt`/`ExitCode`/`RestartCount`) | nine containers `FinishedAt=2026-11-12T15:30:54.5xx–.65Z`, `ExitCode=0`, `StartedAt=2026-11-14T15:47:4xZ`; frontend `StartedAt=2026-11-12T07:34:05Z`, `ExitCode=255`. Restart policy: **`no` on all ten** → G.4 |
| 20 | `git ls-files _tools \| wc -l` · `git status --porcelain` · `git check-ignore -v _tools` | **0** tracked files under `_tools/`; `?? _tools/`, `?? docker-compose.demo.yml`; **no** ignore rule → the startup automation is uncommitted (O-H) |
| 21 | `systemctl list-unit-files \| grep -i amsdp` · `/etc/systemd/system` · `~/.config/systemd/user/` · `~/.config/autostart/` · `crontab -l` | **no AMSDP unit anywhere**; user units are only `carbontally-demo-lab.service`, `preload-qwen.service`; `no crontab for shomonrobie` → no unattended start exists (G.1) |
| 22 | `grep -n -i 'restart' docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` | hardening `:642-643` "No restart policy is set … (deliberate…)"; `:724` "intentionally not set in compose"; one-command §8 item 4 + O-9 → the deferral is documented |
| 23 | `psql` on `audit_events` (login-shaped actions; demo-org actions; last ten rows) | **no login action exists in the schema's usage at all**; demo-org: `appointment.created` ×2, `appointment.status_change` ×3, max `2026-11-10T19:58:18Z`; last rows `2026-11-12T20:46:38–41Z` `staff.created`/`request.denied`, `actor_role=super_admin`, org-1 → G.2 |
| 24 | `psql` — `select username, role, organization_id, branch_id, status from staff_users where username in (6 demo accounts)` | six rows, all `active`, all `demo-org-001` / `demo-br-001` |
| 25 | `sed -n '184,248p' README.md` · `head -80` + `sed -n '94,260p' _tools/amsdp_stack.sh` · `head -30 _tools/init_demo_env.sh` | §3 documents the one-command start; the script's readiness gate (`pg_isready` + 8 × `/health/ready` + frontend 200, 180 s) and `init_demo_env.sh`'s "idempotent; refreshes dates to today" seed are both as described in G.1/G.5 |
| 26 | `journalctl -u snap.docker.dockerd --since '2026-11-14 15:40' --until '2026-11-14 15:55'` (and the 11-12 15:25–15:35 window) | **no entries** — the start that brought nine containers back cannot be attributed (O-G) |

### F.5 Actions deliberately NOT performed

| Not done | Reason |
|---|---|
| No code, Compose, migration, seed or Dockerfile edit | Task scoped as read-only diagnosis; the owner asked for explanation, not fixes |
| No `docker compose up/down/restart`; no container started or stopped | Would change the runtime state under audit |
| No `sudo`; no firewall rule added or removed | Privileged, and the repair must be an owner decision (F.2) |
| No `seed_demo.py` run, no DB write, no migration applied | Would mutate the demo dataset — exactly what is being audited |
| No `pytest` / `npm test` run | Destructive integration suite against a live database; §9 boundaries (Part E.4) |
| No git operation (stage/commit/push/revert) | Outside the task; the working tree is byte-identical (`M frontend/styles/global.css`, `?? _tools/`, `?? docker-compose.demo.yml` untouched) |
| No credential, token, hash or password reproduced anywhere | §3 non-negotiable; verification returned booleans only, and the single login attempt wrote its response to `/tmp` without printing the token |
| No document moved, renamed or deleted | §11; only an additive index update (F.6) |

### F.6 Open items raised for the owner

| ID | Item | Status |
|---|---|---|
| **O-A** | **Who performs R-1 (host firewall)?** It needs `sudo` and is the only blocker that is not project code. | **Owner decision required** — privileges were not escalated |
| **O-B** | **Demo stack or dev stack for the judging run?** The runbook mandates the isolated `amsdp_demo`, which this host has never created. The choice changes the dataset materially (clean vs. `m5-org`/`dqds-org` noise; 18 vs 10 documented patients; 3 vs 2 branches). | **Owner decision required** |
| **O-C** | **Frontend exit `255` is unexplained** — no log line at exit, `OOMKilled=false`, `Error=""`. Only the outcome is proven, not the cause. | Recorded as a risk, not a claim |
| **O-D** | **Index/count drift (per §12, "the tree is the truth"):** `find docs -name '*.md'` returned **65** files while the index header claims a **61**-document snapshot; the body names 64 of the 65, and exactly one file is entirely unregistered: `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md` (24,229 bytes, added by the HEAD commit). `docs/chatgpt/` is **not** one of the §11 subject folders, so its ownership is unclear → reported, **not moved** (§11), and registered in the index as out-of-tree pending the owner's decision. | Registered in `AMSDP_Docs_Index_V1.0.md`; folder decision open |
| **O-E** | **`/health/ready` has no connect timeout** (`backend/common/health.py`), so an unreachable DB makes the probe hang instead of failing fast with a reason. Every diagnosis in this session was slowed by this. | Recommendation R-7; not implemented |
| **O-F** | Whether CI is green on `6bfbec4` | Unverifiable from this host; listed as R-10 |
| **O-G** | **Which command started nine of ten containers on 2026-11-14 at `15:47:4xZ`** — and why the frontend was excluded. The snap Docker journal has **no entries** for `2026-11-14 15:40–15:55` (nor `2026-11-12 15:25–15:35`), so the start cannot be attributed. If it was `_tools/amsdp_stack.sh up` or `docker compose up -d`, the frontend *should* have been attempted and its `StartedAt` would have moved — it did not, which points to a partial start (`docker start` of named containers, or `up` of named services). | Unresolved; stated as a question, not a claim |
| **O-H** | **The startability automation is not in git.** `git ls-files _tools` returns **0** files and `git status` shows `?? _tools/` and `?? docker-compose.demo.yml` (neither is ignored). The one-command script, the demo initialiser and the demo compose overlay therefore exist **only in this working tree**; a fresh clone could not start the demo the way `README.md` §3 documents. | Owner decision: commit them (with the pre-push report's D-2 ownership caveat) or restate §3 |
| **O-I** | **`docs/demo/` content is stale and partly contradicts the tree** — `AMSDP_Limitations_Report_V1.0.md` (dated 2026-11-05) still claims "in-memory storage", "no PostgreSQL", "no migrations run", "no health check endpoints", "no frontend tests" and "zero git commits", all of which are superseded; `AMSDP_Demo_Credentials_V1.0.md` says the accounts live in `org1`/`br1` while the database holds them in `demo-org-001`/`demo-br-001`, and tells the operator to re-seed with `pytest backend/tests/test_e2e.py` instead of `_tools/init_demo_env.sh`. Both are **owner-controlled** (§11) → read and cited here, **not modified**. | Reported only; correction is the owner's act |

---

## Part G — Reconciliation with the owner's account (added 2026-11-15 after owner correction)

The owner's correction was: *"you have already configured AMSDP to start automatically… and there were
also demo users and I could log in."* **Both halves are true, and both are confirmed below from the
tree, the host and the database.** Nothing here contradicts Parts A–F; it dates them, and it corrects
four statements that Parts A–C got wrong or stated too strongly (G.3).

### G.1 "It was configured to start automatically" — what exists, and what it does not do

| Mechanism | State on this host (2026-11-15) | What it actually does |
|---|---|---|
| `_tools/amsdp_stack.sh` (263 lines) | **Present, executable** | `up` / `restart` / `stop` / `status` / `logs` on compose project `amsdp`. `up` is **idempotent** (running services are left alone, stopped ones started), gates on real readiness — `pg_isready` + all 8 × `/health/ready` + frontend HTTP 200, `AMSDP_READY_TIMEOUT=180` — then prints a status table. Refuses to run while the *other* stack holds the ports. Never `down`, never removes a volume, never re-seeds, never prints secrets. **Manual: it runs only when a human invokes it.** |
| `README.md` §3 (`:184-248`) | Documented | The command table, the "access after startup" table, the four guarantees and a troubleshooting table — including "re-run `up`; **it resumes whatever did start**". |
| `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` | Accepted record | §8 item 4: **"No auto-healing / restart policy.** A crashed service is not restarted… Adding compose `restart:` policies was out of scope"; open item **O-9** repeats it. |
| `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md:642-643` | Accepted record | *"No restart policy is set in `docker-compose.yml` (deliberate: a restart policy is a deployment decision for whatever supervisor…)"*; line 724 lists "A restart policy / supervisor for the containers — **intentionally not set in compose**". |
| `docker.service` | **enabled** → the *daemon* starts at boot | Starts Docker. Nothing else. |
| Container restart policies | **`RestartPolicy=no` ×10** (measured) | After any daemon stop the containers stay down. |
| systemd / cron / XDG autostart for AMSDP | **none**: `systemctl list-unit-files`, `/etc/systemd/system`, `~/.config/systemd/user/`, `~/.config/autostart/`, `crontab -l` contain **no** AMSDP unit (`~/.config/systemd/user/` holds only the unrelated `carbontally-demo-lab.service` and `preload-qwen.service`) | No unattended start exists. |

**The precise statement, therefore:** AMSDP is configured for **one-command start**, not for
**unattended start**, and its design explicitly excludes **auto-healing**. That is a deliberate,
recorded decision (two independent reports say so), and my Part B draft implied oversight — corrected.

**Why that distinction produced a three-day outage:**

1. `2026-11-12T15:30:54Z` — daemon stop / host shutdown takes **all ten** containers down.
2. Nothing restarts them; recovery needs a human to run `_tools/amsdp_stack.sh up`.
3. `2026-11-14T15:47:4xZ` — a human **did** start the stack, but only **nine** containers came back;
   the frontend was not started (its `StartedAt` never moved).
4. So even before the 11-14 daemon restarts broke container↔container traffic (D2), the demo had
   already lost its only browser entry point (D1).

**And the automation is not under version control** — `git ls-files _tools` returns **0** files;
`git status` shows `?? _tools/` and `?? docker-compose.demo.yml`; no `.gitignore` rule covers them.
The startability work exists in this working tree only (→ O-H).

**The demo entry point is a different script.** `_tools/init_demo_env.sh` is the isolated-demo
initialiser, not the everyday start: stop demo project → demo DB on its own volume → `alembic upgrade
head` → `seed/seed_demo.py` ("idempotent; refreshes dates to today") → start the rest → verify with
curl, including a **real `receptionist` login**. That last check is a ready-made gate for R-2/R-4.

### G.2 "There were demo users and I could log in" — confirmed, and dated to the minute

| Claim | Verdict | Evidence |
|---|---|---|
| The demo users exist | **Confirmed** | Six accounts in one query, all `status=active`, in `demo-org-001` / `demo-br-001`: `admin` (super_admin), `org_admin`, `br_admin` (branch_admin), `receptionist`, `doctor`, `assistant`. |
| Their passwords work | **Confirmed** | 6/6 bcrypt verifications returned `True` against the `AMSDP_DEMO_PASSWORD_<USERNAME>` values in `.env` (booleans only; no secret reproduced). |
| The owner could log in | **Confirmed, with a timestamp** | `POST /api/v1/staff/users` is guarded by `require_permission("staff.manage")` (`backend/identity/main.py:132`), so it cannot succeed without a valid bearer token minted by a successful `staff_login`. The audit trail holds **six `staff.created` events between `2026-11-12T20:46:38.884Z` and `20:46:41.317Z`** (plus four `request.denied` in the same 2.4 s) with `actor_role=super_admin`, `organization_id=org-1` — i.e. **2026-11-13 02:46 local**. Staff authentication demonstrably worked at that moment. |
| Demo-org activity happened | **Confirmed** | `appointment.created` ×2 and `appointment.status_change` ×3 for `demo-org-001`, latest `2026-11-10T19:58:18Z` (**2026-11-11 01:58 local**). |
| The UI was serving | **Confirmed** | `amsdp-frontend-1` started `2026-11-12T07:34:05Z`, logged `✓ Ready in 2.4s` at `07:34:09Z`, and served until the stack-wide stop at `15:30:54Z`. |

So the owner's recollection is corroborated to the minute, and the credentials were never the
problem. `docs/demo/AMSDP_Demo_Credentials_V1.0.md` supports the same reading — six accounts, login
at `http://localhost:3100`, the `super_admin` password rotated on 2026-11-11 (finding B-12) into
`.env` only. Its organisation names (`org1`/`br1`) and its re-seed instructions are stale (→ O-I).

### G.3 Corrections made to Parts A–C (four)

| # | Earlier statement | Corrected statement | Why it matters |
|---|---|---|---|
| 1 | "`amsdp-frontend-1` exited `255` on 2026-11-12, never restarted" (A/D1, B.1, C.1) | The frontend **stopped with every other container** in a stack-wide stop at `2026-11-12T15:30:54Z` (`FinishedAt` of all ten within 94 ms) and was the one container **not** restarted on `2026-11-14T15:47:4xZ`. It is not a crash and not a crash loop | Calling it a crash invites "restart it and see" — which is the wrong first move; the frontend is only step 2 of 4 (D2 → D1 → D3 → D4) |
| 2 | "no service can ever self-heal … that is exactly how the frontend stayed dead" (B.1, F.1/R-6) | Correct as an effect, but the absence of restart policies is a **documented, deliberate deferral** to "whatever supervisor" (hardening report `:642-643`, `:724`; one-command report §8 item 4, O-9). The intended substitute is the **manual** `_tools/amsdp_stack.sh` | R-6 is re-framed as *closing a recorded gap* or *installing the deferred supervisor*, not as fixing an oversight |
| 3 | "Audit has recorded nothing since 2026-11-12 20:46Z, so no login attempt has ever reached the identity service to be rejected" (C.5.3) | **Wrong.** `staff_login` (`backend/identity/main.py:184-219`) writes **no audit row** on success — only `staff.created` and the denial paths emit events. Login attempts are invisible in `audit_events`, so absence of rows is not evidence about attempts. What is proven instead: the last audit-writing *authenticated* action was `2026-11-12T20:46:41Z`, and today's failure is at the **transport layer** (`HTTP 000` after 25 s, `identity:8000` never answers — C.2 probe 3), not a rejection | The earlier wording overstated the evidence (§7): it inferred something the audit trail structurally cannot show |
| 4 | Journal rows suffixed `Z` (C.1) | `journalctl` was read **without `--utc`**, so those rows are **local (+06)**. Reconciles exactly with the DB stop: `12:49:03+06` = `06:49:03Z` | A six-hour error would have mis-dated the outage boundary for the next reader |

### G.4 Container-level timeline (measured, `docker inspect`, 2026-11-15)

| Container | `StartedAt` | `FinishedAt` | `ExitCode` | `RestartCount` |
|---|---|---|---|---|
| `amsdp-db-1` | `2026-11-14T15:47:43.671Z` | `2026-11-14T06:49:03.048Z` | 0 | 0 |
| `amsdp-identity-1` | `2026-11-14T15:47:50.399Z` | `2026-11-12T15:30:54.574Z` | 0 | 0 |
| `amsdp-organization-1` | `2026-11-14T15:47:50.451Z` | `2026-11-12T15:30:54.637Z` | 0 | 0 |
| `amsdp-patient-1` | `2026-11-14T15:47:50.440Z` | `2026-11-12T15:30:54.567Z` | 0 | 0 |
| `amsdp-doctor-1` | `2026-11-14T15:47:50.429Z` | `2026-11-12T15:30:54.655Z` | 0 | 0 |
| `amsdp-scheduling-1` | `2026-11-14T15:47:50.392Z` | `2026-11-12T15:30:54.599Z` | 0 | 0 |
| `amsdp-appointment-1` | `2026-11-14T15:47:50.445Z` | `2026-11-12T15:30:54.650Z` | 0 | 0 |
| `amsdp-queuing-1` | `2026-11-14T15:47:50.449Z` | `2026-11-12T15:30:54.561Z` | 0 | 0 |
| `amsdp-audit-1` | `2026-11-14T15:47:50.398Z` | `2026-11-12T15:30:54.638Z` | 0 | 0 |
| `amsdp-frontend-1` | **`2026-11-12T07:34:05.200Z`** | `2026-11-12T15:30:54.655Z` | **255** | 0 |

**Three readings, all necessary:**

1. **The 11-12 stop was simultaneous and orderly** — nine containers exited `0` inside the **same
   second** (`…T15:30:54.561Z` → `…T15:30:54.655Z`, a **94 ms** span). That is a daemon stop /
   shutdown, not ten independent failures.
2. **The frontend was never started again** — its `StartedAt` predates the other nine by two days.
   Docker rewrites `StartedAt` on *any* start attempt, so this proves the frontend was **skipped**, not
   that it failed to start. (Its health field still reads `starting` because no health report was ever
   filed for the current incarnation.)
3. **There was at least one further stack generation we cannot date precisely** — the audit rows at
   `2026-11-12T20:46:41Z` were written *after* the 15:30:54Z stop, and the DB's previous stop is
   `2026-11-14T06:49:03Z`. So the backends ran again in between. **Which command performed either
   start is unattributable**: `journalctl -u snap.docker.dockerd` returns **no entries** for
   `2026-11-14 15:40–15:55` or `2026-11-12 15:25–15:35` (→ O-G).

### G.5 What G.1–G.4 change in the repair plan (Part F)

- **R-2 keeps `_tools/amsdp_stack.sh up` as its tool** — it is the documented, idempotent bring-up, and
  its readiness gate means it **exits non-zero while D2 holds**. That makes it a free verification
  gate for R-1: run it after the firewall change and read the exit code, not `docker ps`.
- **R-4's canonical route is `_tools/init_demo_env.sh`** — it already performs `alembic upgrade head`
  and seeds idempotently, and `backend/seed/seed_demo.py:304-358` **re-dates demo-owned appointments
  and queue entries to today** (`created_by`/`added_by = 'demo-seed'`). That is precisely the drift
  measured in Part B (appointments stuck on 11-11/11-12, 0 queue entries), so re-seeding is mandatory
  on demo morning, not optional.
- **R-6 is re-framed, not withdrawn**: either add `restart: unless-stopped` to both compose files, or
  install the supervisor the hardening report deferred to (a systemd user unit running
  `_tools/amsdp_stack.sh up` at boot). The second option keeps the project's own documented decision
  intact; the first is the smaller change.
- **New prerequisite discovered: commit the automation.** `_tools/` and `docker-compose.demo.yml` are
  untracked (O-H). Until they are committed, the startability work does not travel with the
  repository, and `README.md` §3 documents commands a fresh clone cannot run.
- **`docs/demo/` is cited, never edited** (§11 owner-controlled): its stale content is recorded as
  O-I, not corrected here.

---

## Conclusion

The AMSDP feature surface is substantially **built**: 64 route declarations across the eight domain
services, the gateway and the shared `common/` modules; 14 frontend routes; 311 backend test
functions across 19 files; a 9-migration forward-only chain at head; and all 11 MVP-scope items plus
7 extras present in code. It is not **deliverable** in its current state, for reasons that are
almost entirely **environmental and operational rather than programmatic**:

1. **Host container-to-container networking is broken** — after two Docker daemon restarts on
   2026-11-14, the host firewall drops the bridge forward path, so every backend service is
   unhealthy and **sign-in cannot complete at any layer**.
2. **The frontend container has not been running since the stack-wide stop of 2026-11-12** — it was
   the one service **skipped** when nine of ten were restarted on 2026-11-14, and nothing restarts a
   container on its own (a documented deferral, not an oversight — G.1) — so there is no login page at
   all on port 3100.
3. **The isolated demo stack the runbook depends on has never been created on this host**, and the
   demo queue is **empty (0 entries)** while its appointments are **stale-dated to 11-11/11-12**.
4. **One genuine code defect** — the `/orgs` SSR `sessionStorage` crash — sits behind all of the
   above, waiting to surface the moment 1–3 are fixed.

The credentials that were suspected of causing the sign-in failure are, on measurement, **correct**
(6/6 bcrypt verifications pass, all accounts `active`, correct roles and org), and they **demonstrably
worked** — the audit trail shows an authenticated `super_admin` action at `2026-11-12T20:46:41Z`
(2026-11-13 02:46 local, G.2). The failure is environmental, not credential, not authorisation, not
business logic: the accounts are fine, the environment they need is gone.

Repairing **R-1…R-5** restores a demonstrable system; **R-6…R-10** make it survive the next reboot
and keep it diagnosable.

**Nothing was changed. Awaiting review before any fix is applied.**

---

*Written to `docs/audit/` per `.clinerules` §11; registered in
`docs/governance/AMSDP_Docs_Index_V1.0.md` per §12. No document was moved, renamed or deleted, so no
migration-manifest entry is required.*

*Revision 2 (2026-11-15): Part G added, and four statements in Parts A–C corrected, in response to the
owner's correction. Only this report and the documentation index were edited; no code, Compose file,
migration, seed, database row or container was touched, and no document was moved or renamed.*
