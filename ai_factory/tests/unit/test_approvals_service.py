"""Approval service tests: request, decide, and lifecycle integration."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.approvals.service import ApprovalError, ApprovalService
from amsdp_ai_factory.runs.models import RunStatus
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.lifecycle import transition
from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalState,
    Task,
    TaskStatus,
)
from amsdp_ai_factory.tasks.registry import TaskRegistry

from tests.helpers import TempRepoCase


def bring_to_gate(registry: TaskRegistry, gate: TaskStatus) -> Task:
    task = registry.create(
        Task(title="Synthetic approval test", workflow_id="WF-01", task_type="product_story")
    )
    path = (
        TaskStatus.INTAKE_VALIDATION,
        TaskStatus.CONTEXT_VALIDATION,
        TaskStatus.READY_FOR_ANALYSIS,
        TaskStatus.ANALYSIS,
    )
    for status in path:
        transition(task, status, actor="orchestrator")
    if gate == TaskStatus.HUMAN_DESIGN_APPROVAL:
        transition(task, TaskStatus.DESIGN, actor="orchestrator")
        transition(task, TaskStatus.HUMAN_DESIGN_APPROVAL, actor="orchestrator")
    elif gate == TaskStatus.HUMAN_REVIEW:
        transition(task, TaskStatus.READY_FOR_IMPLEMENTATION, actor="orchestrator")
        transition(task, TaskStatus.IN_PROGRESS, actor="orchestrator")
        transition(task, TaskStatus.SELF_CHECK, actor="orchestrator")
        transition(task, TaskStatus.INDEPENDENT_REVIEW, actor="orchestrator")
        transition(task, TaskStatus.HUMAN_REVIEW, actor="orchestrator")
    else:
        raise ValueError(gate)
    return registry.save(task)


class ApprovalServiceTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.registry = TaskRegistry(self.repo_root / "var" / "tasks")
        self.service = ApprovalService(self.registry)

    def test_approve_design_gate(self):
        task = bring_to_gate(self.registry, TaskStatus.HUMAN_DESIGN_APPROVAL)
        self.service.request(task.task_id, requested_by="orchestrator", rationale="design complete")
        updated = self.service.decide(
            task.task_id,
            ApprovalDecision.APPROVED,
            actor="project_owner",
            rationale="design approved",
        )
        self.assertEqual(updated.status, TaskStatus.READY_FOR_IMPLEMENTATION)
        self.assertEqual(updated.approval.state, ApprovalState.APPROVED)
        self.assertEqual(len(updated.approval.decisions), 1)

    def test_reject_human_review(self):
        task = bring_to_gate(self.registry, TaskStatus.HUMAN_REVIEW)
        updated = self.service.decide(
            task.task_id,
            ApprovalDecision.REJECTED,
            actor="project_owner",
            rationale="not acceptable",
        )
        self.assertEqual(updated.status, TaskStatus.REJECTED)
        self.assertTrue(updated.status.is_terminal())

    def test_changes_requested_returns_to_work(self):
        task = bring_to_gate(self.registry, TaskStatus.HUMAN_REVIEW)
        updated = self.service.decide(
            task.task_id,
            ApprovalDecision.CHANGES_REQUESTED,
            actor="reviewer",
            rationale="add concurrency case",
        )
        self.assertEqual(updated.status, TaskStatus.CHANGES_REQUESTED)
        transition(updated, TaskStatus.IN_PROGRESS, actor="orchestrator")
        self.registry.save(updated)
        self.assertEqual(
            self.registry.get(task.task_id).status, TaskStatus.IN_PROGRESS
        )

    def test_request_on_non_gate_raises(self):
        task = self.registry.create(Task(title="not gated"))
        with self.assertRaises(ApprovalError):
            self.service.request(task.task_id)

    def test_decide_on_non_gate_raises(self):
        task = self.registry.create(Task(title="not gated"))
        with self.assertRaises(ApprovalError):
            self.service.decide(task.task_id, ApprovalDecision.APPROVED, actor="x")

    def test_unknown_task_raises(self):
        with self.assertRaises(ApprovalError):
            self.service.request("AMSDP-999999")

    def test_pending_lists_gated_tasks_and_request_is_idempotent(self):
        gated = bring_to_gate(self.registry, TaskStatus.HUMAN_DESIGN_APPROVAL)
        self.registry.create(Task(title="ordinary"))
        before = self.service.pending()
        self.assertEqual([p.task_id for p in before], [gated.task_id])
        first = self.service.request(gated.task_id, requested_by="orchestrator")
        second = self.service.request(gated.task_id, requested_by="orchestrator")
        # Entering the gate already set REQUESTED; request() must not duplicate
        # notes or change the approval state.
        stored = self.registry.get(gated.task_id)
        self.assertEqual(len(stored.escalation_notes), 0)
        self.assertEqual(stored.approval.state, ApprovalState.REQUESTED)
        self.assertEqual(first.task_id, second.task_id)


class ApprovalRunIntegrationTests(TempRepoCase):
    def test_decision_recorded_on_run(self):
        registry = TaskRegistry(self.repo_root / "var" / "tasks")
        runs = RunRecorder(self.repo_root / "runs")
        service = ApprovalService(registry, run_recorder=runs)
        task = bring_to_gate(registry, TaskStatus.HUMAN_DESIGN_APPROVAL)
        run = runs.new_run(task_id=task.task_id, workflow_id="WF-01", environment="test")
        service.decide(
            task.task_id,
            ApprovalDecision.APPROVED,
            actor="project_owner",
            run_id=run.run_id,
        )
        runs.finish(run.run_id, status=RunStatus.SUCCEEDED)
        reloaded = runs.get(run.run_id)
        self.assertEqual(len(reloaded.approvals), 1)
        self.assertEqual(reloaded.approvals[0].actor, "project_owner")


if __name__ == "__main__":
    unittest.main()