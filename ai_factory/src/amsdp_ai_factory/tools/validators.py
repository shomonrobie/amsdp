"""Validator tools enabled for the executable workflows.

``architecture_validator`` (WF-01/WF-05) structurally checks
``ArchitectureProposal`` artifacts; ``doc_link_validator`` (WF-10) checks
that Markdown links inside the task workspace resolve. Both are read-only
with respect to the repository.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from amsdp_ai_factory.contracts.outputs import ArchitectureProposal
from amsdp_ai_factory.tools.tool_registry import ToolCallResult
from amsdp_ai_factory.utils.paths import is_within

_MD_LINK = re.compile(r"\[[^\]]*\]\((\.?/?[^)#\s]+)(?:#[^)]*)?\)")


class ArchitectureValidatorTool:
    """Tool id ``architecture_validator`` — structural proposal checks."""

    tool_id = "architecture_validator"

    def __init__(self) -> None:
        pass

    def validate(self, proposal: ArchitectureProposal) -> ToolCallResult:
        issues: list[str] = []
        if proposal.decision_required and not proposal.affected_services:
            issues.append("decision_required is set but affected_services is empty")
        if proposal.adr_required and len(proposal.alternatives) < 2:
            issues.append("adr_required is set but fewer than 2 alternatives exist")
        if not proposal.summary:
            issues.append("summary is empty")
        return ToolCallResult(
            ok=not issues,
            tool_id=self.tool_id,
            summary="architecture validator report",
            output="\n".join(issues) if issues else "(no structural issues)",
            error="" if not issues else "; ".join(issues),
        )

    def validate_file(self, path: Path) -> ToolCallResult:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            proposal = ArchitectureProposal.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error=f"unreadable proposal: {exc}"
            )
        return self.validate(proposal)


class DocLinkValidatorTool:
    """Tool id ``doc_link_validator`` — workspace Markdown link checks."""

    tool_id = "doc_link_validator"

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run(self, start: str = ".") -> ToolCallResult:
        root = (self.workspace / start).resolve()
        if root not in self.workspace.parents and root != self.workspace:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error="start path escapes workspace"
            )
        broken: list[str] = []
        checked = 0
        for path in root.rglob("*.md"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in _MD_LINK.finditer(text):
                target = match.group(1)
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                resolved_path = (path.parent / target).resolve()
                if not is_within(self.workspace, resolved_path):
                    broken.append(
                        f"{path.relative_to(self.workspace)}: {target} escapes workspace"
                    )
                    continue
                checked += 1
                if not resolved_path.exists():
                    broken.append(
                        f"{path.relative_to(self.workspace)}: {target} does not exist"
                    )
        output = "\n".join(broken) if broken else f"(all {checked} internal links resolve)"
        return ToolCallResult(
            ok=not broken,
            tool_id=self.tool_id,
            summary=f"{checked} internal links checked",
            output=output,
            error="" if not broken else f"{len(broken)} broken link(s)",
        )