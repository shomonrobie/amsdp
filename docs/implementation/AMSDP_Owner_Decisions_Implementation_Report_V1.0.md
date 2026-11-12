# AMSDP — Owner Decisions Q-1 … Q-6: Implementation Report

> **Document ID:** `AMSDP_Owner_Decisions_Implementation_Report`
> **Version:** V1.0 · **Date:** 2026-11-13
> **Branch:** `hackathon-mvp` (base commit `485d141`) · **Pushed:** no
> **Decisions implemented:** `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`
> **Raised in:** `docs/audit/AMSDP_Project_Context_Report_V1.0.md` §11
> **Written to:** `docs/implementation/` per `.clinerules` §11 (implementation reports)

---

## 1. Outcome at a glance

| # | Decision | Shipped | Evidence level |
|---|---|---|---|
| Q-1 | Explicit platform-administration boundary | `common/permissions.py`, `common/auth.py`, `audit/main.py` | **TESTED** (42 assertions) + **VERIFIED** (DB rows) |
| Q-2 | Denial auditing (403/404/422) | `common/denial_audit.py` + 8 service registrations | **TESTED** (8 tests) + **VERIFIED** (130 rows in the trail) |
| Q-3 | Notification worker accepted; demo fallback documented | `docs/demo/AMSDP_Limitations_Report_V1.0.md` | **IMPLEMENTED** (documentation) |
| Q-4 | Limitations report correction | `docs/demo/AMSDP_Limitations_Report_V1.0.md` | **IMPLEMENTED** (documentation) |
| Q-5 | CI pipeline | `.github/workflows/ci.yml`, `backend/requirements-dev.txt` | **IMPLEMENTED**; gates **not** executed on a runner (see §7.4) |
| Q-6 | Owner-controlled documents preserved | 2 files staged unchanged | **IMPLEMENTED** (byte-identical, see §6) |

Nothing in this report is claimed as **ACCEPTED**: acceptance is the Product
Owner's act, not the agent's.

**Headline numbers.** Backend suite before the change: **289 passed**. After:
**318 passed** (289 + 29 new/rewritten assertions), **0 failed**, in 184.56 s.
Frontend: `next build` compiled successfully, `npm test` **43 pass / 0 fail**.

---

## 2. Q-1 — Platform administration boundary

**Before.** `PERMISSIONS["super_admin"] = ["*"]`, and `check()` returned `True`
for any string whenever `"*"` was present. `AuthContext.is_super_admin` compared
the role *string*, so the 20-odd `if auth.is_super_admin:` sites across the
services never consulted the matrix at all. The platform role's authority was
therefore unbounded and unenumerable.

**After.**

1. `common/permissions.py` declares `PLATFORM_CAPABILITIES = ("platform.admin",
   "platform.cross_org")` and gives `super_admin` an explicit list: those two
   capabilities, the concrete administrative capabilities that already existed
   (`org.*`, `branch.*`, `staff.*`, `audit.read`), and the clinic capability
   *namespaces* already granted to `org_admin` (`patient.*`, `doctor.*`,
   `schedule.*`, `appointment.*`, `queue.*`). Nothing is granted that no
   organization-level role already had, so this is **not** an expansion of
   authority — it is the same vocabulary, enumerated (Q-1 boundary).
2. `check()` no longer honours a bare `"*"`. Matching is exact or by a
   `<namespace>.*` pattern. An unknown resource is now denied **for every role**,
   `super_admin` included.
3. `AuthContext.is_super_admin` is derived from `platform.admin`, and the new
   `AuthContext.can_cross_org` from `platform.cross_org`. The existing role checks
   in `identity/routes.py`, `organization/main.py`, `queuing/*` and `audit/main.py`
   now resolve through the matrix without being rewritten — a safe, single-point
   change of meaning rather than a 10-file refactor.
4. **Cross-organization access is gated by capability, not by role.**
   `require_org_access()` and `require_branch_access()` allow a foreign
   organization/branch only when the caller holds `platform.cross_org`; every
   tenant role still receives the non-disclosing **404** required by
   `.clinerules` §3.
5. **Platform access is audited** (Q-1 §6). `record_platform_access()` writes
   `action="platform.cross_org.access"` into the **target** organization's trail
   with `actor_id`, `actor_role`, `after.actor_organization_id` and
   `after.capability`, so the tenant that owns the data can see platform support
   touched it. `audit/main.py` uses it on the cross-tenant read path.

**Deliberate non-change.** The remaining `is_super_admin` call sites were left in
place: they now read the matrix through the property, and rewriting 20 call sites
in this task would have been a refactor the decision did not authorize.

---

## 3. Q-2 — Denial auditing

**Before.** `common/audit.py` was only called by a service that *performed* an
action. A refused request produced a status code and nothing else: a probe that
was rejected left no record anywhere.

**After — one recording site, shared by every service.**
`common/denial_audit.py` provides `install_denial_audit(app, service)`, an ASGI
middleware registered next to `install_health()` in all eight services
(`identity`, `organization`, `patient`, `doctor`, `scheduling`, `appointment`,
`queuing`, `audit`). Because it observes the response of the whole app, it catches
denials raised by a permission dependency, by an endpoint, by the tenant gate and
by request validation alike — with **no** second hook that could log the same
denial twice (Q-2 condition 3).

| Q-2 condition | How it is met |
|---|---|
| Audited statuses | `DENIAL_STATUSES = {403, 404, 422}` |
| No sensitive data | only method, redacted path, status, verified claims, optional `X-Request-ID`; no token, no body, no query string, no entity id |
| No oracle | the audit row is written **after** the response; the status and body the caller sees are unchanged, so nothing learns that a foreign id exists |
| Request id | `X-Request-ID` is stored in `after.request_id` when the caller supplies one |
| No duplicates | single middleware, single write |
| Response preserved | recording happens after `http.response.start` has been forwarded |
| Failure safety | every audit write is wrapped, rolled back and logged; it can never turn a denial into a success or an error |
| Tests | `backend/tests/test_denial_audit.py` (8 tests) |
| Documented exclusion | 401 — see below |

**The 401 exclusion, and why it is not a silent omission.**
`audit_events.organization_id` is `NOT NULL` with a foreign key to
`organizations`, and the trail is read per tenant. A 401 means there is no
*verified* identity, so there is no organization to attribute a row to.
Attribution is **never** taken from an unverified JWT: doing so would let an
anonymous caller choose which tenant's append-only trail their row lands in — a
cross-tenant integrity attack. 401s are therefore written to the
`amsdp.denial_audit` log stream (through `log_denial()`), not to the table. This is
Q-2 condition 8 satisfied by documentation, and it is asserted by a test rather
than left implicit.

**Redaction.** Path segments that look like tokens, uuids or long identifiers
(20+ characters of `[A-Za-z0-9_.~%+-]`) are replaced with `{redacted}` before the
row is built, so a tracking link that caused a 404 does not copy a patient
identifier into a permanent security record. Verified in the database:
`PATCH /api/v1/queue/{redacted}`.

---

## 4. Q-3 and Q-4 — demo documentation corrections

Both edits are confined to `docs/demo/AMSDP_Limitations_Report_V1.0.md`, one
table row each (Q-4: "correct only what is inaccurate").

**Q-4 — patient registration.** The row "No patient registration form — Patients
page only supports search" was false. It now states that the Patients page offers
a **Register** dialog to the roles holding `patient.create` (`receptionist`,
`branch_admin`, `org_admin`, `super_admin`), that `POST /api/v1/patients` provides
the same capability, and that `doctor`/`assistant` are search-only **because the
backend denies them `patient.create`** (`common/permissions.py`). The claim is
tied to an enforced rule, not to a UI impression.

**Q-3 — notifications.** The row "No notification system — No SMS/email
integration" hid two separate facts. It now states that only a `mock` provider is
configured (real delivery remains blocked pending owner approval), that the outbox
is drained by `python3 -m common.notifications.worker --once` which is **not** a
compose service (confirmed against `docker-compose.yml`: the services are `db`,
`identity`, `organization`, `patient`, `doctor`, `scheduling`, `appointment`,
`queuing`, `audit`, `frontend`), and the demo fallback actually used: staff issue a
tracking link with `POST /api/v1/appointments/{id}/tracking-token` (QR at
`/api/v1/track/{token}/qr`) and share `/track/{token}` manually.

**Not touched, deliberately.** The document still describes in-memory storage, no
PostgreSQL and no health endpoints — it is stale in many places. Refreshing it was
explicitly outside Q-4 and is recorded as open item O-3 in §9.

---

## 5. Q-5 — Continuous integration

`.github/workflows/ci.yml` (new) runs two independent jobs on push to `main` /
`hackathon-mvp`, on every pull request, and on demand:

**`backend` — pytest on PostgreSQL 16**
- `python:3.13` toolchain, matching `backend/*/Dockerfile` (`python:3.13-slim`);
- a `postgres:16-alpine` service on host port 5433, matching
  `docker-compose.yml` and the port `common/database.py` expects;
- installs the **union** of the per-service `requirements.txt` files (Q-5: the
  runtime dependencies are declared per service, so the suite needs all of them —
  `appointment` alone adds `qrcode`/`Pillow`) plus `backend/requirements-dev.txt`;
- applies the real migration chain (`python -m alembic upgrade head`) instead of
  letting models create tables, so CI tests the deployment path. The chain has a
  single head — `e6c1a9b3d5f8`, confirmed with `alembic heads` — so the step is
  deterministic;
- runs `python -m pytest -q`.

**`frontend` — build and unit tests**
- `node:22`, matching `frontend/Dockerfile` (`node:22-alpine`);
- `npm ci` against the committed `frontend/package-lock.json`,
  `npm run build`, `npm test` (the existing `node --test tests/*.test.mjs` script).

**What was deliberately not added** (Q-5 boundary): no new test framework, no
coverage gate, no linter the project does not already run, no release/publish
automation, no change to any Dockerfile, compose file or port. The only new
dependency file is `backend/requirements-dev.txt` (pytest + httpx), which no
service image installs.

**Credentials.** The two literals in the workflow (`ci-not-a-secret`) exist only
inside an ephemeral service container. No repository, demo or deployment secret is
used, echoed or stored, and `AMSDP_JWT_SECRET` is left unset so the app takes its
documented development fallback rather than a hard-coded CI secret.

---

## 6. Q-6 — Owner-controlled documents

`docs/AMSDP_Master_Feature_List_V2.0_Draft.md` (+118/−11) and
`docs/architecture/AMSDP_System_Architecture_V1.0.md` (+63/−11) were **not
opened for editing**. They are staged as they stand and travel in the
documentation commit. The agent made no judgement about their content; the diff
statistics above are quoted from `git diff --stat` and nothing else was derived
from them.

---

## 7. Verification and evidence

### 7.1 Baseline (before any change)

The stack was stopped (`docker ps` showed every `amsdp-*` container `exited`) and
the first collection attempt failed with `connection refused` on port 5433 — so
the database container was started (`docker compose -p amsdp up -d db`) and the
suite re-run.

```
289 passed, 150 warnings in 149.25s
```

### 7.2 After the change

```
318 passed, 159 warnings in 184.56s
```

+29 tests: 20 in `backend/tests/test_platform_admin.py`, 8 in
`backend/tests/test_denial_audit.py`, and the identity permission test rewritten
from "super_admin has everything" to capability-based assertions (+1). Zero
regressions.

After the commits, the touched modules were re-run on the committed tree as a
final check — `tests/test_platform_admin.py`, `tests/test_denial_audit.py`,
`audit/tests/test_audit.py`, `identity/tests/test_identity.py` → **59 passed in
10.24 s**.

### 7.3 Independent artefact — the trail itself

Read back from PostgreSQL after the suite (not from the test assertions), 130 rows
carrying the two new actions:

| action | services observed | statuses |
|---|---|---|
| `request.denied` | appointment, audit, doctor, identity, organization, patient, queuing, scheduling | `denied status=403`, `=404`, `=422` |
| `platform.cross_org.access` | audit, unit (dependency-level test) | — |

Sample rows: `POST /api/v1/appointments/no-such-appt/tracking-token`
(receptionist, `m9b-org`/`m9b-br`) and `PATCH /api/v1/queue/{redacted}`. The fact
that rows appear from pre-existing test modules (`m9b-*`, `sq3-*` tenants the new
tests never touch) is the proof that the middleware is actually engaged across the
services rather than only inside the new tests.

### 7.4 What could **not** be executed here

- **The GitHub Actions run itself.** No runner, and no network access to GitHub
  from this environment. The workflow was validated by parsing it
  (`yaml.safe_load`: jobs `backend`/`frontend`; triggers `push`,
  `pull_request`, `workflow_dispatch`) and by running its two payloads locally —
  but **CI has never executed**. It is IMPLEMENTED, not VERIFIED. The first push
  will be its first real run.
- **`pip install` in a clean environment.** The suite was run against the existing
  virtualenv; the requirement files themselves were not re-resolved from scratch.
- **`alembic upgrade head` on an empty database.** Only `alembic current`
  (`e6c1a9b3d5f8 (head)`) and `alembic heads` against the dev database were run;
  a from-scratch migration is the CI step's job.
- **Browser verification.** No UI was opened; the frontend evidence is the build
  and the unit-test suite.

### 7.5 Frontend

```
✓ Compiled successfully          (next build)
ℹ tests 43  ℹ pass 43  ℹ fail 0   (npm test)
```

---

## 8. Governance and skill compliance

**Documents read for this task** (`.clinerules` §12, read on the agent's own
initiative): `docs/governance/AMSDP_Docs_Index_V1.0.md` (the navigation index),
`docs/audit/AMSDP_Project_Context_Report_V1.0.md` §11 (the source of Q-1 … Q-6),
`docs/demo/AMSDP_Limitations_Report_V1.0.md` (the document Q-3/Q-4 amend), plus the
code the changes touch (`common/permissions.py`, `common/auth.py`,
`common/audit.py`, `common/models.py`, `audit/main.py`, `identity/routes.py`,
`patient/main.py`, `docker-compose.yml`, `frontend/package.json`,
`frontend/Dockerfile`, `backend/*/Dockerfile`, `backend/alembic/env.py`).

**Skills.** None installed — `.clinerules` §5 records that no `.clinerules/skills/`,
`.claude/skills/` or repo `skills/` directory exists. No skill was used, and none is
claimed. The routing table (§4) sends this task to the governance documents and to
`saas-application-security.md` / `saas-auth-and-authorisation.md` /
`saas-multitenant-data.md` / `saas-observability.md` / `saas-cicd-workflow.md` **as
adapted** by the governance assessment; the rules that actually bind here are
`.clinerules` §3 and the Business Rules.

**Non-negotiables (§3) re-checked against the diff**

| Non-negotiable | Result |
|---|---|
| No secret logged or exposed | Denial rows store no token/header/body; a forged token is rejected, never recorded |
| UI is never the safety boundary | Every new check is server-side (`permissions.check`, `require_org_access`, middleware) |
| Org/branch from the token, never the body | Unchanged and reinforced: `denial_record()` reads claims from a *verified* token only |
| Cross-tenant access fails closed with 404 | Preserved in `require_org_access`, `require_branch_access`, `_scoped_org`; asserted by tests |
| One tenant key (`organization_id`) | No new tenant column; the platform access row also uses `organization_id` |
| Audit trail append-only | Only `INSERT`s were added; nothing updates or deletes a row |
| Denials recorded, never swallowed | This is Q-2 itself; 401 is logged with a stated reason |
| Schema change ⇒ Alembic migration | No schema change was made, therefore no migration |
| No capability claimed that is not verified | §7.4 lists exactly what was not run |
| No library used merely because it was found | Only Starlette's `run_in_threadpool` (already present via FastAPI) was used |

**Evidence standard (§7).** Q-1 and Q-2 are **TESTED** (named tests pass in this
tree) and **VERIFIED** (independent artefact: rows read back from PostgreSQL).
Q-3, Q-4, Q-5, Q-6 are **IMPLEMENTED**; Q-5's pipeline has never run, which is
stated rather than glossed. Nothing is **ACCEPTED** by the agent.

**Execution boundaries (§9).** Files were edited only through the controlled editor
tool; the only commands executed were read-only inspections, the test suite, the
frontend build/test, `alembic current/heads`, and `docker compose -p amsdp up -d
db` (needed because the stack was down and the suite cannot run without
PostgreSQL). No destructive git command was used, and nothing was pushed.

---

## 9. Deviations, limitations and open items

**Deviations (intentional, inside the approvals)**

- **D-1.** The ~20 `auth.is_super_admin` call sites were not rewritten. They now
  resolve through `platform.admin` via the property, which is the smallest change
  that removes the role-string bypass; rewriting them was outside Q-1's boundary.
- **D-2.** 401 denials are logged, not stored (§3) — the documented exclusion that
  Q-2 condition 8 allows.
- **D-3.** `check()` is stricter than before for non-namespace capabilities: a new
  capability must be added to the matrix explicitly or it is denied for everyone.
  That is the intended consequence of Q-1, and the suite confirms nothing depended
  on the old prefix behaviour.

**Open items**

- **O-1 (blocks VERIFIED).** The CI pipeline has never executed. Its first run will
  be on the first push, which this task does not perform.
- **O-2.** `docs/demo/AMSDP_Limitations_Report_V1.0.md` is still stale about
  storage, migrations and health endpoints (§1, §4 row "No health check
  endpoints"). Q-4 authorized only the registration correction; a wider refresh
  needs its own decision.
- **O-3.** The corrected Q-4 sentence describes `frontend/pages/patients.js` **as it
  stands in the working tree**, where the Register dialog is part of the owner's
  uncommitted frontend work (that file is not mine and was not staged). If that
  work is not committed, the row must be revisited.
- **O-4.** Platform access recording is best effort: if the target organization does
  not exist the insert violates the foreign key, is rolled back and logged, and the
  authorized request still succeeds. Reachable only from endpoints that apply the
  tenant gate before loading the row.
- **O-5.** `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md` remains unregistered
  (pre-existing open item carried from the index's Revision 10).
- **O-6.** Untracked work that is not mine was left untouched and unstaged:
  `_tools/`, `docker-compose.demo.yml`, `docs/security/`, `docs/chatgpt/`,
  `docs/audit/AMSDP_Project_Context_Report_V1.0.md`, `frontend/pages/patients.js`,
  `frontend/styles/global.css`.

---

## 10. Placement and commit separation

**Written to:** `docs/implementation/` (`.clinerules` §11 — implementation reports)
and `docs/decisions/` (decision records). Both are registered in
`docs/governance/AMSDP_Docs_Index_V1.0.md` Revision 11. No document was moved or
renamed, so no migration-manifest entry is required (§11).

**Commits** — five, logically separated, nothing pushed (branch `hackathon-mvp`):

1. `feat(security): explicit platform-administration capability boundary (Q-1)` —
   `backend/common/permissions.py`, `backend/common/auth.py`,
   `backend/audit/main.py`, `backend/identity/tests/test_identity.py`,
   `backend/tests/test_platform_admin.py`.
2. `feat(audit): record denied requests (403/404/422) in every service (Q-2)` —
   `backend/common/denial_audit.py`, the eight service registrations,
   `backend/tests/test_denial_audit.py`.
3. `docs(demo): correct the registration claim and record the manual tracking-link
   fallback (Q-3, Q-4)` — `docs/demo/AMSDP_Limitations_Report_V1.0.md`.
4. `ci: add backend and frontend pipeline (Q-5)` — `.github/workflows/ci.yml`,
   `backend/requirements-dev.txt`.
5. `docs: record the Q-1…Q-6 decisions and their implementation evidence (Q-6)` —
   this report, the decision record, the index revision, and the two
   owner-controlled documents preserved verbatim.

Each commit is self-consistent: the Q-1 hunks in `audit/main.py` never reference
`denial_audit`, and the Q-2 registration lines never reference the platform
helpers, so no commit leaves an undefined import behind.




