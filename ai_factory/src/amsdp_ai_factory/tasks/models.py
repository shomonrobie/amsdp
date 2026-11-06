"""Task models: stable identifiers, lifecycle states, and approval records.

Implements the standard workflow task record (AI Development Workflow V1.0
sections 4) and the task contract (AI Factory Architecture V1.0 section 9).
The state set follows the workflow state machine (Workflow V1.0 section 5).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from amsdp_ai_factory.contracts.common import CheckResult, DocumentReference

TASK_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$"


def now_utc() -> datetime:
    """UTC-aware current timestamp used across task/run records."""
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------------
# Enumerations
# ----------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Finite task lifecycle states (Workflow V1.0 section 5)."""

    PROPOSED = "proposed"
    INTAKE_VALIDATION = "intake_validation"
    NEEDS_CLARIFICATION = "needs_clarification"
    CONTEXT_VALIDATION = "context_validation"
    BLOCKED = "blocked"
    READY_FOR_ANALYSIS = "ready_for_analysis"
    ANALYSIS = "analysis"
    DESIGN = "design"
    HUMAN_DESIGN_APPROVAL = "human_design_approval"
    READY_FOR_IMPLEMENTATION = "ready_for_implementation"
    IN_PROGRESS = "in_progress"
    SELF_CHECK = "self_check"
    INDEPENDENT_REVIEW = "independent_review"
    CHANGES_REQUESTED = "changes_requested"
    HUMAN_REVIEW = "human_review"
    APPROVED_FOR_MERGE = "approved_for_merge"
    MERGED = "merged"
    RELEASE_READINESS = "release_readiness"
    AWAITING_DEPLOYMENT_APPROVAL = "awaiting_deployment_approval"
    RELEASED = "released"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"

    def is_terminal(self) -> bool:
        return self in TERMINAL_TASK_STATUSES


TERMINAL_TASK_STATUSES = frozenset(
    {TaskStatus.CLOSED, TaskStatus.REJECTED, TaskStatus.CANCELLED}
)


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalState(str, Enum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class AttemptOutcome(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class FailureCategory(str, Enum):
    INPUT = "input"
    REQUIREMENT_CONFLICT = "requirement_conflict"
    DESIGN = "design"
    TOOL = "tool"
    TEST = "test"
    SECURITY = "security"
    RESOURCE = "resource"
    INTEGRATION = "integration"
    APPROVAL = "approval"
    OTHER = "other"


# ----------------------------------------------------------------------------
# Task sub-records
# ----------------------------------------------------------------------------


class ApprovalRecord(BaseModel):
    """One human approval decision attached to a task or stage."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = ""
    requested_at: datetime = Field(default_factory=now_utc)
    decided_at: datetime | None = None
    decision: ApprovalDecision
    actor: str = ""
    rationale: str = ""
    affected_stage: str | None = None


class TaskApproval(BaseModel):
    """Approval requirements and accumulated decisions for a task."""

    model_config = ConfigDict(extra="forbid")

    required_before_start: bool = False
    required_before_merge: bool = True
    required_before_deploy: bool = True
    state: ApprovalState = ApprovalState.NOT_REQUESTED
    decisions: list[ApprovalRecord] = Field(default_factory=list)


class TaskScope(BaseModel):
    """Explicit in/out-of-scope boundary for the task."""

    model_config = ConfigDict(extra="forbid")

    included: list[str] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)


class ExecutionAttempt(BaseModel):
    """One bounded execution attempt of the task's workflow."""

    model_config = ConfigDict(extra="forbid")

    attempt_number: int = 1
    started_at: datetime | None = None
    ended_at: datetime | None = None
    outcome: AttemptOutcome | None = None
    error_summary: str = ""
    checks: list[CheckResult] = Field(default_factory=list)


class ArtifactRecord(BaseModel):
    """A verified artifact produced by the task."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    name: str
    kind: str = "output"
    path: Path
    relative_to: str = ""
    sha256: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = Field(default_factory=now_utc)


class StateChangeRecord(BaseModel):
    """Audit entry for one task state transition."""

    model_config = ConfigDict(extra="forbid")

    from_status: TaskStatus | None
    to_status: TaskStatus
    actor: str = ""
    at: datetime = Field(default_factory=now_utc)
    reason: str = ""


class FailureRecord(BaseModel):
    """A recorded failure with its category for escalation handling."""

    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime = Field(default_factory=now_utc)
    stage: str | None = None
    category: FailureCategory = FailureCategory.OTHER
    error_code: str = ""
    message: str = ""
    retried: bool = False


# ----------------------------------------------------------------------------
# The task record
# ----------------------------------------------------------------------------


class Task(BaseModel):
    """The standard, validated task record used by every workflow.

    Status is managed exclusively through ``tasks.lifecycle.transition`` so
    agents cannot invent states or bypass the required sequence.
    """

    model_config = ConfigDict(extra="forbid")

    # Identity -----------------------------------------------------------------
    task_id: str = ""
    title: str = ""
    description: str = ""

    # Workflow and routing -----------------------------------------------------
    task_type: str | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PROPOSED
    requester: str | None = None
    workflow_id: str | None = None
    crew_id: str | None = None
    assigned_agents: list[str] = Field(default_factory=list)
    service: str | None = None

    # Context -------------------------------------------------------------------
    source_documents: list[DocumentReference] = Field(default_factory=list)
    scope: TaskScope = Field(default_factory=TaskScope)
    inputs: dict[str, str] = Field(default_factory=dict)
    expected_outputs: list[str] = Field(default_factory=list)

    # Acceptance and constraints ----------------------------------------------
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)

    # Approval ------------------------------------------------------------------
    approval: TaskApproval = Field(default_factory=TaskApproval)

    # Execution history ---------------------------------------------------------
    attempts: list[ExecutionAttempt] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    history: list[StateChangeRecord] = Field(default_factory=list)
    failure_info: list[FailureRecord] = Field(default_factory=list)
    escalation_notes: list[str] = Field(default_factory=list)
    blocked_reason: str = ""

    # Timestamps -----------------------------------------------------------------
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ---------------------------------------------------------------------------
    @field_validator("task_id")
    @classmethod
    def _task_id_must_be_safe(cls, value: str) -> str:
        if value and not re.fullmatch(TASK_ID_PATTERN, value):
            raise ValueError(
                f"task_id {value!r} must match {TASK_ID_PATTERN!r} "
                "(alphanumeric start, then letters/digits/._-; 2-63 chars)."
            )
        return value

    def touch(self, at: datetime | None = None) -> None:
        """Stamp created/updated timestamps (used by the registry)."""
        stamp = at or now_utc()
        if self.created_at is None:
            self.created_at = stamp
        self.updated_at = stamp

    def summary(self) -> "TaskSummary":
        return TaskSummary(
            task_id=self.task_id,
            title=self.title,
            status=self.status,
            priority=self.priority,
            workflow_id=self.workflow_id,
            task_type=self.task_type,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class TaskSummary(BaseModel):
    """Lightweight listing view of a task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str
    status: TaskStatus
    priority: TaskPriority = TaskPriority.NORMAL
    workflow_id: str | None = None
    task_type: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None