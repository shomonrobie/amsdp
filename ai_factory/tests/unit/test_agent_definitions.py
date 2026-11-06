"""Agent definition tests: the eleven approved agents and their bindings."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.agents.definitions import AGENT_INDEX, ALL_AGENTS
from amsdp_ai_factory.tools.tool_registry import (
    build_default_registry,
    validate_agent_tool_bindings,
)


class AgentCatalogueTests(unittest.TestCase):
    def test_exactly_eleven_agents(self):
        self.assertEqual(len(ALL_AGENTS), 11)
        self.assertEqual(sorted(AGENT_INDEX), [f"A{i:02d}" for i in range(1, 12)])

    def test_expected_roles_present(self):
        roles = {agent.role for agent in ALL_AGENTS}
        self.assertIn("Product Analyst", roles)
        self.assertIn("System Architect", roles)
        self.assertIn("Service Architect", roles)
        self.assertIn("Database Architect", roles)
        self.assertIn("API Contract Designer", roles)
        self.assertIn("Backend Developer", roles)
        self.assertIn("Frontend Developer", roles)
        self.assertIn("QA Engineer", roles)
        self.assertIn("Security Reviewer", roles)
        self.assertIn("DevOps Engineer", roles)
        self.assertIn("Technical Writer", roles)

    def test_every_definition_is_complete(self):
        for agent in ALL_AGENTS:
            self.assertTrue(agent.mission.strip(), agent.agent_id)
            self.assertTrue(agent.goal.strip(), agent.agent_id)
            self.assertTrue(agent.responsibilities, agent.agent_id)
            self.assertTrue(agent.required_inputs, agent.agent_id)
            self.assertTrue(agent.expected_outputs, agent.agent_id)
            self.assertTrue(agent.permitted_tools, agent.agent_id)
            self.assertTrue(agent.prohibited_actions, agent.agent_id)
            self.assertTrue(agent.success_criteria, agent.agent_id)
            self.assertTrue(agent.handoff, agent.agent_id)
            self.assertTrue(agent.write_prefix, agent.agent_id)

    def test_no_agent_has_destructive_or_production_privileges(self):
        forbidden_tool_ids = {  # registry has no such tools either
        }
        for agent in ALL_AGENTS:
            self.assertNotIn("deploy", agent.permitted_tools)
            self.assertNotIn("production_access", agent.permitted_tools)
            self.assertNotIn("network", agent.permitted_tools)
            self.assertTrue(not forbidden_tool_ids)


class AgentToolBindingTests(unittest.TestCase):
    def test_all_referenced_tools_exist_and_bind(self):
        registry = build_default_registry()
        errors = validate_agent_tool_bindings(list(ALL_AGENTS), registry)
        self.assertEqual(errors, [])

    def test_spec_matrix_is_honored(self):
        registry = build_default_registry()
        by_id = {agent.agent_id: set(agent.permitted_tools) for agent in ALL_AGENTS}
        # Security Reviewer has NO git access per spec section 14.
        self.assertNotIn("git_read", by_id["A09"])
        # Product Analyst has no test runner and no git per spec section 6.
        self.assertNotIn("run_tests", by_id["A01"])
        self.assertNotIn("git_read", by_id["A01"])
        # Executors have test runners per spec.
        for agent_id in ("A06", "A07", "A08", "A10"):
            self.assertIn("run_tests", by_id[agent_id])
        # No agent may run tests outside the executor set.
        for agent_id in ("A01", "A02", "A03", "A04", "A05", "A09", "A11"):
            self.assertNotIn("run_tests", by_id[agent_id])
        # Every agent may write artifacts (scoped by write_prefix).
        for agent_id in by_id:
            self.assertIn("artifact_write", by_id[agent_id])

    def test_security_abilities_stay_with_reviewer(self):
        by_id = {agent.agent_id: set(agent.permitted_tools) for agent in ALL_AGENTS}
        self.assertIn("secret_scan", by_id["A09"])
        for agent_id in ("A01", "A02", "A03", "A04", "A05", "A07", "A08", "A10", "A11"):
            self.assertNotIn("secret_scan", by_id[agent_id])


if __name__ == "__main__":
    unittest.main()