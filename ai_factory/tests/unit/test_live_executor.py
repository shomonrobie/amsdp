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

    def test_kickoff_exception_caught_and_reported(self):
        """Phase 4 regression: crew.kickoff() raises before output is returned.
        
        CrewAI's native structured-output validation (ConverterError from
        handle_partial_json, or agent-executor iteration-exhaustion) can
        propagate before a CrewOutput is produced. The executor must catch
        the exception and return an ExecutionResult with ok=False so the
        engine's bounded retry/failure path runs correctly.
        """
        with mock.patch.dict(
            os.environ, {"AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED": "1"}
        ):
            executor = CrewAIExecutor(_settings())
            failing_crew = SimpleNamespace(
                kickoff=lambda: (_ for _ in ()).throw(
                    RuntimeError("structured output validation failed: "
                                 "ConverterError: failed to convert to Pydantic")
                )
            )
            with mock.patch(
                "amsdp_ai_factory.execution.live.build_single_stage_crew",
                return_value=failing_crew,
            ):
                result = executor.execute(REQUEST)
        self.assertFalse(result.ok)
        self.assertIn("crew.kickoff() raised", result.error)
        self.assertIsInstance(result.tool_operations, list)

    def test_build_agent_sets_max_iter(self):
        """Phase 5 regression: build_agent must set max_iter on the CrewAI agent.
        
        The default CrewAI max_iter=25 is insufficient for assessment tasks
        that require many tool calls. The fix sets max_iter=60 to provide
        adequate headroom without permitting unbounded execution.
        """
        from amsdp_ai_factory.agents.definitions.a01_product_analyst import (
            PRODUCT_ANALYST,
        )
        from amsdp_ai_factory.execution.build_crews import build_agent

        agent = build_agent(PRODUCT_ANALYST)
        self.assertEqual(agent.max_iter, 60)

        # Verify other agents also get the increased limit
        from amsdp_ai_factory.agents.definitions.a02_system_architect import (
            SYSTEM_ARCHITECT,
        )
        agent2 = build_agent(SYSTEM_ARCHITECT)
        self.assertEqual(agent2.max_iter, 60)

if __name__ == "__main__":
    unittest.main()