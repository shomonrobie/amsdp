"""CI config validator tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tools.ci_config_validator import CIConfigValidatorTool

from tests.helpers import TempRepoCase


class CIConfigValidatorTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.workspace = self.repo_root
        self.tool = CIConfigValidatorTool(self.workspace)

    def test_no_ci_dir_is_ok(self):
        result = self.tool.run()
        self.assertTrue(result.ok)
        self.assertIn("no", result.output.lower())

    def test_valid_workflow_passes(self):
        gha = self.workspace / ".github" / "workflows"
        gha.mkdir(parents=True)
        (gha / "ci.yaml").write_text(
            "on: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: echo hi\n",
            encoding="utf-8",
        )
        result = self.tool.run()
        self.assertTrue(result.ok)

    def test_missing_jobs_section_flagged(self):
        gha = self.workspace / ".github" / "workflows"
        gha.mkdir(parents=True)
        (gha / "ci.yaml").write_text("name: no-jobs\n", encoding="utf-8")
        result = self.tool.run()
        self.assertIn("no 'jobs:'", result.output)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()