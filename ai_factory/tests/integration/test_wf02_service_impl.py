"""WF-02 Service Implementation integration test."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.models import StageStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task, TaskStatus
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import WorkflowEngine, WorkflowNotExecutableError

from tests.helpers import TempRepoCase


class WF02Test(TempRepoCase):
    def test_stub_run_pauses_at_gate(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        runs = RunRecorder(self.repo_root / "runs")
        engine = WorkflowEngine(
            task_registry=registry,
            run_recorder=runs,
            workspace_root=self.repo_root / "var" / "workspaces",
        )
        task = registry.create(Task(title="Impl queue reorder", workflow_id="WF-02"))
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = engine.run(task.task_id, "WF-02", stub)
        self.assertEqual(run.status.value, "awaiting_approval")
        self.assertEqual(len(run.stages), 5)
        # Developer stage produced static_analysis check? Stub doesn't run tool.

    def test_executable_runs(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        engine = WorkflowEngine(
            task_registry=registry,
            run_recorder=RunRecorder(self.repo_root / "runs"),
            workspace_root=self.repo_root / "var" / "workspaces",
        )
        task = registry.create(Task(title="Impl WF-02", workflow_id="WF-02"))
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = engine.run(task.task_id, "WF-02", stub)
        self.assertIn(run.status.value, ("awaiting_approval", "running"))