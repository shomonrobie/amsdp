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
| **PO-05** | **CLOSED** | MP-04 and MP-26 stay deferred; W3 re-opens only on the pack's stated trigger |
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
| **MP-04, MP-21, MP-26, MP-27** | DEFERRED/GATED | **DEFERRED** | PO-05, PO-06, PO-07 |
| **MP-11, MP-12** | DEFERRED (Q-6 c) | **DEFERRED** unchanged | Not reopened by any decision in this window |

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
| 2026-11-25 | **Q-1 and Q-2 answered by the Product Owner: both APPROVED as recommended, plus a push authorisation and a demo-data authorisation** (decision record §11, Addendum A-1; plan Appendix G, Amendment A-4). Worked in the same window: **Q-1** — `backend/patient/main.py` no longer reads the host clock (the future-DOB check and the age both resolve through `common.timeutil.operational_today`, once per request), 12 new DB-free tests + a source guard; **Q-2** — the Waiting tile now reads `queue_length` and `in_queue` stays visible under its own label, one new PostgreSQL test proving the two populations differ by the appointment-less walk-ins. Evidence, negative controls, commits and the pushed remote tip: **§10**. Q-1/Q-2 rows in §4 are **superseded by §10, not edited**. Report: `implementation/AMSDP_Q1_Q2_Facility_Day_And_Dashboard_Counts_Report_V1.0.md`; Docs Index annex added (Revision 50) |





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



