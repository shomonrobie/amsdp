# AILI CrewAI Execution Architecture and Verification Report — V1.0

> **Date:** 2026-11-05  
> **Purpose:** Determine whether AILI can autonomously coordinate actual software-development work through CrewAI agents.  
> **Method:** Read-only inspection of all execution-relevant AILI source code, tool implementations, test evidence, and environment state.  
> **Constraint:** No modifications made to AILI, AMSDP, or any configuration.

---

## 1. Current Execution Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   AILI Execution Architecture                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────────┐                    │
│  │  CLI / Test   │───>│  WorkflowEngine  │                    │
│  └──────────────┘    └────────┬─────────┘                    │
│                               │                              │
│           ┌───────────────────┼────────────────────┐         │
│           ▼                   ▼                     ▼         │
│   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐  │
│   │  MockAgent   │   │  CrewAIExecutor │   │ Tool Stages  │  │
│   │  Executor    │   │  (provider-     │   │              │  │
│   │  (test/      │   │   gated)        │   │              │  │
│   │   stub only) │   └────────┬───────┘   └──────┬───────┘  │
│   └──────────────┘            │                   │          │
│                        ┌──────┴──────┐             │          │
│                        ▼             ▼             ▼          │
│                ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│                │build_agent │ │build_stage │ │ ToolRegistry│  │
│                │() → CrewAI │ │_task() →   │ │.assert_    │  │
│                │Agent       │ │CrewAI Task │ │allowed()   │  │
│                └────────────┘ └────────────┘ └────────────┘  │
│                        │                                      │
│                        ▼                                      │
│                ┌──────────────────┐                           │
│                │ build_single_    │                           │
│                │ stage_crew()     │                           │
│                │ → CrewAI.Crew    │                           │
│                └──────┬───────────┘                           │
│                       ▼                                       │
│                ┌──────────────────┐                           │
│                │ crew.kickoff()   │ ←── LLM call (if gate open)│
│                └──────────────────┘                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 1.1 Execution flow

1. **CLI** (`cli.py`) or **test** calls `WorkflowEngine.run(task_id, workflow_id, executor)`.
2. Engine validates workflow is EXECUTABLE, loads stages, validates agent/tool bindings.
3. For each **agent stage**: calls `executor.execute(request)`.
4. For each **tool stage**: calls tool implementation directly after `ToolRegistry.assert_allowed()`.
5. For each **gate stage**: pauses task at a human-approval status; requires `ApprovalService.decide()`.
6. Executor choice determines whether CrewAI is invoked or canned output is returned.

---

## 2. Actual CrewAI Execution Path

### 2.1 The `CrewAIExecutor.execute()` method (live.py:57-105)

```python
def execute(self, request, artifact_store=None):
    self._assert_gate()           # Two-gate check
    definition = AGENT_INDEX.get(request.agent_id)
    agent = build_agent(definition, model_id=self.settings.model_id)
    task = build_stage_task(agent, request)
    crew = build_single_stage_crew(agent, task)
    output_holder = crew.kickoff()  # ← THE CrewAI call
    # ... validate output against contract ...
```

### 2.2 Two-gate safety system (live.py:44-55)

| Gate | Check | Error if Missing |
|------|-------|-----------------|
| Gate 1 | `settings.model_provider` AND `settings.model_id` set | "requires AMSDP_FACTORY_MODEL_PROVIDER and AMSDP_FACTORY_MODEL_ID" |
| Gate 2 | `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1` | "live execution is not authorized" |

### 2.3 CrewAI build chain (build_crews.py)

| Step | Code File | Produces |
|------|-----------|----------|
| `build_agent()` | build_crews.py:17-29 | `crewai.Agent(role=..., goal=..., backstory=..., llm=model_id)` |
| `build_stage_task()` | build_crews.py:32-46 | `crewai.Task(description=..., expected_output=..., agent=agent)` |
| `build_single_stage_crew()` | build_crews.py:49-54 | `crewai.Crew(agents=[agent], tasks=[task], process=sequential)` |

### 2.4 VERDICT: Path EXISTS but NEVER EXECUTED LIVE

- **CrewAI 0.11.2 IS installed** in the venv (`pip show crewai` confirms).
- **The code path works** — `build_agent()`, `build_stage_task()`, `build_single_stage_crew()` are all correctly wired.
- **However**, CrewAI currently **fails to import** due to a Python 3.14 dependency incompatibility:
  ```
  AttributeError: module 'ast' has no attribute 'NameConstant'
  ```
- **No live execution has ever occurred.** All tests mock `CrewAIExecutor` or use `MockAgentExecutor`.
---

## 3. Mock versus Live Execution

### 3.1 Execution modes

| Mode | Class | When Used | Produces Real Code? |
|------|-------|-----------|-------------------|
| **Mock** | `MockAgentExecutor` | Default for all tests | ❌ Canned `AgentOutput` from handler function |
| **Stub** | `MockAgentExecutor` + `build_stub_handler()` | Demo/CLI stub runs | ❌ `[STUB-SYNTHETIC]` labeled outputs |
| **Live** | `CrewAIExecutor` | Gate-open, configured only | ❌ Never executed |

### 3.2 Distinguishing mock from live

| Feature | Mock/Stub | Live (CrewAI) |
|---------|-----------|---------------|
| `ExecutionResult.output` | Pre-canned `AgentOutput` | Generated via `crew.kickoff()` |
| Evidence paths | Synthetic (stub) or handler-defined | LLM-generated |
| Tool calls | Not actually executed | Executed via `ToolRegistry.assert_allowed()` |
| `RunRecord.provider` | `None` or `"stub"` | Provider name string |
| Provider configured | No | Yes (model_provider + model_id) |

### 3.3 VERDICT: All existing execution is mock/stub

All 232 AILI tests run via `MockAgentExecutor`. The 329 MediCore and 87 AMSDP tests run via standard `pytest` (not through AILI). **Zero evidence of CrewAI agent output used in AMSDP development.**

---

## 4. Agent-to-Crew Mappings

### 4.1 Agent definitions and their tool permissions

| Agent | ID | Role | Permitted Tools | Write Prefix |
|-------|----|------|----------------|-------------|
| A01 | A01 | Product Analyst | repo_read, doc_reader, git_read, artifact_write | docs/requirements |
| A02 | A02 | System Architect | repo_read, doc_reader, git_read, artifact_write | docs/architecture |
| A03 | A03 | Service Architect | repo_read, doc_reader, git_read, artifact_write | docs/services |
| A04 | A04 | Database Architect | repo_read, doc_reader, git_read, artifact_write, disposable_db, migration_validator | docs/database |
| A05 | A05 | API Contract Designer | repo_read, doc_reader, git_read, artifact_write, openapi_validator, contract_test_tool | contracts |
| A06 | A06 | Backend Developer | repo_read, doc_reader, git_read, artifact_write, run_tests, static_analysis, disposable_db | code |
| A07 | A07 | Frontend Developer | repo_read, doc_reader, git_read, artifact_write, run_tests | frontend |
| A08 | A08 | QA Engineer | repo_read, doc_reader, git_read, artifact_write, run_tests, contract_test_tool | tests |
| A09 | A09 | Security Reviewer | repo_read, doc_reader, git_read, artifact_write, secret_scan, static_analysis | docs/security |
| A10 | A10 | DevOps Engineer | repo_read, doc_reader, git_read, artifact_write, ci_config_validator | ops |
| A11 | A11 | Technical Writer | repo_read, doc_reader, git_read, artifact_write | docs |

### 4.2 Workflow-to-Crew mappings (10 workflows)

| Workflow | Stages | Agents | Status |
|----------|--------|--------|--------|
| WF-01 Requirement→Design | 8 (7 agent + 1 gate) | A01, A02, A03, A04, A05, A08, A09 | EXECUTABLE |
| WF-02 Service Implementation | 5 (4 agent + 1 gate) | A06, A08, A09 | EXECUTABLE |
| WF-03 Frontend Delivery | 8 (7 agent + 1 gate) | A01, A05, A07, A08, A09, A11 | EXECUTABLE |
| WF-04 Defect Resolution | 5 (4 agent + 1 gate) | A06/A07, A08, A09 | EXECUTABLE |
| WF-05 Architecture Decision | 4 (3 agent + 1 gate) | A02, A03, A04 | EXECUTABLE |
| WF-06 Database Change | 4 (3 agent + 1 gate) | A04, A06, A09 | EXECUTABLE |
| WF-07 Security Review | 4 (3 agent + 1 gate) | A09, A06, A08 | EXECUTABLE |
| WF-08 Cross-Service Integration | 4 (3 agent + 1 gate) | A05, A06, A08, A09 | EXECUTABLE |
| WF-09 Release Readiness | 4 (3 agent + 1 gate) | A09, A10, A11, A08 | EXECUTABLE |
| WF-10 Documentation Update | 4 (2 agent + 1 tool + 1 gate) | A11 + doc_link_validator | EXECUTABLE |

### 4.3 VERDICT: All workflows defined; none executed with real agents

Workflow definitions correctly reference agent IDs. The engine validates agent-tool bindings. However, no workflow has ever been through `CrewAIExecutor` with a real LLM.
---

## 5. Tool Permission Enforcement

### 5.1 Default-deny architecture

```python
class ToolPermissionError(PermissionError):
    """Raised when an agent attempts a tool it is not entitled to use."""
```

### 5.2 Permission check points

| Check Point | Code | Location |
|-------------|------|----------|
| Agent→Tool binding | `_validate_executability()` → `registry.assert_binding()` | engine.py:320-334 |
| Tool execution gate | `registry.assert_allowed(agent_id, tool_id)` | engine.py:248-250 |
| Artifact write containment | `_resolve()` → checks prefix, no `..`, no absolute | artifact_writer.py:34-49 |
| Test runner allowlist | `_validate()` → 3 allowed command patterns | test_runner.py:38-55 |

### 5.3 VERDICT: Tool permission enforcement is robust

- Default-deny is correctly implemented.
- Every tool call is gated through `assert_allowed()`.
- Write paths are bounded to the task workspace (cannot modify actual source code).
- Test runner only allows 3 command patterns (`unittest discover`, `compileall`, `py_compile`).

---

## 6. Code-Generation and File-Modification Capabilities

### 6.1 Tool inventory

| Tool | Category | Can Modify Project Files? |
|------|----------|--------------------------|
| `repo_read` | READ | ❌ Read-only |
| `doc_reader` | READ | ❌ Read-only |
| `git_read` | READ | ❌ Read-only |
| `artifact_write` | WRITE | ❌ **Only writes to `<workspace>/<prefix>/`**, NOT to project source |
| `run_tests` | EXECUTE | ❌ Only 3 allowlisted command patterns |
| `static_analysis` | VALIDATION | ❌ Read-only analysis |
| `secret_scan` | SECURITY | ❌ Read-only scanning |
| `disposable_db` | DB | ❌ In-memory SQLite only |
| `migration_validator` | VALIDATION | ❌ Read-only pattern checks |
| `contract_test_tool` | VALIDATION | ❌ Read-only comparison |
| `ci_config_validator` | VALIDATION | ❌ Read-only validation |
| `openapi_validator` | VALIDATION | ❌ Read-only validation |
| `architecture_validator` | VALIDATION | ❌ Read-only validation |
| `doc_link_validator` | VALIDATION | ❌ Read-only workspace link check |

### 6.2 The critical gap: No tool writes to project source code

The `artifact_write` tool is **scoped to the task workspace** (`<workspace_root>/<task_id>/<prefix>/`), NOT to actual project directories (`backend/`, `frontend/`).

```
┌─ Task workspace ─────────────────────┐
│ var/workspaces/TASK-0001/            │
│   ├── code/          (A06 writes)    │
│   ├── frontend/      (A07 writes)    │
│   ├── docs/          (A0X writes)    │
│   ├── contracts/     (A05 writes)    │
│   └── tests/         (A08 writes)    │
└──────────────────────────────────────┘

  ✗ Cannot write to:
    backend/identity/main.py
    frontend/pages/index.js
    docker-compose.yml
```

### 6.3 VERDICT: AILI CANNOT autonomously create or modify project source code

The tool infrastructure prevents any agent from writing to actual AMSDP source files. There is no tool that can:
- Create a new Python/JavaScript file in the project
- Modify an existing service implementation
- Run `git commit` or `git push`
- Execute arbitrary shell commands
- Deploy or release
---

## 7. Execution Evidence

### 7.1 What we found

| Evidence Type | Found? | Details |
|---------------|--------|---------|
| Run record JSON files | ❌ | No run records found in `ai_factory/runs/` |
| Live CrewAI execution trace | ❌ | Never executed |
| Mock execution traces | ✅ | 232 AILI test results (all mock/stub) |
| AILI→AMSDP handoff evidence | ❌ | AMSDP was built by **Cline**, not AILI agents |
| CrewAI `pyproject.toml` dependency | ✅ | `crewai>=0.7` in `ai_factory/pyproject.toml` |
| Working CrewAI import | ❌ | `crewai` fails to import (Python 3.14 incompatibility) |

### 7.2 MediCore and AMSDP execution analysis

| Product | Who Built It? | How? |
|---------|--------------|------|
| **AILI Factory** (232 tests) | Cline | Written directly following AILI specs |
| **MediCore** (329 tests, 9 microservices) | Cline | Written directly following MediCore spec |
| **AMSDP MVP** (87 tests, 8 microservices + frontend) | Cline | Written directly following AMSDP specs |

**There is zero evidence that any AILI CrewAI agent contributed code, generated files, or made decisions for MediCore or AMSDP.** All AMSDP code was created by Cline as the development interface, using the AILI tool infrastructure for verification.

### 7.3 What the MediCore WF-01 test runs prove

The MediCore test files (in `/tmp/medicore_run.py` etc.) exercised `WorkflowEngine.run()` with **MockAgentExecutor**, not `CrewAIExecutor`. These are mock integration tests of the workflow engine, not real agent execution.

---

## 8. Missing Capabilities

| # | Capability | Current State | Required for Autonomous Development |
|---|-----------|---------------|-------------------------------------|
| 1 | **Code write to project** | ❌ `artifact_write` is sandboxed to task workspace | Need a tool that can write to `backend/` and `frontend/` |
| 2 | **File system write outside workspace** | ❌ No shell tool or unrestricted file write exists | Need a bounded write tool |
| 3 | **git commit/push** | ❌ No tool exists (intentionally prohibited) | Needed for delivering code changes |
| 4 | **Arbitrary command execution** | ❌ `run_tests` only allows 3 command patterns | Need broader but bounded execution |
| 5 | **Working LLM provider** | ❌ CrewAI broken on Python 3.14; no provider credentials | Must fix CrewAI + configure provider |
| 6 | **Cross-agent memory** | ❌ `memory=False` on all agents; no context passed between stages | Need shared context across stages |
| 7 | **Agent delegation** | ❌ `allow_delegation=False` on all agents | No multi-agent collaboration |
| 8 | **Inter-agent handoff** | ⚠️ `expected_output_kinds` defined but no artifact passing between stage executions | Need context injection in stage tasks |
| 9 | **Self-correcting agents** | ❌ Retry = "at most 2 attempts"; no agent-driven correction | Need error feedback loop |
| 10 | **Process/task isolation** | ⚠️ Single-agent, single-task Crew per stage | No parallel execution |

---

## 9. Recommended Changes

### 9.1 Critical (required for any autonomous development)

| Priority | Change | Description |
|----------|--------|-------------|
| **P0** | **Fix CrewAI dependency** | Upgrade `crewai` and/or `docstring_parser` to versions compatible with Python 3.14, or pin Python ≤3.13. Currently `import crewai` fails. |
| **P0** | **Add code-write tool** | Create a tool that can write to `backend/<service>/` and `frontend/` directories with path containment. |
| **P0** | **Configure LLM provider** | Set `AMSDP_FACTORY_MODEL_PROVIDER`, `AMSDP_FACTORY_MODEL_ID`, and provider API key. Without this, `CrewAIExecutor` always raises. |

### 9.2 High (needed for reliable autonomous execution)

| Priority | Change | Description |
|----------|--------|-------------|
| **P1** | **Cross-agent context passing** | WF-01 produces `requirement_analysis` → `architecture_proposal` → `service_implementation_plan`. Next agent has NO access to previous output. |
| **P1** | **Agent memory/state** | Enable `memory=True` and pass accumulated context across stages. |
| **P1** | **Evidence verification automation** | Agents produce evidence paths but no tool runs tests and captures results automatically. |

### 9.3 Medium (quality and safety)

| Priority | Change | Description |
|----------|--------|-------------|
| **P2** | **Add `shell_bounded` tool** | Restricted shell execution with explicit allowlist, timeout, and output truncation. |
| **P2** | **Agent output human review** | Before code-write modifies project files, require a human approval gate. |
| **P2** | **Diff generation** | Agents should produce machine-readable diffs for review before applying. |

### 9.4 Governance (constraint preservation)

| Priority | Change | Description |
|----------|--------|-------------|
| **P3** | **Audit trail for code writes** | Every code-write must record: agent_id, file path, content hash, timestamp, approval_id. |
| **P3** | **Write-backup before modification** | Save `.bak` copy before modifying existing files. |
| **P3** | **No-destructive-write guarantee** | Tool must refuse to delete files or truncate to zero length. |
| **P3** | **Rollback support** | One-command rollback to pre-run state if workflow fails after writes.
---

## 10. Summary

### 10.1 What AILI Actually Does

```
┌─────────────────────────────────────────────────┐
│              AILI Capability Summary             │
├─────────────────────────────────────────────────┤
│                                                   │
│  ✅ DEFINES:                                     │
│  ├── 11 specialist agents (A01-A11)              │
│  ├── 10 workflows (WF-01→WF-10)                  │
│  ├── 14 tools with RBAC permission matrix        │
│  ├── Task lifecycle (22 states, FSM validated)   │
│  ├── Structured output contracts (12 artifact    │
│  │   types with field-level validation)          │
│  ├── Human approval gates (request/decide flow)  │
│  └── Run recording (run_id, stages, approvals)   │
│                                                   │
│  ✅ VALIDATES (with mock/stub data):              │
│  ├── Workflow engine → stage progression         │
│  ├── Tool permission enforcement                 │
│  ├── Output contract validation                  │
│  ├── Evidence path verification                  │
│  └── Approval gate state machine                 │
│                                                   │
│  ❌ CANNOT DO (currently):                       │
│  ├── Call an LLM (CrewAI broken on Python 3.14)  │
│  ├── Write code to backend/ or frontend/         │
│  ├── Execute arbitrary commands                  │
│  ├── Git operations                              │
│  ├── Deploy or release                           │
│  └── Autonomous software development             │
│                                                   │
└─────────────────────────────────────────────────┘
```

### 10.2 Answer to the 10 verification points

| # | Question | Answer |
|---|----------|--------|
| 1 | **WF-01–WF-10 invoke actual CrewAI crews?** | **NO.** They define stages with agent references. The `CrewAIExecutor` exists but requires explicit gating. Even if gated, CrewAI fails to import. All existing runs use `MockAgentExecutor`. |
| 2 | **A01-A11 translated into executable CrewAI agents?** | **PARTIALLY.** `build_agent()` produces correct `crewai.Agent` objects. But these are only constructed when `CrewAIExecutor.execute()` is called, which never happens in practice. |
| 3 | **Backend/frontend agents can create/modify project files?** | **NO.** `artifact_write` is confined to a sandboxed task workspace. No tool can write to `backend/` or `frontend/`. |
| 4 | **Tool calls routed through ToolRegistry and permission checks?** | **YES.** Default-deny enforcement, `assert_allowed()` before every call, path containment, and command allowlist are all correctly implemented. |
| 5 | **Agent outputs validated and persisted?** | **YES.** `validate_output()` checks artifact type, structure, evidence paths. Run records persist to JSON with redaction. |
| 6 | **Workflow handoffs between agents?** | **MINIMALLY.** Via `advance_status` field. No cross-agent context or artifact passing — each stage starts fresh. |
| 7 | **Human approval gates interrupt correctly?** | **YES.** `ApprovalService.request()` → `decide()` correctly transitions state with matching `ApprovalDecision`. |
| 8 | **Execution records identify agents, model, provider, tool calls?** | **YES.** `RunRecord` includes `provider`, `model_config_id`, `stages[].agents[]`, `tool_operations[]`, `approvals[]`. |
| 9 | **Mock/stub vs live execution clearly distinguishable?** | **YES.** Mock outputs are `[STUB-SYNTHETIC]` labeled. `CrewAIExecutor` requires explicit gate. Run records show `provider`. |
| 10 | **MediCore/AMSDP execution histories provide evidence?** | **NO.** Zero evidence of CrewAI execution in MediCore or AMSDP. All code was written by Cline, not AILI agents. |

### 10.3 Final Verdict

> **AILI is NOT capable of autonomously performing software development through CrewAI agents in its current state.**
>
> The architecture, agent definitions, workflow definitions, tool registry, approval gates, and run recorder form a **complete and well-designed control framework**. However, three critical gaps prevent actual autonomous execution:
>
> 1. **CrewAI is broken** on the installed Python 3.14 (dependency incompatibility).
> 2. **No provider is configured** — no LLM credentials exist in the environment.
> 3. **No tool can write to project source code** — `artifact_write` is sandboxed to a task workspace.
>
> The AILI Factory is best described as a **comprehensive, well-tested orchestration and approval framework** that requires the deployment-gating steps to be completed and a source-code-write capability to be added before it can execute autonomous development work.

---

*Report produced by read-only inspection. No modifications to AILI or AMSDP were made.*
6. Executor choice determines whether CrewAI is invoked or canned output is returned.