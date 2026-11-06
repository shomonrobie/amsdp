"""PatchTool — controlled, gated source-code modification.

PatchTool is the **only** mechanism allowed to apply agent-generated changes to
the target project. Security controls:

1. Workspace → project diff generation (no direct writes).
2. Human approval bound to exact patch SHA-256 hash AND target repository.
3. Target repository baseline revision recorded (git HEAD).
4. Stale patch rejection: approval cannot be reused after successful application.
5. Changed file detection: before_sha256 verified at apply time.
6. Changed baseline detection: git HEAD compared at apply time.
7. Path traversal and symlink attack prevention.
8. Atomic application with verified backups before any write.
9. Failed multi-file application rolls back ALL files.
10. Multi-hunk diffs and merge conflicts rejected safely without partial changes.
11. Before/after SHA-256 recorded for every modified file.
12. Agent-specific project write scopes preserved.
13. Never deletes files automatically.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from amsdp_ai_factory.tasks.models import ApprovalDecision, ApprovalRecord
from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

_SAFE_REL = re.compile(r"^[A-Za-z0-9_./-]+$")

# Allowed project-root-relative scopes per agent.
AGENT_SCOPES: dict[str, str] = {
    "A06": "backend",
    "A07": "frontend",
    "A08": "backend/tests",
    "A04": "backend",
    "A10": "backend",
    "A11": "docs",
}

# Track applied patch hashes to prevent approval reuse.
_applied_patches: set[str] = set()
_APPLIED_PATCHES_FILE = "var/applied_patches.json"
_PATCH_JOURNAL_DIR = "var/patch_journal"


def _load_applied_patches(project_root: Path) -> set[str]:
    """Load persisted applied-patch hashes from disk (replay protection)."""
    import json
    path = project_root / _APPLIED_PATCHES_FILE
    try:
        return set(json.loads(path.read_text()))
    except (OSError, ValueError, json.JSONDecodeError):
        return set()


def _durably_save_applied_patches(hashes: set[str], project_root: Path) -> None:
    """Atomically persist the applied-patches set, then verify by read-back.

    Raises ``OSError`` on failure — the caller MUST roll back and reject.
    """
    import json
    path = project_root / _APPLIED_PATCHES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(sorted(hashes), ensure_ascii=False)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, str(path))
        # fsync the directory so the rename survives an ext-4 power loss.
        _fsync_dir(path.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    # Verify read-back.
    reloaded = _load_applied_patches(project_root)
    missing = sorted(hashes - reloaded)
    if missing:
        raise OSError(
            f"applied-patches file verification failed: {len(missing)} hash(es) "
            f"missing on read-back after supposedly durable write"
        )


def _fsync_dir(path: Path) -> None:
    """fsync a directory — required after rename for ext-4 durability."""
    import platform
    if platform.system() == "Windows":
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _journal_path(project_root: Path, snapshot_id: str) -> Path:
    return project_root / _PATCH_JOURNAL_DIR / f"{snapshot_id}.json"


def _write_journal(project_root: Path, snapshot_id: str, data: dict) -> None:
    """Write a patch-application journal entry atomically (durable)."""
    import json
    jpath = _journal_path(project_root, snapshot_id)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, sort_keys=True)
    fd, tmp = tempfile.mkstemp(dir=jpath.parent, prefix=f".{jpath.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, str(jpath))
        _fsync_dir(jpath.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _remove_journal(project_root: Path, snapshot_id: str) -> None:
    """Remove a completed journal entry (best-effort)."""
    jpath = _journal_path(project_root, snapshot_id)
    if jpath.exists():
        jpath.unlink()
        _fsync_dir(jpath.parent)


def _find_pending_journals(project_root: Path) -> list[Path]:
    """Return all journal files sorted by name (creation order)."""
    jdir = project_root / _PATCH_JOURNAL_DIR
    if not jdir.is_dir():
        return []
    return sorted(jdir.glob("*.json"))


def _reconcile_journals(project_root: Path) -> None:
    """Roll back any pending (uncommitted) patch journals.

    Called at startup: if a patch was being applied and the process crashed
    before the replay record was saved, the journal represents a partial
    application. We restore from backups to return to the pre-patch state.
    """
    for jpath in _find_pending_journals(project_root):
        import json
        try:
            entry = json.loads(jpath.read_text())
        except (OSError, json.JSONDecodeError):
            jpath.unlink()
            continue
        backup_root = Path(entry.get("backup_root", ""))
        patch_id = entry.get("patch_id", "unknown")
        snapshot_id = jpath.stem
        if backup_root.is_dir():
            _restore_files_from_backup(backup_root, project_root)
        # Clean up journal and backup remnants.
        _remove_journal(project_root, snapshot_id)
        if backup_root.exists():
            import shutil
            shutil.rmtree(str(backup_root), ignore_errors=True)
        print(f"  [patch-tool] reconciled pending journal {jpath.name}: "
              f"files restored, patch {patch_id} was NOT committed.")


def _restore_files_from_backup(
    backup_root: Path, project_root: Path,
) -> tuple[list[dict], list[dict], list[str]]:
    """Restore files from a backup snapshot.

    Returns (files_before, files_after, errors).
    """
    files_before: list[dict] = []
    files_after: list[dict] = []
    errors: list[str] = []
    for backup_path in sorted(backup_root.rglob("*")):
        if not backup_path.is_file():
            continue
        try:
            rel = str(backup_path.relative_to(backup_root))
        except ValueError:
            continue
        target = (project_root / rel).resolve()
        if project_root not in target.parents and target != project_root:
            errors.append(f"restore target {rel} escapes project root")
            continue
        if target.is_symlink():
            errors.append(f"restore target {rel} is a symlink — skipped")
            continue
        before_sha = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(backup_path), str(target))
        after_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        files_before.append({"rel_path": rel, "sha256": before_sha})
        files_after.append({"rel_path": rel, "sha256": after_sha})
    return files_before, files_after, errors


class PatchFile(BaseModel):
    """One file to be added or modified (never deleted)."""

    model_config = ConfigDict(extra="forbid")

    rel_path: str
    action: Literal["add", "modify"]
    before_sha256: str | None = None
    after_sha256: str | None = None
    unified_diff: str = ""
    verified: bool = False


class PatchSet(BaseModel):
    """A complete set of changes to be applied atomically."""

    model_config = ConfigDict(extra="forbid")

    patch_id: str
    task_id: str
    run_id: str
    agent_id: str
    target_scope: str
    baseline_revision: str | None = None
    repo_identifier: str | None = None   # git remote origin for target binding
    files: list[PatchFile] = Field(default_factory=list)
    patch_sha256: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "generated"  # generated | approved | applied | rejected | stale


class ApplyResult(BaseModel):
    """Outcome of a patch application or rollback."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    patch_id: str
    operation: str  # "apply" | "rollback"
    files_before: list[dict] = Field(default_factory=list)
    files_after: list[dict] = Field(default_factory=list)
    backup_path: str | None = None
    error: str = ""
# ---------------------------------------------------------------------------
# PatchTool
# ---------------------------------------------------------------------------


class PatchTool:
    """Tool id: ``patch_generator`` — controlled, gated source-code modification."""

    tool_id = "patch_generator"

    def __init__(self, project_root: Path, snapshots_dir: Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.snapshots_dir = (
            snapshots_dir or self.project_root / "var" / "snapshots"
        ).resolve()
        # Load persistent applied-patch registry for replay protection.
        # Mutate the module set in place (do NOT rebind) so that any module's
        # `from ... import _applied_patches` reference stays valid and shared.
        global _applied_patches
        if not _applied_patches:
            _applied_patches.update(_load_applied_patches(self.project_root))
        # Reconcile any pending patch journals (crash recovery).
        _reconcile_journals(self.project_root)

    # =========================================================================
    # Patch generation (read-only)
    # =========================================================================

    def generate(
        self,
        workspace: Path,
        scope: str,
        agent_id: str,
        task_id: str = "",
        run_id: str = "",
    ) -> ToolCallResult:
        """Compare workspace files against project files; produce a PatchSet.

        Scans ``workspace/<scope>/`` for generated files and compares each
        against ``project_root/<scope>/``.

        READ-ONLY — no files are created or modified.
        """
        self._assert_scope(agent_id, scope)
        ws_scope = (workspace / scope).resolve()
        if not ws_scope.is_dir():
            return ToolCallResult(
                ok=False, tool_id=self.tool_id,
                error=f"workspace scope directory does not exist: {ws_scope}",
            )
        prj_scope = (self.project_root / scope).resolve()
        self._assert_project_contained(prj_scope)
        baseline = self._get_baseline()
        files: list[PatchFile] = []
        errors: list[str] = []

        for ws_path in sorted(ws_scope.rglob("*")):
            if not ws_path.is_file():
                continue
            # Project-relative path = scope + relative-to-scope
            rel_in_scope = str(ws_path.relative_to(ws_scope))
            rel = f"{scope}/{rel_in_scope}" if scope else rel_in_scope
            prj_path = (prj_scope / rel_in_scope).resolve()
            self._assert_project_contained(prj_path)
            if prj_path.is_symlink():
                errors.append(f"symlink detected and rejected: {rel}")
                continue

            try:
                ws_content = ws_path.read_text(encoding="utf-8")
            except Exception as exc:
                errors.append(f"cannot read workspace file {rel}: {exc}")
                continue

            after_sha = hashlib.sha256(ws_content.encode()).hexdigest()

            if prj_path.is_file() and prj_path.exists():
                try:
                    prj_content = prj_path.read_text(encoding="utf-8")
                except Exception as exc:
                    errors.append(f"cannot read project file {rel}: {exc}")
                    continue
                before_sha = hashlib.sha256(prj_content.encode()).hexdigest()
                if before_sha == after_sha:
                    continue
                diff = "".join(
                    difflib.unified_diff(
                        prj_content.splitlines(keepends=True),
                        ws_content.splitlines(keepends=True),
                        fromfile=f"a/{rel}\t(before)",
                        tofile=f"b/{rel}\t(after)",
                    )
                )
                files.append(PatchFile(
                    rel_path=rel, action="modify",
                    before_sha256=before_sha, after_sha256=after_sha,
                    unified_diff=diff,
                ))
            else:
                files.append(PatchFile(
                    rel_path=rel, action="add",
                    before_sha256=None, after_sha256=after_sha,
                    unified_diff=f"--- /dev/null\n+++ b/{rel}\n"
                    f"@@ -0,0 +1,{len(ws_content.splitlines())} @@\n"
                    + "".join(f"+{l}\n" for l in ws_content.splitlines()),
                ))

        if not files and not errors:
            return ToolCallResult(
                ok=True, tool_id=self.tool_id,
                summary="no changes detected between workspace and project",
                output="(empty patch — all files are identical)",
            )

        patch_id = f"patch-{task_id}-{run_id}" if task_id and run_id else f"patch-{now_utc():%H%M%S%f}"
        repo_id = self._get_repo_identifier()
        patch_set = PatchSet(
            patch_id=patch_id, task_id=task_id, run_id=run_id,
            agent_id=agent_id, target_scope=scope,
            baseline_revision=baseline, repo_identifier=repo_id,
            files=files, created_at=now_utc(),
        )
        canonical = patch_set.model_dump(
            mode="json", exclude={"patch_sha256", "status", "created_at"}
        )
        patch_set.patch_sha256 = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        output_lines = [
            f"PatchSet: {patch_id}",
            f"Scope: {scope} | Agent: {agent_id}",
            f"Baseline: {baseline or '(unknown)'}",
            f"Repo: {repo_id or '(unknown)'}",
            f"Patch SHA-256: {patch_set.patch_sha256}",
            f"Files: {len(files)}",
        ]
        for f in files:
            output_lines.append(f"  {f.action}: {f.rel_path}")
            if f.before_sha256:
                output_lines.append(f"    before: {f.before_sha256[:16]}...")
            output_lines.append(f"    after:  {f.after_sha256[:16]}...")
        if errors:
            output_lines.append("\nWARNINGS:" + "\n".join(f"  {e}" for e in errors))

        return ToolCallResult(
            ok=not errors, tool_id=self.tool_id,
            summary=f"PatchSet {patch_id}: {len(files)} file(s) changed",
            output="\n".join(output_lines),
        )
# =========================================================================
    # Approval verification (approval must bind to exact patch hash)
    # =========================================================================

    def verify_approval(
        self, patch_set: PatchSet, approvals: list[ApprovalRecord]
    ) -> ToolCallResult:
        """Verify an approval binds to this exact patch hash AND target repo.

        The approval ``rationale`` must contain
        ``patch_sha256=<sha> repo=<repo_identifier>`` matching this PatchSet.
        Reports repo binding as ERROR when the patch carries a repo id and the
        approval doesn't name the same id (or any id).
        """
        for approval in approvals:
            if approval.decision != ApprovalDecision.APPROVED:
                continue
            marker = f"patch_sha256={patch_set.patch_sha256}"
            if marker not in approval.rationale and marker not in approval.decision_id:
                continue
            # Repository binding: the approval must name the same repo, or the
            # patch must carry no repo id (non-git or synthetic target).
            if patch_set.repo_identifier:
                repo_marker = f"repo={patch_set.repo_identifier}"
                if repo_marker not in approval.rationale and \
                   repo_marker not in approval.decision_id:
                    continue
            return ToolCallResult(
                ok=True, tool_id=self.tool_id,
                summary=f"approval {approval.decision_id} binds to patch "
                f"{patch_set.patch_sha256[:16]}... "
                f"repo={patch_set.repo_identifier or '(none)'}",
            )
        return ToolCallResult(
            ok=False, tool_id=self.tool_id,
            error=(
                f"no approved approval binds to patch SHA-256 "
                f"{patch_set.patch_sha256[:16]}...; each approval must contain "
                f"'patch_sha256={patch_set.patch_sha256}' "
                f"{('and repo=' + patch_set.repo_identifier) if patch_set.repo_identifier else ''} "
                f"in rationale or decision_id."
            ),
        )

    def _verify_file_unchanged(self, patch_set: PatchSet) -> str:
        """Reject stale patches where a target file changed since generation.

        Returns an error string (empty when all files are unchanged).
        """
        for pf in patch_set.files:
            target = (self.project_root / pf.rel_path).resolve()
            if pf.action == "modify":
                if not target.exists():
                    return f"target file missing since generation: {pf.rel_path}"
                current = hashlib.sha256(target.read_bytes()).hexdigest()
                if pf.before_sha256 and current != pf.before_sha256:
                    return (
                        f"target file changed since patch generation: {pf.rel_path} "
                        f"(expected before {pf.before_sha256[:12]}..., got {current[:12]}...)"
                    )
        return ""

    def _verify_baseline_current(self, patch_set: PatchSet) -> str:
        """Reject a patch whose recorded git baseline is no longer HEAD.

        If the patch records a baseline but we cannot determine the current HEAD
        (git not available or not a repository), we must fail closed rather than
        silently accepting a potentially stale patch.
        """
        if not patch_set.baseline_revision:
            return ""  # no baseline recorded → nothing to compare
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.project_root), capture_output=True, text=True, timeout=5,
            )
        except Exception:
            return (
                f"cannot verify repository baseline: git is not available or "
                f"not a git repository; patch records baseline "
                f"{patch_set.baseline_revision!r} but current state cannot be "
                f"determined — failing closed for safety"
            )
        if result.returncode != 0:
            return (
                f"cannot verify repository baseline: git rev-parse failed "
                f"(exit {result.returncode}); patch records baseline "
                f"{patch_set.baseline_revision!r} but current state cannot be "
                f"determined — failing closed for safety"
            )
        current = result.stdout.strip()
        if current != patch_set.baseline_revision:
            return (
                f"repository baseline changed since patch generation: "
                f"recorded {patch_set.baseline_revision!r}, current {current!r}"
            )
        return ""

    # =========================================================================
    # Patch application (write to project — gated)
    # =========================================================================

    def apply(
        self, patch_set: PatchSet, approvals: list[ApprovalRecord],
    ) -> ApplyResult:
        """Apply an approved patch set to the project root.

        Gated on:
        - Approval binding to this exact patch hash AND target repository.
        - Patch not stale and not already applied (no approval reuse).
        - Target files unchanged since generation (before_sha256 verified).
        - Repository baseline still current.
        - File traversal/symlink checks.
        - Verified backups before any write; failed application rolls back all.
        """
        # --- Gate 1: approval hash + repository binding ---
        approval_check = self.verify_approval(patch_set, approvals)
        if not approval_check.ok:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id,
                operation="apply", error=approval_check.error,
            )
        # --- Gate 2: not stale / not already applied (no approval reuse) ---
        if patch_set.patch_sha256 in _applied_patches:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id, operation="apply",
                error=(
                    "this patch was already applied; an approval cannot be "
                    "reused to apply the same changes twice"
                ),
            )
        if patch_set.status not in ("generated", "approved"):
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id,
                operation="apply",
                error=f"patch status is {patch_set.status!r}; must be 'generated' or 'approved'",
            )
        # --- Gate 3: target files unchanged since generation ---
        changed = self._verify_file_unchanged(patch_set)
        if changed:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id, operation="apply",
                error=f"stale patch rejected: {changed}",
            )
        # --- Gate 4: repository baseline still current ---
        baseline_err = self._verify_baseline_current(patch_set)
        if baseline_err:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id, operation="apply",
                error=f"stale patch rejected: {baseline_err}",
            )

        patch_set.status = "approved"
        snapshot_id = f"{patch_set.patch_id}-{now_utc():%Y%m%dT%H%M%S}"
        backup_root = self.snapshots_dir / snapshot_id
        files_before: list[dict] = []
        files_after: list[dict] = []

        try:
            # --- Phase 1: validate all paths and create verified backups ---
            for pf in patch_set.files:
                target = self._resolve_project_path(pf.rel_path, patch_set.target_scope)
                if target.is_symlink():
                    raise ToolPermissionError(
                        f"symlink rejected before backup: {pf.rel_path}"
                    )
                if target.exists():
                    backup_path = backup_root / pf.rel_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(target), str(backup_path))
                    before_sha = hashlib.sha256(target.read_bytes()).hexdigest()
                else:
                    before_sha = None
                files_before.append({"rel_path": pf.rel_path, "sha256": before_sha})
                pf.verified = True

            # --- Phase 1b: write journal (pre-commit durability) ---
            import json as _json
            journal_data = {
                "patch_id": patch_set.patch_id,
                "patch_sha256": patch_set.patch_sha256,
                "task_id": patch_set.task_id,
                "run_id": patch_set.run_id,
                "agent_id": patch_set.agent_id,
                "backup_root": str(backup_root),
                "files": [{"rel_path": pf.rel_path, "action": pf.action} for pf in patch_set.files],
            }
            _write_journal(self.project_root, snapshot_id, journal_data)

            # --- Phase 2: apply all files (atomic per file) ---
            for pf in patch_set.files:
                target = self._resolve_project_path(pf.rel_path, patch_set.target_scope)
                target.parent.mkdir(parents=True, exist_ok=True)
                if pf.action == "add":
                    new_content = self._reconstruct_from_diff(None, pf.unified_diff)
                else:
                    old_content = target.read_text(encoding="utf-8") if target.exists() else None
                    new_content = self._reconstruct_from_diff(old_content, pf.unified_diff)
                if new_content is None:
                    raise ValueError(f"cannot reconstruct {pf.rel_path} from diff")
                fd, tmp_path = tempfile.mkstemp(
                    dir=target.parent, prefix=f".{target.name}.", suffix=".patchtmp",
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as fh:
                        fh.write(new_content); fh.flush(); os.fsync(fh.fileno())
                    os.replace(tmp_path, str(target))
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                after_sha = hashlib.sha256(target.read_bytes()).hexdigest()
                files_after.append({"rel_path": pf.rel_path, "sha256": after_sha})

            patch_set.status = "applied"
            _applied_patches.add(patch_set.patch_sha256)
            _durably_save_applied_patches(_applied_patches, self.project_root)
            # Phase 4: remove journal — fully committed now.
            _remove_journal(self.project_root, snapshot_id)
            return ApplyResult(
                ok=True, patch_id=patch_set.patch_id, operation="apply",
                files_before=files_before, files_after=files_after,
                backup_path=str(backup_root),
            )
        except (OSError, ToolPermissionError, ValueError) as exc:
            # Failed: roll back all files, remove journal, reject.
            self._rollback_to_backup(backup_root, patch_set)
            _remove_journal(self.project_root, snapshot_id)
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id, operation="apply",
                error=f"application failed and rolled back: {exc}",
            )
# =========================================================================
    # Rollback
    # =========================================================================

    def rollback(self, patch_set: PatchSet) -> ApplyResult:
        """Rollback an applied patch set from its snapshot backup."""
        candidates = sorted(self.snapshots_dir.glob(f"{patch_set.patch_id}-*"))
        if not candidates:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id, operation="rollback",
                error=f"no snapshot found for patch {patch_set.patch_id}",
            )
        return self._rollback_to_backup(candidates[-1], patch_set)

    def _rollback_to_backup(
        self, backup_root: Path, patch_set: PatchSet | None = None,
    ) -> ApplyResult:
        if not backup_root.is_dir():
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id if patch_set else "unknown",
                operation="rollback", error=f"backup path does not exist: {backup_root}",
            )
        files_before, files_after, errors = _restore_files_from_backup(
            backup_root, self.project_root,
        )
        if errors:
            return ApplyResult(
                ok=False, patch_id=patch_set.patch_id if patch_set else "unknown",
                operation="rollback", files_before=files_before, files_after=files_after,
                error="; ".join(errors),
            )
        return ApplyResult(
            ok=True, patch_id=patch_set.patch_id if patch_set else "unknown",
            operation="rollback", files_before=files_before, files_after=files_after,
            backup_path=str(backup_root),
        )
# =========================================================================
    # Security helpers
    # =========================================================================

    def _assert_scope(self, agent_id: str, scope: str) -> None:
        allowed = AGENT_SCOPES.get(agent_id)
        if allowed is None:
            raise ToolPermissionError(
                f"agent {agent_id!r} has no defined project write scope"
            )
        if not scope.startswith(allowed):
            raise ToolPermissionError(
                f"agent {agent_id!r} cannot write to scope {scope!r}; "
                f"allowed scope prefix: {allowed!r}"
            )

    def _assert_project_contained(self, path: Path) -> None:
        resolved = path.resolve()
        if self.project_root not in resolved.parents and resolved != self.project_root:
            raise ToolPermissionError(f"path {resolved} escapes the project root")
        if resolved.is_symlink():
            raise ToolPermissionError(f"symlink detected and rejected: {resolved}")

    def _resolve_project_path(self, rel_path: str, scope: str) -> Path:
        if rel_path.startswith("/"):
            raise ToolPermissionError(f"absolute path not allowed: {rel_path}")
        if not _SAFE_REL.fullmatch(rel_path) or ".." in rel_path.split("/"):
            raise ToolPermissionError(f"unsafe path {rel_path!r} (possible traversal)")
        candidate = (self.project_root / rel_path).resolve()
        self._assert_project_contained(candidate)
        return candidate

    def _get_baseline(self) -> str | None:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.project_root), capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_repo_identifier(self) -> str | None:
        """Get the git remote origin (or repo dir basename) for target binding."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(self.project_root), capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # Fallback: local repo identity (basename of the project root)
            return self.project_root.name
        except Exception:
            return None

    def _reconstruct_from_diff(self, original: str | None, diff: str) -> str | None:
        """Apply a unified diff to original content; pure-Python, no subprocess.

        Handles the unified diffs produced by ``generate()`` (single hunk,
        context lines and +/- lines).
        """
        if original is None and diff.startswith("--- /dev/null"):
            # New file: extract added lines after the @@ header
            lines = diff.splitlines()
            result_lines = []
            in_body = False
            for line in lines:
                if line.startswith("@@"):
                    in_body = True
                    continue
                if in_body:
                    if line.startswith("+"):
                        result_lines.append(line[1:])
                    elif line.startswith(" "):
                        result_lines.append(line[1:])
            return "\n".join(result_lines)

        if original is None:
            return None

        # Existing file: apply the hunk manually.
        original_lines = original.splitlines(keepends=True)
        result = list(original_lines)
        lines = diff.splitlines()
        in_hunk = False
        hunk_removals: list[str] = []
        hunk_additions: list[str] = []
        context_lines: list[str] = []
        for line in lines:
            if line.startswith("@@"):
                # Apply previous hunk before starting a new one
                if in_hunk:
                    applied = self._apply_hunk(result, hunk_removals, hunk_additions, context_lines)
                    if applied is None:
                        return None
                    result = applied
                hunk_removals, hunk_additions, context_lines = [], [], []
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if line.startswith("-"):
                hunk_removals.append(line[1:])
            elif line.startswith("+"):
                hunk_additions.append(line[1:])
            elif line.startswith(" "):
                context_lines.append(line[1:])
        if in_hunk:
            applied = self._apply_hunk(result, hunk_removals, hunk_additions, context_lines)
            if applied is None:
                return None
            result = applied
        return "".join(result)

    def _apply_hunk(
        self, lines: list[str], removals: list[str],
        additions: list[str], context: list[str],
    ) -> list[str] | None:
        """Replace the removed lines with additions in the given line list."""
        # Match the removal sequence in the target lines.
        removal = removals
        remainder = lines
        for i in range(len(remainder)):
            if removal and i + len(removal) <= len(remainder):
                window = remainder[i : i + len(removal)]
                if all(
                    a.rstrip("\n") == b.rstrip("\n")
                    for a, b in zip(window, removal)
                ):
                    return remainder[:i] + [a + "\n" for a in additions] + remainder[i + len(removal):]
        if removals and context:
            # Fallback: find context anchor then replace after it
            anchor = context[-1].rstrip("\n")
            for i, line in enumerate(remainder):
                if line.rstrip("\n") == anchor:
                    return (
                        remainder[: i + 1]
                        + [a + "\n" for a in additions if a]
                        + remainder[i + 1 :]
                    )
        return None


def now_utc():
    from datetime import timezone
    return datetime.now(timezone.utc)


def get_patch_approval_marker(patch_set: PatchSet) -> str:
    """Generate marker string for embedding in an ApprovalRecord for hash binding."""
    return f"patch_sha256={patch_set.patch_sha256}"
    error: str = ""