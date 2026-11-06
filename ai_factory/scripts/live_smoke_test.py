"""AILI single-request live smoke test (OpenRouter).

Executes EXACTLY ONE CrewAI agent + one task + one LLM request through
OpenRouter, requesting a small structured RequirementAnalysis.

This script is intentionally gated and must NOT be run without explicit
human approval for the first live LLM request.

Requirements enforced here:
- Exactly one agent (A01 Product Analyst) and one task.
- Exactly one LLM request via CrewAIExecutor.
- Model: deepseek/deepseek-v4-flash via OpenRouter (OpenAI-compatible).
- Produces a validated RequirementAnalysis artifact.
- Does NOT modify any target-project source file.
- Does NOT execute arbitrary shell commands.
- Reports success/failure, model identity, and validated output structure.
- Reads the API key ONLY from OPENROUTER_API_KEY in the process environment.
- NEVER prints, logs, or persists the API key (or any part of it).

Designed to be run from the ai_factory/ directory so the local `.env`
(model_provider/model_id) is discovered:
    cd ai_factory
    OPENROUTER_API_KEY=sk-or-v1-... AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1 \
        .venv313/bin/python scripts/live_smoke_test.py
"""

from __future__ import annotations

import os
import sys


def _require_live_gate() -> None:
    """Fail fast if the operator has not explicitly enabled live execution."""
    if os.environ.get("AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED", "") != "1":
        sys.exit(
            "REFUSING: AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1 must be set in the "
            "process environment before live execution. No LLM call was made."
        )


def _require_api_key() -> str:
    """Return the OpenRouter key from the environment without ever printing it."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit(
            "REFUSING: OPENROUTER_API_KEY is not set in the process environment. "
            "No LLM call was made."
        )
    stripped = key.strip()
    if stripped == "" or stripped.lower() in ("placeholder", "your-api-key"):
        sys.exit(
            "REFUSING: OPENROUTER_API_KEY is empty or a placeholder. "
            "No LLM call was made."
        )
    return key


def main() -> int:
    # Guard before importing anything that could construct an LLM.
    _require_live_gate()
    _require_api_key()

    # Disable interactive telemetry/trace-sharing prompts so the smoke test
    # runs non-interactively and shares nothing with CrewAI.
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

    # Import lazily AFTER the gate so a mistake never triggers a provider call.
    from amsdp_ai_factory.config.settings import FactorySettings
    from amsdp_ai_factory.execution.live import CrewAIExecutor
    from amsdp_ai_factory.execution.models import ExecutionRequest

    settings = FactorySettings()
    if not (settings.model_provider and settings.model_id):
        sys.exit(
            f"REFUSING: model_provider/model_id not configured "
            f"(provider={settings.model_provider!r}, model={settings.model_id!r}). "
            "Check ai_factory/.env. No LLM call was made."
        )
    if settings.model_provider.lower() != "openrouter":
        sys.exit(
            f"REFUSING: this smoke test is written for OpenRouter, but "
            f"model_provider={settings.model_provider!r}. No LLM call was made."
        )

    print(f"Model identity (non-secret): {settings.model_id!r}")
    print(f"Provider: {settings.model_provider!r}")

    executor = CrewAIExecutor(settings)
    request = ExecutionRequest(
        task_id="live-smoke-001",
        stage_id="s1",
        agent_id="A01",  # Product Analyst
        workflow_id="WF-01",
        expected_artifact_kind="requirement_analysis",
        context_summary=(
            "Smoke test: produce a minimal RequirementAnalysis for a tiny "
            "fictional feature. Use synthetic data only."
        ),
    )

    # EXACTLY ONE crew.kickoff() occurs inside execute().
    result = executor.execute(request)

    print("\n--- Smoke test result ---")
    print(f"ok: {result.ok}")
    if result.output is not None:
        out = result.output
        print(f"artifact_type: {out.artifact_type}")
        print(f"title: {out.title}")
        print(f"summary: {out.summary}")
        print(f"agent_id: {out.agent_id}")
        print(f"stage_id: {out.stage_id}")
        print("validated_output_structure: RequirementAnalysis")
    else:
        print(f"error: {result.error}")
    for check in result.checks:
        print(f"check[{check.name}].ok={check.ok}")

    # Never print the key or the raw LLM payload here.
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())