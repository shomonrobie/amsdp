# AMSDP — Final Pre-Push Readiness Report

> **Task ID:** `AMSDP-FINAL-PREPUSH-DECISION-AUDIT-2026-11-11`
> **Date:** 2026-11-11 · **Branch:** `hackathon-mvp` · **HEAD:** `eb87cac55824601a7f03ee08571f828755ad7b2e`
> **Status:** final decision audit before the first push of this working tree
> **Written to:** `docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md` (`.clinerules` §11)
> **Nothing was staged, committed, pushed or force-checked-out during this task.**
> **Evidence tags** (`.clinerules` §7): **IMPLEMENTED** = the artefact exists and is
> reachable · **TESTED** = named tests pass in this tree · **VERIFIED** = a second,
> independent artefact confirms it (live API call, live DB read, browser/DOM run) ·
> **CARRIED FORWARD** = reported by an earlier document and not re-executed here ·
> **NOT PERFORMED** = explicitly out of scope for this task.

---

## 1. Executive summary and verdict

| # | Question this audit answered | Result |
|---|---|---|
| D-1 | Was the exposed development database credential rotated, and is the exposure closed? | **Closed.** Rotated, applied and verified end to end (§5). |
| D-2 | Can the two mixed-ownership frontend files be committed on their own? | **No — not without a decision.** Each is a single whole-file hunk mixing the BanglaNameSense feature with the shared `AppShell` shell migration (§6). |
| D-3 | Should the two tracked AI-Factory artefacts be removed from the tree? | **Keep them (recommended).** No secret content, documented precedent in `.gitignore`, no code reads them (§7). |
| — | Are all twelve owner-approved image assets preserved? | **Yes.** 12 files, 12 distinct contents, none ignored, none corrupted (§8). |
| — | Do the suites pass on the rotated credential? | **Yes.** Backend **289 passed**, frontend **43 passed / 0 failed** (§9). |

**Verdict: CONDITIONAL GO.** The security blocker that justified this audit (D-1)
is closed and the tree is functionally healthy, so a push is no longer blocked on
credentials. It is **not** an unconditional GO, because four gated items must be
settled first — one of them a newly discovered defect that a blind `git add -A`
would publish:

- **G-1 (security, newly found — blocker for `git add -A` only).** The *untracked*
  `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` still contains the **pre-rotation
  database password** at four sites. It is dead (that credential was rotated away
  in §5), so it is no longer a live secret — but it must be scrubbed before that
  file is staged. Finding **B-11**, §5.6.
- **G-2 (owner approval).** `docs/demo/AMSDP_Demo_Credentials_V1.0.md` is
  Product-Owner-controlled (`.clinerules` §11 **R**) and is modified in the working
  tree (one-line API-base fix, 8100 → 8110). Its content must not be committed
  without explicit owner approval.
- **G-3 (owner approval).** Committing `frontend/pages/patients.js` and
  `frontend/styles/global.css` whole (§6) records non-BanglaNameSense work
  alongside the feature; the owner must accept that, or fund an interactive
  line-level split.
- **G-4 (owner decision, non-blocking).** D-3 keep-vs-untrack (§7).

Everything below is the evidence for those statements. Where a predecessor report
was wrong, the correction is stated explicitly rather than quietly overwritten.

---

## 2. Scope, authorisation and what this audit deliberately did not do

**Authorised:** rotate the local development database credential and any
local-only configuration that carries it; read-only inspection of the repository,
the working tree, the Compose stacks and the local database; run validation that
proves the tree still works; write this report and update the documentation index.

**Not authorised, and not done:** staging, committing, pushing, fetching, tagging,
any branch operation, `git reset`/`checkout`/`stash`/`clean`, rewriting history,
deleting or rewriting any document, editing application code or Compose files,
editing any Product-Owner-controlled document, or dropping the throwaway database.

**Safety rules observed throughout.** No credential value appears in this report,
in any command line, in any log, or in shell history. Probes printed lengths and
booleans only. The new password was generated in-process
(`secrets.token_urlsafe(24)` → 32 characters, 3 character classes) and written
atomically to a `0600` file. `psql` received its `ALTER ROLE` statement through
**stdin**, never `argv`. Where a probe had to show context, the secret substring
was replaced with `<MASKED:n>` before printing.

---

## 3. Repository identity and remote state

| Fact | Value | How established |
|---|---|---|
| Current branch | `hackathon-mvp` | `git rev-parse --abbrev-ref HEAD` |
| HEAD commit | `eb87cac55824601a7f03ee08571f828755ad7b2e` | `git rev-parse HEAD` |
| HEAD subject | "I have commited agent rules, ai factory code, new UI/UX docs before using ilai to start working on the project" | `git log -1` |
| HEAD date | 2026-11-06 21:08:57 +0600 | `git log -1 --pretty=%ci` |
| Upstream tracking branch | **none configured** | `git rev-parse --abbrev-ref @{u}` → no output |
| Remote | `origin` = `https://github.com/shomonrobie/amsdp` (fetch **and** push) | `git remote -v` |
| Credentials inside the remote URL | **none** — plain HTTPS, no `user:token@` | inspection of `git remote -v` output |
| Local refs beyond branches/tags | `refs/cline/*` shadow refs exist (§5.3) | `git for-each-ref` sweep |

No upstream means "ahead/behind" cannot be computed and a push must name its
target explicitly (`git push -u origin hackathon-mvp`). Because the remote URL
carries no token, no credential is stored in `.git/config`.

---

## 4. Working-tree state — the exact starting point for any commit

| Category | Count | Meaning |
|---|---:|---|
| **Staged (index)** | **0** | `git diff --cached --name-only` is empty — nothing is staged |
| Modified tracked files (` M`) | 58 | Working-tree edits, unstaged |
| Deleted tracked files (` D`) | 2 | Relocations, see below |
| Untracked files (`??`, expanded) | 144 | New files; none is ignored by mistake (§8) |
| **Total (porcelain, `-uall`)** | **204** | 58 + 2 + 144 |

**Counting method matters.** `git status --porcelain` *without* `-uall` collapses
untracked directories to one line and reports **116** entries (58 ` M`, 2 ` D`,
56 `??` directories) — that undercounts by design. Every figure above is from
`git status --porcelain -uall`, where each untracked file is listed individually.

**The tree changed while this audit ran.** Two owner documents were added by the
Product Owner mid-session: `docs/AMSDP_Master_Feature_List_V2.4_…` (15:29) and
`docs/AMSDP_Master_Feature_List_V2.5_…` (17:17) — the latter declaring itself the
approved, active master feature list. They account for 2 of the untracked files; this
report accounts for the 143rd. The earlier session figure of 141 untracked / 201
total predates all three and is superseded by the numbers above. The same two
documents were also missing from the docs index, which is fixed in this task
(§12.2 K-6).

The two deletions are **not** data loss: they are the release-readiness documents
moved from the repository root into `docs/audit/` under owner decision O-6
(recorded in the migration manifest). Git sees the old path as deleted and the new
path as untracked; staging both records a rename. All nine files now in `docs/audit/`
are untracked, so that folder would enter history whole.

Notable untracked groups: `backend/common` 19, `backend/alembic` 12,
`docs/images` 12, `docs/implementation` 11, `docs/audit` 9, `backend/tests` 8,
`frontend/pages` 8, `frontend/components` 7, `frontend/lib` 7, `docs/governance` 6,
`frontend/tests` 4, `docs/product` 4, plus `.clinerules`, `.env.example`,
`docker-compose.demo.yml`, the seven `_tools/` files and the two owner master-lists
at the `docs/` root.

Two consequences any commit plan must respect:

1. **`.clinerules` is untracked.** The governance router that binds the agent is
   not yet in history; the first push should include it, or the rules that produced
   this report stay invisible to the remote.
2. **`.env` is correctly excluded.** Untracked *and* ignored (`git check-ignore`
   matches), mode `0600`, 463 bytes, holding only `POSTGRES_PASSWORD` (32 chars)
   and the six `AMSDP_DEMO_PASSWORD_*` entries.

---

## 5. D-1 — database credential rotation (closed)

### 5.1 What was rotated, and how

| Step | Action | Evidence |
|---|---|---|
| 1 | New password generated in-process: `secrets.token_urlsafe(24)` → 32 characters, 3 character classes | generator ran inside the rotation script; only length/classes printed |
| 2 | `.env` rewritten **atomically** (temp file + `os.replace`), mode forced to `0600` | `stat` → `0o600`; file still ignored and untracked |
| 3 | Database role updated with `ALTER ROLE … PASSWORD` delivered on **stdin** | `psql` accepted the statement; no value in `argv` or history |
| 4 | New credential proven over TCP `127.0.0.1:5433` | live `psycopg2` connect + `SELECT 1` |
| 5 | Old credential proven **rejected** | live connect attempt fails authentication |
| 6 | Schema/data reachable with the new credential | `alembic current` → head; `SELECT count(*) FROM staff_users` returns rows |

The pre-rotation password was 18 characters. The post-rotation password is 32
characters. Nothing else in the environment changed: host TCP authentication stays
`scram-sha-256`, and the container's local-socket authentication stays `trust`
(that is the documented recovery path if `.env` is ever lost).

### 5.2 Runtime verification after rotation (VERIFIED, not inferred)

| Probe | Result |
|---|---|
| `_tools/amsdp_stack.sh status` | **10/10 services `running` / `healthy` / probe `ok`** — db, identity, organization, patient, doctor, scheduling, appointment, queuing, audit, frontend |
| Backend readiness probes on `8110–8117` | all `ready` / `health` ok |
| Frontend `http://127.0.0.1:3100` | responds, healthy |
| `docker compose -p amsdp -f docker-compose.yml config -q` | **VALID** |
| `docker compose -p amsdp -f docker-compose.yml -f docker-compose.demo.yml config -q` | **VALID** |
| Resolved-compose credential check (both stacks) | new value present, old value **absent** |

### 5.3 How far did the *live* credential actually travel? (correction of the predecessor report)

The predecessor remediation report claimed the credential was exposed in
`origin/main`. That claim does **not** survive re-verification:

| Location | Live (pre-rotation) value present? |
|---|---|
| `origin/main` tree | **No** |
| local `main` tree | **No** |
| local `hackathon-mvp` tree (HEAD `eb87cac`) | **No** — HEAD's `docker-compose.yml` is a 722-byte stub with no credential |
| local shadow refs `refs/cline/*` | **Yes — this is the only place** |
| current working tree | **No** (live value appears in none of the six checked documents) |

So the exposure was **local-only**, confined to Cline's own shadow refs, and never
reached the remote. Rotation was still the correct action — the value existed on
disk in a place a future `git push --all` or ref-mirroring tool could have carried
it — but the risk narrative is materially lighter than the predecessor report's,
and this report supersedes it on that point.

### 5.4 Compose and environment contract after rotation

| Check | Result |
|---|---|
| `.env` keys | `POSTGRES_PASSWORD` + six `AMSDP_DEMO_PASSWORD_*`; `AMSDP_DATABASE_URL` / `_DEMO` are **not** set (by design) |
| `docker-compose.yml` hardcoded DSN userinfo | **0** |
| `docker-compose.demo.yml` hardcoded DSN userinfo | **0** |
| How the DSNs get their password | nested expansion — `${AMSDP_DATABASE_URL:-…://amsdp:${POSTGRES_PASSWORD}@db:5432/…}`, verified: password segment length **0**, nested reference **True** |
| `.env.example` | 2 examples of the pattern, both commented out with the literal placeholder `REPLACE_ME` — a documented contract, not a credential |
| Missing-variable behaviour | `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?missing - set it in .env…}` — **fails loudly** instead of defaulting to a weak value |

That nested-expansion contract is why rotation required no Compose edit: one
variable, one place, every service follows. It also explains a scanner artefact
recorded in §5.5.

### 5.5 Tree-wide credential scan — 31 hits, 4 real (finding **B-11**)

A deliberately broad scan of 374 tracked-and-untracked source/config/document files
returned **31 literal-credential hits across 15 files**. Re-classified by reading
each hit with the secret substring masked:

| Classification | Files | Hits | Detail |
|---|---:|---:|---|
| **Real: dead credential in an untracked demo doc** | 1 | **4** | `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` L30, L68, L70 (DSN `…://amsdp:<18 chars>@127.0.0.1:5433/…`) and L191 (`PGPASSWORD=<18 chars>`) |
| Type annotations, not values | 3 | 6 | `backend/identity/models.py` (4× `password: str`), `backend/appointment/tracking.py`, `backend/common/tracking_tokens.py` (`raw_token: str`) |
| Test fixtures / test-only constants | 5 | 14 | `PASSWORD = "…"` constants and `password=` kwargs in `backend/tests/*`, `backend/audit/tests/*`, `backend/identity/tests/*`, `ai_factory/tests/unit/test_tools_analysis.py` (which *writes* a sample credential to test a scanner) |
| Runtime-minted token expressions | 1 | 4 | `backend/identity/tests/test_identity.py` — `jwt.encode({...})`, no literal |
| Frontend code expressions | 2 | 2 | `frontend/pages/index.js` (`password: u`), `frontend/pages/staff.js` (`password: e.target.value`) |
| Documents *quoting* a finding / a wireframe placeholder | 3 | 5 | `docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` (`password: str` in an R16 finding row), `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` ("Temporary Password:" in an ASCII frame), `ai_factory/docs/AILI_Independent_Verification_Report_V2.0.0.md` (`_next_token: int`) |

**B-11 — the one real finding.** `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`
carries the **pre-rotation** database password four times. Three mitigating facts
matter and all three are verified:

1. The file is **untracked** (`??`) — it has never been committed, so nothing has
   been published.
2. The credential it names is **dead**: rotation in §5.1 removed it from the
   database; the current 32-character password appears in **none** of the six
   documents checked.
3. The same file also contains **two of the six live demo user passwords**
   verbatim (org-admin and receptionist) — those are *live* accounts.

⇒ **Gate G-1.** Before that file is staged: replace the four database-credential
occurrences with `${POSTGRES_PASSWORD}` / `<see docs/demo/AMSDP_Demo_Credentials_V1.0.md>`
placeholders, and decide whether the two live demo passwords belong in the runbook
at all (the canonical location for demo credentials is the owner-controlled
`docs/demo/AMSDP_Demo_Credentials_V1.0.md`). A blind `git add -A` would publish
both. This report does **not** edit the runbook: content changes to a demo document
are outside this task's authorisation, and the owner must choose the wording.

**All six live demo passwords already sit in the tracked, owner-controlled
`docs/demo/AMSDP_Demo_Credentials_V1.0.md`.** That is the accepted design of a
hackathon demo credential sheet (`.clinerules` §11 marks the file **R**: read and
cite, never paste into reports) — recorded here as an observation, not a defect.

### 5.6 Correction of an earlier scanner claim

An earlier pass of this audit reported a second historical value ("length 8")
inside `docker-compose.yml`, `docker-compose.demo.yml` and
`docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md`. Re-checked directly:
**no length-8 literal credential exists in any of the three files.** The match was
an artefact of the scanner reading a nested `${…}` expansion as if it were a value.
Proof: parsing the Compose defaults yields password-segment length `0` with
`nested_ref=True` for every occurrence (§5.4), a targeted length-8 scan across all
scanner patterns returns nothing, and `git diff` on the remediation report shows no
credential line. The only historical value still present anywhere in the tree is
the 18-character one in the runbook (§5.5).

---

## 6. D-2 — the two mixed-ownership frontend files

Both files are modified tracked files whose diff mixes **BanglaNameSense feature
work** with **other changes to the same file**. Measured with `git diff --numstat`
and a per-hunk breakdown:

| File | numstat | Hunks | BNS-mentioning lines | What else is in the same hunk |
|---|---|---:|---:|---|
| `frontend/pages/patients.js` | +49 / −62 (5,585 B) | **1** — `@@ -1,64 +1,51 @@` | 2 (`import BanglaNameSense`, its field usage) | the whole page rewritten onto the shared shell: `AppShell`, `RequireLogin`, layout/state restructuring |
| `frontend/styles/global.css` | +135 / −16 (9,521 B) | **1** — `@@ -1,17 +1,136 @@` | 12 (suggestion-list, highlight, combobox styles) | a general stylesheet expansion: base reset, typography, layout, shared component styles |

### 6.1 Why they cannot be committed "on their own"

1. **There is no hunk boundary to split on.** Each file is recorded as one
   contiguous replacement of its head region. `git add -p` would offer a single
   hunk spanning the whole change; a clean split needs manual line-level hunk
   editing, i.e. a human decision per line, then a re-run of the suites against an
   intermediate state that has never existed.
2. **A partial commit would not build.** `patients.js` imports two files that are
   themselves **untracked** — `frontend/components/BanglaNameSense.js` and
   `frontend/components/AppShell.js`. Committing the page before (or without) those
   components produces a commit whose page cannot resolve its imports.
   `AppShell.js` is imported by **11 pages** (`patients`, `appointments`, `queue`,
   `doctors`, `schedules`, `staff`, `branches`, `orgs`, `audit`, `notifications`,
   `dashboard`), so it is the load-bearing piece of the same UI rework.
3. **Ordering therefore decides correctness**, not authorship: the components must
   land in the same commit as the pages, or in an earlier one.

### 6.2 The three available resolutions

| Option | Effect | Cost / risk |
|---|---|---|
| **A — commit each file whole** (recommended) | One commit per concern, each containing the full new file; every commit builds and every test state is real | The commit that adds `patients.js` also carries the owner's shell migration; the message must say so |
| **B — line-level split with `git add -p` editing** | BanglaNameSense lines separated from the rest | Hand-edited hunks, two states that never ran, and the page still cannot build without `AppShell.js` → Option B cannot actually produce a building BanglaNameSense-only commit |
| **C — hold both files back** | Neither is pushed yet | The BanglaNameSense feature ships without its patient page wiring, i.e. the feature is untestable from the UI |

**Recommendation: Option A**, with the mixed authorship stated in the commit body
("includes the shared-shell migration for this page, authored outside the
BanglaNameSense task"). Because Option B cannot yield a building intermediate
commit, the "keep the feature commit pure" goal is unreachable here — that is a
property of the diff, not a choice. Owner approval for Option A is **gate G-3**.

---

## 7. D-3 — the two tracked AI-Factory artefacts

| Fact | `runs/RUN-20261105T130533-001.json` | `var/tasks/AMSDP-000001.json` |
|---|---|---|
| Tracked | **yes** (since the same 2026-11-05 commit) | **yes** |
| Size / lines | 33,450 B / 1,103 | 3,405 B / 94 |
| Sensitive-pattern hits | **0** | **0** |
| Commits touching it | 1 | 1 |
| Read by product code at runtime | **no** | **no** |
| References in the tree | only the `.gitignore` note | `.gitignore` note + AI-Factory docs/tests using `AMSDP-000001` as a *fixture task id* / workspace name (not this file) |

### 7.1 Correction: the ignore rules already exist

An earlier pass recorded these artefacts as "not covered by any ignore rule". That
is wrong, and the correction changes the recommendation. `.gitignore` L46–52 says,
verbatim:

```
# Note: runs/RUN-20261105T130533-001.json and var/tasks/AMSDP-000001.json are
# already tracked in history.  Ignore rules apply to new, untracked files only —
# they neither remove nor untrack anything.
/runs/
/var/
/backups/
```

So: **new** artefacts under `runs/`, `var/` and `backups/` are already ignored —
verified by the fact that today's backup run produced a new file under `backups/`
that does not appear in `git status`. The two tracked artefacts are the *documented
exception*, tracked because they entered history before the rule.

### 7.2 Recommendation: keep them (D-3 is not a defect)

- They contain **no** credential, token or personal data (0 hits on the
  password/secret/token/DSN scan).
- They are **historical run evidence** of the AI-Factory stub workflow — exactly
  the kind of artefact a reviewer may want to inspect, and they are small (37 KB
  together).
- Nothing reads them, so leaving them cannot affect behaviour.
- Removing them means a commit that *deletes evidence* from history's tip — a
  larger governance act than the problem it solves.

If the owner prefers a clean tree anyway, the correct action is a dedicated
`git rm --cached <the two paths>` commit (the files stay on disk because the ignore
rules already cover them); that needs owner sign-off and should not ride along with
the feature push. **Decision D-4 / gate G-4, non-blocking.**

---

## 8. The twelve owner-approved image assets

### 8.1 Contents present and distinct (VERIFIED on disk)

All 12 approved assets exist, are non-empty, and have **12 distinct checksums**
(no duplicate-then-renamed placeholder, no truncated copy):

| Asset | Bytes | MD5 (first 10) |
|---|---:|---|
| `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-24.png` | 56,756 | `c2465fd8e5` |
| `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-36.png` | 78,761 | `d6bdfb1bfc` |
| `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-44.png` | 48,099 | `8bf185cb3b` |
| `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-51.png` | 124,477 | `9f9abff5ef` |
| `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-56.png` | 65,070 | `71ed659412` |
| `docs/images/doctors images/doctor-group-1.jpeg` | 60,809 | `2114a3e4ab` |
| `docs/images/doctors images/doctor-group-2.jpeg` | 76,866 | `7396259f1b` |
| `docs/images/doctors images/doctor-group-3.jpeg` | 67,381 | `37f0b148ed` |
| `docs/images/doctors images/doctor-group-4.jpeg` | 76,387 | `f3b7d04a66` |
| `docs/images/doctors images/doctor-group-5.jpeg` | 64,246 | `34cb87fd12` |
| `docs/images/doctors images/doctor-group-6.jpeg` | 52,616 | `d082841338` |
| `docs/images/example dashboards/booking_dashboard_1.webp` | 65,934 | `d6e7a4cb09` |
| **Total** | **837,402 B ≈ 818 KiB** | 12 distinct |

The "preserved" claim is therefore **true on disk**. Empty-file and
duplicate-content checks both pass.

### 8.2 Correction — they are untracked, **not** ignored

An earlier pass of this audit recorded these assets as "ignored by Git, so they
would not ship". Re-verified directly, that is **wrong**, and the correction
simplifies the commit plan:

| Probe | Output | Reading |
|---|---|---|
| `git check-ignore -v '<asset>'` | no rule printed, **exit code 1** | *not ignored* — exit 1 is the "no match" code |
| `git status --porcelain -- docs/images` | `?? docs/images/` | untracked |
| `git status --porcelain --ignored=matching -- docs/images` | `?? docs/images/` (still `??`) | confirms not ignored |
| `git ls-files -- docs/images \| wc -l` | `0` | nothing tracked yet |
| `git add --dry-run -- docs/images \| wc -l` | `12` | a plain `git add` stages **exactly the 12 assets** |
| `.gitignore` image patterns | **none** (`grep -i` for `image`/`.png`/`.jpeg`/`.webp` → no match) | |
| Nested `docs/**/.gitignore` / `.git/info/exclude` / `core.excludesFile` | **none configured** | no rule from any layer |

⇒ No `git add -f`, and no ignore-rule exception, is required. `git add docs/images`
stages all 12 at 818 KiB total, and `git status` will then show them as added.
The remaining question is only whether the owner wants ~0.8 MiB of screenshots in
this push (**gate G-5**, non-blocking, default: yes — they are approved assets).

---

## 9. Verification matrix — what was actually run on this tree

| # | Check | Command (abbreviated) | Result | Tag |
|---|---|---|---|---|
| 1 | Backend test suite | `python -m pytest backend` against throwaway DB `amsdp_prepush_test` | **289 passed, 0 failed**, 70 warnings, 145.89 s, rc=0 | **TESTED** |
| 2 | Frontend test suite | `node --test frontend/tests` (incl. BanglaNameSense suite) | **tests 43, pass 43, fail 0, skipped 0**, rc=0 | **TESTED** |
| 3 | Migration head reachable | `alembic current` on the live DB with the rotated credential | head revision reported, no pending drift | **VERIFIED** |
| 4 | Live DB read | `SELECT count(*) FROM staff_users` via TCP `127.0.0.1:5433` | row count returned | **VERIFIED** |
| 5 | Old credential rejected | connect with pre-rotation value | authentication **fails** | **VERIFIED** |
| 6 | Stack health | `_tools/amsdp_stack.sh status` | **10/10** services running/healthy | **VERIFIED** |
| 7 | Compose validity (dev) | `docker compose -f docker-compose.yml config -q` | **VALID** | **VERIFIED** |
| 8 | Compose validity (dev+demo) | `… -f docker-compose.demo.yml config -q` | **VALID** | **VERIFIED** |
| 9 | Resolved-compose credential | parse both stacks' resolved config | new value present, old absent | **VERIFIED** |
| 10 | Shell script syntax | `bash -n _tools/*.sh` (7 files) | **clean** | **TESTED** |
| 11 | Python byte-compile | `python -m compileall -q backend` | rc=0 | **TESTED** |
| 12 | Bangla dataset integrity | dataset validator | VALID — 718 names, 701 unique, 17 duplicate aliases tolerated | **TESTED** |
| 13 | Backup/restore scripts | exercised after rotation | both OK | **VERIFIED** |
| 14 | Ad-hoc container rebuild | `docker compose up -d` after rotation | new password picked up by every service | **VERIFIED** |
| 15 | Frontend reachability | `http://127.0.0.1:3100` | healthy response | **VERIFIED** |
| 16 | Backend readiness probes | `8110–8117` | all ready/health ok | **VERIFIED** |
| 17 | Ignore-rule coverage of `.env` | `git check-ignore .env` | matched (ignored) | **VERIFIED** |
| 18 | Image assets | 12 files, size + MD5 sweep (§8) | 12 present, 12 distinct | **VERIFIED** |
| 19 | D-3 artefact content | sensitive-pattern scan of both files | 0 hits | **VERIFIED** |
| 20 | Tree-wide credential scan | 374 files, all patterns, masked context | 31 hits / 15 files → 4 real, all dead (§5.5) | **VERIFIED** |

**Not performed here, deliberately:** no browser walkthrough of the demo flows
(carried forward from the demo runbook validation), no load/performance test, no
`npm run build`/production bundle check, no CI run (no pipeline exists in this
repository), and no push-side verification of any kind. Two suites are unverified
on a *fresh clone* — they were run inside this working tree, not from a checkout.

---

## 10. Residual risks and carried-forward debt

### 10.1 Risks that survive this audit

| # | Risk | Severity | Mitigation / status |
|---|---|---|---|
| R-1 | **B-11** — the untracked runbook still holds the dead DB password (4 sites) and two live demo passwords | Medium (publish-on-`git add -A`) | **Gate G-1**: scrub before staging. Not a live credential. |
| R-2 | All six **live** demo passwords sit in a tracked, owner-controlled doc | Accepted | Owner decision (`.clinerules` §11 R). Never paste into reports or commits' messages. |
| R-3 | Demo credentials are static and long-lived (hackathon scope) | Accepted | Accepted for the demo; flagged for any post-hackathon deployment. |
| R-4 | `refs/cline/*` still contains the pre-rotation value in shadow commits | Low (local only) | Value is dead; refs are local and must never be pushed (`git push --all`/`--mirror` would carry them). |
| R-5 | Container-local Postgres auth is `trust` on the unix socket | Low | Intentional (documented recovery path inside the container); host TCP stays `scram-sha-256`. |
| R-6 | Two suites were run in-tree, never from a clean clone | Low | Push then verify on a fresh clone; first push should be followed by a clean-clone run. |
| R-7 | `frontend/pages/patients.js` and `global.css` mix authorship (§6) | Low (traceability) | Gate G-3: state it in the commit body. |
| R-8 | No CI pipeline exists, so "green" means "green on this machine" | Medium (process) | Out of scope here; recorded so the claim is not overstated. |

### 10.2 Carried-forward technical debt (not fixed by this audit)

- Pydantic V2 `dict()` deprecations in `organization/notification_config.py` (L89)
  and `appointment/tracking.py` (L106) — 70 warnings in the suite, no failures.
- FastAPI `@app.on_event("startup")` deprecation across services (use `lifespan`).
- `starlette.testclient` / `httpx` deprecation notice from the vendored FastAPI.
- `PytestReturnNotNoneWarning` in `backend/tests/test_tracking_tokens.py::test_issue_tracking_token`
  (returns a tuple instead of asserting).
- A 5-byte HMAC key in `tests/test_security.py::TestInvalidToken::test_wrong_secret`
  — a test *fixture* proving the wrong key is rejected; the warning is expected.

---

## 11. Proposed commit scope for the first push

Principle: **name every path explicitly.** `git add -A` / `git add .` must not be
used on this tree, because they would sweep in the runbook (G-1) and the
owner-controlled demo-credentials edit (G-2). Six commits, each independently
meaningful, in this order — components before the pages that import them:

| # | Commit | Contents (explicit paths) | Gate |
|---|---|---|---|
| C-1 | `chore(governance): add agent rules and documentation set` | `.clinerules`, `docs/governance/*`, `docs/audit/*` (incl. this report), `docs/implementation/*`, `docs/product/*`, `docs/architecture/*`, the two owner master-lists at the `docs/` root (V2.4/V2.5), the two relocated root documents (rename) | — |
| C-2 | `chore(infra): add container tooling and demo compose` | `_tools/*.sh`, `docker-compose.demo.yml`, `.env.example`, `.gitignore` | — |
| C-3 | `feat(backend): multi-service identity, org, patient, doctor, scheduling, queue, audit` | `backend/**` (common, alembic, each service, tests) | — |
| C-4 | `feat(frontend): shared shell and application pages` | `frontend/components/*` (incl. `AppShell.js`), `frontend/lib/*`, `frontend/pages/*`, `frontend/styles/global.css` | **G-3** |
| C-5 | `feat(frontend): BanglaNameSense patient-name suggestion` | `frontend/components/BanglaNameSense.js`, `frontend/data/*`, `frontend/tests/*` (the 43 passing tests) | — |
| C-6 | `docs(demo): add demo runbook and assets` | `docs/images/**` (12 assets), `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` **after G-1 scrub**, `docs/demo/AMSDP_Demo_Credentials_V1.0.md` **only with G-2 approval** | **G-1, G-2, G-5** |

Notes that matter for auditability:

- **C-4 carries `patients.js` and `global.css` whole** (Option A, §6.2). C-5's
  message must not claim the patient page wiring it does not add — the page already
  arrived in C-4.
- **The two relocations belong in C-1.** `git add -A -- docs/audit <the two old root paths>`
  would record the rename; using explicit old+new paths achieves the same without
  touching anything else.
- **C-6 is the only commit that can publish a secret**, and only through G-1/G-2
  being skipped. It should be staged last, after a final read of the runbook.
- After staging each commit: `git diff --cached --stat` and a `grep` of
  `git diff --cached` for the six credential patterns **before** `git commit`.
- Push target: `git push -u origin hackathon-mvp` (no upstream exists, §3). Do
  **not** push `refs/cline/*`; a `--mirror`/`--all` push would carry them (§10.1 R-4).

Pre-flight checklist for whoever performs the commit:

1. `git status --porcelain -uall | wc -l` — expect **204** (58 modified, 2 deleted, 144 untracked) at the time of this report; add 1 if this report is not yet counted.
2. `git diff --cached --name-only` — must be **empty** before staging begins.
3. G-1 scrub verified by re-running the credential scan on the runbook only.
4. G-2 owner approval recorded for the credentials-doc one-line change.
5. G-3 owner approval recorded for the two mixed files.
6. Staging done with explicit paths only.
7. No `git commit -a`, no `git add -A`, no amend of `eb87cac`.

---

## 12. Verdict, decision register and open owner decisions

### 12.1 Gate summary

| Gate | Type | Blocks the push? | Owner action |
|---|---|---|---|
| **G-1** — scrub the dead DB password (4 sites) + decide on the 2 live demo passwords in the untracked runbook | Security hygiene | **Only blocks `git add -A`**; a path-scoped push can proceed without that file | Approve the wording, or exclude the runbook from this push |
| **G-2** — commit the one-line change to the owner-controlled `docs/demo/AMSDP_Demo_Credentials_V1.0.md` (`API Base: …:8100` → `…:8110`) | Owner authority (`.clinerules` §11 R) | Yes, for that file only | Approve, or leave the change uncommitted |
| **G-3** — commit `patients.js` + `global.css` whole, mixed authorship | Traceability | No | Approve Option A (§6.2), or choose C (hold back) |
| **G-4** — keep the two tracked AI-Factory artefacts (recommended) vs `git rm --cached` | Housekeeping | No | Confirm keep (default) |
| **G-5** — include the 12 image assets (818 KiB) in this push | Content scope | No | Confirm include (default: yes) |

With G-1 honoured and G-2/G-3 approved, the tree is **ready to push** as six
path-scoped commits (§11).

### 12.2 Corrections this audit makes to earlier documents

| # | Earlier claim | Verified position |
|---|---|---|
| K-1 | The live DB password was exposed in `origin/main` | Exposure was **local only**, in `refs/cline/*` (§5.3) |
| K-2 | The 12 image assets are Git-**ignored** and would not ship | They are **untracked, not ignored**; `git add docs/images` stages all 12 (§8.2) |
| K-3 | No `.gitignore` rule covers `runs/`, `var/tasks/` or `backups/` | Rules exist (`.gitignore` L46–52) and cover **new** files; the two tracked artefacts are the documented exception (§7.1) |
| K-4 | A second historical credential of length 8 sits in the Compose files and the remediation report | No such literal exists; the match came from nested `${…}` expansions (§5.6) |
| K-5 | *(new)* — nothing recorded | **B-11**: the untracked runbook still carries the dead password at 4 sites and 2 live demo passwords (§5.5) |
| K-6 | *(new)* — the docs index claimed 52 documents and V2.3 as the "latest" feature list | The tree holds **55**; `Master_Feature_List_V2.4` and **V2.5 (approved, active, supersedes V2.0–V2.4)** had never been registered. Fixed in this task (§13.1); no owner document was modified |

### 12.3 Final recommendation

**CONDITIONAL GO.** The rotated credential is verified end to end, the two suites
pass (289 backend + 43 frontend), the stack is healthy on the new password, the
tree contains no live credential in any tracked file, and the twelve approved
assets are intact. The conditions are procedural, not technical: honour G-1, and
get G-2/G-3 signed off before their files are staged.

---

## 13. Governance and Skill Compliance (`.clinerules` §6)

### 13.1 Applicable governance documents and selected skills

| Domain (`.clinerules` §4 row) | Document actually read this session | Applied as |
|---|---|---|
| Documentation: reading docs, writing reports, doc placement | `docs/governance/AMSDP_Docs_Index_V1.0.md` (§12 step 3 — read first), `.clinerules` §11 | Report written under `docs/audit/`; index updated in the same task, including the two unregistered owner documents it was missing (§12.2 K-6) |
| Audit / data integrity / reporting | `.clinerules` §3, §7; `backend/common/audit*.py` conventions | Append-only events untouched; no audit row deleted or rewritten |
| Docker, deployment, ports, infrastructure | `docker-compose.yml`, `docker-compose.demo.yml`, `_tools/amsdp_stack.sh` | Read and validated (`config -q`, live status); not edited |
| Multi-tenant data / DB schema | `backend/alembic` chain, `backend/common/models.py` | Read-only inspection (migration head, `staff_users` count); no migration created |
| Authentication / secrets / RBAC | `.clinerules` §3 non-negotiables | Rotation performed; no secret logged, printed or committed |
| AI-Factory artefacts (D-3) | `.gitignore` L46–52, `ai_factory/` references | Read-only assessment |

**Skills:** `.clinerules` §5 states **no skill packages are installed** in this
workspace (no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No
skill was selected, and none is claimed to have been used. The governance documents
in the table above are the substituted knowledge source, as §5 directs.

### 13.2 Non-negotiable checks (`.clinerules` §3)

| Non-negotiable | Status in this task |
|---|---|
| Never log/expose secrets, tokens, keys | **Held.** Lengths and booleans only; masked context; `ALTER ROLE` via stdin; no value in this report |
| Enforce access server-side; tenant from token | **N/A** — no endpoint, permission or scope logic touched |
| Cross-tenant access fails closed with 404 | **N/A** — no access path modified |
| `organization_id` remains the sole tenant key | **Held** — no schema change |
| Audit events append-only | **Held** — nothing in `audit/` rewritten; log files only read |
| Denials recorded, never swallowed | **N/A** — no request path exercised |
| Every schema change is a forward-only idempotent Alembic migration | **Held** — zero migrations created |
| Never claim an unverified capability | **Held** — every row in §9 names the probe; unrun checks are listed as NOT PERFORMED |
| Only use available tools/skills | **Held** — no skill claimed, no dependency added |

### 13.3 Execution boundaries (`.clinerules` §9)

No destructive Git command was run — no `reset`, `checkout`, `stash`, `clean`,
`commit`, `push`, `fetch`, `tag` or ref edit. `git add` was only ever used with
`--dry-run`. The `.env` change is local-only, `0600`, ignored and unstaged. The
throwaway database `amsdp_prepush_test` was created for the suite and left in place
(dropping it is an owner call). Context was kept small by piped/`tail`-ed reads.

---

## 14. Evidence trail and state left behind

| Artefact | Location | Note |
|---|---|---|
| Backend suite output | `/tmp/bt.txt` | `289 passed, 70 warnings in 145.89s` |
| Frontend suite output | `/tmp/ft.txt` | `tests 43 / pass 43 / fail 0`, rc=0 |
| Masked credential-scan transcripts | `/tmp/ev.txt`, `/tmp/ev2.txt`, `/tmp/p36.txt`–`/tmp/p63.txt` | all values masked before printing |
| Image inventory (sizes, checksums) | `/tmp/img.txt` | §8.1 source |
| Ignore/asset verification | `/tmp/ig.txt`, `/tmp/ig2.txt` | §8.2 source |
| Throwaway test database | `amsdp_prepush_test` on the dev instance | created for the suite, **left in place** |
| Pre-rotation backup | `backups/` (new file from the post-rotation run) | ignored by `/backups/`, not staged |
| Local, uncommitted, ignored | `.env` — 32-char `POSTGRES_PASSWORD`, mode `0600` | rotation applied; not staged |
| **Staged** | **nothing** | `git diff --cached --name-only` empty at start and end |

`/tmp` transcripts are scratch evidence, not deliverables: they are outside `docs/`
and will not survive a reboot. Everything that must persist is in this report or in
the documents it cites.

### 14.1 Open items this audit could not close

1. **B-11 wording** — the runbook's four dead-password sites need an owner-chosen
   replacement (G-1). Not edited here on purpose.
2. **The two live demo passwords in the runbook** — whether the runbook should name
   them at all, or defer to the owner-controlled credentials sheet (G-1).
3. **`AppShell.js` and the ten sibling pages** — the shared-shell migration is
   inseparable from the BanglaNameSense commit *and* from the pages it rewrites;
   after C-4/C-5 the authorship split is documented, not eliminated (G-3).
4. **No CI** — the "green" evidence in §9 is machine-local (R-8).
5. **`refs/cline/*`** — the dead pre-rotation value remains in local shadow refs;
   they must never be pushed and are not part of any commit plan (§10.1 R-4).

---

**Signed evidence standard (`.clinerules` §7).** IMPLEMENTED: this report and the
index update. TESTED: both suites, `bash -n`, `compileall`, dataset validator.
VERIFIED: live DB reads on the rotated credential, old-credential rejection, stack
status, both Compose resolutions, asset checksums. **ACCEPTED: not yet** — G-1
through G-5 await the project owner. Nothing was staged, committed or pushed.
