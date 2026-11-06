# AILI M1-M4 Read-Only Inspection Implementation Report (V1.0)

> **Purpose:** Enable AILI to genuinely inspect the AMSDP repository with its
> own agents and produce an evidence-based implementation-gap assessment.
>
> **Date:** 2026-11-05 andnbsp; **Environment:** `.venv313` (Python 3.13.15, CrewAI
> 1.15.35)

---

## 1. Files changed (7 files)

| File | Change |
|------|--------|
| `src/amsdp_ai_factory/agent_tools.py` | **New.** CrewAI read-only tool wrappers (`repo_read`, `doc_reader`, `git_read`), `ToolBundle`, `ToolOperationCollector`, `build_read_tool_bundle()` (M1 + M4). |
| `src/amsdp_ai_factory/execution/build_crews.py` | `build_agent()` accepts and attaches `tools=[...]` (M1). |
| `src/amsdp_ai_factory/execution/live.py` | `CrewAIExecutor` builds the read-only bundle, attaches collector, surfaces `tool_operations` (M1+M4). |
| `src/amsdp_ai_factory/workflows/engine.py` | Registry-driven `_execute_registered_tool()` (M2); `_load_document_context()` via ContextLoader (M3); ToolOperationRecord provenance + denied audit (M4); `repo_root`/`context_loader` ctor params. |
| `src/amsdp_ai_factory/runs/models.py` | `ToolOperationRecord` extended with M4 provenance fields. |
| `src/amsdp_ai_factory/cli.py` | WorkflowEngine constructed with `repo_root=settings.effective_repo_root()`. |
| `tests/integration/test_m1m4_readonly_inspection.py` | **New.** 14 tests covering M1-M4 + security. |

---

## 2. M1 - Agent tool attachment

- `build_read_tool_bundle(agent, repo_root, loader, registry, collector)`
  instantiates `RepositoryReadTool`, `DocumentReaderTool`, `GitReadTool` against
  the resolved project root and returns a `ToolBundle` of CrewAI `@tool` wrappers.
- Only tool ids in `_READ_ONLY_TOOL_IDS = {repo_read, doc_reader, git_read}` are
  ever attached. `patch_generator`, `artifact_write`, `run_tests`, shell, or any
  source-modification tool is **never** attached in this phase.
- Permission authority is `ToolRegistry.assert_allowed(agent_id, tool_id)`
  (default-deny): any referenced-but-unauthorized read tool fails closed with
  `ToolPermissionError`.
- `build_agent()` now passes `tools=bundle.as_list()` to
  `crewai.Agent(tools=[...])`.

**Verified live:** a `CrewAIExecutor`-built agent for A02 has exactly
`[doc_reader_list_roles, doc_reader_read, git_read_branches, git_read_head,
git_read_log, git_read_status, repo_read_list_paths, repo_read_read_text,
repo_read_search]` - 9 read-only tool wrappers, no write/patch/shell tools (see 7).

---

## 3. M2 - Registry-driven tool dispatch

`WorkflowEngine._run_tool_stage()` now:

1. Resolves `tool_id = stage.tool_stage_tool_id` and `via_agent`.
2. Calls `ToolRegistry.assert_allowed(via_agent, tool_id)`; on denial records a
   `ToolOperationRecord(ok=False, error="denied: ...")` and fails the stage.
3. Dispatches through `_execute_registered_tool(tool_id, task, store)`, mapping
   the registered read tools:
   - `repo_read` = `RepositoryReadTool.list_paths(...)` (bounded)
   - `doc_reader` = `ContextLoader.load_for_task(...)` summary
   - `git_read` = `GitReadTool.run("status")`
   - `doc_link_validator` = workspace link check (preserves prior behavior)
4. Records a `ToolOperationRecord` (started/ended, ok, exit_code, target, error),
   adds a run check, completes/fails the stage.

The former single-case `doc_link_validator` special-case is replaced by this
registry-driven path while preserving existing workflow behavior and approval gates.

---

## 4. M3 - Project-context injection

`_run_agent_stage()` composes stage context as:

```
context_summary = document_context + prior_stage_artifacts (RunContext)
```

`document_context` comes from `_load_document_context(task, stage)`:

- Uses `ContextLoader.load_for_task(task.task_type, max_chars=12000)` selecting
  governed document roles (business rules, MVP scope, system architecture, ...)
  and reading their real text from the repository, bounded per doc and by
  `MAX_TOTAL_CONTEXT_CHARS = 24000`.
- Respects `required_input_kinds`/`expected_output_kinds` (agent stages that
  expect an output artifact).
- Records each loaded doc as an inspection `ToolOperationRecord`
  (doc_reader.read, role, path, sha256) so provenance is preserved.
- Nothing is fabricated: missing documents are reported as unavailable.

---

## 5. M4 - Inspection provenance

- `ToolOperationRecord` extended: `agent_id, stage_id, operation, target, ok,
  error, evidence_refs` (list of `{path, sha256}`).
- Agent tool wrappers push a record via `ToolOperationCollector` per call:
  operation, target path, started/ended, ok/error, and a SHA-256 evidence ref of
  the returned content (skipped for aggregate list/search).
- `CrewAIExecutor.execute()` returns `ExecutionResult.tool_operations`; the
  engine appends them to the run via `run_recorder.add_tool_operation`.
- Engine tool stages record their own `ToolOperationRecord`, and **denied** ops
  are audited with `ok=False, error="denied: ..."`.
- No secrets written: bounded output summaries only; no API keys or credentials.

---

## 6. Live evidence - inspect but cannot modify

Executed against a controlled temp git repo (`backend/main.py` + `secret.txt`):

```
ATTACHED tool names: ['doc_reader_list_roles', 'doc_reader_read',
  'git_read_branches', 'git_read_head', 'git_read_log', 'git_read_status',
  'repo_read_list_paths', 'repo_read_read_text', 'repo_read_search']
ATTACHED count: 9
INSPECT result: 'def f():\n    return 1\n'
main.py unchanged: True
secret.txt unchanged: True
FORBIDDEN tools attached: NONE
PROVENANCE ops recorded: ['repo_read.read_text']
RESULT: INSPECT=OK MODIFY=BLOCKED PROVENANCE=OK
```

- **CAN inspect:** the agent's `repo_read_read_text` returned real file content.
- **CANNOT modify:** both file byte-streams identical before/after; zero
  write/patch/shell/exec tools attached.
- **Provenance:** `repo_read.read_text` captured with agent, stage, target, SHA.

---

## 7. Test results - complete counts

```bash
PYTHONPATH=ai_factory/src:/home/shomonrobie/amsdp/ai_factory \
  /home/shomonrobie/amsdp/.venv313/bin/python /tmp/run_full_suite.py
```

| Metric | Value |
|--------|-------|
| Total tests executed | **286** |
| Passed | **286** |
| Failed | **0** |
| Errors | **0** |
| Skipped | **0** |
| Not collected | **0** |
| Unit modules | 37 |
| Integration modules | 11 |
| New M1-M4 tests | 14 |

New coverage (`tests/integration/test_m1m4_readonly_inspection.py`):

1. `test_agent_receives_authorized_read_tools`
2. `test_unauthorized_write_tool_not_attached`
3. `test_crewai_agent_constructed_with_tools`
4. `test_registered_tool_dispatches`
5. `test_unknown_tool_raises`
6. `test_unbound_agent_denied`
7. `test_loader_injects_actual_document_content`
8. `test_context_limits_enforced`
9. `test_collector_populates_provenance`
10. `test_bundle_collector_records_calls`
11. `test_read_stays_inside_project`
12. `test_traversal_rejected`
13. `test_no_source_modification_by_bundle`
14. `test_tool_stage_records_provenance`

---

## 8. Security requirements - compliance

| Requirement | Status |
|-------------|--------|
| Enforce read-only access throughout | OK - only 3 read tools; no write/patch/shell |
| Reject path traversal and symlink escapes | OK - RepositoryReadTool refuses escapes; tests |
| Enforce agent-specific tool permissions | OK - ToolRegistry.assert_allowed default-deny |
| Prevent unauthorized tool invocation | OK - fail-closed bundle build + engine assert_allowed |
| Record denied and failed inspection attempts | OK - ToolOperationRecord(ok=False, error="denied") |
| Do not expose unrestricted shell execution | OK - no shell tool attached |
| Preserve all existing human approval gates | OK - gate flow unchanged; 286-green regression |

---

## 9. Remaining limitations

| Limitation | Impact |
|-----------|--------|
| CrewAI wrapped tools are direct wrappers; LLM tool selection depends on prompt + model | Agent can call them, but autonomous selection is not unit-testable w/o live LLM |
| git_read attached to all agents that list it (even if unused) | Read-only; acceptable |
| doc_reader reads only governed registry roles, not arbitrary repo refs | Intended: provenance; repo_read covers arbitrary files |
| Git tools on non-git dirs return bounded error result | No crash |
| task-level source_documents still not auto-populated | Tool inspection provenance recorded instead |

---

## 10. Next step (requires your explicit go-ahead)

This report stops before any AMSDP assessment workflow is executed. When you
authorize the live inspection-based AMSDP gap assessment:

```bash
export AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1
cd /home/shomonrobie/amsdp/ai_factory
PYTHONPATH=src ../.venv313/bin/python -m amsdp_ai_factory task_new \
  --title "AMSDP hackathon gap assessment" --workflow-id WF-01 \
  --task-type assessment --description "Evidence-based gap analysis of AMSDP"
```

then `run_workflow` / `approve` / `resume` per the operational HOWTO.

---

*M1-M4 implemented and verified. No AMSDP source modified, no database or Docker
touched, no PatchTool enabled for agents, no commit/push/deploy performed, no
features implemented.*
