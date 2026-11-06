"""Run recorder: durable, redacted execution records.

One JSON file per run in ``<store_dir>/<run_id>.json``, written atomically.
Before any persistence the complete payload is recursively redacted so
accidentally captured secret-shaped values never reach disk.
"""

from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from amsdp_ai_factory.contracts.common import CheckResult, DocumentReference
from amsdp_ai_factory.runs.models import (
    ApprovalRecord,
    RunRecord,
    RunStatus,
    RunSummary,
    StageRecord,
    StageStatus,
    ToolOperationRecord,
)
from amsdp_ai_factory.tasks.models import now_utc
from amsdp_ai_factory.utils.logging import redact

_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{4,64}$")


class RunRecorderError(ValueError):
    """Raised for invalid run ids or missing run records."""


def _redact_tree(value):
    """Recursively redact every string in a JSON-serializable structure."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [_redact_tree(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _redact_tree(v) for k, v in value.items()}
    return value


class RunRecorder:
    """Persists run records and their stage/check/approval details."""

    def __init__(self, store_dir):
        self.store_dir = Path(store_dir)

    # --- creation -----------------------------------------------------------

    def new_run(
        self,
        *,
        task_id: str,
        workflow_id=None,
        model_config_id=None,
        provider=None,
        environment: str = "development",
        source_documents=None,
        start_commit=None,
        at=None,
        agents=None,
    ):
        self.store_dir.mkdir(parents=True, exist_ok=True)
        run = RunRecord(
            run_id=self._next_run_id(),
            task_id=task_id,
            workflow_id=workflow_id,
            model_config_id=model_config_id,
            provider=provider,
            environment=environment,
            source_documents=source_documents or [],
            start_commit=start_commit,
            status=RunStatus.RUNNING,
            agents=list(agents) if agents else [],
        )
        run.touch_start(at=at)
        self._persist(run)
        return run

    # --- reads -------------------------------------------------------------

    def get(self, run_id: str):
        self._validate_run_id(run_id)
        path = self._path(run_id)
        if not path.exists():
            return None
        try:
            return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RunRecorderError(
                f"run record {run_id} is unreadable/corrupt: {exc}"
            ) from exc

    def list(self, *, task_id=None, limit=None):
        if not self.store_dir.exists():
            return []
        summaries = []
        for path in sorted(self.store_dir.glob("*.json")):
            if path.name.startswith("."):
                continue
            try:
                run = RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if task_id is not None and run.task_id != task_id:
                continue
            summaries.append(
                RunSummary(
                    run_id=run.run_id,
                    task_id=run.task_id,
                    workflow_id=run.workflow_id,
                    status=run.status,
                    started_at=run.started_at,
                    ended_at=run.ended_at,
                )
            )
        summaries.sort(key=lambda s: s.started_at or datetime.min, reverse=True)
        if limit is not None:
            summaries = summaries[: max(0, limit)]
        return summaries

    # --- mutations ----------------------------------------------------------

    def save(self, run: RunRecord) -> RunRecord:
        self._validate_run_id(run.run_id)
        current = self.get(run.run_id)
        if current is None:
            raise RunRecorderError(f"unknown run {run.run_id!r}; use new_run() first")
        self._persist(run)
        return run

    def start_stage(self, run_id: str, *, name: str, stage_id=None, agents=None):
        run = self._require(run_id)
        stamp = now_utc()
        stage = StageRecord(
            stage_id=stage_id or f"stage-{len(run.stages) + 1}",
            name=name,
            status=StageStatus.RUNNING,
            started_at=stamp,
            agents=list(agents) if agents else [],
        )
        run.stages.append(stage)
        self._persist(run)
        return stage

    def update_stage(
        self,
        run_id: str,
        stage_id: str,
        *,
        status=None,
        ended_at=None,
        error: str = "",
        retry_count=None,
        approval_id=None,
    ):
        run = self._require(run_id)
        stage = run.get_stage(stage_id)
        if stage is None:
            raise RunRecorderError(f"no stage {stage_id!r} in run {run_id!r}")
        if status is not None:
            stage.status = status
        if ended_at is not None:
            stage.ended_at = ended_at
        if error:
            stage.error = error
        if retry_count is not None:
            stage.retry_count = retry_count
        if approval_id is not None:
            stage.approval_id = approval_id
        self._persist(run)
        return stage

    def add_check(self, run_id: str, check: CheckResult) -> RunRecord:
        run = self._require(run_id)
        run.checks.append(check)
        self._persist(run)
        return run

    def add_tool_operation(self, run_id: str, operation: ToolOperationRecord) -> RunRecord:
        run = self._require(run_id)
        if not operation.op_id:
            operation.op_id = f"op-{len(run.tool_operations) + 1}"
        run.tool_operations.append(operation)
        self._persist(run)
        return run

    def add_approval(self, run_id: str, approval: ApprovalRecord) -> RunRecord:
        run = self._require(run_id)
        run.approvals.append(approval)
        self._persist(run)
        return run

    def add_artifact(self, run_id: str, path: str) -> RunRecord:
        run = self._require(run_id)
        run.artifacts.append(path)
        self._persist(run)
        return run

    def add_error(self, run_id: str, error: str) -> RunRecord:
        run = self._require(run_id)
        run.errors.append(error)
        self._persist(run)
        return run

    def finish(
        self,
        run_id: str,
        *,
        status: RunStatus,
        error: str | None = None,
        at=None,
    ) -> RunRecord:
        if status not in (
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.ABORTED,
            RunStatus.AWAITING_APPROVAL,
        ):
            raise RunRecorderError(
                f"finish() accepts a terminal/paused status, got {status.value!r}"
            )
        run = self._require(run_id)
        run.status = status
        run.ended_at = at or now_utc()
        if error:
            run.errors.append(error)
        self._persist(run)
        return run

    # --- internals ----------------------------------------------------------

    def _require(self, run_id: str) -> RunRecord:
        run = self.get(run_id)
        if run is None:
            raise RunRecorderError(f"unknown run {run_id!r}")
        return run

    def _validate_run_id(self, run_id: str) -> None:
        if not re.fullmatch(_RUN_ID_PATTERN, run_id):
            raise RunRecorderError(f"unsafe run id {run_id!r}")

    def _path(self, run_id: str) -> Path:
        return self.store_dir / f"{run_id}.json"

    def _next_run_id(self) -> str:
        stamp = now_utc().strftime("%Y%m%dT%H%M%S")
        suffix = 1
        while (self.store_dir / f"RUN-{stamp}-{suffix:03d}.json").exists():
            suffix += 1
        return f"RUN-{stamp}-{suffix:03d}"

    def _persist(self, run: RunRecord) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        raw = run.model_dump(mode="json")
        redacted = _redact_tree(raw)
        payload = RunRecord.model_validate(redacted).model_dump_json(indent=2)
        target = self._path(run.run_id)
        fd, tmp_name = tempfile.mkstemp(
            dir=self.store_dir, prefix=f".{run.run_id}.", suffix=".tmp"
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
