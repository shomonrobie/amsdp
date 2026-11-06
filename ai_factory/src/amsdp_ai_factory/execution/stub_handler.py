"""Safe stub handler for demo/test workflow runs.

Produces a clearly labeled synthetic output artifact for any expected kind,
so the full factory control model (stages, gates, approvals, run records)
can be exercised without any model provider. Outputs are explicitly marked
``[STUB-SYNTHETIC]`` and are never represented as real analysis.
"""

from __future__ import annotations

from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS, AgentOutput, ArtifactKind
from amsdp_ai_factory.execution.models import ExecutionRequest


def build_stub_handler():
    """Return a handler producing synthetic, clearly-labeled outputs."""

    def handler(request: ExecutionRequest) -> AgentOutput:
        model = ARTIFACT_MODELS[ArtifactKind(request.expected_artifact_kind)]
        return model(
            task_id=request.task_id,
            workflow_id=request.workflow_id,
            stage_id=request.stage_id,
            agent_id=request.agent_id,
            title=f"[STUB-SYNTHETIC] {request.stage_id}",
            summary="STUB MODE synthetic output; not a real analysis and never "
            "treated as verified product work.",
        )

    return handler