"""CrewAI crew builders (provider-gated; definitions only).

Builds CrewAI ``Agent``/``Task``/``Crew`` objects from the approved agent
definitions. Construction is safe; executing a crew requires the live
executor's explicit authorization gate.

Provider-specific LLM configuration:
- ``openrouter``: constructs a CrewAI ``LLM`` object with ``base_url``
  pointing to https://openrouter.ai/api/v1. The API key is read from the
  ``OPENROUTER_API_KEY`` environment variable at construction time (never
  stored in settings or persisted).
- any other provider: passes the ``model_id`` string directly to the
  ``Agent`` constructor, relying on CrewAI's built-in resolver.
"""

from __future__ import annotations

from crewai import Agent, Crew, LLM, Process, Task as CrewAITask

from amsdp_ai_factory.agents.models import AgentDefinition
from amsdp_ai_factory.agents.prompts.templates import build_role_prompt
from amsdp_ai_factory.execution.models import ExecutionRequest

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def build_agent(
    definition: AgentDefinition,
    model_id: str | None = None,
    model_provider: str | None = None,
    tools: list | None = None,
) -> Agent:
    """Build a CrewAI agent from an approved definition (no kickoff).

    When ``model_provider`` is ``"openrouter"``, a CrewAI ``LLM`` object is
    constructed with the provider's ``base_url`` and the agent is configured
    with that ``LLM`` instance. For other providers (or when unset), the
    ``model_id`` string is passed directly to the Agent constructor and
    CrewAI's built-in provider resolver handles key discovery.

    ``tools`` is the list of CrewAI tool objects this agent is permitted to
    call (from ``build_read_tool_bundle``). When None, no tools are attached.
    """
    llm: str | LLM | None = model_id or None
    if model_provider and model_provider.lower() == "openrouter" and model_id:
        import os as _os
        api_key = _os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set in the process environment. "
                "Live execution cannot construct an LLM without a key; "
                "refusing to build the agent."
            )
        llm = LLM(
            model=model_id,
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            # OpenRouter is an OpenAI-compatible endpoint; the provider name
            # must be "openai" so CrewAI routes through it rather than the
            # built-in provider for the model's prefix (e.g. deepseek).
            provider="openai",
        )
    return Agent(
        role=definition.role,
        goal=definition.goal,
        backstory=build_role_prompt(definition),
        verbose=False,
        memory=False,
        allow_delegation=False,
        llm=llm,
        tools=list(tools) if tools else [],
    )


def build_stage_task(
    agent: Agent, request: ExecutionRequest,
) -> CrewAITask:
    """Build one CrewAI task from a stage execution request.

    When ``request.expected_artifact_kind`` is set and maps to a registered
    output model in ``ARTIFACT_MODELS``, the task is configured with
    ``response_model`` so CrewAI instructs the LLM to produce structured JSON
    matching that schema.  When the model is unavailable (e.g. generic or
    unregistered kind), the task falls back to free-text output without
    forcing a schema.
    """
    task_kwargs: dict = {
        "description": (
            f"Workflow: {request.workflow_id or 'n/a'}; stage {request.stage_id}. "
            f"Produce the approved output artifact of kind "
            f"{request.expected_artifact_kind!r} for task {request.task_id}. "
            f"Context: {request.context_summary or 'n/a'} "
            f"{request.focus_scope or ''}"
            f"{'\\n\\n--- Applicable Agent Rules ---\\n' + request.rules_text if request.rules_text else ''}"
        ),
        "expected_output": (
            f"A validated {request.expected_artifact_kind or 'agent'} artifact "
            "with evidence paths inside the task workspace."
        ),
        "agent": agent,
    }
    if request.expected_artifact_kind:
        from amsdp_ai_factory.contracts.outputs import (
            ARTIFACT_MODELS,
            ArtifactKind,
        )
        try:
            kind = ArtifactKind(request.expected_artifact_kind)
            output_model = ARTIFACT_MODELS.get(kind)
            if output_model is not None:
                # M2/M3 fix: CrewAI 1.15.35's Task executes structured output via
                # ``output_pydantic``/``output_json``; ``response_model`` is
                # declared but never consumed in the crew-kickoff path. Setting
                # it forces the LLM to emit JSON matching the artifact schema
                # (native provider structured output), which the executor then
                # validates strictly against the same model.
                task_kwargs["output_pydantic"] = output_model
                # Keep response_model also populated for older CrewAI builds
                # that may read it; harmless when output_pydantic is set.
                task_kwargs["response_model"] = output_model
        except ValueError:
            pass  # unknown kind → free-text fallback
    return CrewAITask(**task_kwargs)


def build_single_stage_crew(
    agent: Agent, task: CrewAITask, process: Process = Process.sequential
) -> Crew:
    """Crew for one controlled stage (the AI Factory's unit of execution)."""
    return Crew(agents=[agent], tasks=[task], process=process, verbose=False, memory=False)