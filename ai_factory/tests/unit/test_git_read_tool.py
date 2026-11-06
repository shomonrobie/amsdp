"""Git read-only tool tests (real temporary git repositories)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from amsdp_ai_factory.tools.git_read import GitReadTool
from amsdp_ai_factory.tools.tool_registry import ToolPermissionError


def make_git_repo() -> Path:
    """Create a small real git repository in a temp dir."""
    tmp = tempfile.mkdtemp()
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(
        ["git", "config", "user.email", "tests@example.invalid"],
        cwd=str(root),
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"], cwd=str(root), check=True
    )
    (root / "queue.py").write_text("TOKEN = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "queue.py"], cwd=str(root), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add queue module"], cwd=str(root), check=True)
    return root


@unittest.skipUnless(shutil.which("git"), "git executable not available")
class GitReadToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = make_git_repo()
        self.tool = GitReadTool(self.repo_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_root, ignore_errors=True)

    def test_status(self):
        result = self.tool.run("status")
        self.assertTrue(result.ok)
        self.assertIn("main", result.output)

    def test_log(self):
        result = self.tool.run("log", n=5)
        self.assertTrue(result.ok)
        self.assertIn("add queue module", result.output)

    def test_diff_and_branches(self):
        self.assertTrue(self.tool.run("diff_names").ok)
        self.assertTrue(self.tool.run("diff_stat").ok)
        self.assertTrue(self.tool.run("branches").ok)
        self.assertTrue(self.tool.run("head").ok)

    def test_unknown_command_denied(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._argv("push")

    def test_write_commands_have_no_path_through_tool(self):
        for name in ("push", "commit", "merge", "checkout", "reset", "rebase"):
            result = self.tool.run(name)
            self.assertFalse(result.ok)
            self.assertIn("not an allowed read command", result.error)

    def test_log_n_bounds(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._argv("log", n=500)
        with self.assertRaises(ToolPermissionError):
            self.tool._argv("log", n=None)


if __name__ == "__main__":
    unittest.main()