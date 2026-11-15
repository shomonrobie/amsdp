# AMSDP — Documentation Index (navigation)

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10 (revised 2026-11-15) · **Snapshot:** 69 markdown documents (per-file sizes below; recompute with the *Maintenance* command)
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
> `frontend/tests/facility-doctor.test.mjs` (21 tests, including JSX compilation of the three
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
> doctor `bmdc_*` columns and the appointment chamber-snapshot columns. **Not verified and
> recorded as open items:** no browser session was used (report §7.1) and the backend suite
> was not re-run because no backend file changed in this phase (§7.2). No document was moved,
> renamed or deleted, so no manifest entry is due; nothing was staged or committed.

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
| `architecture/` | How is the system and the AI tooling structured? | Service boundaries, data model, agent roles, AI Factory internals, dev workflow |
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
| `AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` | 20,982 | Appointment booking UI, the week/day calendar grid, `lib/calendar/grid.js`, slot capacity, the `date_from`/`date_to` window on `GET /api/v1/appointments`, or how the component's markup is asserted without a browser (§7.4) | — |
| `AMSDP_Facility_Doctor_Frontend_Implementation_Report_V1.0.md` | 15,455 | Doctor Management (`/doctors`), chamber assignment (`/schedules`), the facility tree (`/facilities`), `lib/phone.js`, `lib/facility.js`, BMDC verification UI, or why a conflicting session is warned about client-side but still decided by the server | — |

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

---

## `deployment/` — delivery and hardening

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_M8_Cloud_Deployment_Architecture.md` | 29,056 | Any Docker/compose/port/environment change | — |
| `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | 43,270 | Infra hardening, restart policy, health checks, container limits | — |
| `AMSDP_Auto_Start_and_Demo_Data_Recovery_V1.0.md` | 16,196 | **Before restarting, reseeding, rebooting or re-diagnosing the local stack** — why two containers could not reach each other across the Docker bridge and the network-recreate fix (no `sudo`, no `ufw` change); the two auto-restart layers (`restart: unless-stopped` ×10 and the systemd user unit `amsdp-autostart.service`) and how they supersede the earlier deferral; the `/orgs` SSR fix; the new `_tools/` scripts (`amsdp_autostart.sh`, `install_autostart.sh`, `verify_demo_login.sh`); the live evidence (10/10 healthy, **6/6 demo logins**, 10/10 pages 200, `restarts=7`, data counts identical); and the open items **O-J**/**O-K**/**O-L**, plus carried **O-H**/**O-I** and new **O-M** | — |

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

## `chatgpt/` — one unregistered document, folder ownership unconfirmed (open item O-D)

`find docs -type f -name '*.md'` reports one document in a folder that is **not** among the §11
subject folders. It is registered here so the index matches the tree (§12), but it is **not** moved
and its ownership is not asserted (§11: uncertain ownership → report and leave in place).

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_Hackathon_Implementation_Backlog.md` | 24,229 | Needing the backlog framing that accompanied the 2026-11-14 reconciliation commit — a planning document, **not** an authority: business rules, MVP scope and the frozen design still govern (§1) | unconfirmed — folder outside the §11 set |

Open item: whether `docs/chatgpt/` should be folded into an existing subject folder (`audit/` or
`governance/`) is the Product Owner's decision. Until then the file stays exactly where it is, and
no agent may treat `docs/chatgpt/` as an approved output location (§11).

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


