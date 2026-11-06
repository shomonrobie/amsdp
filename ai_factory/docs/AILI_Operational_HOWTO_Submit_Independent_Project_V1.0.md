# AILI Operational Interface — How to Submit an Independent Project (V1.0)

> **Purpose:** Document the *existing, supported* mechanism for operating AILI
> directly (bypassing Cline as the developer). This is a read-only reference;
> no workflow was executed and no infrastructure was changed in producing it.
>
> **Audience:** Project operator who will communicate with AILI directly.
>
> **Supported environment:** `.venv313` (Python 3.13.15, CrewAI 1.15.35).
> The `.venv` (Python 3.14) environment is NOT supported (broken CrewAI 0.11.2).

---

## 1. Invoking the AILI interface

AILI exposes a Typer CLI. The reliable entry point is the module form (the
`aili` console script is declared but the package is not installed):

```bash
cd /home/shomonrobie/amsdp/ai_factory
export PYTHONPATH=src
alias aili="python -m amsdp_ai_factory"
```

Use the **`.venv313` interpreter** explicitly:

```bash
alias aili="/home/shomonrobie/amsdp/.venv313/bin/python -m amsdp_ai_factory"
```

Registered commands (confirmed by introspection of `cli.app.registered_commands`):

| Command | Signature |
|---------|-----------|
| `version` | () |
| `doctor` | () — environment/document validation |
| `docs_status` | () |
| `agents` | () |
| `workflows [workflow_id]` | list all 10, or detail one |
| `task_new` | `--title <t> [--workflow-id <id>] [--task-type <t>] [--description <d>]` |
| `task_list` | `[--status <s>]` |
| `task_show` | `<task_id>` |
| `run_workflow` | `<task_id> <workflow_id> [--mode stub\|live]` |
| `approve` | `<task_id> <decision> [--actor <a>] [--rationale <r>] [--run-id <id>]` |
| `resume` | `<task_id> [--mode stub\|live]` |
| `run_status` | `<run_id>` |

---

## 2. Registering / initializing a project workspace

**There is no separate "new project" command.** AILI operates within the
factory's configured directories, resolved from `FactorySettings` at the
resolved repository root (`/home/shomonrobie/amsdp`):

| Store | Path | Created by |
|-------|------|-----------|
| Task registry | `<repo_root>/var/tasks/` | `task_new` |
| Run records | `<repo_root>/runs/` | `run_workflow` |
| Task workspace | `<repo_root>/var/workspaces/<task_id>/` | `run_workflow` (auto-provisioned) |
| Patch snapshots | `<repo_root>/var/snapshots/` | `PatchTool.apply` |
| Applied-patch registry | `<repo_root>/var/applied_patches.json` | `PatchTool.apply` |

The **project workspace is created implicitly** by `WorkflowEngine.run()`,
which calls `ArtifactStore(workspace_root, task_id).ensure()` before any stage
executes. To "initialize" a project:

1. `task_new --title "<project title>" --workflow-id WF-01 --task-type "independent_project" --description "<one line>"`
   → prints `created task <task_id> status=proposed`.
2. The workspace directory `<repo_root>/var/workspaces/<task_id>/` is created
   at first `run_workflow`, not at registration.

> **Boundary note:** AILI's isolated write/artifact scope is the task workspace
> under `<repo_root>/var/workspaces/<task_id>/`, not an arbitrary external
> directory. An "independent" project therefore lives inside that workspace
---

## 3. Submitting a project-level requirement

The requirement is attached to the task record. Two supported routes:

**Route A — CLI (`task_new`):**

```bash
aili task_new \
  --title "Code Lint Dashboard" \
  --workflow-id WF-01 \
  --task-type "feature" \
  --description "Independent tool: scan Python files, store results in SQLite, serve a web UI."
```

`TaskRegistry.create()` assigns a stable `task_id` (pattern `TASK-…`) and
persists the record. Effective fields carried on the task:
`task_id, title, description, task_type, priority, status=proposed,
workflow_id, service, scope{included/excluded}, acceptance_criteria,
constraints, prohibited_actions`.

**Route B — Python API (equivalent, for tooling):**

```python
from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.tasks.models import Task

s = FactorySettings()
reg = TaskRegistry(s.task_store_path())
task = reg.create(Task(
    title="Code Lint Dashboard",
    workflow_id="WF-01",
    task_type="feature",
    description="…",
))
```

Verify: `aili task_show <task_id>` or `aili task_list`.

> **Current limitation:** there is no dedicated CLI flag for
> `acceptance_criteria`, `constraints`, or `scope.included/excluded`; these
> must be set via the Python API if you want them registered up front.

---

## 4. Initiating the requirement-analysis and architecture workflow

Requirement analysis + architecture is **WF-01 (Requirement-to-Design)**.
Its confirmed stage map:

| Stage | Kind | Agent(s) | Output kind | Gate |
|-------|------|----------|-------------|------|
| wf01_s1 | agent | A01 | `requirement_analysis` | — |
| wf01_s2 | agent | A02 | `architecture_proposal` | — |
| wf01_s3 | agent | A03 | `service_implementation_plan` | — |
| wf01_s4 | agent | A04 | `database_change_proposal` | — |
| wf01_s5 | agent | A05 | `api_contract` | — |
| wf01_s6 | agent | A08 | `test_plan` | — |
| wf01_s7 | agent | A09 | `security_review` | — |
| wf01_s8 | gate | — | — | `human_design_approval` |

Initiate it:

```bash
# stub mode (no live LLM; uses [STUB-SYNTHETIC] outputs)
aili run_workflow <task_id> WF-01 --mode stub

# live mode (requires the gate + key)
export AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1
export OPENROUTER_API_KEY=sk-or-v1-…   # from your process env, never persisted
aili run_workflow <task_id> WF-01 --mode live
unset AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED
```

The run advances stages in order, records each, and **pauses at wf01_s8** with
`run.status = awaiting_approval`.

Other executable workflows (for later): WF-02 Service Implementation,
WF-03 Frontend Delivery, WF-04 Defect Resolution, WF-05 Architecture
Decision, WF-06 Database Change, WF-07 Security Review, WF-08
Cross-Service Integration, WF-09 Release Readiness, WF-10 Documentation
Update. Inspect any with `aili workflows <id>`.
---

## 5. Inspecting execution records and generated artifacts

| What | Command / Path |
|------|----------------|
| Run record (stages, statuses) | `aili run_status <run_id>` |
| All runs for a task | Python: `RunRecorder(<run_store>).list(task_id=...)` |
| Raw run JSON (full fidelity: checks, approvals, logs) | `<repo_root>/runs/<run_id>.json` |
| Task record (state, history, approval state) | `aili task_show <task_id>` |
| Workspace artifact files | `<repo_root>/var/workspaces/<task_id>/**` |
| Approved decisions | Included in the run JSON under `approvals: []` |

Artifacts produced per stage are registered via `ArtifactStore` and serialized
into run records only as **paths + SHA-256** (the raw content stays in the
workspace files). Use:

```python
from amsdp_ai_factory.runs.recorder import RunRecorder
run = RunRecorder("/home/shomonrobie/amsdp/runs").get(run_id)
for st in run.stages:
    print(st.stage_id, st.status.value, st.artifacts)
```

---

## 6. Human approval gates — present and approve

**Presentation:** after `run_workflow` pauses, the CLI prints:

```
run <run_id> status=awaiting_approval
paused at a human gate; decide with: approve --task-id <id> \
  --decision approved|rejected|changes_requested
```

The full pending list is not exposed as a CLI command; it is available via
`ApprovalService.pending()`:

```python
from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.approvals.service import ApprovalService
s = FactorySettings()
svc = ApprovalService(TaskRegistry(s.task_store_path()), RunRecorder(s.run_store_path()))
for p in svc.pending():
    print(p.as_dict())
```

**Approval (CLI):**

```bash
aili approve <task_id> approved --actor project_owner --run-id <run_id> \
  --rationale "Design package reviewed and accepted"
```

Valid decisions: `approved` | `rejected` | `changes_requested` (mapped to
`ApprovalDecision`). The decision is applied via the lifecycle state machine
(`transition()`), so **only the expected gate decision is legal** — a
`rejected`/`changes_requested` at a design gate routes back appropriately.

**Resume after approval:**

```bash
aili resume <task_id> --mode live   # or --mode stub
```

A run still `awaiting_approval` cannot be resumed until decided (enforced).
---

## 7. Applying patches to the project workspace (authorization model)

This is the **most constrained** part. Precisely what exists today:

| Piece | Status |
|-------|--------|
| `PatchTool` class (generate/verify_approval/apply/rollback, replay journal, backups, scope map `AGENT_SCOPES`) | ✅ Implemented + 272 tests |
| Tool registration `patch_generator` (category WRITE, enabled, bound to A04/A06/A07/A08/A10/A11) | ✅ Registered in `tool_registry.py` |
| Agent `permitted_tools` include `patch_generator` | ✅ (A04/A06/A07/A08/A10/A11) |
| **Engine tool dispatch for `patch_generator`** | ❌ **Not wired.** `WorkflowEngine._run_tool_stage()` only dispatches `doc_link_validator` |
| **CLI command to apply a patch** | ❌ **None exists.** `PatchTool` is not invoked by any CLI command |
| **Executor calling PatchTool** | ❌ **None.** Live/stub executors never touch PatchTool |

**What this means operationally:** the *authorization mechanism* is designed
and unit-tested (approval record must carry `patch_sha256=<hash> repo=<id>`;
application refuses unless that approval exists; files/baseline are
re-verified at apply time; failed applies roll back). **But there is currently
no supported CLI/API route that causes AILI to call `PatchTool.apply()` in a
workflow.** The planned (not yet executable) flow is:

1. Agent writes generated code into its task workspace
   (`var/workspaces/<task_id>/<scope>/`).
2. `PatchTool.generate(workspace, scope, agent_id)` produces a `PatchSet`
   (read-only).
3. The operator approves with a rationale that embeds the exact patch hash:
   ```bash
   aili approve <task_id> approved \
     --rationale "patch_sha256=<hash> repo=<repo-id> reviewed and approved"
   ```
4. `PatchTool.apply(patch_set, approvals)` writes only inside the agent's
   permitted scope (`AGENT_SCOPES`), only after verifying approval hash
   binding, unchanged target files, and current baseline, and only after
   durably saving the applied-patch record with rollback-on-failure.

**To exercise this today** it must be driven from Python directly (not through
the CLI), e.g.:

```python
from pathlib import Path
from amsdp_ai_factory.tools.patch_tool import PatchTool

pt = PatchTool(Path("/home/shomonrobie/amsdp"))          # project root
res = pt.generate(workspace=Path("/home/shomonrobie/amsdp/var/workspaces/<task_id>"),
                  scope="backend", agent_id="A06", task_id="<task_id>", run_id="<run_id>")
# operator reads res.output, approves, then calls pt.apply(patch_set, approvals)
```

**Until the engine dispatch + CLI are wired, do NOT expect a workflow to
produce a project patch on its own.** This is the key gap between the control
framework (done) and end-to-end autonomous application (not yet wired), and
it is the reason AILI is still classified as "orchestration + approval
framework" rather than a fully autonomous code writer.

---

## 8. Confirmed configuration constants (as inspected)

- `repo_root`: `/home/shomonrobie/amsdp`
- `task_store_dir`: `var/tasks`
- `run_store_dir`: `runs`
- `workspace_root`: `var/workspaces`
- Live gate: `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1` (process env only)
- Provider/model (from `ai_factory/.env`): `openrouter` /
  `deepseek/deepseek-v4-flash`
- Retry policy: bounded, `default_max_retries=2`, workflow-engine level only;
  the live executor makes exactly one `crew.kickoff()` per stage with no retry.

---

## 9. Quick-start checklist (operator → AILI)

```bash
export PYTHONPATH=/home/shomonrobie/amsdp/ai_factory/src
alias aili="/home/shomonrobie/amsdp/.venv313/bin/python -m amsdp_ai_factory"

# 1. Register project requirement
aili task_new --title "Code Lint Dashboard" --workflow-id WF-01 \
  --task-type independent_project --description "…"

# 2. (Optional) inspect available workflows + agents
aili workflows; aili agents

# 3. Run requirement → design (live, with your key exported)
export AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1
aili run_workflow <task_id> WF-01 --mode live
unset AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED

# 4. Inspect
aili run_status <run_id>
#    full JSON at $PWD/runs/<run_id>.json, artifacts at var/workspaces/<task_id>/

# 5. Approve the design gate
aili approve <task_id> approved --actor project_owner --run-id <run_id> \
  --rationale "design approved"

# 6. Resume / continue with implementation workflows
aili resume <task_id> --mode live
```

---

*Documentation only — no workflow executed, no AILI or AMSDP infrastructure
modified.*
> boundary until patch application (Section 7) targets a permitted scope.