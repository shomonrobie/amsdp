"""AILI command-line interface.

Core commands only: environment checks, registries, task lifecycle, safe
stub workflow runs, approvals, and resume. Live workflow execution requires
explicit configuration and ``AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1``; the
default stub mode needs nothing.
"""

from __future__ import annotations

import typer

from amsdp_ai_factory import VERSION
from amsdp_ai_factory.agents.definitions import ALL_AGENTS
from amsdp_ai_factory.agents.registry import AgentRegistry
from amsdp_ai_factory.approvals.service import ApprovalService
from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.context.loader import ContextLoader
from amsdp_ai_factory.execution.live import CrewAIExecutor
from amsdp_ai_factory.execution.mock import MockAgentExecutor
from amsdp_ai_factory.execution.stub_handler import build_stub_handler
from amsdp_ai_factory.runs.recorder import RunRecorder
from amsdp_ai_factory.tasks.models import ApprovalDecision, Task
from amsdp_ai_factory.tasks.registry import TaskRegistry
from amsdp_ai_factory.validation.configuration import validate_environment
from amsdp_ai_factory.workflows.engine import (
    WorkflowEngine,
    WorkflowNotExecutableError,
)
from amsdp_ai_factory.workflows.registry import WorkflowRegistry

app = typer.Typer(help="AMSDP AI Factory (AILI) — development-time orchestration.")


def _settings() -> FactorySettings:
    return FactorySettings()


def _engine(mode: str):
    settings = _settings()
    registry = TaskRegistry(settings.task_store_path())
    recorder = RunRecorder(settings.run_store_path())
    engine = WorkflowEngine(
        task_registry=registry,
        run_recorder=recorder,
        workspace_root=settings.workspace_path(),
        workflow_registry=WorkflowRegistry(),
        approval_service=ApprovalService(registry, recorder),
        max_stage_attempts=settings.default_max_retries,
        repo_root=settings.effective_repo_root(),
    )
    if mode == "live":
        executor = CrewAIExecutor(settings)
    else:
        executor = MockAgentExecutor(handler=build_stub_handler())
    return registry, recorder, engine, executor, settings


@app.command()
def version() -> None:
    """Print the AILI factory version."""
    typer.echo(f"AILI (amsdp_ai_factory) version {VERSION}")


@app.command()
def doctor() -> None:
    """Validate the environment and governing documents."""
    settings = _settings()
    report = validate_environment(settings)
    typer.echo(report.as_text())
    # Live execution readiness check
    if settings.model_provider and settings.model_id and os.environ.get("AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED") == "1":
        typer.echo("[INFO] live_execution: ready (configured and authorized)")
    elif settings.model_provider and settings.model_id:
        typer.echo("[WARN] live_execution: configured but NOT authorized (set AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1)")
    else:
        typer.echo("[INFO] live_execution: not configured (stub/mock mode only)")
    if not report.ok:
        raise typer.Exit(code=2)


@app.command()
def docs_status() -> None:
    """List governed documents and their detection status."""
    loader = ContextLoader()
    for line in loader.registry.report_lines(loader.scan()):
        typer.echo(line)


@app.command()
def agents() -> None:
    """List the eleven registered specialist agents."""
    registry = AgentRegistry(ALL_AGENTS)
    for summary in registry.summaries():
        typer.echo(
            f"{summary.agent_id}  {summary.role:<28} tools={summary.tool_count} "
            f"(enabled={summary.enabled})"
        )


@app.command()
def workflows(
    workflow_id: str | None = typer.Argument(
        default=None, help="e.g. WF-01"
    ),
) -> None:
    """List the ten workflows or show one in detail."""
    registry = WorkflowRegistry()
    if workflow_id:
        definition = registry.require(workflow_id)
        typer.echo(
            f"{definition.workflow_id} {definition.name} [{definition.status.value}]"
        )
        typer.echo(definition.purpose)
        for stage in definition.stages:
            typer.echo(
                f"  {stage.stage_id}: {stage.name} ({stage.kind.value}) -> "
                f"{stage.expected_output_kinds or '-'}"
            )
        return
    for definition in registry.list():
        typer.echo(
            f"{definition.workflow_id}  {definition.name:<28} "
            f"status={definition.status.value:<10} stages={len(definition.stages)}"
        )


@app.command()
def task_new(
    title: str = typer.Option(..., prompt=True),
    workflow_id: str | None = typer.Option(default=None, help="e.g. WF-01"),
    task_type: str | None = typer.Option(default=None),
    description: str = typer.Option(default=""),
) -> None:
    """Register a new task in the task registry."""
    registry = TaskRegistry(_settings().task_store_path())
    task = registry.create(
        Task(
            title=title,
            workflow_id=workflow_id,
            task_type=task_type,
            description=description,
        )
    )
    typer.echo(f"created task {task.task_id} status={task.status.value}")


@app.command()
def task_list(status: str | None = None) -> None:
    """List registered tasks (optionally filtered by status)."""
    registry = TaskRegistry(_settings().task_store_path())
    for summary in registry.list(status=status):
        typer.echo(
            f"{summary.task_id}  {summary.title[:44]:<44} {summary.status.value}"
        )


@app.command()
def task_show(task_id: str) -> None:
    """Show one task record."""
    task = TaskRegistry(_settings().task_store_path()).get(task_id)
    if task is None:
        typer.echo(f"unknown task {task_id!r}", err=True)
        raise typer.Exit(code=1)
@app.command()
def run_workflow(
    task_id: str,
    workflow_id: str,
    mode: str = typer.Option("stub", help="stub (default) or live"),
) -> None:
    """Run a workflow for a task. Runs pause at human approval gates."""
    registry, recorder, engine, executor, _ = _engine(mode)
    try:
        run = engine.run(task_id, workflow_id, executor)
    except WorkflowNotExecutableError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2)
    except Exception as exc:
        typer.echo(f"run failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"run {run.run_id} status={run.status.value}")
    if run.status.value == "awaiting_approval":
        typer.echo(
            "paused at a human gate; decide with: approve --task-id <id> "
            "--decision approved|rejected|changes_requested"
        )


@app.command()
def approve(
    task_id: str,
    decision: str = typer.Argument(...),
    actor: str = typer.Option("project_owner"),
    rationale: str = typer.Option(""),
    run_id: str | None = typer.Option(default=None),
) -> None:
    """Record a human decision on a gated task."""
    registry, recorder, engine, _, _ = _engine("stub")
    try:
        choice = ApprovalDecision(decision)
    except ValueError:
        typer.echo(f"invalid decision {decision!r}", err=True)
        raise typer.Exit(code=2)
    task = engine.approval_service.decide(
        task_id, choice, actor=actor, rationale=rationale, run_id=run_id
    )
    typer.echo(f"task {task_id} -> {task.status.value}")


@app.command()
def resume(
    task_id: str, mode: str = typer.Option("stub", help="stub (default) or live")
) -> None:
    """Resume a paused/interrupted run after its gate was decided."""
    try:
        registry, recorder, engine, executor, _ = _engine(mode)
        run = engine.resume(task_id, executor=executor)
    except Exception as exc:
        typer.echo(f"resume failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"run {run.run_id} status={run.status.value}")


@app.command()
def run_status(run_id: str) -> None:
    """Show one run record."""
    run = RunRecorder(_settings().run_store_path()).get(run_id)
    if run is None:
        typer.echo(f"unknown run {run_id!r}", err=True)
        raise typer.Exit(code=1)
    typer.echo(
        f"run {run.run_id} task={run.task_id} workflow={run.workflow_id} status={run.status.value}"
    )
    for stage in run.stages:
        typer.echo(f"  {stage.stage_id}: {stage.name} status={stage.status.value}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
    typer.echo(task.model_dump_json(indent=2))