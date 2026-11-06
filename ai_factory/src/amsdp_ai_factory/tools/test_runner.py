"""Bounded test-runner tool.

Executes ONLY allowlisted command templates. Arguments are passed as an argv
list (never through a shell) and all referenced paths are confined to the
task workspace. Timeouts and output truncation bound side effects.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
)
from amsdp_ai_factory.utils.paths import is_within

_DEFAULT_TIMEOUT = 30.0
_OUTPUT_LIMIT = 4000


class TestRunnerTool:
    """Tool id ``run_tests`` — allowlisted local test execution."""

    tool_id = "run_tests"
    _UNITTEST_PREFIX = ("python", "-m", "unittest", "discover", "-s", "tests")
    _COMPILEALL_PREFIX = ("python", "-m", "compileall", "-q")
    _PYCOMPILE_PREFIX = ("python", "-m", "py_compile")
    _PYTEST_PREFIX = ("python", "-m", "pytest")

    def __init__(self, workspace: Path, timeout: float = _DEFAULT_TIMEOUT, output_limit: int = _OUTPUT_LIMIT) -> None:
        self.workspace = Path(workspace).resolve()
        self.timeout = timeout
        self.output_limit = output_limit

    # --- allowlist ------------------------------------------------------------

    def _validate(self, argv: list[str]) -> list[str]:
        if not argv or not all(isinstance(part, str) for part in argv):
            raise ToolPermissionError("run_tests: invalid argv")
        parts = tuple(argv)
        # unittest discover in workspace tests/
        if parts[: len(self._UNITTEST_PREFIX)] == self._UNITTEST_PREFIX:
            tail = parts[len(self._UNITTEST_PREFIX):]
            if tail in ((), ("-v",)):
                return list(parts)
        # compileall and py_compile with path confinement
        for prefix, path_index in (
            (self._COMPILEALL_PREFIX, 4),
            (self._PYCOMPILE_PREFIX, 3),
        ):
            if parts[: len(prefix)] == prefix and len(parts) == len(prefix) + 1:
                path = self._confined_path(parts[path_index])
                return list(prefix) + [str(path)]
        # pytest with path confinement
        if parts[: len(self._PYTEST_PREFIX)] == self._PYTEST_PREFIX:
            tail = parts[len(self._PYTEST_PREFIX):]
            if len(tail) == 1:
                path = self._confined_path(tail[0])
                return list(self._PYTEST_PREFIX) + [str(path)]
        raise ToolPermissionError(
            f"run_tests: command {list(parts)!r} is not in the allowlist"
        )

    def _confined_path(self, rel: str) -> Path:
        candidate = (self.workspace / rel).resolve()
        if not is_within(self.workspace, candidate):
            raise ToolPermissionError(
                f"run_tests: path {rel!r} escapes the task workspace"
            )
        return candidate

    # --- execution ------------------------------------------------------------

    def run(self, argv: list[str]) -> ToolCallResult:
        try:
            validated = self._validate(argv)
        except ToolPermissionError as exc:
            return ToolCallResult(ok=False, tool_id=self.tool_id, error=str(exc))
        command = " ".join(validated)
        try:
            proc = subprocess.run(
                validated,
                cwd=str(self.workspace),
                timeout=self.timeout,
                capture_output=True,
                text=True,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return ToolCallResult(
                ok=False,
                tool_id=self.tool_id,
                command=command,
                error=f"timed out after {self.timeout:.0f}s",
            )
        except FileNotFoundError as exc:
            return ToolCallResult(
                ok=False,
                tool_id=self.tool_id,
                command=command,
                error=f"executable not found: {exc}",
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
            error="" if proc.returncode == 0 else f"exit code {proc.returncode}",
        )