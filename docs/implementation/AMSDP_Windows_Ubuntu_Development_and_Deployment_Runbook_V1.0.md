# AMSDP — Windows Development / Ubuntu Host Runbook (V1.0)

**Date:** 2026-11-23
**Author:** AMSDP coding agent (unattended verification session)
**Status:** operating runbook. Every Ubuntu-side statement below was executed and
observed in this session; every Windows-side step is **NOT VERIFIED** (§1.2).
**Scope:** how development moves to a Windows workstation while the Ubuntu host in
`/home/shomonrobie/amsdp` remains the only application and database host.

> This runbook does not replace, and must not be read instead of, the two existing
> runbooks. They stay authoritative for what they cover:
>
> * `docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md` — start,
>   restart, stop, rebuild, the failure table and the recovery procedures.
> * `docs/deployment/AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` — the systemd
>   boot unit, the readiness gate and the demo-data refresh.
>
> This document adds the two things those do not cover: the **split between the
> Windows workstation and the Ubuntu host**, and the **branch/merge/publication
> discipline** that QUE-006 proved is easy to get wrong.

---

## 1. Evidence status — read this before trusting anything below

### 1.1 VERIFIED on this Ubuntu host (executed in this session)

| Claim | How it was verified |
|---|---|
| Repository root is `/home/shomonrobie/amsdp`; compose project is `amsdp` | `docker ps` (containers named `amsdp-*`), compose file read |
| Nine services run: `db`, `identity`, `organization`, `patient`, `doctor`, `scheduling`, `appointment`, `queuing`, `audit`, `frontend` | `docker ps` container list |
| Published host ports: `3100` frontend, `5433` db, `8110`–`8117` backends | `ss -ltn`, `docker-compose.yml` (`ports:` entries) |
| `amsdp-autostart.service` (systemd **user** unit) is `active` and `enabled` | `systemctl --user list-unit-files 'amsdp*'`, `is-active`, `is-enabled` |
| Migration graph has exactly one head and applies from an empty database | `alembic heads` → `c4d8e2a91f60 (head)`; `alembic upgrade head` against a throwaway `postgres:16-alpine` container on `127.0.0.1:55460` exited **0** |
| Frontend unit suite passes in this tree | `cd frontend && npm test` → **368 pass / 0 fail**, exit 0 |
| The targeted backend suite for the merged tree passes | `262 passed, 0 failed` (7m13s) |
| Tooling on the host | Python 3.14.4 (`/home/shomonrobie/amsdp/.venv`), Node v24.21.0, npm 11.19.0, Docker 29.1.3, Compose 2.40.3 |

### 1.2 NOT VERIFIED — do not present these as working

| Item | Why it is not verified |
|---|---|
| Any Windows-side step in §5 | No Windows machine, shell or agent session was observed while writing this. The steps are derived from what the repository actually contains (npm scripts, pytest layout, compose files) and must be executed once, by a human, on the Windows workstation, before they are treated as fact |
| SSH access from Windows to this host | `ss -ltn` shows **no listener on port 22**. There is no SSH server reachable on this host today; see §6.1 |
| Human audibility of an announcement in the room | No audio device is attached to the host; QUE-006 keeps this open (B-8) |
| Windows-side Docker Desktop / WSL2 behaviour | Never observed here |

### 1.3 The one security fact this runbook must state plainly

`ss -ltn` shows PostgreSQL published as `0.0.0.0:5433` and `[::]:5433`. That is the
development database — **reachable from the whole LAN, not only from this host**.
The password lives only in the gitignored `.env`, and `.env` is not committed, so
the exposure is password-protected rather than open — but it is still an exposure
that no document records as a decision. §6.3 carries the recommendation; changing
it is an owner decision, not something this runbook did.

### 1.4 The live database is **two revisions behind** the merged code

Verified against the running `amsdp-db-1` container:

```
select version_num from alembic_version;        -> a9c4e1f7b2d8
select to_regclass('voice_packs');               -> (null)
select to_regclass('queue_announcement_deliveries'); -> (null)
```

The merged tree's head is `c4d8e2a91f60`; `a7c3f19d2b64` (queue announcement
deliveries) and `c4d8e2a91f60` (voice packs + platform config) have **not** been
applied to the development database. Consequences, both observed:

* The full backend suite run against the live database reports `682 passed,
  109 errors` — every error is at *fixture setup* with
  `psycopg2.errors.UndefinedTable: relation "voice_packs" does not exist`. Pointed at
  a migrated throwaway database, **the same two files pass: `109 passed` in 78s**
  (§8) — an exact match with the error count, which is what a missing table looks
  like when the code is correct.
* A rebuilt stack would serve `/api/v1/voice-packs` and the delivery-record paths
  against tables that are not there.

So the first operational action after this merge is **migrate, then rebuild**
(§4.3), which is the opposite order from the one people naturally reach for.

---

## 2. Roles, after the handover

```
  Windows workstation                         Ubuntu host  (shomonrobie-H81M-DS2, 192.168.68.108)
  ---------------------                       ---------------------------------------------------
  edits code, runs unit suites                owns the repository of record: /home/shomonrobie/amsdp
  pushes branches to GitHub        ------->    runs docker compose project `amsdp`
  never holds the live database    <-------    holds every volume: amsdp_pg_data, demo volume
                                               serves the only browser origin: http://<host>:3100
```

Three rules follow from that picture, and they are the whole point of the document:

1. **The database has exactly one home.** It is the `amsdp_pg_data` volume on the
   Ubuntu host. A second, Windows-local database is for *tests only* and is never
   called "the app database" (§5.3).
2. **The browser talks to one origin.** Every `/api/v1/*` prefix is proxied from the
   Next.js frontend (`frontend/next.config.js`), so a Windows developer checks the
   application at `http://192.168.68.108:3100` rather than by calling a backend port.
   Calling `8111`–`8117` directly bypasses the proxy — that habit is what hid INT-4
   for a whole milestone.
3. **Code travels through Git, not through a network share.** There is no SSH server
   on this host (§1.2); the supported transport is a push to `origin/hackathon-mvp`
   and a fast-forward pull on the other side (§7).

---

## 3. Host inventory (what exists, where)

| Element | Value |
|---|---|
| Repository | `/home/shomonrobie/amsdp` |
| Compose file (development) | `docker-compose.yml`, project name `amsdp` |
| Compose overlay (demo) | `docker-compose.yml` + `docker-compose.demo.yml`, project name `amsdp_demo` |
| Database volume | `amsdp_pg_data` (development) plus the demo volume from the overlay — never `down -v` |
| Environment file | `.env` in the repository root — gitignored, never committed, never printed (§9.3) |
| Boot unit | `amsdp-autostart.service` (systemd *user* unit, `enabled` + `active`) running `_tools/amsdp_autostart.sh` |
| Operations scripts | `_tools/amsdp_stack.sh`, `_tools/amsdp_rebuild.sh`, `_tools/amsdp_autostart.sh`, `_tools/install_autostart.sh`, `_tools/pg_backup.sh`, `_tools/pg_restore_test.sh`, `_tools/init_demo_env.sh`, `_tools/verify_demo_login.sh` |
| Frontend origin | `http://127.0.0.1:3100` (host) / `http://192.168.68.108:3100` (LAN) |

### 3.1 Service → host port map (from `docker-compose.yml`)

| Service | Container port | Host port | Readiness probe |
|---|---|---|---|
| `identity` | 8000 | **8110** | `/health/ready` |
| `organization` | 8001 | **8111** | `/health/ready` |
| `patient` | 8002 | **8112** | `/health/ready` |
| `doctor` | 8003 | **8113** | `/health/ready` |
| `scheduling` | 8004 | **8114** | `/health/ready` |
| `appointment` | 8005 | **8115** | `/health/ready` |
| `queuing` | 8006 | **8116** | `/health/ready` |
| `audit` | 8007 | **8117** | `/health/ready` |
| `frontend` | 3000 | **3100** | `GET /` |
| `db` (`postgres:16-alpine`) | 5432 | **5433** | `pg_isready -U amsdp -d amsdp` |

Every service declares `restart: unless-stopped`, and every backend gates on the
database being healthy — which is why the order implied by `_tools/amsdp_stack.sh`
matters and why "start the containers in a random order" is not an option.


---

## 4. Operating the Ubuntu host (the only deployment target)

All commands run **from the repository root** (`/home/shomonrobie/amsdp`) unless a
step says otherwise. These are the same commands the existing runbooks give; they
are repeated here only so that a Windows-side developer knows exactly what to ask
for and what "healthy" looks like.

### 4.1 Everyday lifecycle

| Task | Command | What "good" looks like |
|---|---|---|
| Status + health | `_tools/amsdp_stack.sh status` | every backend `healthy` and its `/health/ready` probe answering; frontend answers `GET /` |
| Start / resume | `_tools/amsdp_stack.sh up` | idempotent: running services left alone, stopped ones started, no `down`, no volume removal |
| Graceful restart | `_tools/amsdp_stack.sh restart` | data survives; nothing is re-seeded |
| Stop (keep data) | `_tools/amsdp_stack.sh stop` | containers stop, volumes and data remain |
| Logs | `_tools/amsdp_stack.sh logs [service]` | follows one service; use the names in §3.1 |
| Rebuild after a code change | `_tools/amsdp_rebuild.sh` | rebuilds and recreates only the affected services, then verifies — the restart runbook's procedure, not a plain `restart` |

`docker compose -p amsdp down -v` is **never** part of any of these and must never be
run on this host: `-v` deletes `amsdp_pg_data`.

### 4.2 After the host reboots

`amsdp-autostart.service` is `enabled` and `active` (§1.1). It starts the stack
through the readiness gate and then refreshes the demo data; its behaviour, logging
and recovery steps are owned by
`docs/deployment/AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md`. To confirm it
ran after a reboot:

```
systemctl --user is-active amsdp-autostart.service
journalctl --user -u amsdp-autostart.service -n 50 --no-pager
_tools/amsdp_stack.sh status
```

### 4.3 Schema migrations — do this **before** a rebuild

The merged tree has **one** head — `c4d8e2a91f60` — and this session proved the whole
chain applies to an *empty* database (`alembic upgrade head` exit 0 against a
throwaway `postgres:16-alpine` container). The *live* development database is
**behind** (§1.4): it is at `a9c4e1f7b2d8` and is missing `a7c3f19d2b64` and
`c4d8e2a91f60`. Until it is migrated, the voice-pack API and announcement-delivery
paths have no tables to write to.

```
_tools/pg_backup.sh                 # take the dump FIRST (§4.4)
cd backend
set -a; . ../.env; set +a          # provides POSTGRES_PASSWORD; nothing is printed
../.venv/bin/alembic current       # what the live database is actually at
../.venv/bin/alembic heads         # must print exactly one "(head)" line
../.venv/bin/alembic upgrade head  # forward-only, idempotent
../.venv/bin/alembic current       # now equals the head
cd .. && _tools/amsdp_rebuild.sh   # only now rebuild the images that changed
```

`alembic current` and `alembic heads` disagreeing is normal before an upgrade and a
defect after one. A second *head* is a release blocker, not something to resolve by
hand: it means two migrations were authored in parallel branches, and the fix is a
new forward-only merge revision.

### 4.4 Backup and restore drill

```
_tools/pg_backup.sh                # writes backups/amsdp_amsdp_<timestamp>.sql.gz
_tools/pg_restore_test.sh          # restores into a scratch database and checks it
```

The dump is a `--clean --if-exists` plain SQL dump produced by the `pg_dump`
**inside** the `postgres:16` container, deliberately, so the dumper version always
matches the server. `backups/` is not committed. Run the drill before any step that
touches many rows, and copy the dump off the host — it is the only copy at that
point.

### 4.5 Demo stack (never alongside the development stack)

The demo overlay reuses the **same host ports**, so the development stack must be
stopped first:

```
docker compose -p amsdp down                                        # stop dev, keep volumes
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml up -d --build
# then alembic upgrade head + python seed/seed_demo.py against amsdp_demo
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down
_tools/amsdp_stack.sh up                                            # bring dev back
```

The demo project has its own database (`amsdp_demo`) and its own volume; the
development database is never touched by it. Demo credentials live in
`docs/demo/AMSDP_Demo_Credentials_V1.0.md` and must never be copied into a report, a
log or a commit message.

---

## 5. Preparing the Windows workstation

> **Every step in this section is NOT VERIFIED (§1.2).** It is written from what the
> repository contains — `frontend/package.json` (`npm test` → `node --test
> tests/*.test.mjs`), `backend/conftest.py` (needs `AMSDP_DATABASE_URL` or
> `POSTGRES_PASSWORD`), `backend/requirements-dev.txt` (test/migration tooling;
> runtime dependencies live in each service's own `requirements.txt`) — and it must
> be executed once, on the machine, before anyone relies on it.

### 5.1 Prerequisites

| Tool | Version actually used on the Ubuntu host | Note for Windows |
|---|---|---|
| Python | 3.14.4 in `/home/shomonrobie/amsdp/.venv` | 3.12+ is the realistic floor; create your own venv — the host's `.venv` is not portable |
| Node.js | v24.21.0 (npm 11.19.0) | the frontend suite uses `node --test` and `fetch`, so Node 20+ is required |
| Docker | 29.1.3 / Compose 2.40.3 | only needed for a local **test** database (§5.3) |
| Git | — | the only supported transport between the two machines (§6.1) |

### 5.2 Clone, branch, environment

```
git clone <origin-url> amsdp
cd amsdp
git fetch origin
git switch hackathon-mvp && git merge --ff-only origin/hackathon-mvp
```

Create `.env` beside `docker-compose.yml` by copying `.env.example` and filling it in.
Values are transferred **out of band** (owner → developer), never through Git.
`.env` is gitignored; if `git status` ever shows it, stop and fix that first.

### 5.3 A local **test** database (optional but recommended)

The backend suite writes real rows (it creates organizations, patients, appointments
and queue entries, and purges what it can). Point it at a throwaway database, never
at the host's `amsdp`:

```
docker run -d --name amsdp-test-pg \
  -e POSTGRES_USER=amsdp -e POSTGRES_PASSWORD=<local-test-password> \
  -e POSTGRES_DB=amsdp -p 55460:5432 postgres:16-alpine
```

This is exactly the ritual this session used to prove the migration graph (§1.1),
with the container on host port **55460** so it cannot collide with the host's 5433.
Then give the suite that DSN, and migrate it once:

```
cd backend
export AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:<local-test-password>@127.0.0.1:55460/amsdp"
../.venv/bin/alembic upgrade head
```

(If your `.venv` is a Windows venv, the interpreter is `.venv/Scripts/python.exe`
and `pip` is `.venv/Scripts/pip.exe` — the commands below show the POSIX form the
Ubuntu host uses.)

### 5.4 Run the suites

**Backend** (working directory `backend/`):

```
set -a; . ../.env; set +a            # or export AMSDP_DATABASE_URL=...   (§5.3)
../.venv/bin/python -m pytest -q
```

`backend/conftest.py` reads `AMSDP_DATABASE_URL`, and `backend/common/database.py`
falls back to `AMSDP_DB_PORT` (default **5433**) plus `POSTGRES_PASSWORD`. That is why
a bare `pytest` without a DSN fails at collection with
`psycopg2.OperationalError` — the suite is not "broken", it is unconfigured. Point it
at the migrated test database (§5.3); pointing it at the live one produces
*setup errors*, not failures, whenever that database is behind the migrations
(§1.4). Two narrower invocations used in this session:

```
../.venv/bin/python -m pytest -q organization/tests queuing/tests doctor/tests/test_doctor.py \
    appointment/tests/test_appointment_calendar_filters.py     # 262 passed
../.venv/bin/python -m pytest -q organization/tests/test_voice_packs_api.py \
    queuing/tests/test_queue.py                                # 109 passed (on the test DB)
```

**Frontend** (working directory `frontend/`):

```
npm install        # once
npm test           # node --test tests/*.test.mjs → 368 pass in this session
npm run build      # must compile; the suite does not start Next, so build separately
```

The frontend suite never starts a server: it imports pure modules
(`frontend/lib/announcements/*`, `next.config.js`) and asserts behaviour. That is why
`next-config-rewrites.test.mjs` can pin the proxy table without a browser — and why
it is the test that keeps INT-4 from coming back.

### 5.5 Look at the deployed application, not at a backend port

Open `http://192.168.68.108:3100` and use the browser's network panel. Every API
call must be same-origin (`/api/v1/...`) and answer `2xx`; anything answering
`text/html` with a 404 is an unproxied prefix and a real defect (§8, gate 4).

### 5.6 What a Windows workstation must not do

* Do not run a second full compose stack against the host's volumes — volumes are
  per-machine; two stacks mean two databases and silent data divergence.
* Do not publish a database port to the LAN from the Windows machine either; bind it
  to `127.0.0.1`.
* Do not edit the host's files over a network share while a suite is running on the
  host. Git, not SMB.
* Do not commit `.env`, a JWT secret, a dump or a demo password (§9.3).

---

## 6. Access paths and the two exposures to decide about

### 6.1 There is no SSH server on the host today

`ss -ltn` was checked in this session and **no process is listening on port 22**.
Nothing in the repository documents SSH access, so this is not a regression — it is a
gap. Until an owner decision installs and configures `openssh-server`, the supported
paths are:

| Need | Supported path |
|---|---|
| Source code | Git (`origin/hackathon-mvp`), both directions |
| The running application | `http://192.168.68.108:3100` from the LAN |
| Logs, restarts, backups | a human at the host, or an agent session on the host |
| A dump | produced on the host, then copied out of band (it contains patient data) |

If SSH is installed later, it must be key-only, must not expose the database, and
must be recorded as an owner decision — not added silently by an agent.

### 6.2 The frontend is published on `0.0.0.0:3100`

That is intended: it is the LAN demo origin. It means the login page is reachable
from every device on the network, which is fine for a demo and not fine for
anything holding real patient data.

### 6.3 PostgreSQL is published on `0.0.0.0:5433` — recommended: bind it to loopback

Verified by `ss -ltn`. The compose file publishes `"5433:5432"`, so any device on the
LAN can attempt a password login to the development database. The password is not in
Git, so this is not an open door — but it is a door nobody decided to open.

Recommended change (owner decision, **not applied** in this session because it
changes deployment behaviour):

---

## 7. Branch, merge and publication discipline

This is the part of the handover that QUE-006 got wrong twice, so it is written as
rules with the evidence that produced them.

### 7.1 The rule that a fast-forward-only push actually imposes

A fast-forward push succeeds only when the remote tip is an **ancestor** of what you
are pushing. On 2026-11-23 this repository was in this state:

| Fact | Value |
|---|---|
| `origin/hackathon-mvp` | `2fc007a` — four QUE-006 commits (queue W1/W2, organization W3, audio assets, reports) |
| local working branch | `trial/que006-windows-ubuntu-merge` at `41ac51a` (preservation snapshot on top of `cd2f9ec`) |
| merge base | `37cf3d1` |
| `git rev-list --left-right --count origin/hackathon-mvp...HEAD` | `4  3` — four commits only on origin, three only locally |
| `git merge-base --is-ancestor origin/hackathon-mvp HEAD` | **no** |

So the Ubuntu remediation could not simply be pushed: the push would have been
rejected as non-fast-forward, and forcing it would have **erased the Windows QUE-006
work from the published branch**. The only honest publication is a real merge commit
whose second parent is `2fc007a` — after which `origin/hackathon-mvp` *is* an ancestor
and the push is a plain fast-forward.

That is the discipline in one line: **merge the remote into the work, then publish;
never rewrite the remote to match the work.**

### 7.2 Before publishing, always

```
git fetch origin
git rev-parse HEAD origin/hackathon-mvp
git merge-base --is-ancestor origin/hackathon-mvp HEAD && echo FF-OK || echo MERGE-NEEDED
git rev-list --left-right --count origin/hackathon-mvp...HEAD
git status --porcelain=v1 | wc -l          # must be 0 after the merge commit
git diff --name-only --diff-filter=U       # must be empty: no unresolved conflict
```

If `git rev-parse origin/hackathon-mvp` differs from the value recorded when the
merge was prepared, **stop**: the remote advanced, and the merge must be re-checked
(re-run the suites, re-resolve any new conflict) before it can be published.

### 7.3 Preserve the tree before a merge is committed

A preservation snapshot captures the *whole* working tree — staged, unstaged and
untracked — without touching the branch, the index of record, or the files:

```
export GIT_INDEX_FILE=/tmp/amsdp_snapshot.idx
git read-tree HEAD
git add -A                                   # respects .gitignore; adds untracked files
SNAP_TREE=$(git write-tree)
SNAP=$(git commit-tree "$SNAP_TREE" -p HEAD -p "$(git rev-parse MERGE_HEAD)" \
        -m "wip: preservation snapshot of the QUE-006 merge resolution")
unset GIT_INDEX_FILE
git branch wip/que006-publication-snapshot "$SNAP"
git diff --stat "wip/que006-publication-snapshot"     # must be empty
git diff --binary HEAD "$SNAP" > <backup>/que006-merge-resolution.patch
sha256sum <backup>/que006-merge-resolution.patch
```

`git stash`, `git reset --hard`, `git clean -fd` and `git checkout -- .` are **not**
part of this procedure and must never be used to "tidy up" a merge in this
repository: they are the three commands that have already cost this project a
working tree.

### 7.4 The merge commit itself

```
git add -A
git commit -m "Merge Windows and Ubuntu QUE-006 implementation"
```

* No squash. The two histories stay legible; the merge commit is the record that the
  Windows implementation and the Ubuntu remediation were reconciled.
* The merge message should name the owner decisions whose contract changed
  (for QUE-006: **D-1** foreign branch → `422`, **D-2** retired assignment stays
  inactive, **D-4** room sentence, **D-6** `completed`/`interrupted` vocabulary,
  **D** doctor queue-calling as an organization setting).
* Documentation that *describes* the merge belongs in the merge commit or in an
  immediate follow-up. A report that states the published hash cannot contain its own
  hash; that is expected, not a defect, and it is why the publication report is a
  second commit.

### 7.5 Publishing

```
git push origin HEAD:hackathon-mvp      # fast-forward only; never --force
git rev-parse origin/hackathon-mvp      # record the published hash
```

Record the hash in the publication report. If the push is rejected, the remote moved:
go back to §7.2. Do not "fix" a rejection with `--force` or `--force-with-lease`.

### 7.6 A note on branch ancestry that surprises people

`hackathon-mvp` locally held two commits (`0554f33`, `cd2f9ec` — the website content
proposals) that had **never been pushed**. Because the merge commit's first parent
chain contains them, publishing the merge also publishes those two commits. That is
correct (they are committed work) but it should be a conscious act: check
`git log --oneline origin/hackathon-mvp..HEAD` before pushing, and be able to name
every commit it will publish.


```yaml
  db:
    ports: ["127.0.0.1:5433:5432"]      # host-only; `_tools/*.sh` and alembic still work
```

The Windows workstation does **not** need LAN access to 5433: it runs its own
throwaway container (§5.3) and checks the application through port 3100. Confirm with
`ss -ltn` that only `127.0.0.1:5433` remains after the change.

| Python | 3.14.4 in `/home/shomonrobie/amsdp/.venv` | 3.12+ is the realistic floor; create your own venv — the host's `.venv` is not portable |

---

## 8. Gates — what must be green before anything is called ready

| # | Gate | Command | Evidence in this session |
|---|---|---|---|
| 1 | Frontend unit suite | `cd frontend && npm test` | **368 pass / 0 fail**, exit 0 |
| 2 | Frontend production build | `cd frontend && npm run build` | not re-run in this session; the trial merge's reports record `✓ Compiled successfully` (`docs/implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md`, `…_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md`) |
| 3 | Targeted backend suites | `pytest organization/tests queuing/tests doctor/tests/test_doctor.py appointment/tests/test_appointment_calendar_filters.py` | **262 passed, 0 failed** (7m13s) |
| 4 | Proxy table complete | `frontend/tests/next-config-rewrites.test.mjs` (part of gate 1) | pins voice-packs, platform defaults and every `/api/v1` prefix the UI actually calls — INT-4 cannot silently return |
| 5 | Container-layout import | `pytest organization/tests/test_container_layout_import.py` | imports `main` flat, exactly as `uvicorn main:app` does in the image, so a relative-import regression fails here instead of in a dead container |
| 6 | One migration head, applies from empty | `alembic heads` / `alembic upgrade head` on a throwaway DB | `c4d8e2a91f60 (head)`, upgrade exit **0** |
| 7 | Live origin smoke | browser at `http://<host>:3100` | done in the merge's own verification (queue page, claim, playback); **not** repeated in this session |

**Whole-tree backend run.** The full `pytest -q` on this host reported `682 passed,
109 errors, 0 failed` in 14m03s. The 109 errors are **all at fixture setup**, in two
files (`organization/tests/test_voice_packs_api.py`,
`queuing/tests/test_queue.py`), and all carry the same cause:
`psycopg2.errors.UndefinedTable: relation "voice_packs" does not exist` — the live
development database is two revisions behind (§1.4). Pointed at the migrated
throwaway database (§5.3) the same two files report **109 passed in 78s**, i.e. the
error count and the passing count are the same number. That is the correct way to run
them, and it is why a whole-tree run is evidence about *the database it ran against*
as much as about the code.

---

## 9. Data, secrets and the things that are never done

### 9.1 Never

* Never `docker compose ... down -v` on this host (`-v` deletes the database volume).
* Never `git reset --hard`, `git clean -fd`, `git stash` or `git checkout -- .` to
  "tidy" the tree — roll back with `git revert` (governance §9).
* Never `git push --force` (or `--force-with-lease`) to `hackathon-mvp`.
* Never edit the migration chain of an already-applied revision in place; ship a new
  forward-only revision.
* Never run tests against a database whose loss would matter. That includes the demo
  database.

### 9.2 Data you are responsible for

| Store | Where | Backup |
|---|---|---|
| Development DB | volume `amsdp_pg_data` | `_tools/pg_backup.sh` → `backups/…sql.gz` (not committed) |
| Demo DB | demo volume (`amsdp_demo`) | same script with the demo container/database name, or the demo is simply re-seeded |
| Audit trail | inside the database, append-only by design | covered by the database dump; never delete or rewrite audit rows |

### 9.3 Secrets

`.env` holds `POSTGRES_PASSWORD`, the demo account passwords and (optionally)
`AMSDP_JWT_SECRET`. Rules that already apply and that a Windows developer inherits:

* `.env` is gitignored and is never committed, pasted into a report, or echoed.
  `_tools/amsdp_stack.sh` and `_tools/pg_backup.sh` both source it without printing.
* The compose default JWT key (`dev-synthetic-key-replace-in-prod`) is a development
  placeholder. Before any exposure beyond a trusted LAN, set a real
  `AMSDP_JWT_SECRET` and `AMSDP_ENV=production` in `.env`.
* Demo credentials are in `docs/demo/AMSDP_Demo_Credentials_V1.0.md`; read them to
  operate a demo, never copy them into a document, log or commit message.

---

## 10. Handover checklist

Do these in order, once, when the Windows workstation takes over development.

1. [ ] Clone and fast-forward `hackathon-mvp` (§5.2). Confirm the tip equals the hash
       recorded in `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md`.
2. [ ] Create `.env` from `.env.example` with values transferred out of band; confirm
       `git status` does not list it (§9.3).
3. [ ] Create a throwaway test database (§5.3) and run `alembic upgrade head` against
       it; confirm one head.
4. [ ] Run both suites (§5.4): backend and `npm test`. The frontend must be 368/368 in
   this tree; anything else is a real change, not "flaky".
5. [ ] Apply the pending migrations to the **live** database before rebuilding
       anything: `alembic current` → `alembic upgrade head` → `alembic current`, after
       `_tools/pg_backup.sh` (§1.4, §4.3).
6. [ ] Run a branch of your own against a scratch database; keep `hackathon-mvp`
       clean for merges.
7. [ ] Open `http://192.168.68.108:3100` from Windows and confirm the browser console
       shows same-origin `/api/v1/...` calls answering `2xx` (§5.5).
8. [ ] Read §7 before your first push. If `git merge-base --is-ancestor
       origin/hackathon-mvp HEAD` says no, you are about to need a merge, not a push.
9. [ ] Read §1.2 and §11: four acceptance items are still open by design, and the
       Windows steps are unverified until steps 1–7 have actually run.

### 10.1 Stop and ask the owner when

* a test fails and the only way to make it pass is to weaken the assertion;
* a business contract would change (who may call a patient, what a room announces,
  what a branch assignment means) — that is an owner decision, not a bug fix;
* a migration would need a second head;
* data would have to be deleted, truncated or re-seeded;
* the remote advanced between fetch and push (§7.2).

---

## 11. What is still open, and who closes it

| Item | State after this session | Who / how |
|---|---|---|
| **B-8** human audibility of announcement playback | **NOT VERIFIED** — no automated artefact can prove a person hears the room speaker; the delivery records and the audio assets exist | a human, in the room, with the demo stack running |
| **D-5** documentation index numbering vs the tree | **NOT IMPLEMENTED as a renumbering** — the annex entry added by the publication report is deliberately *unnumbered* so it cannot claim a number the owner has not assigned; reconciling the existing numbering is an owner task | owner decision, then a docs-only commit |
| **D-7** manual-repeat delivery records | **NOT VERIFIED** — the repeat-path records are produced by the implementation and asserted by tests, but no manual scenario has been recorded as evidence | a scripted manual scenario on the host, logged in `docs/testing/` |
| **O-2** facility-level enable/language | **NOT VERIFIED** — the queue-calling configuration is organization-level today (§7.4 of the merge); per-facility overrides do not exist | owner decision on whether facility scope is in MVP; if yes, new migration + tests |
| **RBAC-R3** doctor assignment in the demo seed | **NOT VERIFIED** — the seed and the RBAC tests are green, but the specific "demo doctor is assigned to the branch that owns the queue" assertion has not been confirmed against the *seeded* demo data | run `_tools/verify_demo_login.sh` + inspect one doctor's assignments on the demo stack |
| PostgreSQL published on `0.0.0.0:5433` | **OPEN — owner decision** (§6.3); the change is one line and was not applied | owner approves, then `docker compose up -d db` + `ss -ltn` |
| **Live DB two revisions behind** (`a9c4e1f7b2d8` vs head `c4d8e2a91f60`) | **OPEN — release blocker for the QUE-006 features** (§1.4): `voice_packs` and `queue_announcement_deliveries` do not exist in the running database. Found by the full-suite run, confirmed by SQL, and explained by re-running the 109 erroring tests against a migrated database (`109 passed`) | run `_tools/pg_backup.sh`, then `alembic upgrade head`, then `_tools/amsdp_rebuild.sh` (§4.3) |
| No SSH server on the host | **OPEN — owner decision** (§6.1); today's transport is Git | owner |
| Windows workstation steps (§5) | **NOT VERIFIED** — written from the repository and the host's toolchain, never executed on Windows | the Windows developer, once, following §5–§10 |

Nothing in this list is a defect in the merged code. Each one is either an owner
decision or evidence that a machine or a human has to produce, and pretending
otherwise is exactly what the project's evidence standard (governance §7) forbids.

---

## 12. Evidence appendix — what was actually run

Everything below was executed in this session on the Ubuntu host. Paths under `/tmp`
are ephemeral; the durable record is this section plus
`docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md`.

| Check | Command | Result |
|---|---|---|
| `alembic` graph | `../.venv/bin/alembic heads` | one head, `c4d8e2a91f60` |
| Migration on empty DB | `AMSDP_DATABASE_URL=…:55460/amsdp alembic upgrade head` (container `amsdp-pubverify-pg`, `postgres:16-alpine`) | exit **0** |
| Frontend suite | `cd frontend && npm test` | **368 pass / 0 fail**, exit 0 (`/tmp/amsdp_fe_test.log`) |
| Targeted backend suites | `pytest organization/tests queuing/tests doctor/tests/test_doctor.py appointment/tests/test_appointment_calendar_filters.py` | **262 passed**, 0 failed, 7m13s (`/tmp/amsdp_be_targeted.log`) |
| Whole-tree backend suite, live DB | `bash /tmp/run_be_full.sh` → `pytest -q` | **682 passed, 109 errors, 0 failed**, 14m03s (`/tmp/amsdp_be_full.log`) |
| The 109 errors, on a migrated DB | `AMSDP_DATABASE_URL=…:55460/amsdp pytest -q organization/tests/test_voice_packs_api.py queuing/tests/test_queue.py` | **109 passed**, 78s (`/tmp/amsdp_be_err2.log`) |
| Live DB revision | `psql -tAc 'select version_num from alembic_version'` in `amsdp-db-1` | `a9c4e1f7b2d8`; `to_regclass('voice_packs')` → null |
| Container layout | `pytest organization/tests/test_container_layout_import.py` | passed |
| Proxy table | `node --test tests/next-config-rewrites.test.mjs` | passed (inside the frontend suite) |
| Announcement dedupe | `node --test tests/queue-announcement-dedupe.test.mjs` | passed (inside the frontend suite) |
| Containers | `docker ps` | 11 `amsdp-*` containers |
| Listening ports | `ss -ltn` | 3100, 5433, 8110–8117; **no :22** |
| Boot unit | `systemctl --user is-enabled/is-active amsdp-autostart.service` | `enabled`, `active` |
| Toolchain | python `--version`, node `--version`, `npm --version`, `docker --version`, `docker compose version` | 3.14.4 / v24.21.0 / 11.19.0 / 29.1.3 / 2.40.3 |

### 12.1 Documents this runbook deliberately does not duplicate

| Topic | Owner document |
|---|---|
| Restart, redeploy, rebuild and troubleshooting procedures | `docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md` |
| The one-command restart wrapper those procedures rely on | `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` |
| Boot behaviour and demo data refresh | `docs/deployment/AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` |
| Business rules the merge had to satisfy | `docs/product/AMSDP_Business_Rules_V1.0.md` |
| The merge itself, and the decisions it took | `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` |
| Navigation for all of the above | `docs/governance/AMSDP_Docs_Index_V1.0.md` |

