"""Agent tool binding - attach read-only registry tools to CrewAI agents.

M1 implementation: a CrewAI agent is built with ONLY the tools its agent
definition permits AND that the tool registry authorizes. This phase enables
only read-only inspection tools:

- ``repo_read``  (RepositoryReadTool)
- ``doc_reader`` (DocumentReaderTool)
- ``git_read``   (GitReadTool)

PatchTool / artifact_write / run_tests / shell-like tools are NOT attached.
``ToolRegistry.assert_allowed(agent_id, tool_id)`` is the single permission
authority. Attempting to attach an unauthorized tool raises
``ToolPermissionError`` (fail-closed).

M4 provenance: every tool call that the agent makes through the wrapped CrewAI
tools is recorded into an optional ``ToolOperationCollector`` so the executor
can surface it in the run record.
"""

from __future__ import annotations

import hashlib
import traceback
from datetime import datetime, timezone
from pathlib import Path

from crewai.tools import tool as crewai_tool

from amsdp_ai_factory.agents.models import AgentDefinition
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.runs.models import ToolOperationRecord
from amsdp_ai_factory.tools.document_reader import DocumentReaderTool
from amsdp_ai_factory.tools.git_read import GitReadTool
from amsdp_ai_factory.tools.repository_read import RepositoryReadTool
from amsdp_ai_factory.tools.tool_registry import (
    ToolPermissionError,
    ToolRegistry,
    build_default_registry,
)

_READ_ONLY_TOOL_IDS = frozenset({"repo_read", "doc_reader", "git_read"})


def _now():
    return datetime.now(timezone.utc)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bounded(s: str, limit: int = 200) -> str:
    s = s or ""
    return s[:limit] + ("..." if len(s) > limit else "")


class ToolOperationCollector:
    """Accumulates ToolOperationRecords from agent tool calls (M4)."""

    def __init__(self, agent_id: str = "", stage_id: str = "") -> None:
        self.agent_id = agent_id
        self.stage_id = stage_id
        self._records: list[ToolOperationRecord] = []

    def record(
        self,
        *,
        operation: str,
        target: str = "",
        ok: bool,
        error: str = "",
        output_summary: str = "",
        exit_code: int | None = None,
        evidence_refs: list[dict] | None = None,
    ) -> None:
        self._records.append(
            ToolOperationRecord(
                name=operation.split(".")[0] if "." in operation else operation,
                agent_id=self.agent_id,
                stage_id=self.stage_id,
                operation=operation,
                target=target,
                ok=ok,
                error=_bounded(error, 300),
                args_summary=_bounded(output_summary, 300),
                started_at=_now(),
                ended_at=_now(),
                exit_code=exit_code,
                evidence_refs=evidence_refs or [],
            )
        )

    def records(self) -> list[ToolOperationRecord]:
        return list(self._records)


class ToolBundle:
    """Instantiated read-only tools plus the wrapped CrewAI tools."""

    def __init__(self, repo_root: Path, tools: dict[str, list], collector: ToolOperationCollector) -> None:
        self.repo_root = repo_root
        self._tools = tools
        self.collector = collector

    def ids(self) -> list[str]:
        return sorted(self._tools)

    def count(self) -> int:
        return sum(len(v) for v in self._tools.values())

    def as_list(self) -> list:
        flat: list = []
        for tid in sorted(self._tools):
            flat.extend(self._tools[tid])
        return flat
# --- tool wrappers with M4 provenance --------------------------------------

def _wrap_repo_read(impl: RepositoryReadTool, c: ToolOperationCollector) -> list:
    @crewai_tool("repo_read_list_paths")
    def repo_read_list_paths(rel_dir: str = ""):
        """List files under a directory inside the project (read-only)."""
        try:
            r = impl.list_paths(rel_dir)
            c.record(operation="repo_read.list_paths", target=rel_dir or ".", ok=r.ok, error=r.error, output_summary=r.summary)
            return r.output or "(empty)"
        except Exception as e:
            c.record(operation="repo_read.list_paths", target=rel_dir or ".", ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("repo_read_read_text")
    def repo_read_read_text(rel_path: str, max_chars: int = 8000):
        """Read a file inside the project, bounded, read-only."""
        try:
            r = impl.read_text(rel_path, max_chars=max_chars)
            refs = [{"path": rel_path, "sha256": _sha256_text(r.output or "")}] if r.ok else []
            c.record(operation="repo_read.read_text", target=rel_path, ok=r.ok, error=r.error, output_summary=r.summary, evidence_refs=refs)
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="repo_read.read_text", target=rel_path, ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("repo_read_search")
    def repo_read_search(pattern: str, rel_dir: str = ""):
        """Search project files for a regex, read-only."""
        try:
            r = impl.search(pattern, rel_dir=rel_dir)
            c.record(operation="repo_read.search", target=rel_dir or ".", ok=r.ok, error=r.error, output_summary=f"{r.summary} pattern={_bounded(pattern)}")
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="repo_read.search", target=rel_dir or ".", ok=False, error=repr(e))
            return f"ERROR: {e}"

    return [repo_read_list_paths, repo_read_read_text, repo_read_search]


def _wrap_doc_reader(impl: DocumentReaderTool, c: ToolOperationCollector) -> list:
    @crewai_tool("doc_reader_list_roles")
    def doc_reader_list_roles():
        """List governed document roles available to read."""
        try:
            r = impl.list_roles()
            c.record(operation="doc_reader.list_roles", target="", ok=r.ok, error=r.error, output_summary=r.summary)
            return r.output or "(no documents configured)"
        except Exception as e:
            c.record(operation="doc_reader.list_roles", target="", ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("doc_reader_read")
    def doc_reader_read(role: str, max_chars: int = 12000):
        """Read a governed document by role, bounded, read-only."""
        try:
            r = impl.read(role, max_chars=max_chars)
            refs = [{"path": role, "sha256": _sha256_text(r.output or "")}] if r.ok else []
            c.record(operation="doc_reader.read", target=role, ok=r.ok, error=r.error, output_summary=r.summary, evidence_refs=refs)
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="doc_reader.read", target=role, ok=False, error=repr(e))
            return f"ERROR: {e}"

    return [doc_reader_list_roles, doc_reader_read]


def _wrap_git_read(impl: GitReadTool, c: ToolOperationCollector) -> list:
    @crewai_tool("git_read_status")
    def git_read_status():
        """Read-only git status."""
        try:
            r = impl.run("status")
            c.record(operation="git_read.status", target="", ok=r.ok, error=r.error, output_summary=r.summary, exit_code=r.exit_code)
            return r.output or "(clean)"
        except Exception as e:
            c.record(operation="git_read.status", target="", ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("git_read_log")
    def git_read_log(n: int = 10):
        """Read recent commits (read-only git log)."""
        try:
            r = impl.run("log", n=n)
            c.record(operation="git_read.log", target=f"n={n}", ok=r.ok, error=r.error, output_summary=r.summary, exit_code=r.exit_code)
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="git_read.log", target=f"n={n}", ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("git_read_branches")
    def git_read_branches():
        """List git branches (read-only)."""
        try:
            r = impl.run("branches")
            c.record(operation="git_read.branches", target="", ok=r.ok, error=r.error, output_summary=r.summary, exit_code=r.exit_code)
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="git_read.branches", target="", ok=False, error=repr(e))
            return f"ERROR: {e}"

    @crewai_tool("git_read_head")
    def git_read_head():
        """Read the current git HEAD (read-only)."""
        try:
            r = impl.run("head")
            c.record(operation="git_read.head", target="HEAD", ok=r.ok, error=r.error, output_summary=r.summary, exit_code=r.exit_code)
            return r.output if r.ok else f"ERROR: {r.error}"
        except Exception as e:
            c.record(operation="git_read.head", target="HEAD", ok=False, error=repr(e))
            return f"ERROR: {e}"

    return [git_read_status, git_read_log, git_read_branches, git_read_head]
def build_read_tool_bundle(
    agent: AgentDefinition,
    *,
    repo_root,
    loader: ContextLoader | None = None,
    registry: ToolRegistry | None = None,
    collector: ToolOperationCollector | None = None,
) -> ToolBundle:
    """Build the CrewAI read-only tool bundle for an agent (fail-closed).

    Every tool attached is (a) in the read-only allowlist, (b) declared in
    ``agent.permitted_tools``, and (c) authorized by ``ToolRegistry``. Patch
    application / write / shell tools are never attached here.
    """
    registry = registry or build_default_registry()
    root = Path(repo_root).resolve()
    loader = loader or ContextLoader(repo_root=root)
    c = collector or ToolOperationCollector(agent_id=agent.agent_id)

    repo_impl = RepositoryReadTool(root)
    doc_impl = DocumentReaderTool(loader)
    git_impl = GitReadTool(root)

    tools: dict[str, list] = {}
    for tool_id in agent.permitted_tools:
        if tool_id not in _READ_ONLY_TOOL_IDS:
            continue
        registry.assert_allowed(agent.agent_id, tool_id)

        if tool_id == "repo_read":
            tools[tool_id] = _wrap_repo_read(repo_impl, c)
        elif tool_id == "doc_reader":
            tools[tool_id] = _wrap_doc_reader(doc_impl, c)
        elif tool_id == "git_read":
            tools[tool_id] = _wrap_git_read(git_impl, c)

    return ToolBundle(repo_root=root, tools=tools, collector=c)
