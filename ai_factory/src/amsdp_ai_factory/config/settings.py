"""Factory settings.

Configuration is environment-driven with the ``AMSDP_FACTORY_`` prefix
(e.g. ``AMSDP_FACTORY_ENVIRONMENT=test``). A local ``ai_factory/.env`` file
is read when present. Secrets are NOT part of settings: provider credentials
are read from the process environment at live-run time and are never stored
or logged here.

Runtime directories (``task_store_dir``, ``run_store_dir``,
``workspace_root``) are resolved relative to the repository root. The
directories are created lazily by the stores that use them, not eagerly at
import time.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from amsdp_ai_factory.utils.paths import discover_repo_root

VALID_ENVIRONMENTS = ("development", "test", "production")
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class FactorySettings(BaseSettings):
    """Validated Factory configuration, read from ``AMSDP_FACTORY_*`` env."""

    model_config = SettingsConfigDict(
        env_prefix="AMSDP_FACTORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = Field(default="development", description="development | test | production")
    log_level: str = Field(default="INFO")
    repo_root: Path | None = Field(
        default=None,
        description="Explicit repository root; auto-discovered when unset.",
    )
    task_store_dir: str = Field(default="var/tasks", description="Task registry persistence directory.")
    run_store_dir: str = Field(default="runs", description="Run-record persistence directory.")
    workspace_root: str = Field(default="var/workspaces", description="Task artifact workspaces root.")
    default_max_retries: int = Field(default=2, ge=0, le=10, description="Bound on automatic stage retries.")
    model_provider: str | None = Field(default=None, description="Provider id for live CrewAI runs (non-secret).")
    model_id: str | None = Field(default=None, description="Model id for live CrewAI runs (non-secret).")

    # --- Resolution helpers -------------------------------------------------

    def effective_repo_root(self) -> Path:
        """Resolve the repository root from config or auto-discovery."""
        if self.repo_root is not None:
            root = self.repo_root.expanduser().resolve()
            if not root.is_dir():
                raise ValueError(f"repo_root is not a directory: {self.repo_root}")
            return root
        return discover_repo_root()

    def resolve_path(self, rel: str | Path) -> Path:
        """Resolve a repository-relative path against the repo root."""
        root = self.effective_repo_root()
        candidate = (root / rel).resolve()
        return candidate

    def task_store_path(self) -> Path:
        return self.resolve_path(self.task_store_dir)

    def run_store_path(self) -> Path:
        return self.resolve_path(self.run_store_dir)

    def workspace_path(self) -> Path:
        return self.resolve_path(self.workspace_root)

    # --- Basic field validation ---------------------------------------------

    def validate(self) -> list["ValidationIssue"]:
        """Field-level validation. Returns issues; empty means valid."""
        from amsdp_ai_factory.contracts.common import Severity, ValidationIssue

        issues: list[ValidationIssue] = []
        if self.environment not in VALID_ENVIRONMENTS:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="invalid_environment",
                    message=(
                        f"AMSDP_FACTORY_ENVIRONMENT={self.environment!r} is not one "
                        f"of {VALID_ENVIRONMENTS!r}."
                    ),
                    source="config.settings",
                )
            )
        if self.log_level.upper() not in VALID_LOG_LEVELS:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="invalid_log_level",
                    message=(
                        f"AMSDP_FACTORY_LOG_LEVEL={self.log_level!r} is not one of "
                        f"{VALID_LOG_LEVELS!r}."
                    ),
                    source="config.settings",
                )
            )
        if bool(self.model_provider) != bool(self.model_id):
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="partial_model_config",
                    message=(
                        "model_provider and model_id must be set together (both "
                        "empty is valid: stub/test mode)."
                    ),
                    source="config.settings",
                )
            )
        try:
            root = self.effective_repo_root()
        except ValueError as exc:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="repo_root_unresolvable",
                    message=str(exc),
                    source="config.settings",
                )
            )
            return issues
        if not (root / ".git").exists():
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="no_git_marker",
                    message=f"Resolved repository root lacks a .git marker: {root}",
                    source="config.settings",
                )
            )
        return issues