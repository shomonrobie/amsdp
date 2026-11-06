"""Governed-document registry tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.context.document_registry import (
    DEFAULT_DOCUMENT_SET,
    DocumentCategory,
    DocumentRegistry,
    DocumentSpec,
    detect_document_metadata,
    sha256_file,
)

from tests.helpers import SAMPLE_DOC, TempRepoCase


def install_sample(root: Path) -> Path:
    target = root / "docs" / "product" / "AMSDP_Business_Rules_V1.0.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(SAMPLE_DOC.read_bytes())
    return target


class MetadataDetectionTests(unittest.TestCase):
    def test_detects_header_metadata_from_fixture(self):
        meta = detect_document_metadata(SAMPLE_DOC)
        self.assertEqual(meta["document_id"], "AMSDP-TEST-BR-001")
        self.assertEqual(meta["version"], "1.0")
        self.assertIn("Approved", meta["status"] or "")
        self.assertIn("Sample AMSDP Business Rules", meta["title"] or "")

    def test_sha256_is_64_hex(self):
        digest = sha256_file(SAMPLE_DOC)
        self.assertEqual(len(digest), 64)
        int(digest, 16)  # raises if not hex


class RegistryScanTests(TempRepoCase):
    def _registry(self, specs: list[DocumentSpec]):
        return DocumentRegistry(self.repo_root, documents=specs)

    def test_present_mandatory_document_detected(self):
        target = install_sample(self.repo_root)
        specs = [
            DocumentSpec(
                role="business_rules",
                rel_path="docs/product/AMSDP_Business_Rules_V1.0.md",
                category=DocumentCategory.MANDATORY,
                authority_order=1,
            )
        ]
        result = self._registry(specs).scan()
        self.assertTrue(result.ok)
        self.assertEqual(result.missing_mandatory, [])
        record = result.records[0]
        self.assertTrue(record.exists)
        self.assertEqual(record.resolved_path, target)
        self.assertEqual(record.sha256, sha256_file(target))
        self.assertEqual(record.document_id, "AMSDP-TEST-BR-001")
        self.assertEqual(record.version, "1.0")
        self.assertIsNotNone(record.last_checked)

    def test_missing_mandatory_is_reported_clearly(self):
        specs = [
            DocumentSpec(
                role="mvp_scope",
                rel_path="docs/product/AMSDP_MVP_SCOPE_V1.0.md",
                category=DocumentCategory.MANDATORY,
                authority_order=2,
            )
        ]
        result = self._registry(specs).scan()
        self.assertFalse(result.ok)
        self.assertEqual(len(result.missing_mandatory), 1)
        self.assertEqual(result.missing_mandatory[0].role, "mvp_scope")
        self.assertFalse(result.missing_mandatory[0].exists)

    def test_substitution_notes_recorded(self):
        install_sample(self.repo_root)
        specs = [
            DocumentSpec(
                role="mvp_scope",
                rel_path="docs/product/AMSDP_MVP_SCOPE_V1.0.md",
                category=DocumentCategory.MANDATORY,
                authority_order=2,
                substitutes_for=("docs/product/scope.md",),
            )
        ]
        result = self._registry(specs).scan()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("scope.md" in note for note in result.substitution_notes)
        )

    def test_report_lines_include_status(self):
        install_sample(self.repo_root)
        specs = [
            DocumentSpec(
                role="business_rules",
                rel_path="docs/product/AMSDP_Business_Rules_V1.0.md",
                category=DocumentCategory.MANDATORY,
                authority_order=1,
            )
        ]
        result = self._registry(specs).scan()
        lines = self._registry(specs).report_lines(result)
        joined = "\n".join(lines)
        self.assertIn("[FOUND]", joined)
        self.assertIn("Approved", joined)


class DefaultSetTests(unittest.TestCase):
    def test_six_mandatory_documents(self):
        mandatory = [
            spec for spec in DEFAULT_DOCUMENT_SET
            if spec.category == DocumentCategory.MANDATORY
        ]
        self.assertEqual(
            {spec.role for spec in mandatory},
            {
                "business_rules",
                "mvp_scope",
                "system_architecture",
                "factory_architecture",
                "agent_specification",
                "development_workflow",
            },
        )

    def test_authority_ordering(self):
        order = {spec.role: spec.authority_order for spec in DEFAULT_DOCUMENT_SET}
        self.assertEqual(order["business_rules"], 1)
        self.assertEqual(order["mvp_scope"], 2)
        self.assertEqual(order["system_architecture"], 3)
        # references must never outrank the approved specifications
        self.assertLess(order["development_workflow"], order["product_vision"])

    def test_draft_feature_list_is_reference_not_mandatory(self):
        feature = next(
            spec for spec in DEFAULT_DOCUMENT_SET if spec.role == "feature_list"
        )
        self.assertEqual(feature.category, DocumentCategory.REFERENCE)


if __name__ == "__main__":
    unittest.main()