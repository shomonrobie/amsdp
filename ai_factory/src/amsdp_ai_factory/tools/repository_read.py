"""Read-only repository inspection tool.

Constrained to the repository root: listing, reading, and regex search.
Escapes raise ``ToolPermissionError``; output is bounded.
"""

from __future__ import annotations

import re
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
)
from amsdp_ai_factory.utils.paths import is_within

_DEFAULT_MAX_CHARS = 8000
_DEFAULT_MAX_ITEMS = 200


class RepositoryReadTool:
    """Tool id ``repo_read`` — never writes, never leaves the repo."""

    tool_id = "repo_read"

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root).resolve()

    def _resolve(self, rel_path: str) -> Path:
        candidate = (self.repo_root / rel_path).resolve()
        if not is_within(self.repo_root, candidate):
            raise ToolPermissionError(
                f"repo_read: path {rel_path!r} escapes the repository root"
            )
        return candidate

    def list_paths(self, rel_dir: str = "", max_items: int = _DEFAULT_MAX_ITEMS) -> ToolCallResult:
        try:
            base = self._resolve(rel_dir or ".")
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        items = sorted(
            str(p.relative_to(self.repo_root))
            for p in base.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )
        truncated = items[: max_items]
        output = "\n".join(truncated) if truncated else "(no files)"
        if len(items) > max_items:
            output += f"\n... ({len(items) - max_items} more)"
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"listed {len(truncated)} files", output=output
        )

    def read_text(self, rel_path: str, max_chars: int = _DEFAULT_MAX_CHARS) -> ToolCallResult:
        try:
            target = self._resolve(rel_path)
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        if not target.is_file():
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error=f"not a file: {rel_path}"
            )
        text = target.read_text(encoding="utf-8")
        bounded = text[:max_chars] if len(text) > max_chars else text
        if len(text) > max_chars:
            bounded += f"\n... (truncated from {len(text)} chars)"
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"read {len(text)} chars", output=bounded
        )

    def search(self, pattern: str, rel_dir: str = "", max_results: int = 50) -> ToolCallResult:
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=f"bad pattern: {exc}")
        try:
            base = self._resolve(rel_dir or ".")
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        hits: list[str] = []
        for path in base.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if compiled.search(line):
                        hits.append(f"{path.relative_to(self.repo_root)}:{number}")
                        break
            except (OSError, UnicodeDecodeError):
                continue
            if len(hits) >= max_results:
                break
        output = "\n".join(hits) if hits else "(no matches)"
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"{len(hits)} matches", output=output
        )