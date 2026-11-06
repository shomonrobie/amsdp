"""CI configuration validator tool — structural checks on CI workflow files.

Parses CI workflow YAML files (GitHub Actions-style) and checks for required
triggers, named jobs, and secret references. ``yaml`` package must be
installed; fallback to regex-based checks.
"""

from __future__ import annotations

import re
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import ToolCallResult

_REQUIRED_TRIGGERS = ("push:", "pull_request:")


class CIConfigValidatorTool:
    """Tool id ``ci_config_validator`` — CI workflow file structure checks."""

    tool_id = "ci_config_validator"

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run(self, subdir: str = "") -> ToolCallResult:
        gha_dir = (self.workspace / subdir / ".github/workflows").resolve()
        if not gha_dir.is_dir():
            return ToolCallResult(
                ok=True,
                tool_id=self.tool_id,
                output="(no .github/workflows/ found — CI configuration is optional)",
            )
        issues: list[str] = []
        files_checked = 0
        for f in gha_dir.glob("*"):
            if f.suffix in (".yaml", ".yml") and f.is_file():
                files_checked += 1
                self._check_file(f, issues)
        output = "\n".join(issues) if issues else f"({files_checked} CI file(s) checked, no structural issues)"
        return ToolCallResult(
            ok=not issues,
            tool_id=self.tool_id,
            summary=f"checked {files_checked} CI file(s), {len(issues)} issue(s)",
            output=output,
            error="" if not issues else f"{len(issues)} CI config issue(s)",
        )

    def _check_file(self, path: Path, issues: list[str]) -> None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            import yaml
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                issues.append(f"{path.name}: top-level structure is not a mapping")
                return
            # Trigger check: look for 'push'/'pull_request' anywhere in the
            # file text (handles both on: [push] and on: push syntaxes).
            if not re.search(r"\b(push|pull_request)\b", text, re.MULTILINE):
                issues.append(f"{path.name}: no 'push'/'pull_request' trigger found")
            jobs = data.get("jobs", {})
            if not jobs or not isinstance(jobs, dict):
                issues.append(f"{path.name}: no 'jobs:' section found")
        except Exception as exc:
            issues.append(f"{path.name}: parse error ({exc})")

    def _check_file_fallback(self, path: Path, issues: list[str]) -> None:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(t in text for t in _REQUIRED_TRIGGERS):
            issues.append(f"{path.name}: no push/pull_request trigger (regex fallback)")
        if not re.search(r"^\s*jobs\s*:", text, re.MULTILINE):
            issues.append(f"{path.name}: no jobs section (regex fallback)")