"""Repository-read tool tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tools.repository_read import RepositoryReadTool
from amsdp_ai_factory.tools.tool_registry import ToolPermissionError

from tests.helpers import TempRepoCase


class RepositoryReadToolTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        (self.repo_root / "docs").mkdir()
        (self.repo_root / "docs" / "readme.md").write_text("hello queue world\n", encoding="utf-8")
        (self.repo_root / "app.py").write_text("def token():\n    pass\n", encoding="utf-8")
        self.tool = RepositoryReadTool(self.repo_root)

    def test_read_within_repo(self):
        result = self.tool.read_text("docs/readme.md")
        self.assertTrue(result.ok)
        self.assertIn("hello queue world", result.output)

    def test_read_escape_denied(self):
        result = self.tool.read_text("../outside.md")
        self.assertFalse(result.ok)
        self.assertIn("escapes", result.error)

    def test_list_paths(self):
        result = self.tool.list_paths()
        self.assertTrue(result.ok)
        self.assertIn("app.py", result.output)
        self.assertIn("docs/readme.md", result.output)

    def test_search_finds_match(self):
        result = self.tool.search("queue")
        self.assertTrue(result.ok)
        self.assertIn("docs/readme.md", result.output)
        self.assertNotIn("app.py", result.output)


class RepositoryReadEscapeTests(unittest.TestCase):
    def test_absolute_path_denied(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / ".git").mkdir()
            tool = RepositoryReadTool(root)
            result = tool.read_text("/etc/passwd")
            self.assertFalse(result.ok)
            self.assertIn("escapes", result.error)


if __name__ == "__main__":
    unittest.main()