"""WF-03 — Frontend Delivery workflow (Development Workflow V1.0 §8)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF03 = WorkflowDefinition(
    workflow_id="WF-03",
    name="Frontend Delivery",
    purpose="Implement a user-facing workflow against approved APIs.",
    trigger="An approved user story with an available API contract and UI direction.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf03_s1",
            name="Confirm story",
            description="A01 confirms workflow and acceptance criteria.",
            kind=StageKind.AGENT,
            agent_ids=["A01"],
            expected_output_kinds=["requirement_analysis"],
        ),
        StageDefinition(
            stage_id="wf03_s2",
            name="Confirm contract",
            description="A05 confirms endpoint and error behavior.",
            kind=StageKind.AGENT,
            agent_ids=["A05"],
            expected_output_kinds=["api_contract"],
        ),
        StageDefinition(
            stage_id="wf03_s3",
            name="Implement UI",
            description="A07 implements the workflow and handles all UI states.",
            kind=StageKind.AGENT,
            agent_ids=["A07"],
            expected_output_kinds=["code_change_summary"],
            advance_status=TaskStatus.IN_PROGRESS,
        ),
        StageDefinition(
            stage_id="wf03_s4",
            name="Component tests",
            description="A07 adds component/workflow tests.",
            kind=StageKind.AGENT,
            agent_ids=["A07"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.SELF_CHECK,
        ),
        StageDefinition(
            stage_id="wf03_s5",
            name="Independent QA",
            description="A08 independently tests the workflow.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.INDEPENDENT_REVIEW,
        ),
        StageDefinition(
            stage_id="wf03_s6",
            name="Security check",
            description="A09 checks sensitive display/access behavior when relevant.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf03_s7",
            name="Documentation",
            description="A11 updates usage documentation.",
            kind=StageKind.AGENT,
            agent_ids=["A11"],
            expected_output_kinds=["documentation_update_report"],
        ),
        StageDefinition(
            stage_id="wf03_s8",
            name="Human review",
            description="Pause: human reviewer approves the change.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "UI diff",
        "component/workflow tests",
        "localization evidence",
        "accessibility notes",
        "review",
    ],
    success_condition="The user workflow works against the approved contract and human review is complete.",
)