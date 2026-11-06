"""Integration: PatchTool security + RunContext multi-agent."""
import hashlib, tempfile, unittest
from pathlib import Path

from amsdp_ai_factory.contracts.outputs import RequirementAnalysis
from amsdp_ai_factory.execution.run_context import RunContext
from amsdp_ai_factory.tasks.models import ApprovalDecision, ApprovalRecord
from amsdp_ai_factory.tools.patch_tool import (PatchFile, PatchSet, PatchTool, ToolPermissionError,
    _applied_patches, _load_applied_patches)

class PatchToolSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = self.tmpdir / "project"
        self.workspace = self.tmpdir / "workspace"
        self.snaps = self.tmpdir / "snapshots"
        for d in (self.project, self.workspace, self.snaps): d.mkdir()
        for d in (self.project/"backend", self.workspace/"backend"): d.mkdir(parents=True)
        self.tool = PatchTool(project_root=self.project, snapshots_dir=self.snaps)
        _applied_patches.clear()
    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)
        _applied_patches.clear()
    def _ps(self, sha, files=None):
        return PatchSet(patch_id="t", task_id="T", run_id="R", agent_id="A06",
            target_scope="backend", repo_identifier="test-repo", patch_sha256=sha,
            files=files or [PatchFile(rel_path="x", action="add", after_sha256="a",
                unified_diff="--- /dev/null\n+++ b/x\n@@ -0,0 +1 @@\n+x\n")])
    def _appr(self, sha, repo="test-repo"):
        return ApprovalRecord(decision_id=f"a-{sha}", decision=ApprovalDecision.APPROVED,
            actor="human", rationale=f"patch_sha256={sha} repo={repo}")
    def test_a1_binding(self):
        self.assertTrue(self.tool.verify_approval(self._ps("abc"), [self._appr("abc")]).ok)
    def test_a1_wrong_hash(self):
        self.assertFalse(self.tool.verify_approval(self._ps("abc"), [self._appr("def")]).ok)
    def test_a1_wrong_repo(self):
        self.assertFalse(self.tool.verify_approval(self._ps("abc"), [self._appr("abc","x")]).ok)
    def test_a2_no_reuse(self):
        _applied_patches.add("nr")
        r=self.tool.apply(self._ps("nr"),[self._appr("nr")])
        self.assertFalse(r.ok); self.assertIn("already applied",r.error)
    def test_a3_changed_file(self):
        (self.project/"backend"/"t.py").write_text("orig\n")
        sha=hashlib.sha256(b"orig\n").hexdigest()
        ps=self._ps("c",files=[PatchFile(rel_path="backend/t.py",action="modify",
            before_sha256=sha,after_sha256="b",unified_diff="@@ -1 +1 @@\n-orig\n+new\n")])
        (self.project/"backend"/"t.py").write_text("diff\n")
        r=self.tool.apply(ps,[self._appr("c")])
        self.assertFalse(r.ok); self.assertIn("stale",r.error)
    def test_a4_baseline(self):
        ps=PatchSet(patch_id="b",task_id="T",run_id="R",agent_id="A06",
            target_scope="backend",baseline_revision="abc1234",repo_identifier="test-repo",
            patch_sha256="b",files=[])
        err=self.tool._verify_baseline_current(ps); self.assertNotEqual(err, ""); self.assertIn("failing closed", err)
    def test_a5_traversal(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._resolve_project_path("../../etc/passwd","backend")
    def test_a5_symlink(self):
        link=self.project/"link"; link.symlink_to("/tmp")
        with self.assertRaises(ToolPermissionError):
            self.tool._assert_project_contained(link)
    def test_a6_rollback(self):
        (self.project/"backend"/"f1.py").write_text("one\n")
        (self.project/"backend"/"f2.py").write_text("two\n")
        ps=PatchSet(patch_id="m",task_id="T",run_id="R",agent_id="A06",
            target_scope="backend",repo_identifier="test-repo",patch_sha256="m",
            files=[PatchFile(rel_path="backend/f1.py",action="modify",
                before_sha256=hashlib.sha256(b"one\n").hexdigest(),after_sha256="b",
                unified_diff="@@ -1 +1 @@\n+ok\n"),
                PatchFile(rel_path="backend/f2.py",action="modify",
                before_sha256=hashlib.sha256(b"two\n").hexdigest(),after_sha256="c",
                unified_diff="")])
        r=self.tool.apply(ps,[self._appr("m")])
        self.assertFalse(r.ok)
        self.assertEqual((self.project/"backend"/"f1.py").read_text(),"one\n")
    def test_a7_bad_diff(self):
        (self.project/"backend"/"f.py").write_text("a\nb\n")
        ps=self._ps("bad",files=[PatchFile(rel_path="backend/f.py",action="modify",
            before_sha256="x",after_sha256="y",unified_diff="@@ -10 +10 @@\n-missing\n+added\n")])
        self.assertFalse(self.tool.apply(ps,[self._appr("bad")]).ok)
    def test_a8_hashes(self):
        (self.project/"backend"/"t.py").write_text("orig\n")
        ps=self._ps("h8",files=[PatchFile(rel_path="backend/t.py",action="modify",
            before_sha256=hashlib.sha256(b"orig\n").hexdigest(),after_sha256="b",
            unified_diff="@@ -1 +1 @@\n-orig\n+new\n")])
        r=self.tool.apply(ps,[self._appr("h8")])
        self.assertTrue(r.ok,r.error)
        self.assertEqual(len(r.files_before),1); self.assertEqual(len(r.files_after),1)
        self.assertIsNotNone(r.files_before[0]["sha256"]); self.assertIsNotNone(r.files_after[0]["sha256"])
    def test_a9_scope(self):
        with self.assertRaises(ToolPermissionError):
            self.tool._assert_scope("A07","backend")
        self.tool._assert_scope("A06","backend")

class RunContextIntegrationTests(unittest.TestCase):
    def test_context_flow(self):
        ctx=RunContext()
        a1=RequirementAnalysis(task_id="T",stage_id="s1",agent_id="A01",
            title="Req",summary="Login needed")
        check=ctx.record(stage_id="s1",agent_id="A01",output=a1,
            expected_kinds=["requirement_analysis"])
        self.assertTrue(check.ok)
        self.assertIn("requirement_analysis",ctx.context_for())
        self.assertIn("A01",ctx.context_for())
        self.assertEqual(ctx.context_for(required_kinds=["architecture_proposal"]),"")
class PatchPersistenceTests(unittest.TestCase):
    """Persistent replay protection: durability, restart, crash recovery."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.project = Path(self.tmpdir) / "project"
        self.workspace = Path(self.tmpdir) / "workspace"
        self.snaps = Path(self.tmpdir) / "snapshots"
        for d in (self.project, self.workspace, self.snaps): d.mkdir()
        for d in (self.project / "backend", self.workspace / "backend"): d.mkdir(parents=True)
        _applied_patches.clear()

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)
        _applied_patches.clear()

    def _tool(self):
        return PatchTool(project_root=self.project, snapshots_dir=self.snaps)

    def _valid_patch(self):
        (self.project / "backend" / "target.py").write_text("original\n")
        (self.workspace / "backend" / "target.py").write_text("modified\n")
        result = self._tool().generate(
            workspace=self.workspace, scope="backend", agent_id="A06",
            task_id="TT", run_id="RR",
        )
        sha = ""
        for line in result.output.splitlines():
            if "Patch SHA-256:" in line:
                sha = line.split(": ")[1].strip()
        import hashlib
        before = hashlib.sha256(b"original\n").hexdigest()
        ps = PatchSet(patch_id="persist-test", task_id="TT", run_id="RR",
                      agent_id="A06", target_scope="backend", patch_sha256=sha,
                      files=[PatchFile(rel_path="backend/target.py", action="modify",
                                       before_sha256=before, after_sha256="b",
                                       unified_diff="@@ -1 +1 @@\n-original\n+modified\n")])
        a = ApprovalRecord(decision_id=f"a-{sha}", decision=ApprovalDecision.APPROVED,
                           actor="h", rationale=f"patch_sha256={sha} repo={self.project.name}")
        return ps, a

    def test_durable_save_and_restart(self):
        """Apply persists the hash; a fresh tool instance rejects replay."""
        ps, a = self._valid_patch()
        t1 = self._tool()
        r1 = t1.apply(ps, [a])
        self.assertTrue(r1.ok, r1.error)
        self.assertIn("modified", (self.project / "backend" / "target.py").read_text())
        # Simulate restart: new instance; module set is reloaded from disk.
        _applied_patches.clear()  # simulate fresh process
        _applied_patches.update(
            _load_applied_patches(self.project)
        ) if hasattr(_load_applied_patches, "__call__") else None
        t2 = self._tool()
        r2 = t2.apply(ps, [a])
        self.assertFalse(r2.ok, "replay must be rejected after restart")
        self.assertIn("already applied", r2.error)

    def test_persistence_failure_rolls_back(self):
        """If durable save fails, the patch is rejected and files rolled back."""
        # Import the real module to patch the save function.
        import amsdp_ai_factory.tools.patch_tool as patch_mod
        original = patch_mod._durably_save_applied_patches
        def failing_save(hashes, project_root):
            raise OSError("disk full (simulated)")
        patch_mod._durably_save_applied_patches = failing_save
        try:
            ps, a = self._valid_patch()
            t = self._tool()
            # _valid_patch already created one tool; clear ts
            r = t.apply(ps, [a])
            self.assertFalse(r.ok, "apply must fail when persistence fails")
            self.assertIn("rolled back", r.error)
            # File must be restored to original.
            self.assertEqual(
                (self.project / "backend" / "target.py").read_text(),
                "original\n",
            )
            # Replay record must NOT contain the hash.
            hashes = _load_applied_patches(self.project)
            self.assertNotIn(ps.patch_sha256, hashes)
            # No pending journal should remain.
            import glob
            self.assertEqual(glob.glob(str(self.project / "var" / "patch_journal" / "*.json")), [])
        finally:
            patch_mod._durably_save_applied_patches = original

    def test_crash_before_commit_rolls_back_on_restart(self):
        """A leftover journal (crash between apply and save) restores files."""
        # Manually create a backup snapshot and a pending journal.
        backup = self.snaps / "crashsnap"
        (backup / "backend").mkdir(parents=True)
        (backup / "backend" / "target.py").write_text("original\n")
        (self.project / "backend" / "target.py").write_text("modified\n")  # simulated crash state
        import glob, json
        jdir = self.project / "var" / "patch_journal"
        jdir.mkdir(parents=True)
        (jdir / "crashsnap.json").write_text(json.dumps({
            "patch_id": "crash-patch", "backup_root": str(backup),
            "files": [{"rel_path": "backend/target.py", "action": "modify"}],
        }))
        # New tool instance triggers reconciliation.
        t = self._tool()
        # File must be restored.
        self.assertEqual(
            (self.project / "backend" / "target.py").read_text(),
            "original\n",
        )
        # Journal removed.
        self.assertEqual(glob.glob(str(jdir / "*.json")), [])
