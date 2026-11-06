"""Stub handler tests: synthetic outputs for any artifact kind."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS, ArtifactKind
from amsdp_ai_factory.contracts.outputs import validate_output
from amsdp_ai_factory.execution.models import ExecutionRequest
from amsdp_ai_factory.execution.stub_handler import build_stub_handler


class StubHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = build_stub_handler()

    def _request(self, kind: str) -> ExecutionRequest:
        return ExecutionRequest(
            task_id="AMSDP-000001",
            stage_id="s1",
            agent_id="A01",
            workflow_id="WF-01",
            expected_artifact_kind=kind,
        )

    def test_every_artifact_kind_supported(self):
        for kind in ArtifactKind:
            output = self.handler(self._request(kind.value))
            self.assertEqual(output.artifact_type, kind.value)
            self.assertIn("STUB-SYNTHETIC", output.title)
            check = validate_output(output)
            self.assertTrue(check.ok, msg=f"{kind.value}: {check.issues}")

    def test_stub_never_claims_verified_work(self):
        output = self.handler(self._request("requirement_analysis"))
        self.assertIn("synthetic", output.summary.lower())
        self.assertIn("not a real analysis", output.summary.lower())


if __name__ == "__main__":
    unittest.main()