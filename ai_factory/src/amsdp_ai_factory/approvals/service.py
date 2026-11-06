"""Approval service: request and decide human approval gates.

Integrates with the existing task lifecycle: every decision is applied
through ``tasks.lifecycle.transition`` with an ``ApprovalRecord``, so the
finite state machine and its audit history stay authoritative.
"""

from __future__ import annotations

from amsdp_ai_factory.runs.models import ApprovalRecord as RunApprovalRecord
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.lifecycle import transition
from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalState,
    Task,
    TaskStatus,
    now_utc,
)
from amsdp_ai_factory.tasks.registry import TaskRegistry


class ApprovalError(ValueError):
    """Raised for invalid approval operations."""


# Forward target when a gate is approved (Workflow V1.0 section 5.1).
GATE_FORWARD_TARGETS: dict[TaskStatus, TaskStatus] = {
    TaskStatus.HUMAN_DESIGN_APPROVAL: TaskStatus.READY_FOR_IMPLEMENTATION,
    TaskStatus.HUMAN_REVIEW: TaskStatus.APPROVED_FOR_MERGE,
    TaskStatus.AWAITING_DEPLOYMENT_APPROVAL: TaskStatus.RELEASED,
}


class PendingApproval:
    """Lightweight view of a task currently awaiting a human decision."""

    def __init__(self, task: Task) -> None:
        self.task = task

    @property
    def task_id(self) -> str:
        return self.task.task_id

    @property
    def title(self) -> str:
        return self.task.title

    @property
    def gate_status(self) -> TaskStatus:
        return self.task.status

    @property
    def forward_target(self) -> TaskStatus:
        return GATE_FORWARD_TARGETS[self.task.status]

    def as_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "gate_status": self.gate_status.value,
            "forward_target": self.forward_target.value,
            "approval_state": self.task.approval.state.value,
        }
class ApprovalService:
    """The single sanctioned route for human decisions on task gates."""

    def __init__(
        self, task_registry: TaskRegistry, run_recorder: RunRecorder | None = None
    ) -> None:
        self.task_registry = task_registry
        self.run_recorder = run_recorder

    # --- request ------------------------------------------------------------

    def request(
        self, task_id: str, requested_by: str = "", rationale: str = ""
    ) -> PendingApproval:
        """Mark a gated task as awaiting human approval (idempotent)."""
        task = self._require_task(task_id)
        if task.status not in GATE_FORWARD_TARGETS:
            raise ApprovalError(
                f"task {task_id!r} is in {task.status.value!r}; no human decision "
                "is being requested at this state"
            )
        if task.approval.state != ApprovalState.REQUESTED:
            task.approval.state = ApprovalState.REQUESTED
            task.escalation_notes.append(
                f"{requested_by or 'operator'}: approval requested for gate "
                f"{task.status.value} - {rationale}".strip()
            )
            self.task_registry.save(task)
        return PendingApproval(task)

    def pending(self) -> list[PendingApproval]:
        """All tasks currently paused at a human approval gate."""
        pending: list[PendingApproval] = []
        for summary in self.task_registry.list():
            task = self.task_registry.get(summary.task_id)
            if task is not None and task.status in GATE_FORWARD_TARGETS:
                pending.append(PendingApproval(task))
        pending.sort(key=lambda p: (p.task.updated_at or now_utc()))
        return pending
# --- decide -------------------------------------------------------------

    def decide(
        self,
        task_id: str,
        decision: ApprovalDecision,
        actor: str,
        rationale: str = "",
        run_id: str | None = None,
    ) -> Task:
        """Apply a human decision to a gated task via the lifecycle."""
        task = self._require_task(task_id)
        if task.status not in GATE_FORWARD_TARGETS:
            raise ApprovalError(
                f"task {task_id!r} is in {task.status.value!r}; only gate states "
                "accept decisions"
            )

        if decision == ApprovalDecision.APPROVED:
            target = GATE_FORWARD_TARGETS[task.status]
        elif decision == ApprovalDecision.REJECTED:
            target = TaskStatus.REJECTED
        else:
            target = TaskStatus.CHANGES_REQUESTED

        approval = _new_approval(decision, actor, rationale, task_id)
        # lifecycle.transition enforces arc + matching decision + history.
        transition(task, target, actor=actor, reason=rationale, approval=approval)
        self.task_registry.save(task)
        if self.run_recorder is not None and run_id is not None:
            self.run_recorder.add_approval(run_id, _to_run_approval(approval))
        return task

    # --- internals ----------------------------------------------------------

    def _require_task(self, task_id: str) -> Task:
        task = self.task_registry.get(task_id)
        if task is None:
            raise ApprovalError(f"unknown task: {task_id!r}")
        return task


def _new_approval(
    decision: ApprovalDecision, actor: str, rationale: str, task_id: str
) -> ApprovalRecord:
    return ApprovalRecord(
        decision_id=f"appr-{task_id}-{now_utc().strftime('%H%M%S%f')}",
        decision=decision,
        actor=actor,
        rationale=rationale,
        decided_at=now_utc(),
    )


def _to_run_approval(approval: ApprovalRecord) -> RunApprovalRecord:
    return RunApprovalRecord(
        decision_id=approval.decision_id,
        requested_at=approval.requested_at,
        decided_at=approval.decided_at,
        decision=approval.decision,
        actor=approval.actor,
        rationale=approval.rationale,
    )