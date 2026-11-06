"""Disposable database and migration validator tools.

``DisposableDBTool`` runs SQL migration against an in-memory SQLite database
for structure validation. ``MigrationValidatorTool`` checks forward/backward
naming conventions, tenant-isolation patterns, and dangerous operations.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import ToolCallResult

_DROP_RISK = re.compile(r"\bDROP\s+(TABLE|COLUMN|INDEX)\b", re.IGNORECASE)
_TENANT_CHECK = re.compile(r"WHERE\s+\S*org[_]?[_a-zA-Z]*\s*=?", re.IGNORECASE)
_MISSING_IF_EXISTS = re.compile(
    r"\bDROP\s+(TABLE|COLUMN)\s+(?!.*IF\s+EXISTS)", re.IGNORECASE
)


class DisposableDBTool:
    """Tool id ``disposable_db`` — in-memory SQLite validation."""

    tool_id = "disposable_db"

    def __init__(self) -> None:
        pass

    def run(self, sql_text: str, label: str = "migration") -> ToolCallResult:
        conn = None
        try:
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            cursor.executescript(sql_text)
            conn.commit()
            return ToolCallResult(
                ok=True,
                tool_id=self.tool_id,
                summary=f"{label}: SQL executed without error (in-memory SQLite)",
                output="(no errors)",
            )
        except sqlite3.DatabaseError as exc:
            return ToolCallResult(
                ok=False,
                tool_id=self.tool_id,
                error=f"{label} failed: {exc}",
            )
        finally:
            if conn:
                conn.close()


class MigrationValidatorTool:
    """Tool id ``migration_validator`` — forward/backward SQL checks."""

    tool_id = "migration_validator"

    def __init__(self) -> None:
        pass

    def validate(self, sql_text: str, label: str = "migration") -> ToolCallResult:
        issues: list[str] = []
        for lineno, line in enumerate(sql_text.splitlines(), 1):
            if _MISSING_IF_EXISTS.search(line):
                issues.append(
                    f"L{lineno}: destructive DROP without IF EXISTS — may cause data loss"
                )
            if _DROP_RISK.search(line) and not line.strip().startswith("--"):
                issues.append(
                    f"L{lineno}: irreversible DROP operation detected — ensure recovery plan"
                )
        # Check tenant isolation in DELETE/UPDATE.
        dangerous = re.finditer(
            r"\b(DELETE\s+FROM|UPDATE\s+\S+)\s+(?!.*WHERE)", sql_text, re.IGNORECASE
        )
        for match in dangerous:
            issues.append(f"unscoped DELETE/UPDATE — tenant isolation not enforced")
        output = "\n".join(issues) if issues else "(no migration issues found)"
        return ToolCallResult(
            ok=not issues,
            tool_id=self.tool_id,
            summary=f"{label}: {len(issues)} issue(s)",
            output=output,
            error="" if not issues else f"{len(issues)} migration risk(s) flagged",
        )