# AMSDP — Sequence 4 Acceptance Verification Report

**Sequence:** 4 — end-to-end acceptance verification of the MVP workflows, plus
repair of the defects that verification exposed
**Date:** 2026-11-10 (facility-local; UTC still 2026-11-09 when the run started)
**Tree:** `/home/shomonrobie/amsdp`, branch `hackathon-mvp`, uncommitted working tree
**Status:** **IMPLEMENTED + TESTED + VERIFIED** for the three defects found and
fixed in this sequence. Full suite: **177 passed, 7 skipped, 0 failed**.
Live end-to-end run against eight isolated services: **64/64 workflow assertions
passed** (reproduced on every run, §3). ACCEPTED is **not** claimed —
that is a product-owner act. No commit, no push, no merge, no deploy was performed.

---

## 1. Scope and objective

Sequence 4 verified, against running services rather than unit fixtures, that the
five product workflows behave as `docs/product/AMSDP_Business_Rules_V1.0.md`
requires end to end:

* **A** organization → branch → staff → doctor → schedule setup,
* **B** scheduled appointment with capacity enforcement and check-in,
* **C** walk-in registration and enqueueing,
* **D** live queue operation (call → consult → complete, missed turn, recovery),
* **E** cancellation and rescheduling,
* **F** cross-tenant isolation and non-disclosure.

The run was driven by a purpose-written workflow script against the **isolated**
database `amsdp_seq4_test` (port 5433) with the eight backend services bound to
ports 8110–8117 — never the development database, never the compose stack.

Verification found three defects that the passing unit suites could not see. All
three are fixed, each with a regression test that fails on the pre-fix code
(mutation-checked, §5.3).

Explicitly out of scope: new features, schema changes (none were required —
`alembic check` reports no drift), deployment, AILI changes, commits.

## 2. Governance and skill compliance

Selected per `.clinerules` §4 routing table:

| Domain | Governance document applied | Skill |
|---|---|---|
| Backend API / service endpoints | `saas-application-security.md` (adapted), Business Rules Parts II–X | none installed |
| Auth / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py` | none installed |
| Multi-tenant data | `saas-multitenant-data.md` (adapted), Business Rules §4–6, `common/auth.py` scope helpers | none installed |
| Queue / scheduling / workflow transitions / tokens | Business Rules Parts V–VII (§24–§31), `saas-api-throttling.md` (concurrency, adapted), M4/M5 reports | none installed |
| Database schema / migrations | `saas-multitenant-data.md` §4–5, `saas-cicd-workflow.md` §3 (adapted), Alembic chain | none installed |
| Audit / data integrity / reporting | `saas-observability.md` (adapted — redaction + denial recording), `common/audit.py`, Business Rules Part X | none installed |
| Reporting (operational dates) | Business Rules §8 (facility time zone + UTC timestamps) | none installed |
| Docker / deployment | `saas-cicd-workflow.md` (adapted, honest CI state), `docker-compose.yml` | none installed |
| LLM / agent tooling | §8 routing policy — not exercised, no model call was made | none installed |

**Skills: NONE available.** Re-checked this session: no `.clinerules/skills/`,
no `.claude/skills/`, no repo `skills/` directory. The governance documents above
were used instead; **no skill usage is claimed** (§5 of `.clinerules`).

Non-negotiables actually exercised and evidenced:

* tenant key stays `organization_id`; every query scoped by it (§3, §4);
* cross-tenant/cross-branch access fails closed with **404** — Workflow F
  recorded six refusals, all 404, byte-identical to the unknown-id response;
* denials are audited, never swallowed (check-in now writes the `queue.checkin`
  audit event, §4.2);
* history/audit is append-only: the fixes *add* entries and never rewrite them;
* no schema change without a migration — none was needed (§5.4);
* no claim of unverified capability: every number in this report is a re-runnable
  command in §5 and §6.

## 3. What the acceptance run established (Workflow A–F)

Script: `/tmp/wp2_workflows.py` (verification harness, not product code).
Result: `SUMMARY 64/64 workflow assertions passed`, reproduced on five consecutive
full runs after the fixes (`/tmp/wp4_run.txt` … `/tmp/wp8_run.txt`; the last one on
the final code, which the figures below come from). Representative evidence:

| Workflow | Evidence recorded by the run |
|---|---|
| A | org + branch + admin + receptionist + doctor(+staff account) + schedule created; each login returned 200 |
| B | slot capacity 2 enforced — the 3rd booking in the same slot returned `422 capacity exceeded for this time slot (unreserved capacity 2)`; check-in returned 200; a duplicate queue check-in returned `422 appointment is already queued`; the board then showed `token=T-822D11-001 status=waiting source=appointment` |
| C | walk-in appointment + enqueue: the same board then held 2 entries — `T-822D11-001` (appointment, pos 1) and `T-822D11-002` (walk-in, pos 2) — with distinct tokens for one doctor/day |
| D | call → start → complete on the scheduled entry; missed turn then recovery on the walk-in entry; **3** status-history rows persisted `['waiting','skipped','waiting']` (this is the assertion SEQ4-HISTORY-P0 broke); token unchanged across the recovery (`before=T-822D11-002 after=T-822D11-002`) |
| E | cancel with reason → `CANCELLED` with `history_len=2`, original still traceable; reschedule → new appointment `3c026040…` linked to original `c9106fb9…`, which is marked `RESCHEDULED` |
| F | six cross-tenant reads/writes (patient read + write, doctor read, queue mutation, organization read, audit read) all refused with **404**; the foreign-404 body `{"detail":"Not Found"}` is byte-identical to the unknown-id body; tenant B data unmodified (`200`) |

Independently re-read from the database after the run (§6), which is what turns
"the API said so" into VERIFIED.

## 4. Defects found by the run and repaired

### 4.1 SEQ4-HISTORY-P0 — history writes were silently dropped (data integrity)

**Symptom.** Workflow D expected three status-history rows after
`waiting → skipped → waiting`; the API returned three, the database held one.
Workflow E expected two rows on cancel; the database held one.

**Root cause.** Every history mutation used the in-place-reflex pattern:

```python
h = row.status_history or []      # h IS the committed Python list
h.append({...})
row.status_history = h            # ... assigned back, so nothing is dirty
```

SQLAlchemy's attribute history therefore reports *unchanged*, the JSON column is
omitted from the `UPDATE`, and the row keeps only the entries it was created
with. The response was built from the mutated Python object, so it showed the
full list while the database kept one — which is why the unit suites, which
asserted on responses, stayed green.

**Fix.** Every append now copies first (`h = list(row.status_history or [])`) and
then assigns the new list, so the attribute is dirty by identity. Applied to
every mutation site: appointment status transition, cancel, both reschedule
endpoints, the appointment-history append inside queue check-in, queue
call/start/complete, missed turn, recovery and reorder. The comment
`# list(...) copy: mutating the loaded JSON list in place leaves SQLAlchemy
nothing to persist (finding SEQ4-HISTORY-P0)` marks each site.

**Dependents.** BR §18 traceability, Workflow D step 6 ("the system records the
change history"), Workflow E step 4, the Sequence 3 recovery audit trail.

**Regression tests** (`backend/tests/test_sequence4.py`,
`TestAppointmentHistoryPersists`, `TestQueueHistoryPersists`, 5 tests). They
assert the value read back **from a fresh session**, not from the response — the
distinction that hid the bug.

### 4.2 SEQ4-TOKEN-P1 — two token authorities, duplicate live tokens (P1)

**Symptom.** In the acceptance run, a walk-in enqueued after a scheduled
check-in was issued `T-<DOC>-001` a second time: two **active** queue entries
sharing one token for the same doctor and day — a patient-identification hazard
on the doctor queue display and on printed slips.

**Root cause.** Two different counters for one rule (BR §24–§31: one token per
patient per doctor per day):

* `POST /api/v1/queue/enqueue` and `/queue/check-in` allocated through the atomic
  `queue_sequences` row;
* `POST /api/v1/appointments/{id}/check-in` allocated `count(*) + 1` over
  `queue_entries` — a counter that a walk-in never advances.

That check-in also bypassed the queue service's history rows and the
`queue.checkin` audit event.


**Fix.**

* `backend/common/queue_tokens.py` — the single authority:
  `allocate_daily_token(session, doctor_id, day)` (`INSERT … ON CONFLICT … DO
  UPDATE … RETURNING`, so concurrent check-ins cannot collide) and `token_for()`
  for display. The module docstring records the finding.
* `backend/queuing/main.py` — `_next_sequence` / `_token_for` delegate to it, and
  the queue refuses a second *active* entry for the same appointment
  (`422 appointment is already queued`) instead of minting a second token.
* `backend/appointment/main.py` — check-in allocates from the same authority,
  writes `status_history`, `position_history` and the `queue.checkin` audit
  event, and fails closed: an exception rolls the whole thing back (503) rather
  than leaving the appointment checked in with no queue entry. The unreachable
  `T-…` token stub that followed `finally:` was removed, and the booking-time
  `_serial_token()` formatter now delegates to `token_for()` instead of repeating
  the token layout a second time.
* Check-in is now **idempotent**: a second check-in of an already
  `CHECKED_IN`/`IN_QUEUE` appointment returns the existing entry instead of
  `422 cannot transition from CHECKED_IN to CHECKED_IN`, and never creates a
  second entry.

**Regression tests** (`TestSingleTokenAuthority`, 4 tests): appointment check-in
followed by a walk-in yields distinct tokens; the appointment's serial equals
`queue_sequences.last_value` (the shared counter, not a row count, decided it);
history + `queue.checkin` audit exist; a repeated check-in yields exactly one
entry.

### 4.3 SEQ4-TZ-P1 — two "todays" in one visit (P2)

**Symptom.** At 2026-11-10 00:11 facility time (UTC+6) the UTC date was still
2026-11-09. `POST /api/v1/appointments/walk-in` stamped the appointment with the
**UTC** date while the queue stamped its entry with the **facility-local** date:
one visit, two days, and the visit invisible to the board and the dashboard for
one of them.

**Root cause.** `appointment/main.py` and `appointment/dashboard.py` used
`datetime.now(timezone.utc).date()`; `queuing/main.py` used `date.today()`. BR §8
requires the facility's configured time zone for operational dates (UTC only for
stored timestamps), and the platform already has that fact in a column —
`organizations.timezone`, which the Sequence 3 notification planner formats
against — but no operational path consulted it.

**Fix.** `backend/common/timeutil.py` — `facility_zone(session, organization_id)`
resolves the org's own zone, then `AMSDP_FACILITY_TZ`, then `DEFAULT_TZ`
(`Asia/Dhaka`), so the answer never depends on the container's `TZ`; plus
`operational_today(session, organization_id)` and `utc_timestamp()`, with finding
SEQ4-TZ-P1 documented in the module. Applied to the walk-in appointment, the
`/dashboard/today` aggregate, the queue board's default day and the queue
service's enqueue default — each now passes its own session and org id. Stored
timestamps remain UTC, as BR §8 requires.

**Regression tests** (`TestOperationalDate`, 2 tests): a walk-in appointment and
its queue entry carry the same facility day, and a freshly enqueued entry is
visible on the board for that day. `TestFacilityZone` (2 tests) additionally
asserts that the resolved zone actually comes from `organizations.timezone`
(`Pacific/Kiritimati` for a probe org) and that an unknown zone name falls back
to `DEFAULT_TZ` instead of raising.

### 4.4 Test-isolation defect found while fixing the above

`backend/tests/test_dashboard.py` cleaned up with org-blind
`s.query(Appointment).delete()`, which aborts the whole module with a
`ForeignKeyViolation` once any other suite has issued a PQT `tracking_tokens`
row for a fixture appointment. The fixture now deletes only its own org's rows in
FK-safe order (tracking tokens → queue entries → appointments → audit events),
and its "today" is `operational_today()`, matching the service. Test hygiene
only; product behaviour is unchanged.


## 5. Test evidence

### 5.1 Whole backend suite

```
cd backend && ../.venv/bin/python -m pytest -q -p no:cacheprovider
177 passed, 7 skipped, 23 warnings in 32.43s     (exit 0)
```

The 7 skips are the declared legacy modules (`LEGACY-TESTS-P1`: in-memory
fixtures removed, rewrite pending). No test was skipped, weakened or deleted to
make this run pass.

### 5.2 Focused suites

| Suite | Result |
|---|---|
| `tests/test_sequence4.py` | 13 passed (11 regression + 2 zone-resolution) |
| `queuing/tests/test_queue.py` | 20 passed |
| `tests/test_dashboard.py` | 6 passed |

### 5.3 Mutation checks — the new tests actually catch the bugs

Each fix was reverted in the working file, the targeted tests re-run, the file
restored and its SHA-1 verified identical to the pre-mutation state:

| Mutation | Observed result |
|---|---|
| check-in allocates `count(*) + 1` again | **2 failed, 2 passed** — `test_appointment_check_in_then_walk_in_keeps_tokens_unique`, `test_appointment_check_in_allocates_from_the_shared_counter` |
| walk-in reverts to `datetime.now(timezone.utc).date()` | **1 failed, 1 passed** — `test_walk_in_appointment_and_entry_share_the_facility_day` |
| queue history reverts to `entry.status_history or []` | **1 failed, 1 passed** — `test_action_appends_and_persists` |
| `facility_zone` ignores the organization and uses `DEFAULT_TZ` | **1 failed, 1 passed** — `test_operational_date_follows_the_organization_time_zone` |

`sha1sum -c` reported `OK` after every restore. The full suite was re-run after
the final restore: **177 passed** (above), so the tree is byte-identical to the
verified state.

### 5.4 No schema change was required

```
cd backend && AMSDP_DATABASE_URL=…@127.0.0.1:5433/amsdp_seq4_test \
  ../.venv/bin/python -m alembic check
No new upgrade operations detected.        (RC=0)
```

`queue_sequences` already existed with `UNIQUE (doctor_id, date)`, so the token
authority needed no migration. No forward-only migration was authored, and no
schema was modified by hand.

## 6. Independent database verification (VERIFIED, not just TESTED)

Read straight from `amsdp_seq4_test` after the final live run — not from an API
response:

```
local today 2026-11-10 | utc today 2026-11-09          <- the exact TZ hazard window
walk-ins 2026-11-09  n=5  created 15:27Z .. 18:03Z      <- all pre-fix
walk-ins 2026-11-10  n=5  created 20:20Z .. 20:54Z      <- all post-fix
duplicate live tokens per doctor/day (whole DB): none
queue_sequences vs entries:  doctor 666becad  last_value=2  entries=2
                             doctor 2f20ffc1  last_value=2  entries=2
                             doctor bb312a59  last_value=2  entries=2
orphan rows left by the test suite: 0
```

* Every post-fix walk-in was created between 20:20Z and 20:54Z on UTC
  **2026-11-09** (02:20–02:54 facility time) yet is filed under the facility day
  **2026-11-10**; the five 2026-11-09 rows are the pre-fix ones — the defect and
  its repair side by side in one table.
* Counter and entries agree exactly for every doctor/day: no burned serials, no
  shared tokens, and no two active entries anywhere in the database carry the
  same token.
* The suite leaves no probe rows behind (`tz-probe-*` organizations: 0).

Unauthenticated access, re-checked against the same running services:

```
8111/api/v1/orgs 8111/api/v1/orgs/x/branches 8112/api/v1/patients
8113/api/v1/doctors 8114/api/v1/schedules 8115/api/v1/appointments
8115/api/v1/dashboard/today 8116/api/v1/queue 8117/api/v1/audit/events
  -> all 401
8116/api/public/queue/board/<unknown-branch-uuid>  -> 404
```

Nine protected endpoints refuse with `401`, the public display endpoint does not
disclose whether the branch exists, and **no endpoint returned `403`** (§3
non-negotiable: cross-tenant failure is a non-disclosing 404).

## 7. Open findings and known limitations (not fixed here)

| Id | Finding | Impact | Disposition |
|---|---|---|---|
| SEQ4-DEPLOY-D1 | `backend/app/main.py` is a 10-line "Hello World" stub — there is no aggregated backend app | `docker compose up` cannot serve `/api/v1/...` through one backend entry point; the per-service images are the real runtime (what the acceptance run used) | product-owner / deployment decision (M8–M9 territory) |
| SEQ4-DEPLOY-D2 | `docker-compose.yml` has exactly **1** healthcheck (the database); the eight services and the frontend have none | `depends_on` gives no application-tier start-order guarantee | deployment hardening |
| SEQ4-CORS-D1 | no `CORSMiddleware` anywhere in `backend/`; the frontend works only because Next.js proxies `/api/*` via `rewrites` | a directly-hosted frontend origin would be blocked by the browser | deployment hardening |
| SEQ4-THROTTLE-D1 | login-throttling state is per-process (documented at `identity/main.py`) | ineffective across replicas | deployment hardening |
| SEQ4-INDEX-P3 | `tracking_tokens` carries a plain index redundant with its unique constraint (`common/models.py`) | harmless write cost | future revision |
| SEQ4-TZ-P3 | resolving `organizations.timezone` needs `zoneinfo` data in the image; a tzdata-less base image would fall back to the container zone (the code never raises) | silently wrong facility day in such an image | verify `tzdata` in the service images (deployment) |
| LEGACY-TESTS-P1 | 7 legacy in-memory test modules are skipped | they assert nothing today; no coverage regression vs. their old fixtures, but no coverage either | rewrite |

None of these affects the five workflows verified in §3; all are runtime/deployment
breadth rather than workflow correctness.

## 8. Deviations, exceptions and unresolved issues

* **`.clinerules` §9 (write code only; yield after two files).** This sequence *is*
  a verification task, so the suites and the eight services were executed, and the
  three fixes legitimately span more than two files (appointment, queuing,
  dashboard, two new `common/` modules, tests). Recorded as a deliberate,
  task-scoped deviation, not an unnoticed one.
* **Services were restarted** to load the fixed code before the final live run; the
  64/64 run and the §6 database probe were produced from the current tree.
* **The harness is outside the repo.** `/tmp/wp2_start.sh` and
  `/tmp/wp2_workflows.py` are verification scaffolding and are **not** proposed for
  commit.
* **Isolated database.** All acceptance work ran against `amsdp_seq4_test` on port
  5433 with services on 8110–8117; the development database and the compose stack
  were untouched.
* **No commit, push, merge or deploy** was performed. The working tree also carries
  other sequences' uncommitted work; it was not reformatted, stashed or reset
  (`.clinerules` §9: no destructive Git adjustments).
* **A first TZ fix was narrower than the platform.** `operational_today()` began
  as "the process-local date", and both the module docstring and this report said
  the MVP had no per-organization time-zone column. Checking
  `common/models.py` disproved that — `organizations.timezone` exists and the
  Sequence 3 notification planner already formats against it — so the helper was
  rewritten to resolve the organization's own zone and the wrong statement was
  removed from the code and from this report. Recorded because a stale
  justification in a docstring is itself a defect.
* **Unresolved (needs a decision, not a patch):** SEQ4-DEPLOY-D1, SEQ4-DEPLOY-D2,
  SEQ4-CORS-D1, SEQ4-THROTTLE-D1, SEQ4-INDEX-P3, SEQ4-TZ-P3, LEGACY-TESTS-P1 (§7).

## 9. Evidence standard (`.clinerules` §7)

| Claim | Level | Basis |
|---|---|---|
| History is really persisted | **VERIFIED** | fresh-session DB reads in §5.2 + live run `['waiting','skipped','waiting']` in §3 |
| One token per patient/doctor/day | **VERIFIED** | whole-DB duplicate scan and counter-vs-entries probe, §6 |
| One operational day per visit | **VERIFIED** | walk-in filed under the facility day inside the UTC-behind window, §6 |
| Cross-tenant access fails closed at 404 | **VERIFIED** | six live refusals + identical-body comparison (§3 F), plus §6 |
| Check-in is idempotent | **TESTED** | `test_repeat_check_in_is_idempotent` (mutation-checked, §5.3) |
| Facility day follows the organization's zone | **TESTED** | `TestFacilityZone` (mutation-checked, §5.3) |
| Whole backend suite green | **TESTED** | 177 passed / 7 skipped / 0 failed, §5.1 |
| No schema drift | **VERIFIED** | `alembic check` RC=0, §5.4 |
| `docker compose up` serves the API | **NOT CLAIMED** | SEQ4-DEPLOY-D1, §7 |
| Product acceptance | **NOT CLAIMED** | product-owner act |

## 10. Files changed in this sequence

Product code:

* `backend/common/timeutil.py` *(new)* — `facility_zone()` (organization →
  `AMSDP_FACILITY_TZ` → `DEFAULT_TZ` → process zone), `operational_today()`,
  `utc_timestamp()`; BR §8 rule and SEQ4-TZ-P1 documented in the module.
* `backend/common/queue_tokens.py` — the single token authority
  (`allocate_daily_token`, `token_for`) with SEQ4-TOKEN-P1 documented.
* `backend/appointment/main.py` — history appends copy before mutation; walk-in
  resolves the day from the caller's organization; check-in goes through the token
  authority with history, `queue.checkin` audit, fail-closed error handling and
  idempotency; dead token stub removed.
* `backend/appointment/dashboard.py` — `/dashboard/today` uses the caller's
  facility day.
* `backend/queuing/main.py` — history appends copy before mutation; enqueue/board
  default day resolves the caller's facility zone; sequence allocation delegates
  to `common.queue_tokens`.

Tests:

* `backend/tests/test_sequence4.py` *(new)* — 13 tests across
  `TestAppointmentHistoryPersists`, `TestQueueHistoryPersists`,
  `TestOperationalDate`, `TestSingleTokenAuthority`, `TestFacilityZone`; asserts
  on fresh-session database reads, not responses.
* `backend/queuing/tests/test_queue.py` — fixture dates and the board query use
  the facility day (they were pinned to the UTC date).
* `backend/tests/test_dashboard.py` — facility day, org-scoped FK-safe cleanup.

Verification scaffolding (not committed): `/tmp/wp2_start.sh`,
`/tmp/wp2_workflows.py`, `/tmp/wp2_run`–`/tmp/wp8_run.txt`, `/tmp/probe5.txt`–
`/tmp/probe12.txt`, `/tmp/mut1.txt`–`/tmp/mut5.txt`.

Repository note: `backend/common/` and several `backend/tests/` modules are still
**untracked** in this tree (`git status` shows `?? backend/common/`), because the
package was created inside this sequence series and nothing has been committed.
`git diff --stat` therefore reports only the tracked service files; the verified
state of the untracked files is the state on disk, listed above.

