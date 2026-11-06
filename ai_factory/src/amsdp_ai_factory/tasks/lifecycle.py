"""Validated task lifecycle and state transitions.

Implements the finite state machine from AI Development Workflow V1.0
section 5. Agents cannot invent states: every move goes through
``transition()``, which validates the arc, records the change, and enforces
human-approval requirements on decision gates.
"""

from __future__ import annotations

from datetime import datetime

from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalState,
    StateChangeRecord,
    Task,
    TaskStatus,
    now_utc,
)


class TaskTransitionError(ValueError):
    """Raised when a task state transition is invalid or unauthorized."""

    def __init__(
        self,
        from_status: TaskStatus,
        to_status: TaskStatus,
        reason: str,
    ) -> None:
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(
            f"Invalid task transition {from_status.value!r} -> {to_status.value!r}: "
            f"{reason}"
        )


# --- Allowed transition map (Workflow V1.0 section 5) ------------------------

ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PROPOSED: frozenset({TaskStatus.INTAKE_VALIDATION, TaskStatus.CANCELLED}),
    TaskStatus.INTAKE_VALIDATION: frozenset(
        {TaskStatus.NEEDS_CLARIFICATION, TaskStatus.CONTEXT_VALIDATION, TaskStatus.CANCELLED}
    ),
    TaskStatus.NEEDS_CLARIFICATION: frozenset(
        {TaskStatus.INTAKE_VALIDATION, TaskStatus.CONTEXT_VALIDATION, TaskStatus.CANCELLED}
    ),
    TaskStatus.CONTEXT_VALIDATION: frozenset(
        {
            TaskStatus.BLOCKED,
            TaskStatus.NEEDS_CLARIFICATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.BLOCKED: frozenset(
        {
            TaskStatus.NEEDS_CLARIFICATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.IN_PROGRESS,
            TaskStatus.SELF_CHECK,
            TaskStatus.INDEPENDENT_REVIEW,
            TaskStatus.HUMAN_REVIEW,
            TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
            TaskStatus.CANCELLED,
            TaskStatus.REJECTED,
        }
    ),
    TaskStatus.READY_FOR_ANALYSIS: frozenset({TaskStatus.ANALYSIS, TaskStatus.BLOCKED}),
    TaskStatus.ANALYSIS: frozenset(
        {
            TaskStatus.DESIGN,
            TaskStatus.READY_FOR_IMPLEMENTATION,
            TaskStatus.IN_PROGRESS,
            TaskStatus.RELEASE_READINESS,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.DESIGN: frozenset(
        {
            TaskStatus.HUMAN_DESIGN_APPROVAL,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.HUMAN_DESIGN_APPROVAL: frozenset(
        {
            TaskStatus.READY_FOR_IMPLEMENTATION,
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.REJECTED,
            TaskStatus.BLOCKED,
        }
    ),
    TaskStatus.READY_FOR_IMPLEMENTATION: frozenset(
        {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELLED}
    ),
    TaskStatus.IN_PROGRESS: frozenset(
        {
            TaskStatus.SELF_CHECK,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
            TaskStatus.CHANGES_REQUESTED,
        }
    ),
    TaskStatus.SELF_CHECK: frozenset(
        {
            TaskStatus.INDEPENDENT_REVIEW,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.INDEPENDENT_REVIEW: frozenset(
        {
            TaskStatus.HUMAN_REVIEW,
            TaskStatus.NOT_APPLICABLE,
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.CHANGES_REQUESTED: frozenset(
        {
            TaskStatus.ANALYSIS,
            TaskStatus.DESIGN,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.HUMAN_REVIEW: frozenset(
        {
            TaskStatus.APPROVED_FOR_MERGE,
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.REJECTED,
            TaskStatus.BLOCKED,
        }
    ),
    TaskStatus.APPROVED_FOR_MERGE: frozenset(
        {TaskStatus.MERGED, TaskStatus.BLOCKED, TaskStatus.CHANGES_REQUESTED}
    ),
    TaskStatus.MERGED: frozenset(
        {TaskStatus.RELEASE_READINESS, TaskStatus.CLOSED, TaskStatus.BLOCKED}
    ),
    TaskStatus.RELEASE_READINESS: frozenset(
        {
            TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
            TaskStatus.BLOCKED,
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.AWAITING_DEPLOYMENT_APPROVAL: frozenset(
        {TaskStatus.RELEASED, TaskStatus.CHANGES_REQUESTED, TaskStatus.BLOCKED}
    ),
    TaskStatus.RELEASED: frozenset({TaskStatus.CLOSED, TaskStatus.BLOCKED}),
    TaskStatus.NOT_APPLICABLE: frozenset({TaskStatus.HUMAN_REVIEW}),
    TaskStatus.FAILED: frozenset(
        {
            TaskStatus.BLOCKED,
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.CANCELLED,
            TaskStatus.REJECTED,
            TaskStatus.NEEDS_CLARIFICATION,
            TaskStatus.IN_PROGRESS,
        }
    ),
    # Terminal states have no outgoing transitions.
    TaskStatus.CLOSED: frozenset(),
    TaskStatus.REJECTED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}

# Human gates (Workflow V1.0 section 5.1): a decision made by a human actor.
HUMAN_APPROVAL_GATES: frozenset[TaskStatus] = frozenset(
    {
        TaskStatus.HUMAN_DESIGN_APPROVAL,
        TaskStatus.HUMAN_REVIEW,
        TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
    }
)

# Forward arcs that require an APPROVED decision record.
APPROVAL_REQUIRED_FORWARD: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
    {
        (TaskStatus.HUMAN_DESIGN_APPROVAL, TaskStatus.READY_FOR_IMPLEMENTATION),
        (TaskStatus.HUMAN_REVIEW, TaskStatus.APPROVED_FOR_MERGE),
        (TaskStatus.AWAITING_DEPLOYMENT_APPROVAL, TaskStatus.RELEASED),
    }
)

# Arcs that require a matching REJECTED / CHANGES_REQUESTED decision record.
APPROVAL_REQUIRED_DENIAL: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
    {
        (TaskStatus.HUMAN_DESIGN_APPROVAL, TaskStatus.REJECTED),
        (TaskStatus.HUMAN_DESIGN_APPROVAL, TaskStatus.CHANGES_REQUESTED),
        (TaskStatus.HUMAN_REVIEW, TaskStatus.REJECTED),
        (TaskStatus.HUMAN_REVIEW, TaskStatus.CHANGES_REQUESTED),
        (TaskStatus.AWAITING_DEPLOYMENT_APPROVAL, TaskStatus.CHANGES_REQUESTED),
    }
)


def is_allowed(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """True when the arc exists in the finite state machine."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, frozenset())


def requires_human_approval(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """True when the arc is a human decision gate."""
    return (from_status, to_status) in APPROVAL_REQUIRED_FORWARD or (
        from_status,
        to_status,
    ) in APPROVAL_REQUIRED_DENIAL


def _expected_decision(from_status: TaskStatus, to_status: TaskStatus) -> ApprovalDecision:
    if to_status == TaskStatus.REJECTED:
        return ApprovalDecision.REJECTED
    if to_status == TaskStatus.CHANGES_REQUESTED:
        return ApprovalDecision.CHANGES_REQUESTED
    if (from_status, to_status) in APPROVAL_REQUIRED_FORWARD:
        return ApprovalDecision.APPROVED
    raise TaskTransitionError(from_status, to_status, "arc is not an approval gate")


def transition(
    task: Task,
    to_status: TaskStatus,
    *,
    actor: str,
    reason: str = "",
    approval: ApprovalRecord | None = None,
    at: datetime | None = None,
) -> Task:
    """Validate and apply one task state transition. Mutates and returns ``task``.

    Rules enforced here:
    - the arc must exist in the finite state machine;
    - self-transitions are rejected (no silent no-op jumps);
    - human decision gates require an ``ApprovalRecord`` whose decision
      matches the target state;
    - every change is appended to ``task.history`` with actor and reason.
    """
    if not isinstance(to_status, TaskStatus):
        try:
            to_status = TaskStatus(to_status)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"unknown task status: {to_status!r}") from exc

    stamp: datetime = at or now_utc()
    if task.status == to_status:
        raise TaskTransitionError(
            task.status, to_status, "self-transition is not allowed (state already set)"
        )
    if not is_allowed(task.status, to_status):
        raise TaskTransitionError(
            task.status, to_status, "arc is not part of the approved state machine"
        )

    if requires_human_approval(task.status, to_status):
        if approval is None:
            raise TaskTransitionError(
                task.status,
                to_status,
                "this decision gate requires an explicit human ApprovalRecord",
            )
        expected = _expected_decision(task.status, to_status)
        if approval.decision != expected:
            raise TaskTransitionError(
                task.status,
                to_status,
                f"approval decision {approval.decision.value!r} does not match "
                f"required {expected.value!r}",
            )
        if approval.decided_at is None:
            approval.decided_at = stamp
        task.approval.decisions.append(approval)
        state = {
            ApprovalDecision.APPROVED: ApprovalState.APPROVED,
            ApprovalDecision.REJECTED: ApprovalState.REJECTED,
            ApprovalDecision.CHANGES_REQUESTED: ApprovalState.CHANGES_REQUESTED,
        }[approval.decision]
        task.approval.state = state

    # Entering a human gate means the approval is now being requested.
    if to_status in HUMAN_APPROVAL_GATES and task.approval.state in (
        ApprovalState.NOT_REQUESTED,
        ApprovalState.APPROVED,
        ApprovalState.CHANGES_REQUESTED,
        ApprovalState.REJECTED,
    ):
        task.approval.state = ApprovalState.REQUESTED

    task.history.append(
        StateChangeRecord(
            from_status=task.status,
            to_status=to_status,
            actor=actor,
            at=stamp,
            reason=reason,
        )
    )
    task.status = to_status
    task.updated_at = stamp
    return task