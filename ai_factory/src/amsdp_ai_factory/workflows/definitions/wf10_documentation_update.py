"""WF-10 — Documentation Update workflow (Development Workflow V1.0 §15).

Executable: keep documentation synchronized with approved decisions and
verified implementation, including a real tool stage (doc_link_validator).
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

WF10 = WorkflowDefinition(
    workflow_id="WF-10",
    name="Documentation Update",
    purpose=(
        "Keep documentation synchronized with approved decisions and verified "
        "implementation, without inventing features or claiming unverified "
        "capabilities."
    ),
    trigger="Documentation changes based on approved decisions or verified implementation.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf10_s1",
            name="Identify source",
            description="A11 identifies whether the source is approved or proposed.",
            kind=StageKind.AGENT,
            agent_ids=["A11"],
            expected_output_kinds=["documentation_update_report"],
        ),
        StageDefinition(
            stage_id="wf10_s2",
            name="Draft changes",
            description="A11 updates only the affected documentation.",
            kind=StageKind.AGENT,
            agent_ids=["A11"],
            expected_output_kinds=["documentation_update_report"],
        ),
        StageDefinition(
            stage_id="wf10_s3",
            name="Validate links",
            description="Engine runs the doc_link_validator tool on the workspace docs (A11-mediated).",
            kind=StageKind.TOOL,
            tool_stage_tool_id="doc_link_validator",
            via_agent_id="A11",
            expected_output_kinds=[],
        ),
        StageDefinition(
            stage_id="wf10_s4",
            name="Human review",
            description="Pause: human approval when documentation changes an approved baseline.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Updated docs",
        "source references",
        "validation result",
        "review",
    ],
    success_condition=(
        "Documentation accurately represents approved decisions or verified "
        "behavior; proposed content is labeled; review is recorded."
    ),
)