# AMSDP — Backend Execution Evidence Record — 27 November 2026 — V1.0

| | |
|---|---|
| **Document** | `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` |
| **Purpose** | Preserve, inventory and integrity-stamp the primary artefacts behind the 27 November 2026 backend execution, and state exactly what each artefact proves |
| **Written** | 2026-11-27 (controlled audit-resolution phase) |
| **Authorised by** | The audit-resolution mandate, §3 (evidence preservation, finding **F-07**) |
| **Companion documents** | `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` (independent audit, F-01…F-12 + F-13); `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §15 (the execution record itself) |
| **Status of the underlying work** | **TESTED, not VERIFIED and not ACCEPTED** — a green suite is single-process test evidence, not a browser run, not a CI run, not acceptance |

> **This record adds no new claim.** Everything below is a measurement of an artefact that already
> existed, plus the commands that produced it where those commands are still retained. Where the
> retained evidence does not support a statement in the register, this record says so and leaves the
> register's status unchanged (the mandate authorised no status change).

---

## 1. What this record is, and what it is not

**It is** the durable, hash-stamped record of the execution evidence: what files exist, where they
were, their exact bytes, their SHA-256 digests, the pytest summary lines they contain, and — for each
claim in register §15 — whether the retained output confirms it, partially supports it, or does not
support it.

**It is not:**

- a re-run. **No test was executed while this record was written** (mandate §8, §11). Regenerating a
  missing artefact was prohibited, and none was regenerated.
- a promotion of any work package. The register's §15.4 statuses stand exactly as written.
- proof that the two scratch databases were empty. Emptiness is asserted by the register's narrative;
  the retained artefacts show only that one of the two databases existed before the migration ran and
  that the other was not yet listed at 11:20:38 (see §7).
- a claim about PostgreSQL 17. **The engine under test is PostgreSQL 16.4** — see §7.3, which
  contradicts register §15.1 and is reported as new finding **F-13**.

---

## 2. Evidence inventory — originals, copies, sizes and digests

**Original location of every artefact:** `E:\Temp\` (outside version control; not a repository path).

**Preserved copy of the 27 November set:** `E:\amsdp_audit_evidence_27nov2026\` — created during this
phase by a copying operation that **did not touch the originals**. Every copy was hashed after copying
and compared with its original: **23 of 23 matched, 0 mismatches, 0 missing.**

Three further `amsdp*` files in `E:\Temp` were deliberately **outside** this set because they do not
belong to this execution and carry earlier dates: `amsdp_mig_probe.sqlite` (2026-11-26, a throwaway
SQLite probe), `amsdp_pre_mp35_schema.json` (2026-11-25, the MP-35 schema snapshot), `amsdp-pipcheck`
(2026-11-24, 1 byte, no extension). They were **not** copied, **not** modified and **not** deleted; the
evidence record does not depend on them.

| File | Bytes | Last modified (local) | SHA-256 (original = copy) |
|---|---:|---|---|
| `amsdp_collect.txt` | 205,334 | 2026-11-27 11:30:34 | `19D6B8F942C9D86C619E4C607E271AE2B83A588117213F1893F92555CBED21AD` |
| `amsdp_dbs.txt` | 228 | 2026-11-27 11:20:38 | `7D38E47740AE88689DA9DF652DC5D5610F49D75703268A890BFE9EF96C9DA2CD` |
| `amsdp_files.txt` | 3,838 | 2026-11-27 11:31:08 | `ED5574CC03CA29D57B413507114A636FC40ADAE5FFBFBEC21502DE5C6A98F477` |
| `amsdp_full.txt` | 938 | 2026-11-27 11:30:52 | `9EE278B8101BC71AA188CD09D1FBC2482469CFFD3547AC260ED95EF047A94566` |
| `amsdp_full2.txt` | 14,816 | 2026-11-27 11:53:50 | `B92A0DDE26473D629B42F8D0704BD2CCD6D10944611D84D1CA7242964EFEEF08` |
| `amsdp_full3.txt` | 14,816 | 2026-11-27 12:07:13 | `77DAF4FDE660F43A7ADDA5C88AE77F751647B88A0A2985D353E964CB07BDAD47` |
| `amsdp_mig.txt` | 5,284 | 2026-11-27 11:20:43 | `E8E3DF8A0A4636DAD15CCC6E69596688729920CD55975E52CA301E73B93B49EA` |
| `amsdp_one.txt` | 3,006 | 2026-11-27 11:42:14 | `6A8AEEFC2FD5005A295B9753D4C216EFF887CE7CEE4E253B7454D178D0A3E084` |
| `amsdp_one_err.txt` | 0 | 2026-11-27 11:42:09 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` (empty) |
| `amsdp_perfile.txt` | 3,441 | 2026-11-27 11:42:14 | `792165042489ABDEC2DA05CAFFF31D96A7CDC8D1ED420DC4E7D7B4D0A2D8A5F3` |
| `amsdp_t1.txt` | 261,290 | 2026-11-27 11:20:57 | `B77E9218127A6BFD1C52923E6AAE7E74B68C6702FEA14EB0FCA3201B77542492` |
| `amsdp_t2.txt` | 15,748 | 2026-11-27 11:21:05 | `AD7AF5550B01243E190EB456277BFA5A0AD6045F17DEFA35182442C4318912AC` |
| `amsdp_t3.txt` | 7,870 | 2026-11-27 11:21:28 | `09591BBD6D02A1C209460A4E6FC1B1F889C2D6F5CB1AC7633D84465C55C49539` |
| `amsdp_t4.txt` | 136,404 | 2026-11-27 11:21:39 | `68C44D7BC4041F5658C378C26032434F459A400A9DB14DA3DBACA734F4C2B41F` |
| `amsdp_t5.txt` | 2,890 | 2026-11-27 11:21:56 | `407935809255FAD245A2E07B7997C75EEBAD3511B4DC3284ABB72D2C6250ADA8` |
| `amsdp_t6.txt` | 5,674 | 2026-11-27 11:22:15 | `D7215A3E241202C9EF3FCC1E247FCC679732CC54C2BBFACF54F08F84414F29B3` |
| `amsdp_t7.txt` | 2,686 | 2026-11-27 11:22:24 | `BE5829E6E960E0B4858D1A6D859FA44B8C9A1F9AEE8B24204C8BBF0AB8F1E421` |
| `amsdp_t8.txt` | 4,828 | 2026-11-27 11:22:33 | `902A4A6FE2C872C3077415DF4B9A274F9A936AE3BB57C099F6E10F5709377718` |
| `amsdp_t9.txt` | 4,338 | 2026-11-27 11:23:26 | `E2A7F7D6E144B0C1BEA4193BB2046FA31BBE14CECD11FEA63A5FF61EB6736820` |
| `amsdp_t10.txt` | 4,456 | 2026-11-27 11:23:59 | `0CC29BB61F335FC6321EF8266180CA7882CB5DEAF67950FB452EC8968B5A89E0` |
| `amsdp_t11.txt` | 2,688 | 2026-11-27 11:25:00 | `A59A8F38E733B2C0220D5CFC15E2607106256804F3EDCB9A760037CE16FAC2C0` |
| `amsdp_vp.txt` | 101 | 2026-11-27 11:30:59 | `45B8387B3FC79C776506F7A23EAAFBE72E199B6E1B656A171372094543C70CAC` |
| `amsdp_vp_err.txt` | 0 | 2026-11-27 11:30:59 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` (empty) |

**Integrity check (reproducible, read-only):**

```powershell
Get-ChildItem 'E:\amsdp_audit_evidence_27nov2026' |
  ForEach-Object { "{0} {1}" -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash, $_.Name }
```

If a digest in the table above no longer matches, the copy has been altered and must not be treated as
evidence. The originals in `E:\Temp` are the primary evidence; the copies exist because `E:\Temp` is
not a durable or version-controlled location.

---

## 3. The two executions, stated exactly

### 3.1 Binding each run to its database

The command line is the only artefact that ties a log file to a database URL. Both bindings survive in
PowerShell's retained history
(`E:\Users\RobieS\AppData\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`):

| History line | Command (database URL shown verbatim; no credential is stored in it) | Output file |
|---|---|---|
| 10801–10802 | `cd e:\amsdp\backend; $env:AMSDP_DATABASE_URL='postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_verify_1127'; python -m pytest -q --tb=line 2>&1 \| Tee-Object -FilePath 'E:\Temp\amsdp_full2.txt'` | `amsdp_full2.txt` |
| 10818–10819 | same command with `…/amsdp_verify_1127b` and `Tee-Object -FilePath 'E:\Temp\amsdp_full3.txt'` | `amsdp_full3.txt` |

Each command appears **twice** in history — PowerShell's own duplicate-entry behaviour — and each
file carries a single last-modified timestamp (`amsdp_full2.txt` 11:53:50, `amsdp_full3.txt` 12:07:13),
so one file records one completed run, not two.

The history file is **mutable**: every command typed in the same console appends to it, including the
read-only commands used to write this record. It is cited by line number and content as measured on
2026-11-27, and it is **not** offered as a hash-stable artefact.

### 3.2 First execution

| | |
|---|---|
| Database | `amsdp_verify_1127` (scratch) |
| Command | `python -m pytest -q --tb=line`, one process, from `backend/` |
| Retained output | `amsdp_full2.txt` |
| Summary line (verbatim) | `1061 passed, 66 warnings in 541.58s (0:09:01)` |
| Written at | 2026-11-27 11:53:50 |

### 3.3 Second execution

| | |
|---|---|
| Database | `amsdp_verify_1127b` (scratch) |
| Command | identical, except the database URL |
| Retained output | `amsdp_full3.txt` |
| Summary line (verbatim) | `1061 passed, 50 warnings in 542.27s (0:09:02)` |
| Written at | 2026-11-27 12:07:13 |

**Classification — CONFIRMED.** The pass counts and durations quoted in register §15.2 are exactly the
summary lines in the two retained files. The warning counts differ (66 vs 50), which is itself
consistent with two separate executions rather than one file copied twice — and the files carry
different SHA-256 digests despite identical byte lengths.

**What the runs do not establish.** That `amsdp_verify_1127b` was created empty and migrated zero → head
**before** the second run is not supported by any retained artefact: no creation command, no `alembic`
output for that database, and the database listing in `amsdp_dbs.txt` predates its existence (§7.2).
The second run's green result is real; the *provenance* of the database it ran against rests on the
register's narrative only. That is recorded as a **repeatability-evidence limitation** (F-08) and
changes no status.

---

## 4. Suite completeness — the independent collection artefact

`amsdp_collect.txt` (205,334 bytes) is a `pytest --collect-only -q` transcript:

- final line (verbatim): `1061 tests collected in 2.79s`
- 52 collected module paths, listed in `amsdp_files.txt` (52 non-blank lines) — the same list the
  per-module rollout iterated.

**Classification — CONFIRMED.** The whole-suite figure is not a partial selection: the number of tests
the run reports passing equals the number the collector finds in the same tree, and the run executed in
one process with no `-k`, `-m`, `--deselect`, `-x` or `--maxfail`, and no `pytest-xdist`.

**Caveat that matters.** Collection is a **static** count. It shows what would run; it does not show
that each module ran in the passing run — that inference comes from the summary line plus the 52-file
list, and is stated as an inference, not a measurement.

---

## 5. The per-module rollout, and the intermediate failures it preserves

`amsdp_files.txt` (52 module paths) was iterated by a `Start-Process … pytest <file> -q --tb=line` loop
(history lines 10766–10767), appending one summary line per module to `amsdp_perfile.txt`. The rollout ran
**after** corrections 1 and 2 of register §15.3 but **before** corrections 3, 4 and 5, and it is the only
retained artefact that shows suites failing:

| Module | Line in `amsdp_perfile.txt` |
|---|---|
| `tests/test_display_admin.py` | `1 failed, 12 passed, 3 warnings in 10.70s` |
| `tests/test_tracking_tokens.py` | `1 failed, 16 passed, 18 warnings in 3.69s` |
| the other 50 modules | all `passed`; no `TIMEOUT-240s` line appears anywhere in the file |

**Classification — CONFIRMED, and valuable.** This is the intermediate-failure evidence for register
§15.3 defects 3/4 (`test_display_admin.py`) and defect 5 (`test_tracking_tokens.py`). It also confirms
that no module was dropped for timing out during the rollout.

Two further artefacts belong to the same exploratory phase and are preserved for that reason, not as
pass evidence: `amsdp_full.txt` (938 bytes — an **interrupted** whole-suite attempt that stops mid
progress line at 33 %, with no summary) and `amsdp_one.txt`/`amsdp_one_err.txt` (the last module's
output reused by the loop, plus an empty stderr). `amsdp_vp.txt` (`50 passed in 0.19s`) is a targeted
voice-pack policy run.

**Intermediate-failure limitation (F-10).** The failure text of those two modules is only partially
retained: `amsdp_t6`, `t8`, `t9`, `t10` (display admin) and `amsdp_t1` (tracking) hold exploratory
output, but the rollout's `--tb=line` detail was overwritten each iteration because `amsdp_one.txt` was
reused for every module. The register's description of *why* each test failed is therefore supported by
the current test source and the module transcripts, not by a preserved failing trace for every case.

---

## 6. Migration-chain evidence

`amsdp_mig.txt` (5,284 bytes) captures `alembic upgrade head` against `amsdp_verify_1127` at
2026-11-27 11:20:43 (history line 10696). Retained lines show a full **zero → head** chain, including:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 5f3fce6757cf, initial_schema
…
INFO  [alembic.runtime.migration] Running upgrade c4d8e2a91f60 -> b2e5c7d91a04, add_schedule_blocks
INFO  [alembic.runtime.migration] Running upgrade b2e5c7d91a04 -> d3f5a7b91c24, add_queue_displays
INFO  [alembic.runtime.migration] Running upgrade d3f5a7b91c24 -> e1b7c4a9d236, add_tracking_rate_buckets
```

The file also preserves a PowerShell artefact that must not be misread as a failure: the first three
lines are `NativeCommandError` wrapper text, because `alembic` writes its `INFO` lines to **stderr** and
`2>&1 | Tee-Object` reclassifies them. The migration itself completed; the chain above is the evidence.

**Classification — CONFIRMED for `amsdp_verify_1127`:** the repository chain applied from an empty
schema to the single head `e1b7c4a9d236`, including the three additive revisions named in register §15.1.

**Reported head, separately.** History line 10804 runs `alembic current` and `alembic heads` against
`amsdp_verify_1127`, but its output went to the console only — **no file retained it**. The reported
`alembic current → e1b7c4a9d236 (head)` and `alembic heads → one head` are therefore **REPORT-ONLY**:
consistent with the migration log and with a static reading of the migration graph (single head,
unbroken `down_revision` chain), but not independently captured.

---

## 7. Database-specific evidence, and three corrections to the narrative

### 7.1 What `amsdp_dbs.txt` shows

Retained content (verbatim, 2026-11-27 11:20:38):

```
['amsdp', 'amsdp_mp16_scratch', 'amsdp_verify_1127', 'amsdp_verify_2829', 'postgres', 'template0', 'template1']
```

Three facts follow, and only these: the server at `127.0.0.1:55432` answered a database-list query in
this window (**CONFIRMED**); `amsdp_verify_1127` already existed 5 seconds before the migration ran
(**CONFIRMED**); the developer database `amsdp` exists on the same server and is a **separate** database
from the scratch one (**CONFIRMED**).

### 7.2 What it does not show

- **`amsdp_verify_1127b` is absent from the listing.** Its creation happened after 11:20:38 — consistent
  with the register, but not itself evidence of when, how, or empty it was created. No retained command
  or alembic transcript for `1127b` exists (`CREATE DATABASE`, `createdb`, `psql` and `1127b` were each
  searched in the retained history; only the two run lines in §3.1 mention it).
- **Emptiness at creation is not proven for either database.** A fresh `CREATE DATABASE` yields an empty
  schema, but no artefact here records the command or the pre-migration table count.
- **`amsdp` was not proven untouched.** The listing shows it existed; nothing here shows it was not
  written to. That is why register §15.1's categorical wording is corrected in this phase (finding
  **F-01**): three earlier dashboard invocations against `…/amsdp` remain in retained history, and their
  timing relative to this window is not established.

### 7.3 The engine under test is PostgreSQL 16.4, not 17

Register §15.1 records “PostgreSQL | **17**, listening on `127.0.0.1:55432` (verified this window)”.
That is **not supported**, and three independent local artefacts contradict it:

| Artefact (read-only, filesystem) | Content |
|---|---|
| `C:\Users\RobieS\AppData\Local\amsdp\pgdata\PG_VERSION` | `16` |
| `C:\Users\RobieS\AppData\Local\amsdp\pgsql\bin\pg_config.exe --version` | `PostgreSQL 16.4` |
| `C:\Users\RobieS\AppData\Local\amsdp\pg.log` line 1 | `2026-11-24 10:59:53.313 GMT [28424] LOG:  starting PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit` |

The same log records no restart after that single start (`starting PostgreSQL` and
`database system is ready to accept connections` each appear once in 236,789 bytes), and its last write
is 2026-11-27 12:10:51 — the tail of the second execution's window. The distribution on disk is
`pg16.zip` (338,727,828 bytes, 2026-11-24); no PostgreSQL 17 archive or build exists in that directory.

**Consequence.** The executions are valid evidence, but they are evidence on **PostgreSQL 16.4**. Any
statement that depends on PostgreSQL 17 behaviour is unsupported by this evidence. The discrepancy is
reported as **F-13** in `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md`, outside the
F-01…F-12 set because it was found during this phase rather than in the original audit.

The server's identity and version are established from **local files**, not from a database session:
**no database connection was opened while writing this record** (mandate §11).

---

## 8. Evidence limitations, stated plainly

| # | Limitation | Effect |
|---|---|---|
| L-1 | The database URL survives only in a **mutable** shell-history file | The log → database binding is strong but not hash-stable; history pruning would lose it |
| L-2 | No retained artefact records `amsdp_verify_1127b`'s creation or migration | The “second pristine database” claim is REPORT-ONLY (F-08) |
| L-3 | No captured `alembic current` / `alembic heads` output | The reported head is REPORT-ONLY, though consistent with the chain log and the graph |
| L-4 | Intermediate failing traces were overwritten by the rollout loop | Why each defect failed is reasoned from test source + transcripts, not preserved traces (F-10) |
| L-5 | The engine is PostgreSQL **16.4** | Register §15.1's “17” is wrong; see F-13 |
| L-6 | Single process, no `pytest-xdist` | Nothing here proves multi-worker behaviour; the `pqt:%` reset fixture is process-global (F-04) |
| L-7 | No CI artefact | Nothing was pushed; no workflow ran (register §15.5) |
| L-8 | No browser artefact | No VERIFIED status is supported by any of this (register §15.5) |
| L-9 | The logs live outside version control | Mitigated by the hash-verified copy set in §2, not eliminated |

---

## 9. Claim-by-claim status

| Claim | Basis in this record | Classification |
|---|---|---|
| 1,061 passed on `amsdp_verify_1127` in 541.58 s | `amsdp_full2.txt` + history line 10801 | **CONFIRMED** |
| 1,061 passed on `amsdp_verify_1127b` in 542.27 s | `amsdp_full3.txt` + history line 10818 | **CONFIRMED** |
| The suite is 1,061 tests and every collected test ran | `amsdp_collect.txt`, `amsdp_files.txt`, both summary lines | **CONFIRMED** |
| The chain migrated zero → head `e1b7c4a9d236` on `amsdp_verify_1127` | `amsdp_mig.txt` | **CONFIRMED** |
| `alembic current` reported `e1b7c4a9d236 (head)`, one head | Not captured | REPORT-ONLY |
| `amsdp_verify_1127b` was created empty and migrated zero → head | Not captured | REPORT-ONLY |
| `amsdp_verify_1127` was empty before the migration | No pre-migration count captured | PARTIALLY SUPPORTED |
| The developer database `amsdp` was never contacted or opened | Contradicted for earlier dashboard runs (F-01) | **NOT SUPPORTED as worded** |
| PostgreSQL 17 | Contradicted: 16.4 (§7.3) | **NOT SUPPORTED** |
| Five test defects existed and were fixed | `amsdp_perfile.txt` shows two failing modules pre-fix; diffs show five changes; 1,061 green post-fix | **CONFIRMED** (with L-4) |
| No product file was modified | Repository diff at this phase: three test files + two docs + `.clinerules` | **CONFIRMED** |
| Nothing committed or pushed | `HEAD = origin/hackathon-mvp = 71226e8`, 0 staged, 0 untracked | **CONFIRMED** |
| VERIFIED / ACCEPTED | No browser, CI or owner artefact exists | **NOT CLAIMED, and not supportable** |

---

## 10. Custody rules for this evidence

1. **Do not delete or overwrite** `E:\Temp\amsdp_*` or `E:\amsdp_audit_evidence_27nov2026\*`. They are
   the only primary record of the executions.
2. **Do not edit** the logs to correct the register. Corrections belong in the register, with the log
   quoted as-is.
3. **Do not regenerate** a missing artefact to “fill a gap”. A missing log is a limitation, not
   something to synthesise (mandate §3.3).
4. **Re-hash before use.** The digests in §2 are the reference values.
5. **`pg.log` and the shell history are live files.** They grow with normal use; cite them with the
   observation date and do not treat them as frozen.

---

<!-- Created 2026-11-27 under the audit-resolution mandate §3 (F-07). Additive: no existing document was
     modified by this file's creation, and no test, migration or database operation was performed. -->
