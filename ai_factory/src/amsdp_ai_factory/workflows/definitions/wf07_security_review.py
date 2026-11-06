"""WF-07 — Security Review workflow (Development Workflow V1.0 §12)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF07 = WorkflowDefinition(
    workflow_id="WF-07",
    name="Security Review",
    purpose="Independently assess a change or service for security and privacy risks.",
    trigger=(
        "A security-sensitive change, new service, new data flow, auth/authorization "
        "change, dependency addition, or scheduled review."
    ),
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf07_s1",
            name="Define scope",
            description="A09 defines review scope and assets.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
            advance_status=TaskStatus.ANALYSIS,
        ),
        StageDefinition(
            stage_id="wf07_s2",
            name="Inspect evidence",
            description="A09 inspects architecture, code, contracts, and test evidence.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf07_s3",
            name="Local scans",
            description="A09 runs secret/static scans (planned tools).",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf07_s4",
            name="Remediation",
            description="Responsible developer fixes findings.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["code_change_summary"],
            advance_status=TaskStatus.IN_PROGRESS,
        ),
        StageDefinition(
            stage_id="wf07_s5",
            name="Retest",
            description="A09 retests remediated findings.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf07_s6",
            name="Risk decision",
            description="Pause: project owner disposes of any residual risk.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Security report",
        "findings",
        "remediation",
        "retest evidence",
        "risk decision",
    ],
    success_condition=(
        "No unresolved critical/high finding remains without explicit human risk "
        "disposition."
    ),
)