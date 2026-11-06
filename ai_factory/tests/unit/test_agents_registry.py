"""Agent registry tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.agents.definitions import ALL_AGENTS
from amsdp_ai_factory.agents.models import AgentDefinition
from amsdp_ai_factory.agents.registry import AgentRegistry, AgentRegistryError


class AgentRegistryTests(unittest.TestCase):
    def test_registers_all_eleven(self):
        registry = AgentRegistry(ALL_AGENTS)
        summaries = registry.summaries()
        self.assertEqual(len(summaries), 11)
        self.assertEqual([s.agent_id for s in summaries], [f"A{i:02d}" for i in range(1, 12)])

    def test_get_and_require(self):
        registry = AgentRegistry(ALL_AGENTS)
        self.assertIsNotNone(registry.get("A06"))
        self.assertEqual(registry.require("A01").role, "Product Analyst")
        self.assertIsNone(registry.get("A99"))
        with self.assertRaises(AgentRegistryError):
            registry.require("A99")

    def test_duplicate_rejected(self):
        registry = AgentRegistry()
        registry.register(ALL_AGENTS[0])
        with self.assertRaises(AgentRegistryError):
            registry.register(ALL_AGENTS[0])

    def test_invalid_id_rejected_at_model_boundary(self):
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            AgentDefinition(
                agent_id="B01",
                role="Bogus",
                mission="x",
                goal="x",
                permitted_tools=["repo_read"],
            )

    def test_bad_agent_model_rejected(self):
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            AgentDefinition(agent_id="A12", role="", mission="x", goal="x")


if __name__ == "__main__":
    unittest.main()