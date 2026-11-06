"""Artifact-writer tool tests: prefix confinement and registration."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
from amsdp_ai_factory.tools.artifact_writer import ArtifactWriterTool
from amsdp_ai_factory.tools.tool_registry import ToolPermissionError

from tests.helpers import TempRepoCase


class ArtifactWriterToolTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.store = ArtifactStore(self.repo_root / "var" / "workspaces", "AMSDP-000001")
        self.store.ensure()
        self.tool = ArtifactWriterTool(self.store, write_prefix="contracts")

    def test_write_within_prefix(self):
        result = self.tool.write("api/openapi.yaml", "openapi: 3.0")
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.artifact)
        self.assertEqual(len(result.artifact.sha256 or ""), 64)
        target = self.store.workspace / "contracts/api/openapi.yaml"
        self.assertTrue(target.is_file())

    def test_write_outside_prefix_denied(self):
        result = self.tool.write("../database/schema.sql", "CREATE TABLE x;")
        self.assertFalse(result.ok)
        self.assertIn("escap", result.error)

    def test_write_absolute_escape_denied(self):
        result = self.tool.write("/etc/evil.txt", "boom")
        self.assertFalse(result.ok)

    def test_read_back_and_list(self):
        self.tool.write("openapi.yaml", "openapi: 3.0")
        read = self.tool.read("openapi.yaml")
        self.assertTrue(read.ok)
        self.assertIn("openapi: 3.0", read.output)
        listing = self.tool.list()
        self.assertIn("contracts/openapi.yaml", listing.output)

    def test_invalid_prefix_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            ArtifactWriterTool(self.store, write_prefix="../evil")

    def test_another_agent_cannot_touch_other_prefix(self):
        # A different prefix is a different tool instance scoped elsewhere.
        other = ArtifactWriterTool(self.store, write_prefix="database")
        result = other.write("schema.sql", "CREATE TABLE x;")
        self.assertTrue(result.ok)
        self.assertFalse((self.store.workspace / "contracts").exists())


if __name__ == "__main__":
    unittest.main()