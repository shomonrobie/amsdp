"""Read-only Git inspection tool.

Executes only a whitelist of read commands (status, diff, log, branch,
rev-parse, show). Every write/merge/push operation is rejected by design —
there is no path through this tool that mutates the repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
)

_DEFAULT_TIMEOUT = 15.0
_OUTPUT_LIMIT = 4000


class GitReadTool:
    """Tool id ``git_read`` — status/diff/log/branch inspection only."""

    tool_id = "git_read"

    _READ_COMMANDS: dict[str, tuple[str, ...]] = {
        "status": ("status", "--short", "--branch"),
        "diff_stat": ("diff", "--stat"),
        "diff_names": ("diff", "--name-only"),
        "log": ("log", "-n", "<n>", "--oneline"),
        "branches": ("branch", "--list"),
        "head": ("rev-parse", "HEAD"),
        "show_head": ("show", "--stat", "--oneline", "HEAD"),
    }

    def __init__(self, repo_root: Path, timeout: float = _DEFAULT_TIMEOUT, output_limit: int = _OUTPUT_LIMIT) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.timeout = timeout
        self.output_limit = output_limit

    def _argv(self, name: str, n: int | None = None) -> list[str]:
        if name not in self._READ_COMMANDS:
            raise ToolPermissionError(
                f"git_read: {name!r} is not an allowed read command "
                f"(allowlist: {', '.join(sorted(self._READ_COMMANDS))})"
            )
        template = self._READ_COMMANDS[name]
        if "<n>" in template:
            if n is None or not (1 <= int(n) <= 100):
                raise ToolPermissionError("git_read: log requires n in 1..100")
            argv = [part.replace("<n>", str(int(n))) for part in template]
        else:
            argv = list(template)
        return argv

    def run(self, name: str, n: int | None = None) -> ToolCallResult:
        try:
            argv = self._argv(name, n)
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        command = "git " + " ".join(argv)
        try:
            proc = subprocess.run(
                ["git", *argv],
                cwd=str(self.repo_root),
                timeout=self.timeout,
                capture_output=True,
                text=True,
                shell=False,
            )
        except FileNotFoundError:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, command=command, error="git executable not found"
            )
        except subprocess.TimeoutExpired:
            return ToolCallResult(
                ok=False,
                tool_id=self.tool_id,
                command=command,
                error=f"timed out after {self.timeout:.0f}s",
            )
        combined = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        bounded = combined[: self.output_limit]
        if len(combined) > self.output_limit:
            bounded += "\n... (output truncated)"
        return ToolCallResult(
            ok=proc.returncode == 0,
            tool_id=self.tool_id,
            command=command,
            exit_code=proc.returncode,
            output=bounded,
            error="" if proc.returncode == 0 else f"git returned {proc.returncode}",
        )