"""Workflow models: stages, gates, and the ten approved workflows.

Each ``WorkflowDefinition`` captures purpose, trigger, ordered stages,
expected artifacts, gates, success condition, and failure path following AI
Development Workflow V1.0 sections 6-15.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from amsdp_ai_factory.tasks.models import TaskStatus

WORKFLOW_ID_PATTERN = r"^WF-\d{2}$"


class WorkflowStatus(str, Enum):
    """Honest capability state for each workflow."""

    EXECUTABLE = "executable"
    PARTIAL = "partial"
    PLANNED = "planned"


class StageKind(str, Enum):
    AGENT = "agent"   # an agent produces a validated artifact
    TOOL = "tool"     # the engine runs a workspace tool on behalf of an agent
    GATE = "gate"     # a human approval pause; no agent work


class StageGate(str, Enum):
    NONE = "none"
    HUMAN_DESIGN_APPROVAL = "human_design_approval"
    HUMAN_REVIEW = "human_review"
    DEPLOYMENT_APPROVAL = "awaiting_deployment_approval"


class StageDefinition(BaseModel):
    """One ordered step of a workflow."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str
    name: str
    description: str = ""
    kind: StageKind = StageKind.AGENT
    # Agent stage: the primary agent runs first.
    agent_ids: list[str] = Field(default_factory=list)
    # Agent stage: artifact kinds the agent must produce (ArtifactKind values).
    expected_output_kinds: list[str] = Field(default_factory=list)
    # Input artifact kinds consumed from earlier stages (informational).
    required_input_kinds: list[str] = Field(default_factory=list)
    # Tool stage: which tool executes, and on whose behalf (for permission checks).
    tool_stage_tool_id: str | None = None
    via_agent_id: str | None = None
    # Gate stage: the human gate this stage pauses at.
    gate: StageGate = StageGate.NONE
    # After this stage succeeds, the orchestrator moves the task to this status.
    advance_status: TaskStatus | None = None

    @field_validator("stage_id")
    @classmethod
    def _stage_id_format(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("stage_id must not be empty")
        return value.strip()


class WorkflowDefinition(BaseModel):
    """One approved development workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    name: str
    purpose: str
    trigger: str = ""
    status: WorkflowStatus
    stages: list[StageDefinition] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    success_condition: str = ""
    failure_path: str = (
        "bounded retries per stage; repeated failure escalates to BLOCKED/FAILED "
        "for a human decision"
    )
    retry_policy: str = "bounded: at most 2 attempts per stage; transient errors only"

    @field_validator("workflow_id")
    @classmethod
    def _workflow_id_format(cls, value: str) -> str:
        import re

        if not re.fullmatch(WORKFLOW_ID_PATTERN, value):
            raise ValueError(f"workflow_id {value!r} must match {WORKFLOW_ID_PATTERN!r}")
        return value

    def stage(self, stage_id: str) -> StageDefinition | None:
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None

    def order(self) -> list[str]:
        return [stage.stage_id for stage in self.stages]

    def approval_gates(self) -> list[StageGate]:
        return [stage.gate for stage in self.stages if stage.gate != StageGate.NONE]

    def summary(self) -> "WorkflowSummary":
        return WorkflowSummary(
            workflow_id=self.workflow_id,
            name=self.name,
            status=self.status,
            purpose=self.purpose,
            stage_count=len(self.stages),
        )


class WorkflowSummary(BaseModel):
    """Lightweight listing view."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    name: str
    status: WorkflowStatus
    purpose: str
    stage_count: int