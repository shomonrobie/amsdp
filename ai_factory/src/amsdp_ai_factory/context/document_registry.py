"""Governed-document registry.

Loads and records the project's governing documents: path, category
(mandatory/reference), authority order, detected version/status/document id,
and a SHA-256 content hash. Every requirement is reported; missing documents
are never fabricated.

Expected-but-absent paths from the implementation prompt (e.g.
``docs/product/product-vision.md``, ``docs/product/scope.md``) are recorded
as substitution notes against the documents that authoritatively resolve
them, so operators see exactly how each missing path was handled.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from amsdp_ai_factory.utils.paths import is_within


class DocumentCategory(str, Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    REFERENCE = "reference"


@dataclass(frozen=True)
class DocumentSpec:
    role: str
    rel_path: str
    category: DocumentCategory = DocumentCategory.REFERENCE
    authority_order: int = 100
    substitutes_for: tuple[str, ...] = ()


class DocumentRecord(BaseModel):
    """Metadata for one governed document at scan time."""

    role: str
    rel_path: str
    category: DocumentCategory
    authority_order: int
    substitutes_for: list[str] = Field(default_factory=list)
    exists: bool = False
    resolved_path: Path | None = None
    document_id: str | None = None
    version: str | None = None
    status: str | None = None
    title: str | None = None
    sha256: str | None = None
    last_checked: str | None = None


class DocumentScanResult(BaseModel):
    """Result of one registry scan."""

    records: list[DocumentRecord] = Field(default_factory=list)
    missing_mandatory: list[DocumentRecord] = Field(default_factory=list)
    missing_references: list[DocumentRecord] = Field(default_factory=list)
    substitution_notes: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_mandatory


# --- Default governed document set -----------------------------------------
# Authority order follows the source-of-truth hierarchies in AI Agent
# Specification V1.0 2.1 and AI Development Workflow V1.0 2.1. Lower numbers
# bind earlier (higher authority).

DEFAULT_DOCUMENT_SET: tuple[DocumentSpec, ...] = (
    DocumentSpec(
        role="business_rules",
        rel_path="docs/product/AMSDP_Business_Rules_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=1,
    ),
    DocumentSpec(
        role="mvp_scope",
        rel_path="docs/product/AMSDP_MVP_SCOPE_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=2,
        substitutes_for=("docs/product/scope.md",),
    ),
    DocumentSpec(
        role="system_architecture",
        rel_path="docs/architecture/AMSDP_System_Architecture_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=3,
    ),
    DocumentSpec(
        role="factory_architecture",
        rel_path="docs/architecture/AMSDP_AI_Factory_Architecture_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=4,
    ),
    DocumentSpec(
        role="agent_specification",
        rel_path="docs/architecture/AMSDP_AI_Agent_Specification_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=5,
    ),
    DocumentSpec(
        role="development_workflow",
        rel_path="docs/architecture/AMSDP_AI_Development_Workflow_V1.0.md",
        category=DocumentCategory.MANDATORY,
        authority_order=6,
    ),
    DocumentSpec(
        role="implementation_prompt",
        rel_path="docs/architecture/AMSDP_AI_Factory_Implementation_Prompt_V1.0.md",
        category=DocumentCategory.REFERENCE,
        authority_order=7,
    ),
    DocumentSpec(
        role="feature_list",
        rel_path="docs/AMSDP_Master_Feature_List_V2.0_Draft.md",
        category=DocumentCategory.REFERENCE,
        authority_order=8,
    ),
    DocumentSpec(
        role="product_vision",
        rel_path="README.md",
        category=DocumentCategory.REFERENCE,
        authority_order=9,
        substitutes_for=("docs/product/product-vision.md",),
    ),
    DocumentSpec(
        role="product_vision_note",
        rel_path="docs/AMSDP — E-Health Hackathon Concept Note & Application Summary.md",
        category=DocumentCategory.REFERENCE,
        authority_order=10,
        substitutes_for=("docs/product/product-vision.md",),
    ),
)
# --- Header metadata extraction ----------------------------------------------

_HEADER_PATTERNS: dict[str, re.Pattern[str]] = {
    "document_id": re.compile(r"\*\*Document ID:\*\*\s*(.+)$"),
    "version": re.compile(r"\*\*Version:\*\*\s*(.+)$"),
    # Matches both "**Status:**" and "**Document status:**" forms (the
    # Master Feature List uses a lowercase 's' in "Document status").
    "status": re.compile(r"\*\*(?:Document\s+)?[Ss]tatus:\*\*\s*(.+)$"),
    "title": re.compile(r"^#\s+(.{1,140})$"),
}

_HEADER_KEYS = ("document_id", "version", "status")


def detect_document_metadata(path: Path, max_lines: int = 80) -> dict[str, str | None]:
    """Extract Document ID / Version / Status / title from a doc's header."""
    meta: dict[str, str | None] = {key: None for key in (*_HEADER_KEYS, "title")}
    try:
        with open(path, encoding="utf-8") as fh:
            for _ in range(max_lines):
                line = fh.readline()
                if not line:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                if meta["title"] is None:
                    title_match = _HEADER_PATTERNS["title"].match(stripped)
                    if title_match:
                        meta["title"] = title_match.group(1).strip()
                for key in _HEADER_KEYS:
                    if meta[key] is not None:
                        continue
                    match = _HEADER_PATTERNS[key].search(stripped)
                    if match:
                        meta[key] = match.group(1).strip().rstrip("\\").strip()
                if all(value is not None for value in meta.values()):
                    break
    except OSError as exc:
        meta["status"] = f"unreadable: {exc}"
    return meta


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """Content hash used to detect document drift between runs."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DocumentRegistry:
    """Scan-oriented registry that reports every governed document's state."""

    def __init__(
        self,
        repo_root: Path,
        documents: list[DocumentSpec] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self._specs: tuple[DocumentSpec, ...] = tuple(
            documents or DEFAULT_DOCUMENT_SET
        )

    @property
    def specs(self) -> tuple[DocumentSpec, ...]:
        return self._specs

    def get(self, role: str) -> DocumentSpec | None:
        for spec in self._specs:
            if spec.role == role:
                return spec
        return None

    def scan(self) -> DocumentScanResult:
        """Scan configured documents and report their state."""
        records: list[DocumentRecord] = []
        missing_mandatory: list[DocumentRecord] = []
        missing_references: list[DocumentRecord] = []

        for spec in self._specs:
            record = DocumentRecord(
                role=spec.role,
                rel_path=spec.rel_path,
                category=spec.category,
                authority_order=spec.authority_order,
                substitutes_for=list(spec.substitutes_for),
            )
            candidate = (self.repo_root / spec.rel_path).resolve()
            if is_within(self.repo_root, candidate) and candidate.is_file():
                record.exists = True
                record.resolved_path = candidate
                record.sha256 = sha256_file(candidate)
                metadata = detect_document_metadata(candidate)
                record.document_id = metadata["document_id"]
                record.version = metadata["version"]
                record.status = metadata["status"]
                record.title = metadata["title"]
            record.last_checked = _now_iso()
            records.append(record)
            if record.exists:
                continue
            if record.category == DocumentCategory.MANDATORY:
                missing_mandatory.append(record)
            else:
                missing_references.append(record)

        substitution_notes = self._substitution_notes(records)
        return DocumentScanResult(
            records=records,
            missing_mandatory=missing_mandatory,
            missing_references=missing_references,
            substitution_notes=substitution_notes,
        )

    def _substitution_notes(self, records: list[DocumentRecord]) -> list[str]:
        notes: list[str] = []
        for record in records:
            for expected in record.substitutes_for:
                state = "PRESENT" if record.exists else "MISSING"
                notes.append(
                    f"Expected path {expected!r} was not found; resolved by document "
                    f"role {record.role!r} ({record.rel_path!r}, {state})."
                )
        return notes

    def report_lines(self, result: DocumentScanResult) -> list[str]:
        """Human-readable scan text (used by the CLI/validation)."""
        lines: list[str] = []
        for record in sorted(result.records, key=lambda r: (r.authority_order, r.role)):
            if record.exists:
                existence = "FOUND"
            elif record.category == DocumentCategory.MANDATORY:
                existence = "MISSING"
            else:
                existence = "absent (reference)"
            status = record.status or "n/a"
            version = record.version or "n/a"
            lines.append(
                f"[{existence}] {record.role} ({record.authority_order:>2}) "
                f"{record.rel_path} | status={status!r} version={version!r}"
            )
        for note in result.substitution_notes:
            lines.append(f"[note] {note}")
        return lines