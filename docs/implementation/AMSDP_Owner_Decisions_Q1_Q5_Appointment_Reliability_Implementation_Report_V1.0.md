# AMSDP — Appointment & Calendar Owner Decisions Q1–Q5: Implementation Report

> **Task ID:** `AMSDP-APPT-OWNER-DECISIONS-01`
> **Date:** 2026-11-19 · **Version:** V1.0
> **Status:** implemented, tested and build-verified; **nothing is ACCEPTED** (`.clinerules` §7)
> **Predecessor:** `docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`
> (F-01…F-19). This report covers the owner decisions that the predecessor left open.
> **Behavioural specification:** `docs/architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md`
> **Governed by:** `.clinerules` §1 precedence, §3 non-negotiables, §6 compliance reporting, §7 evidence
> standard, §9 execution boundaries, §11 output location, §12 documentation reading policy.

---

## 1. What this report answers

The remediation report closed nineteen findings and stated, in place, the two it could not close
without an owner decision: **F-01**'s database-level capacity guarantee and **F-18**'s
"mark the outside-session booking as such" half. Five further questions were raised and answered
by the owner in session under task `AMSDP-APPT-OWNER-DECISIONS-01`. This report records what was
built for each, what proves it, and what remains open.

| Decision | Subject | Status in this tree |
|---|---|---|
| **Q1** | Appointment types: `scheduled` / `walk_in` / `unscheduled`, persisted; the outside-session acceptance is an explicit, reasoned, limited, audited override | IMPLEMENTED · TESTED |
| **Q2** | Capacity integrity enforced by **both** the application lock and a database constraint (`slot_allocations`) | IMPLEMENTED · TESTED |
| **Q3** | Check-in is its own capability (`appointment.check_in`), for doctors and assistants **on their own patients only**, without granting `appointment.modify` | IMPLEMENTED · TESTED |
| **Q4** | Cross-branch booking for central-reception staff through an explicitly granted, independently revocable, branch-scoped capability | IMPLEMENTED · TESTED |
| **Q5** | Schedule / session / capacity / policy changes are audited with the specific values that changed, and the override is its own audit event | IMPLEMENTED · TESTED |
| **Q6** | The decisions must be reflected in the project's documents, and the owner-controlled documents must not be touched | **partly done — see §9** |

**On the naming, so nobody conflates two decision families.** The repository holds
`docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`, which records the **Q-1 … Q-6** decisions
from `docs/audit/AMSDP_Project_Context_Report_V1.0.md` (platform-administration boundary, denial
auditing, notification worker, limitations-report accuracy, continuous integration,
owner-controlled documents). Those are a *different* set, and this report cites them only for
their cross-cutting conditions (§8). No decision record for the appointment set (Q1–Q5) exists
under `docs/`; the decisions are recorded here, in the implementing agent's words, exactly as the
predecessor report recorded its own open questions. Authoring a formal decision record for them
is the owner's act, not the agent's, and is raised in §9.

---

## 2. The change in one paragraph

An appointment now carries its own type instead of having one inferred from a missing time; an
appointment's seat is a row in `slot_allocations` that the database guarantees is unique for its
window, claimed before the booking is committed and released when the visit ends; checking a
patient in is a distinct capability that a doctor and an assistant hold for their own patients
and nobody else's; a central-receptionist can be granted the right to book into another branch
of the same organization without gaining any ability to read that branch; and every schedule,
session, capacity and policy change — plus every outside-session acceptance — leaves a specific,
append-only audit event. The frontend states the type it reads, asks for the override reason
only when the day publishes nothing, and translates the new refusals instead of pasting English
into a Bangla screen.

---

## 3. Q1 — appointment types, walk-ins and the explicit override

**Shipped.**

* `Appointment.appointment_type` (`scheduled` default) and `Appointment.override_reason`.
* `POST /api/v1/appointments` accepts `appointment_type` + `override_reason`; `walk_in` is
  refused there (`422 use_walk_in_workflow`) because a walk-in's date/time come from the facility
  clock, not the client.
* `POST /api/v1/appointments/walk-in` decides between `walk_in` (a published session covers the
  arrival) and `unscheduled` (nothing does) and never infers the type from a missing field.
* The override requires the capability `appointment.create_unscheduled`, a reason of ≥3
  characters, the organization's `allow_unscheduled` switch and its per-doctor daily limit
  (default **5**, maximum **100**), and writes `appointment.unscheduled_override`.
* A scheduled booking outside published hours is refused with
  `422 unscheduled_requires_override` rather than silently falling back to "one patient per
  exact minute".
* Frontend: `APPOINTMENT_TYPES`, `typeLabelKey`, `typeBadgeKey`, `bookingMode` (`scheduled` /
  `allFull` / `unscheduled`), `overrideProblem`, the `book-override-reason` input and the
  `walk-reason` input in the walk-in dialog; calendar cards show a type badge.

**Not done, by choice.** No back-dated or forward-dated walk-in; no configurable reason
vocabulary; no automatic conversion of an existing appointment's type (nothing is inferred from
`NULL start_time`).

---

## 4. Q2 — capacity integrity

**Shipped.** `slot_allocations` (one row per claimed seat) with
`UNIQUE (doctor_id, appointment_date, slot_key, seat_number)` and `UNIQUE (appointment_id)`;
`backend/common/capacity.py` (`claim_seat`, `release_seat`, `seat_of`, `SlotFull`); the claim
happens inside the booking transaction after the doctor row lock, and the release happens in the
single status writer for every status that does not occupy a seat.

**Honest limits.** Historical rows are backfilled with the key the migration can derive
(`start_time`) — a 09:07 row of the 09:00 window is not deduplicated by the constraint, though
the application still charges it to the window; pre-existing overruns are **reported, never
repaired**; contention produces `422 slot_full`, not a queue.

---

## 5. Q3 — check-in as its own capability

**Shipped.** `appointment.check_in` in the matrix (receptionist, doctor, assistant, and the
administrator namespace); both doors (`/appointments/{id}/check-in` and `/queue/check-in`) use it;
doctor and assistant callers are narrowed by `can_access_doctor` against the explicit assignment
and receive `404` when it does not match; `appointment.modify` was **not** granted to doctors;
the route now writes the status through the single writer inside one transaction and allocates
the queue token through `allocate_daily_token`, so the duplicate-token defect cannot recur.

---

## 6. Q4 — cross-branch booking by grant

**Shipped.** `StaffCapabilityGrant` + `staff_capability_grants`; `DELEGABLE_CAPABILITIES`
(`appointment.book_cross_branch`, `appointment.create_unscheduled`, `appointment.check_in`);
`GET`/`POST`/`DELETE /api/v1/staff/users/{id}/capabilities`; grants read per request
(revocation effective on the next request); `_may_book_branch` governs the **write** decision
only, so reads keep the ordinary branch scope; the creation event records `cross_branch: true`.

**Why a grant and not a role.** Making "central reception" a role would have widened every
capability, not one. The grant is one named capability, revocable alone, and audited both when
given and when withdrawn.

---

## 7. Q5 — audited configuration changes

**Shipped.** `schedule.created`, `schedule.updated` (full before/after),
`schedule.status_change`, `schedule.effective_dates_changed`, `schedule.templates_changed`,
`schedule.capacity_change` (only the windows whose capacity moved), the session equivalents, the
organization policy event, and the appointment-side `appointment.walk_in_created` /
`appointment.unscheduled_override` events. All append-only; no audit row is updated or deleted.

---

## 8. Files touched

**New (2 source modules + 1 migration + 6 test modules):**

| File | Why |
|---|---|
| `backend/alembic/versions/a9c4e1f7b2d8_appointment_types_and_capacity_integrity.py` | the three schema changes of §9 |
| `backend/common/capacity.py` | seat claim / release / lookup, `SlotFull` |
| `backend/organization/appointment_config.py` | `GET`/`PUT /api/v1/orgs/{org_id}/appointment-config` |
| `backend/appointment/tests/test_capacity_integrity.py` | 10 tests (uniqueness, concurrency, lifecycle, pool) |
| `backend/appointment/tests/test_check_in_permissions.py` | 15 tests (role matrix, ownership, queue door) |
| `backend/appointment/tests/test_cross_branch_capability.py` | 5 tests |
| `backend/identity/tests/test_capability_grants.py` | 16 tests |
| `backend/organization/tests/test_appointment_config.py` | 10 tests |
| `backend/scheduling/tests/test_schedule_audit.py` | 8 tests |

**Modified (backend):** `appointment/main.py` (+459 lines — types, override, guard, seat claim,
walk-in, check-in, audit fields), `common/auth.py` (grants per request, `has_capability`,
`assigned_doctor_ids` normalisation), `common/config.py` (`appointment_config` defaults and
merge), `common/models.py` (`SlotAllocation`, `StaffCapabilityGrant`, `appointment_type`,
`override_reason`), `common/permissions.py` (three capabilities, `DELEGABLE_CAPABILITIES`,
`check_granted`), `common/timeutil.py` (facility clock helpers), `identity/main.py`,
`identity/permissions.py`, `identity/routes.py` (grant endpoints; missing `DELEGABLE_CAPABILITIES`
import fixed), `organization/main.py` (router mount), `queuing/main.py` (check-in door uses
`appointment.check_in` + ownership), `scheduling/main.py` (per-change audit events),
`scheduling/sessions.py` (session audit), plus the affected tests
(`test_appointment.py`, `test_appointment_reliability.py`, `test_reschedule.py`,
`test_symptoms.py`, `test_identity.py`, `test_queue.py`, `test_facility_doctor.py`,
`test_sequence3.py`, `test_sequence4.py`, `test_tracking_tokens.py`, `tests/amsdp_test_support.py`).

**Modified (frontend):** `pages/appointments.js` (override reason, walk-in reason, booking mode,
refusal text), `components/AppointmentCalendar.js` (type badge), `lib/calendar/booking.js`
(types, `bookingMode`, `overrideProblem`, four new refusal keys), and the three affected test
files (`appointments-calendar-integration.test.mjs`, `appointment-booking-feedback.test.mjs` — the
refusal-key count rose 13 → 17 — and `symptom-picker-contract.test.mjs`, whose Bangla match now
uses letter boundaries so `প্রকাশিত` no longer matches the symptom `কাশি`).

---

## 9. Q6 — documentation, and the migration behind all of it

### 9.1 The migration

`a9c4e1f7b2d8` revises the merge point `('b3d7e91f6a24', 'f8a2b3c4d5e6')` and makes three
changes, forward-only and idempotent:

1. `appointments.override_reason` (nullable) — existing rows are **not** rewritten.
2. `slot_allocations` — the database guarantee of §4, backfilled for live appointments with the
   caveat stated there.
3. `staff_capability_grants` — Q4's grant, its unique scope, and its revoked columns.

It is the current head of the local chain (verified with `alembic heads` / version list on
2026-11-19) and was applied in this environment. **Downgrade is documented, not promised**:
dropping the two tables loses allocation and grant *history*; re-running the upgrade rebuilds
allocations from surviving appointments, but a revoked-then-dropped grant cannot be
reconstructed. No existing column is dropped or narrowed by the upgrade.

### 9.2 Documents written for Q6

| Document | State |
|---|---|
| `docs/architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md` | **new** — the behavioural specification (types, capacity, capability catalogue, check-in matrix, cross-branch grant, audit events, refusal vocabulary, API surface, test map) |
| `docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md` | **new** — this report |
| `docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md` | appended §10 — the F-01 and F-18 partial closures are now closed, with pointers |
| `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` | appended resolution status for F-01 … F-19 |
| `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` | appended the capability-catalogue delta (three capabilities + delegable list + grant routes) |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Revision 33** — one new row per document, the two appended reports' size cells and *Read when* text refreshed, revision entry written |

**Deliberately not touched.** `docs/product/AMSDP_Business_Rules_V1.0.md` and
`docs/product/AMSDP_MVP_SCOPE_V1.0.md` are owner-controlled (`.clinerules` §11) and read-only for
agents. This work conforms to them; it does not amend them. If the owner wants the new
capability names, the appointment-type vocabulary or the override limit written into the Business
Rules, that is the owner's edit — raised as item **O-1** in §13. The same applies to
`docs/architecture/AMSDP_System_Architecture_V1.0.md` (owner-controlled; Q-6 of the other
decision set explicitly preserves it verbatim).

---

## 10. Verification

### 10.1 The five acceptance scenarios

Each decision was exercised as an end-to-end scenario through the real API with real tokens and a
real database (`tests/amsdp_test_support.py` builds the principals). None of these were manual
browser walks; the browser was used earlier in the task to observe the calendar, and the build
below is the frontend compiles-or-not evidence.

| # | Scenario | Expected | Proven by |
|---|---|---|---|
| **A** | Solo doctor, no receptionist: a patient arrives mid-morning | the doctor registers the walk-in and checks them in; a patient of another doctor is `404` | `test_check_in_permissions.py::TestCheckInMatrix` (doctor own / doctor other / doctor no assignment), `test_appointment.py` walk-in cases |
| **B** | A day whose slots are all full, and a day with no published slot | full day ⇒ `422 slot_full`, no free-text booking; empty day ⇒ `422 unscheduled_requires_override`, then the override path succeeds with a reason, and stops at the daily limit | `test_capacity_integrity.py`, `test_appointment.py` override cases, `appointment-booking-feedback.test.mjs` |
| **C** | Central receptionist books into another branch | without the grant the branch is unreachable; with it the booking succeeds and is audited `cross_branch: true`; reading that branch still `404`; revocation applies immediately | `test_cross_branch_capability.py` (5), `test_capability_grants.py` (16) |
| **D** | Two receptionists take the last seat of a window at the same instant | exactly one wins; the other receives `422 slot_full`; `slot_allocations` holds one row; the doctor's serial numbers stay unique | `test_capacity_integrity.py::TestConcurrentClaims` (2), `test_appointment_reliability.py::TestCapacityAtomicity` (2) |
| **E** | An administrator moves a window's capacity, deactivates a schedule, and changes the override policy | each change leaves its own specific event (`schedule.capacity_change`, `schedule.status_change`, policy event) with before/after | `test_schedule_audit.py` (8), `test_appointment_config.py` (10) |

### 10.2 Suites

| Command | Result (this task) |
|---|---|
| `pytest backend/appointment backend/scheduling backend/identity backend/organization -q` | **318 passed** |
| `cd frontend && npm test` | **180 passed, 0 failed** |
| `cd frontend && npm run build` | **Compiled successfully**; `/appointments` 23 kB, First Load JS 144 kB |
| `alembic heads` / version list | single head `a9c4e1f7b2d8`, applied |

The frontend is **not** type-checked or linted by this project's test command; `npm run build`
is the check that exists, and it passed. Nothing in this report claims a browser-level
verification beyond what §10.1 states.

**Re-run on 2026-11-19, by the documentation task (Q6), before the figure was quoted again:**
`pytest backend/appointment backend/scheduling backend/identity backend/organization -q` →
**318 passed, 183 warnings in 624.05s**, with the environment sourced so the configured database
is reachable. An earlier attempt in the same session stopped at connection setup because the
environment had not been sourced; that was a setup failure, not a test result, and is not counted.
Only the backend line was re-run — the frontend and build figures above stand as recorded by the
implementation run and are not re-claimed by the documentation task.

---

## 11. Governance and skill compliance

### 11.1 Documents read and applied (`.clinerules` §2 step 3, §4 routing)

| Domain | Governing documents read this task | Applied as |
|---|---|---|
| Backend API / endpoints | `saas-application-security.md` (via Assessment §3), Business Rules Part II–X | server-side authorization on every new route; no client-trusted scope |
| Auth, RBAC, permissions | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py`, M2 security report | capability matrix + grants, fail-closed ownership |
| Multi-tenant / branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6, `backend/common/auth.py` | `organization_id` only; cross-tenant `404`; branch narrowing |
| Database schema / migrations | `saas-cicd-workflow.md` §3 (adapted), Alembic chain, `backend/common/models.py` | one forward-only idempotent migration, documented downgrade |
| Audit / integrity | `saas-observability.md` (adapted), `backend/common/audit.py`, Business Rules Part X | append-only events, specific payloads, no PII |
| Frontend UI | `saas-frontend-ux.md` (adapted), AMSDP UI/UX assessment, `frontend/lib/i18n.js` | Bangla-first captions via i18n keys, no English pasted into the UI |
| Documentation | `.clinerules` §11/§12, `AMSDP_Docs_Index_V1.0.md`, migration manifest | `docs/` placement, index updated, no owner document touched |

Also read: `docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md`,
`docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`,
`docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`, `docs/product/AMSDP_Business_Rules_V1.0.md`
(read-only), `docs/product/AMSDP_MVP_SCOPE_V1.0.md` (read-only).

### 11.2 Skills

**No skill was used, because none is installed** (`.clinerules` §5 — verified: no
`.clinerules/skills/`, `.claude/skills/` or repo `skills/` directory, and no Cline skill
configuration in this workspace). The governance documents above were used in their place. This
report claims no skill usage.

### 11.3 Non-negotiables (§3)

| Rule | Evidence |
|---|---|
| No secret logged or exposed | no credential, token or key appears in any audit payload, refusal text, log line or this report |
| UI is not the boundary | every rule the dialog applies (override reason, type, grant) is re-decided server-side; the dialog is UX only |
| Server-side scope from the token | `get_current_user` derives org/branch from the token; no new route reads scope from a body |
| Cross-tenant / cross-branch fails closed with `404` | `test_cross_branch_capability.py`, `test_check_in_permissions.py`, `test_capability_grants.py` all assert `404`, never `403`, for foreign scope |
| Tenant key stays `organization_id` | `slot_allocations` and `staff_capability_grants` carry `organization_id`; no second tenant column |
| Audit append-only | only `record_audit` inserts; no `update`/`delete` on the audit table in the diff |
| Denials recorded | the denial-audit installer covers the changed routers; the new refusals are audited as before |
| Schema change is a forward-only idempotent migration | `a9c4e1f7b2d8` (§9.1) |
| No invented capability claim | §12 distinguishes IMPLEMENTED / TESTED / VERIFIED / ACCEPTED |
| No destructive git operation | nothing was reset, stashed or cleaned (§14) |

### 11.4 Cross-cutting conditions of `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`

| Decision | Honoured here |
|---|---|
| Q-1 (no wildcard) | untouched; the three new capabilities are ordinary matrix strings, and administrators reach them through the existing enumerated `appointment.*` namespace, which Q-1 explicitly keeps |
| Q-2 (denial auditing) | the changed routes run under the shared denial-audit installer; no duplicate or oracle-producing event was added |
| Q-3 (notification worker) | not in scope, not touched |
| Q-4 (limitations-report accuracy) | not in scope; `docs/demo/AMSDP_Limitations_Report_V1.0.md` is owner-controlled and was not edited |
| Q-5 (CI honesty) | §10.2 quotes only commands actually run in this environment; no CI gate is claimed |
| Q-6 (owner-controlled documents) | `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, `docs/architecture/AMSDP_System_Architecture_V1.0.md` and the Master Feature List drafts are unmodified (§9.2) |

---

## 12. Evidence table (§7)

| Claim | IMPLEMENTED | TESTED | VERIFIED | ACCEPTED |
|---|---|---|---|---|
| Three persisted appointment types | ✔ | ✔ | — | — |
| Override requires capability + reason + limit, and is audited | ✔ | ✔ | — | — |
| Seat uniqueness guaranteed by the database | ✔ | ✔ | — | — |
| Seat released on cancel / no-show / reschedule | ✔ | ✔ | — | — |
| `appointment.check_in` on both doors, ownership-narrowed | ✔ | ✔ | — | — |
| Doctor does **not** gain `appointment.modify` | ✔ | ✔ | — | — |
| Cross-branch grant, branch-scoped, revocable, audited | ✔ | ✔ | — | — |
| Grant does not unlock reads | ✔ | ✔ | — | — |
| Schedule / session / capacity / policy audit events | ✔ | ✔ | — | — |
| Organization override policy with bounds | ✔ | ✔ | — | — |
| Frontend states the type, asks the override reason, translates refusals | ✔ | ✔ | — | — |
| Frontend compiles | ✔ | — | ✔ (`npm run build`) | — |
| Migration applied to the local database | ✔ | ✔ | ✔ (`alembic heads` = `a9c4e1f7b2d8`) | — |
| Production behaviour | — | — | — | — |

Nothing in this table is VERIFIED in the `.clinerules` §7 sense beyond the two rows that name an
independent artefact (the build output and the Alembic head). A green suite is not verification.

---

## 13. Open items, deviations and things this work deliberately did not do

| # | Item | Owner action needed |
|---|---|---|
| **O-1** | The Business Rules do not name `appointment_type`, the three new capabilities or the override limit. This work **conforms** to the rules and does not amend them (`.clinerules` §11). | Yes — if the owner wants the vocabulary in `docs/product/AMSDP_Business_Rules_V1.0.md` |
| **O-2** | No formal decision record exists for the appointment Q1–Q5 set under `docs/decisions/`. This report records them in the agent's words. | Yes — author/publish the decision record |
| **O-3** | Grants and the override policy are **API-only**; there is no administrative screen. `test_capability_grants.py` proves the API, not a UI. | Decide whether a screen is in scope |
| **O-4** | Pre-existing over-capacity days are reported by the migration, not repaired; historical seat keys are approximate (§9.1, §4). | Decide whether a repair pass is wanted |
| **O-5** | The override reason is free text (≥3 characters) with no vocabulary or maximum length. | Decide whether a controlled vocabulary is required |
| **O-6** | `appointment_config` is stored in the organization `config` JSON, so a malformed block silently falls back to defaults rather than failing loudly. This is deliberate (booking must not 500) but means a typo can go unnoticed. | Consider a validation warning on write |
| **O-7** | Frontend has no type-check or lint gate; `npm run build` is the only compile check. | Out of scope of this task (Q-5 forbids new tooling) |

**Deviations from the plan, stated plainly:** the RBAC current-state audit was appended to rather
than rewritten (it already carried unrelated uncommitted rows for the earlier R-12 work, and
`.clinerules` §9 forbids entangling or discarding someone else's uncommitted work); the
`docs/security/AMSDP_M2_Security_Implementation_Report.md` milestone report was **not** amended,
because a milestone report is history, not current state.

---

## 14. Tree state and where this report was written

* Baseline commit: `6b7ef4d`. This work is **uncommitted** in the working tree; nothing was
  committed, pushed, reset, stashed or cleaned (`.clinerules` §9).
* Untracked and **not part of this work**: `docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`,
  which predates this task and must not be staged with it.
* This report: `/home/shomonrobie/amsdp/docs/implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md`
  (`.clinerules` §11 — implementation subject ⇒ `docs/implementation/`).
* Its companion specification: `/home/shomonrobie/amsdp/docs/architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md`
  (architecture subject ⇒ `docs/architecture/`).
* No document was moved or renamed, so no migration-manifest entry was required. Both new
  documents are registered in `docs/governance/AMSDP_Docs_Index_V1.0.md` (§12 obligation).
