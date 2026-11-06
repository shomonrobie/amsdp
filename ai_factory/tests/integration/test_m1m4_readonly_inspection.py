"""Tests for M1-M4: read-only agent tool attachment, registry dispatch,
project-context injection, and inspection provenance."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, "/home/shomonrobie/amsdp/ai_factory/src")

from amsdp_ai_factory.agents.definitions import AGENT_INDEX
from amsdp_ai_factory.agent_tools import (
    ToolOperationCollector,
    build_read_tool_bundle,
)
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.execution.build_crews import build_agent
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import Task
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.workflows.engine import WorkflowEngine
from amsdp_ai_factory.workflows.registry import WorkflowRegistry
from amsdp_ai_factory.approvals.service import ApprovalService


def _make_repo(tmp: Path) -> Path:
    repo = tmp / "proj"
    (repo / ".git").mkdir(parents=True, exist_ok=True)
    (repo / "backend").mkdir(parents=True, exist_ok=True)
    (repo / "frontend").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "product").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "identity").mkdir(parents=True, exist_ok=True)
    (repo / "frontend" / "pages").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "identity" / "main.py").write_text(
        "def health_check():\n    return {'status': 'ok'}\n"
    )
    (repo / "frontend" / "pages" / "login.js").write_text(
        "export default function Login() { return <p>login</p>; }\n"
    )
    (repo / "docs" / "product" / "AMSDP_Business_Rules_V1.0.md").write_text(
        "# Business Rules\nPatients must be unique.\n"
    )
    (repo / "docs" / "product" / "AMSDP_MVP_SCOPE_V1.0.md").write_text(
        "# MVP Scope\nNo patient self-service.\n"
    )
    (repo / "docs" / "architecture" / "AMSDP_System_Architecture_V1.0.md").write_text(
        "# Architecture\nMicroservices.\n"
    )
    return repo


class ToolAttachmentTests(unittest.TestCase):
    """M1: agents receive only authorized read-only tools."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = _make_repo(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_agent_receives_authorized_read_tools(self):
        agent = AGENT_INDEX["A01"]
        bundle = build_read_tool_bundle(agent, repo_root=self.repo)
        ids = bundle.ids()
        self.assertIn("repo_read", ids)
        self.assertIn("doc_reader", ids)
        self.assertGreaterEqual(bundle.count(), 3)

    def test_unauthorized_write_tool_not_attached(self):
        agent = AGENT_INDEX["A09"]
        bundle = build_read_tool_bundle(agent, repo_root=self.repo)
        for tid in bundle.ids():
            self.assertNotIn(tid, {"patch_generator", "artifact_write"})

    def test_crewai_agent_constructed_with_tools(self):
        agent_def = AGENT_INDEX["A02"]
        bundle = build_read_tool_bundle(agent_def, repo_root=self.repo)
        crew_agent = build_agent(agent_def, tools=bundle.as_list())
        attached = getattr(crew_agent, "tools", None) or []
        self.assertGreaterEqual(len(attached), 1)
        names = [getattr(t, "name", "") for t in attached]
        self.assertTrue(any("repo_read" in n for n in names), names)


class ToolDispatchTests(unittest.TestCase):
    """M2: registry-driven dispatch + denial behaviour."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = _make_repo(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _engine(self):
        task_reg = TaskRegistry(store_dir=self.tmp / "tasks")
        task = Task(task_id="T-READ-001", title="read", workflow_id="WF-01")
        task_reg.create(task)
        rec = RunRecorder(store_dir=self.tmp / "runs")
        eng = WorkflowEngine(
            task_registry=task_reg,
            run_recorder=rec,
            workspace_root=self.tmp / "ws",
            workflow_registry=WorkflowRegistry(),
            approval_service=ApprovalService(task_reg, rec),
            repo_root=self.repo,
        )
        return task_reg, rec, eng, task

    def test_registered_tool_dispatches(self):
        _, _, eng, task = self._engine()
        from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
        store = ArtifactStore(self.tmp / "ws", task.task_id)
        result = eng._execute_registered_tool("doc_link_validator", task, store)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "ok"))
        result2 = eng._execute_registered_tool("repo_read", task, store)
        self.assertIsNotNone(result2)
        self.assertIn("backend", (result2.output or ""))

    def test_unknown_tool_raises(self):
        _, _, eng, task = self._engine()
        from amsdp_ai_factory.workflows.engine import WorkflowError
        with self.assertRaises(WorkflowError):
            eng._execute_registered_tool("does_not_exist", task, None)

    def test_unbound_agent_denied(self):
        from amsdp_ai_factory.tools.tool_registry import build_default_registry
        reg = build_default_registry()
        with self.assertRaises(Exception):
            reg.assert_allowed("A01", "doc_link_validator")


class ContextInjectionTests(unittest.TestCase):
    """M3: ContextLoader injects real content, bounded."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = _make_repo(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_loader_injects_actual_document_content(self):
        loader = ContextLoader(repo_root=self.repo)
        docs = loader.load_for_task(None, max_chars=4000)
        self.assertGreater(len(docs), 0)
        full = " ".join(d.text for d in docs)
        self.assertTrue(("Business Rules" in full) or ("MVP" in full), full[:100])
        self.assertTrue(all(d.record.sha256 for d in docs))

    def test_context_limits_enforced(self):
        loader = ContextLoader(repo_root=self.repo)
        docs = loader.load_for_task(None, max_chars=80)
        for d in docs:
            self.assertLessEqual(len(d.text), 80 + 64)


class ProvenanceTests(unittest.TestCase):
    """M4: ToolOperationRecord populated with provenance."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = _make_repo(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_collector_populates_provenance(self):
        c = ToolOperationCollector(agent_id="A02", stage_id="s1")
        c.record(
            operation="repo_read.read_text",
            target="backend/identity/main.py", ok=True,
            output_summary="read 49 chars",
            evidence_refs=[{"path": "backend/identity/main.py", "sha256": "abc123"}],
        )
        r = c.records()[0]
        self.assertEqual(r.agent_id, "A02")
        self.assertEqual(r.stage_id, "s1")
        self.assertEqual(r.operation, "repo_read.read_text")
        self.assertEqual(r.target, "backend/identity/main.py")
        self.assertTrue(r.ok)
        self.assertEqual(r.evidence_refs[0]["sha256"], "abc123")
        self.assertTrue(r.started_at)

    def test_bundle_collector_records_calls(self):
        agent = AGENT_INDEX["A02"]
        c = ToolOperationCollector(agent_id="A02", stage_id="s1")
        bundle = build_read_tool_bundle(agent, repo_root=self.repo, collector=c)
        for tid in bundle.ids():
            for tool in bundle._tools[tid]:
                try:
                    fname = getattr(tool, "name", "") or ""
                    if "read_text" in fname:
                        tool.func(rel_path="backend/identity/main.py")
                except Exception:
                    pass
        ops = [r.operation for r in c.records()]
        self.assertTrue(any("read_text" in o for o in ops), ops)
class RepositoryContainmentTests(unittest.TestCase):
    """Security: traversal containment + no source modification."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = _make_repo(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_read_stays_inside_project(self):
        from amsdp_ai_factory.tools.repository_read import RepositoryReadTool
        tool = RepositoryReadTool(self.repo)
        before = (self.repo / "backend" / "identity" / "main.py").read_bytes()
        r = tool.read_text("backend/identity/main.py")
        self.assertTrue(r.ok)
        after = (self.repo / "backend" / "identity" / "main.py").read_bytes()
        self.assertEqual(before, after, "read must not modify the file")

    def test_traversal_rejected(self):
        from amsdp_ai_factory.tools.repository_read import RepositoryReadTool
        tool = RepositoryReadTool(self.repo)
        r = tool.read_text("../../../etc/passwd")
        self.assertFalse(r.ok, "traversal must be rejected")
        self.assertIn("escapes", r.error)

    def test_no_source_modification_by_bundle(self):
        agent = AGENT_INDEX["A02"]
        bundle = build_read_tool_bundle(agent, repo_root=self.repo)
        targets = [
            "backend/identity/main.py", "frontend/pages/login.js",
            "docs/product/AMSDP_Business_Rules_V1.0.md",
        ]
        snap = {p: (self.repo / p).read_bytes() for p in targets}
        for tid in bundle.ids():
            for tool in bundle._tools[tid]:
                try:
                    fname = getattr(tool, "name", "") or ""
                    if "read_text" in fname:
                        tool.func(rel_path="backend/identity/main.py")
                    elif "list_paths" in fname:
                        tool.func(rel_dir="")
                    elif "status" in fname:
                        tool.func()
                    elif "head" in fname:
                        tool.func()
                    elif "branches" in fname:
                        tool.func()
                    elif "log" in fname:
                        tool.func(n=3)
                    elif "search" in fname:
                        tool.func(pattern="status")
                    elif "roles" in fname:
                        tool.func()
                    elif fname == "doc_reader_read":
                        tool.func(role="business_rules")
                except Exception:
                    pass
        for p, b in snap.items():
            self.assertEqual((self.repo / p).read_bytes(), b, f"{p} was modified!")


class EngineProvenanceTest(unittest.TestCase):
    """M4 end-to-end: repo-read tool stage records provenance."""

    def test_tool_stage_records_provenance(self):
        self.tmp = Path(tempfile.mkdtemp())
        try:
            repo = _make_repo(self.tmp)
            from amsdp_ai_factory.workflows.models import (
                StageKind, StageDefinition, StageGate,
                WorkflowDefinition, WorkflowStatus,
            )
            from amsdp_ai_factory.execution.mock import MockAgentExecutor
            from amsdp_ai_factory.execution.stub_handler import build_stub_handler
            from amsdp_ai_factory.tools.tool_registry import build_default_registry

            task_reg = TaskRegistry(store_dir=self.tmp / "tasks")
            task = Task(task_id="T-PROV-1", title="prov", workflow_id="WF-98")
            task_reg.create(task)
            rec = RunRecorder(store_dir=self.tmp / "runs")
            wf = WorkflowDefinition(
                workflow_id="WF-98", name="read-only", purpose="test",
                status=WorkflowStatus.EXECUTABLE,
                stages=[StageDefinition(
                    stage_id="s1", name="read", kind=StageKind.TOOL,
                    tool_stage_tool_id="repo_read", via_agent_id="A01",
                    gate=StageGate.NONE,
                )],
            )
            wreg = WorkflowRegistry()
            wreg.register(wf)
            eng = WorkflowEngine(
                task_registry=task_reg, run_recorder=rec,
                workspace_root=self.tmp / "ws", workflow_registry=wreg,
                tool_registry=build_default_registry(),
                approval_service=ApprovalService(task_reg, rec),
                max_stage_attempts=1, repo_root=repo,
            )
            stub = MockAgentExecutor(handler=build_stub_handler())
            run = eng.run(task.task_id, "WF-98", stub)
            ops = rec.get(run.run_id).tool_operations
            self.assertGreaterEqual(len(ops), 1, "tool operation must be recorded")
            self.assertTrue(any("repo_read" in (o.name or "") for o in ops), ops)
            self.assertEqual(
                (repo / "backend" / "identity" / "main.py").read_text(),
                "def health_check():\n    return {'status': 'ok'}\n",
            )
        finally:
            import shutil
            shutil.rmtree(self.tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()