"""Context loader and task-type selector tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.context.document_registry import (
    DEFAULT_DOCUMENT_SET,
    DocumentCategory,
    DocumentRegistry,
    DocumentSpec,
)
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.context.selectors import (
    KNOWN_TASK_TYPES,
    select_document_roles,
)

from tests.helpers import TempRepoCase, SAMPLE_DOC


def write_doc(root: Path, rel: str, content: str) -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


class SelectorTests(unittest.TestCase):
    def test_known_task_type(self):
        roles = select_document_roles("Product Story")
        self.assertEqual(roles, ("business_rules", "mvp_scope", "feature_list"))

    def test_dashes_normalize_to_underscores(self):
        roles = select_document_roles("backend-implementation")
        self.assertEqual(
            roles, ("business_rules", "mvp_scope", "system_architecture")
        )

    def test_unknown_type_uses_safe_default(self):
        self.assertEqual(
            select_document_roles("brand_new_thing"),
            ("business_rules", "mvp_scope", "system_architecture"),
        )

    def test_empty_type_uses_safe_default(self):
        self.assertEqual(
            select_document_roles(None),
            ("business_rules", "mvp_scope", "system_architecture"),
        )
        self.assertEqual(
            select_document_roles(""),
            ("business_rules", "mvp_scope", "system_architecture"),
        )

    def test_known_types_nonempty(self):
        self.assertTrue(KNOWN_TASK_TYPES)


class LoaderTests(TempRepoCase):
    def _loader(self) -> ContextLoader:
        write_doc(
            self.repo_root,
            "docs/product/AMSDP_Business_Rules_V1.0.md",
            "# AMSDP Business Rules V1.0\n\n**Version:** 1.0\\\n**Status:** Approved SYNTHETIC fixture\n",
        )
        write_doc(
            self.repo_root,
            "docs/product/AMSDP_MVP_SCOPE_V1.0.md",
            "# AMSDP MVP Scope V1.0\n",
        )
        return ContextLoader(repo_root=self.repo_root)

    def test_load_document_by_role(self):
        loader = self._loader()
        doc = loader.load_document("business_rules")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.role, "business_rules")
        self.assertIn("SYNTHETIC", doc.text)
        self.assertEqual(len(doc.record.sha256 or ""), 64)

    def test_load_unknown_role_returns_none(self):
        loader = self._loader()
        self.assertIsNone(loader.load_document("not_a_role"))
        self.assertIsNone(loader.load_document("agent_specification"))

    def test_max_chars_bounds_content(self):
        loader = self._loader()
        doc = loader.load_document("business_rules", max_chars=20)
        self.assertLessEqual(len(doc.text.split("\\n")[0]) + 1, 48)
        self.assertIn("truncated", doc.text)

    def test_load_for_task_selects_relevant_documents(self):
        loader = self._loader()
        docs = loader.load_for_task("product_story")
        roles = {doc.role for doc in docs}
        self.assertIn("business_rules", roles)
        self.assertIn("mvp_scope", roles)
        # feature_list is selected but absent from the fixture repo: it is
        # simply not loaded — never fabricated.
        self.assertNotIn("feature_list", roles)

    def test_loading_outside_repository_refused(self):
        outside = Path(self._tmp.name) / "outside.md"
        outside.write_text("must never be loaded", encoding="utf-8")
        spec = DocumentSpec(
            role="evil",
            rel_path="../outside.md",
            category=DocumentCategory.REFERENCE,
        )
        registry = DocumentRegistry(self.repo_root, documents=[spec])
        loader = ContextLoader(repo_root=self.repo_root, registry=registry)
        record = next(
            (r for r in loader.scan().records if r.role == "evil"), None
        )
        self.assertIsNotNone(record)
        self.assertIsNone(loader.load_document("evil"))

    def test_summary_is_plain_and_non_secret(self):
        loader = self._loader()
        summary = loader.summary()
        # The fixture repository only supplies two of the six mandatory
        # documents, so the summary must report the gap honestly.
        self.assertEqual(summary["ok"], False)
        self.assertEqual(summary["repo_root"], str(self.repo_root))
        self.assertEqual(summary["documents_scanned"], len(DEFAULT_DOCUMENT_SET))
        self.assertEqual(
            sorted(summary["missing_mandatory"]),
            [
                "agent_specification",
                "development_workflow",
                "factory_architecture",
                "system_architecture",
            ],
        )


if __name__ == "__main__":
    unittest.main()