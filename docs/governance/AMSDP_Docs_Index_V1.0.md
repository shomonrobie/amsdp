# AMSDP — Documentation Index (navigation)

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10 (revised 2026-11-11) · **Snapshot:** 56 markdown documents, ≈1.97 MiB total (per-file sizes below; recompute with the *Maintenance* command)
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
| `decisions/` | What was decided and why? | Any ADR-style decision record (currently empty) |
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

---

## `deployment/` — delivery and hardening

| File | Size | Read when | Owner |
|---|---:|---|---|
| `AMSDP_M8_Cloud_Deployment_Architecture.md` | 29,056 | Any Docker/compose/port/environment change | — |
| `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | 43,270 | Infra hardening, restart policy, health checks, container limits | — |

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


