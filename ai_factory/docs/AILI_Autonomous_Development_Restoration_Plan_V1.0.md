# AILI Autonomous Development Restoration Plan — V1.0

> **Date:** 2026-11-05  
> **Status:** Planning — no modifications made.  
> **Scope:** Environment reconciliation, architecture design, implementation phases, and acceptance criteria for restoring AILI's autonomous development capability.

---

## Phase A: Environment Reconciliation

### A.1 Virtual environment discovery

| Environment | Path | Python Version | Created By | Status |
|-------------|------|----------------|-----------|--------|
| `.venv` | `/home/shomonrobie/amsdp/.venv` | **3.14.4** | `python3 -m venv` | ❌ CrewAI 0.11.2 broken |
| `.venv313` | `/home/shomonrobie/amsdp/.venv313` | **3.13.15** | `uv 0.12.7` | ✅ CrewAI 1.15.35 works |

### A.2 CrewAI installation details

| Property | `.venv` (3.14) | `.venv313` (3.13) |
|----------|----------------|-------------------|
| CrewAI version | **0.11.2** | **1.15.35** |
| Import status | ❌ Fails (`docstring_parser` → `ast.NameConstant` removed in Python 3.14) | ✅ Works |
| AILI factory import | ❌ Fails at `build_crews.py: from crewai import Agent` | ✅ Succeeds |
| `pyproject.toml` compatibility | ❌ `crewai>=1.15.35` not satisfied | ✅ `crewai>=1.15.35,<2.0.0` satisfied |

### A.3 Root cause: Python 3.14.4 incompatibility

The `.venv` environment (Python 3.14.4) was used throughout the session. The `docstring_parser` package (a transitive dependency of `instructor` → `crewai`) references `ast.NameConstant`, which was **removed from Python 3.14's `ast` module**. This is a Python 3.14 breaking change that upstream packages have not yet addressed for CrewAI 0.11.2.

### A.4 CrewAI 1.15.35 API compatibility verification

Tested against `.venv313/bin/python3.13`:

| Operation | Status | Evidence |
|-----------|--------|----------|
| `from crewai import Agent` | ✅ | Works |
| `from crewai import Crew` | ✅ | Works |
| `from crewai import Task` | ✅ | Works |
| `from crewai import Process` | ✅ | Works |
| `from crewai import CrewOutput` | ✅ | Works |
| `Agent(role=..., goal=..., backstory=..., verbose=False, memory=False, allow_delegation=False, llm="gpt-4")` | ✅ | `a.llm.model` returns `"gpt-4"` |
| `Task(description=..., expected_output=..., agent=agent)` | ✅ | Works |
| `Crew(agents=[a], tasks=[t], process=Process.sequential)` | ✅ | Works |
| `CrewOutput.raw` and `.pydantic` | ✅ | Present in model fields |
| AILI `CrewAIExecutor` import | ✅ | `from amsdp_ai_factory.execution.live import CrewAIExecutor` succeeds |

**Verdict: The existing `build_crews.py` and `live.py` code is fully compatible with CrewAI 1.15.35.** No code changes are required for the basic execution path.

### A.5 Recommendation

| # | Action | Rationale |
|---|--------|-----------|
| 1 | **Switch AILI execution to `.venv313` (Python 3.13.15)** | CrewAI 1.15.35 works, satisfies `pyproject.toml`, existing code is compatible |
| 2 | **Remove CrewAI 0.11.2 from `.venv`** | Prevents accidental import of the broken version |
| 3 | **Update `ai_factory/pyproject.toml` pins** | Already correct (`crewai>=1.15.35,<2.0.0`) |
---

## Phase B: Autonomous Development Architecture

### B.1 High-level design

```
 HUMAN INPUT (task request)
       │
       ▼
  ┌──────────────────────────────┐
  │  WorkflowEngine.run(task,    │
  │    workflow_id, executor)     │
  │  executor = CrewAIExecutor(  │
  │    settings)                  │
  └────────┬─────────────────────┘
           │
       ┌───┴──────────┐
       ▼              ▼
  ┌──────────┐   ┌──────────────┐
  │  Agent   │   │  LLM Provider│
  │  Stages  │──>│  (configured │
  │ (A01-A11)│   │   via env)   │
  └────┬─────┘   └──────────────┘
       │
       ▼
  ┌────────────────────────────────────┐
  │  Isolated Task Workspace           │
  │  var/workspaces/<task_id>/         │
  │  ├── source/  ← code generation    │
  │  ├── tests/   ← test execution     │
  │  ├── docs/    ← documentation      │
  │  └── patches/ ← generated diffs    │
  └────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────┐
  │  Validation Pipeline             │
  │  ┌─────────┐  ┌─────────┐       │
  │  │ Tests   │→│ Security│→ ...   │
  │  └─────────┘  └─────────┘       │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────┐
  │  Human Gate: Diff + Approve  │
  │  ApprovalService.decide()    │
  └──────────────┬───────────────┘
                 │ (if approved)
                 ▼
  ┌──────────────────────────────┐
  │  Apply Changes to Target     │
  │  PatchTool.apply_patch()     │
  │  RunRecorder records all     │
  │  Rollback snapshot preserved │
  └──────────────────────────────┘
```

### B.2 Component changes

#### B.2.1 CrewAI executor (existing `live.py` — no changes needed)

| Component | Assessment | Changes Required |
|-----------|-----------|-----------------|
| `CrewAIExecutor._assert_gate()` | Same two-gate system works with `.venv313` | None |
| `CrewAIExecutor.execute()` | Builds crew, kicks off, validates | None |
| `build_agent()` | Creates `crewai.Agent` — compatible with 1.15.35 | None |
| `build_stage_task()` | Creates `crewai.Task` — compatible | None |
| `build_single_stage_crew()` | Creates `crewai.Crew` — compatible | None |

#### B.2.2 LLM provider configuration

| Setting | Status | Required Value |
|---------|--------|----------------|
| `AMSDP_FACTORY_MODEL_PROVIDER` | Not set | e.g., `openai`, `ollama` |
| `AMSDP_FACTORY_MODEL_ID` | Not set | e.g., `gpt-4`, `ollama/llama3` |
| `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED` | Not set | `1` |
| Provider API key | Not stored | **Read from process env only** (never in AILI) |

**Security:** API keys are NEVER in AILI config, settings, or run records. The `RunRecorder` redaction layer strips secret-shaped values before persistence.
#### B.2.3 Cross-agent context passing

| Current | Required Change |
|---------|-----------------|
| Workflow stages have `expected_output_kinds` and `required_input_kinds` but no data flows | Add a **RunContext** dict that accumulates outputs from completed stages |
| `build_stage_task()` uses only `context_summary` from execution request | Inject previous stage outputs into task description |

**Proposed `RunContext` class:**

```python
class RunContext:
    def __init__(self):
        self.stage_artifacts: dict[str, AgentOutput] = {}

    def record(self, stage_id: str, output: AgentOutput):
        self.stage_artifacts[stage_id] = output

    def context_for(self, stage) -> str:
        parts = []
        for kind in stage.required_input_kinds:
            for sid, output in self.stage_artifacts.items():
                if output.artifact_type == kind:
                    parts.append(f"From {sid}: {output.title} — {output.summary}")
        return "\n".join(parts) if parts else ""
```

#### B.2.4 Project source-code modification (PatchTool)

The **most critical new capability**: patch-based generation + human-gated application.

| Step | Component | Description |
|------|-----------|-------------|
| 1 | Isolated workspace | Agent writes code to `var/workspaces/<task_id>/source/` via `artifact_write` |
| 2 | Patch generation | `PatchTool.generate()` compares workspace vs project → unified diffs |
| 3 | Validation | `run_tests`, `static_analysis`, `secret_scan` on generated code |
| 4 | Human review | Patch presented as unified diff |
| 5 | Human approval | Via `ApprovalService.decide()` with `ApprovalDecision.APPROVED` |
| 6 | Apply | `PatchTool.apply_patch()` writes to actual project files |

**Security gates for `apply_patch()`:**
1. Agent must have `patch_generator` in `permitted_tools`
2. `ToolRegistry.assert_allowed(agent_id, "patch_generator")` must pass
3. Human `ApprovalRecord` with `decision=APPROVED` must exist for the task
4. Patch must reference only files within agent's scope
5. Rollback backup created before applying

#### B.2.5 Agent write permission expansion

| Agent | Write prefix (workspace) | Patch scope (project) |
|-------|-------------------------|----------------------|
| A06 Backend Developer | `code` | `backend/<service>/` |
| A07 Frontend Developer | `frontend` | `frontend/pages/` |
| A08 QA Engineer | `tests` | `backend/*/tests/` |
| A04 Database Architect | `docs/database` | `backend/*/migrations/` |
| A10 DevOps Engineer | `ops` | `backend/*/Dockerfile`, config files |
| A11 Technical Writer | `docs` | `docs/*` |

---

## Phase C: Security Architecture

### C.1 The agent-to-application chain

```
AGENT GENERATES CHANGES
→ ISOLATED WORKSPACE (artifact_write: var/workspaces/<task>/)
→ VALIDATION (run_tests, static_analysis, secret_scan)
→ SECURITY REVIEW (A09 agent + automated checks)
→ PATCH GENERATION (PatchTool.generate: workspace vs project)
→ HUMAN DIFF REVIEW (patch presented as formatted diff)
→ HUMAN APPROVAL (ApprovalService.decide: APPROVED)
→ APPLY CHANGES (PatchTool.apply_patch: writes to project)
→ ROLLBACK ON FAILURE (snapshot restored)
→ AUDIT RECORD (RunRecorder: agent, patch, approval, artifacts)
```

### C.2 Security controls matrix

| Control | Implementation | Bypass Prevention |
|---------|---------------|-------------------|
| No direct filesystem writes | Agents use `artifact_write` → workspace only | `PatchTool.apply_patch()` is the **only** code path that writes to project files |
| No unrestricted shell | `run_tests` allowlist (3 commands) | No `shell` tool exists or will be added |
| No autonomous git/deploy | No git or deploy tools exist | Intentionally omitted from all agent definitions |
| Patch scope enforcement | Patch tool validates file paths per agent | A06 → `backend/*`; A07 → `frontend/*` |
| Human gate before project write | ApprovalService | `apply_patch()` checks for approval record before executing |
| Rollback | Pre-apply snapshot | Backup in `var/snapshots/<run_id>/` |
| Credential isolation | API keys from env only | FactorySettings does not store keys; RunRecorder redacts |
| No real patient data | Existing rule | Enforced in prompt templates and lifecycle |

### C.3 What PatchTool must NOT do

| Prohibited | Enforcement |
|-----------|-------------|
| Delete files | Refuse patches that remove files; only create/modify allowed |
| Write outside scope | Path prefix validation per agent |
| Overwrite without backup | Create `var/snapshots/<run_id>/<file>.bak` before writing |
| Change git history | No git operations in tool |
| Modify CI/CD pipelines | No tool writes to `.github/` or `docker-compose.yml` |
| Install packages | `run_tests` allowlist prevents arbitrary commands |
---

## Phase D: Graduation Project Proposal

### D.1 Project overview

| Property | Value |
|----------|-------|
| Name | **"Code Lint Dashboard"** — standalone micro-monitoring tool |
| Why not AMSDP? | First live CrewAI execution must be independent of existing work |
| Type | Single microservice with web UI |
| Tech stack | Python FastAPI + SQLite + HTML/JS (same as AMSDP — familiar to agents) |
| Location | `projects/code-lint-dashboard/` (new directory, no risk to existing code) |

**Functionality:** Scan Python files for lint issues, store in SQLite, serve web UI with statistics.

### D.2 Agent-workflow mapping

| Stage | Agent | Deliverable | Demonstrates |
|-------|-------|-------------|-------------|
| WF-01 S1 | A01 | Requirement analysis | Real LLM output |
| WF-01 S2 | A02 | Architecture proposal | Real LLM output |
| WF-01 S4 | A04 | DB schema + migration SQL | Real LLM + DB tool validation |
| WF-01 S5 | A05 | OpenAPI spec | Real LLM + contract validation |
| WF-01 S8 | Human | Design approval | **HUMAN GATE** |
| WF-02 S1 | A06 | FastAPI service code | **CODE GENERATION** |
| WF-02 S2 | A06 | Self-check + tests | **TEST EXECUTION** |
| WF-02 S3 | A08 | Independent testing | **CROSS-AGENT HANDOFF** |
| WF-02 S5 | Human | Code diff review | **HUMAN GATE + CODE REVIEW** |
| WF-10 S1-4 | A11 | README + docs | Documentation update |
| WF-09 S1-4 | A09/A10/A11 | Release readiness | **AUDIT TRAIL** |

### D.3 Cross-agent context flow

| From | To | Artifact |
|------|----|----------|
| A01 | A02 | `requirement_analysis` |
| A02 | A04 | `architecture_proposal` |
| A04 | A05 | `database_change_proposal` |
| A05 | A06 | `api_contract` |
| A01+A05 | A08 | Requirements + API → test scenarios |
| A06 | A08 | `code_change_summary` |
| A06+A08 | A09 | Code + tests → security review |

### D.4 Graduation criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Real LLM execution | `CrewAIExecutor.execute()` calls `crew.kickoff()` with real model |
| 2 | Code in workspace | A06 calls `artifact_write`; files exist in `var/workspaces/<task>/source/` |
| 3 | Tests pass | `run_tests` returns `exit_code=0` |
| 4 | Patch generated | `PatchTool.generate()` produces unified diff |
| 5 | Human review | Human sees diff; triggers `ApprovalService.decide(APPROVED)` |
| 6 | Patch applied | `PatchTool.apply_patch()` writes to `projects/code-lint-dashboard/` |
| 7 | App works | Service starts; returns 200 |
| 8 | Run record complete | Contains agents, provider, tools, approval, artifacts |
| 9 | Rollback available | Snapshots in `var/snapshots/<run_id>/` |
---

## Implementation Plan

### Phase I: Environment Setup (~0.5 day)
1. Activate `.venv313` for AILI execution — Low risk
2. Remove CrewAI 0.11.2 from `.venv` — Low risk
3. Ensure `.venv313` has all deps (pydantic, typer, etc.) — Low risk
4. Verify AILI tests pass via `.venv313` — Medium risk

### Phase II: Tool Additions (~2-3 days)
1. Implement `PatchTool` class — Medium risk (path validation logic)
2. Register `patch_generator` in tool_registry — Low risk
3. Add tool to A06/A07/A08/A10/A11 permitted_tools — Low risk
4. Gate patch application on human approval — Medium risk
5. Add rollback snapshot mechanism — Medium risk
6. Unit tests for PatchTool — Medium risk (diff comparison)

### Phase III: Context Passing (~1-2 days)
1. Implement `RunContext` class — Low risk
2. Integrate into `WorkflowEngine._run_stage()` — Low risk
3. Integrate into `build_stage_task()` — Low risk
4. Update workflow `required_input_kinds` — Low risk

### Phase IV: LLM Configuration (~0.5 day)
1. Document provider setup in `.env.example` — Low risk
2. Create `.env` with AMSDP_FACTORY_* settings — Low risk
3. Test `CrewAIExecutor.execute()` with real model — Medium risk

### Phase V: Graduation Project (~3-5 days)
1. Run WF-01 through mock executor first — Low risk
2. Run WF-01 through CrewAIExecutor with real LLM — **High risk** (first live)
3. Iterate on prompt quality — Medium risk
4. Run WF-02 for code generation (A06) — **High risk** (first code gen)
5. Apply patches — **High risk** (first file modification)
6. Verify application works — Medium risk

### Phase VI: Hardening (~2-3 days)
1. Agent execution logging — Low risk
2. Run record browser CLI — Low risk
3. Failure notification — Low risk
4. Stress test multiple tasks — Medium risk

---

## Dependencies and Risks

### Dependencies

| # | Dependency | Status |
|---|------------|--------|
| 1 | Python 3.13.15 (`.venv313`) | ✅ Ready |
| 2 | CrewAI 1.15.35 | ✅ Installed |
| 3 | LLM provider API key | ❌ Not configured |
| 4 | Pydantic >=2.12 | ✅ Installed |
| 5 | OpenAI SDK (CrewAI bundled) | ✅ Transitive dep |
| 6 | pytest / unittest | ✅ Available |

### Risk matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| CrewAI 1.15.35 incompatible with build_crews | Low | High | ✅ Already verified compatible |
| LLM output quality too low | Medium | High | Start simple; iterative prompts |
| LLM API cost | Medium | Low | Use Ollama (local) for iteration |
| PatchTool bypass | Low | Critical | Multiple gates: permission + approval + scope |
| Context too large for prompt window | Medium | Medium | Summarize; truncate at 8000 chars |
| `.venv313` not activated | Medium | Medium | Document in Makefile |
| Project scope creep | Medium | Low | Strict acceptance criteria |
| Human reviewer unavailable | Medium | High | CLI pending-approvals command |

### Estimated effort: ~12-14 days total (~8-12 critical path)

---

## Acceptance Criteria

| # | Criterion | Phase | Status |
|---|-----------|-------|--------|
| A | `.venv313` as AILI execution environment | Phase I | ✅ Verified |
| B | `CrewAIExecutor` builds crews with 1.15.35 | Phase I | ✅ Verified |
| C | `PatchTool` implemented with scope validation | Phase II | ❌ Pending |
| D | `RunContext` implemented and wired | Phase III | ❌ Pending |
| E | LLM provider configured (env vars only) | Phase IV | ❌ Pending |
| F | Graduation project delivered by AILI | Phase V | ❌ Pending |
| G | Run record shows: providers, agents, tools, approvals | Phase V | ❌ Pending |
| H | Rollback of graduation project verified | Phase V | ❌ Pending |
| I | AMSDP dev through AILI not started until (F)+(G) pass | Governance | Constraint |

---

*This plan is a proposal. No modifications to AILI or AMSDP have been made.*
| 4 | **No build_crews.py or live.py changes needed** | API surface is compatible |