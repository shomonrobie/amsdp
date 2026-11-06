# AILI Live-Run Verification Report (Stub-Based)

> **Verification date:** 2026-11-06
> **CrewAI:** 1.15.35
> **Model/Provider:** deepseek/deepseek-v4-flash / OpenRouter (configured, not called)
> **Verification type:** End-to-end stub — exercises every production code path
>                    except crew.kickoff(), which requires a live provider API key.
>
> **Environment:** .venv313 (Python 3.13.15), no OpenRouter API key available

---

## 1. What was verified

The stub-based verification (`tests/integration/test_live_verification_stub.py`, 16 tests)
exercises the **identical production code path** used by a live run, replacing only
the provider call with a proven `MockAgentExecutor`:

| Step | Production path | Status |
|------|----------------|--------|
| Engine aggregates run-level agents | `run()` → `_stage_agent_participants()` → `new_run(agents=...)` | ✅ |
| Stage starts with agents | `start_stage(agents=...)` | ✅ |
| Focus scope for assessments | `_assessment_focus()` → `ExecutionRequest.focus_scope` | ✅ |
| Task has output_pydantic | `build_stage_task()` sets both fields | ✅ |
| Description has focus_scope | embedded from request | ✅ |
| Structured output extraction | `_extract_validated_output()` | ✅ |
| Artifact schema validation | `validate_output()` in mock executor | ✅ |
| Evidence path verification | `ArtifactStore.verify()` containment + existence | ✅ |
| Run recorder persists metadata | `get()` returns full record | ✅ |
| No source file modifications | sha256 before/after match | ✅ |
| Engine rejects unknown workflow | raises Exception | ✅ |
## 2. What could NOT be verified

The single step requiring a live provider API key:

- **CrewAI `crew.kickoff()`** — connects to OpenRouter/DeepSeek and returns
  a `CrewOutput`. Without `OPENROUTER_API_KEY` in the process environment,
  this call fails at `LLM` construction time.

  The live-executor wrapper (`CrewAIExecutor.execute`) and the extractor
  (`_extract_validated_output`) were exercised in isolation (tests 10-12).
  The remaining gap is the **integration of `crew.kickoff()` + `_extract_validated_output()`
  with an actual provider response**.

## 3. Acceptance criteria

| Criterion | Met | Evidence |
|-----------|-----|----------|
| A01 completes successfully | ✅ (stub) | test_08 run status=succeeded |
| RequirementAnalysis is valid | ✅ | schema validation passes |
| Run + stage agent records populated | ✅ | tests 06-07, agent_id=A01 |
| Evidence provenance recorded | ✅ | test_13 passes |
| No app source modifications | ✅ | test_15 sha256 unchanged |
| Regression tests green | ✅ | 318/318 pass (37 unit + 13 integration) |

### 3.1 Remaining limitation

A live rerun of WF-01 with an injected `OPENROUTER_API_KEY` is needed to
confirm `crew.kickoff()` + `_extract_validated_output()` integration with
an actual DeepSeek response. The stub proof covers every other code path,
but the provider response shape can only be validated by a live call.

## 4. Test inventory

```
Unit modules:        37
Integration modules: 13
Total executed:      318
Passed:              318
Failed:              0
Errors:              0
```

### New tests (16 in `test_live_verification_stub.py`)

01-02 focus_scope; 03-04 output_pydantic; 05 agent_participants;
06-07 run+stage agent records; 08-09 artifact validation;
10-12 _extract_validated_output; 13 evidence paths;
14 metadata persistence; 15 no-source-modification;
16 engine rejects unknown workflow.

### Previously added (16 in `test_regression_structured_output_agent_persistence.py`)

D1-D6 structured output hardening, DSML markup, agent persistence,
single-shot executor -- all pass.

## 5. How to run the live verification

```bash
export OPENROUTER_API_KEY="sk-or-v1-<your-key>"
cd ai_factory
PYTHONPATH=src python -m unittest discover -s tests -t . -v
```

No OpenRouter API key was found in the environment. The `.env` file at
`ai_factory/.env` documents this requirement and contains a placeholder.

## 6. Files changed (this verification cycle)

| File | Change |
|------|--------|
| `tests/integration/test_live_verification_stub.py` | New -- 16 end-to-end tests |
| `docs/AILI_LiveRun_Verification_Report_V1.0.md` | This report |

No AMSDP application source, database, Docker, or AILI framework source
was modified. No PatchTool enabled. No commit or push made.