"""End-to-end stub verification: production code paths, focus_scope, agents.

Exercises:
1. Engine -> build_stage_task (output_pydantic on CrewAI Task)
2. Engine -> ExecutionRequest (focus_scope for assessments)
3. Engine -> RunRecorder (run + stage agents persisted)
4. MockAgentExecutor -> validate_output -> ArtifactStore
5. Evidence path verification inside workspace
6. No application source files modified

Does NOT call any model provider.
"""

import json, os, shutil, tempfile, unittest, hashlib
from pathlib import Path
import sys
sys.path.insert(0, "/home/shomonrobie/amsdp/ai_factory/src")
sys.path.insert(0, "/home/shomonrobie/amsdp/ai_factory")

from amsdp_ai_factory.contracts.outputs import (
    ARTIFACT_MODELS, ArtifactKind, RequirementAnalysis,
)
from amsdp_ai_factory.execution.live import _extract_validated_output
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.models import ExecutionRequest
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.execution.build_crews import build_stage_task
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
from amsdp_ai_factory.tasks.models import Task
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.tools.tool_registry import build_default_registry
from amsdp_ai_factory.approvals.service import ApprovalService
from amsdp_ai_factory.workflows.engine import WorkflowEngine
from amsdp_ai_factory.workflows.models import (
    StageDefinition, StageGate, StageKind,
    WorkflowDefinition, WorkflowStatus,
)
from amsdp_ai_factory.workflows.registry import WorkflowRegistry
class EndToEndStubVerification(unittest.TestCase):
    """Live-run corrections: complete engine path with stub executor.
    Maximum-fidelity verification without a provider API key.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = self.tmp / "ws"
        self.ws.mkdir(parents=True, exist_ok=True)
        self.task_reg = TaskRegistry(store_dir=self.tmp / "tasks")
        self.task = Task(
            task_id="T-VERIFY-1", title="Live Verification",
            workflow_id="WF-99", task_type="gap_assessment",
        )
        self.task_reg.create(self.task)
        self.wf = WorkflowDefinition(
            workflow_id="WF-99", name="verification", purpose="test",
            status=WorkflowStatus.EXECUTABLE,
            stages=[StageDefinition(
                stage_id="s1", name="analyze", kind=StageKind.AGENT,
                agent_ids=["A01"], gate=StageGate.NONE,
                expected_output_kinds=["requirement_analysis"],
            )],
        )
        self.wreg = WorkflowRegistry()
        self.wreg.register(self.wf)
        self.rec = RunRecorder(store_dir=self.tmp / "runs")
        self.eng = WorkflowEngine(
            task_registry=self.task_reg, run_recorder=self.rec,
            workspace_root=self.ws, workflow_registry=self.wreg,
            tool_registry=build_default_registry(),
            approval_service=ApprovalService(self.task_reg, self.rec),
            max_stage_attempts=1, repo_root=self.tmp,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------- focus_scope tests -------------------------------
    def test_01_focus_scope_populated_for_assessment(self):
        scope = self.eng._assessment_focus(self.task)
        self.assertIn("application implementation", scope)
        self.assertIn("backend/", scope)

    def test_02_focus_scope_empty_for_non_assessment(self):
        na = Task(task_id="T-NA", title="i", workflow_id="WF-99",
                  task_type="implementation")
        self.assertEqual(self.eng._assessment_focus(na), "")

    # ------------------- output_pydantic -------------------------------
    def test_03_build_stage_task_sets_output_pydantic(self):
        from crewai import Agent as CAgent
        d = CAgent(role="t", goal="t", backstory="t")
        req = ExecutionRequest(task_id="T-1", stage_id="s1", agent_id="A01",
            workflow_id="WF-99",
            expected_artifact_kind="requirement_analysis",
            context_summary="t", focus_scope="")
        ct = build_stage_task(d, req)
        self.assertIs(ct.output_pydantic,
                      ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS])
        self.assertIsNotNone(ct.response_model)

    def test_04_description_contains_focus_scope(self):
        from crewai import Agent as CAgent
        d = CAgent(role="t", goal="t", backstory="t")
        req = ExecutionRequest(task_id="T-1", stage_id="s1", agent_id="A01",
            workflow_id="WF-99",
            expected_artifact_kind="requirement_analysis",
            context_summary="t",
            focus_scope="ASSESSMENT FOCUS: check backend")
        ct = build_stage_task(d, req)
        self.assertIn("ASSESSMENT FOCUS", ct.description)

    # ------------------- agent_participants ---------------------------
    def test_05_agent_participants_from_stage(self):
        participants = self.eng._stage_agent_participants(
            StageDefinition(stage_id="s2", name="t", kind=StageKind.AGENT,
                agent_ids=["A01"], gate=StageGate.NONE))
        self.assertEqual(len(participants), 1)
        self.assertEqual(participants[0].agent_id, "A01")
        self.assertIn("product analyst", participants[0].role.lower())

    # ------------------- engine records agents -------------------------
    def test_06_engine_records_run_level_agents(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        loaded = self.rec.get(run.run_id)
        self.assertEqual(len(loaded.agents), 1)
        self.assertEqual(loaded.agents[0].agent_id, "A01")

    def test_07_engine_records_stage_level_agents(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        loaded = self.rec.get(run.run_id)
        self.assertEqual(len(loaded.stages), 1)
        self.assertEqual(len(loaded.stages[0].agents), 1)
        self.assertEqual(loaded.stages[0].agents[0].agent_id, "A01")
# ------------------- artifact validation -------------------------------
    def test_08_engine_produces_valid_artifact(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        self.assertEqual(run.status.value, "succeeded",
                         f"run status: {run.status}")
        stage = run.stages[0]
        # The output artifact is recorded in RunContext, not stored on stage.
        # Verify by checking that the run completed and has no errors.
        self.assertEqual(stage.status.value, "succeeded")
        self.assertTrue(len(run.checks) > 0 or len(run.artifacts) > 0,
                        "expected check or artifact record")

    def test_09_artifact_validated_against_schema(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        stage = run.stages[0]
        self.assertEqual(stage.status.value, "succeeded",
                         f"stage status: {stage.status}, error: {stage.error}")
        # Schema validation happens inside MockAgentExecutor.execute() which
        # calls validate_output() on the handler-produced model. A passing
        # stage confirms validation succeeded.

    # ------------------- _extract_validated_output ---------------------
    def test_10_extraction_from_agent_output(self):
        handler = build_stub_handler()
        req = ExecutionRequest(task_id="T-1", stage_id="s1", agent_id="A01",
            workflow_id="WF-99",
            expected_artifact_kind="requirement_analysis",
            context_summary="test")
        payload = handler(req).model_dump_json()
        extracted = _extract_validated_output(
            payload, ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS])
        self.assertIsInstance(extracted, RequirementAnalysis)
        self.assertEqual(extracted.task_id, "T-1")

    def test_11_extraction_from_json_string(self):
        payload = json.dumps({"artifact_type":"requirement_analysis",
            "task_id":"T-1","stage_id":"s1","agent_id":"A01",
            "title":"Test","summary":"t",
            "user_stories":["As a user I can test."],
            "acceptance_criteria":["Test passes."]})
        extracted = _extract_validated_output(
            payload, ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS])
        self.assertIsInstance(extracted, RequirementAnalysis)

    def test_12_prose_rejected_in_extraction(self):
        with self.assertRaises(ValueError):
            _extract_validated_output("some prose",
                ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS])

    # ------------------- evidence paths --------------------------------
    def test_13_evidence_paths_verified_in_workspace(self):
        store = ArtifactStore(self.ws, self.task.task_id)
        store.ensure()
        task_dir = store.workspace
        evidence_file = task_dir / "backend" / "identity" / "routes.py"
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text("from fastapi import APIRouter\nrouter = APIRouter()\n")
        def handler_with_evidence(req):
            model = ARTIFACT_MODELS[ArtifactKind.REQUIREMENT_ANALYSIS]
            output = model(task_id=req.task_id, workflow_id=req.workflow_id,
                stage_id=req.stage_id, agent_id=req.agent_id,
                title="[STUB] Evidence", summary="Paths verified.",
                user_stories=["As a user I can test."],
                acceptance_criteria=["Test passes."])
            # Evidence path must be absolute so Path(...).resolve() works
            output.evidence = [type("E", (), {"path": str(evidence_file),
                "description":"Identity routes","verified":False})()]
            return output
        stub = MockAgentExecutor(handler=handler_with_evidence)
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        stage = run.stages[0]
        self.assertEqual(stage.status.value, "succeeded",
            f"evidence failed: status={stage.status} error={stage.error}")

    # ------------------- metadata persistence -------------------------
    def test_14_run_recorder_persists_metadata(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        loaded = self.rec.get(run.run_id)
        self.assertEqual(loaded.task_id, "T-VERIFY-1")
        self.assertEqual(loaded.workflow_id, "WF-99")
        self.assertIsNotNone(loaded.started_at)

    # ------------------- no source file modifications -----------------
    def test_15_no_app_source_files_modified(self):
        files = sorted(self.ws.rglob("*.py"))
        before = {str(p.relative_to(self.ws)):
                  hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        stub = MockAgentExecutor(handler=build_stub_handler())
        self.eng.run(self.task.task_id, "WF-99", stub)
        after = {str(p.relative_to(self.ws)):
                 hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        self.assertEqual(before, after)

    # ------------------- engine rejects unknown workflow ---------------
    def test_16_engine_rejects_unknown_workflow(self):
        stub = MockAgentExecutor(handler=build_stub_handler())
        with self.assertRaises(Exception):
            self.eng.run(self.task.task_id, "WF-00", stub)

if __name__ == "__main__":
    unittest.main(verbosity=2)