"""Secret scan tool: regex-based credential detection in workspace files.

Patterns match API keys, private keys, tokens, and credentials. Results are
advisory and never treated as a guarantee that no secrets exist (scanning is
a heuristic, not an audit).
"""

from __future__ import annotations

import re
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import ToolCallResult
from amsdp_ai_factory.utils.logging import _SECRET_PATTERNS as _KNOWN_PATTERNS


class SecretScanTool:
    """Tool id ``secret_scan`` — pattern-based secret discovery in workspace."""

    tool_id = "secret_scan"

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run(self, subdir: str = "", extensions: tuple[str, ...] = (".py", ".js", ".ts", ".yaml", ".yml", ".env", ".cfg", ".conf", ".json", ".toml", ".ini")) -> ToolCallResult:
        root = (self.workspace / subdir).resolve() if subdir else self.workspace
        if root not in self.workspace.parents and root != self.workspace:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error="subdir escapes workspace")
        hits: list[str] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in extensions:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pattern, _ in _KNOWN_PATTERNS:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        hits.append(f"{path.relative_to(self.workspace)}:{lineno}")
                        break  # one hit per pattern per file
        output = "\n".join(hits) if hits else "(no secret patterns detected)"
        return ToolCallResult(
            ok=True,
            tool_id=self.tool_id,
            summary=f"scanned files, {len(hits)} hit(s)",
            output=output,
            error="" if not hits else f"{len(hits)} potential secret pattern(s) found",
        )