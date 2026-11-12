# AMSDP — Pre-Commit Remediation Report V1.0

**Document:** `docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md`
**Date:** 2026-11-11
**Branch / HEAD:** `hackathon-mvp` / `eb87cac`
**Predecessor:** `docs/audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` (findings B-1…B-7)
**Scope:** clear or explicitly disposition blockers B-1…B-7 before any commit
**Status:** **READY TO STAGE** — every blocker is remediated or reduced to a
recorded owner decision. **Nothing was staged, committed or pushed.**

---

## 1. What was done, in one table

| Blocker | Original finding | Action taken | State |
|---|---|---|---|
| **B-1** | `docker-compose.yml` line 41 introduced a literal `POSTGRES_PASSWORD`; line 18 held a literal DSN | Both converted to env references: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?…}`, `AMSDP_DATABASE_URL: ${AMSDP_DATABASE_URL:-…${POSTGRES_PASSWORD:?…}…}` | **REMEDIATED** |
| **B-2** | 10 literal credential-bearing DSNs in `docker-compose.demo.yml` (incl. 2 in header comments) | All 10 converted to `${AMSDP_DATABASE_URL_DEMO:-…}` / `AMSDP_DATABASE_URL` composed from `POSTGRES_PASSWORD` | **REMEDIATED** |
| **B-3** | Literal DSNs in `_tools/init_demo_env.sh` (2) and `_tools/pg_restore_test.sh` (1); `pg_backup.sh` clean | All three scripts now source `.env`, fail fast with `:?`, build the DSN/`PGPASSWORD` internally and never echo them | **REMEDIATED** |
| **B-4** | Not-ignored runtime artefacts: `backend/nohup.out`, `runs/*.json`, `var/**`, `tree.py`, `verify_llm_routing.py` | Narrow `.gitignore` rules added (`nohup.out`, `/runs/`, `/var/`, `/backups/`, `/tree.py`, `/verify_llm_routing.py`) with the already-tracked files called out | **REMEDIATED** |
| **B-5** | Six literal demo passwords in `backend/seed/seed_demo.py` | Passwords moved to `AMSDP_DEMO_PASSWORD_<USERNAME>` / shared `AMSDP_DEMO_PASSWORD`; script exits with an instruction if absent | **REMEDIATED** |
| **B-6** | `patients.js` / `global.css` inseparable from the owner rewrite at hunk level | Re-measured; **inseparability confirmed** (numbers in §7). No safe split exists — owner decision recorded | **OWNER DECISION** |
| **B-7** | 12 binary assets under `docs/images/`, one with a broken extension, spaces in paths | Malformed `doctor-group-2jpeg` renamed to `doctor-group-6.jpeg` (content byte-identical, md5 preserved); all 12 assets kept; spaced paths kept deliberately | **REMEDIATED** |
| **B-8** *(new)* | `backend/common/database.py` and `backend/alembic.ini` (both **untracked**, absent from HEAD) carried the same literal dev DSN | `database.py` composes its fallback from `POSTGRES_PASSWORD`; `alembic.ini` stores no URL at all; `alembic/env.py` resolves it and fails loudly | **REMEDIATED** |
| **B-9** *(new)* | A literal DSN in `docker-compose.yml` was already present in `origin/main` history | Not scrubbable by this task — **credential rotation is the only real remedy** | **OWNER DECISION** |
| **B-10** *(new)* | No documented contract for the credentials now read from the environment | `.env.example` created (keys + meaning, placeholder values only); a matching gitignored `.env` was produced locally so the running stack is unaffected | **REMEDIATED** |

---

## 2. Method and evidence discipline

Removing credentials from a tree is only safe if the credentials never appear in
the transcript, a command line, a log or the report. Three mechanisms enforced
that:

1. **Masked reads.** `/tmp/mask.py` piped every file through a redactor before it
   was displayed, so every inspection printed `<REDACTED>` in place of a value.
   No credential value appears anywhere in this report.
2. **Shape-based rewriting.** `/tmp/rewrite_creds.py` replaced credentials by
   *character-class pattern* (`scheme://user:<secret>@`, `KEY=<secret>`), never by
   literal search-and-replace, so the rewriting tool never needed to know a value.
3. **Behaviour-preservation proof.** The resolved Compose configuration was
   hashed **before** any edit and again **after**, for both stacks. Identical
   hashes prove the remediation changed no service, no port, no volume, no
   environment value — only *where the secret comes from*.

Resolved-configuration SHA-256 (Compose 2.40.3, run from the repository root):

| Stack | Command | Before edits | After edits | Match |
|---|---|---|---|---|
| dev | `docker compose -p amsdp -f docker-compose.yml config` | `8f98e7c08a0856f8f3b466ec0d54555f61dea6d1e37300a61eb9d08ad6a001c8` | `8f98e7c08a0856f8f3b466ec0d54555f61dea6d1e37300a61eb9d08ad6a001c8` | **yes** |
| demo | `docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml config` | `8f2bce61628806b5fe9be2366666fe2d788059c25589fc08835dfa6622e45dcc` | `8f2bce61628806b5fe9be2366666fe2d788059c25589fc08835dfa6622e45dcc` | **yes** |

Both hashes were re-verified after the last edit, so the table reflects the final
tree, not an intermediate state.

---

## 3. The credential pattern now used everywhere

One pattern, applied consistently, replaces six different ad-hoc literals:

```yaml
# source of truth = the environment (or the gitignored .env), never the file
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?missing - set it in .env, see .env.example}
AMSDP_DATABASE_URL: ${AMSDP_DATABASE_URL:-postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD:?missing - set it in .env, see .env.example}@db:5432/amsdp}
```

Three properties make this better than a defaulted value:

- **Nested interpolation** was verified against the installed Compose (2.40.3)
  with a probe variable, not assumed: the inner `:?` is honoured inside the outer
  default.
- **It fails loudly and early.** With no value present the command exits 1 with
  `required variable POSTGRES_PASSWORD is missing a value: missing - set it in
  .env, see .env.example` — a message that names the file to create. A defaulted
  secret (`${POSTGRES_PASSWORD:-…}`) would have *silently* produced a different
  password and surfaced as an authentication error far from the cause.
- **The failure is one message, not six.** The same text is used in the Compose
  files and, in shell form, in all three `_tools/` scripts.

Shell scripts follow the same contract:

```bash
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required - set it in .env (see .env.example)}"
DEMO_DSN="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo"   # built, never echoed
```

`PGPASSWORD` is passed to `docker exec` as `-e PGPASSWORD=<value>` taken from a
variable, so it never appears in an echo, a log line or the script text.

---

## 4. Per-file detail

### 4.1 `docker-compose.yml` (B-1)

| Line | Before | After |
|---|---|---|
| 18 | literal DSN | `${AMSDP_DATABASE_URL:-postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD:?…}@db:5432/amsdp}` |
| 41 | literal password | `${POSTGRES_PASSWORD:?missing - set it in .env, see .env.example}` |

`AMSDP_JWT_SECRET` was already an env reference and was left untouched — it is
still `${AMSDP_JWT_SECRET:-dev-synthetic-key-replace-in-prod}`, a non-secret
development default that `common/auth.py` already refuses in production.

### 4.2 `docker-compose.demo.yml` (B-2)

All **10** credential-bearing DSNs are now environment-driven: 8 service-level
`AMSDP_DATABASE_URL` entries use
`${AMSDP_DATABASE_URL_DEMO:-postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD:?…}@db:5432/amsdp_demo}`,
and the two **header-comment** example commands (lines 14–15) now show the
env-driven form instead of a working credential. A comment that documents a secret
is still a leaked secret — that is why they were converted too.

### 4.3 `_tools/` scripts (B-3)

| Script | Change |
|---|---|
| `init_demo_env.sh` | Sources `.env`; `:?`-guards `POSTGRES_PASSWORD` and the receptionist password; composes `DEMO_DSN` internally; exports `AMSDP_DATABASE_URL` for the `alembic` and seed steps; login-probe payload built into `LOGIN_JSON` |
| `pg_restore_test.sh` | Sources `.env` from the resolved repo root; `DB_PASSWORD="${AMSDP_DB_PASSWORD:-${POSTGRES_PASSWORD:?…}}"`; passes `PGPASSWORD` via `docker exec -e`; composes `RESTORE_DSN` internally |
| `pg_backup.sh` | Same contract; the relative output directory still resolves because the working directory is deliberately left untouched |

### 4.4 `backend/seed/seed_demo.py` (B-5)

The six `"password"` fields are gone. A new `_demo_password(username)` helper
resolves `AMSDP_DEMO_PASSWORD_<USERNAME>`, falls back to the shared
`AMSDP_DEMO_PASSWORD`, and otherwise calls `sys.exit` with an actionable message.
The bcrypt line calls the helper, and the closing console output now prints role +
username only, ending with the line "passwords come from .env" instead of a
credentials block.

### 4.5 `backend/common/database.py`, `backend/alembic.ini`, `backend/alembic/env.py` (B-8)

These were **not** in the original B-1…B-7 list, but both files are *untracked and
absent from HEAD* — so committing them would have introduced a plaintext password
into history, which is exactly the B-1 defect.

- `database.py` — `DATABASE_URL = os.environ.get("AMSDP_DATABASE_URL") or _default_url()`,
  where `_default_url()` composes `postgresql+psycopg2://amsdp:<POSTGRES_PASSWORD>@127.0.0.1:5433/amsdp`
  (host/port/db overridable via `AMSDP_DB_HOST`/`AMSDP_DB_PORT`/`AMSDP_DB_NAME`).
  With no password available it logs one warning and yields a **passwordless** DSN,
  so PostgreSQL rejects the connection explicitly instead of the application
  silently using a committed credential.
- `alembic.ini` — `sqlalchemy.url` is gone; the section explains that the URL comes
  from the environment. Nothing in the file is a credential.
- `alembic/env.py` — a single `_database_url()` helper is used by **both** offline and
  online modes (previously offline mode read the ini only) and raises
  `RuntimeError: AMSDP_DATABASE_URL is not set and alembic.ini defines no
  sqlalchemy.url. Set AMSDP_DATABASE_URL (see .env.example) before running alembic.`

### 4.6 `.env.example` (new file, B-10)

Documents `POSTGRES_PASSWORD` (required), the optional `AMSDP_DATABASE_URL` /
`AMSDP_DATABASE_URL_DEMO` overrides, `AMSDP_DEMO_PASSWORD_<USERNAME>` ×6 plus the
shared `AMSDP_DEMO_PASSWORD`, `AMSDP_DB_PASSWORD` and `AMSDP_JWT_SECRET`. Every
value is a placeholder (`replace-me`, `<choose-a-strong-password>`). It records the
two operational constraints discovered here: passwords only take effect when the
postgres volume is first created, and demo passwords must avoid `"` and `\`
because `init_demo_env.sh` interpolates one into a JSON body.
`.env` itself is matched by `.gitignore:19` and was verified with
`git check-ignore -v .env`.

---

## 5. Credential scan result

`/tmp/check_creds.py` reports literal credentials by shape (DSN userinfo,
`*_PASSWORD`/`*_SECRET`/`*_TOKEN` assignments, bcrypt hashes), ignoring
`${…}`/`$VAR`/`os.environ`/`os.getenv` indirections, Compose `:?` message
fragments and documentation placeholders. Final run:

| File | Verdict |
|---|---|
| `docker-compose.yml` | clean |
| `docker-compose.demo.yml` | clean |
| `_tools/init_demo_env.sh` | clean |
| `_tools/pg_restore_test.sh` | clean |
| `_tools/pg_backup.sh` | clean |
| `backend/seed/seed_demo.py` | clean |
| `backend/common/database.py` | clean |
| `backend/alembic.ini` | clean (only alembic's stock `user:pass@localhost` doc placeholder remains) |
| `backend/alembic/env.py` | clean |
| `.env.example` | clean (placeholders only) |

**0 literal credentials** across all ten files. The scanner itself prints counts and
file/line positions only — never a matched value.

---

## 6. Verification performed (real results, this tree)

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Compose resolves identically, dev stack | `docker compose -p amsdp -f docker-compose.yml config \| sha256sum` | `8f98e7c0…a001c8` — **identical to the pre-edit baseline** |
| 2 | Compose resolves identically, demo stack | `docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml config \| sha256sum` | `8f2bce61…e45dcc` — **identical to the pre-edit baseline** |
| 3 | Missing secret fails loudly | `docker compose --env-file /dev/null … config` | exit **1**, `required variable POSTGRES_PASSWORD is missing a value: missing - set it in .env, see .env.example` |
| 4 | Shell syntax | `bash -n` on all three `_tools/` scripts | **OK / OK / OK** |
| 5 | Python syntax | `py_compile` on `seed_demo.py`, `database.py`, `alembic/env.py` | **OK / OK / OK** |
| 6 | Backend suite | `cd backend && set -a && . ../.env && set +a && python3 -m pytest -q` | **289 passed**, 126 warnings, 120.10 s |
| 7 | Frontend suite (Bangla Name Sense) | `cd frontend && npm test` (`node --test tests/*.test.mjs`) | **43 tests, 43 pass, 0 fail**, 958 ms |
| 8 | Alembic refuses without a URL | `cd backend && env -u AMSDP_DATABASE_URL -u POSTGRES_PASSWORD python3 -m alembic current` | **exit 1** with the RuntimeError text quoted in §4.5 |
| 9 | Alembic works with a URL | same command with `AMSDP_DATABASE_URL` from `.env` | `e6c1a9b3d5f8 (head)` — real database read |
| 10 | DSN resolver, with env | import `common.database`, compare against `POSTGRES_PASSWORD` | password embedded **True**, scheme/user **True**, host part `127.0.0.1:5433/amsdp` |
| 11 | DSN resolver, without env | `env -u …` import | one warning logged, URL `postgresql+psycopg2://amsdp@127.0.0.1:5433/amsdp` (passwordless) |
| 12 | Seed password helper (3 paths) | import `seed_demo`, exercise `_demo_password` | no env → `SystemExit` "no demo password configured…"; per-user env → value matches; shared env → fallback used |
| 13 | Literal-credential scan | `/tmp/check_creds.py` over 10 files | **0 hits** |
| 14 | Image rename integrity | `md5sum` before/after | `d0828413387bca18050c438a027c3838` both sides |

Checks 1–2 are the important ones: they prove the *runtime* is unchanged, so the
credential refactor is not an untested assumption. Checks 6–7 prove the two
completed features still pass with the new configuration path (the backend suite
ran with the DSN supplied exactly the way `.env.example` now documents).

### 6.1 A defect introduced during this task, found and fixed

The first rewrite of `_tools/init_demo_env.sh` left the login probe as
`-d '{"username":"receptionist","password":"${DEMO_LOGIN_PASSWORD}"}'`. In **single**
quotes bash does not expand the variable, so the request would have sent the literal
string `${DEMO_LOGIN_PASSWORD}` and the final "Identity login OK" check would always
fail. Replaced with a `LOGIN_JSON` variable built in double quotes, with a comment
explaining why. Disclosed here rather than silently corrected: a verification step
that can only fail is worse than no verification step.

---

## 7. B-6 — `patients.js` and `global.css` are still not separable

Re-measured on the current tree:

| File | Hunks | Diffstat | Structure |
|---|---|---|---|
| `frontend/pages/patients.js` | **2** | 49 insertions, 62 deletions | The three BNS edits (the `BanglaNameSense` import, the `sg:'Name suggestions'` i18n entry, the component replacing the plain name input) sit inside hunks that also carry the owner's page rewrite |
| `frontend/styles/global.css` | **1** | 135 insertions, 16 deletions | A single contiguous hunk; the BNS styles cannot be lifted out without splitting that block |
| `frontend/package.json` | 1 | 3 / 1 | Fully the BNS change (`test` + `validate:dataset` scripts) |
| `README.md` | 6 | 144 / 4 | Only one hunk is the BNS documentation |

The audit's conclusion stands: there is no hunk-level split that does not also
commit owner work. **Two options, both requiring the owner:**

1. **Accept the mixed commit** — the BNS change and the page rewrite land in
   Commit 1 with the attribution disclosed in the message (the audit's §10 plan).
2. **Owner commits first** — the owner commits `patients.js` and `global.css`
   themselves, after which the three BNS edits can be re-applied as a clean,
   isolated diff.

This task did **not** attempt a partial staging of those files: partial staging
across interleaved hunks risks committing a non-building intermediate state, which
is a worse outcome than an honest attribution note.

---

## 8. B-4 and B-7 — artefacts and assets, decided explicitly

### 8.1 Ignore rules added (B-4)

| Rule | Rationale |
|---|---|
| `nohup.out` | `nohup … &` output, including `backend/nohup.out` (0 bytes) |
| `/runs/` | Root-level AI-Factory run records; the AI Factory's own `ai_factory/runs/` handling is untouched |
| `/var/` | Root-level task/workspace stores |
| `/backups/` | Default output directory of `_tools/pg_backup.sh` — dumps must never be committed |
| `/tree.py`, `/verify_llm_routing.py` | One-off investigation scripts, not product code |

All four directory rules are **root-scoped** on purpose so no AI-Factory
equivalent path changes behaviour. Verified with `git check-ignore -v`:
`runs/X.json` → `/runs/`, `backups/x.sql.gz` → `/backups/`, `nohup.out` →
`nohup.out`, `backend/nohup.out` → `nohup.out`.

**Disclosed caveat.** Two files inside those directories are **already tracked in
history** and are therefore unaffected by the new rules (ignore rules never untrack):

- `runs/RUN-20261105T130533-001.json`
- `var/tasks/AMSDP-000001.json`

The `.gitignore` comment names them so the rules are not mistaken for a cleanup.
Untracking them is a separate, reversible decision (`git rm --cached`) and was
**not** performed — see §10, decision D-3.

### 8.2 Image assets (B-7)

Twelve untracked binaries under `docs/images/`:

| Directory | Files |
|---|---|
| `docs/images/NoteTaker/` | 5 PNG screenshots (`Screenshot From 2026-11-11 11-35-24.png` … `-56.png`) |
| `docs/images/doctors images/` | `doctor-group-1…6.jpeg` |
| `docs/images/example dashboards/` | `booking_dashboard_1.webp` |

- **The extension typo is fixed.** `doctor-group-2jpeg` was *not* a duplicate of
  `doctor-group-2.jpeg` (different size, different md5), so it could not simply be
  dropped as a stray copy. It was renamed to **`doctor-group-6.jpeg`**, continuing
  the existing 1…5 sequence. The content is byte-identical — md5
  `d0828413387bca18050c438a027c3838` before and after. Reversible with one `mv`.
  Nothing in the codebase referenced the old name; the only occurrence is the
  predecessor audit report, which is a historical record and correctly describes
  what existed at the time.
- **All 12 assets are kept** (≈852 KB total, owner-supplied visual material).
- **Spaces in `doctors images/`, `example dashboards/` and the NoteTaker filenames
  are kept deliberately.** No code or config references these paths, so renaming
  would add churn and quoting risk for no functional gain. If the owner later wants
  a canonical kebab-case layout, that is a separate mechanical change.
- No `.gitattributes`/LFS was added: at under 1 MB, binary diffs are not a problem
  yet. The threshold to revisit is when the asset set outgrows the repository's
  comfortable clone size.

---

## 9. Working-tree state after this task

Measured at the end of the task:

| Metric | Value |
|---|---|
| Branch / HEAD | `hackathon-mvp` / `eb87cac` |
| Modified tracked files | **58** |
| Untracked entries (`-uall`) | **141** — includes `.env.example`, this report and the index; `.env` is ignored and is therefore not counted |
| Deleted tracked files | **2** (the recorded docs relocation, unchanged) |
| **Staged files** | **0 — nothing was staged, committed or pushed** |

Files this task changed or created:

| File | Change |
|---|---|
| `docker-compose.yml` | modified (2 credential lines) |
| `docker-compose.demo.yml` | modified (10 credential DSNs) |
| `.gitignore` | modified (artefact rules + caveat comment) |
| `.env.example` | **new** |
| `_tools/init_demo_env.sh` | modified |
| `_tools/pg_restore_test.sh` | modified |
| `_tools/pg_backup.sh` | modified |
| `backend/seed/seed_demo.py` | modified |
| `backend/common/database.py` | modified |
| `backend/alembic.ini` | modified |
| `backend/alembic/env.py` | modified |
| `docs/images/doctors images/doctor-group-6.jpeg` | renamed from `doctor-group-2jpeg` |
| `.env` | **new, local only, mode 0600, gitignored — never to be committed** |
| `docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md` | **new** (this report) |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | modified (registers this report) |

---

## 10. Residual risks and decisions that need the owner

| ID | Decision needed | Why it cannot be decided here |
|---|---|---|
| **D-1** | **Rotate the development and demo database passwords.** A literal DSN was already in `origin/main` before this task (`docker-compose.yml` line 18 in `HEAD`). Removing it from the working tree does not remove it from history or from any clone. | Rotation is an operational act on a live database and any deployment that still holds the old value. History rewriting (`git filter-repo`) is destructive and outside the scope of a pre-commit cleanup. **Recommendation: rotate, then treat the old value as burned.** |
| **D-2** | **B-6 attribution:** accept the mixed commit, or commit `patients.js`/`global.css` first and re-apply the BNS edits. | It changes who authored what in history — an authorship decision, not a technical one. |
| **D-3** | **Untrack two files** (`runs/RUN-20261105T130533-001.json`, `var/tasks/AMSDP-000001.json`) that live in directories now ignored. | It changes tracked content; §9 of the project rules forbids tidying the tree without authorisation. `git rm --cached` is reversible. |
| **D-4** | **The `dev-synthetic-key-replace-in-prod` JWT default** stays as a non-secret development default. Anything reachable from outside the laptop must set `AMSDP_JWT_SECRET` and `AMSDP_ENV=production`. | `common/auth.py` already refuses the default in production; changing it would break local startup for no security gain. |
| **D-5** | **`.env` is now required** for anything that touches the database. Anyone cloning must `cp .env.example .env` and fill it in before `docker compose up` or `pytest`. | Deliberate trade: the alternative was a silently wrong password. The failure message names the file to create. |
| **D-6** | **Distribute the demo credentials** through a channel that is not this repository (the values now live only in `.env`). | Out of scope here; `docs/demo/AMSDP_Demo_Credentials_V1.0.md` remains a read-only owner document and was not modified. |

### 10.1 What is *not* a risk

- No service, port, volume, image or healthcheck changed — proven by the identical
  resolved-config hashes.
- `AMSDP_JWT_SECRET` handling is unchanged; it was already an env reference.
- The test suites pass, so the credential indirection did not break the code paths
  that read the DSN.
- No document was deleted, moved or overwritten. The one rename is an untracked,
  code-unreferenced image asset with its content preserved.
- No credential value was written into this report, a log, a command line or a
  commit message.

---

## 11. Verdict

**READY TO STAGE.**

- **B-1, B-2, B-3, B-4, B-5, B-7** — remediated and verified in this tree.
- **B-6** — technically impossible to separate; reduced to a decision (**D-2**)
  that does not block staging, only the commit message.
- **B-8** (new) — remediated; it would otherwise have shipped a new plaintext secret.
- **B-9** (new) — historic exposure; needs rotation (**D-1**), which no code change
  can substitute for.

The tree can be staged and committed with the predecessor audit's four-commit plan.
Two items should be settled first because they are cheap now and expensive later:
**D-1** (rotate) and **D-2** (attribution choice). Nothing in this task was staged,
committed or pushed, and nothing outside the file list in §9 was touched.

---

## 12. Governance and Skill Compliance

Per `.clinerules` §2 and §6.

| Item | Detail |
|---|---|
| **Domains routed** | Docker/deployment + infrastructure; secrets and configuration; database/migrations; documentation output |
| **Governance documents applied** | `.clinerules` §3 (never log/expose secrets), §9 (execution boundaries, no destructive Git, check a file before staging), §11 (docs output location, filename convention, never overwrite), §12 (read the index first, cite what was opened); `docs/audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` (source of B-1…B-7); `docs/governance/AMSDP_Docs_Index_V1.0.md` (`audit/` table + verification recipe). `docs/product/AMSDP_Business_Rules_V1.0.md` was not needed: a credential-plumbing change touches no business rule, and no owner document was modified. |
| **Skills selected** | **None — none are installed.** Re-verified in this session: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/` directory, no Cline skill configuration. Per `.clinerules` §5 the governance documents above were used instead, and this report says so rather than implying a skill was used. |
| **Non-negotiables honoured** | No secret logged, echoed or quoted (§3). Audit trail untouched. No schema change, so no migration was due — Alembic head is unchanged at `e6c1a9b3d5f8`. No capability claimed that was not run: §6 checks 1–14 are IMPLEMENTED+TESTED; checks 1–2, 9 and 14 are additionally VERIFIED by independent artefacts (resolved Compose config, live database read, file hashes). Nothing staged or committed (§9). No `git reset --hard`, `clean -fd`, `stash` or `checkout .` was run (§9). |
| **Docs policy** | Written to `docs/audit/` — the existing folder that already holds the predecessor readiness report and acceptance evidence. Filename follows `AMSDP_<Topic>_<Version>.md`. The destination was checked before writing; no existing file was overwritten. No file was migrated, so no manifest entry is due. The docs index was updated in the same task (§12 "keep the index current"). `docs/demo/AMSDP_Demo_Credentials_V1.0.md` is owner-controlled read-only and was **not** modified. |
| **Deviations** | Two, both disclosed: (1) the single-quote expansion defect I introduced and then fixed in `init_demo_env.sh` (§6.1); (2) scope extended beyond B-1…B-7 to B-8/B-9/B-10, because committing `database.py`/`alembic.ini` unchanged would have reintroduced the exact defect B-1 was raised to stop. |
| **Unresolved** | D-1…D-6 (§10). None blocks staging; D-1 and D-2 are recommended before the push. |

---

## 13. Documents and files read in this task

Documents (paths opened this session):

- `docs/audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` — findings B-1…B-7,
  commit plan, GO/NO-GO criteria (read targeted, not in full)
- `docs/governance/AMSDP_Docs_Index_V1.0.md` — `audit/` table and the drift
  verification recipe (read targeted)

Source and configuration files inspected (masked where they could contain a
credential): `docker-compose.yml`, `docker-compose.demo.yml`, `.gitignore`,
`_tools/init_demo_env.sh`, `_tools/pg_restore_test.sh`, `_tools/pg_backup.sh`,
`_tools/amsdp_stack.sh`, `backend/seed/seed_demo.py`, `backend/common/database.py`,
`backend/alembic.ini`, `backend/alembic/env.py`, `backend/conftest.py`,
`backend/tests/amsdp_test_support.py`, `frontend/package.json`,
`frontend/pages/index.js`, plus `git` index/status/log output.

**End of report.**






