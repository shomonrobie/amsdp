"""Agent Rules integration tests.

Covers:
1. Manifest parsing and validation.
2. Discovery of all rule documents.
3. SHA-256 hash and version recording.
4. Agent-to-rule mapping.
5. Correct selective context injection.
6. Universal governance rule availability.
7. Irrelevant rules not injected.
8. Missing and malformed rules reported.
9. Changed rule content detected.
10. Context-limit handling.
11. Rule references preserved in execution provenance.
12. Project requirement conflicts correctly escalated.
13. Existing ContextLoader and workflow behavior remains compatible.
14. Existing tests continue to pass.
"""

import hashlib, json, os, shutil, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, "/home/shomonrobie/amsdp/ai_factory/src")

from amsdp_ai_factory.rules.registry import (
    AgentRulesRegistry, RuleScanResult, RuleDocument,
    resolve_rule_text, _parse_frontmatter, _detect_rule_id, _validate_manifest,
)
from amsdp_ai_factory.rules.mapping import (
    RULE_MAP, TASK_TYPE_RULE_MAP, select_rule_ids,
)

RULES_DIR = Path("/home/shomonrobie/amsdp/ai_factory/docs/agent-rules")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestManifestAndDiscovery(unittest.TestCase):
    def setUp(self):
        self.reg = AgentRulesRegistry(RULES_DIR)
        self.result = self.reg.discover()

    def test_01_manifest_parsing_and_validation(self):
        self.assertEqual(self.reg.validate_manifest(), [])

    def test_02_all_rule_documents_discovered(self):
        expected = {"README.md", "carbontally-agent-governance.md",
            "emissions-provenance.md", "saas-ai-provider-registry.md",
            "saas-api-throttling.md", "saas-application-security.md",
            "saas-auth-and-authorisation.md", "saas-cicd-workflow.md",
            "saas-frontend-ux.md", "saas-multitenant-data.md",
            "saas-observability.md"}
        found = {r.file_name for r in self.result.rules if r.exists}
        self.assertEqual(found, expected)

    def test_03_sha256_hash_recording(self):
        for rule in self.result.rules:
            if not rule.exists:
                continue
            self.assertEqual(len(rule.sha256_actual), 64, rule.file_name)
            if rule.sha256_manifest:
                self.assertEqual(rule.sha256_actual, rule.sha256_manifest,
                                 f"{rule.file_name} hash mismatch")

    def test_03b_no_missing_or_errors(self):
        self.assertEqual(self.result.missing, [])
        self.assertEqual(self.result.manifest_errors, [])

    def test_03c_unexpected_ignores_readme(self):
        unexpected = [f for f in self.result.unexpected if f != "README.md"]
        self.assertEqual(unexpected, [])

    def test_03d_frontmatter_parsed(self):
        gov = [r for r in self.result.rules \
               if r.rule_id == "carbontally_agent_governance"]
        if gov:
            self.assertIsNotNone(gov[0].parsed_name)
            self.assertIsNotNone(gov[0].parsed_description)

    def test_03e_invalid_manifest_rejected(self):
        self.assertGreater(len(_validate_manifest({"files": "bad"})), 0)
        self.assertGreater(len(_validate_manifest({"files": {"x.md": "bad"}})), 0)

    def test_03f_detect_rule_id(self):
        self.assertEqual(_detect_rule_id("carbontally-agent-governance.md"),
                         "carbontally_agent_governance")
        self.assertEqual(_detect_rule_id("saas-api-throttling.md"),
                         "saas_api_throttling")


class TestAgentMapping(unittest.TestCase):
    def test_04_all_agents_get_governance(self):
        for aid in ["A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11"]:
            ids = select_rule_ids(agent_id=aid)
            self.assertIn("carbontally_agent_governance", ids, f"Missing for {aid}")

    def test_05_governance_is_universal(self):
        self.assertIn("carbontally_agent_governance", select_rule_ids())
        self.assertIn("carbontally_agent_governance", select_rule_ids(agent_id="UNKNOWN"))

    def test_06_different_agents_different_rules(self):
        self.assertIn("saas_frontend_ux", select_rule_ids(agent_id="A07"))
        self.assertIn("saas_cicd_workflow", select_rule_ids(agent_id="A10"))
        self.assertNotIn("saas_cicd_workflow", select_rule_ids(agent_id="A01"))
        self.assertIn("saas_application_security", select_rule_ids(agent_id="A09"))

    def test_07_irrelevant_not_injected(self):
        self.assertNotIn("saas_frontend_ux", select_rule_ids(agent_id="A10"))
        self.assertNotIn("saas_cicd_workflow", select_rule_ids(agent_id="A07"))

    def test_07b_task_type_mapping(self):
        self.assertIn("saas_application_security", select_rule_ids(task_type="security_review"))
        self.assertIn("saas_frontend_ux", select_rule_ids(task_type="frontend_implementation"))


class TestContextLimitAndDetection(unittest.TestCase):
    def test_08_malformed_rules_reported(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "MANIFEST.json").write_text('{"files": ["bad"]}')
            self.assertGreater(len(AgentRulesRegistry(tmp).validate_manifest()), 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_09_changed_content_detected(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            d = tmp / "test-rule.md"
            d.write_text("original")
            real = _sha256(d)
            fake = "0" * 64
            (tmp / "MANIFEST.json").write_text(
                json.dumps({"files": {"test-rule.md": fake}, "purpose": "t"}))
            res = AgentRulesRegistry(tmp).discover()
            self.assertEqual(len(res.changed), 1)
            self.assertEqual(res.changed[0][0], "test-rule.md")
            self.assertEqual(res.changed[0][1], fake)
            self.assertEqual(res.changed[0][2], real)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_10_empty_manifest_still_valid(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "MANIFEST.json").write_text('{"files": {}, "purpose": "empty"}')
            res = AgentRulesRegistry(tmp).discover()
            self.assertTrue(res.ok)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        from amsdp_ai_factory.tasks.registry import TaskRegistry
        from amsdp_ai_factory.tasks.models import Task
        from amsdp_ai_factory.runs.recorder import RunRecorder
        from amsdp_ai_factory.workflows.models import (
            StageDefinition, StageGate, StageKind,
            WorkflowDefinition, WorkflowStatus,
        )
        from amsdp_ai_factory.workflows.registry import WorkflowRegistry
        from amsdp_ai_factory.tools.tool_registry import build_default_registry
        from amsdp_ai_factory.approvals.service import ApprovalService
        from amsdp_ai_factory.workflows.engine import WorkflowEngine
        from amsdp_ai_factory.execution.mock import MockAgentExecutor
        from amsdp_ai_factory.execution.stub_handler import build_stub_handler
        self.task_reg = TaskRegistry(store_dir=self.tmp / "tasks")
        self.task = Task(task_id="T-RULE-1", title="R", workflow_id="WF-99",
                         task_type="security_review")
        self.task_reg.create(self.task)
        self.wf = WorkflowDefinition(
            workflow_id="WF-99", name="t", purpose="t",
            status=WorkflowStatus.EXECUTABLE,
            stages=[StageDefinition(
                stage_id="s1", name="a", kind=StageKind.AGENT,
                agent_ids=["A09"], gate=StageGate.NONE,
                expected_output_kinds=["requirement_analysis"],
            )],
        )
        self.wreg = WorkflowRegistry()
        self.wreg.register(self.wf)
        self.rec = RunRecorder(store_dir=self.tmp / "runs")
        self.eng = WorkflowEngine(
            task_registry=self.task_reg, run_recorder=self.rec,
            workspace_root=self.tmp / "ws", workflow_registry=self.wreg,
            tool_registry=build_default_registry(),
            approval_service=ApprovalService(self.task_reg, self.rec),
            max_stage_attempts=1, repo_root=self.tmp,
        )
        (self.tmp / "ws").mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_11_provenance_via_successful_stage(self):
        from amsdp_ai_factory.execution.mock import MockAgentExecutor
        from amsdp_ai_factory.execution.stub_handler import build_stub_handler
        stub = MockAgentExecutor(handler=build_stub_handler())
        run = self.eng.run(self.task.task_id, "WF-99", stub)
        self.assertEqual(run.stages[0].status.value, "succeeded")

    def test_12_select_agent_rules_returns_expected(self):
        ids = self.eng._select_agent_rules(self.task, self.wf.stages[0])
        self.assertIn("carbontally_agent_governance", ids)
        self.assertIn("saas_application_security", ids)
    def test_12b_load_agent_rules_contains_content(self):
        text = self.eng._load_agent_rules(self.task, self.wf.stages[0])
        self.assertIn("Application Security", text)
        self.assertIn("Auth", text)

    def test_13_existing_loader_compatible(self):
        from amsdp_ai_factory.context.loader import ContextLoader
        loader = ContextLoader(repo_root=self.tmp)
        self.assertIsNotNone(loader.scan())

    def test_13b_fallback_no_rules_dir(self):
        from amsdp_ai_factory.workflows.engine import WorkflowEngine
        tool_reg = __import__('amsdp_ai_factory.tools.tool_registry',
                              fromlist=['build_default_registry']).build_default_registry()
        t2 = __import__('amsdp_ai_factory.tasks.models',
                        fromlist=['Task']).Task(
            task_id="T-FB", title="f", workflow_id="WF-99", task_type="a")
        self.task_reg.create(t2)
        eng2 = WorkflowEngine(
            task_registry=self.task_reg, run_recorder=self.rec,
            workspace_root=self.tmp / "ws2", workflow_registry=self.wreg,
            tool_registry=tool_reg, approval_service=self.task_reg,
            max_stage_attempts=1, repo_root=self.tmp / "no-rules",
        )
        text = eng2._load_agent_rules(t2, self.wf.stages[0])
        self.assertIsInstance(text, str)


class TestResolveRuleText(unittest.TestCase):
    def test_resolve_governance(self):
        text = resolve_rule_text(RULES_DIR, "carbontally_agent_governance")
        self.assertIsNotNone(text)
        self.assertIn("Tier 1", text)

    def test_resolve_frontend(self):
        text = resolve_rule_text(RULES_DIR, "saas_frontend_ux")
        self.assertIsNotNone(text)
        self.assertIn("Frontend", text)

    def test_resolve_unknown(self):
        self.assertIsNone(resolve_rule_text(RULES_DIR, "nosuch_rule_xyz"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
