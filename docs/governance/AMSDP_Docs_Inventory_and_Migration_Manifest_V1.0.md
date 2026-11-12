# AMSDP — `ai_factory/docs/` Inventory and Documentation Migration Manifest

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10
> **Status:** migration executed and verified · **no commit, push, merge or deploy performed**
> **Governing rule:** `.clinerules` §11 *Documentation Output Location Policy* (installed by this task)
> **Companion report:** `docs/governance/AMSDP_Docs_Output_Policy_Verification_Report_V1.0.md`

---

## 1. Purpose and scope

This document is the inventory of `ai_factory/docs/` and the manifest of the
documentation migration performed on 2026-11-10. It records, for every file in
that directory: which class it belongs to, what happened to it, and — where
nothing happened — why not.

Scope is deliberately narrow:

- **In scope:** classification of the 47 files under `ai_factory/docs/`; the move
  of 20 confirmed Cline-generated AMSDP reports into `docs/`; the record of that
  move.
- **Out of scope:** editing any document's content, editing any Product
  Owner-controlled document, editing application source, committing anything.
  None of those occurred.

---

## 2. Method — how ownership was determined

No file in `ai_factory/docs/` was assumed to be agent-authored. Each of the 47
files was read at least at its header/metadata level and classified on evidence:

| Evidence used | What it establishes |
|---|---|
| Header metadata (`Date`, `Status`, `Milestone`, `Inspector`, `Authorized by`, `Tree`, `Mode`) | who produced the document and for what purpose |
| Presence of `Cline` in the body (per-file grep count) | explicit statement of the producing agent |
| Report structure (IMPLEMENTED/TESTED/VERIFIED claims, milestone IDs, sequence IDs, "no commit was performed" clauses) | agent-produced milestone-report form |
| Subject matter (AMSDP product vs. AI-Factory tooling internals) | whether the file belongs to the AMSDP document set at all |
| Path bindings in code (`workflows/engine.py:600`, `tests/unit/test_agent_rules.py:33`) | files whose location is load-bearing and must not change |
| `git status --porcelain` | provenance: every report file is an untracked working-tree artefact |

Where the evidence was insufficient to assign a file to the AMSDP document set,
it was **retained in place and reported** (§3.5), never moved on assumption.


---

## 3. Inventory of `ai_factory/docs/` — 47 files

| Class | Meaning | Files | Action |
|---|---|---:|---|
| 1 | Cline-generated AMSDP reports eligible for migration | **20** | migrated to `docs/` (§5) |
| 2 | Agent rules / configuration that must remain in place | **12** | retained — path-bound (§3.2) |
| 3 | Reference and supporting material for the `ai_factory` subsystem | **4** | retained (§3.3) |
| 4 | Product Owner-authored or controlled | **0** | none present (§3.4) |
| 5 | Ownership or purpose uncertain | **11** | retained and reported (§3.5) |
| | **Total** | **47** | **20 moved, 27 untouched** |

### 3.1 Class 1 — Cline-generated AMSDP reports (migrated, 20)

All 20 are milestone, sequence or assessment reports about the AMSDP product,
written by the coding agent in this workspace between 2026-11-07 and 2026-11-10.
None carries a human author field; each states its own status and, where
relevant, its own "no commit was performed" clause. Thirteen name Cline in the
body (`grep -ci cline`): `AMSDP_ALL_SEQUENCES_FINAL_SUMMARY` (21),
`AMSDP_Engineering_Governance_Assessment` (31), `AMSDP_Skill_Routing_Architecture`
(15), `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT` (9), `AMSDP_SEQ_04` (6),
`AMSDP_M7` (5), `AMSDP_SEQ_03_COMPLETION` (4),
`AMSDP_UI_UX_and_Reusable_Components_Assessment` (4), `AMSDP_SEQ_02` (2),
`AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT` (2), `AMSDP_M6_Implementation_Plan` (1),
`AMSDP_M6_Implementation_Report` (1), `AMSDP_M8` (1), `AMSDP_M9` (1).

The remaining six — `AMSDP_M2_Security_Implementation_Report`,
`AMSDP_M4_Appointment_Implementation_Report`,
`AMSDP_M5_Queue_Implementation_Report`,
`AMSDP_MVP_Hackathon_Readiness_Assessment`,
`AMSDP_Frontend_Visual_Quality_Investigation`, `AMSDP_Hackathon_Demo_Runbook` —
are the milestone reports for M2–M5 and the readiness/demo artefacts of the same
engagement: same report form, same directory, same untracked provenance, no
human author field. They are the class of document that the pre-migration
`.clinerules` §5 itself described as "milestone implementation reports
(`ai_factory/docs/AMSDP_M*`)".

### 3.2 Class 2 — must remain (12 files, untouched)

`ai_factory/docs/agent-rules/` — 11 markdown rule documents plus
`MANIFEST.json`. These are **load-bearing configuration**, not reports:

- `workflows/engine.py:600` builds its rule search path from
  `repo_root/ai_factory/docs/agent-rules`;
- `tests/unit/test_agent_rules.py:33` hard-codes
  `RULES_DIR = /home/shomonrobie/amsdp/ai_factory/docs/agent-rules`;
- the library's integrity is asserted against `MANIFEST.json` SHA-256 entries, so
  relocating the files would break both the engine and the hash manifest.

Moving these was never a candidate; `.clinerules` §11 records that the directory
must not be relocated.

### 3.3 Class 3 — reference and supporting material (4 files, untouched)

| File | What it is | Why retained |
|---|---|---|
| `architecture.md` | Living ADR record for the `ai_factory` package (ADR-AF-001 …) | Documents the tool that produces AMSDP reports; its authority map is bound to `ai_factory` source paths |
| `operations.md` | AI Factory setup/CLI runbook (`task-new`, `run-workflow`, `approve`, …) | Operational documentation of the tool, not an AMSDP product report |
| `permissions.md` | `ai_factory` tool-registry permission model | Describes `tools/tool_registry.py` behaviour; belongs beside the source |
| `workflows.md` | The ten registered `ai_factory` workflows | Describes `workflows/registry.py`; belongs beside the source |

These four are the AI Factory's own living documentation, written in the present
tense as a description of the current tool. Filing them under `docs/` beside
AMSDP product documents would misrepresent them as AMSDP deliverables.

### 3.4 Class 4 — Product Owner-controlled documents (0 present in this directory)

**Discrepancy reported, not resolved by assumption.** This task named
`ai_factory/docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` as a
Product Owner-controlled file. No such file exists: `ls ai_factory/docs | grep -i master`
returns nothing. The V2.3 Master Feature List — and V2.0, V2.1, V2.2 — exist at
the **`docs/` root** (`docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md`).

Consequences, all handled conservatively:

- No owner-controlled document existed inside `ai_factory/docs/`, so none was
  moved or touched there.
- The `docs/` copies were **not** touched either:
  `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` remains an uncommitted
  modification exactly as found, and V2.1/V2.2/V2.3 remain untracked additions
  exactly as found (`git status` evidence in the companion report §4).
- `.clinerules` §11 now lists the four Master Feature List files at their **real**
  paths, plus the other owner-controlled families, so the protection is anchored
  to the truth rather than to the stale path in the task brief.

### 3.5 Class 5 — ownership or purpose uncertain (11 files, untouched)

`AILI_Agent_Rules_Independent_Verification_Report_V1.0.md`,
`AILI_Agent_Rules_Integration_Report_V1.0.md`,
`AILI_Autonomous_Development_Restoration_Plan_V1.0.md`,
`AILI_CrewAI_Execution_Architecture_and_Verification_Report_V1.0.md`,
`AILI_Independent_Verification_Report_V2.0.0.md`,
`AILI_LiveRun_Verification_Report_V1.0.md`,
`AILI_M1M4_ReadOnly_Inspection_Implementation_Report_V1.0.md`,
`AILI_Operational_HOWTO_Submit_Independent_Project_V1.0.md`,
`AILI_Phase4_Repair_and_Assessment_Report_V1.0.md`,
`AILI_ReadOnly_Inspection_Assessment_Capability_Verification_V1.0.md`,
`AILI_Structured_Output_Investigation_Report_V1.0.md`.

Evidence that these are **not** Cline's AMSDP reports, and why they were left:

1. Their subject is the AI Factory (AILI) subsystem itself — CrewAI execution,
   the tool registry's default-deny model, structured-output compatibility, the
   run recorder, agent-rules integration. They are not AMSDP product reports.
2. Several state their producer explicitly in the header: "**Inspector:** AILI
   Agent Rules Read-Only Verification" (`AILI_Agent_Rules_Independent_Verification_Report_V1.0`),
   "**Inspector:** AILI Agent Rules Repair & Assessment"
   (`AILI_Phase4_Repair_and_Assessment_Report_V1.0`), "**Inspector:** AILI
   Structured-Output Compatibility Investigation"
   (`AILI_Structured_Output_Investigation_Report_V1.0`). The producing system is
   AILI, not the coding agent — so "Cline-generated" is not established.
3. One of them verifies a working artifact
   (`AILI_Independent_Verification_Report_V2.0.0` inspects
   `var/workspaces/AMSDP-000003/requirement_analysis_v2.0.0.json`), tying it to
   AILI run state rather than to AMSDP deliverables.
4. `AILI_Operational_HOWTO_Submit_Independent_Project_V1.0` is an operator
   reference for driving AILI directly.

Per the task's own rule — *do not assume every file in this directory was created
by Cline; leave uncertain files untouched and report them* — these 11 remain in
`ai_factory/docs/`. **Open owner decision O-1 (§8)** records the possible future
move.

---

## 4. Destination rationale

Destinations reused existing `docs/` folders wherever one fit; five folders were
created because no equivalent existed (`docs/` previously held no `audit/`,
`implementation/`, `deployment/`, `security/` or `governance/` folder).

| Destination | Files | Rule applied |
|---|---:|---|
| `docs/audit/` | 4 | Final summaries, readiness assessments and acceptance-verification reports — evidence about what was accepted at a point in time, not how anything is built |
| `docs/governance/` | 2 | The two documents `.clinerules` cites as governance authority (routing assessment, skill-routing architecture) — they must sit where §11 and §10 now point |
| `docs/implementation/` | 9 | Milestone (M4–M6) and sequence (SEQ-02/03) implementation reports plus the two frontend/UI implementation investigations |
| `docs/deployment/` | 2 | Cloud deployment architecture and the post-SEQ4 deployment hardening report |
| `docs/security/` | 1 | M2 security implementation report |
| `docs/product/` | 1 | M9 implementation readiness assessment — product-facing readiness, filed with the product set it assesses |
| `docs/demo/` | 1 | Hackathon demo runbook — joins the existing demo artefacts (`Limitations_Report`, `Demo_Credentials`, `API_Integration_Report`) |
| | **20** | |

`docs/audit/` vs `docs/implementation/` was the only genuinely contested split:
milestone implementation reports state *what was built and how it was tested*
(`docs/implementation/`), while readiness assessments and final summaries state
*what was accepted and what remains* (`docs/audit/`). `AMSDP_M9_Implementation_Readiness_Assessment`
went to `docs/product/` rather than `docs/audit/` because its subject is product
scope readiness, not acceptance of a delivered sequence.

---

## 5. Migration manifest — 20 entries, 2026-11-10

Original path for every row is `ai_factory/docs/<File name>`. Content was moved
byte-for-byte: no file was edited, renamed or reformatted during the move. The
SHA-256 prefix below is the **post-move** hash of the destination file; it was
also computed **before** the move on the source file, and all 20 pairs matched
(§9).

| # | File name | Destination folder | Bytes | SHA-256 (first 16) |
|---:|---|---|---:|---|
| 1 | `AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` | `docs/audit/` | 77,893 | `6cd608fb37146242` |
| 2 | `AMSDP_MVP_Hackathon_Readiness_Assessment.md` | `docs/audit/` | 8,695 | `23d74c39988d18ce` |
| 3 | `AMSDP_M7_Hackathon_Readiness_Report.md` | `docs/audit/` | 21,936 | `115f30362df5d99b` |
| 4 | `AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` | `docs/audit/` | 23,408 | `5d85391011213cc5` |
| 5 | `AMSDP_Engineering_Governance_Assessment.md` | `docs/governance/` | 25,638 | `8a1fa092df7da3a2` |
| 6 | `AMSDP_Skill_Routing_Architecture.md` | `docs/governance/` | 5,839 | `e4af1c63a44c658d` |
| 7 | `AMSDP_M4_Appointment_Implementation_Report.md` | `docs/implementation/` | 4,374 | `860f6cd6dce77d2e` |
| 8 | `AMSDP_M5_Queue_Implementation_Report.md` | `docs/implementation/` | 5,570 | `6292704e9802da11` |
| 9 | `AMSDP_M6_Implementation_Plan.md` | `docs/implementation/` | 6,777 | `f4b2e50698ed8f99` |
| 10 | `AMSDP_M6_Implementation_Report.md` | `docs/implementation/` | 6,753 | `3217c5de207aecf8` |
| 11 | `AMSDP_SEQ_02_COMPLETION_REPORT.md` | `docs/implementation/` | 21,344 | `157c91e3c5153d3d` |
| 12 | `AMSDP_SEQ_03_COMPLETION_REPORT.md` | `docs/implementation/` | 30,485 | `56611b4c9d09401d` |
| 13 | `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` | `docs/implementation/` | 15,328 | `f0e70606f2604ba0` |
| 14 | `AMSDP_Frontend_Visual_Quality_Investigation.md` | `docs/implementation/` | 3,442 | `4371609af6a6f3f9` |
| 15 | `AMSDP_UI_UX_and_Reusable_Components_Assessment.md` | `docs/implementation/` | 6,305 | `3fcfdbc9c8625717` |
| 16 | `AMSDP_M8_Cloud_Deployment_Architecture.md` | `docs/deployment/` | 29,056 | `37a5ee7e84caae66` |
| 17 | `AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` | `docs/deployment/` | 43,275 | `688597ca3760cc7e` |
| 18 | `AMSDP_M2_Security_Implementation_Report.md` | `docs/security/` | 6,374 | `2bd35d37c2e58506` |
| 19 | `AMSDP_M9_Implementation_Readiness_Assessment.md` | `docs/product/` | 33,874 | `c99fd3211f6b5eb2` |
| 20 | `AMSDP_Hackathon_Demo_Runbook.md` | `docs/demo/` | 11,336 | `3ec65977a351434d` |
| | **Total moved** | | **387,702** | |

---

## 6. Files retained in `ai_factory/docs/` and why (27)

### 6.1 Agent rules and configuration — 12 files, no reason to move any

| File | Why retained |
|---|---|
| `agent-rules/README.md` | Rule-library index; path-bound by `tests/unit/test_agent_rules.py` |
| `agent-rules/MANIFEST.json` | SHA-256 integrity manifest for the rule library; relocating it invalidates every recorded path |
| `agent-rules/carbontally-agent-governance.md` | CarbonTally governance source — adaptation input for `.clinerules` §1.4 |
| `agent-rules/emissions-provenance.md` | CarbonTally rules; adapt-only material |
| `agent-rules/saas-ai-provider-registry.md` | Loaded from the `ai_factory` rule search path |
| `agent-rules/saas-api-throttling.md` | ditto |
| `agent-rules/saas-application-security.md` | ditto — cited by `.clinerules` §4 for backend/API work |
| `agent-rules/saas-auth-and-authorisation.md` | ditto — cited for auth/RBAC work |
| `agent-rules/saas-cicd-workflow.md` | ditto — cited for migration/deployment work |
| `agent-rules/saas-frontend-ux.md` | ditto — cited for frontend work |
| `agent-rules/saas-multitenant-data.md` | ditto — cited for multi-tenant/DB work |
| `agent-rules/saas-observability.md` | ditto — cited for audit/observability work |

### 6.2 `ai_factory` subsystem reference documents — 4 files

`architecture.md`, `operations.md`, `permissions.md`, `workflows.md` — reasons in
§3.3.

### 6.3 AILI programme reports — 11 files

Reasons in §3.5; the file list is reproduced there.

**Directory state after the migration:** 15 markdown files plus `agent-rules/`
(12 files) = 27 files — 12 load-bearing rules/configuration, 4 AI-Factory
reference documents, 11 AILI reports awaiting owner decision O-1.

---

## 7. Resulting `docs/` map (AMSDP document set)

```
docs/
├── AMSDP — E-Health Hackathon Concept Note & Application Summary.md   [owner]
├── AMSDP_Business_Rules_V1.1.md                                       [owner]
├── AMSDP_MVP_SCOPE_V1.1.md                                            [owner]
├── AMSDP_Master_Feature_List_V2.0_Draft.md                            [owner]
├── AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md               [owner]
├── AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md               [owner]
├── AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md               [owner]
├── AMSDP_Complete_ASCII_UI_UX_Blueprint.md                            [owner]
├── AMSDP_UI_UX_Blueprint_Structured_Assessment_V1.0.md
├── architecture/     5 files  (incl. AMSDP_System_Architecture_V1.0.md [owner])
├── audit/            6 files  ← 4 migrated + 2 relocated from the repository root (O-6)
├── decisions/        0 files  (empty folder, untouched)
├── demo/             4 files  ← 1 migrated + 3 pre-existing
├── deployment/       2 files  ← migrated (folder created)
├── governance/       6 files  ← 2 migrated + manifest + companion report + navigation index + O-1…O-6 report (folder created)
├── implementation/   9 files  ← migrated (folder created)
├── product/          6 files  ← 1 migrated + 5 pre-existing
└── security/         1 file   ← migrated (folder created)
```

`docs/operations/` and `docs/testing/` do not exist yet. They are named in
`.clinerules` §11 as permitted locations and will be created only when a document
needs to live there — no empty scaffolding was added.

---

## 8. Conflicts, uncertainties and open decisions

**C-1 — Task brief path error (reported, handled).** The brief located the
Product Owner-controlled V2.3 Master Feature List at
`ai_factory/docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md`. No such
file exists; the real file is
`docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md`, and it was not
touched. `.clinerules` §11 lists the real paths.

**C-2 — Migrated documents still cite pre-migration paths.** 10 of the 20 moved
documents contain 36 occurrences of `ai_factory/docs/…` in their bodies
(`docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` 14,
`docs/governance/AMSDP_Engineering_Governance_Assessment.md` 5,
`docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md` 4,
`docs/implementation/AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` 3,
`docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` 2,
`docs/implementation/AMSDP_SEQ_03_COMPLETION_REPORT.md` 2,
`docs/implementation/AMSDP_M6_Implementation_Plan.md` 2,
`docs/deployment/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` 2,
`docs/governance/AMSDP_Skill_Routing_Architecture.md` 1,
`docs/demo/AMSDP_Hackathon_Demo_Runbook.md` 1). These are stale cross-references,
several pointing at files that are no longer at those paths. They were
**deliberately not rewritten**: the task requires original contents to be
preserved and forbids editing document content. Registered in the companion
report §6 for a separate, authorized cleanup.

**C-3 — Two code paths still name `ai_factory/docs/AMSDP_*`.**
`ai_factory/verify_llm_routing.py` and files under `_tools/` reference AMSDP
report paths in `ai_factory/docs/`. Not edited — the task forbids source edits.
Registered, unresolved.

**O-1 — AILI reports (owner decision requested).** Should the 11 `AILI_*`
documents stay in `ai_factory/docs/` as AI-Factory programme records (current
state), or move to a new `docs/ai_factory/`? They were left in place because
class-5 ownership could not be established to the standard required to move them.

**O-2 — Stale cross-reference cleanup (owner decision requested).** Authorize a
separate pass to rewrite the 36 stale `ai_factory/docs/…` references inside the
migrated documents, or leave them as historical record.

**O-3 — `docs/audit/` vs `docs/implementation/` split (informational).** Confirm
the split applied in §4, or request a merge.

---

## 9. Verification of the migration

| Check | Method | Result |
|---|---|---|
| Sources present before move | pre-flight loop over all 20 pairs | 20/20 present |
| Destination collisions | `[ -e "$d" ]` per pair | **0 collisions** |
| Destination folders | `mkdir -p`, then `mv -n` (no-clobber) | 5 created, 2 reused |
| Move outcome | per-pair exit status | **20 moved, 0 failed** |
| Content preserved | SHA-256 of source **before** move vs. destination **after** move | **20/20 identical** |
| Source residue | `[ -e "$s" ]` after move | **0 residue** |
| Untouched files unchanged | SHA-256 of every retained file, before vs. after | **0 changed** |
| Byte total | `wc -c` over the 20 destinations | 387,702 bytes |
| Directory state | `ls`, `find -type f` | `ai_factory/docs` = 15 md + 12 rule files |
| Working-tree scope | `git status --porcelain` before/after | 20 report entries removed, 7 `docs/` entries added, **no tracked file modified by this task** |
| Commit / push / deploy | none executed | confirmed (§10) |

Every row above was produced by a shell command run against the live tree; none
is asserted from memory.

---

## 10. What this manifest does not authorize

This document records a documentation move. It does **not** authorize — and no
step of it performed — any of the following: editing document content; editing
product, business-rules, MVP-scope, feature-list or architecture documents;
deleting any version; editing application source (`backend/`, `frontend/`,
`ai_factory/src`, `docker-compose*`); modifying `agent-rules/`; creating a branch,
commit, merge, push or deployment; or touching any Product Owner-controlled file.
Content changes to any migrated document remain a separate, owner-authorized act.




---

## 11. Owner decisions O-1–O-6 — outcomes and second relocation (2026-11-10)

Task: `AMSDP-DOC-GOVERNANCE-OWNER-DECISIONS-O1-O6-2026-11-10`. The Product Owner
resolved the six open decisions recorded in §8. Outcomes:

| ID | Owner decision | What this task did |
|---|---|---|
| **O-1** | Keep the 11 `AILI_*` reports in `ai_factory/docs/` — they document the AI Factory/AILI subsystem, not AMSDP deliverables | No file moved, renamed or rewritten. `ai_factory/docs/` AILI retention registered in `.clinerules` §11 and in `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| **O-2** | Authorize correction of the 36 stale `ai_factory/docs/…` references inside the migrated documents | 26 path-only corrections in 8 documents; 10 references deliberately left (agent-rules paths still valid; recorded command output / changelog evidence). Register in `docs/governance/AMSDP_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md` §4 |
| **O-3** | Authorize bounded correction of obsolete report paths in `ai_factory/verify_llm_routing.py` and `_tools/` | `ai_factory/verify_llm_routing.py` **does not exist** and `_tools/` holds no report paths — §8's O-3 description was inaccurate; nothing to change. One genuine stale locator in `backend/tests/test_sequence3.py` (docstring only) corrected |
| **O-4** | Confirm: `docs/audit/` = acceptance/readiness/verification evidence; `docs/implementation/` = milestone and sequence implementation reports | Classification confirmed unchanged; no document moved between the two folders |
| **O-5** | Confirm §11 owner-document protection at the real paths (V2.3 feature list is at `docs/`, not `ai_factory/docs/`) | No protected document touched. Two over-broad **R** flags in the index (Engineering Governance Assessment, Skill Routing Architecture — neither is in the §11 protected set) corrected to **—** |
| **O-6** | Relocate the two repository-root release-readiness documents into `docs/audit/` | Executed — entries in §11.1 |

### 11.1 Relocation manifest — 2 entries, 2026-11-10

Contents preserved byte-for-byte; SHA-256 identical before and after, and the
worktree blob hash of each destination equals the blob hash recorded for the
source in `HEAD` — so a later commit records a pure rename (100 % similarity).

| # | Original path | Destination path | Date | Reason | SHA-256 (before = after) |
|--:|---|---|---|---|---|
| 1 | `AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md` (repo root) | `docs/audit/AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md` | 2026-11-10 | O-6: `.clinerules` §11 requires AMSDP documents under `docs/`; audit/ is the confirmed home for readiness assessments (O-4) | `3b4f60226b23f766468502d5f780d701341c741a6f1d6409a87acd0d8727f28f` |
| 2 | `AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md` (repo root) | `docs/audit/AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md` | 2026-11-10 | Same | `3813d62551d13c762e0d4641c9756bb36ccb113b54b594e74d4093476ed6249e` |

Git blob hashes: entry 1 `1056b96571c2e5c845a8521370b1ef40e74d569c`,
entry 2 `487389cb3b18ff42d58095208e596a5eac88631c` — both equal to
`git rev-parse HEAD:<original path>`. No destination collision existed
(`docs/audit/` did not contain either filename). Nothing was staged, committed,
pushed or deployed.

After this relocation **no AMSDP document lives outside `docs/`**. The §7 map is
kept as the snapshot taken at migration time; the live map is
`docs/governance/AMSDP_Docs_Index_V1.0.md`, which is authoritative for the
current tree.

