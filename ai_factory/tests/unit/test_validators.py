"""Validator tool tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.contracts.outputs import ArchitectureProposal
from amsdp_ai_factory.tools.validators import (
    ArchitectureValidatorTool,
    DocLinkValidatorTool,
)

from tests.helpers import TempRepoCase


class ArchitectureValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = ArchitectureValidatorTool()

    def _proposal(self, **kwargs):
        defaults = dict(
            task_id="AMSDP-000001",
            title="t",
            summary="s",
        )
        defaults.update(kwargs)
        return ArchitectureProposal(**defaults)

    def test_valid_proposal_passes(self):
        proposal = self._proposal(
            decision_required=True,
            affected_services=["appointment-service"],
            adr_required=True,
            alternatives=["A", "B"],
        )
        self.assertTrue(self.tool.validate(proposal).ok)

    def test_decision_without_services_fails(self):
        proposal = self._proposal(decision_required=True)
        self.assertFalse(self.tool.validate(proposal).ok)

    def test_adr_without_alternatives_fails(self):
        proposal = self._proposal(adr_required=True, alternatives=["only-one"])
        self.assertFalse(self.tool.validate(proposal).ok)


class DocLinkValidatorTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.workspace = self.repo_root / "var" / "workspaces" / "AMSDP-000001"
        self.workspace.mkdir(parents=True)
        self.tool = DocLinkValidatorTool(self.workspace)

    def test_good_links_pass(self):
        (self.workspace / "README.md").write_text(
            "see [other](docs/other.md)\n", encoding="utf-8"
        )
        (self.workspace / "docs").mkdir(exist_ok=True)
        (self.workspace / "docs" / "other.md").write_text("ok\n", encoding="utf-8")
        result = self.tool.run()
        self.assertTrue(result.ok)

    def test_broken_link_fails(self):
        (self.workspace / "README.md").write_text(
            "see [missing](docs/nope.md)\n", encoding="utf-8"
        )
        result = self.tool.run()
        self.assertFalse(result.ok)
        self.assertIn("does not exist", result.output)

    def test_escape_link_fails(self):
        (self.workspace / "README.md").write_text(
            "[up](../../../etc/passwd)\n", encoding="utf-8"
        )
        result = self.tool.run()
        self.assertFalse(result.ok)
        self.assertIn("escapes workspace", result.output)

    def test_external_links_ignored(self):
        (self.workspace / "README.md").write_text(
            "[http](https://example.com/x)\n", encoding="utf-8"
        )
        self.assertTrue(self.tool.run().ok)


if __name__ == "__main__":
    unittest.main()