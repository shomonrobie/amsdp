"""Workflow execution engine.

Orchestrates the ten approved workflows in controlled, ordered stages:

- validates workflow executability and task eligibility up front;
- runs agent stages through an executor (mock for tests, gated CrewAI live);
- runs tool stages directly after ``ToolRegistry.assert_allowed``;
- validates outputs and evidence before every handoff;
- enforces human gates through approval service records (never agent-approved);
- bounds retries, records everything in run records, and supports resume;
- never deploys and never runs unbounded loops.
"""

from __future__ import annotations

from pathlib import Path

from amsdp_ai_factory.approvals.service import ApprovalService
from amsdp_ai_factory.contracts.common import CheckResult
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.execution.models import ExecutionRequest
from amsdp_ai_factory.execution.run_context import RunContext
from amsdp_ai_factory.runs.models import (
    RunRecord,
    RunStatus,
    StageStatus,
    ToolOperationRecord,
)
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.artifact_store import ArtifactStore
from amsdp_ai_factory.tasks.lifecycle import is_allowed, transition
from amsdp_ai_factory.tasks.models import (
    FailureCategory,
    FailureRecord,
    Task,
    TaskStatus,
    now_utc,
)
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.tools.document_reader import DocumentReaderTool
from amsdp_ai_factory.tools.git_read import GitReadTool
from amsdp_ai_factory.tools.repository_read import RepositoryReadTool
from amsdp_ai_factory.tools.validators import DocLinkValidatorTool
from amsdp_ai_factory.tools.tool_registry import (
    ToolCallResult,
    ToolPermissionError,
    ToolRegistry,
    build_default_registry,
)
from amsdp_ai_factory.workflows.models import (
    StageDefinition,
    StageGate,
    StageKind,
    WorkflowDefinition,
    WorkflowStatus,
)
from amsdp_ai_factory.workflows.registry import WorkflowRegistry

MAX_DOC_CONTEXT_CHARS = 12000      # per governed document read into agent context
MAX_TOTAL_CONTEXT_CHARS = 24000    # total injected context bound across all docs


class WorkflowError(RuntimeError):
    """Base error for workflow engine failures."""


class WorkflowNotExecutableError(WorkflowError):
    """Raised when a workflow is not yet executable (planned/partial)."""


class WorkflowStageError(WorkflowError):
    """Raised when a stage exhausts its bounded retries."""


class WorkflowEngine:
    """The controlled orchestrator for approved workflows."""

    def __init__(
        self,
        *,
        task_registry: TaskRegistry,
        run_recorder: RunRecorder,
        workspace_root: Path,
        workflow_registry: WorkflowRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        approval_service: ApprovalService | None = None,
        max_stage_attempts: int = 2,
        repo_root: Path | None = None,
        context_loader: ContextLoader | None = None,
    ) -> None:
        self.task_registry = task_registry
        self.run_recorder = run_recorder
        self.workspace_root = Path(workspace_root)
        self.repo_root = Path(repo_root) if repo_root else Path(workspace_root)
        self.context_loader = context_loader or ContextLoader(repo_root=self.repo_root)
        self.workflow_registry = workflow_registry or WorkflowRegistry()
        self.tool_registry = tool_registry or build_default_registry()
        self.approval_service = approval_service or ApprovalService(
            task_registry, run_recorder
        )
        self.max_stage_attempts = max(1, max_stage_attempts)

    # --- entry points --------------------------------------------------------

    def run(self, task_id: str, workflow_id: str, executor) -> RunRecord:
        """Start a workflow run. Returns the (possibly paused) run record."""
        workflow = self.workflow_registry.require(workflow_id)
        if workflow.status != WorkflowStatus.EXECUTABLE:
            raise WorkflowNotExecutableError(
                f"workflow {workflow_id} is {workflow.status.value!r}; only "
                "executable workflows may run"
            )
        task = self._require_task(task_id)
        self._prepare_task(task, reason=f"start {workflow_id} {workflow.name}")
        # Provision the task workspace up front.
        ArtifactStore(self.workspace_root, task.task_id).ensure()
        # B: aggregate run-level agent participation for provenance.
        run_agents = []
        seen: set[str] = set()
        for stage in workflow.stages:
            for participant in self._stage_agent_participants(stage):
                if participant.agent_id not in seen:
                    seen.add(participant.agent_id)
                    run_agents.append(participant)
        run = self.run_recorder.new_run(
            task_id=task.task_id,
            workflow_id=workflow.workflow_id,
            environment="test",
            model_config_id=getattr(executor, "model_config_id", None),
            provider=getattr(executor, "provider", None),
            agents=run_agents,
        )
        run_context = RunContext()
        return self._advance_run(task, run, workflow, executor,
                                 run_context=run_context)

    def resume(self, task_id: str, executor=None) -> RunRecord:
        """Resume a paused or interrupted run for a task."""
        task = self._require_task(task_id)
        if task.status in (
            TaskStatus.CLOSED,
            TaskStatus.REJECTED,
            TaskStatus.CANCELLED,
        ):
            raise WorkflowError(
                f"task {task_id!r} is terminal ({task.status.value}); cannot resume"
            )
        runs = self.run_recorder.list(task_id=task_id)
        if not runs:
            raise WorkflowError(f"no runs exist for task {task_id!r}")
        run = self.run_recorder.get(runs[0].run_id)
        workflow = self.workflow_registry.require(run.workflow_id)
        if run.status == RunStatus.AWAITING_APPROVAL and self._at_gate(task):
            raise WorkflowError(
                f"run {run.run_id} is still awaiting human approval; decide first"
            )
        if executor is None and self._has_pending_agent_or_tool_stages(run, workflow):
            raise WorkflowError("an executor is required to resume incomplete stages")
        run_context = RunContext()
        return self._advance_run(task, run, workflow, executor, resume=True,
                                 run_context=run_context)
# --- pipeline ------------------------------------------------------------

    def _advance_run(
        self,
        task: Task,
        run: RunRecord,
        workflow: WorkflowDefinition,
        executor,
        resume: bool = False,
        run_context: RunContext | None = None,
    ) -> RunRecord:
        """Run pending stages in order; persist task/run on every mutation."""
        try:
            for stage in workflow.stages:
                stage_record = run.get_stage(stage.stage_id)
                if stage_record and stage_record.status == StageStatus.SUCCEEDED:
                    continue
                if stage.kind == StageKind.GATE:
                    if (
                        stage_record
                        and stage_record.status == StageStatus.AWAITING_APPROVAL
                        and not self._at_gate(task)
                    ):
                        self._complete_gate_stage(task, run, stage)
                        continue
                    self._enter_gate(task, run, stage)
                    # Re-read the persisted record: the gate finished the run.
                    return self.run_recorder.get(run.run_id)
                if stage.kind == StageKind.TOOL:
                    self._run_tool_stage(task, run, stage, executor)
                else:
                    self._run_agent_stage(task, run, stage, executor, run_context=run_context)
                if (
                    stage.advance_status is not None
                    and task.status != stage.advance_status
                ):
                    self._advance(
                        task, stage.advance_status, f"{stage.stage_id} complete"
                    )
            self.run_recorder.finish(run.run_id, status=RunStatus.SUCCEEDED)
        except WorkflowError:
            raise
        except Exception as exc:
            self._fail(task, run, str(exc))
            raise WorkflowStageError(f"workflow aborted: {exc}") from exc
        return self.run_recorder.get(run.run_id)

    def _run_agent_stage(
        self, task: Task, run: RunRecord, stage: StageDefinition, executor,
        run_context: RunContext | None = None,
    ) -> None:
        """Execute one agent stage with bounded retries and full recording."""
        self._preflight_stage_tools(stage)
        # B: record agent participation on the stage (provenance consistency).
        participants = self._stage_agent_participants(stage)
        stage_record = self.run_recorder.start_stage(
            run.run_id,
            name=stage.name,
            stage_id=stage.stage_id,
            agents=participants,
        )
        # Build context summary from previous stage outputs
        context_summary = ""
        if run_context is not None:
            context_summary = run_context.context_for(
                required_kinds=stage.required_input_kinds,
            )
        # M3: inject actual governed project documents (bounded, provenance-tracked).
        doc_context = self._load_document_context(task, stage)
        if doc_context:
            context_summary = (
                (doc_context + "\n\n" + context_summary)
                if context_summary
                else doc_context
            )
        # D: load applicable Agent Rules
        rules_context = self._load_agent_rules(task, stage)
        if rules_context:
            context_summary = (
                (context_summary + "\n\n" + rules_context)
                if context_summary
                else rules_context
            )
        request = ExecutionRequest(
            task_id=task.task_id,
            stage_id=stage.stage_id,
            agent_id=stage.agent_ids[0],
            workflow_id=run.workflow_id,
            expected_artifact_kind=(
                stage.expected_output_kinds[0] if stage.expected_output_kinds else ""
            ),
            context_summary=context_summary,
            focus_scope=self._assessment_focus(task),
            applied_rule_ids=list(
                self._select_agent_rules(task, stage)
            ) if stage.agent_ids else [],
            rules_text=rules_context or "",
        )
        store = ArtifactStore(self.workspace_root, task.task_id)
        attempt = 0
        last_error = "unknown failure"
        while attempt < self.max_stage_attempts:
            attempt += 1
            result = executor.execute(request, artifact_store=store)
            self.run_recorder.add_check(
                run.run_id, CheckResult(name="stage_output", ok=result.ok)
            )
            for check in result.checks:
                self.run_recorder.add_check(run.run_id, check)
            # M4: record inspected-file provenance surfaced by the executor.
            for op in getattr(result, "tool_operations", None) or []:
                op.stage_id = op.stage_id or stage.stage_id
                op.agent_id = op.agent_id or (stage.agent_ids[0] if stage.agent_ids else "")
                self.run_recorder.add_tool_operation(run.run_id, op)
            if result.output:
                for evidence in result.output.evidence:
                    self.run_recorder.add_artifact(run.run_id, str(evidence.path))
            if result.ok:
                # Record artifact in RunContext for downstream stages
                if run_context is not None and result.output:
                    rc_check = run_context.record(
                        stage_id=stage.stage_id,
                        agent_id=stage.agent_ids[0],
                        output=result.output,
                        expected_kinds=stage.expected_output_kinds,
                    )
                    self.run_recorder.add_check(run.run_id, rc_check)
                    # Record applied agent rules in RunContext
                    run_context.record_rules(
                        stage.stage_id, request.applied_rule_ids,
                    )
                self.run_recorder.update_stage(
                    run.run_id,
                    stage.stage_id,
                    status=StageStatus.SUCCEEDED,
                    ended_at=now_utc(),
                    retry_count=attempt - 1,
                )
                return
            last_error = result.error or "stage validation failed"
            task.failure_info.append(
                FailureRecord(
                    stage=stage.stage_id,
                    category=FailureCategory.TEST,
                    message=last_error,
                    retried=attempt < self.max_stage_attempts,
                )
            )
            self.task_registry.save(task)
        # Bounded retries exhausted: fail the run; downstream stages must stop.
        self.run_recorder.update_stage(
            run.run_id,
            stage.stage_id,
            status=StageStatus.FAILED,
            ended_at=now_utc(),
            error=last_error,
            retry_count=self.max_stage_attempts,
        )
        self._fail(task, run, last_error)
        raise WorkflowStageError(
            f"stage {stage.stage_id} failed after "
            f"{self.max_stage_attempts} attempt(s): {last_error}"
        )

# --- stages ------------------------------------------------------------

    def _load_document_context(self, task: Task, stage: StageDefinition) -> str:
        """Load governed project documents as bounded, provenance-tracked context.

        Respects ``required_input_kinds``/``expected_output_kinds`` by using the
        task's type for role selection and bounding the total injected size.
        Each loaded document is recorded as an inspection ToolOperationRecord so
        provenance (role, path, sha) is preserved. Nothing is fabricated: missing
        documents are reported as unavailable, not invented.
        """
        if stage.kind != StageKind.AGENT:
            return ""
        if not stage.expected_output_kinds:
            return ""
        task_type = task.task_type or None
        docs = self.context_loader.load_for_task(task_type, max_chars=MAX_DOC_CONTEXT_CHARS)
        if not docs:
            return ""
        parts: list[str] = []
        for doc in docs:
            self.run_recorder.add_tool_operation(
                run_id=task.task_id and self._current_run_id(task),
                operation=self._doc_operation(doc),
            )
            record = doc.record
            header = f"[{record.role}] {record.rel_path} (sha256={record.sha256})"
            parts.append(f"{header}\n{doc.text}")
        return "\n\n".join(parts)[: MAX_TOTAL_CONTEXT_CHARS]

    def _current_run_id(self, task: Task) -> str | None:
        runs = self.run_recorder.list(task_id=task.task_id, limit=1)
        return runs[0].run_id if runs else None

    def _doc_operation(self, doc) -> ToolOperationRecord:
        record = doc.record
        return ToolOperationRecord(
            name="doc_reader",
            operation="doc_reader.read",
            agent_id="",
            stage_id="context_loader",
            target=record.rel_path,
            ok=True,
            args_summary=f"{record.role}: {len(doc.text)} chars",
            evidence_refs=[{"path": str(record.rel_path), "sha256": record.sha256 or ""}],
            working_dir=str(self.repo_root),
        )

    def _run_tool_stage(
        self, task: Task, run: RunRecord, stage: StageDefinition, executor
    ) -> None:
        """Engine-run tool stage: assert_allowed, dispatch, record provenance.

        Dispatch is registry-driven: the tool must be registered and enabled in
        ``self.tool_registry`` and the ``via_agent_id`` must be authorized.
        Unlike the earlier special-case for ``doc_link_validator``, this path
        can run any registered read-only tool that the engine provides an
        implementation for (repo_read, doc_reader, git_read, doc_link_validator).
        """
        tool_id = stage.tool_stage_tool_id or ""
        via_agent = stage.via_agent_id or "?"
        # Permission boundary checked immediately before execution.
        try:
            self.tool_registry.assert_allowed(via_agent, tool_id)
        except ToolPermissionError as exc:
            self.run_recorder.add_tool_operation(
                run.run_id,
                ToolOperationRecord(
                    name=tool_id,
                    agent_id=via_agent,
                    stage_id=stage.stage_id,
                    operation=f"{tool_id}.run",
                    ok=False,
                    error=f"denied: {exc}",
                    started_at=now_utc(),
                    ended_at=now_utc(),
                    working_dir=str(self.repo_root),
                ),
            )
            self.run_recorder.update_stage(
                run.run_id, stage.stage_id, status=StageStatus.FAILED,
                ended_at=now_utc(), error=str(exc),
            )
            self._fail(task, run, f"tool access denied: {exc}")
            raise WorkflowStageError(
                f"tool stage {stage.stage_id} denied for {via_agent}: {exc}"
            ) from exc
        self.run_recorder.start_stage(
            run.run_id,
            name=stage.name,
            stage_id=stage.stage_id,
            agents=self._stage_agent_participants(stage),
        )
        store = ArtifactStore(self.workspace_root, task.task_id)
        started = now_utc()
        op_record = ToolOperationRecord(
            name=tool_id,
            agent_id=via_agent,
            stage_id=stage.stage_id,
            operation=f"{tool_id}.run",
            started_at=started,
            working_dir=str(self.repo_root),
        )
        try:
            # Registry-driven dispatch: build the impl and run the default op.
            result = self._execute_registered_tool(tool_id, task, store)
            op_record.ok = result.ok
            op_record.exit_code = 0 if result.ok else 1
            op_record.ended_at = now_utc()
            op_record.target = result.summary
            if not result.ok:
                op_record.error = result.error
        except Exception as exc:
            op_record.ok = False
            op_record.exit_code = 1
            op_record.ended_at = now_utc()
            op_record.error = str(exc)
            self.run_recorder.add_tool_operation(run.run_id, op_record)
            self.run_recorder.update_stage(
                run.run_id,
                stage.stage_id,
                status=StageStatus.FAILED,
                ended_at=now_utc(),
                error=str(exc),
            )
            self._fail(task, run, str(exc))
            raise WorkflowStageError(
                f"tool stage {stage.stage_id} failed: {exc}"
            ) from exc
        self.run_recorder.add_tool_operation(run.run_id, op_record)
        self.run_recorder.add_check(
            run.run_id, CheckResult(name=f"tool:{tool_id}", ok=result.ok)
        )
        self.run_recorder.update_stage(
            run.run_id,
            stage.stage_id,
            status=StageStatus.SUCCEEDED if result.ok else StageStatus.FAILED,
            ended_at=now_utc(),
            error=result.error,
        )
        if not result.ok:
            self._fail(task, run, result.error)
            raise WorkflowStageError(
                f"tool stage {stage.stage_id} failed: {result.error}"
            )

    def _execute_registered_tool(
        self, tool_id: str, task: Task, store: ArtifactStore
    ) -> ToolCallResult:
        """Build a registered read-only tool and run its default operation."""
        if tool_id == "repo_read":
            return RepositoryReadTool(self.repo_root).list_paths(rel_dir="", max_items=400)
        if tool_id == "doc_reader":
            docs = self.context_loader.load_for_task(
                task.task_type or None, max_chars=MAX_DOC_CONTEXT_CHARS
            )
            lines = [
                f"{d.role} {d.record.rel_path} ({len(d.text)} chars)"
                for d in docs
            ]
            output = "\n".join(lines) if lines else "(no governed documents available)"
            return ToolCallResult(ok=True, tool_id=tool_id, summary=f"{len(lines)} doc(s)", output=output)
        if tool_id == "git_read":
            return GitReadTool(self.repo_root).run("status")
        if tool_id == "doc_link_validator":
            return DocLinkValidatorTool(store.task_workspace()).run()
        raise WorkflowError(
            f"no engine implementation for registered tool {tool_id!r}"
        )

    def _enter_gate(self, task: Task, run: RunRecord, stage: StageDefinition) -> None:
        """Move the task into a human gate and pause the run."""
        if stage.advance_status is not None and is_allowed(
            task.status, stage.advance_status
        ):
            self._advance(task, stage.advance_status, f"entering gate {stage.gate.value}")
        self.run_recorder.start_stage(
            run.run_id, name=stage.name, stage_id=stage.stage_id
        )
        self.run_recorder.update_stage(
            run.run_id, stage.stage_id, status=StageStatus.AWAITING_APPROVAL
        )
        self.run_recorder.finish(run.run_id, status=RunStatus.AWAITING_APPROVAL)

    def _complete_gate_stage(
            self, task: Task, run: RunRecord, stage: StageDefinition
        ) -> None:
        """Mark a gate stage satisfied after the task left its gate."""
        approval_id = (
            task.approval.decisions[-1].decision_id if task.approval.decisions else None
        )
        self.run_recorder.update_stage(
            run.run_id,
            stage.stage_id,
            status=StageStatus.SUCCEEDED,
            ended_at=now_utc(),
            approval_id=approval_id,
        )

    def _stage_agent_participants(self, stage: StageDefinition) -> list:
        """AgentParticipation records for the stage's agent ids."""
        from amsdp_ai_factory.runs.models import AgentParticipation
        from amsdp_ai_factory.agents.definitions import AGENT_INDEX

        participants = []
        for agent_id in stage.agent_ids:
            definition = AGENT_INDEX.get(agent_id)
            participants.append(
                AgentParticipation(
                    agent_id=agent_id,
                    role=definition.role if definition else "",
                    model_config_id=(
                        getattr(definition, "model_config_id", None)
                        if definition else None
                    ),
                )
            )
        return participants

    def _assessment_focus(self, task: Task) -> str:
        """Emit an explicit focus directive for an assessment-style task.

        Directs agents to inspect the application implementation (backend,
        frontend, database, APIs, tests, deployment) and to not treat AILI's
        own framework or documentation claims as evidence of implementation.
        """
        if (task.task_type or "").lower() not in ("assessment", "gap_assessment"):
            return ""
        return (
            "ASSESSMENT FOCUS: Inspect the AMSDP application implementation "
            "itself (backend/ services and API routes; frontend/ pages and "
            "components; database models and migrations; auth/RBAC; patient, "
            "doctor, scheduling, appointment, queue, audit features; and "
            "tests/deployment configuration). Do NOT count AILI's own "
            "framework source (ai_factory/) as application functionality. Do "
            "NOT claim a feature is implemented merely because project "
            "documentation or prior reports describe it - verify against "
            "actual code, migrations, and tests, and report 'unverifiable' "
            "where evidence is missing."
        )

    def _select_agent_rules(self, task: Task, stage) -> set[str]:
        """Select applicable agent rule IDs for this stage."""
        from amsdp_ai_factory.rules.mapping import select_rule_ids

        agent_id = stage.agent_ids[0] if stage.agent_ids else None
        task_type = task.task_type if task else None
        return select_rule_ids(agent_id=agent_id, task_type=task_type)

    def _load_agent_rules(self, task: Task, stage) -> str:
        """Load applicable Agent Rules text for this stage.

        Returns concatenated rule text, or '' if no rules apply or the rules
        directory is not found. When rules cannot be loaded, the limitation
        is recorded in the returned text.
        """
        rule_ids = self._select_agent_rules(task, stage)
        if not rule_ids:
            return ""

        from pathlib import Path
        from amsdp_ai_factory.rules.registry import resolve_rule_text

        # Resolve the agent-rules directory relative to the repo root.
        rules_dir = self.repo_root / "ai_factory" / "docs" / "agent-rules"
        if not rules_dir.is_dir():
            rules_dir = self.repo_root / "docs" / "agent-rules"
        if not rules_dir.is_dir():
            ct_rules = Path.home() / "ct_93d5cdd" / "docs" / "agent-rules"
            if ct_rules.is_dir():
                rules_dir = ct_rules
            else:
                return (
                    "[Agent Rules not loaded \u2014 rules directory not found. "
                    f"Searched: repo_root/ai_factory/docs/agent-rules, "
                    f"repo_root/docs/agent-rules, {ct_rules}]"
                )

        parts: list[str] = []
        for rule_id in sorted(rule_ids):
            text = resolve_rule_text(rules_dir, rule_id)
            if text is None:
                parts.append(
                    f"\n[Agent Rule '{rule_id}' expected but NOT FOUND \u2014 "
                    f"proceed without it]\n"
                )
                continue
            parts.append(f"\n--- Agent Rule: {rule_id} ---\n{text}")

        return "\n".join(parts)

    def _preflight_stage_tools(self, stage: StageDefinition) -> None:
        """Verify every tool a stage agent may use is bound and, when enabled,
        fully permitted. Planned tools are bound-checked (execution remains
        denied until enabled)."""
        from amsdp_ai_factory.agents.definitions import AGENT_INDEX

        for agent_id in stage.agent_ids:
            agent = AGENT_INDEX.get(agent_id)
            if agent is None:
                raise WorkflowError(f"stage references unknown agent {agent_id!r}")
            for tool_id in agent.permitted_tools:
                tool = self.tool_registry.get(tool_id)
                if tool is None:
                    raise WorkflowError(
                        f"agent {agent_id} declares unknown tool {tool_id!r}"
                    )
                if tool.enabled:
                    self.tool_registry.assert_allowed(agent_id, tool_id)
                else:
                    self.tool_registry.assert_binding(agent_id, tool_id)

    # --- task helpers --------------------------------------------------------

    def _prepare_task(self, task: Task, reason: str) -> None:
        """Advance a fresh task through intake and into analysis."""
        for status in (
            TaskStatus.INTAKE_VALIDATION,
            TaskStatus.CONTEXT_VALIDATION,
            TaskStatus.READY_FOR_ANALYSIS,
            TaskStatus.ANALYSIS,
        ):
            if task.status == status or not is_allowed(task.status, status):
                continue
            self._advance(task, status, reason)
        self.task_registry.save(task)

    def _advance(self, task: Task, to_status: TaskStatus, reason: str) -> Task:
        self.task_registry.save(
            transition(task, to_status, actor="orchestrator", reason=reason)
        )
        return task

    def _fail(self, task: Task, run: RunRecord, message: str) -> None:
        """Escalate failure: task to FAILED/BLOCKED when the lifecycle allows."""
        task.escalation_notes.append(message)
        if is_allowed(task.status, TaskStatus.FAILED):
            self._advance(task, TaskStatus.FAILED, "workflow stage failure")
        elif is_allowed(task.status, TaskStatus.BLOCKED):
            self._advance(task, TaskStatus.BLOCKED, "workflow stage failure")
        self.task_registry.save(task)
        self.run_recorder.add_error(run.run_id, message)
        self.run_recorder.finish(run.run_id, status=RunStatus.FAILED)

    def _require_task(self, task_id: str) -> Task:
        task = self.task_registry.get(task_id)
        if task is None:
            raise WorkflowError(f"unknown task: {task_id!r}")
        return task

    @staticmethod
    def _at_gate(task: Task) -> bool:
        return task.status in (
            TaskStatus.HUMAN_DESIGN_APPROVAL,
            TaskStatus.HUMAN_REVIEW,
            TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
        )

    def _task_gate_statuses(self, stage: StageDefinition) -> tuple[TaskStatus, ...]:
        return tuple(
            status
            for status in (
                TaskStatus.HUMAN_DESIGN_APPROVAL,
                TaskStatus.HUMAN_REVIEW,
                TaskStatus.AWAITING_DEPLOYMENT_APPROVAL,
            )
            if stage.gate.value == status.value
        )

    def _has_pending_agent_or_tool_stages(
        self, run: RunRecord, workflow: WorkflowDefinition
    ) -> bool:
        for stage in workflow.stages:
            if stage.kind == StageKind.GATE:
                continue
            record = run.get_stage(stage.stage_id)
            if record is None or record.status in (
                StageStatus.PENDING,
                StageStatus.RUNNING,
            ):
                return True
        return False