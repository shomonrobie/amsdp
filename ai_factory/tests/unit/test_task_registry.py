"""Task registry tests: persistence, ids, and invalid input rejection."""

from __future__ import annotations

import unittest
from pathlib import Path

from amsdp_ai_factory.tasks.models import Task, TaskStatus
from amsdp_ai_factory.tasks.registry import (
    TaskRegistry,
    TaskRegistryError,
)

from tests.helpers import TempRepoCase


class TaskRegistryTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.store_dir = self.repo_root / "var" / "tasks"
        self.registry = TaskRegistry(self.store_dir)

    def test_create_assigns_stable_id(self):
        task = Task(title="Queue reorder feature")
        saved = self.registry.create(task)
        self.assertTrue(saved.task_id.startswith("AMSDP-"))
        self.assertIsNotNone(saved.created_at)
        self.assertIsNotNone(saved.updated_at)
        self.assertEqual(self.registry.count(), 1)

    def test_sequential_ids_increment(self):
        first = self.registry.create(Task(title="a"))
        second = self.registry.create(Task(title="b"))
        self.assertEqual(second.task_id, f"AMSDP-{int(first.task_id.split('-')[1]) + 1:06d}")

    def test_duplicate_id_rejected(self):
        self.registry.create(Task(task_id="AMSDP-000001", title="a"))
        with self.assertRaises(TaskRegistryError):
            self.registry.create(Task(task_id="AMSDP-000001", title="b"))

    def test_unsafe_id_rejected_at_model_boundary(self):
        # The task id pattern is enforced by the pydantic model itself, so a
        # path-traversal style id is rejected before it reaches the registry.
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Task(task_id="../../etc/passwd", title="x")

    def test_get_and_persistence_across_restart(self):
        task = self.registry.create(Task(task_id="AMSDP-000042", title="API contract", task_type="api_design"))
        # Simulate process restart: a new registry instance over the same dir.
        fresh = TaskRegistry(self.store_dir)
        loaded = fresh.get("AMSDP-000042")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.title, "API contract")
        self.assertEqual(loaded.task_type, "api_design")

    def test_update_save_persists_changes(self):
        task = self.registry.create(Task(task_id="AMSDP-000001", title="x"))
        task.status = TaskStatus.ANALYSIS
        self.registry.save(task)
        reloaded = TaskRegistry(self.store_dir).get("AMSDP-000001")
        self.assertEqual(reloaded.status, TaskStatus.ANALYSIS)

    def test_save_unknown_task_rejected(self):
        with self.assertRaises(TaskRegistryError):
            self.registry.save(Task(task_id="AMSDP-999999", title="ghost"))

    def test_list_ordering_and_filter(self):
        a = self.registry.create(Task(task_id="AMSDP-000001", title="first"))
        b = self.registry.create(Task(task_id="AMSDP-000002", title="second"))
        b.status = TaskStatus.BLOCKED
        self.registry.save(b)
        listing = self.registry.list()
        self.assertEqual(len(listing), 2)
        self.assertEqual(listing[0].task_id, b.task_id)  # newest first
        filtered = self.registry.list(status="blocked")
        self.assertEqual([s.task_id for s in filtered], [b.task_id])


if __name__ == "__main__":
    unittest.main()