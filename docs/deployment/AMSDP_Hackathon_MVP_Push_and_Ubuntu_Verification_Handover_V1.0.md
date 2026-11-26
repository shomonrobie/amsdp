# AMSDP — Commit, Push and Ubuntu Verification Handover V1.0

**Document:** `docs/deployment/AMSDP_Hackathon_MVP_Push_and_Ubuntu_Verification_Handover_V1.0.md`
**Version:** 1.0 · **Date:** 2026-11-26 · **Branch:** `hackathon-mvp` · **Remote:** `origin` (`https://github.com/shomonrobie/amsdp/`)
**Authority:** Product Owner authorisation of 2026-11-26 — *"AMSDP — Authorisation to Prepare Commit, Push and Ubuntu Verification"* (builds on the existing **A-4** push authorisation)

---

## 0. Document control

| | |
|---|---|
| Purpose | Record exactly what was committed and pushed, on what evidence, and hand the Product Owner a migration assessment plus a verification checklist for the Ubuntu demo environment |
| Written because | The Product Owner authorised commit + push to `hackathon-mvp` and asked for a migration assessment, pull instructions, a browser verification checklist and remaining blockers |
| Authorisation used | Commit and push of **authorised, reviewed work only** to `origin/hackathon-mvp`; no force push, no history rewriting, no branch deletion, no other branch |
| Not authorised, not done | Migration execution, reseeding, container start/stop, `.env` or credential change, network change, MP-47 implementation, work on deferred packages |
| Demo-data position | The Product Owner confirms all data in the Ubuntu environment is demo data. This document nevertheless treats that environment as one where **nothing is migrated without a stated plan and an explicit authorisation** — a backup is required before the upgrade, and the upgrade is not run from this host |
| Status discipline | `.clinerules` §7 applies exactly: IMPLEMENTED / TESTED / VERIFIED / ACCEPTED are distinct, and **nothing in this document is VERIFIED or ACCEPTED** — this host cannot reach a database, start a container or open a browser (see §5.6) |

---

## 1. What was in the working tree before the commit

`git status --porcelain` on `hackathon-mvp`, local `HEAD` = `origin/hackathon-mvp` = `fd4d365` at the start of this task:

- **18 modified** entries, **28 untracked** entries — **46** in total.
- **One** of the 18 is **owner-owned**: `.clinerules` (the Product Owner's own uncommitted edit). It was **not staged, not committed, not reverted** — the instruction was to preserve it, and it is still modified in the working tree after the push.
- The remaining **45** files were attributed to documented, already-reported work packages before anything was staged (§2).
- `git stash list` was empty: there was no hidden work to confuse the review.

No file in the tree was rewritten to make the commit tidier. `.clinerules` §9 forbids destructive Git tidy-ups, and none was needed.

---

## 2. Attribution — every staged file against a work package

Staging was **by explicit path**, never `git add -A` or `git add .`, so an unrelated file could not be swept in.

| Work package | Files |
|---|---|
| **MP-23** (BR §43 reporting, PO-11) | `backend/appointment/reports.py` (new), `backend/appointment/main.py`, `backend/tests/test_operational_reports.py` (new), `frontend/pages/reports.js` (new), `frontend/lib/operational-report.js` (new), `frontend/tests/operational-report.test.mjs` (new), `frontend/next.config.js` (`/api/v1/reports/*` proxy rule) |
| **MP-25** (GAP-20 durable tracking budget) | `backend/common/rate_limit.py` (new), `backend/common/models.py` (`TrackingRateBucket`), `backend/appointment/tracking.py`, `backend/alembic/versions/e1b7c4a9d236_add_tracking_rate_buckets.py` (new), `backend/tests/test_tracking_rate_limit.py` (new), `frontend/pages/track/[token].js` |
| **MP-39** (MD-11 display administration) | `backend/queuing/displays.py` (new), `backend/queuing/main.py`, `backend/tests/test_display_admin.py` (new), `frontend/pages/queue-displays.js` (new), `frontend/lib/displays.js` (new), `frontend/tests/display-admin.test.mjs` (new) |
| **MP-46** (denial-row ownership) | `backend/common/denial_audit.py` |
| **MP-35** (demo display boards) | `backend/seed/seed_demo.py` |
| **MP-38 / MP-41 / MP-45** (public board behaviour) | `frontend/pages/queue-display/[org]/[branch].js`, `frontend/tests/display-board.test.mjs` (new), `frontend/styles/global.css` |
| **MP-24** (queue history) | `frontend/pages/queue-history.js` (new), `frontend/lib/queue/history.js` (new), `frontend/tests/queue-history.test.mjs` (new) |
| **MP-04** (voice-pack admin, scope unchanged under PO-D1) | `frontend/pages/voice-packs.js` (new), `frontend/lib/voice-pack-admin.js` (new), `frontend/tests/voice-pack-admin.test.mjs` (new), `frontend/lib/auth.js` (client mirror reconciled with `backend/common/permissions.py`), `frontend/tests/permissions-mirror.test.mjs` (new), `frontend/components/AppShell.js` (nav entries) |
| **MP-28** (i18n) | `frontend/lib/i18n.js` (241 added lines, bn/en key pairs only) |
| **MP-02 / MP-33** (CI: the two unterminated `test()` callbacks) | `frontend/tests/queue-announcement-delivery.test.mjs`, `frontend/tests/staff-page.test.mjs` |
| **Documentation** (reports, decisions, register, index) | 9 files listed in §3.2 |

**One mixed file, stated plainly.** `frontend/lib/i18n.js` carries the keys for several packages at once; it cannot be split by package without hunk-level staging, which would have created a tree that never existed and a build nobody tested. It was committed whole, in the code commit, because every added line is a `bn`/`en` string pair for a screen committed in the same commit.

---

## 3. The commits and the push

### 3.1 Code commit — `31fcb458ddd8d8c9022d6d72e7cb3ccdac70b60c` (36 files)

```
feat: operational reports, durable tracking budget, display admin, denial marker

Implements the MP-23 / MP-25 / MP-39 / MP-46 window plus the MP-04, MP-24,
MP-28, MP-35 and MP-38 surfaces, and closes the two test callbacks that kept the
frontend suite from running (MP-02 / MP-33).
```

The body records, per package, what the code does and where its evidence is, and closes with the test and build results **including what was not run** (the 34 new backend tests collect but were not executed: no reachable PostgreSQL).

### 3.2 Documentation commit — `62b2facd670583d84712151210dc7de3fb94f647` (9 files)

```
docs: MP-23/MP-04 evidence, owner decisions, roadmap audit, MP-47 proposal
```

| File | Change |
|---|---|
| `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` | new — PO-D1 §7 among the 26 November decisions |
| `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md` | new |
| `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` | new (superseded, kept) |
| `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` | new — includes §12 Amendment A-1 |
| `docs/implementation/AMSDP_Controlled_Implementation_Execution_Report_V1.0.md` | new |
| `docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md` | new |
| `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md` | new — **PROPOSED**, not authorised for build |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | §13 added (PO-D1 applied, MP-47 row, MP-04/MP-23 positions) |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Revision 52 |

Separating code from documentation follows the established history (for example `082e2a0` code, then `1f303d1` documents it, then `fd4d365` pins the verified push point). It also means a reader can see that the commit carrying behaviour is not the commit carrying prose about it.

### 3.3 A defect in the commit process, corrected before the push

The first attempt (`de5b988`) was created from a PowerShell `Set-Content -Encoding UTF8` message file, which wrote a **UTF-8 BOM**; Git recorded it as the first character of the subject line (`git log` showed the BOM before `feat:`). The commit was **unpushed** at that point, so it was amended (`git commit --amend -F`, message file written with `UTF8Encoding($false)`) to `31fcb45`; the subject now begins with `f` (character code 102, read back and checked).

`de5b988` **never existed on the remote** and no published history was rewritten. It is recorded here because a reviewer comparing notes from an earlier turn would otherwise find a SHA that no longer resolves.

### 3.4 The push

```
git push origin hackathon-mvp
  -> fd4d365..62b2fac  hackathon-mvp -> hackathon-mvp
```

Verified after the push, by fetching rather than by trusting the push output:

| Check | Result |
|---|---|
| Local `HEAD` | `62b2facd670583d84712151210dc7de3fb94f647` |
| `origin/hackathon-mvp` | `62b2facd670583d84712151210dc7de3fb94f647` |
| `git status -sb` | `## hackathon-mvp...origin/hackathon-mvp` — **0 ahead, 0 behind** |
| Remaining working-tree entry | ` M .clinerules` (owner-owned, deliberately untouched) |

No force push, no `--force-with-lease`, no tag, no branch other than `hackathon-mvp`, no rewrite of published commits.

### 3.5 The record commits — and why §7.2 does not compare against a fixed SHA

This handover, the register's §14 and the index's Revision 53 are documentation and were committed **after** the code,
so the tip of `origin/hackathon-mvp` advanced past `62b2fac` by a docs-only commit (and by one more when this text
itself was amended for the same reason). Two facts stay stable and are the ones worth checking:

- **`31fcb45` is the last commit that changes behaviour**, and `62b2fac` carries the documentation of that window.
- Every commit after `62b2fac` in this task is **docs-only**: no source, test, schema, migration or configuration file.

An instruction that says "expect `62b2fac`" would therefore fail on Ubuntu for a reason that has nothing to do with the
code. §7.2 instead verifies **ancestry** of the code tip, which is true regardless of how many documentation commits
follow it.


---

## 4. Pre-commit review — secrets, artefacts, debug residue

### 4.1 Secret scan

All 46 changed/untracked files were scanned for `BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE KEY`, `aws_secret`, `aws_access_key`, `ghp_`, `sk-` (20+ trailing chars) and `AKIA` (16 chars):

- **2 hits, both documentation prose** describing an *earlier* credential scan (`AMSDP_Docs_Index_V1.0.md:560`, `AMSDP_Work_Package_Execution_Register_V1.0.md:540`). Neither contains a credential.
- **Zero** credentials, tokens, JWT material, private keys, API keys or database URLs in any staged file.

No `.env`, key, certificate, dump, backup or credential file exists among the 45 committed paths — checked by listing every untracked path with its size before staging.

### 4.2 Generated or temporary artefacts

- `frontend/.next` (build output) and `frontend/.audio-originals-backup` are **not** in the commit: neither appears in `git status`, so the existing ignore rules already cover them. Nothing was added to `.gitignore` to achieve that, and nothing had to be deleted.
- No `__pycache__`, `.pyc`, `.log`, `.sqlite`, `.db`, `.zip` or editor file appears among the 36 code files (§3.1 names them all).

### 4.3 Debug residue

Every changed/new `.js`, `.mjs` and `.py` file was scanned for `console.log`, `console.debug`, `debugger`, `breakpoint()`, `pdb.set_trace`, absolute local paths (`E:\`, `C:\`) and hardcoded hosts:

- `console.log` / `debugger` / `pdb` / absolute paths: **0**
- `localhost:3100`: 2 occurrences, both **pre-existing context lines**, not additions — confirmed with `git diff -U0 | Select-String '^\+.*localhost'`, which returned nothing.
- `print(`: only in `seed_demo.py`, matching that file's existing seed-progress style; **0** in `reports.py`, `rate_limit.py`, `displays.py`, `e1b7c4a9d236`. `TODO`/`FIXME`: **0** in all four.
- `dangerouslySetInnerHTML`, `eval(`, `new Function(`: **0**. The only `http://` additions are Docker service-name proxy targets in `next.config.js` (`http://appointment:8005`), the existing pattern of that file.

### 4.4 What the code review actually checked

Beyond the scans, these were read for behaviour, not only for cleanliness:

- `backend/common/denial_audit.py` — the marker header is removed from the response before it leaves the service, and a route that set it without writing a row would lose the denial record; the comment states that, and the display module only sets it after a committed write.
- `backend/appointment/tracking.py` — the durable budget is charged first; the in-process window is kept **only** on a database exception; the 429 carries `Retry-After` plus the three `X-RateLimit-*` headers and `no-store`. `SessionFactory` is imported at line 11 and every session is closed in `finally`.
- `backend/seed/seed_demo.py` — `_seed_displays` is idempotent per board id, `organization_id` comes from `DEMO_ORG` and never from the row, and `status` is set explicitly rather than defaulted.
- `frontend/lib/auth.js` — the client mirror is now a frozen copy of `PERMISSIONS` with the same prefix rule (`<ns>.*`), and `tests/permissions-mirror.test.mjs` parses the Python matrix so drift fails the suite. That is what closed the MP-04 defect in which `org_admin` was hidden from a screen the server would have served.

---

## 5. Test and build evidence

All commands below were run on this Windows host, in this tree, after the review and before staging. They are the evidence for the commit; **none of them is a substitute for the Ubuntu run** (§8).

### 5.1 Frontend suite — `cd frontend; npm test`

```
tests 526 · pass 524 · fail 0 · cancelled 0 · skipped 2 · todo 0 · duration_ms ≈ 2106
```

Identical to the count reported at Revision 51/52, which is the point: the committed work did not change the suite's shape, only added to it. The two skips are the pre-existing announcement-transport skips (`result.reason === 'not_wired'`), not failures hidden as skips.

### 5.2 Backend static and import checks — `cd backend`

| Check | Result |
|---|---|
| `python -m py_compile` on the 10 changed/new modules (`reports.py`, `main.py`, `tracking.py`, `rate_limit.py`, `models.py`, `denial_audit.py`, `displays.py`, `queuing/main.py`, `seed_demo.py`, `e1b7c4a9d236…py`) | **exit 0** |
| `python -c "import appointment.reports, common.rate_limit, queuing.displays"` | **IMPORT OK** (the only stderr line was `common.database`'s expected development-DSN warning: no `AMSDP_DATABASE_URL`) |
| `pytest --collect-only -q` on the three new test modules | **34 tests collected** (`test_operational_reports.py` + `test_display_admin.py` + `test_tracking_rate_limit.py`), in 1.68 s |

### 5.3 Backend execution — deliberately not performed

`pytest` was **not executed**: there is no reachable PostgreSQL on this host. The 34 collected tests therefore prove the modules import and are discoverable, **not** that their assertions hold. Any statement that the backend is green would be false, and none is made here or in the commit message.

### 5.4 Production build — `cd frontend; npm run build`

Build succeeded; 13 pages generated. The four routes this commit adds or changes are present in the route table:

| Route | Size | First Load JS |
|---|---:|---:|
| `/reports` | 6.8 kB | 122 kB |
| `/queue-displays` | 5.56 kB | 136 kB |
| `/queue-history` | 2.7 kB | 118 kB |
| `/voice-packs` | 7.91 kB | 123 kB |

Shared JS 112 kB. `/queue-display/[org]/[branch]` (2.21 kB) and `/track/[token]` (1.59 kB) also build. A failed build or a missing route would have stopped the commit; nothing was skipped to get a green result.

### 5.5 What the tests do **not** prove

They do not prove that a route answers over HTTP, that a permission refuses a real token, that a display resolves for a real branch, or that a report sums real appointments. Those are the Ubuntu checks in §8, and until they are run the correct labels are **TESTED** (frontend, in-process) and **BUILD VERIFIED** — not VERIFIED, not ACCEPTED.

### 5.6 Why nothing could be verified from here

| Capability | State on this host |
|---|---|
| PostgreSQL | **absent** — connection to `127.0.0.1:5433` refused (`psycopg2.OperationalError … Connection refused`) |
| Python driver | **absent** — `psycopg` is not installed in `.venv`, so even `alembic … --sql` cannot build an engine (`ModuleNotFoundError: No module named 'psycopg'`) |
| Docker / Compose | **absent** — no container runtime, so no stack, no service, no seed |
| Browser | **not available to this agent** — no live UI to drive |

Consequence: the migration revisions in §6 were reviewed as source and their chain was computed by Alembic itself (`ScriptDirectory`), but no revision was applied, rendered or inspected against a live database. **Ubuntu is the first place any migration in this commit will run.**

---

## 6. Database migration assessment (Ubuntu)

### 6.1 The two points

| | Revision |
|---|---|
| Ubuntu demo database, **as reported by the Product Owner** | `c4d8e2a91f60` (`add_voice_packs_and_platform_config`) |
| Committed code at `62b2fac` — **head** | `e1b7c4a9d236` (`add_tracking_rate_buckets`) |
| Previously reported development head | `d3f5a7b91c24` — **superseded**; it is now the middle step, not the head |

Computed from the committed tree, not from memory:

```
ScriptDirectory.from_config(alembic.ini).get_heads()   ->  ['e1b7c4a9d236']
iterate_revisions('e1b7c4a9d236', 'c4d8e2a91f60')      ->  e1b7c4a9d236 -> d3f5a7b91c24 -> b2e5c7d91a04
```

**Single head, no branch, no merge revision needed.** Three linear steps stand between the Ubuntu database and the code.

### 6.2 The three required revisions

| Order | Revision | File | Creates | Touches an existing table? |
|---:|---|---|---|---|
| 1 | `b2e5c7d91a04` | `add_schedule_blocks.py` (MP-16 / BR §15) | `schedule_blocks` + `idx_block_doctor`, `idx_block_schedule`, `idx_block_org` | **No** |
| 2 | `d3f5a7b91c24` | `add_queue_displays.py` (MP-35 / 37 / 41 / 45) | `queue_displays` + `queue_display_doctors` + `idx_display_branch`, `idx_display_org`, `idx_display_doctor_doctor` | **No** |
| 3 | `e1b7c4a9d236` | `add_tracking_rate_buckets.py` (MP-25 / GAP-20) | `tracking_rate_buckets` + `idx_rate_bucket_window` | **No** |

Every one of the three states, in its own docstring, that no existing table, column, constraint, index or row is modified — and reading the `upgrade()` bodies confirms it: there is no `add_column`, `alter_column`, `drop_*` or data-migration statement anywhere in the three files. The only DDL is `create_table` and `create_index`.

### 6.3 Schema detail

**`schedule_blocks`** — `id` PK; `organization_id`, `branch_id`, `schedule_id`, `doctor_id` (all NOT NULL, each FK to its parent table); `start_date`, `end_date` (DATE NOT NULL); `start_time`, `end_time` (`String(5)`, NULL = whole day); `reason` (NOT NULL), `status` (NOT NULL, default `active`); `created_by`/`created_at`/`cancelled_by`/`cancelled_at`/`cancel_reason`. `CHECK end_date >= start_date` (`ck_block_dates_ordered`).

**`queue_displays`** — `id` PK; `organization_id`, `branch_id` (FK); `name`, `code`; `language` (default `bn`), `scope_type` (default `branch`), nullable `department_id`/`room_id` (FK); `footer_text` (default `''`); `show_room`, `show_estimated_wait`, `show_waiting_count` (BOOLEAN NOT NULL default true); `status` (default `active`); `created_by` (FK `staff_users`), `created_at`. Constraints: `UNIQUE (branch_id, code)` (`uq_display_branch_code`), `ck_display_scope_type`, `ck_display_language`, `ck_display_status`, `ck_display_department_scope`, `ck_display_room_scope`.

**`queue_display_doctors`** — composite PK `(display_id, doctor_id)`, both FK, `created_at`; a duplicate membership is impossible by construction.

**`tracking_rate_buckets`** — `bucket` `String(120)` PK; `window_started_at` TIMESTAMPTZ NOT NULL; `hits` INTEGER NOT NULL default `0`. No patient, token, path or query string is stored — the row is a caller's budget, nothing more.

All three provide a symmetric `downgrade()` (drop indexes, then drop tables), so the change is reversible if the verification goes badly.

### 6.4 Is the existing demo data compatible?

**Yes, and the reason is structural rather than hopeful:** the three revisions add tables and never read, rewrite, move or constrain an existing row. Concretely:

| Question | Answer | Consequence for the demo |
|---|---|---|
| Are any existing rows updated or deleted? | **No** | Every patient, appointment, queue entry, voice pack and audit row survives byte-for-byte |
| Is any existing column altered or tightened? | **No** | No lock, no rewrite, no NOT NULL backfill, no default churn on a populated table |
| Do the new FKs constrain existing rows? | **No** — FKs are declared **on the new tables**, pointing outward | `schedule_blocks`/`queue_displays` rows must reference valid parents; existing parents are unaffected |
| What does an empty new table mean? | `schedule_blocks` empty = **no blocked periods** (the correct default); `queue_displays` empty = **no board configured**; `tracking_rate_buckets` empty = every caller starts with a full budget | The demo keeps working exactly as before the upgrade |
| Are the two demo boards created by the migration? | **No** | `DEMO_DISPLAYS` is seeded only by `seed_demo.py::_seed_displays`, which runs from the autostart unit / `_tools/init_demo_env.sh` — **never** from a migration |

**Permissions need no migration and no reseed.** `queue.display.manage` is not a new row or a new grant: `common/permissions.py::check` matches `<namespace>.*` by prefix (`permissions.py:207`–`:220`), so `queue.*` — already held by `super_admin` (`:51`), `org_admin` (`:70`) and `branch_admin` (`:80`) — resolves it. The Reports screen is gated on `appointment.read`, held by every role. The voice-pack screen is gated on `org.read`, held by `super_admin` (`:42`) and `org_admin` (`:54`), which matches `CONFIG_ROLES = ['super_admin', 'org_admin']` in the client (`voice-pack-admin.js:29`). **No staff row, role or seed change is required for any screen in this release.**

### 6.5 What breaks if a revision is missing

The code and the schema must arrive together. The failure modes are specific and were read from the code, not guessed:

| Missing revision | Effect on the running stack |
|---|---|
| `d3f5a7b91c24` (displays) | The display administration routes and the public board resolve against tables that do not exist → **MP-38 / MP-39 / MP-41 / MP-45 cannot be verified**; `seed_demo.py::_seed_displays` would also fail on `QueueDisplay`, so the seed must not be run before this revision |
| `b2e5c7d91a04` (blocks) | The scheduling block surface (MP-16) has no table to read or write → that route errors; nothing else in this release depends on it |
| `e1b7c4a9d236` (rate buckets) | **Degrades, does not fail**: `tracking.py::_rate_limited` catches the database exception, rolls back and falls back to the per-process window, so `/api/track/{token}` still answers. The budget is then per worker and resets on restart — the exact defect MP-25 exists to end, which is why the fallback is documented in the module |

### 6.6 Backup requirement (mandatory before the upgrade)

The migration file for `e1b7c4a9d236` states the procedure in its own docstring: **`alembic current` first, `_tools/pg_backup.sh` before any upgrade.** That script dumps the development database through the `pg_dump` **inside the postgres container** (so the dumper version matches the server) into a timestamped, compressed, plain-SQL `--clean/--if-exists` file under `./backups` by default, and is safe to run while the stack is up.

Requirements as I would put them:

1. Run `_tools/pg_backup.sh` and **record the output filename** before touching the schema.
2. Confirm the dump is non-empty and recent before proceeding.
3. Keep it until the browser checks in §8 pass; only then is it "a backup nobody needed".
4. `.env` is not printed, copied or changed by any of this. `AMSDP_DATABASE_URL` is sourced from the existing file and never echoed.

### 6.7 Risks, with the reason each one is acceptable or not

| Id | Risk | Assessment |
|---|---|---|
| **R-M1** | The Ubuntu database is **not** actually at `c4d8e2a91f60` (owner-reported), so `upgrade head` starts from somewhere else | **Real.** Mitigated by running `alembic current` first and comparing. If it reports anything other than `c4d8e2a91f60`, **stop and report** rather than improvise: a different starting point changes which revisions apply |
| **R-M2** | The three revisions decide idempotency by **inspecting the live database** (`sa.inspect(connection).has_table(...)`), so they cannot be rendered offline; this host has no `psycopg`, and the offline attempt failed | **Accepted.** The pattern is deliberate (it makes a second `upgrade head` a no-op) and the SQL is plain `CREATE TABLE`/`CREATE INDEX`. The consequence is stated plainly: **first live execution is on Ubuntu**, which is why the backup in §6.6 is not optional |
| **R-M3** | In `d3f5a7b91c24`, the constant `DISPLAY_DOCTORS = 'queue_display_doctors'` is defined at the **end** of the module, after `upgrade()` uses it | **Cosmetic, not a fault.** Python resolves module globals at call time and `upgrade()` is only called after the module has finished importing; no `NameError` is possible. Recorded so the next reader does not have to rediscover it, and so nobody "fixes" it mid-window |
| **R-M4** | New images running against an un-migrated database | Additive-only means old surfaces keep working; only the four new screens fail, and they fail loudly (missing table), not silently. Migrating **before** rebuilding is therefore the safe order |
| **R-M5** | Someone re-runs the seed to "make the boards appear" | `_seed_displays` is idempotent and never destructive, but **reseeding is not authorised** in this task. The boards can be created through the MP-39 screen, or the seed run later under a separate authorisation |
| **R-M6** | The demo holds data that a *later* model expects differently | **Not applicable to this release**: no model in the commit reads a column that these three revisions would have added to an existing table — they add none |

### 6.8 Authorisation boundary for the migration

Authorised by the 2026-11-26 instruction: **prepare this assessment**. Explicitly **not** authorised, and not done: executing `alembic upgrade`, downgrading, reseeding, recreating a container, restarting the stack, or changing `.env`. The commands in §7 are for the Product Owner to run, or to authorise separately.

---

## 7. Ubuntu — pull, rebuild, inspect

Every command below is taken from this repository's own runbook (`docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md` §4.4 and `_tools/amsdp_rebuild.sh`) rather than invented. Paths assume `/home/shomonrobie/amsdp`, the path used throughout the deployment documents.

### 7.1 Confirm the branch and the tree before pulling

```bash
cd /home/shomonrobie/amsdp
git rev-parse --abbrev-ref HEAD      # expect: hackathon-mvp
git status --porcelain               # expect: empty, or only changes you can name
git log --oneline -3
```

**If `git status` shows local modifications, stop.** The instruction is explicit: do not overwrite local Ubuntu work. Commit it or report it — do not stash it on my behalf and do not `git checkout .`.

### 7.2 Pull the authorised commit

```bash
cd /home/shomonrobie/amsdp
git fetch origin
git log --oneline HEAD..origin/hackathon-mvp     # review what is about to arrive
git merge --ff-only origin/hackathon-mvp
git rev-parse HEAD                               # note the tip (docs commits sit on top of the code)
git merge-base --is-ancestor 62b2fac HEAD && echo "OK: code tip 62b2fac present"
git log --oneline -3                             # expect the docs commits above 31fcb45 / 62b2fac
```

The `merge-base --is-ancestor` line is the check that matters: it proves the **code** commit arrived, without assuming
the tip is still `62b2fac` (see §3.5). If it prints nothing and exits non-zero, the pull did not bring the code — stop
and report.

`--ff-only` is deliberate: it cannot create a merge commit, and it refuses rather than guesses if the branch has diverged. If it refuses, **stop and report** — that is divergence, not a slow network.

### 7.3 Apply the three migrations — only after a backup

```bash
cd /home/shomonrobie/amsdp
_tools/pg_backup.sh                              # record the filename it prints

cd backend
set -a; . ../.env; set +a
python -m alembic current                        # expect: c4d8e2a91f60
python -m alembic upgrade head                   # b2e5c7d91a04 -> d3f5a7b91c24 -> e1b7c4a9d236
python -m alembic current                        # expect: e1b7c4a9d236 (head)
```

`db` publishes **5433** to the host, which is why host-side alembic reaches it. No Dockerfile and no compose service runs alembic — which is why this step exists at all.

### 7.4 Rebuild and start the changed images

`backend/common/` changed (models, denial audit, rate limiting), so **all eight backend images plus the frontend** are stale:

```bash
cd /home/shomonrobie/amsdp
_tools/amsdp_rebuild.sh --check      # read-only: what changed, what would rebuild
_tools/amsdp_rebuild.sh              # rebuild + recreate exactly the affected services
```

Never `docker compose down -v`: the database lives in the named volume `amsdp_amsdp_pg_data`, and removing it destroys every row.

### 7.5 Inspect service health

```bash
cd /home/shomonrobie/amsdp
_tools/amsdp_rebuild.sh --verify     # expect 10 x ok, exit 0
docker compose ps                    # every service Up, none restarting
```

`--verify` proves readiness, not behaviour (open item **O-X** in the runbook): a green ladder rung does not mean the new screen works. §8 is what answers that.

---

## 8. Browser and integration verification checklist

Ordered by the Product Owner's stated priorities. Each row states **what to do**, **what proves it**, and **which account** — the role matters, because several screens are gated.

Sign-in accounts are the existing demo staff. Their credentials live in `docs/demo/AMSDP_Demo_Credentials_V1.0.md` and are **deliberately not reproduced here** (`.clinerules` §3 and §12).

### 8.1 MP-04 — voice-pack administration

| # | Check | Expected | Account |
|---|---|---|---|
| V-04-1 | Sidebar shows **Voice packs** | Present | `org_admin`, `super_admin` |
| V-04-2 | Sidebar **hides** Voice packs; direct `/voice-packs` shows the refusal panel, not a crash | Hidden + refusal | `branch_admin`, `receptionist`, `doctor`, `assistant` |
| V-04-3 | Library lists the packs the tenant may see; language and status filters narrow the list | Rows render, filters work | `org_admin` |
| V-04-4 | A platform pack that has **not** been released is invisible to the tenant | Absent, no error | `org_admin` |
| V-04-5 | Organisation override: set → preview → roll back | Value saves, preview reflects it, rollback restores | `org_admin` |
| V-04-6 | Lifecycle: approve → publish → retire; release a platform pack to organisations | Status persists across a reload | `super_admin` |
| V-04-7 | A refused action shows the translated refusal message, not a raw 403 page | Locale-correct message | `org_admin` |
| V-04-8 | **No upload form exists** | Confirmed absent — PO-D1 scope, **not** a defect (MP-04 report §12 Amendment A-1) | any |

### 8.2 MP-23 — reporting screen and the real API

| # | Check | Expected | Account |
|---|---|---|---|
| V-23-1 | `/reports` opens from the nav | Renders, no console error | any role |
| V-23-2 | Choose a date range; compare figures against the queue/appointment data | Numbers agree | `org_admin` |
| V-23-3 | `GET /api/v1/reports/operational?...` through the browser origin | **200 + JSON**, not a Next 404 — this is what the new proxy rule exists for | any |
| V-23-4 | Branch scoping | `branch_admin` sees that branch only; no other branch's figures appear | `branch_admin` |
| V-23-5 | Try another `organization_id` in the query | **404**, non-disclosing — never 403, never data | any |
| V-23-6 | Empty range | Renders zeroes, not an error | any |

### 8.3 Authentication, permissions, organisation and branch isolation

| # | Check | Expected |
|---|---|---|
| V-AUTH-1 | Log in as each demo role; the menu differs per role | Each role sees only its own surfaces |
| V-AUTH-2 | Force a denied request; open the audit screen | `request.denied` row exists with actor and path |
| V-AUTH-3 | Force a display denial | `queue.display.denied` recorded **once** — no duplicate generic row (the MP-46 marker) |
| V-AUTH-4 | Cross-branch read with a valid token | 404, no data |
| V-AUTH-5 | Staff page: capability grants still apply and are labelled | Unchanged from pre-release behaviour |

### 8.4 MP-39 / MP-38 / MP-41 / MP-45 — displays

| # | Check | Expected | Account |
|---|---|---|---|
| V-39-1 | `/queue-displays` lists boards; create, edit, disable | Persists; one audit row per change | `org_admin`, `branch_admin` |
| V-39-2 | `receptionist` / `doctor` try the screen and the API | Screen hidden, API refused and audited | `receptionist` |
| V-39-3 | Public board `?display=<code>` | Configured language, footer and field set | public, no login |
| V-39-4 | A **different** organisation's display code | Not found — no cross-tenant disclosure | public |
| V-39-5 | Two boards in one branch | Visibly different, as configured | public |
| V-39-6 | Create a board through the UI **without reseeding** | It appears on the public route | `org_admin` |

### 8.5 MP-47 — infrastructure readiness only

| # | Check | Expected |
|---|---|---|
| V-47-1 | MP-47 is still **PROPOSED** — no upload UI, no new endpoint | Confirm absence |
| V-47-2 | Existing `POST /api/v1/voice-packs` JSON contract answers | 2xx with a valid admin token — the contract Option A will reuse |
| V-47-3 | A request body at the documented size ceiling | Measured, so U-D2 can be answered with a number instead of an opinion |

MP-47 implementation remains **not authorised**. V-47-2 and V-47-3 exist to answer U-D2 cheaply, not to start the build.

### 8.6 Backend tests, on a non-production database

The 34 collected backend tests need a database that is **not** the demo one. Read from the support module, not assumed: every helper writes through `common.database.SessionFactory` — *the same engine the services use* — and `purge_org()` deletes the business rows of the **named** organization only ("Nothing outside `org_id` is touched", `amsdp_test_support.py:309`–`:323`). Each module confines itself to its own identifiers (`mp23-org`, `mp23-other-org`, `dispadmin-org`, a distinct bucket prefix), so the demo organization's rows would survive.

That is not a licence to run it there. The suite **creates** reference organizations, branches, doctors and staff users idempotently and would leave them behind, and the reports tests create appointments and queue entries. On the demo database that is pollution, not damage — and pollution is still unwanted in the volume used for the demonstration.

```bash
cd /home/shomonrobie/amsdp/backend
# point AMSDP_DATABASE_URL at a SCRATCH database, not the demo one
python -m pytest tests/test_operational_reports.py tests/test_display_admin.py \
                 tests/test_tracking_rate_limit.py -v
```

Expected: 34 tests, and their real outcome recorded — pass **or** fail. If no scratch database can be provisioned, record that the backend tests remain **NOT EXECUTED**; that is an honest outcome, whereas running them against the demo volume and reporting green would not be.

---

## 9. Status summary — what is now true

| Item | State | Basis |
|---|---|---|
| Code committed | **DONE** | `31fcb45` (36 files) and `62b2fac` (9 files) |
| Pushed to `hackathon-mvp` | **DONE** | `fd4d365..62b2fac` (code + its documentation), then docs-only record commits; `HEAD` = `origin/hackathon-mvp`, 0 ahead / 0 behind after a fetch (§3.4, §3.5) |
| Secret and artefact review | **DONE** | §4 — 2 documentation false positives, no credential, no generated file |
| Frontend tests | **TESTED** | 526 tests / 524 pass / 0 fail / 2 skipped, in this tree |
| Frontend build | **VERIFIED** (build) | `next build` succeeded; four new routes in the table |
| Backend modules | **IMPLEMENTED** | `py_compile` exit 0, imports OK, 34 tests collected |
| Backend tests | **NOT EXECUTED** | no reachable PostgreSQL on this host |
| Migration chain | **REVIEWED**, not applied | single head `e1b7c4a9d236`; three additive revisions from `c4d8e2a91f60` |
| MP-04 / MP-23 / MP-38 / MP-39 in a browser | **NOT VERIFIED** | requires §7 under authorisation, then §8 |
| MP-47 | **PROPOSED** | nine open decisions, no specification, no authorisation to build |
| Anything ACCEPTED | **Nothing** | acceptance is the Product Owner's act, not an agent's |

---

## 10. What this document deliberately does not claim

1. **It does not claim the migration works.** It was never executed. The assessment says what the SQL does, why it is additive, and what to check first — not that it succeeded.
2. **It does not claim the backend is green.** 34 tests were collected, not run; no statement in this document contradicts that.
3. **It does not claim any screen works in a browser.** Only the Ubuntu checklist can establish that, and it has not been run.
4. **It does not claim MP-04 or MP-23 are complete.** Both remain unimplemented-from-the-browser's-point-of-view and unaccepted; PO-D1 changed MP-04's *scope* record, not its status.
5. **It does not claim MP-47 has begun.** It is a proposal awaiting nine decisions, a specification and an authorisation.
6. **It does not claim the Ubuntu environment is compatible.** It states what must be true and how to confirm it; the confirmation is yours to run.
7. **It does not record a second, independent artefact for the commit itself** — the push verification in §3.4 compares local `HEAD` with a freshly fetched `origin/hackathon-mvp`, which is the strongest confirmation available to an agent without a browser.

---

## 11. Remaining blockers and open Product Owner decisions

### 11.1 Blockers that survive this task

| Id | Blocker | Effect |
|---|---|---|
| **B-1** | No PostgreSQL, no `psycopg`, no Docker and no browser on the Windows authoring host | Nothing can be executed, migrated or observed here. Every VERIFIED claim must come from Ubuntu |
| **B-2** | The Ubuntu database is at `c4d8e2a91f60` while the code is at `e1b7c4a9d236` | The four new screens cannot be exercised until §7.3 is run under authorisation. Until then MP-04 / MP-23 / MP-38 / MP-39 stay **browser-unverified** |
| **B-3** | The migration has never executed anywhere | First live run is Ubuntu (R-M2). The downgrade exists, but it has not been exercised either |
| **B-4** | MP-47 has nine unanswered decisions (U-D1…U-D9) and no written specification | No MP-47 code may be written; the package stays **PROPOSED** |
| **B-5** | Backend tests have never been executed | The backend half of MP-23 and MP-25 remains **NOT EXECUTED**, and saying otherwise would be a false claim |

### 11.2 Decisions the Product Owner now owns

1. **Authorise the migration window** (§7.3) — with the backup filename recorded before and after.
2. **Authorise the rebuild** (§7.4). It is a rebuild-and-recreate, not a `down`: volumes and data are not touched.
3. **Confirm the verification order.** The checklist is ordered by your stated priorities; if you would rather verify displays before reports, say so and I will re-order the record, not the code.
4. **Decide whether to run the demo seed** to create the two demo boards. Not authorised in this task; the MP-39 screen can create them instead (V-39-6).
5. **Answer U-D1…U-D9** for MP-47 when you want the package specified — starting with U-D2 (transport at the documented ceilings), because V-47-3 can answer it with a measurement on Ubuntu.

### 11.3 What this task deliberately did **not** do

- No `alembic` command was executed against any database.
- No container was built, started, stopped or removed; no volume was touched.
- No seed was run; no demo row was created, updated or deleted.
- No `.env`, credential, secret or network setting was read, printed or changed.
- `.clinerules` was not staged, committed or modified.
- No deferred work package was touched, and MP-47 was not begun.
- Nothing was force-pushed, no history was rewritten, no branch other than `hackathon-mvp` was touched.

---

## 12. Governance and skill compliance (`.clinerules` §6)

| Requirement | How it was met |
|---|---|
| §2 task routing | Domains identified: **backend API**, **multi-tenant data**, **database/migrations**, **frontend UI**, **deployment**, **documentation**. Documents loaded from `docs/governance/AMSDP_Docs_Index_V1.0.md` (`deployment/` runbook, the migration files themselves, `common/permissions.py`, the register, the MP-23/MP-04 report) |
| §3 non-negotiables | No secret logged or quoted; no access decision weakened (the client mirror was *tightened to the server*, not loosened); no tenant column invented; audit trail untouched and append-only; the schema change is a forward-only, idempotent migration; no unverified capability claimed (§5.3, §5.5, §10) |
| §4 routing table | "Database schema, migrations" → read the three revision files, checked idempotency and downgrade; "Docker, deployment" → read the runbook rather than inventing commands; "Documentation" → §11/§12 placement and index update |
| §5 skills | **No skill package is installed** in this workspace (verified earlier: no `.clinerules/skills/`, no repo `skills/`). Governance documents were used instead, and no skill was claimed |
| §7 evidence standard | Every state is labelled: frontend **TESTED**, build **VERIFIED**, backend **IMPLEMENTED / NOT EXECUTED**, screens **not browser-verified**, nothing **ACCEPTED** |
| §9 execution boundaries | The one terminal action taken beyond Git was read-only verification (`py_compile`, `pytest --collect-only`, `npm test`, `npm run build`, `alembic` head computation). No server was started, no test suite was run against a database, no destructive Git command was issued |
| §11 documentation location | This report is under `docs/deployment/`; one new document, no document moved, renamed or deleted, so no migration-manifest entry is due. The docs index is updated in the same task (Revision 53); no existing document was overwritten |
| §12 documentation reading | The index was read first; documents are cited by the path opened in this session, not from memory |

<!-- End of AMSDP_Hackathon_MVP_Push_and_Ubuntu_Verification_Handover_V1.0.md -->







