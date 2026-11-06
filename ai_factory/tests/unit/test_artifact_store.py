"""Artifact-store tests: workspace containment and artifact verification."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.tasks.artifact_store import (
    ArtifactStore,
    ArtifactStoreError,
)
from amsdp_ai_factory.tasks.models import now_utc

from tests.helpers import TempRepoCase


class ArtifactStoreTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.store = ArtifactStore(self.repo_root / "var" / "workspaces", "AMSDP-000001")

    def test_workspace_created_under_root(self):
        workspace = self.store.ensure()
        self.assertEqual(workspace, self.repo_root / "var" / "workspaces" / "AMSDP-000001")
        self.assertTrue(workspace.is_dir())

    def test_resolve_keeps_paths_inside(self):
        target = self.store.resolve("docs/service_spec.md")
        self.assertEqual(target, self.store.workspace / "docs" / "service_spec.md")

    def test_resolve_rejects_escape(self):
        with self.assertRaises(ArtifactStoreError):
            self.store.resolve("../../outside.txt")
        with self.assertRaises(ArtifactStoreError):
            self.store.resolve("/etc/passwd")

    def test_register_artifact_verifies_and_hashes(self):
        workspace = self.store.ensure()
        path = workspace / "design.md"
        path.write_text("# Design\ncontent\n", encoding="utf-8")
        record = self.store.register_artifact(name="design", absolute_path=path, kind="design_doc")
        self.assertEqual(len(record.sha256 or ""), 64)
        self.assertEqual(record.size_bytes, path.stat().st_size)
        self.assertTrue(record.path.is_absolute())

    def test_register_artifact_outside_workspace_rejected(self):
        outside = Path(self._tmp.name) / "secret.txt"
        outside.write_text("must never be registered", encoding="utf-8")
        with self.assertRaises(ArtifactStoreError):
            self.store.register_artifact(name="secret", absolute_path=outside)

    def test_register_missing_file_rejected(self):
        self.store.ensure()
        ghost = self.store.workspace / "ghost.md"
        with self.assertRaises(ArtifactStoreError):
            self.store.register_artifact(name="ghost", absolute_path=ghost)

    def test_unsafe_task_id_blocks_store_creation(self):
        with self.assertRaises(ArtifactStoreError):
            ArtifactStore(self.repo_root / "var" / "workspaces", "../escape")

    def test_verify_reports_outside_and_missing(self):
        from amsdp_ai_factory.contracts.common import Severity

        self.store.ensure()
        outside = Path(self._tmp.name) / "x.md"
        outside.write_text("x", encoding="utf-8")
        check_outside = self.store.verify(outside)
        self.assertFalse(check_outside.ok)
        self.assertTrue(
            any(i.code == "artifact_outside_workspace" for i in check_outside.issues)
        )
        check_missing = self.store.verify(self.store.workspace / "nope.md")
        self.assertFalse(check_missing.ok)
        self.assertTrue(
            any(i.code == "artifact_missing" for i in check_missing.issues)
        )
        ok_file = self.store.workspace / "ok.md"
        ok_file.write_text("ok", encoding="utf-8")
        self.assertTrue(self.store.verify(ok_file).ok)


if __name__ == "__main__":
    unittest.main()