"""Agent execution request/result models.

An ``ExecutionResult`` is the validated outcome of one agent stage. It is
independent of any model provider: the mock executor produces these locally
so the full test suite runs with zero network/model calls.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from amsdp_ai_factory.contracts.common import CheckResult
from amsdp_ai_factory.contracts.outputs import AgentOutput
from amsdp_ai_factory.runs.models import ToolOperationRecord


class ExecutionRequest(BaseModel):
    """What a stage asks an agent to produce."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    stage_id: str
    agent_id: str
    workflow_id: str | None = None
    expected_artifact_kind: str = ""  # an ArtifactKind value
    context_summary: str = ""
    evidence_workspace: Path | None = None
    focus_scope: str = ""
    applied_rule_ids: list[str] = Field(default_factory=list)
    rules_text: str = ""

    @property
    def has_rules(self) -> bool:
        return bool(self.applied_rule_ids)


class ExecutionResult(BaseModel):
    """Structured, validated outcome of one agent stage."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    task_id: str
    stage_id: str
    agent_id: str
    output: AgentOutput | None = None
    checks: list[CheckResult] = Field(default_factory=list)
    tool_operations: list[ToolOperationRecord] = Field(default_factory=list)
    error: str = ""