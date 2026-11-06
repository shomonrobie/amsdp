"""Agent prompt template tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.agents.definitions import AGENT_INDEX
from amsdp_ai_factory.agents.prompts.templates import (
    GLOBAL_PROHIBITIONS,
    SOURCE_OF_TRUTH,
    build_role_prompt,
)


class PromptTemplateTests(unittest.TestCase):
    def test_prompt_contains_role_identity_and_governance(self):
        for agent_id in ("A01", "A06", "A09", "A11"):
            prompt = build_role_prompt(AGENT_INDEX[agent_id])
            self.assertIn(f"ROLE: {AGENT_INDEX[agent_id].role}", prompt)
            self.assertIn(f"AGENT ID: {agent_id}", prompt)
            self.assertIn("MISSION:", prompt)
            self.assertIn("EXPECTED OUTPUTS", prompt)
            self.assertIn("PROHIBITED ACTIONS:", prompt)
            self.assertIn("source-of-truth", prompt.lower())
            self.assertIn("untrusted", prompt.lower())

    def test_prompt_includes_each_prohibition(self):
        agent = AGENT_INDEX["A09"]
        prompt = build_role_prompt(agent)
        for item in agent.prohibited_actions:
            self.assertIn(item, prompt)

    def test_prompt_has_no_secret_shaped_values(self):
        for agent in AGENT_INDEX.values():
            prompt = build_role_prompt(agent)
            self.assertNotIn("api_key=", prompt)
            self.assertNotIn("password=", prompt)
            self.assertNotIn("Bearer ", prompt)

    def test_banner_sections_not_empty(self):
        self.assertIn("AMSDP_Business_Rules_V1.0.md", SOURCE_OF_TRUTH)
        self.assertIn("documents conflict", SOURCE_OF_TRUTH)
        self.assertIn("production", GLOBAL_PROHIBITIONS.lower())


if __name__ == "__main__":
    unittest.main()