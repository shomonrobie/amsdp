# AMSDP — Appointment Types, Capacity Integrity and Capability Catalogue

> **Document ID:** `AMSDP_Appointment_Types_Capacity_and_Capability_Spec`
> **Version:** V1.0 · **Date:** 2026-11-19
> **Task ID:** `AMSDP-APPT-OWNER-DECISIONS-01` (owner decisions Q1, Q2, Q3, Q4, Q5)
> **Status:** describes the tree **as implemented and tested on 2026-11-19**; **nothing here is
> ACCEPTED** — see `.clinerules` §7 and the implementation report named in §13.
> **Nature of this document:** a behavioural specification of what the code and its tests do
> *today*. It is not a proposal, not a roadmap, and not an owner decision record. Where a
> statement is a *choice the owner made*, the decision is quoted; where it is an engineering
> detail, the file and symbol are cited so the statement can be checked against the tree.
> **Governed by:** `.clinerules` §1 (precedence), §3 (non-negotiables), §6 (compliance
> reporting), §7 (evidence standard), §11 (output location), §12 (reading/registration).
> **Supersedes nothing.** `docs/product/AMSDP_Business_Rules_V1.0.md` remains the authoritative
> business-rule text and is read-only for agents (`.clinerules` §11); this document describes
> implementation and does not amend it. Where the two disagree, the Business Rules win and the
> disagreement is a defect to be reported — §13 lists the one place the owner must confirm
> wording.

---

## 1. How to read this document

Every numbered statement below is held either by a **named test** (TESTED) or by a file/symbol
citation that can be read in the tree (IMPLEMENTED). Section §11 maps statements to tests.
Claims that are implemented but not asserted by a test are marked *not asserted*. No statement
in this document is presented as VERIFIED or ACCEPTED.

The implemented behaviour is the sum of three layers, and it is worth keeping them apart:

| Layer | Where | What it decides |
|---|---|---|
| Role matrix + grants | `backend/common/permissions.py`, `backend/common/auth.py` | whether a caller *may* attempt an action |
| Row scope | `backend/common/auth.py` (`branch_accessible`, `can_access_doctor`) and `_scoped_write_appointment` | which rows the caller may act on |
| Capacity | `backend/common/capacity.py`, `backend/common/slots.py`, `slot_allocations` table | which seat, if any, the action takes |

An action is allowed only when all three agree. `.clinerules` §3 is explicit that the user
interface is never the boundary: the browser mirrors these rules for usability (Q1's dialog
reason, Q3's hidden buttons) but the server re-decides every one of them.


---

## 2. Appointment types (owner decision Q1)

**The decision.** A booking outside every published session is a legitimate model **only** as a
deliberate, recorded act; the model must be *persisted*, not inferred from a missing
`start_time`, and it must be bounded. Three types are therefore stored on the appointment row:

| `appointment_type` | Meaning | How it is created | Which capacity it consumes |
|---|---|---|---|
| `scheduled` | The ordinary case — the patient holds a published slot | `POST /api/v1/appointments` | the slot **window** it falls in (§3.1) |
| `walk_in` | The patient is at the facility now and an active published session covers the arrival | `POST /api/v1/appointments/walk-in` only | the slot window covering the arrival time |
| `unscheduled` | The patient is accepted **outside** every published session/slot, by staff decision | `POST /api/v1/appointments` with `appointment_type: "unscheduled"`, or `/walk-in` when nothing covers the arrival | the organization's per-doctor daily override pool (§3.3) |

*Persisted fields:* `appointments.appointment_type` (default `scheduled`) and
`appointments.override_reason` (nullable text). Both are added by the forward-only migration
`backend/alembic/versions/a9c4e1f7b2d8_appointment_types_and_capacity_integrity.py`.
**Existing rows are not rewritten**: a row that predates the column keeps `scheduled` and no
override reason, because it never needed an override. Nothing is inferred from a `NULL`
`start_time`.

**Why `walk_in` is refused on the generic route.** `POST /api/v1/appointments` answers
`422 use_walk_in_workflow` for `appointment_type: "walk_in"`. A walk-in's date and time are not
free inputs: the walk-in workflow stamps **today** from the facility clock
(`common.timeutil.operational_today`) and the arrival minute from `operational_now`, then
resolves which session is actually running (`_session_covering`). Accepting a client-supplied
date would let a walk-in be back-dated or forward-dated while still being called a walk-in.

**The override is not a shortcut.** An `unscheduled` creation or walk-in requires, in this order:

1. the capability `appointment.create_unscheduled` — checked **per request** (`_require_capability`),
   so a revoked grant applies to the next request with no cache to clear;
2. a stated reason of at least 3 characters (`422 reason required: …`);
3. the organization's policy to be on (`allow_unscheduled`) and the doctor's daily pool not to be
   exhausted (`422 unscheduled_disabled` / `422 unscheduled_limit: …`);
4. an audit event `appointment.unscheduled_override` **in addition to** the creation event, with
   the reason in the event's `reason` field.

**The browser states the type instead of guessing it.** `frontend/lib/calendar/booking.js`
carries `APPOINTMENT_TYPES`, `typeLabelKey()` and `typeBadgeKey()`; the calendar card shows a
badge for `walk_in` (`typeWalkInShort`) and `unscheduled` (`typeUnscheduledShort`) and no badge
for `scheduled` (`frontend/components/AppointmentCalendar.js`). The booking dialog asks for the
override reason only when `bookingMode(slotChoices).mode === 'unscheduled'`, i.e. when the day
publishes **no** slots at all.

**The three dialog modes** (`bookingMode`, mirrored from the server's availability read):

| Mode | Condition | What the dialog does |
|---|---|---|
| `scheduled` | at least one slot is not full | the slot picker is the path; no reason is asked |
| `allFull` | slots exist, all full | says every slot is full; **does not** offer a free-text time as an equivalent |
| `unscheduled` | nothing is published for that day | asks for the override reason (`book-override-reason`, `overrideProblem`), sends `appointment_type: 'unscheduled'` |

The client-side check (`overrideProblem`, minimum 3 characters) exists to spare a round trip. It
is **not** the boundary; the server applies the same rule independently.

The walk-in dialog is a separate, persistent path: it carries `walk-reason`
(`walkInReason` = "Reason (required outside a session)") and `walk-reason-hint`
(`walkInHint`), and posts to `/api/v1/appointments/walk-in` with
`reason: (walk.reason || '').trim()`.


---

## 3. Capacity integrity (owner decision Q2)

**The decision.** Capacity must be enforced by **both** mechanisms, not one: the application
takes a row lock (`SELECT … FOR UPDATE` on the doctor) and the database holds a real constraint
that makes a duplicate seat impossible. Either alone was rejected — a lock without a constraint
survives only as long as every future code path remembers to take it, and a constraint without a
lock turns a race into an exception instead of a queue.

### 3.1 A seat is charged to the slot **window**, not to the minute

`_guard_slot` (`backend/appointment/main.py`) resolves the booking's time to a published slot via
`common/slots.py::slot_for`, then counts live appointments with
`start_time >= slot.start_time AND start_time < slot.end_time`. A 09:07 booking of the
09:00–09:15 window therefore consumes that window's seat, and the calendar badge that counts the
window agrees with the guard. The bookable capacity is what is left after the walk-in reserve:

```
effective = max(slot.max_patients - reserved_for_capacity(capacity, org.config), 1)
```

`reserved_for_capacity` is the same arithmetic the availability read publishes, so the read and
the write cannot disagree about a slot being full.

### 3.2 The database guarantee: `slot_allocations`

One row per **claimed seat** (`backend/common/models.py::SlotAllocation`), created by
`backend/common/capacity.py::claim_seat`:

| Constraint | Effect |
|---|---|
| `UNIQUE (doctor_id, appointment_date, slot_key, seat_number)` | capacity-N slots stay legal, a duplicate seat number does not |
| `UNIQUE (appointment_id)` | one appointment cannot hold two seats |

`claim_seat` inserts the first free `seat_number` in `1..capacity`; when none is free it raises
`SlotFull`, which `_claim_seat` translates into the **same** vocabulary as the count guard
(`422 slot_full: capacity N reached for the HH:MM slot …`) so a caller sees one meaning
whichever layer refused it. `release_seat` is called from `_apply_status_transition` for every
status outside `APPOINTMENT_ACTIVE_STATUSES`, so the allocation table and the status-based count
cannot drift apart; a reschedule claims the new window and frees the old one; a cancellation and
a no-show free theirs.

**Backfill caveat, stated plainly.** The migration backfills live appointments into
`slot_allocations`, but the slot key it can derive in SQL is the appointment's stored
`start_time` — a published window start is not derivable in SQL because it comes from the
doctor's templates. Rows booked exactly at a window start get exactly the runtime key; a
historically-booked 09:07 row of the 09:00 window gets `09:07` and is therefore **not**
deduplicated against the 09:00 window by the constraint. Those rows are still charged to the
window by the application's count guard. Pre-existing capacity overruns are **reported, never
repaired** by the migration.

### 3.3 The outside-session pool

An `unscheduled` appointment draws on a per-doctor, per-day pool whose size is *configuration*,
not an invented unlimited allowance (`_guard_slot`, `slot_key = 'UNSCHEDULED'`). The pool's
capacity is `appointment_config.unscheduled_daily_limit`; the count is live
`unscheduled` appointments for that doctor and date. The pool is claimed through the same
`claim_seat` path, so two concurrent overrides cannot both take the last place in the pool.

### 3.4 What the concurrency mechanism does *not* claim

* It does not promise fairness or queuing: a loser of a race receives `422 slot_full` and must
  choose another slot. There is no retry loop and no serialisable-isolation retry.
* It does not repair historic overruns (§3.2).
* The doctor row lock (`_lock_doctor`) additionally serialises the daily serial number, so two
  bookings cannot share a token
  (`TestCapacityAtomicity::test_the_serial_number_is_allocated_once`).

---

## 4. The capability catalogue (owner decisions Q1, Q3, Q4)

### 4.1 Capabilities added to the role matrix

`backend/common/permissions.py::PERMISSIONS` gained three strings. They are ordinary matrix
entries — reviewable, testable, and granted only to the roles named beside them:

| Capability | receptionist | doctor | assistant | branch_admin / org_admin / super_admin |
|---|---|---|---|---|
| `appointment.create` | yes | **yes** (own patients) | — | yes — via `appointment.*` |
| `appointment.check_in` | yes | **yes** (own patients) | **yes** (assigned doctors) | yes — via `appointment.*` |
| `appointment.create_unscheduled` | yes | **yes** (own patients) | — | yes — via `appointment.*` |
| `appointment.book_cross_branch` | via **grant** only | via **grant** only | — | yes — via `appointment.*` |
| `appointment.modify` | yes (unchanged) | **no** (unchanged) | no | yes — via `appointment.*` |

The three administrator roles hold the `appointment.*` namespace (Revision of owner decision Q-1
replaced the bare `"*"` with enumerated namespaces, and `appointment.*` is one of them), so all
three automatically cover every appointment capability listed here, including the three new
ones. That is *not* a new grant to them: it is the same namespace they already held.

Reading the table: a doctor may now **create and check in** a patient, which the pilot
(Scenario A — a doctor working without a receptionist) requires, but does **not** gain
`appointment.modify`. Cancel, reschedule and transfer remain front-desk work. The narrowing is
the point: the alternative — giving doctors `appointment.modify` so they can check in — would
have handed them cancellation authority as a side effect.

Every route that applies the doctor's create/check-in capability **also** enforces ownership
against the explicit assignment list (`auth.can_access_doctor`, which fails closed: no active
assignment ⇒ no access), and answers `404`, never `403` (`.clinerules` §3: non-disclosing).

### 4.2 Explicit staff grants

`backend/common/models.py::StaffCapabilityGrant` and the migration's `staff_capability_grants`
table record a capability granted to **one person**, optionally narrowed to **one branch**.
`DELEGABLE_CAPABILITIES` is a closed, three-item list:

```python
DELEGABLE_CAPABILITIES = (
    "appointment.book_cross_branch",    # Q4
    "appointment.create_unscheduled",   # Q1
    "appointment.check_in",             # Q3
)
```

A grant can only **add** to what the role already holds (`permissions.check_granted` is the union
of matrix and grants), so it can never invent a kind of access the matrix does not contain —
`appointment.modify`, `org.manage` and `audit.read` are structurally not delegable.

**Authority to grant.** `_granting_authority` (`backend/identity/routes.py`) admits only
`org_admin` / `super_admin`; a `branch_admin` is refused **by design**, because the capability
exists to cross exactly the boundary they administer. A foreign staff member is `404`.

**Revocation is effective immediately.** Grants are read from the database per request
(`common.auth.get_current_user` → `_load_capability_grants`, active rows only), so a revoked
grant is absent from the very next authorization decision and no token needs reissuing.
Revoking is a **state change, never a delete**: the row remains with `status='revoked'`,
`revoked_by` and `revoked_at`, and the act is audited (`staff.capability_revoked`).

### 4.3 Grant endpoints

| Method | Path | Permission | Notes |
|---|---|---|---|
| `GET` | `/api/v1/staff/users/{user_id}/capabilities` | `staff.read` | active grants by default; `?include_revoked=true` for the history |
| `POST` | `/api/v1/staff/users/{user_id}/capabilities` | `staff.manage` | `201`; idempotent — re-granting reactivates the row instead of duplicating it (`staff.capability_granted`) |
| `DELETE` | `/api/v1/staff/users/{user_id}/capabilities/{capability}` | `staff.manage` | optional `branch_id`; `404` when no active grant matches (`staff.capability_revoked`) |

`422` names the closed list when an unknown or non-delegable capability is requested, so a
caller cannot discover the full permission vocabulary by probing.

### 4.4 Where the two mechanisms meet

`require_permission(capability)` now calls `permissions.check_granted(capability, role, granted)`
— the union of matrix and grants, with **no branch narrowing**. Branch narrowing belongs to the
decision that needs it: `AuthContext.has_capability(capability, branch_id)` returns true only if
a grant's `branch_id` is `NULL` (organization-wide) or equal to the branch being acted on. The
cross-branch booking path (§6) uses the narrowed form; the check-in path uses the union plus the
ownership check, because check-in is not a branch-crossing act.

---

## 5. Check-in authority (owner decision Q3)

**The decision.** Check-in is a capability of its own, `appointment.check_in`, not a side effect
of `appointment.modify`. Two doors lead into the lifecycle and both now ask the same question:

| Door | Permission dependency | Ownership narrowing |
|---|---|---|
| `POST /api/v1/appointments/{id}/check-in` | `require_permission("appointment.check_in")` | doctor/assistant: `can_access_doctor(appt.doctor_id)`, else `404` |
| `POST /api/v1/queue/check-in` | `require_permission("appointment.check_in")` (was `queue.checkin` + `appointment.modify`) | branch scope + `can_access_doctor` |

The behaviour, by caller (all TESTED in `backend/appointment/tests/test_check_in_permissions.py`
and `backend/queuing/tests/test_queue.py`):

| Caller | Result |
|---|---|
| unauthenticated | `401` |
| `super_admin`, `org_admin`, `branch_admin` | allowed in their scope |
| `receptionist`, own branch | allowed |
| `receptionist`, another branch | `404` (never `403`) |
| `doctor`, own patient | allowed |
| `doctor`, no active assignment | `404` — `can_access_doctor` fails closed |
| `doctor`, another doctor's patient | `404` |
| `assistant`, assigned to that doctor | allowed |
| `assistant`, assigned elsewhere / unassigned | `404` |

**One transaction, one writer.** The route loads the appointment through
`_scoped_write_appointment` (tenant filter + branch scope + `FOR UPDATE`), writes the status
through `_apply_status_transition` (the single status writer, which validates the lifecycle,
appends history, audits `appointment.status_change` and revokes tracking access for terminal
statuses), then creates the queue entry with `allocate_daily_token` — the same token authority,
history and `queue.checkin` audit event as `POST /api/v1/queue/check-in`. Before this change the
route called the status route *function* directly, which is how it slipped past
`appointment.modify`, committed twice, and minted a duplicate token.

**Idempotent.** A second click is a no-op: a status already at `CHECKED_IN`/`IN_QUEUE` is not
transitioned again, and an appointment that already has a live queue entry does not get a second
one.

---

## 6. Cross-branch booking by explicit grant (owner decision Q4)

**The decision.** A staff member may be granted the right to **book into another branch of the
same organization** — and nothing else. The narrowing is implemented as a separate predicate,
not by widening the read scope:

```python
def _may_book_branch(auth, branch_id) -> bool:
    if branch_accessible(auth, branch_id):   # owns the branch already
        return True
    return auth.has_capability("appointment.book_cross_branch", branch_id)
```

Consequences, each held by `backend/appointment/tests/test_cross_branch_capability.py`:

* Without the grant the other branch is unreachable — the schedule resolver does not consider it
  and the booking fails.
* With the grant the booking crosses the boundary and the session/chamber in that branch is
  resolved.
* The creation audit event records `cross_branch: true`, so the trail answers "was this booking
  made by someone who cannot read that branch?" without joining anything.
* The grant does **not** unlock reading: a `GET` on the other branch's appointments is still
  refused (`_may_book_branch` governs the *write* decision only; reads keep using
  `branch_accessible`).
* Revocation applies to the next request.
* A grant recorded for Branch B does not answer yes for Branch C (`has_capability` narrows on
  `branch_id`).

The organization's own tenant boundary is unchanged: a foreign organization remains `404`, and
the tenant key remains `organization_id` (`.clinerules` §3).

---

## 7. Audited schedule, session, capacity and policy changes (owner decision Q5)

**The decision.** A governed change is audited, and the trail must answer *what changed* without
diffing JSON. `backend/scheduling/main.py` therefore writes, per change:

| Event | When | Payload |
|---|---|---|
| `schedule.created` | schedule created | the whole schedule |
| `schedule.updated` | any update | complete `before` and `after` |
| `schedule.status_change` | activation / deactivation | `{status}` before and after |
| `schedule.effective_dates_changed` | effective window moved | `effective_from` / `effective_to` before and after |
| `schedule.templates_changed` | templates rewritten | capacity map per window, before and after |
| `schedule.capacity_change` | a window's capacity moved | the **specific** windows and their old/new capacity |
| `session.*` (create / capacity / retire) | facility session changes | the same discipline |

Appointment-side events added by these decisions: `appointment.created` (now carrying
`appointment_type`, `seat`, `session_id`, `room_id`, `override_reason`, `cross_branch`),
`appointment.walk_in_created`, `appointment.unscheduled_override` (with the reason) and
`appointment.status_change`. Identity: `staff.capability_granted` / `staff.capability_revoked`.
Organization policy: one event per accepted `PUT appointment-config` change.

All of these are append-only writes through `common.audit.record_audit`. Nothing in this work
updates or deletes an audit row; denial auditing (owner decision Q-2) is unchanged and continues
to record every `403`/`404`/`422` the services answer.

---

## 8. The organization's override policy

Stored in the organization's `config` JSON under `appointment_config`, read through
`common.config.get_appointment_config` (malformed values fall back to the defaults rather than
raising — a corrupt block must never make booking answer `500`):

| Setting | Default | Bounds |
|---|---|---|
| `unscheduled_daily_limit` | **5** per doctor per day | clamped to `1 … 100` (`MAX_UNSCHEDULED_DAILY_LIMIT`) |
| `allow_unscheduled` | `true` | must be a boolean; anything else falls back to `true` |

| Method | Path | Permission |
|---|---|---|
| `GET` | `/api/v1/orgs/{org_id}/appointment-config` | `org.read` |
| `PUT` | `/api/v1/orgs/{org_id}/appointment-config` | `org.manage` |

A foreign organization is `404`; a `branch_admin` cannot change the policy (`403`); an empty
update is `422`; each accepted change writes its own audit event; the read returns who last
changed it and when, plus `max_unscheduled_daily_limit` so a UI can show the ceiling.

---

## 9. The refusal vocabulary (what a receptionist sees)

| Server refusal | Meaning | Browser key (`frontend/lib/calendar/booking.js`) |
|---|---|---|
| `slot_full: …` | the window has no free seat | `errSlotFull` |
| `no_slot_covers_time: …` | the doctor publishes nothing covering that minute | `errNoSlot` |
| `unscheduled_requires_override: …` | nothing published for that day — the accepted path is the override | `needsOverride` |
| `unscheduled_limit: …` | the doctor's daily outside-session pool is exhausted | `overrideLimit` |
| `unscheduled_disabled: …` | the organization does not accept outside-session patients | `overrideDisabled` |
| `use_walk_in_workflow` | `walk_in` posted to the generic route | `useWalkIn` |
| `reason required: …` | an override without a stated reason | `errNeedReason` |
| `403` | outside the caller's permission | `errForbidden` |
| `404` | not found *or* not yours — deliberately indistinguishable | `errNotFound` |
| anything unrecognised | — | `errUnknown` ("the server gave no reason — try again") |

The mapping is a convenience. The server's sentence remains the authority, and an unrecognised
refusal is reported as unrecognised rather than pasted into a Bangla screen.

---

## 10. API surface touched by these decisions

| Method | Path | Permission | New / changed |
|---|---|---|---|
| `POST` | `/api/v1/appointments` | `appointment.create` | changed — `appointment_type`, `override_reason`, override capability, seat claim |
| `POST` | `/api/v1/appointments/walk-in` | `appointment.create` | changed — decides `walk_in` vs `unscheduled`, requires the override capability when outside a session |
| `POST` | `/api/v1/appointments/{id}/check-in` | `appointment.check_in` | changed — capability, ownership, one transaction |
| `POST` | `/api/v1/queue/check-in` | `appointment.check_in` | changed — same capability, ownership narrowing |
| `GET` | `/api/v1/orgs/{org_id}/appointment-config` | `org.read` | **new** |
| `PUT` | `/api/v1/orgs/{org_id}/appointment-config` | `org.manage` | **new** |
| `GET` | `/api/v1/staff/users/{id}/capabilities` | `staff.read` | **new** |
| `POST` | `/api/v1/staff/users/{id}/capabilities` | `staff.manage` | **new** |
| `DELETE` | `/api/v1/staff/users/{id}/capabilities/{capability}` | `staff.manage` | **new** |
| `PATCH` | `/api/v1/schedules/{id}` | `schedule.*` | changed — validation + per-change audit events |

---

## 11. What holds each statement (test map)

| Statement | Test file / tests |
|---|---|
| The database refuses a duplicate seat | `appointment/tests/test_capacity_integrity.py::TestSeatUniquenessIsInTheDatabase` (2) |
| Two sessions racing for one seat: exactly one wins; capacity-N admits N and refuses N+1 | `::TestConcurrentClaims` (2, incl. `test_capacity_two_admits_two_and_refuses_the_third`) |
| The seat follows the window, and is freed on cancel / no-show / reschedule | `::TestSeatLifecycle` (4) |
| The outside-session pool is its own key and stops at the limit | `::TestUnscheduledPool` (2) |
| Check-in matrix by role and ownership, on both doors | `appointment/tests/test_check_in_permissions.py` (15 — `TestCheckInMatrix` 12, `TestTheQueueDoorAgrees` 3) |
| Cross-branch grant, audit flag, no read unlock, revocation | `appointment/tests/test_cross_branch_capability.py` (5) |
| Grant / refuse / revoke capability, idempotency, 404 discipline | `identity/tests/test_capability_grants.py` (16) |
| Organization policy read / change / bounds / audit | `organization/tests/test_appointment_config.py` (10) |
| Schedule and session audit events | `scheduling/tests/test_schedule_audit.py` (8) |
| Atomicity, serial allocation and the earlier F-01…F-19 guarantees | `appointment/tests/test_appointment_reliability.py` (28) |
| Dialog asks for the type and the override reason (Q1); walk-in, check-in, status change and cancel-with-reason preserved | `frontend/tests/appointments-calendar-integration.test.mjs` (12, incl. `the booking dialog names the appointment type and asks for the override reason (Q1)` and `walk-in, check-in, status change and cancel-with-reason are preserved`) |
| The refusal vocabulary is translated, not pasted | `frontend/tests/appointment-booking-feedback.test.mjs` (9) |

Totals at the time of writing: backend `appointment/ scheduling/ identity/ organization/`
**318 passed**; frontend `npm test` **180 passed / 0 failed**; `npm run build` **compiled
successfully** with `/appointments` at 23 kB. These are the numbers in the implementation report
§7; re-run them before quoting them.

**Re-checked on 2026-11-19** (documentation task Q6): the backend figure was re-run and holds —
`318 passed, 183 warnings in 624.05s`. The per-file counts in the table above were also recounted
against the test sources; one row double-counted `test_capacity_two_admits_two_and_refuses_the_third`,
which lives in `::TestConcurrentClaims`, and the two rows were merged. Every other count matches.
The frontend counts and the build figure were **not** re-run by the documentation task and are
reported as the implementation run recorded them.

---

## 12. Not claimed

* **No production deployment.** The migration is applied to the local/demo database only.
* **No screen for grants or for the policy.** Both are API-only; an administrator uses the API.
  Nothing in this work adds an administrative screen.
* **No fairness or retry** under contention (§3.4).
* **No historical repair** of pre-existing over-capacity days (§3.2).
* **The override reason is free text**, stored verbatim; no vocabulary or length ceiling beyond
  the 3-character minimum is enforced.
* **Nothing ACCEPTED.** Owner sign-off (`.clinerules` §7) has not been given for any row of this
  work.

---

## 13. References

* Decision record and rationale: `docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md`
* Diagnosis the work answers: `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md`
* Earlier remediation (F-01…F-19): `docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`
* Business rules (authoritative, read-only for agents): `docs/product/AMSDP_Business_Rules_V1.0.md`
* Migration: `backend/alembic/versions/a9c4e1f7b2d8_appointment_types_and_capacity_integrity.py`
