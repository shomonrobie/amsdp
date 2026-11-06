"""WF-09 — Release Readiness workflow (Development Workflow V1.0 §14)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF09 = WorkflowDefinition(
    workflow_id="WF-09",
    name="Release Readiness",
    purpose="Prepare an approved set of changes for controlled release.",
    trigger="An approved change set is ready for release preparation.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf09_s1",
            name="Verify change set",
            description="A10 confirms target version and included commits.",
            kind=StageKind.AGENT,
            agent_ids=["A10"],
            expected_output_kinds=["release_readiness_report"],
            advance_status=TaskStatus.RELEASE_READINESS,
        ),
        StageDefinition(
            stage_id="wf09_s2",
            name="Collect CI evidence",
            description="A10 verifies CI results and dependency/migration readiness.",
            kind=StageKind.AGENT,
            agent_ids=["A10"],
            expected_output_kinds=["test_report"],
        ),
        StageDefinition(
            stage_id="wf09_s3",
            name="Security confirmation",
            description="A09 confirms security findings and scans.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf09_s4",
            name="Release package",
            description="A10 prepares release notes, rollback plan, and deployment checklist.",
            kind=StageKind.AGENT,
            agent_ids=["A10"],
            expected_output_kinds=["release_readiness_report"],
            advance_status=TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
        ),
        StageDefinition(
            stage_id="wf09_s5",
            name="Deployment approval",
            description="Pause: authorized human operator approves deployment. The factory never deploys.",
            kind=StageKind.GATE,
            gate=StageGate.DEPLOYMENT_APPROVAL,
            advance_status=TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
        ),
    ],
    required_artifacts=[
        "Release notes",
        "CI evidence",
        "migration plan",
        "rollback plan",
        "approval",
        "post-release verification",
    ],
    success_condition=(
        "Release artifacts and evidence are complete, deployment is "
        "human-authorized, and post-release verification is recorded."
    ),
)