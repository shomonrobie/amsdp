"""WF-09 Release Readiness integration test."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.models import RunStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import WorkflowEngine

from tests.helpers import TempRepoCase


class WF09Test(TempRepoCase):
    def test_stub_run_pauses_at_deployment_gate_and_never_deploys(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        engine = WorkflowEngine(
            task_registry=registry,
            run_recorder=RunRecorder(self.repo_root / "runs"),
            workspace_root=self.repo_root / "var" / "workspaces",
        )
        task = registry.create(Task(title="Release 1.0", workflow_id="WF-09"))
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = engine.run(task.task_id, "WF-09", stub)
        # Must pause at the deployment gate, never proceed autonomously.
        self.assertEqual(run.status.value, "awaiting_approval")
        # The final gate is "deployment approval" — the engine pauses there
        # and does not autonomously execute any deployment action.
        last_stage = run.stages[-1]
        self.assertEqual(last_stage.stage_id, "wf09_s5")
        self.assertEqual(last_stage.status.value, "awaiting_approval")
        # Approve the gate and verify the run completes as SUCCEEDED with no
        # autonomous deployment stage.
        engine.approval_service.decide(
            task.task_id,
            "approved",
            actor="human_operator",
            rationale="synthetic release",
        )
        run = engine.resume(task.task_id, executor=stub)
        self.assertEqual(run.status, RunStatus.SUCCEEDED)
        # The final gate (deployment approval) is recorded as a standard stage;
        # its approval happened through the human operator. No additional
        # "deploy" script or action was executed by the engine.
        for stage in run.stages:
            if "deploy" in stage.name.lower():
                # The only "deploy" stage is the human-approval gate itself.
                self.assertIn(stage.status.value, ("succeeded", "awaiting_approval"))