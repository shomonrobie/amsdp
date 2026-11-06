"""Environment validation tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.contracts.common import Severity
from amsdp_ai_factory.validation.configuration import validate_environment

from tests.helpers import TempRepoCase


class ValidationTests(TempRepoCase):
    def _settings(self) -> FactorySettings:
        return FactorySettings(
            _env_file=None,
            environment="test",
            repo_root=str(self.repo_root),
        )

    def test_missing_mandatory_documents_fail_closed(self):
        report = validate_environment(self._settings())
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                issue.code == "mandatory_document_missing"
                for issue in report.issues
            )
        )
        self.assertTrue(report.python_version)

    def test_report_ok_when_all_mandatory_documents_present(self):
        from tests.helpers import SAMPLE_DOC

        self.repo_root.joinpath("docs/product").mkdir(parents=True, exist_ok=True)
        self.repo_root.joinpath("docs/architecture").mkdir(parents=True, exist_ok=True)
        business = self.repo_root / "docs/product/AMSDP_Business_Rules_V1.0.md"
        business.write_bytes(SAMPLE_DOC.read_bytes())

        # Install a synthetic fixture for each remaining mandatory document so
        # validation passes for this disposable, fictional repository only.
        remaining_mandatory = (
            "docs/product/AMSDP_MVP_SCOPE_V1.0.md",
            "docs/architecture/AMSDP_System_Architecture_V1.0.md",
            "docs/architecture/AMSDP_AI_Factory_Architecture_V1.0.md",
            "docs/architecture/AMSDP_AI_Agent_Specification_V1.0.md",
            "docs/architecture/AMSDP_AI_Development_Workflow_V1.0.md",
        )
        for rel in remaining_mandatory:
            target = self.repo_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"# {Path(rel).name}\n\n**Version:** 1.0\\\n"
                "**Status:** Proposed SYNTHETIC fixture\n",
                encoding="utf-8",
            )

        report = validate_environment(self._settings())
        self.assertTrue(report.ok)
        errors = [i for i in report.issues if i.severity == Severity.ERROR]
        self.assertEqual(errors, [])

    def test_as_text_renders(self):
        report = validate_environment(self._settings())
        text = report.as_text()
        self.assertIn("Python:", text)
        self.assertIn("Result:", text)


if __name__ == "__main__":
    unittest.main()