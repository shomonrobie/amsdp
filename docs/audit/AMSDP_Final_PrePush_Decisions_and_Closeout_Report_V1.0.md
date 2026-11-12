# AMSDP — Final Pre-Push Decisions and Closeout Report V1.0

> **Task ID:** `AMSDP-FINAL-PREPUSH-DECISIONS-AND-CLOSEOUT-2026-11-11`
> **Date:** 2026-11-11 · **Audit scope:** the bounded closeout of the pre-push decision set —
> apply only owner-approved decisions, re-verify the repository state from scratch, protect every
> unresolved gate, and re-derive the commit plan against the tree as it stands now.
> **Written to:** `docs/audit/` (`.clinerules` §11 — audit subfolder; no migration involved, so no manifest entry).
> **Status:** audit complete · **Verdict: CONDITIONAL GO** (§14)
> **Nothing was staged, committed, pushed, merged or deployed by this task** (§4.3, §16).
> **Secret handling:** no credential value appears anywhere in this report; every comparison in §6
> is by SHA-256 or by length only (`.clinerules` §3, §12).

---

## 1. Executive summary

| Question | Verified answer | Evidence |
|---|---|---|
| Is the rotated database credential correctly used by the app, the DB layer and Alembic? | **Yes** | §5.1 — `common/database.py` reads `POSTGRES_PASSWORD`, `alembic/env.py` reads `AMSDP_DATABASE_URL`, `alembic.ini` has no live URL, compose resolves and validates |
| Does the current database password appear in any file that could be committed? | **No — 0 of 382 files** | §6.5 |
| Is anything staged? | **No — `staged=0`** | §4.3 |
| Do the test suites pass on this tree today? | **Yes — 289 backend, 43 frontend** | §9 |
| Is the documentation index reconciled? | **Yes — 55 on disk = 55 registered in-tree before this report; 56 after** (+5 deliberately out-of-tree AI-Factory names) | §7 |
| Are the 12 owner-approved images intact and distinct? | **Yes — 12 files, 12 distinct SHA-256, 837,402 B** | §8 |
| Are all earlier gates resolved? | **No — G-1, G-2, G-3, G-4, G-6, G-8 remain owner decisions; G-7 is a scope change this task applied** | §10 |

Two findings are **new** in this task and matter more than anything else in it:

1. **B-12 — the live demo *administrator* password is already published.** It sits verbatim in two
   **tracked** files that are in `HEAD` (and therefore in `origin/main`), and in one untracked
   security report. The previous report's sentence "the tree contains no live credential in any
   tracked file" is therefore **wrong for demo *user* passwords** — it is true only for the
   *infrastructure* credential (§6.4, §6.5, K-7). This cannot be un-published by scrubbing the working
   tree; it needs an owner decision (G-8).
2. **Five** owner-controlled, tracked documents carry uncommitted edits — not one as previously
   recorded (§5.2, K-8). A `docs/architecture/` or `docs/product/` directory-scoped `git add` would
   publish four of them without approval. G-6 is raised for that.

The audit also found that the old C-1…C-6 plan **left three path groups unassigned**
(`README.md`, `docker-compose.yml`, all of `ai_factory/**`). The plan is therefore re-issued as
**C-1…C-7** with explicit path lists (§11, K-9). Nothing about the technical readiness changed:
the tree is still safe to commit *if* every commit is staged by explicit path.

---

## 2. Scope, authority and boundaries

**Authorised by the task statement:** read-only verification of the repository, application of
decisions the owner has already approved, creation of this report, and the same-task update of the
documentation index.

**Explicitly not done, and not to be inferred from this report:**

- No `git add`, `git commit`, `git push`, `git merge`, `git tag`, release or deployment.
- No `git reset`, `git clean`, `git stash`, `git checkout`, `git revert`, no history rewrite, no amend.
- No application code, Docker or configuration change of any kind.
- No edit to any protected file — including the demo runbook (G-1), the demo credentials sheet (G-2),
  the two mixed-ownership frontend files (G-3), and the five owner-controlled documents with
  uncommitted edits (G-6).
- No credential rotation: `D-1` is closed and nothing discovered here re-opens it (§5.1).
- No staging "just to test the plan". The plan in §11 is paper-only.

**What this report is not:** it is not an approval. Recommendations carried forward from earlier
reports (keep the artefacts, include the images, commit whole files) remain *recommendations* until
the product owner says otherwise in so many words; §10 states, gate by gate, whether approval exists
in the repository, and nothing here infers approval from silence, from a recommendation, or from the
earlier conditional-GO verdict.

---

## 3. Documents and rules consulted in this task

Read in this session, from the repository as it stands (`.clinerules` §12 — cite what was opened):

| Document / artefact | Why |
|---|---|
| `.clinerules` (full) | Root governance: §1 precedence, §3 non-negotiables, §4 routing, §5 skills (none installed), §6 reporting, §7 evidence standard, §9 execution boundaries, §11 output location + owner-controlled list, §12 reading policy |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` (full) | Mandatory first read; the reconciliation subject of §7 |
| `docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md` (headings + §5.5, §11, §12) | The audit this task closes out: gates G-1…G-5, commit plan C-1…C-6, verdict |
| `docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md` (headings) | B-1…B-10 remediation history the current state depends on |
| `docs/audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` (headings) | The original ownership classification and the first commit grouping |
| `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` (header + status lines) | Confirming it declares itself the **approved, active** list superseding V2.0–V2.4 (§5.2) |
| Working tree, `git` object database, `.gitignore`, `docker-compose.yml`, `docker-compose.demo.yml`, `.env.example` (keys only), `frontend/next.config.js`, `backend/common/database.py`, `backend/alembic/env.py`, `backend/alembic.ini` | The verification subjects of §4, §5, §6 |

Governance documents named by `.clinerules` §4 for the domains this task touches (documentation
governance, audit/reporting, deployment/credentials) were reached through the index and the two audit
reports above. The business-rules and multi-tenant documents were **not** re-read, because no
business behaviour is in scope — stated explicitly rather than implied.

**Skills:** none installed (`.clinerules` §5). No skill was used and none is claimed; the governance
documents were the only method material.

---

## 4. Verified repository state (authoritative for this report)

### 4.1 Identity, branch, HEAD, remotes

| Item | Value |
|---|---|
| Current branch | `hackathon-mvp` |
| HEAD | `eb87cac55824601a7f03ee08571f828755ad7b2e` |
| HEAD subject | *"I have commited agent rules, ai factory code, new UI/UX docs before using ilai to start working on the project"* |
| Local branches | `main` = `hackathon-mvp` = `eb87cac` |
| Remote-tracking refs | `refs/remotes/origin/HEAD` → `eb87cac`, `refs/remotes/origin/main` → `eb87cac` |
| Upstream for the current branch | **none** — `git rev-parse @{u}` fails; the first push must use `git push -u origin hackathon-mvp` |
| `git rev-list --left-right --count origin/main...HEAD` | `0  0` — the committed history is already published; only the working tree is unpublished |
| Remote | `origin` = `https://github.com/shomonrobie/amsdp` (fetch and push) |
| Local-only refs | `refs/cline/checkpoints/1793797844051_cpnuj/*` — never pushed, must never be pushed (`--mirror`/`--all` would carry them) |

Consequence: the pending risk in this repository is **the working tree**, not the history. The one
exception is B-12 (§6.4), which is a history fact and is therefore out of reach of any pre-push scrub.

### 4.2 Working-tree reconciliation — 204 paths

Command: `git status --porcelain -uall`. (`-uall` lists files inside untracked *directories*; the
default `-u normal` collapses them to one line per directory and under-counts.)

| Status | Count |
|---|---:|
| ` M` modified tracked | **58** |
| ` D` deleted tracked | **2** |
| `??` untracked | **144** |
| **Total** | **204** |

- **Delta against the previous audit: none, apart from the two files that audit itself wrote.**
  An mtime sweep of every untracked and modified path for anything newer than that report
  (`2026-11-11 18:33:29`) returns exactly two entries:
  `docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md` (18:42, untracked) and
  `docs/governance/AMSDP_Docs_Index_V1.0.md` (18:44, untracked — the whole `docs/governance/`
  folder has no tracked files, so the index counts under `??`, not ` M`). Nothing else appeared
  or disappeared; the 144/2/58 split is identical to the earlier figure.
- **The two deletions are a recorded migration, not data loss.** The root-level
  `AMSDP_Release_Readiness_Stage_{0,1}_…md` documents were relocated byte-for-byte into `docs/audit/`
  under owner decision O-6; their new paths are untracked, so staging old and new paths together
  records a rename rather than a delete + add.
- **Directory shape of the 204 paths** (used by §11), counted by top-level prefix and summing
  exactly to 204: `backend/` **86**, `docs/` **58** (including `docs/images/` 12), `frontend/` **38**,
  `_tools/` **8**, repository root **8** (`.clinerules`, `docker-compose.yml`,
  `docker-compose.demo.yml`, `.env.example`, `.gitignore`, `README.md`, plus the two deleted
  `AMSDP_Release_Readiness_Stage_{0,1}_…md`), `ai_factory/` **6**.
  Post-report totals are 59 `docs/` and 205 overall (§16.2).

### 4.3 Staged state

`git diff --cached --name-only | wc -l` → **0**, measured at the start of this task and again at the
end, after this report and the index update were written. No `git add` was executed at any point.

### 4.4 Paths that must stay outside the first-push scope

| Path | Reason | Gate |
|---|---|---|
| `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` | 4 dead-credential sites + 2 live demo passwords verbatim | G-1 |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | owner-controlled **R** document with an unapproved content change | G-2 |
| `frontend/pages/patients.js`, `frontend/styles/global.css` | whole-file hunks mixing authors; not separable at line level | G-3 |
| `docs/architecture/AMSDP_System_Architecture_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, `docs/AMSDP_Master_Feature_List_V2.0_Draft.md`, `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` | owner-controlled **R** documents carrying uncommitted edits | G-6 |
| `docs/security/AMSDP_M2_Security_Implementation_Report.md` | contains the live demo admin password verbatim (B-12) | G-8 |
| `_tools/*` (8 files), `docker-compose.demo.yml` | excluded by this task's instruction; §11.2 records the conflict with the earlier plan | G-7 |
| `tree.py`, `verify_llm_routing.py` | one-off investigation scripts, deliberately ignored by root-anchored `.gitignore` rules; present on disk, invisible to `git status` | — |

---

## 5. Decisions applied, and their evidence

### 5.1 D-1 — the rotated database credential (closed; re-verified, not assumed)

`D-1` was closed by the previous audit. The task required a *fresh, read-only* verification rather
than a citation, so each configuration surface was re-opened in this session:

| Surface | Verified state | Consequence |
|---|---|---|
| `backend/common/database.py` | `_default_url()` composes the DSN from `AMSDP_DB_HOST` / `AMSDP_DB_PORT` / `AMSDP_DB_NAME` and `os.environ.get("POSTGRES_PASSWORD")` (L24–34); `DATABASE_URL` prefers `AMSDP_DATABASE_URL` (L37); the no-password branch returns a **passwordless** DSN and logs a warning (L28–33) | No literal credential in source; a missing secret fails loudly at authentication instead of silently using a committed default |
| `backend/alembic.ini` | No `sqlalchemy.url` key at all. The only match for a URL is a **commented** template at L89 (`# sqlalchemy.url = driver://user:pass@localhost/dbname`) | Nothing to leak; Alembic cannot start without an injected URL |
| `backend/alembic/env.py` | L47 `url = os.environ.get("AMSDP_DATABASE_URL") or config.get_main_option("sqlalchemy.url")`, L50–51 raise with a remediation message when both are absent, L90 injects the resolved URL | Migrations use the same rotated credential and the same env contract |
| `docker-compose.yml` | L18 `AMSDP_DATABASE_URL: ${AMSDP_DATABASE_URL:-postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD:?missing - set it in .env, see .env.example}@db:5432/amsdp}`, L41 `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?…}` | `${VAR:?message}` fails closed; no default credential can survive into a container |
| `.env` (gitignored) | Read-only access to key names and value **lengths** only; the live DB password is 32 characters; its SHA-256 prefix is `3cadaa05cf87` | Nothing printed, nothing copied |
| `docker compose config --quiet` (with `.env` loaded) | exit **0** | The whole stack interpolates with the rotated credential — the compose file is valid *and* resolvable today |
| `docker compose -f docker-compose.yml -f docker-compose.demo.yml config --quiet` | exit **0** | The demo overlay is valid **only** when composed with the base file; on its own it fails with *"service organization has neither an image nor a build context"* (expected overlay semantics, recorded because §11.2 excludes that file) |

**Verdict on D-1:** closed, and independently re-verified on this tree. The application, the database
layer and the Alembic chain all take the credential from the environment; none carries a literal.

### 5.2 Documentation governance — V2.5 active, earlier versions historical, and a correction

- `docs/AMSDP_Master_Feature_List_V2.5_…md` states in its own header: *"Document status: **APPROVED
  MASTER FEATURE LIST — ACTIVE VERSION**"*, *"Supersedes: All prior AMSDP Master Feature List
  versions, including V1.x, V2.0, V2.1, V2.2, V2.3 and V2.4"*, *"V2.5 is the sole active Master
  Feature List. Older versions are historical records only."* The index registers it as **R**
  (read-only, owner-controlled) and describes it as the active list — verified in §7.
- V2.4 and V2.3 remain in the tree and in the index as historical/superseded. None was deleted,
  renamed or rewritten by this task.
- **Correction (K-8):** the owner-controlled tracked set is larger than previously recorded. The
  earlier report flagged **one** owner document with an uncommitted change (the credentials sheet,
  G-2). There are **five**:

| Owner document | Diff | Nature of the uncommitted edit |
|---|---:|---|
| `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` | +78 / −3 | owner product positioning (patient-facing value, waiting reduction) |
| `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` | +118 / −11 | superseded draft; substantial additions |
| `docs/architecture/AMSDP_System_Architecture_V1.0.md` | +63 / −11 | architecture narrative additions |
| `docs/product/AMSDP_MVP_SCOPE_V1.0.md` | +40 / −0 | approved-scope additions (two-stage notifications, DQDS/PQT boundaries) |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | +1 / −1 | API base port 8100 → 8110 (G-2) |

  Total: **300 insertions, 26 deletions across five files** (`git diff --numstat` per path; the five
  rows sum to exactly 300/26, so no sixth owner document is hiding outside this list). These are
  substantive owner-authored
  content changes, not mechanical cross-reference fixes. `.clinerules` §11 makes these documents
  read-only for the agent; none was modified by this task. What is *also* true is that committing
  them is an act of publication the owner has not approved — hence **G-6**. A directory-scoped
  `git add docs/product` or `docs/architecture` would sweep them in silently; §11.1 therefore names
  every path.
- No document was written to `ai_factory/docs/` (checked: the three untracked files there are
  pre-existing AILI reports, not this task's output).
- This report is the only new document this task created, and the index was updated in the same
  task, as `.clinerules` §11/§12 require.

### 5.3 AI Factory artefacts — preserved, untouched

| Artefact | Tracked? | Working-tree state |
|---|---|---|
| `runs/RUN-20261105T130533-001.json` | yes (in history) | **unmodified** (`git status --porcelain -- runs var backups` is empty) |
| `var/tasks/AMSDP-000001.json` | yes (in history) | **unmodified** |

The ignore rules that protect *new* artefacts are intact in the working `.gitignore`
(L46–52: `/runs/`, `/var/`, `/backups/`, with the explanatory comment naming these two tracked
exceptions). The full `.gitignore` diff adds only: `nohup.out`, the three root-anchored directory
rules, and two root-anchored file rules (`/tree.py`, `/verify_llm_routing.py`). **No broad pattern
was added** — nothing that could hide legitimate source under a subdirectory. `D-3`'s recommendation
(keep) is unchanged and **still awaiting explicit owner confirmation** (G-4).

### 5.4 Images — approved for eventual inclusion, deliberately not staged

The owner's approval is recorded in the task statement ("approved eventual inclusion of the 12
supplied image assets"). It covers *inclusion*, not *staging in this task*: nothing was added to the
index. Verification of the twelve assets, with hashes, is §8.

---

## 6. Credential and secret scan

### 6.1 Method

- **Population:** every tracked file (`git ls-files`, 258) plus every untracked, non-ignored file
  (`git ls-files --others --exclude-standard`, 144) = **382 candidate files**. Excluded from the
  population: `.env` and `.env.local`-style local secret files (never read into evidence), binary
  extensions (images, fonts, archives, `*.pyc`), and the ignored artefact trees
  (`runs/`, `var/`, `backups/`, `node_modules/`).
- **Patterns:** (1) URL/DNS with an inline password (`scheme://user:<value>@`), (2) secret-keyword
  assignment (`password|passwd|pwd|secret|token|api_key|private_key` + `:`/`=` + value),
  (3) PEM private-key blocks, (4) provider token shapes (`ghp_`, `sk-`, `AKIA`, `xox*-`),
  (5) JWT literals (`eyJ…`).
- **Classification:** every hit was re-read with the matched value replaced by `***` and with every
  live `.env` value masked, so classification happened without a single secret reaching the terminal
  or this document.
- **Provenance:** for the values that mattered, SHA-256 equality against (a) the current
  `POSTGRES_PASSWORD` and (b) each `AMSDP_DEMO_PASSWORD_*` value, and against the tokens of the
  owner-controlled credential sheet. Equality was printed as a boolean/label, never as a value.
- **History check:** for the files that carried a live value, both the working-tree copy and
  `git show HEAD:<path>` were tested, to separate "about to be published" from "already published".

### 6.2 Results — 45 hits across 27 files

| Classification | Files | Hits | Detail |
|---|---:|---:|---|
| **Real — dead credential in an untracked demo document (B-11)** | 1 | 4 | `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` L30, L68, L70 (DSN) and L191 (`PGPASSWORD=…`) — all the same 18-character **historical** value |
| **Real — live demo *user* password already in history (B-12, new)** | 2 | — | `frontend/pages/index.js`, `ai_factory/tests/unit/test_tools_analysis.py` — both **tracked, unmodified, present in `HEAD`** |
| **Real — live demo *user* password in an untracked document (B-12, same value)** | 1 | — | `docs/security/AMSDP_M2_Security_Implementation_Report.md` |
| Environment-expression / placeholder — no value | 4 | 6 | `.env.example` L25/L29 (`REPLACE_ME`), `backend/common/database.py` L27/L34 (`os.environ`, f-string with a variable), `backend/alembic.ini` L89 (commented template), `docs/deployment/AMSDP_M8_…` L163 (`user:password@…` placeholder) |
| Documents *describing* the pattern | 3 | 4 | `docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md` L40/L141, `docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md` L216, `docs/audit/AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` L81 (a quoted capacity error message) |
| Test fixtures that *simulate* secrets | 2 | 9 | `ai_factory/tests/unit/test_logging_redaction.py` (fake tokens, a fake PEM block, "Using \<secret\>"); `ai_factory/tests/unit/test_tools_analysis.py` (writes a sample credential to exercise a scanner) |
| Code expressions, kwargs, annotations | 16 | 21 | `jwt.encode(payload, …)`, `get("token", "")`, `Password(String(50))`, `def _attempt(self, username, password)`, `value={f.password}`, `password: str`, `raw_token: str(32)`, `os.environ.get("OPENROUTER_API_KEY", "")`, … |

Nothing in the "code expressions" and "test fixture" rows is a credential. Two files in those rows
deserve a note rather than a defect label: `_tools/write_identity_main.py` L94/L102 is a *generator
script* containing `jwt.encode(payload, _SECRET, …)` and a `Bearer` strip — variables only; and
`frontend/lib/auth.js` L39 is a token **accessor**, not a literal.

### 6.3 B-11 — the untracked demo runbook (gate G-1, unchanged)

`docs/demo/AMSDP_Hackathon_Demo_Runbook.md` is **untracked (`??`) and not staged**. Verified
locations, values never reproduced:

| Line | Kind | Value length | Matches the current DB password? |
|---:|---|---:|---|
| L30 | `AMSDP_DATABASE_URL` row with an inline DSN password | 18 | **No** |
| L68 | DSN inside a shell command (`…amsdp_demo`) | 18 | **No** |
| L70 | identical DSN, second command | 18 | **No** |
| L191 | `PGPASSWORD=<value>` | 18 | **No** |

In addition the file contains **two live demo *user* passwords** verbatim — the organization-admin
and receptionist accounts (identified by hash equality with `AMSDP_DEMO_PASSWORD_ORG_ADMIN` and
`AMSDP_DEMO_PASSWORD_RECEPTIONIST`).

Mitigation status, verified not assumed: the file has never been committed; the four infrastructure
values are **dead** (rotation removed them; the 32-character current value appears in **none** of the
382 files); the two user passwords are **live** (those accounts work today). A blind `git add -A`
would publish the live pair. This task did not edit the document: it is a demo document whose wording
is the owner's call, and the task forbids editing owner-owned documents without approval.
**G-1 remains open.**

### 6.4 B-12 — a live demo password is already in published history (new finding)

This is the finding the earlier audits did not have, because they scanned for *assignments* rather
than testing whether the live values are present:

| File | Tracked? | Working tree | In `HEAD` (`origin/main`)? | Which live value |
|---|---|---|---|---|
| `frontend/pages/index.js` | **yes** | **clean** (no modification) | **yes** | `AMSDP_DEMO_PASSWORD_ADMIN` |
| `ai_factory/tests/unit/test_tools_analysis.py` | **yes** | **clean** | **yes** | `AMSDP_DEMO_PASSWORD_ADMIN` |
| `docs/security/AMSDP_M2_Security_Implementation_Report.md` | no (`??`) | untracked | no | `AMSDP_DEMO_PASSWORD_ADMIN` |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | yes | modified (G-2) | yes (all six) | all six demo user passwords |

Why this is a *different* class from a pre-push blocker:

1. **Nothing can be done about it by staging decisions.** The value is in `eb87cac`, which is the
   published `origin/main`. Removing it from a future commit does not remove it from history; only a
   history rewrite (explicitly forbidden here, and destructive on a published branch) would.
2. **It may be intentional.** `frontend/pages/index.js` is the login page; a hackathon demo that
   prefills credentials on-stage is a legitimate design, and the owner-controlled credential sheet is
   already tracked, which signals that demo *user* passwords are treated as public demo material.
3. **It still contradicts a sentence in the previous report**, which said the tree contains no live
   credential in any tracked file. That sentence is only true for the infrastructure credential. It is
   corrected in K-7 rather than quietly dropped.

**What is *not* tolerated** is extending the exposure: the untracked `docs/security/AMSDP_M2_…md`
carries the same value and is registered in the documentation index, so it will eventually be
committed unless it is handled. It is excluded from every commit in §11 until the owner decides
(**G-8**).

### 6.5 Does the *current* database credential appear anywhere? No.

| Test | Result |
|---|---|
| Files (of 382) containing the current 32-character `POSTGRES_PASSWORD` verbatim | **0** |
| Files containing the 18-character historical value | 1 — the untracked runbook (B-11), 4 sites |
| Files containing any current `AMSDP_DEMO_PASSWORD_*` value | 4 — §6.4 (two tracked, one untracked doc, one owner credential sheet) |
| `.env` | present, gitignored, never read for values — only key names and lengths |

So the *infrastructure* secret is clean everywhere outside `.env`, and the *demo user* secrets are
public by design except in one uncommitted security report. That is the accurate picture, and it is
the one the owner should decide on.

### 6.6 Scanner-false-positive discipline

Two earlier scanner claims are re-tested here and remain **false**, with the current tree as evidence
rather than memory: the "length-8 second credential" in the Compose files (an artefact of reading
nested `${…}` expansions as values — a targeted length-8 scan returns nothing), and the notion that
the runbook's dead value was ever in `origin/main` (it is in an untracked file only; §4.1 shows the
history is `origin/main == HEAD == eb87cac`). No new false positive was carried into this report: each
row of §6.2 was read, masked, and classified individually.

---

## 7. Documentation integrity

Command basis (read-only): count `docs/**/*.md`, extract every `*.md` token from the index, compare
the two sorted name sets with `comm`.

| Check | Result |
|---|---|
| Markdown documents on disk under `docs/` | **55** (before this report) |
| Documents registered in the index | **55** |
| **On disk, not indexed (orphans)** | **none** |
| **Indexed, not on disk (phantoms)** | **none** — the only index-only names are the **5** AI-Factory reference documents (`architecture.md`, `operations.md`, `permissions.md`, `workflows.md`, `README.md`) that owner decision O-1 registers as *deliberately* out-of-tree in `ai_factory/docs/`. Arithmetic closes exactly: 56 in-tree + 5 out-of-tree = 61 registered names |
| `docs/AMSDP_Master_Feature_List_V2.5_…md` registered | **yes** — index L87, size 129,129 B, flagged **R**, described as *"The active fe[ature list]"* |
| V2.4 / V2.3 registered as historical | yes — V2.4 **R** superseded, V2.3 relabelled historical in Revision 6 |
| Audit/remediation reports registered | yes — **10** rows in `audit/` after this task (9 before it), i.e. every markdown file in that folder including the three pre-push documents and this report |
| `docs/testing/`, `docs/operations/` absent from disk | **consistent, not drift** — the index describes both as *"created when first needed"* (L76–77); `docs/decisions/` exists and is empty |
| Reviewable subfolder sizes | `architecture/` 5 · `audit/` 9 → **10** · `demo/` 4 · `deployment/` 2 · `governance/` 6 · `implementation/` 11 · `product/` 6 · `security/` 1 · `images/` 12 files |

After this report and the index update, the reconciliation was re-run and returns **56 in-tree documents,
56 registered** — 0 orphans and 0 phantoms, with the 5 out-of-tree AI-Factory names accounted for
(§16.2 records the post-change verification). **No protected document was
edited to make the audit pass**; the only file changed for index reasons is the index itself, which
`.clinerules` §12 obliges the agent to keep current.

---

## 8. Image integrity — the twelve owner-approved assets

Verified on disk with `find` + `wc -c` + `sha256sum`; hashes below are the evidence, and nothing here
is secret material.

| # | Path | Bytes | SHA-256 |
|---:|---|---:|---|
| 1 | `docs/images/doctors images/doctor-group-1.jpeg` | 60,809 | `3eb299531b4a7fa3a652b5f2c03687f2a3dc8c2e16e5541fb1aed0edce0dbe49` |
| 2 | `docs/images/doctors images/doctor-group-2.jpeg` | 76,866 | `85a5f296e80889aa568765d5d7441a1c36c1cc1e1495164a8b75211497aaa007` |
| 3 | `docs/images/doctors images/doctor-group-3.jpeg` | 67,381 | `a5fc80cc2bd3a88fe011794ada5460f68865b0763346741802acd6020cd763db` |
| 4 | `docs/images/doctors images/doctor-group-4.jpeg` | 76,387 | `3687b155c0bd93ca36bdc9b24f65fc0d15d5c1618257031aca44916b50984ff8` |
| 5 | `docs/images/doctors images/doctor-group-5.jpeg` | 64,246 | `035b3e746101d34ad002db36485939d33724e0bf604cdc6349157f2eb0eeb6c8` |
| 6 | `docs/images/doctors images/doctor-group-6.jpeg` | 52,616 | `d76a65db5810842136bae359f485633b1b1842703a932af13cefa4475206d3dc` |
| 7 | `docs/images/example dashboards/booking_dashboard_1.webp` | 65,934 | `970217ba3e2dbb95c5132ce1c8e0be9dec036a781dbfb80a60f7193383d81a71` |
| 8 | `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-24.png` | 56,756 | `bd267525fb156a87de7bae918a78c3dbe9d649e2c6284879093b98ee643c8269` |
| 9 | `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-36.png` | 78,761 | `c0b187ce5e5522f0825d7e880e5b135a683693205478b3346f5d4817186f1150` |
| 10 | `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-44.png` | 48,099 | `082937948a3f091d009e589c2d208fa18d6313694714e1755f326d2170359d14` |
| 11 | `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-51.png` | 124,477 | `6a92f2bb77eb9ea40afef8444f7e369b062a6b66c8f2dfced8ede57b95c900fa` |
| 12 | `docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-56.png` | 65,070 | `7abc717014908cefd9a4af7185e05343380f8ccaa7797a8c53c2a5e6fe0e394b` |

| Integrity check | Result |
|---|---|
| File count | **12** — exactly the approved set |
| Distinct SHA-256 count | **12** — no duplicate or truncated copy |
| Total size | **837,402 B (≈ 817.8 KiB)** |
| Tracked in Git | **0** — all twelve are untracked |
| Ignored by `.gitignore` | **0** — `git check-ignore docs/images/*` returns nothing, so `git add docs/images` would stage exactly these twelve |
| Unrelated asset inside `docs/images/` | **none** |
| Directory names containing spaces (`doctors images/`, `example dashboards/`) | **present** — the staging command must quote them or use the directory form; `.clinerules` §9 git-safety applies |

Nothing was staged (G-5's approval covers inclusion, and the inclusion happens in C-7 — §11).

---

## 9. Test evidence — actually executed in this task

| Suite | Exact command | Result | Duration |
|---|---|---|---|
| Backend | `cd backend && set -a; . ../.env; set +a; ../.venv/bin/python -m pytest -q` | **289 passed, 0 failed** (134 warnings) | 263.11 s |
| Frontend | `cd frontend && npm test` → `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs` | **43 pass, 0 fail** (0 skipped, 0 todo) | 1.40 s |
| Compose (base) | `docker compose config --quiet` with `.env` loaded | exit **0** | — |
| Compose (base + demo overlay) | `docker compose -f docker-compose.yml -f docker-compose.demo.yml config --quiet` | exit **0** | — |
| Compose (demo overlay alone) | `docker compose -f docker-compose.demo.yml config --quiet` | exit **1** — *"service organization has neither an image nor a build context"* | — |

**Environmental limitation, recorded rather than hidden.** The backend suite is **not** environment-
free: it needs the database credential. Running it without the environment
(`cd backend && ../.venv/bin/python -m pytest -q`, no `.env` loaded) produces **7 collection errors**,
all of the form `connection to server at "127.0.0.1", port 5433 failed: fe_sendauth: no password
supplied`. That is not a code defect — it is `database.py` failing closed as designed (§5.1). The 289-pass
run loaded `.env` with `set -a; . ../.env; set +a`, which exports `POSTGRES_PASSWORD` to the child
process. The value never entered the terminal, this report, or any artefact.

The stack itself was healthy during the run: nine `amsdp-*` containers `Up 5 hours (healthy)` including
`amsdp-db-1` on `5433` and `amsdp-identity-1` on `8110→8000`.

**Not run, and therefore not claimed:** no browser/E2E pass, no `next build`, no load or performance
test, no penetration test. The previous audits' browser observations are cited as their evidence, not
as mine (`.clinerules` §7).

---

## 10. Gate status — G-1 … G-8

No recommendation is treated as approval. "Unresolved" below means *no owner statement exists in the
repository*, regardless of how sensible the recommended action is.

| Gate | Subject | Status | Evidence / why |
|---|---|---|---|
| **G-1** | Scrub (or exclude) the untracked demo runbook | **OPEN — unresolved** | §6.3. 4 dead-credential sites (L30, L68, L70, L191) + 2 live demo passwords. File untracked, not staged, excluded from C-7 until scrubbed. No edit made — wording is the owner's call |
| **G-2** | Commit the 1-line `docs/demo/AMSDP_Demo_Credentials_V1.0.md` change (8100 → 8110) | **OPEN — but the endpoint is now verified as correct** | Doc L6 reads `http://localhost:8110 (Identity Service)`; `docker-compose.yml` L56 publishes identity as `8110:8000`; the string `8100` exists **nowhere** in the repository except in audit-report prose. So 8110 is right and 8100 was wrong. Approval to *commit* the change is still absent → unresolved |
| **G-3** | Commit `patients.js` and `global.css` whole | **OPEN — unresolved** | Re-verified this task: `frontend/pages/patients.js` is **+49 / −62 in a single hunk**; `frontend/styles/global.css` is **+135 / −16 in a single hunk**. Neither can be split by line without reconstructing the file. `AppShell` is imported by **11** page files, so holding `AppShell.js` back to isolate the CSS/patients work would break those pages. Recommendation (Option A: commit whole, message states the Cline/owner mix) stands; approval does not exist |
| **G-4** | Keep the two tracked AI-Factory artefacts | **OPEN — recommendation keep** | §5.3: both present, tracked, unmodified; ignore rules intact; no new broad pattern. Default is "keep" because nothing is broken; the owner's explicit confirmation is still missing |
| **G-5** | Include the 12 image assets | **APPROVED for eventual inclusion — not staged** | Task statement §2.D records the owner's approval; §8 verifies exactly 12 files, 12 distinct hashes, 837,402 B. Staging happens only in C-7 |
| **G-6** | Publish the **five** owner-controlled documents with uncommitted edits | **NEW — OPEN, unresolved** | §5.2, K-8. +300/−26 across concept note, V2.0 feature-list draft, system architecture, MVP scope and the credentials sheet. Four of them are inside directories the old C-1 covered by wildcard; §11.1 names paths instead |
| **G-7** | First-push scope for `_tools/*` and `docker-compose.demo.yml` | **NEW — exclusion applied by instruction; owner confirmation wanted** | The task requires both to stay out of this push, while the previous plan's C-2 explicitly included them (after remediation made them credential-free — verified: the scan found no literal in either). Conflict recorded in §11.2; the instruction wins for now. Nothing is lost by deferring them |
| **G-8** | Live demo **admin** password already published (B-12) + one untracked report carrying it | **NEW — OPEN, unresolved** | §6.4. Decision needed: accept as public demo material (and scrub `docs/security/AMSDP_M2_…md` before it is ever committed), or rotate the demo admin password and update `frontend/pages/index.js` + the credential sheet + the seed together. Not a pre-push blocker for C-1…C-7 as scoped, because the affected paths are excluded |

---

## 11. Proposed commit plan — C-1 … C-7 (path-level, not executed)

### 11.1 The plan

Rules applied throughout: **no `git add -A`, no `git add .`, no `git commit -a`**; every path is
either named or is a directory whose *entire* content is verified below to be in scope. Order keeps
components before the pages that import them.

**C-1 — `chore(governance): add the agent rules and the AMSDP documentation set`**

Include (union of the tracked-modified and untracked entries):

- `.clinerules`
- `docs/governance/AMSDP_Docs_Index_V1.0.md`, `…_Docs_Inventory_and_Migration_Manifest_V1.0.md`,
  `…_Docs_Output_Policy_Verification_Report_V1.0.md`, `…_Engineering_Governance_Assessment.md`,
  `…_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md`, `…_Skill_Routing_Architecture.md` — 6
- `docs/audit/` — all **10** untracked files (the 9 pre-existing ones, including the two relocated
  documents, plus this report), staged together with the two deleted root paths so Git records a rename
- `docs/implementation/` — all 11 files
- `docs/deployment/AMSDP_M8_Cloud_Deployment_Architecture.md`,
  `docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` — 2 (new, formerly unassigned)
- `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`,
  `docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md`,
  `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`,
  `docs/product/AMSDP_Product_Positioning_V1.0.md` — 4 **named**, not `docs/product/*`
- root feature/business lists: `docs/AMSDP_Business_Rules_V1.1.md`, `docs/AMSDP_MVP_SCOPE_V1.1.md`,
  `docs/AMSDP_Master_Feature_List_V2.1_…md`, `…V2.2_…md`, `…V2.3_…md`, `…V2.4_…md`, `…V2.5_…md` — 7
- the two deletions: `AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md`,
  `AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md`

Exclude from C-1: `docs/architecture/*` (its only changed file is the G-6 owner document),
`docs/product/AMSDP_MVP_SCOPE_V1.0.md` (**G-6**), `docs/AMSDP_Master_Feature_List_V2.0_Draft.md`
(**G-6**), `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` (**G-6**),
`docs/demo/*` (**G-1/G-2**), `docs/security/*` (**G-8**).

**C-2 — `chore(infra): environment-driven credentials and the documented env contract`**

Include: `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`.

Exclude: `docker-compose.demo.yml` and `_tools/*` (**G-7**, §11.2); `tree.py`, `verify_llm_routing.py`
(ignored one-off scripts, deliberately not in Git).

**C-3 — `feat(backend): multi-service identity, org, patient, doctor, scheduling, queue, audit`**

Include: `backend/app/main.py`, `backend/conftest.py`, `backend/common/**` (19 files incl. the
`notifications/` package), `backend/alembic.ini`, `backend/alembic/README`, `backend/alembic/env.py`,
`backend/alembic/script.py.mako`, `backend/alembic/versions/*.py` (9 migrations),
`backend/identity/**`, `backend/organization/**` (incl. `notification_config.py`),
`backend/patient/**`, `backend/doctor/**`, `backend/scheduling/**`, `backend/appointment/**` (incl.
`dashboard.py`, `tracking.py`), `backend/queuing/**` (incl. `display.py`, `recovery.py`),
`backend/audit/**`, `backend/seed/**`, `backend/tests/**` (9 files).

Exclusions: **none** — the credential scan returned no literal in any backend path (§6.2), and
`common/database.py` was re-verified line by line (§5.1).

**C-4 — `feat(frontend): shared shell and application pages`** *(gate G-3)*

Include: `frontend/next.config.js`, `frontend/package.json`, `frontend/components/AppShell.js`,
`frontend/components/ui/{Alert,ConfirmDialog,DataTable,Modal,StatusBadge}.js`,
`frontend/lib/auth.js`, `frontend/lib/i18n.js`, `frontend/pages/_app.js`, `…/audit.js`,
`…/branches.js`, `…/notifications.js`, `…/orgs.js`, `…/staff.js`, `…/queue-display/[org]/[branch].js`,
`…/track/[token].js`, `…/appointments.js`, `…/dashboard.js`, `…/doctors.js`, `…/queue.js`,
`…/schedules.js`, `frontend/styles/global.css`, `frontend/pages/patients.js`.

Gate: `patients.js` and `global.css` go in **whole** (one hunk each, §10/G-3). Hold this commit until
G-3 is answered; if the answer is "hold back", drop those two paths and let C-4 carry the rest — the
11 AppShell pages stay internally consistent because `AppShell.js` is in the same commit.

**C-5 — `feat(frontend): BanglaNameSense patient-name suggestion`**

Include: `frontend/components/BanglaNameSense.js`, `frontend/data/README.md`,
`frontend/data/bangla_name_sense.json`,
`frontend/lib/bangla-name-sense/{controller,dataset,matcher,normalize,validate-dataset}.js`,
`frontend/scripts/validate-bangla-name-sense.mjs`,
`frontend/tests/banglanamesense-{controller,dataset,integration,matcher}.test.mjs` — the 43 passing tests.

Exclusions: none. The commit message must not claim it adds the patient-page wiring (C-4 carries it).

**C-6 — `chore(ai-factory): execution fixes and AILI reports`** *(new — the old plan left these unassigned)*

Include: `ai_factory/src/amsdp_ai_factory/execution/build_crews.py`,
`ai_factory/src/amsdp_ai_factory/execution/live.py`,
`ai_factory/tests/unit/test_live_executor.py`,
`ai_factory/docs/AILI_Independent_Verification_Report_V2.0.0.md`,
`ai_factory/docs/AILI_Phase4_Repair_and_Assessment_Report_V1.0.md`,
`ai_factory/docs/AILI_Structured_Output_Investigation_Report_V1.0.md`.

Note: these documents stay in `ai_factory/docs/` (owner decision O-1); committing them records them
*where they are*, it does not relocate them. `test_tools_analysis.py` is **not** in this commit — it is
already tracked and needs no change (and still carries B-12's value, untouched).

**C-7 — `docs(demo): add demonstration assets`** *(gates G-1, G-2, G-5)*

Include: `docs/images/**` — exactly the 12 files of §8 (quote the two directory names containing
spaces).

Conditionally include, only on the named approval: `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`
(after **G-1** scrub, re-scanned and clean), `docs/demo/AMSDP_Demo_Credentials_V1.0.md`
(after **G-2** approval).

Never in this commit: `docs/security/AMSDP_M2_Security_Implementation_Report.md` (**G-8**).

### 11.2 Reconciliation of the old plan against the tree — what changed and why

| # | Finding | Consequence for the plan |
|---|---|---|
| K-9 | The old C-1…C-6 **assigned no commit** to `README.md`, `docker-compose.yml`, or any of the 6 `ai_factory/**` paths | C-2 now carries `docker-compose.yml` + `README.md`; **C-6 is new** for `ai_factory/**`. Without this, 8 paths would be left behind and the tree could never reach a clean `git status` |
| K-10 | The old C-1 used **directory wildcards** (`docs/product/*`, `docs/architecture/*`) | Those wildcards sweep in four G-6 owner documents. C-1 names paths instead; `docs/architecture/` is excluded entirely because its only changed file is the owner document |
| K-11 | `_tools/*` and `docker-compose.demo.yml` were **included** in the old C-2 | This task excludes them (**G-7**). The conflict is stated rather than hidden, and the instruction is followed. Nothing is lost: both are credential-free (verified in §6.2), so they can travel later in one small commit of their own |
| K-12 | `docs/deployment/` was in **no** earlier commit | Added to C-1 (2 files, both new documents the index already registers) |
| K-13 | The 12 images were bundled with the runbook | C-7 keeps them together but makes the images **unconditional** and the two demo documents conditional, so G-1/G-2 can no longer hold the assets hostage |

### 11.3 Pre-flight checklist for whoever executes the plan

1. `git diff --cached --name-only` → empty before starting; this is the standing `staged=0` invariant.
2. `git status --porcelain -uall | wc -l` → **205** expected: the 204 of §4.2 plus this report (§16).
3. Re-run the §6.3 scan and require **0 live-value hits** before C-7's runbook path is staged.
4. Record the G-2 / G-3 / G-6 / G-8 answers in the repository (a decisions document) **before**
   staging the paths they govern — an approval that exists only in chat cannot be audited later.
5. After every `git add`: `git diff --cached --stat`, then re-run the five scan classes of §6.1
   against the **index** rather than the working tree.
6. Never `git commit -a`; never amend `eb87cac`; never `git push --all` / `--mirror` — that would
   publish the `refs/cline/*` scratch refs (§4.1).
7. Push with `git push -u origin hackathon-mvp`; the branch has no upstream today.

### 11.4 What the plan does **not** do

It does not stage, commit, push, branch, tag, amend, rebase, reset, clean or stash. It does not touch
`.env`. It does not modify any owner-controlled document. Every path decision above is a
recommendation awaiting the owner; with G-2, G-3, G-6 and G-8 unanswered, C-4 and C-7 are not
executable in full, and C-1 is executable only in the named-path form written here (not in the old
wildcard form).

---

## 12. Findings and corrections register

### 12.1 Blocking findings carried forward

| ID | Severity | Finding | Gate |
|---|---|---|---|
| **B-11** | High | Untracked demo runbook holds 4 dead-credential sites + 2 **live** demo user passwords | G-1 |
| **B-12** | Critical (publication state) / informational (this push) | Live demo **admin** password is already in `origin/main` via two clean tracked files, and in one untracked security report | G-8 |
| **K-8** | High | Five owner-controlled tracked documents carry uncommitted owner edits; wildcard staging would publish them | G-6 |

### 12.2 Corrections to the earlier audit record

| ID | Earlier claim | Corrected position | Evidence |
|---|---|---|---|
| **K-7** | "No live credential appears in any tracked file in the tree." | True only for the **infrastructure** credential. A live **demo user** password is in `frontend/pages/index.js` and `ai_factory/tests/unit/test_tools_analysis.py`, both clean and committed | §6.4 |
| **K-8** | One owner-controlled document has an uncommitted change (the credentials sheet). | **Five** do: +300/−26 | §5.2, §10/G-6 |
| **K-9** | The commit plan accounted for all 204 changed paths. | It did not: `README.md`, `docker-compose.yml`, and 6 `ai_factory/**` paths had no assigned commit | §11.2 |
| **K-10** | C-1 is `git add docs/` (wildcard). | Wildcards would publish four owner documents; the plan now names paths | §11.1, §11.2 |
| **K-11** | `_tools/*` and `docker-compose.demo.yml` belong in the first push. | Credential-free (verified), but excluded by this task's instruction → G-7 | §11.2 |
| **K-12** | `docs/deployment/` needs no commit. | Two new documents there were unassigned; added to C-1 | §11.2 |

### 12.3 Null results, recorded so they are not re-investigated

- The scanner's "length-8 second credential" in the Compose files: **not reproducible**; a targeted
  length-8 scan of `docker-compose*.yml` returns nothing. It was an artefact of parsing `${…}`.
- The runbook's historical password was **never** in `origin/main`; the file is untracked (§4.1, §6.3).
- `docs/testing/` and `docs/operations/` missing from disk: **not drift**; the index documents them as
  future folders (§7).
- `tree.py` and `verify_llm_routing.py` appearing "missing" from `git status`: **by design**; root-
  anchored ignore rules, deliberate (§5.3).
- `D-1` reopened: **no regression**; every surface re-verified in §5.1.
- Alembic `/backend/alembic/README` (no extension) being untracked: **correct to commit**; it is the
  standard Alembic readme, not a stray file (C-1/C-3).

---

## 13. Residual risks

| Risk | Likelihood | Impact | Mitigation in this plan |
|---|---|---|---|
| A future `git add -A` publishes B-11's two live demo passwords | Medium | High | Excluded from every commit; G-1 requires a scrub *and* a re-scan before C-7 |
| An owner document is published by a wildcard `git add` | Medium | High (owner-authored content, irreversible in history) | C-1 names paths; a pre-flight `git diff --cached --name-only` review is mandatory (§11.3) |
| The demo admin password stays public after the push | Certain (already public) | Medium — accepted risk if the owner says the demo is disposable | G-8 asks for an explicit decision, and for the untracked M2 report to be scrubbed before it is ever committed |
| Push is done with `--all`/`--mirror`, publishing `refs/cline/*` | Low | Medium | §11.3 step 6 forbids it; push command is given explicitly |
| A stale frontend test count is cited later | Low | Low | §9 records the exact command and the 43/289 numbers |
| Images arrive truncated or duplicated | Low | Low | 12 files / 12 distinct hashes / 837,402 B recorded (§8) for comparison after staging |
| The backend suite is run without `.env` in CI and 7 collection errors are mistaken for failures | Medium | Medium | §9 records the cause (fail-closed credential design) and the exact working command |

---

## 14. Verdict

**CONDITIONAL GO.**

The repository is in a pushable *technical* state: no infrastructure credential anywhere outside
`.env`, the compose stack resolves, 289 backend and 43 frontend tests pass in this tree, the
documentation tree is complete and indexed, and the twelve approved images are intact. D-1 is closed
and independently re-verified rather than cited.

It is **not** an unconditional GO, because four decisions are the owner's alone and none of them
exists in writing:

1. **G-1** — the demo runbook still holds two **live** demo passwords, and it is one `git add -A`
   away from publication.
2. **G-6** — five owner-controlled documents carry uncommitted owner edits; publishing them is a
   product decision, not a technical one.
3. **G-2 / G-3** — two small, low-risk commits (a one-line port fix; two whole-file frontend changes)
   need approval before C-4/C-7 can run in full.
4. **G-8** — a live demo admin password is *already* published; the owner must decide whether that is
   accepted demo material or a rotation task, and must not let the untracked M2 security report carry
   it into history.

With G-1, G-2, G-3 and G-8 answered, and G-6 either authorised or declined, the plan in §11 becomes
executable end to end without any further analysis. Nothing in the plan requires a code change: the
work remaining is approval, staging by explicit path, and one push.

---

## 15. Owner decisions requested

| Gate | The decision, in one line | Recommended answer |
|---|---|---|
| **G-1** | Scrub `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` — replace the 4 dead DSN/`PGPASSWORD` values with placeholders and the 2 live demo passwords with `<see credential sheet>` — or keep the file out of the first commit | Scrub, re-scan, then include in C-7 |
| **G-2** | Approve committing the one-line `8100 → 8110` change in `docs/demo/AMSDP_Demo_Credentials_V1.0.md` (the endpoint is verified correct) | Approve |
| **G-3** | Approve committing `frontend/pages/patients.js` (+49/−62, one hunk) and `frontend/styles/global.css` (+135/−16, one hunk) whole, with a message that discloses the mixed authorship | Approve (Option A) |
| **G-4** | Confirm keeping the two tracked AI-Factory artefacts `runs/RUN-20261105T130533-001.json` and `var/tasks/AMSDP-000001.json` in history | Keep |
| **G-6** | Authorise committing the four remaining owner documents (concept note, V2.0 draft, system architecture, MVP scope) as part of C-1 — or decline and leave them uncommitted | Authorise the concept note and MVP scope; leave the superseded V2.0 draft and the architecture document for a separate owner commit |
| **G-7** | Confirm `_tools/*` (8 files) and `docker-compose.demo.yml` stay out of this push | Confirm |
| **G-8** | Accept the published demo admin password as public demo material (and scrub the untracked M2 report), or rotate it in code + seed + credential sheet | Rotate after the hackathon; scrub the M2 report now; exclude it from this push either way |

---

## 16. Boundary confirmation and evidence trail

### 16.1 What this task did

| Action | Count / detail |
|---|---|
| Files created | **1** — this report |
| Files edited | **1** — `docs/governance/AMSDP_Docs_Index_V1.0.md` (index entry + revision bump, required by `.clinerules` §11/§12). It is an existing **untracked** file, so its content changed while its Git class did not — it remains `??` |
| Files deleted | **0** |
| Files staged | **0** — `git diff --cached --name-only` empty |
| Commits / pushes / branches / tags / amends / resets | **0** each |
| `.env` read for values | **never** — key names and value lengths only |
| Owner-controlled documents edited | **0** |
| Documents written to `ai_factory/docs/` | **0** |
| Scratch scripts written (outside the repo) | `/tmp/scan.py`, `/tmp/mask2.py`, `/tmp/hist_check.py` — hash/boolean only, no value ever printed |

Read-only commands used: `git status`, `git diff`, `git log`, `git ls-files`, `git show`, `git
check-ignore`, `sha256sum`, `wc`, `find`, `grep`, `comm`, `docker compose config`, `pytest`, `npm test`.
No state-changing Git command was run at any point.

### 16.2 Post-change verification (re-run after this report and the index update)

| Check | Expected after this task | Observed |
|---|---|---|
| `docs/**/*.md` on disk | 56 | 56 |
| Documents registered in the index | 56 in-tree | 56 in-tree (+5 deliberately out-of-tree AI-Factory names, 61 total) |
| Orphans / phantoms | 0 / 0 | 0 / 0 |
| `git status --porcelain -uall \| wc -l` | 205 (204 + this report) | 205 |
| Modified / deleted / untracked split | 58 / 2 / 145 | 58 / 2 / 145 |
| `git diff --cached --name-only` | empty | empty |
| Branch / HEAD | `hackathon-mvp` / `eb87cac` | unchanged |
| Backend tests | 289 passed | 289 passed |
| Frontend tests | 43 passed | 43 passed |

Verified values are recorded in §16.3; anything the tools did not confirm is marked as a limitation in
the section that discusses it rather than asserted here.

### 16.3 Evidence artefact index

| Artefact | Holds |
|---|---|
| `/tmp/t1_git.txt` … `/tmp/t27b.txt` | git identity, branch/HEAD/remotes, staged state, per-path reconciliation |
| `/tmp/status_all.txt` | full `git status --porcelain -uall`, 204 entries before this report |
| `/tmp/scan_out.txt`, `/tmp/mask_out.txt` | scanner hits and their masked classification |
| `/tmp/hist_out.txt` | `git show HEAD:<path>` comparisons for the live-value files |
| `/tmp/be_test2.txt`, `/tmp/fe_test.txt` | raw pytest and node:test output (289 / 43) |
| `/tmp/t29_owner.txt` | `git diff --numstat` for the five owner-controlled documents |
| `/tmp/t28_g3.txt` | numstat + hunk counts for `patients.js` / `global.css`, AppShell importer count |

---

---

## 17. Governance and Skill Compliance (`.clinerules` §6)

**Applicable governance documents, per the §4 routing table:**

| Domain | Routing row | Documents actually used |
|---|---|---|
| Documentation: reading, writing, placement, index maintenance | §4 row *Documentation* + §11 + §12 | `docs/governance/AMSDP_Docs_Index_V1.0.md` (read in full, then updated); `AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` (referenced for the O-6 relocation) |
| Audit / reporting / denials | §4 row *Audit* | `docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md`, `…PreCommit_Remediation_Report_V1.0.md`, `…PreCommit_Push_Readiness_Report_V1.0.md` |
| Docker / deployment / ports / infrastructure | §4 row *Docker, deployment* | `docker-compose.yml`, `docker-compose.demo.yml`, `.env.example`; `saas-cicd-workflow.md` adapted for git safety and honest CI state |
| Secrets and credential handling | §3 non-negotiables | applied directly: no value printed, SHA-256/boolean comparison only |

**Evidence the instructions were followed:**

- **§11 output location** — this report lives in `docs/audit/`, an existing subfolder, with no new
  near-duplicate folder created and no migration performed (so no manifest entry is owed).
- **§11 never-overwrite** — the destination filename was checked before writing; the file did not
  exist, so nothing was overwritten or deleted.
- **§11 owner-controlled documents** — five were *read* (permitted, §12) and none was modified,
  moved or renamed.
- **§12 read-before-plan** — the index was opened first and every document cited in §3 was actually
  opened in this session; no remembered path or remembered claim was relied on.
- **§12 index currency** — the index was updated in the same task, with a Revision 7 entry and a
  registered row (56 in-tree documents).
- **§3 non-negotiables** — no secret logged or exposed; nothing was staged, so no unreviewed path can
  reach history; denials and unresolved gates are recorded rather than swallowed (§10, §15).
- **§7 evidence standard** — every claim is labelled IMPLEMENTED / TESTED / VERIFIED where it applies:
  the test suites are **TESTED** (real runs, §9); the git counts are **VERIFIED** (independent `git`
  reads, §16.2); the credential absence is **VERIFIED** by hashes over 382 files (§6.5). No claim of
  ACCEPTED is made for anything the owner has not signed.
- **§9 execution boundaries** — read-only commands plus the two test suites; no server started, no
  state-changing Git command, no destructive command, and no file staged before checking whether it
  carried someone else's uncommitted work (K-8 exists precisely because five files do).

**Tests and verification performed, with real results:** §9 (289 backend, 43 frontend, three compose
validations) and §16.2 (56/56 documents, 205 paths, 58/2/145 split, `staged=0`).

**Deviations and exceptions:**

1. **Ownership wording.** Earlier audits described the demo runbook as an ordinary untracked file.
   This report treats it as owner-authored demo material and therefore did **not** edit it even
   though a scrub would be trivial — recorded as a deviation in favour of ownership, with G-1
   raised instead.
2. **A new finding changed the verdict's conditions.** B-12 (§6.4) is outside the scope the task
   described (a working-tree closeout), because it is a history fact. It is reported rather than
   silently excluded, and it is not treated as a blocker for the scoped plan.
3. **A scope conflict is stated, not resolved unilaterally.** `_tools/*` and
   `docker-compose.demo.yml` were in the earlier plan and are excluded by this task's instruction;
   §11.2 records both positions and G-7 asks for confirmation.

**Skills unavailable or not applicable:** `.clinerules` §5 — **no skill packages are installed** in
this workspace (verified: no `.clinerules/skills/`, `.claude/skills/` or repo `skills/` directory, no
Cline skill configuration). No skill was used, and none is claimed. The applicable alternative was the
governance-document route described above, which is what this report used.

---

**Report status:** complete. **Commit status:** nothing staged, nothing committed, nothing pushed —
pending the owner decisions in §15.

---

# 18. Step 1 close-out — owner decisions G-1…G-8 applied and verified (2026-11-12)

> **Current position.** This section supersedes the gate statuses in §10 and the path list in §11.1
> wherever they differ. §10 and §11 are left exactly as written — they record the state *before* the
> owner decided. **§18 is the governing record for Step 2.**

**Task:** `AMSDP-HACKATHON-MVP-STEP1-OWNER-DECISIONS-2026-11-12` — apply G-1…G-8, re-verify the test
suites and the secret scan, and re-issue the staging plan as an exact path list.

**State after this step:** **207** working-tree entries (62 tracked-modified, 145 untracked paths;
two of the tracked modifications are deletions whose content reappears under `docs/audit/`);
**staged = 0** (`git diff --cached --name-only | wc -l` → `0`); `HEAD` = `eb87cac`; **nothing
committed, nothing pushed.**

## 18.1 Decision register — final dispositions

| Gate | Owner decision | What was actually done | Status |
|---|---|---|---|
| **G-1** | Scrub the demo runbook | Every dead-DSN site now resolves from the environment — `AMSDP_Hackathon_Demo_Runbook.md` L30 and L69–L72 use `postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@…` after `set -a; . ../.env; set +a`, and L194–L197 pass `-e PGPASSWORD="$POSTGRES_PASSWORD"` into `psql`; the receptionist probe (L124) now sends `$AMSDP_DEMO_PASSWORD_RECEPTIONIST`; L35 and L129 document the `AMSDP_DEMO_PASSWORD_<USERNAME>` convention. The receptionist and organisation-admin password literals are gone from the file — the values are not reproduced here, only the keys that supply them | **CLOSED** |
| **G-2** | Commit the 8100 → 8110 correction | No edit was needed: the sheet already read `http://localhost:8110 (Identity Service)` (L6) and the string `8100` exists nowhere in the tree. The file's real change in this step is the **G-8** rotation edit (§18.2) | **CLOSED** |
| **G-3** | `patients.js` + `global.css` | **Defer.** Both stay modified-but-unstaged and are excluded from C-1…C-7; this push does not carry them | **CLOSED (deferred)** |
| **G-4** | Two tracked AI-Factory artefacts | **Keep** — untouched, still tracked, ignore rules unchanged | **CLOSED** |
| **G-5** | 12 image assets | **Include**, staged only in C-7 | **CLOSED** |
| **G-6** | Owner-controlled documents | **Include** `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` and `docs/product/AMSDP_MVP_SCOPE_V1.0.md`; **exclude** `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` and `docs/architecture/AMSDP_System_Architecture_V1.0.md` | **CLOSED** |
| **G-7** | `_tools/*` + `docker-compose.demo.yml` | **Excluded** from this push (9 paths: 8 scripts + 1 compose file) | **CLOSED** |
| **G-8** | Already-published demo admin password | **Rotate + scrub** — new value lives only in the gitignored `.env`; the database hash was refreshed; four files were scrubbed (§18.2); rotation verified end to end (§18.3) | **CLOSED** |

**Nothing is left open.** Every gate in §10 now has an owner decision and a recorded disposition.
The remaining constraints are *risks* (§18.9), not unanswered questions.

## 18.2 What changed in the tree during this step

| File | Change | Why |
|---|---|---|
| `.env` (**gitignored, never committed**) | `AMSDP_DEMO_PASSWORD_ADMIN` now holds the rotated value; the other five `AMSDP_DEMO_PASSWORD_*` keys are unchanged | the runtime source of every seed credential |
| `backend/seed/seed_demo.py` | new `_configured_password(username)` helper (L57–L60) returning `AMSDP_DEMO_PASSWORD_<USERNAME>` then a shared `AMSDP_DEMO_PASSWORD`; the **existing-staff** branch (L233–L235) now re-hashes `password_hash` from that value; the startup banner (L421) prints only the key convention | a rotation must be reproducible by re-running the seed, not by a one-off `UPDATE` on the demo database. No password literal exists anywhere in the script |
| `frontend/pages/index.js` | login hint (L45) reads *"password in `.env`"* instead of the old literal | last live literal in tracked frontend source |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | admin row (L14) points to `AMSDP_DEMO_PASSWORD_ADMIN` in `.env`; a rotation note (L21–L26) explains that the sheet stays the single documented place for the *other* seed accounts | G-8, and it settles the G-2 endpoint (already 8110) |
| `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` | 4 DSN/PGPASSWORD sites + the receptionist probe rewritten to environment substitution | G-1 |
| `docs/security/AMSDP_M2_Security_Implementation_Report.md` | the published admin password at L65 redacted to a reference | G-8 — defensive, because that path is *not* in this push anyway |
| `ai_factory/tests/unit/test_tools_analysis.py` | fixture literal → `EXAMPLE-NOT-A-REAL-SECRET` | the fixture must not look like a credential even though the value was synthetic |

**Seed re-run (VERIFIED, `/tmp/s34_seed.txt`, exit 0):** the script re-hashes the six demo staff rows
from `.env`, prints only usernames+e-mails, and states *"Password source: AMSDP_DEMO_PASSWORD_<USERNAME>"*.
This is what makes the rotation survive a fresh environment instead of living in a hand-edited row.

## 18.3 Rotation verification — VERIFIED

Evidence: `/tmp/s25_auth.txt` (both entry points), `/tmp/s36_auth3.txt` (all six accounts),
`/tmp/s72_verify.txt` (post-rotation API probe, no credential or token printed).

| Probe | Result | Meaning |
|---|---|---|
| `POST /api/v1/staff/login` on **:8110** (direct) with the rotated password | `200`, token issued (252 chars) | the new credential is live in the database |
| same on **:3100** (frontend proxy) | `200`, token issued | the whole demo entry path works, not just the service port |
| `:8110` and `:3100` with the **old** password | `401` | rotation is complete — the published value is dead |
| a wrong guess on `:8110` | `401` | no accidental bypass, and the throttle path is untouched |
| all six demo accounts (`admin`, `org_admin`, `br_admin`, `receptionist`, `doctor`, `assistant`) | `200` each, roles `super_admin` / `org_admin` / `branch_admin` / `receptionist` / `doctor` / `assistant` | the rotation did not disturb the other five seeds |
| `GET /api/v1/staff/users` with the rotated admin token | `200`, **512** rows | a real authenticated read succeeds after rotation |
| same call with a bogus token / with no token | `401` / `401` | access still fails closed; the UI is not the boundary |

> **One probe was wrong, and it is recorded rather than hidden.** An earlier attempt called
> `/api/v1/staff/me` and got `404` on both ports. `backend/identity/routes.py` exposes only
> `/api/v1/staff/users`, `/api/v1/staff/users/{user_id}`, `PATCH /api/v1/staff/users/{user_id}` and
> `/api/v1/staff/check-permission` — **there is no `/me` route**, so the 404 was a bad path in the
> probe, not a regression. It is therefore *not* counted as evidence either way.

## 18.4 Secret scan after the scrub — VERIFIED

Script: `/tmp/scan_secrets.py` (lives in `/tmp`, never committed). It builds its candidate list from
`git ls-files -co --exclude-standard`, so it scans **exactly the future-commit universe**, and it
compares against eight runtime-derived values (the six `AMSDP_DEMO_PASSWORD_*` values plus the two
legacy values — the pre-rotation admin password and the historic dev DSN password, both assembled at
runtime so the script itself contains neither) and five token patterns.

```
candidate_files=403  text_scanned=389  skipped_binary_or_huge=12
secret_values_checked=8  regex_patterns=5
HITS=8   (all eight classified in §18.7)
```

| Question | Answer |
|---|---|
| Does the **rotated** admin password appear anywhere? | **No** — 0 hits |
| Does the **pre-rotation** admin password appear anywhere in the future-commit set? | **No** — 0 hits (it survives only inside the stale, gitignored `frontend/.next/` build cache) |
| Does the dev database password appear anywhere? | **No** — 0 hits |
| Do any JWT, PEM, AWS or GitHub-token literals appear? | **No** — the only pattern hits are the redaction code and its synthetic fixtures |
| Any real credential in the 193 in-plan paths? | **None.** The only non-synthetic hits are four *demo-seed* passwords printed in the owner-controlled credential sheet, by design (§18.7, §18.9 R-2) |

## 18.5 Test suites re-run after the edits — TESTED

Timestamps prove ordering: `seed_demo.py` was edited at 00:47 and the backend suite ran at 01:04;
`test_tools_analysis.py` was edited at 01:09 and the AI-Factory suite ran at 01:12; the frontend
suite and the scan ran afterwards. Nothing was edited after the last run of the suite that covers it.

| Suite | Command | Result | Evidence |
|---|---|---|---|
| Backend (11 service test dirs + `backend/tests/`) | `. ./.env` then `python -m pytest backend -q` | **289 passed**, 0 failed, 142 warnings, 177.03 s, exit 0 | `/tmp/s44_backend.txt`, `/tmp/s49_btail.txt` |
| Frontend (BanglaNameSense: matcher, dataset, controller, integration) | `node --test tests/*.test.mjs` (Node v24.21.0) | **43 pass**, 0 fail, 1.04 s | `/tmp/s66_fe.txt` |
| AI Factory (`test_tools_analysis.py`, the file scrubbed for the fixture) | `PYTHONPATH=ai_factory/src python -m pytest ai_factory/tests/unit/test_tools_analysis.py -q` | **5 passed**, 1.09 s | `/tmp/s53_aitest.txt` |
| Rotation / RBAC probe | `/tmp/verify_rotated_admin.py` | login 200, staff list 200 (512 rows), bad token 401, anonymous 401 | `/tmp/s72_verify.txt` |

**Not re-run, and why:** the full `ai_factory` suite (only the one scrubbed module was affected), the
Playwright/browser E2E suite (no browser session was started — §9 execution boundaries), and the
compose-based `test_e2e.py` (already inside the 289 backend tests). No test result is claimed that was
not produced in this task.

## 18.6 Documentation updated in this step

| Document | Update |
|---|---|
| `docs/audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` | this §18 — dispositions, rotation evidence, scan results, re-issued plan |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Revision 8** entry recording the applied decisions and naming §18 as the evidence; snapshot **stays at 56 documents** (nothing created, moved or retired, so no manifest entry is owed — `.clinerules` §11) |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | admin row + rotation note (owner-approved, G-8) |
| `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` | environment-driven DSN/PGPASSWORD/probe (G-1) |
| `docs/security/AMSDP_M2_Security_Implementation_Report.md` | redaction at L65 (G-8; the path stays out of the push) |

Both demo documents live under `docs/demo/` per `.clinerules` §11, and the report under `docs/audit/`
(reusing an existing subfolder rather than creating `docs/reports/`).

## 18.7 The eight scan hits — classified, none is a real secret

| Hit | What it actually is | Verdict |
|---|---|---|
| `ai_factory/src/amsdp_ai_factory/utils/logging.py` — `private_key_block` | the *regex source* of the redaction filter (`-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----`), L51–L54 | **not a secret** — the detector matching its own detector |
| `ai_factory/tests/unit/test_logging_redaction.py` — `openai_sk` | a synthetic `sk-`-prefixed fixture string at L32 (the value is withheld here; it is not, and never was, a credential) | **not a secret** — a canned string for the redaction test |
| `ai_factory/tests/unit/test_logging_redaction.py` — `private_key_block` | synthetic PEM `…SUPERSECRETBASE64…`, L41 | **not a secret** — deliberately fake |
| `ai_factory/tests/unit/test_tools_analysis.py` — `openai_sk` | synthetic fixture in a generated temp file, L53 | **not a secret** — the fixture's own comment says so; the neighbouring live-looking value was replaced in this step |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` — 4 × `value:AMSDP_DEMO_PASSWORD_{ORGANISATION_ADMIN,RECEPTIONIST,DOCTOR,ASSISTANT}` | the *demo seed* passwords for the four non-admin roles, printed in the sheet that the owner designated as their single documented location | **by design, owner-controlled** — see R-2 |

**Conclusion: 0 real secrets in the 193 in-plan paths.** Two of the eight hits are the redaction
machinery itself, two are synthetic test fixtures, and four are demo-only credentials in the one file
that is supposed to document them.

## 18.8 Step 2 — the exact staging sequence (193 paths, not executed)

### 18.8.1 Invariants for every commit

1. **No wildcard bulk staging.** No `git add -A`, no `git add .`, no `git commit -a`, no
   `git add docs/`, no `git add backend/`. Every path below is named explicitly (directory-level
   `git add` is *not* used even where a directory is fully in scope, so an unexpected new file can
   never ride along).
2. **Read back before every commit.** `git diff --cached --name-status` must show exactly the paths
   listed for that commit and nothing else. If a path appears that is not in this section, run
   `git restore --staged <path>` and stop.
3. **One commit per group, in the order C-1 → C-7.** C-4 imports `AppShell.js` and
   `lib/{auth,i18n}.js`, so those ship in the same commit; C-5 is self-contained (its only importer,
   `frontend/pages/patients.js`, is deferred under G-3), so its order after C-4 is safe.
4. **Nothing is staged as part of Step 1.** This section is a plan: it exists so the owner can
   authorise a mechanical sequence, not so an agent can run it unattended.

### 18.8.2 Composition

| Commit | Message | Paths | Note |
|---|---|---:|---|
| **C-1** | `chore(governance): add the agent rules and the AMSDP documentation set` | **45** | includes the two root deletions so Git records the rename into `docs/audit/` |
| **C-2** | `chore(infra): environment-driven credentials and the documented env contract` | **4** | |
| **C-3** | `feat(backend): multi-service identity, org, patient, doctor, scheduling, queue, audit` | **86** | |
| **C-4** | `feat(frontend): shared shell and application pages` | **24** | `patients.js` + `global.css` withheld (G-3) |
| **C-5** | `feat(frontend): BanglaNameSense patient-name suggestion` | **13** | inert until `patients.js` ships |
| **C-6** | `chore(ai_factory): execution fixes and AILI reports` | **7** | |
| **C-7** | `docs(demo): hackathon runbook, rotated credential sheet and demo images` | **14** | 2 documents + 12 images |
| | **Total in plan** | **193** | |
| **Excluded** | not staged at all | **14** | `_tools/*` (8), `docker-compose.demo.yml`, `docs/security/*`, the two G-6 exclusions, `patients.js`, `global.css` |
| | **Working-tree total** | **207** | 193 + 14 |

The count is machine-checked: a classifier over `git status --porcelain -uall` assigns every one of
the 207 entries to exactly one bucket and reports **`UNASSIGNED: 0`** (`/tmp/step2_plan.py` →
`/tmp/s73_plan.txt`).

### 18.8.3 C-1 — governance and documentation (45 paths)

```bash
git add .clinerules \
  "docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md" \
  docs/AMSDP_Business_Rules_V1.1.md \
  docs/AMSDP_MVP_SCOPE_V1.1.md \
  docs/AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md \
  docs/AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md \
  docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md \
  docs/AMSDP_Master_Feature_List_V2.4_Modular_Healthcare_Platform_Edition.md \
  docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md \
  docs/product/AMSDP_MVP_SCOPE_V1.0.md \
  docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md \
  docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md \
  docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md \
  docs/product/AMSDP_Product_Positioning_V1.0.md \
  docs/governance/AMSDP_Docs_Index_V1.0.md \
  docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md \
  docs/governance/AMSDP_Docs_Output_Policy_Verification_Report_V1.0.md \
  docs/governance/AMSDP_Engineering_Governance_Assessment.md \
  docs/governance/AMSDP_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md \
  docs/governance/AMSDP_Skill_Routing_Architecture.md \
  docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md \
  docs/audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md \
  docs/audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md \
  docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md \
  docs/audit/AMSDP_MVP_Hackathon_Readiness_Assessment.md \
  docs/audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md \
  docs/audit/AMSDP_PreCommit_Remediation_Report_V1.0.md \
  docs/audit/AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md \
  docs/audit/AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md \
  docs/audit/AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md \
  docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md \
  docs/implementation/AMSDP_Frontend_Visual_Quality_Investigation.md \
  docs/implementation/AMSDP_M4_Appointment_Implementation_Report.md \
  docs/implementation/AMSDP_M5_Queue_Implementation_Report.md \
  docs/implementation/AMSDP_M6_Implementation_Plan.md \
  docs/implementation/AMSDP_M6_Implementation_Report.md \
  docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md \
  docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md \
  docs/implementation/AMSDP_SEQ_03_COMPLETION_REPORT.md \
  docs/implementation/AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md \
  docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md \
  docs/deployment/AMSDP_M8_Cloud_Deployment_Architecture.md \
  docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md \
  AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md \
  AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md

# expect 45 rows — 43 added/modified + the 2 deletions that pair with the docs/audit/ copies
git diff --cached --name-status
git commit -m "chore(governance): add the agent rules and the AMSDP documentation set"
```

### 18.8.4 C-2 — infrastructure and the env contract (4 paths)

```bash
git add .gitignore .env.example README.md docker-compose.yml
# expect exactly 4: A .env.example, M .gitignore, M README.md, M docker-compose.yml
git diff --cached --name-status
git commit -m "chore(infra): environment-driven credentials and the documented env contract"
```

> `.env` is **never** added — it is ignored, and it is the only place the rotated password lives.
> `docker-compose.demo.yml` stays out (G-7).

### 18.8.5 C-3 — backend (86 paths, staged in two commands, committed once)

```bash
# C-3a — platform layer: alembic chain, app entrypoint, shared code, seed (36)
git add backend/alembic.ini backend/alembic/README backend/alembic/env.py \
  backend/alembic/script.py.mako \
  backend/alembic/versions/3c8e5d0a9b2f_add_patient_age.py \
  backend/alembic/versions/5f3fce6757cf_initial_schema.py \
  backend/alembic/versions/9d8a1f2b3c4d_add_staff_doctor_link.py \
  backend/alembic/versions/a1f2b3c4d5e6_add_tracking_tokens.py \
  backend/alembic/versions/b7c1e4d90a52_add_notifications.py \
  backend/alembic/versions/c7d3601e2486_add_audit_branch.py \
  backend/alembic/versions/ccf34da72c1b_add_queue_sequences.py \
  backend/alembic/versions/d4b2c8e1f7a3_add_login_attempts.py \
  backend/alembic/versions/e6c1a9b3d5f8_drop_redundant_tracking_token_index.py \
  backend/app/main.py backend/conftest.py \
  backend/common/__init__.py backend/common/audit.py backend/common/auth.py \
  backend/common/config.py backend/common/database.py backend/common/health.py \
  backend/common/log_redaction.py backend/common/login_throttle.py \
  backend/common/models.py backend/common/permissions.py \
  backend/common/queue_tokens.py backend/common/timeutil.py \
  backend/common/tracking_tokens.py \
  backend/common/notifications/__init__.py backend/common/notifications/config.py \
  backend/common/notifications/hooks.py backend/common/notifications/outbox.py \
  backend/common/notifications/providers.py backend/common/notifications/worker.py \
  backend/seed/__init__.py backend/seed/seed_demo.py

# C-3b — services and their tests (50)
git add backend/appointment/Dockerfile backend/appointment/dashboard.py \
  backend/appointment/main.py backend/appointment/requirements.txt \
  backend/appointment/tracking.py backend/appointment/tests/test_appointment.py \
  backend/appointment/tests/test_reschedule.py \
  backend/audit/Dockerfile backend/audit/main.py backend/audit/requirements.txt \
  backend/audit/tests/test_audit.py \
  backend/doctor/Dockerfile backend/doctor/main.py backend/doctor/requirements.txt \
  backend/doctor/tests/test_doctor.py \
  backend/identity/Dockerfile backend/identity/main.py backend/identity/models.py \
  backend/identity/permissions.py backend/identity/requirements.txt \
  backend/identity/routes.py backend/identity/tests/test_identity.py \
  backend/organization/Dockerfile backend/organization/main.py \
  backend/organization/notification_config.py backend/organization/requirements.txt \
  backend/organization/tests/test_organization.py \
  backend/patient/Dockerfile backend/patient/main.py backend/patient/requirements.txt \
  backend/patient/tests/test_patient.py \
  backend/queuing/Dockerfile backend/queuing/display.py backend/queuing/main.py \
  backend/queuing/recovery.py backend/queuing/requirements.txt \
  backend/queuing/tests/test_queue.py \
  backend/scheduling/Dockerfile backend/scheduling/main.py \
  backend/scheduling/requirements.txt backend/scheduling/tests/test_scheduling.py \
  backend/tests/amsdp_test_support.py backend/tests/test_dashboard.py \
  backend/tests/test_dqds.py backend/tests/test_e2e.py backend/tests/test_patient_age.py \
  backend/tests/test_security.py backend/tests/test_sequence3.py \
  backend/tests/test_sequence4.py backend/tests/test_tracking_tokens.py

# expect 86 rows, all under backend/ — no frontend, no docs, no _tools
git diff --cached --name-status | wc -l
git commit -m "feat(backend): multi-service identity, org, patient, doctor, scheduling, queue, audit"
```

**C-3 is the only commit with a runtime dependency on C-2**: `common/config.py`, `common/database.py`
and the nine migrations assume the environment contract introduced there (no DSN literal anywhere —
verified in §5.1 and re-verified by the scan in §18.4). Commit order already satisfies this.

### 18.8.6 C-4 — frontend shell and pages (24 paths)

```bash
git add frontend/next.config.js frontend/package.json \
  frontend/components/AppShell.js \
  frontend/components/ui/Alert.js frontend/components/ui/ConfirmDialog.js \
  frontend/components/ui/DataTable.js frontend/components/ui/Modal.js \
  frontend/components/ui/StatusBadge.js \
  frontend/lib/auth.js frontend/lib/i18n.js \
  frontend/pages/_app.js frontend/pages/appointments.js frontend/pages/audit.js \
  frontend/pages/branches.js frontend/pages/dashboard.js frontend/pages/doctors.js \
  frontend/pages/index.js frontend/pages/notifications.js frontend/pages/orgs.js \
  "frontend/pages/queue-display/[org]/[branch].js" frontend/pages/queue.js \
  frontend/pages/schedules.js frontend/pages/staff.js "frontend/pages/track/[token].js"

# expect 24 rows, all under frontend/ (no patients.js, no styles/global.css)
git diff --cached --name-status | wc -l
git commit -m "feat(frontend): shared shell and application pages"
```

`frontend/pages/index.js` is in this commit **because of the G-8 scrub** (the login hint no longer
prints a password), not because of a feature change.

### 18.8.7 C-5 — BanglaNameSense (13 paths)

```bash
git add frontend/components/BanglaNameSense.js \
  frontend/data/README.md frontend/data/bangla_name_sense.json \
  frontend/lib/bangla-name-sense/controller.js \
  frontend/lib/bangla-name-sense/dataset.js \
  frontend/lib/bangla-name-sense/matcher.js \
  frontend/lib/bangla-name-sense/normalize.js \
  frontend/lib/bangla-name-sense/validate-dataset.js \
  frontend/scripts/validate-bangla-name-sense.mjs \
  frontend/tests/banglanamesense-controller.test.mjs \
  frontend/tests/banglanamesense-dataset.test.mjs \
  frontend/tests/banglanamesense-integration.test.mjs \
  frontend/tests/banglanamesense-matcher.test.mjs

# expect 13 rows; `node --test tests/*.test.mjs` = 43 pass (§18.5)
git diff --cached --name-status | wc -l
git commit -m "feat(frontend): BanglaNameSense patient-name suggestion"
```

**Known consequence of G-3:** the only page that imports `BanglaNameSense` is
`frontend/pages/patients.js`, which stays unstaged. In the pushed tree the component is therefore
present but unreferenced — dead weight until the deferred file ships in a later commit. It is split
into its own commit precisely so that later commit is a single line of diff.

### 18.8.8 C-6 — AI Factory fixes and AILI reports (7 paths)

```bash
git add ai_factory/src/amsdp_ai_factory/execution/build_crews.py \
  ai_factory/src/amsdp_ai_factory/execution/live.py \
  ai_factory/tests/unit/test_live_executor.py \
  ai_factory/tests/unit/test_tools_analysis.py \
  ai_factory/docs/AILI_Independent_Verification_Report_V2.0.0.md \
  ai_factory/docs/AILI_Phase4_Repair_and_Assessment_Report_V1.0.md \
  ai_factory/docs/AILI_Structured_Output_Investigation_Report_V1.0.md

# expect 7 rows; `PYTHONPATH=ai_factory/src pytest ai_factory/tests/unit/test_tools_analysis.py -q` = 5 passed
git diff --cached --name-status | wc -l
git commit -m "chore(ai_factory): execution fixes and AILI reports"
```

The three `AILI_*.md` files stay under `ai_factory/docs/` under owner decision **O-1** (registered as
out-of-tree in the docs index); they are committed where they live, not moved into `docs/`.

### 18.8.9 C-7 — demo material and images (14 paths)

```bash
git add docs/demo/AMSDP_Demo_Credentials_V1.0.md \
  docs/demo/AMSDP_Hackathon_Demo_Runbook.md \
  "docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-24.png" \
  "docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-36.png" \
  "docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-44.png" \
  "docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-51.png" \
  "docs/images/NoteTaker/Screenshot From 2026-11-11 11-35-56.png" \
  "docs/images/doctors images/doctor-group-1.jpeg" \
  "docs/images/doctors images/doctor-group-2.jpeg" \
  "docs/images/doctors images/doctor-group-3.jpeg" \
  "docs/images/doctors images/doctor-group-4.jpeg" \
  "docs/images/doctors images/doctor-group-5.jpeg" \
  "docs/images/doctors images/doctor-group-6.jpeg" \
  "docs/images/example dashboards/booking_dashboard_1.webp"

# expect 14 rows: 1 M + 1 A + 12 A (binary); 12 distinct SHA-256, 837,402 B total (§8)
git diff --cached --name-status | wc -l
git commit -m "docs(demo): hackathon runbook, rotated credential sheet and demo images"
```

### 18.8.10 Post-plan verification (what the owner should see after C-7)

```bash
git log --oneline -8                  # 7 new commits on top of eb87cac
git diff --cached --name-only | wc -l # 0  — nothing left staged
git status --porcelain -uall          # exactly the 14 excluded paths, nothing else
git ls-files -co --exclude-standard | wc -l   # 0 — no untracked file left outside .gitignore
```

The last command is the real end-state test: after C-7 the only paths `git` still reports must be the
14 deliberately excluded ones, and every one of them must be either ignored or an explicit
owner-deferred file. If any *other* path appears, the plan was not followed.

## 18.9 Residual risks after Step 1

| # | Risk | Severity | Why it is acceptable now | What closes it |
|---|---|---|---|---|
| **R-1** | `docs/security/AMSDP_M2_Security_Implementation_Report.md` stays untracked, so the security review is not in repository history | Medium | it contains security findings; the owner has not authorised publishing it, and `.clinerules` §3 puts secrets above completeness | an owner-approved redacted version under `docs/security/`, in its own commit |
| **R-2** | Four **demo-seed** passwords (`org_admin`, `receptionist`, `doctor`, `assistant`) remain printed in `docs/demo/AMSDP_Demo_Credentials_V1.0.md` (§18.7) | Medium, deliberate | that file is the owner-designated single source for demo credentials; the accounts are demo-only, seeded from `.env` | rotate all six before the repo becomes public, or drop the sheet from the public mirror |
| **R-3** | After C-7 the tree is still dirty: `patients.js`, `global.css` and the 12 excluded paths remain | Low | it is the recorded G-3/G-6/G-7 deferral, not an accident | a follow-up commit pair once the `patients.js` visual work is finished |
| **R-4** | `.env` holds the only copy of the rotated admin password; a fresh clone without `.env` cannot seed staff | Low, fails safe | `_demo_password()` exits with `ERROR: no demo password configured for staff account …` instead of using a default (§18.2) — no silent default credential exists | `.env.example` (C-2) documents every key; `_tools/init_demo_env.sh` generates them |
| **R-5** | Every green suite in §18.5 ran **locally**; there is still no verified CI pipeline | Medium | claimed honestly — no CI gate is claimed anywhere in this report (§3, §7) | a workflow file in its own commit, then one green CI run |
| **R-6** | 837,402 B of images enter history permanently | Low | owner approved (G-5); the files are the only copies | nothing — accepted |
| **R-7** | `BanglaNameSense` ships unreferenced until `patients.js` lands (G-3) | Low | inert code plus tests; nothing in the pushed tree imports it | swap the one import line when the deferred page ships |

## 18.10 Governance and skill compliance (`.clinerules` §6)

**Applicable governance documents** — `.clinerules` §4 routing, rows *Documentation*,
*Authentication/sessions/RBAC*, *Multi-tenant data*, *Database schema/migrations*,
*Audit/data integrity*, *Frontend UI*, *Docker/deployment*:

- `.clinerules` (§1–§12) — read in full in this session
- `docs/governance/AMSDP_Docs_Index_V1.0.md` — read first per §2 step 3 / §12; advanced to **Revision 8** in this task
- `docs/governance/AMSDP_Engineering_Governance_Assessment.md` — §3 adaptation rules
- `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md` — read-only, cited for the RBAC and scope statements
- `docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` — consulted; **no manifest entry owed** (no document moved, renamed or retired)
- `docs/governance/AMSDP_Skill_Routing_Architecture.md` — skill onboarding path

**Selected skills: none.** `.clinerules` §5 records that no skill package is installed in this
workspace (verified again: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`), so every
row of the §4 table fell through to the governance documents above. **No skill was used, and none is
claimed.**

**Non-negotiables (§3) — how each was respected in this step**

| Rule | Evidence in this step |
|---|---|
| No secret is logged or exposed | the rotated password is read from the environment only; `/tmp/verify_rotated_admin.py` prints status codes and token *length*, never the token; the four remaining sheet passwords are demo-seed values in the owner-controlled file only |
| The UI is never the fallback boundary | the rotation probe calls the API directly on :8110 and through :3100; anonymous and bogus-token reads return 401 (§18.3) |
| Access enforced server-side, org from the token | no authorisation code was modified; the 512-row staff read used the token's own scope |
| Cross-tenant failure returns 404, never 403 | untouched — `git diff` in this step covers the seed script, one test fixture, the demo docs and one login hint |
| One tenant key, `organization_id` | no model and no migration changed |
| Audit trail append-only | no audit code or row modified; the seed touches staff identity rows only |
| Denials audited, never swallowed | `/api/v1/staff/check-permission` untouched |
| Forward-only idempotent Alembic migrations | no new migration; the nine existing ones are merely staged for C-3 |
| Never claim an unverified capability | §18.5 names the suites **not** re-run; §18.3 records the incorrect `/me` probe instead of hiding it; R-5 states plainly that no CI gate exists |
| No destructive git operations | `git diff --cached` verified empty (`/tmp/s62_state.txt`); nothing staged, committed, pushed, reset, cleaned or stashed |

**Evidence standard (§7):** the rotation is **VERIFIED** — a live 200 on two ports, a live 401 for the
retired value, and a database-backed staff read are three independent artefacts. The suites are
**TESTED** — named commands with captured output. Nothing here is claimed as **ACCEPTED**: that is the
owner's signature, and it is exactly what Step 2 is waiting for.

## 18.11 Handoff — what the owner must authorise

**State at handoff:** `HEAD` = `eb87cac`; **staged = 0**; 207 working-tree entries; 7 planned commits
covering 193 paths; 14 paths deliberately excluded; **nothing committed, nothing pushed.**

The one decision still outstanding is authorisation to execute §18.8. It is deliberately *not* run:
`.clinerules` §9 and the task instruction both put repository writes behind the owner's explicit word.
Everything the plan needs already exists — the path list is machine-derived and complete
(`UNASSIGNED: 0`), the suites are green, and the scan finds zero real secrets in the future-commit set.

When authorisation comes the sequence is mechanical: run §18.8.3 → §18.8.9 in order, check the
`git diff --cached --name-status` row count at every step, then run §18.8.10 and confirm the tree holds
nothing but the 14 excluded paths.

**Open items for the owner (no action blocked):** R-1 (publish or keep the M2 security report out of
history), R-2 (rotate the four documented demo passwords before any public mirror), R-3 (the follow-up
commit pair for `patients.js` + `global.css` once the visual work lands), R-5 (decide whether a CI
workflow is in MVP scope).

---

## 18.12 Pre-flight of the authorised push — one deviation, resolved before staging

The owner authorised execution of §18.8.3–§18.8.10 on 2026-11-12. Before staging anything, every
§18.8.1 invariant and every pre-flight check was re-run against the live tree.

| Pre-flight check | Result |
|---|---|
| Branch | `hackathon-mvp` |
| `HEAD` | `eb87cac55824601a7f03ee08571f828755ad7b2e` — the audited commit, unchanged |
| Remote `origin` | `https://github.com/shomonrobie/amsdp` (fetch and push) |
| Upstream | none configured — as §18.7 anticipated; the push uses `git push -u origin hackathon-mvp` |
| `origin/hackathon-mvp` | does not exist yet (only `origin/main`) — the push creates it |
| Staged changes | 0 |
| Worktree entries | 207 → classifier `UNASSIGNED: 0`, C-1/C-2/C-3/C-4/C-5/C-6/C-7 = 45/4/86/24/13/7/14, EXCLUDED 14 |
| Plan ↔ document cross-check | 193 documented paths, 193 unique, 0 absent from `git status` |
| Active git hooks / `core.hooksPath` | none / unset |
| **Secret scan** | **11 hits — 3 more than the audited 8** (see below) |

**The deviation.** §18 was written *after* the audit recorded `HITS=8` (§18.4), and in doing so it
quoted three strings it should have described instead of reproduced: two demo-seed password literals
in the G-1 row and the synthetic `sk-`-prefixed fixture in §18.7. Because this document is path 20 of
C-1, committing the plan verbatim would have carried two real demo passwords into history and made
§18.4's own figure false.

**Resolution.** The owner authorised a redaction that touches no path, no count, no ordering and no
exclusion: the G-1 row now identifies the removed literals by the `AMSDP_DEMO_PASSWORD_*` keys that
supply them, and §18.7 names the fixture without reproducing it. A re-scan over the same 403
candidates returns **exactly 8 hits — the audited set, unchanged**: 4 in `ai_factory` (2 redaction
machinery, 2 synthetic fixtures) and 4 in the owner-controlled credential sheet (R-2 demo values).
Nothing legacy reappeared: the rotated admin password, the retired admin password and the historical
dev database password all score zero.

Nothing was staged, committed or pushed while the deviation was open. Everything below §18.8 stands
exactly as documented — the path lists executed in C-1…C-7 are the ones in §18.8.3–§18.8.9, run in
that order, with the `git diff --cached --name-status` row count checked against 45/4/86/24/13/7/14
before each commit. The resulting commit hashes and the push outcome are recorded in the task
execution report rather than amended back into this section, so that the tree the push leaves behind
contains nothing but the 14 documented exclusions.

---

*End of §18 — the governing record for Step 2. §1–§17 stand unchanged as the pre-decision record.*
