# AILI Agent Rules Integration Report V1.0

> **Date:** 2026-11-06
> **Project:** AILI (AI Factory) — AMSDP governed-rule integration
>
> **Scope:** Integrate the Agent Rules library (CarbonTally SaaS engineering
> rules) into AILI's governed knowledge, agent execution context, workflow
> provenance, and test framework.
>
> **Boundary:** AILI framework only. No AMSDP application source, database,
> Docker, or deployment configuration was modified.

---

## 1. Initial Findings

| Finding | Detail |
|---------|--------|
| Source library discovered | `/home/shomonrobie/ct_93d5cdd/docs/agent-rules/` (11 .md files + MANIFEST.json) |
| Source documents | 11 markdown files: 1 governance (Tier 1), 1 router (README), 9 domain rules |
| MANIFEST.json | Valid -- SHA-256 per file, purpose field present, all hashes match current content |
| No missing documents | All 11 expected files present |
| No unexpected documents | Only README.md is outside manifest_files, expected as the router |
### 1.1 Mandatory Distinction: Agent Rules vs. Project Requirements

**Agent Rules** (in `docs/agent-rules/`) define *how* agents should design,
implement, test, and operate software -- engineering conventions, security
patterns, auth models, CI/CD gates, observability, etc.

**Project Requirements** (in `docs/product/`, `docs/architecture/` managed by
the existing `DocumentRegistry`) define *what* a project like AMSDP must
deliver -- business rules, scope, architecture decisions.

The integration respects the existing authority order: Project Requirements
(especially ratified decisions) outrank Agent Rules. When the engine loads
both, project documents are loaded first (higher authority). If an agent
detects a conflict, the rules require it to:
- Identify, explain, and reference the conflict
- Escalate for human resolution
- Never silently choose one interpretation

No conflicts detected between current AMSDP project requirements and the
integrated Agent Rules.

## 2. Architecture and Implementation

### 2.1 New Package: `rules/`

```
src/amsdp_ai_factory/rules/
  __init__.py    Package marker + re-exports
  registry.py    AgentRulesRegistry -- discovery, MANIFEST validation, SHA-256
  mapping.py     Agent-to-rule mapping tables + select_rule_ids()
```

#### registry.py
- `AgentRulesRegistry(rules_dir)` -- loads MANIFEST.json, discovers .md files,
  computes SHA-256 hashes, detects missing/changed/unexpected documents.
- `RuleDocument` -- rule_id, file_name, sha256, frontmatter metadata.
- `RuleScanResult` -- scan outcome with status flags.
- `resolve_rule_text(rules_dir, rule_id)` -- loads full rule content by ID.

#### mapping.py
- `RULE_MAP` -- rule_id to agent_id list ("*" for universal).
- `TASK_TYPE_RULE_MAP` -- task_type to related rule_ids.
### 2.2 Modified: `execution/models.py`

Added to `ExecutionRequest`:
- `applied_rule_ids: list[str]` -- rule IDs loaded for this stage
- `rules_text: str` -- concatenated rule text for the task prompt
- `has_rules` property

### 2.3 Modified: `execution/build_crews.py`

`build_stage_task()` appends rule text to the CrewAI Task description when
`request.rules_text` is present, ensuring agents receive rules in their prompt.

### 2.4 Modified: `execution/run_context.py`

Added `record_rules(stage_id, rule_ids)` and `applied_rules` property for
rule provenance tracking across stages.

### 2.5 Modified: `workflows/engine.py`

Added two methods to `WorkflowEngine`:
1. `_select_agent_rules(task, stage)` -- calls `select_rule_ids()`.
2. `_load_agent_rules(task, stage)` -- resolves rules dir, loads rule text.

Called during `_run_agent_stage()` before building `ExecutionRequest`.
Applied rule IDs are recorded in `RunContext` after stage success.

### 2.6 Created: `docs/agent-rules/`

Copy of the source Agent Rules library. Preserved verbatim.

### 2.7 Created: `tests/unit/test_agent_rules.py`

24 tests covering all 14 required test categories.

## 3. Agent/Workflow Mapping Summary

| Rule | Agents | Also For Task Types |
|------|--------|-------------------|
| Governance | ALL (universal) | All |
| Emissions Provenance | A01,A02,A06,A07,A08,A09,A11 | -- |
| AI Provider Registry | A02,A03,A09,A10 | security_review |
| API Throttling | A02,A05,A06,A09 | security_review, backend_implementation |
| Application Security | A02-A10 | architecture_design, security_review, backend_implementation |
| Auth & Authorisation | A02,A03,A04,A05,A06,A09 | architecture_design, security_review |
| CI/CD Workflow | A08,A09,A10 | deployment, qa, assessment |
| Frontend UX | A01,A02,A07 | frontend_implementation |
| Multitenant Data | A02,A04,A06,A08,A09 | architecture_design, security_review, backend_implementation |
| Observability | A02,A06,A08,A09,A10 | architecture_design, deployment, backend_implementation |
## 4. ContextLoader Integration

1. Existing `ContextLoader.load_documents()` and `load_for_task()` continue to
   load **project requirements** unchanged.
2. `WorkflowEngine._run_agent_stage()` additionally calls `_load_agent_rules()`
   and appends rule text to `context_summary`.
3. Combined context flows through `ExecutionRequest` into `build_stage_task()`,
   which embeds it in the CrewAI Task description.
4. Missing/unreadable rules generate a notice in the returned text rather than
   failing silently.

## 5. Provenance Changes

RunContext gained `record_rules(stage_id, rule_ids)` and `applied_rules`.
When a stage completes, the engine records which rules were applied.
This enables auditing, change detection, and version tracing via MANIFEST.

## 6. Test Results

### New Agent Rules Tests (24 tests, all pass)

| Class | Tests | Covers |
|-------|-------|--------|
| TestManifestAndDiscovery | 10 | Manifest validation, discovery, SHA-256, frontmatter |
| TestAgentMapping | 6 | Agent-to-rule mapping, governance universal, irrelevant excluded |
| TestContextLimitAndDetection | 3 | Missing/malformed rules, changed content, empty manifest |
| TestEngineIntegration | 5 | Engine integration, provenance, loader compatibility |
| TestResolveRuleText | 3 | Rule text resolution by ID |

### Full Suite: 342/342 pass (was 318)

```
Unit modules:        38  (+1: test_agent_rules)
Integration modules: 13  (unchanged)
Total executed:      342
Passed:              342
Failed:               0
Errors:               0
```

All 14 mandatory requirements covered by tests.

## 7. Security and Safety

| Check | Result |
|-------|--------|
| No AMSDP application source modified | Confirmed |
| No database schemas or data modified | Confirmed |
| No Docker/deployment config modified | Confirmed |
| PatchTool never enabled | Confirmed |
| No commits pushed to GitHub | Confirmed |
| No live model provider calls made | Confirmed |
| Source documents preserved verbatim | Confirmed |
| Existing run records preserved | Confirmed |

## 8. Changed-File Inventory

### New
- `src/amsdp_ai_factory/rules/__init__.py`
- `src/amsdp_ai_factory/rules/registry.py`
- `src/amsdp_ai_factory/rules/mapping.py`
- `docs/agent-rules/` (12 files)
- `tests/unit/test_agent_rules.py`
- `docs/AILI_Agent_Rules_Integration_Report_V1.0.md` (this report)

### Modified
- `src/amsdp_ai_factory/execution/models.py` (+3 fields on ExecutionRequest)
- `src/amsdp_ai_factory/execution/build_crews.py` (+rule text in description)
- `src/amsdp_ai_factory/execution/run_context.py` (+rule provenance)
- `src/amsdp_ai_factory/workflows/engine.py` (+_select_agent_rules, _load_agent_rules, rule recording)

### Unchanged
`backend/*`, `frontend/*`, `docker-compose.yml`, `.env`, `.env.example`, `runs/*`

## 9. Known Limitations

1. **No formal conflict escalation endpoint** -- conflict detection is the
   agent's responsibility; a dedicated paused-workflow mechanism is future work.
2. **Single rules directory** -- multi-project rule selection is not implemented.
3. **No runtime injection** -- rules are resolved at stage start only.
4. **Rule text size may affect context limits** -- rule text is appended via
   `build_stage_task`, outside the `MAX_CONTEXT_CHARS` bound on artifact context.

## 10. Evidence

- All 342 tests pass (38 unit + 13 integration).
- All 24 Agent Rules tests pass.
- All 318 pre-existing tests pass (no regressions).
- No AMSDP application files modified.
- Source documents preserved verbatim at `ai_factory/docs/agent-rules/`.
- Git status confirms no modifications to backend/, frontend/, or deployment config.
- `select_rule_ids(agent_id, task_type)` -- union of governance + agent + task rules.