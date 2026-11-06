"""Repository-root discovery tests."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from amsdp_ai_factory.utils.paths import discover_repo_root, is_within

from tests.helpers import TempRepoCase


class RepoRootTests(TempRepoCase):
    def test_discovers_git_marker_walking_up(self):
        nested = self.repo_root / "a" / "b" / "c"
        nested.mkdir(parents=True)
        self.assertEqual(discover_repo_root(start=nested), self.repo_root)

    def test_start_itself_with_git_marker(self):
        self.assertEqual(discover_repo_root(start=self.repo_root), self.repo_root)

    def test_env_override_wins(self):
        with mock.patch.dict(
            "os.environ", {"AMSDP_FACTORY_REPO_ROOT": str(self.repo_root)}
        ):
            self.assertEqual(discover_repo_root(), self.repo_root)

    def test_env_override_invalid_raises_clear_error(self):
        with mock.patch.dict(
            "os.environ",
            {"AMSDP_FACTORY_REPO_ROOT": "/definitely/not/a/real/dir"},
        ):
            with self.assertRaises(ValueError):
                discover_repo_root()

    def test_no_marker_falls_back_to_start(self):
        plain = Path(self._tmp.name) / "plain"
        plain.mkdir(parents=True)
        self.assertEqual(discover_repo_root(start=plain), plain.resolve())


class PathContainmentTests(TempRepoCase):
    def test_inside_and_outside_detection(self):
        inside = self.repo_root / "docs" / "x.md"
        outside = Path(self._tmp.name) / "outside.md"
        self.assertTrue(is_within(self.repo_root, inside))
        self.assertTrue(is_within(self.repo_root, self.repo_root))
        self.assertFalse(is_within(self.repo_root, outside))

    def test_traversal_rejected(self):
        traversal = self.repo_root / ".." / ".." / "escape.md"
        self.assertFalse(is_within(self.repo_root, traversal))


if __name__ == "__main__":
    unittest.main()