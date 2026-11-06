"""Task lifecycle tests: finite transitions and approval gate enforcement."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tasks.lifecycle import (
    TaskTransitionError,
    transition,
    is_allowed,
    requires_human_approval,
)
from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalState,
    Task,
    TaskStatus,
    now_utc,
)


def make_task(status: TaskStatus = TaskStatus.PROPOSED) -> Task:
    task = Task(task_id="AMSDP-000001", title="synthetic task")
    task.status = status
    return task


class LifecycleHappyPathTests(unittest.TestCase):
    def test_requirement_to_design_flow(self):
        task = make_task()
        path = [
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
        ]
        for status in path:
            transition(task, status, actor="orchestrator")
        self.assertEqual(task.status, TaskStatus.DESIGN)
        self.assertEqual(len(task.history), len(path))
        self.assertEqual(task.history[-1].actor, "orchestrator")

    def test_design_approval_gate_requires_approval(self):
        task = make_task()
        for status in (
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.HUMAN_DESIGN_APPROVAL,
        ):
            transition(task, status, actor="orchestrator")
        self.assertEqual(task.approval.state, ApprovalState.REQUESTED)
        with self.assertRaises(TaskTransitionError):
            transition(
                task, TaskStatus.READY_FOR_IMPLEMENTATION, actor="orchestrator"
            )

    def test_design_approval_accepted_and_recorded(self):
        task = make_task()
        for status in (
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.HUMAN_DESIGN_APPROVAL,
        ):
            transition(task, status, actor="orchestrator")
        approval = ApprovalRecord(
            decision_id="d1",
            decision=ApprovalDecision.APPROVED,
            actor="project_owner",
        )
        transition(
            task,
            TaskStatus.READY_FOR_IMPLEMENTATION,
            actor="project_owner",
            approval=approval,
        )
        self.assertEqual(task.approval.state, ApprovalState.APPROVED)
        self.assertEqual(len(task.approval.decisions), 1)

    def test_design_approval_rejection_routes_to_rejected(self):
        task = make_task()
        for status in (
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.HUMAN_DESIGN_APPROVAL,
        ):
            transition(task, status, actor="orchestrator")
        rejection = ApprovalRecord(
            decision_id="d2",
            decision=ApprovalDecision.REJECTED,
            actor="project_owner",
        )
        transition(
            task, TaskStatus.REJECTED, actor="project_owner", approval=rejection
        )
        self.assertEqual(task.status, TaskStatus.REJECTED)
        self.assertTrue(task.status.is_terminal())

    def test_full_service_implementation_flow(self):
        task = make_task()
        approval = ApprovalRecord(
            decision_id="d1", decision=ApprovalDecision.APPROVED, actor="owner"
        )
        sequential = [
            (TaskStatus.INTAKE_VALIDATION, None),
            (TaskStatus.CONTEXT_VALIDATION, None),
            (TaskStatus.READY_FOR_ANALYSIS, None),
            (TaskStatus.ANALYSIS, None),
            (TaskStatus.READY_FOR_IMPLEMENTATION, None),  # no design required
            (TaskStatus.IN_PROGRESS, None),
            (TaskStatus.SELF_CHECK, None),
            (TaskStatus.INDEPENDENT_REVIEW, None),
            (TaskStatus.HUMAN_REVIEW, None),
            (TaskStatus.APPROVED_FOR_MERGE, approval),
        ]
        for status, record in sequential:
            transition(task, status, actor="orchestrator", approval=record)
        self.assertEqual(task.status, TaskStatus.APPROVED_FOR_MERGE)

class LifecycleFailureTests(unittest.TestCase):
    def test_invalid_arc_rejected(self):
        task = make_task()
        with self.assertRaises(TaskTransitionError):
            transition(task, TaskStatus.CLOSED, actor="orchestrator")

    def test_self_transition_rejected(self):
        task = make_task(TaskStatus.ANALYSIS)
        with self.assertRaises(TaskTransitionError):
            transition(task, TaskStatus.ANALYSIS, actor="orchestrator")

    def test_terminal_state_has_no_outgoing(self):
        task = make_task(TaskStatus.CANCELLED)
        with self.assertRaises(TaskTransitionError):
            transition(task, TaskStatus.CLOSED, actor="orchestrator")

    def test_wrong_approval_decision_rejected(self):
        task = make_task(TaskStatus.HUMAN_REVIEW)
        wrong = ApprovalRecord(
            decision_id="x",
            decision=ApprovalDecision.CHANGES_REQUESTED,
            actor="owner",
        )
        with self.assertRaises(TaskTransitionError):
            transition(
                task, TaskStatus.APPROVED_FOR_MERGE, actor="owner", approval=wrong
            )

    def test_changes_requested_loop_returns_to_work(self):
        task = make_task(TaskStatus.HUMAN_REVIEW)
        requested = ApprovalRecord(
            decision_id="r1",
            decision=ApprovalDecision.CHANGES_REQUESTED,
            actor="reviewer",
        )
        transition(
            task, TaskStatus.CHANGES_REQUESTED, actor="reviewer", approval=requested
        )
        self.assertEqual(task.status, TaskStatus.CHANGES_REQUESTED)
        transition(task, TaskStatus.IN_PROGRESS, actor="orchestrator")
        transition(task, TaskStatus.SELF_CHECK, actor="orchestrator")

    def test_failed_task_can_be_escalated(self):
        task = make_task(TaskStatus.FAILED)
        transition(
            task, TaskStatus.BLOCKED, actor="orchestrator", reason="provider outage"
        )
        self.assertEqual(task.status, TaskStatus.BLOCKED)
        self.assertEqual(task.history[-1].reason, "provider outage")


class LifecyclePredicateTests(unittest.TestCase):
    def test_predicates(self):
        self.assertTrue(is_allowed(TaskStatus.ANALYSIS, TaskStatus.DESIGN))
        self.assertFalse(is_allowed(TaskStatus.DESIGN, TaskStatus.CLOSED))
        self.assertTrue(
            requires_human_approval(
                TaskStatus.HUMAN_REVIEW, TaskStatus.APPROVED_FOR_MERGE
            )
        )
        self.assertFalse(
            requires_human_approval(TaskStatus.IN_PROGRESS, TaskStatus.SELF_CHECK)
        )


if __name__ == "__main__":
    unittest.main()