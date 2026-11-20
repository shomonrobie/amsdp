# AMSDP — Appointment & Calendar Reliability Remediation

> **Task ID:** `AMSDP-APPT-RELIABILITY-01`
> **Date:** 2026-11-19 · **Status:** implemented and tested; **nothing is ACCEPTED**
> **Input:** `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` (19 findings, F-01…F-19)
> **Scope:** Stage 1 → Stage 4 of that document's §9 roadmap, backend and frontend
> **Governed by:** `.clinerules` §1 (precedence), §3 (non-negotiables), §6 (compliance reporting),
> §7 (evidence standard), §9 (execution boundaries), §11 (output location), §12 (reading/registration)

---

## 1. What this report answers

The gap analysis read the appointment and scheduling services and recorded nineteen findings,
graded `CODE-READ`. This report is the remediation half: what was changed for each finding, what
proves it, what was deliberately **not** changed, and which owner decisions are still open.

It does not upgrade the analysis's grades by assertion. Each row of §4 carries its own evidence
grade from §7 of `.clinerules`:

* **IMPLEMENTED** — the code exists and is reachable from a route or a page.
* **TESTED** — a named test in this tree asserts it and passes.
* **VERIFIED** — an independent artefact (a build, a live call, a database read) confirms it.
* **ACCEPTED** — only the project owner can sign a row, and none is signed.

Two findings are closed only in part, and both say so in place: **F-01** (application-level lock
shipped; the database-level guarantee is owner decision Q2) and **F-18** (the consequence of an
outside-session booking is now stated in the dialog; marking it as *unscheduled* is a schema and
product decision that Q1 still gates). Nothing else is partially closed.

---

## 2. The change in one paragraph

The write path now resolves before it writes: the doctor must exist in the tenant (`_tenant_doctor`),
the appointment this actor may mutate is fetched with tenant, branch scope and a row lock in one
place (`_scoped_write_appointment`), the seat is charged to the **slot window** rather than to the
minute string (`_guard_slot` + `backend/common/slots.py`), and every lifecycle change goes through
one writer (`_apply_status_transition`) that no route can reach without having passed its permission
dependency. Configuration writes are validated and audited (`scheduling/main.py`), the availability
read and the write path share one definition of "this slot exists", and the calendar read has a
window bound. On the browser side the grid's slot expansion, day filter and effective-window test
now mirror the server, and the booking dialog says what a refusal means instead of pasting English
into a Bangla screen.

---

## 3. Files touched

| File | State | Why |
|---|---|---|
| `backend/common/slots.py` | **new** | The one slot arithmetic: parsing, defaults, normalisation, expansion, `slot_for`. Used by scheduling and appointment (F-02, F-03, F-14, F-15, F-16). |
| `backend/appointment/main.py` | modified | Stage 1 guards (`_tenant_doctor`, `_resolve_location` branch scope, `_scoped_write_appointment`, `_apply_status_transition`), Stage 2 capacity (`_lock_doctor`, `_guard_slot`, reschedule/transfer re-checks), Stage 4 window (`_calendar_window`). |
| `backend/scheduling/main.py` | modified | Template and effective-date validation on write, audit rows for create/update, `_optional_date`, availability read rebuilt on `common/slots.py` (F-12…F-16). |
| `backend/queuing/main.py` | modified | `POST /api/v1/queue/check-in` also requires `appointment.modify` — the second door into the lifecycle (F-07). |
| `backend/appointment/tests/test_appointment_reliability.py` | **new** | 28 tests, 7 classes — the regression suite for F-01…F-11, F-17. |
| `backend/scheduling/tests/test_scheduling.py` | modified | `TestSlotGridGuards` (8) and `TestScheduleWriteGuards` (10) for F-12…F-16. |
| `backend/appointment/tests/test_appointment_calendar_filters.py` | modified | Fixture now publishes a slot, because an unbounded/unpublished booking is no longer a legal one. |
| `frontend/lib/calendar/grid.js` | modified | `DEFAULT_SLOT_DURATION`/`MAX_SLOTS_PER_TEMPLATE` mirror the server, `expandTemplate` defaults to 15-minute slots, `scheduleCovers` mirrors `_date_covered`, `templatesForDate` honours status/window and treats a missing `day_of_week` as every day. |
| `frontend/lib/calendar/booking.js` | **new** | `freeSeats`, `seatsWord`, `refusalCode`, `REFUSAL_KEYS` — the booking dialog's two explanations (F-18, F-19). |
| `frontend/pages/appointments.js` | modified | Uses both modules; a refusal is translated, a nearly full slot is worded, an empty day explains its fallback. |
| `frontend/tests/calendar-grid.test.mjs` | modified | 3 new tests: slot-default parity, a legacy template with no weekday, effective-window gating. |
| `frontend/tests/appointment-booking-feedback.test.mjs` | **new** | 9 tests for F-18/F-19 and the module's purity. |
| `backend/tests/test_e2e.py` | modified | The end-to-end fixture declared a Monday template but booked a Wednesday and still expected twelve slots — it encoded the F-15 defect. It now declares the booking date's weekday (`2`). |
| `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` | modified | One header row added: its remediation outcome, pointing here. The analysis itself is unchanged. |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | modified | Revision 32: both documents registered, snapshot totals reconciled against `find docs -name '*.md'` (88 on disk, 86 registered), open item **O-3** for the two unregistered files of other workstreams. |

No migration was written, no schema was altered, and no existing document was modified. The
migration F-01's stronger answer needs is not in this change — see §7.


---

## 4. The nineteen findings, one by one

Grades: **I** = implemented, **T** = tested (`pytest` / `node --test`), **V** = verified by an
independent artefact. No row is ACCEPTED. Where a finding is closed only in part, the row says
which part and why.

| # | Sev | Change | Where | Regression test | Grade |
|---|---|---|---|---|---|
| **F-01** | High | Every write that claims a seat locks the doctor's row first (`_lock_doctor`), so count-then-insert and the `count(*) + 1` serial become atomic per doctor. **The database-level guarantee (partial unique index) is not added** — capacity-N templates legitimately share a slot start, so it needs owner decision **Q2**. | `appointment/main.py:386-402` (called from create, reschedule, walk-in, transfer) | `TestCapacityAtomicity::test_two_parallel_bookings_cannot_take_the_last_seat`, `::test_the_serial_number_is_allocated_once` | I·T |
| **F-02** | Medium | `start_time` is now `HH:MM` (422 otherwise), and a time the configuration does not publish is refused with `no_slot_covers_time: …` instead of silently getting capacity 1. The unconfigured-doctor fallback is kept deliberately (Q1). | `appointment/main.py:434-458`, `:545-551`; `common/slots.py:24,40-42` | `TestSlotWindowCapacity::test_a_malformed_time_is_refused`, `::test_an_off_template_time_is_refused` | I·T |
| **F-03** | High | The seat is charged to the **slot window** (`start_time >= window.start AND < window.end`), so 09:07 consumes the 09:00–09:15 seat instead of opening a new bucket. | `appointment/main.py:460-488`; `common/slots.py:140-182` | `TestSlotWindowCapacity::test_a_minute_inside_a_slot_consumes_that_slot`, `::test_the_neighbouring_slot_stays_bookable`, `::test_a_capacity_of_two_admits_two_and_refuses_the_third` | I·T |
| **F-04** | High | Reschedule re-resolves the chamber **and** re-checks capacity against the destination slot, excluding the row being moved. | `appointment/main.py:1021-1105` | `TestRescheduleCapacity` (3 tests) | I·T |
| **F-05** | High | `doctor_id` is resolved in the tenant before a booking is written; unknown and other-tenant ids both answer `404 doctor not found` (§3: non-disclosing). | `appointment/main.py:370-383`, used by create/walk-in/transfer | `TestTenantAndBranchScope::test_a_foreign_doctor_cannot_be_booked`, `::test_an_unknown_doctor_is_not_disclosed` | I·T |
| **F-06** | High | The schedule/session resolver only considers branches the caller may act on, so a booking cannot be filed into a branch the caller cannot read. Imposes the read side's scope on the write side; **whether a receptionist should book org-wide is owner decision Q4**. | `appointment/main.py:276-332` (branch filter at `:298-301`, `:319-323`) | `TestTenantAndBranchScope::test_a_schedule_in_another_branch_does_not_move_the_booking` | I·T |
| **F-07** | Critical | `check-in` declares `appointment.modify` and calls the shared transition writer instead of the status route function; the queue service's own check-in route now also requires `appointment.modify`. One transaction, so a failed queue allocation no longer leaves `CHECKED_IN` with no entry. | `appointment/main.py:506-533`, `:1112-1184`; `queuing/main.py` check-in route | `TestCheckInCapability` (4 tests) | I·T |
| **F-08** | High | Every mutation loads through `_scoped_write_appointment`: tenant filter, branch scope, `404` when either fails, and `SELECT … FOR UPDATE`. | `appointment/main.py:491-503` (used by status, cancel, reschedule, check-in, no-show, transfer) | `TestTenantAndBranchScope::test_a_cross_branch_appointment_is_invisible`, `::test_a_cross_branch_status_write_is_refused`, `::test_a_cross_branch_check_in_is_refused` | I·T |
| **F-09** | Medium | The detail read requires `appointment.read` and applies branch scope; out-of-scope is a bare `404`. | `appointment/main.py:953-973` | `TestTenantAndBranchScope::test_a_cross_branch_appointment_is_invisible` | I·T |
| **F-10** | Medium | A transfer's `new_branch_id` must exist in the tenant **and** be branch-accessible, else `404 branch not found`. | `appointment/main.py:1304-1312` | `TestTransferTarget::test_a_transfer_to_an_unknown_branch_is_refused`, `::test_a_transfer_to_an_out_of_scope_branch_is_refused` | I·T |
| **F-11** | Medium | One time is resolved once and both stored and snapshotted; the destination then obeys `_guard_slot`. | `appointment/main.py:1316-1340` | `TestTransferTarget::test_a_transfer_without_a_new_time_keeps_the_original_hour`, `::test_a_transfer_to_a_foreign_tenant_doctor_is_refused` | I·T |
| **F-12** | Medium | Schedule create and update write audit rows with before/after; the service now imports `record_audit`. | `scheduling/main.py` (`create_schedule`, `update_schedule`) | `TestScheduleWriteGuards::test_creating_a_schedule_writes_an_audit_row`, `::test_updating_a_schedule_writes_before_and_after` | I·T |
| **F-13** | Medium | Effective dates are parsed and validated (`_optional_date`), and an end before the start is refused — no longer swallowed. | `scheduling/main.py:118-133` | `TestScheduleWriteGuards::test_an_invalid_effective_date_is_refused`, `::test_an_end_before_the_start_is_refused` | I·T |
| **F-14** | Medium | Template contents are validated on write (time format, forwards window, duration ≥ 5, capacity ≥ 1, weekday 0–6) and normalised on read; a corrupt stored row is skipped, not a `500`. | `scheduling/main.py` (create/update validators); `common/slots.py:64-137` | `TestScheduleWriteGuards` (5 validation tests); `TestSlotGridGuards::test_a_corrupt_stored_template_is_skipped_not_a_500`, `::test_a_corrupt_template_does_not_hide_the_readable_ones` | I·T |
| **F-15** | Medium | `available-slots` honours weekday, schedule status and the effective window, and counts bookings per slot window — the same predicate the write path uses, with no `count()` per slot. | `scheduling/main.py` (`get_available_slots`) on `common/slots.py` | `TestSlotGridGuards::test_a_weekday_without_a_template_publishes_nothing`, `::test_an_inactive_schedule_publishes_nothing`, `::test_a_day_before_the_effective_window_publishes_nothing`, `::test_a_day_after_the_effective_window_publishes_nothing`, `::test_a_booking_inside_a_slot_window_occupies_that_slot` | I·T |
| **F-16** | Medium | One definition of a slot (`common/slots.py`) shared by scheduling and appointment, and re-implemented to match in the browser grid. | `common/slots.py`; `frontend/lib/calendar/grid.js` | `TestSlotGridGuards`; `calendar-grid.test.mjs` (slot-default parity, legacy template, effective-window gating) | I·T |
| **F-17** | Low | The calendar read is bounded: a default window when neither date is given, `422 date_range_too_wide` beyond the maximum span, and a single-day read keeps its meaning. | `appointment/main.py:673-712` | `TestCalendarWindow` (4 tests) | I·T |
| **F-18** | Low | The empty-day state no longer presents a free time as equivalent to a slot: it keeps the field (a documented walk-in fallback, Q1 open) and states that the time falls outside every slot and session and is counted one patient at a time. **The "mark it unscheduled so the grid shows it" half of the direction is not done** — it needs a stored field plus Q1 and Q3. | `frontend/pages/appointments.js` (empty-day branch); `frontend/lib/calendar/booking.js` | `appointment-booking-feedback.test.mjs::an empty day explains the fallback it offers (F-18)` | I·T |
| **F-19** | Low | A nearly full or full slot says so in words (`last seat`, `{n} left`, `Full`), and its tooltip gives capacity plus that wording; a refusal is mapped from the server's sentence or HTTP status to a translated caption with a next step, and an unrecognised answer says it is unrecognised instead of pasting English. | `frontend/lib/calendar/booking.js`; `frontend/pages/appointments.js` (`refusalText`, slot button) | `appointment-booking-feedback.test.mjs` (9 tests, incl. `every refusal the appointment service raises maps to one code` and `the booking dialog translates refusals instead of pasting the server sentence`) | I·T·V (build) |

---

## 5. Two behaviours a reader will notice, and why they are correct

**A `422` now says something a receptionist can act on.** `slot_full: …` names the slot window and
the free seats; `no_slot_covers_time: …` says the doctor publishes nothing covering that minute;
`no clinic session covers this time — book inside the doctor's session window` is unchanged in
wording but is now translated in the dialog instead of appended raw. The browser maps these to
Bangla/English captions (`booking.js::refusalCode`), and anything unrecognised becomes
"the server gave no reason — try again" rather than an English sentence inside a Bangla screen.

**A template without a `day_of_week` still applies to every day.** `templates_for_day` treats a
missing weekday as "every day", the grid now does the same, and one scheduling test pins it
(`TestSlotGridGuards::test_a_template_without_a_weekday_still_applies_to_every_day`). Closing a
doctor's published hours because a legacy row lacks a field would be the worse failure.

---

## 6. Governance and skill compliance (`.clinerules` §6)

**Documents consulted in this task.** `.clinerules` (always loaded) ·
`docs/governance/AMSDP_Docs_Index_V1.0.md` (read first, per §12, and updated by this task) ·
`docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` (the input, read in
full: findings, roadmap, decisions Q1–Q5) · the source and test files named in §3.

**Routing rows applied (§4 table).** Backend API/service endpoints · authentication, sessions,
RBAC (`common/permissions.py`, `common/auth.py` scope checks) · multi-tenant data (org/branch
isolation) · database schema **consulted but not changed** (no migration was written) · frontend
UI/components (`pages/appointments.js`, `components/AppointmentCalendar.js`, `lib/calendar/`) ·
audit/data integrity (`backend/common/audit.py`, denials) · documentation placement (§11) and
registration (§12).

**Skills.** The §5 registry records **no installed skill packages** in this workspace, so none was
used and none is claimed. The work was done against the governance documents and the existing code,
as §4 prescribes for a row with no skill.

**§3 non-negotiables, checked one by one.**

| Non-negotiable | How this change satisfies it |
|---|---|
| Access enforced server-side; identity from the token, never the body | Every new guard reads `auth` from the dependency; no branch or org is taken from a request body. `_tenant_doctor` and `_scoped_write_appointment` query with `auth.organization_id`. |
| Cross-tenant/cross-branch access fails closed with `404` | `_tenant_doctor`, `_scoped_write_appointment`, `get_appointment`, the transfer's branch check and the resolver's branch filter all answer `404`, never `403` and never a partial row. |
| The tenant key stays `organization_id` | No second tenant column was introduced; every new query filters on the existing key. |
| Audit trail append-only; denials recorded | Only `record_audit` inserts were added (scheduling create/update, status, transfer). Nothing deletes or rewrites an audit row; the existing denial audit is untouched. |
| Schema changes ship as forward-only idempotent migrations | **No schema change was made in this task**, so none is required. The one place a migration would be needed (F-01's partial unique index) is left to Q2 rather than slipped in. |
| Never claim an unverified capability | §8 lists exactly what was not run. F-01 and F-18 are recorded as partially closed rather than done. |
| No secrets in code, logs, docs or replies | No credential, token or DSN appears in this report, the tests or the diff. |

**Deviations, recorded rather than smoothed over.**

1. **F-01 is closed at the application level only.** `_lock_doctor` makes count-then-insert atomic
   per doctor; the database constraint that would make it true without the lock needs Q2.
2. **F-18 is closed at the message level only.** The dialog now states the consequence of a
   free-text time; it does not mark the booking as unscheduled, because that needs a stored field
   and Q1/Q3.
3. **Q3 and Q4 were answered by the code, not by the owner.** Check-in now requires
   `appointment.modify` (the Q3 "receptionist capability" branch) and writes are branch-scoped per
   the read side (the Q4 restriction). Both are the conservative reading of the existing read path
   and both narrow access rather than widen it — but they are owner rulings and are flagged in §7.
4. **Two test fixtures were corrected, not worked around.** `backend/tests/test_e2e.py` declared a
   Monday template and expected twelve slots on a Wednesday (the F-15 defect, encoded); it now
   declares the booking date's weekday. `test_appointment_calendar_filters.py` now publishes a slot
   because an unpublishable booking is no longer legal.
5. **`weekday` semantics** are Python's `date.weekday()` (Monday = 0) throughout, and the browser
   mirror uses the same convention via `Date.getDay()` → `(getDay()+6)%7`. That conversion is tested
   only through the pure grid functions, not in a browser (§8).


---

## 7. Open items and the decisions they need

| # | Item | Why it is not closed here | What closes it |
|---|---|---|---|
| **Q1** | Is a booking outside every published session a legitimate model, and what governs its capacity? | A product ruling. The code keeps the historical unconfigured fallback (capacity 1 per exact minute) and the dialog now *states* it (`noSlotsHint`). | An owner answer; then either a stored `is_unscheduled` flag (a migration) or removal of the fallback. |
| **Q2** | Which concurrency mechanism is authoritative: a partial unique index + `FOR UPDATE`, or serialisable transactions with retry? | Both satisfy BR §23.8; the choice changes the migration and its lock behaviour. `_lock_doctor` is the application-level answer, not a substitute for the constraint. | An owner answer, then one forward-only idempotent Alembic migration plus a concurrency test. |
| **Q3** | May a doctor check in their own patient, or is check-in a receptionist capability? | Implemented as `appointment.modify` on both doors — the conservative branch. If doctors are meant to check in, the matrix needs a capability that grants it. | Owner confirmation, or a new capability in `common/permissions.py`. |
| **Q4** | May a branch-scoped actor mutate an appointment in another branch of the same organization? | Implemented as "no": writes now match the read side's branch scope. If the intended policy is org-wide booking for receptionists, the resolver's branch filter (`appointment/main.py:298-301`) is the single place to revisit. | Owner confirmation. |
| **Q5** | Do schedule/capacity writes require an audit event? | Implemented as yes (F-12), on the `.clinerules` §3 reading that governed data changes are audited. | Owner confirmation that this is intended. |
| **O-1** | `doctor/tests/test_doctor.py` reuses hard-coded mobile numbers and never removes the doctors it creates, so once those numbers exist the file returns `409 a doctor with this mobile number already exists` and its search assertions then see extra rows. | Pre-existing and unrelated to this change: it fails on doctor creation, and no doctor code was touched. Fixing it means making the fixtures unique per run. | A small test-only change to `test_doctor.py` (`uniq()` mobiles), not staged by this task. |
| **O-2** | No browser run, no live API call, no container rebuild. | `.clinerules` §9 limits terminal work to what the change needs; this change is proven by tests and a production build, not by a running stack. | `_tools/amsdp_rebuild.sh` plus a short browser pass over the booking dialog (a full slot, a refused booking, a day with no session). |

---

## 8. Test and verification evidence (real results, nothing estimated)


**Backend, full suite** — `python3 /tmp/rt.py -q -p no:randomly` from the repository root (the
runner loads the gitignored `.env` into the process environment *without printing it*):

```
12 failed, 572 passed, 178 warnings in 657.50s (0:10:57)
```

All twelve are accounted for:

* **10 × `doctor/tests/test_doctor.py`** — `409 a doctor with this mobile number already exists` on
  the file's hard-coded mobile numbers (`01711111111`, `01722222222`), then cascading search
  assertions that see the extra rows. The file creates doctors and never removes them, so it passes
  only on a database that has not run it before. This is **O-1**, pre-existing, and no doctor code
  was touched by this change.
* **2 × `tests/test_e2e.py`** — `test_09_available_slots` returned 0 slots and
  `test_11_the_slot_is_now_taken` indexed an empty list. Cause, confirmed rather than guessed: the
  fixture declared `day_of_week: 0` (Monday) and booked `BOOKING_DATE = "2026-04-15"`, which is a
  **Wednesday** — previously it passed only because `available-slots` ignored the weekday (F-15).
  The fixture now declares the booking date's weekday.

**Backend, the affected subset after that correction** —
`python3 /tmp/rt.py -q -p no:randomly tests/test_e2e.py appointment/tests scheduling/tests queuing/tests`:

```
269 passed, 5 warnings in 545.17s (0:09:05)
```

That run includes the whole end-to-end workflow (schedule → twelve slots → book → slot now taken →
check-in → queue) and the new `test_appointment_reliability.py` (28 tests collected,
`--collect-only` verified).

**Frontend** — `cd frontend && npm test` (plain `node --test`, no dependency added):

```
ℹ tests 179
ℹ pass 179
ℹ fail 0
```

That total includes the 9 tests in the new `tests/appointment-booking-feedback.test.mjs` and the 3
added to `tests/calendar-grid.test.mjs`. Two of the 9 were red while this report was being written
(`no-show reason required`, `branch not found` were unmapped refusals) and were fixed by extending
the marker table, not by weakening the assertion — the transcript is in the task's scratch files.

**Frontend production build** — `cd frontend && npx next build`:

```
 ✓ Compiled successfully
 ✓ Generating static pages (8/8)
├ ƒ /appointments                         21.5 kB         142 kB
EXIT=0
```

This is the one independent artefact in the change: it proves the edited page and the new module
type-check and bundle, which the source-contract tests alone cannot show.

**Not run, and therefore not claimed:** no browser session, no live API call, no container rebuild,
no database read, and no second full-suite run after the end-to-end fixture correction. The ten
`test_doctor.py` failures above would still be present in a fresh full run; they are recorded rather
than papered over.

---

## 9. Registration and repository state

**Written by this task, both under `docs/`** (`.clinerules` §11): this report, and the index update
described below. No document was moved, renamed, overwritten or deleted, so no migration-manifest
entry is required.

**Index registration** (`.clinerules` §12). Two entries were owed and both are now in
`docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 32): this report under `implementation/`, and
`audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` — which the analysis task
created on 2026-11-19 and deliberately left unregistered because that task was read-only (its §12
says so and supplies the pending line).

**Two documents remain unregistered, and were left alone.** `find docs -name '*.md'` now counts 88
files against 86 registered rows: `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`
and `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` belong to other, still
uncommitted workstreams. `.clinerules` §11 says documents of uncertain ownership are reported and
left in place, so no row was invented for them; the drift is recorded in the index as open item
**O-3** rather than silently absorbed into the totals.

**Uncommitted work preserved.** The tree carried another workstream's changes before this task began
(`backend/common/auth.py`, `backend/identity/*`, `backend/tests/test_sequence3.py`,
`backend/queuing/tests/test_queue.py`, two `docs/` RBAC documents) plus one untracked document
(`docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`). None of
it was edited, reverted, staged or committed. `.clinerules` §9's rule was applied: files were checked
before staging, and only the paths this task changed were staged.

**Commit.** One commit, on top of `6d3acdf` (the RBAC workstream's commit), subject
`fix(appointment): reliability remediation F-01…F-19 of the gap analysis`, containing the fifteen
paths listed in §3 and this report itself — sixteen files, and nothing else. The nine entries of the
other workstream (`.clinerules` §9) are still uncommitted and were neither staged nor touched.
**Nothing was pushed**; no `git reset`, `git checkout`, `git stash` or `git clean` was run.

---

## 10. Follow-up (2026-11-19) — the owner decisions that closed F-01 and F-18

This report left two findings open because closing them required an owner decision rather than a
corrective change: **F-01** (capacity enforced only by an application count, no database
guarantee) and the *marking* half of **F-18** (an outside-session booking was accepted but was
not identified as such). Both are now closed by task `AMSDP-APPT-OWNER-DECISIONS-01`, together
with three further decisions taken in the same session:

| Finding | How it is now closed |
|---|---|
| **F-01** capacity integrity | `slot_allocations` with `UNIQUE (doctor_id, appointment_date, slot_key, seat_number)` and `UNIQUE (appointment_id)`, claimed under the existing doctor row lock and released by the single status writer. Application lock **and** database constraint, as the owner required. Migration `a9c4e1f7b2d8`. |
| **F-18** outside-session booking | `appointment_type` (`scheduled` / `walk_in` / `unscheduled`) is a persisted column, not a value inferred from a missing `start_time`; the override needs the `appointment.create_unscheduled` capability, a stated reason, the organization's daily limit, and writes its own audit event. |

Behavioural specification: `docs/architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md`.
Implementation report: `docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md`.

**Nothing in this report's §8 test evidence is invalidated by the follow-up work**: the nineteen
findings' tests still pass, and the suites listed there have grown (the follow-up adds 64 backend
tests across six new modules). Where a test name or count in §8 differs from the follow-up
report, the follow-up report is the later measurement.

