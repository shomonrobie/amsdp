"""Workflow engine tests: ordering, gates, retries, failure, resume."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.approvals.service import ApprovalDecision
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.models import RunStatus, StageStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task, TaskStatus
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import (
    WorkflowEngine,
    WorkflowError,
    WorkflowStageError,
)
from amsdp_ai_factory.workflows.models import StageKind, StageDefinition

from tests.helpers import TempRepoCase


class WorkflowEngineTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.registry = TaskRegistry(self.repo_root / "var" / "tasks")
        self.runs = RunRecorder(self.repo_root / "runs")
        self.workspaces = self.repo_root / "var" / "workspaces"
        self.engine = WorkflowEngine(
            task_registry=self.registry,
            run_recorder=self.runs,
            workspace_root=self.workspaces,
            max_stage_attempts=2,
        )
        self.stub = MockAgentExecutor(handler=build_stub_handler())

    def _task(self, workflow_id="WF-01") -> Task:
        return self.registry.create(
            Task(
                title="Synthetic WF test",
                workflow_id=workflow_id,
                task_type="product_story",
            )
        )

    def test_wf01_pauses_at_design_gate(self):
        task = self._task("WF-01")
        run = self.engine.run(task.task_id, "WF-01", self.stub)
        self.assertEqual(run.status, RunStatus.AWAITING_APPROVAL)
        self.assertEqual(len(run.stages), 8)
        gate_stage = run.get_stage("wf01_s8")
        self.assertEqual(gate_stage.status, StageStatus.AWAITING_APPROVAL)
        reloaded = self.registry.get(task.task_id)
        self.assertEqual(reloaded.status, TaskStatus.HUMAN_DESIGN_APPROVAL)
        # Stages executed in order: s1..s7 succeeded.
        for idx in range(1, 8):
            self.assertEqual(run.get_stage(f"wf01_s{idx}").status, StageStatus.SUCCEEDED)

    def test_approve_then_resume_completes_wf01(self):
        task = self._task("WF-01")
        self.engine.run(task.task_id, "WF-01", self.stub)
        self.engine.approval_service.decide(
            task.task_id,
            ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="verified",
        )
        run = self.engine.resume(task.task_id, executor=self.stub)
        self.assertEqual(run.status, RunStatus.SUCCEEDED)
        self.assertEqual(run.get_stage("wf01_s8").status, StageStatus.SUCCEEDED)
        reloaded = self.registry.get(task.task_id)
        self.assertEqual(reloaded.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.assertEqual(len(reloaded.approval.decisions), 1)

    def test_rejected_gate_stops_work(self):
        task = self._task("WF-01")
        self.engine.run(task.task_id, "WF-01", self.stub)
        self.engine.approval_service.decide(
            task.task_id,
            ApprovalDecision.REJECTED,
            actor="project_owner",
            rationale="not acceptable",
        )
        reloaded = self.registry.get(task.task_id)
        self.assertEqual(reloaded.status, TaskStatus.REJECTED)
        # There is no pending gate to resume past.
        with self.assertRaises((WorkflowError, WorkflowStageError)):
            self.engine.resume(task.task_id, executor=self.stub)

    def test_all_workflows_executable(self):
        from amsdp_ai_factory.workflows.definitions import DEFAULT_WORKFLOWS

        stub = MockAgentExecutor(handler=build_stub_handler())
        for definition in DEFAULT_WORKFLOWS:
            task = self.registry.create(
                Task(title="Test", workflow_id=definition.workflow_id)
            )
            run = self.engine.run(task.task_id, definition.workflow_id, stub)
            # All workflows have at least one stage and lead to a gate.
            self.assertGreater(len(run.stages), 0, definition.workflow_id)
            self.assertIn(
                run.status.value, ("awaiting_approval", "succeeded"),
                f"{definition.workflow_id} did not complete or gate",
            )

    def test_stage_failure_is_bounded_and_stops_downstream(self):
        task = self._task("WF-01")

        def failing_handler(request):
            raise RuntimeError("provider unavailable")

        executor = MockAgentExecutor(handler=failing_handler)
        with self.assertRaises(WorkflowStageError):
            self.engine.run(task.task_id, "WF-01", executor)
        reloaded = self.registry.get(task.task_id)
        self.assertEqual(reloaded.status, TaskStatus.FAILED)
        self.assertTrue(reloaded.escalation_notes)
        run = self.runs.list(task_id=task.task_id)[0]
        run_record = self.runs.get(run.run_id)
        self.assertEqual(run_record.status, RunStatus.FAILED)
        # Downstream stage never started.
        self.assertEqual(len(run_record.stages), 1)
        self.assertEqual(run_record.stages[0].status, StageStatus.FAILED)

    def test_preflight_rejects_unknown_agent(self):
        stage = StageDefinition(
            stage_id="bad",
            name="bad",
            kind=StageKind.AGENT,
            agent_ids=["A99"],
            expected_output_kinds=["requirement_analysis"],
        )
        with self.assertRaises(WorkflowError):
            self.engine._preflight_stage_tools(stage)

    def test_wf10_tool_stage_runs(self):
        task = self._task("WF-10")
        run = self.engine.run(task.task_id, "WF-10", self.stub)
        self.assertEqual(run.status, RunStatus.AWAITING_APPROVAL)
        tool_stage = run.get_stage("wf10_s3")
        self.assertEqual(tool_stage.status, StageStatus.SUCCEEDED)
        self.assertIn("tool:doc_link_validator", [c.name for c in run.checks])


if __name__ == "__main__":
    unittest.main()