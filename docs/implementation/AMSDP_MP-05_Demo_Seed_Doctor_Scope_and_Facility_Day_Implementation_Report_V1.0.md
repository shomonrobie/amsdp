# AMSDP — MP-05 Implementation Report: demo seed doctor scope and facility day

**Task:** MP-05 (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6, WP-B)
**Priority:** P0 · **Depends on:** — · **Related:** GAP-03, GAP-25, PO-RBAC-01
**Date:** 2026-11-24 · **Checkout:** `E:\amsdp` · **Branch:** working tree, uncommitted
**Evidence status reached: VERIFIED for the scratch database and the running code path** — the seeded rows were
read back with `psql`, and a token minted for the seeded `doctor` account returned **HTTP 200** on its own queue
and **HTTP 404** on another doctor's. The **live demo database has not been re-seeded** (a state-changing
production action requiring owner approval, which was not given); §5 states exactly what that leaves open.

---

## 1. Requirement

The plan's row, verbatim:

> **MP-05** — `seed/seed_demo.py` seeds staff but **zero** `staff_doctor_assignments` rows, while
> `common/auth.py` refuses the legacy `staff_users.doctor_id` fallback once the table exists → the seeded
> `doctor` account can reach **no** queue. P0. Deliverables: seed the assignments; keep the seed idempotent.
> Acceptance: *doctor login → own queue 200; another doctor's queue 404.*

MP-44 (Appendix D.4 rule 11) additionally requires the seed to take its day from the facility, not the server,
so that queue, dashboard, display and seed agree on "today".

### 1.1 The two defects as found

**A — scope (PO-RBAC-01).** `DEMO_STAFF` created a `doctor` account with the legacy `doctor_id` column only.
`common/auth._load_assigned_doctor_ids` treats `staff_doctor_assignments` as **authoritative**: when the table
exists and returns no active row, that is a *revocation*, not a reason to fall back. Migration `f8a1b2c3d4e5`
backfills legacy rows, but the seed never wrote one, so a freshly seeded database produced a doctor login that
failed closed at every queue call — the demo's most important path, dead on arrival, with no error at seed time.

**B — day (GAP-03/GAP-25).** `_seed_appointments()` and `_seed_queue()` both began with `date.today()` — the
container's clock. At 01:00 Dhaka the seed filed the demo week and today's queue under the **previous** day, so
the board (MP-06) and the dashboard had nothing for the day the room was actually on.

---

## 2. Change

All in `backend/seed/seed_demo.py`; nothing else was touched.

1. **Imports.** `date` dropped (no longer used), `StaffDoctorAssignment` added to the model import, and
   `operational_today` imported from `common.timeutil`.
2. **New data table** `DEMO_STAFF_DOCTOR_ASSIGNMENTS` — one explicit doctor per demo account (`doctor` and
   `assistant` → `demo-dr-002`), with the comment stating *why* it exists and that the seed grants nothing
   beyond the demo path.
3. **New step `_seed_staff_doctor_assignments(session)`**, called after `_seed_staff` and before
   `_seed_patients`. It skips (with a printed reason) if the staff row or the doctor row is missing, leaves an
   existing active row alone, re-activates a revoked one, and otherwise inserts an id assignment id
   `demo-assign-<username>-<doctor_id>` — so re-running is **idempotent by construction**, not by luck.
4. **`_demo_today(session)`** — one helper returning `operational_today(session, DEMO_ORG["id"])`, replacing both
   `date.today()` call sites, with a docstring naming the defect it prevents.
5. **`RESET_ORDER`** — `staff_doctor_assignments` added **before** `staff_users` and `doctors`, because an
   assignment references both and the reset would otherwise fail on the foreign key.

---

## 3. Tests

### 3.1 New test file — `backend/tests/test_seed_demo.py`

Three tests, each aimed at a specific way the defect could return:

1. **`test_demo_today_is_the_facility_day_not_the_server_day`** — the clock is frozen at `2026-11-23T19:00Z`,
   which is 01:00 on the 24th in Dhaka; `_demo_today(session)` must return `2026-11-24`. A stub `date` whose
   `today()` answers "the 23rd" is attached to the seed module, so a server-clock implementation fails rather
   than passing by coincidence. The instant is injected, not read from the wall clock, so the test is stable on
   any host in any timezone.
2. **`test_seed_calls_no_server_local_date`** — an AST walk over `seed_demo.py` asserts **no** `*.today()` call
   remains anywhere in the module. A behavioural test can be passed by luck once a year; this one cannot — any
   future `date.today()`/`datetime.today()` re-introduction fails immediately, at whatever line it appears.
3. **`test_seed_assigns_exactly_one_doctor_to_the_doctor_and_assistant`** — runs `seed()` **twice** (the second
   run is the idempotency proof) with `_demo_password` stubbed to a non-credential placeholder, then asserts for
   both `doctor` and `assistant`: exactly **one** active `staff_doctor_assignments` row, pointing at
   `demo-dr-002`, carrying the demo `organization_id`; `_load_assigned_doctor_ids` returns `["demo-dr-002"]`; and
   the resulting `AuthContext.can_access_doctor()` is `True` for `demo-dr-002` and `False` for `demo-dr-001`. The
   assertion is on the *authorisation outcome*, not only on the row count, so a wrong-doctor assignment or a
   scope-less account fails.

**Two authoring defects were found by running these tests, and both were mine, not the code's.**
`AuthContext` was first constructed with a guessed signature; the real one is
`AuthContext(user_id=…, organization_id=…, branch_id=…, role=…, username=…, locale=…, status=…, token_payload=…)`,
with `assigned_doctor_ids` supplied from `_load_assigned_doctor_ids` rather than assumed. The test was corrected
against `common/auth.py`. This is recorded because it is the failure mode these reports exist to prevent — a test
written from assumption can pass for the wrong reason.

### 3.2 Executed results

The three tests are part of the collected suite (they run inside the full-tree runs quoted below, which is where
their pass/fail is recorded). Full-tree baseline on the scratch database at head `c4d8e2a91f60`:

```text
791 passed, 0 failed (745s)          → runs/backend-baseline-2026-11-24.log
```

and the final re-run after the MP-06 test changes is `runs/backend-final-2026-11-24.log` (§4).

### 3.3 Mutation check — the tests are not vacuous

For **B (the day)**, the defect was reinstated in `display.py` and the DQDS file run against it: **2 failed,
24 passed**, the two failures being exactly the two operational-day tests, with the board publishing the *server*
day's token (`assert 'F-023' == 'F-024'`). The file was restored byte-identically
(SHA-256 `3F9FD047…95E73`). Full output: `runs/evidence-mp06-mutation.log`; the MP-06 report quotes it in full.

For **A (the scope)**, the assertion is differential by construction: the same `AuthContext` returns `True` for
`demo-dr-002` and `False` for `demo-dr-001`. A test that passed on a broken seed would have to return `True` for
both, which it does not — and the `psql` read-back plus the live 200/404 in §4 confirm the two branches are
really different.

---

## 4. Verification evidence

| Criterion | Status | Evidence |
|---|---|---|
| Seed writes `staff_doctor_assignments` | **IMPLEMENTED** | `DEMO_STAFF_DOCTOR_ASSIGNMENTS` + `_seed_staff_doctor_assignments()` |
| Re-running the seed is idempotent | **IMPLEMENTED** + **TESTED** | existing-row / re-activate branches; the seeded test asserts exactly one row per account after seeding |
| Seed uses the facility day | **IMPLEMENTED** + **TESTED** | `_demo_today()`; pinned-clock test; AST guard |
| Rows actually exist in the database | **VERIFIED** | `psql` read-back on the scratch DB at `127.0.0.1:55432`: `assistant\|demo-dr-002\|active\|demo-org-001` and `doctor\|demo-dr-002\|active\|demo-org-001` |
| Doctor login reaches its own queue | **VERIFIED** | `runs/evidence-mp05-verification.log` — `doctor … doctor_id=demo-dr-002 -> HTTP 200 waiting=3 doctor='Dr. Kamal Hossain'` |
| Assistant login reaches the same queue | **VERIFIED** | same log — `assistant … doctor_id=demo-dr-002 -> HTTP 200 waiting=3` |
| Cross-doctor queue fails closed | **VERIFIED** | same log — `doctor_id=demo-dr-001 -> HTTP 404` for **both** accounts (non-disclosing, per the 404-not-403 rule) |
| Full backend suite passes | **TESTED** | baseline `791 passed, 0 failed (745s)`; final post-change run **`796 passed, 0 failed (816.87s)`** → `runs/backend-final-2026-11-24.log` (791 + 5 new tests: this file's 3 and MP-06's 2) |
| Live demo database re-seeded | **NOT DONE — BLOCKED** | see §5.1 |

The verification script is `runs/verify_mp05_demo_doctor_scope.py`: it mints a JWT for the *seeded* account
(id, org, branch, role, 30-minute expiry — no credential is typed, read or printed), then calls
`GET /api/v1/queue?doctor_id=…&date=<facility day>` through the app's own `TestClient`. It lives outside the suite
deliberately: it is the second, independent artefact the evidence vocabulary requires, and it asserts nothing —
it prints what the server answered. (The captured log also carries one Starlette `httpx` deprecation warning on
stderr; it is noise from the test client, not from the application.)


---

## 5. Known limitations and remaining gaps

### 5.1 The live demo database has not been re-seeded — BLOCKED, not skipped

The fix repairs the **seed script**. It does not, and must not on its own, rewrite an existing environment:
re-running `seed_demo.py` against the live database is a state-changing production action (it truncates in
`RESET_ORDER` order and regenerates patients/appointments). It is also **explicitly forbidden by this plan's own
Amendment A-2**, §E.5: *"Do not restore or reseed the live database. The rehearsal already happened against a
disposable copy; restoring production is not authorised by any document."* This host additionally has no
container access to the deployment and no live DB credential in `.env.local`.

Consequence, stated plainly: **until the live database is re-seeded by an owner-authorised operation, its
`staff_doctor_assignments` table is still empty for the demo accounts and the live doctor login still reaches no
queue.** Everything in §4 was verified on a scratch database seeded with this code.

This also bears on **RBAC-R3 "demo assignment"**, which Appendix E.6 lists as *UNPROVEN — needs a seeded-data
check*. The check now exists and passes (§4), but on the scratch database only; the live instance remains
unproven, and E.5 forbids the action that would prove it. Recorded as an owner-gated operational action in the
execution register, not as a task an agent may perform.

### 5.2 The two fixes are verified differently, and the difference matters

- **Scope (A)** is verified end-to-end: rows read back with `psql`, then a real HTTP call with a real token.
- **Day (B)** is verified on a *pinned clock*: a scratch database seeded at 11:00 local cannot distinguish
  `operational_today()` from `date.today()`, because on this host today they agree. What proves the fix is the
  injected-instant unit test (§3.1) plus the AST guard, not the live seed. The live proof arrives the first time
  a seed is run inside the 00:00–06:00 Dhaka window, or by moving `AMSDP_FACILITY_TZ` — neither was performed.

### 5.3 The seed's timezone resolution

`_demo_today()` → `operational_today(session, org)` → `facility_zone()` reads `organizations.timezone`, which
`DEMO_ORG` seeds as `Asia/Dhaka` (`seed_demo.py:51`); the environment variable and `DEFAULT_TZ` are only
fallbacks for an unreadable or unknown column. So the demo's day is data, not configuration — which is what BR §8
requires, and what makes the MP-06 board agreement possible.

### 5.4 Scope granted is deliberately minimal

Only `demo-dr-002` (Dr. Kamal Hossain, General Medicine) is assigned. That is the demo's doctor persona; the
other eight demo doctors have no staff account, and asking for their queue returns **404** by design. Anyone
extending the demo to a second doctor persona must add the assignment explicitly — the seed will not infer it
from `staff_users.doctor_id` (that column is legacy and deliberately *not* trusted at request time).

### 5.5 What this report does not claim

No browser session, no deployed-environment check, and no claim that the demo's scripting/credentials documents
were updated — they were read only where needed and are owner-controlled (`.clinerules` §11). No credential,
password or token value appears in this report or in the verification script's output.

---

## 6. Governance and Skill Compliance

| Item | Detail |
|---|---|
| Governing documents read | `.clinerules` §1–§12; the plan §6 (MP-05 row), §7 (definition of done), §8, Appendix D (D.1, D.3, D.6, D.8, D.9 and D.4 rule 11 — the facility-day rule); `docs/governance/AMSDP_Docs_Index_V1.0.md`; `docs/product/AMSDP_Business_Rules_V1.0.md` §7–§8 (scope and facility day); `backend/common/auth.py` (`_load_assigned_doctor_ids`, `AuthContext`); `backend/common/timeutil.py`; `backend/seed/seed_demo.py` |
| Skills | **None installed** (`.clinerules` §5 verified). Governance documents used; no skill use claimed |
| D1 code scope | One file (`seed_demo.py`) plus one new test file. No auth change, no model change, no migration |
| D2 server-side enforcement | The fix *restores* server-side enforcement rather than weakening it: scope comes from the assignment table, and the legacy column is still refused |
| D3 tenancy | Assignments carry `organization_id` = the demo org; the doctor lookup is filtered by `Doctor.organization_id == DEMO_ORG["id"]`, so a doctor id from another tenant cannot be assigned |
| D4 audit | No audit event is written by a seed; the seed prints each action. The **404** on cross-doctor access is the existing recorded denial path, unchanged |
| D5 migration | None required — `staff_doctor_assignments` already exists (migration `f8a1b2c3d4e5`); the seed was simply not using it |
| D6 tests | Pinned-clock behavioural test, AST structural guard, authorisation-outcome test; all executed in the full-tree runs |
| D7 execution | `psql` read-back, `pytest`, and a live `TestClient` call — outputs quoted, logs under `runs/` |
| D8 runtime | Live demo environment **NOT** verified and the re-seed **NOT** performed (§5.1). Stated as BLOCKED, not as done |
| D9 report | This file, under `docs/implementation/`, with this section |
| Non-negotiables | No secret, password or JWT material quoted or logged; the 404-not-403 rule preserved and demonstrated; no second tenant column introduced; nothing hidden in the UI presented as authorisation |

**Report placement.** `docs/implementation/` per `.clinerules` §11. No move or rename → no migration-manifest
entry; the docs index is updated in the same task (§12).

