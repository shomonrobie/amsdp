"""CLI smoke tests using the typer CliRunner (synthetic, local-only)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from amsdp_ai_factory.cli import app

from tests.helpers import make_pseudo_repo

runner = CliRunner()


class CliSmokeTests(unittest.TestCase):
    def test_version(self):
        result = runner.invoke(app, ["version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("AILI", result.output)

    def test_agents(self):
        result = runner.invoke(app, ["agents"])
        self.assertEqual(result.exit_code, 0)
        for agent_id in (f"A{i:02d}" for i in range(1, 12)):
            self.assertIn(agent_id, result.output)

    def test_workflows(self):
        result = runner.invoke(app, ["workflows"])
        self.assertEqual(result.exit_code, 0)
        for workflow_id in (f"WF-{i:02d}" for i in range(1, 11)):
            self.assertIn(workflow_id, result.output)

    def test_workflow_detail_and_statuses(self):
        result = runner.invoke(app, ["workflows", "WF-01"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("executable", result.output)

    def test_task_workflow_approve_resume_flow(self):
        # Run the full flow inside a disposable pseudo-repository.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            make_pseudo_repo(root)
            (root / "var").mkdir()
            env = {"AMSDP_FACTORY_REPO_ROOT": str(root)}
            with mock.patch.dict(os.environ, env, clear=False):
                created = runner.invoke(
                    app,
                    ["task-new", "--title", "CLI test task", "--workflow-id", "WF-01"],
                )
                self.assertEqual(created.exit_code, 0, created.output)
                task_id = created.output.strip().split()[2]  # "created task <id> status=..."

                ran = runner.invoke(
                    app,
                    ["run-workflow", task_id, "WF-01", "--mode", "stub"],
                )
                self.assertEqual(ran.exit_code, 0, ran.output)
                self.assertIn("awaiting_approval", ran.output)

                approved = runner.invoke(
                    app,
                    ["approve", task_id, "approved", "--actor", "project_owner"],
                )
                self.assertEqual(approved.exit_code, 0, approved.output)
                self.assertIn("ready_for_implementation", approved.output)

                resumed = runner.invoke(app, ["resume", task_id, "--mode", "stub"])
                self.assertEqual(resumed.exit_code, 0, resumed.output)
                self.assertIn("succeeded", resumed.output)


if __name__ == "__main__":
    unittest.main()