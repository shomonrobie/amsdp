"""Artifact workspace and path containment.

Every artifact produced by an agent must live inside the task's approved
workspace under ``workspace_root/<task_id>/``. The store refuses any path
that escapes the workspace, verifies that claimed files actually exist, and
records a SHA-256 for the run record. No files outside the workspace are
ever read or written here.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from amsdp_ai_factory.contracts.common import CheckResult, Severity, ValidationIssue
from amsdp_ai_factory.tasks.models import TASK_ID_PATTERN, ArtifactRecord, now_utc

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactStoreError(ValueError):
    """Raised when an artifact path or registration is unsafe/invalid."""


def _sha256_file(path: Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


class ArtifactStore:
    """Constrained workspace for one task's artifacts."""

    def __init__(self, workspace_root: Path, task_id: str) -> None:
        if not re.fullmatch(TASK_ID_PATTERN, task_id):
            raise ArtifactStoreError(
                f"task id {task_id!r} is not safe for workspace creation"
            )
        self.workspace_root = Path(workspace_root).resolve()
        self.task_id = task_id
        self.workspace = self.workspace_root / task_id

    def ensure(self) -> Path:
        """Create the task workspace and return it."""
        self.workspace.mkdir(parents=True, exist_ok=True)
        return self.workspace

    def task_workspace(self) -> Path:
        return self.workspace

    # --- containment -------------------------------------------------------

    def resolve(self, relative_path: str) -> Path:
        """Resolve a workspace-relative path, refusing any escape."""
        candidate = (self.workspace / relative_path).resolve()
        if not self._is_inside(candidate):
            raise ArtifactStoreError(
                f"path {relative_path!r} escapes the task workspace {self.workspace}"
            )
        return candidate

    def is_inside(self, candidate: Path) -> bool:
        return self._is_inside(candidate)

    def _is_inside(self, candidate: Path) -> bool:
        resolved = candidate.resolve()
        return resolved == self.workspace or self.workspace in resolved.parents

    # --- registration & verification ----------------------------------------

    def register_artifact(
        self,
        *,
        name: str,
        absolute_path: Path | str,
        kind: str = "output",
        artifact_id: str | None = None,
    ) -> ArtifactRecord:
        """Verify an artifact exists inside the workspace and record it."""
        if not re.fullmatch(_SAFE_NAME, name):
            raise ArtifactStoreError(f"artifact name {name!r} is not safe")
        path = Path(absolute_path).resolve()
        if not self._is_inside(path):
            raise ArtifactStoreError(
                f"artifact {absolute_path!s} is outside the task workspace"
            )
        if not path.is_file():
            raise ArtifactStoreError(f"artifact does not exist or is not a file: {path}")
        digest = _sha256_file(path)
        return ArtifactRecord(
            artifact_id=artifact_id or f"{name}-{digest[:10]}",
            name=name,
            kind=kind,
            path=path,
            relative_to=str(path.relative_to(self.workspace)),
            sha256=digest,
            size_bytes=path.stat().st_size,
            created_at=now_utc(),
        )

    def verify(self, path: Path | str) -> CheckResult:
        """Independent verification that a claimed artifact path is valid."""
        candidate = Path(path).resolve()
        if not self._is_inside(candidate):
            return CheckResult(
                name="artifact_containment",
                ok=False,
                issues=[
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="artifact_outside_workspace",
                        message=f"{candidate} is outside the task workspace",
                        source="tasks.artifact_store",
                    )
                ],
            )
        if not candidate.is_file():
            return CheckResult(
                name="artifact_exists",
                ok=False,
                issues=[
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="artifact_missing",
                        message=f"claimed artifact does not exist: {candidate}",
                        source="tasks.artifact_store",
                    )
                ],
            )
        return CheckResult(name="artifact_exists", ok=True)