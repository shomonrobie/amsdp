# AI Factory Decision Record

Living record of implementation decisions for the AMSDP AI Factory.
Precedence conflicts with the approved governing documents are resolved per
the AI Factory Implementation Prompt V1.0 and the source-of-truth
hierarchies in the approved documents.

## ADR-AF-001 — Package layout (approved 2026-11-04)

- Decision: implement the AI Factory as an installable Python package under
  `ai_factory/src/amsdp_ai_factory/` with tests under `ai_factory/tests/`.
- Rationale: the Implementation Prompt's suggested layout (`src/`
  package) makes the package importable, testable with `PYTHONPATH=src`,
  and keeps module boundaries clear; the AI Factory Architecture document's
  flat layout (`agents/`, `crews/`, `workflows/` at the top level) is
  explicitly a "proposed logical layout" to be reconciled with the real
  repository. Both documents defer to the actual repo.
- Consequence: top-level packages inside `src/amsdp_ai_factory/` are
  `config`, `context`, `contracts`, `agents`, `crews`, `workflows`,
  `tasks`, `tools`, `approvals`, `runs`, `validation`, and `utils`.
- Status: recorded and approved.

## ADR-AF-002 — Test framework (approved 2026-11-04)

- Decision: standard-library `unittest` only. No pytest, ruff, mypy, or
  other third-party tooling at this stage.
- Rationale: `.venv313` contains no test tooling; the repo has no existing
  dependency manifest or strategy; the human authorizes zero new package
  installations.
- Test command: `cd ai_factory && PYTHONPATH=src .venv313/bin/python -m
  unittest discover -s tests -p 'test_*.py' -v`.

## ADR-AF-003 — Governing documents authority mapping (approved 2026-11-04)

Authority order used by context loading and validation (lowest number is
highest authority), aligned to the source-of-truth hierarchies in the AI
Agent Specification V1.0 §2.1 and AI Development Workflow V1.0 §2.1:

| Order | Role | Path | Category |
|------:|------|------|----------|
| 1 | business_rules | `docs/product/AMSDP_Business_Rules_V1.0.md` | mandatory |
| 2 | mvp_scope | `docs/product/AMSDP_MVP_SCOPE_V1.0.md` | mandatory |
| 3 | system_architecture | `docs/architecture/AMSDP_System_Architecture_V1.0.md` | mandatory |
| 4 | factory_architecture | `docs/architecture/AMSDP_AI_Factory_Architecture_V1.0.md` | mandatory |
| 5 | agent_specification | `docs/architecture/AMSDP_AI_Agent_Specification_V1.0.md` | mandatory |
| 6 | development_workflow | `docs/architecture/AMSDP_AI_Development_Workflow_V1.0.md` | mandatory |
| 7 | implementation_prompt | `docs/architecture/AMSDP_AI_Factory_Implementation_Prompt_V1.0.md` | reference |
| 8 | feature_list | `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` | reference (draft status retained) |
| 9 | product_vision | `README.md` | reference |
| 10 | product_vision_note | `docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md` | reference |

- `AMSDP_MVP_SCOPE_V1.0.md` is the **authoritative product scope** and
  resolves the expected path `docs/product/scope.md`.
- README and the hackathon concept note are contextual references for
  product vision only; they resolve the expected path
  `docs/product/product-vision.md`.
- The approved Business Rules and System Architecture remain authoritative.
- Contextual references can never override approved specifications. The
  authority order is enforced by the context selector and recorded in every
  document record.

## ADR-AF-004 — Environment (approved 2026-11-04)

- `.venv313` (Python 3.13.15, CrewAI 1.15.35, pydantic 2.12.5) is the
  supported Factory environment. `.venv` (Python 3.14.4) is not used and
  not modified.
- Configuration is environment-driven through the `AMSDP_FACTORY_*`
  prefix; `.env.example` holds placeholders only.

## ADR-AF-005 — Guardrails (approved 2026-11-04)

Mandatory for all phases: no Git commits/pushes/branch changes; no
modifications to approved baseline documents; no backend/frontend runtime
implementation; no package installations without approval; no paid model
calls in tests; no secrets in logs or records.

## ADR-AF-006 — Task registry persistence (implemented 2026-11-04)

- Decision: one JSON file per task in `var/tasks/<task_id>.json` (atomic
  write via temp file + `os.replace`). Run records use the same pattern
  under `runs/RUN-<timestamp>-<n>.json`.
- Rationale: the AI Factory Architecture's recommended "structured local
  run records" and the MVP requirement for simple, inspectable, restart-safe
  persistence; no database is justified yet.
- The registry never deletes records; cleanup is a separate human-approved
  process.

## ADR-AF-007 — Task lifecycle state set (implemented 2026-11-04)

- Decision: the finite state machine from AI Development Workflow V1.0
  section 5 is implemented verbatim (PROPOSED → … → CLOSED plus
  NEEDS_CLARIFICATION / BLOCKED / CHANGES_REQUESTED / FAILED / REJECTED /
  CANCELLED / NOT_APPLICABLE).
- Human decision gates (HUMAN_DESIGN_APPROVAL, HUMAN_REVIEW,
  AWAITING_DEPLOYMENT_APPROVAL) are enforced in code: an `ApprovalRecord`
  whose decision matches the target state is required to leave a gate. A
  successful agent response can never mark these transitions.

## ADR-AF-008 — Structured output contracts (implemented 2026-11-04)

- Decision: 12 typed Pydantic artifacts in `contracts/outputs.py` (the
  eleven Implementation-Prompt artifact categories, with TestPlan and
  TestReport modeled separately). `validate_output()` checks structure and
  declared type; the workflow engine (Phase 4) still verifies evidence
  paths and test evidence before accepting a stage.

## ADR-AF-009 — Dependency verification gate (2026-11-04)

- Before Phase 2, an AST import-graph scan confirmed the package's only
  third-party imports are `pydantic` and `pydantic_settings`; both are
  declared in `ai_factory/pyproject.toml`, as are `crewai` (lazy import,
  live runs) and `typer` (Phase 5 CLI). No packages were installed.

## ADR-AF-010 — AILI product naming (approved 2026-11-04)

- Product identity: **AILI** (AI Laboratory for Intelligent Development).
- Technical Python package: `amsdp_ai_factory` (unchanged).
- Repository directory: `ai_factory/` (unchanged).
- Decision: naming/branding must never rename or restructure the working
  package or directory.

## ADR-AF-011 — Tool registry and default-deny (implemented Phase 3)

- `tools/tool_registry.py` defines 14 tools: 5 active (`repo_read`,
  `doc_reader`, `git_read`, `artifact_write`, `run_tests`) and 9 declared
  but disabled ("planned": `disposable_db`, `openapi_validator`,
  `contract_test_tool`, `migration_validator`, `secret_scan`,
  `static_analysis`, `architecture_validator`, `ci_config_validator`,
  `doc_link_validator`).
- Enforcement is in code (`assert_allowed`), not prompts only. No agent has
  deploy, network, production, or destructive capability.
- `validate_agent_tool_bindings` fails loudly if an agent references a tool
  that is unregistered or not bound to it.

## ADR-AF-012 — Approval service (implemented Phase 3)

- `approvals/service.py` is the only sanctioned route for human decisions:
  `request()` marks gates; `decide()` maps approved/rejected/
  changes-requested onto the lifecycle targets and applies them through
  `tasks.lifecycle.transition`, so the finite state machine and audit
  history remain authoritative. Decisions are persisted on the task and
  optionally appended to run records.

## ADR-AF-013 — Mock agent execution (implemented Phase 3)

- `execution/mock.py` executes agent stages from canned handlers, validates
  outputs via `contracts.outputs.validate_output`, and verifies every
  evidence path inside the task workspace. No model provider, network, or
  CrewAI `kickoff` is ever contacted, which is what keeps the entire test
  suite free of paid API calls.

## ADR-AF-014 — Workflow engine (implemented Phase 4)

- `workflows/engine.py` orchestrates ordered stages with input/output
  validation, human gates via ApprovalService, bounded retries, pause/
  resume, run recording, and mandatory `ToolRegistry` enforcement at every
  actual tool invocation. Execution is stage-based (one agent per stage),
  with crews defined for CrewAI rather than a per-workflow monolithic
  kickoff, preserving bounded, auditable control.

## ADR-AF-015 — Live (CrewAI) execution gating (implemented Phase 4)

- `execution/live.py` raises unless provider+model are configured AND
  `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1`. No silent provider fallback.
  The live path was implemented and gate-tested but intentionally not
  executed in Phase 4.

## ADR-AF-016 — Crew definitions (implemented Phase 4)

- `execution/build_crews.py` builds CrewAI Agent/Task/Crew objects from the
  approved definitions (no delegation, no memory, provider-gated). The six
  approved crews map to workflows per `docs/workflows.md`.

## ADR-AF-017 — Validator tools enabled (implemented Phase 4)

- `architecture_validator` (A02/A03) and `doc_link_validator` (A11) became
  active for the executable workflows (WF-01, WF-10). All other planned
  tools remain declared-but-disabled.

## ADR-AF-018 — Phase 5: six planned tools enabled (implemented 2026-11-04)

- `static_analysis` (A06, A09), `secret_scan` (A09), `disposable_db`
  (A04/A06/A08), `migration_validator` (A04), `contract_test_tool`
  (A05/A08), and `ci_config_validator` (A10) became active. All six use
  only stdlib or packages already in `.venv313` — zero new dependencies.

## ADR-AF-019 — Lifecycle extensions (implemented Phase 5)

- Added `ANALYSIS → IN_PROGRESS` and `ANALYSIS → RELEASE_READINESS` arcs to
  the lifecycle's allowed transitions, enabling direct paths from analysis
  to implementation and release-readiness stages.

## ADR-AF-020 — All ten workflows executable (Phase 5)

- WF-02 through WF-09 updated from `partial`/`planned` to `executable`
  following the tool enablements.