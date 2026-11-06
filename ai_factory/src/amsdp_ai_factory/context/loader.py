"""Project-context loading.

The loader resolves the repository root, scans the governed-document
registry, and reads the text of the documents relevant to a task type. It
refuses to read files outside the repository, does not transmit content
anywhere, and reports (never fabricates) missing documents.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from amsdp_ai_factory.context.document_registry import (
    DocumentRecord,
    DocumentRegistry,
    DocumentScanResult,
)
from amsdp_ai_factory.context.selectors import select_document_roles
from amsdp_ai_factory.utils.paths import discover_repo_root, is_within


class LoadedDocument(BaseModel):
    """One governed document plus its loaded (bounded) text."""

    record: DocumentRecord
    text: str = ""

    @property
    def role(self) -> str:
        return self.record.role

    @property
    def path(self) -> Path | None:
        return self.record.resolved_path


class ContextLoader:
    """Loads governed project documents and applies task-type selection."""

    def __init__(
        self,
        repo_root: Path | None = None,
        registry: DocumentRegistry | None = None,
    ) -> None:
        self.repo_root = (repo_root or discover_repo_root()).resolve()
        self.registry = registry or DocumentRegistry(self.repo_root)
        self._scan: DocumentScanResult | None = None

    def scan(self) -> DocumentScanResult:
        """Run and cache a registry scan."""
        if self._scan is None:
            self._scan = self.registry.scan()
        return self._scan

    # --- loading ------------------------------------------------------------

    def load_document(
        self, role: str, max_chars: int | None = None
    ) -> LoadedDocument | None:
        """Load one document by role. Returns None if unknown or missing."""
        result = self.scan()
        record = next((r for r in result.records if r.role == role), None)
        if record is None or not record.exists or record.resolved_path is None:
            return None
        path = record.resolved_path.resolve()
        # Defense in depth: never read outside the repository root.
        if not is_within(self.repo_root, path):
            return None
        text = path.read_text(encoding="utf-8")
        if max_chars is not None and len(text) > max_chars:
            text = text[:max_chars] + f"\n...[truncated to {max_chars} chars]"
        return LoadedDocument(record=record, text=text)

    def load_documents(
        self, roles: list[str] | tuple[str, ...], max_chars: int | None = None
    ) -> list[LoadedDocument]:
        """Load several documents, preserving input order."""
        loaded: list[LoadedDocument] = []
        for role in roles:
            document = self.load_document(role, max_chars=max_chars)
            if document is not None:
                loaded.append(document)
        return loaded

    def load_for_task(
        self, task_type: str | None, max_chars: int | None = None
    ) -> list[LoadedDocument]:
        """Load the minimum context selection for a task type."""
        roles = select_document_roles(task_type)
        return self.load_documents(roles, max_chars=max_chars)

    # --- reporting ----------------------------------------------------------

    def summary(self) -> dict[str, object]:
        """Non-secret summary used for run records and CLI output."""
        result = self.scan()
        return {
            "repo_root": str(self.repo_root),
            "documents_scanned": len(result.records),
            "missing_mandatory": [r.role for r in result.missing_mandatory],
            "missing_references": [r.role for r in result.missing_references],
            "substitution_notes": list(result.substitution_notes),
            "ok": result.ok,
        }