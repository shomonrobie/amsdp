# AMSDP — MP-01 Reconciliation and PostgreSQL Evidence Report, V1.0

**Date:** 24 November 2026 · **Checkout:** `E:\amsdp` (Windows workstation) · **Branch:** `hackathon-mvp`
· **HEAD:** `a4ddc2cf58e019b57dccf59f3a859743e3c48430`
**Task type:** dependency verification (MP-01), environment discovery, and the first execution of tests that three
previous windows recorded as **UNRUN**. No production action, no migration of any existing database.
**Status:** MP-01 is **not complete** — it needs the *live* database, which still has no reachable credential. But the
blocker that made MP-17/18/19/20/22 "unrun" was **not** what the register said, and this report corrects it.

---

## 1. MP-01 — what was asked, what was found

MP-01 is *"prove the runtime — never re-apply an applied migration"*: on the Ubuntu host, read `alembic current`,
confirm `c4d8e2a91f60`, read the three tables, and quote the output. Appendix E of the plan redefined it from
"migrate" to "verify".

| Check (read-only) | Result |
|---|---|
| Live deployment reachable from this host | **Yes.** TCP `192.168.68.108:8110` and `:3100` open; `GET /health` → **200**, `GET :3100/` → **200** |
| Live PostgreSQL reachable | **Yes.** TCP `192.168.68.108:5433` open |
| SSH to the host | **No** — `:22` refused, unchanged from the 2026-11-24 baseline report |
| Database credential for the live DB | **Absent.** `POSTGRES_PASSWORD`, `AMSDP_DATABASE_URL`, `AMSDP_DB_HOST/PORT/NAME` all **unset** in this shell; `.env.local` carries two API keys only. A connect attempt fails with `fe_sendauth: no password supplied` |
| `alembic` against the live DB | **Not possible** — no credential, and the plan forbids an unconditional upgrade. **Nothing was run against the live database.** |
| Migration graph, static | **17 revisions, single head `b2e5c7d91a04`**, chain `… ← a9c4e1f7b2d8 ← a7c3f19d2b64 ← c4d8e2a91f60 ← b2e5c7d91a04` |

**A material discrepancy, recorded rather than resolved.** The plan and the deployment baseline say the live database
is at **`c4d8e2a91f60`**. The working tree's head is now **`b2e5c7d91a04`** — MP-16's `add_schedule_blocks` revision,
authored after that baseline was written. So one of two things is true, and this host cannot tell which:

- the live database is **one revision behind this tree**, and `schedule_blocks` does not exist there; or
- the live database was migrated again and is at `b2e5c7d91a04`, which is not recorded anywhere in the tree.

**MP-01 therefore remains BLOCKED, on a narrower and more precise reason than before:** the HTTP runtime is proven and
the revision graph is proven, but the live revision and the three (now four) tables cannot be read without a credential,
and no upgrade may be run without owner authorisation. That is recorded as **B-4** in the register.

---

## 2. What the register said about PostgreSQL, and why it was wrong

Every window from MP-16 onward carried "no PostgreSQL on this host — 5433 refused" as the reason its behavioural
tests were unrun, and O-1 carried "31 identity tests cannot execute". Both were true about the ports that were probed
(`127.0.0.1:5432/5433/5434`) and **false about the database that was actually available**.

MP-16's own report records the DSN it used: `postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp`. Port **55432**, not
5433. Probed on 2026-11-24 in this window:

```
port 55432 open=True
connected  amsdp
alembic_version: ['b2e5c7d91a04']
to_regclass: ('schedule_blocks', 'voice_packs')
```

A local development database is running, at the head of this tree, with the MP-16 table present. The earlier windows
looked one port to the right. **This is the defect: a probe list that was never reconciled against the project's own
recorded command.** It is corrected here and the register carries the correction.

### 2.1 The isolated database used for this window

The tests were **not** pointed at `amsdp` (the development database MP-16 seeded) and not at the live deployment.
A fresh database was created for this window and migrated from the first revision:

| Step | Command (exact) | Output |
|---|---|---|
| Create | `psycopg2 … create database "amsdp_verify_2829"` | `amsdp_verify_2829 created` |
| Migrate | `cd backend; $env:AMSDP_DATABASE_URL='postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_verify_2829'; python -m alembic upgrade head` | the whole chain, ending `Running upgrade c4d8e2a91f60 -> b2e5c7d91a04, add_schedule_blocks`, **exit 0** |
| Confirm | `python -m alembic current` | **`b2e5c7d91a04 (head)`** |

This is a genuine, independent confirmation that the chain applies cleanly from empty on this tree — the same property
MP-16 claimed for `b2e5c7d91a04` and the one MP-35's future revision must preserve.

---

## 3. Results — the tests that were recorded as unrun

All runs: `AMSDP_DATABASE_URL=…/amsdp_verify_2829`, from `E:\amsdp\backend`.

| Suite | Tests | Result | Meaning |
|---|---:|---|---|
| `tests/test_dashboard.py` (MP-22) | 12 | **12 passed in 2.51s** | after the fix in §4.1 |
| `doctor/tests/test_doctor_mobile_duplicates.py` (MP-17) | 12 | **11 passed, 1 failed** | §4.2 |
| `scheduling/tests/test_schedule_audit.py` (MP-18) | 12 | **8 passed, 4 failed** | §4.3 |
| `identity/tests` (O-1, MP-19/20) | 75 | **71 passed, 4 errors** | §4.4 |

First combined run, before the dashboard fix: `6 failed, 30 passed in 29.54s`.

**What this changes about previous grades — and what it does not.** MP-17 and MP-18 were graded on DB-free evidence
and said so; the behavioural half is now measured, and it is **not green**. Their reports are not rewritten: their
sections on "unrun here" remain true of the window they describe, and the register carries the superseding figures

---

## 4. Defects found by running the tests, and what was done with each

### 4.1 D-0 — MP-22 date selector accepted an unpadded date — **FIXED**

`GET /api/v1/dashboard/today?date=2026-1-5` returned **200**; the documented contract (and the test) is **422**.
Cause: `datetime.strptime(date, "%Y-%m-%d")` accepts unpadded fields, so the selector's contract was wider than
"`YYYY-MM-DD`" and an ambiguous string travelled to the query.

Fix (`backend/appointment/dashboard.py`): after parsing, require an exact round-trip —

```python
if today.isoformat() != date:
    raise HTTPException(422, "date must use YYYY-MM-DD")
```

Re-run: `tests/test_dashboard.py` → **12 passed in 2.51s**. The six MP-22 endpoint cases are green for the first time.

### 4.2 D-2 — MP-17: an organisation admin gets a generic 403, not the platform-administrator refusal — **OPEN**

```
FAILED test_only_a_platform_administrator_may_grant_the_allowance
  assert 'platform administrator' in '{"detail":"insufficient permissions"}'
```

The route (`doctor/profile.py:1010`) *does* refuse with `403 "only a platform administrator may change the doctor
mobile-number duplicate policy"`, but the refusal in the run comes from the **capability dependency**
(`require_permission("org.manage")`) that runs before the handler body. So the caller never reaches the message the
docstring promises, and an auditor sees a generic denial where the code intends a specific one.

**Not fixed in this window, deliberately.** Which gate should fire first is a design decision — the two candidates are
(a) check platform administration before the capability, or (b) keep the capability first and accept the generic
message, changing the test. Both alter an authorisation surface, and §3 requires that to be explicit. The security
property itself is intact: the write was refused, and the test proves nothing was written.

### 4.3 D-1 — MP-18: the projection audit fires twice, or when nothing moved — **OPEN, grade reduced**

Four of the twelve PostgreSQL tests fail, all in `TestScheduleProjectionAudit`:

| Test | Expected | Observed |
|---|---|---|
| `test_creating_a_session_audits_the_schedule_projection` | one event, `before = {09:00-10:00: 1}` | `before` already contains the new window |
| `test_moving_a_session_audits_both_window_sets` | one event | **two** events (`assert 2 == 1`) |
| `test_retiring_the_last_session_audits_the_window_disappearing` | one event | **two** events |
| `test_an_edit_that_does_not_move_a_window_writes_no_schedule_event` | no event | **one** event |

Every symptom points the same way: the "before" snapshot in `audit_template_projection`
(`stored_before = list(schedule.slot_templates or [])`) is not the pre-write projection the comparison needs, so the
helper records a change that either already happened or did not happen at all. The static guard MP-18 shipped — "every
write route calls an audit helper with `after=`" — passed while the behaviour was wrong, which is exactly the
limitation its own report predicted and why it shipped two guards rather than one.

**Not fixed in this window.** The fix is a state-capture change inside a write path shared by four services and the
audit trail; guessing it without reading the ORM loading order risks a second silent mutation, which is the defect
class MP-18 exists to close. Recorded as **D-1**; MP-18's grade is reduced to **TESTED (static guard only) — 4 of 12
behavioural tests FAIL**.

### 4.4 D-3 — identity: four `TestDoctorLink` fixtures error on a fresh database — **OPEN (test fixture)**

```
ERROR identity/tests/test_identity.py::TestDoctorLink::test_create_with_doctor_link
  psycopg2.errors.ForeignKeyViolation: insert or update on table "doctors" violates
  foreign key constraint "doctors_organization_id_fkey"
```

`71 passed, 4 errors`. The four are **setup** errors, not assertion failures: the class inserts a doctor for an
organisation row the fixture assumes another test has seeded. On the shared development database it passes because the
row is already there; on a clean database the ordering matters. A test-isolation defect — the class of problem a fresh
database is supposed to expose.


---

## 5. Files changed in this window

| File | Change |
|---|---|
| `backend/appointment/dashboard.py` | D-0 fix: exact `YYYY-MM-DD` round-trip before the query |
| `frontend/**` (five pages, `lib/i18n.js`, six test files) | MP-28 — see its own report |
| `docs/implementation/AMSDP_MP-28_…_V1.0.md`, this report | new |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`, `docs/governance/AMSDP_Docs_Index_V1.0.md` | updated |

**Database state:** `amsdp_verify_2829` was created for this window and **left in place** so the results can be
reproduced; the development `amsdp` database and the live deployment were not touched. No migration was run against any
existing database. No test was weakened, skipped or deleted.

---

## 6. What is still outstanding

1. **B-4 — live database credential and owner authorisation.** MP-01 cannot close without reading the live
   `alembic_version`; MP-25 depends on it.
2. **D-1 (MP-18), D-2 (MP-17), D-3 (identity fixture)** — each needs a decision or its own fix step.
3. **The live-revision discrepancy of §1** — resolve by reading `alembic_version` on `192.168.68.108:5433` when a
   credential exists. Until then no document should assert which revision the live database is at.
4. **The remaining Q-3 pair** — dataset provenance and the module that will not load; unchanged.

---

## 7. Governance and skill compliance

| Requirement (`.clinerules`) | Compliance |
|---|---|
| §2 automatic routing | Domains: database/migration, deployment, backend API, audit. Read: Docs Index first; plan §6 (MP-01), Appendix E, the MP-17/18/22 rows; the MP-16 report (which held the DSN that corrected the blocker) |
| §3 non-negotiables | No live database write, no migration on an existing database, no credential value read into any output (only *presence* was tested), no grade promoted without execution, no test weakened |
| §4 routing table | Database-migration and deployment rows applied; **no skill installed**, stated rather than invented |
| §6 compliance reporting | This section |
| §7 evidence standard | Every number is a quoted run; §3 marks which grade improved (MP-22) and which fell (MP-18) |
| §9 execution boundaries | Read-only probes to the live host; a **new** isolated database for tests; no destructive git command; short captures outside the tree |
| §11/§12 | Reports in `docs/implementation/`; index updated in the same task; nothing deleted |

---

*End of report.*

and the defects. MP-22's endpoint half, previously "unrun", is now **green** — which is the only grade that improves.
