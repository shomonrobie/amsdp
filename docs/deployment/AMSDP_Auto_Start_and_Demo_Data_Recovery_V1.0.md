# AMSDP — Automatic Start, Demo Data Refresh and Login Recovery (V1.0)

> **Status:** implemented and verified on this host, 2026-11-15.
> **Scope:** make the local AMSDP stack restart by itself (crash and reboot), keep the
> demo data current, and prove that **all six demo accounts can sign in**.
> **Supersedes:** the *deferral* of restart policies recorded in
> `deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md:642-643` and `:724`
> (owner instruction, 2026-11-15).
> **Where written:** `docs/deployment/` — an existing §11 subject folder, chosen over
> creating `docs/operations/` because this is a deployment/runtime-configuration change,
> not a day-to-day runbook.

---

## 1. Outcome

| # | Requirement | Result |
|---|---|---|
| 1 | The stack restarts automatically after a crash | **DONE** — `restart: unless-stopped` on all ten services; the daemon restarted a probe container 7× in 9 s |
| 2 | The stack restarts automatically after a host reboot | **DONE** — same policy **plus** the systemd user unit `amsdp-autostart.service` (enabled, `Linger=yes`, ran to `status=0/SUCCESS`) |
| 3 | It comes up **with demo data** | **DONE** — the boot unit re-runs the idempotent seed: 7 appointments and 2 queue entries now dated **2026-11-15** (today), 6 staff hashes refreshed from `.env` |
| 4 | **All users can log in** | **DONE** — 6/6 accounts returned `HTTP 200` with the correct role through `http://localhost:3100/api/v1/staff/login` |
| 5 | All ten services healthy | **DONE** — `db`, 8 backends and `frontend` all `running / healthy / ok` |

The two defects that actually blocked the demo (`D1` frontend down, `D2` container↔container
forwarding dropped) are both cleared, and `D4` (`/orgs` server-render crash) is fixed.

---

## 2. What was wrong, and the exact fix

### 2.1 `D2` — container↔container traffic dropped (the reason nobody could log in)

Measured from **inside** the identity container before any change:

| Probe from `amsdp-identity-1` | Result |
|---|---|
| `db:5432` (resolves to `172.19.0.2`) | **timed out** |
| `172.19.0.2:5432` (the database container, directly) | **timed out** |
| `172.19.0.1:5433` (the database via the host's published port) | **CONNECTED** |
| host → `127.0.0.1:8110/health` | `200` (liveness fine) |
| host → `127.0.0.1:8110/health/ready` | **no response** (readiness blocked) |

So the service itself was healthy, but every call that crossed the bridge — which is
every service→database call *and* every frontend→identity proxy call
(`/api/v1/staff/:path*` → `http://identity:8000`, `frontend/next.config.js:7`) — was
being dropped. Login could therefore never succeed, no matter what the credentials were.

**Diagnostic that isolated it:** a **newly created** Docker network on the same daemon
forwarded correctly (`NEW_NETWORK_FORWARD=OK` — two containers, same images). The block
was therefore per-bridge state, not a global firewall policy: the existing `amsdp_default`
bridge had lost its per-interface ACCEPT rules in the failed nftables deletion on
2026-11-14.

**Fix applied (no root required):**

```bash
docker compose -p amsdp -f docker-compose.yml down     # keeps volumes; removes the network
docker compose -p amsdp -f docker-compose.yml build frontend
_tools/amsdp_stack.sh up                               # recreates the network, waits for readiness
```

Compose recreated `amsdp_default`; the daemon inserted a fresh rule set for the new bridge
interface, and every `db:5432` call started working. **No `ufw` rule was changed, no
firewall was disabled, and `sudo` was not needed.**

> **Honest limit of this verification.** The mechanism inside the kernel rule set is
> **inferred, not read**: `nft list ruleset` and `iptables -L` both return
> *“Operation not permitted (you must be root)”* for this account. What is verified is the
> **behaviour** (cross-bridge traffic dead on the old bridge, alive on a new one, alive
> again after recreating it), not the rule text.

**Not durable across another failed daemon restart.** If dockerd again fails to rebuild the
bridge rules, the same symptom returns. The recovery is a network recreate — now documented
in `README.md` §3 troubleshooting so it is not rediscovered under time pressure.

### 2.2 `D1` — frontend container absent

`amsdp-frontend-1` was `Exited (255)` since 2026-11-12 while the other nine containers ran,
so the only public entry point was down. It is now running, healthy, and serving.

### 2.3 `D4` — `/orgs` crashed the server render

`frontend/pages/orgs.js` was the **only** page missing the `typeof window` guard that every
other page has (`staff.js`, `patients.js`, `doctors.js`, `branches.js`, `appointments.js`,
`schedules.js` all guard; `orgs.js` did not). It read `sessionStorage` during server render →
`ReferenceError` → HTTP 500. Both lines now match the existing convention:

```js
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
...
const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
```

---

## 3. What was added

| File | Change |
|---|---|
| `docker-compose.yml` | `restart: unless-stopped` on all ten services + a header note recording the owner decision that supersedes the earlier deferral |
| `docker-compose.demo.yml` | Header note: the overlay inherits the policy, so it is not repeated |
| `frontend/pages/orgs.js` | The two SSR guards above |
| `_tools/amsdp_autostart.sh` | **New** — waits for the Docker daemon, runs `amsdp_stack.sh up`, then refreshes the demo data |
| `_tools/install_autostart.sh` | **New** — installs/enables/removes the systemd user unit (`--status`, `--uninstall`) |
| `_tools/verify_demo_login.sh` | **New** — signs in all six demo accounts through the frontend proxy, prints OK/FAIL, exits non-zero on any failure |
| `README.md` §3 | New “Automatic start and demo data” subsection + a bridge-forwarding troubleshooting entry |

**Two independent layers, deliberately:**

* `restart: unless-stopped` — the Docker daemon restarts a crashed container and brings the
  whole stack back when the daemon starts at boot. No script, no login, no intervention.
* `amsdp-autostart.service` — a systemd **user** unit (no root needed; this account already
  has `Linger=yes`, so it runs at boot without anyone logging in). It cannot declare
  `Requires=docker.service` — a user unit cannot be ordered against a system unit — so it
  waits for the daemon itself, then adds the readiness gate and the demo-data refresh.

Either layer alone keeps the demo up. Together they also keep the demo **data** current.

**Deliberate behaviour:** a container stopped *explicitly* (`docker stop`, `docker kill`) is
**not** restarted. That is Docker's documented `unless-stopped` semantics and it is the
behaviour we want — an operator who stops the stack is not fought by a supervisor.

---

## 4. Verification performed (real results, this tree, this host)

### 4.1 Stack health

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

`_tools/amsdp_stack.sh up` exited `0` (“all services ready after 2 probe(s)”).

### 4.2 Every demo account signs in (the actual requirement)

`_tools/verify_demo_login.sh` → exit `0`:

```
  ACCOUNT        RESULT DETAIL
  admin          OK     HTTP 200, role=super_admin
  org_admin      OK     HTTP 200, role=org_admin
  br_admin       OK     HTTP 200, role=branch_admin
  receptionist   OK     HTTP 200, role=receptionist
  doctor         OK     HTTP 200, role=doctor
  assistant      OK     HTTP 200, role=assistant

All 6 demo accounts signed in through http://localhost:3100.
```

Credentials come from `.env` (`AMSDP_DEMO_PASSWORD_<USERNAME>`); no password or token is
printed by the script, this report or any log.

### 4.3 Every page server-renders

`/`, `/dashboard`, `/orgs`, `/staff`, `/patients`, `/appointments`, `/branches`, `/doctors`,
`/schedules`, `/queue` → **all `200`** (`/orgs` was `500` before the fix).

### 4.4 Auto-restart actually fires

| Test | Result |
|---|---|
| `docker inspect` restart policy, all ten containers | `unless-stopped` x10 |
| Disposable container with the same policy, exiting `1` | `status=restarting restarts=7` after 9 s - the daemon keeps restarting it |
| `docker kill amsdp-identity-1` | **not** restarted, `RestartCount=0` - correct: an explicit kill is a manual stop |
| `kill -9` of PID 1 from inside the container | no effect - PID 1 in a PID namespace ignores in-namespace signals (expected kernel behaviour) |
| `kill -9` of the container init from the host | **not possible** for this account: `Operation not permitted` (container processes run as root) |

Because a live crash of a *real* service could not be induced without root, the
crash-restart guarantee is evidenced by the disposable-container test above **plus** the
identical policy on all ten real containers - not by crashing a production service.

### 4.5 Boot unit

```
Loaded: loaded (/home/shomonrobie/.config/systemd/user/amsdp-autostart.service; enabled)
Active: active (exited)
Process: ExecStart=.../_tools/amsdp_autostart.sh (code=exited, status=0/SUCCESS)
Restart=on-failure   RestartUSec=30s   Type=oneshot   RemainAfterExit=yes
```

`Linger=yes` was already set for this user, so the unit starts at boot with nobody logged in.
`_tools/install_autostart.sh --status` and `--uninstall` are the day-to-day controls.

### 4.6 Demo data refreshed, and nothing lost

Seed output (per account): `Staff '<user>' exists - password hash refreshed from environment`
for all six accounts; appointments re-dated to today.

| Table | Before the repair | After the repair |
|---|---:|---:|
| `organizations` | 56 | 56 |
| `staff_users` | 559 | 559 |
| `patients` | 1,595 | 1,595 |
| `appointments` | 82 | 82 |
| `audit_events` | 3,484 | **3,484** |

The `down`/`up` cycle removed containers and the network but **not** the volume
(`amsdp_amsdp_pg_data`), and the audit trail is unchanged - append-only, nothing deleted
(`.clinerules` section 3).

Demo board now: `appointment_date = 2026-11-15` -> 7 appointments; `queue_entries.date =
2026-11-15` -> 2 entries; six `active` staff in `demo-org-001` / `demo-br-001`.

---

## 5. Governance and Skill Compliance

**Applicable governance documents** (`.clinerules` section 4 routing):

| Domain | Document applied | Evidence |
|---|---|---|
| Docker / deployment / infrastructure | `deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md`, `deployment/AMSDP_M8_Cloud_Deployment_Architecture.md`, `docker-compose.yml` | read before changing any service; the earlier deferral is explicitly superseded, in writing, in the compose header |
| Frontend UI | `frontend/components/`, `frontend/pages/*` conventions | the `/orgs` guard copies the exact pattern used by the other seven pages |
| Documentation placement | `.clinerules` section 11 and 12; `governance/AMSDP_Docs_Index_V1.0.md` | report written to an existing subject folder; index updated in the same task |
| Evidence standard | `.clinerules` section 7 | every claim below is IMPLEMENTED, TESTED or VERIFIED as labelled |

**Skills:** **none installed** in this workspace (`.clinerules` section 5 - no
`.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used or claimed;
governance documents were used instead.

**Non-negotiables checked:**

* **Secrets** - `.env` values are sourced, never echoed. The DSN is built in-process and not
  printed. `verify_demo_login.sh` writes the token response to a `umask 077` temp file and
  deletes it on exit. No password, token or JWT material appears in this report or any log.
* **Server-side authorization** - untouched; no endpoint, permission or tenancy code changed.
* **Audit trail** - row count identical before/after; nothing deleted or rewritten.
* **Migrations** - none needed; no schema change was made.
* **Git safety** - nothing staged, committed, pushed, reset, stashed or checked out. The
  pre-existing uncommitted `frontend/styles/global.css` was **not** modified by this task
  (it is, however, now baked into the rebuilt frontend image, since a rebuild reads the
  working tree).

**Evidence grades:**

| Claim | Grade |
|---|---|
| Restart policies present on all ten services | VERIFIED (`docker inspect` x10) |
| A failing container is restarted by the daemon | VERIFIED (probe container, `restarts=7`) |
| The real services would be restarted by a crash | **TESTED in principle only** - the real-crash test needs root (section 4.4) |
| Boot unit installed, enabled and running as designed | VERIFIED (`systemctl --user`, `status=0/SUCCESS`) |
| Survives an actual host reboot | **NOT verified** - no reboot was performed. The mechanism is verified; the reboot itself is not |
| All six demo accounts can log in | VERIFIED (6/6 `HTTP 200`, correct roles, through the frontend proxy) |
| Demo data current | VERIFIED (7 appointments + 2 queue entries on 2026-11-15) |
| No data lost by the repair | VERIFIED (identical counts incl. `audit_events=3484`) |

**Deviations / judgement calls:**

1. **`docker-compose.yml` was edited** although the earlier hardening report had deferred
   restart policies. The owner's instruction on 2026-11-15 supersedes that deferral; the
   supersession is recorded in the file header so the two documents do not contradict.
2. **`docs/operations/` was not created.** The report went to the existing `deployment/`
   folder (section 11: reuse an existing subject folder; `operations/` is for runbooks and
   incident procedures).
3. **`docs/demo/*` were not edited** - owner-controlled (section 11); their staleness stays open.

---

## 6. Open items

| ID | Item | Why it matters |
|---|---|---|
| **O-J** | **A real crash of a production service was not induced** (needs root). If a service crashes and does *not* come back, run `_tools/amsdp_stack.sh up`. | The guarantee rests on identical policy plus probe evidence |
| **O-K** | **Host reboot not performed.** The boot path is verified by unit state and a successful `status=0/SUCCESS` run, not by an actual reboot. | First reboot is the real acceptance test - run `_tools/verify_demo_login.sh` afterwards |
| **O-L** | **The bridge-rule loss can recur** if dockerd again fails to restore nftables rules. Recovery: `docker compose -p amsdp down && _tools/amsdp_stack.sh up` (documented in `README.md` section 3). A permanent fix needs root (`ufw` forward policy / `ufw-docker`) and was **not** attempted. | Same symptom could reappear after any daemon restart |
| **O-H** (carried) | `_tools/` and `docker-compose.demo.yml` are **still untracked** - now including the three new scripts. On a fresh clone, `README.md` section 3 points at files that do not exist. | Owner decision needed: commit them, or restate the README |
| **O-I** (carried) | `docs/demo/AMSDP_Limitations_Report_V1.0.md` and `AMSDP_Demo_Credentials_V1.0.md` are stale (org naming, re-seed instructions). Owner-controlled, so reported and not modified. | Demo-facing documentation |
| **O-M** | `frontend/styles/global.css` carries uncommitted work from before this task; it is now inside the rebuilt image. | Not caused here, but it is in the running demo |

---

## 7. Reproduce this state from a cold start

```bash
_tools/install_autostart.sh          # once per machine: installs + enables the boot unit
_tools/verify_demo_login.sh          # gate: exits 0 only when all six can sign in
```

Day-to-day:

```bash
_tools/amsdp_stack.sh status         # state, health and probes
_tools/amsdp_stack.sh up             # resume after a deliberate stop
_tools/install_autostart.sh --status # boot unit state
```
