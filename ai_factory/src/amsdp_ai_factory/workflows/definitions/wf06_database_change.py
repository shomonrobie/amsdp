"""WF-06 — Database Change workflow (Development Workflow V1.0 §11)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF06 = WorkflowDefinition(
    workflow_id="WF-06",
    name="Database Change",
    purpose="Safely design, implement, and verify a service-owned database change.",
    trigger="Schema, constraint, index, or migration work in an assigned service.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf06_s1",
            name="Confirm data ownership",
            description="A04 identifies the owning service and business reason.",
            kind=StageKind.AGENT,
            agent_ids=["A04"],
            expected_output_kinds=["database_change_proposal"],
            advance_status=TaskStatus.ANALYSIS,
        ),
        StageDefinition(
            stage_id="wf06_s2",
            name="Design migration",
            description="A04 designs schema, constraints, indexes, tenant isolation, and recovery.",
            kind=StageKind.AGENT,
            agent_ids=["A04"],
            expected_output_kinds=["database_change_proposal"],
            advance_status=TaskStatus.DESIGN,
        ),
        StageDefinition(
            stage_id="wf06_s3",
            name="Disposable migration test",
            description="A04 tests the migration on a disposable database with synthetic fixtures.",
            kind=StageKind.AGENT,
            agent_ids=["A04"],
            expected_output_kinds=["database_change_proposal"],
        ),
        StageDefinition(
            stage_id="wf06_s4",
            name="Compatibility regression",
            description="A08 verifies existing behavior and contract compatibility.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
        ),
        StageDefinition(
            stage_id="wf06_s5",
            name="Human approval",
            description="Pause: human reviewer; project owner for material data-risk changes.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Schema spec",
        "migration",
        "test evidence",
        "recovery plan",
        "approvals",
    ],
    success_condition=(
        "Migration is tested, ownership and tenant rules are preserved, risk is "
        "documented, and required approvals are recorded."
    ),
)