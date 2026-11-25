# AMSDP — Implementation State and Next Task: Investigation Report, V1.0

**Date:** 2026-11-23 (host clock) · **Subject checkout:** `E:\amsdp` (Windows) · **Branch:** `hackathon-mvp`
· **HEAD:** `a4ddc2cf58e019b57dccf59f3a859743e3c48430` · **Working tree:** clean · **Upstream:** `origin/hackathon-mvp` at the same commit
**Task type:** read-only investigation. **Status:** the stopping point is established; **no** code, schema, branch,
commit, deployment or Git history was changed, and **no test suite was executed**.
> **Correction, 24 November 2026 — do not quote this report's runtime baseline as current.** The
> statement that "the live database is two revisions behind" was **true when this session ran on
> 2026-11-23** and was superseded later the same day: the migration was applied then, after a
> rehearsal against a disposable restored database and with a pre-migration backup, taking the live
> database to the single head `c4d8e2a91f60` and creating `voice_packs`,
> `queue_announcement_deliveries` and `announcement_platform_config`. The deployment also **does**
> answer from the Windows checkout (`192.168.68.108:8110–8117` and `:3100`, all HTTP 200 on
> 2026-11-24); the earlier `:8000`/`:3000` probes targeted container-internal ports and the wrong
> host. Reconciliation record: `docs/implementation/AMSDP_Live_Deployment_Baseline_Reconciliation_Report_V1.0.md`.
> Everything else in this report — the QUE-006 state matrix, the four open owner decisions, the
> evidence vocabulary — stands unchanged.

**Verdict in one line:** QUE-006 is **merged and published** (`ea9c2a0`, tip `a4ddc2c`, verified on `origin`), the merge
blocker is fixed and browser-verified, **four owner decisions plus three carried items remain open**, and the
**live database is two revisions behind** — that migration is the next planned task and is **not** done.
*(**Superseded 2026-11-24:** the migration was applied on 2026-11-23 — see the correction banner above. The remaining
task is the post-migration suite baseline, not the migration.)*

---

## 0. Labels, method, and what was and was not executed

| Label | Meaning here |
|---|---|
| **VERIFIED** | Produced in this session by a command whose output is quoted, or by a second independent artefact (e.g. `git ls-remote` *and* a local ref). |
| **REPORTED** | Stated by a document read in this session; the document is cited. Not re-executed here. |
| **IMPLEMENTED** | The file/symbol exists in this tree at `a4ddc2c` and is reachable; established by read/grep, not by running it. |
| **NOT VERIFIED** | No artefact in this session confirms it. *Unproven here*, not false. |
| **CONFLICT** | Two sources disagree. Recorded, not resolved (`.clinerules` §1). |

Commands actually run (all read-only): `git rev-parse --abbrev-ref HEAD`; `git log -1 --format=…`;
`git status --porcelain=v1 -uall`; `git status -sb`; `git rev-list --left-right --count HEAD...origin/hackathon-mvp`;
`git rev-parse origin/hackathon-mvp`; `Test-Path .git\MERGE_HEAD`; `git branch -vv`; `git tag --list`;
`git stash list`; `git rev-list --count HEAD`; `git log -1 --format='%h %p' ea9c2a0`; `git remote -v`;
`git ls-remote origin refs/heads/hackathon-mvp`; `git log -20 --format=…`; `git log -6 --name-status`;
`git log -1 -- <path>` per document; plus `Test-Path` / `Get-ChildItem` / `Select-String` reads of the files cited below.

**Not executed, deliberately:** `pytest`, `npm test`, `npm run build`, `alembic`, `docker compose`, any live API call,
any database read. Reason: this is a Windows development checkout — `backend\.venv` does not exist and `pytest` is not on
`PATH` (`Test-Path` → `False`; `Get-Command pytest` → nothing), and the live stack and live database are on the Ubuntu host,
which is not reachable from this session. `frontend\node_modules` **is** present, so the frontend suite is *runnable*
here, but `.clinerules` §9 forbids running suites unless the owner asks.

**Methodological warning about chronology.** Every `.md` under `docs/` carries `LastWriteTime = 2026-11-23 15:16:53`
(a checkout/refresh artefact — verified over the newest 15 files). File mtime therefore **cannot** sequence the
documents. Chronology in this report is taken from **commit history** instead.

---

## A. Repository state — VERIFIED

| Item | Observed value | How |
|---|---|---|
| Branch | `hackathon-mvp` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `a4ddc2cf58e019b57dccf59f3a859743e3c48430` | `git log -1` |
| HEAD date / author / subject | 2026-11-23 20:21:43 +0600 · `shomonrobie` · *docs(queue): record the post-teardown container count in the runbook evidence appendix* | `git log -1 --format='%H\|%ci\|%an\|%s'` |
| Upstream | `origin/hackathon-mvp`, **0 ahead / 0 behind** | `git rev-list --left-right --count HEAD...origin/hackathon-mvp` → `0  0` |
| Remote tip | `a4ddc2cf58e019b57dccf59f3a859743e3c48430 refs/heads/hackathon-mvp` | `git ls-remote origin refs/heads/hackathon-mvp` (and local `origin/hackathon-mvp` identical) — **publication VERIFIED by two artefacts** |
| Working tree | **clean — 0 entries** | `git status --porcelain=v1 -uall \| Measure-Object -Line` → `0`; `git status -sb` → `## hackathon-mvp...origin/hackathon-mvp` |
| Merge in progress | **none** | `.git\MERGE_HEAD` absent |
| Local branches | one only: `hackathon-mvp a4ddc2c [origin/hackathon-mvp]` | `git branch -vv` |
| Tags | none | `git tag --list` (empty) |
| Stashes | none | `git stash list` (empty) |
| Total commits | 64 | `git rev-list --count HEAD` |
| Remote | `https://github.com/shomonrobie/amsdp/` (fetch and push) | `git remote -v` |

**Recent history** (`git log -20 --format='%h|%ad|%s' --date=iso`):

| Commit | Date | Subject |
|---|---|---|
| `a4ddc2c` | 2026-11-23 20:21:43 | docs(queue): record the post-teardown container count in the runbook evidence appendix |
| `d9432db` | 2026-11-23 20:21:28 | docs(queue): correct the container count and tighten two claims in the runbook and report |
| `c185428` | 2026-11-23 20:20:03 | docs(queue): state the tip-check command instead of a hash that goes stale |
| `4e6a523` | 2026-11-23 20:19:42 | docs(queue): record the published remote tip in the publication report |
| `4e7250d` | 2026-11-23 20:18:29 | docs(queue): publication report and unnumbered index registration |
| `ea9c2a0` | 2026-11-23 20:11:21 | **Merge Windows and Ubuntu QUE-006 implementation** |
| `41ac51a` | 2026-11-22 16:38:21 | wip(queue): preservation snapshot of the Ubuntu working tree (pre QUE-006 trial merge) |
| `2fc007a` | 2026-11-22 06:42:32 (+0000) | docs(queue): QUE-006 workstream reports and documentation |

Merge parentage — **VERIFIED**: `git log -1 --format='%h %p' ea9c2a0` → `ea9c2a0 41ac51a 2fc007a`.

`git log -6 --name-status` shows the five post-merge commits are **documentation-only** (runbook, publication report,
docs index). No source file was touched after the merge commit.

---

## B. Last completed task

Two answers, because the record contains two kinds of "last".

| # | Task | State | Evidence |
|---|---|---|---|
| B-1 | **Last implementation task — D-4 and D-6 decision closure** (rooms announced from a configured room; one playback vocabulary `completed`/`interrupted`) | **COMPLETED and TESTED**, carried in the merge | `AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md` is committed **by `ea9c2a0`** (`git log -1 -- <path>`); its fixes are present in the tree: `playedToEnd()` at `frontend/lib/announcements/prerecorded-audio.js:192`, the `PLAYBACK` vocabulary in the controller/delivery classifier, and the D-4 tests in `frontend/tests/queue-announcement-room.test.mjs` (REPORTED 14/14) |
| B-2 | **Last task overall — QUE-006 trial-merge integration, publication and runbook correction** | **COMPLETED, PUBLISHED** | `ea9c2a0` (merge) + `4e7250d`, `4e6a523`, `c185428`, `d9432db`, `a4ddc2c` (docs) = the tip; `origin/hackathon-mvp` = `a4ddc2c` (VERIFIED) |

The publication report's own record of what it delivered — **REPORTED**, `AMSDP_Final_Merge_Publication_Report_V1.0.md`
§1: published commit `ea9c2a0` on `hackathon-mvp`, "fast-forward from `2fc007a`", verified by `git ls-remote` **and** by a
local ref after a fresh fetch; 193 files vs the Ubuntu parent, 55 vs the Windows parent, 36 files touched by both.
I re-verified the *publication fact* independently in this session (§A); I did **not** re-derive the file counts.

---

## C. Latest report

| Rank | Document | Why it is the latest | State |
|---|---|---|---|
| 1 | `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` | last edited by `d9432db`, and its closing line refuses to claim a current tip ("For the current tip, run `git ls-remote`") — the newest *content* | **REPORTED**; published |
| 2 | `docs/implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md` | edited by the final commit `a4ddc2c` | REPORTED; operating document |
| 3 | `docs/implementation/AMSDP_QUE006_Final_Merge_Readiness_Verification_Report_V1.0.md` | verdict **MERGE-READY, CONDITIONALLY**; the merge blocker fixed and browser-verified | REPORTED |
| 4 | `docs/implementation/AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md` | D-4/D-6 closed; frontend `355/355`, build compiled | REPORTED |
| 5 | `docs/implementation/AMSDP_QUE006_Acceptance_Readiness_Verification_Report_V1.0.md` | verdict **NOT READY** at the time; found and repaired the container import defect | REPORTED (superseded on the blocker by #3) |

**CONFLICT 1 (state staleness, not contradiction).** Reports #3–#5 describe the repository as *the same uncommitted trial
merge* on branch `trial/que006-windows-ubuntu-merge`, HEAD `41ac51a`, `MERGE_HEAD 2fc007a`. That was true when they were
written. Today the merge is **committed** (`ea9c2a0`) on `hackathon-mvp`, the tree is **clean**, there is **no**
`MERGE_HEAD`, and the branch name they cite no longer exists. Any further work must re-read state, not trust those headers.

---

## D. Current phase status

**Phase: QUE-006 trial-merge integration — merged and published; feature NOT released at runtime; NOT ACCEPTED.**

| Workstream | Plan status (master plan) | Actual state at `a4ddc2c` | Label |
|---|---|---|---|
| **W1** prerecorded engine | complete | `frontend/lib/announcements/segments.js`, `prerecorded-audio.js` present; `playedToEnd()` at line 192 | IMPLEMENTED |
| **W2** queue integration + delivery claim | complete | `controller.js`, `call-announcer.js`, `delivery.js`; backend `backend/queuing/announcements.py` (claim + outcome), `backend/queuing/events.py` (`qce:<entry>:<index>`), table `queue_announcement_deliveries` (`models.py:931`), migration `a7c3f19d2b64` | IMPLEMENTED; browser-verified REPORTED |
| **W3** voice configuration / voice packs | complete incl. admin UI | `backend/organization/voice_packs.py`, `announcement_config.py` (`CONFIG_KEY = "announcement"`), `voice_pack_policy.py`, migration `c4d8e2a91f60`, `next.config.js` rewrites for `/api/v1/voice-packs` and `/api/v1/platform/**`; dual-layout import guards + `backend/organization/tests/test_container_layout_import.py` | IMPLEMENTED — **but no admin UI exists**; the W3 report itself says "no admin UI … everything is API-only" |
| **W4** room support | **blocked (POD-2)** | resolved in substance by **D-4** (2026-11-22): a configured room is announced from the entry's `room_name` (appointment booking snapshot); no schema change, no new field. `backend/queuing/main.py::_entry_to_dict` serialises it | IMPLEMENTED via decision; blocker stale |
| **W5** remote installation | agent verified, server half absent | `scripts/que-006-agent/` present (installer, atomic swap, rollback, status); the agent downloads a JSON *bundle* from a configurable URL. Report: "The **server-side distribution API does not exist**" | **PARTIALLY IMPLEMENTED** |
| **W6** asset cleanup | report only (POD-7) | dependency report written; **no file moved or deleted**; `frontend/public/audio` holds **72 files** — 71 clips under `bn/`+`en/` × `number/`+`phrase/` plus `manifest.json` (counted) | DELIVERED AS ANALYSIS; cleanup NOT DONE |
| **W7** integrated verification | complete | `QUE-006_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | DELIVERED |
| Runtime | — | ~~**live database two revisions behind** (`a9c4e1f7b2d8` vs head `c4d8e2a91f60`); `voice_packs` and `queue_announcement_deliveries` absent from it~~ **Superseded 2026-11-24:** the migration was applied on 2026-11-23; live DB at head `c4d8e2a91f60`, the three tables created; all eight services and the frontend answered HTTP 200 when re-probed on 2026-11-24 | Was REPORTED then, **NOT VERIFIED** even now (the revision was never queried from this checkout); the 2026-11-24 service probes **are** verified |

Decision/blocker board as it stands (REPORTED unless labelled):

* **Closed:** D-4, D-6 (2026-11-22, implemented in the merge); B-9 (non-disclosing 404 retained); INT-3/INT-3b/INT-4; the
  announcement playback defect (Chromium fires `pause` before `ended`); the container import defect.
* **Deliberately red:** D-1 / D-2 (doctor branch contract) — left as pre-existing, tenant-safe questions.
* **Open owner decisions:** **D-3**, **D-5**, **D-7**, **O-2** (the four carried forward), plus roadmap **POD-1, POD-3,
  POD-7, POD-8, POD-9, POD-10, POD-11** and the infrastructure items.
* **Unproven, not decisions:** **B-8** audibility (no audio device on the verifying host); **RBAC-R3** demo doctor holds no
  `staff_doctor_assignments` row; **B-5** pre-existing test defects; **B-10** not tightened; the unexecuted Windows runbook steps.

---

## E. Remaining work, in the order the record implies

| # | Item | Why it is still open | Owner |
|---|---|---|---|
| E-1 | **Record the post-migration suite baseline** (`pytest` + `npm test` against the migrated database) — the migration itself was applied on 2026-11-23 and must **not** be re-run | ~~Release blocker: live DB at `a9c4e1f7b2d8`, head `c4d8e2a91f60`~~ **Superseded 2026-11-24.** Still open: no suite run against the migrated database has been recorded, so no "the suite is green" claim can be made | Owner authorisation + operator |
| E-2 | Re-run the whole-tree backend suite against the migrated DB | The publication report predicts the 109 errors clear; unproven until run | Engineering |
| E-3 | Execute the Windows half of the runbook (§5–§10), once, on a real Windows developer machine | The "Windows steps — NOT VERIFIED" row closes only that way | Owner/developer |
| E-4 | **W5 server-side distribution API** | The agent is verified only against a *stub* endpoint; no distribution API exists | Engineering, after scope authorisation |
| E-5 | **W3 voice-pack management surface** | The master plan lists a frontend admin page; only the API exists; DR-7 promises preview/publish/retire | Engineering, after scope authorisation |
| E-6 | W6 asset disposition (15 unreferenced files) | Blocked on POD-7 | Owner |
| E-7 | Audibility + device matrix (B-8, V-18/V-19, human listening O-3/POD-11) | No automated artefact can close these | Owner/human reviewer |
| E-8 | D-3 (unused `dedupe.js` — **verified**: only its own test imports it), D-7 manual-repeat scenario, O-2 facility scope, RBAC-R3 demo seed | Each needs a decision or a small recorded scenario | Owner / Engineering |
| E-9 | Infrastructure: PostgreSQL published on `0.0.0.0:5433`; no SSH listener; D-5 index numbering | Security/operations exposure and documentation debt | Owner |

---

## F. Next planned task

There are two candidate "next tasks" in the record. They are resolved here explicitly rather than silently:

1. **The QUE-006 workstream sequence (master plan W1→W7).** Every unblocked engineering item in it is done; what is left is
   W5's server half (E-4) and W3's UI (E-5) — both need a scope authorisation that does not exist yet — plus W6, blocked on POD-7.
2. **The publication report's ordered list (§10), which is the newer approved artefact** and the only place where an
   ordered, executable next step is written down.

**Therefore the next planned task is publication report §10, step 1:**

> **Back up and migrate the live database on the Ubuntu host, then rebuild** — `_tools/pg_backup.sh`, then
> `alembic upgrade head`, then `_tools/amsdp_rebuild.sh`, in the runbook's §1.4/§4.3 order — followed immediately by
> **step 2**, the whole-tree backend suite against the migrated database.

Its justification is in the record, not invented here: §10 says "Without this the published QUE‑006 features cannot be
exercised at runtime", and §7 classifies the same row as "OPEN — release blocker for the QUE‑006 features".

**Not started.** No migration, backup, rebuild, suite, container action or deployment was performed in this session, and
this checkout could not perform it if it tried (the live host is not reachable from Windows).

---

## G. Open Product Owner decisions

| ID | Question | Blocks | Status |
|---|---|---|---|
| **D-3** | Wire F3's bounded per-event store into `announce()`, or delete `dedupe.js` + its test and document the single-slot window as policy | Honest tree; unused module today | OPEN — **verified**: the only importer of `frontend/lib/announcements/dedupe.js` is `frontend/tests/queue-announcement-dedupe.test.mjs`; `controller.js:20-22` imports only `content.js`, `speech-synthesis.js`, `prerecorded-audio.js` and dedupes inline with one slot (`DEFAULT_DEDUPE_WINDOW_MS`, `lastEventKey`, `lastEventAt`) |
| **D-5** | Confirm index head = Revision 48, then number the annex entries in one pass | Documentation integrity | OPEN |
| **D-7** | Should an operator's manual repeat create a second delivery/audit record? (the behaviour is deliberate and documented) | Audit completeness | OPEN |
| **O-2** | Is per-facility (branch) announcement enable/language in MVP? | Facility-scope configuration; would need a migration | OPEN |
| **POD-2** | Room source — *substantively answered by D-4*; no document formally closes the ID | The master plan and W7 still show "POD-2 OPEN / W4 blocked" | **CONFLICT — confirm closure** |
| **POD-5 / POD-6** | Storage scope is settled by DR-3 (organisation-level, `org.manage`/`platform.admin`). POD-6 (default enablement) never entered the register, and no facility enable flag exists | Facility on/off semantics | OPEN (POD-6) |
| **POD-7** | May the 15 unreferenced files be removed from the served tree? | W6 | OPEN |
| **POD-1 / POD-3 / POD-8 / POD-9 / POD-10 / POD-11** | Ranges; inter-clip gap; trailing silence; comma discrepancy; reference voice; named reviewer | Validation bounds, pacing, wording sign-off, pronunciation claim | OPEN |
| **Infra** | Approve binding PostgreSQL to `127.0.0.1`; decide the SSH transport | Exposure / operations | OPEN |

---

## H. Recommended action

1. **Accept this report as the stopping point.** The state is internally consistent and published; nothing is half-applied
   in Git, and the only unapplied change is the live-database migration, which is a deliberate blocker.
2. **Authorise exactly one operational task first:** E-1 + E-2 (backup → migrate → rebuild → whole-tree suite). It is
   reversible through the backup, has a written runbook, and unblocks runtime exercise of every QUE‑006 feature.
3. **Take the four carried decisions in one batch** (D-3, D-5, D-7, O-2) — each is small and each has a stated closing
   condition; then confirm POD-2's formal closure, since the master plan still shows W4 blocked after D‑4 decided it.
4. **Only then choose a feature increment.** The two real candidates are W5's server half (E-4) and the W3 management
   surface (E-5). Both are unbuilt product, not defects.
5. **Do not** claim acceptance, audibility or delivery at any point before E-1, E-7 and the owner's sign-off.

---

## Conflicts and discrepancies surfaced (not resolved here)

1. **Report state headers are stale** (CONFLICT 1 above): `trial/que006-windows-ubuntu-merge` / `41ac51a` / open
   `MERGE_HEAD` versus today's committed merge `ea9c2a0` on a clean `hackathon-mvp`.
2. **Lineage labelling is inconsistent.** The docs-index annex heads the section "Final merge publication **(Ubuntu**,
   2026-11-23)" and the publication report §2.1 calls `41ac51a` the **Ubuntu** lineage, yet `41ac51a`'s own message is
   *"preservation snapshot of the Ubuntu working tree (pre QUE-006 trial merge)"* (2026-11-22 16:38 **+0600**) while
   `2fc007a` is 2026-11-22 06:42 **+0000**. The SHAs are certain; the labels are not mutually consistent. It does not change
   any implementation status.
3. **O‑2 citation.** The publication report §7 cites `queue_calling_config.py` for announcement configuration; the actual
   language/voice-pack configuration is `backend/organization/announcement_config.py` (`CONFIG_KEY = "announcement"`, fields
   `language` and `voice_packs`). `queue_calling_config.py` holds `doctor_queue_calling_enabled`, a different policy. Both
   files exist.
4. **The master plan is stale on POD-12 and POD-2.** POD-12 is approved *and* implemented (report + `frontend/lib/queue/queue-call.js`);
   POD-2's blocker is decided by D-4. Neither plan row has been updated.
5. **Plan-versus-delivered scope on W3.** The master plan's W3 deliverable includes "frontend admin page"; no such page
   exists (`frontend/pages/` holds **16** page modules — `index`, `dashboard`, `appointments`, `patients`, `doctors`, `staff`,
   `branches`, `facilities`, `orgs`, `schedules`, `queue`, `notifications`, `audit`, `_app`, `queue-display/[org]/[branch]`,
   `track/[token]` — none announcement- or voice-related). The only announcement-config consumer is
   `frontend/components/queue/QueueAnnouncements.js:17`, which imports `resolveAnnouncementConfig` to *resolve* configuration;
   nothing in the frontend creates, previews, publishes or retires a voice pack.
6. **Test numbers differ across reports** — frontend `355/355` then `368/368`; whole tree `768 pass / 3 fail` (derived
   `769/2`), then `790 pass / 1 fail`, then `682 pass / 109 errors / 0 fail`. Each has a stated reason (different host,
   different database state, newer tests, harness dependency gap). None was re-run here, so all remain **REPORTED**.
7. **Table naming.** The delivery table is `queue_announcement_deliveries` (`models.py:931`), not
   `call_announcement_deliveries`; a search for the latter returns nothing. Reports that say "delivery table" are correct;
   code written against the wrong name would not be.
8. **No persisted facility announcement enable flag.** `controller.js`'s header calls its `enabled` option "the facility
   switch (disabled ⇒ nothing is attempted)", but the value is not stored anywhere: the React shell seeds it as a literal
   `enabled: true` (`QueueAnnouncements.js:22`) and uses it only to choose the "audio off" badge, while `call-announcer.js:97`
   skips on `state.enabled === false`. The only persisted announcement record is the organisation-level block in
   `backend/organization/announcement_config.py` (`CONFIG_KEY = "announcement"`, holding `language` and `voice_packs`) — no
   branch/facility enable or language override exists. That absence is the substance of O‑2 and POD‑6.

---

## Governance and Skill Compliance

*(`.clinerules` §6 and §2 step 11.)*

| Domain (§4 row) | Governance applied | Evidence |
|---|---|---|
| Documentation: reading and writing | `.clinerules` §11/§12; `docs/governance/AMSDP_Docs_Index_V1.0.md` (incl. its trial-merge annex) | the index was read first; this report is placed in `implementation/` and registered in the same task |
| Repository/branch/publication discipline | `saas-cicd-workflow.md` as adapted (Assessment §3) | read-only commands only; no reset/clean/stash/checkout/force-push; the tip was compared with `ls-remote` rather than assumed |
| Multi-tenant data, schema, migrations | `saas-multitenant-data.md` §4–5 (adapted) | schema position taken from reports; **no** migration, DDL or database read performed |
| Queue / workflow transitions, audit | Business Rules Parts V–VII and X as recorded in the QUE‑006 reports; `backend/common/audit.py` context | audit open items (D‑7, B‑8) stated as unproven, not claimed |
| Evidence standard | `.clinerules` §7 | every section carries VERIFIED / REPORTED / IMPLEMENTED / NOT VERIFIED; no green-suite inference made |

**Skills:** none installed in this workspace (`.clinerules` §5; re-verified — no `.clinerules/skills/`, no `.claude/skills/`,
no repo `skills/`). No skill was used and none is claimed.

**Non-negotiables honoured:** no secret, token, JWT or credential is quoted; no code, schema or audit row was written; no
Git history was rewritten; nothing was deleted or overwritten (the destination filename was checked with `Test-Path` →
`False` before creation); no capability is claimed that this session did not verify.

**Deviation, declared:** this report is the only artefact written. It adds one new file and one unnumbered annex
registration, because `.clinerules` §11/§12 require it. Its content is an investigation, not an implementation, and it
changes no source file, migration, container or branch.
