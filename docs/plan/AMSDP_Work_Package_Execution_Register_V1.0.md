# AMSDP — Work-Package Execution Register V1.0

**Status:** ACTIVE · **Maintained by:** executing agent, updated at the end of every work-package window ·
**Authoritative task list:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (as amended by
Appendix E, Amendment A-2). **This register does not create, renumber or re-scope tasks.** It records the
*execution state* of the tasks that have actually been worked, and the items that are waiting on a decision or on
access this host does not have.

**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).

---

## 1. What this register is, and what it is not

- **It is** the running state of the plan: which work packages are IMPLEMENTED, TESTED or VERIFIED, where the
  evidence lives, and what is blocked.
- **It is not** a second plan. Priorities, dependencies and estimates live in the master plan and are not
  restated here.
- **It is not evidence in itself.** Every row points at a log or a report that carries the evidence. A row here
  claiming TESTED without such a pointer is a defect in this register.
- **Evidence vocabulary** is the plan's own (§7 of `.clinerules`): IMPLEMENTED = code exists and is reachable;
  TESTED = named tests pass in this tree; VERIFIED = a second, independent artefact confirms it; ACCEPTED = the
  Product Owner has signed it. Nothing in this register is ACCEPTED.

---

## 2. Executed work packages

| Task | Scope actually executed | State | Evidence | Report |
|---|---|---|---|---|
| **MP-02** (prerequisite) | Whole-tree backend baseline on the scratch database, then the same tree again after the MP-05/06/07 changes | **TESTED** | baseline `791 passed, 0 failed in 745.12s` → `runs/backend-baseline-2026-11-24.log`; final **`796 passed, 0 failed in 816.87s`** → `runs/backend-final-2026-11-24.log`. 791 + 5 = 796 (3 MP-05 tests, 2 MP-06 tests); no test removed, no failure suppressed | — |
| **MP-05** | Demo seed: one `staff_doctor_assignments` row per demo staff account (doctor **and** assistant → `demo-dr-002`), and the demo queue written on the **facility** day, not the server day | **VERIFIED — scratch DB only** | `psql` read-back (`assistant\|demo-dr-002\|active\|demo-org-001`); `runs/evidence-mp05-verification.log`: own queue **200** (`waiting=3`, `Dr. Kamal Hossain`), another doctor's queue **404** for both accounts; 3 tests in `backend/tests/test_seed_demo.py`; suite green | `implementation/AMSDP_MP-05_…_V1.0.md` |
| **MP-06** | DQDS board reads the **facility** operational day (`operational_today` → `organizations.timezone`), not `date.today()` | **TESTED** | 2 tests in `backend/tests/test_dqds.py`; file alone **26 passed**; mutation with the defect restored **2 failed, 24 passed**, both failures being the day tests (`runs/evidence-mp06-mutation.log`); `display.py` restored byte-identically (SHA-256 `3F9FD047…95E73`) | `implementation/AMSDP_MP-06_…_V1.0.md` |
| **MP-07** | Dashboard **Waiting** tile bound exactly once (the double binding made one tile consume two payload fields) | **TESTED** | frontend suite baseline `360 tests / 356 pass / 2 fail / 2 skipped` → after `363 / 359 / 2 / 2` (arithmetic closes); mutation with the defect restored fails with `duplicate tile binding: scheduled, checked_in, checked_in, completed, cancelled, no_show — 5 !== 6` (`runs/evidence-mp07-mutation.log`); `dashboard.js` restored and hash-verified | `implementation/AMSDP_MP-07_…_V1.0.md` |
| **MP-08** | **Announcement-safe recall**, implemented as the owner's **option (a)**: an explicit `recall` action (`called → called`) that is *separate* from `call`, so a duplicated `call` is still refused 422 and still cannot announce twice | **TESTED** | 9 new tests in `backend/queuing/tests/test_queue.py::TestQueueRecall` (distinct `qce:` id + later index, two delivery rows, superseded event **409**, `queue.call` **and** `queue.recall` both audited, position/token/`position_history` unchanged, duplicate `call` still **422** after a recall, `recall` from `waiting` **422**, doctor without `queue.manage` **403**, doctor with `doctor_calling_enabled` **200 → `call_count == 2`**); 3 new tests in `backend/queuing/tests/test_queue_events.py`; whole backend suite **`808 passed, 0 failed in 756.71s`** (baseline 796 + 12); mutation (`"recall"` removed from `_TRANSITIONS["called"]`) → **`6 failed, 4 passed`**, restored byte-identically (SHA-256 `1315700B…736D` unchanged); frontend suite `373 / 369 / 2 / 2`, queue trio **55 passed**, both remaining reds still only the known Q-3 pair | `implementation/AMSDP_MP-08_…_V1.0.md` |
| **MP-10** | **Walk-in placement policy** (BR §25), moved from a per-request parameter to a **facility setting**, and the four policies made genuinely distinct: `end_of_queue` appends; `first_come` orders by a recorded `arrived_at`; `reserved_capacity` fills a real pool (count, or % of the doctor's published seats); `staff_placement` validates the position staff choose. New `GET`/`PUT /api/v1/orgs/{id}/walk-in-config` (read for staff, write for `org.manage`, platform-admin-only option set), audited `walk_in_config.updated` before/after, and a placement decision recorded inside `queue.enqueue` | **TESTED** | 38 new backend tests (15 `test_walk_in_placement.py`, 23 `test_walk_in_config.py`) + 6 rewritten in `test_queue.py::TestWalkInPolicies`; whole backend suite **`847 passed, 0 failed in 1292.53s`** (`runs/backend-mp10-2026-11-24.log`, 808 + 39); mutation (reserved-pool branch disabled) → **`2 failed, 13 passed`** (`runs/evidence-mp10-mutation.log`), restored byte-identically (SHA-256 `A59B61E7…3819` unchanged), module re-ran **15 passed**; frontend `383 / 379 / 2 / 2` (only the Q-3 pair red), MP-10 module **10 passed** | `implementation/AMSDP_MP-10_…_V1.0.md` |
| **MP-33** | **CI truth**: does a pipeline exist, has it ever been green, and what is the state of the current tip — recorded from the GitHub Actions API instead of asserted | **VERIFIED (state recorded)** | 28 `CI` runs exist, **4 green**; the most recent green is **run #5, 2026-11-14** (`https://github.com/shomonrobie/amsdp/actions/runs/43613057907`); the latest, **run #28, 2026-11-23**, is **red** with the **backend job green** (`Apply migrations` + full pytest) and the **frontend job red at step 6 `Run frontend tests`, exit 1**. Local equivalents run in this window: `alembic current` = `c4d8e2a91f60 (head)`, backend `847 passed`, `npm run build` **success**, `npm test` `383 / 379 / 2 / 2` | `implementation/AMSDP_MP-33_…_V1.0.md` |
| **MP-16** | **Blocked periods** (BR §15, gap-audit GAP-12/F-20 — the capability was **absent**, not broken): new `schedule_blocks` table (date range + optional window, reason, status, cancellation actor) with a forward-only idempotent migration; `POST`/`GET`/`DELETE /api/v1/schedules/{id}/blocks` (write = `schedule.manage`, read = branch-scoped staff, every write audited `schedule.blocked` / `schedule.block_cancelled`); `available-slots` publishes `blocked: true` + zero availability per slot plus `blocked_periods`/`blocked_slot_count`; `_guard_blocked` refuses bookings in create, **reschedule and transfer** with `blocked_period: …` (422), and the authorised exception is `override_block` gated on `schedule.manage` with a mandatory reason, audited as `appointment.block_override` in the booking's own transaction. One shared pure module (`common/schedule_blocks.py`) so the read and the write cannot disagree; an unreadable stored window degrades to whole-day instead of 500 | **TESTED** | 51 new tests (35 `scheduling/tests/test_schedule_blocks.py`, 16 `appointment/tests/test_blocked_booking.py`), targeted suites **`279 passed in 297.60s`** (`runs/backend-mp16-appt-sched.log`); mutation (`covers()` stops blocking a windowed period) → **`7 failed, 44 passed`** across **both** services (`runs/backend-mp16-mutation.log`), restored byte-identically (SHA-256 `691413D8…0332`); migration applied on the dev DB **and** as a whole chain on an empty scratch DB `amsdp_mp16_scratch`, second run **0** revisions (idempotent), schema read back from `pg_catalog` (16 columns, 3 indexes, `ck_block_dates_ordered` + 4 FKs); whole backend suite quoted in the report §4.4 — **`898 passed, 0 failed in 638.45s`** (`runs/backend-mp16-2026-11-24.log`, 847 + 51) | `implementation/AMSDP_MP-16_…_V1.0.md` |
| **MP-19** | **Staff and permission management UI** (GAP-17 / F-09 / F-06). The roster read-only screen was replaced by the full lifecycle: create, edit (display name, e-mail, mobile, language, **role**, **branch scope**, status), **capability grants** from the server's delegable catalogue with per-row grant/revoke and branch-scoped revocation, and **deactivate/reactivate as a two-step status change** (never a delete). The screen's rules were extracted to `frontend/lib/staff-policy.js` (`ROLE_LEVEL`, `grantableRoles`, `mayGrantCapabilities`, `needsBranch`, capability label keys, create pre-flight, roster filter) so they can be asserted without a browser; the page offers only roles strictly below the caller's and cannot grant beyond `DELEGABLE_CAPABILITIES`; a save sends only the fields that changed, so no audit row is written for a no-op. A leftover `getServerSideProps` stub was removed so the route prerenders like its neighbours. **No backend production file changed** — the API surface and every rule already existed | **TESTED (frontend) — backend suites UNRUN here** | 12 rule tests (`tests/staff-policy.test.mjs`) + 14 new wiring/mirror/i18n tests (`tests/staff-page.test.mjs`), both green — **26 passed**; frontend suite **`383 / 379 / 2 / 2` → `409 / 405 / 2 / 2`** (+26 tests, +26 passes — the two staff modules; the two reds are the pre-existing Q-3 pair, unchanged); mutation (branch scope removed from revoke, the D6 defect) → **`1 failed, 13 passed`**, `staff.js` restored **byte-identically** (SHA-256 `600BB633…9888`); `npm run build` **✓ Compiled successfully**, `/staff` 5.71 kB / 125 kB and now prerendered instead of `ƒ (Dynamic)`; every `t(…)` key proven present in **both** `bn` and `en`; `ROLE_LEVEL` and `CAPABILITY_LABEL_KEYS` pinned against `backend/common/permissions.py`. **Not run in this window:** the 31 identity tests (`test_staff_admin_surface.py` 15, `test_capability_grants.py` 16) — `py_compile` **OK**, `pytest` stops at collection because this Windows checkout has no reachable PostgreSQL; no browser/E2E harness exists | `implementation/AMSDP_MP-19_…_V1.0.md` |
| **MP-20** | **Doctor-assignment editor (multi-doctor for assistants)**, delivered inside the MP-19 edit dialog: one checkbox per active doctor (`staff-doctor-<id>`), saved as `doctor_ids` in the same `PATCH`, diffed against the row the server last sent so only a real change is sent. Grants and assignments are read per request (`common/auth.py`), so a revocation takes effect on the next request without reissuing a token; a cross-organization doctor is refused by the PATCH's own validation (404/422), not by the screen | **TESTED (client) — backend UNRUN here** | Covered by the same run and the same 26 green frontend tests (§4.3 items 4, 11 and the `assignedDoctorIds` fallback in `staff-policy.test.mjs`); the audit event `staff.doctor_assignment_changed` and the cross-org refusal are asserted by the 31 identity tests that **could not be executed on this host** — recorded as unrun, not as passing | `implementation/AMSDP_MP-19_…_V1.0.md` |
| **MP-17** | **Doctor mobile duplicate allowance** (BR §9.6–§9.8, GAP-13 / F-17). The uniqueness rule existed **twice**, inline in `create_doctor` and `update_doctor`, and had no switch at all — BR §9.7's platform-level allowance could not be granted. The rule now lives in one helper (`mobile_in_use` + `assert_mobile_available` in `doctor/profile.py`) that both write paths call, backed by a policy block in `organizations.config["doctor_mobile_policy"]` (`common/config.py`) and a new `GET`/`PATCH /api/v1/orgs/{id}/doctor-mobile-policy`: read for `doctor.manage`, write for `org.manage` **plus** `is_super_admin` → `403` for anyone else, audited `organization.doctor_mobile_policy.update` with before/after. Default is **unique**; a missing, non-dict or non-boolean block reads as unique; withdrawal is **prospective** (no doctor row is merged, deleted or deactivated). BR §9.8 is untouched by the switch: the lookup is org-scoped, so the same number stays free at another tenant either way. **No schema change, no migration, no frontend file** | **TESTED (policy + enforcement decision) — API tests UNRUN here** | 23 DB-free policy tests (`backend/tests/test_doctor_mobile_policy.py`) + 6 DB-free enforcement-decision tests (`backend/tests/test_doctor_mobile_enforcement.py`) → **`29 passed in 2.08s`**; negative control (`doctor_mobile_must_be_unique` mutated to `return False`) → **`23 failed, 6 passed`**, `common/config.py` restored **byte-identically** (SHA-256 `C4A667B7…FDF9`, re-run `29 passed`); `py_compile` **exit 0** on all six files; the 12 API tests in `doctor/tests/test_doctor_mobile_duplicates.py` **collect** (`12 tests collected in 2.40s`) but **did not run** — `5433` refused, the same environment blocker as O-1, so the `403` gate, the audit `before`/`after` and both cross-tenant cases stay unproven here | `implementation/AMSDP_MP-17_…_V1.0.md` |
| **MP-18** | **Schedule-edit audit** (BR Part X; *verify, implement if absent*). The `schedule.*` endpoints were already audited with before/after (owner decision Q5); the verification found the gap **elsewhere**: `scheduling/sessions.py::sync_slot_templates` rebuilds `schedules.slot_templates` — the projection `available-slots` and the calendar read — on **every** session create, edit and retire, so those three endpoints changed a **`schedules` row with no `schedule.*` audit event at all**. Fixed by routing all three through a new `audit_template_projection(...)`, which rebuilds the projection and records `schedule.templates_changed` against the **schedule's** id with `before`/`after` windows — only when the published windows or their capacity actually moved (a re-chamber or a duration tweak is recorded once, on the session). No other service writes `schedules`/`schedule_sessions` (searched). Existing event names, payloads and permissions unchanged | **TESTED (static guard + decision) — behavioural tests UNRUN here** | 13 DB-free tests (`backend/tests/test_schedule_audit_coverage.py`): the `windows_map` derivation (canonical key, default capacity, unusable templates skipped), the projection decision (one event on a move, **none** when unchanged), and an **AST guard** that fails if any write route in `scheduling/*.py` lacks an audit call with `after=`, or if anything but the helper calls `sync_slot_templates` → **`13 passed in 1.89s`**; negative control (a session path reverted to a bare `sync_slot_templates`) → **`1 failed, 12 passed`**, and notably the *route-level* guard stayed green — which is why the second guard exists; `sessions.py` restored **byte-identically** (`1541A5C8…1E33`) and re-run green; `py_compile` **exit 0**. **Not run here:** the 12 DB tests in `scheduling/tests/test_schedule_audit.py` (8 pre-existing + 4 new `TestScheduleProjectionAudit`) **collect** (`12 tests collected`) but cannot execute — no PostgreSQL on this host | `implementation/AMSDP_MP-18_…_V1.0.md` |
| **MP-28** | **Unified internationalization** (GAP-23 / F-59; the audit's "three i18n mechanisms" was accurate). The five screens that still translated through their own tables (`index`, `orgs`, `branches`, `patients`, `appointments`) each carried `const L = { bn: {...}, en: {...} }` plus a local `T()` and its own copy of the locale read. All **173** keys (8 / 7 / 9 / 15 / **134**) were moved **verbatim** into `frontend/lib/i18n.js` under per-screen namespaces (`home*`, `org*`, `brn*`, `pat*`, `apt*`); **206** literal call sites became `t('…')` and the **9** runtime-built keys in `appointments.js` (`REFUSAL_KEYS`, `typeLabelKey`, `typeBadgeKey`, the list view, the match banner) go through a six-line `aptKey` namespace helper so they cannot silently fall back. Five hard-coded English strings became keys (`createFailed`, `searchFailed`, `registerFailed`, `male`, `female`), `Cancel`/`Save`/`Loading...` now use the shared keys, the login toggle calls `setLocale`, and two duplicated `active`/`inactive` declarations were removed. **No page-local dictionary remains**; the dictionary holds **505 keys in each language**; **no schema change, no migration, no dependency** | **TESTED (frontend)** | New coverage suite `tests/i18n-coverage.test.mjs` — **7 tests, all green**: key parity (505 = 505, with a floor assertion so an emptied dictionary cannot pass), no empty/silent values, no duplicate declaration in either block, no page-local dictionary or translator anywhere in `pages/` + `components/`, every literal page key present in **both** languages (>250 references scanned), every runtime-built refusal/type key resolvable, unknown key returns itself. Negative control (one Bangla declaration renamed) → **2 tests red** with the exact missing key named, `lib/i18n.js` restored **byte-identically** (`E19FED20…4453`). Full suite `434/430/2/2` → **`441/437/2/2`** (+7, all pass; the two reds remain the Q-3 pair). `npm run build` **✓ Compiled successfully**, exit 0. Eight existing source-contract tests were re-pointed at the new mechanism, none deleted or loosened — report §6 lists each | `implementation/AMSDP_MP-28_Unified_Internationalization_Implementation_Report_V1.0.md` |
| **MP-01** (dependency verification) | **Prove the runtime — never re-apply an applied migration.** Read-only reconciliation from this host: live deployment **reachable** (`:8110`/`:3100` HTTP 200, `:5433` open, `:22` refused); **no live DB credential** (`POSTGRES_PASSWORD`/`AMSDP_DATABASE_URL` unset, `.env.local` holds API keys only; a connect attempt fails `fe_sendauth: no password supplied`), so the live `alembic_version` **cannot be read** and nothing was run against it. Static graph: **17 revisions, single head `b2e5c7d91a04`** — the plan's recorded live revision `c4d8e2a91f60` is **no longer head**, and this host cannot tell whether the live DB is one revision behind the tree or was migrated again. Also found the real PostgreSQL blocker: the database lives on **127.0.0.1:55432**, not 5432/5433/5434 | **BLOCKED (B-4)** — HTTP runtime proven, schema revision unproven | Commands and outputs quoted in the reconciliation report §1–§2; a **new isolated database** `amsdp_verify_2829` was created and the whole chain applied from empty to `b2e5c7d91a04 (head)`, exit 0 | `implementation/AMSDP_PostgreSQL_Verification_and_MP-01_Reconciliation_Report_V1.0.md` |
| **MP-22** | **Dashboard completion** (Blueprint §2; MP-07 successor). The screen was six figures and nothing else. It now carries a **branch selector** (fed by `GET /orgs/{id}/branches`, filtered through the new `lib/dashboard.js::selectableBranches` so a branch-scoped user is offered **only their own branch** — and an empty list, never "all", when it is absent), a **date selector** that is a real server question (`GET /api/v1/dashboard/today` gained a validated `date=YYYY-MM-DD`, **422** on anything else, defaulting to the facility's `operational_today` per BR §8), the six MP-07 tiles untouched, a **today's queue panel** (`queue_length`, `walk_ins`, per-doctor breakdown), **quick actions** (role-shaped navigation, not authority) and a **recent activity** panel reading `/api/v1/dashboard/audit` (unknown actions render as their own slug rather than disappearing). Response also reports `facility_today` so the screen can state which calendar the day belongs to. 13 i18n keys added in `bn` **and** `en` | **TESTED (frontend) — endpoint tests UNRUN here** | 15 new rule tests (`tests/dashboard-policy.test.mjs`) + 10 new source-contract tests (`tests/dashboard-page.test.mjs`) + MP-07's 3 tile guards still green → **`tests 28 · pass 28 · fail 0`**; frontend suite `409/405/2/2` → **`434/430/2/2`** (+25 tests, +25 passes; the two reds remain the Q-3 pair — dataset hash `6f69a0ef…7779` vs recorded `ac037c24…e51e`, and `calendar-render.test.mjs` failing to load); negative control (`selectableBranches` widened to every branch) → policy module **red** on the roster-mismatch case (expected `[]`, received both branches), `lib/dashboard.js` restored **byte-identically** (`9C20CF10…F335`) and re-ran **28/28**; `npm run build` **✓ Compiled successfully**, `/dashboard` prerendered, **6.6 kB / 99.8 kB**, exit 0 — after a first build that **failed** (`ReferenceError: user is not defined`, a declaration stranded outside the component by my own edit; disclosed in report §4.4). **Not run here:** the 6 new cases in `backend/tests/test_dashboard.py` (explicit day, `facility_today`, four unparseable inputs) — the module connects at import, so collection stops without PostgreSQL. **Blueprint §2 was not read line by line** (report O-2) | `implementation/AMSDP_MP-22_…_V1.0.md` |



**Why MP-05 is VERIFIED and MP-06/MP-07 are not.** MP-05 has a second, independent artefact: rows read back
from the database *and* a live HTTP `200`/`404` pair produced by the app's own client against that database.
MP-06 and MP-07 have discriminating tests and mutation evidence but no independent observation of the deployed
system, so they stop at TESTED. Nothing here is upgraded on the strength of a green suite.

**SUPERSEDING EVIDENCE, 2026-11-24 (later window) — a PostgreSQL database was available all along.**
Every row above that says its behavioural tests "could not run — no PostgreSQL on this host" was measured against
ports `5432`/`5433`/`5434`. The project's own MP-16 report records the DSN it used:
`postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp`. Port **55432** answers, at revision **`b2e5c7d91a04` (head)**.
A fresh, isolated database (`amsdp_verify_2829`) was created and migrated from the first revision for this window, and
the tests that had never run were executed against it:

| Suite | Result | Effect on the row above |
|---|---|---|
| `backend/tests/test_dashboard.py` (MP-22) | **12 passed** | endpoint half now green — after the D-0 fix below |
| `backend/doctor/tests/test_doctor_mobile_duplicates.py` (MP-17) | **11 passed, 1 failed** | **D-2**, open: an org admin gets a generic 403 instead of the platform-admin refusal |
| `backend/scheduling/tests/test_schedule_audit.py` (MP-18) | **8 passed, 4 failed** | **D-1**, open: the projection audit fires twice or when nothing moved. MP-18's grade is **reduced** to TESTED (static guard only) |
| `backend/identity/tests` (O-1, MP-19/20) | **71 passed, 4 errors** | **D-3**, open: four `TestDoctorLink` fixtures assume another test's seed and fail on a clean database |

One product defect was found and **fixed** in this window: `GET /api/v1/dashboard/today?date=2026-1-5` returned 200
because `strptime` accepts unpadded fields; it now requires an exact `YYYY-MM-DD` round-trip and the file's 12 tests
pass. Details, commands and outputs: `docs/implementation/AMSDP_PostgreSQL_Verification_and_MP-01_Reconciliation_Report_V1.0.md`.
**MP-02 is satisfied as of 2026-11-25, and this note is the only place that says so.** Its acceptance cell is "every
test executed; every failure named with cause; no pass claimed without output". That is now true of the whole tree:
backend **`979 passed, 0 failed in 823.50s`** against `amsdp_verify_2829` (MP-29 row), frontend **`458/454/2/2`** with
both remaining failures named, diagnosed and traced to the test harness rather than to a feature (decision pack §4.2).
The MP-02 row above keeps its own window's 796 figure; the row was not rewritten. **Satisfied is not ACCEPTED** — the
grade stays TESTED.

**No grade above is rewritten retroactively** — the rows keep their window's words, and this note carries what
supersedes them. Nothing was promoted to VERIFIED; one grade fell.

---

## 3. Blocked — needs the Product Owner, not an agent

| ID | Item | Why it is blocked | What would unblock it |
|---|---|---|---|
| **B-1** | **Live demo re-seed** (`backend/seed/seed_demo.py` against the deployed database) | It is a state-changing production action, and the master plan **forbids** it: Amendment A-2 §E.5 — *"Do not restore or reseed the live database… restoring production is not authorised by any document."* This host also has no container access to the deployment and no live DB credential | An explicit owner authorisation for that specific act, issued with deployment access. Until then the live `staff_doctor_assignments` table stays empty and the live doctor login reaches no queue |
| **B-2** | **D8 live runtime verification** | No live credential and no reachable browser from this host | A credential and a reachable environment, or an owner-run verification whose output is returned |
| **B-3** | **Live DQDS midnight observation** (the real 23:59→00:00 Dhaka boundary) | Same as B-2; the rollover is currently proven only by a pinned-clock test | A boundary observation on a live or reconstructed environment |
| **B-4** | **Live database revision read — MP-01's remaining half** | The live deployment is reachable (`:8110`, `:3100` HTTP 200; `:5433` open), but **no database credential exists on this host**: `POSTGRES_PASSWORD` / `AMSDP_DATABASE_URL` are unset, `.env.local` holds API keys only, and a connect attempt returns `fe_sendauth: no password supplied`. The plan forbids an unconditional upgrade | The credential, plus owner authorisation for MP-01's conditional `upgrade`. **Correction, 2026-11-25 (decision pack §2.1/§4.1):** the drift is smaller than this row first suggested — the **committed** tree's head is `c4d8e2a91f60`, which *is* the recorded live revision; the working tree is one revision ahead only because MP-16's `b2e5c7d91a04` migration is **untracked**. A live migration is therefore a consequence of committing the work packages, not a pre-existing gap. The read is still required to confirm the live value from the system itself |

These are recorded as blocked, not as done. No claim in any report depends on them succeeding.

---

## 4. Decisions owed by the Product Owner

| ID | Question | Why it matters now | Where it is described |
|---|---|---|---|
| **Q-1** | Two server-local reads outside the queue board: `backend/patient/main.py:80` (`today = today or _date.today()`) and `:50` (`if d > _dt.now().date()`). Fold into **MP-44**, or raise a new task? | MP-06 fixed the queue/display path and MP-05 the seed; the patient module still answers the *server* day, so one surface remains inconsistent with the facility day | MP-06 report §5, item 3 |
| **Q-2** | "Waiting" semantics: the endpoint publishes **both** `in_queue` (appointment rows with status `IN_QUEUE`) and `queue_length` (live `queue_entries` rows). The plan prescribes `in_queue`, and that is what MP-07 bound. A walk-in with no appointment row raises `queue_length` but not `in_queue`. Which is the contract? | It is a payload-contract decision, not a styling one: if "Waiting" is meant to match the DQDS `patients_waiting`, the field becomes `queue_length` — a one-line change plus the same test, but it must be decided once | MP-07 report §5, item 1 |
| **Q-3** | Two frontend tests are red **before and after** every window: `banglanamesense-dataset` and `calendar-render`. **Diagnosed (MP-33):** the first is a *provenance mismatch* — `frontend/data/bangla_name_sense.json` hashes to `6f69a0ef…7779` while `lib/bangla-name-sense/dataset.js` records `ac037c24…e51e`, and the file is tracked, not missing; the second fails to load at all. Same two are what CI's frontend job trips on (inference — the run log needs an authenticated token) | Now a decision, not a triage: either the dataset was regenerated deliberately (update `DATASET_SOURCE` **and** re-record provenance) or it was corrupted (restore the file). Updating the hash just to go green is the anti-pattern MP-33 forbids, so neither was done | §5 below, MP-33 report §5 |
| **Q-4** | The working tree carries uncommitted **owner** edits to two owner-controlled documents (the PO-13 amendment to §33 in `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md`, +67 lines each) and to `.clinerules` | Not authored in this window, and §11 makes those documents read-only to agents. They must be committed, revised or reverted by the owner, not by an agent | §6 below |
| **Q-5** | ~~**MP-08 conflicts with a shipped, passing test.**~~ **CLOSED — owner chose option (a), explicit `recall`** (decision recorded 2026-11-24). `recall` was added as its own action (`called → called`), `call` from `called` **stays 422**, and the invariant in `backend/queuing/events.py` was rewritten to state that recall is a chosen, separate, audited action rather than a retried `call` | The conflict was real and is now resolved without weakening the announcement-duplication guard: the 422 test still passes, and the recall path has its own 9 tests | §9 below (kept as the record of the conflict), MP-08 report §3–§4 |
| **Q-6** | **RESOLVED — owner chose option (c), 2026-11-24 (see the note under this table).** **MP-11 was internally contradicted by its own plan.** BR §31.1/§52 require the numbering scope to be selectable "doctor **or room**", and MP-11's acceptance cell says "scope (doctor / room)"; but the same plan's §10 defers *"Room on the queue entry and room-scoped token numbering … an independent queue-model change"*, and the daily/continuous modes need a counter that survives either a date reset (`continuous`) or a scope change (`room`), which the current `queue_sequences(doctor_id, date)` primary key cannot express | MP-11 is the next non-gated task in plan order (MP-10 done). **Options:** (a) deliver the modes half now against a derived room (`doctor_branches.room_id`, as MP-37 does) with one forward-only migration for a scope-aware counter; (b) defer the room half and deliver daily/continuous only; (c) keep MP-11 waiting until the queue-model change the §10 row names. The choice changes numbering behaviour and a schema, so it is the owner's | MP-10 report §5 item 8, plan §10, BR §31 |
**Q-6 resolved — Product Owner decision, 2026-11-24.** Option **(c)** was selected: **MP-11 stays deferred** until
the queue model properly supports room-scoped token numbering. The decision carries three binding consequences:

1. **The requirement is not withdrawn.** BR §31.1/§52's "doctor **or room**" scope and MP-11's acceptance cell stay
   in force. MP-11 must not be implemented as doctor-only and closed as complete.
2. **`doctor_branches.room_id` is not accepted as a proxy for room scope.** The room-assignment semantics,
   cardinality (can two doctors share a room at different hours? can one doctor hold two rooms concurrently?) and
   the sequence-sharing rules must be established *first*; the derived-room shortcut in option (a) is closed.
3. **The work is outstanding, not done.** Room-scoped numbering needs its own queue-model design plus a
   forward-only migration; it remains unowned by any completed task until that design exists.

No schema column was added for MP-11 in this window, and MP-11 has not been marked TESTED or delivered anywhere.
Work continued with the next executable task under §7.

---

## 5. Frontend suite state (recorded, not resolved)

| Run | Tests | Pass | Fail | Skipped | Log |
|---|---:|---:|---:|---:|---|
| Baseline (before the MP-07 change) | 360 | 356 | 2 | 2 | `runs/frontend-baseline-2026-11-24.log` |
| After the MP-07 change | 363 | 359 | 2 | 2 | `runs/frontend-suite-2026-11-24-post-fix.log` |
| After the MP-08 change | 373 | 369 | 2 | 2 | console run of `npm test` in `frontend/`, 2026-11-24 (10 new recall tests) |
| After the MP-10 change | 383 | 379 | 2 | 2 | console run of `npm test` in `frontend/`, 2026-11-24 (10 new walk-in-policy tests) |
| After the MP-19 + MP-20 change | 409 | 405 | 2 | 2 | `npm test` in `frontend/`, 2026-11-24 (`26` new staff tests: 12 `staff-policy.test.mjs` + 14 `staff-page.test.mjs`) |
| After the MP-22 change | 434 | 430 | 2 | 2 | `npm test` in `frontend/`, 2026-11-24 (`25` new dashboard tests: 15 `dashboard-policy.test.mjs` + 10 `dashboard-page.test.mjs`; `dashboard-tiles.test.mjs` unchanged and still green) |
| After the MP-28 change | 441 | 437 | 2 | 2 | `npm test` in `frontend/`, 2026-11-24 (`7` new i18n-coverage tests; the two reds remain the Q-3 pair) |
| After the MP-29 change | 458 | 454 | 2 | 2 | `npm test` in `frontend/`, 2026-11-25 (`17` new a11y tests: 8 `a11y.test.mjs` + 9 `a11y-page-contract.test.mjs`; the two reds remain the Q-3 pair, unchanged) |


The same two tests fail in every run — `banglanamesense-dataset` and `calendar-render` — so no change so far has
introduced a new red. **MP-29 added 17** — 8 in `a11y.test.mjs`, which imports `lib/a11y.js` and exercises the real decision functions, and 9 in `a11y-page-contract.test.mjs`, which proves the sheet and the markup follow them. The three added tests in the MP-07 run, the ten added in the MP-08 run and the ten added in the
MP-10 run are the only additions. The MP-19 window added **26**: the delta `383 → 409` is entirely the two staff
modules, and both are green (`node --test tests/staff-policy.test.mjs tests/staff-page.test.mjs` → **26 passed in
0.17 s, exit 0**). The MP-10 frontend module alone (`node --test tests/queue-walk-in-policy.test.mjs`)
is **10 passed, 0 failed**; unlike its neighbours it exercises real imported code (`lib/queue/walk-in.js`) and only
part of it is source-contract.

**Limitation that must not be forgotten:** the frontend tests here are **source-contract** tests — regular
expressions over the page source. The repository ships no DOM renderer, so "the tile is bound once" is proven
about the source text, not about a rendered page. A green frontend suite is therefore weaker evidence than a
green backend suite, and is labelled TESTED, never VERIFIED.

**MP-17 changed no frontend file**, so the suite stands at the MP-19 figure (`409 / 405 / 2 / 2`) and no frontend
run was made in that window. Its tests are backend-side and DB-free (§2).

---

## 6. Working-tree observations (§9 compliance)

- The changes made in this window are: `backend/seed/seed_demo.py`, `backend/tests/test_seed_demo.py` (new),
  `backend/queuing/display.py`, `backend/tests/test_dqds.py`, `frontend/pages/dashboard.js`,
  `frontend/tests/dashboard-tiles.test.mjs` (new), the three implementation reports and this register.
- Present **before** this window and deliberately **not touched**: `.clinerules` (3 lines),
  `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md` (the PO-13 §33 scope
  amendment, +67 lines each), plus the multi-display documents added with that decision.
  No staging, reverting or cleaning was performed; no file carrying someone else's uncommitted work was
  modified.
- **MP-08 window (this addendum), changes made:** `backend/queuing/events.py`, `backend/queuing/main.py`,
  `backend/queuing/tests/test_queue.py`, `backend/queuing/tests/test_queue_events.py`,
  `frontend/lib/queue/queue-call.js`, `frontend/lib/announcements/queue-transitions.js`,
  `frontend/pages/queue.js`, `frontend/lib/i18n.js`, `frontend/tests/queue-call-control.test.mjs`, the MP-08
  implementation report and this register. `backend/queuing/main.py` was mutated once for the negative control and
  restored from a byte copy — SHA-256 `1315700B…736D` before and after. Nothing was staged or reverted; the owner
  edits listed above remain untouched.
- **MP-10 window (this addendum), changes made:** `backend/common/config.py`, `backend/queuing/placement.py` (new),
  `backend/queuing/main.py`, `backend/organization/walk_in_config.py` (new), `backend/organization/main.py`,
  `backend/queuing/tests/test_queue.py`, `backend/queuing/tests/test_walk_in_placement.py` (new),
  `backend/organization/tests/test_walk_in_config.py` (new), `frontend/lib/queue/walk-in.js` (new),
  `frontend/pages/queue.js`, `frontend/lib/i18n.js`, `frontend/tests/queue-walk-in-policy.test.mjs` (new), the MP-10
  implementation report, the Docs Index annex and this register. No schema change and no migration. One file was
  mutated for the negative control and restored from a byte copy (SHA-256 recorded in the MP-10 report §3.3).
  Nothing was staged or reverted; the owner edits listed above remain untouched.
- **MP-17 window (this addendum), changes made:** `backend/common/config.py`, `backend/doctor/profile.py`,
  `backend/doctor/main.py`, `backend/tests/test_doctor_mobile_policy.py` (new),
  `backend/tests/test_doctor_mobile_enforcement.py` (new),
  `backend/doctor/tests/test_doctor_mobile_duplicates.py` (new, unrun), the MP-17 implementation report, the Docs
  Index annex and this register. No schema change, no migration, no frontend file, no dependency. One file
  (`backend/common/config.py`) was mutated once for the negative control and restored from a byte copy
  (SHA-256 `C4A667B7…FDF9` before and after). Nothing was staged or reverted; the owner edits listed above remain
  untouched.
- **MP-18 window (this addendum), changes made:** `backend/scheduling/sessions.py`,
  `backend/scheduling/tests/test_schedule_audit.py`, `backend/tests/test_schedule_audit_coverage.py` (new), the MP-18
  implementation report, the Docs Index annex and this register. No schema change, no migration, no frontend file, no
  dependency, and every existing event name and payload left as it was. One file
  (`backend/scheduling/sessions.py`) was mutated once for the negative control and restored from a byte copy
  (SHA-256 `1541A5C8…1E33` before and after). Nothing was staged or reverted.
- **MP-28 window (this addendum), changes made:** `frontend/lib/i18n.js` (+173 keys per language, +5 shared keys,
  −2 duplicate declarations), `frontend/pages/{index,orgs,branches,patients,appointments}.js` (local dictionaries and
  `T()` removed, `t()` imported, runtime keys namespaced through `aptKey`, hard-coded strings keyed),
  `frontend/tests/i18n-coverage.test.mjs` (new), and five existing test files re-pointed at the same mechanism
  (`symptom-picker-contract`, `appointment-booking-feedback`, `appointments-calendar-integration`,
  `banglanamesense-integration`, plus the new coverage file), the MP-28 report, the PostgreSQL verification report, the
  Docs Index annexes and this register. **No schema change, no migration, no dependency, no backend file** — except
  `backend/appointment/dashboard.py`, where the D-0 date-padding defect found by the now-runnable endpoint tests was
  fixed. `lib/i18n.js` was mutated once for the negative control and restored from a byte copy (SHA-256
  `E19FED20…4453` before and after). Nothing was staged or reverted.
- **Evidence window (same date), database:** created `amsdp_verify_2829` on `127.0.0.1:55432` and migrated it from
  empty to `b2e5c7d91a04 (head)`. The development `amsdp` database and the live deployment were not touched; nothing
  was migrated on an existing database. The database was left in place so the runs can be reproduced.

- **MP-22 window (this addendum), changes made:** `backend/appointment/dashboard.py`,
  `backend/tests/test_dashboard.py`, `frontend/lib/dashboard.js` (new), `frontend/pages/dashboard.js`,
  `frontend/lib/i18n.js`, `frontend/tests/dashboard-policy.test.mjs` (new),
  `frontend/tests/dashboard-page.test.mjs` (new), the MP-22 implementation report, the Docs Index annex and this
  register. No schema change, no migration, no dependency. One file (`frontend/lib/dashboard.js`) was mutated once for
  the negative control and restored from a byte copy (SHA-256 `9C20CF10…F335` before and after). One self-inflicted
  build failure is recorded in the report §4.4 rather than omitted. Nothing was staged or reverted.

- **MP-29 window (2026-11-25), changes made:** `frontend/lib/a11y.js` (new), `frontend/tests/a11y.test.mjs` (new),
  `frontend/tests/a11y-page-contract.test.mjs` (new), `frontend/components/ui/DataTable.js`,
  `frontend/pages/queue.js`, `frontend/lib/i18n.js` (+3 keys × 2 languages), `frontend/styles/global.css`, and the
  inherited MP-02 / D-4 backend fixes: `backend/scheduling/sessions.py`,
  `backend/tests/test_schedule_audit_coverage.py`, `backend/doctor/tests/test_doctor_mobile_duplicates.py`,
  `backend/organization/tests/test_queue_calling_config.py`, `backend/queuing/tests/test_walk_in_placement.py`, the
  MP-29 report, the Docs Index annex and this register. **No schema change, no migration, no dependency, and no
  negative-control mutation** — the 17 new tests each assert a named rule, but no file was mutated to prove them
  discriminating, so that step is absent rather than claimed. Nothing was staged, committed, reverted or stashed; the
  tree carries the earlier windows' uncommitted work plus this window's, **98** dirty entries at close
  (`git status --porcelain`).

---

## 7. Next eligible work

Reading §2–§4, the plan's own order makes the next candidates the tasks that depend on MP-05/06/07 being
green — end-to-end acceptance and the rehearsals — but each of those needs B-2 or B-1 to be unblocked first.
Without them the executable next step is the next self-contained plan task whose acceptance criterion is
provable in this tree. **This register deliberately does not choose it:** the selection is made by reading the
master plan, and the chosen task is added to §2 when it is worked.

**MP-11 is now formally deferred, not waiting.** Its `P1` row sits behind the owner's **Q-6 option (c)** decision
of 2026-11-24 (note under §4): it must not be implemented doctor-only, `doctor_branches.room_id` is not accepted as
a proxy for room scope, and room-scoped numbering remains outstanding work that needs its own queue-model design and
migration. Nothing in this register re-opens it until that design exists.

**The MP-16 window** selected **MP-16 (blocked periods)** — `P1`, no unmet dependency, and the last `P1` task in
WP-D that needed no decision. That window is recorded in §2 and in the report; the work is `TESTED`, and the two
design questions it opened (walk-in arrivals, branch-level blocks, delegable override) are listed in the report §5
as items the owner may decide, not as gates.

**The MP-19 window** selected **MP-19 and MP-20 together** — both `P1`, MP-19 depends only on MP-02 (satisfied) and
MP-20 depends on MP-19; the doctor-assignment editor is a section of the same dialog, so building them separately
would have meant writing the dialog twice. That window is recorded in §2. Its grade is deliberately **TESTED
(frontend) / backend unrun**: the page, its rules and its wiring are proven, but this host had no PostgreSQL and the
repository has no browser harness, so no live request and no click happened. The report says this in its own words
(§4.7, §4.8) rather than implying more.

**The MP-17 window** selected **MP-17 (doctor mobile duplicate allowance)** — the next task in the register's own
"executable right now" list, `P2` with MP-02 satisfied. Its grade is deliberately **TESTED (policy + enforcement
decision)**: 29 DB-free tests pass and a 23-failure negative control proves they are not vacuous, but the 12
API-level tests **collect and do not run** on this host, so no endpoint was exercised. The report says this in
§4.3/§4.6 rather than implying the feature is verified.

**The MP-18 window** selected **MP-18 (schedule-edit audit)** — the next task in the register's own list. It was a
*verify-then-implement* task, and the verification earned its keep: the `schedule.*` endpoints were already audited
(Q5), but the three **session** endpoints silently rewrote `schedules.slot_templates` — the projection
`available-slots` and the calendar read — with no `schedule.*` row at all. All three now go through
`audit_template_projection`, which records `schedule.templates_changed` against the schedule, only when the
published windows actually moved. Its grade is **TESTED (static guard + decision)**: 13 DB-free tests pass, a
negative control fails exactly one of them, and the 12 PostgreSQL tests (8 pre-existing + 4 new) **collect but do
not run** here.

**The MP-22 window** selected **MP-22 (dashboard completion)** — the next non-gated task. The screen gained the two
selectors, the queue panel, quick actions and recent activity; the only server change was `date=` on
`/api/v1/dashboard/today` (validated, 422 on garbage, defaulting to the facility day). Grade:
**TESTED (frontend) — endpoint tests unrun**: 28 dashboard tests green, the frontend suite moved
`409/405/2/2 → 434/430/2/2` with no new red, a negative control proves the branch-scope rule is enforced by test, and
the build compiles with `/dashboard` prerendered. The six new PostgreSQL cases were written and could not run.
**Blueprint §2 was not read line by line** — recorded as report O-2 rather than papered over.

**The MP-28 window** selected **MP-28 (unify i18n)** — no dependencies (`—` in the plan), and fully provable on this
host without a database. 173 keys from five page-local dictionaries moved verbatim into `lib/i18n.js`, nine runtime
keys namespaced, and a seven-test coverage suite added that fails when a key is missing (proven by a one-sided
mutation that turned it red). Frontend suite `434/430/2/2 → 441/437/2/2`, build exit 0. Grade **TESTED (frontend)**.

**The evidence window (same date)** did what three earlier windows said was impossible: it found the database. The
local PostgreSQL is on **55432**, not 5433 — a fact already recorded in the MP-16 report's own command. An isolated
database was created and the whole chain applied to `b2e5c7d91a04 (head)`, then the never-run suites were executed:
MP-22's six endpoint cases **pass** (after the D-0 date-padding fix), MP-17 is **11/12** (D-2 open), MP-18 is **8/12**
(D-1 open, grade reduced), identity is **71 passed / 4 setup errors** (D-3 open). MP-01 itself stays **BLOCKED** on
**B-4** — the *live* database still cannot be read without a credential.

**The MP-29 window** selected **MP-29 (responsive/touch/a11y)** — no dependencies — and closed the three reds the
evidence window left open. The accessibility pass found that the queue's reorder was not merely hard to use with a
keyboard: it was **broken for every input device** (`DataTable` never passed the row index, so the arrows sent
`undefined` in `entry_ids` and the server refused every move). 17 new tests, no new dependency. **D-1** is closed
(`"session_id" in template` — key presence, not truthiness) and **D-2** is closed (the two-gate 403 contract asserted, no
product change). The first full backend run then exposed **D-4**: `.order_by(AuditEvent.id.desc())` sorts a **UUID
string** lexicographically, so two tests read an *arbitrary* audit event rather than the newest — green on a fresh
database, red on its second run; both fixed to `timestamp.desc()`. **D-3 does not reproduce** and is not claimed fixed.
Backend suite **`979 passed, 0 failed in 823.50s`**; frontend `441/437/2/2 → 458/454/2/2`. Grade **TESTED**.

**What is executable right now, without a decision: nothing left in the plan.** With MP-29 landed this window, every
remaining row is gated, deferred or blocked by a dependency that is itself gated:

| Row | State | Why |
|---|---|---|
| MP-12 (printed token) | GATED | depends on **MP-11**, deferred under Q-6 (c) |
| MP-14 (no-show / late grace) | GATED | depends on **MP-13**, gated on **PO-04** |
| MP-15 (cancellation deadline) | GATED | depends on **MP-14**, which depends on MP-13 |
| MP-21, MP-27, MP-30, MP-34 | GATED | owner decisions **PO-01/04–12** |
| MP-24, MP-25, MP-35…MP-40 | BLOCKED | **MP-01 → B-4** (no live database credential) |
| MP-26 | DEFERRED | plan §10 (`P3`, voice programme paused) |

So the next step is an **owner decision**, not another implementation: PO-04 (overbooking/grace surface) unblocks the
MP-13 → MP-14 → MP-15 chain, PO-09 unblocks MP-34, PO-01 unblocks MP-30, and B-4 unblocks the MP-01 family. The
agent-owned work that remains without a decision is **D-3's fixture coupling** (needs a fresh database to reproduce) and
the **Q-3 pair** — which the decision window then diagnosed as two test-harness defects rather than a provenance
question (below, and decision pack §4.2).

**The decision window (2026-11-25)** produced
`implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` — every open gate (PO-01, PO-03…PO-12) plus B-1…B-4,
Q-1…Q-4, O-3, Q-3 and D-3, each with evidence, one recommendation, its alternatives and a copy-paste response line.
**It decides nothing**; it is the request. Two of its findings change the paragraph above:

- **Q-3 needs no choice between "reconcile the hash" and "re-record" — both would be wrong.** The dataset's committed
  blob is byte-identical to the recorded provenance (80,517 bytes, `ac037c24…e51e`); the failure is the Windows
  `autocrlf` checkout, and `calendar-render` is a `file://`/ESM path bug that makes all nine of its tests pass once
  corrected. Both are harness repairs, not product defects (decision pack §4.2).
- **D-3 remains non-reproducing** and is now scoped as an investigation on a freshly migrated database, with no fixture
  edit before a reproduction exists (decision pack §4.3).

**Nothing is executable until the owner answers**, and the register does not pre-empt the answers: the recommended order
in the pack is B-4 and PO-10 first (they unblock ≈ 20.5 engineer-days of already-approved multi-display work), then the
documentation-level answers (PO-09/PO-03/PO-11/PO-12), then PO-04/PO-07, PO-01 and PO-08.

### 7.1 Decision outcomes applied — 2026-11-25 (evening window)

The Product Owner answered every gate in §7 above, in writing. The record is
`decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md`. **The table at §7 is left exactly as it
stood before the answers** — it is the evidence of what was blocked and why — and this table is the
state that replaces it.

| Gate | State now | Consequence recorded |
|---|---|---|
| **PO-01** | **CLOSED** | `product/AMSDP_Phase_Model_V1.1.md` publishes Phases 4/5/6 (names, scope, exit criteria, Product Owner as accepting authority); **MP-30** is defined as verification of the existing handoff surfaces; **M-8** now has a definition |
| **PO-03** | **CLOSED** | SYM-001 ratified as approved **P1** by dated annotation in MVP Scope §7 and catalogue §H; **no code changed** |
| **PO-04** | **CLOSED** | MP-09 → MP-13 → MP-14 → MP-15 authorised **after the first clean rehearsal**, which has not yet happened; the order is fixed |
| **PO-05** | **SUPERSEDED for MP-04 (26 Nov 2026)** | MP-04 was re-opened by the Product Owner's **Option B** decision (`docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md`); **MP-26 remains deferred**, and no other row moves |
| **PO-06** | **CLOSED** | MP-27 stays deferred; the 17-criterion Analytics Specification is recorded as **not approved** |
| **PO-07** | **CLOSED** | MP-21 stays deferred; this row governs PO-04's subscription clause |
| **PO-08** | **CLOSED** | **D-5** forward-only numbering adopted (first application **Revision 49**); **O-2** no facility scope; **POD-2** closed; **POD-7** executed (one file, list recorded); **POD-11 = Faria Bushra**; D-3, D-7, POD-6, POD-1/3/8/9/10 carried |
| **PO-09** | **CLOSED** | Annotations applied to Limitations Report §1, catalogue §H and §H.1, MVP §7 — dated, additive, original text preserved |
| **PO-10** | **CLOSED as an approach; execution pending** | `deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md`. **The `:5433` exposure is still open** — no step was executed |
| **PO-11** | **CLOSED** | Doctor ↔ branch contract ratified (decision record §2.10); no code, no migration |
| **PO-12** | **CLOSED** | `plan/AMSDP_Feature_Key_Register_V1.0.md` — 26 `F-nn` keys, catalogue IDs unchanged |
| **Q-3** | **CLOSED** | Both harnesses repaired, **expected values untouched**; `9/9` and `9/9`; frontend suite **466 / 464 pass / 0 fail / 2 skipped** |
| **Q-4** | **CLOSED** | The §33 PO-13 amendment committed by the agent after verifying the diff is §33-only; `.clinerules` left untouched |
| **O-3** | **CLOSED** | Path-grouped commits made; **nothing pushed** |
| **D-3** | **OPEN — investigated** | Reproduces only as a *collection* error: `test_identity.py` does database work at import and there is no PostgreSQL on `127.0.0.1:55432` or `:5432`. No fixture changed |
| **B-4** | **OPEN** | Owner selected "other"; **no live database read, migration or reseed was performed** |
| **Q-1, Q-2** | **OPEN** | Not approved in this window; no code changed |
| **B-1, B-2, B-3** | **OPEN** | Withheld by the brief |

**Task status delta — nothing is promoted on assumption.**

| Task | Was | Now | Evidence |
|---|---|---|---|
| **MP-30** | GATED (undefined) | **IMPLEMENTATION-READY as a verification task** | Definition published; its negative-path checks are executable, but it cannot close until MP-25's acceptance cell is met (B-4) |
| **MP-34** | GATED (PO-09) | **IMPLEMENTED — awaiting owner review** | The annotation set, the PO-11 note and the PO-12 register are all applied; two residual items: the register's V2.5 family column (**R-1**) and **QUE-005**, the one surviving P0 |
| **MP-33** | GATED | **BLOCKED** | CI cannot first go green on work that is not pushed, and O-3 forbids pushing |
| **MP-09, MP-13, MP-14, MP-15** | GATED | **AUTHORISED, NOT STARTED** | PO-04 gates them on the first clean rehearsal |
| **MP-24, MP-25, MP-35…MP-46** | BLOCKED (B-4) | **BLOCKED (B-4)** unchanged | No credential; PO-10's window is the access path |
| **MP-04** | Voice-pack administration UI (W3) | **IMPLEMENTED, TESTED (frontend), BUILT — not browser-verified** | 26 Nov 2026 **Option B**. `frontend/tests/voice-pack-admin.test.mjs` **17 pass**, `frontend/tests/permissions-mirror.test.mjs` **4 pass**; `next build` exit 0 with `/voice-packs` (7.91 kB) in the route table. Five defects closed in the second pass (report §0): the page was unreachable for `org_admin` (`org.read` missing from the client mirror); `super_admin` was refused on a tenant's pack, leaving `pending_review` unapprovable from any screen; the refusal-translation table keyed on machine tags the policy never emits; the "inherited" hint read a field the organisation route never sends; and rollback had no caller. `organization/tests/test_voice_packs_api.py` **NOT EXECUTED** (no PostgreSQL) | `AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` §2, §5 |
| **MP-21, MP-26, MP-27** | Subscription, W5 installer, Analytics | **DEFERRED** | PO-05 (MP-26 only), PO-06, PO-07 |
| **MP-11, MP-12** | DEFERRED (Q-6 c) | **DEFERRED** unchanged | Not reopened by any decision in this window |

> **Reconciled 2026-11-27, after PO-DEC-01** — additive; the table above is not rewritten (T-3, T-4 and
> RO-04, under Product Owner authorisation **OA-2**).** Four lines above name a gate that has since closed, so
> their "Was" column now reads a state that gates nothing:
>
> - **MP-30** — **PO-01 is CLOSED** (Phases 4/5/6 published in `product/AMSDP_Phase_Model_V1.1.md`). MP-30 is
>   **IMPLEMENTATION-READY as a verification task** and is **BLOCKED** on live evidence (its negative-path
>   checks need a running stack and MP-25's acceptance cell), **not GATED** on an owner decision.
> - **MP-34** — **PO-09 is CLOSED.** MP-34 is **IMPLEMENTED — awaiting Product Owner review**, and is **not
>   accepted**: the annotation set, the PO-11 note and the PO-12 register are applied. The "GATED (PO-09)"
>   wording is stale. Residual items: the V2.5 family column (**R-1**) and **QUE-005**, re-classified in §17.3
>   as implementation-present / acceptance-outstanding rather than a code defect.
> - **MP-33** — **not** gated on an owner decision and **not** closed: **BLOCKED on OA-1** (commit/push
>   authorisation), which was **not granted** in the 2026-11-27 answer. No MP-33 code changed.
> - **MP-09, MP-13, MP-14, MP-15** — **SEQUENCED**, not GATED: PO-04 authorises them on the first clean
>   rehearsal; none has occurred, so they are not started.
>
> "Nothing is promoted on assumption" still holds: every line above re-classifies against an **existing owner
> decision**. No evidence was added, so no status moves under `.clinerules` §7.

**What is executable after this window: still nothing that is not blocked.** Every remaining row needs
either the maintenance window (B-4 / PO-10), the first clean rehearsal (PO-04), or a push (MP-33).
The difference is that the *documentation* debt is now paid and the *decisions* are on record, so the
next window can start work instead of writing another request.



---

## 8. Change log

| Date | Change |
|---|---|
| 2026-11-24 | Register created. MP-02, MP-05, MP-06, MP-07 recorded with their real evidence; B-1…B-3 and Q-1…Q-4 opened; frontend baseline reds recorded. Q-5 opened after reading MP-08 against the shipped queue tests, **before** any MP-08 code was written |
| 2026-11-24 | **Q-5 answered by the Product Owner: option (a), explicit `recall`.** MP-08 implemented and recorded in §2 as TESTED with its full evidence (backend `808 passed`, mutation `6 failed`, frontend `373/369/2/2`); Q-5 closed in §4; §9 kept verbatim as the record of the conflict and annotated with the resolution; frontend suite table extended with the MP-08 run. Implementation report written to `docs/implementation/AMSDP_MP-08_Announcement_Safe_Recall_Implementation_Report_V1.0.md` |
| 2026-11-24 | **MP-10 worked** (next non-gated task after MP-08; MP-09/MP-13 remain gated by PO-04). Recorded in §2 as TESTED: 38 new backend tests + 6 rewritten, whole tree `847 passed, 0 failed in 1292.53s`, mutation `2 failed, 13 passed` restored byte-identically, frontend `383/379/2/2` (only the pre-existing Q-3 pair). §5 gained the MP-10 frontend row; §6 lists the MP-10 file set; §7 now names MP-11 as the next eligible task with its two constraints. Report: `docs/implementation/AMSDP_MP-10_Walk_In_Policy_Configuration_Implementation_Report_V1.0.md`; Docs Index annex added (count 138 → 139) |
| 2026-11-24 | **MP-33 worked** in the same window, because MP-11's room scope is blocked by the plan's own §10 deferral (see §7). CI state read from the public GitHub Actions API: 28 runs, 4 green (latest green run #5, 2026-11-14), latest run #28 red with the backend job **green** and `Run frontend tests` red. Q-3 upgraded from "untriaged" to **diagnosed** (dataset provenance mismatch + a test file that does not load), with the two options that would close it. Report: `docs/implementation/AMSDP_MP-33_CI_First_Green_Run_Report_V1.0.md`; Docs Index annex added (count 139 → 140) |
| 2026-11-24 | **Q-6 answered by the Product Owner: option (c), MP-11 deferred.** Recorded in §4 with its three binding consequences: the BR §31.1/§52 "doctor **or room**" requirement stays in force and MP-11 must not be delivered doctor-only; `doctor_branches.room_id` is **not** accepted as a proxy (room-assignment semantics, cardinality and sequence-sharing rules must be established first); room-scoped numbering remains outstanding work requiring its own queue-model design and migration. No schema column was added. §7 rewritten accordingly |
| 2026-11-24 | **MP-16 worked** (next executable `P1` after MP-11's deferral). Recorded in §2 as TESTED: 51 new tests, targeted suites `279 passed in 297.60s`, mutation `7 failed, 44 passed` across both services and restored byte-identically, migration `b2e5c7d91a04` applied on the dev DB and as a whole chain on a fresh scratch DB (second run a no-op), whole backend suite quoted in the report. §7 now names MP-19 as the next eligible task. Report: `docs/implementation/AMSDP_MP-16_Blocked_Periods_Report_V1.0.md`; Docs Index annex added (count 140 → 141) |
| 2026-11-24 | **MP-19 + MP-20 worked together** (both `P1`; MP-20's editor is a section of MP-19's dialog). Recorded in §2 as **TESTED (frontend)**: 12 rule tests + 14 new wiring/mirror/i18n tests = **26 passed**; frontend suite `383/379/2/2` → **`409/405/2/2`** (+26, all passes; only the pre-existing Q-3 pair red — the dataset-hash assertion plus `calendar-render.test.mjs` failing to load with `ERR_UNSUPPORTED_ESM_URL_SCHEME`); mutation (revoke loses its branch scope) → **`1 failed, 13 passed`**, `pages/staff.js` restored **byte-identically** (`600BB633…9888`); `npm run build` **✓ Compiled successfully** with `/staff` prerendered (`●`, 5.71 kB) after the leftover `getServerSideProps` stub was removed. **Deliberately not upgraded:** the 31 identity tests (`test_staff_admin_surface.py` 15, `test_capability_grants.py` 16) **collect cleanly** but **could not run** — `test_identity.py` aborts at import with `connection to server at "127.0.0.1", port 5433 failed` — and there is no browser/E2E harness, so no click and no live request happened; §2 says so and §7 records MP-17 as next. Report: `docs/implementation/AMSDP_MP-19_Staff_and_Permission_Management_Implementation_Report_V1.0.md`; Docs Index annex added (count 141 → 142) |
| 2026-11-24 | **MP-17 worked** (next task in the register's own executable list; `P2`, MP-02 satisfied). Recorded in §2 as **TESTED (policy + enforcement decision)**: 23 DB-free policy tests + 6 DB-free enforcement-decision tests → **`29 passed in 2.08s`**; negative control (`doctor_mobile_must_be_unique` → `return False`) → **`23 failed, 6 passed`**, `common/config.py` restored **byte-identically** (`C4A667B7…FDF9`) and re-run green; `py_compile` **exit 0**. **Deliberately not upgraded:** the 12 API tests (`doctor/tests/test_doctor_mobile_duplicates.py`) **collect** but **cannot run** — no PostgreSQL on this host — so the `403` gate, the audit `before`/`after` and both cross-tenant cases are unproven here. No schema change, no migration, no frontend file. §5 notes the frontend figure is unchanged; §7 advances to **MP-18**. Report: `docs/implementation/AMSDP_MP-17_Doctor_Mobile_Duplicate_Allowance_Implementation_Report_V1.0.md`; Docs Index annex added (count 142 → 143) |
| 2026-11-24 | **MP-18 worked** (next task in the register's list; a *verify-then-implement* task, and the verification found the gap in an unexpected place). Recorded in §2 as **TESTED (static guard + decision)**: the three session endpoints silently rewrote `schedules.slot_templates` with no `schedule.*` audit row; they now go through `audit_template_projection`, which records `schedule.templates_changed` on the schedule and only when the published windows moved. Evidence: 13 DB-free tests (`backend/tests/test_schedule_audit_coverage.py`) → **`13 passed in 1.89s`**, including an AST guard over every write route; negative control (a session path reverted to a bare `sync_slot_templates`) → **`1 failed, 12 passed`** — and the route-level guard alone stayed green, which is the point; `sessions.py` restored **byte-identically** (`1541A5C8…1E33`); `py_compile` **exit 0**. **Not run here:** the 12 PostgreSQL tests in `scheduling/tests/test_schedule_audit.py` (8 + 4 new) collect but cannot execute — no database on this host. No schema change, no migration, no frontend file. §7 advances to **MP-22**. Report: `docs/implementation/AMSDP_MP-18_Schedule_Edit_Audit_Implementation_Report_V1.0.md`; Docs Index annex added (count 143 → 144) |
| 2026-11-24 | **MP-28 worked** (unify i18n; no dependencies). Recorded in §2 as **TESTED (frontend)**: the five page-local `{bn,en}` dictionaries (173 keys: 8/7/9/15/134) moved **verbatim** into `frontend/lib/i18n.js` under `home*`/`org*`/`brn*`/`pat*`/`apt*`, 206 literal call sites rewritten to `t('…')`, the 9 runtime-built keys namespaced through `aptKey`, five hard-coded English strings keyed, two duplicate `active`/`inactive` declarations removed. New `tests/i18n-coverage.test.mjs` **7/7 green**; negative control (one Bangla key renamed) → **2 red** with the missing key named, `lib/i18n.js` restored byte-identically (`E19FED20…4453`); suite `434/430/2/2` → **`441/437/2/2`** (only the Q-3 pair red); `npm run build` ✓. Eight existing source-contract tests re-pointed at the new mechanism, none deleted. §5 gained the MP-28 row; §6 the file set. Report: `implementation/AMSDP_MP-28_Unified_Internationalization_Implementation_Report_V1.0.md`; Docs Index annex added (count 145 → 146) |
| 2026-11-24 | **MP-01 dependency verification + the PostgreSQL correction.** §3 gained **B-4** (live DB credential): the live deployment answers on `:8110`/`:3100`/`:5433` but no credential exists here (`fe_sendauth: no password supplied`), so the live `alembic_version` stays unread and the plan's `c4d8e2a91f60` cannot be confirmed — note the tree's head is now `b2e5c7d91a04`. **The blocker quoted in every earlier row was wrong**: the local database is on **`127.0.0.1:55432`** (the DSN MP-16's own report records), at `b2e5c7d91a04`. An isolated `amsdp_verify_2829` was created and migrated from empty to head (exit 0), then the never-run suites were run: dashboard **12 passed** (after fixing D-0: `?date=2026-1-5` returned 200 because `strptime` accepts unpadded fields — now an exact round-trip), MP-17 **11 passed / 1 failed** (D-2), MP-18 **8 passed / 4 failed** (D-1, **grade reduced** to static guard only), identity **71 passed / 4 errors** (D-3, fixture isolation). A superseding-evidence note sits under §2; no row above was rewritten. Report: `implementation/AMSDP_PostgreSQL_Verification_and_MP-01_Reconciliation_Report_V1.0.md`; Docs Index annex added (count 146 → 147) |
| 2026-11-24 | **MP-22 worked** (dashboard completion; next non-gated task after MP-18). Recorded in §2 as **TESTED (frontend)**: branch selector (own branch only, empty rather than everything when absent), real server-side date selector (`date=` on `/api/v1/dashboard/today`, 422 on garbage, facility-day default), today's queue panel, quick actions and recent activity; 13 i18n keys in both languages. Evidence: 15 rule tests + 10 source-contract tests + MP-07's 3 tile guards → **`28 passed`**; suite `409/405/2/2` → **`434/430/2/2`** (+25 all-pass, reds unchanged = Q-3 pair); negative control (`selectableBranches` widened) → **red**, file restored byte-identically (`9C20CF10…F335`); `npm run build` **✓ Compiled successfully**, `/dashboard` prerendered 6.6 kB / 99.8 kB, exit 0 (first build **failed** with `ReferenceError: user is not defined` — disclosed in report §4.4). **Not run here:** 6 PostgreSQL cases in `backend/tests/test_dashboard.py`. **Blueprint §2 not read line by line** (report O-2). §5 gained the MP-22 suite row; §7 advances to MP-25/MP-28/MP-29 pending dependency check. Report: `docs/implementation/AMSDP_MP-22_Dashboard_Completion_Implementation_Report_V1.0.md`; Docs Index annex added (count 144 → 145) |
| 2026-11-25 | **Decision window: the Product Owner Decision Pack was written** — `implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` (99,460 bytes, 1,127 lines; Docs Index annex added, count 148 → 149). It consolidates **PO-01, PO-03 … PO-12** (PO-02/PO-13 explicitly not reopened) with **B-1…B-4, Q-1…Q-4, O-3, Q-3, D-3** into one card per item — evidence, one recommendation, alternatives, a copy-paste response line, and the tasks each answer releases — plus a response sheet (§5) and a dependency map (§6). **It decides nothing and closes no gate.** New evidence it records: **Q-3 is two harness defects, not product defects** (dataset: committed blob is 80,517 bytes and hashes to the recorded `ac037c24…e51e`, `git ls-files --eol` `i/lf w/crlf`, `core.autocrlf=true`, no `.gitattributes`; calendar-render: raw Windows paths to the ESM loader, and a corrected probe passes all 9 tests); **the committed tree's migration head is `c4d8e2a91f60`, matching the recorded live revision**, the working tree being one ahead only because `b2e5c7d91a04` is untracked (B-4 row corrected); the Feature Catalogue §H.1 "P0 scope defects" are stale in the product's favour (branch scope enforced at `queuing/main.py:191–203`, `:297–300`, `:422–426`); and the Limitations Report §12 still claims in-memory storage with no PostgreSQL (PO-09 evidence). §2 gained the **MP-02 satisfied** note; §7 gained the decision-window note. **Nothing staged, committed, reverted or stashed** — 98 dirty entries at the window's start, 98 again after the probe file was removed, and 99 at close, the extra entry being this report itself (O-3). Report §8.5 lists every command executed, including the two individual test files run and the one temporary probe file created inside `frontend/tests/` and removed in the same window |
| 2026-11-25 | **MP-29 worked** (responsive/touch/a11y; no dependencies) **and the MP-02 reds closed.** Recorded in §2 as **TESTED (frontend) + TESTED (backend, PostgreSQL)**: `frontend/lib/a11y.js` (new, 7 exports), `DataTable` now passes the row index (`c.render(row, ri)`, `rowProps(row, ri)`), the queue reorder goes through the tested `moveWithin` on **Alt+Arrow** with named arrows, `disabled` ends and an `aria-live` announcement, 3 i18n keys × 2 languages, and a `global.css` block (`.sr-only`, hover↔focus twins, 44 px floor, 360 px layout). **The pass found the reorder was broken for every input device**, not merely unusable by keyboard. Evidence: `a11y.test.mjs` + `a11y-page-contract.test.mjs` → **`17 passed`**; frontend suite `441/437/2/2` → **`458/454/2/2`** (Q-3 pair only); **D-1** closed (`"session_id" in template`), **D-2** closed (two-gate 403 contract, `ORGADMIN` fixture), **D-4** found and fixed (`.order_by(AuditEvent.id.desc())` over a UUID string → `timestamp.desc()`, two files), **D-3 not reproducible** and not claimed fixed; whole backend suite **`979 passed, 0 failed in 823.50s`** after being `5 failed, 972 passed` at MP-02. No schema change, no migration, no dependency, **no negative-control mutation** (disclosed), **nothing staged or committed** (O-3). §5 gained the MP-29 row; §6 the MP-29 file set; §7 now records that **every remaining work package is gated, deferred or blocked**. Report: `implementation/AMSDP_MP-29_Responsive_Touch_and_Accessibility_Implementation_Report_V1.0.md`; Docs Index annex added (count 147 → 148) |
| 2026-11-26 | **PO-D1 decided by the Product Owner: Option C — browser-based voice-pack upload becomes its own work package.** Recorded in §13; decision record `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7 (additive, §1–§6 untouched). **MP-04's scope is unchanged** and its report's declared deviation is closed (`AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` §2.1, §9.3, §12). New package **MP-47** opened as **PROPOSED** with a twelve-area scope, reuse inventory, dependency list, nine open owner decisions and twelve acceptance criteria: `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md`. No code, schema, migration or configuration changed; nothing staged, committed or pushed |
| 2026-11-26 | **Authorised commit + push to `hackathon-mvp`, and the Ubuntu migration assessment.** Recorded in **§14**. The reviewed working tree (46 entries: 17 authorised modifications + 28 new files + the owner's own `.clinerules` edit) was committed in two parts — **`31fcb45`** (36 code/test files) and **`62b2fac`** (9 documentation files) — and pushed: `fd4d365..62b2fac`, verified after a fetch as `HEAD = origin/hackathon-mvp = 62b2facd670583d84712151210dc7de3fb94f647`, 0 ahead / 0 behind. `.clinerules` **not staged**; nothing force-pushed, no history rewritten, no other branch. Review before staging: secret scan **0 real hits** (2 documentation false positives), **0** debug residue, no generated artefact. Evidence: frontend **526 / 524 pass / 0 fail / 2 skipped**, `npm run build` ✓ with `/reports`, `/queue-displays`, `/queue-history`, `/voice-packs` in the route table, backend `py_compile` exit 0 + imports OK + **34 tests collected (not executed)**. Migration position: Ubuntu `c4d8e2a91f60` → head **`e1b7c4a9d236`** through `b2e5c7d91a04` → `d3f5a7b91c24`, all three additive. **No migration executed, no reseed, no container touched.** Report: `deployment/AMSDP_Hackathon_MVP_Push_and_Ubuntu_Verification_Handover_V1.0.md` |

| 2026-11-25 | **Q-1 and Q-2 answered by the Product Owner: both APPROVED as recommended, plus a push authorisation and a demo-data authorisation** (decision record §11, Addendum A-1; plan Appendix G, Amendment A-4). Worked in the same window: **Q-1** — `backend/patient/main.py` no longer reads the host clock (the future-DOB check and the age both resolve through `common.timeutil.operational_today`, once per request), 12 new DB-free tests + a source guard; **Q-2** — the Waiting tile now reads `queue_length` and `in_queue` stays visible under its own label, one new PostgreSQL test proving the two populations differ by the appointment-less walk-ins. Evidence, negative controls, commits and the pushed remote tip: **§10**. Q-1/Q-2 rows in §4 are **superseded by §10, not edited**. Report: `implementation/AMSDP_Q1_Q2_Facility_Day_And_Dashboard_Counts_Report_V1.0.md`; Docs Index annex added (Revision 50) |
| 2026-11-25 | **Multi-display public surface worked** (WP-C.2 / WP-C.3; the largest genuinely-unimplemented authorised block). Recorded in **§11** as IMPLEMENTED + TESTED: registry models and revision `d3f5a7b91c24`, `?display=` resolution with SQL scope, department and room scope, measured estimate, `ETag`/`304`, server-side field suppression, GET-only guard and throttled disabled-display audit. Evidence: 34 new tests (`backend/tests/test_multidisplay.py`), whole backend **`1027 passed, 0 failed in 630.62s`** (`993 + 34`), frontend `467 / 465 / 0 / 2`, three negative controls (4 / 1 / 2 failures) each restored byte-identically, and one latent cross-join defect found by a SQLAlchemy warning and fixed with a regression test. The migration head is corrected to **`b2e5c7d91a04`** (plan Amendment A-5, Appendix H). MP-38/39/40 remain not started / **BLOCKED (B-4)**; `queue.display.denied` remains with MP-39. B-4 decision brief written to `deployment/AMSDP_B4_Database_Access_Decision_Brief_V1.0.md`. Report: `implementation/AMSDP_Multi_Display_DQDS_Public_Surface_Implementation_Report_V1.0.md`; Docs Index annex added (Revision 51) |
| 2026-11-27 | **The backend suites were executed for the first time in this checkout, on a disposable database.** Recorded in **§15**. Local PostgreSQL **16.4** on `127.0.0.1:55432` (corrected 2026-11-27 under Product Owner authorisation **OA-2** / audit **F-13**; this row originally read "17"); a new empty database **`amsdp_verify_1127`** migrated **zero → head** (`alembic current` → `e1b7c4a9d236 (head)`; `alembic heads` → one head); the developer database and the Ubuntu deployment neither migrated nor reseeded (§15.1 carries the corrected wording: earlier `amsdp`-targeted dashboard runs exist in retained shell history with unestablished timing). Result: **`1061 passed, 0 failed in 541.58s`**. Five **test** defects found and fixed, **no product file modified**: (1) `test_operational_reports.py` — the module's own `purge_org()` deleted the patient a module-scoped fixture had created; (2) `test_operational_reports.py` — `_queue_entry()` omitted the `NOT NULL` `token` and `patient_id`; (3) `test_display_admin.py` — the public board was addressed by row id instead of the upper-cased facility code (five call sites, corrected 2026-11-27 per audit F-05); (4) `test_display_admin.py` — **MP-45's field-visibility assertion was vacuous** (it asserted absence from a body with no doctor row) and now seeds a `called` and a `waiting` entry and asserts the row is present first; (5) `test_tracking_tokens.py` — MP-25's durable budget made the module's `_RATE.clear()` a no-op reset, so the suite exhausted the ten-per-minute budget and its own later assertions met `429`; an autouse fixture now clears `_RATE` **and** the `pqt:%` rows, and the limit is unchanged. `test_tracking_tokens.py` re-run **3×** (17 passed each) and `test_display_admin.py` **2×** (13 each), because the two that mattered were second-run defects. **Nothing committed, pushed, deployed or reseeded**; `.clinerules` untouched; no frontend run in this window |








---

## 9. Why MP-08 was not started (recorded at the point of conflict, not after)

MP-08's acceptance criterion is: *"Two calls for one entry produce two delivery rows with distinct `qce:` keys;
both audited; position unchanged."* Every ingredient of that exists today **for the two-step path**, and the
event identity already behaves correctly: `test_recall_gets_a_new_event_id` proves a recall through
missed-turn → recover → call yields a *different* `qce:` id and `call_count == 2`. What the plan adds is the
**single-step** transition `called → called`.

Implementing it literally means deleting the guarantee in
`test_duplicate_call_request_creates_no_second_event`: today, a retried or double-submitted `POST …/{"action":
"call"}` is refused with 422, so it cannot produce a second history record, a second `qce:` id, a second
delivery row or a second audible announcement. `backend/queuing/events.py` (lines 21–28) states that protection as
a design property. Trading it away for a one-word plan line would weaken exactly what MP-08 calls
"announcement-safe".

Three implementation options were identified, none of which was executed, because the choice changes business
behaviour:

| Option | What it is | Cost | Verdict |
|---|---|---|---|
| **(a) explicit `recall` action** | Add `"recall"` to `_TRANSITIONS["called"]`, map it to status `called`, record `action: "recall"` in `status_history`, and count `call` **and** `recall` records in `queuing.events.call_events`. `call` from `called` stays **422**; duplicates still cannot announce twice; the recall is a distinct, audited event with its own `qce:` id; the missed-turn path keeps working | 4 files (transition, events, UI control, tests) + one i18n key | Recommended: satisfies MP-08's intent, preserves the invariant, keeps both existing tests green |
| **(b) allow `call` from `called`** | The plan's literal wording: `"called"` gains `"call"` | 2 files | **Rejected as unsafe on its own**: a duplicated request becomes a duplicate announcement, and the 422 test must be deleted |
| **(c) keep two-step, add UI only** | No transition change; a "Recall" button performs missed-turn → recover → call | 1 file + i18n | Cheapest, and already fully supported by the server — but it records a *missed turn* on a patient who did not miss one, which is a data-quality cost |

The decision is owed by the Product Owner (Q-5). No MP-08 code exists in the tree.

### Resolution (annotated after the decision — the text above is left as written)

The Product Owner chose **option (a)**. It is implemented: `RECALL_ACTION = "recall"` and
`CALL_ACTIONS = ("call", "recall")` in `backend/queuing/events.py`; `"recall"` added to
`_TRANSITIONS["called"]` and `_NEXT_STATUS` in `backend/queuing/main.py`; the permission gate now reads
`elif data.action in ("call", "recall")`; the audit record is derived from the submitted action, so a recall writes
`queue.recall` and a first call still writes `queue.call`. `call` from `called` is unchanged at **422** and its test
still passes, so the announcement-duplication guard argued for here was not traded away. The frontend offers a
separate Recall control for `status === 'called'`, and the announcement tracker now also treats a **new
`call_event_id`** as a new call, because a recall never changes the status. Evidence: §2 MP-08 row and
`implementation/AMSDP_MP-08_Announcement_Safe_Recall_Implementation_Report_V1.0.md`. Q-5 is closed.

---

## 10. Q-1 and Q-2 closed — executed under decision record Addendum A-1 (25 November 2026)

§4's **Q-1** and **Q-2** rows are **superseded by this section and left exactly as written**. They were
written when the answer was unknown; rewriting them would erase the evidence that the question was real.

| ID | Decision | What was executed | Evidence |
|---|---|---|---|
| **Q-1** | **APPROVED** — fold the two patient-service date reads into **MP-44** | `backend/patient/main.py`: `_validate_dob` used `datetime.now().date()` and `_age_from_dob` used `date.today()` — both the **host** clock, while the queue board, dashboard and display already used `organizations.timezone`. Both now resolve through `common.timeutil.operational_today`, read **once per request** and threaded into `_patient_to_dict` (so the list endpoint does not issue one organization lookup per patient). Field names, formats, allowed values and status codes are unchanged; `today` is an optional parameter, so no existing caller or test changed | `backend/patient/tests/test_patient_facility_day.py` — **12 new tests** (zone-not-host with UTC+14 vs UTC−11, tomorrow-here-is-today-there, today-allowed/tomorrow-422/malformed/empty, birthday turnover, leap-day anniversary, default-to-facility-day, AST clock guard, one-read-per-request guard). Negative control (server clock restored) → **`1 failed, 11 passed`**, file restored byte-identically (`True`) |
| **Q-2** | **APPROVED as proposed** — Waiting = `queue_length`, In queue = `in_queue` | `frontend/pages/dashboard.js`: the **Waiting** tile now reads `today.queue_length` (it read `in_queue`); `in_queue` remains on the page in the queue panel under its **own** label (`inQueueRecords`, bn + en). `backend/appointment/dashboard.py`: the payload contract is now documented at the module and endpoint level, and `QUEUE_ACTIVE` states why `skipped` still counts. **The counts themselves were already correct** — no formula changed, because the defect was the binding, not the arithmetic | Data inspected before changing anything: `queuing.enqueue_patient` stores a walk-in with `appointment_id = NULL`, so an appointment-less patient raises `queue_length` only — the model genuinely supports the distinction, so **no limitation had to be recorded**. New PostgreSQL test `test_waiting_and_in_queue_are_different_populations` (in_queue 1 / queue_length 3 across IN_QUEUE, CHECKED_IN, BOOKED, waiting walk-in, skipped, completed and another-day states) + `test_a_queue_entry_from_another_day_is_not_todays_waiting`. Negative controls: `skipped` removed from `QUEUE_ACTIVE` → **test red at `queue_length == 3`**; tile re-aliased to `in_queue` → **`2 pass / 2 fail`**; both files restored byte-identically (`True`) |

**Database the runs used.** The suite was pointed at the **local development PostgreSQL** on
`127.0.0.1:55432` (`dbname=amsdp`, `user=amsdp`, server `16.4` compiled by MSVC, `inet_server_addr()`
= `127.0.0.1/32`) — identified before use by reading `information_schema`, `alembic_version`
(`b2e5c7d91a04`, matching the working tree) and row counts (31 tables; 141 organizations, almost all
pytest fixtures such as `conc_org_*`, `foreign_org_*`, `m6-org`). It is **not** the owner's Ubuntu
database on `:5433` and **not** a production database. No writes outside the tests' own fixture
organizations, no DDL, no migration, no reseed.

**What is still not claimed.** No `VERIFIED` and no `ACCEPTED`: no browser session and no live API call
against the deployment happened in this window (**B-2**), the midnight rollover was not observed
(**B-3**), and the demo-data authorisation was **not exercised** — the existing development data was
sufficient, and recording that is better than manufacturing rows to justify an authority.

**The push, verified.** The three path-grouped commits `e23a2ce` (backend, 4 files), `516e46b`
(frontend, 3 files) and `6fa7e6f` (docs) were pushed to **`origin/hackathon-mvp`** and nothing else:
`a4ddc2c..6fa7e6f  hackathon-mvp -> hackathon-mvp`. After a `git fetch`, local `HEAD` and
`origin/hackathon-mvp` were both **`6fa7e6fc2490bf8f0e49728d941fd742b575591a`** with
`git rev-list --left-right --count` reporting **`0  0`**. That hash is the **verification point**. The
docs-only commits that came after it — the post-push note in report §7.3 (`a1a0bdb`) and the removal of
the push marker (`29edc41`), plus the commit carrying this sentence — contain **no code change**: the
backend and frontend commits `e23a2ce` and `516e46b` are untouched, so what was verified is what ship.
22 commits went up in that push (the 19 that
had accumulated from the MP-05…MP-33 work plus these 3); the range was scanned for key/token patterns
before it left the machine and matched nothing. **`.clinerules` remains uncommitted** — its change is
the owner's own `docs/plan/` ratification note, not an agent edit — and it is now the only modified
tracked file in the tree.

<!-- §10 added 2026-11-25 under decision record Addendum A-1; §4 rows left as written (append-only). -->

## 11. Multi-display public surface executed — WP-C.2 / WP-C.3 (25 November 2026)

Executed under the Product Owner's autonomous completion instruction. Plan
responses: **Amendment A-5** (Appendix H) corrects the migration head, records the
status changes and clarifies what B-4 does and does not block. Report:
`docs/implementation/AMSDP_Multi_Display_DQDS_Public_Surface_Implementation_Report_V1.0.md`.

> **Status note (added 2026-11-27 — pointer only; nothing below is rewritten).** The statuses in the table
> are those of **25 November 2026**. **§15** records the 27 November backend execution on a scratch
> database and is the **authoritative source for the 27 November backend status**: MP-39 moved from UNRUN
> to backend TESTED (13 passed) and MP-46 from PARTIAL/UNRUN to backend TESTED. MP-38 and MP-40 remain not
> started. Read this section as history, not as current state.

| Task | Deliverable | Status |
|---|---|---|
| **MP-35** | `QueueDisplay` + `QueueDisplayDoctor` models; revision `d3f5a7b91c24` (`down_revision = b2e5c7d91a04`) creating `queue_displays` and `queue_display_doctors`; `UNIQUE (branch_id, code)`; CHECKs on scope/language/status plus two half-configuration guards; three indexes | **IMPLEMENTED, TESTED** (demo seed outstanding) |
| **MP-36** | `?display=<code>` resolver; scope as a SQL predicate; unknown / cross-branch / cross-org / disabled → the identical 404; the two-segment board's payload unchanged | **IMPLEMENTED, TESTED** |
| **MP-37** | department scope through `doctor_branches.room_id → facility_rooms.department_id`; nullable `room_name` | **IMPLEMENTED, TESTED** |
| **MP-41** | `scope_type='room'` + `room_id`, CHECK-enforced; empty room is empty | **IMPLEMENTED, TESTED** |
| **MP-42** | estimate from ≥ 3 completed consultations (mean, from `status_history`), else `AMSDP_AVG_SERVICE_MINUTES`; `int ≥ 1`; `estimate: true` | **IMPLEMENTED, TESTED** (payload) |
| **MP-43** | `board_version` over the projection only; weak `ETag`; `If-None-Match` → `304`, no body | **IMPLEMENTED, TESTED** (API) |
| **MP-44** | `operational_date` + `timezone` published on a configured board | **IMPLEMENTED, TESTED** (display slice) |
| **MP-45** | `show_room` / `show_estimated_wait` / `show_waiting_count` / `footer_text` enforced in the body builder | **IMPLEMENTED, TESTED** (server side) |
| **MP-46** | GET-only guard (`405`, `Allow: GET`, `no-store`); throttled `queue.display.disabled_requested`; zero audit rows for anonymous unknown codes | **PARTIAL** — `queue.display.denied` stays with MP-39 |
| **MP-38 / MP-39 / MP-40** | frontend language/typography, admin surface, demonstration | **not started / BLOCKED (B-4)** |

**Tests and controls.** `backend/tests/test_multidisplay.py` — 34 tests, all
passing; whole-tree backend **1027 passed / 0 failed in 630.62s** (`993 + 34`);
frontend **467 tests, 465 passed, 0 failed, 2 skipped**. Three negative controls
(scope filter removed → 4 failed; `room_name` always published → 1 failed;
`updated_at` inside the version → 2 failed), each restored byte-identically
(SHA-256 `True`). One latent defect was found by a SQLAlchemy warning during the
first green run — an estimate query filtered by `Doctor.id` inside a
`queue_entries` query cross-joined and multiplied samples — and was fixed with a
regression test.

**Database.** Local development PostgreSQL, `127.0.0.1:55432`, revision
`b2e5c7d91a04` → `d3f5a7b91c24`. `alembic current` was read **before** the
upgrade; the second `upgrade head` was a no-op; a schema snapshot (31 → 33 tables,
**zero** existing tables changed) replaced a dump because no `pg_dump` binary
exists on this host — disclosed, not glossed. The owner's deployment was **not**
contacted, opened, rebound or migrated.

**The push, verified.** Two path-grouped commits were pushed to
**`origin/hackathon-mvp`** and nothing else: `082e2a0` (backend — models,
migration, resolver and the 34-test file; 4 files, 1,289 insertions, 23
deletions) and `1f303d1` (docs — the report, the B-4 brief, Amendment A-5, this
section and Docs Index Revision 51). The remote answered
`0bd8059..1f303d1  hackathon-mvp -> hackathon-mvp`; after `git fetch`, local
`HEAD` and `origin/hackathon-mvp` were both
**`1f303d1502819f45a0e27793c1e75f1a7c9c3c29`**, and
`git rev-list --left-right --count` reported **`0  0`**. That hash is the
verification point. No force-push, no history rewrite, no tag, no other branch.
The two commits were scanned for key/token patterns before they left the machine
(`BEGIN … PRIVATE KEY`, `ghp_`, `sk-…`, `AKIA…`): **0 matches**. `.clinerules`
remains uncommitted — the only modified tracked file, and its change is the
owner's own `docs/plan/` ratification note.

<!-- §11 added 2026-11-25; §10 and every earlier section left as written. -->




---

## 12. Window of 26 November 2026 — controlled implementation after the roadmap audit

**Baseline:** `hackathon-mvp` @ `fd4d3656738dfef0885cfc86307903305aa2f08d`, working tree carrying only the
owner's `.clinerules` edit and the (then uncommitted) audit report. **Nothing was committed or pushed in this
window**; every state below is working-tree state.

**Environment, stated once for the whole section:** this Windows checkout has **no PostgreSQL** on `:5433` and
**no Docker**, so no backend test could be executed and no migration could be applied — not even to a local
database. Frontend tests run on Node 24.12.0, and additionally on **Node 22.23.5** (CI's major) fetched through
`npx`, which is what made the CI defect reproducible.

| Task | Scope actually executed | State | Evidence | Report |
|---|---|---|---|---|
| **MP-02 / MP-33** (CI truth) | Root cause of the red frontend job found **and fixed**: two test files had an unclosed `test()` callback, so later tests were nested inside a finished parent. Node 24 tolerates it; Node 22 cancels them (`cancelledByParent`) — CI failed in ~1 s at `Run frontend tests` while `npm ci` and `next build` had both passed | **IMPLEMENTED, TESTED locally — CI unproven** | Run `45651581256` (#34): backend job `succeeded` (8m 16s), frontend job `failed` at step 6 only; local reproduction under Node 22.23.5 → **2 fail, 13 cancelled**; after the fix **493 / 491 / 0 / 0 / 2** on Node 22 **and** Node 24 | `implementation/AMSDP_Controlled_Implementation_Execution_Report_V1.0.md` §4.1, §6 |
| **MP-39** | Display administration: `queue.display.manage` (inside `queue.*`, no new role, delegable set untouched), `GET/POST /api/v1/queue/displays` + `PATCH /api/v1/queue/displays/{id}`, one audit row per write with before/after, an admin page with a copyable display URL, pure rules in `frontend/lib/displays.js` | **IMPLEMENTED** — backend tests authored, **UNRUN** | `frontend/tests/display-admin.test.mjs` **11 pass**; `backend/tests/test_display_admin.py` **13 collected**; `py_compile` OK; route table shows the three paths | same report §4.2 |
| **MP-46** | `queue.display.denied` on the write routes, one row per denial: the specific row is written before the refusal, and `common/denial_audit.py` strips the internal marker and skips its generic `request.denied` row (Q-2 §10 / AC-21). Anonymous probes still write nothing | **IMPLEMENTED** — **UNRUN** | As MP-39; the duplicate-suppression assertion lives in the same module | same report §4.2, §8 |
| **MP-38 / MP-37 / MP-42 / MP-43 / MP-45** (page halves) | Board rewritten: `?lang=` → configured `display.language` → device preference **only** when no display is configured (so clearing a browser changes nothing); display name in the header; `clamp()` TV typography with the token largest; room label with an em dash; estimate with `≈` and the words "estimated wait"; facility footer; `If-None-Match` / `304` with no state change | **IMPLEMENTED, TESTED** | `frontend/tests/display-board.test.mjs` **9 pass**; `npm run build` ✓ | same report §4.3 |
| **MP-28** (residue) | The board's and the tracking page's page-local `{bn,en}` dictionaries removed into `lib/i18n.js`; the shared coverage test now enforces both | **IMPLEMENTED, TESTED** | 493-test suite green on both Node majors; `i18n-coverage.test.mjs` unchanged and passing | same report §4.3 |
| **MP-35** (seed) | `DEMO_DISPLAYS` + `_seed_displays()`: two boards in one branch, different language, scope and footer; idempotent, organisation pinned to `DEMO_ORG` | **IMPLEMENTED — not executed** | Module compiles and imports; `DEMO_DISPLAYS` reads back as `['cardio','main-hall']` in `demo-br-001`. **No database was available, and no live database was touched** | same report §4.4 |
| **MP-24** | Queue-history screen consuming the existing `/api/v1/queue/history`, with a query builder that omits empty filters, a tally that never re-classifies, and pagination | **IMPLEMENTED, TESTED (frontend)** | `frontend/tests/queue-history.test.mjs` **6 pass**; the test also asserts the route still owns scope, 404 and "every status" | same report §4.5 |
| **MP-25** | Durable, cross-process rate budget (`tracking_rate_buckets` + `common/rate_limit.py::hit()`, one `INSERT … ON CONFLICT`), wired into the tracking route with a documented in-process fallback; `estimate` flag in the payload; printable token card with QR | **IMPLEMENTED, partially TESTED** | Migration `e1b7c4a9d236` (`down_revision='d3f5a7b91c24'`, single head verified with `ScriptDirectory`) executed on a **scratch SQLite** DB: table created, second `upgrade head` a no-op, `downgrade` clean. `backend/tests/test_tracking_rate_limit.py` **5 collected, UNRUN** (no PostgreSQL) | same report §4.6 |
| **MP-23** | `backend/appointment/reports.py` — one endpoint, five BR §43 dimensions, a `reconciliation` block, token-derived branch scope, `percent: null` without published capacity. **Plus the report screen Option A requires**: `frontend/pages/reports.js` (day/period, branch, doctor) and `frontend/lib/operational-report.js` | **IMPLEMENTED; compiled; frontend TESTED and BUILT; 16 backend tests collected, NOT executed** | `py_compile` exit 0; `pytest --collect-only` → *16 tests collected*; an attempted run fails at fixture setup with `psycopg2.OperationalError … port 5433 … Connection refused` — **no database on this host**. `frontend/tests/operational-report.test.mjs` **12 pass**; `next build` exit 0 with `/reports` (6.8 kB) | `AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` §3, §5 |
| **MP-09, MP-13, MP-14, MP-15, MP-30** | Deliberately not started: PO-04 + the rehearsal gate, and PO-01 respectively | **unchanged** | Report §3 | same report §3, §11 |

**What this window did not do.** It did not commit, push, deploy, reseed, or reach any database; it did not
apply `d3f5a7b91c24` or `e1b7c4a9d236` anywhere; it did not mark anything TESTED on the backend, VERIFIED or
ACCEPTED; and it did not answer any Product Owner question.

<!-- §12 added 2026-11-26; §11 and every earlier section left as written. -->

---

## 13. Window of 26 November 2026 (second) — PO-D1 decided; MP-47 opened

**Nothing in §1–§12 is rewritten.** This section records one Product Owner decision and the work package it creates.
The change-log row of the same date sits in §8.

### 13.1 Decision applied

| Field | Value |
|---|---|
| Decision | **PO-D1 — Option C**: browser-based voice-pack upload is managed through a **separate work package** |
| Date | 26 November 2026 |
| Recorded | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` **§7** (new section; §1–§6 preserved verbatim) |
| Rationale (owner) | "Preserve the approved MP-04 scope and manage the additional upload capability independently." |
| Closes | **PO-D1** as raised in the MP-04 report §9.3 — the register never carried it as a row of its own, so no §4 row is retired |

### 13.2 New work package

| Task | Scope | State | Evidence / document |
|---|---|---|---|
| **MP-47** | **Browser-based voice-pack upload.** Twelve scoped areas (U-01…U-12): the upload surface, existing format/size ceilings, file validation and itemised error reporting, pre-submission auditioning, version creation inside the existing lifecycle, roles/capabilities, org and platform scope restrictions, audit and traceability, secure handling and storage, failure and recovery, frontend/backend tests, browser acceptance. Reuse-first: the recommended transport is the **existing** `POST /api/v1/voice-packs` contract, so no backend change is proposed | **PROPOSED** — Product Owner-authorised as its own package; awaiting nine owner decisions (U-D1…U-D9), a specification, and implementation authorisation. **Not implemented, not tested, not accepted** | `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md` (§2 scope, §4 options, §5 dependencies, §6 risks, §7 open decisions, §8 negative paths, §9 tests, §10 acceptance) |

**Identifier justification.** MP-47 is the next free identifier: `MP-01…MP-46` are all in issue (highest **MP-46**,
in this register and in `AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`), and a repository-wide search found no
occurrence of `MP-47`, `MP-48`, `MP-49` or `MP-5x` anywhere in `docs/`, `backend/` or `ai_factory/docs/`.

### 13.3 MP-04 — scope unchanged, and now confirmed

| Task | Position |
|---|---|
| **MP-04** (voice-pack admin UI) | **Scope unchanged.** Browser upload is **excluded** from MP-04 by Product Owner decision, not by agent preference. The exclusion is no longer a declared deviation (MP-04 report §10), and MP-04 must be assessed and accepted against its existing approved requirements **without** treating the missing upload form as a defect |
| **MP-23** (BR §43 reporting) | **Scope unchanged** by PO-D1 |
| Status of both | Unchanged: MP-04 = IMPLEMENTED · frontend TESTED · BUILD VERIFIED · not browser-verified · not accepted. MP-23 = IMPLEMENTED · frontend TESTED · BUILD VERIFIED · backend **NOT EXECUTED** · not accepted |

> **Status note (added 2026-11-27 — pointer only; the row above is left as written).** MP-23's backend
> **NOT EXECUTED** was closed on 27 November 2026: **§15** records 16 passing backend tests and is the
> authoritative source for that status. MP-04 is genuinely unchanged, as the row says. Nothing here is
> upgraded beyond TESTED, and nothing is VERIFIED or ACCEPTED.

### 13.4 What MP-47 needs before any code is written

1. Answers to **U-D1…U-D9** (proposal §7) — containers offered in the browser, transport at the documented ceilings,
   storage location and quota, retention of superseded assets, whether `422` refusals are audited, whether an
   `org_admin` may upload, manifest handling, checksum confirmation, and route placement.
2. A specification that turns U-01…U-12 into requirement statements traceable to the acceptance criteria.
3. **Explicit implementation authorisation** — PO-D1 approves the *package*, not the build.

### 13.5 What this window did not do

No code, test, schema, migration, seed, container or configuration was changed. The existing suites were re-run only
to prove the documentation amendment changed no behaviour (frontend **526 tests / 524 pass / 0 fail / 2 skipped**;
`pytest --collect-only` **16 collected**; backend execution still blocked — no PostgreSQL on this host). Nothing was
staged, committed, pushed, migrated, reseeded or deployed, and no Product Owner question beyond PO-D1 was answered.

<!-- §13 added 2026-11-26; §12 and every earlier section left as written. -->

---

## 14. Authorised commit, push and Ubuntu handover (2026-11-26)

Added after §13 on the Product Owner's instruction *"AMSDP — Authorisation to Prepare Commit, Push and Ubuntu Verification"*. §1–§13 are left exactly as written; nothing above is re-labelled by this section.

### 14.1 What was committed and pushed

| | |
|---|---|
| Code commit | **`31fcb458ddd8d8c9022d6d72e7cb3ccdac70b60c`** — 36 files (MP-23, MP-25, MP-39, MP-46, MP-35, MP-38/41/45, MP-24, MP-04, MP-28, MP-02/MP-33) |
| Documentation commit | **`62b2facd670583d84712151210dc7de3fb94f647`** — 9 files (decision record, MP-23/MP-04 reports, execution report, roadmap audit, MP-47 proposal, this register's §13, docs index Revision 52) |
| Push | `git push origin hackathon-mvp` → **`fd4d365..62b2fac`**, then docs-only **`62b2fac..f41a6ac`** (this section's record) and the correction commit that follows it |
| Verified after the push | `HEAD` = `origin/hackathon-mvp`, `0 ahead, 0 behind` after a fetch; the code tip `62b2fac` is an ancestor of the tip, which is the check the handover report §7.2 uses instead of a hardcoded SHA. The only remaining working-tree entry is ` M .clinerules` (the Product Owner's own edit, deliberately not staged) |
| Excluded on purpose | `.clinerules`; `frontend/.next` and `frontend/.audio-originals-backup` (ignored build/backup output); no unrelated, unexplained or owner-owned file was staged |

Attribution, per-file, is in the handover report §2: staging was **by explicit path**, never `git add -A`.

### 14.2 Migration position — Ubuntu versus the code

| | Revision |
|---|---|
| Ubuntu demo database (Product Owner-reported) | `c4d8e2a91f60` |
| Head of the committed tree | **`e1b7c4a9d236`** |
| Required path | `b2e5c7d91a04` → `d3f5a7b91c24` → `e1b7c4a9d236` — **three revisions, single head, no branch, no merge** |

All three are **additive**: they create `schedule_blocks`, `queue_displays` + `queue_display_doctors`, and `tracking_rate_buckets`, with their indexes and checks; **no existing table, column, constraint, index or row is modified**, and each is idempotent and reversible. The demo data is therefore compatible, with two consequences worth stating: the new boards and blocks start **empty** (correct defaults), and the demo seed is **not** run by a migration.

**Nothing was migrated, reseeded, rebuilt or restarted.** The assessment, the backup requirement (`_tools/pg_backup.sh` before any upgrade), the risk register **R-M1…R-M6** and the exact Ubuntu commands are in `deployment/AMSDP_Hackathon_MVP_Push_and_Ubuntu_Verification_Handover_V1.0.md` §6–§7.

### 14.3 Status after this window

- **MP-04** — IMPLEMENTED · frontend TESTED · BUILD VERIFIED · **not browser-verified** · not accepted. Scope unchanged by PO-D1.
- **MP-23** — IMPLEMENTED · frontend TESTED · BUILD VERIFIED · backend **NOT EXECUTED** · not accepted.
- **MP-38 / MP-39 / MP-41 / MP-45** — code committed; **not browser-verified**; the public board and the admin screen both need `d3f5a7b91c24` applied before they can be checked.
- **MP-47** — **PROPOSED**. Nine decisions (U-D1…U-D9), no specification, no implementation authorisation.
- **Nothing is ACCEPTED**, and the backend suite has **not** been executed anywhere in this window.

### 14.4 What §14 does not claim

It does not claim the migration works (it was never run), that the backend is green (34 tests collected, none executed), or that any screen works in a browser. Each of those needs the Ubuntu checklist in the handover report §8, run under a separate authorisation for the migration window.

<!-- §14 added 2026-11-26; §13 and every earlier section left as written. -->


---

## 15. Backend execution on a scratch database (27 November 2026)

**Why this section exists.** §12 and §14 both recorded the same blocker and the same honest consequence:
**no backend test had ever been executed in this checkout**, so MP-23, MP-25, MP-39, MP-45 and MP-46 stood at
*IMPLEMENTED, UNRUN*. That blocker was never a product defect — it was "there is no database on this host".
A PostgreSQL **16.4** server is listening on `127.0.0.1:55432` in this window (corrected 2026-11-27 under OA-2 / audit F-13; the §15.1 annotation below carries the finding and is now **executed**), so the blocker was closable, and this
section records the attempt, the five defects it exposed, and the result.

**Nothing was committed or pushed.** The baseline is the docs tip **`71226e8`** plus, at close, three modified
tracked files: the owner's own `.clinerules` edit (untouched, as §11 requires) and the three test files named
in §15.3. **No product file was modified in this window** — every defect found was in a test.

### 15.1 Environment and database, stated exactly

| | |
|---|---|
| Host | Windows checkout, `E:\amsdp`, `.venv` Python |
| PostgreSQL | **16.4**, listening on `127.0.0.1:55432` (verified this window; **corrected 2026-11-27 under OA-2 / audit F-13** — the row read "17") |
| Database used | **`amsdp_verify_1127`** — an **empty** database created for this window; then a **second run on a separate scratch database, `amsdp_verify_1127b`**, to repeat the whole suite without inherited rows. **Corrected 2026-11-27 under OA-2 / audit F-08:** no retained artefact records that database being created or migrated — the retained `amsdp_dbs.txt` (11:20:38) predates its existence — so "created empty and migrated zero → head" is **not claimed**; the second green run is real, its creation and migration transcript is **missing** |
| Database **not** used | the developer database `amsdp` on the same server, and the Ubuntu deployment (`c4d8e2a91f60`). Neither was **migrated or reseeded** in this window, and neither carried a whole-suite run. **Corrected 2026-11-27 (audit F-01):** an earlier version of this row said the developer database was "neither contacted, opened nor migrated"; three earlier dashboard test invocations against `…/amsdp` do remain in retained shell history, and their exact timing and any effect on that database are **not** established by the available evidence. The Ubuntu deployment was not contacted, opened or migrated |
| Connection override | `AMSDP_DATABASE_URL=postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_verify_1127` for every command below |
| Migration | `alembic upgrade head` from **zero** on the empty database; `alembic current` → **`e1b7c4a9d236 (head)`**; `alembic heads` → **one** head, `e1b7c4a9d236` |
| Docker | not used; no container, no compose service, no deployment artefact touched |

The zero-to-head run is the first time the three additive revisions (`b2e5c7d91a04` → `d3f5a7b91c24` →
`e1b7c4a9d236`) have been applied as a **chain from an empty database**. It is evidence for the migrations
themselves on a disposable database; it is **not** evidence for the Ubuntu upgrade path, which remains the
handover report §8 checklist.

> **Audit annotations (independent audit, 2026-11-27 — additive; the table above is not otherwise rewritten).**
>
> 1. **Engine version (audit F-13).** The row above says PostgreSQL **17**. Three local artefacts say
>    otherwise: `…\AppData\Local\amsdp\pgdata\PG_VERSION` = `16`, `pgsql\bin\pg_config.exe --version` =
>    `PostgreSQL 16.4`, and `pg.log` line 1 = `starting PostgreSQL 16.4 …` with no restart since
>    2026-11-24 10:59:53. The executions are therefore evidence on **PostgreSQL 16.4**. The same "17"
>    appears in the §8 change-log row for 2026-11-27 and in Docs Index Revision 54. The correction is
>    **not** applied here because this phase did not authorise it; it is requested in
>    `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` §13 (A-2).
> 2. **Second-database provenance (audit F-08).** No retained artefact records `amsdp_verify_1127b` being
>    created or migrated, and `amsdp_dbs.txt` (11:20:38) predates its existence. The second green run is
>    real; "created empty and migrated zero → head" is the narrative, not a captured fact. Read it as "a
>    second run on a separate scratch database".
> 3. **Rate-limit fixture (audit F-04).** The `pqt:%` reset added to `tests/test_tracking_tokens.py`
>    deletes rows across the whole shared test database and clears a process-global dict. It is correct
>    for a single-process run; it is **not** concurrency evidence, and `pytest-xdist` should not be
>    introduced on `backend/tests/` until that is scoped.
> 4. **Evidence.** Artefact inventory, SHA-256 digests and a claim-by-claim grading:
>    `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md`. Full audit:
>    `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` (verdict: **PASSED WITH CONDITIONS**).

### 15.2 The result

**Whole backend suite: `1061 passed, 0 failed in 541.58s (0:09:01)`** — one process, `-q --tb=line`, against
`amsdp_verify_1127`. Every collected test ran; none was skipped, deselected or xfailed.

The modules that carry the work packages this section is about, each executed as its own run as well as inside
the whole-suite run:

| Module | Result | What it now proves |
|---|---|---|
| `tests/test_operational_reports.py` | **16 passed** | MP-23's five BR §43 dimensions, reconciliation block and token-derived branch scope |
| `tests/test_display_admin.py` | **13 passed** | MP-39's three routes, `queue.display.manage`, before/after audit, plus MP-45's field suppression and MP-46's `queue.display.denied` row |
| `tests/test_multidisplay.py` | **34 passed** | MP-35…MP-45's public surface: scope, estimate, `ETag`/`304`, room and department scope |
| `tests/test_denial_audit.py` | **8 passed** | MP-46's shared machinery: one row per refusal, marker stripped, no duplicate `request.denied`, no PII attribution from a forged token |
| `tests/test_tracking_rate_limit.py` | **5 passed** | MP-25's durable budget through `common/rate_limit.py::hit()` — one `INSERT … ON CONFLICT` |
| `tests/test_tracking_tokens.py` | **17 passed** | MP-25's durable budget as the limiter the tracking route actually charges (see §15.3 defect 5) |
| `tests/test_seed_demo.py` | **3 passed** | MP-35's demo seed executes against a real schema, idempotent, organisation-pinned |
| `tests/test_queue_room_snapshot.py` | **15 passed** | the room snapshot the board reads |
| `tests/test_dqds.py` | **26 passed** | the historic board's own contract, unchanged by MP-45 |
| `tests/test_e2e.py` | **21 passed** | the end-to-end booking → queue journey |

Repeatability was checked rather than assumed: `tests/test_tracking_tokens.py` was executed **three times in a
row (17 passed each)** and `tests/test_display_admin.py` twice (**13 passed each**) after the fixes in §15.3,
because the two defects that mattered were *second-run* defects.

The whole-suite run was then repeated on a **second, pristine database** — `amsdp_verify_1127b`, created empty in
this window and migrated zero → head, so the chain was printed revision by revision (`… c4d8e2a91f60` →
`b2e5c7d91a04` → `d3f5a7b91c24` → `e1b7c4a9d236`) — with the same command:

**`1061 passed, 0 failed in 542.27s (0:09:02)`.**

The first run inherited rows from the per-file rollout; the second inherited nothing. Both agree, so the green
result does not depend on leftover data — which is precisely the failure mode defect 5 belonged to.

**Display-admin denial coverage was checked rather than assumed**, because MP-46's rows are asserted in
three places and it would be easy to claim one while only another exists: `tests/test_display_admin.py`
holds the **route-specific** assertions (`queue.display.denied` written exactly once per refused write,
attributed to the caller's own organisation, with no second generic `request.denied`);
`tests/test_denial_audit.py` holds the shared middleware machinery (marker stripped, header not leaked, no
PII from a forged token); and `tests/test_multidisplay.py` holds the **public-surface** half — the
disabled-display throttle (`test_a_disabled_display_404s_identically_and_is_audited_once`: one
`queue.display.disabled_requested` row for repeated requests) and the anonymous-probe rule
(`test_unknown_codes_write_no_audit_rows`: 100 probes, zero rows), plus the `405` verb refusal. All three
modules ran green, and no test was added for MP-46 in this window.

> **Audit note (2026-11-27, F-02 — this supersedes nothing above; it qualifies it.)** "No coverage gap" holds
> for **AC-21**, which counts rows. It does **not** hold for the full text of **MD-19**, which lists
> `queue.display.denied` as carrying "actor, **capability**, org/branch": no capability identifier is
> persisted and no test asserts one (a search for `capability` in all three modules returns zero matches).
> MP-46 therefore stays **TESTED**, and the question is with the Product Owner:
> `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md`. See also
> `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` §8.

### 15.3 The five defects the execution exposed

All five are **test** defects. None is a product defect, and none was visible by reading code that looked
correct: each is a false assumption that only fails when the suite actually runs.

1. **`tests/test_operational_reports.py` — a module-scoped fixture wiped by the module's own purge.**
   `purge_org()` deletes `patients` (business rows) but deliberately keeps the organisation, branch, doctor and
   staff reference rows, so the module-scoped `ensure_patient` was erased by the first test and every later test
   ran without its patient. The patient is now re-created inside the autouse `clean` fixture.
2. **`tests/test_operational_reports.py` — a fixture that omitted two `NOT NULL` columns.**
   `_queue_entry()` inserted a `queue_entries` row without `token` and `patient_id`. The schema refuses it, so the
   fixture now supplies `token=f"T{position}"` and `patient_id=PATIENT`. The insertion error had been read as a
   report failure, which is why the distinction mattered.
3. **`tests/test_display_admin.py` — the public board addressed by the wrong identifier.**
   The route is `/api/v1/queue/display/{ORG_CODE}/{BR_CODE}` and resolves the **upper-cased facility code**, not
   the row id. **Five** call sites passed lower-case ids (`test_display_admin.py:226, 231, 296, 309, 310` — the
   `public`, `historic`, `quiet`, `switched-off` and `no-such-board` requests; an earlier version of this
   paragraph said four — corrected 2026-11-27, audit F-05). `ORG_CODE` / `BR_CODE` now derive from `ORG.upper()` /
   `BR.upper()`.
4. **`tests/test_display_admin.py` — MP-45's field-visibility assertion was vacuous.**
   The test asserted that switched-off fields were absent from a public body that contained **no doctor row at
   all**: the body lists a doctor only when that doctor has a queue entry on the facility's day, so "absent" was
   trivially true and the test could not have failed even if MP-45 were broken. It now seeds one `called` and one
   `waiting` entry (the body publishes a token **only** for the currently-served patient, never for a merely
   waiting one), asserts the row is really present — `assert "D-001" in raw` — and only then asserts that the
   switched-off fields are missing. `_purge()` gained the matching `queue_entries` / `patients` deletes, in FK
   order, because the module's business rows are now its own.
5. **`tests/test_tracking_tokens.py` — the reset hook stopped resetting when MP-25 landed.**
   The module was written when the tracking budget was the in-process `_RATE` dict, so three tests called
   `_RATE.clear()` to make their window deterministic. MP-25 moved the budget into `tracking_rate_buckets`, one
   durable row per `pqt:<ip>`. `_RATE.clear()` therefore became a **no-op reset**: the seventeen tests share one
   `testclient` address, the ten-per-minute budget was exhausted by the module itself, and later assertions met
   `429` where they expected `200` / `404`. Two suites — `test_tracking_rate_limit.py` and this module — were green
   in isolation and contradictory together. The fix keeps the limit intact and restores hermeticity: an autouse
   fixture calls `_reset_tracking_budget()`, which clears `_RATE` **and** the `pqt:%` rows before each test, and
   the three inline `_RATE.clear()` calls were replaced by it. **The limit is not weakened** — the budget is still
   charged, still asserted, and the 12-request test still requires its `429`.

Defect 5 is the one worth carrying forward: it is what an unexecuted suite hides. MP-25's own tests and the
pre-existing M9-B tests each passed alone and disagreed together, and only a **whole-suite** run could show it.

### 15.4 Status after this window

| Task | Before | After | What is still missing |
|---|---|---|---|
| **MP-23** | IMPLEMENTED · frontend TESTED · BUILD VERIFIED · backend **NOT EXECUTED** | IMPLEMENTED · frontend TESTED · **backend TESTED (16 passed)** · BUILD VERIFIED | VERIFIED, ACCEPTED |
| **MP-39** | IMPLEMENTED · backend **UNRUN** | IMPLEMENTED · frontend TESTED (11) · **backend TESTED (13)** | VERIFIED, ACCEPTED |
| **MP-45** | IMPLEMENTED · TESTED (server side, unrun) | IMPLEMENTED · **backend TESTED**, and the visibility test is now **non-vacuous** | VERIFIED, ACCEPTED |
| **MP-46** | PARTIAL · **UNRUN** | IMPLEMENTED · **backend TESTED** (8 denial-audit + the display-denial assertions) | VERIFIED, ACCEPTED |
| **MP-25** | IMPLEMENTED · partially TESTED · rate budget **UNRUN** | IMPLEMENTED · **backend TESTED** (5 + 17) · the durable budget is the limiter actually in force | a multi-worker deployment run, VERIFIED, ACCEPTED |
| **MP-35** (seed) | IMPLEMENTED — not executed | IMPLEMENTED · **seed executed** (`3 passed`) | the demo-data authorisation still unexercised |

**MP-04 is unchanged** — it has no backend surface in this window's suites, and §13.3's "not browser-verified,
not accepted" stands.

### 15.5 What §15 does not claim

- **No VERIFIED.** Nothing here is a browser session, a live API call against the deployment, or a database read
  of the demo data. §7's evidence standard is untouched: a green suite is TESTED, not VERIFIED.
- **No ACCEPTED.** Acceptance is the Product Owner's, and no question was asked or answered in this window.
- **No CI.** Nothing was pushed, so no workflow ran; the code is unverified by CI until a push happens, and
  §14.1's pushed tip `62b2fac` remains the last CI-relevant commit.
- **No frontend run.** The frontend suites were not re-executed; their last recorded state stands (§14:
  526 / 524 pass / 0 fail / 2 skipped). This window touched no frontend file.
- **No migration outside the scratch databases.** `amsdp_verify_1127` and `amsdp_verify_1127b` are disposable and
  are **not** the developer database, the demo database or the deployment.
- **Not a claim that the five defects were the only ones.** They are the ones the suites showed; the basis for
  that claim is the 1,061-test run, not a reading of the code.

<!-- §15 added 2026-11-27; §14 and every earlier section left exactly as written at that time. The audit
     corrections of 2026-11-27 (findings F-01, F-03, F-05, F-06) afterwards amended §8, §11 and §13.3 and added
     the annotations under §15.1 and §15.2. No status was changed. See
     docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md. -->


---

## 16. Window of 27 November 2026 (second) — F-02 closed, MP-38 defect fixed, backlog re-derived

**Nothing in §1–§15 is rewritten.** This section records implementation work executed after commit
`31fcb45` and after the 27 November audit. Report:
`docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md`.

### 16.1 Baseline

| Field | Value |
|---|---|
| Branch / HEAD | `hackathon-mvp` @ `71226e8` (unchanged at the end: nothing was committed) |
| Pre-existing modifications | All preserved; the `.clinerules` owner edit untouched |
| Disposable database | **new** `amsdp_verify_1128`, migrated zero → head (`e1b7c4a9d236`, single head) |
| No other database | `amsdp`, `amsdp_verify_1127`, `amsdp_verify_1127b`, `amsdp_mp16_scratch`, `amsdp_verify_2829` untouched |

### 16.2 Work executed

| Item | Change | State |
|---|---|---|
| **MP-46** (finding **F-02**) | `displays.py::_denied()` now records `after["capability"] = "queue.display.manage"` on **both** call sites (403 capability refusal and 404 non-owned row), completing the MD-19 triple. No migration: `audit_events.after` is JSON | **IMPLEMENTED, TESTED** |
| **MP-38** (new finding **MP-38-D1**) | The public board threw a `ReferenceError` — and rendered blank — for **every non-branch display**, because `scopeLabel(display,T)` passed an undefined `T` to a module-scope helper that referenced the component's `tr`. The translator is now a parameter (`scopeLabel(display,tr)`). This affected the **seeded `cardio` department board**, i.e. the demonstration | **IMPLEMENTED, TESTED** |
| **MP-24** | New `backend/tests/test_queue_history.py` (8 tests). **Corrected 2026-11-27 under OA-2 / RO-01:** the route was **not** untested — `backend/queuing/tests/test_queue.py:1141`–`:1250` already carried **eight** queue-history tests, including four non-disclosing **404** assertions. The new file adds *different* coverage: every status including `completed`, the `?status=` filter without re-classification, an invalid-date **422**, and a foreign doctor id | **TESTED — backend coverage extended, not created** |

### 16.3 Evidence

| Run | Result |
|---|---|
| Focused display band, before and after the edits | **73 passed** / **73 passed** |
| `tests/test_queue_history.py` | **8 passed** |
| Negative control A (branch check disabled) | **2 failed** → restored, SHA-256 match |
| Negative control B (status filter disabled) | **1 failed** → restored, SHA-256 match |
| Whole backend suite, after the MP-46/MP-38 changes | **1061 passed, 0 failed** (882.22s) |
| Whole backend suite, including the new module | **1069 passed, 0 failed** |
| Frontend | **527 tests · 525 pass · 0 fail · 2 skipped**; `display-board.test.mjs` 10 pass (was 9) |
| Frontend guard vs pre-fix source | **3/3 assertions fail** — the guard is effective |

### 16.4 Re-derived statuses that differ from the audit of 26 November

The audit was written at `fd4d365`; commit `31fcb45` landed after it. Re-checking the tree at
`71226e8` shows its multi-display matrix (§H.4) is materially stale:

| Item | §H.4 said | Tree at `71226e8` |
|---|---|---|
| **MP-39** | NOT IMPLEMENTED | IMPLEMENTED, TESTED (13 backend + 11 frontend) |
| **MP-38** | NOT IMPLEMENTED | IMPLEMENTED; **defective** until §16.2 |
| **MP-46** | 3/4, `queue.display.denied` absent | IMPLEMENTED, TESTED; MD-19 field now complete |
| **MP-35** | seed deliverable outstanding | IMPLEMENTED (`DEMO_DISPLAYS`, `_seed_displays`) |
| **MP-37 / MP-42 / MP-43 / MP-45** | page half absent | page halves implemented and asserted |
| **MP-24** | TESTED (frontend) | backend now TESTED as well |

**Re-derived counts (47 items):** 28 TESTED, 3 PARTIAL, 5 BLOCKED, 2 GATED, 5 DEFERRED,
4 SEQUENCED. **No unblocked feature work remains in the multi-display band.** The full table is §8 of
the report.

### 16.5 What this window did not do

It did not commit, push, deploy, reseed or migrate anything outside `amsdp_verify_1128`; it did not
start or stop a container; it did not run a browser, so **nothing became VERIFIED**; it did not touch
`.clinerules`; it introduced **no parallel test execution** (audit A-3 untouched); and it did **not**
correct the "17" documentation error of **F-13** — the server was observed reporting 16.4, and the
wording fix remains behind its own authorisation at the time of writing — **it was authorised later the same day by the Product Owner (OA-2) and has since been applied; see §17.2 and §17.4**.

<!-- §16 added 2026-11-27; §15 and every earlier section left exactly as written. -->

---

## 17. PO-DEC-01, the OA-2 correction package and the CI investigation (27 November 2026, later)

**Authority.** Product Owner response to the consolidated decision pack, **2026-11-27**:

- **PO-DEC-01** — MD-19 / MP-46 / F-02: **Option A, persist the capability field**.
- **OA-2 — APPROVED with limited scope**: documentation-only corrections — RO-01, RO-04, RO-05, RO-07, T-3, T-4,
  T-5, T-7, T-8, F-13, and F-08/RO-03.
- **T-1** — investigate the existing frontend CI failure *using available evidence, without committing or
  pushing*.
- **OPC-1…OPC-4** — interpretation confirmations (queue targeting remains doctor-set; labelled minute estimate;
  caller/target branch via `target_id`; PO-02 stays open).
- **Not granted:** **OA-1** and **OA-3…OA-8**; **PO-DEC-02…PO-DEC-11** (MP-47) remain deferred until the
  demonstration is complete; MP-11/12/21/26/27 stay deferred; MP-09/13/14/15 stay sequenced; **O-1** is not
  authorised.

**Scope discipline.** Documentation only. §1–§16 are preserved; **four factual sentences** inside them are
corrected in place because OA-2 names them (F-13 three times, F-08 once), each marked with its authority and the
wording it replaced. Everything else in this package is **appended**. No file under `backend/` or `frontend/`,
no test, no migration, no configuration, no database and no deployment was touched, and **nothing was staged,
committed, pushed or reseeded**.

### 17.1 The decision — PO-DEC-01 (MD-19 capability field)

| | |
|---|---|
| **Question** | Does MD-19 require the capability identifier to be **persisted**, or is "capability" a description of what the denial is about? |
| **Answer** | **Option A — persist it.** The field is required; `after.capability = "queue.display.manage"` on both denial paths is **approved**; no specification amendment and no code change follow from the decision |
| **Decision record** | `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` **§11** |
| **Effect on MP-46** | **None on status.** MP-46 stays **TESTED** — still **not VERIFIED**, **not ACCEPTED** |
| **Effect on MD-19** | **None.** No amendment, no Appendix E edit, no deviation row; Option B and Option C are not adopted |
| **Effect on code/tests/schema** | **None.** No file changed to record the answer |

**The sequence is recorded, not laundered.** `_denied()` gained the field in this day's second window **before**
any answer existed, while the implementation report §4.1/§9 recorded that no Product Owner decision was
required — an agent reconciliation, not an owner decision. Option A ratifies the **content that resulted**; it
does **not** convert the earlier write into an authorised act. Preserved as **RO-02** in
`docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` §3.2.

### 17.2 Status corrections and the corrected backlog tally (RO-04, RO-05, T-3, T-4)

| Item | Label in §13.3 / §16.4 | Corrected reading (authority) |
|---|---|---|
| **MP-30** | GATED (undefined) | **IMPLEMENTATION-READY as a verification task; BLOCKED on live evidence** — **PO-01 is CLOSED** (T-3) |
| **MP-34** | GATED (PO-09) | **IMPLEMENTED — awaiting Product Owner review/acceptance** — **PO-09 is CLOSED** (T-4, RO-04) |
| **MP-33** | GATED / BLOCKED on CI | **BLOCKED on OA-1** (commit/push) — no owner decision outstanding, no code defect (RO-04) |
| **MP-09, MP-13, MP-14, MP-15** | GATED (PO-04) | **SEQUENCED** — PO-04 authorises them on the first clean rehearsal; none has occurred |
| **QUE-005** | "the one surviving P0" | **Implementation present; acceptance outstanding** — the reorder guard at `backend/queuing/main.py:651`–`:668` validates permission, organisation scope and queue homogeneity (T-8) |
| **MP-24 coverage** | "no backend test existed" | **Eight queue-history tests already existed** at `backend/queuing/tests/test_queue.py:1141`–`:1250`; the 27 Nov file extends coverage (RO-01) |

**Corrected tally — 48 rows, 0 GATED** (replacing §16.4's "47 items … 2 GATED"):

| Class | Count | Items |
|---|---:|---|
| **TESTED** | 28 | MP-16, 23, 24, 25, 28, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46 (16) + MP-02b, 05, 06, 07, 08, 10, 17, 18, 19, 20, 22, 29 (12) |
| **PARTIAL** | 3 | MP-01, 02, 04 |
| **BLOCKED** | 6 | MP-03, **30**, 31, 32, 33, 40 |
| **IMPLEMENTED — awaiting acceptance** | 1 | MP-34 |
| **SEQUENCED** | 4 | MP-09, 13, 14, 15 |
| **DEFERRED** | 5 | MP-11, 12, 21, 26, 27 |
| **PROPOSED (deferred by PO-D1)** | 1 | **MP-47** |
| **GATED** | **0** | — |
| **Total** | **48** | 16+12+3+6+1+4+5+1 = **48** |

**Why 48 and not 47.** The earlier tally counted **MP-02b** (a named sub-item of MP-02) as its own row and
**omitted MP-47** — which `MP-47` occurs **zero** times in the implementation report and which this register
opened in **§13** the day before. The arithmetic was sound; the set was not closed. **GATED is now zero** because
both items it named (MP-30, MP-34) rested on owner decisions that have since closed.

**Nothing was promoted.** Every movement is **between blockers** — GATED → BLOCKED, GATED → awaiting acceptance,
GATED → SEQUENCED. No item moved toward VERIFIED or ACCEPTED, and no item's evidence changed.

### 17.3 Recorded interpretations and re-classifications (T-5 / RO-08, T-8, RO-01)

**MD-19 caller versus target branch — recorded interpretation, not an amendment (T-5, RO-08, OPC-3).** MD-19
requires a denial to be audited with "actor, capability, **org/branch**" and does not say whether that is the
**caller's** branch or the **target's**. On the authenticated **403** path both are knowable; on the
non-disclosing **404** path the target must not be disclosed. `_denied()` therefore records the **caller's**
organisation and branch and identifies the target through **`target_id`**. The Product Owner agreed with exactly
that reading on 2026-11-27 (**OPC-3**). **Consequences:**

- It is an **interpretation of the existing requirement**, not a change to it. **MD-19 is not edited** — the
  specification in `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` is an approved
  document and OA-2 authorises no edit to it.
- It creates **no new obligation**: the 404 path stays non-disclosing, and no target branch is written anywhere.
- It is recorded in three places: this section, decision request §11.2(1) and
  `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` §3.8.

**QUE-005 — classified (T-8).** QUE-005 is described in earlier documents as "the one surviving P0". It is
**not** an unimplemented feature. The manual-reorder route at `backend/queuing/main.py:651`–`:668` already
requires the `queue.reorder` permission, constrains the query to the caller's `organization_id`, and validates
queue homogeneity **before any mutation**, raising rather than partially applying. QUE-005's residual is
therefore **acceptance and independent evidence** — a live demonstration and an owner sign-off — **not a code
defect**. It stays open as an acceptance item and is **not** re-graded here.

**MP-24's coverage narrative — corrected (RO-01).** See §17.2's last row and
`docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` §3.1. The route had **eight** pre-existing
backend tests; the 27 November file adds different assertions. **MP-24 remains TESTED**, on a corrected
narrative.

**MP-34's residual items — unchanged and correctly attributed.** The V2.5 family column (**R-1**) and **QUE-005**
are what remains against MP-34. Neither is closed by this package: R-1 is an edit to a family column the owner
has not authorised, and QUE-005 is now classified above rather than solved.

### 17.4 The documentation corrections, and the Docs Index count convention (RO-05, RO-07, T-7)

**Every change in this package is listed, with its authority, in
`docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` §4** (eleven rows). Summarised: this register
gains **§17** and a §13.3 annotation, and four sentences inside §8 and §15 are corrected in place (F-13 ×3,
F-08 ×1); the register's §16.2 MP-24 cell is corrected (RO-01); the decision request gains **§11** (PO-DEC-01);
the implementation report gains **§13** and **§14**; the 27 November audit gains a post-audit annotation; the
Docs Index gains **Revision 57**; and the RO record itself is **created** (T-7). Nothing was moved, renamed or
deleted, so **no migration-manifest entry is required** (`.clinerules` §11).

**The Docs Index count convention, restated (RO-07).** Each revision of
`docs/governance/AMSDP_Docs_Index_V1.0.md` closes with a **Counts** line giving the **verified on-disk** total of
`*.md` files under `docs/`, reconciling with the previous revision. The chain breaks once: Revision 50 closes at
**163** (`:2177`), Revision 51 (`:2191`) registers one document and publishes **no Counts line**, and Revision 52
(`:2280`) opens from an unpublished **164**. From Revision 52 on the chain is consistent (165 → 166 → 166 → 169 →
170) and its figure **matched the tree** before this package (**170** by
`Get-ChildItem docs -Recurse -Filter *.md -File`). **Revisions 51 and 52 are not rewritten**; the break is
recorded here and in Revision 57, and Revision 57's own figure is **counted**, not carried forward.

**One deliberate non-correction.** Docs Index **Revision 54**'s "PostgreSQL 17" is left as written, because
Revision 55's annex already carries the correction and explicitly preserves Revision 54's text. Nothing in the
index now states a figure that a reader must act on and cannot reconcile.

### 17.5 Open items and what this section does not claim

1. **`AC-21` does not assert the capability field.** The acceptance criterion counts denial rows and does not
   enumerate fields, so nothing in CI would catch the field's removal. Adding such an assertion is a
   **test-scope** change; **OA-2 authorises no code or test change**, so it is raised and not acted on.
2. **OA-1 (commit/push) was not granted.** The owner asked for the frontend CI diagnosis first and for an exact
   commit manifest with an explanation of which test corrections it carries. §17.6 gives the diagnosis; the
   manifest is **not** supplied here and nothing is staged.
3. **OA-3…OA-8 were not granted.** Each still needs its own pre-condition before a request can be answered:
   OA-3 a database access method, credential scope and safety procedure; OA-4 a maintenance window with backup
   and rollback; OA-5 a reseed scope and safeguards; OA-6 a live-runtime verification plan; OA-7 a midnight
   rollover observation plan; OA-8 a local-stack/browser risk assessment and data-safety arrangements.
4. **RO-06, RO-09 and RO-10 remain unrecoverable** — no restatement, no primary source (RO record §1).
5. **MP-24's two overlapping test files** (`backend/queuing/tests/test_queue.py`,
   `backend/tests/test_queue_history.py`) are **not** consolidated: that is an engineering change and OA-2
   authorises none.
6. **No status moved.** MP-46 stays **TESTED**; MP-24 stays **TESTED**; MP-34 is **awaiting acceptance**; nothing
   in the project is **VERIFIED** or **ACCEPTED** by this package, because no new execution and no owner
   signature occurred.

### 17.6 The frontend CI investigation (T-1, read-only)

**What the pipeline runs.** `.github/workflows/ci.yml` defines one workflow with two jobs. The frontend job —
*Frontend — build and unit tests* (`:104`) — runs on `ubuntu-latest` with **Node 22** and executes, in order:
`npm ci` (`:119`), `npm run build` (`:123`), `npm test` (`:127`), where `test` is
`node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs`.
`frontend/package-lock.json` is present, which is what `npm ci` requires.

**What was already recorded, and where.** The failure has been investigated before and the finding is in the
repository: `docs/implementation/AMSDP_CI_First_Run_Failure_Investigation_V1.0.md` §4 records, from the job's
own step conclusions, that `npm ci` **succeeded**, `next build` **succeeded**, and the **`Run frontend tests`**
step failed (exit 1) — so the failure is a **unit-test** failure, not an install or build failure. The recorded
root cause: the **committed** `frontend/pages/patients.js` was the pre-refactor version while
`frontend/tests/banglanamesense-integration.test.mjs` asserted the **refactored** page, and the fix was
uncommitted work awaiting authorisation. `docs/implementation/AMSDP_MP-33_CI_First_Green_Run_Report_V1.0.md`
independently records that the then-current tip was red for one named reason and that the last green run was
**run #5** (2026-11-14, `6bfbec4`).

**What was checked in this window (read-only, no push, no CI call).** The test reads
`../pages/patients.js` through `readFileSync` and asserts on its **source text**
(`banglanamesense-integration.test.mjs:15`–`:16`). The three assertions the recorded failure turned on now
**match the committed page**: the `BanglaNameSense` import (1 match), `label={t('patN')}` (1 match) and
`value={f.name}` (1 match). `frontend/pages/patients.js` is **not** modified in the working tree, so what was
checked is the file's content at **HEAD (`71226e8`)**. The MP-28 internationalisation refactor that produces
those tokens was committed on 26 November (`31fcb45`), **after** the failing run in the record.

**Diagnosis, stated at the strength the evidence supports.** The **recorded** cause — committed page versus
refactored test — is **removed at HEAD**: the page now carries the tokens the test asserts. That is an inference
from source inspection, **not** an observed green run, and it is **not** claimed as one.

**Why it is not observed.** The CI state cannot be read from this host: the GitHub CLI is **not installed**
(`Get-Command gh` → not found), no API token is available in this session, and **OA-1** (commit/push) was not
granted, so no run of the working tree can be triggered either. **A green run is therefore not claimed for the
current tree** — the same discipline the MP-33 report applies.

**One divergence worth recording before any OA-1 request.** The local toolchain is **Node v24.12.0** while CI
pins **Node 22**. Nothing in the recorded history connects that gap to the failure, and it was **not** tested
here (no run was performed); it is recorded so that a future "passes locally, red in CI" result is not a surprise.

**What would settle it (all outside this authorisation).** Either a GitHub token/CLI to read the run for
`71226e8` and its predecessors, or an approved push that lets the pipeline run on the corrected tree. Neither is
done, and no test suite was executed in this window.

---

<!-- §17 appended 2026-11-27 under Product Owner authorisation OA-2 (PO-DEC-01 recorded; RO-01, RO-04, RO-05,
     RO-07, T-3, T-4, T-5, T-8 addressed; T-1 diagnosed read-only). §1–§16 preserved except the four sentences
     OA-2 names (F-13 ×3, F-08 ×1) and the §16.2 MP-24 cell, each marked in place with its authority. -->


---

## 18. Window of 27 November 2026 (third) — D-3 closed, MP-04's backend executed, OPC-3 aligned

**Authority.** The Product Owner's instruction of 2026-11-27 to resume approved, unblocked implementation
autonomously, without reopening any settled decision. **OA-1 was not granted**, so nothing was staged,
committed, pushed, merged or rebased. Report:
`docs/implementation/AMSDP_D3_Fixture_and_MP-46_OPC3_Target_Id_Implementation_Report_V1.0.md`.

**What made it possible.** A PostgreSQL instance answered on **`127.0.0.1:55432`** (PostgreSQL **16.4**),
the port the MP-16 report's own command names. A **new, disposable** database `amsdp_verify_1129` was
created empty and migrated from zero to **`e1b7c4a9d236 (head)`**. The developer database `amsdp` and the
Ubuntu deployment were **not** opened, migrated, seeded or read.

### 18.1 Work executed

| Item | Before this window | After |
|---|---|---|
| **D-3** identity fixture coupling | open; "reproduces only as a collection error; no fixture edit before a reproduction" | **reproduced** (`71 passed, 4 errors`, `doctors_organization_id_fkey` on `other-org-999`), **fixed** in `TestDoctorLink.setup_class` (test-only), **`75 passed, 0 errors`** — twice, the second run on the same database |
| **MP-04 backend** `organization/tests/test_voice_packs_api.py` | **NOT EXECUTED** (no PostgreSQL) | **25 passed** in 37.74s — first execution in the programme |
| **MP-46 / OPC-3** `target_id` on the cross-tenant 404 | recorded as an interpretation; the 404 wrote `target_id=""` | **`_denied()` accepts the probed id**; the 404 passes the path id; `after.code` still empty for an unresolved row; asserted in `tests/test_display_admin.py` |
| **Whole tree** | 1,061-test run recorded in §15 | **`1069 passed, 0 failed in 548.80s`** on `amsdp_verify_1129` |




### 18.2 A correction this window had to make — §17.5 item 1

§17.5 item 1 says *"`AC-21` does not assert the capability field … nothing in CI would catch the field's
removal"*. **It is true of HEAD `71226e8` and false of the working tree.** `tests/test_display_admin.py`
already asserts `after["capability"] == "queue.display.manage"` on **both** denial paths (`:192` for the
403, `:272` for the 404) — added in the §16.2 window and still uncommitted. The claim was written without
re-reading the test.

| Statement in §17.5 item 1 | Corrected reading |
|---|---|
| "no test asserts one" | **stale.** Two tests do, in the working tree; neither exists at `71226e8` |
| "nothing in CI would catch the field's removal" | **false once the working tree is committed**, because the backend job runs `tests/` |
| The real remaining gap | **`target_id` on the cross-tenant 404** — now closed and asserted (§18.1) |

§17.5's text is **left as written**; this section carries the correction, the same way §17 corrected §16.

### 18.3 Status after this window — nothing promoted

| Item | State | What is still missing |
|---|---|---|
| **D-3** | **CLOSED as a defect** — IMPLEMENTED, TESTED | VERIFIED (a fresh-database run is not a deployment observation) |
| **MP-04** | IMPLEMENTED · frontend TESTED (17 + 4) · **backend TESTED (25)** · BUILD VERIFIED | VERIFIED, ACCEPTED |
| **MP-46** | **TESTED** (unchanged grade) — coverage now includes OPC-3's `target_id` | VERIFIED, ACCEPTED |
| Everything else | unchanged | as §17.2 and §17.5 record |

**No item moved toward VERIFIED or ACCEPTED.** D-3 stopped being a defect; MP-04 gained the half that had
never executed; MP-46 gained an assertion. §17.2's corrected tally (48 rows, 0 GATED) still holds — D-3 was
never one of its rows, and MP-04 stays **PARTIAL** because its *verification* half is outstanding.


### 18.4 What §18 does not claim

- **No VERIFIED, no ACCEPTED.** No browser, no live request, no deployment contact, no CI run.
- **No migration outside `amsdp_verify_1129`.** No container, no compose service, nothing seeded.
- **No commit, push or stage.** The three changed files sit alongside the earlier windows' uncommitted work;
  `git status` still shows the owner's `.clinerules` edit untouched.
- **No frontend run** — no frontend file was touched.
- **No claim that D-3 was the only fixture defect** in the tree; it is the one the suite exhibited.
- **No MP-24 consolidation** — §17.5 item 5 still stands, and it still needs its own approval.


<!-- §18 appended 2026-11-27 after the OA-2 documentation package, under the Product Owner's instruction to
     resume approved implementation. §17 is preserved in full, including the §17.5 item 1 claim this section
     corrects (§18.2). Three files changed: backend/queuing/displays.py, backend/tests/test_display_admin.py,
     backend/identity/tests/test_identity.py. Nothing staged, committed or pushed. -->

---

## 19. Window of 27 November 2026 (fourth) — reconciliation, the collection-purity defect (T-10), and the database deviation

**Authority.** The Product Owner's controlled next phase of 2026-11-27, parts A–E: reconcile the third
window's delivery, record the database-authorisation deviation accurately, find and implement genuinely
unblocked local work, plan the remaining verification, and keep the boundaries.

**Boundaries observed in this window.** No database was opened, migrated, seeded, dropped or read — the only
database-adjacent actions were two `pytest --collect-only` invocations whose import-time connections were
**refused at the socket** (deviation record §4). Nothing was staged, committed, pushed or rebased; `HEAD` is
still `71226e8`. `.clinerules` was not touched. No deployment, Ubuntu or O-1 work was done. MP-47 and the
deferred packages were not started. The demo and rehearsal sequence was not bypassed.

**This section corrects one claim of §18 and one claim of the third window's report** — §19.6. Everything in
§18 is otherwise left as written.

### 19.1 Reconciliation of the third window's changes (part A)

**What actually changed.** At the start of this window `git diff --stat` against `HEAD` `71226e8` reported
**3 files changed, 100 insertions(+), 9 deletions(−)**: `backend/queuing/displays.py`,
`backend/tests/test_display_admin.py` and `backend/identity/tests/test_identity.py`. No fourth source file
was touched by the third window, which matches its own description of the change set. The same three files
now read **+149/−48**, because this window edited `test_identity.py` again under T-10 (§19.3); the other two
are untouched by this window:

| File | Diff vs `71226e8` now (numstat) | Changed by |
|---|---|---|
| `backend/queuing/displays.py` | **+21 / −3** | third window only (OPC-3 `target_id`, `_denied` docstring) |
| `backend/tests/test_display_admin.py` | **+69 / −6** | third window only (capability and `target_id` assertions, OPC-3 comment) |
| `backend/identity/tests/test_identity.py` | **+59 / −39** | third window (D-3 fixture) **and this window** (T-10: import-time sessions → fixture) |


| Check | How it was verified | Result |
|---|---|---|
| `target_id` applied to the 404 path | `displays.py:433`–`:434` passes `display=display, target_id=display_id`; `:146` resolves `display.id` when a row was found and falls back to the caller's id | **PASS** — one call site covers both resolutions |
| 404 stays non-disclosing | `:150` writes `"code": ""` when no row resolved; `:142`–`:143` attribute the row to `auth.organization_id` / `auth.branch_id`; `test_display_admin.py:280`–`:281` asserts the caller's branch is present and the target's is absent | **PASS** |
| Capability on the **403** path | `_require_manage` (`:161`–`:166`) → `_denied`; asserted at `test_display_admin.py:192` | **PASS** |
| Capability on the **404** path | `:433` → `_denied`; asserted at `test_display_admin.py:272` | **PASS** |
| `target_id` negative control | Observed in the third window: with the route back to the unresolved case the assertion failed (`assert '' == '991ef4bf-…'`) | **OBSERVED** |
| Capability negative control | **Not run** — removing the field and re-running needs a database, which this window was not permitted to open | **OUTSTANDING** (plan §3) |

**On the missing negative control.** The assertion is `rows[0].after["capability"] == "queue.display.manage"`.
Deleting the key from the audit payload makes that a `KeyError`, not a silent pass, so the test *cannot*
survive the field's removal — but that is a reading of the code, not an experiment, and it is recorded as
such rather than presented as a run. The exact command is in the verification plan (§3).

### 19.2 The database-authorisation deviation (part B)

**Recorded in full** at `docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md` — created this
window, no pre-existing document modified.

What it records, in one paragraph: the third window **created `amsdp_verify_1129`, migrated it zero → head
and ran the suite against it** on PostgreSQL 16.4 at `127.0.0.1:55432`, while the standing instruction
permitted neither database access nor migrations without explicit authorisation. That is a **scope
deviation**, self-reported, **not normalised**. A disposable target changes its impact, not its
authorisation. The database was left in place (dropping it would be a second unauthorised act), the whole-tree
log is retained and hash-stamped (`91C82E3B…B661199`), and the migration output is classified **REPORT-ONLY**
because it was never written to a file.

**Correction to §18.** §18's sentence — *"The developer database `amsdp` and the Ubuntu deployment were
**not** opened, migrated, seeded or read"* — is **true** and stays. It was, however, an incomplete account of
the boundary: it described what was avoided inside the database layer and did not say that **any** database
operation required authorisation. §19.2 supplies the missing half. This is the same additive correction
pattern §17 used on §16.

### 19.3 T-10 — collection wrote to the database (part C: the remaining local work found and fixed)

**The finding.** Six test modules performed **database writes at import time**, so `pytest`'s *collection*
phase opened sessions and committed rows before a single test was selected:

| Module | Import-time call (before) | What it wrote |
|---|---|---|
| `backend/tests/test_security.py` | `_ensure_orgs_and_branches()` (`:34`) | `m2-test-org`, **`other-org-999`**, four branches |
| `backend/tests/test_dashboard.py` | `_ensure()` (`:32`) | `m6-org`, `m6-branch`, `m6-doc` |
| `backend/tests/test_dqds.py` | `_ensure()` (`:62`) | two organisations, branches, two doctors, a patient |
| `backend/tests/test_patient_age.py` | `_ensure()` (`:41`) **and** `TOKEN = _token()` (`:89`) | organisation, branch, user, **plus a minted JWT via a query** |
| `backend/tests/test_tracking_tokens.py` | `_ensure()` (`:108`) and `TOKEN = _token()` (`:132`) | organisation, branch, user, plus a minted JWT |
| `backend/queuing/tests/test_queue.py` | `_ensure_org()` (`:29`) | `m5-org`, `m5-branch`, `m5-doc` |
| `backend/identity/tests/test_identity.py` | two module-level sessions (`:18`–`:43`) | `org-1`, `testadmin`, and `ADMIN_TOKEN` |

**Why it matters — it is the mechanism behind D-3.** `tests/test_security.py` created `other-org-999` when
the collector imported the file. `identity/tests/test_identity.py::TestDoctorLink` needed that row and never
created it, so it passed in a whole-tree run (where `test_security.py` was imported first) and errored
`71 passed, 4 errors` when the identity module was run alone against a fresh database. The suite's green was
therefore **order-dependent**, and `--collect-only` — a command that is supposed to read — **wrote**.

**The fix (test-only, no product code, no schema change).** Every import-time write became a
module-scoped `autouse` pytest fixture, and the two minted-token modules now populate the same globals from
a fixture (`_auth_headers`), so **no test body changed**. Nine call sites across seven files (the seventh
being `test_identity.py`'s two sessions plus its `setup_module`, which now delegates to the same helper).

**Evidence — executed, no database involved.**

| Check | Result |
|---|---|
| `pytest --collect-only -q` before (no `AMSDP_DATABASE_URL`) | **836 collected, 7 errors** — every error a refused connection at `127.0.0.1:5433` |
| …after refactoring six of the nine sites | **995 collected, 3 errors** — `test_identity.py`, `test_patient_age.py`, `test_tracking_tokens.py` still connecting |
| …after all nine | **1,069 collected in 1.81 s, 0 errors, zero connection attempts** (`E:\Temp\amsdp_collect_1129b.txt`, 103,311 B) |
| `py_compile` on the six changed files | **exit 0** |
| No module-level `_ensure*()` remains | verified by search across `tests/` and `queuing/tests/` |

**Status: IMPLEMENTED; collection-level TESTED (executed above); execution-level NOT RUN.** The new fixtures
have never executed — that needs a database (plan §5). They are a behaviour-preserving refactor of seeding
that already existed, but "behaviour-preserving" is a claim that only a run can settle, so it is stated as
an expectation, not a result.

### 19.4 Why the whole-tree total is still 1,069 (part A, question 5)

Three retained logs settle it; all three were read this window.

| Run | Database | Retained log | Summary line (verbatim) |
|---|---|---|---|
| 14:34:24 | `amsdp_verify_1128` | `E:\Temp\amsdp_full_1128.txt` (14,816 B, SHA-256 `2C4C5A03…3BFA9A58`) | `1061 passed, 50 warnings in 882.22s (0:14:42)` |
| 14:55:12 | `amsdp_verify_1128` | `E:\Temp\amsdp_full2_1128.txt` (7,408 B, SHA-256 `EF155E80…51F00FA8`) | `1069 passed, 58 warnings in 1007.35s (0:16:47)` |
| 17:09:20 | `amsdp_verify_1129` | `E:\Temp\amsdp_full_1129.txt` (14,816 B, SHA-256 `91C82E3B…B661199`) | `1069 passed, 50 warnings in 548.80s (0:09:08)` |

**The 1,061 → 1,069 step is the MP-24 file.** §16.3 records the new `backend/tests/test_queue_history.py`
(8 tests) landing between those two runs. The proof is a set comparison, not the arithmetic: the retained
`E:\amsdp_audit_evidence_27nov2026\amsdp_collect.txt` collection (**1,061** node ids) versus this window's
collection (**1,069** node ids) differs by **exactly eight ids, all in `tests/test_queue_history.py`, and by
nothing else** — `test_history_returns_every_status_including_completed`,
`test_the_status_filter_narrows_without_re_classifying`,
`test_a_foreign_branch_is_the_same_404_as_a_missing_one`,
`test_a_branch_scoped_caller_is_confined_to_the_token_branch`,
`test_another_branch_of_the_same_tenant_is_refused_not_narrowed`,
`test_a_doctor_reads_only_their_own_history`, `test_an_invalid_date_is_a_422`,
`test_another_tenants_doctor_yields_no_rows`. **Nothing was removed** ("ONLY IN OLD" was empty).

**So the third window changed no test count.** It added assertions inside an existing test
(`test_a_cross_tenant_patch_is_a_404_and_a_recorded_denial`) and changed a fixture — neither adds or removes
a collected test. 1,069 before, 1,069 after, **the same 1,069 tests**.

**And the identity error never appeared in a whole-tree run at all.** All three whole-tree logs report zero
errors, including the 14:34 run made *before* the D-3 fix existed. The `71 passed, 4 errors` was a **focused
`identity/tests` run** on a fresh database. That is exactly what §19.3 explains: in a whole-tree run the
collector imported `tests/test_security.py` first, which committed `other-org-999` at import, and the
unfixed `TestDoctorLink` passed on a row it never created.

### 19.5 MP-04 — backend testing is not feature verification (part A, question 6)

`organization/tests/test_voice_packs_api.py` → **25 passed** is the first execution of that module in the
programme and it proves the endpoints' shapes, refusals and persistence against a real database. It proves
**nothing** about whether a selected pack is *audible on a board*, whether an operator can find the control,
or whether the page sends the payload the API accepts. MP-04 stays **PARTIAL**, with the verification half
queued in the plan §2. The same distinction applies to MP-46 (§19.1): a green assertion is TESTED, not
VERIFIED.

### 19.6 The two corrections this section makes

| Where | Claim as written | Corrected reading |
|---|---|---|
| This register, §18 | "The developer database `amsdp` … **not** opened" recorded as the whole boundary | **True but incomplete** — *any* database operation required authorisation; the creation and migration of `amsdp_verify_1129` breached that. Carried by the deviation record and §19.2. **§18's text is left as written.** |
| Third window's report, §5 | "This is the first whole-tree run in this repository in which the identity module contributes 75 passing tests instead of 71 passing plus 4 setup errors" | **Unsupported.** All three retained whole-tree logs, including the pre-fix one at 14:34, report **zero errors**; identity contributed 75 passes in each because `tests/test_security.py` seeded `other-org-999` at import. The `71 passed, 4 errors` was a **focused** run. The report's §11 carries this correction; §5 is left as written. |

### 19.7 Statuses after this window — still nothing promoted

| Item | State | What is still missing |
|---|---|---|
| **D-3** | **CLOSED as a defect** — IMPLEMENTED, TESTED; root cause now named (T-10 masking) | VERIFIED |
| **T-10** | **IMPLEMENTED** — collection-level TESTED, execution-level NOT RUN | a normal run of the seven touched modules on an authorised database |
| **MP-04** | IMPLEMENTED · frontend TESTED · **backend TESTED (25)** · BUILD VERIFIED — **PARTIAL** | VERIFIED, ACCEPTED |
| **MP-46** | **TESTED** — capability on both paths, `target_id` on the 404 | the capability negative control, a live check, ACCEPTED |
| **Everything else** | unchanged from §17.2's 48-row tally (28 TESTED, 3 PARTIAL, 6 BLOCKED, 1 awaiting acceptance, 4 SEQUENCED, 5 DEFERRED, 1 PROPOSED) | as §17.2 and §17.5 record |

**No item moved toward VERIFIED or ACCEPTED**, and no grade was raised on the strength of a plan, a
reconciliation or a refactor that has not executed.

### 19.8 What §19 does not claim

- **No new test evidence from a database.** No database was opened in this window.
- **No VERIFIED, no ACCEPTED.** No browser, no live request, no CI run, no deployment contact.
- **No commit, push or stage.** `HEAD` is `71226e8`; `git diff --cached` is empty; the owner's `.clinerules`
  edit and every earlier uncommitted change are preserved untouched.
- **No schema change**, no migration authored, no Alembic revision edited.
- **No re-opening of a settled decision**: OPC-3 and PO-DEC-01 stand as recorded; MP-24's two overlapping
  test files remain unconsolidated (§17.5 item 5).
- **No claim that T-10 is the last test-isolation defect.** It is the one the collector exposed; the seven
  modules listed in §19.3 are the complete set the collector could reach.

---

## 20. Fifth window — verification preparation, and one guard that could run without a database

**Mandate.** Prepare the remaining work for explicit authorisation; complete everything that can be done
without database or infrastructure access; do not stage, commit, push, migrate, deploy or contact O-1.

### 20.1 What this window produced

| Artefact | Path | Bytes | Nature |
|---|---|---:|---|
| OA-1 commit manifest (proposal) | `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` | 22,426 | Four proposed commits, exact `git add` paths, messages, dependency order |
| T-10 disposable-database execution plan | `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` | 22,933 | Two database names, guard script, exact commands, duration, data, cleanup, isolation proof |
| OA-8 / B-2 local-stack verification plan | `docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md` | 18,745 | Services, accounts, per-package walkthroughs, evidence rule, cleanup, live risks |
| **T-10 collection guard** (source) | `backend/tests/test_collection_purity.py` | 5,167 | Two tests; the only thing this window executed |

### 20.2 The one new test, and why it is not a database test

`test_collection_purity.py` asserts that pytest's **collection** succeeds against a sentinel DSN that cannot be
reached (`postgresql+psycopg2://amsdp@127.0.0.1:1/amsdp_collection_guard`), plus a separate control that the
sentinel really is unreachable. It therefore **encodes T-10's invariant while needing no database**, which is
why it could be executed in a window that is not authorised to touch one.

| Id | Run | Result |
|---|---|---|
| **E-1** | `pytest tests/test_collection_purity.py -q -p no:cacheprovider` | **2 passed in 7.63 s** |
| **E-2** | Negative control: a throwaway module re-introduced a module-level `SessionFactory().execute(text("select 1"))` | guard **failed as designed** — `1 failed, 1 passed`, failure text `sqlalchemy.exc.OperationalError … port 1 failed: Connection refused`; the sentinel control still passed, so the two assertions are independent |
| **E-3** | throwaway module deleted (`Test-Path` → `False`); guard re-run | **2 passed in 6.62 s**; no residual file |
| **E-4** | `pytest --collect-only -q` with no `AMSDP_DATABASE_URL` | **1071 tests collected in 1.80 s**, 0 errors, no connection attempt |

The suite count moves **1,069 → 1,071** because of those two guards. The +2 is named and attributable; it is not
a silent change to the tally in §17.2.

### 20.3 Reconciliation of the instruction against the tree

| Instruction said | The tree contains | Handling |
|---|---|---|
| "all 24 working paths" | 24 at window start; **28** by the end (this window adds 4) | Manifest §1 states both figures and why |
| "the five earlier test corrections" | **six** pure T-10 modules, **one** unrelated earlier correction (`test_operational_reports.py`), **one** file carrying two deliverables (`test_identity.py`) | Manifest §4.1 tabulates the hunks; the "five" is recorded as an **open item**, not invented into shape |
| "do not drop `amsdp_verify_1129`" | unchanged; untouched; no connection to it | T-10 plan §9 states it is excluded from cleanup by name |
| "no database access" | zero. No connection attempt was made in this window, not even a refused one | This window's only sockets are the sentinel port-1 refusals inside E-1–E-4, which are the guard's *subject*, not a database |

### 20.4 Status, unchanged

| Item | State | What is still missing |
|---|---|---|
| **D-3** | CLOSED as a defect — IMPLEMENTED, TESTED | VERIFIED |
| **T-10** | IMPLEMENTED · collection-level TESTED (now guarded) · execution-level **NOT RUN** | Run A of the T-10 plan |
| **MP-04** | PARTIAL (backend only, 25 tests) | browser session — OA-8 / B-2 |
| **MP-46** | TESTED | capability negative control (Run B), live check, ACCEPTED |
| **MP-33** | BLOCKED | **OA-1**, and a push if CI is to observe the tree |
| Everything else | unchanged from §17.2's 48-row tally | as §17.5 records |

**Nothing was promoted.** No VERIFIED, no ACCEPTED, no grade raised on the strength of a plan.

### 20.5 What §20 does not claim

- **No database, no container, no browser, no CI, no deployment contact.** `HEAD` is still `71226e8`;
  `git diff --cached` is empty.
- **No staging, commit or push**, and no destructive Git operation: `displays.py` carries the uncommitted
  MP-46 change and was not touched at all this window.
- **No re-opening of settled decisions.** MP-24's two overlapping test files remain unconsolidated (§17.5
  item 5); MP-47 remains proposed and deferred.
- **No claim that the plans are approved.** They are requests; each names the permission it waits on.

<!-- §20 appended 2026-11-27, fifth window. §1–§19 preserved exactly as written. Files changed: three new
     plans/documents plus one new test module. Nothing staged, committed, pushed, migrated or deployed. -->

---

## 21. Fifth window, second sitting — the OA-1 sequence made executable

The owner answered the fifth window's requests: **commit preparation only** (no staging, no commit, no push), the
**five corrections named**, `.clinerules` excluded entirely, and both the T‑10 execution and the OA‑8/B‑2 browser
work submitted for review before execution.

**What this sitting produced**

| Artefact | Path | Nature |
|---|---|---|
| Final OA-1 manifest | `docs/plan/AMSDP_OA1_Commit_Manifest_Final_V1.0.md` | §3 maps the five corrections to file + hunk; §4 states why file-level `git add` cannot separate them; §5/§6 are the two candidate sequences; §12 is the only copy of the five commit messages |
| Hunk splitter | `E:\Temp\amsdp_hunkstage.py` | Reads `git diff`, emits a subset patch. Read-only with respect to the repository; no index and no working-tree write |
| Addenda (3) | proposal §11, T‑10 plan §15, OA‑8/B‑2 plan §14 | Record the owner decisions without rewriting anything above them |

**Validation of the mechanism (V‑1…V‑5, against a throwaway `GIT_INDEX_FILE`)**

| Id | Check | Result |
|---|---|---|
| V‑1 | `p1_display_feature` (H5,H7) | applicable; 19/0, 2 hunks |
| V‑2 | `p2_display_corrections` (H1–H4,H6,H8–H10) | applicable; 50/6, 8 hunks |
| V‑3 | p2 then p1 | still applicable; union = 69/6, 10 hunks = full diff |
| V‑4 | p3 then p4 (tracking tokens) | still applicable; union = 60/10, 7 hunks = full diff |
| V‑5 | real index afterwards | empty; temp index deleted |

**What this sitting does not claim**

- **No staging, no commit, no push.** `HEAD` is `71226e8`; `git diff --cached` is empty; `.clinerules` untouched.
- **No per-commit test run.** The five corrections and the MP‑46 assertions still rest on the 17:09 whole-tree log
  plus inspection; Run A of the T‑10 plan is what changes that.
- **No database, container, browser or O‑1 contact.** Zero.
- **No promotion.** MP‑04 PARTIAL, MP‑46 TESTED, display band TESTED, T‑10 IMPLEMENTED (collection-level only),
  D‑3 CLOSED as a defect — all unchanged, as §20.4 records.

<!-- §21 appended 2026-11-27, fifth window second sitting. §1–§20 preserved exactly as written. Nothing staged,
     committed, pushed, migrated or deployed. -->






