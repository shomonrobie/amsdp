# AMSDP — Documentation Index (navigation)

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10 (revised 2026-11-21) · **Snapshot:** **109** markdown documents on disk, **106** of them registered below (mechanical basename check, Revision 37; re-counted in Revision 47) — **11** at the `docs/` root, **94** across the subject folders (including the 6 `architecture/saas/` documents registered in Revision 27 and the SaaS reconciliation report registered in Revision 29), and the **4** `docs/chatgpt/` planning files listed in that section (§12). Per-file sizes below; recompute with the *Maintenance* command. *(Document-count check, 2026-11-19, Revision 32: `find docs -name '*.md'` = 88; every basename on disk is named in a row except the two recorded in Revision 32's open item **O-3**. Earlier history: Revision 27 registered the six-document SaaS set → 81; Revision 28 closed **O-Y** (the `chatgpt/` count drift) at 81; Revision 29 added `governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md` → 82; Revision 30 corrected three records in place with no row-count change, still 82; Revision 31 added `product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` → 83; Revision 32 added the appointment/calendar reliability gap analysis and its remediation report → 85 registered, against 88 on disk; Revision 33 added the appointment-types/capacity/capability specification and the Q1–Q5 implementation report → **88** registered, against **90** on disk; Revision 34 added the QUE-006/OD-1 browser speech-synthesis implementation report → **89** registered, against **91** on disk, the same two documents still unregistered under O-3; Revision 35 corrected that disk figure by one — the **92**nd document is the Phase 3 queue/DQDS/QUE-006 gap analysis, on disk but unregistered, its row proposed in its own Appendix C and not applied → **89** registered, against **92** on disk.)*
> **Status:** active navigation artefact — intended to be read at the start of every task
> **Enforced by:** `.clinerules` §12 (reading) and §11 (writing)
> **Revision 2 — 2026-11-10**, task `AMSDP-DOC-GOVERNANCE-OWNER-DECISIONS-O1-O6-2026-11-10`:
> two tracked release-readiness documents relocated from the repository root into `docs/audit/`
> (owner decision O-6); AI Factory / AILI documentation registered as deliberately retained
> outside this tree (O-1); byte sizes refreshed for the eight documents whose cross-references
> were corrected (O-2); two over-broad **R** flags corrected to **—** (O-5 scope). Evidence:
> `docs/governance/AMSDP_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md`.
> **Revision 3 — 2026-11-10**, task pair `AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10`
> and `AMSDP-OPS-ONE-COMMAND-RESTART-2026-11-10`: two new implementation reports
> registered under `implementation/` (the index grew from 48 to 50 documents).
> The BanglaNameSense report records why it lives here and not in
> `ai_factory/docs/` (§11), and the restart report documents the one-command
> start/restart procedure now described in `README.md` §3.
> **Revision 4 — 2026-11-11**, task `AMSDP-PRECOMMIT-PUSH-READINESS-AUDIT-2026-11-11`:
> `audit/AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` registered (the index grew from
> 50 to 51 documents). The report classifies every change in the working tree by owner,
> records the sensitive-data and runtime-artefact exclusions, and returns a NO-GO on a
> wholesale commit with a conditional GO on a four-commit plan.
> **Revision 5 — 2026-11-11**, task `AMSDP-PRECOMMIT-REMEDIATION-2026-11-11`:
> `audit/AMSDP_PreCommit_Remediation_Report_V1.0.md` registered (the index grew from
> 51 to 52 documents). It records the remediation of blockers B-1…B-7 — credentials
> removed from the Compose files, `_tools/` scripts and the demo seed and replaced by
> a single environment-driven pattern, artefact ignore rules, the malformed image
> asset renamed — plus three findings the predecessor audit did not cover
> (`database.py`/`alembic.ini` literal DSNs, historic exposure needing rotation, and
> the `.env`/`.env.example` contract). Behaviour preservation is proven by identical
> resolved-compose hashes for both stacks. Nothing was staged, committed or pushed.
> **Revision 6 — 2026-11-11**, task `AMSDP-FINAL-PREPUSH-DECISION-AUDIT-2026-11-11`:
> `audit/AMSDP_Final_PrePush_Readiness_Report_V1.0.md` registered — it closes D-1
> (credential rotation, verified end to end), assesses D-2 (the two mixed-ownership
> frontend files) and D-3 (the two tracked AI-Factory artefacts), verifies the twelve
> image assets, and returns a **conditional GO** with gates G-1…G-5. This revision also
> **fixes index drift found while reconciling**: two owner documents had never been
> registered — `AMSDP_Master_Feature_List_V2.5_…` (declares itself the **approved,
> active** master feature list, superseding V2.0–V2.4) and `AMSDP_Master_Feature_List_V2.4_…`
> (superseded, retained for traceability). V2.3 is therefore no longer "latest".
> The snapshot moves from 52 to **55** documents. Nothing was staged, committed or pushed.
> **Revision 7 — 2026-11-11**, task `AMSDP-FINAL-PREPUSH-CLOSEOUT-AUDIT-2026-11-11`:
> `audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` registered (the index grew
> from 55 to 56). It re-verifies D-1 from scratch, records the credential scan (382 files; the
> current database password appears in **0** of them), verifies the twelve images by SHA-256 and
> the 289 backend / 43 frontend tests, reconciles the documentation tree (56 = 56, no orphans or
> phantoms), and re-issues the first-push plan as **C-1…C-7 with explicit per-path lists**. It
> corrects the earlier record in four places — the owner-controlled set with uncommitted edits is
> **five** documents, not one (K-8); a live demo *user* password is already published in two
> tracked files (K-7/B-12); the previous plan left `README.md`, `docker-compose.yml` and
> `ai_factory/**` unassigned (K-9); and wildcard staging would have published owner documents
> (K-10). Verdict: **conditional GO**, with gates G-1…G-8. Nothing was staged, committed or pushed.
> **Revision 8 — 2026-11-12**, task `AMSDP-HACKATHON-MVP-STEP1-OWNER-DECISIONS-2026-11-12`:
> the owner decisions **G-1…G-8** were applied and verified (Step 1 of the hackathon-MVP
> close-out) — the demo `super_admin` password was **rotated** in the running database and in
> `.env`, and the four files that carried the old value or dead DSN literals were scrubbed
> (`demo/AMSDP_Hackathon_Demo_Runbook.md`, `demo/AMSDP_Demo_Credentials_V1.0.md`,
> `frontend/pages/index.js`, `security/AMSDP_M2_…md`, plus one synthetic fixture in
> `ai_factory/tests/unit/test_tools_analysis.py`); `backend/seed/seed_demo.py` now refreshes
> existing staff hashes from `.env` so a rotation propagates by re-running the seed. No document
> was created, moved or retired: the snapshot stays at **56** documents. Re-verified in the same
> task: 289 backend tests, 43 frontend tests, 5 AI-Factory analysis tests, and a 403-path secret
> scan with **0** hits for any live or legacy credential. Evidence and the re-issued Step 2 plan:
> `audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` §18. Nothing was staged,
> committed or pushed — `git diff --cached` remains empty.
> **Revision 9 — 2026-11-12**, task `AMSDP-HACKATHON-MVP-STEP2-COMMIT-PUSH-2026-11-12`:
> Step 2 executed. The 193-path plan C-1…C-7 was staged group by group, gate-checked (row count
> with `--no-renames`, **exact** set equality against the documented path list, and a secret scan
> over added lines only) and committed, then pushed: `hackathon-mvp` carries **7** commits on top
> of `eb87cac` — `261e1f4`, `8ab01d0`, `1448612`, `3cff475`, `e240bc5`, `7f39b4d`, `a0d6ded` —
> and the branch now exists on `origin` with its upstream set. Staged = 0; the 14 documented
> excluded paths remain uncommitted; 193 unique paths changed (+44,027 / −2,240).
> `audit/AMSDP_Tree_Commit_and_Push_Execution_Record_V1.0.md` is registered — the snapshot grows
> from 56 to **57** documents. It records the per-commit hashes, the three defects found in the
> *verification tooling* (not in the plan), the §18.8.10 end-state assertions, the post-push
> verification — `HEAD`, the local `origin/hackathon-mvp` ref and the remote's own
> `ls-remote` advertisement all report `a0d6ded` — and the updated R-1…R-7 register.
> **This revision and that record are committed as C-8** — message
> `docs(audit): record MVP commit and push execution`, exactly two authorised paths, created after the push. A commit
> cannot record its own hash, so verify it with `git log -1 --format=%H -- docs/audit/…Execution_Record_V1.0.md`.
> One document on disk is **not** registered here: `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md`, which appeared
> 2026-11-12 13:22 outside this task in a folder that is not among the §11 subfolders. It is left in place and
> **unregistered** rather than silently adopted (§11: uncertain-ownership files are reported, not migrated), so the
> on-disk count is 58 against the **57** registered above — an open item, not an index claim.
> **Revision 10 — 2026-11-12**, task `AMSDP-PROJECT-CONTEXT-REPORT-2026-11-12`:
> `audit/AMSDP_Project_Context_Report_V1.0.md` registered — an evidence-graded repository picture
> written for the external (ChatGPT) collaborator: §3.3/§3.4 verify the migration chain and the
> architecture against the tree (AR-1…AR-6), §4 the 14-table data model, §5 a per-capability matrix
> carrying an explicit status vocabulary, §6 the frontend rewrite seam **and the defect it produces
> (F-1: the PQT page fetches `/api/v1/track/…` while only `/track/…` is rewritten, so the page 404s)**,
> §7 risks P1-1…P3-4, §9 the document-vs-tree conflicts C-1…C-6, §10 a ranked reading list, §11 the
> re-verification protocol and owner questions Q-1…Q-6. The snapshot grows from 57 to **58**
> documents. The report re-runs nothing: every capability row is `TESTED` (reported), `IMPLEMENTED`
> (static) or `ABSENT`, and nothing is claimed as `VERIFIED`. `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md` **remains
> unregistered** — it is still an uncertain-ownership file in a folder outside §11, so the on-disk
> count is 59 against the 58 registered here (open item, not an index claim). Two owner-controlled
> documents carry uncommitted edits (`AMSDP_Master_Feature_List_V2.0_Draft.md` +118/−11,
> `architecture/AMSDP_System_Architecture_V1.0.md` +63/−11); they were **read only** and are flagged in
> the report's §9.3. Nothing was staged, committed or pushed.


> **Revision 11 — 2026-11-13**, task `AMSDP-OWNER-DECISIONS-Q1-Q6-2026-11-13`:
> the six owner decisions taken 2026-11-12 in answer to the context report's §11 questions
> are now recorded and implemented. Two new documents are registered — a **decision record**
> `decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md` (the first entry in `decisions/`, which
> this index previously listed as empty) and `implementation/AMSDP_Owner_Decisions_Implementation_Report_V1.0.md`
> (scope, evidence, `TESTED`/`VERIFIED` grading, deviations, open items). The snapshot grows
> from 58 to **60** documents. Implementation: an explicit platform-administration capability
> set replaced the `super_admin` wildcard and every cross-organization access is audited
> (Q-1); a shared middleware records denied requests 403/404/422 in all eight services
> (Q-2); the demo limitations report gained the corrected registration row and the manual
> tracking-link fallback (Q-3, Q-4); `.github/workflows/ci.yml` plus
> `backend/requirements-dev.txt` add the first pipeline, **unexecuted** and reported as
> `IMPLEMENTED`, not `VERIFIED` (Q-5); the two owner-controlled documents were preserved
> verbatim (Q-6). Backend suite 289 → **318 passed**; frontend build ✓ and 43 tests ✓.
> Nothing was pushed; the `docs/chatgpt/` open item of Revision 10 is unchanged.

> **Revision 12 — 2026-11-13**, task `AMSDP-CI-FIRST-RUN-FAILURE-2026-11-13`:
> the first execution of the pipeline added by Revision 11 (run `43352469508`) failed both
> jobs, and both causes are now diagnosed and reproduced locally. One new document is
> registered: `implementation/AMSDP_CI_First_Run_Failure_Investigation_V1.0.md`. The
> snapshot grows from 60 to **61** documents. Backend: the `alembic` **CLI was declared in
> no requirements file**, and `python -m alembic` is unresolvable from `working-directory:
> backend` because `backend/alembic/` (no `__init__.py`) shadows the distribution as a
> namespace package — `.github/workflows/ci.yml` now calls the console script
> (`alembic upgrade head`) and `backend/requirements-dev.txt` declares `alembic>=1.13`.
> Frontend: the committed `frontend/pages/patients.js` is the pre-refactor page, so three
> assertions in `tests/banglanamesense-integration.test.mjs` fail; the fix is the owner's
> uncommitted page refactor and was **not** committed by this task. Verified locally: the
> chain applies to a pristine database and the backend suite passes **318** on that
> chain-created schema; the frontend suite is **43/43** with the owner's page. Neither job
> is green *on a runner* yet, and nothing was pushed — see the report's §7 and §9.

> **Revision 13 — 2026-11-14**, task `AMSDP-V25-RECONCILIATION-PROPOSAL-2026-11-14`:
> one new document is registered —
> `audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md` — a
> **read-only proposal**: the 2026-11-13 owner decisions D-01 (two informational payment
> indicators), D-02 (Missed-Turn Recovery remains approved MVP/P0) and D-03 (BanglaNameSense
> is advisory Phase 1 scope) recorded as register-ready text, plus a reconciliation matrix
> C-01…C-09 covering Business Rules V1.1, MVP Scope V1.1, Master Feature List V2.5, the PQV
> decision, the decision register and `.clinerules`. The snapshot grows from 61 to **62**
> documents. **Nothing was applied**: no governed document, schema, endpoint, component or
> test changed, and this task's only edit to an existing file is this index entry plus this
> revision line. Each proposed replacement was located by exact single-occurrence match and
> proved to apply with `git apply --check` (rc=0 for all eight patches and for the combined
> 45,809-byte patch). The proposal carries blocking open items — **U-1** (the decision
> records are reconstructed from their effects, because no upstream decision artefact exists)
> and **U-2** (the MTR reconciliation direction follows the later 2026-11-09 approval and
> must be inverted if the owner intended a demotion) — and reviews nothing as implemented.
> Nothing was staged, committed or pushed; the pre-existing `frontend/styles/global.css`
> modification and the untracked `_tools/`, `docker-compose.demo.yml` were not touched.

> **Revision 14 — 2026-11-14**, task `AMSDP-V25-RECONCILIATION-PROPOSAL-2026-11-14` (continued):
> one new document is registered —
> `audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.1_DRAFT.md` — which
> **supersedes V1.0 as the current review copy**; V1.0 stays on disk unmodified and is retained
> for history. V1.1 corrects all three V1.0 decision records: **D-01** is the two permitted
> informational Yes/No payment answers and settles *nothing* about storage, nullability,
> placement, permissions or migration (V1.0 wrongly required nullable columns and an Alembic
> migration); **D-02** is the `.clinerules` §1/§10 authority-reference correction (V1.0 wrongly
> made it the Missed-Turn Recovery approval and wrongly extended the change to §11); **D-03** is
> the authorisation to prepare this reconciliation material (V1.0 wrongly made it the
> BanglaNameSense Phase 1 decision). The Missed-Turn Recovery MVP/P0 approval of 2026-11-09 and
> BanglaNameSense's advisory Phase 1 status are recorded in V1.1 §3.4 as separate restated
> decisions (R-1, R-2), not attributed to D-02/D-03. V1.1 also withdraws one incorrect V1.0
> finding (there is no V2.5 §22/§25.7 cross-reference drift) and drops the patch that would have
> rewritten the historical `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`.
> The set is now 6 patches / 35 edits / 30 hunks / 34,079 bytes, every one proved with
> `git apply --check` (rc=0) against HEAD `c5fc646`. The snapshot grows from 62 to **63**
> documents. Still **read-only**: no governed document, code file, schema, migration, endpoint,
> component or test was modified; no test suite was run, because no code changed. Remaining
> blocking items are the owner's: **U-3/U-4** (D-01 storage, permission, interface and audit
> design — they do not block the proposal text), **U-5** (status of the superseded Business Rules
> revision draft), **U-6** (permission to apply the `.clinerules` patch, which is an owner act
> under §11) and **U-7** (final C-09 wording). **U-1 and U-2 are closed.** Nothing was staged,
> committed or pushed; `frontend/styles/global.css`, `_tools/` and `docker-compose.demo.yml`
> were not touched.
> **Revision 15 — 2026-11-15**, task `AMSDP-DEMO-DIAGNOSIS-CURRENT-STATE-AUDIT-2026-11-15`:
> one new document is registered — `audit/AMSDP_Current_State_Demo_Diagnosis_and_Feature_Audit_V1.0.md`
> — a **read-only** diagnosis of why the hackathon demo fails and staff cannot sign in: the four
> defects D1–D4 (frontend container down since 2026-11-12 with no restart policy; host-level
> container↔container forwarding dropped after two Docker daemon restarts on 2026-11-14 with `ufw`
> active; the isolated `amsdp_demo` stack never created on this host, its queue empty and its demo
> appointments stale-dated; and the `/orgs` SSR `sessionStorage` crash), proof that the six demo
> credentials are **correct** (6/6 bcrypt verifications, booleans only, no secret reproduced), the
> 64-route / 14-page / 311-test feature matrix graded IMPLEMENTED / TESTED / VERIFIED, and the
> prioritised repair plan R-1…R-10. Nothing was fixed, restarted, seeded or committed. The header
> count is also corrected in this revision: the tree held **65** documents before this entry while
> the header still claimed 61 and the revision log claimed 63 — the tree is the truth (§12) — so the
> snapshot now reads **66** after registering this document. One further file is registered for the
> first time in the new `chatgpt/` section below:
> `chatgpt/AMSDP_Hackathon_Implementation_Backlog.md`, added by the HEAD commit and never indexed;
> that folder is **not** one of the §11 subject folders, so the file is reported and left in place
> (ownership not asserted, nothing moved, no manifest entry required).
> **Revision 16 — 2026-11-15** (same task, second pass after an **owner correction**): the owner
> stated that AMSDP had been configured to start automatically, that the demo users existed and that
> sign-in had worked. Re-verification **confirmed both halves** and added **Part G** to
> `audit/AMSDP_Current_State_Demo_Diagnosis_and_Feature_Audit_V1.0.md`: the startability mechanism that
> does exist (`_tools/amsdp_stack.sh`, documented in `README.md` §3 and in the one-command restart
> report) is a **manual one-command start with no auto-healing** — the omission of `restart:` policies
> is a recorded, deliberate deferral (`deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md:642-643`
> and `:724`); no systemd unit, cron entry or XDG autostart exists for AMSDP; all ten containers report
> `RestartPolicy=no`; and the automation itself is **untracked** (`git ls-files _tools` → 0 files).
> The same pass **corrected four statements** in Parts A–C (frontend exit `255` was a stack-wide stop
> and a *skipped* restart, not a crash; the restart-policy omission was a documented deferral, not an
> oversight; the inference that absent audit rows prove no login was **wrong**, because `staff_login`
> writes no audit row — `backend/identity/main.py:184-219`; and journal rows read without `--utc` are
> local time, not `Z`). It also adds open items **O-G** (which command restarted nine of ten
> containers on 2026-11-14 is unattributable — the snap Docker journal is empty for those windows),
> **O-H** (`_tools/` and `docker-compose.demo.yml` uncommitted) and **O-I** (`docs/demo/` content is
> stale and, being owner-controlled, was cited but **not modified**). New evidence rows 19–26 in the
> report's F.4. File size in the table below refreshed. No document was moved, renamed or deleted.
> **Revision 17 — 2026-11-15**, task `AMSDP-AUTOSTART-AND-DEMO-LOGIN-FIX-2026-11-15`: the owner
> then instructed that the stack be made to **restart automatically with demo data so all users
> can log in**, so the read-only diagnosis was followed by a repair. One new document is
> registered — `deployment/AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` — recording what
> changed and how it was verified. In outline: the real blocker was **`D2`** (the old
> `amsdp_default` bridge had lost its forwarding rules; a newly created network on the same
> daemon forwarded correctly, which isolated it to per-bridge state), fixed by **recreating the
> network** (`down`/`up`) with **no `sudo`, no `ufw` change and no firewall disabled**;
> `D1` cleared by starting the frontend; `D4` fixed in `frontend/pages/orgs.js` by adding the
> `typeof window` guard that every other page already had. Automatic restart is now two
> independent layers: `restart: unless-stopped` on all ten services in `docker-compose.yml`
> (the earlier deferral in `deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md:642-643`
> is explicitly superseded in that file's header, by owner instruction) and the systemd user
> unit `amsdp-autostart.service` installed by the new `_tools/install_autostart.sh`, which
> waits for the daemon, runs `_tools/amsdp_stack.sh up`, then re-runs the idempotent demo seed.
> Three new `_tools/` scripts were added (`amsdp_autostart.sh`, `install_autostart.sh`,
> `verify_demo_login.sh`). Verified live: 10/10 services `running/healthy/ok`; **6/6 demo
> accounts return `HTTP 200` with the correct role** through
> `http://localhost:3100/api/v1/staff/login`; all ten pages server-render `200`; the daemon
> restarted a failing probe container 7 times in 9 s; the boot unit ran to `status=0/SUCCESS`
> with `Linger=yes`; demo data is dated today (7 appointments, 2 queue entries); and row counts
> including `audit_events` (3,484) are **identical before and after**, so nothing was lost.
> Not verified and recorded as open items: a real crash of a production service (needs root),
> and an actual host reboot (unit state verified, reboot not performed) — **O-J**, **O-K**,
> **O-L**; the carried **O-H** (`_tools/` still untracked) and **O-I** (`docs/demo/` stale,
> owner-controlled) remain open, plus **O-M** (`frontend/styles/global.css` carries unrelated
> uncommitted work that is now inside the rebuilt image). No document was moved, renamed or
> deleted; nothing was staged or committed.
> **Revision 18 — 2026-11-15**, task `AMSDP-APPOINTMENT-CALENDAR-VIEW-2026-11-15`, owner
> instruction *"refactor বুকিং to calendar view like standard booking system"*. One new
> document is registered — `implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md`
> — recording the refactor and its evidence. In outline: the appointment surface is now a
> **week/day grid** (`frontend/components/AppointmentCalendar.js`) over a **pure, unit-tested
> model** (`frontend/lib/calendar/grid.js`, 15 tests), with `তালিকা` preserving the old
> table, a **slot picker** that replaces free-text time entry and shows `booked/capacity`
> per slot, and a patient **type-ahead** replacing the 100-row select. Two traps were
> handled explicitly: `slot_templates[].day_of_week` is **0 = Monday**
> (`backend/seed/seed_demo.py:101`) while the display week starts **Saturday**, so
> `pythonWeekday()` and `jsDay()` are separate functions; and the real demo data contains
> off-grid times (`21:30`, `02:45`), so the row axis is the **union of slot starts and
> appointment times** — a naive slot grid would have hidden those bookings. One additive,
> backwards-compatible backend change: optional `date_from`/`date_to` on
> `GET /api/v1/appointments` (inclusive, `422` on a malformed bound, organization scoping
> unchanged, no migration). Verified: frontend **72/72** `node --test`, production build
> `exit 0`, backend appointment suite **25/25**, live window query `200` with **0 rows
> outside the range**, the old single-`date` filter still returning the same 8 rows for
> 2026-11-15, malformed bounds `422`, and the rebuilt image serving the new bundle. The
> component's **emitted markup** is also asserted, without a browser and without a new
> dependency, by server-rendering it with the SWC compiler and `react-dom/server` that
> already ship with Next (`frontend/tests/calendar-render.test.mjs`, 6 tests, report §7.4).
> Not verified and recorded as open item **O-N**: no browser session was used, so the
> rendered pixels and click paths still need a human look; plus **O-O** (seeded schedules
> cover only Mon–Thu), **O-P** (demo bookings outside clinic hours), **O-Q** (appointment
> reads remain organization-scoped, not branch-scoped) and **O-R** (an empty out-of-hours
> row still offers `+`; current behaviour pinned by a test, left for an owner decision).
> Carried **O-M**
> (`frontend/styles/global.css` untouched by this task). No document was moved, renamed or
> deleted; nothing was staged or committed.

> **Revision 19 — 2026-11-15**, task `AMSDP-FACILITY-DOCTOR-01` (frontend half), owner
> instruction to finish the redesigned facility/doctor screens on top of the already-green
> backend. One new document is registered —
> `implementation/AMSDP_Facility_Doctor_Frontend_Implementation_Report_V1.0.md` — and the
> snapshot grows from 68 to **69** documents. In outline: `/doctors` is now a real directory
> (canonical `01XXXXXXXXX` mobile, structured specialities, per-branch chamber, BMDC badge
> and verification dialog, photograph) instead of a form over one free-text speciality;
> `/schedules` is a chamber-assignment screen (weekday + half-open window + room, with the
> two 409s warned about client-side by `windowConflicts`); `/facilities` is new and renders
> the floor → department → room tree with room usage and the speciality catalogue. Two new
> pure modules carry the rules — `frontend/lib/phone.js` (mirror of
> `backend/common/phone.py`) and `frontend/lib/facility.js` (weekdays 0 = Monday, BMDC
> transitions, chamber labels, overlap/conflict logic) — and both are covered by
> `frontend/tests/facility-doctor.test.mjs` (22 tests, including JSX compilation of the three
> pages through the SWC build shipped with Next, and Bangla/English dictionary parity).
> That suite also proved the frontend proxy table complete: `PATCH`/`DELETE
> /api/v1/floors|departments|rooms|specialties/{id}` were missing from
> `frontend/next.config.js`, so facility edits and retirements would have 404'd in the
> browser while the API itself was correct; the rewrites were added and the test was shown
> to fail without them.
> Verified: frontend **93/93** `node --test`, `next build` **exit 0** with `/doctors`,
> `/facilities`, `/schedules` emitted, `alembic heads` → `f7d2b4c6e8a1` as the only head, and
> a live `amsdp-db-1` read confirming `alembic_version = f7d2b4c6e8a1`, the
> `facility_floors|departments|rooms`, `doctor_branches` and `schedule_sessions` tables, the
> doctor `bmdc_*` columns and the appointment chamber-snapshot columns. The stack was then
> **rebuilt** (`docker compose up -d --build frontend organization doctor scheduling
> appointment`) because the compose images are baked with no bind mounts, and the rebuilt
> stack was probed: all six services healthy, `/facilities`, `/doctors` and `/schedules` serve
> 200, the previously 404 facility/session/profile routes answer 401 (i.e. they now exist),
> an authenticated `org_admin` read returns 200 from the facility tree, speciality, doctors,
> sessions and registration-policy endpoints, and the frontend proxy returns FastAPI JSON
> rather than Next's HTML 404 page for the by-id facility and session routes (report §5.4).
> **Not verified and recorded as open items:** nothing rendered was checked in a browser
> (report §7.1), the backend suite was not re-run (§7.2), and the demo organisation still has
> an empty facility tree, so the screens open on their empty state (§7.8). No document was
> moved, renamed or deleted, so no manifest entry is due. The work is committed as
> `729054c`, `7f681c4` and `3875f18` on `hackathon-mvp` and pushed to `origin`.

> **Revision 20 — 2026-11-16**, task `AMSDP-FRONTEND-UX-DEMO-01` (demo readiness: the
> dialog focus defect, the shared design system, the Doctor/Facility redesigns, calendar
> polish and a realistic demo dataset). One new document is registered —
> `implementation/AMSDP_Frontend_Usability_Shared_Design_System_and_Demo_Readiness_V1.0.md`
> — and the registered row count grows from 68 to **69**. In outline: the committed
> `Modal` ran `useEffect(() => el.focus(), [onClose])`, so an inline `onClose` prop made
> every keystroke re-focus the panel and a receptionist could type exactly one character;
> `Modal` is now a thin wrapper over a Radix-based `Dialog` that focuses once on open, and
> `frontend/tests/dialog-focus.test.mjs` guards the defect class (no component or page may
> call `.focus()` inside an effect). A shadcn-style token layer plus 13 primitives replaced
> per-page inline styling; `/doctors` and `/facilities` were rebuilt on it; the appointment
> calendar was re-paletted onto the same tokens without breaking its SSR markup contract.
> `components/AppShell.js` now reads the `sessionStorage` session after mount, removing one
> React #418/#423 hydration failure; the page-level remainder is open item **O-1**.
> `backend/seed/seed_demo.py` gained a facility tree, a bilingual speciality catalogue, ten
> doctors, thirty patients, ten schedules, a rolling −3…+7-day appointment week and a
> guarded `--reset`; the development database went from 60 organisations / 596 staff / 295
> doctors / 1 632 patients to 54 / 6 / 10 / 30, and the reset **refused to delete
> `audit_events`** (4 646 rows intact), which is why 54 audit-only husk organisations
> survive — owner decision needed (**O-4**).
> Verified in this session: frontend **96/96** `node --test`, backend **216 passed** on a
> scratch `amsdp_test` database, `next build` **exit 0**, the frontend **image rebuilt** and
> serving the new UI (container healthy), `_tools/verify_demo_login.sh` **6/6**, and a
> headless-Chrome acceptance run that drove the real UI — signing in through the login
> form, typing `রহ` → `রহিম ` → `রহিম উদ্দিন` into the add-doctor dialog while asserting the
> caret stayed in the field after every chunk, then opening the facility tree, the calendar,
> a doctor's queue and a patient search: **12/12 checks pass**. Two layout defects were
> found only because that run rendered the pages — the legacy `.flex` alias in
> `styles/global.css` was silently applying `gap` and `align-items:center` to every Tailwind
> `flex` container (centring and shrink-wrapping the facility card stack and the dialog
> body), and `Field` labels inherited ambient alignment; both are fixed and both are
> recorded with before/after evidence. A jsdom-based DOM test was attempted first and
> abandoned after repeated OOM kills on this host; that is stated in the report rather than
> hidden. Nothing was moved, renamed or deleted, so no manifest entry is due. Nothing was
> staged, committed or pushed; `docs/chatgpt/` is still unregistered (carried as **O-7**).

> **Revision 21 — 2026-11-16**, task `AMSDP-SYMPTOM-01` (optional bilingual symptom
> recording and the onset question in the appointment booking form). One new document is
> registered —
> `implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` —
> and the registered row count grows from 69 to **70**. In outline: a new
> `symptom_catalog` table carries 79 curated, patient-reported symptoms in both scripts
> with synonyms, category, speciality *ranking hints*, source and review status
> (`curated`, **not** clinically validated); a new `appointment_symptoms` table records
> each selected symptom as `kind = catalogue | free_text` with a booking-time **name
> snapshot**, a shape `CHECK` and two partial unique indexes for duplicate suppression;
> and `appointments` gains `symptom_onset_code` (a closed seven-answer vocabulary — never
> a forced date) plus an optional note. Migration `b3d7e91f6a24` (guarded, forward-only,
> no backfill). Two routes were added (`GET /api/v1/symptoms`,
> `GET /api/v1/symptoms/onset-options`) and the two booking payloads gained four optional
> fields; every appointment payload now carries `symptoms[]` and the onset answer.
> Reschedule and transfer copy the complaint forward while the original visit keeps its
> own rows. The browser-side search **reuses** `lib/bangla-name-sense/normalize.js` and
> adds only multi-alias lookup plus a speciality *tie-break*; nothing is pre-selected and
> neither age nor sex is passed to the picker. Verified in this session: **25** new
> appointment integration tests and **9** shipped-catalogue data tests pass, the
> appointment module is **50 passed**, the full backend suite is **389 passed / 9 failed**
> where all nine failures are a pre-existing isolation defect in
> `backend/doctor/tests/test_doctor.py` (unmodified, last committed 2026-11-12; recorded
> as the report's **O-2**), frontend **135/135** `node --test` (39 new) and `next build`
> **exit 0**. **No browser run was performed for this feature** and the running demo
> containers still carry the previous images, both stated in the report (§12). Nothing was
> moved, renamed or deleted, so no manifest entry is due. Nothing was staged, committed or
> pushed.
> While reconciling, the maintenance check found **index drift**: `find docs -type f -name
> '*.md'` reports **72** files while 69 were registered. One is the report added above
> (rows 69 → **70** in the subject trees); the other two are `docs/chatgpt/` planning
> documents that the `chatgpt/` section described as "one unregistered document".
> `AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md` had never been
> mentioned at all; `AMSDP_Project_Handover_2026-11-12.md` is unregistered by an earlier
> revision on purpose. Both are now listed in that section, neither is moved or adopted,
> and the snapshot line states the on-disk total (72) with that split made explicit.

> **Revision 22 — 2026-11-16**, task `AMSDP-SYMPTOM-01`, **Phase 1 (runtime)** — no new
> document, so the registered row count stays **70**; the existing
> `implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md`
> gained a §18 ("Phase 1 — demo runtime rebuild and browser verification") and its row
> now records the real size, **67,128** bytes from `wc -c`. In outline: migration
> `b3d7e91f6a24` verified applied, 79 catalogue rows untouched, 5 320 audit rows intact
> and **no database reset**; `amsdp-appointment` and `amsdp-frontend` rebuilt and only
> those two containers recreated (the other seven were deliberately left running — no
> other service enforces `symptom.*` or maps the new tables, recorded as O-15); both
> healthy, `/health` and `/health/ready` 200. Verified through the **frontend proxy**
> (the browser's own path): 79 items, 79 `name_bn` and 79 `name_en`, 13 categories,
> seven onset codes, 401 unauthenticated, 403 for `include_inactive` as `receptionist`
> versus 200 as `org_admin`. Six bookings covering no symptom / one / three / free text
> / onset-only / mixed all returned **201** with the expected rows and audit metadata
> (counts, ids and the onset code — never the patient's words); an unknown symptom id
> and an invalid onset code both returned **422** without leaving a partial record. The
> shipped matcher, run against the live entries, resolves `জ্বর`→`fever`,
> `fever`→`fever` and the synonym `গা গরম`→`fever`. A **real-Chrome** run (Playwright
> 1.63 driving the installed Google Chrome) signed in through the login form and drove
> the picker by keyboard: focus sampled after every keystroke of `জ্বর` stayed in
> `book-symptoms-input`; `ArrowDown`/`Enter` added chips for Bangla, English and the
> patient's own words; chip removal returned the caret; and the booking reached the
> server as `POST /api/v1/appointments` **201** with the free text verbatim —
> **34/35 checks**, the single failure being the app-wide pre-existing React hydration
> errors (#418/#423) that also fire on `/dashboard` and `/patients` (new **O-12**). The
> detail-dialog read-back was **7/7**. O-1 and O-3 are now closed; new O-11 (Banglish
> queries do not match), O-13 (token numbers collide across doctors on one date), O-14
> (seven verification appointments left in the demo DB) and O-15 (seven images still
> carry the pre-change `common/`) are recorded for the owner. Nothing was moved,
> renamed or deleted, so no manifest entry is due; `git status` is byte-identical to
> the pre-phase snapshot, nothing staged, nothing committed, nothing pushed, `HEAD`
> still `133ce83`.

> **Revision 23 — 2026-11-16**, task `AMSDP-APPT-LIST-UX` — appointment UX refactor
> (cards, toolbar, server-paged list). **No new document**, so the registered row count
> stays **70**: the existing
> `implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` gained a
> §11 and its row now records the real size, **40,404** bytes from `wc -c`. In outline: the
> calendar card became a patient-first four-row card (name + token, `time · doctor`, the
> status **in words** as well as colour, the chamber snapshot), with the fourth card in a
> week cell replaced by an `আরও N` control (`chipLayout()`/`moreLabel()` in
> `lib/calendar/grid.js`, pure and tested); the ad-hoc header became `PageHeader` +
> `Toolbar`/`Filter`/`SearchInput`/`Select`/`BranchSelect` with a 300 ms debounced search
> and a clear-filters action that appears only when something is filtered; and `তালিকা`
> became a server-paged view over one new read-only route,
> `GET /api/v1/appointments/list` (search on name/mobile/token, doctor/status/branch/date
> filters, whitelisted sort with `422` on anything else, `25/50/100` pages, envelope
> `{items,total,page,limit,pages}`, branch scope from the token with a non-disclosing
> `404`), behind a new pure client model `frontend/lib/calendar/list.js`. **No scheduling,
> lifecycle or queue rule changed**; no migration; no write path added. Verified: frontend
> **146/146** `node --test` (8 new `calendar-list`, 2 new render, 1 new contract test),
> `next build` **exit 0** (`ƒ /appointments 18.5 kB`), backend appointment suite
> **76/76** (26 in the new `test_appointment_list.py`), both images rebuilt and healthy,
> live probes `200/42` rows with `pages=9`, page 2 → 17 rows, `sort=patient` → A→Z,
> `422` on bad sort/order/date/limit, `404` on an out-of-scope branch, `401` without a
> token, `q=%`/`q=_` → 0 rows, and a **real-Chrome** run of the shipped page at **22/22**
> checks (cards, `আরও 1`, sortable headers with `aria-sort`, search 25→2, clear-filters).
> One measured inconsistency is recorded as **O-S**: the grid endpoint is
> organization-scoped (41 rows over two branches) while the new list is branch-scoped
> (37 rows), because `.clinerules` §3 requires the latter — so the header now prints the
> grid count only while the calendar is visible. New **O-T** (a chip falls back to
> `#<id>` for doctors absent from `/api/v1/doctors`; demo data), **O-U** (pager digits stay
> Latin beside API-valued dates) and **O-V** (preflight off ⇒ the shared `Button` keeps the
> UA border; predates this task) are recorded; **O-N** is narrowed by the Chrome pass but
> not closed. Nothing moved, renamed or deleted, so no manifest entry is due; nothing
> staged, committed or pushed.

> **Revision 24 — 2026-11-16**, task `AMSDP-RESTART-RUNBOOK` — **one new document**, so the
> registered row count goes **70 → 71**: `deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md`
> (14,427 bytes, `wc -c`), with a new row under `deployment/`. It answers the owner's
> question *"do I have to restart the whole platform to see a code change?"*: **no for the
> change already delivered** — `amsdp-frontend-1` and `amsdp-appointment-1` were recreated after
> the code changed (up 49 min / ~1 h while the other eight had been up 11–29 h), all ten
> `healthy`, `GET /api/v1/appointments/list` without a token answers `401` (so the route is in
> the running image), `/appointments` answers `200`, and the Chrome pass was 22/22 — and **yes
> for any further change**, because the source is `COPY`ied into the images and compose mounts no
> code, so `docker compose restart` is a no-op for code and `backend/common/` forces all eight
> backend rebuilds. It ships `_tools/amsdp_rebuild.sh` (auto-detects changed services, rebuilds
> only those, waits for readiness, then verifies; `--check` and `--verify` are read-only and were
> the modes run here — the apply path was not re-run because nothing needed rebuilding). No
> schema change, no migration, no data touched; nothing staged, committed or pushed. New open
> items **O-W** (`_tools/` is untracked), **O-X** (readiness is not behavioural proof) and
> **O-Y** (this index recorded 2 `docs/chatgpt/` files; the tree holds 4 — header corrected to
> the verified **74 = 70 + 4**, and the drift left visible for the owner). `README.md` also gained
> two rows in its command table so the new script is discoverable from where restarts are already
> documented.

> **Revision 25 — 2026-11-16**, task `AMSDP-APPT-FILTER-DIAGNOSIS` — **one new document**, so the
> registered row count goes **71 → 72** and the on-disk snapshot **74 → 75**
> (72 in the `docs/` trees + 4 `docs/chatgpt/`):
> `audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md`, with a new row under `audit/`. It
> answers the owner's question *"why doesn't the search box or the Status/Branch filter change the
> appointments on the calendar?"* with a diagnosis only: **in Week and Day view the search box and
> both pickers write only into the paged list's query state, while the grid is rendered from a
> separate `GET /api/v1/appointments` request built solely from the calendar window and the doctor**
> — measured as **0** `/appointments` requests after typing a name (chips stayed at 40) and a
> correct `GET /appointments/list?q=Tariqul&status=CANCELLED&branch_id=…` on switching to List.
> Findings F-1…F-9 (the grid endpoint has no `q`/`branch_id` and the page never sends the `status`
> the endpoint does support; grid is org-scoped while the list is branch-scoped, 47 vs 42 for a
> receptionist; the list silently clamps to the visible week; no highlighting; an unknown status
> returns `200`/0 rows; no names in the grid payload; a source-contract test that **asserts** the
> defective request shape and a therefore green 146/146 suite; Bangla-name search unverified for
> lack of data), per-filter and per-view evidence matrices, four root-cause classes, minimal
> correction options with blast radius, and two owner decisions it deliberately does not take —
> **O-AA** (should the calendar be branch-scoped like the list?) and **O-AB** (may a search leave
> the visible week?). No code, data, schema or migration was changed; the diagnosis tooling lives in
> `/tmp/amsdp_diag/` and was not committed; nothing staged, committed or pushed. New open items
> **O-Z** (filters do not reach Week/Day), **O-AC** (test-contract gap) and **O-AD** (Bengali-name
> data gap).
> **Revision 26 — 2026-11-16**, task `AMSDP-CALENDAR-FILTER-01` — **no new document**, so the
> registered row count stays **72** and the on-disk snapshot stays **75**; two registered
> documents gained an appended section (nothing moved, renamed, deleted or rewritten):
> `implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` (**§12**, file
> 40,404 → 67,732 bytes) and `audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md`
> (**Part I — Resolution**, 45,613 → 50,236 bytes, plus a `RESOLVED` line in its header). The task
> implements the correction the Revision 25 diagnosis only described: the toolbar's search box and
> its **Status**/**Branch** pickers now reach **Week and Day** as well as the list, from one shared
> predicate module (`backend/appointment/appt_filters.py`) and one client filter builder
> (`buildFilterParams`), with a new counts-only `GET /api/v1/appointments/matches` date index that
> tells the calendar *where else* a search matched (`near` ordering, cap 120 + `truncated`), a
> banner with a one-click route to the nearest other date, `<mark class="appt-cal-hit">`
> highlighting on the name and the token, **422** for an unknown status or a malformed date
> instead of a silent empty grid, names joined into the grid payload (replacing the 30 per-week
> patient lookups the diagnosis measured), and `appointment.read` required on the grid route. The two decisions the diagnosis
> left open were taken as **D-1 branch-scoped** (the calendar follows the token's branch — 37 rows
> for the demo receptionist, `404` for an out-of-scope branch) and **D-2 the search may leave the
> week** (the banner says so). Evidence: frontend **167 passed / 0 failed**, backend **108 passed**,
> live API probes (10 cases incl. no-token `401`, out-of-scope `404`, `q=%` literal, unknown
> status `422`), and a real-Chrome run of **24 recorded steps across two roles** with
> `consoleErrors: []` / `failedResponses: []` — which is also what caught a sentence defect the
> counts could not (`"1 more matches on 1 other dates"`), fixed by `matchesBannerKey` plus three
> EN/BN keys. No schema change, no migration, no product rule changed; nothing staged, committed
> or pushed. New open items **O-AG** (D-1/D-2 not yet filed in `docs/decisions/`), **O-AH** (the
> 120-date index cap) and **O-AI** (cards-per-cell under a filter); **O-S**, **O-T**, **O-Z**,
> **O-AA**, **O-AB** and **O-AC** are closed, **O-AD** and **O-N** remain open.
> **Revision 27 — 2026-11-17**, task `AMSDP-HYBRID-SAAS-ARCH-2026-11-17` — **six new documents**,
> so the registered row count goes **74 → 80** (the 74 rows before included 3 `chatgpt/` planning
> files; 71 were `docs/`-tree documents, and 71 + 6 = **77** `docs/`-tree files on disk, verified
> with `find`; plus 4 `docs/chatgpt/` = **81** total on disk against **80** registered rows).
> All six live in a **new subfolder**, `architecture/saas/`, registered above as its own sub-table
> rather than as six rows in the `architecture/` table — the folder is one coordinated set, not six
> independent documents. Sizes are `wc -c`: architecture specification **57,124**, current-state
> audit **41,705**, IAM specification **41,112**, tenant/organization specification **34,421**,
> subscription/entitlement specification **33,204**, implementation roadmap **35,588**.
> What the set is: a single, mutually cross-referenced specification of the multi-tenant SaaS
> layer — the request pipeline and module keys, a corrected audit of what the tree does today
> (R-01…R-18, C-1…C-9), identity and authorisation, tenant lifecycle, subscription/entitlement
> (including the `entitlements_version` cache contract and the numeric-limit model) and a phased
> roadmap (Phases 0–5+, risk register K-1…K-11, abort criteria, requirement traceability).
> **One canonical open-item registry** — `O-SaaS-1…O-SaaS-16`, defined once in the architecture
> specification §14.3; every other document cites those ids and none mints its own.
> Nothing was implemented: **no code, schema, migration, endpoint, component, test or running stack
> was touched**, so no test suite was run and nothing is claimed as `TESTED` or `VERIFIED` from this
> task. No existing document was moved, renamed, overwritten or deleted, so no manifest entry is
> required (§11); `architecture/saas/` is a subfolder **inside** the §11 tree, not a new top-level
> output location. Nothing was staged, committed or pushed. No new index-level open item: the
> substantive ones are the sixteen `O-SaaS` entries in the architecture specification §14.3, which
> is where they belong (one registry, one place).
> **Revision 28 — 2026-11-17**, task `AMSDP-CHATGPT-REFERENCE-DOCS-ADOPTION-2026-11-17` — **no new
> document written, two existing documents newly tracked and registered**: on owner instruction the
> two remaining ChatGPT-produced reference documents in `docs/chatgpt/` were added to the repository
> — `AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md` (40,267 bytes, 1,337
> lines, SHA-256 `5a988b00…ade58a3f8`) and
> `AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` (20,944 bytes, 509 lines, SHA-256
> `4954cf81…7a7bc52e`), both self-dated 2026-11-16. Registered row count **80 → 81** while the
> on-disk snapshot stays **81** (77 `docs/`-tree rows + 4 `chatgpt/` rows), so for the first time
> **every** markdown file in `docs/` has a row. Consequences recorded rather than assumed: the
> `chatgpt/` section heading and prose were rewritten from "three documents, two unregistered" to
> "four, all registered", and a `Read when`/`Owner` cell was corrected on the multi-sector row —
> these are table corrections under §12, not a rewrite of any document's content. **O-D** is closed
> as to *ownership* (the owner supplied these files, so provenance is established) and stays open as
> to *placement* (folding the folder into `audit/` or `governance/` is still the owner's call);
> **O-Y** (the `chatgpt/` count drift, open since Revision 24) is **closed** — 4 files on disk, 4
> rows. **Nothing moved, renamed, overwritten or deleted**, so no migration-manifest entry is
> required (§11); both files were added byte-for-byte as supplied, which the SHA-256 values above
> pin. Both remain **reference material, not authority** (§1) and neither authorises implementation
> — the Connect document says so itself. Credential scan of both files (`ghp_`, `sk-`, `AKIA`,
> private-key blocks, `api_key`/`password` assignments, long `Bearer` tokens): **0** hits. **No
> code, schema, migration, endpoint, test or running stack was touched**, so no test suite was run
> and nothing is claimed `TESTED` or `VERIFIED`; no new index-level open item is raised.
> **Revision 29 — 2026-11-17**, task `AMSDP-HYBRID-SAAS-DECISION-RECONCILIATION-2026-11-17` —
> **one new document, no document moved**: all six documents of the `architecture/saas/` set were
> revised **in place to Revision 2** to reconcile them against the Product Owner's decision packet
> (`O-SaaS-1…O-SaaS-16` plus directions A1–A4), and the reconciliation report itself
> (`governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md`, 25,554 bytes) is the one new
> file. Registered rows **81 → 82**, on-disk snapshot **81 → 82** (78 `docs/`-tree rows + 4 `chatgpt/`
> rows), so every file on disk still has a row. Only the six size cells and their *Read when* text in
> the `architecture/saas/` sub-table were updated (post-revision `wc -c`: 98,511 / 46,232 / 46,345 /
> 39,178 / 37,293 / 43,005 against 57,124 / 41,705 / 41,112 / 34,421 / 33,204 / 35,588 at Revision 27). What changed in the set, in one line each: the architecture
> specification gained the ADR register (§12), traceability (§13), the **closed** decision registry
> with verbatim rulings (§14.3) and the engineering questions `EQ-1…8` (§14.3.1); the audit kept every
> finding **verbatim** and gained correction notes only, because its questions A-1…A-5 are now decided
> and its evidence grades are untouched; IAM gained multi-membership (§8, ADR-SAAS-014 superseding 013)
> and converted its open items into an applied-rulings table; the tenant specification gained the
> second-operator suspension (O-SaaS-14) and two-approver closure with data retained by default
> (O-SaaS-16); the subscription specification gained the settled platform-audit split (O-SaaS-2 option
> A), the approved ten module keys (O-SaaS-4) and explicitly does **not** create billing columns
> (O-SaaS-6); the roadmap converted its "decisions required" gates into "decisions applied" and moved
> **multi-membership from Phase 5+ into Phase 2** (`EQ-1…3`), adding the platform-audit table (2.15) and
> the two-person primitive (3.11 → 3.12). **Two-axis status** (decision vs evidence) is used
> throughout, `PROPOSED` is now a declared synonym of `SPECIFIED`, and **no decision advanced any
> evidence grade**: no code, schema, migration, endpoint, component, test or running stack was touched,
> so no suite was run and nothing is claimed `TESTED` or `VERIFIED`. Nothing was moved, renamed,
> overwritten or deleted, so **no migration-manifest entry is required** (§11). Nothing was staged,
> committed or pushed. Index-level open items: none raised — the set's open questions are `EQ-1…8`
> (engineering) plus `EQ-7`, which is explicitly an **owner** question, both already registered in
> architecture specification §14.3.1 rather than here.
> *(Post-commit note, 2026-11-17 — the owner subsequently instructed the commit: the reconciliation
> landed as `597d9b1`, `docs(saas): reconcile the six-document SaaS set with the owner decision
> packet`, 8 files / +1,220 −346, pushed to `origin/hackathon-mvp` and verified after the push. The
> clause above recording "nothing staged, committed or pushed" is the state **at the end of that
> task**, kept as written; Revision 30 records what followed. See
> `governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md` §M.1.)*
> **Revision 30 — 2026-11-17**, task `AMSDP-SAAS-POST-COMMIT-CORRECTION-2026-11-17` — **no new
> document, no move, no rename**: a documentation-only correction of three records in the six-document
> SaaS set and its reconciliation report. (1) **O-SaaS-15 / MFA.** The set had described operator MFA
> as `DEFERRED` with the risk "accepted for MVP" and MFA as the "first post-launch hardening item",
> which reads as optional or permanently accepted. It now separates three contexts — **hackathon MVP**
> (temporary exception, explicitly documented as a security risk, restricted to a limited authorised
> operator group), **production launch** (MFA **mandatory before any platform operator receives
> production access**) and **post-launch** (MFA already in place) — in architecture §1.5, the new
> §9.3 rule 7, §11's non-goal row, §14.3 and §14.4; IAM §13, §13.1, the new **§13.2** and §14.1; and
> the roadmap's phase table, §6.1, §8, §9.4, the new **§9.6 production-launch gate** and §14.1. No
> provider, protocol, enrolment flow, implementation status or test result was invented: MFA remains
> `NOT IMPLEMENTED` and every §9.6 gate box is unsatisfied. (2) **A3 profiles.** The report and one
> roadmap line still said "internal/dedicated"; both now state the approved set — `private`,
> `government`, `ngo`, `community`, `outreach` — as configurable presets independent of deployment
> pattern. Architecture §2.2 was already correct and was not rewritten. (3) **Commit status.** The
> report's header, §B, §E, §H, §K and §L no longer describe the reconciliation as uncommitted,
> unpushed or "sitting in the working tree"; §M records the commit, the push and this amendment as a
> subsequent documentation-only act, without rewriting the original task narrative. All three changed
> documents carry a **Revision 3** history entry (architecture §15.1/§15.3, IAM §15.1/§15.3, roadmap
> §15.1/§15.3); this index updated only their size cells, their *Read when* text, the report row and
> this revision block. **No decision, `A1–A4` direction or `EQ` question changed** (`EQ-4`, `EQ-5`,
> `EQ-7` remain open), **no document moved, renamed, overwritten or deleted** (no manifest entry,
> §11), and **no code, schema, migration, endpoint, component, test or running stack was touched**, so
> no suite was run and nothing is claimed `TESTED` or `VERIFIED`. Row count unchanged at **82**. No
> new index-level open item.

> **Revision 31 — 2026-11-17**, task AMSDP-MVP-FEATURE-CATALOGUE-2026-11-17 — **one new document**: product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md, a feature-level catalogue and acceptance checklist for the AMSDP Hackathon MVP. No code, schema, migration, endpoint, component, test or running stack was touched. Row count increased from 82 to 83.

> **Revision 32 — 2026-11-19**, task `AMSDP-APPT-RELIABILITY-01` — **two documents registered**:
> `audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` (created by the read-only
> analysis task on 2026-11-19, which recorded its own missing index entry in its §12 and supplied the
> pending line) and `implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`
> (the remediation of all 19 findings: 28 new backend tests, 9 new frontend tests, 3 grid tests, one
> production build; two findings closed only in part, with the owner decisions that would close them).
> No document was moved, renamed or deleted, so no migration-manifest entry is required. Row count
> increased from 83 to 85 registered, against 88 files on disk. **Open item O-3 (reported, not
> fixed):** two documents on disk are still unregistered — `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`
> and `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md`. Both belong to other
> workstreams whose work is still uncommitted; `.clinerules` §11 says documents of uncertain
> ownership are reported and left in place, so no row was invented for them here.

> **Revision 33 — 2026-11-19**, task `AMSDP-APPT-OWNER-DECISIONS-01` (documentation half, owner
> decision **Q6**) — **two documents registered, no document moved, renamed or deleted** (no
> migration-manifest entry, §11):
> `architecture/AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md` (the behavioural
> specification of Q1–Q5: appointment types and the outside-session override, the `slot_allocations`
> capacity guarantee with its stated limits, the capability catalogue and the closed delegable list,
> the check-in matrix, the grant endpoints, the audited schedule/session/policy events) and
> `implementation/AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md`
> (what was built and what the evidence for each claim is, plus open owner items O-1…O-7).
> Three existing records were **appended to, never rewritten**: the gap analysis gained
> **Appendix D** (closure status of all 19 findings — F-01 and F-18 are now closed, superseding the
> front matter's "closed only in part"), the remediation report gained **§10** (same two closures),
> and — outside this index — the RBAC audit gained a capability-catalogue delta. The size cells for
> both appended reports were refreshed and their *Read when* text updated; the predecessor's
> **open item O-3** is unchanged, so the RBAC audit and the QUE-006 catalogue addition remain
> unregistered by their own workstreams. Row count increased from 85 to **88 registered**, against
> **90** files on disk (the same two documents remain unregistered under **O-3**, which this
> revision does not touch). No product code, schema, migration, endpoint, component or test was touched
> by *this documentation task*; the suite results it cites belong to the implementation task and are
> attributed to it, not claimed here.

> **Revision 34 — 2026-11-20**, task `AMSDP-QUE-006-OD-1` — **one document registered, no document
> moved, renamed or deleted** (no migration-manifest entry, §11):
> `implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md`
> (the browser-native Web Speech API mechanism for QUE-006 under owner decision OD-1: the adapter,
> the approved Bangla/English content with the token-serial pronunciation rule, voice selection that
> never substitutes a language, activation/autoplay refusal detection, duplicate and overlap control,
> the `/queue` operator boundary, 49 new frontend tests with the exact command and result, and open
> items O-1…O-10 — including the room clause no queue payload can supply, the absent facility
> configuration (OD-2), the absent server-side event and audit, and the fact that **no browser or
> device playback run was performed**, so nothing is claimed VERIFIED).
> This revision also refreshes the snapshot counts in the header (90 → **91** on disk, 88 → **89**
> registered, subject-folder rows 75 → **76**). **Open item O-3 is unchanged**: the previous two
> revisions already record that `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`
> and `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` remain to be registered by
> their own workstreams, and this revision does not adopt them either. No backend file, schema,
> migration, endpoint, permission or product document was touched by this task; the frontend suite
> result it cites belongs to that implementation task.

> **Revision 35 — 2026-11-20**, task `AMSDP-QUE-006-OD-1` (count correction only) — **no document
> registered, moved, renamed or deleted; no row added**. Revision 34 stated "91 on disk"; the
> measured figure is **92** (`find docs -name '*.md' | wc -l`), and the subject-folder count is
> **77**, not 76, because the 92nd document is
> `audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` — on disk, but neither named nor
> registered here. It was created by task `AMSDP-PHASE-3-GAP-ANALYSIS` (read-only discovery,
> 2026-11-20), and that task deliberately supplied its own row in its **Appendix C** "for owner
> review, not applied"; this revision **does not apply it** either — an index row is the index
> owner's editorial decision, not a side effect of correcting a count. The arithmetic therefore
> reads: **89** registered + the **2** documents recorded under **O-3** + this **1** unregistered
> gap analysis = **92** on disk. **O-3 is unchanged**, and committing the two documents it names
> (done in the same push as this revision) does not register them here.
> No code, schema, migration, endpoint or test was touched. The figure is a measurement, not a
> verdict: nothing about the gap analysis is ACCEPTED by being counted. Two stale **size cells**
> were refreshed to the bytes on disk (measurements only, no text rewritten): this task's own
> report row (26,520 → **28,119**, this revision's §15.1 amendment), and
> `implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md`
> (16,394 → **41,767**, grown by that document's own Phase-1D capability record of 2026-11-18,
> which is not this task's work).

---


> **Revision 36 — 2026-11-20**, task `AMSDP-QUE-006-DOCTOR-NAME-REMOVAL-AND-AUDIO-CATALOGUE` — **two new documents registered under `implementation/`**, so the registered row count goes **89 → 91** and the on-disk snapshot stays **92**: `implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` — complete audio generation catalogue (28 recording assets for the doctor-name-free QUE-006 announcement composition strategy), and `implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` — implementation report covering doctor-name removal, the four approved sentences, test results, and remaining limitations. No document was moved, renamed or deleted; no migration-manifest entry is required (§11).
> **Revision 37 — 2026-11-20**, task `AMSDP-QUE-006-GEMINI-TTS-UTILITY` — **one new
> document registered under `implementation/`**: `implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md`
> — the standalone Gemini TTS audio-generation utility in `scripts/que-006-audio/`
> (10 modules + README, no dependency added), the command runs that were actually
> executed with their observed exit codes, the honest state of the asset set
> (**1 of 28 clips on disk** — the deliberate 300 ms silent pause; the 27 spoken
> clips are not generated because `GEMINI_API_KEY` is absent), container-structure-only
> validation with no audio decoder on the machine, the declared
> `en.phrase.no-room` comma override awaiting an owner decision, and the fact that
> nothing in it is VERIFIED or ACCEPTED.
>
> **Count recheck (mechanical, not a tally).** `Get-ChildItem docs -Recurse -Filter '*.md'`
> now returns **95** documents — **11** at the `docs/` root, **80** across the subject
> folders, **4** in `chatgpt/`. Matching every disk basename against this file's text
> finds **94** named and **1** unregistered:
> `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md`, an
> owner-controlled document (§11) that this task has no authority to register or
> annotate. The running row tally was **91** after Revision 36 and is **92** after
> this one, so the tally understates the mechanical count by two — a drift of the
> same kind already recorded for O-3, carried forward here as **open item O-4**
> rather than guessed at. The subtitle below now carries the verified 95/94 figures
> instead of the stale 92/89. No document was moved, renamed, overwritten or
> deleted; no migration-manifest entry is required (§11).
>
> **Revision 38 — 2026-11-20**, task `AMSDP-QUE-006-GEMINI-TTS-UTILITY` (continuation) —
> **no document added, moved, renamed or deleted**, so the registered row count stays
> **92** and the on-disk snapshot stays **95** (94 named, 1 intentionally unregistered;
> O-4 open). Two measurement/content refreshes only:
> `implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md`
> (18,327 → **26,986**, grown by its own §11 Revision 2 record) and that row's
> *Read when* text, which previously stated two facts that verified runtime state has
> since contradicted: the key is no longer absent but **rejected** by Google
> (`API_KEY_INVALID`; the resolved value is 35 characters, not the 39 of an AI Studio
> key), and `ffmpeg`/`ffprobe` 9.1 **are** installed and now used, so validation is
> container-plus-codec rather than container-only. The utility gained
> `scripts/que-006-audio/lib/decode.mjs`, key-shape diagnostics (`describeKeyShape()`)
> and an `api-key-invalid` error classification; nothing was generated (still
> **1/28** clips on disk) and nothing is VERIFIED or ACCEPTED.
>
> **Revision 39 — 2026-11-20**, task `AMSDP-QUE-006-GEMINI-TTS-UTILITY` (continuation) —
> **no document added, moved, renamed or deleted**; registered rows stay **92**, on-disk
> snapshot stays **95** (O-4 still open). One measurement/content refresh: the same
> report (**26,986 → 36,519**, grown by its own §12 "Revision 3" record) and that row's
> *Read when* text. The utility is no longer Gemini-only: it now selects a provider
> (`--provider gemini|elevenlabs`, default gemini) over two new modules
> (`lib/elevenlabs-tts.mjs`, `lib/provider.mjs`) plus a shared `lib/tts-error.mjs`.
> Verified in this session: syntax of all 16 modules, the catalogue self-check, both
> dry-run paths, absence-of-key exit codes, `validate.mjs` (still 1/28), and — most
> importantly — a **live 401 from `api.elevenlabs.io` with a placeholder key**,
> classified `api-key-invalid` with `stopRun` and followed by a probe short-circuit.
> **No ElevenLabs clip was generated** (no valid key exists) and **no claim is made that
> Bangla works** on `eleven_multilingual_v2`: the documented language list returned
> HTTP 403 to this session, so the preflight probe and a native speaker remain the only
> acceptable evidence. Nothing is VERIFIED as audio and nothing is ACCEPTED.

> **Revision 40 — 2026-11-21**, task `AMSDP-QUE-006-GEMINI-TTS-UTILITY` (continuation) —
> **no document added, moved, renamed or deleted**; registered rows stay **92**, on-disk
> snapshot stays **95** (O-4 still open). One measurement/content refresh: the same
> report (**36,519 → 43,034**, grown by its own §13 "Revision 4") and that row's size
> cell. A real ElevenLabs key turned up in `.env.local`, but **under a voice-id variable
> name**, and it authenticates while being **unscoped** for every endpoint the utility
> uses (`401 missing_permissions … models_read / voices_read`) — so the run stays blocked
> on an owner action, not on code. That live data exposed and fixed three defects:
> `key-permissions` is now classified separately from a rejected key (naming the missing
> scope instead of advising a pointless re-copy), a synthesis-only least-privilege key is
> no longer hard-failed by the model/voice listing checks, and a stale 6-character
> `ELEVEN_LABS_API_KEY` can no longer silently shadow a complete key in `.env.local`
> (the resolver reports what it ignored). Also established: the `GEMINI_API_KEY` value is
> an `sk-` key, not an AI Studio key, which explains every earlier `API_KEY_INVALID`.
> **Still no ElevenLabs clip exists**; still 1/28 assets on disk; nothing VERIFIED as
> audio, nothing ACCEPTED; Bangla on `eleven_multilingual_v2` remains unclaimed.
> **Superseded 2026-11-21 by Revision 41:** 28 recordings are now on disk and 27 of
> them are standardised and technically validated — read the standardisation report
> below before trusting the "1/28" in this row.

> **Revision 41 — 2026-11-21**, task `AMSDP-QUE-006-AUDIO-FORMAT-STANDARDISATION` —
> **one document registered**: `implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md`
> (**42,041 bytes**), so registered rows go **92 → 93** and the on-disk snapshot
> **95 → 96**. No document was moved, renamed or deleted, and no existing document's
> content was rewritten; **open item O-4** (the index tally understating the mechanical
> document count) is unchanged and unchanged in cause.
>
> The task converted, validated and manifested the audio set under
> `frontend/public/audio/`: **27 WAV masters** (PCM 44.1 kHz/16-bit/mono) and **27 MP3
> playback files** (44.1 kHz/mono/128 kbps CBR), with all **28 originals preserved
> byte-for-byte** in `frontend/.audio-originals-backup/` and hashed in
> `ORIGINALS.json`. The manifest was rebuilt as schema
> `AMSDP-QUE-006-audio-assets/2.0` with 54 verified checksums.
>
> Two contradictions were found by inspecting the filesystem rather than the manifest,
> and both changed what could honestly be delivered. First, `bn/phrase/room-suffix.wav`
> is **byte-identical to the English silence placeholder**
> (`sha256 651d0bac16d2…`, 300 ms, `mean_volume −91.0 dB`), so
> **`bn.phrase.room-locative` (`-এ আসুন।`) has no recording anywhere** — the instructed
> rename to `room-locative.wav` was therefore **not** performed, because it would have
> made a missing Bangla clip indistinguishable from a present one. Second,
> `ffmpeg`/`ffprobe` **9.1 are installed but not on `PATH`**, which the utility now
> resolves explicitly instead of concluding the tools are absent.
>
> **Status: PARTIALLY COMPLETE — 27/28 technically validated, 1 asset missing.** No
> `humanReviewStatus` was set above `pending` and nothing is pronunciation-approved;
> `playable.integratedWithApplication` remains `false` in the manifest and in fact —
> `frontend/lib/announcements/speech-synthesis.js` is untouched and no component reads
> `audio/manifest.json`. Prerecorded-audio playback remains **unimplemented**, and this
> revision makes no claim that any recording has been listened to.
>
> **Superseded 2026-11-21 by Revision 42:** the Bangla locative recording was supplied
> and converted, so the set is **28/28** and the "no recording anywhere" statement above
> no longer describes the tree. The refusal to rename the English silence placeholder
> into the Bangla slot still stands — that decision was correct, and the real recording
> arrived separately rather than being manufactured from a placeholder.

> **Revision 42 — 2026-11-21**, task `AMSDP-QUE-006-BANGLA-LOCATIVE-CONVERSION` —
> **no document added, moved, renamed or deleted**; one existing document **updated in
> place**: `implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md`
> (**42,041 → 59,816 bytes**, V1.0 → V1.1 with a new §17). Registered rows stay **93**
> and the on-disk snapshot stays **96**. No migration manifest entry was required,
> because nothing was relocated and no content was rewritten — V1.0's §0–§16 are intact
> and the correction is stated in §0.1 and §17, so the earlier "missing recording"
> finding remains on record instead of being erased.
>
> The task converted the recording the owner supplied at
> `frontend/public/audio/bn/phrase/room-locative.mpeg` into the delivery contract.
> **The extension is wrong**: `ffprobe` reports container `mp3`, codec `mp3`, **48 kHz**
> mono, 1.819979 s, 44,973 bytes, `sha256 7c2c58bc…ee3cbd`, `mean_volume −22.1 dB`,
> `max_volume −4.5 dB` — real speech, and a rate that genuinely required resampling.
> Outputs: **master** `bn/phrase/room-locative.wav` (PCM 44.1 kHz/16-bit/mono,
> 160,602 B, `sha256 bc01c501…b98c`) and **playback** `bn/phrase/room-locative.mp3`
> (44.1 kHz/mono/128 kbps CBR, 30,137 B, `sha256 b15c1b16…99f4`), the MP3 encoded
> **from the validated master**, never from the source.
>
> The original is preserved unchanged in both places: the in-tree `.mpeg` still hashes
> to `7c2c58bc…ee3cbd` and its verified copy is at
> `frontend/.audio-originals-backup/bn/phrase/room-locative.mpeg` (`copied-verified`),
> taking the backup record to **29** entries. `manifest.json` was rebuilt as schema
> `AMSDP-QUE-006-audio-assets/2.0` with the entry `bn.phrase.room-locative`,
> `spokenText: "-এ আসুন।"`, `technicalValidationStatus: pass`,
> `humanReviewStatus: pending`, `playbackDerivation: encoded-from-master`, and summary
> `complete: true` (28 masters, 28 playback, 0 missing, 0 failing, **0 human-approved**).
>
> Validation ran **strict** in all three scripts, with `--allow-missing` deliberately
> not used: `validate-audio-assets.mjs` exit 0 (`28/28 pass`, `56` checksums verified,
> `29` preserved originals re-verified, CBR frame spread `0.3 kbps`),
> `validate.mjs` exit 0 (`28/28`), `rebuild-audio-manifest.mjs --check` exit 0
> ("manifest is current"). A before/after SHA-256 baseline of all 70 tree files proves
> the blast radius: **2 files added, none removed, none other modified** except
> `manifest.json`.
>
> Disclosed tool change: `lib/audio-standard.mjs` no longer declares
> `bn.phrase.room-locative` as `missing-content`, and gained an explicit
> `ORIGINAL_SOURCE_BY_ID` override (with `originalCandidatesFor()`) so the master is
> derived from the `.mpeg` rather than from our own 128 kbps playback;
> `standardise-audio.mjs` now shares that candidate list instead of duplicating it.
> **Still unimplemented and unclaimed:** prerecorded-audio playback in the frontend
> (`speech-synthesis.js` untouched, `integratedWithApplication: false`, no component
> reads the manifest), human listening review for all 28 clips (O-3), trailing-silence
> trimming (O-2, now covering this 1.15 s of silence that is **in the supplied
> recording**), and the extra `.m4a` / placeholder files in the served tree (O-7).
> O-1 (record the Bangla locative clip) is **closed**.

> **Revision 43 — 2026-11-21**, task `AMSDP-QUE-006-HUMAN-VERIFICATION-PREP` —
> **one document registered**: `implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md`
> (**27,650 bytes**), so registered rows go **93 → 94** and the on-disk snapshot
> **96 → 97** (mechanical count `Get-ChildItem docs -Recurse -Filter '*.md'` = 97,
> re-run in this session). No document was moved, renamed, overwritten or deleted;
> **open item O-4** (the index tally understating the mechanical document count by
> two, one of them the owner-controlled hackathon concept note) is unchanged and
> unchanged in cause.
>
> The task built **human-review preparation tooling only**, entirely inside
> `scripts/que-006-audio/preview/`: **20 composed WAV samples** (5 cases × 4
> announcement patterns) that are byte-for-byte concatenations of the 28 delivered
> clips — no ffmpeg, no re-encode, no trimming; a loopback-only static server; a
> reviewer page that imports the product's own `content.js` so no wording is
> hard-coded; a CSV/Markdown review record; and a headless-Chrome harness
> (`check-page.mjs`, 12 checks over the DevTools protocol, **no new dependency**)
> that **passed 12/12, exit 0, on the current files**. Composition was proven, not
> assumed: 120/120 copied PCM ranges identical to source, 20/20 decode-verified,
> 20/20 captions equal to `buildAnnouncement()`, and `catalogueUnchanged: true`
> across 72 hashed catalogue files (`manifestSha256 f4a10872…a328c`).
>
> **Nothing is approved.** All 28 assets remain `humanReviewStatus: pending`, no
> clip was modified, no product file was touched by this task, and no commit or
> push was made. The report records the measurements that the owner has to judge —
> **Bangla clips carry 0.874–1.388 s of trailing silence each (mean 1.260 s, all 14
> of them) against 0.014–0.331 s for English**, which is why Bangla samples run
> about twice as long — and the open items that block a verdict: the room-number
> range is still an unapproved "1–999" recommendation, the junction pause is 0 ms
> by measurement rather than by decision, the `en.phrase.no-room` override is
> undecided, and no reviewer is named. Human listening (O-3 of the standardisation
> report) remains the missing evidence.
> **Revision 44 — 2026-11-21**, task `AMSDP-QUE-006-VOICE-ROADMAP` —
> **one document registered**: `implementation/QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md`
> (**93,147 bytes**), so registered rows go **94 → 95** and the on-disk snapshot
> **97 → 98** (mechanical count `Get-ChildItem docs -Recurse -Filter '*.md'` = 98,
> re-run in this session). No document was moved, renamed, overwritten or deleted.
> The header snapshot line, which still read **95 on disk / 94 registered** and
> therefore understated the on-disk count by two after Revision 43, is corrected in
> this revision to **98 / 95** with the composition **11** at the `docs/` root,
> **83** across the subject folders and the **4** `docs/chatgpt/` documents
> (11 + 83 + 4 = 98). The registered tally moved by one, not by three: the two
> documents the old line failed to count were already on disk, so the remaining
> **98 − 95 = 3** difference is the pre-existing registration gap already recorded
> as Revision 32's **O-3** and Revision 43's **O-4**, unchanged in cause and in
> size by this revision.
>
> The task was **documentation and inspection only**. It records the Product
> Owner's decision that the current English and Bangla announcement output is an
> **approved DRAFT** — recordings and composition retained, no re-recording, no
> refactoring, and explicitly **not** audio-quality, pronunciation or production
> acceptance (§2) — and it classifies every QUE-006 feature with one evidence-based
> status from the seven permitted values: **two** independently verified (the audio
> catalogue's technical integrity; the isolated preview harness), **six** awaiting
> an owner decision, **nine** not implemented at all, the rest IMPLEMENTED BUT NOT
> VERIFIED. The material findings, all from this session's inspection:
> **no facility announcement configuration exists** (`organizations.config` has
> `queue_config`, `appointment_config` and `registration_policy` only), and the
> audited `appointment_config.py` route template is gated on `org.manage`, which
> **`branch_admin` does not hold** — so the approved configuration boundary cannot
> be reached without an owner decision (**POD-5**); **no room exists on a queue
> entry** (`QueueEntry`, `models.py:854-882`), so the with-room templates are
> unreachable (**POD-2**); the queue `call` action still **has no user interface**
> (QOP-001), so nothing can trigger an announcement; the speech adapter reports
> **`start`, not completion**; the **remote local-agent installation architecture has
> zero artefacts** in code or docs; and `frontend/public/audio/` holds **72 files
> against 56 manifest references**, leaving **15 unreferenced** (13 `.m4a`, one
> `.mpeg`, one mislabelled `room-suffix.wav`) for O-7.
>
> **Tests run in this task:** the four announcement suites — **53 tests, 52 pass,
> 1 skipped, 0 fail** (the skip is the JSX compile check; `next/dist/build/swc` is
> unavailable in this install). **Nothing is approved, nothing is implemented, no
> production code, asset, manifest, schema or permission was changed, and no commit
> or push was made.** Twelve Product Owner decisions (POD-1…POD-12) and the human
> listening review (O-3) remain open; the recommended next task is the isolated
> prerecorded playback engine, and it must not start without authorisation.
>
> **Revision 45 — 2026-11-21**, task `AMSDP-QUE-006-MASTER-IMPLEMENTATION` —
> **eight documents registered**, all in `implementation/`: the master plan
> (19,772 B), the W1 prerecorded-playback report (9,364 B), the W2 queue-integration
> report (9,159 B), the W3 voice-configuration report (7,519 B), the W4 room-support
> report (4,949 B), the W5 remote-installation report (7,268 B), the W6 asset
> dependency report (5,500 B) and the final implementation/verification report
> (19,529 B). Registered rows go **95 → 103** and the on-disk snapshot
> **98 → 106** (mechanical count re-run in this session:
> `Get-ChildItem docs -Recurse -Filter '*.md'` = 106), composition **11** at the
> `docs/` root, **91** across the subject folders and the **4** `docs/chatgpt/`
> documents (11 + 91 + 4 = 106). No document was moved, renamed, overwritten or
> deleted, so no manifest entry is owed; the remaining **106 − 103 = 3** difference
> is the same pre-existing registration gap recorded as Revision 32's **O-3** and
> Revision 43's **O-4**, unchanged in cause by this revision. Verified mechanically in
> this session: 103 rows whose first cell is a backticked `.md` path, resolving to 103
> distinct files, none duplicated; the three documents on disk with no row are
> `implementation/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
> `implementation/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` and
> `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`.
> **Two pre-existing byte figures were also corrected** to match the tree, because the
> index must not disagree with disk: `QUE-006_AUDIO_GENERATION_CATALOGUE.md`
> (15,234 → 17,144 B) and
> `QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md`
> (18,432 → 11,809 B). Only the numbers changed — both prose descriptions were
> checked against the documents and left exactly as their authors wrote them.
>
> The task implemented part of the QUE-006 programme and, just as importantly,
> **refused to implement the rest**. Landed: a pack-driven prerecorded playback
> engine (`segments.js`, `prerecorded-audio.js`), a controller transport switch with
> browser speech demoted to an explicitly configured alternative, a `waiting → called`
> transition rule plus a fire-and-forget page seam, a configuration-precedence
> resolver with organisation isolation, and a facility-side installer agent
> (`scripts/que-006-agent/`) with checksum verification, atomic install, rollback,
> crash recovery and offline use. Verified by **108 tests: 107 pass, 0 fail,
> 1 skipped**. Not landed, and stated as such in every report: the server-side
> voice-pack domain and its migration (this host has no `pytest`/`fastapi`/
> `sqlalchemy`, so a migration could not be run or its routes denied-tested), the
> room data (POD-2), the distribution API, any asset deletion (POD-7) and any
> browser, device or disconnected-network verification. No audio file, manifest,
> approved wording, schema or permission was changed; nothing was committed,
> pushed or deployed. **QUE-006 is explicitly not implementation complete.**
>
> **Revision 46 — 2026-11-21**, task `AMSDP-QUE-006-W1-W2-REPORT-RECOVERY` —
> **two documents registered**, both in `implementation/`:
> `QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_IMPLEMENTATION_REPORT.md` (19,448 B) and
> `QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md` (19,623 B). Registered rows go
> **103 → 105** and the on-disk snapshot **106 → 108** (mechanical count re-run in this session:
> `Get-ChildItem docs -Recurse -Filter '*.md'` = 108), composition **11** at the `docs/` root, **93**
> across the subject folders and the **4** `docs/chatgpt/` documents (11 + 93 + 4 = 108). No document
> was moved, renamed, overwritten or deleted, so no manifest entry is owed; the remaining
> **108 − 105 = 3** difference is the same pre-existing registration gap recorded as Revision 32's
> **O-3** and Revision 43's **O-4**, unchanged in cause by this revision. Verified mechanically:
> 103 rows before this revision (counting the index's own self-reference row at the `governance/`
> table, which is why the figure is 103 and not 102) resolving to 103 distinct files, none duplicated;
> the three documents on disk with no row are
> `audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
> `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` and
> `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`.
>
> **Why two new rows rather than a rename.** The Product Owner reported the W1/W2 reports missing
> after a power loss, under filenames ending `_IMPLEMENTATION_REPORT.md`; the earlier session had used
> the master plan's own convention, `QUE-006_W<n>_<NAME>_REPORT.md`. Both files existed and were
> intact, so neither was renamed: the two earlier reports stay byte-unchanged as history and the two
> new documents supersede them for naming and are self-describing about the relationship. The
> assignment's filename requirement and the master plan's §5 step 6 convention conflict; the conflict
> is recorded in both new documents and raised to the owner rather than resolved unilaterally.
>
> **A byte-size convention was discovered and applied.** Auditing all 101 size figures that resolve to
> a file showed **78 "mismatches" that are not stale at all**: the table's convention is the
> **LF-normalised UTF-8 byte count**, while this Windows worktree stores CRLF, so those rows differ
> from raw disk size by exactly the file's line count (proven on `product/AMSDP_Business_Rules_V1.0.md`:
> index 42,812 = LF size exactly, raw CRLF 43,924 = 42,812 + 1,112 lines). Those 78 figures were
> therefore **left alone**; "correcting" them to CRLF would have made the index wrong on the platform
> the `.clinerules` paths target. Eight figures were genuinely stale and were corrected, numbers only,
> prose untouched: `AMSDP_M2_Security_Implementation_Report.md` 6,374 → 6,390,
> `AMSDP_M4_Appointment_Implementation_Report.md` 4,374 → 6,169,
> `AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` 25,336 → 26,974,
> `AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` 58,648 → 95,368,
> `AMSDP_Tree_Commit_and_Push_Execution_Record_V1.0.md` 17,583 → 19,186,
> `AMSDP_Demo_Credentials_V1.0.md` 2,422 → 3,106, `AMSDP_Hackathon_Demo_Runbook.md` 11,331 → 11,794
> and `AMSDP_Limitations_Report_V1.0.md` 4,379 → 5,119. **Fourteen** figures were expressed as **raw CRLF bytes** instead of the LF basis, every one of them a
> QUE-006 document registered while working on Windows (Revisions 43-45), and each was converted,
> numbers only, prose untouched: `QUE-006_AUDIO_GENERATION_CATALOGUE.md` 17,144 → 16,877,
> `QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` 11,809 → 11,595,
> `QUE-006_Gemini_Audio_Generation_Implementation_Report.md` 43,034 → 42,439,
> `QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` 27,650 → 27,204,
> `QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md` 93,147 → 92,002,
> `QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` 59,816 → 58,904,
> `QUE-006_MASTER_IMPLEMENTATION_PLAN.md` 19,772 → 19,523,
> `QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_REPORT.md` 9,364 → 9,247,
> `QUE-006_W2_QUEUE_INTEGRATION_REPORT.md` 9,159 → 9,049,
> `QUE-006_W3_VOICE_CONFIGURATION_REPORT.md` 7,519 → 7,415,
> `QUE-006_W4_ROOM_SUPPORT_REPORT.md` 4,949 → 4,875,
> `QUE-006_W5_REMOTE_INSTALLATION_REPORT.md` 7,268 → 7,162,
> `QUE-006_W6_ASSET_DEPENDENCY_REPORT.md` 5,500 → 5,406 and
> `QUE-006_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` 19,529 → 19,257. After those changes the
> same audit reports **0 stale figures out of 103 checked**. One
> filing defect is **recorded, not fixed**: the row for
> `AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` sits in the
> `audit/` table although the document lives in `implementation/`; moving rows is a structural change
> beyond this task, so it is raised as an open item.
>
> **The task recovered and re-verified rather than implemented.** Every claim in the two new reports
> was re-derived from code and a fresh test run: W1 **22/22** own tests, the four pre-existing
> announcement suites **53 tests, 52 pass, 1 skipped**, all eight announcement suites **98 tests, 97
> pass, 1 skipped**, the agent suite **10/10**, and the whole `frontend/tests` population **270 tests,
> 266 pass, 2 fail, 2 skipped** — the two failures pre-existing and unrelated
> (`banglanamesense-dataset` pinned checksum, `calendar-render` Windows `E:` ESM URL). W1 is recorded
> as IMPLEMENTED AND TESTED at unit level and **not browser-verified**; W2 as **PARTIALLY
> IMPLEMENTED** because no UI control issues a queue `call` (POD-12), there is no polling on the queue
> page, event identity is per-client (`entry:<id>:call:0`), and no announcement audit record exists
> (POD-4). No production code, asset, manifest, schema or permission was changed; nothing was
> **Revision 47 — 2026-11-21**, task `AMSDP-QUE-006-POD-12-QOP-001` —
> **one document registered**, in `implementation/`:
> `QUE-006_POD-12_QUEUE_CALL_CONTROL_IMPLEMENTATION_REPORT.md` (30,225 B, the LF-normalised basis
> established in Revision 46; raw CRLF on this worktree = 30,672 B = 30,225 + 447 line terminators).
> Registered rows go **105 → 106** and the on-disk snapshot **108 → 109**; composition **11** at the
> `docs/` root, **94** across the subject folders (`implementation/` gained this document: 38 → 39) and
> the **4** `docs/chatgpt/` documents (11 + 94 + 4 = 109, re-counted mechanically in this session).
> No document was moved, renamed, overwritten or deleted, so no manifest entry is owed; the remaining
> **109 − 106 = 3** difference is the same pre-existing registration gap recorded as Revision 32's
> **O-3** and Revision 43's **O-4** — `audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
> `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` and
> `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md` — unchanged in
> cause by this revision, and the three are again the only unregistered basenames on disk. Before this
> revision the table held 105 rows resolving to 105 distinct basenames (no duplicates); after it, 106
> rows resolving to 106 distinct basenames. The pre-existing filing defect of Revision 46 (the
> `AMSDP_Phase_0_…_Report_V1.0.md` row sitting in the `audit/` table while the file lives in
> `implementation/`) is **still recorded, not fixed**, for the same reason: moving rows is a structural
> change beyond this task.
>
> **The document records an implementation, and is explicit about what the implementation does not
> prove.** POD-12 (approved) added the queue **Call** control that finally issues the server
> `PATCH /api/v1/queue/{id} {action:"call"}` (gap **QOP-001**), so the W2 announcement seam at last has
> a trigger: `frontend/lib/queue/queue-call.js` (new), the page handler plus button, three bilingual
> captions, one new frontend test file (**18 tests**) and two new backend tests. Production backend
> code, the permission matrix, the manifest and every audio asset are byte-unchanged; **no permission
> was granted and no schema changed**, which is why `branch_admin` gains nothing — it already held
> `queue.manage` through its pre-existing `queue.*` wildcard.
>
> **Evidence re-derived, not repeated.** `node --test tests/queue-call-control.test.mjs` **18/18**;
> `tests/queue-*.test.mjs` **116 tests, 115 pass, 0 fail, 1 skipped**; the whole `frontend/tests`
> population **288 tests, 284 pass, 2 fail, 2 skipped** — 270 + 18 = 288, the two failures being the
> pre-existing unrelated `banglanamesense-dataset` checksum and `calendar-render` Windows `E:` ESM URL.
> `frontend/node_modules` was absent, so dependencies were installed with the lockfile-preserving
> `npm ci --no-audit --no-fund` (**125 packages**, `package-lock.json` unchanged), and
> **`npm run build` now exits 0** — `✓ Compiled successfully`, `/queue` 13.4 kB — which also
> **supersedes the W2 row's "not compiler-verified" note** for `pages/queue.js`. The two JSX compile
> checks still report "swc unavailable" although the binary is installed: both import a bare `E:/…`
> specifier instead of `pathToFileURL()`, the same defect that makes `calendar-render` fail. That is
> recorded as **DEV-3** in the new report and deliberately not fixed here; a direct SWC transform of
> `pages/queue.js` (42,963 chars, containing `callEntry`) supplies the compiler evidence instead.
>
> **One required test could not be satisfied, and was not faked.** POD-12 permits calls by doctors
> "where their existing permissions grant `queue.manage`"; no doctor role holds it and it is absent
> from `DELEGABLE_CAPABILITIES`, so no grant can create it. The suite therefore asserts the truthful
> boundary in both matrices and the backend test asserts **403**; required test #2 is reported as
> **not satisfiable without a separate owner decision** (**DEV-1**), alongside **DEV-4** (the frontend
> `can()` mirror cannot see delegated grants). Backend execution, browser verification, cross-terminal
> dedupe (POD-8), announcement audit (POD-4), the room clause (POD-2/W4) and pronunciation (O-3) all
> remain **NOT VERIFIED**, and **W2 stays PARTIALLY IMPLEMENTED** — implementing POD-12 does not
> complete W2. Nothing was staged, committed, pushed or deployed; HEAD remains `37cf3d1`.


> **Revision 48 — 2026-11-21**, task `AMSDP-QUE-006-W2-RELIABILITY` —
> **one document registered**, in `implementation/`:
> `QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md` (25,558 B on the LF-normalised
> basis established in Revision 46; raw CRLF on this worktree = 25,934 B = 25,558
> + 376 line terminators). Registered rows go **106 → 107** and the on-disk
> snapshot **109 → 110**; composition **11** at the `docs/` root, **95** across
> the subject folders (`implementation/` gained this document: 39 → 40) and the
> **4** `docs/chatgpt/` documents (11 + 95 + 4 = 110, re-counted mechanically in
> this session). No document was moved, renamed, overwritten or deleted, so no
> manifest entry is owed; the remaining **110 − 107 = 3** difference is the same
> pre-existing registration gap recorded as Revision 32's **O-3**, Revision 43's
> **O-4** and Revision 47 — `audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
> `governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` and
> `implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`
> — unchanged in cause by this revision. Revision 47's recorded filing defect (the
> `AMSDP_Phase_0_…_Report_V1.0.md` row sitting in the `audit/` table while the file
> lives in `implementation/`) is **still recorded, not fixed**, for the same reason.
>
> **The document closes five named defects and refuses to claim the sixth thing.**
> It supersedes the "dedupe is per browser tab", "identity is invented by the
> client", "no announcement audit record", "no polling" and "an entry already
> `called` is never announced" findings of
> `QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md`: identity is
> now `qce:<entry_id>:<history index>` derived on the server from the append-only
> `status_history`, dedupe is a `UNIQUE(call_event_id)` row claimed with
> `ON CONFLICT DO NOTHING`, the announcement is audited as three separate facts
> (`queue.call` ≠ `requested` ≠ `completed`), and the queue page refreshes on a
> 20 s visible-tab timer with focus/visibility/online triggers. **No queue state
> machine, permission matrix, template or audio asset changed**; the only i18n
> addition is one bilingual key (`announceElsewhere`).
>
> **Evidence re-derived in this session, and the gap stated as loudly as the
> passes.** `tests/queue-announcement-delivery.test.mjs` **18/18**,
> `tests/queue-refresh-safety.test.mjs` **8/8**,
> `tests/queue-announcement-w2-integration.test.mjs` **19/19** (15 pre-existing +
> 4 new), `tests/queue-call-control.test.mjs` **18/18**; `tests/queue-*.test.mjs`
> **146 tests, 145 pass, 0 fail, 1 skipped** (was **116**: +18 +8 +4 = 30); the
> whole `frontend/tests` population **318 tests, 314 pass, 2 fail, 2 skipped**
> (was **288**), the two failures being the pre-existing unrelated
> `banglanamesense-dataset` checksum and `calendar-render` Windows `E:` ESM URL;
> **`npm run build` exit 0** — `✓ Compiled successfully`, `/queue` 15.3 kB (was
> 13.4 kB), which is the compiler evidence the skipped JSX check cannot give.
> `python scripts/que-006-w2-reliability/check_call_event_identity.py` executes the
> **13** pure identity tests **13/13** on this host; `py_compile` on the three
> touched backend modules exits 0. **The 18 new backend tests in
> `backend/queuing/tests/test_queue.py` were NOT run**: this host has no
> `fastapi`, no `pytest`, no `sqlalchemy`, no `psycopg2` and no PostgreSQL — the
> imports were attempted and all four failed. No browser, no audio device and no
> second terminal existed either, so **cross-terminal dedupe (POD-8), the persisted
> announcement audit (POD-4) and the migration are NOT VERIFIED** and **W2 remains
> PARTIALLY IMPLEMENTED**. Nothing was staged, committed, pushed or deployed.




## How to use this index


1. **Read this page first.** It is deliberately short so it costs almost nothing
   even on a small-context profile.
2. Find the row(s) whose *Read when* column matches the task.
3. Read **only** those documents — plus `grep` for a specific fact when a
   document is very large (the ASCII blueprint is 320 KB; never dump it whole).
4. Treat **R** rows as read-and-cite only: they are Product Owner-controlled and
   must not be edited, moved or renamed without explicit owner approval.

**Precedence reminder.** If a document disagrees with verified runtime state
(actual code, actual API response, actual test result), verified runtime state
wins (`.clinerules` §1). Report the contradiction — do not silently follow either
side.

**Folder map — what each folder answers**

| Folder | Answers the question | Read when the task involves |
|---|---|---|
| `docs/` (root) | What is approved? What is in scope? | Business behaviour, scope, feature set, UI/UX design intent, hackathon framing |
| `architecture/` | How is the system and the AI tooling structured? | Service boundaries, data model, agent roles, AI Factory internals, dev workflow — and, in `architecture/saas/`, the Hybrid SaaS set: tenancy, IAM, entitlements, tenant lifecycle, delivery roadmap |
| `product/` | What was decided, and what is being built next? | Business rules, MVP scope, product decisions, positioning, next-milestone readiness |
| `security/` | What security guarantees exist and how? | Auth, RBAC, tenancy enforcement, secrets handling, penetration findings |
| `implementation/` | What was built, and how was it tested? | Any change to an existing milestone/sequence feature; regression risk |
| `audit/` | What has been accepted, and what remains? | Claims of completeness, readiness, release gates |
| `deployment/` | How is it deployed and hardened? | Docker, compose, ports, environments, cloud architecture |
| `demo/` | How is it demonstrated? | Demo scripts, credentials, known limitations, API integration status |
| `governance/` | What rules bind the agent? | Rule changes, routing, document policy, evidence standards |
| `decisions/` | What was decided and why? | Any ADR-style decision record (Q-1…Q-6 recorded, see below) |
| `operations/` | How is it run day to day? | Runbooks, incident/response procedures (created when first needed) |
| `testing/` | What is the test strategy/evidence? | Test plans, coverage reports, verification logs (created when first needed) |

---

## Root — approved scope and design authority

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Business_Rules_V1.1.md` | 47,338 | **Any** task touching business behaviour — the newest business-rules text | R |
| `AMSDP_MVP_SCOPE_V1.1.md` | 37,492 | Deciding whether something is in or out of MVP | R |
| `AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | 129,129 | **The active feature list** — any question about what the product contains, module scope or product direction (declares itself approved and supersedes V2.0–V2.4) | R |
| `AMSDP_Master_Feature_List_V2.4_Modular_Healthcare_Platform_Edition.md` | 128,060 | Historical comparison only — superseded by V2.5; V2.3 baseline is reproduced inside it | R |
| `AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` | 68,316 | Historical comparison only — superseded by V2.4 and V2.5 | R |
| `AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md` | 62,621 | Historical comparison only | R |
| `AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md` | 60,740 | Historical comparison only | R |
| `AMSDP_Master_Feature_List_V2.0_Draft.md` | 37,975 | Historical comparison only | R |
| `AMSDP_Complete_ASCII_UI_UX_Blueprint.md` | 320,262 | Any UI/UX work: screens, layout, wording, states. **Grep it — never load whole** | R |
| `AMSDP_UI_UX_Blueprint_Structured_Assessment_V1.0.md` | 52,805 | Reviewing or revising the blueprint; UI gap analysis | R |
| `AMSDP — E-Health Hackathon Concept Note & Application Summary.md` | 11,879 | Framing a demo, pitch, or scope argument | R |

> **Version pairs.** `AMSDP_Business_Rules_V1.1.md` (root) is newer than
> `product/AMSDP_Business_Rules_V1.0.md`, and `AMSDP_MVP_SCOPE_V1.1.md` (root) is
> newer than `product/AMSDP_MVP_SCOPE_V1.0.md`. Where they differ, the newer
> version governs and the older one remains the approved baseline of record. Both
> are owner-controlled: read and cite, never modify either.
>
> **Master Feature List lineage.** V2.5 is the active, owner-approved master feature
> list and supersedes V2.0–V2.4; V2.3's own text is preserved inside both V2.4 and
> V2.5 for traceability. `.clinerules` §11 names V2.0–V2.3 explicitly and adds that
> the same read-only rule "extends to any other document the Product Owner
> subsequently declares authoritative" — V2.4 and V2.5 are covered by that clause and
> are registered here as **R**.

---

## `architecture/` — system and tooling structure

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_System_Architecture_V1.0.md` | 53,050 | Before changing any service boundary, data model or cross-cutting concern | R |
| `AMSDP_AI_Agent_Specification_V1.0.md` | 55,489 | Defining or auditing agent roles, outputs and evidence expectations | R |
| `AMSDP_AI_Development_Workflow_V1.0.md` | 46,237 | Changing how work is sequenced, reviewed or evidenced | R |
| `AMSDP_AI_Factory_Architecture_V1.0.md` | 56,079 | Touching `ai_factory/` internals (engine, harness, routing) | R |
| `AMSDP_AI_Factory_Implementation_Prompt_V1.0.md` | 44,288 | Prompt/behaviour changes inside the AI Factory | R |
| `AMSDP_Appointment_Types_Capacity_and_Capability_Spec_V1.0.md` | 28,085 | **Before changing appointment types, walk-ins, the outside-session override, slot capacity/seat allocation, the check-in capability, staff capability grants, or the cross-branch booking rule** — the behavioural specification of owner decisions Q1–Q5: the three persisted types and their refusal vocabulary, the `slot_allocations` guarantee and its stated limits, the capability catalogue with the closed delegable list, the check-in matrix, the grant endpoints, the audited schedule/session/policy events, the API surface and the statement→test map | — |

### `architecture/saas/` — the Hybrid SaaS architecture set (six coordinated documents)

One mutually cross-referenced set specifying the multi-tenant SaaS layer **before** any code is
written. `AMSDP_System_Architecture_V1.0.md` (above, **R**) remains the frozen design of record;
this set extends it and never overrides it (§1). **One canonical decision registry:**
`O-SaaS-1…O-SaaS-16` is defined once, in the architecture specification §14.3 — every other
document in the set cites those ids and mints none. **All sixteen were decided by the Product
Owner on 2026-11-17**; the eight engineering questions the rulings left open (`EQ-1…8`) are listed in
§14.3.1 of the same document. Status is two-axis throughout (decision vs evidence, architecture §1.3):
**no decision advanced an evidence grade, and none of the six documents describes working software.**

| File | Size (Rev 2) | Read when | Owner |
|---|---:|---|---|
| `saas/AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` | 102,190 | Starting **any** SaaS, tenancy, entitlement or platform-plane task — the request pipeline (§5), the fixed module keys (§6), the ADR register (§12), traceability (§13), the decision registry and rulings (§14.3), the engineering questions (§14.3.1), **the O-SaaS-15 MFA production precondition (§9.3 rule 7)**, revision history (§15) | — |
| `saas/AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` | 46,232 | Establishing what the tree actually does **today** before claiming a gap — findings R-01…R-18, corrections C-1…C-9, the §4.6 table of claims that were wrong, and the 2026-11-17 correction notes (evidence unchanged; the questions it raised are now decided) | — |
| `saas/AMSDP_Identity_and_Access_Management_Specification_V1.0.md` | 51,470 | Authentication, login, sessions, principals, RBAC, plane separation, **multi-membership** (§8, ADR-SAAS-014) and **the three MFA contexts — hackathon exception, production launch, post-launch (§13.2)** — §9 is the single authorisation chain (9 factors) | — |
| `saas/AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md` | 39,178 | Organization/branch lifecycle, suspension and closure (both **two-person**, O-SaaS-14/16), the platform metadata surface, tenant-switch rules, operator disclosure | — |
| `saas/AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md` | 37,293 | Plans, entitlements, the module gate, numeric limits, the `entitlements_version` cache contract, entitlement failure modes, the settled platform-audit split (§9.3) | — |
| `saas/AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` | 48,538 | Sequencing delivery — Phases 0–5+, flag-on/flag-off gates, multi-membership in Phase 2 (§5.2.1), the two-person primitive (§6.2 3.11), **the production-launch MFA gate (§9.6)**, risk register K-1…K-11, abort criteria, requirement traceability R-01…R-18 / C-1…C-9 | — |

> These six are **specification and planning documents only**. They change no code, schema,
> migration, endpoint or test; every claim in them is graded per `.clinerules` §7 (IMPLEMENTED /
> TESTED / VERIFIED / ACCEPTED), and the audit's findings are `static` or `reported`, never
> `VERIFIED` unless a second artefact confirms them.
>
> **Revision 2 of all six (2026-11-17)** reconciled them against the owner's decision packet. Sizes
> above are the current `wc -c` values after **Revision 3** of three of them (architecture, IAM,
> roadmap) and are: 102,190 / 46,232 / 51,470 / 39,178 / 37,293 / 48,538. They were
> 57,124 / 41,705 / 41,112 / 34,421 / 33,204 / 35,588 at Revision 27 and
> 98,511 / 46,232 / 46,345 / 39,178 / 37,293 / 43,005 at Revision 29. No new file was created inside
> `architecture/saas/`, so this sub-table keeps six rows; the reconciliation report itself is
> registered under `governance/` (Revision 29, re-sized in Revision 30). Nothing was moved, renamed,
> overwritten or deleted, so no migration-manifest entry is required (§11).

---

## `product/` — business rules, scope and decisions

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Business_Rules_V1.0.md` | 42,812 | Business behaviour where V1.1 is silent or where the approved baseline matters | R |
| `AMSDP_MVP_SCOPE_V1.0.md` | 34,976 | MVP boundary questions (the baseline of record) | R |
| `AMSDP_Product_Positioning_V1.0.md` | 14,963 | Wording, audience or value-proposition decisions | R |
| `AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | 21,583 | Any work on patient queue visibility, DQDS or patient communication | — |
| `AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` | 5,698 | Understanding *proposed* (not yet approved) rule changes — never cite as approved | — |
| `AMSDP_M9_Implementation_Readiness_Assessment.md` | 33,874 | Planning the next milestone; knowing what is missing before M9 | — |
| `AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` | — | Product Owner feature-level review and acceptance decisions for the hackathon MVP | — |

---

## `security/` — enforcement evidence

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_M2_Security_Implementation_Report.md` | 6,390 | Any auth/RBAC/tenancy change; any security claim in a report | — |

---

## `decisions/` — what was decided and why

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Owner_Decisions_Q1_Q6_V1.0.md` | 9,599 | You need the authority behind the platform-administration boundary, denial auditing, the notification-worker acceptance, the limitations-report correction, the CI pipeline, or the handling of owner-controlled documents | — |

---

## `implementation/` — what was built and tested

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_SEQ_02_COMPLETION_REPORT.md` | 21,344 | Touching patient queue visibility (DQDS) | — |
| `AMSDP_SEQ_03_COMPLETION_REPORT.md` | 30,485 | Touching missed-turn recovery, scheduling or the notification outbox | — |
| `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` | 15,329 | Judging whether SEQ-03 claims hold up | — |
| `AMSDP_M4_Appointment_Implementation_Report.md` | 6,169 | Appointment features | — |
| `AMSDP_M5_Queue_Implementation_Report.md` | 5,570 | Queue management features | — |
| `AMSDP_M6_Implementation_Plan.md` | 6,785 | Planning work that builds on M6 | — |
| `AMSDP_M6_Implementation_Report.md` | 6,753 | M6 audit/observability behaviour | — |
| `AMSDP_UI_UX_and_Reusable_Components_Assessment.md` | 6,305 | Frontend work; what shared components exist and what is missing | — |
| `AMSDP_Frontend_Visual_Quality_Investigation.md` | 3,442 | Frontend visual regressions or styling standards | — |
| `AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` | 26,974 | Patient-name entry, the BanglaNameSense dataset/matcher/component, or any reuse in doctor/staff forms | — |
| `AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` | 14,732 | Starting/restarting/stopping the local stack, `_tools/amsdp_stack.sh`, startup failures | — |
| `AMSDP_Owner_Decisions_Implementation_Report_V1.0.md` | 22,388 | The platform-administration capability boundary, denial auditing, the CI pipeline, or how Q-1…Q-6 were verified (and what was not) | — |
| `AMSDP_CI_First_Run_Failure_Investigation_V1.0.md` | 25,424 | Diagnosing why the CI pipeline fails, `alembic`/`python -m` invocation questions, or the frontend test failures in `banglanamesense-integration.test.mjs` | — |
| `AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` | 67,732 | Appointment booking UI, the week/day calendar grid and card anatomy, `lib/calendar/grid.js` + `lib/calendar/list.js`, `chipLayout()` overflow, slot capacity, the `date_from`/`date_to` window on `GET /api/v1/appointments`, the paged `GET /api/v1/appointments/list` (search/sort/paging/scope, §11.4) and how the component's markup is asserted without a browser (§7.4, §11.5); **§12** — the toolbar's search/status/branch now reach Week and Day through one shared filter builder, the counts-only `GET /api/v1/appointments/matches` date index, the "matched elsewhere" banner, hit highlighting, and the 167/108 + 24-step browser evidence | — |
| `AMSDP_Facility_Doctor_Frontend_Implementation_Report_V1.0.md` | 20,296 | Doctor Management (`/doctors`), chamber assignment (`/schedules`), the facility tree (`/facilities`), `lib/phone.js`, `lib/facility.js`, BMDC verification UI, why a conflicting session is warned about client-side but still decided by the server, and what the post-rebuild runtime probes do and do not prove (§5.4) | — |
| `AMSDP_Frontend_Usability_Shared_Design_System_and_Demo_Readiness_V1.0.md` | 45,536 | **Before touching a dialog, a form field, the shared UI primitives, `/doctors`, `/facilities`, the appointment calendar, or the demo dataset** — the focus-loss root cause (`useEffect(… el.focus() …, [onClose])`) and why the Radix rewrite removes it, the token/Tailwind layer and the 14 primitives, the legacy `.flex` alias that shadowed Tailwind and the two layout defects it caused (§6), what was redesigned where, the calendar polish that keeps its SSR contract green, the hydrated-session fix and the page-level hydration remainder (**O-1**), the reset+reseed of the developer database with its audit-preserving `--reset` (54 husk organisations, **O-4**), and the full evidence set: 96/96 frontend, 216 backend, build exit 0, 6/6 demo logins, and the headless-Chrome run that typed three chunks into a real dialog while asserting the caret stayed — **12/12 checks**. §9.7 explains what the shipped focus test does and does not prove | — |
| `AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` | 67,128 | **Before touching the booking form's symptom control, the symptom catalogue, the onset question, or any appointment payload** — why the catalogue is one API response searched in memory (and why server-side search would fork the Bengali normaliser), the `symptom_catalog` / `appointment_symptoms` model with its booking-time name snapshot and two partial unique indexes, the closed onset vocabulary versus a forced date, the four optional booking fields and the three response keys, the copy-forward rule for reschedule/transfer, the ranking order (`rank → speciality tie-break → sort_order → code`) and why age/sex are never used, the 79-entry curated catalogue and its `curated` (not clinically validated) review status, the authorization matrix, the exact test/build results including the **9 pre-existing doctor-module failures**, the explicit statement that **no browser run was performed** in the morning (§12, superseded by §18), and open items O-1…O-10; **§18 is the Phase-1 runtime record** — rebuilt `appointment`/`frontend` images, only those two containers recreated, the six booking cases with their HTTP/DB/audit evidence, the Bangla/English search matrix executed against the live 79 entries, and the real-Chrome keyboard/focus run (34/35 checks, 7/7 on the detail read path), plus the O-1/O-3 closures and new items O-11…O-15 | — |
| `AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md` | 28,589 | **Before changing an appointment/scheduling write path, a slot or capacity rule, or the booking dialog's messages** — what each of F-01…F-19 was fixed by (with the function and test that prove it), the two partial closures (F-01's database constraint, F-18's *unscheduled* marking) — **§10** records how the owner decisions Q1–Q5 then closed both, with a pointer to the Q1–Q5 report — and the original evidence: 12 pre-existing failures accounted for, 269/269 on the affected backend subset, 179/179 frontend, `next build` compiled | — |
| `AMSDP_Owner_Decisions_Q1_Q5_Appointment_Reliability_Implementation_Report_V1.0.md` | 25,642 | **Before changing appointment types, walk-ins, `slot_allocations`, `appointment.check_in`, `appointment.create_unscheduled`, staff capability grants or cross-branch booking** — what Q1–Q5 actually produced (code, endpoint, migration `a9c4e1f7b2d8`, test), the evidence standard reached for each claim, the backfill caveat for pre-existing slot overruns, and the open owner items O-1…O-7 (Business Rules vocabulary, no formal decision record, grants being API-only, no historic repair) | — |
| `AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md` | 28,119 | **Before changing queue announcements, `lib/announcements/`, the `/queue` announcement panel, or the OD-3 wording** — the Web Speech API adapter and its "silence is not success" rule, the voice-selection rules that never substitute a language, the token-serial pronunciation rule and the PII boundary, the duplicate/overlap policy, the room clause no queue payload can supply (**O-1**), the absent facility configuration (**O-2**), the absent server-side event/audit (**O-3**), and the fact that **no browser or device playback run was performed** — nothing is VERIFIED | — |
| `implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` | 16,877 | Complete audio generation catalogue for QUE-006: 28 recording assets (8 fixed phrases + 20 digit recordings across English and Bangla), number coverage and composition rules, recording instructions, proposed folder structure, manifest schema, demo workflow. Doctor names and honourifics excluded. | — |
| `implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` | 11,595 | Doctor-name removal from QUE-006 announcements: the four approved sentences (English and Bangla, with and without room), code changes, test results (48/48 pass), catalogue creation, remaining limitations (local prerecorded audio not implemented, no browser verification). | — |
| `implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md` | 42,439 | **Before running, trusting or extending `scripts/que-006-audio/`** — the standalone audio utility that generates, validates and manifests the 28 catalogue clips through **either Gemini or ElevenLabs** (`--provider`, default gemini): module map, both API contracts as implemented, the command runs actually executed with observed exit codes, honest asset state (**1/28 on disk**, 27 blocked because the stored `GEMINI_API_KEY` is an `sk-` key, not a Google AI Studio key — `API_KEY_INVALID`, 35 characters instead of 39; the ElevenLabs path has now been exercised against the live API with a real but unscoped key — see §13), container-plus-codec validation (ffprobe 9.1 + ffmpeg 9.1 installed and now used on every clip, with negative controls recorded), the ElevenLabs facts that shaped the code (`wav_24000` default because 44.1 kHz PCM/WAV is Pro-tier; `pcm_*` refused rather than assumed 16-bit; `language_code` unsupported on multilingual_v2; request logging on by default; **no claim that Bangla works**), the declared `en.phrase.no-room` comma override awaiting an owner decision, the absent playback engine, and the human listening review (Bangla in particular) that no script can replace. Nothing in it is VERIFIED or ACCEPTED. | — |
| `implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md` | 27,204 | **Before listening to, extending or trusting `scripts/que-006-audio/preview/`** — the isolated human-review preparation tooling for QUE-006: 20 composed WAV samples built as byte-for-byte concatenations of the 28 delivered clips (no ffmpeg, no re-encode, no trimming; 120/120 copied PCM ranges identical, 20/20 decode-verified, 20/20 captions equal to the product's own `buildAnnouncement()`), the loopback-only static server and its 16 probed route/refusal responses including four traversal attempts and a NUL byte, the reviewer page (no wording hard-coded — it imports `frontend/lib/announcements/content.js`), the CSV/Markdown review record with its 23 columns and blank verdict fields, and the headless-Chrome harness (`check-page.mjs`, 12 checks over the DevTools protocol, no new dependency) that passed **12/12, exit 0**. Also records what the measurement found: **Bangla clips end with 0.874–1.388 s of near-silence each (mean 1.260 s, all 14)** versus 0.014–0.331 s for English, `en.phrase.room-suffix` is punctuation-only and correctly silent, and the room-number range is still an unapproved recommendation. Nothing approved, nothing accepted, all 28 assets still `humanReviewStatus: pending`. | — |
| `implementation/QUE-006_VOICE_ANNOUNCEMENT_FUTURE_REFACTORING_AND_IMPLEMENTATION_ROADMAP.md` | 92,002 | **Before planning, estimating or authorising any further QUE-006 work** — the planning layer over the five QUE-006 evidence documents: the Product Owner's **approved-DRAFT** decision and what it does and does not mean; the current architecture (speech-synthesis path, seams, and the four things it cannot do — no `call` trigger, no room, no facility configuration, no completion signal); the audio catalogue's real state (72 files on disk, 56 manifest references, **15 unreferenced**, 0 human-approved); a **35-row status table** where every feature carries exactly one of the seven permitted statuses and an evidence anchor; the future **voice-refactoring plan** (recording, timing, engine, catalogue/versioning, the sanctioned generation workflow with `GEMINI_API_KEY` never leaving the environment, risks and phases P0–P4); the **six remaining workstreams** with acceptance criteria (playback engine, facility configuration + permission enforcement, non-blocking queue integration, remote local-agent installation, asset cleanup, operational verification); the corrected **implementation sequence** and its four evidence-based amendments (split the engine from its wiring; insert the missing queue `call` UI; pull a browser smoke test forward; clean up only after remote installation exists); a **21-row verification matrix**; risks and rollback; and **twelve open Product Owner decisions (POD-1…POD-12)**. Records the findings that decide the plan — no facility announcement config exists, `branch_admin` cannot reach the `org.manage`-gated config precedent, `QueueEntry` carries no room, the speech adapter reports `start` not completion, and the approved remote-installation architecture has **zero artefacts** — plus the test evidence gathered (**53 announcement tests: 52 pass, 1 skipped, 0 fail**) and the recommended next task, which is not started. | — |
| `implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` | 58,904 | **Before converting, re-encoding, trimming or serving any `frontend/public/audio/` file** — the format-standardisation pass that turns the catalogue clips into a 44.1 kHz/16-bit/mono PCM WAV master plus a 44.1 kHz/mono/128 kbps CBR MP3 playback file, with every original preserved byte-for-byte in `frontend/.audio-originals-backup/` (`ORIGINALS.json` holds sizes, SHA-256 and format facts). Records the as-found inventory (28 files: 13 English MP3, 13 Bangla M4A, 2 silence placeholders), the two contradictions found outright — `bn/phrase/room-suffix.wav` is **byte-identical to the English placeholder**, so `bn.phrase.room-locative` (`-এ আসুন।`) has **no recording anywhere**, and ffmpeg/ffprobe 9.1 are **not on `PATH`** — the conversion settings, the twelve-check validator (`validate-audio-assets.mjs`, modes `all`/`missing`/`checksums`), the v2 manifest schema and its 54 verified checksums, the eight defects found by running the tool (in-place ffmpeg refusal, dry-run false failure, backup record absorbing its own outputs, lost `playbackDerivation`, over-strict path check, `validate.mjs` 24 kHz assumptions, a PowerShell cp1252 round-trip that corrupted a source file), and the English room-suffix assessment (300 ms of −91 dB silence, retained as an intentional pause). **V1.1 (2026-11-21): the missing Bangla recording `bn/phrase/room-locative.mpeg` was supplied by the owner and converted — that asset now passes in both formats, so the set is 28/28 complete (strict validator exit 0, 56 checksums, 29 preserved originals); §17 records the source's real container (an MP3 stream, 48 kHz, despite the `.mpeg` name), the conversion settings, the blast-radius hash diff, and why the English silence placeholder was still not renamed into the slot.** Every `humanReviewStatus` is `pending`; nothing is pronunciation-approved, and prerecorded-audio playback in the frontend remains **unimplemented** (`speech-synthesis.js` untouched). | — |
| `implementation/QUE-006_MASTER_IMPLEMENTATION_PLAN.md` | 19,523 | **Before implementing any QUE-006 workstream** — the programme plan over the roadmap: the inspected baseline (HEAD `37cf3d1`, announcement modules and line counts, the 72-file audio tree, the 28-asset manifest, the queue `call` gap), the **decision register** (DR-1…DR-10 approved, POD-1…POD-12 open, TF-1…TF-7 technical findings), the configurable **voice-library architecture** (pack descriptor, `voice_packs` table contract, precedence, API surface, permission mapping onto the existing `org.manage`/`platform.admin` capabilities — POD-5 closed here in favour of organisation scope because `branch_admin` holds neither capability), the seven workstreams with files/dependencies/exit gates, the ordering consequence (W1 → W3 → W2) and the phase-gate protocol. | — |
| `implementation/QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_REPORT.md` | 9,247 | **Before changing the playback engine or its wording contract** — W1: `segments.js` (pack-driven asset resolution, refusals) and `prerecorded-audio.js` (sequential clips, completion only from the final `ended`, no fetch, no speech fallback), with roadmap §8.1 **AC-1…AC-8** preserved verbatim and each mapped to the test that proves it (AC-1 over an **80-combination** matrix comparing the resolved clips with `buildAnnouncement()`). Records the design decisions (pack boundary, the silent clip as a 300 ms gap, refusal before sound), the two normalisation notes (clip-boundary whitespace; English digit words vs Bangla glyphs) and what is **not** verified: no browser, no real decode, offline proven only as "no fetch issued". | — |
| `implementation/QUE-006_W2_QUEUE_INTEGRATION_REPORT.md` | 9,049 | **Before wiring announcements into the queue page** — W2: the controller gains a `player` and an explicit `strategy` (prerecorded by default; `strategy: 'prerecorded'` without a player throws rather than downgrading), `playPrerecorded()` maps `completed` → `spoken` and everything else to a failure with its reason, `activate()` unlocks by playing the catalogue's own silence, and `queue-transitions.js` announces a `waiting → called` change exactly once through a fire-and-forget seam (15 tests). States plainly that the automatic trigger is **unreachable in the UI** until a `call` control exists (QOP-001 / POD-12), and that automatic announcements need an operator gesture to unlock audio. | — |
| `implementation/QUE-006_W3_VOICE_CONFIGURATION_REPORT.md` | 7,415 | **Before implementing voice-pack storage, upload, approval or the configuration API** — W3's verified half (`voice-packs.js`: precedence organisation → platform → built-in → none, organisation isolation, only `published` selectable, five refusal codes) and its **unimplemented** half with the reason (no `pytest`/`fastapi`/`sqlalchemy` on the host, so no migration and no denied-API test could run). Carries the ready-to-implement contract: `voice_packs` columns, `organizations.config["announcement"]` (no migration needed), the nine routes, the `org.manage`/`platform.admin` mapping and the audit requirement. Do not read it as a delivered feature. | — |
| `implementation/QUE-006_W4_ROOM_SUPPORT_REPORT.md` | 4,875 | **Before adding any room column, payload field or migration** — W4 is **BLOCKED by POD-2**, and this report is why it stayed blocked: `queue_entries` has no room, but `appointments.room_name` is snapshotted at booking, `doctor_branches.room_id` is the doctor's chamber and `schedule_sessions.room_id` assigns one per session — the open question is *which source is authoritative*, not whether data exists. Names the three candidates and their consequences, the two decisions that gate the work (POD-1, POD-2) and the exact change set once decided. No schema change was made. | — |
| `implementation/QUE-006_W5_REMOTE_INSTALLATION_REPORT.md` | 7,162 | **Before running, deploying or trusting `scripts/que-006-agent/`** — W5: the facility agent (outbound-only, no listener) with SHA-256 verification of the received bytes, path-traversal refusal, staging plus rename-based atomic swap, previous-version retention, rollback, crash recovery and offline `activeRoot()`; 10 tests against a real HTTP stub server and a temporary install root. Records the security properties actually enforced, the token handling (environment only, never printed), and the gaps: **no server-side distribution API**, no server-side entitlement check (so organisation isolation is unimplemented), no facility PC, no service wrapper, no compatibility refusal. | — |
| `implementation/QUE-006_W6_ASSET_DEPENDENCY_REPORT.md` | 5,406 | **Before deleting, moving or renaming anything under `frontend/public/audio/`** — the dependency report the assignment asks for when rollback is not established: the recount (71 non-manifest files, 56 referenced, **15 unreferenced**, 493,073 bytes; 28 assets, all `humanReviewStatus: pending`), the classification of every class of file (playback, WAV master, retained original, mislabelled placeholder, backup), the minimum asset set per announcement variant, and why nothing was removed (POD-7 open; the unreferenced files are provenance and one is defect evidence). Ends with the safe-cleanup procedure for the owner's decision. | — |
| `implementation/QUE-006_FINAL_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | 19,257 | **Before claiming QUE-006 is complete, or planning what comes next** — the consolidated W7 assessment: what changed and what deliberately did not, DR-1…DR-8 mapped to where each is implemented, the final architecture, the seven-workstream status table, integrated evidence (**108 tests: 107 pass, 0 fail, 1 skipped**), the announcement-behaviour matrix, a table of claims **not** made (no browser, no device, no disconnected network, no pronunciation), ten known limitations, the open decisions (POD-1/2/3/4/7/8/9/12, O-2, O-3), files added/modified, rollback instructions, and the explicit finding that **QUE-006 is not implementation complete** — technical completion separated from Product Owner acceptance. | — |
| `implementation/QUE-006_W1_PRERECORDED_PLAYBACK_ENGINE_IMPLEMENTATION_REPORT.md` | 19,448 | **Before changing the playback engine, or before quoting W1 as done** — the recovery and re-verification record: the provenance after the power loss (the earlier `..._REPORT.md` was intact; only the requested filename was missing), the pack-driven resolver and sequential player cited by file:line, AC-1…AC-8 each classified, the exact commands and counts (**22/22** own tests, 53/52/1 pre-existing, 98/97/1 across all eight suites, 270/266/2 for the whole tree with two pre-existing unrelated failures), the asset check (28 assets, 0 missing on disk), and the honest boundary — no browser, no device, no real decode, offline proven only as "no fetch issued", AC-1 proves agreement with the wording contract rather than with the recorded clips, and the English no-room draft carries no comma. | — |
| `implementation/QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md` | 19,623 | **Before wiring or claiming an automatic queue-call announcement** — the four-link trigger chain with the missing link named: the server `call` exists and is audited (`queue.manage`), **no UI control issues it** (POD-12), the client observes the `waiting → called` transition and announces fire-and-forget, and audio needs an operator gesture. Also records what the earlier report did not: the queue page has **no polling**, an entry that arrives already `called` is never announced, dedupe is per browser tab (two terminals both speak), event identity is `entry:<id>:call:0`, **no announcement audit record exists** (POD-4), and the JSX edits are not compiler-verified because `frontend/node_modules` is absent. | — |
| `implementation/QUE-006_POD-12_QUEUE_CALL_CONTROL_IMPLEMENTATION_REPORT.md` | 30,225 | **Before touching the queue Call control, or before quoting POD-12 as verified** — the control that finally issues the server `call` (gap QOP-001): `lib/queue/queue-call.js` (`isCallable`, ref-held synchronous `createCallGate`, `performCall` payload), the page wiring, the announcement still driven by the existing `waiting → called` tracker, and the role table for both matrices. States plainly what is **not** proven: doctor workflow blocked by the permission matrix (**DEV-1** — no doctor holds `queue.manage` and it is not delegable), backend tests written but unexecuted (no `pytest`/PostgreSQL/Docker), **no browser verification**, and the JSX compile checks skipping because of a Windows ESM-path defect rather than a missing SWC binary (**DEV-3**). Build: `npm run build` exit 0. W2 remains PARTIALLY IMPLEMENTED. | — |
| `implementation/QUE-006_W3_VOICE_CONFIGURATION_IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | 60,991 | **Before changing `voice_pack_policy.py`, `voice_packs.py`, `announcement_config.py`, the voice-pack tables, or before quoting W3 as delivered** — the W3 build that follows `QUE-006_W3_VOICE_CONFIGURATION_REPORT.md`: the stdlib-only decision layer (role gate, scope resolution, selectability, precedence, lifecycle, versioning/rollback, metadata checks, upload validation, W1-compatible descriptors), the versioned pack registry and its authenticated API (upload, validate/submit/approve/reject/publish/retire/availability, manifest, preview, asset streaming), platform defaults in their own table plus organisation override on the existing `organizations.config["announcement"]` JSON, and the forward-only migration. Permission claims are enforced three times over server-side (capability matrix, role allow-list, token-derived scope with non-disclosing 404), self-approval is structurally impossible, and nothing is written until 14 ordered upload checks pass. Evidence: **49/49 policy tests executed**, 146/145/1 pre-existing frontend suite, `py_compile` on 9 files, migration-graph check; the **18 API tests, the migration and any browser run are NOT executed** (no `fastapi`/`pytest`/`sqlalchemy`/`alembic`/PostgreSQL on the host), W2's migration declares the wrong parent (double head, fix unapplied), the docs index registration is owed, and the configuration is **not yet wired to the terminals** — it is real but not audible. | — |
| `implementation/QUE-006_W2_RELIABILITY_COMPLETION_REPORT.md` | 25,558 | **Before quoting W2 as reliable, cross-terminal-safe or audited, and before running the W2 backend tests** — the reliability pass on `QUE-006_W2_QUEUE_ANNOUNCEMENT_INTEGRATION_IMPLEMENTATION_REPORT.md`'s five open defects: server-owned event identity `qce:<entry_id>:<index>` derived from append-only `status_history`, `queue_announcement_deliveries` with `UNIQUE(call_event_id)` + `ON CONFLICT DO NOTHING` claim, the two endpoints (`/queue/{id}/announcement`, `/queue/announcements/{id}/outcome`) with 404/409/422 semantics, three separated facts (`queue.call`, `requested`, `completed`), the claim→play→report announcer, the muted cross-terminal panel note, and the 20 s visible-tab refresher with its trade-offs. Evidence: **146 queue tests (145 pass, 1 pre-existing skip)**, **318 whole-tree (314 pass, 2 pre-existing unrelated failures)**, `npm run build` exit 0, identity suite **13/13** run without pytest. States plainly that the backend endpoints and migration were **not executed** (no `fastapi`/`pytest`/`sqlalchemy`/`psycopg2`/PostgreSQL), no browser and no two-terminal observation, so **W2 stays PARTIALLY IMPLEMENTED**. | — |







---

## `audit/` — acceptance and readiness evidence

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` | 77,897 | Needing the consolidated implementation-evidence picture across all sequences | — |
| `AMSDP_M7_Hackathon_Readiness_Report.md` | 21,912 | Any demo-readiness or release-gate claim | — |
| `AMSDP_MVP_Hackathon_Readiness_Assessment.md` | 8,695 | Judging overall MVP completeness | — |
| `AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` | 23,408 | Verifying acceptance criteria and what "accepted" means here | — |
| `AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md` | 12,768 | Scoping a release-readiness review; what the system contained at Stage 0 | — |
| `AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md` | 8,706 | The detailed Stage 1 readiness findings that follow the Stage 0 inventory | — |
| `AMSDP_PreCommit_Push_Readiness_Report_V1.0.md` | 47,940 | Before staging, committing or pushing anything: change classification by owner, exclusion lists, commit grouping, GO/NO-GO | — |
| `AMSDP_PreCommit_Remediation_Report_V1.0.md` | 27,298 | Remediating blockers B-1…B-7: how each credential is supplied now, the ignore rules, the image rename, the new findings B-8…B-10 and the owner decisions still open | — |
| `AMSDP_Final_PrePush_Readiness_Report_V1.0.md` | 40,986 | Immediately before the first push: rotation evidence (D-1, closed), the two mixed-ownership files (D-2), the tracked AI-Factory artefacts (D-3), the twelve image assets, the six-commit plan and gates G-1…G-5 | — |
| `AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` | 95,368 | The last check before executing any commit: fresh verification of every earlier claim, the credential-scan result, the corrected owner-document set (five, not one), the published demo password finding (B-12), and the re-issued path-level plan C-1…C-7 with gates G-1…G-8 | — |
| `AMSDP_Tree_Commit_and_Push_Execution_Record_V1.0.md` | 19,186 | After the first push: the seven executed commits with hashes and per-commit counts, how each gate was checked, the defects found in the verification tooling, the §18.8.10 assertions, post-push verification and the R-1…R-7 register | — |
| `AMSDP_Project_Context_Report_V1.0.md` | 60,177 | **Briefing an external collaborator, or needing an evidence-graded picture of what the tree actually contains** — per-capability status with `path:line` citations, the architecture reality check AR-1…AR-6, the defect register F-1/F-2, the risk register P1-1…P3-4, the document-vs-tree conflicts C-1…C-6, a ranked reading list, and the re-verification protocol. Read this before quoting any readiness claim | — |
| `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md` | 82,914 | **History only — superseded by the V1.1 proposal below.** V1.0's §3 misdescribes D-01/D-02/D-03 and is not to be used for the decision records; read it only to see what changed between versions | — |
| `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.1_DRAFT.md` | 115,496 | **Before applying any Business Rules V1.1 / MVP Scope V1.1 / Master Feature List V2.5 / PQV / `.clinerules` / decision-register correction** — the corrected D-01…D-03 records (two permitted payment answers; `.clinerules` §1/§10 authority references; authorisation to prepare this material), the restated decisions R-1…R-4, the evidence-checked capability status table, the C-01…C-09 matrix with exact replacement wording, the six verified patches and the combined patch in Appendix A, the near-misses checked and left alone, and the open items U-1…U-7 (U-1/U-2 closed). Proposal only: nothing in it is applied and no capability in it is implemented | — |
| `AMSDP_Current_State_Demo_Diagnosis_and_Feature_Audit_V1.0.md` | 60,907 | **Before any attempt to "fix the demo" or to claim the demo is ready** — why the demo fails and staff cannot sign in (D1 frontend container absent since the stack-wide stop of 2026-11-12 and skipped in the 2026-11-14 nine-of-ten restart; D2 host-level container↔container forwarding dropped after the 2026-11-14 Docker daemon restarts with `ufw` active; D3 the isolated `amsdp_demo` stack never created, queue empty and appointments stale-dated; D4 the `/orgs` SSR `sessionStorage` crash), the evidence that the demo credentials are **correct** and **demonstrably worked** (6/6 bcrypt verifications; authenticated `super_admin` audit events at 2026-11-12T20:46:41Z), the 64-route / 14-page / 311-test matrix graded IMPLEMENTED / TESTED / VERIFIED, the prioritised repair plan R-1…R-10 with exact verification gates, the evidence appendix (26 rows), the actions deliberately not performed, the open items O-A…O-I, and **Part G** — reconciliation with the owner's account, the four corrections to Parts A–C, and the container-level timeline. Read-only: nothing was fixed | — |
| `AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md` | 50,236 | **Before wiring or "fixing" the appointment calendar's search box or its Status/Branch filters** — why they do nothing in Week and Day view: the toolbar writes only the paged list's query state while the grid is rendered from a separate `GET /api/v1/appointments` request built from the window and doctor alone (measured: 0 requests after typing a name, chips unchanged at 40, while switching to List issues the correct `?q=…&status=…&branch_id=…`); the grid endpoint has no `q`/`branch_id` and the page never sends the `status` it does support; grid 47 rows (org) vs list 42 (branch) for one receptionist; the list silently clamps to the visible week; no highlighting; unknown status → `200`/0 rows; no names in the grid payload (30 lookups per week); the source-contract test that **asserts** the defective request shape and the therefore-green 146/146 suite; Bangla-name search unverified (no such data). Includes the per-filter and per-view evidence matrices, four root-cause classes, minimal correction options with blast radius, and the two decisions left to the owner — **O-AA** (calendar branch scope) and **O-AB** (may a search leave the visible week). **Part I (2026-11-16)** records the resolution: both decisions taken, every finding F-1…F-9 mapped to the correction that shipped and to its evidence, and the one sentence defect the browser run of the fix caught | — |
| `AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` | 41,767 | MVP scope lock (25 KEEP / 1 DEFER) and Operational RBAC authorization hardening; six P0 defects fixed and regression-tested | — |
| `AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md` | 113,662 | **Before planning appointment/calendar capacity, slot, booking or scheduling-configuration work** — the 19 `CODE-READ` findings (WP-2.1…WP-2.7) with `file:line` evidence, the four-stage roadmap and decisions Q1–Q5; its remediation is `implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`, and **Appendix D** records the closure status of all 19 findings after the Q1–Q5 work order | — |

---

## `deployment/` — delivery and hardening

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_M8_Cloud_Deployment_Architecture.md` | 29,056 | Any Docker/compose/port/environment change | — |
| `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | 43,270 | Infra hardening, restart policy, health checks, container limits | — |
| `AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` | 16,196 | **Before restarting, reseeding, rebooting or re-diagnosing the local stack** — why two containers could not reach each other across the Docker bridge and the network-recreate fix (no `sudo`, no `ufw` change); the two auto-restart layers (`restart: unless-stopped` ×10 and the systemd user unit `amsdp-autostart.service`) and how they supersede the earlier deferral; the `/orgs` SSR fix; the new `_tools/` scripts (`amsdp_autostart.sh`, `install_autostart.sh`, `verify_demo_login.sh`); the live evidence (10/10 healthy, **6/6 demo logins**, 10/10 pages 200, `restarts=7`, data counts identical); and the open items **O-J**/**O-K**/**O-L**, plus carried **O-H**/**O-I** and new **O-M** | — |
| `AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md` | 14,427 | **After any code change, before claiming a change is live** — why code is baked into the images and `docker compose restart` therefore redeploys nothing; the minimum action per changed path (`backend/common/` ⇒ all eight backends); `_tools/amsdp_rebuild.sh` (`--check` / `--verify` / `--all`, rebuilds only what changed, waits for `/health/ready`); the full-platform commands via `_tools/amsdp_stack.sh` and in raw compose; what a restart never does (no migrations, no re-seed, no `.env` change); the L0–L5 verification ladder; a symptom→fix table; open items **O-W** (untracked `_tools/`) and **O-X** (readiness ≠ behaviour) | — |

---

## `demo/` — demonstration assets

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Demo_Credentials_V1.0.md` | 3,106 | Running or describing a demo login. Contains credentials — cite the file, never paste secrets into reports or logs | R |
| `AMSDP_Hackathon_Demo_Runbook.md` | 11,794 | Walking through the demo flow end to end | — |
| `AMSDP_Limitations_Report_V1.0.md` | 5,119 | Stating honestly what does not work — the canonical source for limitation claims | R |
| `AMSDP_API_Integration_Report_V1.0.md` | 4,807 | Frontend↔backend integration status | — |

---

## `governance/` — the rules that bind the agent

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Docs_Index_V1.0.md` (this file) | — | **Start of every task** | — |
| `AMSDP_Engineering_Governance_Assessment.md` | 25,642 | Understanding how CarbonTally agent-rules were adapted; any rule change | — |
| `AMSDP_Skill_Routing_Architecture.md` | 5,868 | Skill selection, onboarding a new skill | — |
| `AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` | 24,959 | Establishing where a document came from, or the authority for its location | — |
| `AMSDP_Docs_Output_Policy_Verification_Report_V1.0.md` | 22,021 | Confirming that the output-location policy was actually installed and verified | — |
| `AMSDP_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md` | 35,361 | Confirming how owner decisions O-1…O-6 were implemented; the 36-reference register; relocation evidence | — |
| `AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md` | 33,007 | Confirming how the six `architecture/saas/` documents were reconciled against owner decisions `O-SaaS-1…16` and A1–A4 — what changed per document, the six conflicts and their dispositions, the residue scan, the evidence status (nothing `TESTED`/`VERIFIED`), **and §M: the post-commit record (`597d9b1`, pushed) plus the 2026-11-17 O-SaaS-15 / A3 / commit-status amendments**. **Registered 2026-11-17** (Revision 29; amended in Revision 30) | — |

---

## Repository-root legacy documents — relocated on 2026-11-10 (owner decision O-6)

The two tracked release-readiness documents that used to sit at the repository
root now live inside this tree, at `docs/audit/` (listed in the `audit/` table
above). They were moved byte-for-byte — SHA-256 identical before and after — and
the move is recorded in
`docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` §11.
No AMSDP document now lives outside `docs/`.

---

## AI Factory / AILI documentation — deliberately kept outside this tree (O-1)

`ai_factory/docs/` is **not** part of the AMSDP document set above and is not
indexed file-by-file here. Two things live there, both intentionally:

| Contents | Why it stays | Rule |
|---|---|---|
| `agent-rules/` (12 files incl. `MANIFEST.json`) | Path-bound by `ai_factory/src/amsdp_ai_factory/workflows/engine.py` and `ai_factory/tests/unit/test_agent_rules.py`; relocating it breaks both | Never move (§1.4, §11) |
| 11 `AILI_*.md` reports + AI-Factory reference docs (`architecture.md`, `operations.md`, `permissions.md`, `workflows.md`) | They document the AI Factory / AILI subsystem, not AMSDP product deliverables | Owner decision **O-1** (2026-11-10): keep in place — do not move, rename or rewrite |

For an AILI or AI Factory task, read those files directly under
`ai_factory/docs/`; do not expect them here. New AMSDP reports are still never
written there (§11).

---

## `chatgpt/` — four ChatGPT-produced planning documents, all registered and adopted on 2026-11-17

`find docs -type f -name '*.md'` reports **four** documents in a folder that is **not** among the
§11 subject folders. On **2026-11-17** the Product Owner instructed that the two planning documents
below that were still unregistered — the multi-sector plan and the AMSDP Connect proposal — be
**added to the repository** as ChatGPT-produced reference material; they were committed and are
registered here in the same task (§12). All four files now have a row. None is moved: the
instruction was to adopt the documents, not to relocate them, so `docs/chatgpt/` stays exactly
where it is and no migration entry applies (§11). None of them is an authority — business rules,
MVP scope and the frozen design still govern (§1) — and none authorises work: the Connect document
states of its own capabilities that they are *not approved for implementation*, and the
multi-sector plan is a post-hackathon roadmap.

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Hackathon_Implementation_Backlog.md` | 24,229 | Needing the backlog framing that accompanied the 2026-11-14 reconciliation commit — a planning document, **not** an authority: business rules, MVP scope and the frozen design still govern (§1) | unconfirmed — folder outside the §11 set |
| `AMSDP_Project_Handover_2026-11-12.md` | 28,984 | Needing the 2026-11-12 handover narrative. **Unregistered** by earlier revisions on purpose; listed here only so the tree count is honest | unconfirmed — folder outside the §11 set |
| `AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md` | 40,267 | Reading the post-hackathon multi-sector plan (private / government / NGO / community / outreach delivery models, microservices direction, phased roadmap). **Registered 2026-11-17** when the owner adopted it into the repository — found by the Revision 21 maintenance check (2026-11-16). Planning only: it authorises no hackathon-scope change | Product Owner — adopted 2026-11-17 (ChatGPT-produced reference); not authoritative |
| `AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` | 20,944 | Reading the proposed communication / voice / AI capability set — hypotheses for customer discovery, explicitly **not** committed Core features (its own header: *"Not approved for implementation"*), and outside the hackathon MVP scope | Product Owner — adopted 2026-11-17 (ChatGPT-produced reference); not authoritative |

**O-D status.** The ownership half is **closed**: the Product Owner supplied and adopted these
documents on 2026-11-17, so their provenance is no longer unknown. Whether the folder should
eventually be folded into an existing subject folder (`audit/` or `governance/`) remains the Product
Owner's decision; until it is taken the folder stays exactly where it is, and no agent may treat
`docs/chatgpt/` as an approved output location (§11).

---

## Maintenance obligations

- **Same-task update.** Creating, moving, renaming or retiring a document
  obligates the agent to update this index **in the same task** (and to add a
  manifest entry in `AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` when a
  file moves). Never overwrite an existing row — append or correct it and say so.
- **Refresh command** (read-only; prints path, bytes and first heading for every
  document, to check that this index still matches the tree):

```bash
find docs -type f -name '*.md' | sort | while read -r f; do
  printf '%s\t%s\t%s\n' "$f" "$(wc -c < "$f")" \
    "$(grep -m1 -E '^#{1,3} [^#]' "$f" | cut -c1-90)"
done
```

- Compare the command's output against the tables above. Any file present in one
  and not the other is an index-drift defect to be fixed before the task ends.



---

## Trial-merge annex — unmerged Ubuntu index revisions (QUE-006 integration trial, 2026-11-22)

> **Status: PROPOSED, NOT APPLIED. No revision number has been assigned.**
> This annex exists because the two lineages numbered revisions independently and they
> **collide**: the Windows lineage (`2fc007a`, whose index is the base of this file)
> already occupies **Revisions 36–48**, which is exactly the range the Ubuntu lineage's
> two unmerged index edits used (**Revisions 36 and 37** of the pre-merge Ubuntu index).
> Assigning a revision number is the index owner's act (`.clinerules` §11/§12), so the
> entries are preserved below with their original numbers labelled *unmerged-local*, and
> the documents are recorded as **unregistered** in the numbering above until that
> decision is taken (open item **D-5**).

### Unmerged local Revision 36 (Ubuntu, 2026-11-20) — two registrations

| File | Bytes | What the unmerged revision recorded |
|---|---:|---|
| `architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md` | 146,910 | READ-ONLY design / plan of record; the HEAD it cites is `37cf3d1` with a clean tree. Its §3.1–§3.4 are the F1–F4 findings; §18 separates owner-approved statements from engineering recommendations |
| `implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md` | 29,118 | The F1–F4 corrections report: IMPLEMENTED and TESTED, **NOT VERIFIED**, **NOT ACCEPTED** |

The unmerged revision moved its own registered-snapshot count from 89 to **91
registered against 95 on disk**.

### Unmerged local Revision 37 (Ubuntu, 2026-11-22) — one registration

| File | Bytes | What the unmerged revision recorded |
|---|---:|---|
| `implementation/AMSDP_Windows_Commit_Seven_File_Compatibility_Assessment_V1.0.md` | 53,312 | Compatibility assessment of the Windows commit's seven changed announcement files against the Ubuntu F1–F4 work |

It recorded `find docs -name '*.md'` = **98** on the Ubuntu tree, **92**
registered, with **6** unregistered files enumerated. The unregistered Ubuntu-side
documents this trial can name are:

| File | Bytes | Note |
|---|---:|---|
| `implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` | 77,284 | Ubuntu-side agent report, 2026-11-22 |
| `implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md` | 49,745 | Ubuntu-side agent report, 2026-11-22 |
| `chatgpt/AMSDP_Project_Handover_2026-11-20.md` | 26,412 | ChatGPT handover, 2026-11-20 — authorship not provable from Git |
| `implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md` | — | This trial's report, written after this annex |
| `implementation/AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md` | — | Follow-up to the trial report: B-1 (W3 upload `TypeError`), B-9 (cross-tenant selection disclosure) and INT-3/INT-3b (automatic room announcement) fixed and regression-tested; re-verification of both suites, the build and the migration graph. Also written after this annex, so it is unregistered for the same D-5 reason |
| `implementation/AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md` | — | **D-4** (a configured room is announced, otherwise the approved room-less sentence) and **D-6** (`completed`/`interrupted` as the only playback vocabulary, pre-merge spellings removed rather than aliased) implemented and pinned by tests: six announcement suites `98/98`, room suite `14/14`, full frontend suite `355/355`, build `✓ Compiled successfully`. Records the repository-wide vocabulary sweep, the re-exported preservation artefacts (`13_`/`14_`/`15_`), and keeps **B-5**, **B-8**, **D-3**, **D-5**, **D-7** open. Written after this annex, so unregistered for the same D-5 reason — it does **not** claim a revision number |

**Open item — D-5 (index numbering).** The base index ends at Revision 48, but the
Windows lineage's own reports state that its index registration was still owed, so
the index owner must confirm 48 is the true head before any further revision number
is assigned. No number is claimed here; the documents above stay **unregistered**
until that confirmation.


### Trial merge acceptance-readiness verification (Ubuntu, 2026-11-23) — one registration

| File | Bytes | What the report records |
|---|---:|---|
| `implementation/AMSDP_QUE006_Acceptance_Readiness_Verification_Report_V1.0.md` | 20,896 | The acceptance-readiness verification of the trial merge (`41ac51a`, merge uncommitted) and the verdict **NOT READY**. Headline: the built `organization` container **could not start** on the unmodified head — `uvicorn main:app` makes `main.py` a top-level module, so the unguarded `from . import voice_pack_policy` in `voice_packs.py`/`announcement_config.py` raised *attempted relative import with no known parent package* and the whole organisation service (branches, facilities, the W3 voice-pack registry) never came up, while every unit test still passed because the harness imports it as a package; repaired with dual-layout import guards plus `test_container_layout_import.py`, proven by a **negative control** that fails on the pre-repair bytes. Also records: three PG 16.15 scenarios (fresh migrate; restored **live** dump with `DATA_PRESERVED=YES` and idempotent re-run; isolated `q6arv` stack, 8/8 services 200), suite results (**768 pass / 3 fail** — one of them the new test's own route-collection bug, hence a derived **769/2** — frontend 355/355, build exit 0), the live-verified permission matrix (queue `call` 401/403/403/200), non-disclosing cross-branch **404**, claim idempotency (`claimed:true` → `claimed:false duplicate_event`), two-terminal duplicate suppression corroborated by **exactly one delivery row per call event**, audio-unavailable degradation (`failed`, queue stays `called`), and the honest gaps: **no run produced a `completed` delivery** (the claiming terminal reported `interrupted`; a late-mounting terminal announced nothing), audibility unproven, and **INT-4** — `next.config.js` has no rewrite for `/api/v1/voice-packs` or `/api/v1/platform/**`, so both return Next's own 404 through the application origin. Decision items D-1/D-2 (doctor branch contract) are left red on purpose as pre-existing, tenant-safe questions. Teardown confirmed; live stack and live database untouched |

**Open item — D-5 still applies.** No revision number is claimed for this registration: the
index head remains unconfirmed (see the note above), so the report is registered here without
advancing the numbering.

### Final merge-readiness verification (Ubuntu, 2026-11-23) — one registration

| File | Bytes | What the report records |
|---|---:|---|
| `implementation/AMSDP_QUE006_Final_Merge_Readiness_Verification_Report_V1.0.md` | 36,307 | The close-out of the W2 merge-readiness review on an **isolated** stack (`q6fmr`, own volumes/network, all traffic through the application origin `:59030`). Headline: the merge blocker is **the announcement playback defect** — Chromium fires `pause` *before* `ended`, `playSegment()` read that pause as `FAILED/INTERRUPTED`, so the activation prime never reported `primed`, the queue page never left *audio off*, and no announcement could ever play; fixed by `playedToEnd()` in `prerecorded-audio.js` (+3 AC-2 regression tests, one encoding the browser's exact event order). Before/after in a real browser: badge `অডিও বন্ধ` → `অডিও চালু`, 1 clip → 4 clips each played to its full duration, claim `201 claimed:true`, outcome `completed`. Re-verifies live over the deployed origin: **INT-4** (superseding the earlier no-rewrite finding — `voice-packs` 200 JSON, `platform/**` 403 admin-only, negative control `text/html`), **B** (foreign branch `422`, 0 rows), **C** (retired assignment not serialised; row retained inactive), **D** (policy default off, doctor 403 off / 200 on, foreign entry 404, receptionist keeps the action, foreign-org PUT 404, audited `queue.call by doctor`). Suites: frontend **368/368**, targeted backend **187/187**, whole tree 790 pass/1 fail explained as a **harness** gap (`qrcode` missing; endpoint verified live — 200 `image/png`, no-cache headers, 328×328). Schema: one head `c4d8e2a91f60`, DB at head. Writes up **D-3**, **D-5**, **D-7**, **O-2** with status and closing condition, records **RBAC-R3** (demo `doctor` holds no assignment) and keeps **audibility NOT VERIFIED** (no audio device) — a bare claim is deliberately not made. The facility policy was restored to its default `off` after measurement; the isolated stack itself is still running and is disposable (`docker compose -p q6fmr -f /tmp/que006_fmr/compose.fmr.yml down -v`) |



### Final merge publication (Ubuntu, 2026-11-23) — two registrations

| File | Bytes | What it records |
|---|---:|---|
| `implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md` | 36,125 | The operating runbook for the post-handover split: Windows workstation for development, Ubuntu host for deployment. Roles; host inventory with a service→port map; Ubuntu operations (start/stop/status, rebuild, database maintenance including the **backup → `alembic current/heads/upgrade head` → rebuild** order, logs, recovery); Windows preparation (prerequisites, clone/branch, throwaway test database on port 55460, running both suites, looking at the deployed origin rather than a backend port, and the things a Windows machine must not do); the two exposures to decide about (no SSH listener, PostgreSQL published on `0.0.0.0:5433`); branch/merge/publication discipline; the gates that must be green; data and secrets; the handover checklist; the open items with their closing conditions; and an evidence appendix of what was actually executed. It deliberately does **not** duplicate the restart/redeploy runbook, the one-command restart report or the boot/demo-data document, and says so in §12.1 |
| `implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` | 19,005 | The merge and its publication. Published commit `ea9c2a0` on `hackathon-mvp`, fast-forward from `2fc007a`, verified by `git ls-remote` **and** by a local ref after a fresh fetch; the four commits the push delivered; what each lineage contributed (193 files vs the Ubuntu parent, 55 vs the Windows parent, 36 files touched by both) and how each collision was resolved; the pre-commit evidence (frontend 368/368, `next build` **compiled successfully**, targeted backend 262 passed, whole tree 682 passed / 109 errors / 0 failed with the 109 explained as fixture setup against a live database two revisions behind — the same two files pass 109/109 on a migrated one); schema single head `c4d8e2a91f60` with the live database still at `a9c4e1f7b2d8`; preservation (snapshot commit `5fc6a75` whose tree is byte-identical to the published tree, plus two `--binary` patches and their SHA-256 sums outside the repository); disclosure that the pre-merge Ubuntu snapshot `41ac51a` is now published; what was deliberately excluded (audio originals backup, `/tmp` logs, throwaway database); and the open items — live-database migration, **B-8**, **D-5**, **D-7**, **O-2**, **RBAC-R3**, the `0.0.0.0:5433` exposure, the missing SSH listener, and the unexecuted Windows steps |

**Open item — D-5 still applies.** Neither registration claims a revision number: the
index head is still unconfirmed (see the two notes above), so both documents are
registered here without advancing the numbering. The tree currently holds **125** `.md`
files under `docs/`; a full recount against the registered rows, and the numbering
reconciliation that depends on it, remain the owner's D-5 task. This annex registers
exactly the two files named above and makes no claim about the others.


### Implementation-state investigation (Windows checkout, 2026-11-23) — one registration

| File | Bytes | What it records |
|---|---:|---|
| `implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` | 23,831 | A **read-only** investigation of the stopping point, requested before any further work was authorised. Section A pins the repository state by command: branch `hackathon-mvp`, HEAD `a4ddc2c` (2026-11-23 20:21:43 +0600), upstream `origin/hackathon-mvp` **0/0**, remote tip identical per `git ls-remote`, working tree **clean (0 entries)**, **no** `MERGE_HEAD`, one local branch, no tags, no stashes, 64 commits; merge parentage `ea9c2a0` = `41ac51a` + `2fc007a`. Section B separates the last **implementation** task (D-4/D-6 closure) from the last task overall (merge publication + runbook correction). Section C ranks the five newest reports and flags that their state headers (`trial/…` branch, `41ac51a`, open `MERGE_HEAD`) are now stale. Section D gives the W1–W7 matrix: W1/W2/W7 complete, W3 API-only with **no admin UI**, W4 resolved by D-4 with the plan row still showing the blocker, W5 **partially** implemented (no server-side distribution API), W6 analysis only, and the **live database two revisions behind** as a reported, unverified runtime fact. Section E orders the remaining work (migration first). Section F names the next planned task — publication report §10 step 1, backup → `alembic upgrade head` → rebuild, then the whole-tree suite — and states it was **not started**. Section G lists the open owner decisions (D-3, D-5, D-7, O-2, POD-2 formally, POD-3/POD-5/POD-6, POD-7, POD-1/POD-8/POD-9/POD-10/POD-11, infrastructure). Section H recommends accepting the state and authorising only the migration. Eight conflicts are surfaced rather than resolved, including the stale report headers, inconsistent lineage labels, the `queue_calling_config.py` citation for announcement configuration, the stale POD-12/POD-2 plan rows, the W3 plan-versus-delivered scope gap, the differing test counts across reports, the `queue_announcement_deliveries` naming, and the absence of any facility announcement enable flag (the substance of O-2/POD-6). It records what was **not** executed and why (`pytest`, `alembic`, containers and live calls are unavailable from a Windows checkout that has no `backend/.venv`), and warns that every `docs/*.md` mtime is `2026-11-23 15:16:53`, so chronology must come from commit history |

**Open item — D-5 still applies.** This registration claims no revision number: the index
head is still unconfirmed, so the document is registered here without advancing the numbering.
With it the tree holds **126** `.md` files under `docs/` (measured with
`Get-ChildItem -Recurse -Filter '*.md'`), one more than the 125 recorded in the registration
above; the recount against the registered rows and the numbering reconciliation that depends
on it remain the owner's D-5 task. This annex registers exactly the one file named above and
makes no claim about the others.

### Requirements reconciliation and master plan (Windows checkout, 2026-11-24) — two registrations

| File | Bytes | What it records |
|---|---:|---|
| `audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | 71,649 | A **read-only** reconciliation of the nine requirement documents against the `hackathon-mvp` tree. Pins the repository state by command (branch `hackathon-mvp`, HEAD `a4ddc2c`, upstream 0/0, migration head `c4d8e2a91f60`, live database reported two revisions behind). Registers the nine sources with declared status and authority tiers T1–T4, and explains that V2.5's approval covers only the §C module catalogue. Records **seven unresolved conflicts C-1…C-7** — DQDS and SMS phase labels against MVP §16, the unratified symptoms feature, Phases 4–6 never written down, "approved" meaning two things, the unapproved analytics specification, and the unphased subscription rules. Gives a **66-key feature matrix F-01…F-66** (21 implemented-and-tested, 13 implemented, 11 partial, 1 API-only, 1 unverified, 17 not implemented, 1 unratified, 1 CI-never-green), a **business-rule compliance matrix for §3–§56 plus §27A** (25 compliant, 13 partial, 14 not compliant, 1 conflicted, 53 rule sections assessed), a **Blueprint-to-frontend screen matrix** (9 of 23 screens implemented, 9 partial, 5 absent), a **27-item gap register GAP-01…GAP-27** with severity S1–S4, hackathon readiness against MVP §12 (7 of 11 steps ready in code, 3 not, 1 partial), full product readiness (about 60 per cent), and an assessment of the seven plan-shaped artefacts that exist — concluding that **no comprehensive plan exists** and that the unpersisted T-1…T-12 roadmap was never executed. Retracts one earlier negative finding (denial auditing **does** exist). Ends with twelve owner decision requests PO-01…PO-12 and eight explicit evidence limitations |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.0.md` | 35,864 | The master implementation plan the audit found missing, marked **PROPOSED — awaiting Product Owner authorisation**. Nine work packages **WP-A…WP-I** and 34 dependency-ordered tasks **MP-01…MP-34**, each with current state, priority P0–P3, dependencies, deliverables, a failable acceptance criterion and an engineer-day estimate; the critical path (MP-01 runtime restoration and live-database migration first, then the whole-tree baseline, then the demo-blocking bundle MP-05/06/07, then end-to-end acceptance and two rehearsals) with a minimum demo path of about 5.75 engineer-days; eight milestones M-1…M-8; the **PO-01…PO-12 decision gates** with what each blocks; definition of ready, a nine-gate definition of done and the evidence vocabulary; seven sequencing rules; ten risks; deferred and rejected work with reasons; a GAP-to-task traceability table with a coverage check; and command recipes for MP-01, MP-02 and MP-03. It supersedes the unpersisted T-1…T-12 roadmap and records where each item went |

**Open item — D-5 still applies, and `plan/` is new.** Neither registration claims a revision
number: the index head is still unconfirmed, so both documents are registered here without
advancing the numbering. With them the tree holds **128** `.md` files under `docs/` (measured
with `Get-ChildItem -Recurse -Filter '*.md'`), two more than the 126 recorded in the registration
above; the recount against the registered rows and the numbering reconciliation that depends on
it remain the owner's D-5 task. Both documents record a **placement deviation**: `docs/plan/` was
created because the Product Owner's authorising instruction named a plan folder, and §11's
sanctioned subfolder list does not include it — the deviation is stated in plan §12 and flagged
for either ratification of the folder or migration of the file to `docs/implementation/` with a
manifest entry. No existing document was moved, renamed or overwritten by either registration.

### Multi-display DQDS scope change (Windows checkout, 2026-11-24) — three new documents, two amendments

| File | Bytes | What it records |
|---|---:|---|
| `architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | 50,246 | The missing multi-display DQDS requirement document, **PROPOSED and unauthorised**. Records the current state by evidence (one branch-wide board route in `backend/queuing/display.py`, 24 board tests, 10 s polling, device-local language, **no** display table, **no** display capability, **no** device pairing, **no** SSE/WebSocket) and separates implemented, partially implemented, documented-but-absent and unverified. States the three source conflicts it works inside (BR §33's later-phase sentence vs MVP §16/PQV §B.6; V2.x's deferred "advanced" multi-display; BR §34's administrator ownership of display configuration) and resolves none of them as business fact. Defines the hackathon minimum **MD-01…MD-12**, the twelve deferrals **D-01…D-12**, Phase 3 placement with Phase 6 demonstration, acceptance **AC-01…AC-14**, and the measured limiter arithmetic that forces per-display accounting (30 req/min per client IP against 6 req/min per screen: five screens sit exactly on the ceiling, six are refused). |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | 49,357 | The plan **amended, not replaced**: V1.0 is preserved as issued. Adds work package **WP-C.2** (Phase 3) with tasks **MP-35** registry and migration, **MP-36** display resolution and server-side doctor scope, **MP-37** department scope and room label, **MP-38** configured language and TV-scale presentation, **MP-39** capability/admin API/page/audit; and **MP-40** (Phase 6) multi-display demonstration including the six-screen load and stale/reconnect evidence. Adds gate **PO-13**, milestones **M-9/M-10**, assumptions **A-6/A-7**, risks **R-11/R-12**, sequencing rules 8–9, GAP-28 traceability and a verification recipe. 40 tasks; ≈ 65.5 engineer-days (≈ 10.5 added). The six-phase sequence, every other task, gate and estimate are unchanged; the V1.1 deferral table replaces the V1.0 row that had marked multi-display as deferred. |
| `implementation/AMSDP_Multi_Display_DQDS_Documentation_Update_Report_V1.0.md` | 14,098 | The task report: current multi-display capability by evidence (one branch-wide route, 24 board tests, polling only, no display table, no capability, no device pairing), the classification of all six capability areas, the gap list, the hackathon scope now included, every document changed or created and why the owner-controlled ones were not, the Phase 3/Phase 6 confirmation, the nine outstanding implementation items with their blocking gate, the validation actually performed, and the Governance and Skill Compliance section. States plainly that no application code, schema, deployment or infrastructure was changed. |

**Two existing documents were amended in place, append-only, with the original text preserved:**

- `audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` → **§14 Amendment A-1** (71,649 → 80,953 bytes): reclassifies **F-53** from *later phase* to *Hackathon Phase 3* by owner instruction 2026-11-24 and PQV §B.6 while leaving its **NOT IMPLEMENTED** status untouched; adds **GAP-28** (S2), making the register 28 gaps (S1 5 · S2 14 · S3 6 · S4 3); adds decision request **PO-13**; corrects four transcription errors in §4.6 (route and line counts for `display.py`, the `test_dqds.py` length, the location of the tracking routes, and a test file name that does not exist); and lists the documents reconciled. No finding was withdrawn and no severity lowered.
- `audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` → **Appendix D Amendment A-1** (149,752 → 155,457 bytes): records that **OD-4** is answered for the hackathon, maps the effect onto each of **DQD-001…DQD-014**, and keeps DQD-002 (room on the queue entry), DQD-005 (estimate/countdown), DQD-008 (next tokens) and durable rate limiting deferred.

**Read, never modified (owner-controlled):** `product/AMSDP_Business_Rules_V1.0.md`, `AMSDP_Business_Rules_V1.1.md`, `product/AMSDP_MVP_SCOPE_V1.0.md`, `AMSDP_MVP_SCOPE_V1.1.md`, `product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`, `product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`, and the master feature lists V2.0–V2.5. Their DQDS wording still says what it says; the conflict is recorded in the specification §2 and the audit §14, and referred to the Product Owner as **PO-02**/**PO-13**.

**Open item — D-5 still applies, and the count moves again.** None of the three new files claims a revision number. With them the tree holds **131** `.md` files under `docs/` (`Get-ChildItem -Recurse -Filter '*.md'`), three more than the 128 recorded above; the recount against the registered rows and the numbering reconciliation remain the owner's **D-5** task. The `docs/plan/` placement deviation recorded above now covers two files, not one. No existing document was moved, renamed or deleted.

### Product Owner decisions PO-13 / PO-02 / MP-06 applied (2026-11-24) — amendments, no new requirement document

Four owner decisions arrived after the annex above was written. They are recorded here because they changed **governance**, **an owner-controlled requirement baseline** and **three working documents**.

| Decision | Disposition |
|---|---|
| **PO-13** — Full-featured multi-display DQDS **APPROVED** for Hackathon delivery; management/configuration not deferrable | Requirement set extended **MD-13…MD-19** (estimated waiting time, room scope, refresh-on-change, facility-local operational day, facility-controlled public fields, read-only enforcement, denial accounting) with **AC-15…AC-22** and tasks **MP-41…MP-46**; multi-display is no longer described as optional anywhere |
| **PO-02** — DQDS requirements alignment **RESOLVED**; no MVP/Hackathon/Later-Releases tier; BR §33 later-phase wording must go | **`product/AMSDP_Business_Rules_V1.0.md` §33 and `AMSDP_Business_Rules_V1.1.md` §33 edited — the only owner-controlled edit in this task, and explicitly instructed by PO-02.** A new §33.1 scope-status block replaces the later-phase paragraph in both copies; the items 1–13 list is untouched |
| **MP-06** — Facility-local operational day, `Asia/Dhaka` default, applied to queue, dashboards and DQDS | Recorded as **implementation compliance** with BR §0 item 8, which already required it. `organizations.timezone` exists (`models.py:38`), so no migration is needed; **MP-44** is its DQDS proof. GAP-03/GAP-25 remain open and now include the display path (GAP-32) |
| **`docs/plan/` ratified** as an approved repository location for plans and roadmaps | **Governance changed:** `.clinerules` §11 now lists `plan/` in the sanctioned subfolder list and records the ratification. The earlier "placement deviation" is **closed**; nothing was moved, renamed or migrated, so **no migration-manifest entry is required** |

| File | Bytes before → after | What changed |
|---|---:|---|
| `audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | 80,953 → **92,574** | **§15 Amendment A-2**: decisions recorded; all thirteen BR §33 items reconciled item-by-item against code; **GAP-29…GAP-34** added (estimated wait, room scope, change signal, server-local day, public-field policy, read-only/denial audit); **GAP-28** restated as a delivery gap over MD-01…MD-19; unresolved items listed |
| `architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | 50,246 → **69,052** | **Appendix E (Amendment A-1)**: approved-scope status, **D-04 withdrawn**, **D-08 split**, MD-13…MD-19, AC-15…AC-22, data-model delta, contract deltas, §6 banner and D-04/D-08 annotations, §9.4 gates marked decided, §11.3 status updated |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | 49,357 → **62,905** | **Appendix D (Amendment A-1)**: **WP-C.3 MP-41…MP-46** (+7.5 eng-days, 40 → 46 tasks, ≈ 65.5 → ≈ 73.0), gates PO-02/PO-13 closed, sequencing 10–14, risks R-13…R-15, milestone conditions, placement-deviation closure |
| `product/AMSDP_Business_Rules_V1.0.md` | 42,812 → **47,353** | §33.1 scope-status block; header amendment line |
| `AMSDP_Business_Rules_V1.1.md` | 47,338 → **51,954** | Identical §33.1 block (byte-identical, 3,433 chars), so no stale DQDS wording survives in either copy |
| `.clinerules` §11 | — | `plan/` ratified; deviation closed |
| `implementation/AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md` | new | The reconciliation report for this task |

**Read, still unmodified:** `product/AMSDP_MVP_SCOPE_V1.0.md` §16, `AMSDP_MVP_SCOPE_V1.1.md`, `product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`, the master feature lists V2.0–V2.5, `architecture/AMSDP_System_Architecture_V1.0.md`, the ASCII UI/UX Blueprint and the demo documents. **PO-02 settled the DQDS conflict in favour of DQDS itself, so MVP §16 requires no edit**: its §16.1 already places DQDS in Phase 1 and its §16.5 "documented requirements only — not yet implemented" is a status statement, still true.


---

## Live deployment baseline correction (Windows checkout, 2026-11-24) — one new registration, five amendments

**Why this annex exists.** Six documents carried the sentence "the live database is two migration
stages behind". It was a **true measurement taken on 2026-11-23** that the same-day migration
superseded; no document in this tree recorded the application, so the sentence outlived the fact and
was inherited as current by the audit and the plan. A read-only reconciliation established the real
baseline and corrected every operative statement. Superseded sentences are **retained and dated**, not
deleted — the record shows what was believed and when.

**Verified baseline.** Branch `hackathon-mvp`, HEAD `a4ddc2cf58e019b57dccf59f3a859743e3c48430`; live
database **`c4d8e2a91f60`** (single head), migrated **2026-11-23** from `a9c4e1f7b2d8`, creating
`voice_packs`, `queue_announcement_deliveries` and `announcement_platform_config`; rehearsed on a
disposable restored database with a pre-migration backup; seeded counts preserved (organizations 421,
patients 2963, doctors 601, appointments 642, queue_entries 11, audit_events 20490).

**Freshly verified on 2026-11-24 (not inherited):** the eight services on `192.168.68.108:8110–8117`
and the frontend on `:3100` all return HTTP 200; the deployed organization service advertises all
eleven `/api/v1/voice-packs…` routes plus the platform/org announcement-config routes, and the queuing
service advertises the W2 delivery routes — code that exists only in the merged tree whose head is
`c4d8e2a91f60`. **Not verified:** the live schema revision and the three tables (no `alembic`,
`psql` or `docker` binary and no DB credential on the checking host; an authenticated probe would need
a writing `POST /api/v1/staff/login`). That gap is carried to **MP-01**.

| File | Bytes before → after | What changed |
|---|---:|---|
| `audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | 92,572 → **102,386** | **§16 Amendment A-3**: corrected baseline, fresh-vs-historical evidence table, root-cause chain, scope of change, what it does not do. §1.1 verdict, §1.4 recommendation, §2.1 live-DB row, §2.3 two rows, **GAP-01**, §8 step 1, §12 item 3 corrected in place. Severity totals unchanged |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | 62,905 → **72,842** | **Appendix E (Amendment A-2)**: §3.1 runtime row, §5.2 critical-path label, §5.3 **M-1** → "Runtime proven", **MP-01** redefined as verification (never re-apply), **MP-02** reason clarified, §9 **R-1**, §11 **GAP-01**, Appendix B recipe made conditional, Appendix C next action + change history. **No task, gate or estimate changed** |
| `implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md` | 36,213 → **38,698** | §1.4 marked **RESOLVED 2026-11-23** with a status banner; closing advice inverted to "verify first"; §4.3 made conditional and its command block now checks before upgrading; §8 sentence qualified; §11 blocker row **CLOSED**; §12 evidence rows annotated as pre-migration |
| `implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` | 20,301 → **22,092** | Dated correction note under the header; §4.2 and §4.3 rows marked as written-before-the-migration; §7 blocker row **CLOSED 2026-11-23**; §10 action 1 **DONE**, action 2 restated as a prediction |
| `implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` | ≈23,831 → **25,449** | Correction banner; header verdict, §D runtime row and §E **E-1** corrected ("record the post-migration suite baseline") |

### Registration

| Field | Value |
|---|---|
| Document | `implementation/AMSDP_Live_Deployment_Baseline_Reconciliation_Report_V1.0.md` |
| Size | 27,746 bytes · 13 sections |
| Read when | Any question about the live database revision, about **MP-01**, or about why two reports disagreed on migration state. It carries the evidence classes (VERIFIED / REPORTED / HISTORICAL / PREDICTED / NOT VERIFIED) for every claim |

**Byte figures in earlier registrations are registration-time, not current.** Where this pass amended a
document that an earlier annex registered, the figure above is the current one: runbook **36,125 →
38,698**, merge publication report **19,005 → 22,092**, implementation-state report **23,831 → 25,449**,
gap audit **80,953 → 92,574 → 102,386** (the 92,574 in the previous annex and the 92,572 measured at the
start of this pass differ by two bytes, a trailing-newline artefact; neither figure is load-bearing).
Each amended document now carries a dated correction banner or crossed-out text, so a reader arriving at
an old registration is told, in the document itself, that the migration statement there is historical.

**Counts and D-5.** The previous annex recorded **132** `.md` files under `docs/`; this pass adds one
file, so the tree now holds **133**. **D-5 is unchanged:** no revision number is advanced and no
number is invented. Nothing was moved, renamed or deleted, so no migration-manifest entry is required.
The `0.0.0.0:5433` PostgreSQL exposure is **not** addressed by this pass and remains an open security
risk requiring an owner decision.


---

## Annex — MP-05 / MP-06 / MP-07 implementation reports (2026-11-24)

Three implementation reports were written in one execution window, together with a work-package register. All
four are new files; nothing was moved, renamed or deleted.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-05_Demo_Seed_Doctor_Scope_and_Facility_Day_Implementation_Report_V1.0.md` | 15,029 | Any question about the demo **doctor → queue** linkage, about why the seeded `staff_doctor_assignments` rows were missing, or about **RBAC-R3** "demo assignment". Records the seed fix, the three new tests, the `200`/`404` scope evidence and the **§5.1 BLOCKED live re-seed** (forbidden by plan Amendment A-2 §E.5) |
| `implementation/AMSDP_MP-06_DQDS_Operational_Day_Implementation_Report_V1.0.md` | 12,322 | Any question about the DQDS board showing the **wrong day** after a Dhaka midnight, or about `operational_today` / `organizations.timezone`. Carries the mutation evidence (`2 failed, 24 passed` with the defect restored) and the two `test_dqds.py` tests |
| `implementation/AMSDP_MP-07_Dashboard_Waiting_Tile_Implementation_Report_V1.0.md` | 11,394 | Any question about the dashboard **Waiting tile** double-counting, about `frontend/pages/dashboard.js` tile bindings, or about the open `in_queue` vs `queue_length` payload decision. Carries the source-contract test and the `duplicate tile binding` mutation failure |
| `plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | see its own registration | The **execution state** of the work packages touched in this window: what is TESTED / VERIFIED, what is BLOCKED and why, and the decisions still owed by the Product Owner. Read it before selecting the next task |

**Evidence artefacts (outside `docs/`, therefore not registered here):** `runs/backend-baseline-2026-11-24.log`
(`791 passed`), `runs/backend-final-2026-11-24.log` (`796 passed, 0 failed, 816.87s`),
`runs/evidence-mp06-mutation.log`, `runs/evidence-mp06-fixpass.log`, `runs/evidence-mp05-verification.log`,
`runs/evidence-mp07-mutation.log`, `runs/frontend-baseline-2026-11-24.log`,
`runs/frontend-suite-2026-11-24-post-fix.log`, and the two restore copies `runs/display.py.orig`,
`runs/dashboard.js.orig`. These are run logs, not AMSDP documents, and are kept beside the code deliberately.

**Counts and D-5.** The previous annex recorded **133** `.md` files under `docs/`; this pass adds three
implementation reports and one register, so the tree now holds **137** (133 + 4, measured at write time).
**D-5 is unchanged:** no revision number is advanced and none is invented. No migration-manifest entry is
required, because nothing was moved, renamed or deleted — all four files are new.


---

## Annex — MP-08 implementation report (2026-11-24)

One implementation report was written in the MP-08 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-08_Announcement_Safe_Recall_Implementation_Report_V1.0.md` | 15,016 | Any question about **queue recall**, about why `call` from `called` still returns **422**, about the `recall` action's transition/permission/audit contract, about `call_events()` counting `call` **and** `recall`, or about the announcement tracker's new `call_event_id` rule. Records the plan/code conflict, the Product Owner's **option (a)** decision, the 22 new tests, the `808 passed` backend run, the `6 failed` mutation and the queue-trio frontend run |

The **execution state** for this work (row MP-08, Q-5 closed, the §9 resolution note) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **137** `.md` files under `docs/`; this pass adds one implementation
report, so the tree now holds **138** (measured at write time: `Get-ChildItem docs -Recurse -Filter *.md`).
**D-5 is unchanged:** no revision number is advanced and none is invented.

**One cross-document effect worth knowing.** The evidence status of all three reports is capped at TESTED, and
MP-05 at VERIFIED **on a scratch database only** — no live environment was touched. `plan/` therefore now
contains both an authorised plan (V1.1) and an execution register that must be read with it; the register, not
this index, is where task state is maintained.

---

## Annex — MP-10 implementation report (2026-11-24)

One implementation report was written in the MP-10 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-10_Walk_In_Policy_Configuration_Implementation_Report_V1.0.md` | 23,050 | Any question about **walk-in placement** (BR §25): which of the four policies a facility uses, where that setting lives (`organizations.config["queue_config"]`), how the four behaviours differ at insertion time, why the per-request `walk_in_policy` field was retired, how the reserved pool is computed and filled, why `arrived_at` exists, what `queue.reposition` rows a placement writes, or who may change the policy (`PUT /api/v1/orgs/{id}/walk-in-config`). Also records the **§8 rule 3 deviation** (no Alembic revision, with the reason) and the token-gap limitation |

The **execution state** for this work (row MP-10, frontend run, working-tree additions) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **138** `.md` files under `docs/`; this pass adds one implementation
report, so the tree now holds **139** (measured at write time: `Get-ChildItem docs -Recurse -Filter *.md`).
**D-5 is unchanged:** no revision number is advanced and none is invented.

---

## Annex — MP-33 CI truth report (2026-11-24)

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-33_CI_First_Green_Run_Report_V1.0.md` | 7,793 | Any question about the **pipeline's real state**: whether a green run exists (yes — run #5, 2026-11-14), which job is red on the latest run and at which step (frontend, `Run frontend tests`, exit 1), what the two frontend reds actually are (a BanglaNameSense dataset **provenance mismatch** and a test file that does not load), and which local equivalents were executed in this window (`alembic current` = head, 847 backend tests, `npm run build` success, `npm test` 383/379/2/2) |

The **execution state** for this work (row MP-33, Q-3 diagnosis) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **139** `.md` files under `docs/`; this pass adds one report, so the
tree now holds **140** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 140). **D-5 unchanged.**

---

## Annex — MP-16 blocked-periods report (2026-11-24)

One implementation report was written in the MP-16 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-16_Blocked_Periods_Report_V1.0.md` | 27,859 | Any question about **blocked periods** (BR §15): why the capability was recorded as *absent* rather than broken (GAP-12/F-20), where a block lives (`schedule_blocks`, its columns/indexes/`CHECK`), why it is a table and not `organizations.config`, why enforcement is **doctor-wide** rather than per schedule or per branch, what the three routes are (`POST`/`GET`/`DELETE /api/v1/schedules/{id}/blocks`) and who may call them (`schedule.manage` to write, branch-scoped staff to read), what `available-slots` now publishes (`blocked`, `blocked_periods`, `blocked_slot_count`), how a booking is refused (`blocked_period: …`, 422, in create **reschedule and transfer**), how the authorised exception works (`override_block` + mandatory reason + `appointment.block_override`, gated on `schedule.manage` and **not** delegable), why an unreadable stored window degrades to whole-day instead of 500, and what is deliberately still missing (no UI, walk-in arrivals not covered, blocks are not branch-scoped, no recurring rules). Also the D1–D9 evidence table, the mutation result (`7 failed, 44 passed`) and the whole-suite run (`898 passed`) |

The **execution state** for this work (row MP-16, Q-6 resolution, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **140** `.md` files under `docs/`; this pass adds one report, so the
tree now holds **141** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 141). **D-5 unchanged:** no revision
number is advanced and none is invented.

**One cross-document effect worth knowing.** MP-16 adds a schema object (`schedule_blocks`) and a new migration head
(`b2e5c7d91a04`, replacing `c4d8e2a91f60`). Any document that quotes the head revision — including the MP-33 annex
above, which correctly recorded `c4d8e2a91f60` at the time it was written — is a **historical** statement, not a
current one. The current head is the one named in the MP-16 report §4.1.

## Annex — MP-19 staff and permission management report (2026-11-24)

One implementation report was written in the MP-19 window (it covers MP-20 as well, because the doctor-assignment
editor is a section of the same dialog). It is a new file; nothing was moved, renamed or deleted, so no
migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-19_Staff_and_Permission_Management_Implementation_Report_V1.0.md` | 28,644 (373 lines) | Any question about the **staff administration screen** (MP-19/MP-20, GAP-17/F-09/F-06): what the screen offers (roster, create, edit, role, branch scope, deactivation, capability grants, doctor assignment), why the rules live in `frontend/lib/staff-policy.js` rather than in the page, why the delegable **set** is read from `GET /api/v1/staff/capabilities` while only its **labels** are client-side, why saving is a diff (no audit row for a no-op), why deactivation is a two-step status change and never a delete, why revoking a branch-scoped grant must name the branch, what the 12 policy tests and the 14 wiring/mirror/i18n tests assert, the mutation result (revoke scope removed → `1 failed, 13 passed`, file restored byte-identically `600BB633…9888`), the frontend suite arithmetic (`383/379/2/2` → `409/405/2/2`, +26 all-pass, the two reds being the pre-existing Q-3 pair — the dataset-hash assertion plus `calendar-render.test.mjs` failing to load on Windows), the build result (`/staff` prerendered, 5.71 kB / 125 kB), and — stated plainly — that the 31 identity tests collect cleanly but were **not run** on this host (`test_identity.py` aborts at import: no PostgreSQL on port 5433), so nothing here is VERIFIED. Also the governance/skill compliance table and open items O-1…O-6 |

The **execution state** for this work (rows MP-19 and MP-20, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **141** `.md` files under `docs/`; this pass adds one report, so
the tree now holds **142** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 142). **D-5 unchanged:** no
revision number is advanced and none is invented.

**One thing this annex deliberately does not claim.** MP-19 changes no schema and adds no migration, so the
migration head is unchanged (`b2e5c7d91a04`, as recorded in the MP-16 annex and report §4.1). The screens changed
are `frontend/pages/staff.js`, `frontend/lib/staff-policy.js` and `frontend/lib/i18n.js`; the frontend test tree
gained `tests/staff-page.test.mjs`.

---

## Annex — MP-17 doctor mobile duplicate allowance report (2026-11-24)

One implementation report was written in the MP-17 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-17_Doctor_Mobile_Duplicate_Allowance_Implementation_Report_V1.0.md` | 23,224 (304 lines) | Any question about **doctor mobile-number uniqueness** (MP-17, GAP-13 / F-17, BR §9.6–§9.8): what the rule was before (implemented twice, inline, with no switch), why the allowance is stored in `organizations.config["doctor_mobile_policy"]` rather than in a column, why a missing/non-dict/non-boolean block reads as **unique** instead of permissive, why only a platform administrator may change it and why that is a `403` rather than a hidden route, why withdrawing the allowance is **prospective** and leaves existing duplicates in place, why the duplicate lookup stays organization-scoped so §9.8 holds under either setting, what the 23 policy tests and the 6 enforcement-decision tests assert, the negative control (`doctor_mobile_must_be_unique` → `return False` → `23 failed, 6 passed`, file restored byte-identically `C4A667B7…FDF9`), and — stated plainly — that the 12 API tests **collect** but were **not run** on this host (no PostgreSQL on port 5433), so the `403` gate, the audit `before`/`after` and both cross-tenant cases are unproven and nothing here is VERIFIED. Also the governance/skill compliance table and open items O-1…O-4 |

The **execution state** for this work (row MP-17, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **142** `.md` files under `docs/`; this pass adds one report, so
the tree now holds **143** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 143). **D-5 unchanged:** no
revision number is advanced and none is invented.

**One thing this annex deliberately does not claim.** MP-17 changes no schema and adds no migration, so the migration
head is unchanged (`b2e5c7d91a04`, as recorded in the MP-16 annex and report §4.1). No frontend file was touched, so
the frontend suite figure stands at the MP-19 record (`409 / 405 / 2 / 2`) and no frontend run was made in that
window. The backend test tree gained `tests/test_doctor_mobile_policy.py`,
`tests/test_doctor_mobile_enforcement.py` and `doctor/tests/test_doctor_mobile_duplicates.py`.

---

## Annex — MP-18 schedule-edit audit report (2026-11-24)

One implementation report was written in the MP-18 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-18_Schedule_Edit_Audit_Implementation_Report_V1.0.md` | 20,774 (269 lines) | Any question about **who changed a doctor's published hours or capacity, and what the values were** (MP-18, BR Part X): the write-path inventory that was actually inspected (schedule POST/PATCH, session POST/PATCH/DELETE, block POST/DELETE) and what each already recorded; the **gap the verification found** — `sync_slot_templates` rewrites `schedules.slot_templates` (the projection `available-slots` and the calendar read) on every session write, so the schedule row changed with no `schedule.*` event; how `audit_template_projection` closes it (same `schedule.templates_changed` action, targeted at the schedule, only when the published windows moved); why `windows_map` is local to `sessions.py` (circular-import reason) and how it stays consistent with `main._capacity_map`; the 13 DB-free tests including the **AST guard** over every write route; the negative control (`1 failed, 12 passed`, `sessions.py` restored byte-identically `1541A5C8…1E33`) and why the route-level guard alone stayed green; and — stated plainly — that the 12 PostgreSQL tests in `scheduling/tests/test_schedule_audit.py` (8 pre-existing + 4 new) **collect but were not run** on this host (no database on port 5433), so nothing here is VERIFIED. Also the governance/skill compliance table and open items O-1…O-4 |

The **execution state** for this work (row MP-18, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **143** `.md` files under `docs/`; this pass adds one report, so the
tree now holds **144** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 144). **D-5 unchanged:** no revision
number is advanced and none is invented.

**One thing this annex deliberately does not claim.** MP-18 changes no schema and adds no migration, so the migration
head is unchanged (`b2e5c7d91a04`). No frontend file was touched, so the frontend suite figure stands at the MP-19
record (`409 / 405 / 2 / 2`). The files that changed are `backend/scheduling/sessions.py`,
`backend/scheduling/tests/test_schedule_audit.py` and the new
`backend/tests/test_schedule_audit_coverage.py`.

---

## Annex — MP-22 dashboard completion report (2026-11-24)

One implementation report was written in the MP-22 window. It is a new file; nothing was moved, renamed or deleted,
so no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-22_Dashboard_Completion_Implementation_Report_V1.0.md` | 20,268 (262 lines) | Any question about the **dashboard** (MP-22, Blueprint §2): what the screen carried before (six figures, no selectors) and why the date selector had to become a server question (`date=YYYY-MM-DD` on `/api/v1/dashboard/today`, 422 on anything else, facility-day default per BR §8, `facility_today` in the response); why the branch selector is filtered in `lib/dashboard.js::selectableBranches` and why a branch-scoped user with no matching branch gets an **empty** list rather than "all"; the quick-action and activity rules (an unknown audit action renders as its own slug); why the six MP-07 tiles were left verbatim; the evidence (28 dashboard tests green, frontend suite `409/405/2/2 → 434/430/2/2`, negative control on the selector-widening defect with the file restored byte-identically `9C20CF10…F335`, `npm run build` exit 0 with `/dashboard` prerendered 6.6 kB / 99.8 kB); the **failed** first build and its cause, disclosed rather than omitted (§4.4); and, plainly, that the six new PostgreSQL cases were **not run** and that **Blueprint §2 was not read line by line** (O-2). Also the governance/skill compliance table and open items O-1…O-5 |

The **execution state** for this work (row MP-22, suite table, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **144** `.md` files under `docs/`; this pass adds one report, so the
tree now holds **145** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 145). **D-5 unchanged:** no revision
number is advanced and none is invented.

**One thing this annex deliberately does not claim.** MP-22 changes no schema and adds no migration (the date
selector is a query parameter, not a column), so the migration head is unchanged (`b2e5c7d91a04`). The frontend suite
**did** move in this window — `409/405/2/2 → 434/430/2/2` — unlike the MP-17 and MP-18 windows, because the change is
a screen.


---

## Annex — MP-28 and the PostgreSQL evidence window (2026-11-24, later)

Two implementation reports were written in this window. Both are new files; nothing was moved, renamed or deleted, so
no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-28_Unified_Internationalization_Implementation_Report_V1.0.md` | 17,362 (275 lines) | Any question about **translation** (MP-28, GAP-23 / F-59): which five screens carried their own `{bn,en}` dictionary and how the 173 keys were moved **verbatim** into `frontend/lib/i18n.js` under `home*`/`org*`/`brn*`/`pat*`/`apt*`; why `appointments.js` needs an `aptKey` namespace helper for the nine runtime-built keys (`REFUSAL_KEYS`, `typeLabelKey`, `typeBadgeKey`, the list view, the match banner) and what would silently break without it; what the new `tests/i18n-coverage.test.mjs` proves (parity, no silent fallback, no duplicate declaration, no page-local dictionary, every literal **and** runtime key in both languages) and the mutation that turned it red; why eight older source-contract tests were re-pointed rather than deleted (§6); the suite `434/430/2/2 → 441/437/2/2` and the build; and what is **not** proven — no browser run, the component label defaults left as Bangla-only fallbacks, one English developer note on the login page (§7) |
| `implementation/AMSDP_PostgreSQL_Verification_and_MP-01_Reconciliation_Report_V1.0.md` | 12,740 (209 lines) | Any question about **the database, the migration head, or why earlier windows said tests could not run**: the read-only MP-01 probes (live `:8110`/`:3100`/`:5433` reachable, `:22` refused, **no DB credential** → live revision unread, **B-4**); the discovery that the local database is on **`127.0.0.1:55432`** rather than 5433 and sits at `b2e5c7d91a04`; the isolated `amsdp_verify_2829` created and migrated from empty to head; and the first execution of the previously unrun suites — dashboard **12 passed** after the D-0 date-padding fix, MP-17 **11/12** (D-2), MP-18 **8/12** (D-1, grade reduced), identity **71 passed / 4 setup errors** (D-3) |

The **execution state** for both (rows MP-28 and MP-01, the superseding-evidence note under §2, suite table, next
eligible task) lives in `plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **145** `.md` files under `docs/`; this pass adds two, so the tree now
holds **147** (`Get-ChildItem docs -Recurse -Filter *.md` → 147). **D-5 unchanged:** no revision number is advanced
and none is invented.

**One thing this annex deliberately does not claim.** Neither task changes the schema — MP-28 is frontend strings and
the D-0 fix is a query-parameter validation — so the migration head is unchanged at `b2e5c7d91a04`. The isolated
database created for the evidence window is **not** the live deployment and says nothing about it; the live revision
stays unread under **B-4**, and the discrepancy between the plan's recorded `c4d8e2a91f60` and the tree's
`b2e5c7d91a04` is recorded as an open question, not resolved by inference.




---

## Annex — MP-29 responsive/touch/accessibility report (2026-11-25)

One implementation report was written in the MP-29 window. It is a new file; nothing was moved, renamed or deleted, so
no migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_MP-29_Responsive_Touch_and_Accessibility_Implementation_Report_V1.0.md` | 29,962 (379 lines) | Any question about **keyboard, touch or small-screen use of the queue and appointment screens** (MP-29, WP-G): why the reorder arrows never worked for anyone (`DataTable` called `c.render(row)` with no index, so `move(undefined, ±1)` wrote `undefined` into `entry_ids` and the server refused every reorder); the rules in `frontend/lib/a11y.js` (`MIN_TARGET_PX = 44`, `Alt` as the reorder chord, `toPosition` refusing `null`/`''`/`NaN`, `moveWithin` as a no-op rather than a clamp) and why bare arrows deliberately keep scrolling the page; the 17 new tests (8 decision tests + 9 source-contract tests that parse `global.css`); the inherited **MP-02** reds — **D-1** (`"session_id" in template`, key presence not truthiness, in `scheduling/sessions.py`), **D-2** (the two-gate 403 contract asserted with a new `ORGADMIN` fixture) — and the further **D-4** the first full run exposed (`.order_by(AuditEvent.id.desc())` over a **UUID** string returns an arbitrary event, not the newest; two instances fixed to `timestamp.desc()`); the suite figures (backend `979 passed, 0 failed`, frontend `441/437/2/2 → 458/454/2/2`, the two reds still the Q-3 pair); **D-3 does not reproduce** and is not claimed as fixed; and the four acceptance clauses that remain unproven because no browser, viewport, screen reader or auditing tool was used (§7). Also the governance/skill compliance table — including the verification that no skill package is installed — and open items O-1…O-5 |

The **execution state** for this work (row MP-29, suite table, next eligible task) lives in
`plan/AMSDP_Work_Package_Execution_Register_V1.0.md` and is not restated here.

**Counts and D-5.** The previous annex recorded **147** `.md` files under `docs/`; this pass adds one report, so the
tree now holds **148** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 148). **D-5 unchanged:** no revision
number is advanced and none is invented.

**One thing this annex deliberately does not claim.** MP-29 changes no schema and adds no migration — the queue row's
accessibility is markup, CSS and a tested pure module — so the migration head is unchanged at `b2e5c7d91a04`. The
frontend suite **did** move (`441/437/2/2 → 458/454/2/2`) and the backend suite is now green against the isolated
`amsdp_verify_2829`, which is **not** the live deployment; the live revision stays unread under **B-4**. No file was
staged, committed, reverted or stashed in this window (report O-3).

---

## Annex — Product Owner Decision Pack (2026-11-25)

One document was written in this window. It is a **new file**; nothing was moved, renamed or deleted, so no
migration-manifest entry is required.

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` | 99,460 (1,127 lines) | **Before taking any owner decision on the roadmap, or before asking the owner for one.** It is the single consolidated request covering the eleven open plan gates (**PO-01, PO-03 … PO-12**, PO-02/PO-13 explicitly not reopened), the owner-controlled blockers found by execution evidence (**MP-01 / B-4**, **Q-1 … Q-4**, **B-1 … B-3**, **O-3**), and the two technical investigations the owner arbitrates (**Q-3**, **D-3**). One card per item: why it is needed, what the requirements say, what the code actually does, one recommendation with its rationale, two or three alternatives with their task consequences, a copy-paste response line, and the implementation consequences. Also contains the consolidated response sheet (§5) and the decision → task dependency map (§6.2–§6.3). **New evidence recorded there and nowhere else yet:** the Q-3 dataset "hash mismatch" is a **CRLF artefact** (the committed blob is 80,517 bytes and hashes to the recorded `ac037c24…e51e`; `git ls-files --eol` shows `i/lf w/crlf`, `core.autocrlf=true`, no `.gitattributes`), and `calendar-render` is a **Windows ESM path bug in the harness** (all 9 tests pass once the paths go through `pathToFileURL`), so neither is a product defect and no expected value should be reconciled; the *committed* tree's migration head is `c4d8e2a91f60` — the recorded live revision — while the working tree is one revision ahead only because MP-16's `b2e5c7d91a04` is **untracked**; the Feature Catalogue §H.1 "P0 scope defects" are stale in the product's favour (branch scope is enforced at `queuing/main.py:191–203`, `:297–300`, `:422–426`); and the Limitations Report §12 still claims in-memory storage with no PostgreSQL |

The **execution state** it reasons from lives in `plan/AMSDP_Work_Package_Execution_Register_V1.0.md`, and the gates
themselves in `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §4. Neither is restated here.

**Counts and D-5.** The previous annex recorded **148** `.md` files under `docs/`; this pass adds one, so the tree now
holds **149** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → 149). **D-5 unchanged:** no revision number is
advanced and none is invented — the pack itself recommends the forward-only numbering rule that would end this
ambiguity (its PO-08 card).

**What this annex deliberately does not claim.** The pack is a **decision request**: it records no decision, closes no
gate, amends no plan task and changes no code. Every recommendation in it is labelled as a recommendation. Its own
evidence grades are stated in its §8.4, and the only commands it executed are listed in its §8.5 — two individual
frontend test files, read-only git and search commands, and two scratch scripts written outside the repository (one
temporary probe file was created inside `frontend/tests/` and removed in the same window; the dirty-entry count was
re-measured afterwards). Nothing was staged, committed, reverted or stashed.

---

## Annex — Product Owner decisions applied (2026-11-25) — **Revision 49**

**This annex is numbered, and that is the point of it.** Product Owner decision **PO-08** (25 November
2026) adopted a forward-only numbering rule — *the next revision is the highest previously recorded
revision + 1, and each annex names the revision it was issued under* — because the annexes written
between 21 and 25 November each said "no revision number is advanced", which left them unidentifiable.
The base index ends at **Revision 48**, so this annex is **Revision 49**. The earlier unnumbered annexes
are **not** retro-labelled: D-5 is forward-only and retro-labelling would rewrite history rather than
fix the rule.

Everything below is a **new file** except where stated. One binary asset was deleted outside `docs/`
(`frontend/public/audio/bn/phrase/room-suffix.wav`, POD-7, listed in its own report); **no document was
moved, renamed or deleted**, so no migration-manifest entry is required. `docs/plan/` was an untracked
folder until this window and is now under version control, which changes no path.

| File | Bytes | Read when |
|---|---:|---|
| `decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` | 19,068 | **Before acting on any decision in the pack.** It is the authoritative record of what the Product Owner approved (PO-01, PO-03…PO-12 as the recommended options, POD-11 = Faria Bushra, Q-4 scope, O-3 scope, Q-3, D-3) **and what was not approved** (B-1…B-3, Q-1, Q-2, B-4 — the owner selected "other"), so nothing can be inferred by adjacency. Also records the two measured corrections to the request: the index's next revision is **49**, not 48, and the unreferenced audio list is **one** file, not fifteen |
| `product/AMSDP_Phase_Model_V1.1.md` | 5,894 | Any question about **Phases 4, 5, 6** or about what **MP-30** now is (PO-01): the names come from the multi-display specification, each phase has a scope, an exit criterion and the Product Owner as accepting authority, and MP-30 is verification of four named handoff surfaces with **no new clinical feature** |
| `plan/AMSDP_Feature_Key_Register_V1.0.md` | 6,077 | Any traceability question (PO-12): 26 `F-nn` keys, each mapped to its catalogue ID, Business Rules section, milestone, delivering task and evidence basis. Catalogue IDs are not renamed. One declared gap: **R-1**, the V2.5 family column |
| `deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md` | 5,700 | Before the **PO-10 maintenance window**, and before anyone claims the `:5433` exposure is closed — it is not. Order (SSH, then loopback binding, then verification, then the B-4 read), rollback for each change, and the rule that the read is read-only and stops if the revision already matches the committed head |
| `implementation/AMSDP_W6_Audio_Asset_Reference_Verification_Report_V1.0.md` | 4,163 | Before deleting or re-encoding any announcement audio (POD-7). Method: every asset path declared in `frontend/public/audio/manifest.json` compared with every file on disk — 71 files, 70 declared, 1 undeclared, 0 missing. The "15 unreferenced" figure is withdrawn |
| `implementation/AMSDP_PO_Decisions_25_November_2026_Implementation_Report_V1.0.md` | 18,581 | Before building on this window's work: initial and final repository state, the 19 path-grouped commits, the Q-3 repair (25 insertions / 15 deletions, no expected value changed), the annotation set, the D-3 investigation (reproduces only as a module-import collection error with no database), the tests actually run and their exact figures, and the disclosures — including a git race that was corrected and why the backend suite has no figure |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (**modified**) | 72,842 → +82 lines | The plan now carries **Amendment A-3** (Appendix F), append-only in the shape of A-1 and A-2: the gates closed, MP-30 defined, MP-34 re-graded, and the tasks that stay blocked, deferred or authorised-but-not-started |
| `plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (**modified**) | 67,264 → +§7.1 | The register's new **§7.1** records one row per gate and the task-status delta. §7 itself is left exactly as it stood, as the evidence of what was blocked and why |
| `demo/AMSDP_Limitations_Report_V1.0.md`, `product/AMSDP_MVP_SCOPE_V1.0.md`, `product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` (**modified, annotation only**) | — | §1, §7, §H and §H.1 respectively. Every change is a dated, additive block; **no original sentence was rewritten or deleted** (PO-03, PO-09) |

**Counts.** The previous annex recorded **149** `.md` files under `docs/`; this window adds six new
documents (the six rows above marked with a size, excluding the three modified files), so the tree now
holds **155** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → **155**).

**What this annex deliberately does not claim.** No decision in it is `VERIFIED` or `ACCEPTED` except
the owner's own written answers. No test figure appears that was not run in this window — in particular
**the backend suite could not run at all** (no PostgreSQL on this host) and no figure is claimed for it.
No live change happened: no migration, no reseed, no restart, no host configuration, and the database
port is still reachable. Nothing was pushed; the remote tip is unchanged, and **`.clinerules` remains
uncommitted** because Q-4 authorises Business Rules §33 only.




---

## Annex — Q-1 and Q-2 closed, and the first push of `hackathon-mvp` (2026-11-25) — **Revision 50**

**Numbering.** Product Owner decision PO-08 (25 November 2026) made revision numbering forward-only:
*the next revision is the highest previously recorded revision + 1*. The last recorded revision is
**49** (the annex above), so this annex is **Revision 50**. Nothing is retro-labelled.

**Trigger.** The Product Owner's second written instruction of 25 November 2026
(`decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` **§11, Addendum A-1**) answered **Q-1**
and **Q-2** and granted two authorities: pushing the local commits on `hackathon-mvp`, and adding demo
data to demo/testing environments within stated limits. The plan applies it as **Amendment A-4**
(Appendix G).

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_Q1_Q2_Facility_Day_And_Dashboard_Counts_Report_V1.0.md` | 16,263 | Before building on either change, or before quoting any test figure from this window. It carries the database identification (`127.0.0.1:55432`, PostgreSQL 16.4, `alembic_version` `b2e5c7d91a04`, fixture-heavy development data), the two defects, the three negative controls, and the exact figures: `46 passed` targeted, **`993 passed, 0 failed` whole backend suite in 967.75s**, `467 / 465 / 0 / 2` frontend, `Compiled successfully` build |
| `decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` (**modified**) | 19,068 → 24,622 | The authority itself. Addendum A-1 (§11.1–§11.6) records Q-1, Q-2, the push authorisation, the demo-data limits, **what A-1 does not decide**, and the evidence pointers — append-only; no earlier answer is rewritten |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (**modified**) | 72,842 → 84,239 | The plan's new **Amendment A-4** (Appendix G): the gate table after the addendum, MP-07's corrected target field, the note that MP-33 is *mechanically unblocked but not accepted*, and the four things the amendment refuses to claim |
| `plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (**modified**) | 67,264 → 76,664 | The register's new **§10**. §4's Q-1/Q-2 rows are left exactly as written — superseded, not edited — because rewriting them would erase the evidence that the question existed |

**Counts.** The previous annex recorded **155** `.md` files under `docs/`; this window adds **one** new
document, so the tree now holds **156** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → **156**).

**Commits and the push.** Three path-grouped commits, in this order: backend `e23a2ce` (4 files,
301 insertions, 16 deletions), frontend `516e46b` (3 files, 37 insertions, 3 deletions), and the commit
carrying this annex and the documents above. Nothing was staged that had not been read; **`.clinerules`
remains uncommitted** because its change is the owner's own `docs/plan/` ratification note, not an
agent's edit. The push target is `origin/hackathon-mvp` only — no force-push, no history rewrite, no
branch deletion, no other branch. The remote tip after the push is recorded in the report's post-push
verification section and in register §10.

**What this annex deliberately does not claim.**

1. **No task is `ACCEPTED`.** The Product Owner has not signed this work; `ACCEPTED` is assigned by the
   owner, never inferred from a green suite.
2. **Nothing is `VERIFIED`.** No browser session and no live API call against the deployment happened
   in this window; the changes are `IMPLEMENTED` and `TESTED` on the local development database only
   (**B-2** outstanding, **B-3** outstanding).
3. **No live change happened.** No DDL, no migration, no reseed, no service restart, no host
   configuration change, **no database port opened**. The `:5433` exposure recorded in the PostgreSQL
   exposure plan is unchanged. **B-4 remains undecided**: the owner clarified which database exists but
   did not select an access method.
4. **The demo-data authority was not exercised.** No rows were seeded and no seeding script was added;
   the reason is recorded in report §6 rather than left as a silent omission.
5. **The push does not make CI green.** MP-33's acceptance still needs an observed first green run.


---

## Annex — multi-display public surface executed (2026-11-25) — **Revision 51**

**Numbering.** The rule is unchanged (PO-08, forward-only): *the next revision is the highest previously
recorded revision + 1*. The last recorded revision is **50** (the annex above), so this annex is
**Revision 51**. Nothing is retro-labelled.

**Trigger.** The Product Owner's autonomous completion instruction of 25 November 2026 authorised
continued execution of the plan, including "the multi-display DQDS work under MP-35 through MP-46,
respecting the dependency chain and B-4 restriction", with the standing rule that work not requiring
B-4 must continue. The plan applies it as **Amendment A-5** (Appendix H).

| File | Bytes | Read when |
|---|---:|---|
| `implementation/AMSDP_Multi_Display_DQDS_Public_Surface_Implementation_Report_V1.0.md` | 28,479 | Before building on the display registry or quoting any figure from this window. It carries the environment (local `127.0.0.1:55432`, revision `b2e5c7d91a04` → `d3f5a7b91c24`), the schema proof (31 → 33 tables, **zero** existing tables changed), the public contract before/after, the nine disclosures, and the exact results: 34 new tests, **`1027 passed, 0 failed` in 630.62s**, frontend `467 / 465 / 0 / 2`, three negative controls |
| `deployment/AMSDP_B4_Database_Access_Decision_Brief_V1.0.md` | 7,204 | Before answering **B-4**. States exactly what a read consists of (three `select`s and `docker compose ps`), the three safe access options with their exposure, which tasks each unblocks, that a read alone needs no production change, and that applying the new revision to the deployment needs a **separate** go-ahead |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (**modified**) | 84,239 → 92,009 | The plan's new **Amendment A-5** (Appendix H): the executed status changes, the correction that the migration head is **`b2e5c7d91a04`** rather than the `c4d8e2a91f60` four places still state, the clarification of what the B-4 row blocks, one schema interpretation and one sequencing deviation |
| `plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (**modified**) | 76,664 → 82,410 | The register's new **§11** and its §8 change-log row. §10 and every earlier section are left exactly as written |

**Counts.** The previous annex recorded **156** `.md` files under `docs/`; this window adds **two** new
documents, so the tree now holds **158** (measured: `Get-ChildItem docs -Recurse -Filter *.md` → **158**).

**Commit.** The code change is one path-grouped commit, `082e2a0` — `backend/common/models.py`,
`backend/queuing/display.py`, the new revision and the new test file; 4 files, 1,289 insertions,
23 deletions. The commit carrying this annex contains only `docs/`. **`.clinerules` remains
uncommitted**: its change is the owner's own `docs/plan/` ratification note, not an agent edit.

**What this annex deliberately does not claim.**

1. **No task is `ACCEPTED`.** The Product Owner has not signed this work.
2. **Nothing is `VERIFIED` for the deployment.** Every artefact is from the local development database
   and `TestClient`; no browser session, no live API call, no deployment query (**B-2** outstanding,
   **B-3** outstanding, **B-4** undecided).
3. **No live or production change happened.** No migration on the deployment, no reseed, no service
   restart, no host configuration change, no port opened. **The new revision is applied to the local
   development database only.**
4. **M-9 and M-10 are not met.** MP-38 (configured language and TV typography), MP-39 (display
   administration) and MP-35's demo seed are outstanding, and MP-40's evidence cannot be produced
   without B-4.

