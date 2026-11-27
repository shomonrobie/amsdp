# AMSDP — T-10 Disposable-Database Execution Plan — V1.0

| | |
|---|---|
| **Document** | `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` |
| **Purpose** | Request authority for two specific disposable-database runs, with the exact commands, targets, data, duration, cleanup and evidence rules stated in advance |
| **Written** | 2026-11-27, fifth window (controlled verification preparation) |
| **Status** | **PLAN ONLY.** No database was accessed, created, migrated, seeded, modified or dropped to write it. `amsdp_verify_1129` is untouched and is **not** to be dropped |
| **Governing constraints** | `.clinerules` §3 (fail closed, audit, no secrets), §9 (no execution without request); the standing instruction that **database access requires explicit authorisation** (OA-3) |
| **Companion** | `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` §10 (C1 is committed on retained evidence *because* this run has not happened) |

> **What is being asked for.** Permission to create two empty databases on the existing local PostgreSQL
> instance at `127.0.0.1:55432`, migrate them, run two bounded test commands against them, mutate one source
> line and restore it byte-identically, and keep the logs. Nothing else.

---

## 1. The two gaps these runs close

| Gap | Finding | Why nothing local can close it |
|---|---|---|
| **G-1 — T-10 fixtures have never executed** | The seven modules' import-time seeding was moved into module-scoped `autouse` fixtures (register §19.3). Collection-level evidence is complete (`1,071 collected, 0 errors, no connection attempt`); **execution-level evidence is zero** | The fixtures create rows by design. Their correctness can only be observed against a live schema |
| **G-2 — MP-46 capability has no negative control** | `_denied()` records `"capability": DISPLAY_MANAGE` (`backend/queuing/displays.py:149`) and two assertions read it (`tests/test_display_admin.py:192`, `:272`). That the assertions are *load-bearing* was argued from code, not observed | Removing the field and watching both tests fail requires a database — the refusal cannot be reached otherwise |

Both are **execution** gaps, not design gaps. Neither changes a line of product code; G-1 must not change
one, and G-2's mutation is reverted inside the same session.

## 2. Environment, as verified before writing this plan

| Item | Value | Source |
|---|---|---|
| PostgreSQL instance | **16.4**, `127.0.0.1`:**55432**, role `amsdp`, local trust (no password in any DSN) | Deviation record §2; the same instance the third window used |
| Developer database `amsdp` | reachable only through the **compose** stack, host port **`5433`** → container `db:5432`, volume `amsdp_pg_data` | `docker-compose.yml:49` (`ports: ["5433:5432"]`), `:52`–`:55` |
| DSN precedence | `AMSDP_DATABASE_URL` **always wins**; the fallback composes `5433/amsdp` | `backend/common/database.py:37`, `:24`–`:34` |
| Python | 3.13.5, venv `e:\amsdp\.venv`; psycopg2 2.9.13, SQLAlchemy 2.1.9, Alembic 1.20.1 | measured this window |
| Alembic chain | 19 revisions, `backend/alembic.ini` + `backend/alembic/versions` | measured this window |
| Suite size | **1,071** tests (1,069 + 2 collection-purity guards) | `pytest --collect-only -q` |

**Databases this plan creates — both new, neither existing:**

| Name | Used by | Notes |
|---|---|---|
| `amsdp_t10_a_1127` | Run A — whole suite | Empty at creation; schema built by the migration |
| `amsdp_t10_b_1127` | Run B — capability negative control | Empty at creation; schema built by the migration |

Neither name collides with anything known to exist (`amsdp`, `amsdp_demo`, `amsdp_verify_1127`,
`amsdp_verify_1127b`, `amsdp_verify_1128`, `amsdp_verify_1129`, `amsdp_mp16_scratch`, `amsdp_verify_2829`).
The existence check below is idempotent and prints the catalogue before creating anything, so a collision
stops the run instead of overwriting.

---

## 3. Pre-flight: verify the target *before* touching anything

Two files are created under `E:\Temp\` (outside the repository, so nothing is added to the tree). They are
reproduced in full here so they can be reviewed before they exist.

### 3.1 `E:\Temp\amsdp_target_guard.py` — refuses to proceed on the wrong target

```python
"""Refuse unless AMSDP_DATABASE_URL names the intended disposable database.

Usage:  python E:\Temp\amsdp_target_guard.py <expected-database-name>
Exit 0 = target verified.  Any other exit = STOP; do not run pytest.
"""
import os
import sys
from urllib.parse import urlparse

import psycopg2

EXPECTED_PORT = 55432
FORBIDDEN = {"amsdp", "amsdp_demo"}

db = sys.argv[1]
if db in FORBIDDEN or not db.startswith("amsdp_t10_"):
    sys.exit("REFUSING: %r is not a T-10 disposable database" % db)

url = os.environ.get("AMSDP_DATABASE_URL")
if not url:
    sys.exit("REFUSING: AMSDP_DATABASE_URL unset - the fallback is the dev DSN (5433/amsdp)")

parts = urlparse(url)
if parts.port != EXPECTED_PORT:
    sys.exit("REFUSING: port %r, expected %d" % (parts.port, EXPECTED_PORT))
if parts.path.lstrip("/") != db:
    sys.exit("REFUSING: URL names %r, expected %r" % (parts.path.lstrip("/"), db))

conn = psycopg2.connect(url.replace("postgresql+psycopg2", "postgresql"))
cur = conn.cursor()
cur.execute("select current_database(), inet_server_port(), version()")
name, port, version = cur.fetchone()
if name != db or port != EXPECTED_PORT:
    sys.exit("REFUSING: server reports %r on %r" % (name, port))
cur.execute("select datname from pg_database order by 1")
print("TARGET VERIFIED:", name, "port", port)
print("server:", version.split(",")[0])
print("catalogue:", [row[0] for row in cur.fetchall()])
conn.close()
```

**Why the check is two-sided.** The URL is checked (port, database name, not a forbidden name) *and* the
server's own answer is checked (`current_database()`, `inet_server_port()`). A typo in either direction
fails closed, and it fails before the first `pytest` process starts — not after.

### 3.2 `E:\Temp\amsdp_create_db.py` — idempotent creation, never overwrites

```python
"""Create one empty database on the disposable cluster; abort if it already exists."""
import sys
import psycopg2

name = sys.argv[1]
conn = psycopg2.connect(host="127.0.0.1", port=55432, dbname="postgres", user="amsdp")
conn.autocommit = True
cur = conn.cursor()
cur.execute("select 1 from pg_database where datname = %s", (name,))
if cur.fetchone():
    sys.exit("REFUSING: %r already exists - not touching it" % name)
cur.execute('create database "%s"' % name)
cur.execute("select datname from pg_database order by 1")
print("created:", name)
print("catalogue:", [row[0] for row in cur.fetchall()])
conn.close()
```

### 3.3 The pre-flight sequence (read-only until step 3)

```powershell
cd e:\amsdp\backend
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp@127.0.0.1:55432/postgres"
..\.venv\Scripts\python.exe -c "import psycopg2; c=psycopg2.connect(host='127.0.0.1',port=55432,dbname='postgres',user='amsdp'); cur=c.cursor(); cur.execute('select version(), inet_server_port()'); print(cur.fetchone()); cur.execute('select datname from pg_database order by 1'); print([r[0] for r in cur.fetchall()])"
```

**Stop conditions at this point** (each one ends the session, nothing created):

1. the instance answers on any port other than 55432, or does not answer;
2. `amsdp_t10_a_1127` or `amsdp_t10_b_1127` already exists;
3. authentication fails — **do not** improvise a password; report and stop (§3 forbids quoting credentials
   anywhere, including logs).


---

## 4. Create and migrate (for each database)

```powershell
cd e:\amsdp\backend
..\.venv\Scripts\python.exe E:\Temp\amsdp_create_db.py amsdp_t10_a_1127
..\.venv\Scripts\python.exe E:\Temp\amsdp_create_db.py amsdp_t10_b_1127

# A
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_t10_a_1127"
..\.venv\Scripts\python.exe E:\Temp\amsdp_target_guard.py amsdp_t10_a_1127
..\.venv\Scripts\python.exe -m alembic upgrade head *>&1 | Tee-Object -FilePath E:\Temp\amsdp_t10_a_alembic_1127.txt
..\.venv\Scripts\python.exe -m alembic current  *>&1 | Tee-Object -Append -FilePath E:\Temp\amsdp_t10_a_alembic_1127.txt

# B
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_t10_b_1127"
..\.venv\Scripts\python.exe E:\Temp\amsdp_target_guard.py amsdp_t10_b_1127
..\.venv\Scripts\python.exe -m alembic upgrade head *>&1 | Tee-Object -FilePath E:\Temp\amsdp_t10_b_alembic_1127.txt
..\.venv\Scripts\python.exe -m alembic current  *>&1 | Tee-Object -Append -FilePath E:\Temp\amsdp_t10_b_alembic_1127.txt
```

**Difference from the third window.** There, the migration output went to the console
(`Select-Object -Last 12`) and was never captured, which is why "the chain ran zero → head" is classified
REPORT-ONLY in the deviation record §2. Here both `upgrade head` and `current` are tee'd to files, so the
claim becomes artefact-backed. `alembic current` must print the same head revision the repository's chain
ends at; if it does not, the run stops before any test executes.

## 5. Run A — execution-level T-10 (whole suite)

```powershell
cd e:\amsdp\backend
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_t10_a_1127"
..\.venv\Scripts\python.exe E:\Temp\amsdp_target_guard.py amsdp_t10_a_1127
..\.venv\Scripts\python.exe -m pytest -q --tb=short *>&1 | Tee-Object -FilePath E:\Temp\amsdp_t10_runA_1127.txt
Get-Content E:\Temp\amsdp_t10_runA_1127.txt -Tail 5
```

**Pass condition.** `1071 passed` (or more, if the suite grew) with **0 failed, 0 errors**, and no
`OperationalError` anywhere in the log. This is the first execution of the T-10 fixtures; a failure here is a
**result**, not an obstacle — it is recorded and the run is not patched mid-flight.

**What it proves if green:** collection is pure *and* the fixtures still do their job — the rows that used to
be created at import are now created for every module that needs them, in whatever order pytest chooses.
That is the invariant T-10 was about.

## 6. Run B — MP-46 capability negative control (mutation, reverted in-session)

The mutation is **one deleted line**, chosen because both assertions read it:

```
backend/queuing/displays.py:149      "capability": DISPLAY_MANAGE,
```

```powershell
cd e:\amsdp
# 1  record the pre-mutation state
Get-FileHash backend\queuing\displays.py -Algorithm SHA256
Copy-Item backend\queuing\displays.py E:\Temp\displays_before_1127.py -Force
git --no-pager diff --numstat -- backend/queuing/displays.py

# 2  mutate: delete the single line that writes the capability ("capability": DISPLAY_MANAGE,)
#    (one line, no other edit; the surrounding after={...} dict is otherwise untouched)

# 3  confirm exactly two tests are selected before running them
cd backend
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_t10_b_1127"
..\.venv\Scripts\python.exe E:\Temp\amsdp_target_guard.py amsdp_t10_b_1127
..\.venv\Scripts\python.exe -m pytest tests/test_display_admin.py -k "refused or cross_tenant" --collect-only -q

# 4  run them; expect TWO FAILURES, both on the capability assertion
..\.venv\Scripts\python.exe -m pytest tests/test_display_admin.py -k "refused or cross_tenant" -q *>&1 |
    Tee-Object -FilePath E:\Temp\amsdp_t10_runB_mutation_1127.txt

# 5  restore byte-identically and prove it
cd e:\amsdp
Copy-Item E:\Temp\displays_before_1127.py backend\queuing\displays.py -Force
Get-FileHash backend\queuing\displays.py -Algorithm SHA256          # must equal step 1
git --no-pager diff --numstat -- backend/queuing/displays.py        # must be 21/3 again, nothing more

# 6  re-run to green
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_display_admin.py -k "refused or cross_tenant" -q *>&1 |
    Tee-Object -FilePath E:\Temp\amsdp_t10_runB_restored_1127.txt
```

**Pass condition for Run B** is a *sequence*, all four parts required:

| Step | Required observation |
|---|---|
| 3 | exactly **2** tests selected (if the selector picks a different number, stop — the control is not measuring what it claims) |
| 4 | exactly **2 failed**, each a `KeyError`/assertion on `capability` — not an import error, not a collection error |
| 5 | SHA-256 identical to step 1; `git diff --numstat` back to `21 3` |
| 6 | exactly **2 passed** |

**Why the restore is a copy, not `git checkout`.** `displays.py` carries the **uncommitted** MP-46 change.
Any `git checkout --`, `git stash`, `git restore` or `git reset` on that path would destroy work rather than
restore it, and `.clinerules` §9 forbids exactly those operations. A byte copy plus a hash comparison is the
only safe inverse here.


---

## 7. Duration and external services

| Step | Expected | Basis |
|---|---|---|
| Pre-flight + creation (2 databases) | < 10 s | one catalogue query each |
| Migration, both databases | < 30 s | 19 revisions against an empty schema, measured previously in seconds |
| **Run A** (1,071 tests) | **9–12 min**, hard stop at 20 min | the retained third-window log: `1069 passed … in 548.80s` (9:08) |
| **Run B** (4 short invocations) | < 1 min | two 2-test runs plus hash/restore |
| Recording hashes and results | ~10 min | writing them into the register and this plan's §11 |
| **Whole session** | **~15 min of machine time**, ~25 min wall clock | |

**External services required: none.** No Docker, no compose stack, no container, no network beyond loopback
`127.0.0.1:55432`, no browser, no O-1/Ubuntu host, no GitHub, no CI, no deployment. The frontend suite is not
run (it needs no database and is unaffected by T-10).

## 8. What data will be written

**Run A** — the suite's own fixtures write, into `amsdp_t10_a_1127` only:

- reference rows: organisations, branches, departments/rooms, staff users, doctors, the demo-style patient
  rows the modules require;
- business rows: queue entries with status history, appointments, clinic sessions, schedules;
- audit rows: `record_audit` output including denial rows (`queue.display.denied`, `request.denied`);
- tracking tokens and notification rows for the PQT and token modules;
- whatever the modules purposely leave behind — several purge per test, several keep reference rows to
  preserve an audit trail.

**Run B** — into `amsdp_t10_b_1127` only: the same fixture rows for `test_display_admin.py`, plus one denial
row per refused request, each carrying the caller's org/branch and a target id that a test asserted against.

**Never written:** no row in `amsdp`, `amsdp_demo`, `amsdp_verify_*` or any other database; nothing exported
from any database; no file in the repository; no credential or DSN-with-secret in any log.

## 9. Cleanup, and the one database that is not ours to drop

| Object | Disposition |
|---|---|
| `amsdp_t10_a_1127` | **Recommended: dropped at the end of the approved session**, after the log hashes are captured and the results recorded. Alternative if the owner prefers re-inspection: retained 7 days, dropped under a later approval |
| `amsdp_t10_b_1127` | Same as above |
| **`amsdp_verify_1129`** | **Untouched. Not dropped.** It is the subject of a recorded deviation; dropping it would be a second unauthorised act on the same object (deviation record §3, §6) |
| `E:\Temp\amsdp_*_1127.txt`, `displays_before_1127.py` | Retained until the resulting report is accepted; their SHA-256 values are recorded in-repo, so the files can be discarded later without losing provenance |

```powershell
# only if the owner authorises the drop, and only after the hashes are recorded
..\.venv\Scripts\python.exe -c "import psycopg2; c=psycopg2.connect(host='127.0.0.1',port=55432,dbname='postgres',user='amsdp'); c.autocommit=True; cur=c.cursor(); [cur.execute('drop database if exists %s' % n) for n in ('amsdp_t10_a_1127','amsdp_t10_b_1127')]; cur.execute('select datname from pg_database order by 1'); print([r[0] for r in cur.fetchall()])"
```

## 10. How this plan guarantees the developer database `amsdp` is not accessed

Five independent mechanisms, in the order they take effect:

1. **Different port, different instance.** The developer database is published on **`5433`** by the compose
   stack (`docker-compose.yml:49`); every command here names **`55432`**. No command in this plan mentions
   5433, `amsdp` or `amsdp_demo` as a target.
2. **The environment variable is set explicitly, in the same shell that runs the command.** `AMSDP_DATABASE_URL`
   takes precedence over the fallback (`common/database.py:37`), and the fallback is exactly the dev DSN
   (`5433/amsdp`, `:24`–`:34`). Setting it per-session means a stale value cannot leak in from another shell.
3. **`amsdp_target_guard.py` fails closed on six conditions** before any test process starts: unset variable,
   forbidden name, wrong prefix, wrong port, wrong database name, or a server that disagrees with the URL.
4. **The guard connects with the same URL the suite will read** — not with a copy of the string — so what is
   verified is the actual target, and it verifies it by asking the server (`current_database()`,
   `inet_server_port()`), not by trusting the string.
5. **No `docker` command is used,** so the compose stack is neither started nor addressed, and no container
   port mapping is involved.

**One honest qualification.** If `55432` and the compose stack happened to be the *same* PostgreSQL cluster,
`amsdp` would still be a distinct database that no command here names, opens or writes — the guarantee would
degrade from "different instance" to "different database", which is still sufficient. What the plan
deliberately does **not** do is connect to 5433 to prove the two are separate, because that would itself be
the unauthorised access this section is designed to avoid.


---

## 11. Logs, hashes and retention

Every command's output is captured to a file, and each file is hashed immediately after it is written:

```powershell
Get-ChildItem E:\Temp\amsdp_t10_*_1127.txt, E:\Temp\amsdp_*_alembic_1127.txt |
    Get-FileHash -Algorithm SHA256 |
    ForEach-Object { $_.Hash + '  ' + [System.IO.Path]::GetFileName($_.Path) }
```

| Planned artefact | Contents it must contain |
|---|---|
| `E:\Temp\amsdp_t10_a_alembic_1127.txt` | `Running upgrade … -> <head>` for every revision, then `alembic current` printing the same head |
| `E:\Temp\amsdp_t10_b_alembic_1127.txt` | the same, for Run B's database |
| `E:\Temp\amsdp_t10_runA_1127.txt` | the whole-suite summary line (`… passed in …s`) and any failure text |
| `E:\Temp\amsdp_t10_runB_mutation_1127.txt` | `2 failed`, with the capability assertion in both tracebacks |
| `E:\Temp\amsdp_t10_runB_restored_1127.txt` | `2 passed` |
| `E:\Temp\displays_before_1127.py` | the exact pre-mutation bytes (kept as the restore source *and* as evidence) |

**Where the hashes are recorded.** Into the register as a new section (§20, appended at execution time) and
into this document as a filled-in §11.1 — never only into a chat message. Those two are in the repository, so
the logs themselves become disposable once the report is accepted; the provenance does not.

**Not retained, and said so:** console scrollback, and the PowerShell history file beyond the lines cited in
the deviation record — it is mutable, and the earlier record already treats it as a pointer rather than a
hash-stable artefact.

## 12. If something fails

| Situation | Response |
|---|---|
| Guard refuses | **Stop.** Nothing was created or touched. Report which condition fired |
| Migration does not reach head | **Stop before any test.** Record the `alembic current` output; do not re-run, do not edit a migration |
| Run A fails on a specific test | **Record it.** Capture the failing ids and tracebacks, finish the log, and report. Do **not** patch a test or the product code in the same session — that would destroy the evidence the run exists to produce |
| Run A fails at *collection* | Contradiction with E-4 (1,071 collected with no database). Record it and stop; it means the environment differs from the one this plan was written against |
| Run B's selector picks ≠ 2 tests | **Stop.** Record what it selected. The control is only valid at 2 |
| Run B's mutation produces 0 failures | **That is a finding**: the assertions are not load-bearing. Record it, restore the file, report — do not adjust the mutation to make it fail |
| Restore hash differs | **Stop everything.** The working tree now differs from the reviewed state; report before any further step |
| Authentication fails | Stop. Do not type, guess or log a password |

## 13. What approval would cover — and what it would still not

**Authorised acts, if granted (OA-3 for this plan specifically):**

1. run read-only catalogue queries on `127.0.0.1:55432` as role `amsdp`;
2. create exactly two empty databases: `amsdp_t10_a_1127`, `amsdp_t10_b_1127`;
3. run `alembic upgrade head` and `alembic current` against those two databases only;
4. write test-fixture data into those two databases by running the suite against them;
5. delete **one line** in `backend/queuing/displays.py` (line 149) and restore it byte-identically in the same
   session, hash-verified;
6. run `pytest` four times: the whole suite once, and the two-test selector three times;
7. create and retain the six files listed in §11 under `E:\Temp\`, and the two helper scripts in §3;
8. drop `amsdp_t10_a_1127` and `amsdp_t10_b_1127` at the end of the session — **only if the owner grants this
   explicitly**; otherwise they are retained.

**Still forbidden under this approval, without a separate grant:**

- any access to the developer database `amsdp` or to `amsdp_demo`;
- any access to, or drop of, **`amsdp_verify_1129`** or any other pre-existing database;
- any further mutation of source beyond the single reverted line;
- any staging, commit, push or destructive Git operation (that is OA-1, a separate request);
- starting the compose stack, the demo stack, or contacting O-1 / Ubuntu;
- writing a new migration, changing the schema, or reseeding demo data;
- editing `.clinerules`.

## 14. What this plan does not claim

It does not claim T-10 is verified — it is implemented and collection-tested only. It does not claim MP-46's
capability field is proven load-bearing until Run B has run. It does not promote, accept or close any package.
It has not touched a database: the plan is a request, and this window's database access remains **zero**.

<!-- Plan only. Written 2026-11-27, fifth window; no database was accessed to write it. -->

---

## 15. Owner decision recorded — 27 November 2026 (fifth window)

| Question put in §13 | Owner answer |
|---|---|
| Execute Run A and Run B? | **Not yet.** The commands are submitted for final review first (this document, §2–§9) |
| Drop `amsdp_t10_a_1127` and `amsdp_t10_b_1127` afterwards? | **No. Both are retained.** §9's cleanup therefore means *stop using them and leave them in place*: no `DROP DATABASE` runs, and a drop needs a separate, explicit grant later |
| Scope | Confirmed exactly as §2/§3 state: the two newly created disposable databases, `127.0.0.1:55432`, explicit proof that neither connection can resolve to `amsdp`, Run A and Run B exactly as specified, complete logs + migration transcript + database-identity evidence + file hashes |

Consequences for execution, stated so they are not improvised later:

1. **`DROP DATABASE` is removed from the procedure.** §9.3 becomes: leave both databases in place, record them as
   retained by owner decision, and record their existence in the evidence file.
2. `amsdp_verify_1129` remains untouched and is still excluded by name (§9.1).
3. "No other database may be accessed" is enforced by §5's target guard; this decision does not relax it.
4. Nothing else in §2–§8 changes: same commands, same order, same expected results.

<!-- §15 appended 2026-11-27. §1–§14 preserved exactly as written; the only operative change is that the
     post-run drop is withdrawn and the two databases are retained. -->


