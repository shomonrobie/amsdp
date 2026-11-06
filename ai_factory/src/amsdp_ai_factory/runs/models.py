"""Run and workflow-stage record models.

Follows AI Development Workflow V1.0 section 21 (minimum run record) and the
AI Factory Implementation Prompt section 6.9 (run records and auditability).
Run records never store secrets: the recorder applies redaction before any
persistence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from amsdp_ai_factory.contracts.common import CheckResult, DocumentReference
from amsdp_ai_factory.tasks.models import ApprovalRecord, now_utc


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"
    AWAITING_APPROVAL = "awaiting_approval"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_APPROVAL = "awaiting_approval"


class AgentParticipation(BaseModel):
    """One agent involved in a run or stage (non-secret metadata only)."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str = ""
    model_config_id: str | None = None


class ToolOperationRecord(BaseModel):
    """A recorded tool call with its bounded result summary and provenance."""

    model_config = ConfigDict(extra="forbid")

    op_id: str = ""
    name: str
    args_summary: str = ""
    working_dir: str = ""
    started_at: datetime | None = None
    ended_at: datetime | None = None
    exit_code: int | None = None
    # --- M4 provenance (populated by the executor/engine) -------------------
    agent_id: str = ""
    stage_id: str = ""
    operation: str = ""          # e.g. repo_read.read_text, doc_reader.read
    target: str = ""             # target file/resource inspected
    ok: bool | None = None       # None while in-flight, True/False on completion
    error: str = ""              # short failure/denial summary (no secrets)
    evidence_refs: list[dict] = Field(default_factory=list)  # [{path, sha256}]


class StageRecord(BaseModel):
    """One workflow stage within a run."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str
    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    ended_at: datetime | None = None
    agents: list[AgentParticipation] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    approval_id: str | None = None
    error: str = ""
    retry_count: int = 0


class RunRecord(BaseModel):
    """The durable trace of one workflow execution."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = ""
    task_id: str = ""
    workflow_id: str | None = None
    workflow_version: str = "1.0"
    model_config_id: str | None = None
    provider: str | None = None
    environment: str = "development"
    source_documents: list[DocumentReference] = Field(default_factory=list)
    start_commit: str | None = None
    agents: list[AgentParticipation] = Field(default_factory=list)
    stages: list[StageRecord] = Field(default_factory=list)
    tool_operations: list[ToolOperationRecord] = Field(default_factory=list)
    approvals: list[ApprovalRecord] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    status: RunStatus = RunStatus.PENDING
    started_at: datetime | None = None
    ended_at: datetime | None = None

    def touch_start(self, at: datetime | None = None) -> None:
        if self.started_at is None:
            self.started_at = at or now_utc()

    def get_stage(self, stage_id: str) -> StageRecord | None:
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None


class RunSummary(BaseModel):
    """Lightweight listing view of a run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    task_id: str
    workflow_id: str | None = None
    status: RunStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None