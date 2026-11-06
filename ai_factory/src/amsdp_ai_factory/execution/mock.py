"""Mock agent executor.

Replaces the CrewAI provider executor in tests and stub runs. A callable
handler supplies the canned ``AgentOutput``; the mock validates it against
the output contracts and verifies every claimed evidence path inside the
task workspace. No model, provider, or network is ever contacted.
"""

from __future__ import annotations

from collections.abc import Callable

from amsdp_ai_factory.contracts.common import Severity, ValidationIssue
from amsdp_ai_factory.contracts.outputs import AgentOutput, validate_output
from amsdp_ai_factory.execution.models import ExecutionRequest, ExecutionResult
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore


class MockAgentExecutor:
    """Executes agent stages with canned outputs under full validation."""

    def __init__(
        self,
        handler: Callable[[ExecutionRequest], AgentOutput] | None = None,
    ) -> None:
        self._handler = handler

    def execute(
        self,
        request: ExecutionRequest,
        artifact_store: ArtifactStore | None = None,
    ) -> ExecutionResult:
        """Run the mock stage and validate the result end-to-end."""
        if self._handler is None:
            return ExecutionResult(
                ok=False,
                task_id=request.task_id,
                stage_id=request.stage_id,
                agent_id=request.agent_id,
                error="no mock handler registered for this executor",
            )
        try:
            output = self._handler(request)
        except Exception as exc:  # handler failures are reported, never silent
            return ExecutionResult(
                ok=False,
                task_id=request.task_id,
                stage_id=request.stage_id,
                agent_id=request.agent_id,
                error=f"mock handler raised: {exc}",
            )

        checks = [validate_output(output)]
        issues: list[ValidationIssue] = []

        # Evidence-path verification: every claimed path must exist inside the
        # task workspace.
        if artifact_store is not None:
            for evidence in output.evidence:
                check = artifact_store.verify(evidence.path)
                checks.append(check)
                evidence.verified = check.ok
                if not check.ok:
                    issues.extend(check.issues)

        ok = checks and all(check.ok for check in checks)
        return ExecutionResult(
            ok=ok,
            task_id=request.task_id,
            stage_id=request.stage_id,
            agent_id=request.agent_id,
            output=output,
            checks=checks,
            error="" if ok else _first_error(checks),
        )


def _first_error(checks) -> str:
    for check in checks:
        for issue in check.issues:
            if issue.severity == Severity.ERROR:
                return f"{check.name}: {issue.message}"
    return "validation failed"