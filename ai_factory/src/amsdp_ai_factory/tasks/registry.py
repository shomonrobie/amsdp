"""Task registry with JSON-file persistence.

Storage is deliberately simple and inspectable: one JSON file per task in
``<store_dir>/<task_id>.json``. Writes are atomic (temp file + ``os.replace``)
so a crash cannot leave a partially written record. The registry never
deletes records — retirement/cleanup is a separate, human-approved process.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from amsdp_ai_factory.tasks.models import (
    TASK_ID_PATTERN,
    Task,
    TaskSummary,
    now_utc,
)

_TASK_SUFFIX = re.compile(r"^([A-Za-z]+-)?(\d+)$")


class TaskRegistryError(ValueError):
    """Raised for registry-level errors (duplicate/missing/unsafe ids)."""


class TaskRegistry:
    """Persistent task store used by the AI Factory orchestrator.

    ``store_dir`` may be the settings-defined ``var/tasks`` directory; tests
    use disposable directories so nothing touches real data.
    """

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = Path(store_dir)

    # --- creation ---------------------------------------------------------

    def create(self, task: Task, at: datetime | None = None) -> Task:
        """Assign a stable task id if missing and persist the task."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        if not task.task_id:
            task.task_id = self._next_task_id()
        self._validate_id(task.task_id)
        if self._path(task.task_id).exists():
            raise TaskRegistryError(
                f"task id already exists in registry: {task.task_id}"
            )
        task.touch(at=at)
        self._write(task)
        return task

    def get(self, task_id: str) -> Task | None:
        """Load one task; returns None when absent or malformed-safe."""
        self._validate_id(task_id)
        path = self._path(task_id)
        if not path.exists():
            return None
        try:
            return Task.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # fail closed on corrupt records
            raise TaskRegistryError(
                f"task record {task_id} is unreadable/corrupt: {exc}"
            ) from exc

    def save(self, task: Task, at: datetime | None = None) -> Task:
        """Persist an updated task. Refuses to invent a task on save."""
        if not task.task_id:
            raise TaskRegistryError("cannot save a task without a task_id")
        self._validate_id(task.task_id)
        if not self._path(task.task_id).exists():
            raise TaskRegistryError(
                f"cannot save unknown task {task.task_id!r}; use create() first"
            )
        task.updated_at = at or now_utc()
        self._write(task)
        return task

    # --- listing ----------------------------------------------------------

    def list(self, *, status: str | None = None, limit: int | None = None) -> list[TaskSummary]:
        """List task summaries, newest first. ``status`` filters by state name/value."""
        if not self.store_dir.exists():
            return []
        summaries: list[TaskSummary] = []
        for path in sorted(self.store_dir.glob("*.json")):
            if path.name.startswith("."):
                continue
            try:
                task = Task.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue  # skip corrupt file in listings; get() reports it clearly
            if status is not None:
                wanted = status.lower().replace(" ", "_")
                if task.status.value != wanted and task.status.name.lower() != wanted:
                    continue
            summaries.append(task.summary())
        summaries.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        if limit is not None:
            summaries = summaries[: max(0, limit)]
        return summaries

    def count(self) -> int:
        if not self.store_dir.exists():
            return 0
        return sum(
            1 for path in self.store_dir.glob("*.json") if not path.name.startswith(".")
        )

    # --- internals ----------------------------------------------------------

    def _path(self, task_id: str) -> Path:
        return self.store_dir / f"{task_id}.json"

    def _validate_id(self, task_id: str) -> None:
        if not task_id or not re.fullmatch(TASK_ID_PATTERN, task_id):
            raise TaskRegistryError(
                f"unsafe task id {task_id!r}; must match {TASK_ID_PATTERN!r}"
            )

    def _next_task_id(self) -> str:
        largest = 0
        if self.store_dir.exists():
            for path in self.store_dir.glob("*.json"):
                match = _TASK_SUFFIX.match(path.stem)
                if match:
                    largest = max(largest, int(match.group(2)))
        return f"AMSDP-{largest + 1:06d}"

    def _write(self, task: Task) -> None:
        payload = task.model_dump_json(indent=2)
        target = self._path(task.task_id)
        # Atomic replace: write to a sibling temp file, then os.replace.
        fd, tmp_name = tempfile.mkstemp(
            dir=self.store_dir, prefix=f".{task.task_id}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)