# AMSDP — Ubuntu Replacement Pre-flight Inspection Report

**Document ID:** `AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT`
**Version:** 1.0
**Date:** 2026-11-22
**Author:** Cline (agent), read-only pre-flight inspection
**Location:** `/home/shomonrobie/amsdp/docs/implementation/` (per `.clinerules` §11 — subject folder `implementation/`; no new folder created)
**Subject host:** Ubuntu workstation, working copy `/home/shomonrobie/amsdp`
**Subject of inspection:** the planned replacement of this Ubuntu source tree with the Windows-pushed commit `2fc007a3f7a96639c3df36341c6081cee4d24a48`
**Nature of document:** evidence record plus an owner-executed procedure. It states what was **observed** on this host, and what the observed facts imply. It executes nothing.

---

## 0. Label legend and honesty statement

| Label | Meaning in this document |
|---|---|
| **VERIFIED** | An independent artefact confirms it: executed command output, a live read-only PostgreSQL query, or a commit-pinned remote read whose result is quoted. |
| **IMPLEMENTED** | The artefact exists in the target tree and is reachable from a route, import, or entry point. Established by reading the tree, not by running it. |
| **PARTIALLY VERIFIED** | The artefact exists and is reachable, but a required runtime confirmation was not performed in this session. |
| **ASSUMPTION** | Stated inference from observed facts; not directly evidenced. Always marked as such where it appears. |
| **NOT VERIFIED** | No artefact confirms it. Not the same as "false" — it means *unproven*. |
| **BLOCKED** | The check could not be performed, for a stated reason. |

**Honesty statement.**

- This inspection was **strictly read-only** on this host. No file, database row, container, image, volume, migration or Git ref was created, modified, started, stopped, or deleted by the inspection. No migration was run. No test suite was executed.
- The only file this task created is **this report** (§13.4 re-verifies that claim).
- Nothing here is **ACCEPTED**: nothing was submitted to the Product Owner for sign-off.
- The only section that reaches outside the host is §3 (target-commit verification), which used `git ls-remote` (ref listing only, no fetch) and commit-pinned HTTPS reads of `github.com/shomonrobie/amsdp`. Those reads change nothing locally and are quoted where used.
- Where this report says the target *will* do something at runtime, that is an **ASSUMPTION** built on the read target code, and is labelled as such. Nothing in the target commit was executed on this host.

---

## 1. Scope, authorization, method

### 1.1 Mandate

The Product Owner has approved replacing this Ubuntu working copy's source, untracked files and documentation with the Windows-pushed commit `2fc007a3f7a96639c3df36341c6081cee4d24a48` (branch `hackathon-mvp`). This document is the pre-flight inspection that must precede that act.

### 1.2 The ten required questions

| # | Question | Answered in |
|---|---|---|
| 1 | Current Ubuntu HEAD, branch, remotes, complete Git status | §2 |
| 2 | Does the target commit exist on the remote? | §3 |
| 3 | Environment files, secrets, configuration, Docker volumes, DB volumes, uploads, other persistent data | §4 |
| 4 | What must survive source replacement to keep the runtime operational | §5 |
| 5 | Docker Compose services, container names, ports, volumes, health | §6 |
| 6 | Database name, server version, Alembic revision, schema state (read-only) | §7 |
| 7 | Target migration graph versus live database revision | §8 |
| 8 | Startup and database compatibility risks | §9 |
| 9 | Exact replacement procedure using the target commit | §10 |
| 10 | Rollback instructions | §11 |

### 1.3 Restrictions honoured

No modification or deletion; no container stopped or started; no database altered; no migration run; no `pull`/`reset`/`checkout`/`clean`/`merge`/`rebase`/`fetch`; nothing staged or committed. Commands used: `git rev-parse`, `git symbolic-ref`, `git log`, `git remote -v`, `git for-each-ref`, `git ls-tree`, `git hash-object` (hash only, never `-w`), `git cat-file -t`, `git ls-files`, `git show --stat`, `git status --short -uall`, `git status --ignored --short`, `git diff --stat`, `git stash list`, `git ls-remote`, `find`, `ls`, `du`, `wc`, `grep`, `sed`, `df`, `crontab -l`, `systemctl list-unit-files`, `systemctl list-units`, `docker compose ps`, `docker ps -a`, `docker volume ls`, `docker network ls`, `docker image ls`, `docker image inspect`, `docker info`, `docker volume inspect`, `docker exec … psql` (**`SELECT`/catalog reads only**), and HTTPS `GET` of the GitHub API / raw content pinned to the target commit.

### 1.4 Method for comparing a host file with a file at the target commit

Comparing trees normally needs a `fetch`, which is forbidden here. The method used instead is byte-exact and fetch-free:

1. Read the target tree object through the GitHub API (`git/trees/<sha>`), which returns each blob's **Git blob SHA-1** and size.
2. Compute the same blob SHA-1 locally with `git hash-object <path>` (no `-w`, so nothing is written).
3. Equal blob SHA-1 ⇒ **byte-identical content**. Different ⇒ different content, with no claim about *how* different.

That is why §8 can state that 14 of the target's 16 migration files are byte-identical to this host's without having fetched anything.

### 1.5 Scratch artefacts

Raw output was staged outside the repository at `/tmp/ubupre/` (`git_identity.txt`, `git_status.txt`, `docs_impl.txt`, `docker_state.txt`, `config_inventory.txt`, `mounts.txt`, `db_state.txt`, `local_hashes.txt`, `compose.txt`, `tree_overview.txt`, `lsremote.txt`, `db_missing_tables.txt`, `db_probe2.txt`, `db_columns.txt`, `db_sizes.txt`, `env_tools.txt`, `runtime_extra.txt`, `image_detail.txt`, `tree2.txt`, `scripts.txt`, `persistent.txt`, `services.txt`, `graph.txt`, `hostenv.txt`, `local_commits.txt`, `announce_local.txt`). That directory is scratch, not an AMSDP document location.

---

## 2. Current Ubuntu repository state — VERIFIED

| Item | Observed value | How |
|---|---|---|
| Working directory | `/home/shomonrobie/amsdp` | `pwd` |
| Branch | `hackathon-mvp` (symbolic HEAD) | `git rev-parse --abbrev-ref HEAD`; `git symbolic-ref -q --short HEAD` |
| HEAD commit | `cd2f9ecdf51b363105214e3ffd504d3adc151ada` | `git rev-parse HEAD` |
| HEAD author/date | `shomonrobie <shomonrobie@gmail.com>` · Fri Nov 20 15:03:30 2026 +0600 | `git log -1 --format` |
| HEAD subject | *docs: add AMSDP website content and copywriting proposal* | `git log -1 --format=%s` |
| Root tree at HEAD | `5f46294a961317a3aabc2d0155f06734fdd02af8` | `git rev-parse HEAD^{tree}` |
| Remotes | `origin  git@github.com:shomonrobie/amsdp.git` (fetch **and** push) | `git remote -v` |
| Upstream tracking | `hackathon-mvp -> origin/hackathon-mvp [[ahead 2]]`; `main -> origin/main []` | `git for-each-ref --format='%(upstream:track)'` |
| Stale remote ref | `origin/hackathon-mvp` = `37cf3d1` — the last *fetched* state, **not** the current remote state | `git log --oneline origin/hackathon-mvp -3` |
| Stashes | none | `git stash list` (empty) |

### 2.1 Two discrepancies with the task brief — reported, not silently resolved

1. **The configured remote is SSH, not HTTPS.** The brief gives `https://github.com/shomonrobie/amsdp/`; this repository's `origin` is `git@github.com:shomonrobie/amsdp.git`. Both address the same GitHub repository — confirmed because `git ls-remote origin` (SSH) and the GitHub API (HTTPS) report the identical commit SHA for `refs/heads/hackathon-mvp` (§3). The procedure in §10 therefore uses the configured SSH remote, which is **VERIFIED reachable** (`git ls-remote` exit 0).
2. **The local branch is "ahead 2" of a stale remote ref.** That count is computed against `origin/hackathon-mvp` = `37cf3d1`, which this host has not refreshed. The live remote head is `2fc007a` (§3). The true relationship between local `cd2f9ec` and remote `2fc007a` is **BLOCKED** — see §3.3, and it matters for rollback (§11).

### 2.2 The two local commits that "ahead 2" refers to — VERIFIED

| Commit | Subject | Files touched |
|---|---|---|
| `0554f33` | docs: add website content proposal | `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` (0 insertions) |
| `cd2f9ec` | docs: add AMSDP website content and copywriting proposal | `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` (+913 lines) |

Both touch a single documentation file. That file is **absent from the target commit's `frontend/public` tree** (§8.5), so its content will not exist in the working tree after replacement. The commit objects themselves survive only if a rescue ref is created first (§10 step 2).

### 2.3 Complete Git status at the time of inspection — VERIFIED

`git status --short -uall`: **21 entries — 13 modified, 8 untracked, 0 staged, 0 deleted.**

Modified (tracked, uncommitted):

```
 M .gitignore
 M backend/appointment/main.py
 M backend/queuing/main.py
 M backend/queuing/recovery.py
 M docs/governance/AMSDP_Docs_Index_V1.0.md
 M frontend/lib/announcements/content.js
 M frontend/lib/announcements/controller.js
 M frontend/lib/announcements/speech-synthesis.js
 M frontend/pages/queue.js
 M frontend/tests/queue-announcement-content.test.mjs
 M frontend/tests/queue-announcement-controller.test.mjs
 M frontend/tests/queue-announcement-speech.test.mjs
 M frontend/tests/queue-announcements-boundary.test.mjs
```

Untracked:

```
?? backend/common/locations.py
?? backend/tests/test_queue_room_snapshot.py
?? docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md
?? docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md
?? docs/implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md
?? docs/implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md
?? frontend/lib/announcements/dedupe.js
?? frontend/tests/queue-announcement-dedupe.test.mjs
```

These 21 entries are the Ubuntu-local QUE-006 F1–F4 announcement work plus documentation. The Product Owner has approved their discard; §9.6 states precisely what "discard" removes and what it leaves behind.

---

## 3. Target commit verification — VERIFIED (existence), BLOCKED (ancestry)

### 3.1 The commit exists on the remote and is the remote branch head — VERIFIED

`git ls-remote --heads --tags origin` (read-only network call, exit 0):

```
2fc007a3f7a96639c3df36341c6081cee4d24a48	refs/heads/hackathon-mvp
eb87cac55824601a7f03ee08571f828755ad7b2e	refs/heads/main
```

The target SHA is **exactly** the head of `refs/heads/hackathon-mvp` on `origin`. Independently confirmed over HTTPS by the GitHub commit API:

| Field | Value (quoted from the API response) |
|---|---|
| `sha` | `2fc007a3f7a96639c3df36341c6081cee4d24a48` |
| `commit.author` | `Shomon Robie <shomonrobie@gmail.com>` |
| `commit.author.date` | `2026-11-22T06:42:32Z` |
| `commit.committer.date` | `2026-11-22T06:42:32Z` |
| `commit.verification` | `verified: false`, `reason: unsigned` |
| `commit.tree.sha` | `b3e1356298d14a130599cb599d3d24c5cba86af7` |
| `commit.message` | *"docs(queue): QUE-006 workstream reports and documentation index registration"* + body: the master plan, the W1…W6 reports, the audio catalogue and format standardisation records, the POD-12 call control report, the W2 pre-commit review and reliability completion, and the W3 implementation and verification report; registration in the docs index; and the note that "a commit is not a verification, and the API suite, the migration and the browser run remain unexecuted" |

That last clause is the target commit author's own evidence statement: **the target's API suite, its migration, and its browser run were not executed before the commit**. It is quoted here because it bounds what may be claimed after the replacement (§9.1).

### 3.2 The commit object is NOT present in this host's object database — VERIFIED

`git cat-file -t 2fc007a3f7a96639c3df36341c6081cee4d24a48` → `fatal: git cat-file: could not get object info`.

Consequence: no `git show`, `git diff`, `git merge-base` or `git log` against the target is possible on this host without a `fetch`, which this read-only mandate forbids. Everything this report says about the target's *contents* therefore comes from commit-pinned remote reads (§1.4), not from local Git objects.

### 3.3 Ancestry of local HEAD relative to the target — BLOCKED

Determining whether `cd2f9ec` is an ancestor of `2fc007a` requires the target's commit graph, i.e. a `fetch`. Not performed. What *is* known:

- `2fc007a`'s parent chain was not read in this session (the API response was truncated before the `parents` array; no further request was made, because ancestry cannot be established from parents alone).
- The local "ahead 2" figure is against a stale ref (`37cf3d1`) and must not be read as "two commits to push".
- **Evidence that argues against ancestry:** the two local commits add `frontend/public/WEBSITE_CONTENT_PROPOSAL.md`, and the target's `frontend/public` tree (`f0ade6a2…`, read recursively, `truncated: false`) contains **only** the `audio/` subtree and `audio/manifest.json` — no `WEBSITE_CONTENT_PROPOSAL.md`. A file added in an ancestor and still present at the descendant would appear there. **(ASSUMPTION, stated as such):** the two local commits were never pushed, or were pushed and superseded by an independent Windows-side commit with different content. Either way the file will not be present after replacement.
- **Practical implication for §10/§11:** do not rely on fast-forward. Create a rescue ref before touching the working tree.

---

## 4. Environment files, secrets, configuration and persistent data

### 4.1 Secrets and environment files — names only, no values

**No secret value appears in this report.** Only key *names*, byte sizes and ignore status are recorded, per `.clinerules` §3.

| File | Size | Git status | Keys it defines (names only) |
|---|---|---|---|
| `/home/shomonrobie/amsdp/.env` | 469 B | **gitignored** (`!!` in `git status --ignored`) | `POSTGRES_PASSWORD`, `AMSDP_DEMO_PASSWORD_ADMIN`, `AMSDP_DEMO_PASSWORD_ORG_ADMIN`, `AMSDP_DEMO_PASSWORD_BR_ADMIN`, `AMSDP_DEMO_PASSWORD_RECEPTIONIST`, `AMSDP_DEMO_PASSWORD_DOCTOR`, `AMSDP_DEMO_PASSWORD_ASSISTANT` |
| `/home/shomonrobie/amsdp/ai_factory/.env` | 1 001 B | **gitignored** | `AMSDP_FACTORY_ENVIRONMENT`, `AMSDP_FACTORY_LOG_LEVEL`, `AMSDP_FACTORY_DEFAULT_MAX_RETRIES`, `AMSDP_FACTORY_MODEL_PROVIDER`, `AMSDP_FACTORY_MODEL_ID`, `OPENROUTER_API_KEY` |
| `.env.example` | 2 594 B | tracked, clean | template; blob `dccb6c62a5a93f522a03f35120f7393c6d212713` — **byte-identical to the target** |

Notable observations:

- **`AMSDP_JWT_SECRET` is not set** in `.env`. `docker-compose.yml` therefore applies its documented default `dev-synthetic-key-replace-in-prod` to every service, on both sides of the replacement. Consequence: **tokens issued before the replacement stay valid after it** (same secret), and no re-login is needed. It also means the development signing key is in use — pre-existing, not introduced by this replacement.
- **`POSTGRES_PASSWORD` is mandatory**: compose declares `${POSTGRES_PASSWORD:?missing - set it in .env, see .env.example}`. If `.env` is lost or renamed, `docker compose` refuses to start the stack. That is why `.env` is item 1 in §5.
- No `*.pem`, `*.key` or `*.crt` file exists anywhere in the tree outside `frontend/node_modules`: a `find` sweep excluding `node_modules`, `.venv`, `.venv313` and `.git` returned only `ai_factory/src/…/secret_scan.py`, its two `.pyc` files, and a `caniuse-lite` data file named `credential-management.js`. **VERIFIED.**

### 4.2 Configuration files — blob comparison against the target

| File | Size | Blob SHA-1 (local working tree) | Blob SHA-1 at target | Same? |
|---|---|---|---|---|
| `docker-compose.yml` | 6 244 B | `363cf792ced6decb1b5a685ea04e69605b951fef` | same | **identical** |
| `docker-compose.demo.yml` | 3 086 B | `a68e3d0aca75f8a96e922d989d00f2343e62ff0b` | same | **identical** |
| `.env.example` | 2 594 B | `dccb6c62a5a93f522a03f35120f7393c6d212713` | same | **identical** |
| `README.md` | 17 659 B | `bba8a152b7036d2e7884761b8282baa11dce68f3` | same | **identical** |
| `.clinerules` | 17 087 B | `fbb31bdef44126a83b4762ce0a6c7c246d2ff76f` | same | **identical** |
| `.github/workflows/ci.yml` | 4 321 B | `a59b3f074aed41d68eb531c73283ac19cd3d5a91` | same | **identical** |
| `frontend/Dockerfile` | 128 B | `ff5e3e4319c3e84413d3f62a75b5ff93e1183741` | same | **identical** |
| `frontend/next.config.js` | 3 220 B | `1ef4090f7bbb78d6da72583cab1aa007db6daa07` | same | **identical** |
| `frontend/package.json` | 710 B | `63405ee30d48df9edc461a416125be3aeed6c5b6` | same | **identical** |
| `frontend/package-lock.json` | 70 104 B | `38f0000089b662d5ddcd12531da3b44332f7cb41` | same | **identical** |
| `frontend/tailwind.config.js` | 3 635 B | `f06a20ae0aaa0b257251be8549a3bfebf446f114` | same | **identical** |
| `backend/seed/seed_demo.py` | 47 216 B | `6cb598af63c7d3c17617522d3e47b92c6913ea19` | same | **identical** |
| `.gitignore` | — | HEAD `f817087b…`; **worktree modified** `14ada417…` | `69cc6ab559be1315e53fed1f7bacec6852e478fc` | **differs** |

Two consequences worth stating plainly:

- **No dependency drift.** `package.json`, `package-lock.json`, the frontend `Dockerfile`, `next.config.js` and `tailwind.config.js` are byte-identical, so the rebuild resolves the same dependency graph from the same lockfile. `backend/seed/seed_demo.py` is byte-identical too — the boot-time demo seed is unaffected by the replacement (§9.4).
- **`.gitignore` will change.** The target's version (1 304 B, read in full during inspection) ignores `.env`, `.env.*` (with `!.env.example`), `.venv/`, `.venv*/`, `node_modules/`, `.next/`, `/runs/`, `/var/`, `/backups/`, `/tree.py`, `/verify_llm_routing.py`, `ai_factory/var/`, `ai_factory/runs/`, `ai_factory/workspaces/`, and — new in the target — `/frontend/.audio-originals-backup/` ("Binary copies of the recordings: kept on disk as evidence, never committed"). So **every secret-bearing and runtime file in §5 stays ignored after the replacement**. `.gitignore` is one of the 13 modified files, so the local uncommitted variant (which differs from *both* HEAD and the target) is discarded.

### 4.3 `_tools/` is byte-identical to the target — VERIFIED

`git ls-tree HEAD _tools` → tree `9b201df334a9e18353437c35ce2d95027adf5a45`; the target root tree lists `_tools` as `9b201df334a9e18353437c35ce2d95027adf5a45`. Equal tree SHA-1 ⇒ **identical directory**. The ops scripts (`amsdp_stack.sh`, `amsdp_rebuild.sh`, `amsdp_autostart.sh`, `install_autostart.sh`, `pg_backup.sh`, `pg_restore_test.sh`, `init_demo_env.sh`, `verify_demo_login.sh`) are unchanged by the replacement, so §10 may use them without re-validation. The same holds for `ai_factory` (`af903260…`), `.github` (`2601371c…`), `runs` (`d2bf0f2c…`) and `var` (`dffd6be4…`).

### 4.4 No `.dockerignore` exists — VERIFIED

`ls .dockerignore backend/.dockerignore frontend/.dockerignore` → all three absent. Build contexts are therefore the full `./backend` (6.6 MB) and `./frontend` (371 MB, including `node_modules`). Pre-existing and unchanged by the replacement; recorded because it dictates how long the mandatory rebuild takes (§9.3).

---

## 5. What must survive the replacement

A `git checkout`/`clean` of tracked paths does **not** remove gitignored files, so almost everything below survives automatically. The table exists because the owner's instruction also permits discarding *untracked* files, and because an operator running `git clean -fdx` (explicitly **not** recommended here) would destroy every row below.

| # | Artefact | Location | Size | Why it must survive | Survives a plain `git checkout -f <target>`? |
|---|---|---|---|---|---|
| 1 | `.env` | repo root | 469 B | `POSTGRES_PASSWORD` is mandatory in compose; the six demo-account passwords are what make the demo logins work after the scheduled re-seed | **Yes** (gitignored) |
| 2 | `ai_factory/.env` | `ai_factory/` | 1 001 B | AI Factory / LLM routing configuration and its API key | **Yes** (gitignored) |
| 3 | PostgreSQL data | Docker volume `amsdp_amsdp_pg_data` → `/var/lib/postgresql/data` | DB is 22 MB | **The entire application state**: 27 tables, 19 694 audit events, 407 organisations, 8 queue entries | **Yes** (outside the working tree) |
| 4 | `.venv` | repo root | 261 MB, Python 3.14.4 | `_tools/amsdp_autostart.sh` runs the boot-time demo seed with `.venv/bin/python` | **Yes** (gitignored) |
| 5 | `backups/` | repo root | 708 KB | Two `pg_dump` archives (`amsdp_amsdp_20261111-152003.sql.gz`, `amsdp_amsdp_20261116-084923.sql.gz`) — the existing rollback material | **Yes** (gitignored `/backups/`) |
| 6 | Docker images (current set) | Docker root `/var/snap/docker/common/var-lib-docker` | 9 `amsdp-*:latest` + `amsdp-appointment:post-seq4` + 9 `amsdp_demo-*` | The only exact copy of the code that is **running right now**; a rebuild from any commit will not reproduce these bytes | **Yes** (not pruned) |
| 7 | `runs/`, `var/` | repo root | 176 KB / 68 KB | AI Factory run records and task/workspace stores (some entries are tracked in history, new ones ignored) | **Yes** (mostly gitignored; tracked entries are byte-identical at the target) |
| 8 | `docs/` untracked reports | `docs/…` | — | Three untracked QUE-006 documents plus the reconciliation evidence report. Not required for runtime; listed because they are the only copy of that work on this host | **Yes** (untracked files are left alone) — but **only** if no `git clean` is used |
| 9 | `frontend/node_modules`, `.venv313` | repo root / `frontend/` | 371 MB / 872 MB | Not needed for a compose runtime (images carry their own dependencies). Rebuildable; kept only to save time if someone runs the suites on the host | **Yes** (gitignored) |
| 10 | `.aider.*` caches, `nohup.out`, `tree.py`, `verify_llm_routing.py` | repo root | ~36 KB + 95 KB | Disposable. `tree.py` / `verify_llm_routing.py` are gitignored one-off scripts | **Yes** |

**Nothing else is persistent.** Two negative findings matter as much as the positive ones:

- **No bind mounts for application code.** `docker inspect` on `db`, `queuing`, `frontend`, `identity` and `audit` shows a volume only for `db` (`amsdp_amsdp_pg_data`) and **no mounts at all** for the five application containers. Code is `COPY`ed into the images by the Dockerfiles; `_tools/amsdp_rebuild.sh` documents exactly this ("The source is COPYied into the images and docker-compose.yml mounts no code, so `docker compose restart` restarts the OLD image"). **VERIFIED.**
- **No host-side upload store.** There is no uploads directory, no bind mount, and `frontend/public` contains only tracked assets (locally one file, `WEBSITE_CONTENT_PROPOSAL.md`). Any user-supplied file in this system lives in the database, not on disk. **(ASSUMPTION on generality:** verified for the compose topology and the filesystem; not every service source file was read to rule out a hard-coded path.)

**Safe to discard** (per the owner's approval): all 13 modified tracked files, all 8 untracked files, and the byte-identical-to-HEAD portions of the tree. **Not safe to discard:** rows 1–6 above. Row 8 deserves a decision before §10 step 6 runs (§12, O-R3).

---

## 6. Runtime topology as observed — VERIFIED

### 6.1 Compose project, services, containers, ports, health

Compose project **`amsdp`**. `docker compose ps` — **10 services, 10 containers, all `Up 39 hours (healthy)`** at the time of inspection:

| Service | Container | Published port → container port | Health | Restart policy |
|---|---|---|---|---|
| `db` | `amsdp-db-1` | `5433 → 5432` | healthy (`pg_isready`) | `unless-stopped` |
| `identity` | `amsdp-identity-1` | `8110 → 8000` | healthy (`/health/ready`) | `unless-stopped` |
| `organization` | `amsdp-organization-1` | `8111 → 8001` | healthy | `unless-stopped` |
| `patient` | `amsdp-patient-1` | `8112 → 8002` | healthy | `unless-stopped` |
| `doctor` | `amsdp-doctor-1` | `8113 → 8003` | healthy | `unless-stopped` |
| `scheduling` | `amsdp-scheduling-1` | `8114 → 8004` | healthy | `unless-stopped` |
| `appointment` | `amsdp-appointment-1` | `8115 → 8005` | healthy | `unless-stopped` |
| `queuing` | `amsdp-queuing-1` | `8116 → 8006` | healthy | `unless-stopped` |
| `audit` | `amsdp-audit-1` | `8117 → 8007` | healthy | `unless-stopped` |
| `frontend` | `amsdp-frontend-1` | `3100 → 3000` | healthy (Node `fetch('http://127.0.0.1:3000/')`) | `unless-stopped` |

Topology notes from the compose file (read in full; byte-identical to the target):

- **The frontend is the only public entry point**: it proxies every `/api/v1/*` prefix to the owning service (`frontend/next.config.js`), which is why there is no aggregate backend and no CORS middleware.
- **Every service receives the same `AMSDP_DATABASE_URL` and `AMSDP_JWT_SECRET`** through the `x-backend-env` anchor, and every backend gates its start on `db: service_healthy`.
- **No service runs a migration.** There is no `alembic` command anywhere in `docker-compose.yml`, `_tools/amsdp_stack.sh`, `_tools/amsdp_rebuild.sh` or `_tools/amsdp_autostart.sh` (grep for `alembic` over those files returns nothing). Schema changes are a **manual, out-of-band step** — the single most important operational fact in this report (§9.3).

### 6.2 Volumes and networks

| Item | Value |
|---|---|
| Named volumes used by this project | `amsdp_amsdp_pg_data` (declared `amsdp_pg_data`) |
| Volume mountpoint on host | `/var/snap/docker/common/var-lib-docker/volumes/amsdp_amsdp_pg_data/_data` (Docker is the **snap** package) |
| Volume created | `2026-11-07T14:33:53+06:00` |
| Other AMSDP-family volume | `amsdp_demo_amsdp_demo_pg_data` — the isolated demo database; **no demo container is running** |
| Network | `amsdp_default` (bridge, id `c7b7a85b092e`) |

### 6.3 Images — the running code is older than every candidate commit

| Image | Image ID | Created |
|---|---|---|
| `amsdp-queuing:latest` | `472611afa809` | `2026-11-17T07:44:43+06:00` |
| `amsdp-frontend:latest` | `3b0c02b17d87` | `2026-11-17T07:45:36+06:00` |
| `amsdp-identity:latest` | `718dfa1bc50e` | 2026-11-17 (same build window) |
| `amsdp-organization:latest` | `1c9c965803f2` | 2026-11-17 |
| `amsdp-patient:latest` | `a5ce0a83eb96` | 2026-11-17 |
| `amsdp-doctor:latest` | `e7a95171a65d` | 2026-11-17 |
| `amsdp-scheduling:latest` | `d95f8a8209f5` | 2026-11-17 |
| `amsdp-appointment:latest` | `8e8936468eed` | 2026-11-17 |
| `amsdp-audit:latest` | `d9ff043406a7` | 2026-11-17 |
| `amsdp-appointment:post-seq4` | `e69b25d7e0e2` | 2026-11-10 |

Image labels are only `com.docker.compose.project/service/version` (compose 2.40.3) — **there is no source-commit label**, so an image cannot be tied to a Git commit from its metadata. **VERIFIED.**

**Consequence, stated plainly:** the containers were created 39 hours ago from images built 2026-11-17 07:44. Local HEAD is 2026-11-20 and the target is 2026-11-22. **Nothing running corresponds to either commit.** Neither `docker compose restart` nor `up -d` without `--build` will run the target code.

### 6.4 Neighbouring stacks — untouched, no port conflict

| Stack | Running containers | Ports | Conflict with AMSDP ports? |
|---|---|---|---|
| `freellmapi` | `freellmapi-freellmapi-1` | `127.0.0.1:3001` | no |
| `n8n` | `n8n-n8n-1` | `5678` | no |
| `carbontally_demo_lab` (Supabase) | storage `5000`, postgrest `8000`, realtime `4000`, auth `9999`, gateway `127.0.0.1:54430` | as listed | **no** — none of 3100/5433/8110-8117 |
| `supabase_*_carbon_ledger` | db `54326`, api `54325`, auth `9999`, realtime `4000` | as listed | no |
| `amsdp_demo` | **none running** (images exist, 13 days old) | would reuse 3100/5433/8110-8117 | n/a — stopped |

`docker ps -a` also lists ~40 long-`Exited` containers from earlier CarbonTally/stage/verify projects. They occupy no ports and hold no AMSDP data. **VERIFIED** that no other project binds 3100, 5433 or 8110-8117.

### 6.5 Boot behaviour — an enabled systemd *user* unit

| Item | Value |
|---|---|
| Unit | `amsdp-autostart.service` (`systemctl --user list-unit-files` → **enabled**) |
| Runs | `_tools/amsdp_autostart.sh` |
| What it does | waits for the Docker daemon (≤180 s), runs `_tools/amsdp_stack.sh up` (idempotent; containers are already brought back by `restart: unless-stopped`), then **re-runs the idempotent demo seed** with `.venv/bin/python`, using a DSN built from `.env` |
| Installed by | `_tools/install_autostart.sh` |
| Cron | none (`crontab -l` shows no amsdp/docker entry) |
| System-level units | none for AMSDP; only the snap Docker units (`snap.docker.dockerd.service`, `snap-docker-3613.mount`, `snap-docker-3618.mount`, `snap.docker.nvidia-container-toolkit.service`) |
| Logs | `journalctl --user -u amsdp-autostart.service` |

This matters for the replacement in three ways: `.venv` and `.env` must survive (§5 rows 1 and 4); the boot seed runs the **target's** `seed_demo.py` after the replacement (byte-identical, therefore safe — §4.2); and a failure of that seed is silent unless the journal is read.

### 6.6 Host environment

| Item | Value |
|---|---|
| Docker root | `/var/snap/docker/common/var-lib-docker` (snap) |
| Docker inventory | 104 images, 99 containers (most long-`Exited`) |
| Compose | `2.40.3+ds1-0ubuntu1` |
| Git | `2.53.0` |
| `.venv` interpreter | Python `3.14.4` |
| Free space on `/` | 506 GB available of 938 GB (44 % used) |

---

## 7. Database state — VERIFIED (read-only queries)

All statements below were produced by `SELECT`/catalog queries executed inside the running `amsdp-db-1` container as the container's own `POSTGRES_USER`/`POSTGRES_DB`. **No `INSERT`, `UPDATE`, `DELETE`, DDL or `alembic` command was issued.**

| Item | Observed value | Query |
|---|---|---|
| Database name | `amsdp` | `select current_database()` |
| Role | `amsdp` | `select current_user` |
| Server version | `PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit` (`postgres:16-alpine`) | `select version()` |
| Alembic revision | `a9c4e1f7b2d8` — **exactly one row** (`count(*)=1`, `min=max=a9c4e1f7b2d8`) | `select version_num from alembic_version`; `select count(*), min(version_num), max(version_num) from alembic_version` |
| Tables in `public` | **27** | `select count(*) from information_schema.tables where table_schema=current_schema()` |
| Database size | `22 MB` | `pg_database_size(current_database())` |
| Queue rows | `8` | `select count(*) from queue_entries` |
| Organisations | `407` | `select count(*) from organizations` |
| Audit events | `19 694` rows, 8 888 kB | `select count(*) from audit_events`; `pg_total_relation_size` |
| Largest tables | `audit_events` 8 888 kB, `patients` 856 kB, `staff_users` 768 kB, `appointments` 416 kB, `doctors` 344 kB, `slot_allocations` 344 kB | `pg_total_relation_size` ranking |
| `queue_entries` columns | `id, organization_id, branch_id, doctor_id, date, position, token, patient_id, appointment_id, entry_source, status, status_history, position_history, notes, added_by, created_at` | `information_schema.columns` |

Two of those rows matter for §9:

- **`status_history` exists** on `queue_entries`. The target's W2 module derives its cross-terminal `call_event_id` from exactly this column (`backend/queuing/events.py`), so the *data dependency* for W2 is already satisfied by the live schema.
- **`audit_events` holds 19 694 rows.** `.clinerules` §3 makes the audit trail append-only and non-rewritable; this constrains rollback (§11.3).

---

## 8. Migration graph: live database versus the target commit

### 8.1 The live graph is a single, fully-applied chain — VERIFIED

Local `backend/alembic/versions/` holds **14** revision files. Reading `revision` / `down_revision` from each gives this graph:

```
5f3fce6757cf  initial_schema            (base, down_revision=None)
   └─ ccf34da72c1b  add_queue_sequences
        └─ c7d3601e2486  add_audit_branch
             └─ 9d8a1f2b3c4d  add_staff_doctor_link
                  └─ 3c8e5d0a9b2f  add_patient_age
                       └─ a1f2b3c4d5e6  add_tracking_tokens
                            └─ b7c1e4d90a52  add_notifications
                                 └─ d4b2c8e1f7a3  add_login_attempts
                                      └─ e6c1a9b3d5f8  drop_redundant_tracking_token_index
                                           ├─ f7d2b4c6e8a1  add_facility_hierarchy_doctor_profile
                                           │      └─ b3d7e91f6a24  add_symptom_catalogue
                                           └─ f8a1b2c3d4e5  add_staff_doctor_assignments
                                                  └─ f8a2b3c4d5e6  add_platform_audit_events
                                                          └─ a9c4e1f7b2d8  ← MERGE(b3d7e91f6a24, f8a2b3c4d5e6)
```

- **One head: `a9c4e1f7b2d8`.** The live database's `alembic_version` holds exactly that single row (§7). **The live schema and the local migration graph agree exactly.**
- 14 revisions, one fan-out at `e6c1a9b3d5f8` (two children), one merge at `a9c4e1f7b2d8`.

### 8.2 The target adds two revisions — 14 of 16 files are byte-identical to this host's

Target `backend/alembic/versions/` (tree `8d7ff1d03c4b023ce0401dd60c4c7ed7bb182d6e`, read with `truncated: false`) holds **16** files. Comparing blob SHA-1s (§1.4):

| File | Size | Target blob | Local blob (`git hash-object`) | Same? |
|---|---|---|---|---|
| `3c8e5d0a9b2f_add_patient_age.py` | 974 | `1b9f2cd9…` | `1b9f2cd9…` | identical |
| `5f3fce6757cf_initial_schema.py` | 12 014 | `45ba64f5…` | `45ba64f5…` | identical |
| `9d8a1f2b3c4d_add_staff_doctor_link.py` | 1 132 | `e8461145…` | `e8461145…` | identical |
| `a1f2b3c4d5e6_add_tracking_tokens.py` | 1 498 | `77169423…` | `77169423…` | identical |
| **`a7c3f19d2b64_add_queue_announcement_deliveries.py`** | **4 372** | **`8fbb4455…`** | **absent locally** | **NEW** |
| `a9c4e1f7b2d8_appointment_types_and_capacity_integrity.py` | 12 082 | `816390ba…` | `816390ba…` | identical |
| `b3d7e91f6a24_add_symptom_catalogue.py` | 9 272 | `dc430859…` | `dc430859…` | identical |
| `b7c1e4d90a52_add_notifications.py` | 3 979 | `348606d6…` | `348606d6…` | identical |
| **`c4d8e2a91f60_add_voice_packs_and_platform_config.py`** | **6 327** | **`eb21e8fc…`** | **absent locally** | **NEW** |
| `c7d3601e2486_add_audit_branch.py` | 868 | `6c147547…` | `6c147547…` | identical |
| `ccf34da72c1b_add_queue_sequences.py` | 1 110 | `34891d4d…` | `34891d4d…` | identical |
| `d4b2c8e1f7a3_add_login_attempts.py` | 2 342 | `c2526d62…` | `c2526d62…` | identical |
| `e6c1a9b3d5f8_drop_redundant_tracking_token_index.py` | 1 807 | `1fd1f67f…` | `1fd1f67f…` | identical |
| `f7d2b4c6e8a1_add_facility_hierarchy_doctor_profile.py` | 20 967 | `9fc055bc…` | `9fc055bc…` | identical |
| `f8a1b2c3d4e5_add_staff_doctor_assignments.py` | 5 407 | `9dcbaead…` | `9dcbaead…` | identical |
| `f8a2b3c4d5e6_add_platform_audit_events.py` | 2 462 | `3e72ca2a…` | `3e72ca2a…` | identical |

**No existing revision is edited, renumbered or deleted.** The two new revisions are purely additive. That is the good news. The bad news is §8.3.

### 8.3 The target has **two Alembic heads** — verified from the target's own files

```
f8a2b3c4d5e6  add_platform_audit_events
   ├─ a9c4e1f7b2d8  ← MERGE(b3d7e91f6a24, f8a2b3c4d5e6)   ← the live database is here
   └─ a7c3f19d2b64  add_queue_announcement_deliveries       ← NEW, revises f8a2b3c4d5e6
          └─ c4d8e2a91f60  add_voice_packs_and_platform_config   ← NEW, revises a7c3f19d2b64
```

`a7c3f19d2b64` declares `down_revision = 'f8a2b3c4d5e6'` — **not** `a9c4e1f7b2d8`, the revision that the local tree and the live database consider the head. Because `f8a2b3c4d5e6` already has the merge `a9c4e1f7b2d8` as a child, adding `a7c3f19d2b64` as a second child **creates a second head**.

The target commit says so itself. Quoted verbatim from the docstring of `backend/alembic/versions/c4d8e2a91f60_add_voice_packs_and_platform_config.py` at `2fc007a`:

> "``down_revision`` is ``a7c3f19d2b64`` (the QUE-006/W2 delivery-claim table), the newest revision present in this working tree. That revision currently declares ``down_revision = 'f8a2b3c4d5e6'`` instead of the true head ``a9c4e1f7b2d8``, **which creates a second Alembic head**; the defect is recorded in ``docs/implementation/QUE-006_W2_PRE_COMMIT_REVIEW_REPORT.md`` and is *not* fixed here (W2 is out of this task's scope). Once W2's revision is reparented to ``a9c4e1f7b2d8`` this migration follows it correctly with no further change."

So the head set at the target is **{`a9c4e1f7b2d8`, `c4d8e2a91f60`}**, and it is a **known, documented, deliberately-unfixed defect in the commit being deployed**. Its operational consequence is in §9.2 (R-1).

### 8.4 What the two new revisions would create

Read from the target files (both are idempotent: each object is created only when absent, and neither alters any existing table, column, constraint or row).

**`a7c3f19d2b64` — `queue_announcement_deliveries`** (QUE-006 / W2 cross-terminal delivery claim):

| Column | Type | Notes |
|---|---|---|
| `id` | `String` | primary key |
| `organization_id` | `String` | **not null**, FK → `organizations.id` |
| `branch_id` | `String` | nullable, FK → `branches.id` |
| `queue_entry_id` | `String` | **not null**, FK → `queue_entries.id` |
| `call_event_id` | `String(120)` | **not null**, **UNIQUE** (`queue_announcement_deliveries_call_event_id_key`) — "the first terminal to insert the claim wins and every later terminal is refused" |
| `language`, `voice_pack_id`, `transport`, `outcome_reason` | `String(8/80/20/120)` | not null, `''` default |
| `voice_pack_version` | `Integer` | not null, `0` default |
| `requested_by` | `String` | not null (FK-looking, **no** FK declared) |
| `requested_by_role` | `String(30)` | nullable |
| `requested_at` | `DateTime(timezone=True)` | not null |
| `status` | `String(24)` | not null, `'requested'` default; progresses to `completed` / `failed` / `blocked` / `interrupted` / `skipped_busy` |
| `outcome_at` | `DateTime(timezone=True)` | nullable |

Indexes: `idx_queue_announcement_entry (queue_entry_id)`, `idx_queue_announcement_org_time (organization_id, requested_at)`. Retention: "rows are never deleted by this migration or by the application".

**`c4d8e2a91f60` — `voice_packs` and `announcement_platform_config`** (QUE-006 / W3):

- `voice_packs` — 26 columns keyed by `id String(80)`: `organization_id` (nullable = platform-wide), `language`, `voice_name`, `version`, `status`, `base_path`, `manifest` (JSON), `manifest_checksum`, `compatibility` (JSON), `available_to_organizations` (bool, default false), validation trio (`validation_status/problems/validated_at`), review quartet (`review_status/reviewed_by/reviewed_at/review_note`), publish/retire timestamps, `created_by/created_at/updated_at`. Unique `(organization_id, language, voice_name, version)`; FK → `organizations.id`; indexes `idx_voice_packs_scope_language`, `idx_voice_packs_status`.
- `announcement_platform_config` — `id String(20)`, `language String(8)` default `'bn'`, `voice_packs` (JSON), `updated_by`, `updated_at`.

**These three tables do not exist in the live database — VERIFIED by catalog lookup, not inferred:**

```
select to_regclass('public.queue_announcement_deliveries'),
       to_regclass('public.voice_packs'),
       to_regclass('public.announcement_platform_config'),
       to_regclass('public.queue_entries');
→ ABSENT | ABSENT | ABSENT | queue_entries
```

### 8.5 Everything else that differs at the target

The replacement is not only a migration change. Commit-pinned tree reads establish:

| Area | Local (this host) | Target `2fc007a` | Same? |
|---|---|---|---|
| `backend/alembic/versions/` | 14 files | 16 files (the two above added) | **differs** (additive) |
| `backend/queuing/` | `__init__.py`, `display.py`, `main.py`, `recovery.py` (+ `Dockerfile`, `requirements.txt`, `migrations/`, `tests/`) | adds **`announcements.py` (13 756 B)** and **`events.py` (4 799 B)** | **differs** |
| `frontend/lib/announcements/` | `content.js`, `controller.js`, `dedupe.js` (untracked), `speech-synthesis.js` | **8 modules**: `call-announcer.js` (7 637), `content.js` (6 987), `controller.js` (13 930), `delivery.js` (8 228), `queue-transitions.js`, `segments.js` (8 140), `speech-synthesis.js` (13 898), `voice-packs.js` (5 909) | **differs** — target has five modules that do not exist here, and **no** `dedupe.js` |
| `frontend/public/` | tracked `WEBSITE_CONTENT_PROPOSAL.md` only | **`audio/` tree only**: `audio/bn/number/digit-*` and `audio/en/number/digit-*` recordings in `m4a` + `mp3` + `wav`, `audio/en/phrase/{no-room,proceed-to-room,room-suffix,token-number}` in `mp3` + `wav`, and `audio/manifest.json` (53 888 B) — **binary recordings, no `WEBSITE_CONTENT_PROPOSAL.md`** | **differs, both ways** |
| `backend/common/locations.py` | present (untracked, 1 of the 8 untracked files) | **404 — not present** | **local-only file** |
| `_tools/`, `.github/`, `ai_factory/`, `docker-compose*.yml`, `.env.example`, `backend/seed/seed_demo.py`, all frontend build files | — | byte-identical (§4.2, §4.3) | **identical** |

`frontend/lib/announcements/` blob comparison makes the divergence concrete: local `content.js` `1e0eebd1…` vs target `efb1f4a1…`; local `controller.js` `5587c3be…` vs target `1cbed8f2…`; local `speech-synthesis.js` `ca2f4361…` vs target `ea828280…`. **The two sides are different implementations of the same feature** — the Ubuntu F1–F4 corrections here, the Windows W1–W6 workstream there. There is no file-level merge; the replacement is a whole-feature substitution.

---

## 9. Startup and database compatibility risks

### 9.1 What this replacement will *not* prove — read this before celebrating a green stack

The target commit's own message says: *"a commit is not a verification, and the API suite, the migration and the browser run remain unexecuted."* Nothing in this pre-flight closes that gap. After the procedure in §10:

- A healthy container means the process started and `/health/ready` answered — **not** that the W2/W3 announcement endpoints work.
- **No test suite will have run.** The backend suite needs a database and the frontend suite needs `node`; neither is part of the documented rebuild path in §10. If the owner wants the target's suites executed, that is a separate, explicitly authorised task.
- **Nothing will have been exercised in a browser** — including audio playback, which is the whole point of the W1–W6 workstream.
- The migration will have been applied to the **development** database only; the isolated `amsdp_demo` database (`amsdp_demo_amsdp_demo_pg_data`, no container running) stays at `a9c4e1f7b2d8` and will need the same two revisions before the demo stack is usable.

### 9.2 R-1 — the target has two Alembic heads, so `alembic upgrade head` will fail (severity **HIGH**)

| Field | Value |
|---|---|
| Evidence | §8.3: `a7c3f19d2b64.down_revision = 'f8a2b3c4d5e6'` while `a9c4e1f7b2d8` (live) is that revision's other child; heads = {`a9c4e1f7b2d8`, `c4d8e2a91f60`}. The target's own `c4d8e2a91f60` docstring names the defect and states it is deliberately unfixed. |
| Effect | Any `alembic upgrade head` aborts with *"Multiple head revisions are present for given argument 'head'"*. It does **not** corrupt anything — it refuses to run. |
| Blast radius | Migration only. Containers start regardless (nothing in compose runs alembic — §9.3). |
| Mitigation in §10 | Apply the **named** head: `alembic upgrade c4d8e2a91f60`. Then verify with `alembic current` (two rows: `a9c4e1f7b2d8`, `c4d8e2a91f60`). |
| Permanent fix (owner item) | Reparent `a7c3f19d2b64` to `a9c4e1f7b2d8`, or add a merge revision — a change to the target tree, **not** part of this pre-flight. Recorded as O-R1 (§12). |
| Assumption | That `alembic` behaves per its documented multiple-head rule. Standard tool behaviour; **not** executed here (running it would have violated the read-only mandate). |

### 9.3 R-2 — nothing in this stack applies migrations (severity **HIGH**)

| Field | Value |
|---|---|
| Evidence | `grep -nE 'alembic|upgrade'` over `docker-compose.yml`, `_tools/amsdp_stack.sh`, `_tools/amsdp_rebuild.sh`, `_tools/amsdp_autostart.sh` returns **no alembic invocation**. The compose file has no migration service, no entrypoint override, and no init hook. `_tools/amsdp_rebuild.sh` explicitly lists what it does *not* do: "never runs `down`, never removes a volume, never re-seeds or resets". |
| Effect | Replacing the source and rebuilding the images leaves the database at `a9c4e1f7b2d8` with **none** of the three new tables. The images then run code that expects them. |
| Mitigation in §10 | Step 8 applies the migration manually with the published host port (`127.0.0.1:5433`), using the same pattern the demo compose header documents (`cd backend && AMSDP_DATABASE_URL=… python -m alembic upgrade …`). |

### 9.4 R-3 — the boot-time autostart seed runs target code against the live database (severity **LOW**)

| Field | Value |
|---|---|
| Evidence | `amsdp-autostart.service` is enabled (§6.5) and runs `_tools/amsdp_autostart.sh`, which runs `_tools/amsdp_stack.sh up` and then the idempotent demo seed with `.venv/bin/python`. `backend/seed/seed_demo.py` is **byte-identical** at the target (`6cb598af…`, §4.2) and the seed's tables are untouched by the two new revisions. |
| Effect | The seed keeps working: same file, same tables, same schema. It will simply run *after* the replacement instead of before, re-dating the demo board and re-hashing the demo passwords from `.env`. |
| Residual risk | The autostart unit fires on a **user** login/boot, not on the replacement. If the migration in §10 step 8 has not run yet and the host reboots in between, the seed still succeeds (it touches no new table) — but the W2/W3 features remain broken until step 8 runs. |
| Not verified | That the seed's own imports still resolve under the target's `backend/common/` (the target has no `locations.py`; the seed was not read line-by-line). **ASSUMPTION:** safe, because the seed file is byte-identical to a file that runs successfully today against the same `backend/common/` modules the target keeps unchanged. |

### 9.5 Remaining risks — R-4 to R-11

| ID | Risk | Severity | Evidence | Mitigation |
|---|---|---|---|---|
| **R-4** | **Feature breakage until migrated**: any endpoint or page that touches `queue_announcement_deliveries`, `voice_packs` or `announcement_platform_config` raises `UndefinedTable` → HTTP 500. | **HIGH** | §8.4 — the three tables are `ABSENT`; `backend/queuing/announcements.py` and the eight `frontend/lib/announcements/*` modules ship in the same commit and expect them | §10 step 8 (migration) — then re-probe |
| **R-5** | **Stale images**: restart/recreate without `--build` runs 2026-11-17 code. | **HIGH** | §6.3 — images built 2026-11-17 07:44, no source-commit label; `_tools/amsdp_rebuild.sh` header states restart restarts the OLD image | §10 step 7 must **build**, not just restart |
| **R-6** | **Local commits and the website-content file are lost** unless rescued first. | **MEDIUM** | §2.2, §3.3 — `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` exists only in the two local commits and is absent at the target | §10 step 2 creates a rescue branch; §10 step 6 removes exact paths only, never `git clean -fdx` |
| **R-7** | **Leftover local-only files shadow the target**, e.g. `backend/common/locations.py`, `frontend/lib/announcements/dedupe.js`, `backend/tests/test_queue_room_snapshot.py`, `frontend/tests/queue-announcement-dedupe.test.mjs`. Untracked files are **not** removed by a checkout. | **MEDIUM** | §2.3 (the 8 untracked entries); §8.5 (how far the two implementations diverge) | §10 step 6 lists the exact paths to delete; no blanket clean |
| **R-8** | **A binary-asset tree arrives that this host has never held** (Bangla and English digit/phrase recordings in three container formats, plus a 53 888 B manifest) and `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` disappears. | **LOW** | §8.5; the blobs carry real binary sizes, and no Git LFS pointers are involved | Nothing to do beyond a normal checkout; the frontend image rebuild copies `public/` |
| **R-9** | **No idempotent re-application path for the schema**: if someone runs `alembic upgrade heads` instead of the named revision on a two-head graph, behaviour depends on Alembic's ordering; if they run `upgrade head`, it aborts (R-1). | **MEDIUM** | §8.3, §9.2 | Always name the revision; record `alembic current` output |
| **R-10** | **`audit_events` growth is irreversible**: any rollback that restores a dump rewinds 19 694 append-only rows. | **MEDIUM (governance)** | §7; `.clinerules` §3 | §11.3 — prefer forward-fix; restore into a **new** database, never over the live one, without explicit owner approval |
| **R-11** | **Demo database drifts behind**: `amsdp_demo` stays at `a9c4e1f7b2d8`, so the demo stack would fail the same way once started. | **LOW** | §9.1; demo volume exists, no demo container running | Apply the same named-revision upgrade to `amsdp_demo` when the demo stack is next used |

**Risks that were checked and did *not* materialise** (recorded so the owner knows they were considered rather than forgotten):

- **No port conflict** with the four neighbouring Docker stacks (§6.4).
- **No dependency drift**: `package.json` / `package-lock.json` / frontend build config identical (§4.2).
- **No secret rotation needed**: `AMSDP_JWT_SECRET` unchanged on both sides; `.env` survives and stays ignored (§4.1, §4.2).
- **No new Python dependency for the queue service**: `backend/queuing/requirements.txt` and `backend/queuing/Dockerfile` are byte-identical at the target (`0375dab0…`, `a012ad8f…`).
- **No data migration**: both new revisions are pure `create_table`/`create_index` — no `ALTER`, no `UPDATE`, no backfill (§8.4).
- **No volume reset**: nothing in `_tools/` or compose removes a volume; `_tools/pg_backup.sh` is the sanctioned dump path.

### 9.6 What "discard the Ubuntu changes" removes, precisely

| Group | Paths | Fate |
|---|---|---|
| 13 modified tracked files | `.gitignore`, `backend/appointment/main.py`, `backend/queuing/main.py`, `backend/queuing/recovery.py`, `docs/governance/AMSDP_Docs_Index_V1.0.md`, `frontend/lib/announcements/{content,controller,speech-synthesis}.js`, `frontend/pages/queue.js`, 4 × `frontend/tests/queue-announcement*.test.mjs` | **Reverted to the target's version** by the checkout. For the 4 announcement modules the target's version is a *different implementation* (§8.5), not merely a loss of local edits. |
| 8 untracked files | `backend/common/locations.py`, `backend/tests/test_queue_room_snapshot.py`, `frontend/lib/announcements/dedupe.js`, `frontend/tests/queue-announcement-dedupe.test.mjs`, 3 × `docs/…` reports, `docs/implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md` | **Left in place by a checkout** (untracked ≠ removed). §10 step 6 deletes the 4 code/test files explicitly; the 4 documents should be *preserved*, not deleted — they are the only copies of that evidence. |
| 2 local commits | `0554f33`, `cd2f9ec` (`frontend/public/WEBSITE_CONTENT_PROPOSAL.md`) | **Unreachable from the branch** after the move unless a rescue ref is created first (§10 step 2). |
| Everything gitignored | `.env`, `ai_factory/.env`, `.venv`, `backups/`, `runs/`, `var/`, `node_modules` | **Untouched** (§5). |

### 9.7 Predicted startup sequence after the replacement — ASSUMPTION, not observed

Built from the read target code and the observed compose health checks. **Not executed.**

1. `docker compose … build` succeeds (same Dockerfile, same lockfile, same requirements files).
2. `up -d` recreates the 10 containers; each backend waits for `db: service_healthy`, then serves and answers `/health/ready`.
3. **Health is schema-agnostic**: the probes hit `/health/ready`, which the observed stack answers without touching announcement tables. Expect **10/10 healthy even before the migration** — which is exactly why a green `docker compose ps` must not be read as "the replacement worked" (§9.1).
4. Any request reaching the W2 delivery-claim endpoint or the W3 voice-pack/config endpoints **before step 8** fails with a PostgreSQL `UndefinedTable` error surfacing as HTTP 500.
5. The next login/boot fires `amsdp-autostart.service` → stack up (no-op) → demo seed (unchanged file) → success.

---

## 10. Exact replacement procedure (owner-executed)

**Nothing in this section was executed.** Each step is written to be verifiable, with a decision point where a failure must stop the run. `<TS>` is a timestamp such as `20261122-1530`. Run from `/home/shomonrobie/amsdp` unless stated.

### Step 0 — Pre-conditions (abort if any fails)

```bash
cd /home/shomonrobie/amsdp
git rev-parse HEAD                     # expect cd2f9ecdf51b363105214e3ffd504d3adc151ada
git status --short -uall | wc -l       # expect 21 (13 M + 8 ??)
docker compose -p amsdp -f docker-compose.yml ps      # expect 10/10 "Up ... (healthy)"
docker compose -p amsdp -f docker-compose.yml exec -T db \
  psql -U amsdp -d amsdp -Atc 'select version_num from alembic_version'   # expect a9c4e1f7b2d8
df -h /                                # expect > 5 GB free so far: 506 GB
```

If the stack is not 10/10 healthy *before* the replacement, stop: a new failure could not then be distinguished from an old one.

### Step 1 — Back up the database (the only irreplaceable state)

```bash
_tools/pg_backup.sh backups            # writes backups/amsdp_amsdp_<TS>.sql.gz
ls -l backups/ | tail -3               # confirm the new dump exists and is not empty
```

`_tools/pg_backup.sh` uses the `pg_dump` **inside** the `postgres:16` container (version-matched to the server) and emits a `--clean/--if-exists` plain SQL dump; it is safe while the stack is up. This dump is also the rollback material for §11.

### Step 2 — Rescue the local history before anything moves

```bash
git branch rescue/ubuntu-<TS> HEAD                        # keeps 0554f33 + cd2f9ec reachable
git rev-parse rescue/ubuntu-<TS>                          # expect cd2f9ec...
git bundle create /tmp/amsdp-ubuntu-<TS>.bundle --all     # optional off-repo copy
```

Rationale: §3.3 could not prove that `cd2f9ec` is an ancestor of the target, and the target's `frontend/public` tree does not contain the file those commits add. A rescue branch costs nothing and removes R-6.

### Step 3 — Fetch and pin the target

```bash
git fetch origin
git rev-parse origin/hackathon-mvp             # expect 2fc007a3f7a96639c3df36341c6081cee4d24a48
git cat-file -e 2fc007a3f7a96639c3df36341c6081cee4d24a48^{commit} && echo "object present"
git rev-parse origin/hackathon-mvp^{tree}      # expect b3e1356298d14a130599cb599d3d24c5cba86af7
```

If either SHA differs from those two values, **stop**: the remote has moved since this pre-flight, and every statement in §8 about the target's contents would need re-verification before continuing.

### Step 4 — Switch the working tree to the target

```bash
git checkout -f 2fc007a3f7a96639c3df36341c6081cee4d24a48               # detached HEAD; discards the 13 modifications
git branch -f hackathon-mvp 2fc007a3f7a96639c3df36341c6081cee4d24a48   # only if the branch should follow the remote
git checkout hackathon-mvp
git status --short -uall | head                                        # expect ONLY untracked leftovers + this report
```

`-f` is deliberate: it discards the 13 tracked modifications the owner has approved. It does **not** delete untracked files — that is step 6.

### Step 5 — Prove the checkout is what was inspected

```bash
git rev-parse HEAD                              # 2fc007a3f7a96639c3df36341c6081cee4d24a48
git rev-parse HEAD^{tree}                       # b3e1356298d14a130599cb599d3d24c5cba86af7
ls backend/alembic/versions/*.py | wc -l        # 16
git hash-object backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py
                                                # 8fbb44551a3deb614cf3822182733a552c5f685a
git hash-object backend/alembic/versions/c4d8e2a91f60_add_voice_packs_and_platform_config.py
                                                # eb21e8fc5542b6ce7bc54ccb25f516d0949b8d1a
ls frontend/lib/announcements/                  # 8 modules, no dedupe.js
ls frontend/public/                             # audio/ only
```

### Step 6 — Remove the four local-only code/test leftovers (exact paths, no blanket clean)

```bash
rm -f backend/common/locations.py \
      backend/tests/test_queue_room_snapshot.py \
      frontend/lib/announcements/dedupe.js \
      frontend/tests/queue-announcement-dedupe.test.mjs
```

Deliberately **not** removed: `docs/implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md`, `docs/implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md`, `docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md`, `docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md`, and **this report** — they are the only copies of that evidence on this host. If a pristine working copy is required, move them out of the tree (e.g. `mv … /home/shomonrobie/archive/`) rather than deleting them. **Never** run `git clean -fdx`: it would also destroy `.env`, `backups/` and `.venv` (§5).

### Step 7 — Rebuild and recreate every image (build, not restart)

```bash
docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep amsdp > /tmp/amsdp-images-before-<TS>.txt   # rollback asset
_tools/amsdp_rebuild.sh --all        # or: docker compose -p amsdp -f docker-compose.yml build
                                     #      docker compose -p amsdp -f docker-compose.yml up -d
docker compose -p amsdp -f docker-compose.yml ps        # all 10 recreated, new Created timestamps
docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}}' | grep amsdp
```

Record the **old** image IDs (§6.3) before this step: they are the exact-runtime rollback asset (§11.4). With no `.dockerignore` (§4.4) the first build is slow; 506 GB free is ample.

### Step 8 — Apply the schema change, by *named* revision

```bash
set -a; . ./.env; set +a        # POSTGRES_PASSWORD, never echoed
cd backend
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp" \
  ../.venv/bin/python -m alembic upgrade c4d8e2a91f60
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp" \
  ../.venv/bin/python -m alembic current        # expect BOTH a9c4e1f7b2d8 and c4d8e2a91f60
cd ..
```

- **`upgrade head` will fail** (§9.2). Naming `c4d8e2a91f60` walks `f8a2b3c4d5e6 → a7c3f19d2b64 → c4d8e2a91f60`, the missing branch; the `a9c4e1f7b2d8` branch is already applied and stays recorded.
- Credentials come from `.env` and are never printed. If `alembic` is not installed in `.venv`, run it inside a container that ships `backend/` (e.g. `docker compose … exec -T queuing python -m alembic upgrade c4d8e2a91f60`), or install it into a throwaway venv — **do not** silently mutate `.venv`.

### Step 9 — Verify the schema landed

```bash
docker compose -p amsdp -f docker-compose.yml exec -T db \
  psql -U amsdp -d amsdp -Atc "select to_regclass('public.queue_announcement_deliveries'), \
    to_regclass('public.voice_packs'), to_regclass('public.announcement_platform_config')"
# expect: queue_announcement_deliveries|voice_packs|announcement_platform_config
docker compose -p amsdp -f docker-compose.yml exec -T db \
  psql -U amsdp -d amsdp -Atc "select version_num from alembic_version order by 1"
# expect two rows: a9c4e1f7b2d8 and c4d8e2a91f60
docker compose -p amsdp -f docker-compose.yml exec -T db \
  psql -U amsdp -d amsdp -Atc "select count(*) from audit_events"
# expect >= 19694  -- the audit trail must not have been rewritten (.clinerules §3)
```

### Step 10 — Operational smoke check (not verification)

```bash
_tools/amsdp_rebuild.sh --verify          # read-only probe of the running stack
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3100/                 # expect 200/307
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3100/appointments
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3100/queue
journalctl --user -u amsdp-autostart.service -n 40 --no-pager | tail -20
```

Then, and only then, a human logs in with a demo account and exercises the queue announcement path in a browser. **Until that happens the W1–W6 workstream is IMPLEMENTED, not VERIFIED** (§9.1).

### Step 11 — Record the outcome

Write a short completion record to `docs/implementation/` stating: the commit deployed, the `alembic current` output, the `to_regclass` output, the container table, the `audit_events` count before/after, and exactly what was **not** exercised. Per `.clinerules` §6/§7 that record must keep IMPLEMENTED / TESTED / VERIFIED distinct.

---

## 11. Rollback

### 11.1 Decision order — cheapest reversible act first

1. **Redeploy the old code from the rescue branch** (§11.2) — no database change, no data loss.
2. **Restore the pre-replacement dump into a new database** and repoint the stack — no live data rewritten (§11.3).
3. **Overwrite the live database from a dump** — last resort, owner-approved only (§11.3, R-10).
4. **Retag the retained images** (§11.4) when the goal is to return to the *exact* runtime rather than to a rebuild of the old commit.

### 11.2 Code rollback (no database involvement)

```bash
cd /home/shomonrobie/amsdp
git checkout -f rescue/ubuntu-<TS>          # or exactly cd2f9ecdf51b363105214e3ffd504d3adc151ada
git status --short -uall                    # expect the original 21 entries back
_tools/amsdp_rebuild.sh --all               # rebuild images from that source
docker compose -p amsdp -f docker-compose.yml up -d
```

A rebuild from `cd2f9ec` does **not** reproduce the images that were running before the replacement (they were built 2026-11-17, three days earlier — §6.3). If exact-runtime restoration matters, use §11.4 instead.

### 11.3 Database rollback — and the governance constraint that bounds it

Both new revisions are additive and each has a `downgrade()` that drops only what it created:

```bash
cd backend
AMSDP_DATABASE_URL="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp" \
  ../.venv/bin/python -m alembic downgrade a9c4e1f7b2d8
# drops announcement_platform_config, voice_packs, queue_announcement_deliveries
```

That is safe **only while those tables hold nothing worth keeping**. Announcement delivery rows are themselves an audit record of "who announced what, when" — deleting them is a data-loss act that needs owner approval, exactly like any other audit deletion.

Restoring a dump (`backups/amsdp_amsdp_<TS>.sql.gz`, `--clean/--if-exists`) **rewinds `audit_events` from whatever it then holds back to 19 694 rows**. `.clinerules` §3 states the audit trail is append-only and must never be deleted, truncated or rewritten. Therefore:

- **Preferred:** restore into a **new** database (`amsdp_rollback`) and point `AMSDP_DATABASE_URL` at it, leaving the live database and its audit trail intact and inspectable.
- **Never** overwrite the live `amsdp` database without an explicit, per-act owner decision recorded under `docs/decisions/`.
- Restoring *forward* into another environment is unaffected by this constraint.

### 11.4 Exact-runtime rollback via the retained images

The pre-replacement images still exist and are the only byte-exact copy of the running code (§6.3, §5 row 6):

```bash
docker tag 472611afa809 amsdp-queuing:pre-replacement      # and the other eight, by recorded ID
docker tag 3b0c02b17d87 amsdp-frontend:pre-replacement
docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep amsdp
# compare against /tmp/amsdp-images-before-<TS>.txt from §10 step 7
```

Building `2fc007a` overwrites the `amsdp-<service>:latest` tags, so record the old IDs **before** step 7 and re-tag afterwards if they must stay addressable. **Do not** prune images while the replacement is unsettled.

---

## 12. Open items for the Product Owner

| ID | Item | Why it is open | Suggested owner decision |
|---|---|---|---|
| **O-R1** | **Reparent `a7c3f19d2b64`** to `a9c4e1f7b2d8` (or add a merge revision) in the target tree. | The target ships a two-head graph and documents the defect as deliberately unfixed (§8.3, R-1). Until fixed, `alembic upgrade head` is unusable and every future migration inherits the ambiguity. | Approve a follow-up commit on `hackathon-mvp`; apply migrations by *named revision* until then (§10 step 8). |
| **O-R2** | **Decide whether the three new tables are created before or after the first W2/W3 click.** | Health checks pass without them, so a green stack can hide a broken feature (§9.7.3–4). | Create them in the same maintenance window as the rebuild (§10 step 8), not later. |
| **O-R3** | **Preserve the four untracked QUE-006 documents** (this report, the F1–F4 corrections report, the local audio architecture plan, the ChatGPT handover) outside the working tree. | They are the only copies of that evidence; a checkout leaves them, but they would linger untracked in a tree that no longer contains the code they describe (§9.6). | Move them to an archive path, or commit them on the rescue branch. |
| **O-R4** | **Register this report in `docs/governance/AMSDP_Docs_Index_V1.0.md`.** | Deferred deliberately — see §13.3. | Owner or a docs task pastes the prepared row (below the table) into the `implementation/` table, after resolving the filename question. |
| **O-R5** | **`amsdp_demo` database will drift behind.** | It stays at `a9c4e1f7b2d8`; the demo stack would exhibit the same feature breakage (R-11). | Apply the same named-revision upgrade when the demo stack is next started. |
| **O-R6** | **Decide when the target's suites are actually run.** | Neither the commit nor this pre-flight ran them (§9.1; the commit message says so itself). | Authorise a separate test task after the replacement, with the results recorded per §7 of `.clinerules`. |
| **O-R7** | **Add `.dockerignore` files** (observation, not a blocker). | Build contexts ship `node_modules`/`__pycache__`; unrelated to this replacement (pre-existing, §4.4). | Defer; note for CI build-time work. |
| **O-R8** | **Consider a source-commit image label.** | Images carry no commit identity, so "which code is running?" cannot be answered from Docker metadata (§6.3). | Defer; a build-arg label in the Dockerfiles would make future pre-flights cheap. |

**O-R4 — the prepared index row.** Row shape taken from the index itself (`implementation/` table, alongside `AMSDP_M6_Implementation_Report.md` at line ~883): ``| `NAME.md` | size | read-when | flags |``.

```text
| `AMSDP_Ubuntu_Replacement_Preflight_Report_V1.0.md` | 77,284 | Planning any replacement of this working copy with a remote commit, or any environment pre-flight | — |
```

Two things to settle before pasting it:

1. **Filename.** The file on disk is `AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` (the name this task specified); the row above uses the `AMSDP_<Topic>_<Version>.md` convention (`.clinerules` §11). A rename is a *recorded migration act* (§11: manifest entry, byte-for-byte check), so either register the current name or rename and record it — index and file must agree.
2. **Size.** `77,284` bytes is the size at the time of writing; the index's *Maintenance* command recomputes sizes, so refresh it if the report changes first.

---

## 13. Governance and skill compliance

### 13.1 Applicable governance documents and skills (`.clinerules` §4 routing)

The task spans several §4 rows; each listed document either shaped this report or was not needed.

| Domain row | Governance applied | How it shaped this document |
|---|---|---|
| Evidence standard (§7) | `.clinerules` §3, §7, §9 | Every claim carries VERIFIED / ASSUMPTION / BLOCKED; no test suite is claimed to have run; a green stack is explicitly refused as proof (§9.1). |
| Documentation: reading docs, writing reports, placement | `.clinerules` §11, §12; `docs/governance/AMSDP_Docs_Index_V1.0.md` | Report written under `docs/implementation/`; index registration deferred with reasons (§13.3). |
| Deployment / Docker / infrastructure | `saas-cicd-workflow.md` **as adapted** in `docs/governance/AMSDP_Engineering_Governance_Assessment.md` §3 (git safety, honest CI state), `docker-compose.yml`, `_tools/*` | §10 forbids destructive git operations and `git clean`, and refuses to claim CI/test state that was not observed. |
| Database schema / migrations | `saas-multitenant-data.md` §4–§5 **as adapted**, the Alembic chain, `backend/common/models.py` | §8 treats the migration graph as the primary compatibility artefact and checks the tenant key on both new tables. |
| Audit / data integrity | `saas-observability.md` **as adapted**, `backend/common/audit.py`, Business Rules Part X | §7 and §11.3 protect the append-only audit trail; R-10 states the constraint. |

**Skills: none installed.** `.clinerules` §5 records that no skill packages exist in this workspace (no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). **No skill was used and none is claimed** — the governance documents above are the prescribed substitute.

**What was actually opened this session, versus cited as a routing target** — stated because `.clinerules` §12 forbids describing a document that was not read:

- **Opened and used:** `.clinerules` (read in full as the governing rules), `docs/governance/AMSDP_Docs_Index_V1.0.md` (header and the `implementation/` table row format, to confirm the correct row shape for O-R4), `docker-compose.yml`, `docker-compose.demo.yml` (header), `_tools/amsdp_rebuild.sh`, `_tools/amsdp_stack.sh`, `_tools/amsdp_autostart.sh`, `_tools/pg_backup.sh` (headers and the lines those scripts execute), `.gitignore` at the target, both new target migrations, the target `backend/queuing/events.py`, and this host's `backend/alembic/versions/*` revision headers.
- **Cited only as the §4 routing target, *not* opened here:** `docs/governance/AMSDP_Engineering_Governance_Assessment.md` (the adaptation source for the `saas-*` rule files), `docs/product/AMSDP_Business_Rules_V1.0.md` Part X, `backend/common/models.py`. No claim in this report depends on their wording; where an audit-trail rule was applied, the rule applied was `.clinerules` §3 itself.

**Deliberate non-applications:** the frontend, auth and queue rows were touched only as *evidence subjects*; `saas-frontend-ux.md`, `saas-auth-and-authorisation.md` and `saas-api-throttling.md` were not needed to answer any of the ten questions and are not claimed as applied.

### 13.2 Non-negotiables check (`.clinerules` §3)

| Non-negotiable | Status in this work |
|---|---|
| Never log or expose secrets / tokens / keys | **Honoured.** Only `.env` **key names**, sizes and ignore status are recorded; no value is printed (§4.1). DSN examples use `${POSTGRES_PASSWORD}` symbolically. |
| Enforce access server-side; never trust the body | Not exercised (no auth code touched). |
| Cross-tenant access fails closed with 404 | Not exercised. Both new tables carry `organization_id` (+ `branch_id` FK) — recorded in §8.4 as an observation, **not** as a verification of isolation behaviour. |
| Tenant key is `organization_id` | Observed and respected: `queue_announcement_deliveries` and `voice_packs` both hang off `organizations.id`; no second tenant column appears. |
| Audit events append-only and persistent | Protected in §11.3 / R-10: no rewrite path is proposed without explicit owner approval. |
| Denials recorded, never silently swallowed | Not exercised. |
| Every schema change ships as a forward-only, idempotent Alembic migration | Observed: both new revisions are idempotent and additive — **but the chain is not single-headed**, which is O-R1. |
| Never claim an unverified capability | **Honoured**: §9.1 refuses to treat a healthy stack as verification. |
| No skill/tool used merely because it was discovered | **Honoured**: no skill exists; the commit-pinned HTTPS reads were used only because a `fetch` was forbidden and the comparison needed the target's bytes. |
| No destructive git (`reset --hard`, `clean -fd`, `stash`, `checkout .`) | **Honoured**: none run; §10 warns against `clean -fdx` and gives explicit `rm -f` paths instead. |
| Do not stage or commit | **Honoured**: nothing staged, nothing committed (§13.4). |

### 13.3 Documentation placement, and why the index registration is deferred

- **Placement:** `docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` — subject folder `implementation/`, existing folder reused, no new folder created (§11). Filename follows `AMSDP_<Topic>_<Version>.md` (§11).
- **No collision:** `docs/implementation/` was listed before writing; no file matching `*preflight*` existed (`ls docs/implementation | grep -i preflight` → none).
- **Not written anywhere else:** nothing was added to `ai_factory/docs/`; `/tmp/ubupre/` is scratch only (§1.5); no AMSDP report was created at the repository root.
- **Index registration — deferred, deliberately.** `.clinerules` §12 obliges an index update in the same task. `docs/governance/AMSDP_Docs_Index_V1.0.md` is currently **modified and uncommitted** with unrelated in-flight QUE-006 work (it is one of the 13 `M` entries, §2.3), and §9 forbids staging or editing a file "already carrying someone else's uncommitted work". Adding a row would interleave two owners' changes in one dirty file, and would also inject a stale index into a tree that §10 step 4 is about to replace with the target's version. **Decision: defer, state it, and hand the obligation to the owner as O-R4.** A documented deviation from §12, not an omission.
- **No document migration was performed**, so no manifest entry is required (§11).

### 13.4 Read-only proof and evidence ledger

**Read-only proof.** The inspection's only write is this report:

- `git status --short -uall` before writing: **21 entries** (13 `M`, 8 `??`). After writing: **22 entries** — the single added line is `?? docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md`.
- `git diff --stat` unchanged: no tracked file was touched.
- `git stash list` still empty; `HEAD` still `cd2f9ec`; branch still `hackathon-mvp`; `git ls-remote` used for reading only.
- No container was started, stopped or restarted (`docker compose ps` still reports the same `Up 39 hours` ages); no volume created or removed; no image built, tagged or pruned.
- The database received only `SELECT`/catalog statements. One earlier probe was malformed (`$$` was expanded by the host shell, producing `trailing junk after numeric literal`); PostgreSQL rejected it at parse time, so it read and wrote nothing. It was re-run correctly.
- No migration and no test suite was executed.

**Evidence ledger for this report's own claims:**

| Classification | Count | What they are |
|---|---|---|
| **VERIFIED** | 24 | Repository identity and status; remote head = target SHA; target object absent locally; env-file inventory; compose/service/port/health table; container mounts; volume identity and path; image IDs and dates; `_tools` / dependency / seed blob equality; DB name, version, revision, table count, sizes, columns; the three new tables `ABSENT`; the 16-file target migration list with 14 identical blob SHAs; the two-head graph; `_tools` scripts containing no `alembic` invocation. |
| **IMPLEMENTED (read, not run)** | 6 | Target's `announcements.py`, `events.py`, the eight `frontend/lib/announcements/*` modules, the audio asset tree, both new revisions' idempotency guards, and the `call_event_id` uniqueness rule. |
| **ASSUMPTION** | 4 | Local commits not in the target's history (§3.3); `UndefinedTable` surfacing as HTTP 500 (§9.7.4); health endpoints being schema-agnostic (§9.7.3); the seed's imports resolving under the target's `backend/common/` (§9.4). |
| **BLOCKED** | 1 | Whether local `cd2f9ec` is an ancestor of the target (§3.3) — requires a `fetch`. |
| **NOT VERIFIED** | 1 class | Any runtime behaviour of `2fc007a`: nothing from that commit has ever executed on this host. |
| **ACCEPTED** | **0** | Nothing was submitted for sign-off. |

### 13.5 Where this document was written

`/home/shomonrobie/amsdp/docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` — per `.clinerules` §11 (subject folder), §12 (index registration deferred → O-R4), with no document migration performed and therefore no manifest entry.

