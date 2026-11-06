"""Shared test helpers.

Bootstraps ``sys.path`` so the local ``src`` package is importable without
installation, and provides temporary pseudo-repository fixtures. Everything
here uses synthetic data only.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

AI_FACTORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = AI_FACTORY_ROOT / "src"
FIXTURES_DIR = AI_FACTORY_ROOT / "tests" / "fixtures"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SAMPLE_DOC = FIXTURES_DIR / "documents" / "sample_business_rules.md"


def make_pseudo_repo(root: Path) -> Path:
    """Create a temporary pseudo-repository containing a .git marker.

    ``root`` must be an empty temporary directory. The ``.git`` marker is a
    plain directory — enough for repository-root discovery tests.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir(exist_ok=True)
    return root


class TempRepoCase(unittest.TestCase):
    """TestCase that provides a disposable pseudo-repository."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name) / "repo"
        self.repo_root = make_pseudo_repo(root)

    def tearDown(self) -> None:
        self._tmp.cleanup()