# AMSDP — Restart, Redeploy and Verify the Full Platform (V1.0)

> **Status:** verified on this host, 2026-11-16.
> **Scope:** answer one question — *"do I have to restart the platform to see a code change, and
> how do I do it without losing data?"* — and give a repeatable restart + verification procedure.
> **Where written:** `docs/deployment/` (§11 subject folder — this is deployment/runtime
> configuration, not a product or implementation report). Nothing was moved or renamed.
> **Companions, not superseded:**
> `deployment/AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` (crash/reboot auto-start, demo
> data refresh, the Docker-bridge fix), `deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md`
> (health probes, ports, hardening) and `README.md` §"Start / restart" (the one-line command
> table). This document adds the **code-change** case, which those three do not cover.

---

## 1. The answer, first

**No — the work already on this host needs no restart to be verified.** It is already running,
and that was measured, not assumed:

| Evidence | Result |
|---|---|
| Images rebuilt and containers recreated | `amsdp-frontend-1` up **49 min**, `amsdp-appointment-1` up **~1 h** (both recreated *after* the code changed, while the other eight stayed up for 11–29 h) |
| Container health | 10 / 10 `running / healthy` |
| New backend route is in the running image | `GET :8115/api/v1/appointments/list` without a token → **HTTP 401** (route present, auth enforced) |
| New backend route answers real data | with a token: `total=42`, `pages=9`, page 2 → 17 rows, `sort=patient` → A→Z, `q=%` → 0 |
| Changed UI page is served | `http://127.0.0.1:3100/appointments` → **HTTP 200** |
| Feature driven in a browser | real-Chrome run of the shipped page: **22 / 22** checks (§11 of the calendar report) |

**Yes — any *new* code change needs a rebuild + recreate of the services that carry it.** A
restart alone is not enough, for the reason in §2.

| What you changed | Minimum action | Typical cost (this host) |
|---|---|---|
| `frontend/**` | `_tools/amsdp_rebuild.sh frontend` | 1 image, ≈1–3 min |
| `backend/appointment/**` | `_tools/amsdp_rebuild.sh appointment` | 1 image, ≈10–20 s |
| `backend/common/**` | `_tools/amsdp_rebuild.sh` (auto-detects **all 8** backends) or `--all` | 9 images, ≈2–4 min |
| `docker-compose.yml` / `.env` only | `docker compose -p amsdp up -d` (no build) | seconds |
| Docs, tests, `_tools/` | nothing — no image contains them | — |
| A migration (`backend/alembic/versions/*`) | `python -m alembic upgrade head` (no image rebuild needed) — see §4.4 | seconds |

---

## 2. The rule that decides everything: code is baked into the images

`frontend/Dockerfile` is `COPY . . && RUN npm run build && CMD npm start`.
`backend/<service>/Dockerfile` is `COPY <service>/ ./` plus `COPY common/ ./common/`.
`docker-compose.yml` declares **no bind mounts** for code (only `db` has a named volume).

Two consequences that cause most "my change isn't there" confusion:

1. **`docker compose restart` does not deploy code.** It stops and starts the *same* container
   from the *same* image. It is the right tool for `.env`/compose changes and for clearing a
   wedged process — and the wrong tool after editing source.
2. **`backend/common/` is copied into all eight backend images.** A one-line change there needs
   eight rebuilds; rebuilding only the service you were thinking about leaves seven stale.

The full rebuild of everything is `AMSDP_BUILD=1 _tools/amsdp_stack.sh up`, which is correct but
rebuilds all ten images even for a one-line change — that is why §3 exists.


---

## 3. Fastest path after a code change (recommended)

`_tools/amsdp_rebuild.sh` (new in this task) rebuilds **only** the services whose source changed,
recreates just those containers, waits for real readiness and then verifies.

### 3.1 Look before you touch anything (read-only)

```bash
cd /home/shomonrobie/amsdp
_tools/amsdp_rebuild.sh --check
```

Real output on this host (2026-11-16), abbreviated:

```
==> Uncommitted changes: 84 file(s) in this tree
  images that carry them:
    - appointment
    - audit
    ...
    - scheduling
  (docs, tests, _tools and compose changes alter no image;
   a compose/env change only needs: docker compose -p amsdp -f docker-compose.yml up -d)

NAME                   IMAGE                SERVICE        STATUS                       PORTS
amsdp-appointment-1    amsdp-appointment    appointment    Up About an hour (healthy)   0.0.0.0:8115->8005/tcp
...
```

That list contains **all nine** services with an image, because `backend/common/` is modified in
this tree — exactly the trap in §2.2, reported instead of hidden.

### 3.2 Apply

```bash
_tools/amsdp_rebuild.sh                        # rebuild what changed (auto-detected)
_tools/amsdp_rebuild.sh appointment frontend    # or name services explicitly
_tools/amsdp_rebuild.sh --all                   # every image (frontend + 8 backends)
_tools/amsdp_rebuild.sh --no-cache              # clean build when a layer cache lies
```

It runs, in order: `docker compose build <targets>` → `docker compose up -d --no-deps <targets>`
→ readiness wait (`/health/ready` on all 8 backends, `pg_isready` for `db`, `GET /` for the
frontend, 240 s default) → `--verify`.

### 3.3 Verify without changing anything

```bash
_tools/amsdp_rebuild.sh --verify
```

Real output:

```
==> Verifying the running stack (read-only)
  SERVICE        STATE     HEALTH   PROBE
  db             running   healthy  ok
  identity       running   healthy  ok
  organization   running   healthy  ok
  patient        running   healthy  ok
  doctor         running   healthy  ok
  scheduling     running   healthy  ok
  appointment    running   healthy  ok
  queuing        running   healthy  ok
  audit          running   healthy  ok
  frontend       running   healthy  ok

==> Deployed-code checks (through the published API)
  appointments/list without a token: HTTP 401 (route deployed, auth enforced)  ok
  http://127.0.0.1:3100/appointments: HTTP 200 (200/307 = page present, 5xx = broken build)
```

The `401` line is the useful one: it proves the newest route exists **in the running image** and
needs no credentials, so it is a safe "is my code actually live?" check that can be run any time.

### 3.4 What the script will not do

No `docker compose down`, no volume removal, no re-seed, no database reset, no `git add`/`commit`/
`reset`, and it never prints `.env` values, the JWT secret or the database URL. `--check` and
`--verify` are pure reads.

---

## 4. Restarting the **whole** platform

### 4.1 When a full restart is actually the right move

| Situation | Command |
|---|---|
| You edited `.env` / `docker-compose.yml` | `_tools/amsdp_stack.sh restart` |
| A container is wedged but its image is current | `_tools/amsdp_stack.sh restart` |
| You want every image rebuilt from the current tree | `_tools/amsdp_rebuild.sh --all` **or** `AMSDP_BUILD=1 _tools/amsdp_stack.sh up` |
| The host was rebooted | nothing — `restart: unless-stopped` ×10 plus the systemd user unit `amsdp-autostart.service` bring it back (see the Auto-Start document) |
| A code change in one or two services | **§3**, not a full restart |

### 4.2 The full-platform commands, in order of preference

```bash
cd /home/shomonrobie/amsdp

_tools/amsdp_stack.sh status     # 1. what is running now (read-only)
_tools/amsdp_stack.sh restart    # 2. graceful restart of all ten services, data kept
_tools/amsdp_stack.sh up         # 3. or: start/resume — idempotent, waits for readiness
AMSDP_BUILD=1 _tools/amsdp_stack.sh up   # 4. full rebuild of all images, then start
_tools/amsdp_stack.sh logs [svc] # 5. follow logs (all, or one service)
```

`amsdp_stack.sh` already: uses the one `docker-compose.yml` (no second orchestration), refuses to
start when the isolated `amsdp_demo` stack holds the same ports, waits for real `/health/ready`
probes before printing success, and never runs `down` or touches volumes.

### 4.3 The same thing in raw compose, if you prefer no script

```bash
cd /home/shomonrobie/amsdp
docker compose -p amsdp -f docker-compose.yml ps
docker compose -p amsdp -f docker-compose.yml up -d                 # start/resume
docker compose -p amsdp -f docker-compose.yml up -d --build          # rebuild everything
docker compose -p amsdp -f docker-compose.yml restart                # restart, same images
docker compose -p amsdp -f docker-compose.yml up -d --build appointment frontend   # one or two services
```

**Never** add `-v` / `--volumes`, and never `down` to "clean up": the database lives in the named
volume `amsdp_amsdp_pg_data`, and removing it destroys every patient, appointment and audit row.
`down` (without `-v`) is only for the Docker-network recreation described in the Auto-Start
document.

### 4.4 What a restart does *not* do

- **It never applies migrations.** No Dockerfile and no compose service runs `alembic`; the schema
  is migrated deliberately:

  ```bash
  cd /home/shomonrobie/amsdp/backend
  set -a; . ../.env; set +a
  python -m alembic upgrade head
  ```

  (`db` publishes **5433** to the host, so host-side alembic reaches it.) The calendar work in this
  release added **no** migration, so this step was not needed — it is documented, not exercised.
- **It never re-seeds demo data.** The idempotent seed runs only from the boot unit
  (`_tools/amsdp_autostart.sh`), by design.
- **It never changes `.env`.** `POSTGRES_PASSWORD` and `AMSDP_JWT_SECRET` must already be set;
  compose fails fast with a clear message if the password is missing.


---

## 5. Verification ladder (cheap → full)

Each rung answers a different question; a green lower rung does not imply a higher one.

| # | Question | Command | Expected |
|---|---|---|---|
| L0 | Is anything running? | `docker compose -p amsdp ps` | 10 services, `(healthy)` |
| L1 | Are all services ready? | `_tools/amsdp_rebuild.sh --verify` | 10 × `ok`, exit 0 |
| L2 | Is the *new* code in the image? | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8115/api/v1/appointments/list` | `401` |
| L3 | Does the UI build serve? | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3100/appointments` | `200` (or `307` to `/login` when signed out) |
| L4 | Does data flow end-to-end? | sign in at <http://localhost:3100> and open **Appointments → তালিকা** | rows with doctor/branch names, working search, pager |
| L5 | Does the whole surface still work? | real-browser script (calendar report §11.7) | 22/22 checks |

L0–L3 were run for this document. L4/L5 were run earlier in the same session against the same
containers (42 rows / `pages=9`; 22/22 browser checks).

---

## 6. When it goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| Change is not visible, container "Up 3 days" | container never recreated — `restart` re-runs the old image | `_tools/amsdp_rebuild.sh <svc>` (§3.2) |
| One backend serves new behaviour, another does not | `backend/common/` changed but only one image rebuilt | `_tools/amsdp_rebuild.sh --all` |
| `port is already allocated` | the `amsdp_demo` stack is running | `docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down` |
| Frontend `502`, some `/health/ready` hang while `/health` is `200` | the Docker bridge lost forwarding after a daemon restart | `docker compose -p amsdp down` (no `-v`) then `_tools/amsdp_stack.sh up` — recreates the network, keeps data |
| Login fails after a rebuild | services got different `AMSDP_JWT_SECRET` values | keep it in one `.env`; every service must share it |
| `POSTGRES_PASSWORD` / interpolation error on `up` | `.env` missing or the variable unset | copy `.env.example` → `.env` and fill it in |
| Build fails on `npm run build` | the change does not compile — the image is *not* replaced, the old one keeps serving | fix the build; `npm run build` in `frontend/` reproduces it locally |


---

## 7. Scope and open items

- No product, scheduling or business rule is expressed here; this is runtime procedure only.
- **O-W (new):** `_tools/` is not tracked by git (it is untracked on this host, alongside the
  earlier stack scripts). `_tools/amsdp_rebuild.sh` therefore exists on disk but not in history;
  whether `_tools/` should be committed is an owner decision, not taken here.
- **O-X (new):** the readiness wait covers HTTP readiness only. It does not assert business
  behaviour — L4/L5 in §5 remain the honest checks for that, and a green `--verify` is not a
  substitute (`.clinerules` §7 evidence standard).
- **O-Y (new, pre-existing):** `docs/governance/AMSDP_Docs_Index_V1.0.md` recorded "2"
  `docs/chatgpt/` planning files; the tree holds **4**. The header now states the verified count
  (74 on disk = 70 in the `docs/` trees + 4 chatgpt) and the discrepancy is left visible rather
  than silently reconciled, because which two extra files are intended is an owner call.
- `_tools/amsdp_rebuild.sh` was validated with `bash -n` and by running its **read-only** modes
  (`--check`, `--verify`) on this host. Its apply path (`build` + `up -d --no-deps`) is the same
  compose invocation already proven earlier in the session when `appointment` and `frontend` were
  rebuilt and recreated; it was **not** re-run for this document because nothing needed rebuilding.

---

## 8. Governance and evidence compliance

| Requirement | How it was met |
|---|---|
| `.clinerules` §4 (Docker/deployment domain) | `saas-cicd-workflow.md` as adapted in the governance assessment: honest CI state, no destructive git, no invented capability |
| §11 output location | written to `docs/deployment/`, an existing subject folder; no new folder, no collision |
| §12 index currency | row added to `docs/governance/AMSDP_Docs_Index_V1.0.md` in the same task |
| §3 non-negotiables | no secret printed; no schema change; audit trail untouched; nothing staged or committed |
| §7 evidence standard | IMPLEMENTED (script + document) · TESTED (`bash -n`, `--check`, `--verify` exit 0) · VERIFIED (the 10/10 table, the `401` and the `200` came from the running containers) |
| §9 execution boundaries | only read-only probes were run; no restart, no rebuild, no test suite was triggered by this task |
| Skills | none installed (`.clinerules` §5) — governance documents used instead |

