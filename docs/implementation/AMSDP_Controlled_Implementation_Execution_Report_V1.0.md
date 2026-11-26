# AMSDP — Controlled Implementation Execution Report V1.0

**Status:** ISSUED — implementation evidence, **not** accepted work · **Written:** 26 November 2026 ·
**Repository:** `E:\amsdp` (Windows development checkout) · **Branch:** `hackathon-mvp`

**Authority.** Product Owner implementation mandate of 26 November 2026, issued after
`docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md`. The mandate authorises
implementation of the authorised, non-deferred and currently executable parts of the 13 PARTIALLY IMPLEMENTED
and 8 NOT IMPLEMENTED roadmap items. It does **not** authorise a Product Owner decision, a deployment action,
a reseed of any live database, or a claim of acceptance.

**Evidence vocabulary** (`.clinerules` §7): IMPLEMENTED → TESTED → VERIFIED → ACCEPTED. A green suite does not
make something VERIFIED; documentation does not prove implementation. Nothing in this report is ACCEPTED.

---

## 1. Baseline — what this session found, before it changed anything

| Item | Observed value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD | `fd4d3656738dfef0885cfc86307903305aa2f08d` — "docs: pin the verified push point (1f303d1)…" |
| Upstream | `origin/hackathon-mvp` = `fd4d365…` — not ahead, not behind |
| Working tree | `M .clinerules` (**the owner's own uncommitted edit — preserved untouched**) and `?? docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md` (the audit report from the previous session, uncommitted) |
| Stashes | none |
| Work landed since `fd4d365` | **none** — the audit's observed state is the state this session started from |

**Environment limits established before any test claim** (these are why several §7 rows are BLOCKED, not
passed):

1. **No PostgreSQL.** `common.database` resolves `postgresql+psycopg2://amsdp@127.0.0.1:5433/amsdp`;
   connecting raises `psycopg2.OperationalError: connection to server at "127.0.0.1", port 5433 failed:
   Connection refused (0x0000274D/10061)`. `alembic current` cannot run.
2. **No Docker.** `docker` is not installed (`CommandNotFoundException`), so no scratch database can be
   started on this host.
3. **Node is available**: v24.12.0 locally and **v22.23.5** fetched through `npx --package node@22`, which is
   what made the CI failure of §4.1 reproducible instead of suspected.
4. **GitHub Actions is readable without a token** through the public API; a job's *log text* is not
   (`Sign in to view logs`).

---

## 2. Governing documents read in this session

| Document | What was taken from it |
|---|---|
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | The navigation index, and the A-5 annex whose conventions this report follows |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | §4 gates, §5.2 critical path, §6 WP-A/WP-B/WP-C/WP-C.2, Appendix D.3 (WP-C.3 table and AC-15…AC-22), §7 D1–D9, §8 sequencing (esp. rules 8 and 9), §9 risks, §10 deferred work, Appendix H (A-5) |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | Execution state carried forward; the style of the §3 table |
| `docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md` | The 21-item state re-checked here, and findings F-1…F-11 |
| `.clinerules` | §1 precedence, §3 non-negotiables, §6 compliance reporting, §9 execution boundaries, §11 placement, §12 reading policy |

**Two conformance notes, recorded rather than assumed:**

- The mandate names the MP-04 deferral gate as **PO-05**; roadmap §4 defines PO-05 as the authorisation whose
  absence *is* the deferral. Both agree on the operative fact — **MP-04 is not authorised** — and it was
  treated as such.
- The mandate lists MP-09/13/14/15 under **PO-04**. PO-04 authorises them *after the first clean rehearsal*
  (MP-32), in the sequence MP-09 → MP-13 → MP-14 → MP-15. No rehearsal is recorded, so the gate is not
  satisfied and none of the four was started.

---

## 3. The twenty-one items — classification and what happened

Codes (mandate §3): **A** ready · **B** partially ready · **C** gated · **D** deferred by the Product Owner ·
**E** decision required · **F** blocked by environment or access.

| Item | Audit status | Class | What this session did | Current state |
|---|---|---|---|---|
| MP-01 | PARTIAL | **F** (B-4) | Re-read only; no host contacted | **BLOCKED** — unchanged |
| MP-02 | PARTIAL | **A** + F residue | Found and fixed the **cause** of the red frontend CI job; the deployment half stays blocked | **PARTIAL → progressed** (§4.1) |
| MP-04 | PARTIAL | **D** (PO-05) | Not built; discrepancy recorded (§11.2) | **DEFERRED** — unchanged |
| MP-09 | NOT IMPL. | **C** (PO-04 + rehearsal) | Not started | **GATED** — unchanged |
| MP-13 | NOT IMPL. | **C** (PO-04 + rehearsal) | Not started | **GATED** — unchanged |
| MP-14 | NOT IMPL. | **C** (PO-04 → MP-13) | Not started | **GATED** — unchanged |
| MP-15 | NOT IMPL. | **C** (PO-04 → MP-14) | Not started | **GATED** — unchanged |
| MP-23 | NOT IMPL. | **E** | Decision brief prepared (§11.1) | **DECISION REQUIRED** |
| MP-24 | PARTIAL | **A** | Queue-history screen, helpers, tests | **IMPLEMENTED, TESTED (frontend)** |
| MP-25 | PARTIAL | **A** | Durable limiter, migration, estimate flag, QR print flow | **IMPLEMENTED, partially TESTED** |
| MP-28 | PARTIAL | **A** | Board and tracking-page dictionaries moved into `lib/i18n.js` | **IMPLEMENTED, TESTED** |
| MP-30 | NOT IMPL. | **C** (PO-01) | Not started — still undefined | **GATED** — unchanged |
| MP-33 | PARTIAL | **A** | Diagnosed and fixed the CI failure; stated exactly what is and is not CI-proven | **IMPLEMENTED, TESTED locally** |
| MP-35 | PARTIAL (seed) | **A** | Two demo displays, seeded idempotently | **IMPLEMENTED — not executed (no DB)** |
| MP-37 | PARTIAL (page) | **A** | Room label, em dash for "no chamber" | **IMPLEMENTED, TESTED** |
| MP-38 | NOT IMPL. | **A** | Configured language, name, TV typography, BN/EN, footer | **IMPLEMENTED, TESTED** |
| MP-39 | NOT IMPL. | **A** | Capability + list/create/patch API + audit + admin page with copyable URL | **IMPLEMENTED; backend tests UNRUN** |
| MP-42 | PARTIAL (page) | **A** | Estimate marker and label on the board | **IMPLEMENTED, TESTED** |
| MP-43 | PARTIAL (page) | **A** | `If-None-Match` / `304` with no re-render | **IMPLEMENTED, TESTED** |
| MP-45 | PARTIAL (admin) | **A** | Admin toggles for the four policy fields | **IMPLEMENTED, TESTED (page)** |
| MP-46 | PARTIAL | **A** | `queue.display.denied` on the write routes, one row per denial | **IMPLEMENTED; backend test UNRUN** |

**Dependency order actually used, and why.** MP-38 and MP-39 both depend only on MP-35 + MP-36 (roadmap §6
"Depends on" columns), so neither strictly precedes the other; the earlier A-5 note ("MP-39 first") and the
audit's advisory ("MP-38 first") are both compatible with the plan. §8 rule 9 says MP-39 *may* ship after
MP-36–MP-38 and that the demonstration may not claim a configured facility until MP-39 exists. MP-45's admin
controls and MP-46's write-route denial accounting both land *inside* MP-39. The order chosen was therefore
**MP-38 → MP-39 → (MP-45 toggles, MP-46 denials)**, which is the plan's stated intent and the only order in
which the admin screen can be exercised against a board that already honours the configuration.


---

## 4. What was implemented

### 4.1 The frontend CI failure at `fd4d365` — cause found, not assumed

The audit (F-1) recorded the frontend job red at `fd4d365` with an unnamed cause and explicitly refused to
assume Q-3. This session established the cause from evidence:

| Evidence | Value |
|---|---|
| Run | CI **#34**, run id `45651581256`, head `fd4d3656738dfef0885cfc86307903305aa2f08d`, conclusion `failure` |
| Backend job | **succeeded** — `139337314777`, 16:11:01 → 16:19:17 (8m 16s), every step `success` (install, `alembic upgrade head`, `python -m pytest -q`) |
| Frontend job | **failed** — `139337315238`, 16:11:01 → 16:11:29. `Set up job`, `checkout`, `setup-node`, `Install dependencies` (`npm ci`) and **`Build` (`next build`) all succeeded**; only **`Run frontend tests`** failed — **16:11:26 → 16:11:27, i.e. about one second**, exit code 1 |
| Log text | **not public** (`Sign in to view logs`); the API returns `output.text: null` and the single failure annotation is only `Process completed with exit code 1` |
| Local reproduction, Node 24 | `npm test` → **467 tests, 465 pass, 0 fail, 2 skipped** — so the failure is not visible on this host's Node |
| Local reproduction, **Node 22.23.5** (CI's major) | `node --test tests/*.test.mjs` → **2 failures and 13 cancelled** — reproduced |

**Root cause.** Two test files had a **structural defect**: a `test(...)` callback was left unclosed, so the
tests that followed were declared *inside* the previous test's callback (in `staff-page.test.mjs` the following
four tests even sat inside a `for` loop inside that callback). Node 24 runs those nested tests anyway; Node 22
treats them as subtests of a parent that has already finished and cancels them —
`failureType: 'cancelledByParent'`, `error: 'test did not finish before its parent and was cancelled'`,
`code: 'ERR_TEST_FAILURE'` — which is why the job died in ~1 s with a real failure rather than a timeout.

**Fix (minimal, no assertion changed):** close the missing callback in
`frontend/tests/queue-announcement-delivery.test.mjs` (one `});` after line 177, removing the stray closing at
end of file) and in `frontend/tests/staff-page.test.mjs` (close the `for` loop and its test after line 164,
removing the stray closing at end of file). The diff is **3 lines in each file** and changes no assertion.

**Verified after the fix:** 493 tests — **491 pass, 0 fail, 0 cancelled, 2 skipped** — under **both**
Node 24.12.0 and Node 22.23.5. This is local evidence at the working-tree SHA; it is **not** a CI claim
(§8).

### 4.2 MP-39 — display administration, and MP-46's denial accounting

**New module `backend/queuing/displays.py`** (mounted in `backend/queuing/main.py`):

| Route | Behaviour |
|---|---|
| `GET /api/v1/queue/displays?branch_id=` | Lists one branch's boards; branch resolved from the token (or an explicit branch the caller may access); an organization-wide caller with no branch is asked for one (**422**), never guessed |
| `POST /api/v1/queue/displays` | Creates a board: code normalised to the lower-case handle, branch-org-suffixed, duplicate → **409**, scope target validated against **this** branch (department / room / posted doctors) → **422** if foreign |
| `PATCH /api/v1/queue/displays/{id}` | Partial update; switching scope drops the target that no longer applies; a real change writes **one** audit row with before/after; an unchanged save writes none |

- **Capability.** `queue.display.manage`, inside the existing `queue.*` namespace, so organization and branch
  administrators hold it through the matrix they already have. **No role was added** and
  `DELEGABLE_CAPABILITIES` is unchanged (3 entries) — a display is branch configuration, not a delegable
  front-desk act. The capability is decided *inside* the route through the same `check_granted` the shared
  dependency uses, because a `Depends(require_permission(...))` refusal is answered before the route body runs
  and therefore cannot be recorded as `queue.display.denied`.
- **MP-46 (denial accounting).** A refused display action writes **one** `queue.display.denied` row
  (`target_type=queue_display`, actor, role, org, branch, status, reason) *before* the refusal, then answers
  **403** (missing capability) or **404** (foreign or missing row) carrying the internal marker
  `X-AMSDP-Denial-Audit`. `backend/common/denial_audit.py` — the single recording site created by Q-2 — strips
  that header and **skips its generic `request.denied` row**, so one denial stays one row (Q-2 §10, AC-21)
  instead of being counted twice. If the specific row cannot be written the marker is omitted, so the generic
  recorder still leaves the denial visible somewhere. An **anonymous** probe writes nothing: it cannot be
  attributed to a tenant (the Q-2 exclusion, unchanged), and the public route's unknown-code behaviour is
  untouched.
- **Tenancy.** `organization_id` comes from the authenticated principal; a branch is validated against it and
  against `branch_accessible`; a foreign display is a non-disclosing 404. No request body is ever read as an
  authority claim.


**New admin page `frontend/pages/queue-displays.js`** — branch selector, board list with code / language /
scope / status, create-and-edit dialog (name, code, language, scope, department, room, doctor membership,
footer), the three MP-45 publication toggles, enable/disable as a single audited PATCH, and a **copyable display
URL** (`/queue-display/<org>/<branch>?display=<code>`). Pure rules live in `frontend/lib/displays.js`
(`codeLooksValid`, `validateDisplayDraft` returning **i18n keys**, `createPayload` sending a target only for the
chosen scope, `patchPayload` sending only what changed, `displayUrl`) so they are testable without a DOM. The
screen is offered only under `can('queue.display.manage')` and shows `PermissionDenied` otherwise — a courtesy,
never the boundary.

### 4.3 MP-38 / MP-37 / MP-42 / MP-43 / MP-45 (page halves) and MP-28

`frontend/pages/queue-display/[org]/[branch].js` was rewritten around four rules:

1. **Language precedence (MP-38 / AC-08).** `?lang=` → the **configured** `display.language` from the API →
   the device preference, and the device preference is consulted **only** on an unconfigured branch board. A
   configured board therefore reads and writes no storage at all, so *clearing a browser changes nothing*; an
   operator's own switch is written into the URL (`history.replaceState`) and survives a TV restart without
   storage.
2. **Validator handling (MP-43).** The weak `ETag` is kept and sent as `If-None-Match`; a `304` returns before
   any `setState`, so an idle screen does not re-render on the ten-second poll.
3. **Presentation (MP-38 / AC-11).** The display's configured **name** heads the board; the type scale is
   `clamp()` against the viewport (`styles/global.css`), the token is the largest element by construction
   (`clamp(1.8rem, 5.2vw, 6.5rem)`), and the old fixed `max-width:1180px` card cap is gone
   (`max-width:min(96vw,1800px)`); the facility footer renders in the board's language.
4. **Absence is honest (MP-37 / MP-42 / MP-45).** `room_name`, `patients_waiting` and
   `estimated_wait_minutes` are rendered **only when present in the payload**; a `null` room renders `—`; the
   estimate carries `≈` and the words "estimated wait" beside the number (never a bare figure, R-13).

**MP-28.** The board's page-local `{bn,en}` dictionary and its local translator are gone (`lib/i18n.js` keys
`dqds*`), and the same was done for the patient tracking page (`pqt*`), which still carried one. The existing
`i18n-coverage.test.mjs` now enforces both through the shared dictionary; the new tests additionally assert no
page-local table can return.

### 4.4 MP-35 — the outstanding demo-seed deliverable

`backend/seed/seed_demo.py` gains `DEMO_DISPLAYS` and `_seed_displays()`, called after rooms/departments:

| Display | Code | Language | Scope | Footer |
|---|---|---|---|---|
| Cardiology Board | `cardio` | `bn` | `department` → `demo-dp-br1-card` | `কার্ডিওলজি বিভাগ — চেম্বার ২০১` |
| Main Waiting Hall | `main-hall` | `en` | `branch` | `Please keep your token visible` |

Two boards in **one** branch, different in every dimension a facility can configure — the pair MP-40 needs and
a working example for a new facility. Synthetic demo data only; idempotent (an existing board is never
rewritten, so a re-run cannot undo an administrator's choices); `organization_id` always taken from
`DEMO_ORG`. **Not executed**: the seed needs a database this host does not have, and no live database was
touched (§12).

### 4.5 MP-24 — queue history

`frontend/pages/queue-history.js` consumes the **existing** `GET /api/v1/queue/history` (unchanged) through
`frontend/lib/queue/history.js`: branch / doctor / date / status selectors, a per-status tally built from what
the server returned (never re-classified), and a paginated table (token, position, patient, status, source).
The query builder omits empty optional filters rather than sending `""` — the server reads an absent
`branch_id` as "the caller's branch" and an absent `status` as "every status", and `""` is neither. Branch
scoping, doctor/assistant self-scope and the non-disclosing 404 stay where they already were, in the route; the
test asserts the route still owns them and that history is **not** filtered to live statuses.


### 4.6 MP-25 — durable rate limit, estimate flag, QR print flow

| Part | What changed |
|---|---|
| **Durable limiter** | New model `TrackingRateBucket` (`tracking_rate_buckets`: `bucket` PK, `window_started_at`, `hits`) and new helper `common/rate_limit.py::hit()`, which allocates one request with a single `INSERT … ON CONFLICT (bucket) DO UPDATE … RETURNING`. PostgreSQL serialises two workers updating the same row, so the budget is shared across processes and survives a restart — the property the module-level dict could not have. The window is **fixed**, not sliding (at most 2× the limit across a boundary); that is stated in the module docstring rather than discovered later |
| **Route wiring** | `appointment/tracking.py::_rate_limited` charges the durable budget (`pqt:<ip>`, 10 per 60 s) and refuses with **429 + `Retry-After`** and the rate headers. The in-process window remains only as a **fallback** when the database cannot be reached, so a public tracking link never 500s; while it is in force the budget is per process again, and that is written down rather than hidden |
| **Estimate label** | The tracking payload now carries `"estimate": true/false` beside `estimated_wait_min`, and the page renders `≈ <n>` with the words "estimated wait" in the patient's language |
| **QR print flow** | `pages/track/[token].js` shows the QR from the existing `/api/v1/track/{token}/qr`, offers a Print button, and prints a token card via `@media print` rules that keep the token and the QR and drop the screen furniture. Nothing printed identifies the patient: no name, no mobile, no record id |
| **MP-28 residue** | The tracking page's page-local dictionary also moved into `lib/i18n.js`; its status map resolves through the shared dictionary instead of English literals |

**Migration.** `backend/alembic/versions/e1b7c4a9d236_add_tracking_rate_buckets.py`, `down_revision =
'd3f5a7b91c24'` — the graph's single head, confirmed with Alembic's own `ScriptDirectory` (`heads
['d3f5a7b91c24']`, 18 revisions before this one). One additive table plus one index, created only when absent;
forward-only and idempotent, exactly like the existing revisions.

---

## 5. Files changed

**New (12):** `backend/queuing/displays.py` (MP-39 API + MP-46 denials) ·
`backend/common/rate_limit.py` (MP-25 budget) ·
`backend/alembic/versions/e1b7c4a9d236_add_tracking_rate_buckets.py` ·
`backend/tests/test_display_admin.py` (13 tests) · `backend/tests/test_tracking_rate_limit.py` (5) ·
`frontend/pages/queue-displays.js` · `frontend/pages/queue-history.js` · `frontend/lib/displays.js` ·
`frontend/lib/queue/history.js` · `frontend/tests/display-board.test.mjs` (9) ·
`frontend/tests/display-admin.test.mjs` (11) · `frontend/tests/queue-history.test.mjs` (6).

**Modified (10):** `backend/common/models.py` (+`TrackingRateBucket`) · `backend/common/denial_audit.py`
(domain-denial marker) · `backend/queuing/main.py` (mounts the admin router) ·
`backend/appointment/tracking.py` (durable limiter + estimate flag) · `backend/seed/seed_demo.py` (two demo
boards) · `frontend/pages/queue-display/[org]/[branch].js` (MP-38 rewrite) ·
`frontend/pages/track/[token].js` (MP-25 + MP-28) · `frontend/lib/i18n.js` (`dqds*`, `disp*`, `hist*`, `pqt*`
keys) · `frontend/styles/global.css` (TV scale + print rules) · the two test files whose callbacks were
unclosed (§4.1).

**Deliberately not modified:** `.clinerules` (the owner's uncommitted edit), every Product-Owner-controlled
document (§11), `frontend/pages/queue.js`, and every route of `queuing/main.py` other than the router mount.


---

## 6. Tests run — exact commands and results

| # | Command | Result |
|---|---|---|
| 1 | `cd frontend; npm test` (Node 24.12.0) | **493 tests · 491 pass · 0 fail · 0 cancelled · 2 skipped** |
| 2 | `node --test tests/*.test.mjs` under **Node 22.23.5** (`npx --package node@22`), CI's major | **493 · 491 · 0 · 0 · 2** — same result on CI's interpreter |
| 3 | Same suite **before** the §4.1 fix, Node 22.23.5 | **467 · 450 · 2 fail · 13 cancelled** — the CI failure reproduced locally |
| 4 | `cd frontend; npm run build` | **✓ Compiled successfully**; `/queue-display/[org]/[branch]` 2.2 kB, `/queue-displays` 4.97 kB, `/queue-history` 4.83 kB |
| 5 | `node --test tests/display-board.test.mjs` | **9 pass, 0 fail** |
| 6 | `node --test tests/display-admin.test.mjs` | **11 pass, 0 fail** |
| 7 | `node --test tests/queue-history.test.mjs` | **6 pass, 0 fail** |
| 8 | `python -m py_compile` on every changed/added Python file | **OK** — `queuing/displays.py`, `queuing/main.py`, `common/rate_limit.py`, `common/models.py`, `common/denial_audit.py`, `appointment/tracking.py`, `seed/seed_demo.py`, both new test modules, the new revision |
| 9 | `python -m pytest tests/test_display_admin.py --collect-only -q` | **13 tests collected** — the module imports and every fixture resolves |
| 10 | `python -m pytest tests/test_tracking_rate_limit.py --collect-only -q` | **5 tests collected** |
| 11 | `python -m pytest tests/test_display_admin.py -q -x` | **ERROR at setup — `psycopg2.OperationalError: connection to server at "127.0.0.1", port 5433 failed: Connection refused`.** **BLOCKED**, not passed |
| 12 | Alembic head graph, `ScriptDirectory.from_config(...).get_heads()` | **`['d3f5a7b91c24']`** before this session's revision — a single head, so `down_revision` is correct |
| 13 | New revision executed on a **scratch SQLite** database: stamp `d3f5a7b91c24` → `upgrade head` **twice** → `downgrade` | `tables_after_upgrade=['tracking_rate_buckets']`; `columns={'bucket':'VARCHAR(120)','window_started_at':'DATETIME','hits':'INTEGER'}`; `pk=['bucket']`; `indexes=['idx_rate_bucket_window']`; the second `upgrade head` emitted **no** migration (idempotent); `table_after_downgrade=False` |
| 14 | FastAPI route table via `app.openapi()` | `/api/v1/queue/displays` **get, post**; `/api/v1/queue/displays/{display_id}` **patch**; the public `/api/v1/queue/display/{org_code}/{branch_code}` **get** unchanged |

**Not run, and why:**

- **The backend pytest suite and both new backend modules** — no PostgreSQL, no Docker (§1). They are
  authored, collectible and compiled; that is **not** evidence of passing behaviour.
- **`alembic upgrade head` against PostgreSQL**, and therefore D5's "verified on a scratch database" — the
  SQLite probe in row 13 exercises the revision's DDL and its idempotency guard, not its PostgreSQL behaviour.
- **Offline SQL rendering** (`alembic upgrade head --sql`) — it fails at `sa.inspect()` on Alembic's
  `MockConnection`. That is a property of this chain's **existing** idempotency pattern (`d3f5a7b91c24` does
  the same), not something this revision introduced; recorded rather than worked around.
- **Any browser, load or live-API evidence** — B-2 / B-4 (§8).

---

## 7. CI evidence — what the pipeline says, and at which commit

| Fact | Value |
|---|---|
| Last run touching this SHA | CI **#34**, run `45651581256`, head **`fd4d3656738dfef0885cfc86307903305aa2f08d`**, 2026-11-25T16:10:42Z → 16:19:17Z, conclusion **failure** |
| Backend job at that SHA | **succeeded** (`139337314777`) — install, `alembic upgrade head`, `python -m pytest -q`, 8m 16s |
| Frontend job at that SHA | **failed** (`139337315238`) at `Run frontend tests`, ~1 s (§4.1) |
| Any run at the **current working tree** | **none** — nothing in this session has been committed or pushed |
| Therefore | The backend job's green at `fd4d365` is real CI evidence **for that commit only**. There is **no** CI evidence for any change in this report, and none of it is claimed |

**A green pipeline is still not established.** Backend green + the frontend fix predicts a green run, but a
prediction is not a run. MP-33 stays **open** until a run at a commit containing these changes reports green —
one fact that needs saying before someone quotes "CI is fixed".


---

## 8. Security and negative-control evidence

| Control | How it is held, and where it is asserted |
|---|---|
| **Tenant key** | `organization_id` only; `backend/queuing/displays.py` derives it from `auth.organization_id`, never from a body. Asserted by `test_a_cross_tenant_patch_is_a_404_and_a_recorded_denial` and by a frontend assertion that `data.organization_id` appears nowhere in the module |
| **Branch scope from the token** | `_branch_or_404` requires `Branch.organization_id == auth.organization_id` **and** `branch_accessible(auth, branch.id)` |
| **Fail-closed 404, never 403, for cross-tenant access** | The foreign display and the missing display take the same path; the test asserts the stored row is unchanged and the caller's own tenant carries the denial row |
| **UI is not the boundary** | Controls are offered only under `can('queue.display.manage')`; the server re-decides it. `test_a_receptionist_is_refused_and_the_refusal_is_one_row` fails the request at the API |
| **Denials audited, once** | `queue.display.denied` written before the refusal; the marker suppresses the generic duplicate; the test asserts `request.denied` has **zero** rows for the same request |
| **Anonymous probes write nothing** | `test_an_anonymous_caller_gets_401_and_writes_nothing`; the public board's unknown-code path is untouched (`display.py` unchanged this session) |
| **A switched-off field is absent, not hidden** | `test_mp45_switching_a_field_off_removes_it_from_the_public_body` asserts on `response.text`; the page renders a field only when it is present |
| **No new privilege** | No role added; `DELEGABLE_CAPABILITIES` unchanged at 3 entries, asserted against `backend/common/permissions.py` |
| **No patient identity on public surfaces** | The board renders doctor name, token, counts, room label, estimate; the test asserts no `patient_name`/`patient_id`. The printed token card carries the token and the QR only |
| **No secrets** | The diff was scanned for `password|secret|token=|api_key|BEGIN RSA/PRIVATE`; the only match is a removed variable name in the tracking-page rewrite. No credential, token or key is added, echoed or logged |
| **Existing contracts preserved** | The historic two-segment board payload is untouched (asserted); the queue-history route is unmodified and its test asserts it still scopes, still 404s and still returns terminal statuses |

**The one shared-file change.** `common/denial_audit.py` gained a single additive concept: a route that has
already written a domain-specific denial row marks the response, and the middleware strips the marker and skips
its generic row. It fails safe both ways — no marker means the generic row is written as before, and a marker is
only set after the specific row commits. The alternative (two rows per denial) would have violated Q-2 §10 and
AC-21. **It has not been executed against a database on this host**, so it is IMPLEMENTED and reviewed, not
TESTED.

---

## 9. Blockers — precise, and what each one still blocks

| ID | State | Still blocks |
|---|---|---|
| **B-1** (live reseed withheld) | unchanged | Any claim that the deployment's dataset matches `seed_demo.py`; MP-35's seed cannot be demonstrated there |
| **B-2** (live runtime verification) | unchanged | MP-01's evidence, MP-03, MP-31, MP-32, MP-40, and every D8 runtime-evidence gate |
| **B-3** (midnight rollover observation) | unchanged | MP-44's observation half — an actual deployment watch |
| **B-4** (deployment DB access method) | **undecided by the Product Owner** | Reading the deployment's schema revision (MP-01); applying `d3f5a7b91c24` or this session's `e1b7c4a9d236`; any evidence from the live stack |
| **B-8** (audio hardware) | unchanged | MP-03; MP-32's audibility half |
| **B-9 — new** | CI **log text** needs an authenticated session; the API exposes step conclusions but `output.text: null` | Confirming the original failure message verbatim. Mitigated: the cause was reproduced on CI's Node major and fixed |
| **Host limit — new** | No PostgreSQL and no Docker on this Windows checkout | Every backend test execution, `alembic upgrade`, and therefore every TESTED claim for backend code here |

---

## 10. Milestone impact

| Milestone | Before | Now |
|---|---|---|
| **M-9 — multi-display functional** | not met | **closer**: MP-38 and MP-39 exist and are tested at page/rule level, MP-35's seed exists, MP-46's denial accounting exists. **Still not met** — the backend halves are unexecuted here and MP-40 needs B-4 |
| **M-10 — Hackathon Version complete** | not met | unchanged; AC-09/AC-12 need a running stack |
| **M-6 — admin surfaces** | met | unaffected |
| **M-7 — reporting** | not met | unchanged — MP-23 awaits a decision (§11.1) |


---

## 11. Product Owner decisions required

### 11.1 MP-23 — operational reports (Business Rules §43)

Full brief: `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md`. Summary:

| Option | Scope | Effect on M-7 | Position |
|---|---|---|---|
| **A** | Complete BR §43 — appointments by day/doctor/branch, status counts, walk-ins, queue activity, utilisation | Satisfies M-7 in one step; ≈ 4.0 engineer-days plus tests; reconciliation evidence needs MP-01 | not now |
| **B** | Defer MP-23 explicitly to a later phase | M-7 explicitly unmet **by decision**; nothing else is blocked | fallback if the demonstration is the priority |
| **C** | MVP subset — appointments by day/doctor/branch, status counts and walk-ins from existing tables; queue activity and utilisation deferred **in writing** | M-7 partially met; ≈ 2.0 days; every figure reconcilable with **no schema change** | **recommended** |

**Why C.** The first three §43 dimensions can be answered from `appointments` and `queue_entries` with no
schema change, and each reconciles against a fixed day. Queue activity and utilisation need definitions the
business rules do not yet pin down ("active minutes" of what?), and inventing them is a product decision, not
an engineering one. C delivers a truthful report and defers exactly the part that needs owner definition.

### 11.2 MP-04 — the voice-pack deferral versus the API that exists

PO-05 defers the W3 admin UI; the server API, the `voice_packs` table and its policy layer already exist and
are exercised by tests. The audit's F-6 records this as approved-but-unbuilt-and-undecided; the discrepancy is
that a **deferred feature already has a working backend**.

**Recommendation: maintain the deferral**, and have the limitations report state "API present, administration
deferred" at the next documentation window (MP-34, itself gated on PO-09). Reopening would need PO-05 answered
*and* an administration surface demonstrating that every `voice_pack_policy.py` refusal still holds. What must
not happen is the current state being read as approval: an API is not a feature, and a deferred administration
surface is still deferred.

### 11.3 Nothing else needs a decision

MP-09/13/14/15 need the **first clean rehearsal** (MP-32), which needs MP-31, which needs B-2/B-4 — an
environment dependency, not a decision. MP-11/12 (Q-6(c)), MP-21, MP-26 and MP-27 stay deferred.

---

## 12. What this report does NOT claim

1. **No item is ACCEPTED.** Acceptance is the Product Owner's; nothing here was signed.
2. **No item is VERIFIED.** Every artefact is a local test run, a source assertion or a scratch-database DDL
   execution. There was **no browser session, no live API call, no deployment query** (B-2/B-4).
3. **No backend behaviour is TESTED here.** The 18 new backend tests are authored, compiled and collectible;
   the suite could not run without PostgreSQL (§6, row 11). A claim that they pass would be invented.
4. **The migration is not applied anywhere.** It was executed only on a throwaway SQLite file, and it is
   **not** applied to the deployment — that needs B-4 *and* a separate go-ahead.
5. **Nothing is committed or pushed.** The working tree carries the changes; `.clinerules` still carries the
   owner's own uncommitted edit, untouched.
6. **No live data was read, written or reseeded.** No host was contacted; no port was opened.
7. **CI is not proven green.** The fix predicts a green frontend job; that prediction is not a run (§7).
8. **M-9 and M-10 are not met** and are not implied by any of the above.


---

## 13. Next actions, in dependency order

| Order | Action | Owner |
|---|---|---|
| 1 | Commit the code changes on `hackathon-mvp` (path-grouped; no push during an active freeze) and let CI run at the new SHA — the only way MP-33's claim can be earned | Engineer, with A-4 authority |
| 2 | Answer **B-4** (`docs/deployment/AMSDP_B4_Database_Access_Decision_Brief_V1.0.md`) — unblocks MP-01, the post-migration baseline, MP-30/31/32/40, and the two outstanding revisions on the deployment | **Product Owner** |
| 3 | Decide **MP-23** (Option A / B / C) | **Product Owner** |
| 4 | Re-affirm or reopen the **MP-04** deferral | **Product Owner** |
| 5 | With a database available: execute `test_display_admin.py` and `test_tracking_rate_limit.py`, then the whole backend suite — the TESTED step for §4.2 and §4.6 | Engineer |
| 6 | Only then: MP-31 → MP-32 (first clean rehearsal), which releases PO-04's MP-09/13/14/15 | Engineer + owner |

---

## 14. Governance and skill compliance (`.clinerules` §6)

| Requirement | How it was met |
|---|---|
| §2 automatic routing — read the docs index before acting | §2 table; every governing document was opened in this session, not remembered |
| §3 non-negotiables | Tenant key `organization_id` only; 404 not 403 across tenants; server-side enforcement on every new route; append-only audit with denials recorded and nothing deleted; forward-only idempotent migration; no secrets; no unverified capability claim (§12) |
| §4 domain routing | Multi-tenant data, DB schema, queue/workflow and audit rows applied. **No installed skill exists** (§5) — the applicable governance documents were used instead, as required, and no skill is claimed |
| §6 compliance reporting | This section |
| §7 evidence standard | IMPLEMENTED / TESTED / VERIFIED / ACCEPTED distinguished per item; nothing promoted on one artefact |
| §8 LLM routing | Not a model-selection decision: 12 new files and 10 modified is the escalation case by definition |
| §9 execution boundaries | No destructive git operation; the owner's `.clinerules` edit preserved; tests run where the mandate asked for them; logs kept small. One 0-byte artefact created by a failed shell `cd` was spotted in `git status` and removed before finishing |
| §11 documentation placement | Report under `docs/implementation/`, decision brief under `docs/decisions/`; nothing moved, renamed, deleted or overwritten; the index gains one revision entry |
| §12 documentation reading | Index read first; large documents read in sections; no owner-controlled document modified |
| Roadmap §7 D1–D9 | D1 smallest complete change; D2 server-side enforcement; D3 tenancy; D4 before/after audit; D5 forward-only idempotent revision; D6 negative tests authored; **D7 partially unmet** (backend unexecuted); D8 no runtime evidence → BLOCKED declared, not claimed; D9 this report |
| Roadmap §8 sequencing | Rule 8's public-surface contract preserved (historic payload asserted unchanged); rule 9's "MP-39 after MP-36–MP-38"; no freeze bypassed; no PO decision taken |

**Deviations and exceptions, stated rather than smoothed over:**

1. **A shared security module was modified** (`common/denial_audit.py`) to keep one denial to one row — additive,
   fails safe, and unexecuted here.
2. **Two test files were edited** to fix their structure — not to force a green result, but because the missing
   brace *was* the CI failure. No assertion was weakened or removed.
3. **The scratch-DB verification used SQLite**, not PostgreSQL, because none exists on this host. It proves the
   revision's DDL and idempotency; it does not prove PostgreSQL behaviour, and the report says so.
4. **MP-25's fallback keeps the limitation visible**: while the database is unreachable the budget is per
   process again — exactly the defect MP-25 exists to end. Documented in the module and here.

---

## 15. Document control

| Field | Value |
|---|---|
| Document | `docs/implementation/AMSDP_Controlled_Implementation_Execution_Report_V1.0.md` |
| Version | V1.0 — first issue, 26 November 2026 |
| Status | **ISSUED** (not ACCEPTED) |
| Trigger | Product Owner implementation mandate, 26 November 2026, following the roadmap audit |
| Baseline | `hackathon-mvp` @ `fd4d3656738dfef0885cfc86307903305aa2f08d` |
| Predecessor evidence | `docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md` |
| Registers updated | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (§12, additive); `docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 49) |
| Migration authored | `e1b7c4a9d236` — applied to **no** deployment and **no** database on this host |
| Nothing overwritten | No historical report, register or index entry was edited or removed |

*End of report.*

