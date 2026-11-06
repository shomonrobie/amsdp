"""Live (CrewAI) executor gating tests — never a real provider call."""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest import mock

from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.execution.live import CrewAIExecutor, LiveExecutionError
from amsdp_ai_factory.execution.models import ExecutionRequest

REQUEST = ExecutionRequest(
    task_id="AMSDP-000001",
    stage_id="s1",
    agent_id="A05",
    workflow_id="WF-01",
    expected_artifact_kind="api_contract",
)


def _settings(provider="openai", model_id="gpt-test"):
    return FactorySettings(
        _env_file=None,
        environment="development",
        repo_root="/tmp",
        model_provider=provider,
        model_id=model_id,
    )


class LiveExecutorGateTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED", None)

    def test_missing_provider_raises(self):
        executor = CrewAIExecutor(_settings(provider=None, model_id=None))
        with self.assertRaises(LiveExecutionError) as ctx:
            executor._assert_gate()
        self.assertIn("MODEL_PROVIDER", str(ctx.exception))

    def test_not_authorized_raises(self):
        executor = CrewAIExecutor(_settings())
        with self.assertRaises(LiveExecutionError) as ctx:
            executor._assert_gate()
        self.assertIn("not authorized", str(ctx.exception))

    def test_authorized_path_builds_and_validates_output(self):
        with mock.patch.dict(
            os.environ, {"AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED": "1"}
        ):
            executor = CrewAIExecutor(_settings())
            payload = (
                '{"artifact_type":"api_contract","task_id":"AMSDP-000001",'
                '"title":"T","summary":"S","service_name":"svc"}'
            )
            fake_crew = SimpleNamespace(
                kickoff=lambda: SimpleNamespace(pydantic=None, raw=payload)
            )
            with mock.patch(
                "amsdp_ai_factory.execution.live.build_single_stage_crew",
                return_value=fake_crew,
            ):
                result = executor.execute(REQUEST)
        self.assertTrue(result.ok)
        self.assertEqual(result.output.service_name, "svc")

    def test_invalid_live_output_fails_contract(self):
        with mock.patch.dict(
            os.environ, {"AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED": "1"}
        ):
            executor = CrewAIExecutor(_settings())
            fake_crew = SimpleNamespace(
                kickoff=lambda: SimpleNamespace(pydantic=None, raw='{"artifact_type":"api_contract"}')
            )
            with mock.patch(
                "amsdp_ai_factory.execution.live.build_single_stage_crew",
                return_value=fake_crew,
            ):
                result = executor.execute(REQUEST)
        self.assertFalse(result.ok)
        self.assertIn("contract validation", result.error)


if __name__ == "__main__":
    unittest.main()