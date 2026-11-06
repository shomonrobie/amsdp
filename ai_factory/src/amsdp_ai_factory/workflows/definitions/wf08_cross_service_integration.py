"""WF-08 — Cross-Service Integration workflow (Development Workflow V1.0 §13)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF08 = WorkflowDefinition(
    workflow_id="WF-08",
    name="Cross-Service Integration",
    purpose="Implement and verify a business workflow that spans multiple AMSDP microservices.",
    trigger="An approved feature requires more than one service to collaborate.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf08_s1",
            name="Service interaction map",
            description="A02 prepares the interaction map with ownership explicit.",
            kind=StageKind.AGENT,
            agent_ids=["A02"],
            expected_output_kinds=["architecture_proposal"],
            advance_status=TaskStatus.ANALYSIS,
        ),
        StageDefinition(
            stage_id="wf08_s2",
            name="Finalize contracts",
            description="A05 finalizes interfaces and event schemas.",
            kind=StageKind.AGENT,
            agent_ids=["A05"],
            expected_output_kinds=["api_contract"],
            advance_status=TaskStatus.DESIGN,
        ),
        StageDefinition(
            stage_id="wf08_s3",
            name="Isolated service tasks",
            description="A06 implements each service in an isolated workspace.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["code_change_summary"],
            advance_status=TaskStatus.IN_PROGRESS,
        ),
        StageDefinition(
            stage_id="wf08_s4",
            name="Contract tests",
            description="A05 validates each service boundary.",
            kind=StageKind.AGENT,
            agent_ids=["A05"],
            expected_output_kinds=["test_report"],
        ),
        StageDefinition(
            stage_id="wf08_s5",
            name="Integration QA",
            description="A08 tests success, failure, retry, timeout, and duplicate delivery cases.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
        ),
        StageDefinition(
            stage_id="wf08_s6",
            name="Cross-tenant security",
            description="A09 tests cross-service authorization and tenant propagation.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf08_s7",
            name="Combined human review",
            description="Pause: human reviewer approves the combined change.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Interaction map",
        "contracts",
        "service changes",
        "integration tests",
        "security review",
    ],
    success_condition=(
        "All service contracts and integration tests pass, cross-service behavior "
        "is documented, and human approval is complete."
    ),
)