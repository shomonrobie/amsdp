"""Workspace-bounded artifact writer tool.

Writes files under ``<task workspace>/<write_prefix>/`` only. The prefix is
the agent's assigned subpath (e.g. ``architecture``, ``contracts``), so an
agent can never touch another discipline's outputs or escape the workspace.
Writes are registered as verified artifacts.
"""

from __future__ import annotations

import re
from pathlib import Path

from amsdp_ai_factory.tasks.artifact_store import ArtifactStore, ArtifactStoreError
from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
)

_SAFE_REL = re.compile(r"^[A-Za-z0-9_./-]+$")


class ArtifactWriterTool:
    """Tool id ``artifact_write`` — scoped, registered workspace writes."""

    tool_id = "artifact_write"

    def __init__(self, store: ArtifactStore, write_prefix: str) -> None:
        self.store = store
        self.write_prefix = _clean_prefix(write_prefix)

    # --- building blocks ----------------------------------------------------

    def _resolve(self, rel_path: str) -> Path:
        if rel_path.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", rel_path):
            raise ToolPermissionError(
                f"artifact_write: absolute path {rel_path!r} is not allowed"
            )
        if not rel_path or not _SAFE_REL.fullmatch(rel_path) or ".." in rel_path.split("/"):
            raise ToolPermissionError(
                f"artifact_write: unsafe relative path {rel_path!r} (escape attempt)"
            )
        root = self.store.workspace / self.write_prefix
        candidate = (root / rel_path).resolve()
        if root not in candidate.parents and candidate != root:
            raise ToolPermissionError(
                f"artifact_write: path {rel_path!r} escapes write prefix {self.write_prefix!r}"
            )
        return candidate

    def write(
        self, rel_path: str, content: str, kind: str = "output"
    ) -> ToolCallResult:
        """Write content inside the assigned prefix and register the artifact."""
        try:
            target = self._resolve(rel_path)
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            record = self.store.register_artifact(
                name=target.name,
                absolute_path=target,
                kind=kind,
            )
        except (OSError, ArtifactStoreError) as exc:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error=f"write failed: {exc}"
            )
        return ToolCallResult(
            ok=True,
            tool_id=self.tool_id,
            summary=f"wrote {target.relative_to(self.store.workspace)}",
            artifact=record,
        )

    def read(self, rel_path: str, max_chars: int = 8000) -> ToolCallResult:
        try:
            target = self._resolve(rel_path)
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        if not target.is_file():
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error=f"not a file within prefix: {rel_path}"
            )
        text = target.read_text(encoding="utf-8")
        bounded = text[:max_chars] if len(text) > max_chars else text
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"read {len(text)} chars", output=bounded
        )

    def list(self) -> ToolCallResult:
        root = self.store.workspace / self.write_prefix
        if not root.exists():
            return ToolCallResult(ok=True, tool_id=self.tool_id, output="(empty workspace)")
        lines = sorted(str(p.relative_to(self.store.workspace)) for p in root.rglob("*") if p.is_file())
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"{len(lines)} files", output="\n".join(lines)
        )


def _clean_prefix(prefix: str | None) -> str:
    cleaned = (prefix or "").strip().strip("/")
    if not cleaned or not re.fullmatch(r"[A-Za-z0-9_-]+", cleaned):
        raise ValueError(f"invalid write prefix: {prefix!r}")
    return cleaned