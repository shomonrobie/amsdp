# AI Factory Permissions

## Model

Default-deny, enforced in code by `tools/tool_registry.py`:

- `assert_allowed(agent_id, tool_id)` — denied unless the agent is bound and
  the tool is enabled. Raised BEFORE any tool invocation.
- `assert_binding(agent_id, tool_id)` — declared+bound check used at stage
  preflight for planned (disabled) tools, whose execution remains denied.

## Active tools (Phase 4)

| Tool | Category | Agents |
|---|---|---|
| `repo_read` | read | A01–A11 |
| `doc_reader` | read | A01–A11 |
| `git_read` | read (git) | A02, A03, A05, A06, A07, A08, A10, A11 |
| `artifact_write` | write (workspace, per-agent prefix) | A01–A11 |
| `run_tests` | execute (allowlisted, bounded) | A06, A07, A08, A10 |
| `architecture_validator` | validation | A02, A03 |
| `doc_link_validator` | validation | A11 |
| `static_analysis` | security (pattern-based) | A06, A09 |
| `secret_scan` | security (regex-based) | A09 |
| `disposable_db` | DB (SQLite in-memory) | A04, A06, A08 |
| `migration_validator` | validation (SQL structure) | A04 |
| `contract_test_tool` | validation (API contract diff) | A05, A08 |
| `ci_config_validator` | validation (CI workflow YAML) | A10 |

## Declared-but-disabled (planned) tool

`openapi_validator` — bound to A05, denied until enabled.

## Retry and iteration limits

Each stage attempts execution up to `default_max_retries` (default 2, configurable via `AMSDP_FACTORY_DEFAULT_MAX_RETRIES`). Repeated failure moves the task to `FAILED`/`BLOCKED`. The engine records every attempt in the run record (retry count per stage) and in the task's `failure_info`.

## Write prefixes

A01→requirements · A02→architecture · A03→service-specs · A04→database ·
A05→contracts · A06→code · A07→frontend · A08→tests · A09→security ·
A10→infrastructure · A11→docs.

## Denied for everyone

Production access, deployment, network, unrestricted shell/filesystem,
Git writes, secret stores, real patient data.