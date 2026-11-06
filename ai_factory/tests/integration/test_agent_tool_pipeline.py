"""Phase 3 integration: agent -> tool -> validated output -> approval.

Exercises the approved permission model and delivery path with synthetic
data only, and without any model/provider calls.
"""

from __future__ import annotations

import unittest

from amsdp_ai_factory.agents.definitions import ALL_AGENTS
from amsdp_ai_factory.agents.registry import AgentRegistry
from amsdp_ai_factory.approvals.service import ApprovalService
from amsdp_ai_factory.contracts.outputs import ApiContract, EndpointSpec, EvidenceRef
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.models import ExecutionRequest
from amsdp_ai_factory.runs.models import RunStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
from amsdp_ai_factory.tasks.lifecycle import transition
from amsdp_ai_factory.tasks.models import ApprovalDecision, Task, TaskStatus
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.tools.artifact_writer import ArtifactWriterTool
from amsdp_ai_factory.tools.tool_registry import (
    ToolPermissionError,
    build_default_registry,
)

from tests.helpers import TempRepoCase


class AgentToolPipelineTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.registry = TaskRegistry(self.repo_root / "var" / "tasks")
        self.runs = RunRecorder(self.repo_root / "runs")
        self.tool_registry = build_default_registry()
        self.agent_registry = AgentRegistry(ALL_AGENTS)
        self.store = ArtifactStore(self.repo_root / "var" / "workspaces", "AMSDP-000001")
        self.store.ensure()

    def _task_at_design_approval(self) -> Task:
        task = self.registry.create(
            Task(
                title="Queue reorder API contract",
                workflow_id="WF-01",
                task_type="api_design",
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
        return self.registry.save(task)

    def test_contract_designer_delivers_approved_contract(self):
        task = self._task_at_design_approval()
        agent = self.agent_registry.require("A05")
        writer = ArtifactWriterTool(self.store, write_prefix=agent.write_prefix)

        # Tool permission is enforced BEFORE the tool is used.
        self.tool_registry.assert_allowed("A05", "artifact_write")

        contract_path = self.store.workspace / "contracts" / "appointments" / "openapi.yaml"
        contract_path.parent.mkdir(parents=True)
        contract_path.write_text("openapi: 3.0.1\n", encoding="utf-8")
        writer_result = writer.write(
            "appointments/openapi.yaml", "openapi: 3.0.1\n", kind="contract"
        )
        self.assertTrue(writer_result.ok)

        def handler(request):
            return ApiContract(
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                stage_id=request.stage_id,
                agent_id=request.agent_id,
                title="Appointments API contract",
                summary="Synthetic first contract.",
                service_name="appointment-service",
                breaking=False,
                endpoints=[
                    EndpointSpec(
                        method="POST",
                        path="/appointments",
                        auth_required=True,
                        idempotent=True,
                        error_codes=["409", "422"],
                    )
                ],
                evidence=[EvidenceRef(kind="artifact", path=str(contract_path))],
            )

        executor = MockAgentExecutor(handler=handler)
        request = ExecutionRequest(
            task_id=task.task_id,
            stage_id="stage-design",
            agent_id="A05",
            workflow_id="WF-01",
            expected_artifact_kind="api_contract",
        )
        result = executor.execute(request, artifact_store=self.store)
        self.assertTrue(result.ok)
        self.assertEqual(result.output.service_name, "appointment-service")
        self.assertTrue(len(result.checks) >= 2)  # contract + evidence checks

        # Human approval converts the design gate into implementation readiness.
        approvals = ApprovalService(self.registry, run_recorder=self.runs)
        run = self.runs.new_run(
            task_id=task.task_id, workflow_id="WF-01", environment="test"
        )
        decided = approvals.decide(
            task.task_id,
            ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="contract evidence verified",
            run_id=run.run_id,
        )
        self.assertEqual(decided.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.runs.finish(run.run_id, status=RunStatus.SUCCEEDED)
        self.assertEqual(len(self.runs.get(run.run_id).approvals), 1)

    def test_permission_denials_are_enforced_in_code(self):
        # A09 (Security Reviewer) has no git_read binding per the specification.
        with self.assertRaises(ToolPermissionError):
            self.tool_registry.assert_allowed("A09", "git_read")
        # A01 (Product Analyst) has no run_tests binding.
        with self.assertRaises(ToolPermissionError):
            self.tool_registry.assert_allowed("A01", "run_tests")
        # An unknown tool is always denied.
        with self.assertRaises(ToolPermissionError) as ctx:
            self.tool_registry.assert_allowed("A05", "unknown_tool_xyz")
        self.assertIn("unknown", str(ctx.exception))
        # An unknown agent id gets nothing.
        with self.assertRaises(ToolPermissionError):
            self.tool_registry.assert_allowed("A99", "repo_read")

    def test_agents_cannot_escape_write_prefix(self):
        agent = self.agent_registry.require("A01")
        writer = ArtifactWriterTool(self.store, write_prefix=agent.write_prefix)
        result = writer.write("../../architecture/service-design.md", "nope")
        self.assertFalse(result.ok)
        self.assertFalse((self.store.workspace / "architecture").exists())


if __name__ == "__main__":
    unittest.main()