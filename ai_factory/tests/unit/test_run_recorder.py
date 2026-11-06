"""Run recorder tests: records, persistence, and secret redaction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from amsdp_ai_factory.contracts.common import CheckResult
from amsdp_ai_factory.runs.models import (
    RunStatus,
    StageStatus,
    ToolOperationRecord,
)
from amsdp_ai_factory.runs.recorder import RunRecorder, RunRecorderError
from amsdp_ai_factory.tasks.models import (
    ApprovalDecision,
    ApprovalRecord,
    now_utc,
)

from tests.helpers import TempRepoCase


class RunRecorderTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.store_dir = self.repo_root / "runs"
        self.recorder = RunRecorder(self.store_dir)

    def _new_run(self, **kwargs):
        kwargs.setdefault("task_id", "AMSDP-000001")
        kwargs.setdefault("workflow_id", "WF-02")
        kwargs.setdefault("environment", "test")
        return self.recorder.new_run(**kwargs)

    def test_new_run_records_metadata(self):
        run = self._new_run(model_config_id="stub", provider="mock")
        self.assertTrue(run.run_id.startswith("RUN-"))
        self.assertEqual(run.status, RunStatus.RUNNING)
        self.assertEqual(run.environment, "test")
        self.assertIsNotNone(run.started_at)

    def test_stage_lifecycle(self):
        run = self._new_run()
        stage = self.recorder.start_stage(run.run_id, name="analysis")
        self.assertEqual(stage.status, StageStatus.RUNNING)
        self.recorder.update_stage(
            run.run_id, stage.stage_id, status=StageStatus.SUCCEEDED, ended_at=now_utc()
        )
        loaded = self.recorder.get(run.run_id)
        self.assertEqual(loaded.stages[0].status, StageStatus.SUCCEEDED)

    def test_finish_sets_terminal_status(self):
        run = self._new_run()
        self.recorder.finish(run.run_id, status=RunStatus.SUCCEEDED)
        loaded = self.recorder.get(run.run_id)
        self.assertEqual(loaded.status, RunStatus.SUCCEEDED)
        self.assertIsNotNone(loaded.ended_at)

    def test_finish_rejects_invalid_status(self):
        run = self._new_run()
        with self.assertRaises(RunRecorderError):
            self.recorder.finish(run.run_id, status=RunStatus.RUNNING)

    def test_persistence_survives_restart(self):
        run = self._new_run()
        stage = self.recorder.start_stage(run.run_id, name="qa")
        self.recorder.add_check(
            run.run_id,
            CheckResult(name="output_contract", ok=True),
        )
        self.recorder.add_approval(
            run.run_id,
            ApprovalRecord(
                decision_id="a1",
                decision=ApprovalDecision.APPROVED,
                actor="owner",
            ),
        )
        self.recorder.finish(run.run_id, status=RunStatus.SUCCEEDED)

        fresh = RunRecorder(self.store_dir)
        reloaded = fresh.get(run.run_id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.status, RunStatus.SUCCEEDED)
        self.assertEqual(len(reloaded.stages), 1)
        self.assertEqual(len(reloaded.checks), 1)
        self.assertEqual(len(reloaded.approvals), 1)

    def test_list_filters_by_task(self):
        run_a = self._new_run(task_id="AMSDP-000001")
        run_b = self._new_run(task_id="AMSDP-000002")
        listing = self.recorder.list(task_id="AMSDP-000001")
        self.assertEqual([r.run_id for r in listing], [run_a.run_id])
        self.assertNotIn(run_b.run_id, [r.run_id for r in listing])

    def test_unsafe_run_id_rejected(self):
        with self.assertRaises(RunRecorderError):
            self.recorder.get("../../etc/passwd")

    def test_secret_redacted_on_disk(self):
        secret_value = "sekrit-token-value-abc123"
        run = self._new_run()
        self.recorder.add_error(run.run_id, f"connection failed token={secret_value}")
        raw = json.loads((self.store_dir / f"{run.run_id}.json").read_text(encoding="utf-8"))
        dumped = json.dumps(raw)
        self.assertNotIn(secret_value, dumped)
        self.assertIn("[REDACTED]", dumped)


if __name__ == "__main__":
    unittest.main()