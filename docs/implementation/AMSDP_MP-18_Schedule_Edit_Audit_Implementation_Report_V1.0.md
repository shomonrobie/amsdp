# AMSDP — MP-18 Schedule-Edit Audit Implementation Report V1.0

**Work package:** MP-18 — *schedule-edit audit — verify, implement if absent*, **P2**, depends on MP-02 (satisfied).
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).
**Authoritative scope:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` row MP-18, acceptance
**1.0** — *"any schedule write produces an audit row with before/after; no silent schedule mutation remains."*
**Where written:** `docs/implementation/` (`.clinerules` §11). New file; nothing was moved, renamed or deleted, so
no migration-manifest entry is required.

---

## 1. What the plan said, and what the code actually had

MP-18 is a **verify-then-implement** task: the register already noted that the `schedule.created` /
`schedule.updated` / `schedule.capacity_change` events with before/after existed, so the first job was to read every
write path in the scheduling service rather than assume the task was satisfied.

The verification found **one real silent mutation**, and it was not in the code the plan named:

| Write path | Audit before this window | Verdict |
|---|---|---|
| `POST /api/v1/schedules` | `schedule.created`, payload `after` | Covered |
| `PATCH /api/v1/schedules/{id}` | `schedule.updated` (`before`+`after`) **plus** `schedule.status_change`, `schedule.effective_dates_changed`, `schedule.templates_changed`, `schedule.capacity_change` when the relevant values moved | Covered — this is the owner decision Q5 work already shipped |
| `POST /api/v1/schedules/{id}/sessions` | `schedule.session.create` (`after`) | **Gap** — see below |
| `PATCH /api/v1/sessions/{id}` | `schedule.session.update` (`before`+`after`) + `schedule.session.capacity_change` | **Gap** — see below |
| `DELETE /api/v1/sessions/{id}` | `schedule.session.retire` (`before`+`after`) | **Gap** — see below |
| `POST /api/v1/schedules/{id}/blocks` | `schedule.blocked` (`after`, with the reason) | Covered (MP-16) |
| `DELETE /api/v1/schedules/{id}/blocks/{id}` | `schedule.block_cancelled` (`before`+`after`, actor, reason) | Covered (MP-16) |

### The gap: a session write also rewrites the schedule, silently

`scheduling/sessions.py::sync_slot_templates` rebuilds `schedules.slot_templates` from the active
`ScheduleSession` rows, and it is called on **every** session create, edit and retire. That list is not a cache of
the sessions — it is the projection `GET /api/v1/schedules/{id}/available-slots` and the appointment calendar read
(the module's own docstring says "a session must never be persisted without it").

So each of those three endpoints changed a **`schedules` row** while the trail recorded only a
`schedule_session` event. An auditor asking "who changed this doctor's published hours, and what were they
before?" could not answer it from `schedule.*` events at all: the schedule's hours had moved with no `schedule.*`
row. That is precisely MP-18's *"no silent schedule mutation remains"*.

No other service writes `schedules` or `schedule_sessions` — searched the tree for `Schedule(`,
`ScheduleSession(` and `slot_templates =` outside `scheduling/`, tests and the demo seed; the only hits are the
model definitions in `common/models.py`. The demo seed is fixture data, not an API write path.

---

## 2. What was built

### 2.1 `scheduling/sessions.py` — the projection write is now an audited schedule change

| Addition | Purpose |
|---|---|
| `windows_map(templates)` | The `{"0 09:00-10:00": 1}` shape `schedule.templates_changed` carries, derived through `common.slots.normalise_template` so it cannot disagree with the schedule `PATCH`'s own `_capacity_map` |
| `audit_template_projection(session, schedule, auth, reason)` | Rebuilds the projection **and** records `schedule.templates_changed` against the **schedule's** id with `before`/`after` windows, when the published windows or their capacity actually moved |
| the three `sync_slot_templates(...)` call sites | Replaced by `audit_template_projection(..., "session created" / "session updated" / "session retired")` |

Two properties matter and are both tested (§4.1):

1. **It names the row that moved.** `target_type="schedule"`, `target_id=schedule.id` — not the session. Searching
   the trail for one schedule now returns its session-driven hour changes too.
2. **It only fires when the hours moved.** The comparison is on the *window map*, not on the raw JSON list: adding
   `session_id`/`room_id` to a template, re-chambering a session, or changing its slot duration leaves the
   published windows where they were, so no schedule event is written and the change is recorded once, on the
   session. An event that claims a change that did not happen is as unhelpful as one that is missing.

`windows_map` is defined locally rather than imported from `main.py` because `main.py` imports this module's router;
an import back would be circular. The shared derivation is `common.slots.normalise_template`, so the two maps are
the same function of the same input.

### 2.2 `scheduling/tests/test_schedule_audit.py` — four new behavioural tests (PostgreSQL)

Appended as `TestScheduleProjectionAudit`: session create, session move, session retire each produce exactly one
`schedule.templates_changed` on the schedule's id with the expected before/after windows and reason; and an edit
that does not move a window writes **no** schedule event while still recording `schedule.session.update`. The eight
existing tests in the module are unchanged.

### 2.3 `backend/tests/test_schedule_audit_coverage.py` — 13 tests that run without a database

The MP-18 acceptance criterion has two halves. "Every write produces an audit row with before/after" is behaviour
and is proven by the PostgreSQL tests above — which **cannot run on this host** (§4.3). "No silent schedule
mutation remains" is a property of the code's shape, and that half is checkable statically, so it is now a guard
rather than a promise:

| Test group | What it asserts |
|---|---|
| `windows_map` (5 tests) | The canonical key and capacity; the default capacity of 1; unusable templates are skipped (`end <= start`, an unparseable time such as `9:00`, a non-dict) exactly as every reader skips them; empty input is empty |
| `audit_template_projection` (3 tests) | A moved projection records **one** `schedule.templates_changed` naming the schedule, with the before/after windows, org, branch, actor and reason; an unchanged projection records nothing; retiring the last session reports the window disappearing |
| source guard (3 tests) | Every `POST`/`PUT`/`PATCH`/`DELETE` route in `scheduling/*.py` contains an audit call and passes `after=`; `sync_slot_templates` is called **only** from `audit_template_projection`; the helper itself passes `before`, `after`, `action` and `target_id` |

The guard is deliberately static, and §4.2 shows why the two guards are not redundant: reverting a session path to
a bare `sync_slot_templates` leaves the route's own `schedule.session.create` event in place, so the first guard is
satisfied and only the second one fails — which is the defect MP-18 exists for.

It cannot prove that an event carries the *right values*; that is the PostgreSQL tests' job, and this report does
not pretend otherwise.

---

## 3. Decisions taken, and why

| # | Decision | Why |
|---|---|---|
| D1 | The schedule-side event is `schedule.templates_changed`, the same action the schedule `PATCH` writes | One event name for one question ("did this doctor's hours move?") means one search, wherever the change was made. A new `schedule.projection_rebuilt` action would have hidden the change from the existing query |
| D2 | It targets the **schedule**, not the session | The row that changed is `schedules`. Targeting the session would keep the schedule's history incomplete |
| D3 | The event is written only when the *window map* changes | Comparing raw JSON would fire on a re-chambering or a duration tweak, producing "the hours changed" for a change that did not touch the hours. The map is also what the event carries, so the payload states the comparison that was made |
| D4 | `reason` names the cause (`session created` / `updated` / `retired`) | The generic field is what makes the two paths distinguishable in one query without a join |
| D5 | `windows_map` is local to `sessions.py` | `main.py` imports this module's router; importing `_capacity_map` back would be a cycle. The shared truth is `common.slots.normalise_template` |
| D6 | The existing eight audit tests and every shipped event were left untouched | They already assert the right values; MP-18's gap was a *missing* event, not a wrong one, and rewriting passing tests would have obscured that |
| D7 | A static guard was added rather than only more behavioural tests | The behavioural tests need PostgreSQL, which this host does not have. The guard runs here, fails on the exact regression (an unaudited write path), and costs no dependency |
| D8 | `PATCH /api/v1/schedules/{id}` keeps writing `schedule.updated` even when nothing changed | Out of MP-18's scope: a no-op audit row is noise, not a silent mutation. Recorded as an observation (§7, O-2) rather than changed here, because tightening it could alter existing clients' expectations |

---

## 4. Verification — what was actually run, and what it showed

Every number below is a run in this tree on 24 November 2026, Windows, `E:\amsdp`, from the repository root with
the project virtualenv (`.\.venv\Scripts\python.exe`).

### 4.1 The new module — **13 tests, executable without a database**

```
python -m pytest backend/tests/test_schedule_audit_coverage.py -q
13 passed in 1.89s
```

A first version of the `windows_map` test asserted that `"9:00"` canonicalises to `"09:00"`; it failed (`{}`), and
the failure was the *test* being wrong, not the code: `common.slots.to_minutes` accepts only zero-padded `HH:MM`,
so a template written as `9:00` is one that every reader skips. The test was corrected to assert that skip, and
`test_windows_map_drops_a_time_that_is_not_hhmm` now records the boundary.

### 4.2 Negative control — the guard catches the MP-18 defect, and the route guard alone would not

`create_session` was reverted to a bare `sync_slot_templates(session, schedule)` (the pre-MP-18 code), the module
was re-run, and the file was restored:

| Step | Result |
|---|---|
| Baseline | `13 passed in 1.57s` |
| Mutated (`create_session` calls `sync_slot_templates` directly) | **`1 failed, 12 passed in 2.05s`** — `test_the_projection_helper_is_the_only_caller_of_sync_slot_templates`, message: `sync_slot_templates changes schedules.slot_templates; call audit_template_projection instead: sessions.py::create_session` |
| Restored from a byte copy | SHA-256 `1541A5C8…1E33` **before and after**, and `13 passed` again |

The informative part is what did **not** fail: the route-level guard still passed, because `create_session` keeps
its own `schedule.session.create` event. A guard that only counted audit calls per route would therefore have
called the mutated code clean. That is exactly why the second guard exists, and the report states it rather than
presenting one mutation as proof of both.

### 4.3 The behavioural tests — written and collected, **not run**

| File | Tests | State |
|---|---:|---|
| `backend/scheduling/tests/test_schedule_audit.py` | **12** (8 existing + 4 new) | `12 tests collected in 1.81s`; **not executed** — every test opens a real session against PostgreSQL |
| `backend/tests/test_schedule_audit_coverage.py` | **13** | **Executed**, green (§4.1) |
| `backend/tests/test_doctor_mobile_policy.py` + `..._enforcement.py` (MP-17) | **29** | Re-ran together with the new module after the MP-18 edits: **`42 passed in 2.50s`** |

The environment is unchanged from MP-17 and MP-19: `Test-NetConnection 127.0.0.1 -Port 5433` → `False`, and
`pytest backend/tests/test_dqds.py --collect-only` dies with `sqlalchemy.exc.OperationalError`. No endpoint-level
test in this repository can run on this host, so the four new behavioural tests are recorded as **written and
collected, not run**.

### 4.4 Compilation

| Check | Result |
|---|---|
| `python -m py_compile backend/scheduling/sessions.py` | **exit 0** |
| `python -m py_compile backend/scheduling/tests/test_schedule_audit.py` | **exit 0** |
| `pytest --collect-only` on the behavioural module | **12 tests collected** — imports resolve, no connection attempted at import |
| The static guard parses all five `scheduling/*.py` modules with `ast` | green (§4.1) |

### 4.5 What is **not** verified here

| Claim | Status |
|---|---|
| Creating/moving/retiring a session writes a `schedule.templates_changed` row with the right windows, **end to end** | **NOT VERIFIED HERE** — the four behavioural tests need a database (§4.3) |
| Every existing schedule write still produces its before/after row after the change | **NOT VERIFIED HERE** — the eight pre-existing tests are also DB-backed; they are unrun, not passing |
| No write route in `scheduling/` can be added without an audit event | **TESTED** — the static guard, with the mutation in §4.2 as its negative control |
| The projection event is not noise (no event when the windows did not move) | **TESTED for the decision** (§4.1) and asserted end to end by the fourth behavioural test, unrun |

Nothing here promotes MP-18 to **VERIFIED**: the report has a static proof of shape and an executed proof of the
decision, but no independent observation of the stored audit rows.

---

## 5. Files touched

| File | Lines now | Change |
|---|---:|---|
| `backend/scheduling/sessions.py` | 663 | `windows_map`, `audit_template_projection`, `normalise_template` imported, and the three `sync_slot_templates` call sites replaced by the audited helper |
| `backend/scheduling/tests/test_schedule_audit.py` | 251 | **`TestScheduleProjectionAudit`** added — 4 behavioural tests, collected, **not run** (§4.3) |
| `backend/tests/test_schedule_audit_coverage.py` | 258 | **New** — 13 DB-free tests: the projection diff, the decision, and the source guard |

No schema change, no migration, no frontend file, no new dependency, and no change to an existing event name or
payload. One production file was mutated once for the negative control and restored from a byte copy — SHA-256
`1541A5C8…1E33` before and after (§4.2).

---

## 6. Governance and Skill Compliance (`.clinerules` §6)

### 6.1 Documents read and applied

| Domain routed (§4) | Document applied | How it shaped this work |
|---|---|---|
| Audit / data integrity / reporting | `saas-observability.md` (adapted, Assessment §3), Business Rules Part X, `backend/common/audit.py` | The whole task is that rule: every write leaves an append-only row with the values that moved. The new event names the row that changed and carries before/after |
| Queue / scheduling / workflow transitions | Business Rules Parts V–VII, `backend/scheduling/*` | The session→schedule projection is a scheduling invariant; the change was made in the module that owns it, not in the appointment reader |
| Backend API / service endpoints | `saas-application-security.md` (adapted) | No route, permission or payload changed; the existing `schedule.manage` / branch gates are untouched |
| Multi-tenant data | `saas-multitenant-data.md` (adapted) | The event carries the schedule's own `organization_id` and `branch_id`, both already scoped by the caller's token |
| Database schema / migrations | `saas-multitenant-data.md` §4–§5 (adapted) | No schema change, so no Alembic revision was written or applied |
| Documentation placement | `.clinerules` §11–§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | This report is in `docs/implementation/`; the index annex and the execution register were updated in the same window (§8) |

Step 1 of `.clinerules` §2 was followed literally for this task: **inspect before implementing**. The inspection —
every write path first, then a search for writers outside the service — is what showed the gap was in the session
projection and not in the `schedule.*` endpoints the register had already credited.

### 6.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5). No skill was claimed or simulated.

### 6.3 Non-negotiables (`§3`) — point by point

| Rule | Status here |
|---|---|
| Never log or expose secrets | The event payload holds schedule windows and capacity only — no token, credential or personal data |
| The UI is never the fallback safety boundary | No UI involved; the audit is written server-side inside the same transaction as the change |
| Access enforced server-side, principal from the token | Unchanged: `schedule.manage`, `require_branch_access`, `scoped_schedule` |
| Cross-tenant / cross-branch fails closed with **404** | Unchanged; the new event is written only after those checks passed |
| `organization_id` is the only tenant key | Unchanged; the event uses the schedule's own org id |
| Audit events are append-only; never deleted or rewritten | No delete or update path added; the new row is another append |
| Denials are recorded | Unchanged (`install_denial_audit`); this change affects allowed writes only |
| Forward-only idempotent migrations for schema change | No schema change, so no migration |
| Never claim unverified capability | §4.3/§4.5 state that the four behavioural tests were **not run**; the grade is `TESTED (static guard + decision) / behavioural unrun` |
| Do not use a tool/library merely because it was discovered | No dependency added; `ast` and `pytest` are already used by the suite |

### 6.4 Deviations and exceptions

1. **The end-to-end behaviour is not executed here.** No PostgreSQL on this host (§4.3) — the same environment gap as
   MP-17's and MP-19's O-1.
2. **One mutation, not a campaign.** §4.2 reverts one of the three call sites; the other two are guarded by the same
   static rule and were not individually mutated.
3. **The static guard is not behaviour.** It proves no write path is unaudited; it cannot prove the payload values.
   Stated in §2.3 and §4.5 rather than glossed.

---

## 7. Open items, and what should happen next

| # | Item | Effect | Suggested handling |
|---|---|---|---|
| **O-1** | The 12 tests in `scheduling/tests/test_schedule_audit.py` are **unrun** (§4.3) | The four new projection assertions and the eight pre-existing ones are unproven here | On a host with PostgreSQL: `python -m pytest backend/scheduling/tests -q`; if green, amend §4.5 and the register row to `TESTED` |
| **O-2** | `PATCH /api/v1/schedules/{id}` writes `schedule.updated` even when the body changes nothing (D8) | A no-op request leaves an audit row saying "updated" with identical before/after — noise an auditor has to read past | Not a silent mutation and not MP-18's criterion. If the owner wants parity with MP-19's diff discipline, it is a small separate change plus one test |
| **O-3** | The session→schedule projection is a *derived* list | A session edit is audited twice (session event + schedule event) when the windows move — deliberate, because two rows genuinely changed | None; recorded so a future reader does not mistake it for double-counting |
| **O-4** | Q-3's two pre-existing frontend reds are untouched | Unrelated to MP-18 (no frontend file changed) | Owner decision on the dataset hash; `pathToFileURL` for `calendar-render.test.mjs` |

**Next eligible work package.** **MP-22** (dashboard completion) is next among the non-gated tasks the register
names, followed by MP-25 (tracking hardening — needs MP-01), MP-28 (unify i18n) and MP-29 (responsive/touch/a11y).
The gated rows (MP-04, MP-09, MP-13, MP-21, MP-27, MP-30, MP-34) stay behind their owner decisions, and MP-24 /
MP-35…MP-40 stay behind MP-01/B-2.

---

## 8. Where this report is registered

- **Docs Index:** `docs/governance/AMSDP_Docs_Index_V1.0.md` — annex *"MP-18 schedule-edit audit report
  (2026-11-24)"* added with the file's byte size and line count, and the tree count updated **143 → 144**
  (measured).
- **Execution register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` — an **MP-18** row in §2 with
  the evidence quoted from §4 here, §6 listing the files touched, and §7's next-task line advanced to **MP-22**.
- **Nothing was moved, renamed or deleted**, so no migration-manifest entry was created and no version number was
  advanced.
