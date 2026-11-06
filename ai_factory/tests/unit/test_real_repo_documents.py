"""Integration check against the real repository documents.

This module validates the acceptance criterion "required governing documents
are detected and their status is reported" against the actual AMSDP
repository. It self-skips when run outside the AMSDP repository (e.g. in an
unrelated checkout).
"""

from __future__ import annotations

import unittest

from amsdp_ai_factory.context.document_registry import (
    DEFAULT_DOCUMENT_SET,
    DocumentRegistry,
)
from amsdp_ai_factory.utils.paths import discover_repo_root


class RealRepoDocumentTests(unittest.TestCase):
    def test_default_document_set_resolves_in_real_repo(self):
        root = discover_repo_root()
        if not (root / "docs").is_dir():
            self.skipTest("discovered repository root has no docs/ directory")

        registry = DocumentRegistry(root)
        scan = registry.scan()
        self.assertTrue(scan.ok, msg=f"missing: {scan.missing_mandatory}")

        found = {record.role: record for record in scan.records if record.exists}
        for role in (
            "business_rules",
            "mvp_scope",
            "system_architecture",
            "factory_architecture",
            "agent_specification",
            "development_workflow",
        ):
            self.assertIn(role, found, msg=f"{role} not found in real repo")

        business = found["business_rules"]
        self.assertEqual(business.version, "1.0")
        self.assertEqual(
            business.status, "Approved business-rule baseline for implementation"
        )
        self.assertEqual(len(business.sha256 or ""), 64)

        scope = found["mvp_scope"]
        self.assertEqual(scope.version, "1.0")
        self.assertEqual(scope.status, "Baseline for MVP planning")

        # The draft status of the master feature list must be preserved.
        feature = found["feature_list"]
        self.assertIn("Draft", feature.status or "")

        # Expected-but-absent prompt paths are reported as substitution notes.
        notes = "\n".join(scan.substitution_notes)
        self.assertIn("product-vision.md", notes)
        self.assertIn("scope.md", notes)

        # Documented authority order: specifications outrank references.
        order = {spec.role: spec.authority_order for spec in DEFAULT_DOCUMENT_SET}
        self.assertLess(order["agent_specification"], order["product_vision"])


if __name__ == "__main__":
    unittest.main()