# AMSDP — Documentation Index (navigation)

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10 (revised 2026-11-17) · **Snapshot:** **83** markdown documents on disk, every one now accounted for below — **79** in the `docs/` trees (11 at the `docs/` root + 68 across the subject folders, of which 6 are the `architecture/saas/` set registered in Revision 27 and 1 is the SaaS reconciliation report registered in Revision 29) plus the **4** `docs/chatgpt/` planning files listed in that section (§12). Per-file sizes below; recompute with the *Maintenance* command. *(Document-count check, 2026-11-17, Revision 29: 78 + 4 = **82** on disk and **82** registered rows. Revision 27 registered the six-document SaaS set → 81; Revision 28 closed open item **O-Y** (the `chatgpt/` count drift) at 81; Revision 29 added `governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md` → **82**. Revision 30 corrected three records in place — O-SaaS-15/MFA, the A3 profiles and the report's commit status — with **no** row-count change: still **82**. Revision 31 added `product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` → **83**.)*
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
> **Revision 31 — 2026-11-17**, task AMSDP-MVP-FEATURE-CATALOGUE-2026-11-17 — **one new document**: product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md, a feature-level catalogue and acceptance checklist for the AMSDP Hackathon MVP. No code, schema, migration, endpoint, component, test or running stack was touched. Row count increased from 82 to 83.
> new index-level open item.

---


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
| `AMSDP_M2_Security_Implementation_Report.md` | 6,374 | Any auth/RBAC/tenancy change; any security claim in a report | — |

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
| `AMSDP_M4_Appointment_Implementation_Report.md` | 4,374 | Appointment features | — |
| `AMSDP_M5_Queue_Implementation_Report.md` | 5,570 | Queue management features | — |
| `AMSDP_M6_Implementation_Plan.md` | 6,785 | Planning work that builds on M6 | — |
| `AMSDP_M6_Implementation_Report.md` | 6,753 | M6 audit/observability behaviour | — |
| `AMSDP_UI_UX_and_Reusable_Components_Assessment.md` | 6,305 | Frontend work; what shared components exist and what is missing | — |
| `AMSDP_Frontend_Visual_Quality_Investigation.md` | 3,442 | Frontend visual regressions or styling standards | — |
| `AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` | 25,336 | Patient-name entry, the BanglaNameSense dataset/matcher/component, or any reuse in doctor/staff forms | — |
| `AMSDP_One_Command_Restart_Implementation_Report_V1.0.md` | 14,732 | Starting/restarting/stopping the local stack, `_tools/amsdp_stack.sh`, startup failures | — |
| `AMSDP_Owner_Decisions_Implementation_Report_V1.0.md` | 22,388 | The platform-administration capability boundary, denial auditing, the CI pipeline, or how Q-1…Q-6 were verified (and what was not) | — |
| `AMSDP_CI_First_Run_Failure_Investigation_V1.0.md` | 25,424 | Diagnosing why the CI pipeline fails, `alembic`/`python -m` invocation questions, or the frontend test failures in `banglanamesense-integration.test.mjs` | — |
| `AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` | 67,732 | Appointment booking UI, the week/day calendar grid and card anatomy, `lib/calendar/grid.js` + `lib/calendar/list.js`, `chipLayout()` overflow, slot capacity, the `date_from`/`date_to` window on `GET /api/v1/appointments`, the paged `GET /api/v1/appointments/list` (search/sort/paging/scope, §11.4) and how the component's markup is asserted without a browser (§7.4, §11.5); **§12** — the toolbar's search/status/branch now reach Week and Day through one shared filter builder, the counts-only `GET /api/v1/appointments/matches` date index, the "matched elsewhere" banner, hit highlighting, and the 167/108 + 24-step browser evidence | — |
| `AMSDP_Facility_Doctor_Frontend_Implementation_Report_V1.0.md` | 20,296 | Doctor Management (`/doctors`), chamber assignment (`/schedules`), the facility tree (`/facilities`), `lib/phone.js`, `lib/facility.js`, BMDC verification UI, why a conflicting session is warned about client-side but still decided by the server, and what the post-rebuild runtime probes do and do not prove (§5.4) | — |
| `AMSDP_Frontend_Usability_Shared_Design_System_and_Demo_Readiness_V1.0.md` | 45,536 | **Before touching a dialog, a form field, the shared UI primitives, `/doctors`, `/facilities`, the appointment calendar, or the demo dataset** — the focus-loss root cause (`useEffect(… el.focus() …, [onClose])`) and why the Radix rewrite removes it, the token/Tailwind layer and the 14 primitives, the legacy `.flex` alias that shadowed Tailwind and the two layout defects it caused (§6), what was redesigned where, the calendar polish that keeps its SSR contract green, the hydrated-session fix and the page-level hydration remainder (**O-1**), the reset+reseed of the developer database with its audit-preserving `--reset` (54 husk organisations, **O-4**), and the full evidence set: 96/96 frontend, 216 backend, build exit 0, 6/6 demo logins, and the headless-Chrome run that typed three chunks into a real dialog while asserting the caret stayed — **12/12 checks**. §9.7 explains what the shipped focus test does and does not prove | — |
| `AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` | 67,128 | **Before touching the booking form's symptom control, the symptom catalogue, the onset question, or any appointment payload** — why the catalogue is one API response searched in memory (and why server-side search would fork the Bengali normaliser), the `symptom_catalog` / `appointment_symptoms` model with its booking-time name snapshot and two partial unique indexes, the closed onset vocabulary versus a forced date, the four optional booking fields and the three response keys, the copy-forward rule for reschedule/transfer, the ranking order (`rank → speciality tie-break → sort_order → code`) and why age/sex are never used, the 79-entry curated catalogue and its `curated` (not clinically validated) review status, the authorization matrix, the exact test/build results including the **9 pre-existing doctor-module failures**, the explicit statement that **no browser run was performed** in the morning (§12, superseded by §18), and open items O-1…O-10; **§18 is the Phase-1 runtime record** — rebuilt `appointment`/`frontend` images, only those two containers recreated, the six booking cases with their HTTP/DB/audit evidence, the Bangla/English search matrix executed against the live 79 entries, and the real-Chrome keyboard/focus run (34/35 checks, 7/7 on the detail read path), plus the O-1/O-3 closures and new items O-11…O-15 | — |

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
| `AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` | 58,648 | The last check before executing any commit: fresh verification of every earlier claim, the credential-scan result, the corrected owner-document set (five, not one), the published demo password finding (B-12), and the re-issued path-level plan C-1…C-7 with gates G-1…G-8 | — |
| `AMSDP_Tree_Commit_and_Push_Execution_Record_V1.0.md` | 17,583 | After the first push: the seven executed commits with hashes and per-commit counts, how each gate was checked, the defects found in the verification tooling, the §18.8.10 assertions, post-push verification and the R-1…R-7 register | — |
| `AMSDP_Project_Context_Report_V1.0.md` | 60,177 | **Briefing an external collaborator, or needing an evidence-graded picture of what the tree actually contains** — per-capability status with `path:line` citations, the architecture reality check AR-1…AR-6, the defect register F-1/F-2, the risk register P1-1…P3-4, the document-vs-tree conflicts C-1…C-6, a ranked reading list, and the re-verification protocol. Read this before quoting any readiness claim | — |
| `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md` | 82,914 | **History only — superseded by the V1.1 proposal below.** V1.0's §3 misdescribes D-01/D-02/D-03 and is not to be used for the decision records; read it only to see what changed between versions | — |
| `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.1_DRAFT.md` | 115,496 | **Before applying any Business Rules V1.1 / MVP Scope V1.1 / Master Feature List V2.5 / PQV / `.clinerules` / decision-register correction** — the corrected D-01…D-03 records (two permitted payment answers; `.clinerules` §1/§10 authority references; authorisation to prepare this material), the restated decisions R-1…R-4, the evidence-checked capability status table, the C-01…C-09 matrix with exact replacement wording, the six verified patches and the combined patch in Appendix A, the near-misses checked and left alone, and the open items U-1…U-7 (U-1/U-2 closed). Proposal only: nothing in it is applied and no capability in it is implemented | — |
| `AMSDP_Current_State_Demo_Diagnosis_and_Feature_Audit_V1.0.md` | 60,907 | **Before any attempt to "fix the demo" or to claim the demo is ready** — why the demo fails and staff cannot sign in (D1 frontend container absent since the stack-wide stop of 2026-11-12 and skipped in the 2026-11-14 nine-of-ten restart; D2 host-level container↔container forwarding dropped after the 2026-11-14 Docker daemon restarts with `ufw` active; D3 the isolated `amsdp_demo` stack never created, queue empty and appointments stale-dated; D4 the `/orgs` SSR `sessionStorage` crash), the evidence that the demo credentials are **correct** and **demonstrably worked** (6/6 bcrypt verifications; authenticated `super_admin` audit events at 2026-11-12T20:46:41Z), the 64-route / 14-page / 311-test matrix graded IMPLEMENTED / TESTED / VERIFIED, the prioritised repair plan R-1…R-10 with exact verification gates, the evidence appendix (26 rows), the actions deliberately not performed, the open items O-A…O-I, and **Part G** — reconciliation with the owner's account, the four corrections to Parts A–C, and the container-level timeline. Read-only: nothing was fixed | — |
| `AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md` | 50,236 | **Before wiring or "fixing" the appointment calendar's search box or its Status/Branch filters** — why they do nothing in Week and Day view: the toolbar writes only the paged list's query state while the grid is rendered from a separate `GET /api/v1/appointments` request built from the window and doctor alone (measured: 0 requests after typing a name, chips unchanged at 40, while switching to List issues the correct `?q=…&status=…&branch_id=…`); the grid endpoint has no `q`/`branch_id` and the page never sends the `status` it does support; grid 47 rows (org) vs list 42 (branch) for one receptionist; the list silently clamps to the visible week; no highlighting; unknown status → `200`/0 rows; no names in the grid payload (30 lookups per week); the source-contract test that **asserts** the defective request shape and the therefore-green 146/146 suite; Bangla-name search unverified (no such data). Includes the per-filter and per-view evidence matrices, four root-cause classes, minimal correction options with blast radius, and the two decisions left to the owner — **O-AA** (calendar branch scope) and **O-AB** (may a search leave the visible week). **Part I (2026-11-16)** records the resolution: both decisions taken, every finding F-1…F-9 mapped to the correction that shipped and to its evidence, and the one sentence defect the browser run of the fix caught | — |
| `AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` | 16,394 | MVP scope lock (25 KEEP / 1 DEFER) and Operational RBAC authorization hardening; six P0 defects fixed and regression-tested | — |

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
| `AMSDP_Demo_Credentials_V1.0.md` | 2,422 | Running or describing a demo login. Contains credentials — cite the file, never paste secrets into reports or logs | R |
| `AMSDP_Hackathon_Demo_Runbook.md` | 11,331 | Walking through the demo flow end to end | — |
| `AMSDP_Limitations_Report_V1.0.md` | 4,379 | Stating honestly what does not work — the canonical source for limitation claims | R |
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


