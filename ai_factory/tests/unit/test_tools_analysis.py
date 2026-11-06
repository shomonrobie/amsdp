"""Static analysis and secret scan tool tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.tools.static_analysis import StaticAnalysisTool
from amsdp_ai_factory.tools.secret_scan import SecretScanTool

from tests.helpers import TempRepoCase


class StaticAnalysisTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.tool = StaticAnalysisTool(self.repo_root)

    def test_clean_code_passes(self):
        safe = self.repo_root / "app.py"
        safe.write_text("x = 1\nprint(x)\n", encoding="utf-8")
        result = self.tool.run()
        self.assertTrue(result.ok)
        self.assertIn("0 finding", result.summary)

    def test_eval_detected(self):
        code = self.repo_root / "danger.py"
        code.write_text("eval(input())\n", encoding="utf-8")
        result = self.tool.run()
        self.assertTrue(result.ok)  # tool runs to completion
        self.assertIn("eval", result.output)

    def test_hardcoded_password_detected(self):
        code = self.repo_root / "config.py"
        code.write_text('password = "admin123"\n', encoding="utf-8")
        result = self.tool.run()
        self.assertIn("hardcoded_password", result.output)


class SecretScanTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.tool = SecretScanTool(self.repo_root)

    def test_clean_workspace_scans_clean(self):
        (self.repo_root / "notes.md").write_text("no secrets here\n", encoding="utf-8")
        result = self.tool.run()
        self.assertTrue(result.ok)
        self.assertIn("0 hit", result.summary)

    def test_api_key_detected(self):
        (self.repo_root / "config.env").write_text(
            "API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8"
        )
        result = self.tool.run()
        self.assertFalse(result.error == "")
        self.assertGreater(len(result.output.strip().splitlines()), 0)
        self.assertIn("config.env", result.output)


if __name__ == "__main__":
    unittest.main()