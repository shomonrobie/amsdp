"""Provider-gated live (CrewAI) agent executor.

Never contacts any model provider unless BOTH conditions hold:

1. settings define ``model_provider`` and ``model_id``; and
2. the environment variable ``AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1``.

Any missing piece raises a clear error BEFORE a crew is ever built or run.
There is no silent fallback to another provider or model.

Structured-output handling
--------------------------
CrewAI 1.15.35 drives native structured output through ``Task.output_pydantic``
(``response_model`` alone is declared but not consumed by the crew executor).
When the model nevertheless returns prose, DSML/markdown fences, or an empty
payload, this executor extracts candidate JSON substrings and validates every
candidate STRICTLY against the artifact Pydantic model. Arbitrary prose is
never accepted; a result is produced only when a candidate that satisfies the
contract exists.
"""

from __future__ import annotations

import json
import os
import re

from amsdp_ai_factory.agents.definitions import AGENT_INDEX
from amsdp_ai_factory.agent_tools import (
    ToolOperationCollector,
    build_read_tool_bundle,
)
from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS, ArtifactKind
from amsdp_ai_factory.execution.build_crews import (
    build_agent,
    build_single_stage_crew,
    build_stage_task,
)
from amsdp_ai_factory.execution.models import ExecutionRequest, ExecutionResult
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore

LIVE_EXECUTION_ENV = "AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED"


class LiveExecutionError(RuntimeError):
    """Raised when live execution is not configured or not authorized."""


def _strip_markup(text: str) -> str:
    """Remove DSML / markdown fences and leading prose around JSON.

    Returns the cleaned text; the caller still validates any candidate JSON
    against the contract, so stripping alone never accepts prose.
    """
    if not text:
        return ""
    # Remove fenced code blocks (```json ... ```, ``` ... ```).
    text = re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", text)
    # Remove DSML markers like "|json|", "│json│", ".json_input", etc.
    text = re.sub(r"[|│]\s*(?:json|json_next_call|json_input|info|text)[|│]?", "", text)
    text = text.replace("\\n", "\n")
    return text.strip()


def _json_candidates(text: str):
    """Yield (json_string, start) candidates parsed from ``text``.

    Tries the whole cleaned text, then the largest balanced ``{...}`` object
    (and ``[...]`` array) it can locate, with a bounded number of attempts.
    """
    cleaned = _strip_markup(text)
    if cleaned:
        yield cleaned.strip(), 0
    # Balanced-brace scan: try the first '{' opening a valid JSON object.
    for m in re.finditer(r"\{", cleaned):
        depth = 0
        for i in range(m.start(), len(cleaned)):
            ch = cleaned[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield cleaned[m.start() : i + 1].strip(), m.start()
                    break
            if i - m.start() > 60000:  # hard bound per candidate
                break
    # Array fallback for list-kind artifacts.
    for m in re.finditer(r"\[", cleaned):
        depth = 0
        for i in range(m.start(), len(cleaned)):
            ch = cleaned[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    yield cleaned[m.start() : i + 1].strip(), m.start()
                    break
            if i - m.start() > 60000:
                break


def _extract_validated_output(payload, model) -> object:
    """Strictly coerce ``payload`` into ``model`` (a Pydantic artifact).

    Accepts (a) an already-parsed dict, (b) a Pydantic instance, or (c) a JSON
    string. String payloads are probed in order: exact parse first, then each
    extracted JSON substring. Anything that fails the contract raises.
    """
    if isinstance(payload, model):
        return payload
    if isinstance(payload, dict):
        return model.model_validate(payload)
    if not isinstance(payload, str):
        raise ValueError(f"unexpected payload type: {type(payload).__name__}")

    # Exact full-string parse first.
    try:
        return model.model_validate_json(payload)
    except Exception:
        pass

    # Then probe extracted candidates (markup/prose-tolerant).
    last_err: Exception | None = None
    for candidate, _pos in _json_candidates(payload):
        try:
            return model.model_validate_json(candidate)
        except Exception as exc:  # keep validating further candidates
            last_err = exc
    if last_err is not None:
        raise ValueError(
            "no JSON payload in the model response satisfies the artifact "
            f"contract; last error: {last_err}"
        )
    raise ValueError(
        "model returned an empty response; no structured artifact could be "
        "extracted"
    )


class CrewAIExecutor:
    """Live executor gated on explicit configuration AND authorization."""

    model_config_id: str | None = None
    provider: str | None = None

    def __init__(self, settings) -> None:
        self.settings = settings
        self.model_config_id = settings.model_id
        self.provider = settings.model_provider

    def _assert_gate(self) -> None:
        if not (self.settings.model_provider and self.settings.model_id):
            raise LiveExecutionError(
                "live execution requires AMSDP_FACTORY_MODEL_PROVIDER and "
                "AMSDP_FACTORY_MODEL_ID to be configured; mock/stub execution "
                "needs no configuration"
            )
        if os.environ.get(LIVE_EXECUTION_ENV, "") != "1":
            raise LiveExecutionError(
                f"live execution is not authorized: set {LIVE_EXECUTION_ENV}=1 "
                "explicitly after reviewing the model/provider configuration"
            )

    def execute(
        self, request: ExecutionRequest, artifact_store: ArtifactStore | None = None
    ) -> ExecutionResult:
        """Gate, build the stage crew, run it, and validate the output.

        The CrewAI agent is given ONLY the read-only tools its definition
        permits (repo_read / doc_reader / git_read); no source-modification
        or shell tool is attached during this phase.
        """
        self._assert_gate()

        definition = AGENT_INDEX.get(request.agent_id)
        if definition is None:
            return ExecutionResult(
                ok=False,
                task_id=request.task_id,
                stage_id=request.stage_id,
                agent_id=request.agent_id,
                error=f"unknown agent {request.agent_id!r}",
            )
        # M1: attach only authorized read-only tools.
        collector = ToolOperationCollector(
            agent_id=definition.agent_id, stage_id=request.stage_id
        )
        bundle = build_read_tool_bundle(
            definition,
            repo_root=self.settings.effective_repo_root(),
            collector=collector,
        )
        agent = build_agent(
            definition,
            model_id=self.settings.model_id,
            model_provider=self.settings.model_provider,
            tools=bundle.as_list(),
        )
        task = build_stage_task(agent, request)
        crew = build_single_stage_crew(agent, task)
        output_holder = crew.kickoff()

        payload = getattr(output_holder, "pydantic", None)
        if payload is None:
            payload = getattr(output_holder, "raw", None)
        model = ARTIFACT_MODELS[ArtifactKind(request.expected_artifact_kind)]
        try:
            output = _extract_validated_output(payload, model)
        except Exception as exc:
            return ExecutionResult(
                ok=False,
                task_id=request.task_id,
                stage_id=request.stage_id,
                agent_id=request.agent_id,
                error=f"live output failed contract validation: {exc}",
                tool_operations=collector.records(),
            )
        checks = []
        if artifact_store is not None:
            for evidence in output.evidence:
                check = artifact_store.verify(evidence.path)
                checks.append(check)
                evidence.verified = check.ok
        ok = all(check.ok for check in checks) or not checks
        return ExecutionResult(
            ok=ok,
            task_id=request.task_id,
            stage_id=request.stage_id,
            agent_id=request.agent_id,
            output=output,
            checks=checks,
            tool_operations=collector.records(),
        )