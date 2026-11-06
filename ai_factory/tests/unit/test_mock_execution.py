"""Mock agent executor tests: validation without any model/provider call."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.contracts.outputs import EvidenceRef, RequirementAnalysis
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.models import ExecutionRequest
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore

from tests.helpers import TempRepoCase


class MockExecutionTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.store = ArtifactStore(self.repo_root / "var" / "workspaces", "AMSDP-000001")
        self.store.ensure()
        self.request = ExecutionRequest(
            task_id="AMSDP-000001",
            stage_id="stage-1",
            agent_id="A01",
            workflow_id="WF-01",
            expected_artifact_kind="requirement_analysis",
        )

    def _valid_output(self):
        return RequirementAnalysis(
            task_id="AMSDP-000001",
            workflow_id="WF-01",
            stage_id="stage-1",
            agent_id="A01",
            title="Queue reorder analysis",
            summary="Synthetic requirement analysis.",
            user_stories=["As a receptionist, I can reorder the queue."],
        )

    def test_valid_output_passes(self):
        executor = MockAgentExecutor(handler=lambda req: self._valid_output())
        result = executor.execute(self.request)
        self.assertTrue(result.ok)
        self.assertEqual(result.agent_id, "A01")
        self.assertTrue(all(check.ok for check in result.checks))
        self.assertNotIn("error", result.error)

    def test_no_handler_fails_gracefully(self):
        executor = MockAgentExecutor(handler=None)
        result = executor.execute(self.request)
        self.assertFalse(result.ok)
        self.assertIn("no mock handler", result.error)

    def test_invalid_output_fails(self):
        def bad_handler(req):
            output = self._valid_output()
            output.summary = ""  # violates the non-empty validator
            return output

        executor = MockAgentExecutor(handler=bad_handler)
        result = executor.execute(self.request)
        self.assertFalse(result.ok)
        self.assertFalse(result.checks[0].ok)

    def test_unverified_evidence_path_fails(self):
        missing = self.store.workspace / "missing.md"

        def handler_with_evidence(req):
            output = self._valid_output()
            output.evidence = [EvidenceRef(kind="artifact", path=str(missing))]
            return output

        executor = MockAgentExecutor(handler=handler_with_evidence)
        result = executor.execute(self.request, artifact_store=self.store)
        self.assertFalse(result.ok)
        self.assertTrue(any(not check.ok for check in result.checks))
        self.assertEqual(result.output.evidence[0].verified, False)

    def test_verified_evidence_path_passes(self):
        target = self.store.workspace / "analysis.md"
        target.write_text("# Analysis\n", encoding="utf-8")

        def handler(req):
            output = self._valid_output()
            output.evidence = [EvidenceRef(kind="artifact", path=str(target))]
            return output

        executor = MockAgentExecutor(handler=handler)
        result = executor.execute(self.request, artifact_store=self.store)
        self.assertTrue(result.ok)
        self.assertTrue(result.output.evidence[0].verified)


if __name__ == "__main__":
    unittest.main()