"""Tests for RunContext — Phase III."""

from __future__ import annotations
import unittest

from amsdp_ai_factory.contracts.outputs import (
    AgentOutput,
    RequirementAnalysis,
    ArchitectureProposal,
)
from amsdp_ai_factory.contracts.common import Severity
from amsdp_ai_factory.execution.run_context import RunContext


def _output(kind, title="Title", summary="Summary", stage="s1", agent="A01"):
    """Create the correct model for each artifact kind."""
    common = dict(
        task_id="T", stage_id=stage, agent_id=agent,
        title=title, summary=summary,
    )
    if kind == "architecture_proposal":
        return ArchitectureProposal(**common)
    # Default: requirement_analysis (also supports arbitrary generic tests)
    return RequirementAnalysis(**common)


class TestRunContextArtifactPassing(unittest.TestCase):
    """8. Artifact passing between stages."""

    def test_record_stores_artifact(self):
        ctx = RunContext()
        check = ctx.record(stage_id="s1", agent_id="A01",
                           output=_output("requirement_analysis"),
                           expected_kinds=["requirement_analysis"])
        self.assertTrue(check.ok)
        self.assertEqual(ctx.count, 1)

    def test_unexpected_type_rejected(self):
        ctx = RunContext()
        check = ctx.record(stage_id="s1", agent_id="A01",
                           output=_output("requirement_analysis"),
                           expected_kinds=["api_contract"])
        self.assertFalse(check.ok)
        self.assertIn("expected one of", str(check.issues[0].message))

    def test_context_includes_provenance(self):
        ctx = RunContext()
        ctx.record(stage_id="s1", agent_id="A01",
                   output=_output("requirement_analysis"))
        ctx_str = ctx.context_for()
        self.assertIn("s1", ctx_str)
        self.assertIn("A01", ctx_str)
        self.assertIn("Title", ctx_str)

    def test_context_filtered_by_kind(self):
        ctx = RunContext()
        ctx.record(stage_id="s1", agent_id="A01",
                   output=_output("requirement_analysis"))
        ctx.record(stage_id="s2", agent_id="A02",
                   output=_output("architecture_proposal", title="Arch"))
        ctx_str = ctx.context_for(required_kinds=["architecture_proposal"])
        self.assertIn("Arch", ctx_str)
        self.assertNotIn("Title", ctx_str)


class TestRunContextIntegrity(unittest.TestCase):
    """9. Artifact integrity."""

    def test_record_hashes_content(self):
        ctx = RunContext()
        o = _output("requirement_analysis")
        ctx.record(stage_id="s1", agent_id="A01", output=o)
        r = ctx.recorded()
        self.assertGreater(len(r[0].sha256), 0)

    def test_same_content_same_hash(self):
        o = _output("requirement_analysis")
        ctx1, ctx2 = RunContext(), RunContext()
        ctx1.record(stage_id="s1", agent_id="A01", output=o)
        ctx2.record(stage_id="s1", agent_id="A01", output=o)
        self.assertEqual(ctx1.recorded()[0].sha256, ctx2.recorded()[0].sha256)

    def test_immutable_kind_marked(self):
        ctx = RunContext()
        ctx.record(stage_id="s1", agent_id="A01",
                   output=_output("architecture_proposal", title="V1"))
        check = ctx.record(stage_id="s2", agent_id="A02",
                           output=_output("architecture_proposal", title="V2"))
        # Warning issued, not error
        self.assertTrue(check.ok)
        self.assertGreater(len(check.issues), 0)
        self.assertEqual(check.issues[0].severity, Severity.WARNING)
        self.assertIn("immutable_artifact_resupplied", check.issues[0].code)
        recorded = ctx.recorded()
        self.assertTrue(recorded[1].replaced)


class TestRunContextSizeLimit(unittest.TestCase):
    """10. Size limits."""

    def test_context_truncated(self):
        ctx = RunContext()
        for i in range(10):
            ctx.record(stage_id=f"s{i}", agent_id="A01",
                       output=_output("requirement_analysis",
                                      summary="X" * 2000))
        ctx_str = ctx.context_for(max_chars=2000)
        self.assertLess(len(ctx_str), 5000)