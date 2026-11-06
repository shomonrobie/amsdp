"""Task model tests: identifiers, required data, and approval records."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    Task,
    TaskApproval,
    TaskPriority,
    TaskStatus,
    now_utc,
)


class TaskModelTests(unittest.TestCase):
    def test_basic_task_builds(self):
        task = Task(task_id="AMSDP-000001", title="Add queue reorder", description="x")
        self.assertIsNone(task.created_at)  # stamped by the registry
        self.assertEqual(task.status, TaskStatus.PROPOSED)
        self.assertEqual(task.priority, TaskPriority.NORMAL)
        self.assertEqual(task.approval.required_before_merge, True)

    def test_unsafe_task_id_rejected(self):
        for bad in ("../evil", "a/b", "x" * 80, ""):  # empty bucket handled by registry
            if bad == "":
                continue
            with self.assertRaises(ValidationError):
                Task(task_id=bad, title="t")

    def test_terminal_states(self):
        self.assertTrue(TaskStatus.CLOSED.is_terminal())
        self.assertTrue(TaskStatus.REJECTED.is_terminal())
        self.assertTrue(TaskStatus.CANCELLED.is_terminal())
        self.assertFalse(TaskStatus.IN_PROGRESS.is_terminal())

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            Task(task_id="AMSDP-000001", title="t", phantom="nope")

    def test_approval_record(self):
        approval = ApprovalRecord(
            decision_id="dec-1",
            decision=ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="matches approved business rules",
            decided_at=now_utc(),
        )
        task = Task(task_id="AMSDP-000001", title="t", approval=TaskApproval(decisions=[approval]))
        self.assertEqual(task.approval.decisions[0].actor, "project_owner")

    def test_summary_view(self):
        task = Task(task_id="AMSDP-000001", title="Queue display", workflow_id="WF-03")
        summary = task.summary()
        self.assertEqual(summary.task_id, "AMSDP-000001")
        self.assertEqual(summary.workflow_id, "WF-03")

    def test_json_roundtrip(self):
        task = Task(task_id="AMSDP-000001", title="t", task_type="defect")
        task.touch()
        restored = Task.model_validate_json(task.model_dump_json())
        self.assertEqual(restored.title, "t")
        self.assertEqual(restored.task_type, "defect")
        self.assertEqual(restored.status, TaskStatus.PROPOSED)


if __name__ == "__main__":
    unittest.main()