# AMSDP — Final Merge and Publication Report V1.0

**Scope:** the merge of the Windows QUE-006 lineage into the Ubuntu lineage, and the
publication of the result to `origin/hackathon-mvp`.
**Repository:** `/home/shomonrobie/amsdp` → `git@github.com:shomonrobie/amsdp.git`
**Date:** 2026-11-23
**Status:** **PUBLISHED and independently verified.** Merge commit `ea9c2a0`, fast-forward
on `hackathon-mvp`, confirmed by a server-side `git ls-remote`.
**Not verified in this report:** audible playback by a human, manual-repeat evidence,
facility-level configuration, the demo doctor's branch assignment, and runtime
availability of the new tables (the live database is still behind — §7).

---

## 1. Publication record

| Item | Value |
|---|---|
| Branch published | `hackathon-mvp` |
| Merge commit | `ea9c2a01603b95ded744adc9e7f8629ec8477b9f` |
| First parent (Ubuntu lineage) | `41ac51a0aea6a4462d3e2356cd5f3e58da57b326` |
| Second parent (Windows lineage) | `2fc007a3f7a96639c3df36341c6081cee4d24a48` |
| Previous remote tip | `2fc007a3f7a96639c3df36341c6081cee4d24a48` |
| Push result | `2fc007a..ea9c2a0  hackathon-mvp -> hackathon-mvp`, exit 0 |
| Force used | **No.** `git merge-base --is-ancestor 2fc007a ea9c2a0` is true, so the push was a true fast-forward; no `+`, no `--force`, no `--force-with-lease` |
| Server-side confirmation | `git ls-remote origin refs/heads/hackathon-mvp` → `ea9c2a01603b95ded744adc9e7f8629ec8477b9f` |
| Local confirmation | `git rev-parse origin/hackathon-mvp` and `git rev-parse HEAD` both `ea9c2a0…` after `git fetch --prune` |
| Published tree | `dbc6abb817026633e110a711c88843566516baca` |
| Remote advanced between fetch and push | No — `git fetch origin --prune` immediately before the push returned nothing |

Two independent artefacts therefore agree on the published state: the local ref after a
fresh fetch, and the remote's own advertisement via `ls-remote`. Under the project's
evidence standard (`docs/governance/AMSDP_Engineering_Governance_Assessment.md` §7) that
is **VERIFIED**, not merely TESTED.

### 1.1 Commits the push delivered

The push moved the remote by four commits, three of which had never been published:

| Commit | Date | Subject | Note |
|---|---|---|---|
| `0554f33` | 2026-11-20 | docs: add website content proposal | Was local-only |
| `cd2f9ec` | 2026-11-20 | docs: add AMSDP website content and copywriting proposal | Was local-only |
| `41ac51a` | 2026-11-22 | wip(queue): preservation snapshot of the Ubuntu working tree (pre QUE-006 trial merge) | Was local-only; **published by this push** (see §5.3) |
| `ea9c2a0` | 2026-11-23 | Merge Windows and Ubuntu QUE-006 implementation | The merge |

---

## 2. What each side contributed

### 2.1 Ubuntu lineage (`41ac51a`)

The queue domain itself: the queue API, call control, room support, the display board,
the tracking tokens and the RBAC plumbing, plus the F1–F4 hardening and the verification
reports listed in §4.4. This is the side that owns `backend/queuing/`, the queue pages
and the acceptance vocabulary.

### 2.2 Windows lineage (`2fc007a`)

The voice announcement workstream: the prerecorded audio engine, the voice-pack registry,
the audio asset pipeline and the delivery pipeline (`queue_announcement_deliveries`), plus
the W1–W6 reports and the audio catalogue. This is the side that owns
`frontend/lib/announcements/`, `backend/organization/voice_packs.py` and
`scripts/que-006-*`.

### 2.3 Size of the integration, measured two ways

| Comparison | Result |
|---|---|
| Merge commit vs Ubuntu parent (`41ac51a..ea9c2a0`) | 193 files, +36,394 / −658 |
| Merge commit vs Windows parent (`2fc007a..ea9c2a0`) | 55 files, +11,907 / −202 |
| Files touched by **both** sides (the real collision surface) | 36 (§3) |

The asymmetry is the honest shape of this merge: the larger movement is *towards* the
Windows parent, because the Ubuntu line had accumulated the queue platform and the
documentation set that the Windows line was written against.

---

## 3. The collision files and how each was resolved

Every path below was changed on both sides, so each is a decision, not a mechanical union.
Grouped by decision, not by directory.

### 3.1 Announcement engine (the behavioural core)

| File | Resolution |
|---|---|
| `frontend/lib/announcements/prerecorded-audio.js` | Windows engine kept, plus the **Chromium event-order fix**: `pause` fires before `ended`, so `playSegment()` treated a finished clip as an interrupt. `playedToEnd()` added and pinned by an AC-2 regression test that encodes the browser's exact event order |
| `frontend/lib/announcements/controller.js` | Windows state machine, with the Ubuntu side's server-truth reconciliation retained |
| `frontend/lib/announcements/delivery.js` | Windows delivery records — `completed` / `interrupted` only, no pre-merge aliases |
| `frontend/lib/announcements/call-announcer.js` | Joined so the queue's call event drives the Windows pipeline (INT‑3) |
| `frontend/lib/announcements/content.js` | D‑4/D‑6 sentence selection: a configured room is announced, otherwise the approved room-less sentence |
| `frontend/lib/announcements/speech-synthesis.js` | Kept as the fallback path, vocabulary aligned with the delivery records above |
| `frontend/components/queue/QueueAnnouncements.js` | Merged panel: Windows controls, Ubuntu permission gating |
| `frontend/pages/queue.js` | Both sides' queue UI joined; the audio badge reflects real engine state |

### 3.2 Backend voice configuration

| File | Resolution |
|---|---|
| `backend/organization/voice_packs.py` | W3 registry kept; **import guarded for both layouts** (`uvicorn main:app` has no package parent) |
| `backend/organization/voice_pack_policy.py` | Policy kept (default **off**), guard added |
| `backend/organization/announcement_config.py` | Ubuntu config joined to the Windows pack registry, guard added |
| `backend/organization/queue_calling_config.py` | Added (organization-level enable/language) — **not** facility-level (§7) |
| `backend/organization/main.py` | Router registration for both feature sets |
| `backend/queuing/main.py` | Windows delivery hooks joined to the Ubuntu call lifecycle |
| `backend/common/config.py` | One settings surface for both feature sets |
| `backend/doctor/profile.py` | Doctor profile joins preserved — no branch-contract change, D‑1/D‑2 stay pre-existing |
| `backend/alembic/versions/a7c3f19d2b64_add_queue_announcement_deliveries.py` | Kept as part of the single chain to head `c4d8e2a91f60` |

### 3.3 Proxy table and tests

| File | Resolution |
|---|---|
| `frontend/next.config.js` | INT‑4 fix: `/api/v1/voice-packs` and `/api/v1/platform/**` are rewritten to the backend, so they answer `2xx` JSON through the application origin instead of Next's own HTML 404 |
| `frontend/tests/next-config-rewrites.test.mjs` | Added — pins the whole rewrite table; this is the test that keeps INT‑4 from coming back |
| `frontend/tests/queue-call-control.test.mjs`, `queue-announcement-controller/delivery/prerecorded/room.test.mjs` | Union of both sides' cases, vocabulary updated to the merged delivery records |
| `backend/organization/tests/test_voice_packs_api.py`, `test_voice_pack_policy.py`, `test_queue_calling_config.py` | Union; `test_container_layout_import.py` added as the negative-control guard for 3.2 |
| `backend/appointment/tests/test_appointment_calendar_filters.py`, `backend/doctor/tests/test_doctor.py` | Ubuntu cases kept unchanged |

### 3.4 Documentation

`docs/governance/AMSDP_Docs_Index_V1.0.md` and the six QUE‑006 reports both sides wrote
were merged rather than chosen between: the index keeps both annex sections and each
report is preserved in full. No report from either side was rewritten, condensed or
deleted to make the merge easier.


---

## 4. Verification evidence, before the commit was made

### 4.1 Suites and build

| Check | Command | Result |
|---|---|---|
| Frontend suite | `cd frontend && npm test` | **368 pass / 0 fail**, exit 0 |
| Frontend build | `cd frontend && npm run build` (re-run on the exact staged tree, after the merge resolution) | **`✓ Compiled successfully`**, 8/8 static pages generated, exit 0 (`/tmp/q6_build.log`) |
| Targeted backend | `pytest -q organization/tests queuing/tests doctor/tests/test_doctor.py appointment/tests/test_appointment_calendar_filters.py` | **262 passed**, 0 failed |
| Whole-tree backend | `pytest -q` | **682 passed, 109 errors, 0 failed** (14m03s) |
| The 109 errors, explained | `pytest -q organization/tests/test_voice_packs_api.py queuing/tests/test_queue.py` against a **migrated** throwaway database | **109 passed** (78s) — the error count and the pass count are the same number |

### 4.2 Why the whole-tree run is reported as 109 errors rather than 791 green

The live development database `amsdp-db-1` is at `a9c4e1f7b2d8`, **two revisions behind**
the single head `c4d8e2a91f60`. `voice_packs` and `queue_announcement_deliveries` do not
exist there, so every `voice_packs`/`queue` test dies at *fixture setup* with
`psycopg2.errors.UndefinedTable` — no test assertion ever fails. This is
database-state evidence, not a code defect, and the isolated re-run on a migrated
database proves it: the same two files report 109 passes, matching the error count
exactly.

It is recorded here rather than quietly omitted because it is also a **release blocker**:
the merge is published, but the running stack cannot serve `voice_packs` until the live
database is migrated (`_tools/pg_backup.sh` → `alembic upgrade head` →
`_tools/amsdp_rebuild.sh`).

### 4.3 Schema

| Check | Result |
|---|---|
| `alembic heads` | one head, `c4d8e2a91f60` |
| `alembic upgrade head` on a fresh PostgreSQL 16 container | exit 0 |
| `alembic current` on the live database | `a9c4e1f7b2d8` — **behind**, see §4.2 |
| Merge introduced a second head | No |

### 4.4 Reports that carry the detailed evidence

`AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md`,
`AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md`,
`AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md`,
`AMSDP_QUE006_Acceptance_Readiness_Verification_Report_V1.0.md`,
`AMSDP_QUE006_Final_Merge_Readiness_Verification_Report_V1.0.md` — all in
`docs/implementation/`, all published by this merge. This report does not restate their
measurements; it records what was merged and what was pushed.

---

## 5. Preservation and recoverability

### 5.1 Snapshot commit (two parents, same tree)

Before committing, the staged resolution was written to a snapshot commit through an
alternate index file, so `.git/index` was never disturbed:

```
GIT_INDEX_FILE=/tmp/q6snap_index git read-tree HEAD && git add -A
git write-tree                                  → dbc6abb817026633e110a711c88843566516baca
git commit-tree <tree> -p 41ac51a -p 2fc007a    → 5fc6a75445f373c12dbc175400ae97c322afcfaf
git branch -f wip/que006-merge-resolution-snapshot-v1 5fc6a75
```

The published merge commit `ea9c2a0` has tree `dbc6abb8…` — **byte-identical to the
snapshot tree** (`git rev-parse HEAD^{tree}` compared against `git rev-parse 5fc6a75^{tree}`).
The published content is therefore recoverable even if the merge commit were ever
rewritten, and the snapshot's two parents prove which trees the resolution was built from.

Earlier preservation branches remain: `wip/que006-ubuntu-preservation` (`41ac51a`).

### 5.2 Artefacts outside the repository

`/home/shomonrobie/amsdp-backups/que006-publication/`:

| File | Bytes | SHA-256 |
|---|---:|---|
| `resolution-vs-ubuntu-parent.patch` | 5,586,192 | `2def590f9fb0336c1ec1e764191b823e2208ea1b8488be38c2023e4a5ac98cfc` |
| `resolution-vs-windows-parent.patch` | 867,914 | `f1dcacc739e431a4862249d59a70eed0019b3a795014ef4f9f04394506b526dd` |
| `snapshot-tree.txt` | 71,447 | `7388dd62937e573fb90a45c12342e2c76c4d6258a010c9cd5ec2c90616d4cfd4` |

Plus `snapshot-meta.txt` (snapshot commit, tree, both parents, timestamp, host) and
`SHA256SUMS`. The patches are `--binary`, so they reproduce the resolution without the
repository.

### 5.3 One thing the owner should know about the published history

`41ac51a` — the Ubuntu preservation snapshot — is now **published**. It was a local
snapshot of the Ubuntu working tree taken before the trial merge was resolved; while it
was local, publishing it was a choice, and the choice made here was to keep it, because
the merge commit names it as its first parent and dropping it would have meant rewriting
the history being published. It contains no secret material: the staged set was scanned
for `.env`, keys, certificates, dumps and credential files and returned nothing.

---

## 6. What was deliberately **not** committed

| Item | Why | Where it lives |
|---|---|---|
| `frontend/.audio-originals-backup/` | binary copies of the recordings, kept as evidence, not as source | on disk; excluded by four lines added to `.gitignore` in this merge |
| Audio originals' provenance | already recorded in `QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` | in the repo as text |
| `/tmp/amsdp_*.log`, `/tmp/q6_*.log` | ephemeral run logs; the durable record is this report and the runbook | `/tmp` |
| `amsdp-pubverify-pg` throwaway database | verification scaffolding, torn down at the end of this task | removed |
| `.env`, JWT secrets, demo passwords | never committed, never printed | owner-held |


---

## 7. Still open after publication — nothing here is a merge defect

| Item | State | Closing condition |
|---|---|---|
| **Live database two revisions behind** | **OPEN — release blocker for the QUE‑006 features.** `a9c4e1f7b2d8` vs head `c4d8e2a91f60`; `voice_packs` and `queue_announcement_deliveries` absent | `_tools/pg_backup.sh`, then `alembic upgrade head`, then `_tools/amsdp_rebuild.sh` — documented in the runbook §1.4/§4.3, **not executed here** |
| **B‑8** human audibility of playback | **NOT VERIFIED** — no automated artefact can prove a person hears the speaker; delivery rows and audio assets exist | a human, in the room, with the demo stack running |
| **D‑5** documentation index numbering | **NOT IMPLEMENTED as a renumbering** — this report is registered in an unnumbered annex; no revision number is claimed | owner confirms the index head, then a docs-only commit |
| **D‑7** manual-repeat delivery records | **NOT VERIFIED** — the repeat path is implemented and tested, but no manual scenario has been recorded | a scripted manual scenario logged under `docs/testing/` |
| **O‑2** facility-level enable/language | **NOT VERIFIED** — configuration is organization-level (`queue_calling_config.py`); per-facility overrides do not exist | owner decision on whether facility scope is in MVP; if yes, a new migration plus tests |
| **RBAC‑R3** demo doctor's branch assignment | **NOT VERIFIED** — seed and RBAC tests are green, the specific seeded assignment has not been inspected | `_tools/verify_demo_login.sh` plus one doctor's assignments on the demo stack |
| **PostgreSQL on `0.0.0.0:5433`** | **OPEN — owner decision** | owner approves, then bind to `127.0.0.1` and `docker compose up -d db` |
| **No SSH listener on the host** | **OPEN — owner decision**; transport today is Git | owner |
| **Windows steps of the runbook** | **NOT VERIFIED** — written from the repository and the host's toolchain, never executed on Windows | the Windows developer, once, following runbook §5–§10 |

The merge is published; none of the above is made worse by that, and none of it is
claimed as done.

---

## 8. Governance and skill compliance

**Applicable governance (`.clinerules` §4 routing):**

| Domain | Documents read and applied |
|---|---|
| Branch/merge/publication discipline, git safety | `saas-cicd-workflow.md` as adapted in the governance assessment §3 — forward-only history, no destructive git, honest CI state |
| Docker/deployment claims | `docker-compose.yml`, `docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md`, M6 constraints |
| Multi-tenant data, schema and migrations | `saas-multitenant-data.md` §4–5 (adapted), `backend/common/models.py`, the Alembic chain |
| Backend endpoints, RBAC | `saas-application-security.md` and `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8 |
| Documentation placement and registration | `.clinerules` §11–§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` |

**Skills:** none installed in this workspace (`.clinerules` §5 — verified: no
`.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used, and
none is claimed.

**Non-negotiables honoured (`§3`):**

* No secret, token, JWT material or credential was printed, logged or committed; the
  staged set was scanned and the scan is recorded in §5.3.
* Cross-tenant behaviour was not weakened by any resolution; the B‑9 non-disclosing 404
  fix was retained, not dropped in the merge.
* Audit trail untouched: no commit was amended, squashed, rebased or reset. The merge is
  a real two-parent merge commit; the snapshot is an additional branch, not a rewrite.
* No destructive git: no `reset --hard`, `clean -fd`, `stash`, `checkout .` or force-push.
  The push was a fast-forward, proven by ancestry and by `ls-remote`.
* No schema was changed ad hoc: the merge adds no migration beyond the one already in the
  chain, and the head remains single.
* Evidence standard (`§7`): IMPLEMENTED / TESTED / VERIFIED are used in their defined
  senses — publication is VERIFIED by two independent artefacts (§1); audibility, D‑7,
  O‑2 and RBAC‑R3 are explicitly **not** claimed.

---

## 9. Where this report lives, and its registration

Written to `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md`, per
`.clinerules` §11 (implementation subject → `docs/implementation/`). No document was
moved or renamed by this task, so no manifest entry is owed; a docs-index annex entry is
added in the same commit (`docs/governance/AMSDP_Docs_Index_V1.0.md`, unnumbered section
"Final merge publication"), registering this report and
`AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md`. The annex deliberately
claims no revision number — that is D‑5, and it stays open.

---

## 10. Next actions, in order

1. Back up and migrate the live database, then rebuild — runbook §4.3. Without this the
   published QUE‑006 features cannot be exercised at runtime.
2. Re-run the whole-tree backend suite against the migrated live database; expect the 109
   errors to disappear (they already pass on a migrated database — §4.2).
3. Hand the runbook to the Windows developer; the first clone-and-run produces the
   evidence that closes the "Windows steps" row in §7.
4. Owner decisions on the three `OPEN — owner decision` rows.
5. Close B‑8, D‑7, O‑2 and RBAC‑R3 with the evidence named in §7, not with a green suite.

**Published commit: `ea9c2a01603b95ded744adc9e7f8629ec8477b9f` on `hackathon-mvp`.**

