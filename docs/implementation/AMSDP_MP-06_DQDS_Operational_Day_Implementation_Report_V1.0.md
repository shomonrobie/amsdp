# AMSDP — MP-06 Implementation Report: facility-local operational day on the DQDS board

**Task:** MP-06 (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6, WP-B)
**Priority:** P0 · **Depends on:** — (none; MP-06 gates MP-36 and MP-44)
**Date:** 2026-11-24 · **Checkout:** `E:\amsdp` · **Branch:** working tree, uncommitted
**Evidence status reached: TESTED** (code reachable and named tests executed here; runtime verification on the
live stack is **not** available from this host and is recorded as such, not claimed)

---

## 1. Requirement

The plan's WP-B row, verbatim:

> **MP-06** — `queuing/display.py:138` → `operational_today(session, org)`. Current state: **VERIFIED defect**.
> P0. Deliverables: one-line fix, regression test. Acceptance & verification: *New test pins a 01:00-Dhaka
> instant and asserts today's tokens appear; existing `test_dqds.py` stays green.*
> Risk: *Org resolution added to a public endpoint — must remain org-scoped.*

Business rule basis: BR §8 — operational dates follow the **facility's** configured time zone while stored
timestamps remain UTC. The DQDS is the room the facility looks at, so "today" must roll over at *its* midnight.

### 1.1 The defect as found

`backend/queuing/display.py`, in the public board route:

```python
today = date.today()          # the container's clock, not the facility's
```

`date.today()` reads the process clock. The deployment runs `Asia/Dhaka` (UTC+6) inside a container that is
not required to carry that zone. For the first six hours of every Dhaka day — local midnight to 06:00 — a
UTC-clock container reports the **previous** date, so the public board filtered on the wrong day and published
yesterday's tokens while today's queue was invisible. The same defect class is GAP-03/GAP-25, and appears in
`seed_demo.py` (MP-05); the dashboard was already compliant.

---

## 2. Change

One call site, in the public route. Nothing else in the module was touched.

```diff
-from datetime import date, datetime, timezone
+from datetime import datetime, timezone

 from common.database import SessionFactory
 from common.models import Organization, Branch, QueueEntry, Doctor
+from common.timeutil import operational_today

         org, branch = _org_branch_or_404(session, org_code, branch_code)
-        today = date.today()
+        # Facility-local day (BR §8), never the server's date: the board must
+        # roll over at the facility's midnight, not the container's. The org
+        # comes from the path and is already tenant-validated, so the zone
+        # lookup stays inside this tenant.
+        today = operational_today(session, org.id)
```

The `date` import was dropped because it became unused; `datetime`/`timezone` are still used by the
cache-header and `Retry-After` maths.

### 2.1 Tenancy (D3) — the risk the plan named

`operational_today(session, org.id)` receives the organization **already resolved and tenant-validated** by
`_org_branch_or_404`, which is what produced the 404 for unknown, cross-org and inactive organizations in the
first place. The zone lookup reads `organizations.timezone` for that one organization, so:

- no new query path is introduced on behalf of the caller;
- the caller still cannot choose an organization — it comes from the path and is validated exactly as before;
- the payload, the 404 contract, the `Cache-Control` contract and the rate limiter are unchanged.

`common.timeutil.facility_zone` falls back to `AMSDP_FACILITY_TZ` and then `Asia/Dhaka` when the column is
unreadable, so a bad column value cannot take the board down.

---

## 3. Tests

### 3.1 New regression tests

Two tests, appended to the existing DQDS suite rather than a new file, because they assert the same public
contract as their neighbours.

**`test_dqds_uses_the_facility_day_not_the_server_day`** — the rollover itself. The clock is frozen at
`2026-11-23T19:00Z`, which is **01:00 on 24 November in Asia/Dhaka**:

- `common.timeutil.datetime` is replaced by a frozen subclass, so `operational_today` sees that instant;
- `queuing.display.date` is set to a stub whose `today()` answers **23 November** — the server's own calendar,
  i.e. exactly what the old code read. After the fix the module does not even import `date`, so the stub is
  inert; if the route ever reads the server clock again the stub answers "the 23rd" and the test fails;
- three entries are inserted for the demo branch: `F-024` in consultation and `F-025` waiting on the facility
  day, `F-023` in consultation on the server day;
- the board must report `currently_serving == "F-024"` and `patients_waiting == 1`.

**Why the assertion is on `currently_serving`, and not on a token appearing in the body:** the first version of
this test asserted that `F-024`'s token was in the payload and that `F-023`'s was not — which was **vacuous**.
The public schema deliberately never publishes a *waiting* token (privacy, BR §33); only the serving token is
published. The test was wrong, not the code, and it was rewritten after the payload was read properly. This is
the second test-authoring defect this session caught by running the test rather than trusting it.

**`test_dqds_honours_the_configured_facility_zone`** — the second, independent case, which the plan did not ask
for but the fix implies. The same instant (`2026-11-23T19:00Z`) with the org configured `America/New_York` is
**14:00 on the 23rd**, so the board must publish the 23rd's token (`N-023`), not the 24th's. A board hard-wired
to `Asia/Dhaka`, or to the server clock, passes the first test only by coincidence and fails this one. It proves
the day comes from `organizations.timezone` — data — and not from a constant.

Both tests restore the org's timezone and clear the queue in a `finally` block, so neither leaks state into the
rest of the suite (which is what keeps the other 24 tests in the file green).

### 3.2 Mutation check

The old line was reinstated (`today = date.today()`, `date` re-imported) and the whole DQDS file run:

```text
$ python -m pytest backend/tests/test_dqds.py -q
MUTATED
['from common.timeutil import operational_today', 'today = date.today()']
...
FAILED backend/tests/test_dqds.py::test_dqds_uses_the_facility_day_not_the_server_day
FAILED backend/tests/test_dqds.py::test_dqds_honours_the_configured_facility_zone
2 failed, 24 passed, 3 warnings in 3.85s
```

The failure is the defect, visible:

```text
>           assert dina["currently_serving"] == "F-024", dina
E           AssertionError: {'doctor_name': 'Dr. Dina', 'currently_serving': 'F-023', 'patients_waiting': 0}
E           assert 'F-023' == 'F-024'
```

With the defect restored the board serves the **server** day's token — the exact production symptom. The file was
then restored from a byte-identical copy: SHA-256 `3F9FD04789B5D1F4F9C9755D04665F44C66DE334E0720A34E7F17DA819595E73`
for both `runs/display.py.orig` and `backend/queuing/display.py`. Full output:
`runs/evidence-mp06-mutation.log`.

### 3.3 Executed results

| Run | Result |
|---|---|
| `backend/tests/test_dqds.py` alone, **fix in place** | 26 passed |
| Whole backend tree, baseline at head `c4d8e2a91f60` (`runs/backend-baseline-2026-11-24.log`) | `791 passed, 0 failed in 745.12s` |
| Whole backend tree, final, after both MP-06 tests and MP-05's (`runs/backend-final-2026-11-24.log`) | **`796 passed, 0 failed in 816.87s`** |

791 + 5 = 796: the three MP-05 tests and these two. No test was removed, and no failure is hidden in the totals.

---

## 4. Verification evidence

| Criterion | Status | Evidence |
|---|---|---|
| Code reachable and used by the public route | **IMPLEMENTED** | import + call site in `dqds_board`, read back by the route test |
| New tests pass on this tree | **TESTED** | `pytest backend/tests/test_dqds.py -q` → **26 passed in 2.14s**; both names confirmed by `--collect-only` (`runs/evidence-mp06-fixpass.log`) |
| New tests fail with the defect restored | **TESTED** | mutation: **2 failed, 24 passed**, exactly the two day tests (`runs/evidence-mp06-mutation.log`, §3.2) |
| File restored byte-identically after mutation | **VERIFIED** | SHA-256 `3F9FD047…95E73` equal for `runs/display.py.orig` and `backend/queuing/display.py` |
| Existing DQDS suite still green | **TESTED** | 24 non-day tests pass in the same mutated run, and all 26 in the fix run |
| Whole backend tree green | **TESTED** | `796 passed, 0 failed in 816.87s` (`runs/backend-final-2026-11-24.log`) |
| 01:00-Dhaka behaviour on the **live** board | **NOT AVAILABLE** | no live DB/container access from this host; the instant is pinned in the test instead |

**Not claimed: VERIFIED.** A second independent artefact (a live board request across a real Dhaka midnight)
does not exist for this host, and the plan's evidence vocabulary (§7 of `.clinerules`) forbids upgrading on the
strength of a green suite alone.

---

## 5. Known limitations and remaining gaps

1. **Live confirmation pending.** The rollover is proven by a pinned-clock test, not by a live observation.
   MP-36's display signing must not claim it covers this until a real (or reconstructed) boundary observation
   exists.
2. **MP-44 residue.** Appendix D.4 rule 11 requires MP-44 to land *with* MP-06 so queue, dashboard, display and
   seed share one helper. The display call site (this task) and the seed (MP-05) are now on the helper; the
   **rendered facility clock** and the explicit 23:59→00:00 boundary test remain MP-44's own acceptance
   criteria and stay open.
3. **Adjacent server-local reads, reported not changed** (D1: implement the named requirement only):
   - `backend/patient/main.py:80` — `today = today or _date.today()`
   - `backend/patient/main.py:50` — `if d > _dt.now().date():`
   Both are patient-module date semantics, outside the queue board. They are candidates for MP-44 follow-up or
   a new task if the owner wants the whole surface on the facility day.
4. **Rate limiter untouched.** `_DQDS_RATE` remains the in-process limiter of GAP-20 (MP-25); MP-43 re-keys it
   per display. MP-06 neither improves nor worsens it.

---

## 6. Governance and Skill Compliance

| Item | Detail |
|---|---|
| Governing documents read this session | `.clinerules` §1–§12; `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-B, §7, §8, Appendices A and D (D.1, D.3, D.4 rules 10–14); `backend/common/timeutil.py`; `backend/queuing/display.py`; `backend/tests/test_dqds.py`; `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Business rules applied | BR §8 (operational date = facility time zone; storage stays UTC) via `common.timeutil.operational_today`, whose docstring cites it |
| Skills | **None installed** in this workspace (`.clinerules` §5: no `.clinerules/skills/`, `.claude/skills/`, repo `skills/`). Governance documents used in their place; no skill use is claimed |
| D1 code scope | One call site plus the import it requires; no unrelated refactor |
| D2 server-side enforcement | Unchanged — the route is public by design; no authorisation path added or weakened |
| D3 tenancy | Organization from the path, validated by `_org_branch_or_404` **before** the zone read; 404 parity preserved; no second tenant column introduced |
| D4 audit | No state change → no audit row expected, and none written. Nothing suppressed |
| D5 migration | None required — `organizations.timezone` already exists (`common/models.py`, default `Asia/Dhaka`) |
| D6 tests | Positive **and** negative assertion in one test; mutation-checked |
| D7 execution | Commands run here; output quoted; unexecuted claims avoided |
| D8 runtime | **BLOCKED** — no live container/DB access from this host; stated, not faked |
| D9 report | This file, under `docs/implementation/`, containing this section |
| Secrets | None read, logged, quoted or written; the test uses no credential |

**Report placement.** `docs/implementation/` per `.clinerules` §11 (implementation subject). No file was moved
or renamed, so no migration-manifest entry is required. The docs index is updated in the same task (§12).

