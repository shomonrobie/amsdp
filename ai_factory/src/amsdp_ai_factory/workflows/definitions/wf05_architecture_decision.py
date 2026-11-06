"""WF-05 — Architecture Decision workflow (Development Workflow V1.0 §10)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF05 = WorkflowDefinition(
    workflow_id="WF-05",
    name="Architecture Decision",
    purpose=(
        "Evaluate a change to system architecture, service boundaries, integration "
        "patterns, or platform design and produce a human decision."
    ),
    trigger=(
        "A proposal affects microservice boundaries, ownership, gateway, event/communication, "
        "database ownership, consistency, auth architecture, deployment, or observability."
    ),
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf05_s1",
            name="Record problem",
            description="A02 records the architectural problem, constraints, and affected services.",
            kind=StageKind.AGENT,
            agent_ids=["A02"],
            expected_output_kinds=["architecture_decision_request"],
            advance_status=TaskStatus.ANALYSIS,
        ),
        StageDefinition(
            stage_id="wf05_s2",
            name="Options analysis",
            description="A02 prepares options and trade-offs.",
            kind=StageKind.AGENT,
            agent_ids=["A02"],
            expected_output_kinds=["architecture_proposal"],
            advance_status=TaskStatus.DESIGN,
        ),
        StageDefinition(
            stage_id="wf05_s3",
            name="Security impact",
            description="A09 reviews security and operational impact.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf05_s4",
            name="ADR proposal",
            description="A02 writes the ADR proposal into the workspace.",
            kind=StageKind.AGENT,
            agent_ids=["A02"],
            expected_output_kinds=["architecture_decision_request", "documentation_update_report"],
        ),
        StageDefinition(
            stage_id="wf05_s5",
            name="Project owner decision",
            description="Pause: human project owner approves, rejects, or requests changes.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_DESIGN_APPROVAL,
            advance_status=TaskStatus.HUMAN_DESIGN_APPROVAL,
        ),
    ],
    required_artifacts=[
        "Options analysis",
        "ADR proposal",
        "human decision",
        "updated architecture docs",
    ],
    success_condition=(
        "An explicit human decision is recorded, affected documents are updated, "
        "and implementation work is traceable to the decision."
    ),
)