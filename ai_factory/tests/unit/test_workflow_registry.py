"""Workflow registry tests: ten workflows, statuses, integrity."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS
from amsdp_ai_factory.workflows.models import WorkflowStatus
from amsdp_ai_factory.workflows.registry import (
    WorkflowRegistry,
    WorkflowRegistryError,
    validate_registry_integrity,
)


class WorkflowRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = WorkflowRegistry()

    def test_ten_workflows(self):
        self.assertEqual(len(self.registry.list()), 10)
        self.assertEqual(
            [workflow.workflow_id for workflow in self.registry.list()],
            [f"WF-{i:02d}" for i in range(1, 11)],
        )

    def test_statuses_are_all_executable(self):
        for workflow in self.registry.list():
            self.assertEqual(workflow.status, WorkflowStatus.EXECUTABLE)

    def test_all_workflows_listed_after_hardening(self):
        self.assertEqual(
            [workflow.workflow_id for workflow in self.registry.executable()],
            [f"WF-{i:02d}" for i in range(1, 11)],
        )

    def test_no_placeholder_labeled_complete(self):
        # After Phase 5 all 10 workflows are executable and their tool stages
        # reference only enabled tools.
        enabled = {
            tool.tool_id
            for tool in self.registry.tool_registry.list()
            if tool.enabled
        }
        for workflow in self.registry.executable():
            for stage in workflow.stages:
                if stage.tool_stage_tool_id:
                    self.assertIn(stage.tool_stage_tool_id, enabled)
        self.assertEqual(len(self.registry.executable()), 10)

    def test_integrity_validation_passes(self):
        self.assertEqual(validate_registry_integrity(self.registry), [])

    def test_every_artifact_kind_referenced_is_known(self):
        known = {kind.value for kind in ARTIFACT_MODELS}
        for workflow in self.registry.list():
            for stage in workflow.stages:
                for kind in stage.expected_output_kinds:
                    self.assertIn(kind, known, msg=f"{workflow.workflow_id}/{stage.stage_id}")

    def test_every_stage_has_an_agent_tool_or_gate(self):
        for workflow in self.registry.list():
            for stage in workflow.stages:
                if stage.kind.value == "agent":
                    self.assertTrue(stage.agent_ids, workflow.workflow_id)
                elif stage.kind.value == "tool":
                    self.assertTrue(stage.tool_stage_tool_id, workflow.workflow_id)
                    self.assertTrue(stage.via_agent_id, workflow.workflow_id)
                elif stage.kind.value == "gate":
                    self.assertNotEqual(stage.gate.value, "none", workflow.workflow_id)

    def test_unknown_workflow_rejected(self):
        with self.assertRaises(WorkflowRegistryError):
            self.registry.require("WF-99")

    def test_duplicate_registration_rejected(self):
        from amsdp_ai_factory.workflows.definitions import DEFAULT_WORKFLOWS

        with self.assertRaises(WorkflowRegistryError):
            self.registry.register(DEFAULT_WORKFLOWS[0])

    def test_every_workflow_lists_required_artifacts(self):
        for workflow in self.registry.list():
            self.assertTrue(workflow.required_artifacts, workflow.workflow_id)
            self.assertTrue(workflow.success_condition, workflow.workflow_id)


if __name__ == "__main__":
    unittest.main()