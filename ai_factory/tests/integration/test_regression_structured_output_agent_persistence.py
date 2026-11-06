"""Regression tests: structured-output hardening, focus_scope, agent persistence.

D1-D6 style: validates _extract_validated_output rejects prose/malformed JSON
and correctly extracts from DSML-markup and fenced blocks, that request carries
focus_scope for assessments, and that run/stage agents are persisted.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = (_HERE / ".." / ".." / "src").resolve()
os.environ.setdefault("PYTHONPATH", str(_SRC))

import sys

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS, ArtifactKind
from amsdp_ai_factory.execution.live import _extract_validated_output
from amsdp_ai_factory.tasks.models import Task


def _valid_payload() -> dict:
    return {
        "artifact_type": "requirement_analysis",
        "task_id": "T-1",
        "stage_id": "s1",
        "agent_id": "A01",
        "title": "Regression Analysis",
        "summary": "Validated.",
        "user_stories": ["As a user, I can login."],
        "acceptance_criteria": ["Login works."],
    }
class ExtractorTests(unittest.TestCase):
    """Guarantees _extract_validated_output enforces the contract strictly."""

    model = ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS]

    def test_d1_valid_json_string_passes(self):
        out = _extract_validated_output(json.dumps(_valid_payload()), self.model)
        self.assertIsNotNone(out)
        self.assertEqual(out.title, "Regression Analysis")

    def test_d2_valid_dict_passes(self):
        out = _extract_validated_output(_valid_payload(), self.model)
        self.assertIsNotNone(out)

    def test_d3_prose_rejected(self):
        with self.assertRaises(ValueError):
            _extract_validated_output(
                "I will analyse the codebase for assessment gaps.", self.model
            )

    def test_d4_malformed_json_rejected(self):
        with self.assertRaises(ValueError):
            _extract_validated_output(
                '{"artifact_type": "requirement_analysis", "title":', self.model
            )

    def test_d5_empty_payload_rejected(self):
        with self.assertRaises(ValueError):
            _extract_validated_output("", self.model)

    def test_d5b_none_raw_rejected(self):
        with self.assertRaises(ValueError):
            _extract_validated_output(None, self.model)
class DSMLAndFocusTests(unittest.TestCase):
    """DSML markup extraction, fenced JSON, assessment focus."""

    model = ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS]

    def test_dsml_markup_with_valid_json_extracted(self):
        raw = (
            "|text| Opening repository ...\n"
            "|json| " + json.dumps(_valid_payload()) + "\n"
            "|json_next_call| tool-xyz\n"
        )
        out = _extract_validated_output(raw, self.model)
        self.assertIsNotNone(out)
        self.assertEqual(out.title, "Regression Analysis")

    def test_fenced_json_extracted(self):
        raw = "Here:\n```json\n" + json.dumps(_valid_payload()) + "\n```\nDone."
        out = _extract_validated_output(raw, self.model)
        self.assertIsNotNone(out)

    def test_prose_with_malformed_json_rejected(self):
        with self.assertRaises(ValueError):
            _extract_validated_output(
                "Heading\n|json| {broken}\nsurrounding text", self.model
            )

    def test_partial_json_rejected(self):
        partial = {"artifact_type": "requirement_analysis"}
        with self.assertRaises(ValueError):
            _extract_validated_output(json.dumps(partial), self.model)

    def test_assessment_task_carries_focus_scope(self):
        from amsdp_ai_factory.workflows.engine import WorkflowEngine

        task = Task(task_id="T-FOCUS", task_type="gap_assessment")
        scope = WorkflowEngine._assessment_focus(None, task)
        self.assertIn("application implementation", scope)
        self.assertIn("backend/", scope)
        self.assertIn("AILI", scope)

    def test_non_assessment_returns_empty(self):
        from amsdp_ai_factory.workflows.engine import WorkflowEngine

        task = Task(task_id="T-FOCUS2", task_type="implementation")
        scope = WorkflowEngine._assessment_focus(None, task)
        self.assertEqual(scope, "")


class AgentPersistenceTests(unittest.TestCase):
    """Validates agents are recorded on runs and stages."""

    def test_new_run_accepts_agents(self):
        from amsdp_ai_factory.runs.recorder import RunRecorder
        from amsdp_ai_factory.runs.models import AgentParticipation

        tmp = Path(tempfile.mkdtemp())
        try:
            rec = RunRecorder(store_dir=tmp / "runs")
            ap = AgentParticipation(agent_id="A01", role="analyst")
            run = rec.new_run(task_id="T-1", workflow_id="WF-1", agents=[ap])
            self.assertEqual(len(run.agents), 1)
            self.assertEqual(run.agents[0].agent_id, "A01")
        finally:
            import shutil; shutil.rmtree(tmp, ignore_errors=True)

    def test_new_run_agents_default_empty(self):
        from amsdp_ai_factory.runs.recorder import RunRecorder

        tmp = Path(tempfile.mkdtemp())
        try:
            rec = RunRecorder(store_dir=tmp / "runs")
            run = rec.new_run(task_id="T-1", workflow_id="WF-1")
            self.assertEqual(run.agents, [])
        finally:
            import shutil; shutil.rmtree(tmp, ignore_errors=True)

    def test_stage_persists_agents(self):
        from amsdp_ai_factory.runs.recorder import RunRecorder
        from amsdp_ai_factory.runs.models import AgentParticipation

        tmp = Path(tempfile.mkdtemp())
        try:
            rec = RunRecorder(store_dir=tmp / "runs")
            run = rec.new_run(task_id="T-1", workflow_id="WF-1")
            ap = AgentParticipation(agent_id="A01", role="analyst")
            rec.start_stage(run.run_id, name="a", stage_id="s1", agents=[ap])
            loaded = rec.get(run.run_id)
            self.assertEqual(loaded.stages[0].agents[0].agent_id, "A01")
        finally:
            import shutil; shutil.rmtree(tmp, ignore_errors=True)


class ExecutorRetryTests(unittest.TestCase):
    """Validates the executor does NOT re-invoke the LLM on failure."""

    def test_execute_body_has_single_kickoff(self):
        import inspect
        import amsdp_ai_factory.execution.live as live_mod
        src = inspect.getsource(live_mod.CrewAIExecutor.execute)
        self.assertEqual(src.count("kickoff()"), 1)
        self.assertNotIn("while True", src)
        self.assertNotIn("for attempt in", src)
        self.assertNotIn("for try_ in", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)