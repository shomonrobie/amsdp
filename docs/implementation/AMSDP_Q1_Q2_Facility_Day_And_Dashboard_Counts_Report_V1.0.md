# AMSDP — Q-1 and Q-2: the facility day in the patient service, and the two dashboard counts

**Implementation report, V1.0 — 25 November 2026**
**Authority:** Product Owner instruction of 25 November 2026 (second window), recorded in
`docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` **§11, Addendum A-1**, and applied to the
plan in `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` **Appendix G, Amendment A-4**.
**Written to:** `docs/implementation/` (`.clinerules` §11 — the folder the subject belongs to).
**Nothing in this report is `ACCEPTED`.** `ACCEPTED` is the Product Owner's signature, not an agent's inference.

---

## 1. What was asked, and what was delivered

| Item | Decision | Delivered | Status |
|---|---|---|---|
| **Q-1** | APPROVED — consolidate the two patient-service date reads into **MP-44** | Both reads now resolve through `common.timeutil.operational_today`, once per request | **IMPLEMENTED · TESTED** |
| **Q-2** | APPROVED — **Waiting** = `queue_length` (patients waiting), **In queue** = `in_queue` (appointment records in the queue) | The Waiting tile was re-bound to `queue_length`; `in_queue` is shown under its own label; the payload contract is documented | **IMPLEMENTED · TESTED** |
| **Push** | AUTHORISED for `hackathon-mvp` | 19 local commits pushed; the remote tip is recorded in §7 | **PERFORMED** |
| **Demo data** | AUTHORISED with limits | **Not exercised** — the existing development data was sufficient (§6). Recording that is more honest than manufacturing rows to justify the authority | **NOT NEEDED** |

---

## 2. Repository state, inspected before any change

| Fact | Value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD at the window's start | `387d04a` — *docs(decisions): mark the PO-08 response line as adapted, and correct the commit count* |
| Remote | `origin` → `https://github.com/shomonrobie/amsdp/` |
| Relation to remote at the start | **19 commits ahead** of `origin/hackathon-mvp`, 0 behind |
| Working tree at the start | **11 dirty entries** — all preserved. No `reset --hard`, no `clean -fd`, no `stash`, no `checkout .` (`.clinerules` §9) |
| Owner-controlled documents | **Not modified.** `.clinerules`, `docs/AMSDP_Business_Rules_V1.1.md`, `docs/product/AMSDP_Business_Rules_V1.0.md`, the Master Feature List drafts, the System Architecture and the ASCII Blueprint carry pre-existing owner edits that were left exactly as found |

**The previous window's report was not treated as proof.** The state above was read from git in this
window, and every claim below is backed by a command run in this window.

### 2.1 The database question, answered before anything wrote to anything

The instruction required identifying the database and environment **before** use, and forbade assuming
a live database is a demo database. Measured, read-only:

| Property | Value | Method |
|---|---|---|
| Host / port | `127.0.0.1:55432` | TCP probe; `inet_server_addr()` = `127.0.0.1/32` — a **loopback** server |
| Server | PostgreSQL **16.4**, compiled by MSVC (Windows) | `version()` |
| Database / user | `amsdp` / `amsdp`, trust auth on loopback | `psycopg2` connection, no password |
| Schema | **31** tables; `alembic_version` = `b2e5c7d91a04` (matches the working tree) | `information_schema`, `alembic_version` |
| Contents *(measured at the close of the window; the counts move while tests run)* | 153 organizations, 125 branches, 388 doctors, 686 patients, 113 appointments, 14 queue entries, 538 staff users, 8,373 audit events | `count(*)` per table |
| Nature of the data | **Test fixtures + development demo.** Organizations are pytest fixtures (`conc_org_*`, `foreign_org_*`, `m5-org`, `m6-org`, `legacy-*`, `sq3-org`, several *Uposhak Clinic* rows) plus one hand-made development organization, `demo-org-001` *Uposhak Hospital* | `select id, name from organizations` |

**Conclusion.** This is the local development/test database. It is **not** the Product Owner's Ubuntu
database (`:5433`, closed in this window) and **not** a production database. Every test below ran here.
**No DDL, no migration, no `alembic upgrade`, no reseed, no `DELETE`/`TRUNCATE`** was issued by hand:
the only writes are the tests' own fixtures inside their own organizations (`m6-org`, `legacy-pat-*`).

`AMSDP_DATABASE_URL` was exported per command
(`postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp`); **no configuration file was changed**, so the
repository's default remains unchanged and nothing in the tree now points at a different database.


---

## 3. Q-1 — one facility day for the patient service

### 3.1 The defect, precisely

`backend/patient/main.py` resolved "today" from the **host clock** in two places, while the queue
board, the dashboard, the schedule and the display already resolved it from
`organizations.timezone` through `common.timeutil.operational_today`:

| Function | Before | Consequence |
|---|---|---|
| `_validate_dob` | `datetime.now().date()` | A date of birth that is valid in the facility's day could be rejected as "in the future" — or a genuinely future date accepted — whenever the host and the facility sat on different sides of midnight |
| `_age_from_dob` | `date.today()` | The age shown on the patient record could be one day off on the patient's birthday, so the same patient read 34 on one screen and 35 on another |

Two reads, two clocks, one record. That is exactly what BR §8 (facility day) exists to prevent.

### 3.2 The change

* Both reads now call **`common.timeutil.operational_today`**, the helper the rest of the product
  already uses. No behaviour was invented: the function is the existing, tested one.
* `today` is threaded as an **optional keyword** through `_validate_dob`, `_age_from_dob` and
  `_patient_to_dict`. Defaults are unchanged, so **no existing caller or test needed editing** — the
  proof is that the pre-existing 20 patient tests still pass untouched.
* **One facility-day read per request**, resolved at the top of each of the four endpoints
  (create / list / get / update). The list endpoint resolves it **once per page, not once per row**,
  so a 100-patient page costs one organization lookup rather than 100. This is the same "read the day
  once and pass it down" shape the dashboard uses; it was chosen over per-call resolution precisely
  because the per-row version is an obvious N+1.
* **Nothing else changed:** field names, date formats, validation messages, status codes, audit events
  and the response envelope are unchanged in shape. No new dependency, no schema change, no migration.

### 3.3 Evidence

`backend/patient/tests/test_patient_facility_day.py` — **12 new tests, DB-free, no fixture writes**:

| Test (exact name) | What it pins |
|---|---|
| `test_operational_today_follows_the_facility_zone_not_the_process_zone` | the helper itself returns the facility's day, not the process's — the premise the other eleven rest on |
| `test_a_birth_date_that_is_tomorrow_here_is_today_there` | `Pacific/Kiritimati` (UTC+14) vs `Pacific/Midway` (UTC−11) are **always one calendar day apart**, so the same date is "tomorrow" for the host and "today" for the facility. Non-flakeable by construction — no sleep, no freeze, no wall-clock race |
| `test_a_birth_date_of_the_facility_today_is_accepted` | the boundary case that was broken: today-in-the-facility is not "the future" |
| `test_a_birth_date_after_the_facility_today_is_refused` | the check still refuses a genuinely future date — it was not weakened to make the first case pass |
| `test_an_empty_birth_date_is_still_optional` | DOB stays optional; no new required field |
| `test_a_malformed_birth_date_is_a_format_error_not_a_future_error` | error classification is preserved (format, not "future") |
| `test_the_age_turns_over_on_the_facility_birthday` | the age increments on the facility's birthday, not the host's |
| `test_a_leap_day_birth_date_is_aged_without_fabrication` | 29 February birth date in a non-leap facility year — no invented date |
| `test_the_age_defaults_to_the_facility_day` | with no `today=` argument the function still resolves the facility day (the optional parameter did not become a bypass) |
| `test_the_module_no_longer_reads_the_local_clock` | **source guard**: asserts `datetime.now()`, `date.today()` and `utcnow()` appear nowhere in the module |
| `test_the_facility_day_is_read_once_per_request` | the single-read contract, including the list endpoint's page-level read |
| `test_the_module_resolves_the_day_through_the_shared_helper` | the module calls `operational_today` where it should, so the fix is *through the shared helper*, not a private reimplementation |

The guard uses `(?<!def )` before the call pattern so the definition of `operational_today` itself does
not trip it — a guard that fails on its own subject is worse than no guard.

**Negative control (executed, then reverted).** The original `datetime.now().date()` was restored in
`_validate_dob` → **`1 failed, 11 passed`**, the failing test naming the host clock. The file was then
restored and verified byte-identical by SHA-256 (`True`). Without this step the new tests would only
prove that green tests exist.

---

## 4. Q-2 — Waiting means waiting; In queue means in the queue

### 4.1 The defect, precisely

The dashboard publishes two figures, and they are **not** the same population:

| Figure | Source | Population |
|---|---|---|
| `queue_length` | live queue entries in `QUEUE_ACTIVE = {waiting, called, in_consultation, skipped}` | **people physically in / called from the queue** — includes walk-ins, who have **no appointment record** |
| `in_queue` | appointment records whose status is *in queue* for today | **appointment records** in the queue today |

The page bound the **Waiting** tile to `in_queue`, so a walk-in standing at the desk did not increment
"Waiting", and an appointment-less patient was invisible on the tile. Two different questions were
sharing one number. The owner's answer separated them.

### 4.2 Why this was implementable rather than a limitation

Before touching the page, the write path was inspected: **`queuing.enqueue_patient` stores a walk-in
with `appointment_id = NULL`**. The data model therefore genuinely distinguishes "a person in the
queue" from "an appointment in the queue" — so the approved distinction could be shown truthfully.
Had the model stored a synthetic appointment for every walk-in, this report would have had to record a
limitation instead of an implementation. That check is why the change is a **rebinding**, not a
redefinition.

### 4.3 The change

| File | Change |
|---|---|
| `frontend/pages/dashboard.js` | **Waiting** tile re-bound: `in_queue` → **`queue_length`** |
| `frontend/pages/dashboard.js` | the queue panel now renders **both**: `waitingNow` (`queue_length`) and a separate `inQueueRecords` figure (`in_queue`), alongside `walkIns` — so the operator can see why the two numbers differ |
| `frontend/lib/i18n.js` | `inQueueRecords` added in **both** languages (`bn`, `en`) — 1 key × 2, no English-only leak |
| `backend/appointment/dashboard.py` | module docstring states the two populations and why `skipped` still counts as active; the endpoint docstring records the Q-2 decision. **No formula changed** — the arithmetic was already right; the *binding* was wrong |
| `frontend/tests/dashboard-tiles.test.mjs` | the guard now asserts Waiting → `queue_length`, that `in_queue` is **not** a tile but *is* rendered under its own label, and that no tile reads the same field twice |

### 4.4 Evidence

| Artefact | Result |
|---|---|
| `test_waiting_and_in_queue_are_different_populations` *(new, PostgreSQL)* | builds one day containing `IN_QUEUE`, `CHECKED_IN`, `BOOKED`, a **walk-in with `appointment_id = NULL`**, a `SKIPPED`, a `COMPLETED` and a queue entry from **another day** → asserts `in_queue == 1` *and* `queue_length == 3` **in the same test**. A single-number assertion could not have caught the original defect |
| `test_a_queue_entry_from_another_day_is_not_todays_waiting` *(new, PostgreSQL)* | yesterday's waiting entry does not inflate today's tile |
| `frontend/tests/dashboard-tiles.test.mjs` | includes the no-duplicate-binding guard; the three dashboard files together are **29 tests / 29 passed** (§5.2) |


**Negative controls (executed, then reverted).**

1. `skipped` dropped from `QUEUE_ACTIVE` → the population test goes **red at `queue_length == 3`**, so
   the test constrains the *definition*, not merely the plumbing.
2. The Waiting tile re-aliased back to `in_queue` → **`2 pass / 2 fail`** in the tile guard.

Both files were restored and verified byte-identical by SHA-256 (`True`). With the Q-1 control (§3.3)
that makes **three controls, three reds, three clean restores** — each change is constrained from the
inside, not merely accompanied by a green suite.

---

## 5. What was actually run

Every figure below is copied from a command executed in this window against the database identified in
§2.1. No figure is estimated, extrapolated or remembered.

### 5.1 Backend, targeted

| Command | Result |
|---|---|
| `pytest patient/tests/test_patient.py patient/tests/test_patient_facility_day.py` | **`32 passed`** (20 pre-existing, untouched + 12 new), `38.3 s` |

| `pytest tests/test_dashboard.py` | **`14 passed`** — the whole dashboard file (9 pre-existing test functions, some parametrised, plus the **2 new Q-2 tests**), so the new cases did not disturb the old ones |

| `pytest tests/test_dashboard.py patient/tests/test_patient.py patient/tests/test_patient_facility_day.py` | **`46 passed`**, `36.22 s` — the three files that Q-1 and Q-2 touch, green in one run |


### 5.2 Frontend

| Command | Result |
|---|---|
| `node --test tests/dashboard-tiles.test.mjs tests/dashboard-page.test.mjs tests/dashboard-policy.test.mjs` | **`29 tests / 29 passed / 0 failed`**, `155 ms` |
| `npm test` (whole suite) | **`467 tests / 465 passed / 0 failed / 2 skipped`**, `1.66 s` — the two skips are the known **Q-3** pair (`banglanamesense-dataset`, `calendar-render`), unchanged by this work |

### 5.3 Backend, whole suite

| `pytest backend -q` (every backend test, against `127.0.0.1:55432`) | **`993 passed, 0 failed, 0 errored, 90 warnings in 967.75s (16:07)`** |

**The arithmetic is the evidence.** The previous recorded whole-suite figure in this tree was
**`979 passed, 0 failed`** (register §8, MP-29 row). This window adds **12** patient-service tests and
**2** dashboard tests, and the total is **993** — exactly `979 + 14`, with the failure count unchanged
at **0**. A regression hidden behind a re-baselined count would not produce that sum.


### 5.4 What these numbers do and do not prove

They prove the changes are **TESTED** in this tree, on this database, in this window. They do **not**
prove `VERIFIED`: that needs a second, independent artefact — a browser run or a live API call against
the running application — and none was performed (**B-2**). A green suite is evidence of regression
safety, not of product behaviour on the deployment.

---

## 6. Demo data — authorised, deliberately not used

The instruction authorised adding demo data to demo/testing environments with a list of limits. **No
data was added in this window**, and the reason matters more than the restraint:

1. The database in §2.1 already holds realistic development data — `demo-org-001` *Uposhak Hospital*
   with branches, doctors, patients, appointments and queue entries — which was sufficient to write and
   prove both tests.
2. Every limit in the instruction (no invented clinical facts, no fabricated audit history, no seeded
   credentials, no production writes) would have to be honoured *per row*; adding rows that nothing
   then uses would be noise that later readers must treat as evidence.
3. The report would otherwise have to say "demo data exists" without a consumer. **Silence about an
   unused authority is more useful than rows nobody asked for.**

The authority is therefore **recorded as unused, not as exercised**. Nothing was seeded, and no script
that would seed anything was added to the tree.

**However, the tests did write.** The suite creates its own fixtures inside fixture organizations
(`m6-org`, `legacy-pat-*`, `conc_org_*`, …) — that is the tests' normal behaviour, not a seed. The
counts in §2.1 (153 organizations, 8,373 audit events) reflect those fixture writes and will keep
moving as the suite runs; they are not a curated dataset.

---

## 7. Commits and the authorised push

### 7.1 The order, and why it is path-grouped

Three commits, not one, because one commit mixing a backend clock fix, a dashboard tile and four
documents cannot be reverted in isolation. Nothing was staged that had not been read first, and
`git diff <file>` was inspected before staging each group (`.clinerules` §9).

| # | Commit | Scope | Contents |
|---|---|---|---|
| 1 | **`e23a2ce`** | backend | `patient/main.py`, `patient/tests/test_patient_facility_day.py` (new), `appointment/dashboard.py`, `tests/test_dashboard.py` — **4 files, 301 insertions, 16 deletions** |
| 2 | **`516e46b`** | frontend | `pages/dashboard.js`, `lib/i18n.js`, `tests/dashboard-tiles.test.mjs` — **3 files, 37 insertions, 3 deletions** |
| 3 | the commit carrying this report | docs | decision record §11 (Addendum A-1), plan Appendix G (Amendment A-4), register §10 + change-log row, Docs Index Revision 50, this report |

Each commit message states the decision it implements, the mechanism, and the figures actually
observed — so `git log` alone does not have to be read alongside a document to be truthful.

### 7.2 What was *not* staged, and why

| Path | State | Reason |
|---|---|---|
| `.clinerules` | **left modified, uncommitted** | The change is the Product Owner's own ratification note for `docs/plan/` (2026-11-24). It is an owner-controlled document (`.clinerules` §11). Committing it would attribute an owner decision to an agent, and discarding it would destroy the owner's edit. It is left exactly as found — the same treatment the previous window recorded |
| any other path | **untouched** | The working tree at the close holds exactly the ten changed files listed above plus the new test file and this report. Nothing else was modified, reverted or stashed — so no foreign uncommitted work was captured, and none was lost |


**No destructive git command was run:** no `reset --hard`, no `clean -fd`, no `stash`, no
`checkout .`, no `rebase`, no `amend`, no `force`. The repository went from **19 commits ahead** of
`origin/hackathon-mvp` (and 0 behind) to **22 ahead** before the push, with nothing lost.

### 7.3 The push

Authorised scope, honoured literally: **`origin/hackathon-mvp` only**. No force, no tag, no other
branch, no PR, no CI trigger beyond what a push causes by itself.

**Observed result — not a claim, a transcript:**

```
$ git push origin hackathon-mvp
To https://github.com/shomonrobie/amsdp/
   a4ddc2c..6fa7e6f  hackathon-mvp -> hackathon-mvp

$ git fetch origin; git rev-parse HEAD; git rev-parse origin/hackathon-mvp
local  6fa7e6fc2490bf8f0e49728d941fd742b575591a
remote 6fa7e6fc2490bf8f0e49728d941fd742b575591a

$ git rev-list --left-right --count origin/hackathon-mvp...HEAD
0       0
```

* **The remote tip is `6fa7e6fc2490bf8f0e49728d941fd742b575591a`** — the docs commit carrying this
  report. Local and remote are identical (0 ahead, 0 behind) — the G-4 claim in Amendment A-4 that the
  push happened is `VERIFIED`, unlike the *product behaviour* it describes, which is not.
* **22 commits went up** in this push, all inspected by `--oneline` and by `diff --stat`
  (**114 files, 19,688 insertions, 650 deletions** across the whole ahead-set) before the push. They
  are the 19 that had accumulated from the MP-05…MP-33 work plus the 3 from this window.
* **The pushed range was scanned for secret material** before it left the machine
  (`BEGIN … PRIVATE KEY`, `ghp_…`, `sk-…`, `AKIA…` patterns): **0 matches**. No credential is in the
  history that was pushed.
* The only modified tracked file still in the working tree is **`.clinerules`** (the owner's
  `docs/plan/` ratification note, §7.2) — deliberately not committed, and visible in
  `git status --branch` as the sole entry.
* This verification paragraph was written **after** the push and therefore lands in a follow-up docs
  commit; the queue-relevant fact it records is the tip above, which is what `origin/hackathon-mvp`
  held at verification time.


<!-- Push verified above: a4ddc2c..6fa7e6f, then 6fa7e6f..a1a0bdb. Any further docs-only commit that
     touches this report or the register is itself after the push and cannot contain its own hash. -->


---

## 8. What is still open — stated plainly, not buried

| Item | State after this window | Nothing was done to resolve it because |
|---|---|---|
| **B-4** — read the owner's live database | **OPEN — undecided** | The owner clarified *which* database exists (Ubuntu host, `:5433`) but has **not selected an access method**. No port, firewall, SSH or `pg_hba.conf` change was made or attempted |
| **B-2** — live application/runtime verification | **OUTSTANDING** | Requires a browser session or a live API call against the deployment. Not performed, therefore not claimed |
| **B-3** — midnight rollover observation | **OUTSTANDING** | Requires either a live observation or a clock control on the deployment. Neither is available in this window |
| **B-1** — live reseed | **WITHHELD** | The demo-data authority is not a reseed authority; the two were deliberately kept apart |
| **First clean rehearsal** (PO-04) | **NOT HELD** | The overbooking/priority gate stands; MP-09 → MP-13 → MP-14 → MP-15 stay authorised-but-gated |
| **QUE-005** | **OPEN** | No owner was named; assigning one myself would invent an answer |
| **MP-33** — first green CI run | **MECHANICALLY UNBLOCKED, NOT ACCEPTED** | The push makes a green run *possible*; it does not provide one, and it certainly does not provide the owner's signature |
| **Q-3 pair** (`banglanamesense-dataset`, `calendar-render`) | **UNCHANGED** | Both are harness defects with a recorded diagnosis (committed blob hash, `git ls-files --eol`, ESM loader paths); neither is touched by this work |

**What Q-1 and Q-2 did *not* do.** They did not close a milestone, they did not move MP-33, and they
did not touch MP-44's own multi-display scope — Q-1 was *folded into* MP-44, which is still blocked by
B-4 for everything else it contains.

---

## 9. Governance and skill compliance (`.clinerules` §6)

### 9.1 Documents read and applied, by domain (§4 routing table)

| Domain | Governing material read in this window | How it was followed |
|---|---|---|
| Frontend UI / components | `frontend/components/`, `frontend/lib/i18n.js`, the dashboard page and its three test files | The tile change reuses the existing tile array and the existing `t()` dictionary; the new caption exists in **both** languages; no component was duplicated and no new dependency was added |
| Backend API | `docs/product/AMSDP_Business_Rules_V1.0.md` §8 (facility day), the patient and dashboard modules | The day resolves through the **existing** `common.timeutil.operational_today`, which reads `organizations.timezone`; no second day-source was introduced |
| Multi-tenant data / isolation | `backend/common/auth.py` scope checks, the dashboard's own branch scoping | Neither change touched a query, a scope filter or a tenant column — the org remains derived from the token, and the tests that assert cross-org behaviour (`test_today_cross_org_empty`) still pass |
| Audit / integrity | `backend/common/audit.py`, BR Part X | No audit event was added, removed or rewritten; the audit-coverage tests passed in the full run |
| Database / migrations | The migration chain and `alembic_version` | **No schema change, no migration, no ad-hoc DDL.** `alembic_version` is `b2e5c7d91a04`, unchanged from the start of the window |
| Documentation (§11, §12) | `docs/governance/AMSDP_Docs_Index_V1.0.md` (read first, Revision 49), the decision record, the plan, the register | Every document written went to `docs/implementation/`, `docs/plan/` or `docs/decisions/` — existing subfolders only. Append-only additions; **no earlier sentence was rewritten, moved or deleted**. Docs Index advanced to **Revision 50** in the same task |
| LLM routing (§8) | — | Not applicable: no model call is made by the product code, and none was needed by this work |

### 9.2 Skills

**No specialized skill package is installed in this workspace** (`.clinerules` §5 — verified: no
`.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). Therefore **no skill was used and none
is claimed.** The governance documents in §9.1 stood in their place, as §5 instructs. Installing a
skill would require owner approval and was not attempted.

### 9.3 Non-negotiables (§3) — point by point

| Non-negotiable | Evidence in this window |
|---|---|
| Never log or expose secrets | No credential, token or key was read, printed or committed. The test database needed no password (loopback trust); the one database URL used was exported per-command in the shell and **never written into a file in the tree** |
| The UI is never the safety boundary | The tile change is a *display* fix and is declared as such. Nothing in it grants or denies access; the server-side scope filters are untouched and re-tested |
| Access enforced server-side | No endpoint's authorization logic was modified. The dashboard's org/branch derivation from the token is unchanged |
| Cross-tenant failure is a non-disclosing 404 | Re-tested and green (`test_today_cross_org_empty`, in the 993-test run) |
| One tenant key, `organization_id` | No new column, no second tenant key |
| Audit events append-only | No audit write path was modified; no audit row was deleted or rewritten |
| Denials are recorded | No denial path was touched |
| Forward-only idempotent migrations | No migration was created or applied |
| Never claim unverified capability | Every figure here was produced by a command in this window. `VERIFIED` and `ACCEPTED` are **not** claimed for anything. No CI gate is claimed |
| Don't use a library because it was discovered | No dependency was added to either package manifest |

### 9.4 Verification actually performed (§7 evidence standard)

* **IMPLEMENTED** — both changes exist and are reachable from the running code paths (§3.2, §4.3).
* **TESTED** — `993 passed, 0 failed` backend; `467 / 465 / 0 / 2` frontend; `29/29` on the three
  dashboard files; `46 passed` on the three touched backend files; a successful production build.
* **VERIFIED** — **not claimed.** The independent artefact the standard requires (a browser run or a
  live API call against the deployment) does not exist for these changes (**B-2**).
* **ACCEPTED** — **not claimed.** The owner's signature is outstanding.
* **Negative controls** — three, each producing the expected red, each file restored byte-identically.

### 9.5 Disclosures — including a mistake made in this window

1. **A document edit was made wrongly and repaired immediately.** While appending a change-log row to
   the register, the *first* edit replaced the existing **MP-29** row instead of adding a row after it.
   The mistake was caught in the same minute by reading `git diff --stat`, which showed `2 ++` where an
   append should have shown an addition; the MP-29 row was restored verbatim from the text still visible
   in the failed edit's output, and the final diff shows **2 insertions, 0 deletions**. It is disclosed
   rather than quietly fixed, because a documentation loss is exactly the kind of thing that is silent
   unless someone says so.
2. **One stray blank line** sits before the new annex in `docs/governance/AMSDP_Docs_Index_V1.0.md`. It
   came from an aborted append helper before the annex was written properly; it is whitespace only, it
   is part of the same addition, and no existing line was touched.

3. **The backend suite took 16 minutes**, and an earlier attempt's transcript came back empty — which is
   why no figure was claimed until the run's own summary line had been read.
4. **The database is a development database** with pytest fixtures in it; its counts move as tests run,
   so the figures in §2.1 are a point-in-time measurement, not a curated dataset.
5. **No demo data was seeded** despite the authority (§6), and **no access method for B-4 was chosen**.

### 9.6 Where this report was written

`docs/implementation/AMSDP_Q1_Q2_Facility_Day_And_Dashboard_Counts_Report_V1.0.md` — an existing
subfolder, subject-matching name, `AMSDP_<Topic>_<Version>.md` convention (`.clinerules` §11).
**No migration** was performed, so no manifest entry is required. The Docs Index was updated in the same
window (**Revision 50**), as §12 obliges.
