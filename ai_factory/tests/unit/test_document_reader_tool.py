"""Document-reader tool tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.context.document_registry import (
    DocumentCategory,
    DocumentRegistry,
    DocumentSpec,
)
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.tools.document_reader import DocumentReaderTool

from tests.helpers import TempRepoCase


class DocumentReaderToolTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        target = self.repo_root / "docs/product/AMSDP_Business_Rules_V1.0.md"
        target.parent.mkdir(parents=True)
        target.write_text(
            "# AMSDP Business Rules V1.0\n\n**Version:** 1.0\\\n"
            "**Status:** Approved SYNTHETIC fixture\n\nQueue is separate from status.\n",
            encoding="utf-8",
        )
        self.loader = ContextLoader(repo_root=self.repo_root)
        self.tool = DocumentReaderTool(self.loader)

    def test_read_present_role(self):
        result = self.tool.read("business_rules")
        self.assertTrue(result.ok)
        self.assertIn("Queue is separate", result.output)

    def test_read_missing_role_reports_missing(self):
        result = self.tool.read("agent_specification")  # not present in fixture repo
        self.assertFalse(result.ok)
        self.assertIn("unavailable", result.error)

    def test_list_roles_reports_presence(self):
        result = self.tool.list_roles()
        self.assertTrue(result.ok)
        self.assertIn("business_rules", result.output)

    def test_missing_documents_never_fabricated(self):
        # Even a configured role with an absent file returns unavailable, not bogus text.
        registry = DocumentRegistry(
            self.repo_root,
            documents=[
                DocumentSpec(
                    role="phantom",
                    rel_path="docs/absent.md",
                    category=DocumentCategory.MANDATORY,
                )
            ],
        )
        tool = DocumentReaderTool(ContextLoader(repo_root=self.repo_root, registry=registry))
        result = tool.read("phantom")
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()