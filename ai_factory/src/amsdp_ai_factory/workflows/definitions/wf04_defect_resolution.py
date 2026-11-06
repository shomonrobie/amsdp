"""WF-04 — Defect Resolution workflow (Development Workflow V1.0 §9)."""

from __future__ import annotations

from amsdp_ai_factory.tasks.models import TaskStatus
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)

WF04 = WorkflowDefinition(
    workflow_id="WF-04",
    name="Defect Resolution",
    purpose="Investigate and correct a defect without unrelated behavior changes.",
    trigger="A reproducible defect, failed test, regression, or verified issue is reported.",
    status=WorkflowStatus.EXECUTABLE,
    stages=[
        StageDefinition(
            stage_id="wf04_s1",
            name="Defect intake",
            description="A08 records expected/actual behavior, reproduction, severity; no real patient data.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.ANALYSIS,
        ),
        StageDefinition(
            stage_id="wf04_s2",
            name="Root-cause investigation",
            description="A06 inspects code and tests; A02 joins for cross-service causes.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["code_change_summary"],
        ),
        StageDefinition(
            stage_id="wf04_s3",
            name="Fix implementation",
            description="A06 implements the bounded fix and regression test.",
            kind=StageKind.AGENT,
            agent_ids=["A06"],
            expected_output_kinds=["code_change_summary", "test_report"],
            advance_status=TaskStatus.IN_PROGRESS,
        ),
        StageDefinition(
            stage_id="wf04_s4",
            name="Regression verification",
            description="A08 reproduces the original scenario and verifies the fix.",
            kind=StageKind.AGENT,
            agent_ids=["A08"],
            expected_output_kinds=["test_report"],
            advance_status=TaskStatus.SELF_CHECK,
        ),
        StageDefinition(
            stage_id="wf04_s5",
            name="Security retest",
            description="A09 retests security defects when the defect is security-related.",
            kind=StageKind.AGENT,
            agent_ids=["A09"],
            expected_output_kinds=["security_review"],
        ),
        StageDefinition(
            stage_id="wf04_s6",
            name="Human review",
            description="Pause: human reviewer approves the change.",
            kind=StageKind.GATE,
            gate=StageGate.HUMAN_REVIEW,
            advance_status=TaskStatus.HUMAN_REVIEW,
        ),
    ],
    required_artifacts=[
        "Defect report",
        "root-cause analysis",
        "fix diff",
        "regression test",
        "verification report",
    ],
    success_condition=(
        "The original defect is no longer reproducible, regression coverage exists, "
        "quality gates pass, and data/security risk is addressed."
    ),
)