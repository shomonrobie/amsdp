"""Bounded test-runner tool tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.tools.test_runner import TestRunnerTool
from amsdp_ai_factory.tools.tool_registry import ToolPermissionError

from tests.helpers import TempRepoCase


class TestRunnerToolTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        workspace = self.repo_root / "var" / "workspaces" / "AMSDP-000001"
        workspace.mkdir(parents=True)
        self.workspace = workspace
        self.tool = TestRunnerTool(workspace)

    def test_allowed_unittest_discover_runs(self):
        (self.workspace / "tests").mkdir()
        (self.workspace / "tests" / "test_sample.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )
        result = self.tool.run(
            ["python", "-m", "unittest", "discover", "-s", "tests"]
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.command, "python -m unittest discover -s tests")

    def test_compileall_within_workspace(self):
        (self.workspace / "lib.py").write_text("x = 1\n", encoding="utf-8")
        result = self.tool.run(["python", "-m", "compileall", "-q", "lib.py"])
        self.assertTrue(result.ok)

    def test_disallowed_command_rejected(self):
        result = self.tool.run(["rm", "-rf", "/"])
        self.assertFalse(result.ok)
        self.assertIn("not in the allowlist", result.error)

    def test_shell_metacharacters_rejected(self):
        result = self.tool.run(["python", "-m", "unittest", "discover", "-s", "tests", "&&", "echo", "hi"])
        self.assertFalse(result.ok)

    def test_arg_escape_path_rejected(self):
        result = self.tool.run(["python", "-m", "py_compile", "../../etc/passwd"])
        self.assertFalse(result.ok)
        self.assertIn("escapes", result.error)

    def test_no_shell_invocation_used(self):
        # Paths containing shell syntax must be treated as literal, not executed.
        result = self.tool.run(["python", "-m", "py_compile", "x; echo pwned"])
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()