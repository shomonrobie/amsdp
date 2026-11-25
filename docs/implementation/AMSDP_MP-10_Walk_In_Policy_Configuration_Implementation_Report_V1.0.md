# AMSDP — MP-10 Implementation Report: walk-in policy configuration

**Status:** TESTED (not VERIFIED — no live browser, no live credential and no container access; see §5)
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`)
**Task source:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-C, MP-10, read against
`docs/product/AMSDP_Business_Rules_V1.0.md` §24–§25 and §52.
**Register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §2 (row MP-10), §5 (frontend run), §6
(working tree), §8 (change log).

---

## 1. Requirement

Plan acceptance criterion, quoted: *"BR §25/§52: four **distinct** behaviours proven by tests; a policy change never
reorders an active queue; the change is audited."*

BR §25, quoted: *"Facility may choose among: (1) **End of queue** … (2) **First-come, first-served** … (3) **Reserved
capacity:** reserve a configurable number or percentage of capacity for walk-ins. (4) **Staff-controlled placement:**
authorized staff selects queue position. Super Admin defines available options/limits. Facility Admin selects policy.
Only authorized users may change it. Changes are audit logged and apply prospectively; they must not silently reorder
an active queue or alter existing appointments."*

### 1.1 What the code did before this task

- The policy was a **per-request parameter**: `walk_in_policy` on `POST /api/v1/queue/enqueue` and on
  `POST /api/v1/queue/check-in` (`backend/queuing/main.py`, former lines 244 and 370). Any caller holding
  `queue.checkin` chose the rule for that one patient, so "Facility Admin selects policy" had no implementation at
  all, and two receptionists could place two patients under two different rules in the same queue.
- Only **one** of the four policies had a behaviour: `staff_placement` used the supplied `position`. The other three
  all computed `pos = seq` — the daily token sequence — so `end_of_queue`, `first_come` and `reserved_capacity` were
  the same code path. The tests that "covered" them asserted a `201` and nothing about placement.
- The reserved-capacity *split* did exist, but only in the booking path: `common.config.get_queue_config` +
  `reserved_for_capacity` stop advance bookings from consuming the last N % (or N seats) of a slot
  (`backend/appointment/main.py:611`, `backend/scheduling/main.py:360,403`). Nothing wrote that configuration —
  there was no endpoint — and nothing in the queue enforced the pool the reservation creates. That is the "real
  `reserved_capacity` pool" the plan asks for.
- There was no `walk-in-config` surface, so no audited place for an administrator to change any of it.

### 1.2 Design decision — where the policy is stored

The plan says MP-10 "requires its own revision" (§8 rule 3). **No migration was written, deliberately.**

Configuration in this codebase is `organizations.config` JSON with a sibling router per policy
(`queue_calling_config.py`, `appointment_config.py`, `registration_policy` in `doctor/profile.py`), each audited with
before/after and each defaulted so an absent block changes nothing. The reserve split MP-10 must build on *already*
lives in `organizations.config["queue_config"]`, read by the booking path. A new table would have been a **second**
mechanism for the same data, with two readers that could disagree — the failure mode the plan's own D5 exists to
prevent. MP-10 therefore extends the existing block to
`{"walk_in_policy", "walk_in_reserve_mode", "walk_in_reserve_value", "allowed_walk_in_policies"}` and adds the
missing writer. This is recorded as a deviation with its reason in §5, item 1; the schema is unchanged, so §8 rule 3
has nothing to sequence.

---

## 2. Change

| File | Change |
|---|---|
| `backend/common/config.py` | `WALK_IN_POLICIES`, `DEFAULT_WALK_IN_POLICY`, reserve bounds, `allowed_walk_in_policies()`, an extended `get_queue_config()` (policy + allowed set + hardened reserve parsing, so a corrupt value can no longer raise inside the booking path), and `get_walk_in_config()` / `merge_walk_in_config()`. One block, read by the queue, the booking path and the API view. |
| `backend/queuing/placement.py` *(new)* | `active_queue()` (locked, doctor/day scoped), `day_capacity()` (published seats for the weekday, from `schedules.slot_templates` via `common.slots`), `reserve_pool()`, `_shift_from()` (position history + one `queue.reposition` audit per moved row) and `place()` — the single implementation of the four BR §25 behaviours. |
| `backend/queuing/main.py` | `walk_in_policy` and `position` **removed** from `CheckInRequest`; `walk_in_policy` removed from `QueueEnqueueRequest`, `arrived_at` added; both write paths now call `place_entry()`; a placement refusal is a 422; the `queue.enqueue` audit row carries the placement decision (`policy`, `basis`, `pool`, `pool_used`, `shifted`). Local `WALK_IN_POLICIES` constant deleted (now one definition, in `common.config`). |
| `backend/organization/walk_in_config.py` *(new)* | `GET`/`PUT /api/v1/orgs/{org_id}/walk-in-config`. Read open to the organization's own staff; write needs `org.manage`; foreign org → 404; policy validated against the allowed set; reserve validated against its mode's bound; `allowed_walk_in_policies` settable **only** by a platform administrator (`platform.admin`); audited as `walk_in_config.updated` with before/after. |
| `backend/organization/main.py` | Mounts the new router, in the same try/except import style as its siblings. |
| `frontend/lib/queue/walk-in.js` *(new)* | `effectivePolicy()`, `needsPosition()`, `policyLabelKey()`, `buildEnqueueBody()`. The body builder never emits `walk_in_policy`, and emits `position` only where the facility's policy asks staff for one. Pure, so it is tested without React. |
| `frontend/pages/queue.js` | The policy `<select>` is gone. The walk-in form reads `/walk-in-config` when it opens, **shows** the facility's policy (translated), and asks for a position only under `staff_placement`. The request body now comes from the tested module. |
| `frontend/lib/i18n.js` | 5 new keys in Bangla and English (`placementPolicy`, `policyFirstCome`, `policyReservedCapacity`, `policyStaffPlacement`, `positionRequired`); `endOfQueue` was reused for the default policy. |
| `backend/queuing/tests/test_queue.py` | `TestWalkInPolicies` rewritten to the new contract: the policy is configured on the organization, the body cannot choose it, and an unknown stored value falls back instead of refusing work. |
| `backend/queuing/tests/test_walk_in_placement.py` *(new)* | 15 tests — the behaviour of all four policies, the prospective-only guarantee, the audit content and the denial record. |
| `backend/organization/tests/test_walk_in_config.py` *(new)* | 23 tests — effective value and defaults, who reads and who writes, the platform-defined option set, reserve bounds, tenant scoping, partial updates, config-block preservation, audit. |
| `frontend/tests/queue-walk-in-policy.test.mjs` *(new)* | 10 tests — the pure decisions, the translation coverage, the page wiring, and the backend/frontend agreement on the retired field. |

**The four behaviours, as implemented** (`backend/queuing/placement.py`):

| Policy | Position | Moves existing rows? | How it is distinguished |
|---|---|---|---|
| `end_of_queue` | `max(position) + 1` | no | appends; nothing is audited as moved |
| `first_come` | first row whose `created_at` is later than the entry's arrival instant, else append | yes, when the arrival is earlier | a back-dated `arrived_at` lands ahead of patients registered after it |
| `reserved_capacity` | end of the reserved block, while the block holds fewer than `pool` walk-ins; otherwise append | yes, while the block fills | the pool is a count, or a percentage of the day's published seats |
| `staff_placement` | the validated position staff supplied (1 … `max+1`) | yes | a missing or out-of-range position is a 422 |

An appointment checking in is **not** placed by the walk-in policy (BR §25 governs walk-ins); it takes the append
path under every setting, so a facility configured for `staff_placement` can still check a booked patient in.

---

## 3. Tests

### 3.1 New and rewritten tests

| Where | Count | What it pins |
|---|---:|---|
| `backend/queuing/tests/test_walk_in_placement.py::TestEndOfQueue` | 2 | append, and "an append reorders nothing" (the `queue.reposition` count is unchanged); a booked patient checks in under `staff_placement` without a position |
| `…::TestFirstCome` | 3 | a back-dated arrival is placed ahead and the displaced row's history says so (`from 1 → to 2`, reason names `first_come`) plus exactly one `queue.reposition` audit; no arrival time ⇒ append; an unparseable `arrived_at` ⇒ 422 and nothing written |
| `…::TestReservedCapacity` | 4 | the block fills at 1 and 2 for `count = 2` and the third walk-in appends at 6 (⇒ genuinely distinct from `end_of_queue`, where it would be 4); the pool is a guarantee, not a cap; percentage mode uses published capacity (4 slots × 2 seats × 50 % = 4); percentage mode with nothing published ⇒ append, never an error |
| `…::TestStaffPlacement` | 3 | the requested position is used and the rest shift; a missing position is a 422 naming `staff_placement_position_required`; `0`, `5` (on a 1-row queue) and `-1` are refused and write nothing |
| `…::TestPolicyIsProspective` | 1 | `end_of_queue → staff_placement` with three patients waiting moves nobody and audits no reposition |
| `…::TestAudit` | 2 | the `queue.enqueue` audit row carries the placement decision (`policy`, `basis`, `position` matching the entry); a 422 placement refusal leaves a `request.denied` row |
| `backend/organization/tests/test_walk_in_config.py` | 23 | default view, platform set and bounds, staff/doctor read, stored value round-trip, malformed fallback, foreign-org 404, audited write with before/after, both reserve modes, partial update, unrelated `config` block preserved on write, reset to default, 403 for receptionist and doctor, 404 for a foreign administrator, unknown policy 422, empty body 422, four reserve-bound refusals, a refused write changes nothing, platform-admin-only option narrowing, facility cannot select outside the set, narrowing below the current policy falls back to `end_of_queue`, empty/unknown option set 422 |
| `backend/queuing/tests/test_queue.py::TestWalkInPolicies` (rewritten) | 6 | each policy is reachable through configuration; `walk_in_policy` in the body is **ignored** (the entry is appended at 2 although the body asked for position 1); an unknown stored policy falls back |
| `frontend/tests/queue-walk-in-policy.test.mjs` | 10 | unknown policy ⇒ `end_of_queue`; only `staff_placement` asks for a position; every policy label exists in **bn and en**; the body never carries `walk_in_policy` and carries `position` only under staff placement; unusable positions refused before the request; missing doctor/patient refused; the page reads `/walk-in-config`, uses the tested module and contains no `walk_in_policy`/`WALK_POLICIES`; the backend request models no longer declare the field; the page never computes a position |

### 3.2 Executed results

| Run | Command | Result |
|---|---|---|
| MP-10 placement module | `python -m pytest backend/queuing/tests/test_walk_in_placement.py -q` | **15 passed, 0 failed** (27.23 s) |
| MP-10 organization module | `python -m pytest backend/organization/tests/test_walk_in_config.py -q` | **23 passed, 0 failed** (77.35 s) — first run of the audit test failed and is explained in §3.4 |
| Both MP-10 backend modules together | `python -m pytest backend/organization/tests/test_walk_in_config.py backend/queuing/tests/test_walk_in_placement.py -q` | **38 passed, 0 failed** (87.09 s) |
| Whole backend tree | `python -m pytest backend -q -p no:cacheprovider` | **`847 passed, 0 failed in 1292.53s (0:21:32)`** — `runs/backend-mp10-2026-11-24.log` |
| Frontend tree | `cd frontend && npm test` | **383 tests / 379 pass / 2 fail / 2 skipped** — the two reds are the pre-existing Q-3 pair (`banglanamesense-dataset`, `calendar-render`), unchanged; +10 tests versus the MP-08 run (373 → 383), all green |
| MP-10 frontend module | `node --test tests/queue-walk-in-policy.test.mjs` | **10 passed, 0 failed** |

**Arithmetic.** The MP-08 tree ran **808 passed**. This window adds 38 backend tests (15 placement + 23 configuration)
and one more in `TestWalkInPolicies`, whose rewritten form has 6 tests where the retired version had 5: 808 + 38 + 1 =
**847**, which is exactly what the whole-tree run reports. No test was deleted and no failure was suppressed.

### 3.3 Mutation check — the tests are not vacuous

One negative control, on the behaviour the plan singles out ("a real `reserved_capacity` pool"):

- **Mutation:** `backend/queuing/placement.py` line 257 changed from `if policy == "reserved_capacity":` to
  `if policy == "reserved_capacity" and False:  # MUTATION: pool not enforced`, so a walk-in under that policy falls
  through to the append path — exactly the pre-task behaviour.
- **Result:** `python -m pytest backend/queuing/tests/test_walk_in_placement.py -q` → **`2 failed, 13 passed`**
  (`test_walk_ins_fill_the_reserved_block_then_append`, `test_percentage_mode_uses_the_published_capacity`), log
  `runs/evidence-mp10-mutation.log`. The two survivors are the correct ones: "the pool is a guarantee, not a cap" and
  "no published hours ⇒ no pool" hold under both behaviours, so they must not fail.
- **Restore:** the file was restored from a byte copy; SHA-256
  **`A59B61E737136AAE00B9E6D9105D97B795D858576ED67A63DBD3EA9667A93819`** before and after — identical — and the module
  then re-ran **15 passed** in 28.16 s.

### 3.4 The first whole-tree run failed, and here is why

The first whole-tree run reported `1 failed, 846 passed in 1379.69s`, the failure being
`test_the_facility_administrator_selects_a_policy_and_it_is_audited`. The cause was in the **test**, not the code:
it selected the audit row with `order_by(AuditEvent.id.desc()).first()`, and `AuditEvent.id` is `uuid4()` — a random
identifier, not a sequence, so "descending id" is not "newest". It passed in isolation only because no earlier row
matched. The test now asserts the *transition it caused* exists (`before.walk_in_policy == "end_of_queue"` and
`after.walk_in_policy == "reserved_capacity"`), which is order-independent and still fails if the audit write is
removed. The module then passed alone (23/23), with its sibling module (38/38) and in the whole-tree re-run quoted in
§3.2.

The same latent mistake is present in `backend/organization/tests/test_queue_calling_config.py:133`, a pre-existing
test that belongs to another task's evidence. It is recorded in §5 (item 4) rather than edited here; it passes today
because the fixture resets the block, and it could misread its own audit row only if a second
`queue_calling_config.updated` row ever targeted the same organization.

---

## 4. Verification evidence

**This task is TESTED, not VERIFIED.** Evidence vocabulary (`.clinerules` §7): a green suite is not VERIFIED, and a
source-contract frontend test is weaker still.

| Claim | Evidence | Grade |
|---|---|---|
| The four policies behave differently | 15 tests in `test_walk_in_placement.py`, executed; positions and `position_history` read back from PostgreSQL | TESTED |
| A policy change never reorders an active queue | `TestPolicyIsProspective::test_changing_the_policy_moves_nobody` — positions and the `queue.reposition` count are compared before and after the change | TESTED |
| Every change is audited | `walk_in_config.updated` before/after (organization test) and the placement decision inside `queue.enqueue` (queue test), read back from `audit_events` | TESTED |
| The per-request parameter is retired | the field is gone from both request models; a test sends it and proves it has no effect; a frontend test asserts the page cannot send it | TESTED |
| The facility's policy is what the form shows | `frontend/lib/queue/walk-in.js` unit tests + page source assertions | TESTED (source-contract) |

**What would make it VERIFIED**, and why it did not happen here: start the stack, set the policy with
`PUT /api/v1/orgs/{id}/walk-in-config` as the facility administrator, register two walk-ins from the queue page and
observe the resulting positions in the browser *and* in the `queue_entries` table. That is D8 runtime evidence and it
needs a live credential and a reachable browser — registered as B-2, unchanged by this task.

---

## 5. Known limitations and remaining gaps

1. **Deviation from plan §8 rule 3 — no Alembic revision.** The rule says MP-10 requires its own revision; the
   implementation stores the policy in `organizations.config["queue_config"]`, which already held the reserve split
   and is what the booking path reads. A table would have duplicated that reader. The schema is unchanged, so there
   is no migration to sequence. **Flagged for the Product Owner:** if the intent was that this configuration must be
   a first-class table (reportable, indexable, joinable), that is a different task and should be stated as such.
2. **A refused placement consumes the day's next token number.** `_next_sequence()` runs before `place_entry()` in
   both write paths, because reversing that order would invert the lock order against `check-in` and risk a deadlock.
   A refusal (staff placement without a position, or an out-of-range one) therefore leaves a gap in the token series
   for that doctor/day. No token is reused and no patient is affected.
3. **`first_come` orders by the registration clock.** Existing rows are ordered by `created_at`, the new entry by its
   `arrived_at` (or "now"). A back-dated arrival is accepted without limit and without a separate audit event; the
   `queue.enqueue` row records the position and basis, not the arrival time. A future timestamp sorts last, which
   appends.
4. **Pre-existing latent flake, not fixed:** `backend/organization/tests/test_queue_calling_config.py:133` selects its
   audit row with `order_by(AuditEvent.id.desc())`, and that id is a random UUID (see §3.4). Left untouched because it
   is another task's evidence.
5. **No administration screen.** The policy is set through the API only. BR §25 does not require a screen and the
   plan schedules none in this window; the queue page deliberately only *reads* the policy.
6. **`reserved_capacity` percentage mode needs published hours.** The pool is a share of the seats the doctor
   publishes in `schedules.slot_templates`; a doctor with no published schedule has no pool, so walk-ins append. It
   is tested, and it is the honest reading of "reserve a percentage of capacity" when no capacity is published.
7. **The platform option set is per organization.** "Super Admin defines available options" is implemented as
   `allowed_walk_in_policies`, written by a `platform.admin` holder for one organization at a time. There is no
   platform-wide catalogue; a new organization gets all four until an administrator narrows it.
8. **Queue scope is doctor + day, not branch.** The pool and the shift are computed over the doctor's day queue, so a
   doctor working in two branches on one day shares one position space and one pool. That is the pre-existing model
   (tokens are allocated per doctor/day), not a choice made here; MP-11's token-scope task is where it changes.
9. **Nothing in this task is ACCEPTED.** No owner signature has been requested or given.

---

## 6. Governance and Skill Compliance

**Domains identified** (`.clinerules` §4 routing table): Backend API / service endpoints; Multi-tenant data and
org/branch isolation; Frontend UI and forms; Database schema (assessed, unchanged); Documentation.

**Governance documents read in this session, not remembered:** `docs/governance/AMSDP_Docs_Index_V1.0.md`,
`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (§4 gates, §5 roadmap, §6 WP-C, §7 DoR/DoD, §8
sequencing), `docs/product/AMSDP_Business_Rules_V1.0.md` §24–§26 (§25 quoted in §1),
`docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`, `.clinerules`.

**Task selection.** MP-09 and MP-13 are `GATED (PO-04)`, so §8 rule 5 excludes them; MP-10's dependency (MP-02) is
satisfied and it is the next non-gated task in the plan's own order (WP-C; configuration before behaviour, §8 rules
2 and 4). The selection was made by reading the plan, not by preference.

**Non-negotiables (`.clinerules` §3) — evidence in this tree:**

| Rule | How it is met here |
|---|---|
| Access is enforced server-side; the UI is never the boundary | The policy is resolved and validated in `placement.place()` and in the organization router; the page only mirrors it. A body that still carries `walk_in_policy` changes nothing — proven by a test |
| The principal's org comes from the token | Every query filters on `auth.organization_id`; neither the placement nor the config endpoint reads an organization from the body |
| Cross-tenant access fails closed with 404 | `_scoped_org()` → 404; tested for a foreign administrator on `GET` and `PUT` |
| One tenant key | `organization_id` only; no second tenant column (no schema change at all) |
| Audit is append-only; denials are recorded | Writes to `audit_events` go only through `record_audit()`; the 422 path is covered by `request.denied` and a test asserts the row exists |
| Forward-only migrations only for schema change | No schema change, no migration (§5 item 1) |
| No invented capabilities | Nothing is claimed VERIFIED; the frontend evidence is labelled source-contract |

**Skills.** No skill package is installed in this workspace (`.clinerules` §5), so none was used and none is claimed.
The work followed the existing sibling implementations instead: `organization/queue_calling_config.py` and
`organization/appointment_config.py` for the router shape, `queuing/recovery.py` for the renumber/audit pattern, and
`frontend/lib/queue/queue-call.js` for the pure-module-plus-test pattern.

**Execution boundaries (§9).** This task touched 11 files, beyond the §9 *local-model* triage limit; that limit is
scoped to the local-model context, and this window ran on the frontier profile under the owner's continuous-execution
mandate. No destructive Git command was issued; nothing was staged, reverted or cleaned. The one negative control
(§3.3) mutated a single file from a byte copy and restored it byte-identically.

**Written to:** `docs/implementation/AMSDP_MP-10_Walk_In_Policy_Configuration_Implementation_Report_V1.0.md` (this
file). No document was moved or renamed, so no migration-manifest entry is due; the Docs Index is updated in the same
task (`.clinerules` §12).
