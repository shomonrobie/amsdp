"""Tool registry tests: default-deny enforcement and binding integrity."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tools.tool_registry import (
    ToolCategory,
    ToolDefinition,
    ToolPermissionError,
    ToolRegistry,
    build_default_registry,
    validate_agent_tool_bindings,
)


class ToolRegistryPermissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = build_default_registry()

    def test_allowed_for_bound_agent(self):
        tool = self.registry.assert_allowed("A06", "run_tests")
        self.assertEqual(tool.tool_id, "run_tests")

    def test_unbound_agent_denied(self):
        with self.assertRaises(ToolPermissionError):
            self.registry.assert_allowed("A01", "run_tests")  # nothing bound for A01

    def test_unknown_tool_denied(self):
        with self.assertRaises(ToolPermissionError):
            self.registry.assert_allowed("A06", "does_not_exist")

    def test_planned_tool_denied_with_clear_message(self):
        # No planned tools remain — verify unknown tool is denied clearly.
        with self.assertRaises(ToolPermissionError) as ctx:
            self.registry.assert_allowed("A05", "does_not_exist")
        self.assertIn("unknown", str(ctx.exception))

    def test_registered_count(self):
        tools = self.registry.list()
        self.assertEqual(len(tools), 15)
        active = [t for t in tools if t.enabled]
        planned = [t for t in tools if not t.enabled]
        self.assertEqual(len(active), 15)
        self.assertEqual(len(planned), 0)

    def test_no_deploy_or_network_or_production_tools(self):
        for tool in self.registry.list():
            self.assertNotIn(tool.category, (ToolCategory.DEPLOY, ToolCategory.NETWORK))


class BindingValidatorTests(unittest.TestCase):
    def test_definitions_match_registry(self):
        from amsdp_ai_factory.agents.definitions import ALL_AGENTS

        errors = validate_agent_tool_bindings(list(ALL_AGENTS), build_default_registry())
        self.assertEqual(errors, [])

    def test_stale_definition_detected(self):
        from amsdp_ai_factory.agents.models import AgentDefinition

        registry = build_default_registry()
        rogue = AgentDefinition(
            agent_id="A99",
            role="Rogue",
            mission="x",
            goal="x",
            permitted_tools=["repo_read", "run_tests"],  # run_tests must fail for A99
        )
        errors = validate_agent_tool_bindings([rogue], registry)
        self.assertFalse(errors == [])
        self.assertTrue(any("A99" in error for error in errors))

    def test_custom_registry_denies_unknown_mappings(self):
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                tool_id="repo_read",
                name="r",
                description="d",
                category=ToolCategory.READ,
                enabled=True,
                status="active",
                allowed_agents={"A01"},
            )
        )
        with self.assertRaises(ToolPermissionError):
            registry.assert_allowed("A08", "repo_read")


if __name__ == "__main__":
    unittest.main()