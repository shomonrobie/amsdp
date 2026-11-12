# AMSDP — Documentation Output Location Policy: Verification Report

> **Task ID:** `AMSDP-DOC-GOVERNANCE-OUTPUT-LOCATION-2026-11-10`
> **Date:** 2026-11-10
> **Status:** policy installed in `.clinerules` §11 · migration verified · **no commit, push, merge or deploy performed**
> **Companion manifest:** `docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md`

---

## 1. What this report verifies

1. That `.clinerules` now contains a permanent, self-explanatory rule fixing the
   single authoritative output location for AMSDP documents, and that §1–§10
   survive the edit intact.
2. That new AMSDP reports created by this task respect the installed policy.
3. That the 20 migrated reports arrived byte-for-byte intact and that nothing
   else in the tree moved.
4. That every Product Owner-controlled document is untouched.
5. That nothing was committed, staged, pushed, merged or deployed, and that all
   pre-existing uncommitted work is preserved.

---

## 2. The installed rule

**Location:** `.clinerules`, section `## 11. Documentation Output Location Policy
(single authoritative docs tree)`, lines 112–121 (file now 121 lines; the file
was 110 lines before).

The section states, in full:

| Element | Rule installed |
|---|---|
| Authoritative location | Every AMSDP document/report/assessment/runbook/plan/manifest is written under `/home/shomonrobie/amsdp/docs/`, in the matching subfolder (`audit/`, `architecture/`, `product/`, `governance/`, `implementation/`, `testing/`, `deployment/`, `security/`, `operations/`, `demo/`, `decisions/`); reuse before creating; no near-duplicate folders |
| `ai_factory/docs/` | Accepts **no new AMSDP reports**; holds only `agent-rules/` (path-bound by `workflows/engine.py` and `tests/unit/test_agent_rules.py`) and AI-Factory/AILI subsystem documentation |
| Fallbacks | No fallback location: not `/tmp`, not the repository root, not any other directory |
| Preservation | Never overwrite an existing destination filename; never delete, consolidate away or "clean up" a historical version |
| Naming | `AMSDP_<Topic>_<Version>.md`, or the exact existing name when migrating |
| Migrations | Collision check + byte-for-byte preservation (SHA-256 before/after) + a manifest under `docs/governance/` recording original path, destination, date, reason; content is not rewritten during a move; uncertain files are reported and left in place |
| Owner-controlled files | Read-only — read and cite, never modified, moved, renamed or overwritten without explicit Product Owner approval for that specific act; named at their **real** paths (V2.0/V2.1/V2.2/V2.3 feature lists, Business Rules, MVP scope, product decisions, system architecture, ASCII UI/UX blueprint, concept note, demo limitations + credentials) |
| Additivity | Additional to §1–§10; relaxes nothing; §1 precedence, §3 non-negotiables, §6 compliance reporting, §7 evidence standard, §9 boundaries and the agent-rules library all continue to apply; every report must state where it was written and cite the manifest if it involved a migration |

### 2.1 §1–§10 preserved — only three path corrections

The edit was additive plus three path corrections, all of them repairs of
references that the migration made stale. Nothing else in §1–§10 changed:

| Line | Before | After |
|---|---|---|
| 12 | `ai_factory/docs/AMSDP_Engineering_Governance_Assessment.md` | `docs/governance/AMSDP_Engineering_Governance_Assessment.md` |
| 70 | reports at `ai_factory/docs/AMSDP_M*`; governance docs at `ai_factory/docs/…` | reports at `docs/implementation/AMSDP_M*`, `docs/implementation/AMSDP_SEQ_*`; governance docs at `docs/governance/…` |
| 108–109 | governance assessment + skill routing architecture at `ai_factory/docs/…` | both at `docs/governance/…` |

Verified mechanically: all eleven section headings are present and in order
(`1.` … `11.`, lines 8/19/37/50/67/74/83/91/96/104/112), and the only remaining
`ai_factory/docs` references in the file are the three that **must** stay — the
agent-rules path at line 13, the agent-rules index entry at line 110, and the
statement in §11 that the rule library is not to be relocated.

---

## 3. Policy conformance of documents created by this task

| Document | Written to | Conforms |
|---|---|---|
| `AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` | `docs/governance/` | ✔ existing authoritative folder, no fallback used |
| `AMSDP_Docs_Output_Policy_Verification_Report_V1.0.md` (this file) | `docs/governance/` | ✔ |
| Nothing else was created | — | ✔ no file written to `/tmp` as a deliverable (scratch command output only), none to the repo root, none to `ai_factory/docs/` |

Both filenames follow `AMSDP_<Topic>_<Version>.md`; neither overwrote an existing
file (the collision pre-check confirmed both paths were free).

---

## 4. Product Owner-controlled documents — untouched

Evidence is `git status --porcelain` captured before and after the migration and
compared byte-for-byte on the tracked-modification list.

| Owner document (real path) | State before | State after | Changed by this task |
|---|---|---|---|
| `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` | ` M` | ` M` | **No** |
| `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` | ` M` | ` M` | **No** |
| `docs/AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md` | `??` | `??` | **No** |
| `docs/AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md` | `??` | `??` | **No** |
| `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` | `??` | `??` | **No** |
| `docs/AMSDP_Business_Rules_V1.1.md` | `??` | `??` | **No** |
| `docs/AMSDP_MVP_SCOPE_V1.1.md` | `??` | `??` | **No** |
| `docs/architecture/AMSDP_System_Architecture_V1.0.md` | ` M` | ` M` | **No** |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | ` M` | ` M` | **No** |
| `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` | (tracked, clean) | (tracked, clean) | **No** |
| `docs/product/*` (Business Rules V1.0, MVP scope V1.0, revision proposal, PQV decision, positioning) | unchanged | unchanged | **No** |

The comparison is strengthened by the whole-tree check in §5: the tracked
modification list is **identical line-for-line** before and after, so no tracked
owner document can have been touched, and the untracked set changed by exactly
the 20 moved report entries less the 7 new `docs/` entries.

**Note on the brief's path:** the brief placed the V2.3 Master Feature List under
`ai_factory/docs/`. It is at `docs/`, as shown above, and is untouched. `.clinerules`
§11 records the real path so the protection no longer depends on the wrong one.

---

## 5. Unrelated uncommitted work — preserved

`git status --porcelain`, before vs. after:

| Measure | Before | After | Reconciliation |
|---|---:|---:|---|
| Total entries | 128 | 115 | −13 |
| Tracked modifications (` M`) | 56 | 56 | **identical list** (`diff` → no output) |
| Untracked (`??`) | 72 | 59 | −20 moved report entries, +7 new `docs/` entries = −13 |

The 56 tracked modifications — `README.md`, 20 files under `backend/`
(appointment, audit, doctor, identity, organization, patient, queuing,
scheduling, e2e), `ai_factory` build-crews/live/test-live-executor,
`docker-compose.yml`, 8 frontend pages + `next.config.js` + `global.css`, and the
four `docs/` owner files — are the same 56 before and after. No unrelated work was
disturbed, reverted, stashed or reformatted. Nothing was staged, so nothing was
mis-attributed to this task.

---

## 6. Stale reference register (found, not fixed)

Two classes of stale reference to the old path were found and deliberately left
in place; fixing them requires editing content or source, which this task forbids.

**R-1 — inside migrated documents (36 occurrences, 10 files).** Body-text
cross-references such as `ai_factory/docs/AMSDP_Hackathon_Demo_Runbook.md`
(8 occurrences across the tree), `…/AMSDP_SEQ_02_COMPLETION_REPORT.md` (4),
`…/AMSDP_M9_Implementation_Readiness_Assessment.md` (4),
`…/AMSDP_SEQ_04_ACCEPTANCE_VERIFICATION_REPORT.md` (3),
`…/AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` (3),
`…/AMSDP_SEQ_03_COMPLETION_REPORT.md` (3),
`…/AMSDP_POST_SEQ4_DEPLOYMENT_HARDENING_REPORT.md` (3),
`…/AMSDP_M7_Hackathon_Readiness_Report.md` (3),
`…/AMSDP_M5_Queue_Implementation_Report.md` (3),
`…/AMSDP_MVP_Hackathon_Readiness_Assessment.md` (2),
`…/AMSDP_M8_Cloud_Deployment_Architecture.md` (2),
`…/AMSDP_M6_Implementation_Report.md` (2),
`…/AMSDP_M4_Appointment_Implementation_Report.md` (2),
`…/AMSDP_M2_Security_Implementation_Report.md` (2),
`…/AMSDP_UI_UX_and_Reusable_Components_Assessment.md` (1), plus bare
`ai_factory/docs/` references. These now point at paths that no longer hold the
file. They are historical records of where documents lived at the time of
writing; rewriting them is owner decision **O-2**.

**R-2 — inside code (2 files).** `ai_factory/verify_llm_routing.py` and files
under `_tools/` contain `ai_factory/docs/AMSDP_*` report paths. Not edited — source
edits were out of scope. Registered, unresolved.

Both registers are carried in the manifest (§8, C-2 and C-3).

---

## 7. Verification checklist — all executed against the live tree

| # | Check | Command basis | Result |
|---:|---|---|---|
| 1 | §11 present and complete | `grep -n '^## ' .clinerules` | present, last of eleven sections, lines 112–121 |
| 2 | §1–§10 intact | heading list + line-by-line read | all ten present, order unchanged, content unchanged except the three path corrections (§2.1) |
| 3 | No new AMSDP report written to `ai_factory/docs/` | `ls ai_factory/docs` | 15 md + `agent-rules/` — no additions |
| 4 | `agent-rules/` not touched | SHA-256 of all 12 files before/after | unchanged |
| 5 | `ai_factory/docs` reference material unchanged | SHA-256 (`architecture.md`, `operations.md`, `permissions.md`, `workflows.md`) | unchanged |
| 6 | All 20 reports present at destination | `wc -c`, `sha256sum` per file | 20/20 present, 387,702 bytes total |
| 7 | Content preserved through the move | source hash before vs. destination hash after | 20/20 identical |
| 8 | No source residue | existence test per source path | 0 residue |
| 9 | No destination overwritten | collision pre-check + `mv -n` | 0 collisions |
| 10 | Owner documents untouched | `git status` diff of the ` M` list | identical |
| 11 | Unrelated work preserved | `git status` before/after counts | 56 ` M` identical, `??` 72→59 reconciled exactly |
| 12 | No commit/stage/push/merge/deploy | no `git add`/`commit`/`push`, no container commands in this task | confirmed |
| 13 | No application source edited | `git status` ` M` list identical; no `backend/`/`frontend/`/`ai_factory/src` entry added | confirmed |
| 14 | Deliverables in the authoritative location | this file + manifest under `docs/governance/` | conforms to §11 |

---

## 8. Open items requiring the Product Owner

| ID | Item | Recommendation |
|---|---|---|
| **O-1** | 11 `AILI_*` reports left in `ai_factory/docs/` (ownership not established to the standard required to move them) | Decide whether they are AI-Factory programme records (stay) or should join `docs/` under a `docs/ai_factory/` folder |
| **O-2** | 36 stale `ai_factory/docs/…` cross-references inside the 20 migrated documents | Authorize a separate, content-editing pass — or keep as historical record |
| **O-3** | 2 code files still name `ai_factory/docs/AMSDP_*` (`ai_factory/verify_llm_routing.py`, `_tools/`) | Authorize a source-file fix in a separate task |
| **O-4** | `docs/audit/` vs `docs/implementation/` split for M7/M9/SEQ-04 style reports (manifest §4) | Confirm the split or request a merge |
| **O-5** | The brief's `ai_factory/docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` path does not exist; the real file is `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` | Confirm the §11 text (now naming the real path) is the intended protection scope |

---

## 9. Governance and Skill Compliance

Mandatory per `.clinerules` §6.

**Task domain routing (§4 table).** The task is documentation governance. §4 has
no row for documentation, so the nearest applicable rows were applied for their
spirit — *Audit / data integrity / reporting* (preservation and traceability of
records) and, for the migration mechanics, *Database schema, migrations, data
integrity* (verify before/after, forward-only, no ad-hoc mutation). Recorded
explicitly rather than silently skipped.

**Governing documents applied**

| Document | How it governed this task |
|---|---|
| `.clinerules` §1 precedence | Owner instruction over agent convention; verified runtime state over assumption — hence the pre-flight checks before any `mv` |
| `.clinerules` §3 non-negotiables | "Never claim a capability that is not verified"; audit records are append-only and never rewritten → documents preserved verbatim, no content rewrite |
| `.clinerules` §5 skills registry | The registry is empty in this workspace; no skill was used and none is claimed |
| `.clinerules` §6 compliance reporting | This section |
| `.clinerules` §7 evidence standard | Classification applied in §10 |
| `.clinerules` §9 execution boundaries | Only the authorized moves plus read-only inspection commands; no test suites, servers, installs or destructive git operations |
| `.clinerules` §10 document index | Updated to the post-migration paths |
| `docs/governance/AMSDP_Engineering_Governance_Assessment.md` (migrated) | Contained the pre-existing arrangement by which `.clinerules` §5 pointed at `ai_factory/docs/` for milestone reports — the stale pointer this task repairs in the rule text |
| `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md` | Read for scope boundaries only; a documentation move touches no business behaviour |

**Selected skills: none.** Verified — no `.clinerules/skills/`, no `.claude/skills/`
and no repository `skills/` directory exists in this workspace. No skill usage is
claimed.

**Verification performed, with real results:** the 14 checks in §7, each run as a
shell command against the live tree — 0 collisions, 20/20 hash match, 0 source
residue, 0 changed retained files, 56 ` M` entries identical, `??` 72→59 reconciled
exactly.

**Deviations and exceptions**

| ID | Deviation | Justification / handling |
|---|---|---|
| D-1 | The brief's owner-document path (`ai_factory/docs/…V2.3…`) does not exist | Reported as C-1/O-5; the rule names the real path; no missing file was invented |
| D-2 | 11 files left inside the directory the task targeted | Task rule: do not assume Cline authorship; uncertain files are reported, not moved (O-1) |
| D-3 | 36 stale internal references and 2 code references not repaired | Content/source edits were forbidden; registered as R-1/R-2 |
| D-4 | Shell commands executed although §9 asks not to run scripts unless requested | They were read-only inspection commands (`ls`, `find`, `grep`, `sha256sum`, `wc`, `git status`) required to satisfy task requirement E and the §3/§7 evidence standard. No server, test suite, install or state-changing command beyond the authorized `mkdir`/`mv` |

**Unresolved:** O-1 … O-5; registers R-1 and R-2.

---

## 10. Evidence classification (§7 standard)

| Claim | Class | Basis |
|---|---|---|
| `.clinerules` §11 exists and §1–§10 survive | **IMPLEMENTED + TESTED** | file edited; heading list and line ranges read back from disk |
| 20 reports moved and byte-identical | **VERIFIED** | two independent artefacts: SHA-256 source-before / destination-after pairs (20/20) and the `git status` entry reconciliation |
| Owner documents untouched | **VERIFIED** | independent artefact: `diff` of the ` M` list (no output) plus the per-file state table in §4 |
| Unrelated work preserved | **VERIFIED** | independent artefact: `git status` counts 128→115 with exact reconciliation, and untouched-file SHA-256 comparison |
| Policy successfully prevents future misplacement | **NOT CLAIMED** | a rule is an instruction, not an enforced gate; it is demonstrable only on the next report written under it. Not marked ACCEPTED — that is the owner's act |
| The 11 AILI files are correctly retained | **IMPLEMENTED (documented), not ACCEPTED** | a defensible decision, pending O-1 |

---

## 11. Statement of no deployment, commit or push

No `git add`, `git commit`, `git push`, `git merge`, branch creation, tag,
container start, image build or deployment occurred in this task. Every change is
an uncommitted working-tree change:

- modified in place: `.clinerules` (itself untracked)
- added (untracked): `docs/audit/` (4), `docs/governance/` (2 migrated + 2 authored
  by this task), `docs/implementation/` (9), `docs/deployment/` (2),
  `docs/security/` (1), `docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md`,
  `docs/demo/AMSDP_Hackathon_Demo_Runbook.md`
- removed (untracked): the 20 `ai_factory/docs/AMSDP_*.md` sources, by move

**Documents created by this task, and where**

| Document | Path | Reason |
|---|---|---|
| Inventory + migration manifest | `docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` | §11 requires a manifest for any migration |
| This verification report | `docs/governance/AMSDP_Docs_Output_Policy_Verification_Report_V1.0.md` | §6 requires a compliance report with every delivery |

---

## 12. Addendum — documentation retrieval policy (same task, second pass)

Owner request: *configure the agent to read the relevant `docs/` material itself
and to place its own reports in the right folder, without being reminded every
prompt.* The writing half was already §11; the **reading** half did not exist and
was added.

**What was added**

| Artefact | Contents |
|---|---|
| `.clinerules` §2, step 3 (new) | Task routing now begins by reading the docs index; steps renumbered 1–11, and step 11 now obliges the agent to choose the report folder itself |
| `.clinerules` §4, new row | *Documentation: reading project docs, writing reports, doc placement or migration* → §12 + §11 + index + manifest |
| `.clinerules` §10 | Index and manifest registered in the governance document index |
| `.clinerules` §12 (new section) | Nine rules: read the index unsolicited before planning; locate by pattern not guess; cite only documents actually opened; read-only ≠ never-read; source-of-truth order while reading; context discipline for large files; credentials never travel; keep the index current in the same task; never ask the owner where to write or what to read |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` (new) | 12-folder subject map, per-document *Read when* cues with sizes and owner flags, version-pair note (Rules V1.1/V1.0, MVP V1.1/V1.0), legacy out-of-tree register, maintenance obligations and a read-only refresh command |

**Verification of the addendum (executed against the live tree)**

| Check | Result |
|---|---|
| `.clinerules` headings, order, count | §1–§12 present, in order, file 137 lines |
| Every `docs/` markdown file appears in the index | 45 tree files, 45 matched — **0 missing** (`comm -23` empty, `LC_ALL=C`) |
| Index lists nothing that does not exist | only 2 extra entries, both the real repo-root legacy files, labelled as such |
| Table integrity | pipe-count distribution: 14 rows × 4 columns (folder map) and 67 rows × 5 columns (file tables) — no malformed rows after fixing one note that had been placed inside a table row |
| Tracked files modified | none — `git status` still 59 `??` + 56 ` M` |

**Not claimed:** that the agent *will* obey §12 on every future task. A rule is an
instruction, not an enforced gate; it becomes demonstrable on the next task that
uses it.

**New open item**

| ID | Item | Why it needs the owner |
|---|---|---|
| **O-6** | Two tracked, committed AMSDP documents still sit at the repository root: `AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md`, `AMSDP_Release_Readiness_Stage_1_Detailed_Review_V1.0.md` | They predate §11 and violate its location rule, but moving **tracked** files changes committed history-level state, so it needs explicit approval and a manifest entry; they are registered in the index meanwhile |





---

## 13. Addendum — owner decisions O-1…O-6 resolved (later task, same day)

> Appended 2026-11-10 by task `AMSDP-DOC-GOVERNANCE-OWNER-DECISIONS-O1-O6-2026-11-10`.
> Nothing above this section was rewritten; this is a dated status note so a reader
> does not act on superseded open items.

| Item | Status now |
|---|---|
| **O-1** AILI reports | **Closed** — owner decided *keep in place*; nothing moved. Registered in `.clinerules` §11 and in `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| **O-2** 36 stale references | **Closed** — 26 corrected (path-only), 10 deliberately left as evidence / still-valid paths. Register: `docs/governance/AMSDP_Owner_Decisions_O1_O6_Implementation_Report_V1.0.md` §3 |
| **O-3** code paths | **Closed** — **correction to §6 / §8 of this report:** `ai_factory/verify_llm_routing.py` does not exist in this tree and `_tools/` contains no report-path references, so C-3's "two code files" was inaccurate. One genuine stale locator (`backend/tests/test_sequence3.py:3`, docstring) was corrected |
| **O-4** audit vs. implementation split | **Confirmed** by the owner; no document reclassified |
| **O-5** owner-document protection | **Confirmed** at the real paths; no protected document touched. Two over-broad **R** flags in the index were corrected to **—** |
| **O-6** two repo-root documents | **Closed** — relocated to `docs/audit/`, byte-identical (SHA-256 + Git blob hash equal), recorded in the manifest §11.1 |

Remaining open item: **O-7** — one cosmetic sentence in
`docs/governance/AMSDP_Engineering_Governance_Assessment.md:193` still reads as if
`ai_factory/docs/` held the milestone reports; fixing it needs a reworded cell,
which the O-2 authorization did not cover.

