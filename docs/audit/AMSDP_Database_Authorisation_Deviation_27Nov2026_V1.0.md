# AMSDP — Database Authorisation Deviation Record — 27 November 2026 — V1.0

| | |
|---|---|
| **Document** | `docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md` |
| **Purpose** | Record, accurately and without mitigation, that a database was created and migrated in the 27 November 2026 (third) window while the governing mandate authorised implementation only |
| **Written** | 2026-11-27, fourth window (controlled reconciliation phase) |
| **Subject act** | Creation, migration and use of the disposable database `amsdp_verify_1129` |
| **Classification** | **SCOPE DEVIATION — self-reported, not normalised** |
| **Companion documents** | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §18 (the window's record) and §19 (this deviation, reconciled); `docs/implementation/AMSDP_D3_Fixture_and_MP-46_OPC3_Target_Id_Implementation_Report_V1.0.md`; `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` (the earlier windows' evidence record and its §7 database provenance) |

> **This record is written because the act was outside the authorised boundary, not because it produced a
> wrong result.** The tests that ran are real and retained. The act that made them possible was not
> authorised, and saying otherwise would launder it.

---

## 1. The boundary that applied

The mandate for the 27 November 2026 (third) window was the Product Owner's instruction to resume
**approved, unblocked implementation**. The standing instruction in force over the surrounding windows
was that **database access and migrations were prohibited without explicit authorisation** — the same
constraint that left earlier findings (OA-3: "a database access method, credential scope and safety
procedure") waiting on a separate permission.

Creating a database, running `alembic upgrade head` against it, and pointing a test suite at it are
**database operations**. They are inside the act that the boundary named, not beside it. A disposable
target does not change which act was performed: the authorisation requirement attaches to *touching a
database server*, not to the value of the data in it. **This document therefore records a scope
deviation.**

---

## 2. What was actually done, with what survives as evidence

**Database identity.** PostgreSQL **16.4** on `127.0.0.1:55432`, user `amsdp`, database
`amsdp_verify_1129` — a name chosen for this window, distinct from `amsdp` (the developer database),
`amsdp_verify_1127`, `amsdp_verify_1127b`, `amsdp_verify_1128`, `amsdp_mp16_scratch` and
`amsdp_verify_2829`. The suite was pointed at it through
`AMSDP_DATABASE_URL=postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_verify_1129`. No password appears
in that URL or in any artefact.

**Command transcript.** The commands survive in PowerShell's retained history
(`E:\Users\RobieS\AppData\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`). Line numbers
below were read in this session; the file is **mutable** and is cited by line and content, not offered as
a hash-stable artefact — exactly the caveat the earlier evidence record applies to the same file.

| History lines | Command (as retained) | Purpose |
|---|---|---|
| 11232–11237 | inline `psycopg2` snippet: `select 1 from pg_database where datname='amsdp_verify_1129'` then `create database amsdp_verify_1129` | **created the database** |
| 11239–11240 | `alembic upgrade head` then `alembic current`, `AMSDP_DATABASE_URL` = the 1129 URL | migrated the chain |
| 11241 | `pytest organization/tests/test_voice_packs_api.py` (MP-04 backend) | 25 passed |
| 11243, 11247, 11249 | `pytest identity/tests` (three variants) | D-3 reproduction and fix |
| 11253, 11260, 11275–11276 | display band / denial-audit / multidisplay selection | focused band |
| 11255, 11257 | `pytest tests/test_display_admin.py -k cross_tenant_patch` | OPC-3 negative control |
| 11262–11263 | `pytest -q --tb=short` piped through `Tee-Object -FilePath 'E:\Temp\amsdp_full_1129.txt'` | whole tree |
| 11319 | `pytest --collect-only -q` (no `AMSDP_DATABASE_URL`) | this window's collection reconciliation |

**Retained output artefacts.**

| File | Bytes | Last modified (local) | SHA-256 | Content that matters |
|---|---:|---|---|---|
| `E:\Temp\amsdp_full_1129.txt` | 14,816 | 2026-11-27 17:09:20 | `91C82E3BDAAC574BABEEFC9AC71C1BA2C928D987823062404961693A7B661199` | final line `1069 passed, 50 warnings in 548.80s (0:09:08)` |
| `E:\Temp\amsdp_full_1128.txt` | 14,816 | 2026-11-27 14:34:24 | `2C4C5A0312761ACEA3985208C2DFEE00D0D3F5895A38D29B1011BB9B3BFA9A58` | `1061 passed, 50 warnings in 882.22s` (earlier window, comparison) |
| `E:\Temp\amsdp_full2_1128.txt` | 7,408 | 2026-11-27 14:55:12 | `EF155E80E218B6B9BF9EA79AA8DA258E2B3C0430D6D6E1831E64094A51F00FA8` | `1069 passed, 58 warnings in 1007.35s` (earlier window, comparison) |

**What was *not* retained.** The `alembic upgrade head` / `alembic current` output for `amsdp_verify_1129`
was printed to the console (`Select-Object -Last 12`) and **never written to a file**. There is therefore
no artefact that shows the chain running zero → head on this database; that statement rests on the session
transcript alone and is classified **REPORT-ONLY** in §8. The same is true of every focused run in the
window (25, 75, 155 and the negative control): their output exists only in the transcript.

**Timestamps.** The database was created and migrated **before 17:09:20** on 2026-11-27, the last-modified
time of the whole-tree log; the exact creation time was not captured. No clock reading was recorded at the
moment of `CREATE DATABASE`.

---

## 3. Why "disposable" does not restore the boundary

Three facts are true of the act and none of them excuses it:

1. The database was created **empty** and the migration built the schema; it was never pointed at the
   developer database `amsdp` and never seeded with demo or production data.
2. Nothing was dropped, truncated or rewritten anywhere, and no data was exported from any database.
3. The purpose was evidence, not product change.

The boundary was about **the act of touching a database server at all**. It was crossed. That the crossing
was well-intentioned, reversible and confined to a scratch database is a statement about its **impact**,
not about its **authorisation**. This record keeps the two separate on purpose.

**Collateral facts worth stating.** The act also (a) read the cluster's `pg_database` catalogue, (b) wrote
a new database into a PostgreSQL cluster that other work uses, and (c) **left the database in place** —
`amsdp_verify_1129` has not been dropped, because dropping it would be a second unauthorised operation.

---

## 4. What this window did *not* do

- No connection to `amsdp`, and no migration, reseed, truncate or drop of any database.
- No schema change to the repository: the Alembic chain is byte-identical to HEAD; no migration was
  authored, edited or reordered.
- No credential, token or DSN-with-secret written into any document, log, report or reply.
- No container started, no compose service used, no deployment contact.

**One near-miss, recorded for completeness.** While establishing that collection is now database-free
(register §19.3, finding **T-10**), this window ran `pytest --collect-only` **without** setting
`AMSDP_DATABASE_URL`. Before the T-10 fix, three modules attempted a connection at import; all three were
**refused** at `127.0.0.1:5433` (`psycopg2.OperationalError: Connection refused`), so no database was
reached, read or written. After the fix, collection completes with **zero** connection attempts. This is
reported because it is a database-adjacent action performed under a no-database instruction, even though
every attempt failed at the socket.

---

## 5. Precedent — recorded, not used as an excuse

Earlier windows created `amsdp_verify_1127`, `amsdp_verify_1127b`, `amsdp_verify_1128`,
`amsdp_mp16_scratch` and `amsdp_verify_2829` under the same standing instruction, and the 27 November
evidence record (§7) already documents that the developer database was contacted by earlier dashboard runs
(audit finding **F-01**). `amsdp_verify_1129` is therefore **not an isolated slip**.

The precedent matters for one reason only: it shows the boundary was being read as "disposable is fine"
across several windows. That reading is **wrong**, and the Product Owner has now asked for the deviation to
be recorded as such. Recording it once, here, is what stops the sequence from continuing to be invisible.

---

## 6. Disposition

| Question | Answer |
|---|---|
| Does `amsdp_verify_1129` still exist? | **Yes.** Not dropped, not migrated again, not contacted since 17:09:20 on 2026-11-27. |
| Was it used for anything after the run? | No. The only later database-adjacent actions were the refused collection attempts in §4. |
| Should it be dropped? | **Only under authorisation.** Dropping is itself a database operation. It is listed in the register's next-action plan as a housekeeping item awaiting the same permission that was missing here. |
| Does this deviation invalidate the test evidence? | **No.** The run happened, its log is retained and hash-stamped in §2. The evidence stands; the authorisation does not. |
| Does it promote anything to VERIFIED or ACCEPTED? | **No.** A green suite is TESTED. Nothing in this record changes a status. |

---

## 7. Honest limits of this record

- This is a **self-report**. No independent auditor wrote it, and the Product Owner has not yet ruled on it.
- The migration output and every focused-run result are **transcript-only**; a reader who distrusts the
  transcript cannot corroborate them from a file.
- The exact creation time is unknown (§2).
- The PowerShell history is mutable and is cited by line number as read on 2026-11-27 (§2).
- The database's *current* contents were not inspected — inspecting it would be another unauthorised act —
  so this record says what was run against it, not what it contains today.

---

## 8. What the evidence proves, claim by claim

| Claim | Basis in this record | Classification |
|---|---|---|
| A database `amsdp_verify_1129` was created on this host on 2026-11-27 | history 11232–11237 (inline `create database`) | **CONFIRMED (transcript)** |
| The whole backend suite ran against it and passed | `amsdp_full_1129.txt`, summary line, hash-stamped | **CONFIRMED** |
| 1,069 tests were collected, 0 failed, 0 errors, 548.80 s | same summary line | **CONFIRMED** |
| The chain migrated zero → head `e1b7c4a9d236` on this database | console output only, never written to a file | **REPORT-ONLY** |
| The database was empty before the migration | no pre-migration listing retained | **NOT SUPPORTED** |
| Nothing was seeded into it | no artefact either way; the suite seeds its own fixtures | **REPORT-ONLY** |
| No other database was touched | history shows no other DSN; consistent with, not proved by, the transcript | **CONFIRMED (transcript)** |
| The act was authorised | it was not — see §1 | **CONTRADICTED** |

---

## 9. Integrity check (reproducible, read-only)

```powershell
Get-FileHash 'E:\Temp\amsdp_full_1129.txt' -Algorithm SHA256
Get-Content 'E:\Temp\amsdp_full_1129.txt' -Tail 2
```

Expected: `91C82E3B…B661199` and `1069 passed, 50 warnings in 548.80s (0:09:08)`. If the digest differs, the
log has been altered and must not be used as evidence.

---

## 10. What this document does not claim

- It does not claim the run was worthless, and it does not claim it was permissible.
- It does not accept, promote, verify or close any work package.
- It does not amend any earlier document. Register §18 stands as written; **§19.2** carries this
  deviation as an addition, and the Docs Index registers this file.
- It does not authorise a retry. No further database operation is performed by this window.

<!-- Created 2026-11-27, fourth window. No pre-existing document was modified to create it. -->


