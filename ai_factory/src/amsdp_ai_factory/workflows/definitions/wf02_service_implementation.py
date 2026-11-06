"""WF-02 — Service Implementation workflow (Development Workflow V1.0 §7)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF02 = WorkflowDefinition(
    workflow_id="WF-02",
    name="Service Implementation",
    purpose="Implement one approved feature within one microservice.",
    trigger="An approved service design and implementation task are available.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf02_s1",
            name="Developer implementation",
            description="A06 implements the assigned service behavior and tests.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["code_change_summary"],
            advance_status=TaskStatus.IN_PROGRESS,
        ),
        StageDefinition(
            stage_id="wf02_s2",
            name="Developer self-check",
            description="A06 runs lint/type/unit checks and records evidence.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.SELF_CHECK,
        ),
        StageDefinition(
            stage_id="wf02_s3",
            name="Independent QA",
            description="A08 independently verifies the change.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.INDEPENDENT_REVIEW,
        ),
        StageDefinition(
            stage_id="wf02_s4",
            name="Security review",
            description="A09 reviews security-sensitive changes when applicable.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf02_s5",
            name="Human review",
            description="Pause: human reviewer inspects the diff and evidence.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Code diff",
        "tests",
        "migration if authorized",
        "documentation",
        "execution evidence",
        "review",
    ],
    success_condition=(
        "Acceptance criteria pass, quality gates pass or explicitly approved, and "
        "a human reviewer approves merge."
    ),
)