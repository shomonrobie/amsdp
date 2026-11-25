# AMSDP — MP-16 Implementation Report: blocked periods

> **Task ID:** `AMSDP-MP-16-BLOCKED-PERIODS-2026-11-24`
> **Plan task:** **MP-16 — Blocked periods** (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-D), **P1**, depends on *nothing*
> **Requirement:** **BR §15** (schedule configuration must support "breaks and unavailable periods" and "blocked dates and periods"; availability is validated when an appointment is saved) and **MVP Scope** ("Support schedule blocking for unavailable periods"; "Blocked periods cannot be booked unless an explicitly authorized exception is supported by the approved rules")
> **Plan acceptance:** *"a blocked period cannot be booked unless an authorised exception is used; `available-slots` degrades without error"*
> **Status:** **TESTED** — code exists, is reachable, and its tests pass in this tree. Not VERIFIED in the `.clinerules` §7 sense beyond the executed API/DB artefacts quoted in §4 (no browser, no live server in this environment).
> **Report location:** `docs/implementation/` (`docs/` is the single authoritative documentation tree, `.clinerules` §11)
> **Date:** 2026-11-24

---

## 1. Requirement

BR §15 is short and specific:

> Schedules are internal to authorized facility users. […] Schedule configuration should support: Working days and start/end times. **Breaks and unavailable periods.** Appointment duration for time-slot models. Serial capacity for serial models. Hybrid rules. **Blocked dates and periods.** Facility defaults with permitted doctor/branch overrides.
> **Validate availability and capacity when an appointment is saved, not only when the form is opened.**

MVP Scope adds the acceptance sentence quoted in the header, and the plan's MP-16 row reduces both to two
observable outcomes: a blocked period **cannot be booked** unless an authorised exception is used, and
`available-slots` **degrades without error**.

### 1.1 What the code did before this task

**Nothing.** The capability the plan calls "confirm absence, then implement" was confirmed absent, in four
independent places:

| Evidence | Result |
|---|---|
| `backend/common/models.py` | no table, no column, no relationship for a block (the only `Schedule`-adjacent model is `ScheduleSession`, which is *recurring* availability, not an exception) |
| `backend/scheduling/` | no route, no schema, no validation (`main.py`, `sessions.py`) |
| `backend/appointment/main.py` | no guard: `_guard_slot` checked published hours and capacity, never an unavailability record |
| gap audit `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | **GAP-12 / F-20: "Blocked periods unverified — absent from scheduling and appointment modules"**, BR §15 |

A blocked period was therefore not merely unenforced, it was **unrepresentable**: there was no way to record
"Dr. Rahman is on leave on 20 April", so no test could assert anything about one.

### 1.2 Design decisions, and why

1. **A table, not `organizations.config`.** MP-10 could keep the walk-in policy in the existing JSON configuration
   block because a policy is a small scalar set. A block is *dated business data*: queried per doctor **and per
   day** on every availability read and every booking, listed per schedule, cancelled individually, each row
   carrying its own actor and reason. Filtering a JSON array on that path would defeat every index.
2. **Enforced per doctor, not per schedule row.** A block is stored against one `schedule` (provenance and
   scoping) but matched by `doctor_id` + date. A doctor working two branches, or holding two schedule rows, is
   unavailable in both — the safe direction, and what "the doctor is unavailable" means. Consequence recorded in
   §5: a block created at branch A also covers branch B that day.
3. **Cancel, never delete.** `DELETE` sets `status='cancelled'` with the actor and the reason. `.clinerules` §3
   (append-only audit) and the tree's own convention (nothing is deleted) both require it.
4. **The authorised exception is gated on `schedule.manage`, not on a new capability.** BR §15 says an *authorised*
   exception must exist but does not name a capability, and inventing one would either widen `DELEGABLE_CAPABILITIES`
   (a security-surface change) or add a privilege nobody has. `schedule.manage` is the authority that **creates** a
   block; using it to override one keeps the principle "whoever can close availability can re-open it", and it is
   held by super/org/branch administrators only — a receptionist or doctor is refused **403**. Whether the front
   desk should be able to *receive* a delegated exception is an open product question, recorded in §5.
5. **The reason is mandatory in both directions.** A block needs a reason (≥3 characters) and so does an override;
   both are audited. A configuration change with no stated reason cannot be reviewed later (BR §13.6).
6. **Degrade closed, never raise.** A stored row whose window cannot be parsed (`"9:00"`) covers the whole day
   rather than turning `available-slots` into a 500. The failure mode is "refused a slot that might have been
   free", never "booked into a block" — the same rule `common/slots.py` follows for templates (F-14).


---

## 2. Change

Seven files, one migration, two new test modules. No existing behaviour was removed and no other task's code was
refactored.

| File | Change |
|---|---|
| `backend/common/models.py` | **new** `ScheduleBlock` (`schedule_blocks`): org, branch, schedule, doctor, inclusive `start_date`/`end_date`, optional `start_time`/`end_time` (both NULL = whole day), `reason`, `status`, creator, cancellation actor/time/reason; `CHECK (end_date >= start_date)`; three indexes (`idx_block_doctor` for the availability/booking path, `idx_block_schedule` for the schedule's list, `idx_block_org`) |
| `backend/alembic/versions/b2e5c7d91a04_add_schedule_blocks.py` | **new** forward-only, idempotent revision on head `c4d8e2a91f60`; creates only when absent; no existing object touched |
| `backend/common/schedule_blocks.py` | **new** pure helper module: `normalise_window` → `whole_day` / `window` / `malformed`, `window_label`, `covers_date`, `covers` (overlap, fail-closed), `first_covering`. No database, no FastAPI, no policy — the single definition both services share |
| `backend/scheduling/blocks.py` | **new** router: `POST /api/v1/schedules/{id}/blocks` (201), `GET …/blocks` (`date_from`, `date_to`, `include_cancelled`), `DELETE …/blocks/{block_id}` (cancel, keep the row); audit `schedule.blocked` / `schedule.block_cancelled` with before/after; `schedule.manage` to write, authenticated branch-scoped staff to read |
| `backend/scheduling/main.py` | mounts the router; `available-slots` reads the doctor's active blocks for the day and publishes each slot with `blocked: true` and **zero** availability, plus `blocked_periods` (id + window label, **no reason text**) and `blocked_slot_count` |
| `backend/appointment/main.py` | **new** `_guard_blocked()`; called by create, reschedule and transfer after `_guard_slot` using the slot window the booking actually consumes; `override_block` on `AppointmentCreate` / `AppointmentReschedule` / `AppointmentTransfer`, gated on `schedule.manage` with a mandatory reason and audited as `appointment.block_override` |
| `backend/tests/amsdp_test_support.py` | `purge_org` deletes `schedule_blocks` before the schedules it references (test isolation, not product code) |

**Refusal vocabulary.** A plain booking inside a block answers **422** with a stable prefix —
`blocked_period: the doctor is unavailable for a blocked period covering 2026-04-20–2026-04-20 (09:00–09:30) …`.
**403** is reserved for the unauthorised *override* attempt (`schedule.manage` missing), so a caller can tell
"the rule refused me" from "you may not ask for that". **404** is untouched: a schedule in another tenant or
another branch is indistinguishable from one that does not exist.

---

## 3. Tests

### 3.1 New tests

| Module | Tests | What they pin down |
|---|---|---|
| `backend/scheduling/tests/test_schedule_blocks.py` | **35** | create (whole-day / windowed / multi-day, defaults, audit row with actor and reason); validation (reason required and ≥3 chars, half a window, inverted window, unpadded clock, inverted dates, impossible date, 366-day bound); tenancy (cross-tenant 404 **and nothing written**, other-branch administrator 404, org-admin allowed, receptionist 403, doctor 403, unknown schedule 404); list (ordering, overlap filter, inverted query range, cancelled hidden by default and shown on request, cross-tenant 404); cancel (row kept, audit before/after, double cancel 422, unknown 404, receptionist 403); availability (blocked slots publish `available: 0` + `blocked: true`, whole-day blocks everything, another day unaffected, cancelled block inert, block covers the doctor across two schedules, another doctor unaffected, a stable payload shape on an out-of-range day, unreadable window degrades to whole-day **without a 500**) |
| `backend/appointment/tests/test_blocked_booking.py` | **16** | booking refused (`blocked_period`, nothing written; 09:07 into a 09:00–09:15 blocked slot refused; whole-day refuses every time); no over-refusal (outside the window, touching the boundary, another day, another doctor, cancelled block); override (403 without the capability, 422 without a reason, allowed → 201 **and** an `appointment.block_override` audit row carrying the block id, the window and the reason; an override flag on an unblocked hour writes no exception record); reschedule (into a block refused **and the original visit untouched** — proving the guard is inside the move's transaction; outside the block succeeds; override with a reason succeeds and is audited; front-desk override 403) |

Both modules use the shared `amsdp_test_support` fixtures (real Postgres, real JWT, real routes) like every other

### 3.2 Executed results

Every command below was run in this window against the real database
(`postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp`); the outputs are quoted, not summarised.

**Targeted suites — the two services MP-16 touches:**

```
python -m pytest scheduling appointment -q
279 passed, 5 warnings in 297.60s (0:04:57)
```

279 = the 51 new tests (35 scheduling + 16 appointment) **plus** the pre-existing scheduling and appointment
suites, all green — which is the point: the availability payload gained keys and the booking guard gained a
step, and nothing that already depended on either regressed.

**Mutation check — the tests are not vacuous:**

| Step | Result |
|---|---|
| Baseline SHA-256 of `backend/common/schedule_blocks.py` | `691413D8…6FFC0332` |
| Mutation applied: `covers()` returns `False` for a windowed block (whole-day blocks still block) | — |
| `pytest scheduling/tests/test_schedule_blocks.py appointment/tests/test_blocked_booking.py -q` | **7 failed, 44 passed** in 73.06s |
| Tests that caught it | `test_blocked_slots_publish_zero_availability`, `test_block_covers_the_doctor_not_only_one_schedule`, `test_booking_inside_a_blocked_window_is_refused`, `test_a_blocked_slot_is_measured_as_a_window_not_a_minute`, `test_override_books_and_is_audited`, `test_reschedule_into_a_blocked_window_is_refused`, `test_reschedule_override_with_a_reason_succeeds` |
| Mutation reverted; SHA-256 re-checked | `691413D8…6FFC0332` — **byte-identical** |

The mutation is caught on **both** sides of the shared helper (the scheduling read *and* the appointment write
guard), which is the property the design depends on: one definition, two consumers, each independently pinned.

**Whole backend suite:** see §4 — the result is quoted there together with the full command.

### 3.3 What the tests deliberately do *not* claim

- No test asserts anything about a **UI**: the blueprint's `[Block Time]` control is not part of MP-16's
  acceptance cell, and no page renders `blocked` yet (§5).
- No test covers the **walk-in arrival** path, because MP-16 does not change it (§5 records the decision).
- The scheduling suite inserts a deliberately corrupt block row **directly** (`start_time="9:00"`) to prove the
  read degrades; that is the only place a test bypasses an API, and it is the only way to simulate a hand-edited row.


---

## 4. Verification evidence

### 4.1 The migration is not a claim — it was upgraded twice, on two databases

D5 requires "one forward-only, idempotent Alembic revision on head `c4d8e2a91f60`; upgrade verified on a scratch
database".

| Evidence | Output |
|---|---|
| Dev database (`amsdp`) | `Running upgrade c4d8e2a91f60 -> b2e5c7d91a04, add_schedule_blocks` then `alembic current` → `b2e5c7d91a04 (head)` |
| **Scratch** database (`amsdp_mp16_scratch`, created empty in this window) | the **whole chain** ran from the first revision to head, ending `Running upgrade c4d8e2a91f60 -> b2e5c7d91a04, add_schedule_blocks`; `alembic current` → `b2e5c7d91a04 (head)` |
| Idempotency | a second `alembic upgrade head` on the scratch database executed **0** revisions |
| What actually exists (read back from `pg_catalog`, not from the migration source) | 16 columns; indexes `idx_block_doctor`, `idx_block_org`, `idx_block_schedule`, `schedule_blocks_pkey`; constraints `ck_block_dates_ordered`, `schedule_blocks_pkey`, and the four foreign keys (`organization_id`, `branch_id`, `schedule_id`, `doctor_id`) |
| Main DB after the tests | `alembic_version` = `b2e5c7d91a04`; the same 16 columns and 6 constraints |

No existing table, column, constraint or row was modified by the revision; it creates one table and three indexes
only when they are absent.

### 4.2 What "degrade without error" means, demonstrated

`test_unreadable_window_degrades_without_error` writes a block row with `start_time="9:00"` (unpadded, therefore
unreadable) straight into the database and asserts that `GET /available-slots` answers **200** with every slot
marked `blocked` and the block's label reading `all day (unreadable window)`. Before this task such a request had
nothing to read; with a naive implementation it would have raised a 500 on `int("9:00")` — the F-14 failure mode
`common/slots.py` was written to prevent.

### 4.3 Evidence vocabulary (`.clinerules` §7)

- **IMPLEMENTED** — the table, the migration, the three routes, the availability projection, the create/reschedule/
  transfer guard and the override audit all exist and are reachable through the service routers.
- **TESTED** — 51 new tests pass in this tree, in both services, and the whole backend suite is quoted below.
- **VERIFIED** — **partially**: the artefacts here are live API responses through the application (FastAPI
  `TestClient`, real Postgres, real JWTs) and direct database reads of the audit and schema state. There is **no
  browser run and no live server** in this environment, so D8's "browser or API artefact from the running stack"
  is met at the API level and **not** at the UI level; no screenshot, no recorded walkthrough, no claim of one.
- **ACCEPTED** — not claimed. The Product Owner has not signed MP-16.


### 4.4 The whole backend suite

```
python -m pytest -q            # from backend/, real Postgres
898 passed, 82 warnings in 638.45s (0:10:38)
```

898 = **847** (the whole-tree figure recorded at MP-10) **+ 51** new tests, exactly. No test was removed, renamed
away, skipped or marked xfail to make this green, and no existing assertion was relaxed: the availability payload
gained keys (`blocked`, `blocked_periods`, `blocked_slot_count`) and every pre-existing availability test still
passes unchanged. Output: `runs/backend-mp16-2026-11-24.log`.

---

## 5. Known limitations and remaining gaps

Stated so that nothing here is mistaken for delivered scope. None of these blocks MP-16's acceptance cell; three of
them are decisions the Product Owner may want to take.

1. **No user interface.** The service publishes `blocked` and `blocked_periods` per slot; no page renders them and
   the Blueprint's `[Block Time]` control (`docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md:343`) is **not**
   implemented. Verified: the frontend has **no** consumer of `available-slots` today, so nothing regressed — but
   staff create and cancel blocks through the API only. A block-management screen is new work, not a silent
   extension of MP-16's cell.
2. **Walk-in arrivals are not refused.** `POST /api/v1/appointments/walk-in` registers an *arrival* through the
   MP-10 placement policy; MP-16 refuses **bookings**. A patient who presents during a blocked period is an
   operational judgement for the desk. Extending the rule to arrivals is a product decision (it would also need a
   rule for what happens to the arrival's placement).
3. **Check-in during a block is allowed.** The visit was booked before the block existed; refusing check-in would
   strand the patient. This is BR §13.7 (new settings apply prospectively; history is not rewritten) applied to a
   blocked period.
4. **A block is doctor-wide, not branch-scoped** (§1.2 item 2). "Unavailable at branch A but working at branch B"
   cannot be expressed. If that is needed it is a different rule and needs a decision, not a wider column.
5. **Override authority is `schedule.manage` and is not delegable.** A branch administrator (or a holder of the
   `schedule.*` namespace) can override; a receptionist or doctor cannot, and `DELEGABLE_CAPABILITIES` — a
   deliberately closed list — was **not** widened. Whether the front desk should be able to *receive* that
   exception is open.
6. **One reason field on a move.** A reschedule/transfer that also overrides a block records its single `reason` in
   both audit rows (`appointment.rescheduled`/`transfer` and `appointment.block_override`). Splitting them needs a
   request-schema change.
7. **No recurring or exclusion rules.** No public holidays, no "every Monday", no per-room blocks. Each block is a
   date range (≤366 days). BR §15 names none of the former, and inventing them silently would be policy.
8. **Overlapping blocks are permitted** and simply union. Harmless; documented rather than "fixed" with a rule
   nobody asked for.
9. **Frontend suite state is unchanged** — the two known red modules (Q-3) were not touched by this window and are
   still red for the reasons recorded in the register.
10. **MP-11 / Q-6 is deferred, not done.** The owner chose option (c) on 2026-11-24: MP-11 waits for a queue model
    that supports room-scoped numbering, the BR §31.1/§52 requirement stays outstanding, and `doctor_branches.room_id`
    is explicitly **not** accepted as a proxy. No schema column was added for numbering in this window.


---

## 6. Governance and Skill Compliance

*(Required by `.clinerules` §6.)*

### 6.1 Documents read and applied (`.clinerules` §4 routing)

| Domain row applied | Documents read **in this session** | How their instructions changed the work |
|---|---|---|
| Database schema, migrations, indexes, data integrity | `.clinerules` §§3, 11, 12; `docs/governance/AMSDP_Docs_Index_V1.0.md`; plan §7 D5 and §8 rule 3; the head revision `c4d8e2a91f60`; `saas-multitenant-data.md` as adapted (governance assessment §3) | one forward-only, idempotent revision; additive only; `organization_id` as the only tenant key; a `CHECK` and three indexes chosen for the queries the code actually runs; the migration's docstring states why this is a table and not configuration |
| Backend API / service endpoints | `.clinerules` §3; BR §13 (configuration governance), §15 (schedules), §56 (configurable decisions); MVP Scope ("Support schedule blocking…", "Blocked periods cannot be booked unless an explicitly authorized exception…"); plan MP-16 row | the acceptance cell's two outcomes, nothing more: refusal **and** degrade-without-error; reasons mandatory; every configuration change audited (BR §13.6); no invented policy |
| Authentication, RBAC | BR §7–§8 via the existing matrix; `backend/common/permissions.py` read (not modified); `DELEGABLE_CAPABILITIES` left closed | write = `schedule.manage`; read = authenticated + branch-scoped; the override reuses `schedule.manage` instead of inventing a capability or widening the delegable list |
| Multi-tenant data, org/branch isolation | `.clinerules` §3 non-negotiables; `backend/common/auth.py` (`branch_accessible`) | organization always from the token (the block body has **no** organization field at all); cross-tenant and cross-branch both **404**; tests assert that nothing is written |
| Audit / data integrity | `.clinerules` §3 (append-only, denials recorded); BR §40–§41 via the existing `record_audit` / `install_denial_audit` | `schedule.blocked`, `schedule.block_cancelled` with before/after; `appointment.block_override` in the booking's own transaction; blocks are cancelled, never deleted; the availability read omits free-text reasons (minimisation) |
| Documentation placement | `.clinerules` §11, §12; Docs Index | this report written to `docs/implementation/`; no `ai_factory/docs/` writes; register and index updated in the same task; no file moved, so no manifest entry is due |

### 6.2 Skills

**No skill package is installed in this workspace** (verified previously: no `.clinerules/skills/`, no
`.claude/skills/`, no repo `skills/`). Per `.clinerules` §4 the governance documents above were used instead, and
**no skill was claimed**. No new skill was installed (that needs owner approval).

### 6.3 Non-negotiables — checked one by one

| Rule | Evidence |
|---|---|
| No secrets logged or exposed | no new configuration, token or credential is read or written; nothing secret appears in the audit payloads (test asserts the payload's shape, not any credential) |
| The UI is never the safety boundary | there is no UI in this change; every refusal is server-side (`_guard_blocked`, `require_permission`, `branch_accessible`) |
| Principal's org/branch from the token | `BlockCreate` carries no organization field; `scoped_schedule` filters `organization_id == auth.organization_id`, then `branch_accessible` |
| Cross-tenant/cross-branch → 404, never 403 | `test_another_tenant_schedule_is_a_non_disclosing_404`, `test_another_branch_administrator_gets_a_404`, `test_other_tenant_cannot_list` |
| `organization_id` is the only tenant key | the new table's only tenant column is `organization_id`; no second tenant column exists |
| Audit append-only | blocks are cancelled (`status='cancelled'`), the row is kept, and the test asserts `count() == 1` after cancellation |
| Denials recorded | the scheduling and appointment apps already install `install_denial_audit`, so the 403/404/422 answers from these routes reach the trail through the existing middleware |
| Forward-only, idempotent migration | §4.1 — applied twice, on two databases, second run a no-op |
| Never claim an unverified capability | §4.3 — API/DB evidence only; no browser, no live-server claim; the `[Block Time]` UI declared absent in §5 item 1 |

### 6.4 Definition of Done (plan §7.2) — gate by gate

| Gate | Requirement | Evidence in this task |
|---|---|---|
| **D1 — Code** | implements the named requirement only | the diff adds the block feature (model, migration, shared helper, router, availability projection, booking guard) and one line in test support; no unrelated refactor, no formatting sweep, no dependency added |
| **D2 — Server-side enforcement** | every action authorised server-side with the existing helpers | `require_permission("schedule.manage")` on create/cancel; `_require_capability(auth, "schedule.manage", …)` on all three override paths; reads through `branch_accessible`. The UI is not involved at all |
| **D3 — Tenancy** | every query scoped by org (and branch); 404 on violation | `scoped_schedule` (org → branch → 404), `_scoped_block` (org + schedule), `_guard_blocked` (org + doctor). Four tests assert 404 **and** that nothing was written |
| **D4 — Audit** | every BR §40 state change audited with actor, org, branch, before/after, reason | `schedule.blocked` (after + reason), `schedule.block_cancelled` (before/after + reason), `appointment.block_override` (block, target, reason, same transaction). Three tests read the rows back |
| **D5 — Migration** | one forward-only, idempotent revision on head `c4d8e2a91f60`; scratch upgrade; no data loss | §4.1 — `b2e5c7d91a04`, whole chain on an empty scratch database, second run a no-op, schema read back from `pg_catalog` |
| **D6 — Tests** | unit/integration tests for the rule **including the negative path** | 51 tests; the negatives are the majority: refusals, 403/404/422, double cancel, cross-tenant, cross-branch, over-refusal guards |
| **D7 — Execution** | new tests **and** surrounding suite executed, output quoted | §3.2 (279 passed for the two services), §3.3 (mutation, 7 failed), §4.4 (whole backend suite) |
| **D8 — Runtime evidence** | browser or API artefact from the running stack, or BLOCKED naming the missing capability | API-level artefacts through the application against real Postgres, quoted in §3.2; **no browser and no live server exist in this environment**, so D8 is met at the API level only and that limitation is stated (§4.3) |
| **D9 — Report** | report under `docs/implementation/` with §6 compliance | this document |

### 6.5 Deviations, exceptions and unresolved issues

- **No deviation from the plan.** MP-16's acceptance cell is met as written; no task outside MP-16 was performed.
- **Two design decisions inside the plan's scope**, both recorded in §1.2 and escalated as open questions rather
  than settled policy: doctor-level (not branch-level) enforcement, and `schedule.manage` (not a new/delegable
  capability) as the override authority.
- **§8 rule 6 (no parallel edits to shared files) respected:** `appointment/main.py` is a collision hotspot shared
  with MP-13/MP-14/MP-15, all of which are gated or not started, so no coordination was required.
- **Unresolved:** §5 items 1–10. Items 2, 4 and 5 would change behaviour and need an owner decision before anyone
  implements them.

---

## 7. Artefacts produced in this window

| Artefact | Path |
|---|---|
| Report (this file) | `docs/implementation/AMSDP_MP-16_Blocked_Periods_Report_V1.0.md` |
| Implementation | `backend/common/models.py`, `backend/common/schedule_blocks.py`, `backend/scheduling/blocks.py`, `backend/scheduling/main.py`, `backend/appointment/main.py` |
| Migration | `backend/alembic/versions/b2e5c7d91a04_add_schedule_blocks.py` |
| Tests | `backend/scheduling/tests/test_schedule_blocks.py` (35), `backend/appointment/tests/test_blocked_booking.py` (16), `backend/tests/amsdp_test_support.py` (purge) |
| Executed evidence | `runs/backend-mp16-appt-sched.log` (279 passed), `runs/backend-mp16-mutation.log` (7 failed / 44 passed under mutation), `runs/backend-mp16-2026-11-24.log` (whole backend suite) |
| Execution state | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §2 (MP-16 row), §4 (Q-6 resolved), §7 (next eligible work), §8 (change log) |
| Navigation | `docs/governance/AMSDP_Docs_Index_V1.0.md` — MP-16 annex |
| Database | `amsdp_mp16_scratch` (created for D5; disposable, left in place so the chain can be re-verified) |

Nothing was moved, renamed or deleted; no migration-manifest entry is due (`.clinerules` §11). No
Product-Owner-controlled document was modified.


suite in the tree; nothing is mocked at the service boundary.
