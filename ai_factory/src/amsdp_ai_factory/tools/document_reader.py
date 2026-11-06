"""Governed-document reader tool.

Reads approved governing documents through the context loader. Read-only,
bounded, and never fabricates missing documents.
"""

from __future__ import annotations

from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.tools.tool_registry import ToolCallResult

_DEFAULT_MAX_CHARS = 12000


class DocumentReaderTool:
    """Tool id ``doc_reader`` — governed-document access for all agents."""

    tool_id = "doc_reader"

    def __init__(self, loader: ContextLoader) -> None:
        self.loader = loader

    def list_roles(self) -> ToolCallResult:
        result = self.loader.scan()
        lines = [
            f"{record.role} -> {record.rel_path} ({'present' if record.exists else 'MISSING'})"
            for record in result.records
        ]
        output = "\n".join(lines) if lines else "(no documents configured)"
        return ToolCallResult(
            ok=True, tool_id=self.tool_id, summary=f"{len(result.records)} roles", output=output
        )

    def read(self, role: str, max_chars: int = _DEFAULT_MAX_CHARS) -> ToolCallResult:
        document = self.loader.load_document(role, max_chars=max_chars)
        if document is None:
            return ToolCallResult(
                ok=False,
                tool_id=self.tool_id,
                error=f"document role {role!r} is unavailable (missing or unknown)",
            )
        return ToolCallResult(
            ok=True,
            tool_id=self.tool_id,
            summary=f"{role}: {len(document.text)} chars",
            output=document.text,
        )