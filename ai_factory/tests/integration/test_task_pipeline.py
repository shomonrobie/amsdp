"""Phase 2 integration: task -> lifecycle -> artifacts -> run record.

No agents, no model calls, no production data. Exercises the complete
Phase 2 data path in a disposable repository with synthetic content only.
"""

from __future__ import annotations

import unittest

from amsdp_ai_factory.contracts.common import CheckResult
from amsdp_ai_factory.contracts.outputs import (
    RequirementAnalysis,
    validate_output,
)
from amsdp_ai_factory.runs.models import RunStatus, StageStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
from amsdp_ai_factory.tasks.lifecycle import transition
from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalState,
    Task,
    TaskStatus,
    now_utc,
)
from amsdp_ai_factory.tasks.registry import TaskRegistry

from tests.helpers import TempRepoCase


class TaskPipelineIntegrationTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.registry = TaskRegistry(self.repo_root / "var" / "tasks")
        self.runs = RunRecorder(self.repo_root / "runs")
        self.workspaces = self.repo_root / "var" / "workspaces"

    def _new_approved_design_task(self) -> Task:
        task = self.registry.create(
            Task(
                title="Design queue-reorder acceptance tests",
                task_type="product_story",
                workflow_id="WF-01",
                acceptance_criteria=[
                    "queue position is separate from appointment status",
                    "reorder does not change appointment date/time",
                ],
                constraints=["no clinical triage", "staff-mediated booking only"],
            )
        )
        for status in (
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.HUMAN_DESIGN_APPROVAL,
        ):
            transition(task, status, actor="orchestrator")
        approval = ApprovalRecord(
            decision_id="app-1",
            decision=ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="Synthetic acceptance criteria match approved business rules.",
        )
        transition(
            task,
            TaskStatus.READY_FOR_IMPLEMENTATION,
            actor="project_owner",
            approval=approval,
        )
        return self.registry.save(task)

    def test_end_to_end_task_artifact_run_flow(self):
        task = self._new_approved_design_task()
        self.assertEqual(task.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.assertEqual(len(task.approval.decisions), 1)

        # Artifact produced inside the task workspace, then verified.
        store = ArtifactStore(self.workspaces, task.task_id)
        spec_path = store.ensure() / "service_spec.md"
        spec_path.write_text("# Service Specification (SYNTHETIC)\n", encoding="utf-8")
        artifact = store.register_artifact(
            name="service_spec", absolute_path=spec_path, kind="design_doc"
        )
        task.artifacts.append(artifact)
        self.registry.save(task)

        # A validated agent-style output backing the stage.
        output = RequirementAnalysis(
            task_id=task.task_id,
            workflow_id="WF-01",
            stage_id="stage-1",
            title="Queue reorder requirement analysis",
            summary="Synthetic analysis of queue reorder guardrails.",
            user_stories=["As a receptionist, I can reorder the queue."],
            acceptance_criteria=list(task.acceptance_criteria),
        )
        contract_check = validate_output(output)
        self.assertTrue(contract_check.ok)
        existence_check = store.verify(artifact.path)
        self.assertTrue(existence_check.ok)

        # Full run record with stages, checks, approvals, artifacts.
        run = self.runs.new_run(
            task_id=task.task_id,
            workflow_id="WF-01",
            environment="test",
        )
        stage = self.runs.start_stage(run.run_id, name="requirement_analysis")
        self.runs.add_check(run.run_id, contract_check)
        self.runs.add_check(run.run_id, existence_check)
        self.runs.add_artifact(run.run_id, str(artifact.path))
        self.runs.add_approval(
            run.run_id,
            ApprovalRecord(
                decision_id="app-1",
                decision=ApprovalDecision.APPROVED,
                actor="project_owner",
            ),
        )
        self.runs.update_stage(
            run.run_id,
            stage.stage_id,
            status=StageStatus.SUCCEEDED,
            ended_at=now_utc(),
        )
        self.runs.finish(run.run_id, status=RunStatus.SUCCEEDED)

        # Both records survive a fresh process (new instances, same dirs).
        reloaded_task = TaskRegistry(self.repo_root / "var" / "tasks").get(task.task_id)
        reloaded_run = RunRecorder(self.repo_root / "runs").get(run.run_id)
        self.assertEqual(reloaded_task.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.assertEqual(len(reloaded_task.artifacts), 1)
        self.assertEqual(reloaded_run.status, RunStatus.SUCCEEDED)
        self.assertEqual(len(reloaded_run.stages), 1)
        self.assertEqual(len(reloaded_run.checks), 2)
        self.assertEqual(len(reloaded_run.approvals), 1)

    def test_rejected_approval_stops_progress(self):
        task = self._new_approved_design_task()
        transition(task, TaskStatus.IN_PROGRESS, actor="orchestrator")
        transition(task, TaskStatus.SELF_CHECK, actor="backend_developer")
        transition(task, TaskStatus.INDEPENDENT_REVIEW, actor="orchestrator")
        transition(task, TaskStatus.HUMAN_REVIEW, actor="orchestrator")
        rejection = ApprovalRecord(
            decision_id="app-2",
            decision=ApprovalDecision.CHANGES_REQUESTED,
            actor="reviewer",
            rationale="Acceptance criteria need a concurrency case.",
        )
        transition(
            task, TaskStatus.CHANGES_REQUESTED, actor="reviewer", approval=rejection
        )
        self.registry.save(task)
        reloaded = TaskRegistry(self.repo_root / "var" / "tasks").get(task.task_id)
        self.assertEqual(reloaded.status, TaskStatus.CHANGES_REQUESTED)
        self.assertEqual(reloaded.approval.state, ApprovalState.CHANGES_REQUESTED)


if __name__ == "__main__":
    unittest.main()