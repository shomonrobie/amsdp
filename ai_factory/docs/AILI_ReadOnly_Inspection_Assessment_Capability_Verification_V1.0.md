# AILI Read-Only Repository-Inspection Assessment — Capability Verification (V1.0)

> **Purpose:** Verify whether AILI can inspect the AMSDP repository and produce
> an implementation-gap assessment using its own agents and workflows, before
> any assessment task is submitted.
>
> **Method:** Static inspection of the AILI execution path (builders, executors,
> engine dispatch, run recorder). No workflow was executed, no repository was
> modified, and neither AMSDP nor AILI infrastructure was changed.
>
> **Date:** 2026-11-05

---

## 1. Which existing AILI tools allow read-only inspection?

These read-only tool classes exist and are permission-bound to agents:

| Tool id | Class | Read operations | Bound to agents |
|---------|-------|-----------------|-----------------|
| `repo_read` | `RepositoryReadTool(repo_root)` | `list_paths`, `read_text`, `search` (never writes) | all A01-A11 |
| `doc_reader` | `DocumentReaderTool(loader)` | read governed documents | all A01-A11 |
| `git_read` | `GitReadTool(repo_root)` | git status/diff/log/branch | A02,A03,A05,A06,A07,A08,A10,A11 |
| `architecture_validator` | `ArchitectureValidatorTool` | structural checks | A02,A03 |
| `doc_link_validator` | `DocLinkValidatorTool` | markdown link checks | A11 |
| `openapi_validator`/`contract_test_tool` | read-only validation | read-only | A05/A08 |
| `secret_scan`, `static_analysis`, `migration_validator`, `ci_config_validator` | read-only scanning | read-only | A04,A06,A08,A09,A10 |

**Verdict: the read-only tool implementations exist and are permission-registered.**

---

## 2. Can AILI agents access the AMSDP source tree at /home/shomonrobie/amsdp?

**Configured destination: YES. Executable access: NO (current wiring).**

- `FactorySettings.effective_repo_root()` resolves to `/home/shomonrobie/amsdp`
  (verified) and `RepositoryReadTool` confines all reads inside that root, so the
  mechanism is pointed at the correct tree.
- **However, the live CrewAI agent is built without any tools.**
  `build_agent()` calls `crewai.Agent(role=..., goal=..., backstory=..., verbose,
  memory, allow_delegation, llm)` — **there is no `tools=[...]` argument**. A live
  CrewAI agent therefore has zero tools to call; `repo_read`, `doc_reader`,
  `git_read` are never attached.
- The WorkflowEngine's only tool-stage dispatch is `doc_link_validator`:
  `if tool_id == "doc_link_validator": ... else: raise WorkflowError("no engine
  implementation for tool ...")`. No generic dispatch for repo/doc/git reads.
- The stub/mock executor returns canned outputs from a handler and never calls
  any repository tool (verified: stub handler performs no read).

**Conclusion: the permission matrix claims these tools, but the execution path
never hands them to the agent or runs them.**

---

## 3. Are default repo_root and workspace config appropriate?

| Setting | Value | Appropriate? |
|---------|-------|--------------|
| `repo_root` | `/home/shomonrobie/amsdp` | Correct target |
| `task_store_dir` | `var/tasks` | Yes |
| `run_store_dir` | `runs` | Yes |
| `workspace_root` | `var/workspaces` | Yes (isolated per task) |
| provider/model | `openrouter` / `deepseek/deepseek-v4-flash` | Configured |
| live gate | `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1` (process env) | Gate-ready |

**Paths are appropriate; this is not a configuration problem.**

---

## 4. Can WF-01 perform requirements analysis against actual AMSDP source?

**No — not with the current execution wiring.** Evidence:

1. `build_stage_task(agent, request)` injects only: workflow id, stage id,
   artifact kind, task id, and `context_summary`. `context_summary` comes from
   `RunContext.context_for()` (prior agent-artifact summaries) and is **empty**
   for the first stage. No source-file content, governed-doc content, or
   `source_documents` are injected.
2. `WorkflowEngine.run()` calls `new_run()` without `source_documents`
   (defaults to `[]`) and without `start_commit`.
3. `ExecutionRequest` fields are exactly: `task_id, stage_id, agent_id,
   workflow_id, expected_artifact_kind, context_summary, evidence_workspace`.
   There is no repository-content field and no tool call is made during a stage.
4. `ContextLoader.load_for_task()` exists but is only used by CLI surfacing
   (`docs_status`/`doctor`); the engine and executors never call it.

Consequently a live WF-01 would base `requirement_analysis` on the model's
prior and prompt text — **not** on inspection of backend/ or frontend/ or the
project docs. That would be fabrication-driven analysis and must not be run.

---

## 5. Do execution records preserve provenance of inspected files/artifacts?

| Aspect | Recorded today? | Mechanism |
|--------|-----------------|-----------|
| Generated artifact provenance | Yes | `EvidenceRef(path, sha256, verified)`; `ArtifactRecord(sha256)`; stage records |
| Approval provenance | Yes | `ApprovalRecord(decision, actor, rationale, decided_at)` in run JSON |
| **Inspected-file provenance** | **No** | `ToolOperationRecord(...)` model exists but neither executor populates it and no repo tool executes |

Artifact/approval provenance is preserved; **inspected-file provenance is not
recorded because no inspection occurs.**

---

## 6. Conclusion — the precise missing capability

Read-only tool implementations exist and the permission matrix is correct,
but the execution path does not connect them.

**M1 — no tools attached:** `build_agent()` must attach the permitted
read-only tools (`repo_read`, `doc_reader`, `git_read`) via
`Agent(tools=[...])`.

**M2 — no generic tool dispatch:** `WorkflowEngine._run_tool_stage()` only
handles `doc_link_validator`. A registry-driven dispatch is required so
`repo_read`/`doc_reader`/`git_read` execute on behalf of `via_agent_id` after
`ToolRegistry.assert_allowed`.

**M3 — no source/doc context injection:** Either call
`ContextLoader.load_for_task()` (governed docs) and pass results into
`ExecutionRequest.context_summary`, or gather source-file snapshots via
`repo_read` before a stage, bounded by workflow `required_input_kinds`.

**M4 — no tool-operation recording:** the live executor must populate
`ToolOperationRecord` (name, args summary, working dir, timing, exit code) so
inspected-file provenance is audit-traceable.

Until M1-M4 are implemented, **AILI cannot assess the AMSDP repository with its
own agents** (live or stub). No CLI command should be run that claims to do so.

---

## 7. As-is CLI behaviour (for the record)

Task/workspace registration and stub/live running work. But a live WF-01 run
would produce an analysis **without inspecting the repository**, and stub mode
produces `[STUB-SYNTHETIC]` outputs. Neither satisfies the assessment mission.
Hence **no task is submitted** in this deliverable.

---

*Verification only. No assessment executed. No repository or infrastructure
modified.*
