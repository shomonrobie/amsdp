"""WF-01 — Requirement-to-Design workflow (Development Workflow V1.0 §6).

Executable vertical slice: turns an approved product need into a traceable,
implementation-ready design package.
"""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF01 = WorkflowDefinition(
    workflow_id="WF-01",
    name="Requirement-to-Design",
    purpose=(
        "Turn an approved product need into a traceable, implementation-ready "
        "design package (requirements, architecture impact, service/data/API "
        "design, test and security planning)."
    ),
    trigger="A new feature or material behavior change is requested.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf01_s1",
            name="Product analysis",
            description="A01 drafts user stories, acceptance criteria, and traceability.",
            kind=StageKind.AGENT,
            agent_ids=["A01"],
            expected_output_kinds=["requirement_analysis"],
        ),
        StageDefinition(
            stage_id="wf01_s2",
            name="Architecture impact",
            description="A02 identifies affected services and architecture decisions.",
            kind=StageKind.AGENT,
            agent_ids=["A02"],
            expected_output_kinds=["architecture_proposal"],
        ),
        StageDefinition(
            stage_id="wf01_s3",
            name="Service design",
            description="A03 produces the service specification; design phase begins.",
            kind=StageKind.AGENT,
            agent_ids=["A03"],
            expected_output_kinds=["service_implementation_plan"],
            advance_status=TaskStatus.DESIGN,
        ),
        StageDefinition(
            stage_id="wf01_s4",
            name="Database design",
            description="A04 proposes schema, constraints, and tenant isolation.",
            kind=StageKind.AGENT,
            agent_ids=["A04"],
            expected_output_kinds=["database_change_proposal"],
        ),
        StageDefinition(
            stage_id="wf01_s5",
            name="API contract design",
            description="A05 defines API/event contracts and error behavior.",
            kind=StageKind.AGENT,
            agent_ids=["A05"],
            expected_output_kinds=["api_contract"],
        ),
        StageDefinition(
            stage_id="wf01_s6",
            name="Test planning",
            description="A08 maps acceptance criteria to test scenarios.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_plan"],
        ),
        StageDefinition(
            stage_id="wf01_s7",
            name="Security planning",
            description="A09 reviews authorization, tenant, and data implications.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf01_s8",
            name="Human design approval",
            description="Pause: the complete design package awaits owner approval.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_DESIGN_APPROVAL,
            advance_status=TaskStatus.HUMAN_DESIGN_APPROVAL,
        ),
    ],
    required_artifacts=[
        "Product Requirements Package",
        "Architecture Impact Assessment",
        "service specs",
        "data/API contracts",
        "test strategy",
        "approval record",
    ],
    success_condition=(
        "Design package is validated, required decisions are approved by a human, "
        "and the task leaves the gate as READY_FOR_IMPLEMENTATION."
    ),
)