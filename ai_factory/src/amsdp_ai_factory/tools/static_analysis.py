"""Static analysis tool: scan workspace files for security-sensitive patterns.

Does NOT install or run third-party linters. Uses regex patterns to flag
common dangerous constructs; results are advisory and never treated as a
certification of safety.
"""

from __future__ import annotations

import re
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import ToolCallResult

_PATTERNS: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
    (re.compile(r"\beval\s*\("), "high", "eval", "Use of eval() can execute arbitrary code"),
    (re.compile(r"\bexec\s*\("), "high", "exec", "Use of exec() can execute arbitrary code"),
    (re.compile(r"os\.system\s*\("), "high", "os_system", "Shell command execution"),
    (re.compile(r"subprocess\.(call|run|Popen)\s*\("), "medium", "subprocess", "Subprocess execution — ensure command injection is prevented"),
    (re.compile(r"password\s*=\s*['\"][^'\"\n]+['\"]"), "high", "hardcoded_password", "Hardcoded credential detected"),
    (re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"), "critical", "private_key", "Embedded private key block in source"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{12,}\b"), "critical", "api_key_in_source", "API key pattern in source code"),
)


class StaticAnalysisTool:
    """Tool id ``static_analysis`` — local, pattern-based static analysis."""

    tool_id = "static_analysis"

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run(self, subdir: str = "", extensions: tuple[str, ...] = (".py", ".js", ".ts", ".yaml", ".yml")) -> ToolCallResult:
        root = (self.workspace / subdir).resolve() if subdir else self.workspace
        if root not in self.workspace.parents and root != self.workspace:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error="subdir escapes workspace")
        findings: list[str] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in extensions:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pattern, severity, finding_id, description in _PATTERNS:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        findings.append(
                            f"[{severity.upper()}] {finding_id}: {path.relative_to(self.workspace)}:{lineno} — {description}"
                        )
        output = "\n".join(findings) if findings else "(no issues found)"
        return ToolCallResult(
            ok=True, tool_id=self.tool_id,
            summary=f"scanned {sum(1 for _ in root.rglob('*') if _.is_file() and _.suffix in extensions)} files, {len(findings)} finding(s)",
            output=output,
            error="" if not findings else f"{len(findings)} finding(s) reported for review",
        )