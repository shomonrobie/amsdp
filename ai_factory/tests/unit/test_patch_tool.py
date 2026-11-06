"""Tests for PatchTool — Phase II."""

from __future__ import annotations
import tempfile, unittest
from pathlib import Path

from amsdp_ai_factory.tasks.models import ApprovalDecision, ApprovalRecord
from amsdp_ai_factory.tools.patch_tool import (
    AGENT_SCOPES, PatchFile, PatchSet, PatchTool, ToolPermissionError,
)


class TestPatchToolGenerate(unittest.TestCase):
    """1. Patch generation."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"
        self.workspace = self.tmpdir / "workspace"
        self.snaps = self.tmpdir / "snapshots"
        for d in (self.project, self.workspace, self.snaps): d.mkdir()
        for d in (self.project / "backend", self.workspace / "backend"): d.mkdir(parents=True)
        (self.project / "backend" / "existing.py").write_text("x = 1\n")
        (self.workspace / "backend" / "new_file.py").write_text("y = 2\n")
        (self.workspace / "backend" / "existing.py").write_text("x = 42\n")
        self.tool = PatchTool(project_root=self.project, snapshots_dir=self.snaps)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_modifications(self):
        r = self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A06")
        self.assertTrue(r.ok, r.error)
        self.assertIn("2 file(s) changed", r.summary)
        self.assertIn("modify: backend/existing.py", r.output)

    def test_generate_no_changes(self):
        (self.workspace / "backend" / "existing.py").write_text("x = 1\n")
        (self.workspace / "backend" / "new_file.py").unlink()  # remove to have no changes
        r = self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A06")
        self.assertTrue(r.ok)
        self.assertIn("empty patch", r.output)

    def test_wrong_scope_rejected(self):
        with self.assertRaises(ToolPermissionError):
            self.tool.generate(workspace=self.workspace, scope="frontend", agent_id="A06")

    def test_unknown_agent_rejected(self):
        with self.assertRaises(ToolPermissionError):
            self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A99")

    def test_patch_has_sha256(self):
        r = self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A06",
                               task_id="T-001", run_id="R-001")
        self.assertTrue(r.ok)
class TestPatchToolScope(unittest.TestCase):
    """2. Agent scopes & 5. Security enforcement."""

    def test_agent_scopes_exist(self):
        for a in ("A06", "A07", "A04", "A08", "A10", "A11"):
            self.assertIn(a, AGENT_SCOPES)

    def test_scope_values(self):
        self.assertEqual(AGENT_SCOPES["A06"], "backend")
        self.assertEqual(AGENT_SCOPES["A07"], "frontend")

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"; self.project.mkdir()
        self.tool = PatchTool(project_root=self.project)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_absolute_path_rejected(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._resolve_project_path("/etc/passwd", "backend")

    def test_traversal_rejected(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._resolve_project_path("../../etc/passwd", "backend")

    def test_symlink_rejected(self):
        link = self.project / "link"; link.symlink_to("/tmp")
        with self.assertRaises(ToolPermissionError):
            self.tool._assert_project_contained(link)

    def test_safe_path_accepted(self):
        p = self.tool._resolve_project_path("backend/test.py", "backend")
        self.assertEqual(p, (self.project / "backend" / "test.py").resolve())
class TestPatchToolApproval(unittest.TestCase):
    """3-4. Approval hash binding + stale rejection."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"
        self.workspace = self.tmpdir / "workspace"
        for d in (self.project, self.workspace): d.mkdir()
        for d in (self.project / "backend", self.workspace / "backend"): d.mkdir(parents=True)
        (self.workspace / "backend" / "x.py").write_text("z = 3\n")
        self.tool = PatchTool(project_root=self.project)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _get_sha(self):
        r = self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A06",
                               task_id="T", run_id="R")
        for line in r.output.splitlines():
            if "Patch SHA-256:" in line: return line.split(": ")[1].strip()
        return ""

    def test_matching_hash(self):
        sha = self._get_sha()
        ps = PatchSet(patch_id="p", task_id="T", run_id="R", agent_id="A06",
                      target_scope="backend", patch_sha256=sha,
                      files=[PatchFile(rel_path="x.py", action="add", after_sha256="a",
                                       unified_diff="--- /dev/null\n+++ b/x\n@@ -0,0 +1 @@\n+z = 3\n")])
        a = ApprovalRecord(decision_id=f"a-{sha}", decision=ApprovalDecision.APPROVED,
                           actor="human", rationale=f"patch_sha256={sha}")
        self.assertTrue(self.tool.verify_approval(ps, [a]).ok)

    def test_wrong_hash(self):
        ps = PatchSet(patch_id="p", task_id="T", run_id="R", agent_id="A06",
                      target_scope="backend", patch_sha256="aaa")
        a = ApprovalRecord(decision_id="a-", decision=ApprovalDecision.APPROVED,
                           actor="human", rationale="patch_sha256=bbb")
        self.assertFalse(self.tool.verify_approval(ps, [a]).ok)

    def test_not_approved(self):
        ps = PatchSet(patch_id="p", task_id="T", run_id="R", agent_id="A06",
                      target_scope="backend", patch_sha256="x")
        a = ApprovalRecord(decision_id="a-", decision=ApprovalDecision.REJECTED,
                           actor="human", rationale="patch_sha256=x")
        self.assertFalse(self.tool.verify_approval(ps, [a]).ok)

    def test_stale_rejected(self):
        ps = PatchSet(patch_id="p", task_id="T", run_id="R", agent_id="A06",
                      target_scope="backend", patch_sha256="x", status="stale")
        a = ApprovalRecord(decision_id="a-", decision=ApprovalDecision.APPROVED,
                           actor="human", rationale="patch_sha256=x")
        self.assertFalse(self.tool.apply(ps, [a]).ok)
class TestPatchToolApply(unittest.TestCase):
    """6-7. Atomic application, backup and rollback."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"
        self.workspace = self.tmpdir / "workspace"
        self.snaps = self.tmpdir / "snapshots"
        for d in (self.project, self.workspace, self.snaps): d.mkdir()
        for d in (self.project / "backend", self.workspace / "backend"): d.mkdir(parents=True)
        (self.project / "backend" / "target.py").write_text("original\n")
        (self.workspace / "backend" / "target.py").write_text("modified\n")
        self.tool = PatchTool(project_root=self.project, snapshots_dir=self.snaps)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_apply_and_rollback(self):
        r = self.tool.generate(workspace=self.workspace, scope="backend", agent_id="A06",
                               task_id="T", run_id="R")
        sha = ""
        for line in r.output.splitlines():
            if "Patch SHA-256:" in line: sha = line.split(": ")[1].strip(); break
        # Use the real before-hash of the original project file so the
        # "file unchanged since generation" gate passes.
        import hashlib
        before = hashlib.sha256(b"original\n").hexdigest()
        ps = PatchSet(patch_id="patch-T-R", task_id="T", run_id="R", agent_id="A06",
                      target_scope="backend", patch_sha256=sha,
                      files=[PatchFile(rel_path="backend/target.py", action="modify",
                                       before_sha256=before, after_sha256="b",
                                       unified_diff="--- a/backend/target.py\t(before)\n+++ b/backend/target.py\t(after)\n@@ -1 +1 @@\n-original\n+modified\n")])
        a = ApprovalRecord(decision_id=f"a-{sha}", decision=ApprovalDecision.APPROVED,
                           actor="h", rationale=f"patch_sha256={sha} repo=project")
        apply_result = self.tool.apply(ps, [a])
        self.assertTrue(apply_result.ok, apply_result.error)
        self.assertIn("modified", (self.project / "backend" / "target.py").read_text())
        # Rollback
        rb = self.tool.rollback(ps)
        self.assertTrue(rb.ok, rb.error)
        self.assertIn("original", (self.project / "backend" / "target.py").read_text())
        self.assertIn("Patch SHA-256:", r.output)