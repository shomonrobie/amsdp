# AMSDP — Post-Sequence-4 Deployment Hardening Report

| | |
|---|---|
| **Report id** | AMSDP-HARDENING-POST-SEQ4 |
| **Date** | 2026-11-10 |
| **Supersedes** | the "unresolved findings" section (Seq-4 acceptance report §7) for the seven items below |
| **Tree state** | uncommitted working tree; no commit, push, merge or deploy performed |
| **Verdict** | **Six of seven open findings are closed and verified against a running stack. One (SEQ4-DEPLOY-D1) is closed by an explicit topology decision, not by code.** No new finding is left unresolved at P1/P2. |

---

## 1. Mandate and scope

The Sequence-4 acceptance verification report
(`docs/audit/AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md`) closed with
seven open findings that were **not** workflow-correctness defects but
deployment/operations breadth:

| Id | Class | What it said |
|---|---|---|
| SEQ4-DEPLOY-D1 | D (deploy) | `backend/app/main.py` is a "Hello World" stub — there is no aggregated backend app |
| SEQ4-DEPLOY-D2 | D (deploy) | `docker-compose.yml` has exactly one healthcheck (the database); the eight services and the frontend have none, so `depends_on` guarantees no application-tier start order |
| SEQ4-CORS-D1 | D (deploy) | No `CORSMiddleware` anywhere; the frontend works only because Next.js proxies `/api/*` |
| SEQ4-THROTTLE-D1 | D (deploy) | Login-throttle state is per-process → a second worker/replica multiplies the allowance |
| SEQ4-INDEX-P3 | P3 | `tracking_tokens` carries a plain index redundant with its unique constraint |
| SEQ4-TZ-P3 | P3 | Resolving `organizations.timezone` needs `zoneinfo` data in the image; a tzdata-less base image silently falls back to the container zone |
| LEGACY-TESTS-P1 | P1 | Seven test modules were written against the pre-database in-memory stores and were skipped — they asserted nothing |

This pass had one job: **turn those seven rows into a stated disposition with
evidence**, and stop claiming "the suite is green" while one third of it was
quarantined.

Scope boundary: no product behaviour was changed, no endpoint added or removed,
no authorization rule relaxed, no business rule reinterpreted, no schema object
renamed or dropped except the duplicated index named in SEQ4-INDEX-P3.

---

## 2. Disposition of the seven findings

| Id | Before | Now | Evidence level |
|---|---|---|---|
| SEQ4-DEPLOY-D2 | 1 healthcheck (db only) | All 8 services expose `GET /health` (liveness, no DB) and `GET /health/ready` (readiness, `SELECT 1`); compose healthchecks every service **and** the frontend, all 8 services gate on `db: service_healthy` | **VERIFIED** — 16 probes answered 200 in the running stack; start-order log captured (§5) |
| SEQ4-DEPLOY-D1 | Ambiguous stub that looks like the backend entry point | **Closed by decision**: the runtime is the eight per-service apps behind the Next.js proxy. The stub is annotated as a non-entry-point and is still built by nothing | **VERIFIED** — the whole API answered through `:3100` (§5.3); stub annotated (§3.8) |
| SEQ4-CORS-D1 | No CORS; browser only works via rewrite | **Closed by the same decision**: one public origin (the frontend) and no browser-to-backend origin, so no CORS middleware is added or needed | **VERIFIED** — login + 4 protected reads through `:3100`, 401 without a token (§5.3) |
| SEQ4-THROTTLE-D1 | In-process dict, per-worker allowance | Throttle state moved to PostgreSQL (`login_attempts`, migration `d4b2c8e1f7a3`) with `pg_advisory_xact_lock` serialising count-then-insert | **VERIFIED** — 20×`401` then `429` + `Retry-After: 60`, and 20 rows readable in `login_attempts` from another process (§5.4) |
| SEQ4-INDEX-P3 | `ix_tracking_tokens_hash` duplicates the unique constraint's index | Dropped by forward-only, idempotent migration `e6c1a9b3d5f8` | **VERIFIED** — `pg_indexes` on the running database lists no `ix_tracking_tokens_hash`; `alembic check` is clean (§6) |
| SEQ4-TZ-P3 | Unverified `zoneinfo` availability in the service image | Verified in the **image**, not just the venv: 486 IANA zones, `ZoneInfo('Asia/Dhaka')` resolves, `operational_today()` returns the facility day | **VERIFIED** (§5.5), with a stated condition (§8) |
| LEGACY-TESTS-P1 | 7 modules skipped | All 7 rewritten against the real database, plus a shared support module and one `conftest.py` | **TESTED** — 112 tests, green both isolated and in the full suite (§4) |

No finding was silently dropped, and none is marked resolved on the strength of
"the code exists".

---

## 3. Changes delivered

### 3.1 Liveness and readiness — `backend/common/health.py` (SEQ4-DEPLOY-D2)

One module, imported by all eight services (`install_health(app, "<service>")`),
deliberately exposing **two** endpoints:

* `GET /health` — liveness only. It answers from the ASGI process and **never
  touches the database**. A database outage is not a reason to restart a web
  process; restarting one only adds connection churn while the database is down.
* `GET /health/ready` — readiness. It runs `SELECT 1` through the shared engine
  and returns `503 {"detail": "database unavailable"}` on failure. Compose gates
  the application tier on this, so no container joins the network before it can
  serve.

Both are unauthenticated by design (a healthcheck cannot present a token) and
leak nothing but the service name — no tenant ids, no DSN, no driver error text
(the exception body is replaced with a fixed string precisely because a
driver error can contain host, user and database names).

Verified call sites: `appointment`, `audit`, `doctor`, `identity`,
`organization`, `patient`, `queuing`, `scheduling` — eight of eight.

### 3.2 `docker-compose.yml` — rewritten around the real topology

| Change | Reason |
|---|---|
| `x-healthcheck-defaults` anchor (10 s / 5 s / 5 retries / 20 s start period) and a per-service `test` | one shape, no drift between services |
| `x-db-gate: {db: {condition: service_healthy}}` on all 8 services | application-tier start order, which `depends_on` alone never gave (SEQ4-DEPLOY-D2) |
| `x-backend-env` anchor: one `AMSDP_DATABASE_URL` **and** one `AMSDP_JWT_SECRET` for every service | a service signing/validating with a different secret 401s every authenticated call — the classic multi-service foot-gun |
| `frontend` depends on `identity: service_healthy` | the proxy must not come up against a dead upstream |
| Header comment naming the topology decision (single public origin, no aggregate app, therefore no CORS) | the decision is recorded where a deployer looks, not only in this report |
| `AMSDP_JWT_SECRET: ${AMSDP_JWT_SECRET:-dev-synthetic-key-replace-in-prod}` | the default is the value `common/auth.py` already falls back to, and the file says plainly that a real key goes in the environment |

`docker compose config` was validated before the run (§5.1), and the demo
override `docker-compose.demo.yml` is an *override* of this file, so it inherits
every healthcheck rather than duplicating them.

### 3.3 The audit service was unstartable — fixed with the compose rewrite

`backend/audit/` built from the wrong context, shipped no `common/` package and
no PostgreSQL driver, so `docker compose up` could not bring the audit service
up at all. Its `Dockerfile` and `requirements.txt` now match the other seven
(same context `./backend`, `COPY common/ ./common/`, `psycopg2-binary`), and its
`main.py` imports `common.health` like every sibling. In §5 the audit service
builds, becomes healthy, answers `200` on an authenticated read and `401`
without a token — the same container that previously could not start.

### 3.4 Durable login throttling — `common/login_throttle.py` + migration `d4b2c8e1f7a3`

Sequence 4 throttled `/api/v1/staff/login` from a module-level `dict` in
`identity/main.py`. With N uvicorn workers (or N replicas — layouts M8 §5.2
allows) an attacker received **N × the allowance**, and every restart cleared
all buckets. SEQ4-THROTTLE-D1 was exactly that: a control that looked present
and was ineffective in the deployment shapes we intend to run.

The state now lives in the `login_attempts` table in the PostgreSQL instance
every service already shares:

| Property | Implementation | Why it matters |
|---|---|---|
| Shared across processes | row per attempt, `count` query per bucket | the allowance is the allowance, not the allowance × workers |
| Exact under concurrency | `pg_advisory_xact_lock(hashtext(key))` serialises count-then-insert | without it two simultaneous attempts both read "19" and both pass |
| Sliding window, not fixed counter | stored `attempted_at` timestamps, `>= now − window` | a burst at a bucket boundary cannot double the rate |
| Bounded table | rows older than 600 s pruned on every call, index-covered | an abandoned bucket cannot grow the table without limit |
| Keyed on (client IP, username) | both, capped and case-folded | one noisy user cannot lock out a shared office NAT; one IP cannot spray every account silently |
| **No account lockout** | saturation answers `429`, never `403`/`423` | lockout converts a rate limit into a denial-of-service tool against a known username |
| Success clears the bucket | `clear_bucket()` on the success path | a legitimate user recovers immediately instead of waiting out the window |
| Fails **open**, loudly | throttle errors log a warning and let the attempt continue | the credential check that follows reads the same database, so a broken database cannot become an authentication bypass |
| Only rate-limit state stored | client IP, capped username, timestamp | no password, token or request body is persisted, and `audit_events` is untouched (it stays append-only) |

Migration `d4b2c8e1f7a3_add_login_attempts` (revises `b7c1e4d90a52`) is
forward-only and idempotent: the table and both indexes are created only when
absent, `downgrade` drops the table only when present.

Live behaviour in the containerised stack — 22 attempts on a throwaway
username, then a direct read of the table:

```
codes [401 ×20, 429, 429]      retry_after 60
login_attempts | throttle-probe | 20          <- read from another process
```

`Retry-After` is emitted on the refusal; the probe rows were deleted afterwards.

### 3.5 Redundant index removed — migration `e6c1a9b3d5f8` (SEQ4-INDEX-P3)

`a1f2b3c4d5e6` created `tracking_tokens` with **both** `UniqueConstraint('token_hash')`
(which PostgreSQL implements as a unique B-tree on that column) **and** a plain
`ix_tracking_tokens_hash` on the same column. The plain index served no access
path the unique index does not serve, and cost a second index write on every
INSERT/UPDATE/DELETE.

`e6c1a9b3d5f8_drop_redundant_tracking_token_index` (revises `d4b2c8e1f7a3`)
drops it with `DROP INDEX IF EXISTS`, so a re-run is a no-op; `downgrade`
recreates it with `CREATE INDEX IF NOT EXISTS`, so the revision rolls back
cleanly without duplicating the object. Both are guarded on `has_table`, so the
migration is safe on an environment where `tracking_tokens` does not exist yet.

### 3.6 Zoneinfo in the image (SEQ4-TZ-P3) — verified, not patched

`common/timeutil.py` resolves `organizations.timezone` with `zoneinfo` and never
raises: without tz data it falls back to the process zone. That fallback is
right for availability and wrong for correctness — a container with no tz data
would silently file a visit under the wrong facility day, which is the defect
SEQ4-TZ-P1 repaired. The finding therefore asked for a **verification**, not a
patch, and §5.5 performs it inside the built image rather than in the developer
venv.

### 3.7 LEGACY-TESTS-P1 — seven modules rewritten against the database

The seven quarantined modules asserted against private in-memory dicts
(`_patients_db`, `_orgs_db`, `_appointments_db`, `_users_db`, …) that no longer
exist, so they could not have been passing. They are rewritten, not deleted:

| Module | Tests | What it now exercises |
|---|---|---|
| `appointment/tests/test_appointment.py` | 13 | booking, listing, status transitions, permission refusals, tenant scoping |
| `appointment/tests/test_reschedule.py` | 6 | reschedule as two rows plus a link between them; edge cases asserted in the database |
| `doctor/tests/test_doctor.py` | 14 | create/read/update, org derived from the token (body `organization_id` ignored), scoped counts |
| `organization/tests/test_organization.py` | 20 | orgs, branches, `/me/branches`, cross-tenant 404s |
| `patient/tests/test_patient.py` | 16 | registration, search, branch scoping, age derivation, merge-route absence |
| `scheduling/tests/test_scheduling.py` | 22 | schedule CRUD, slot templates, capacity, permission matrix |
| `tests/test_e2e.py` | 21 | the MVP workflow, one token at a time, across all eight services |

Two supporting pieces:

* `backend/tests/amsdp_test_support.py` — `ensure_org` / `ensure_doctor` /
  `ensure_user` (idempotent reference rows), `purge_org` (deletes only the
  business rows of one organization, in FK order), `token` / `headers` (signs a
  **real** JWT from a real `staff_users` row, so the tests run through
  `common.auth.get_current_user` → role → permission exactly as production
  does), plus `db_session`, `uniq` and `load_app`.
* `backend/conftest.py` — puts `backend/` and `backend/tests/` on `sys.path`
  once, replacing the per-file `sys.path.insert` dance. It sets no environment
  variable and patches no product code; the database URL still comes from
  `AMSDP_DATABASE_URL`.

Three conventions make them safe on a shared database:

1. **Reference rows are created once and never deleted** — organizations,
   branches, doctors and staff users are referenced by foreign key from the
   append-only `audit_events` trail, so deleting them would rewrite history.
2. **Owned business rows are purged** before *and* after every test by an
   autouse `purge_org(<this module's org>)`, in FK order, scoped to that org id
   alone — before, so a crashed earlier run cannot poison the assertions; after,
   so a completed run leaves the database as it found it.
3. **Count assertions are scoped by `uniq()` names**, because a shared database
   accumulates rows across runs; an unscoped `count(*)` is a flake waiting for
   the second run.

`load_app(service)` imports `<service>/main.py` with that service's directory on
`sys.path` **only for the duration of the import** — `identity` resolves its
Pydantic schemas with a bare `from models import …`, and leaving all eight
directories on the path lets one service's `models` shadow another's. That
shadowing is the failure mode the abandoned `test_e2e.py` hit by importing eight
services by file path.

### 3.8 SEQ4-DEPLOY-D1 — decided, then annotated

The decision: **AMSDP has no aggregate backend app.** The runtime is the eight
per-service applications, each built from its own Dockerfile, with the frontend
as the single public origin (`next.config.js` rewrites `/api/v1/<prefix>` to the
owning service). Building an aggregate app would create a divergent second copy
of eight routers and a second place to get authorization wrong.

`backend/app/main.py` therefore stays a stub — and its docstring now says what
it is, which eight apps are the runtime, that compose builds none of it, and
that deploying `app.main:app` would answer `GET /` with `Hello World` and 404
every real route. A stub that *looks* like an entry point is the defect
SEQ4-DEPLOY-D1 named; an annotated non-entry-point is not.

---

## 4. Test results

### 4.1 Full suite

```
cd backend && ../.venv/bin/python -m pytest -q
289 passed, 94 warnings in 169.32s (0:02:49)
```

0 failed, 0 skipped, 0 errors, 0 xfail. Run **three** times on the way here:
`289 passed` in 112.17s before the fixture teardown purge was added, `289 passed`
in 169.32s after it (the second run also purges the rows its predecessor left),
and `289 passed, 110 warnings in 114.19s` as a final confirmation on the exact
delivered tree (§10). The warning count moves between runs (94 → 110) because
pytest de-duplicates warnings per collection order; no warning is an error, and
there is no `pytest.ini` / `pyproject.toml` / `setup.cfg` in this tree, so
nothing is filtered out. Before this
pass the same command reported `177 passed / 7 skipped / 0 failed` — the 177
pre-existing tests are still green and still counted; the difference is the 112
rewritten tests that used to be skipped.

### 4.2 Isolation — each rewritten module run alone

A module that only passes because another module ran first is not a test, so
each of the seven was executed on its own, against the **final** tree:

| Command (`cd backend`) | Result |
|---|---|
| `pytest appointment/tests/test_appointment.py` | `13 passed` in 6.23s |
| `pytest appointment/tests/test_reschedule.py` | `6 passed` in 3.87s |
| `pytest doctor/tests/test_doctor.py` | `14 passed` in 13.64s |
| `pytest organization/tests/test_organization.py` | `20 passed` in 18.39s |
| `pytest patient/tests/test_patient.py` | `16 passed` in 10.28s |
| `pytest scheduling/tests/test_scheduling.py` | `22 passed` in 26.17s |
| `pytest tests/test_e2e.py` | `21 passed` in 3.81s |

`13 + 6 + 14 + 20 + 16 + 22 + 21 = 112`, and `112 + 177 = 289` — the module
counts reconcile with the suite total, which is what makes the green run
checkable rather than asserted.

### 4.3 What "green" means here

Every rewritten test drives the **real service app** —
`TestClient(load_app("<service>"))`, i.e. the same `main.py` the container runs —
and asserts through `SessionFactory` / `db_session()`, i.e. reads the row back
from PostgreSQL. There is no monkeypatched store, no fake session and no
`organization_id` injected from a test body: the tenant comes from a signed
token, exactly as in production. So a passing assertion means **persisted**, not
"the dict remembered it".

Two deliberate non-tests, recorded so nobody "fixes" them later:

* `patients/merge` does not exist as a POST route (the path resolves to
  `GET /api/v1/patients/{patient_id}` → `405`); the test asserts the absence,
  because a merge endpoint is a scope decision, not a missing line.
* `tests/test_e2e.py::test_13_audit` cannot POST an audit event: `audit_events`
  is written by the services themselves and is append-only by rule, so the test
  asserts that a client cannot write one.

---

## 5. Deployment verification (live, bounded)

Everything in this section was executed against this tree. No image was pushed,
no host was deployed, no production DSN was touched.

### 5.1 Build

```
docker compose build identity organization patient doctor scheduling appointment queuing audit
  -> all 8: Built
docker compose build frontend
  -> Built
```

`docker compose config -q` validated the file before the run (anchors
resolved, no duplicate keys, RC=0). The frontend image was built as well,
because the single-origin claim in §5.3 is only worth verifying end-to-end.

### 5.2 Start order — the point of SEQ4-DEPLOY-D2

`docker compose up -d` output, unedited excerpt:

```
 Container amsdp-appointment-1  Recreate
 ...
 Container amsdp-db-1  Healthy          <- eight times, once per service
 Container amsdp-doctor-1  Starting
 ...
 Container amsdp-identity-1  Started
```

Every service waited for `db: condition: service_healthy`; the frontend waited
for `identity: service_healthy`. Final state — **ten containers, ten healthy**:

```
amsdp-appointment-1   Up (healthy)
amsdp-audit-1         Up (healthy)
amsdp-db-1            Up (healthy)
amsdp-doctor-1        Up (healthy)
amsdp-frontend-1      Up (healthy)
amsdp-identity-1      Up (healthy)
amsdp-organization-1  Up (healthy)
amsdp-patient-1       Up (healthy)
amsdp-queuing-1       Up (healthy)
amsdp-scheduling-1    Up (healthy)
```

The healthcheck for each service is the readiness endpoint, meaning "healthy"
here asserts *database reachable through that service's own engine*, not merely
"process alive".

### 5.3 The API really serves — directly and through the single public origin

Sixteen health probes, answered by the containers on host ports 8110–8117:

```
identity      /health 200 {"status":"ok","service":"identity"}      /health/ready 200 {"status":"ready","service":"identity"}
organization  /health 200 ... /health/ready 200 ...
patient       /health 200 ... /health/ready 200 ...
doctor        /health 200 ... /health/ready 200 ...
scheduling    /health 200 ... /health/ready 200 ...
appointment   /health 200 ... /health/ready 200 ...
queuing       /health 200 ... /health/ready 200 ...
audit         /health 200 ... /health/ready 200 ...
```

Authenticated reads against each service, using **one** token obtained from the
identity container — which is also the proof that all eight containers share one
JWT secret, the failure the `x-backend-env` anchor exists to prevent:

| Service | Route | Result |
|---|---|---|
| identity | `/api/v1/staff/users` | `200` |
| organization | `/api/v1/orgs` | `200` |
| patient | `/api/v1/patients` | `200` |
| doctor | `/api/v1/doctors` | `200` |
| scheduling | `/api/v1/schedules` | `200` |
| appointment | `/api/v1/dashboard/today` | `200 {"date":"2026-11-10",...}` |
| queuing | `/api/v1/queue?date=…&doctor_id=…` | `200` |
| audit | `/api/v1/audit/organization/demo-org-001` | `200 []` |
| audit (same route, no token) | — | `401 {"detail":"authentication required"}` |

`422` responses seen while probing (queuing without its required `date` and
`doctor_id`) are validation refusals *after* authentication — they confirm the
token was accepted, not that it was rejected.

Through the frontend, i.e. the deployment shape a browser actually uses
(`http://127.0.0.1:3100`):

```
proxy login             200      (POST /api/v1/staff/login  -> identity)
home                    200      HTML
proxy orgs              200      (-> organization)
proxy dashboard today   200      (-> appointment)
proxy audit             200      (-> audit)
proxy patients noauth   401      (-> patient, refused as designed)
```

This is what closes SEQ4-DEPLOY-D1 and SEQ4-CORS-D1 as **verified**, not
argued: one public origin serves the entire API, browser requests are
same-origin, and no `CORSMiddleware` is required because no browser talks to a
backend origin.

### 5.4 Throttle behaves in the deployed stack (SEQ4-THROTTLE-D1)

```
22 × POST /api/v1/staff/login  (username: throttle-probe, wrong password)
codes        [401 ×20, 429, 429]
retry_after  60
```

and, read from a *different* process (the database container), the state is
durable and shared:

```
select username, count(*) from login_attempts group by username;
throttle-probe|20
```

The probe rows were deleted after the check (`delete from login_attempts where
username='throttle-probe'`), leaving `login_attempts` empty.

### 5.5 Time-zone data inside the image (SEQ4-TZ-P3)

Run **inside** the built backend image, not in the host venv:

```
docker run --rm amsdp-appointment:post-seq4 python -c "import zoneinfo; print(len(zoneinfo.available_timezones()))"
486

docker run --rm amsdp-appointment:post-seq4 python -c "from common import timeutil; print(timeutil.operational_today(), timeutil.facility_zone())"
2026-11-10 Asia/Dhaka

TZPATH  ('/usr/share/zoneinfo', '/usr/lib/zoneinfo', '/usr/share/lib/zoneinfo', '/etc/zoneinfo')
pip show tzdata  -> (not installed; the zones come from the base image's system tzdata)
```

So the facility day resolves from `organizations.timezone` in the image as
built. Condition, stated rather than assumed: the zones come from the
`python:3.13-slim` **system** tz database, not from a pinned dependency. §8
records what that implies for a future base-image change.

---

## 6. Database and migration verification

### 6.1 Migration chain

Nine revisions exist in `backend/alembic/versions/`; the two added by this pass
are the tail of a single linear chain (verified from each file's
`down_revision`):

```
5f3fce6757cf  initial_schema
ccf34da72c1b  add_queue_sequences
c7d3601e2486  add_audit_branch
9d8a1f2b3c4d  add_staff_doctor_link
3c8e5d0a9b2f  add_patient_age
a1f2b3c4d5e6  add_tracking_tokens
b7c1e4d90a52  add_notifications
d4b2c8e1f7a3  add_login_attempts                      <- this pass
e6c1a9b3d5f8  drop_redundant_tracking_token_index     <- this pass (head)
```

Commands and results (database `amsdp` on 127.0.0.1:5433):

```
cd backend && ../.venv/bin/python -m alembic upgrade head    -> RC 0
cd backend && ../.venv/bin/python -m alembic current
  e6c1a9b3d5f8 (head)
cd backend && ../.venv/bin/python -m alembic check
  No new upgrade operations detected.
```

`alembic check` returning clean is the important one: the models in
`common/models.py` and the migration chain agree, so there is **no pending
model-vs-schema drift** — the new `LoginAttempt` model is exactly what
`d4b2c8e1f7a3` creates, and the dropped index is not re-declared in the model.

### 6.2 The index is really gone (SEQ4-INDEX-P3, read from the live database)

```
select indexname from pg_indexes where tablename='tracking_tokens';
tracking_tokens_appointment_id_key
tracking_tokens_pkey
tracking_tokens_token_hash_key        <- the unique constraint's index; kept
```

No `ix_tracking_tokens_hash`. The unique index that serves the only access path
(hash equality) is intact, so the drop removes a write cost and changes no plan.

### 6.3 Migration-safety properties, stated as properties

| Property | Why it holds |
|---|---|
| Forward-only | neither revision edits or deletes existing data; `add_login_attempts` creates a table, `drop_redundant_…` drops one index |
| Idempotent | `has_table` / `get_indexes` guards + `IF EXISTS` / `IF NOT EXISTS`; re-applying either revision on an environment that already has the object is a no-op |
| Safe on an empty environment | `e6c1a9b3d5f8` returns early when `tracking_tokens` does not exist yet, so a fresh `upgrade head` cannot fail on ordering |
| Reversible where it claims to be | `downgrade` drops the table only if present; the index `downgrade` recreates it only if absent |
| No ad-hoc DDL | both changes are Alembic revisions in `backend/alembic/versions/`; nothing was applied by hand to any database |

### 6.4 Test-suite footprint on the shared database

The rewritten modules are safe to run against the development database *and*
leave it as they found it. Read after the final full-suite run:

```
organizations matching 'legacy-%'                              13   <- reference rows
patients / appointments / schedules / queue entries in them     0   <- purged
doctors / branches in them                            117 / 36   <- reference rows, kept
tracking_tokens whose appointment no longer exists              0
login_attempts                                                  0
```

Re-read after the third (final-tree) run, same numbers — so the teardown purge
holds on a repeat run, not just the first one.

The purge runs both **before and after** each test (`purge_org(ORG)` either side
of the fixture's `yield`), which is why a completed run leaves zero business rows
of its own organisations; an earlier revision of the fixtures purged only on the
way in and left the last test's rows behind (8 patients and 3 appointments across
the 13 orgs were observed and are gone now).

The 13 organizations are the reference rows the rewritten modules create
idempotently (`legacy-appt-org`, `legacy-doc-org`, `legacy-e2e-org`, …). They are
**not deleted by the suite and must not be**: `audit_events` is append-only and
references them by foreign key, so deleting an organization to tidy a test run
would either fail on the FK or rewrite audit history. Their business rows —
the rows the assertions are about — are purged.

For the same reason the database is **not empty overall**, and this is stated
rather than left to be discovered: organisations seeded by earlier sequences and
the demo (`m5-org` 1039 patients, `m7p-org` 252, `m6-org` 90, `demo-org-001` 18,
…) still hold their rows — 1403 patients and 55 appointments in total at the time
of writing. This pass neither created nor removed them; the zeroes above are
scoped to the organisations this pass's fixtures own, which is exactly the
guarantee a shared development database allows.

### 6.5 Audit trail untouched

The suite and both migrations add rows to `audit_events` (every mutating service
call audits) and **remove none**: no test and no migration deletes, truncates or
rewrites an audit row, and `purge_org` never touches that table. The
rate-limit table is separate from the audit table on purpose — dropping
`login_attempts` rows is not an audit operation.

---

## 7. Governance and Skill Compliance

Required by `.clinerules` §6 for every implementation report.

### 7.1 Skills

**No skill was used, because none is installed.** Verified in this workspace:
no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/` directory and no
Cline skill configuration. Per `.clinerules` §4/§5 the governance documents were
used instead, and this report says so rather than implying a skill ran.

### 7.2 Precedence applied (`.clinerules` §1)

1. **Verified runtime state first.** Every claim in §5–§6 comes from an executed
   command against this tree (containers, live HTTP, database reads), not from
   reading code.
2. **Approved business rules untouched.** No BR was reinterpreted; the two
   migrations add a rate-limit table and drop a duplicate index, neither of
   which encodes a business rule.
3. **Project governance** — `.clinerules` §3 non-negotiables were the acceptance
   criteria for this pass (see §7.4).
4. **Agent-rules as adapted** by `AMSDP_Engineering_Governance_Assessment.md` §3.

### 7.3 Domain routing (`.clinerules` §4) — which documents governed which change

| Domain | Document applied | How it was followed |
|---|---|---|
| Docker / deployment / ports / infrastructure | `saas-cicd-workflow.md` (adapted; "state CI's real capability") | No CI capability is claimed anywhere in this report: the repository has no workflow that runs these tests, so the results below are *local runs*, cited by command, not by a green badge. No image was pushed and no production migration was applied. |
| Authentication, sessions, throttling | `saas-auth-and-authorisation.md` §7 + `saas-api-throttling.md` as adapted (Assessment §3.8) | Server-side enforcement unchanged and re-verified in-container (`401` without a token); the limiter is a route-level call on `/api/v1/staff/login` only, state in PostgreSQL, refusal `429` with a header, no lockout, health checks never limited. |
| Multi-tenant data / schema / migrations | `saas-multitenant-data.md` §4–§7 | Both migrations are forward-only, idempotent Alembic revisions in the pinned chain; the tenant key remains `organization_id` (the new table carries no tenant column at all — it is rate-limit state, not tenant data); no speculative index was added; the one index changed was *removed* for being redundant, which is what §7 ("do not add indexes speculatively") implies in reverse. |
| Queue / scheduling / workflow | `saas-api-throttling.md` §2 concurrency intent | The advisory-lock serialisation exists so the limiter stays exact under concurrent workers — the same concurrency concern the queue work already handles with `queue_sequences`. |
| Audit / data integrity | `saas-observability.md` (adapted), BR Part X | `audit_events` stays append-only; the throttle table is explicitly *not* audit data; denials are still recorded by the services (§6.5). |
| Frontend / single origin | `saas-frontend-ux.md` (only as far as the proxy) | No UI change was made; the frontend is verified as the serving origin (§5.3). |

### 7.4 Non-negotiables checked (`.clinerules` §3)

| Non-negotiable | Status in this pass |
|---|---|
| Never log or expose secrets | The new health endpoints return only `{"status", "service"}`; the throttle warning logs no IP, username or credential; no secret is printed in this report (the compose default key is documented as a placeholder, not a credential) |
| UI is never the safety boundary | The tests authorize through real JWTs and assert `401`/`404` from the server; nothing was made to pass by hiding a button |
| Tenant derived from the token | Every rewritten test relies on the service deriving `organization_id` from the token — several tests exist specifically to prove a body-supplied `organization_id` is ignored |
| Cross-tenant fails closed at 404 | Asserted in the organization/doctor/patient/scheduling modules and in the e2e flow; no `403` is used for cross-tenant |
| One tenant key (`organization_id`) | Unchanged; the new table has no tenant column |
| Audit is append-only and persistent | Untouched by tests and migrations; no delete/truncate/rewrite of `audit_events` anywhere in the diff |
| Denials are recorded | Unchanged, and re-exercised by the permission-refusal tests |
| Forward-only idempotent migrations only | Both new revisions (§6.3); no hand-written DDL applied to any database |
| Never claim an unverified capability | This is the spine of §9 — every claim carries its basis, and four things are explicitly *not* claimed (no CI, no orchestrator, no production readiness, no multi-worker load test — §8.4) |
| Don't use a tool/library merely because it was discovered | The throttle uses only what the services already ship (`sqlalchemy`, `psycopg2`, PostgreSQL advisory locks); no new dependency, no Redis, no scheduler |

---

## 8. Deviations, exceptions and honest limits

### 8.1 Deliberate deviations

1. **`.clinerules` §9 ("write code only"; yield after two files).** This pass is a
   verification and hardening task, so the suite, ten containers and two
   databases were executed, and the work legitimately spans more than two files
   (eight service `main.py` files, a shared `common/` module, compose, two
   migrations, nine test files). Recorded as a deliberate, task-scoped deviation
   — the same one the Sequence-4 report recorded — not an unnoticed one.
2. **The fixtures were tightened mid-pass.** The first green run left the last
   test's rows behind (the purge ran only on the way in); teardown purges were
   added, the suite was re-run, and **both** runs are reported in §4.1 rather
   than only the nicer one.
3. **Tests run against the shared development database** (`amsdp` on
   `127.0.0.1:5433`), not a throwaway one. Mitigated by module-unique
   organizations, `uniq()`-scoped count assertions, and purge before **and**
   after each test — verified as zero business residue in §6.4. A throwaway
   database would be cleaner; it is not available in this environment without
   creating a second volume, and the mitigation is measured rather than assumed.
4. **`backend/app/main.py` was edited in a documentation-only way** (docstring),
   because a stub that reads like an entry point is the defect SEQ4-DEPLOY-D1
   named. No behaviour changed; `GET /` still returns `Hello World`.

### 8.2 Known gaps, accepted for now

| Gap | Why it is acceptable now | What would close it |
|---|---|---|
| The limiter emits `Retry-After` only, not the `X-RateLimit-Limit/Remaining/Reset` triplet | The adapted rule (Assessment §3.8) requires "429 with headers"; the triplet is a CarbonTally-specific client contract that AMSDP has no consumer for | add the three headers if/when a client displays remaining attempts |
| Zones come from the base image's system tzdata, not a pinned dependency | Verified in the built image (§5.5); the Dockerfiles are pinned to `python:3.13-slim` | pin `tzdata` in the service requirements, or assert `zoneinfo.available_timezones()` at startup, if the base image ever changes |
| No multi-worker load test of the limiter | The shared-state property is proven directly: rows written by the service are read from another process (§5.4) | run two uvicorn workers and repeat the 22-attempt probe |

### 8.3 Environment notes

* Ten containers were built and started for §5, then **stopped**; the development
  database container was restarted and left running as it was found. No image
  was pushed and nothing was deployed.
* The probe username's rate-limit rows were deleted after the check; the
  development database has `login_attempts` empty.
* The working tree carries other sequences' uncommitted work (126 entries in
  `git status --porcelain`, including the untracked `backend/common/` and
  `backend/alembic/` trees). Nothing was stashed, reset, reformatted or
  reverted; the only Git commands run were read-only (`status`, `diff`, `log`).

### 8.4 Explicitly **not** claimed

* **No CI claim.** No workflow in this repository runs these tests; §4 is a local
  run cited by command, not a green build badge.
* **No orchestrator claim.** Healthchecks are read by `docker compose` as
  configured here; no Kubernetes/Render manifest exists or was written.
* **No production claim.** No TLS, reverse proxy, backup/restore, monitoring or
  alerting was exercised. No restart policy is set in `docker-compose.yml`
  (deliberate: a restart policy is a deployment decision for whatever supervisor
  runs the stack), and the compose JWT secret defaults to a *placeholder* — a
  real `AMSDP_JWT_SECRET` and `AMSDP_ENV=production` are deployment-time inputs,
  as the compose header states.
* **No concurrency proof beyond the database.** See §8.2 row three.

---

## 9. Evidence standard (`.clinerules` §7)

| Claim | Level | Basis |
|---|---|---|
| The whole backend suite is green, with nothing skipped | **TESTED** | `289 passed, 94 warnings in 169.32s`, §4.1 |
| Each rewritten module passes on its own | **TESTED** | seven isolated runs, §4.2 |
| Rewritten tests assert persisted state, not in-memory state | **TESTED** | they read through `SessionFactory` after the app returned, §4.3 |
| Every service has liveness + readiness and answers it | **VERIFIED** | 16 probes, 200 each, from the containers, §5.3 |
| The stack starts in order behind a healthy database | **VERIFIED** | compose start log + 10/10 healthy, §5.2 |
| The API serves through one public origin | **VERIFIED** | login + 4 protected reads through `:3100`, 401 without a token, §5.3 |
| All eight services share one JWT secret | **VERIFIED** | one token from identity accepted by all eight containers, §5.3 |
| Login throttling is durable and process-shared | **VERIFIED** | 20×401 → 429 + `Retry-After: 60`, and 20 rows read from another process, §5.4 |
| Migrations are at head with no model drift | **VERIFIED** | `alembic current` = `e6c1a9b3d5f8 (head)`, `alembic check` clean, §6.1 |
| The redundant index is really gone | **VERIFIED** | `pg_indexes` on the live database, §6.2 |
| The test suite leaves no business rows behind | **VERIFIED** | database reads after the run: 0 patients / 0 appointments / 0 schedules / 0 queue entries / 0 orphan tokens in the suite's orgs, §6.4 |
| Facility-day resolution works in the production image | **VERIFIED** | 486 zones, `Asia/Dhaka`, `operational_today()` inside the built image, §5.5 |
| The service serves the facility day on a tzdata-less image | **NOT CLAIMED** | it would silently fall back; §8.2 |
| CI runs any of this | **NOT CLAIMED** | no such workflow exists, §8.4 |

---

## 10. Files changed by this pass

Scope note: the working tree also carries earlier sequences' uncommitted work —
`backend/identity/{routes,models,permissions}.py`, `backend/*/tests/test_identity.py`…
`test_queue.py`, `test_audit.py`, `frontend/pages/*`, `frontend/styles/global.css`,
`ai_factory/**` and several `docs/**` files show as modified and are **not** part
of this pass. The lists below are only what this pass touched.

### New

| File | Purpose |
|---|---|
| `backend/common/health.py` | `install_health(app, service)` — `/health`, `/health/ready` |
| `backend/common/login_throttle.py` | DB-backed, advisory-locked sliding-window limiter |
| `backend/alembic/versions/d4b2c8e1f7a3_add_login_attempts.py` | `login_attempts` table + two indexes |
| `backend/alembic/versions/e6c1a9b3d5f8_drop_redundant_tracking_token_index.py` | drops the duplicate index |
| `backend/tests/amsdp_test_support.py` | seeding / auth / purge helpers for the rewritten tests |
| `backend/conftest.py` | one `sys.path` bootstrap for the whole suite |
| `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | this report |

### Modified

| File(s) | Change |
|---|---|
| `backend/common/models.py` | `LoginAttempt` model (matches `d4b2c8e1f7a3`) |
| `backend/{identity,organization,patient,doctor,scheduling,appointment,queuing,audit}/main.py` | `install_health(app, "<service>")`; identity additionally calls the limiter and clears the bucket on success |
| `backend/audit/Dockerfile`, `backend/audit/requirements.txt` | build context `./backend`, `COPY common/`, `psycopg2-binary` — the service could not start before |
| `backend/{identity,organization,patient,doctor,scheduling,appointment,queuing}/{Dockerfile,requirements.txt}` | aligned base image, context and shared-package copy |
| `docker-compose.yml` | healthcheck defaults, db gate, shared env anchors, frontend gate, topology header (158 lines changed) |
| `frontend/next.config.js` | missing proxies added so every `/api/v1` prefix reaches its owning service (6 lines) |
| `backend/appointment/tests/test_appointment.py`, `.../test_reschedule.py`, `backend/doctor/tests/test_doctor.py`, `backend/organization/tests/test_organization.py`, `backend/patient/tests/test_patient.py`, `backend/scheduling/tests/test_scheduling.py`, `backend/tests/test_e2e.py` | the seven quarantined modules, rewritten against PostgreSQL |
| `backend/app/main.py` | docstring only: this is not the deployment entry point |

### Already present in the tree, exercised here

`backend/tests/test_security.py` carries `TestLoginThrottle` (429 after the
allowance, per-username isolation, success clears the bucket) — part of the 177
tests that were already green; it is listed because it is what keeps the new
limiter honest between the container-level probe (§5.4) and the code.

### Not changed, on purpose

Product endpoints, permission tables, business rules, `audit_events` semantics,
the tenant key, and every other service's authorization logic.

---

## 11. What remains

| Item | Owner | Note |
|---|---|---|
| A real `AMSDP_JWT_SECRET` and `AMSDP_ENV=production` at deploy time | deployment | the compose default is an explicit placeholder |
| A restart policy / supervisor for the containers | deployment | intentionally not set in compose |
| `tzdata` pinned (or startup assertion) **if** the base image ever changes | future hardening | currently verified against the system tz database (§5.5) |
| `X-RateLimit-*` headers if a client ever shows remaining attempts | future | §8.2 |
| A throwaway test database in CI | future | today the suite runs against the shared dev database with measured zero residue |
| Committing this work | project owner | no commit, push, merge or deploy was performed, per §8.3 |

**Finish line reached:** all seven findings from the Sequence-4 report now have a
disposition with evidence attached, the full suite is green with nothing skipped,
and the stack was observed serving the API through one origin rather than
described as if it would.

---

*End of report.*
