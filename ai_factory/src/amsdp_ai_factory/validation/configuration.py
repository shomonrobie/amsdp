"""Environment and configuration validation.

``validate_environment()`` combines interpreter, settings, CrewAI library,
and governed-document checks into a single report. It never prints or stores
secrets, never calls a model provider, and treats unresolvable state as a
failure (fail-closed).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.contracts.common import Severity, ValidationIssue
from amsdp_ai_factory.context.document_registry import DocumentRegistry

_MIN_PYTHON = (3, 13)
MIN_PYTHON_DISPLAY = "3.13"
MIN_CREWAI_VERSION = (1, 15, 35)


class ValidationReport(BaseModel):
    """Aggregated result of environment validation."""

    issues: list[ValidationIssue] = Field(default_factory=list)
    python_version: str = ""
    crewai_version: str | None = None
    repo_root: str = ""

    @property
    def ok(self) -> bool:
        return not any(issue.severity == Severity.ERROR for issue in self.issues)

    def as_text(self) -> str:
        lines = [
            f"Python: {self.python_version}",
            f"CrewAI: {self.crewai_version or 'not importable'}",
            f"Repo root: {self.repo_root or 'unresolved'}",
        ]
        for issue in self.issues:
            source = f" ({issue.source})" if issue.source else ""
            lines.append(
                f"[{issue.severity.value.upper()}] {issue.code}: {issue.message}{source}"
            )
        lines.append(
            f"Result: {'OK' if self.ok else 'FAILED'} ({len(self.issues)} issue(s), "
            f"{sum(1 for i in self.issues if i.severity == Severity.ERROR)} error(s))"
        )
        return "\n".join(lines)


def _crewai_version() -> str | None:
    try:
        module = importlib.import_module("crewai")
        return str(getattr(module, "__version__", "unknown"))
    except Exception:
        return None


def validate_environment(settings: FactorySettings | None = None) -> ValidationReport:
    """Validate the Factory environment and report all issues found."""
    settings = settings or FactorySettings()
    issues: list[ValidationIssue] = []

    # Interpreter ---------------------------------------------------------
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info < _MIN_PYTHON:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="python_too_old",
                message=(
                    f"Python {python_version} detected; {MIN_PYTHON_DISPLAY}+ required."
                ),
                source="validation.configuration",
            )
        )
    else:
        issues.append(
            ValidationIssue(
                severity=Severity.INFO,
                code="python_ok",
                message=f"Python {python_version} >= {MIN_PYTHON_DISPLAY}.",
                source="validation.configuration",
            )
        )

    # Settings --------------------------------------------------------------
    issues.extend(settings.validate())

    try:
        repo_root = settings.effective_repo_root()
    except ValueError as exc:
        repo_root = ""
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="repo_root_unresolvable",
                message=str(exc),
                source="validation.configuration",
            )
        )
    else:
        issues.append(
            ValidationIssue(
                severity=Severity.INFO,
                code="repo_root_resolved",
                message=str(repo_root),
                source="validation.configuration",
            )
        )

    # CrewAI library --------------------------------------------------------
    crewai_version = _crewai_version()
    if crewai_version is None:
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="crewai_missing",
                message=(
                    "crewai is not importable. Context loading, task records, and "
                    "tests work without it; live agent runs (CrewAI kickoff) will "
                    "be unavailable until the supported environment is active."
                ),
                source="validation.configuration",
            )
        )
    else:
        parts = [int(p) for p in crewai_version.split(".")[:3] if p.isdigit()]
        ok = len(parts) == 3 and tuple(parts) >= MIN_CREWAI_VERSION
        issues.append(
            ValidationIssue(
                severity=Severity.INFO if ok else Severity.WARNING,
                code="crewai_version",
                message=(
                    f"crewai {crewai_version} detected"
                    + (
                        ""
                        if ok
                        else f" (verified minimum is {'.'.join(map(str, MIN_CREWAI_VERSION))})"
                    )
                ),
                source="validation.configuration",
            )
        )
# Model provider (non-secret checks only) -------------------------------
    if settings.model_provider and settings.model_id:
        issues.append(
            ValidationIssue(
                severity=Severity.INFO,
                code="model_configured",
                message=(
                    f"model_provider={settings.model_provider!r} "
                    f"model_id={settings.model_id!r}."
                ),
                source="validation.configuration",
            )
        )
    else:
        issues.append(
            ValidationIssue(
                severity=Severity.INFO,
                code="model_not_configured",
                message=(
                    "No model provider configured; live CrewAI runs are disabled. "
                    "Context loading, validation, task records, and the stub test "
                    "suite are unaffected."
                ),
                source="validation.configuration",
            )
        )

    # Governing documents ----------------------------------------------------
    if repo_root:
        registry = DocumentRegistry(Path(repo_root))
        scan = registry.scan()
        for record in scan.missing_mandatory:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="mandatory_document_missing",
                    message=(
                        f"Required governing document missing: {record.role!r} at "
                        f"{record.rel_path!r}. The affected workflow cannot run; "
                        "the missing specification is NOT fabricated."
                    ),
                    source=f"docs:{record.role}",
                )
            )
        for record in scan.records:
            if not record.exists:
                continue
            issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    code="document_found",
                    message=(
                        f"{record.role!r}: {record.rel_path} "
                        f"(status={record.status!r} version={record.version!r})."
                    ),
                    source="validation.configuration",
                )
            )
        for note in scan.substitution_notes:
            issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    code="document_substitution",
                    message=note,
                    source="context.document_registry",
                )
            )

    return ValidationReport(
        issues=issues,
        python_version=python_version,
        crewai_version=crewai_version,
        repo_root=str(repo_root),
    )