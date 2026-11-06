"""WF-07 Security Review integration test."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import WorkflowEngine

from tests.helpers import TempRepoCase


class WF07Test(TempRepoCase):
    def test_stub_run_gate(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        engine = WorkflowEngine(
            task_registry=registry,
            run_recorder=RunRecorder(self.repo_root / "runs"),
            workspace_root=self.repo_root / "var" / "workspaces",
        )
        task = registry.create(Task(title="Code security review", workflow_id="WF-07"))
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = engine.run(task.task_id, "WF-07", stub)
        self.assertEqual(run.status.value, "awaiting_approval")
        self.assertEqual(len(run.stages), 6)