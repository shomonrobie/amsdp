"""Shared typed models and validation primitives.

These models are deliberately small and stable; agent/workflow output
contracts (``contracts.outputs``) are added in a later phase.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity of a validation issue or check result."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """A single finding produced by configuration or environment validation."""

    severity: Severity
    code: str
    message: str
    source: str | None = Field(
        default=None, description="Check or document the issue refers to."
    )


class CheckResult(BaseModel):
    """Outcome of one named check."""

    name: str
    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class DocumentReference(BaseModel):
    """Minimal reference to a governed project document."""

    role: str
    path: Path
    authority_order: int = 100