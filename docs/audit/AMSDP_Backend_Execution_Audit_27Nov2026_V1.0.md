# AMSDP — Independent Audit of the 27 November 2026 Backend Execution — V1.0

| | |
|---|---|
| **Document** | `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` |
| **Audit type** | Independent, read-only audit of a claimed execution window — not a re-run, not a review of the auditor's own work |
| **Subject** | The backend test execution recorded in `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §15 (27 November 2026): **1,061 passing tests** on two scratch PostgreSQL databases, five test corrections, and the register / Docs Index updates that accompany them |
| **Audited revision** | Branch `hackathon-mvp`, `HEAD = 71226e8faaef477ae3ac5e744b023451acb0c5bf`, equal to `origin/hackathon-mvp`, working tree carrying six modified files and no untracked files |
| **Audit performed** | 2026-11-27 (original audit, delivered in conversation) and re-verified 2026-11-27 during this resolution phase |
| **Companion documents** | `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` (evidence record, F-07); `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` (F-02 decision request) |
| **Verdict** | **INDEPENDENT AUDIT PASSED WITH CONDITIONS** |

---

## 1. Executive conclusion

The execution reported in register §15 **happened, and it happened as described in its headline
numbers.** Two whole-suite runs are preserved with their exact summary lines —
`1061 passed, 66 warnings in 541.58s (0:09:01)` and `1061 passed, 50 warnings in 542.27s (0:09:02)` —
and each is bound to a *different* scratch database by the retained command line, not by narrative.
An independent collection artefact shows the suite really is 1,061 tests across 52 modules, so the pass
count is not a selected subset. The migration log shows the full chain applied from an empty schema to
the single head `e1b7c4a9d236`. The five corrected tests are genuine, the product code was not touched,
and nothing was committed or pushed.

**Four of the five test corrections are justified outright; the fifth is justified with concerns.**
The rate-limit correction (defect 5) is the one to watch: it makes the suite green by clearing a
*shared, process-global* budget between tests, which is correct for a single-process run and
unproven — arguably unsafe — if the suite is ever parallelised.

**Nothing in the window is VERIFIED and nothing is ACCEPTED.** No browser ran, no CI ran, and no
Product Owner decision was sought. The register says so itself; this audit confirms the register is
right to say so.

The conditions attached to the pass are the twelve findings in §12, of which **two are MEDIUM**
(F-02, the MP-46 denial-record capability field, and F-04, the rate-limit fixture's blast radius) and
**none is HIGH or CRITICAL**. Two further items were found during this resolution phase and are
reported separately as **F-13** rather than folded into the original twelve: the local server is
**PostgreSQL 16.4**, not 17 as register §15.1 states, and the second "pristine" database has no
retained creation or migration record.

**What the verdict means in practice.** The evidence is sufficient to treat the backend suites as
**TESTED on a disposable PostgreSQL 16.4 instance in this checkout**, and insufficient to treat any work
package as VERIFIED, browser-proven, CI-proven or accepted. That is exactly the claim the register
makes, and it is the claim the evidence supports.

---

## 2. Audit scope and methodology

### 2.1 In scope

1. The five test corrections in register §15.3 — whether each is justified by the product contract it
   tests, and whether any of them weakens what the suite proves.
2. The execution claims: pass count, duration, database binding, suite completeness, repeatability.
3. The migration claim: zero → head `e1b7c4a9d236`, one head, three additive revisions.
4. The work-package statuses in §15.4 — whether any exceeds TESTED, and whether the per-module figures
   match the tests that exist.
5. The documentation claims: the register's additive edit, the Docs Index revision, the counts.
6. Governance: `.clinerules` §3/§7/§11 compliance, the evidence standard, and the handling of the
   owner's own uncommitted `.clinerules` edit.

### 2.2 Out of scope, and deliberately so

- **No re-run.** The audit did not execute pytest, so it verifies the *record* of a run, not a fresh run.
  (The resolution phase forbade execution entirely — mandate §8, §11.)
- **No database session.** Neither phase connected to PostgreSQL. Database facts come from retained
  command output and from local server files (§6.3).
- **No browser, no CI, no Docker, no deployment.** Those are §11's outstanding requirements.
- **No judgement on business value.** The audit asks whether claims are supported, not whether the work
  is the right work.

### 2.3 Method

1. **Baseline first** — branch, `HEAD`, remote equality, staged/untracked counts, per-file diffstat,
   before reading any claim.
2. **Diff against claim** — each correction read against its own diff *and* against the product code it
   exercises. A correction is "justified" only if the product contract makes the old assertion wrong or
   vacuous, not merely if it makes the test pass.
3. **Contract tracing** for the corrections that change what is asserted (MP-45 field suppression,
   MP-46 denial row): read the emitter, the route resolver and the audit writer, and ask whether the new
   assertion can fail if the feature regresses.
4. **Artefact reading** — the retained logs, tail-first for summary lines, then the command history that
   binds each log to a database.
5. **Static counts** — `def test_` counts per module against the claimed statuses; collected count
   against the pass count.
6. **Static migration-graph inspection** — single head, unbroken `down_revision` chain, revision file
   presence.
7. **Document arithmetic** — register and index sizes, CRLF adjustment, insertion/deletion counts, `.md`
   inventory.
8. **Independent second artefacts** wherever a claim could rest on one file (collection vs summary;
   history vs log; local server files vs register prose).

### 2.4 Evidence grading used throughout

| Grade | Meaning |
|---|---|
| **CONFIRMED** | A second, independent artefact corroborates the claim |
| **PARTIALLY SUPPORTED** | The artefact is consistent with the claim but does not establish it alone |
| **REPORT-ONLY** | The claim exists in the register and no retaining artefact was produced for it |
| **NOT SUPPORTED** | An artefact contradicts the claim, or the claim cannot be true as worded |
| **INFERENCE** | A reasoning step from confirmed facts, labelled as reasoning |

---

## 3. Repository baseline

Measured at the start of this phase, and identical to the baseline the original audit recorded:

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD | `71226e8faaef477ae3ac5e744b023451acb0c5bf` |
| `origin/hackathon-mvp` | `71226e8faaef477ae3ac5e744b023451acb0c5bf` — **0 ahead, 0 behind** |
| Staged files | **0** |
| Untracked files | **0** |
| Modified tracked files | **6** |
| Diffstat | **285 insertions, 14 deletions across 6 files** |

| File | + | − | Nature |
|---|---:|---:|---|
| `.clinerules` | 2 | 1 | **Owner's own edit** — the PO-dated §11 `docs/plan/` ratification. Not touched by the execution, and not touched by this audit |
| `backend/tests/test_display_admin.py` | 50 | 6 | Test corrections 3 and 4 |
| `backend/tests/test_operational_reports.py` | 9 | 0 | Test corrections 1 and 2 |
| `backend/tests/test_tracking_tokens.py` | 37 | 7 | Test correction 5 |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | 42 | 0 | Revision 54 registration |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | 145 | 0 | §15 appended |

**Baseline differences since the original audit: none.** No new change appeared between the audit and
this phase — itself evidence that the execution window was closed cleanly and that no unrecorded work
continued afterwards.

**No product file appears in that list.** The claim "no product file was modified in this window" is
**CONFIRMED** by the diff itself, and the governing principle — a failing test is a claim about the
product, not a licence to change the product — was preserved.

---

## 4. The five test corrections, assessed

Each was assessed against two questions: **is the old test wrong by the product's own contract?** and
**does the new test still fail if the feature regresses?** A correction that only makes a suite green
would fail the second question.

### 4.1 Summary

| # | Module | Correction | Verdict |
|---|---|---|---|
| 1 | `test_operational_reports.py` | A module-scoped patient fixture was deleted by the module's own purge, so every test after the first ran without its patient | **JUSTIFIED** |
| 2 | `test_operational_reports.py` | A fixture inserted `queue_entries` without the `NOT NULL` `token` and `patient_id` columns | **JUSTIFIED** |
| 3 | `test_display_admin.py` | The public board was addressed by display row id instead of the facility code the route resolves — **five** call sites, not four (F-05) | **JUSTIFIED** |
| 4 | `test_display_admin.py` | MP-45's field-suppression assertion was vacuous: it asserted absence from a body that contained no doctor row at all | **JUSTIFIED** |
| 5 | `test_tracking_tokens.py` | MP-25 moved the budget to a durable table, so `_RATE.clear()` stopped resetting anything and the module exhausted its own limit | **JUSTIFIED WITH CONCERNS** (F-04) |

### 4.2 Correction 1 — the fixture the purge deleted

`purge_org()` removes business rows (`patients`) but deliberately keeps the organisation, branch, doctor
and staff reference rows. A `module`-scoped `ensure_patient` fixture therefore survived only until the
first test's autouse `clean` ran, and the remaining tests asserted against a patient that no longer
existed. The repair re-creates the patient inside the autouse fixture.

**Why this is the test's fault, not the product's:** the purge's asymmetry is deliberate and part of the
test support layer; a fixture that assumes the opposite is simply wrong. **Does the new test still
bite?** Yes — the patient is created per test, so a report that ignores patients still fails.

### 4.3 Correction 2 — two `NOT NULL` columns omitted

`_queue_entry()` inserted a row without `token` and `patient_id`. The schema refuses that insertion, and
the resulting error had been read as a *report* failure — which is why the distinction mattered: the
product was never wrong here, the fixture was.

**Does the new test still bite?** Yes, and more strongly than before: the entry is now a real row the
report can count, so a report that miscounts queue activity fails on data rather than on an exception.

### 4.4 Correction 3 — the wrong identifier in the URL, at five call sites

The route is `/api/v1/queue/display/{org_code}/{branch_code}` and resolves the **facility code** stored
on the organisation and branch (`backend/queuing/display.py:151–160`, exact equality against
`Organization.code` / `Branch.code`). The tests passed the display's row id. The repair derives the codes
from the fixture (`ORG_CODE = ORG.upper()`, `BR_CODE = BR.upper()`).

**The audit's own count is five call sites, not four** (`test_display_admin.py:226, 231, 296, 309, 310` —
the `public`, `historic`, `quiet`, `switched-off` and `no-such-board` requests). Register §15.3 and the
§8 change-log row said four; both are corrected in this phase (**F-05**).

**Does the new test still bite?** Yes. A resolver that stopped matching the facility code would 404 on
all five requests and the module would fail. **Residual observation (F-11):** two conventions now coexist
in one URL — facility codes are stored upper-case by the fixture
(`backend/tests/amsdp_test_support.py:80, 91`) and matched case-sensitively, while display codes are
lower-case (`doctored`, `quiet`, `switched-off`) and also matched case-sensitively. A mismatch is
deliberately indistinguishable from an unknown board (that is MD-09/MD-19's design), so this class of
defect stays silent unless a test asserts the positive case — which four of the five call sites now do.

### 4.5 Correction 4 — the vacuous MP-45 assertion (the most interesting one)

The old test asserted that switched-off fields were **absent** from a public body that contained **no
doctor row at all**. The body publishes a doctor only when that doctor has a queue entry on the facility's
day, so "absent" was trivially true: the assertion could not have failed even if MP-45 were completely
broken.

The repair seeds one `called` and one `waiting` entry, asserts the row is **present** first
(`assert "D-001" in raw`), and only then asserts the switched-off fields are missing.

**Why the repair is non-vacuous — proven from the emitter, not from the test:**
`backend/queuing/display.py` builds `room_name` and `patients_waiting` **unconditionally** whenever the
corresponding display toggle is on (`display.py:499–509`), and adds the doctor row only when that doctor
has an entry on the facility's day (`display.py:477–479`). With the toggle on and a row present, those
keys are always emitted; therefore their **absence** while the row is present can only be caused by the
toggle. The assertion now has exactly one way to pass.

**Does the new test still bite?** Yes — and this is the correction that most improves the suite, because
before it MP-45's server-side enforcement was **untested in effect** while appearing tested.

### 4.6 Correction 5 — the reset hook that stopped resetting (JUSTIFIED WITH CONCERNS)

When the module was written, the tracking budget was an in-process dict, so three tests called
`_RATE.clear()` to make their window deterministic. MP-25 replaced that with a durable
`tracking_rate_buckets` table, one row per `pqt:<address>`. `_RATE.clear()` therefore became a **no-op
reset**: the seventeen tests share one test-client address, the ten-per-minute budget was exhausted by
the module itself, and later assertions met `429` where they expected `200`/`404`. Two suites —
`test_tracking_rate_limit.py` and this module — were green in isolation and contradictory together.

The repair keeps the limit intact and adds an autouse fixture calling `_reset_tracking_budget()`, which
clears `_RATE` **and** deletes every `pqt:%` row before each test. The 12-request test still requires its
`429`, so the budget is still charged and still asserted.

**Why this is justified:** the module's hermeticity assumption became false when the limiter moved to
durable storage; leaving it would have made the suite order-dependent, which is the worse outcome.

**The concerns (F-04, MEDIUM):**

1. The fixture is **not isolated to this module's data.** It deletes *all* `pqt:%` rows from the shared
   test database and clears a *process-global* dict. Any other test relying on limiter state — or any
   future parallel worker — is affected.
2. Under `pytest-xdist`, two workers sharing one database would reset each other's buckets
   nondeterministically: the suite would be flaky in a way that looks like a product defect.
3. It therefore converts a genuine design tension (a durable limiter is global by nature) into a
   **test-local workaround**. That is acceptable for a single-process run and is **not** proof that the
   limiter behaves correctly under concurrency — which is precisely what MP-25's remaining acceptance
   requirement asks for ("a multi-worker deployment run", register §15.4).

**Verdict: JUSTIFIED WITH CONCERNS.** Correct for the run that was performed; it must not be read as
concurrency evidence; and `pytest-xdist` should not be introduced on `backend/tests/` until F-04 is
scoped.

---

## 5. Backend test execution evidence

Full artefact inventory, digests and the claim-by-claim grading live in
`docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md`. This section states the audit's
conclusions.

### 5.1 The two runs

| | First execution | Second execution |
|---|---|---|
| Database | `amsdp_verify_1127` | `amsdp_verify_1127b` |
| Retained output | `E:\Temp\amsdp_full2.txt` | `E:\Temp\amsdp_full3.txt` |
| Summary line | `1061 passed, 66 warnings in 541.58s (0:09:01)` | `1061 passed, 50 warnings in 542.27s (0:09:02)` |
| Bound to its database by | shell history line 10801 | shell history line 10818 |
| Written at | 2026-11-27 11:53:50 | 2026-11-27 12:07:13 |

**CONFIRMED.** The counts and durations in register §15.2 are matches to the character. The two files
differ in warning count (66 vs 50) and in SHA-256 digest despite identical length — two runs, not one
file copied twice.

### 5.2 Binding, and why it matters

A pytest log by itself does not say which database it ran against; the `AMSDP_DATABASE_URL` override
lives only in the command line. Retained PowerShell history supplies it, and it supplies **different URLs
for the two runs**. This is the strongest available form of the claim and it is genuine primary
evidence — but it is a **mutable** file (every later command appends to it), so it is cited by line and
content, not by digest (evidence record L-1).

### 5.3 Completeness

`amsdp_collect.txt` records `1061 tests collected in 2.79s`, and `amsdp_files.txt` lists the 52 module
paths. **CONFIRMED:** the whole-suite figure equals an independent collection count, executed in one
process with no `-k`, `-m`, `--deselect`, `-x`, `--maxfail` or `pytest-xdist` in the command.

The step from "1,061 collected" to "every module ran and passed" is an **INFERENCE** (a summary line
counts what ran), not a measurement; there is no per-module transcript for the whole-suite run itself.

### 5.4 Repeatability, and what it actually proves

The register claims repeatability from a second database plus targeted re-runs. The audit's position:

| Element | Grade |
|---|---|
| Two whole-suite runs, both green | **CONFIRMED** |
| `test_tracking_tokens.py` run three times (17 passed each) | **PARTIALLY SUPPORTED** — the register records it; the targeted transcripts (`amsdp_t11`, `amsdp_vp`) are consistent but not a three-run series |
| `test_display_admin.py` run twice (13 each) | **PARTIALLY SUPPORTED** — same basis |
| Second database was created empty and migrated zero → head | **REPORT-ONLY** — no creation command and no alembic transcript for `amsdp_verify_1127b` survive (F-08) |

So the green result is **repeatable across two runs**; the stronger claim — that the second run inherited
nothing — is the register's narrative. That does not make the second run invalid; it makes one sentence
of its provenance unverified.

### 5.5 Intermediate failure evidence

`amsdp_perfile.txt` (the per-module rollout) preserves two *still-failing* modules —
`test_display_admin.py`: `1 failed, 12 passed` and `test_tracking_tokens.py`: `1 failed, 16 passed` — and
50 all-green modules with no timeouts. This is genuine intermediate-failure evidence for corrections 3,
4 and 5 (corrections 1 and 2 were already applied when the rollout ran, which is why
`test_operational_reports.py` shows `16 passed`). It is **not** a preserved trace of every failure
(F-10): the loop reused one output file, so the detailed trace of each iteration was overwritten.

---

## 6. Database and migration audit

### 6.1 The migration graph, inspected statically

| Check | Result |
|---|---|
| Head revision file present | `backend/alembic/versions/e1b7c4a9d236_add_tracking_rate_buckets.py` |
| Single head | **Yes** — one terminal revision, `e1b7c4a9d236` |
| `down_revision` of the head | `d3f5a7b91c24` (the `add_queue_displays` revision) |
| Chain integrity | Unbroken to the base revision; the merge revision `a9c4e1f7b2d8` joins `b3d7e91f6a24` and `f8a2b3c4d5e6` before the linear tail |
| Three additive revisions of the window | `b2e5c7d91a04` → `d3f5a7b91c24` → `e1b7c4a9d236` |

**CONFIRMED statically.** The graph is consistent with the register's claim of one head and with the
chain printed in the migration log.

### 6.2 The applied chain

`amsdp_mig.txt` shows `upgrade head` running from `initial_schema` (`5f3fce6757cf`) through the merge
revision to `e1b7c4a9d236`, on `amsdp_verify_1127`, at 11:20:43. **CONFIRMED:** the chain was applied from
an empty schema to head on that database.

The `NativeCommandError` text at the top of that file is PowerShell reclassifying Alembic's `stderr`
`INFO` lines, not a failed upgrade — worth recording, because a hasty reader would call it a failure.

**REPORT-ONLY:** `alembic current` and `alembic heads` were run (history line 10804) but their output was
not captured to a file. The reported `e1b7c4a9d236 (head)` and "one head" are consistent with the log and
with the static graph, and are not independently captured.

### 6.3 The engine: PostgreSQL 16.4, not 17

Register §15.1 states "PostgreSQL **17**, listening on `127.0.0.1:55432` (verified this window)". **That
is not supported, and three local files contradict it:**

| Artefact | Content |
|---|---|
| `…\AppData\Local\amsdp\pgdata\PG_VERSION` | `16` |
| `…\AppData\Local\amsdp\pgsql\bin\pg_config.exe --version` | `PostgreSQL 16.4` |
| `…\AppData\Local\amsdp\pg.log` line 1 | `starting PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit` |

The log records one start (2026-11-24 10:59:53) and no restart, with its last write at 2026-11-27
12:10:51 — the tail of the second run. The distribution present is `pg16.zip`; no PostgreSQL 17 build
exists in that directory. Reported as **F-13**.

**Why this matters, and why it is not fatal.** Every claim about the *tests* stands: the suites ran, on a
real PostgreSQL server, and passed. What does not stand is any claim that depends on PostgreSQL 17
semantics. Two consequences follow: register §15.1 needs a correction it was not authorised to receive as
a rewrite in this phase, and any future statement of the form "verified on PostgreSQL 17" must be
withdrawn until a 17 instance is used.

**No database session was opened to establish this.** The version comes from local files, which is
stronger evidence than a query result would be: a query proves what the server *reports*, whereas
`PG_VERSION` and `pg_config` prove what is installed and which data directory it serves.

### 6.4 What the database evidence does not establish

1. That `amsdp_verify_1127` was empty at creation — no pre-migration table count was captured.
2. That `amsdp_verify_1127b` was created empty and migrated — no artefact for it survives (F-08).
3. That the developer database `amsdp` was untouched — it exists on the same server (`amsdp_dbs.txt`
   lists it), and three earlier dashboard invocations against it remain in shell history with
   unestablished timing (F-01).
4. That no other database was written to. The listing names the scratch databases; the audit can say the
   runs were *configured* to use them, not that nothing else was touched.

---

## 7. Work package status audit

### 7.1 Statuses recorded, and their ceiling

| Work package | Status after the window (register §15.4) | Exceeds TESTED? |
|---|---|---|
| MP-23 | IMPLEMENTED · frontend TESTED · **backend TESTED (16 passed)** · BUILD VERIFIED | No |
| MP-39 | IMPLEMENTED · frontend TESTED (11) · **backend TESTED (13)** | No |
| MP-45 | IMPLEMENTED · **backend TESTED**, visibility test now non-vacuous | No |
| MP-46 | IMPLEMENTED · **backend TESTED** (8 denial-audit + display-denial assertions) | No — and see §8 |
| MP-25 | IMPLEMENTED · **backend TESTED** (5 + 17) · durable budget in force | No — multi-worker run still missing |
| MP-35 (seed) | IMPLEMENTED · **seed executed** (3 passed) | No |
| MP-04 | **Unchanged** — no backend surface in this window | No |

**No status exceeds TESTED; none is VERIFIED; none is ACCEPTED.** The register applies the project's own
evidence standard correctly (`.clinerules` §7: TESTED ≠ VERIFIED), and §15.5 explicitly disclaims
VERIFIED, ACCEPTED, CI, frontend and non-scratch-database claims. **CONFIRMED as conformant.**

### 7.2 Do the figures match the tests that exist?

Static test-function counts in the cited modules were compared with the recorded pass counts:

| Module | Recorded passes | Test functions (`def test_`) | Parametrized | Verdict |
|---|---:|---:|---:|---|
| `test_operational_reports.py` | 16 | 16 | 0 | ✔ exact |
| `test_display_admin.py` | 13 | 13 | 0 | ✔ exact |
| `test_denial_audit.py` | 8 | 8 | 0 | ✔ exact |
| `test_tracking_rate_limit.py` | 5 | 5 | 0 | ✔ exact |
| `test_tracking_tokens.py` | 17 | 17 | 0 | ✔ exact |
| `test_seed_demo.py` | 3 | 3 | 0 | ✔ exact |
| `test_queue_room_snapshot.py` | 15 | 15 | 0 | ✔ exact |
| `test_dqds.py` | 26 | 26 | 0 | ✔ exact |
| `test_e2e.py` | 21 | 21 | 0 | ✔ exact |
| `test_multidisplay.py` | 34 | 28 | 3 | ✔ consistent — the three `parametrize` decorators expand 28 functions to 34 items |

**CONFIRMED.** A pass count *larger* than the number of tests that exist would be the clearest possible
sign of an inflated figure; instead every figure equals its module's item count. Equal counts do not by
themselves prove execution — the summary lines do that — but they remove the inflation risk.

### 7.3 The one status statement this audit qualifies

Register §15.2 says "**no coverage gap is recorded for MP-46**". That sentence is true of the modules it
names and false as a statement about MD-19, because the specification's `capability` element is asserted
nowhere. That is **F-02**; §15.2 now carries a pointer to this audit instead of a rewritten claim.

---

## 8. MP-46 / MD-19 coverage discrepancy (F-02)

The full analysis and the Product Owner decision request are in
`docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md`. The finding is summarised here
because it is a condition of this audit's verdict.

### 8.1 The requirement, the criterion and the code

| Document | Says |
|---|---|
| Specification **MD-19** (Appendix E.3, approved under PO-13 on 2026-11-24) | “Authenticated display-management denials are audited (`queue.display.denied`: actor, **capability**, org/branch)” |
| Specification **AC-21** | “An authenticated cross-branch display write produces one `queue.display.denied` row; …” — row counts only, no field list |
| Master plan, MP-46 acceptance | “one denial = one row; 100 unknown-code probes add zero audit rows (spec AC-20, AC-21)” |
| Implementation (`backend/queuing/displays.py:115–142`) | records `actor_id`, `actor_role`, `organization_id`, `branch_id`, `action`, `target_type`, `target_id`, `after.status`, `after.code`, `after.request`, `reason` — **no capability** |
| Tests | **zero** occurrences of `capability` in the three denial-related modules |

### 8.2 Why the suite is green anyway

AC-21, and MD-19's own verification column, measure **counts and identity**, not fields. A missing field is
therefore invisible to every test: nothing asserts it, so nothing fails. The green suite is not evidence
about this question in either direction, and no one should read it as such.

### 8.3 Schema position

`audit_events.after` is a `JSON` column and already carries request-scoped detail (`status`, `code`,
`request`; the generic recorder puts `request_id` there too). Adding `after["capability"]` would need
**no migration and no model change**; a dedicated column would need both, against a table shared by every
service. The capability string itself (`queue.display.manage`) is already in scope at both `_denied()` call
sites (`displays.py:149`, `:415`), so the change — if authorised — is two call sites, one payload key and
two assertions.

### 8.4 Audit conclusion and consequence

- **Discrepancy: real and material to acceptance, not to behaviour.** MD-19's prose is approved text and
  nothing found later amends it; AC-21 is satisfied as written.
- **MP-46 stays TESTED.** It cannot be VERIFIED (no browser/live evidence) and must not be ACCEPTED while
  the question is open, because accepting it would mean accepting against the weaker of two approved
  documents.
- **No implementation was performed or authorised** in this phase: MD-19, AC-21, `_denied()`, the audit
  model, the tests and the statuses are all untouched.
- **Residual risk if left open:** an acceptance that silently narrows approved scope. That is the specific
  failure the decision brief exists to prevent.

---

## 9. Documentation audit

### 9.1 The register edit

| Check | Result |
|---|---|
| Original size | 99,886 bytes + 677 CRLF lines = **100,563** bytes on disk |
| Recorded size after the edit | **113,835** bytes |
| Arithmetic | 100,563 + 13,272 = 113,835 ✔ |
| Diff shape | **145 insertions, 0 deletions** |
| Sections rewritten | **None** — §1–§14 byte-identical; §15 appended, with a comment recording that fact |
| Change log | §8 gained one 2026-11-27 row, itself additive |

**CONFIRMED: pure append.** No historical statement was deleted, no earlier status silently upgraded, and
the owner's decisions are untouched. This is the correct shape for a governance register — the record
accumulates, it does not revise itself.

### 9.2 The Docs Index edit

| Check | Result |
|---|---|
| Revision numbering | 53 → **54**, sequential; no gap, no duplicate |
| Diff shape (Revision 54's own edit) | **42 insertions, 0 deletions** — the working tree reads 105/0 once Revision 55 is added |
| Earlier revisions | All preserved verbatim |
| Counts stated | 166 `.md` files under `docs/`, stated as unchanged because Revision 54 created no document |

**CONFIRMED.** The index obeyed its own rule — a revision that creates no document registers a state
change and says so.

### 9.3 Defects found in the documentation

| Finding | Defect |
|---|---|
| **F-01** | Register §15.1 and §8 state categorically that the developer database was "neither contacted, opened nor migrated"; three earlier dashboard invocations against `…/amsdp` remain in shell history |
| **F-03** | §11 and §13.3 still say MP-23/MP-39/MP-46 are "NOT EXECUTED"/"UNRUN"/"BLOCKED" with no pointer to the later §15 |
| **F-05** | "Four call sites" — it is **five** |
| **F-06** | MP-46's coverage paragraph names two modules; `test_multidisplay.py` carries the throttle and the 100-probe rule |
| **F-13** | Register §15.1, the §8 change-log row for 2026-11-27 and Docs Index Revision 54 all state PostgreSQL **17**; the server is **16.4** |
| **F-08** | Register §15.2 and Revision 54 describe `amsdp_verify_1127b` as "created empty and migrated zero → head"; no artefact for that database survives |

The first four were corrected in this phase (§5 corrections of the mandate, authorised — see the resolution
table in §12). **F-13 and F-08 were not rewritten**: the mandate authorised four specific corrections and
neither is among them. Both are recorded here and in the evidence record, and the §15 claim they touch is
flagged with a pointer rather than silently edited.

### 9.4 Documentation created by this phase

| File | Purpose |
|---|---|
| `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` | this report |
| `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` | evidence inventory, digests, claim grading |
| `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` | the F-02 decision request |

`docs/testing/` **did not exist** before this phase; it is an authorised subfolder under `.clinerules` §11.
The other two folders existed. No file in any of the three was overwritten: `docs/audit/` held 19 documents
and none is a backend-execution audit; `docs/decisions/` held no MP-46 capability brief.

---

## 10. Governance audit

### 10.1 `.clinerules` §3 — non-negotiables

| Rule | Audit position |
|---|---|
| Never log or expose secrets | No credential appears in any test, log, diff or new document. The database URL used all window is password-less (`postgresql+psycopg2://amsdp@…`) |
| UI is never the safety boundary | Not engaged by this window; the corrected tests assert **server-side** field suppression (MP-45) and server-side denial recording (MP-46) |
| Access enforced server-side; principal from the token | The MP-46 row is attributed via `auth.organization_id` / `auth.branch_id`, never from the request body |
| Cross-tenant/cross-branch fails closed with 404 | Preserved: the resolver returns the identical 404 for unknown, cross-branch, cross-org and disabled |
| Tenant key is `organization_id` | No second tenant column introduced |
| Audit trail append-only | No audit event was deleted. The one deletion the window performs is of `pqt:%` **rate-limit bucket** rows in a test database — not audit rows (but see F-04) |
| Denials recorded, not swallowed | MP-46's helper writes **before** refusing, and omits the marker only when the row could not be written so the generic recorder still leaves the denial visible — a careful design |
| Schema changes ship as forward-only, idempotent Alembic migrations | No schema change in this window; the graph has one head |
| Never claim an unverified capability | §15.5 disclaims VERIFIED, ACCEPTED, CI, frontend and non-scratch DB; §7.1 of this report confirms no status exceeds TESTED |
| No invented skill usage | No skill was claimed: `.clinerules` §5 records that **no skill package is installed** |

### 10.2 `.clinerules` §7 — evidence standard

The register used the project's ladder correctly: IMPLEMENTED (code exists) → TESTED (named tests pass in
this tree) → **stop**. VERIFIED needs a second independent artefact (browser run, live API call, database
read); none exists for this window, and the register does not claim one.

**One nuance this audit adds:** the evidence record created in this phase is **not** a second artefact for
the tests. It describes them. Reading it upgrades nothing.

### 10.3 `.clinerules` §9 — execution boundaries and git safety

| Rule | Audit position |
|---|---|
| No destructive git (`reset --hard`, `clean -fd`, `stash`, `checkout .`) | None used; the working tree was preserved across both phases |
| Do not stage someone else's uncommitted work | `.clinerules` was left unstaged and unedited in both phases |
| Keep terminal output small | Observed — reads were tail-first and targeted |
| Do not run suites unless asked | No suite was run in either phase; the resolution mandate forbade it |

### 10.4 `.clinerules` §11 — documentation output location

The original audit delivered its report **in conversation only**, because the mandate said "no repository
files" while §11 says reports go under `docs/`. That conflict is **F-09** and is **resolved in this phase**
by writing the report to `docs/audit/` and registering it — satisfying both the newer instruction and §11's
placement rule.

### 10.5 Governance items not exercised

`.clinerules` §8 (LLM execution routing) and §5 (skills) were **not exercised** in this window: no local
model was used and no skill is installed. Nothing in the window depends on either, but no artefact records
that the routing policy was considered — a minor omission noted under F-12 rather than raised separately.

---

## 11. Outstanding verification requirements

| # | Requirement | Why it is outstanding | What would satisfy it |
|---|---|---|---|
| V-1 | **MP-46 capability decision** | MD-19 vs AC-21 conflict (F-02) | A Product Owner answer to `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` |
| V-2 | **Multi-worker rate-limit proof** | The suite is single-process; the reset fixture is process-global (F-04) | A concurrency test or a deployment run with ≥ 2 workers, asserting the durable budget holds across processes |
| V-3 | **Browser VERIFIED pass** | No browser session exists for any multi-display, dashboard or reporting screen | A recorded browser run (V-04 / V-23 / V-39 / V-45 / V-46 in the handover checklist) with screenshots or HAR evidence |
| V-4 | **CI verification** | Nothing was pushed; last CI-relevant commit is `62b2fac` | A push, then a green run at that commit |
| V-5 | **Ubuntu upgrade path** | `c4d8e2a91f60` → `e1b7c4a9d236` is assessed, not executed | The handover §8 pull / backup / migrate sequence on the Ubuntu host |
| V-6 | **PostgreSQL 17 evidence** | The engine used was 16.4 (F-13) | Re-run on a 17 instance **if** any claim depends on 17 semantics |
| V-7 | **Product Owner acceptance** | No decision was sought | Explicit acceptance per work package, on the evidence in §15 + this report |
| V-8 | **Evidence retention** | Logs live outside version control; history is mutable | Keep `E:\Temp\amsdp_*` and `E:\amsdp_audit_evidence_27nov2026\`; re-hash against the record |
| V-9 | **`amsdp_verify_1127b` provenance** | No creation/migration artefact survives (F-08) | Nothing can recover it; treat the second run as "a second green run", not "a pristine second database" |

**None of V-1…V-9 can be closed by documentation.** Each needs an artefact the repository does not yet
contain, which is why no status was upgraded in this phase.

---

## 12. Findings register

Severity across the original twelve: **0 CRITICAL · 0 HIGH · 2 MEDIUM · 5 LOW · 5 INFORMATIONAL.** The
thirteenth is new to this phase and is graded separately.

**Resolution status vocabulary.** `RESOLVED` = the defect is corrected in the repository and the correction
is verifiable in the diff. `DOCUMENTED` = the limitation is recorded but nothing in the tree could correct
it. `AWAITING PRODUCT OWNER DECISION` = a person must choose. **No finding is marked resolved merely
because a document mentions it.**

| # | Finding | Severity | Status after this phase |
|---|---|---|---|
| **F-01** | Register claimed the developer database `amsdp` was "neither contacted, opened nor migrated"; three earlier dashboard invocations against `…/amsdp` remain in retained shell history, timing unestablished | LOW | **RESOLVED** — register §15.1 and §8 now distinguish what is established (not migrated or reseeded in this window; not used for the 1,061-test runs) from what is not (earlier invocations exist; their timing and effects are not established). The word "contacted" is withdrawn |
| **F-02** | MD-19 requires actor/capability/org/branch in `queue.display.denied`; the row has no capability field; no test asserts it; AC-21 measures only counts | **MEDIUM** | **AWAITING PRODUCT OWNER DECISION** — brief written (`docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md`); MP-46 stays TESTED |
| **F-03** | Register §11 and §13.3 still showed pre-§15 statuses (NOT EXECUTED / UNRUN / BLOCKED) with no forward pointer | LOW | **RESOLVED** — additive pointers under both sections; historical text preserved as written |
| **F-04** | `_reset_tracking_budget()` clears a process-global dict and deletes all `pqt:%` rows from the shared test database; not module-isolated; unsafe under parallel workers | **MEDIUM** | **DOCUMENTED** — audit §4.6, evidence-record L-6, register §15.1 audit annotation (item 3). Fixture deliberately unchanged (mandate §8) |
| **F-05** | "Four call sites" — five GET call sites were changed (`test_display_admin.py:226, 231, 296, 309, 310`) | LOW | **RESOLVED** — register §15.3 and §8 corrected to five |
| **F-06** | MP-46 coverage paragraph named `test_display_admin.py` and `test_denial_audit.py` only, omitting `test_multidisplay.py` (throttle + 100-probe rule) | LOW | **RESOLVED** — third module added; the F-02 gap explicitly retained, not papered over |
| **F-07** | Primary execution evidence lives outside version control in `E:\Temp` with no durable record | LOW | **RESOLVED** — 23 artefacts hash-verified and copied to `E:\amsdp_audit_evidence_27nov2026\`; inventory, digests and grading recorded in `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` |
| **F-08** | Repeatability evidence is thinner than the narrative: no creation/migration artefact for `amsdp_verify_1127b`; the targeted re-run series is not fully preserved | INFORMATIONAL | **DOCUMENTED** — retained as a limitation (evidence record L-2, §3.3, §5.4; V-9) |
| **F-09** | The audit report existed only in conversation; `.clinerules` §11 requires it under `docs/` | INFORMATIONAL | **RESOLVED** — this report, registered in Docs Index Revision 55 |
| **F-10** | Intermediate failure traces partially overwritten by the rollout loop | INFORMATIONAL | **DOCUMENTED** — retained (evidence record §5, L-4) |
| **F-11** | Two facility-code conventions coexist (upper-cased facility codes, lower-case display codes, both case-sensitive); a mismatch is indistinguishable from an unknown board | INFORMATIONAL | **DOCUMENTED** — retained (audit §4.4) |
| **F-12** | No temporary repository artefacts were left behind by the execution | INFORMATIONAL | **DOCUMENTED** — re-verified at this phase: 0 untracked, 0 staged, no probe file in `frontend/tests/` or `backend/tests/` |
| **F-13** | *(new, this phase)* Register §15.1 and Docs Index Revision 54 state PostgreSQL **17**; the server is **16.4** (`pgdata/PG_VERSION`, `pg_config --version`, `pg.log` start line) | **MEDIUM** | **DOCUMENTED, not rewritten** — no register rewrite was authorised; a correction is recommended in §13 (A-2) |

### 12.1 Why F-13 is not folded into the twelve

The mandate forbids inventing findings and requires any new one to be reported separately with its basis.
F-13 was discovered during this phase, not in the original audit, and is reported on its own footing: it
changes no test result and no status, but it does invalidate a specific sentence in an approved register and
a specific sentence in Revision 54.

### 12.2 What these statuses do **not** mean

- F-01, F-03, F-05 and F-06 are **documentation** corrections: they make the record accurate, change no
  behaviour and upgrade no status.
- F-07 and F-09 make evidence **durable and citable**; they do not make it stronger.
- F-02 and F-04 remain the only conditions that could affect an acceptance decision.

---

## 13. Recommended actions

| # | Action | Owner | Effect if not done |
|---|---|---|---|
| **A-1** | Answer the MP-46 capability question (Option A / B / C) | Product Owner | MP-46 can never exceed TESTED without a recorded position; an acceptance would silently narrow approved scope |
| **A-2** | Authorise wording corrections for **F-13** and **F-08**: register §15.1 and the §8 change-log row, “PostgreSQL 17” → **16.4**, and `amsdp_verify_1127b` described as “a second run on a separate scratch database” rather than “created empty and migrated zero → head”. The same two sentences in Docs Index Revision 54 (Revision 55's annex already carries the correction) | Product Owner | A known-wrong sentence stays in an evergreen register and in Revision 54 |
| **A-3** | Decide the rate-limit fixture's fate **before** `pytest-xdist` is introduced: module-scoped isolation, a per-test unique client address, or an explicit "single-process only" declaration | Engineering, on PO authority | Parallel test execution stays unsafe and silently flaky |
| **A-4** | Do not promote any work package above TESTED until a browser run exists — and, for MP-25, a multi-worker run | Product Owner / engineering | VERIFIED and ACCEPTED would be claimed without evidence |
| **A-5** | Keep `E:\Temp\amsdp_*` and `E:\amsdp_audit_evidence_27nov2026\` intact; re-hash against the evidence record before quoting any figure | Whoever quotes the figures | The primary evidence can be lost by a temp cleanup |
| **A-6** | When a push is next authorised, use a commit that **contains** the five test corrections and record the run id — the last CI-relevant commit `62b2fac` predates them | Engineering, on push authority | CI green would say nothing about the corrected tests |
| **A-7** | Cite register §15 as the authoritative status block for the 27 November backend work; read §11/§13.3 statements as historical | All readers | The register's own history gets misread as current state |

Nothing in A-1…A-7 is implemented in this phase. A-2 in particular was **not** performed: correcting a
factual sentence is exactly what the four authorised corrections did for F-01/F-03/F-05/F-06, and F-13 sits
outside that enumerated list, so it is escalated rather than assumed.

---

## 14. Final safety declaration

For both the audit and this resolution phase:

- **No application source code was modified.** `git status` shows three test files, two documents and the
  owner's `.clinerules` edit; no `backend/**` module outside `tests/` changed.
- **No test code was modified by this audit or by the resolution phase.** The five corrections are the
  execution window's, and they were read, not altered.
- **No database was accessed or modified.** No session was opened. Database facts come from retained
  command output and from local server files.
- **No migration was executed.** The chain was read statically and from the retained log.
- **No configuration was modified.** No `.env`, compose file, dependency manifest or CI workflow changed.
- **No Product Owner decision was rewritten.** `.clinerules` was left exactly as the owner left it.
- **No roadmap scope, work-package status or acceptance criterion was changed.** MP-46 stays TESTED; no
  status was upgraded.
- **No deployment was performed**, no container touched, no O-1 work started.
- **No Git history was modified** — no commit, amend, rebase, merge, cherry-pick, tag, reset, clean, stash
  or checkout, and **nothing was pushed**.
- **The only changes made were the explicitly authorised documentation and evidence-preservation acts:**
  three new documents under `docs/`, four authorised register corrections plus additive audit annotations,
  Docs Index Revision 55, and a hash-verified copy of the 27 November evidence outside the repository.

**Verdict restated: INDEPENDENT AUDIT PASSED WITH CONDITIONS.** The conditions are F-02 (a decision) and
F-04 (a documented limitation), with F-13 and F-08 escalated for authorisation.

---

<!-- Written 2026-11-27 under the audit-resolution mandate §6 (finding F-09). The audit conclusion is
     preserved from the original independent audit; nothing was upgraded to VERIFIED or ACCEPTED. -->

---

## Post-audit annotation (2026-11-27, later — additive; the audit's findings are not altered)

**Authority.** Product Owner answer to the consolidated decision pack, 2026-11-27: **PO-DEC-01** (Option A) and
**OA-2** (documentation-only corrections). Added by the agent; **§1–§13 stand as written**.

1. **A-1 — the decision request for F-02 — is answered.** **PO-DEC-01: Option A**, persist the MD-19 capability
   field. The decision is recorded in
   `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` **§11**. **MP-46 remains TESTED**:
   the answer is a decision, not an execution, so nothing becomes VERIFIED, and no signature makes it ACCEPTED.
2. **A-2 — the F-13 wording correction — is executed.** The register's three operative sentences now read
   **PostgreSQL 16.4**: the §8 change-log row for 2026-11-27, the §15 introduction, and the §15.1 table row —
   each marked with the authority and the wording it replaced. The §15.1 annotation above is **preserved as
   written**, including its statement that the correction had not yet been applied.
   **Docs Index Revision 54 is deliberately left as written**: Revision 55's annex already carries the
   correction and explicitly preserves that text, and the register — not an index revision entry — is the
   operative record. No operative document now states "17".
3. **F-08 — the second-database provenance — is resolved as a documentation act.** Register §15.1 now states
   that no retained artefact records `amsdp_verify_1127b` being created or migrated, describes it as "a second
   run on a separate scratch database", and does **not** claim zero → head. The evidentiary limitation stands:
   the second green run is real, its creation transcript is missing.
4. **Every other finding stands as written.** None was withdrawn, softened or re-graded. The sequencing
   condition recorded for **A-3** — no `pytest-xdist` on `backend/tests/` until the shared-fixture issue is
   scoped — is unaffected and remains in force.
5. **Nothing was re-executed.** This annotation records **documentation** acts only. It adds no evidence, so it
   cannot and does not upgrade anything to VERIFIED or ACCEPTED (`.clinerules` §7).

**Where the corrections live.** `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` §4 lists all
eleven edits with their authority; register §17 records the decision, the status corrections and the corrected
backlog tally; Docs Index Revision 57 registers the RO record.

<!-- Post-audit annotation appended 2026-11-27 under PO-DEC-01 + OA-2. Findings untouched; nothing re-executed. -->