"""Phase 4 integration: WF-01 Requirement-to-Design vertical slice.

Runs the complete executable workflow with the stub executor (no model
calls), exercises the design-approval gate, and verifies the full run/task
record trail.
"""

from __future__ import annotations

import unittest

from amsdp_ai_factory.approvals.service import ApprovalDecision
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.models import RunStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task, TaskStatus
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import WorkflowEngine

from tests.helpers import TempRepoCase


class WF01VerticalSliceTests(TempRepoCase):
    def _engine(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        runs = RunRecorder(self.repo_root / "runs")
        engine = WorkflowEngine(
            task_registry=registry,
            run_recorder=runs,
            workspace_root=self.repo_root / "var" / "workspaces",
            max_stage_attempts=2,
        )
        task = registry.create(
            Task(
                title="Queue reorder design package",
                workflow_id="WF-01",
                task_type="product_story",
                acceptance_criteria=[
                    "queue position is separate from appointment status",
                    "reorder does not change appointment date/time",
                ],
            )
        )
        return registry, runs, engine, task

    def test_full_wf01_slice(self):
        registry, runs, engine, task = self._engine()
        executor = MockAgentExecutor(handler=build_stub_handler())

        run = engine.run(task.task_id, "WF-01", executor)
        self.assertEqual(run.status, RunStatus.AWAITING_APPROVAL)
        self.assertEqual(
            registry.get(task.task_id).status, TaskStatus.HUMAN_DESIGN_APPROVAL
        )

        # All seven agent stages produced validated stub artifacts and their
        # run records carry checks/artifacts.
        self.assertEqual(len(run.stages), 8)
        self.assertTrue(run.checks)

        # Human approves the design package.
        engine.approval_service.decide(
            task.task_id,
            ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="design package verified",
            run_id=run.run_id,
        )

        run = engine.resume(task.task_id, executor=executor)
        self.assertEqual(run.status, RunStatus.SUCCEEDED)
        reloaded_task = registry.get(task.task_id)
        self.assertEqual(reloaded_task.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.assertEqual(len(reloaded_task.approval.decisions), 1)
        self.assertEqual(len(run.approvals), 1)

        # The complete run record is inspectable after execution.
        fresh = RunRecorder(self.repo_root / "runs").get(run.run_id)
        self.assertEqual(fresh.status, RunStatus.SUCCEEDED)
        self.assertEqual(len(fresh.stages), 8)

    def test_workspace_contains_stub_artifacts(self):
        from amsdp_ai_factory.tasks.artifact_store import ArtifactStore

        registry, runs, engine, task = self._engine()
        executor = MockAgentExecutor(handler=build_stub_handler())
        engine.run(task.task_id, "WF-01", executor)
        workspace = ArtifactStore(
            self.repo_root / "var" / "workspaces", task.task_id
        ).task_workspace()
        self.assertTrue(workspace.is_dir())


if __name__ == "__main__":
    unittest.main()