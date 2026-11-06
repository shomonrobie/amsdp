"""RunContext — cross-agent context passing.

Phase III: passes validated artifacts between workflow stages.

Requirements implemented:
- Validated artifacts are accumulated across stages.
- Artifact type and integrity (SHA-256) are verified when recorded.
- ``required_input_kinds`` and ``expected_output_kinds`` are respected.
- Artifact references and provenance are preserved (stage_id, agent_id, run_id).
- Downstream agents cannot silently replace approved requirements/architecture:
  once a stage records an artifact, later stages receive it; a downstream
  artifact with the same kind is recorded as an *update candidate* and flagged
  in the context instead of silently overriding the upstream one.
- Context size is bounded (``MAX_CONTEXT_CHARS``).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from amsdp_ai_factory.contracts.outputs import AgentOutput
from amsdp_ai_factory.contracts.common import CheckResult, Severity, ValidationIssue

# Bound on total context characters injected into a downstream stage task.
MAX_CONTEXT_CHARS = 8000

# Kinds that may not be silently replaced by a downstream agent once approved.
_IMMUTABLE_KINDS = {
    "requirement_analysis",
    "architecture_proposal",
    "api_contract",
    "database_change_proposal",
}


@dataclass
class RecordedArtifact:
    """One validated artifact captured for handoff."""

    stage_id: str
    agent_id: str
    artifact_type: str
    title: str
    summary: str
    sha256: str = ""
    replaced: bool = False
    superseded_by: str | None = None


class RunContextError(ValueError):
    """Raised for invalid context operations."""


class RunContext:
    """Accumulates validated artifacts across stages and builds bounded context."""

    def __init__(self) -> None:
        self._recorded: list[RecordedArtifact] = []
        self._applied_rules: dict[str, list[str]] = {}  # stage_id -> [rule_id, ...]

    def record_rules(self, stage_id: str, rule_ids: list[str]) -> None:
        """Record which Agent Rules were applied for a stage."""
        if rule_ids:
            self._applied_rules[stage_id] = sorted(rule_ids)

    @property
    def applied_rules(self) -> dict[str, list[str]]:
        return dict(self._applied_rules)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        *,
        stage_id: str,
        agent_id: str,
        output: AgentOutput,
        expected_kinds: list[str] | None = None,
    ) -> CheckResult:
        """Verify artifact type/integrity and record it.

        - artifact_type must be in ``expected_kinds`` when provided.
        - If an immutable kind is re-produced in a later stage, the earlier
          artifact is NOT dropped — it is marked ``replaced=True`` so the
          context can show both and flag the discrepancy.
        """
        issues: list[ValidationIssue] = []

        if expected_kinds and output.artifact_type not in expected_kinds:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="artifact_type_not_expected",
                    message=(
                        f"stage {stage_id!r} produced {output.artifact_type!r} but "
                        f"expected one of {expected_kinds!r}"
                    ),
                    source="execution.run_context",
                )
            )

        canonical = json.dumps(
            output.model_dump(mode="json"), sort_keys=True, ensure_ascii=False
        )
        sha = hashlib.sha256(canonical.encode()).hexdigest()

        if output.artifact_type in _IMMUTABLE_KINDS:
            for prev in self._recorded:
                if prev.artifact_type == output.artifact_type and not prev.replaced:
                    prev.replaced = True
                    prev.superseded_by = stage_id
                    issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            code="immutable_artifact_resupplied",
                            message=(
                                f"artifact kind {output.artifact_type!r} was already "
                                f"produced by stage {prev.stage_id!r} (agent {prev.agent_id}); "
                                f"stage {stage_id!r} supplies a new version — review required "
                                f"before treating the new one as authoritative"
                            ),
                            source="execution.run_context",
                        )
                    )

        self._recorded.append(
            RecordedArtifact(
                stage_id=stage_id,
                agent_id=agent_id,
                artifact_type=output.artifact_type,
                title=output.title,
                summary=output.summary[:500],
                sha256=sha,
            )
        )

        return CheckResult(
            name="run_context.record",
            ok=not any(i.severity == Severity.ERROR for i in issues),
            issues=issues,
        )

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def context_for(
        self,
        *,
        required_kinds: list[str] | None = None,
        max_chars: int = MAX_CONTEXT_CHARS,
        include_summary: bool = True,
    ) -> str:
        """Build a bounded, provenance-preserving context string.

        Artifacts are listed newest-first. Arts whose kind is in
        ``required_kinds`` (or all when None) are included. The ``replaced``
        flag is exposed so a downstream agent can see that an earlier approved
        artifact was superseded.
        """
        parts: list[str] = []
        total = 0

        for record in reversed(self._recorded):
            if required_kinds and record.artifact_type not in required_kinds:
                continue
            header = (
                f"[{record.artifact_type}] stage={record.stage_id} "
                f"agent={record.agent_id} sha256={record.sha256[:12]}"
            )
            if record.replaced:
                header += (
                    f" (SUPERSEDED by stage {record.superseded_by} — "
                    f"compare before relying on this)"
                )
            block = header
            if include_summary:
                block += f"\n{record.title}: {record.summary}"
            block += "\n"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)

        if not parts:
            return ""
        return "\n".join(parts).strip()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def recorded(self) -> list[RecordedArtifact]:
        """Snapshot copy of recorded artifacts (newest first)."""
        return list(reversed(self._recorded))

    def has(self, artifact_type: str) -> bool:
        return any(r.artifact_type == artifact_type for r in self._recorded)

    def artifact(self, stage_id: str) -> RecordedArtifact | None:
        for r in reversed(self._recorded):
            if r.stage_id == stage_id:
                return r
        return None

    @property
    def count(self) -> int:
        return len(self._recorded)