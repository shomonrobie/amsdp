"""Workflow registry: the ten approved workflows plus integrity checks.

Validates that every stage references known agents, known tools that are
bound to the stage's agents, and artifact kinds that exist in the output
contract catalogue — so definitions stay in lockstep with Phases 1-3.
"""

from __future__ import annotations

from collections.abc import Sequence

from amsdp_ai_factory.agents.definitions import AGENT_INDEX
from amsdp_ai_factory.contracts.outputs import ARTIFACT_MODELS, ArtifactKind
from amsdp_ai_factory.tools.tool_registry import (
    ToolRegistry,
    build_default_registry,
)
from amsdp_ai_factory.workflows.definitions import DEFAULT_WORKFLOWS
from amsdp_ai_factory.workflows.models import (
    WorkflowDefinition,
    WorkflowStatus,
)


class WorkflowRegistryError(ValueError):
    """Raised for unknown/invalid workflow registrations."""


class WorkflowRegistry:
    """Registry of approved workflow definitions."""

    def __init__(
        self, workflows: Sequence[WorkflowDefinition] | None = None
    ) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}
        self.tool_registry = build_default_registry()
        for workflow in workflows or DEFAULT_WORKFLOWS:
            self.register(workflow)

    def register(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        if workflow.workflow_id in self._workflows:
            raise WorkflowRegistryError(
                f"workflow already registered: {workflow.workflow_id}"
            )
        self._workflows[workflow.workflow_id] = workflow
        return workflow

    # --- reads --------------------------------------------------------------

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def require(self, workflow_id: str) -> WorkflowDefinition:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowRegistryError(f"unknown workflow: {workflow_id!r}")
        return workflow

    def list(self) -> list[WorkflowDefinition]:
        return [self._workflows[key] for key in sorted(self._workflows)]

    def executable(self) -> list[WorkflowDefinition]:
        return [
            workflow
            for workflow in self.list()
            if workflow.status == WorkflowStatus.EXECUTABLE
        ]

    # --- integrity ----------------------------------------------------------

    def validate(self) -> list[str]:
        """Return a list of problems; empty means every workflow is consistent."""
        errors: list[str] = []
        known_agents = set(AGENT_INDEX)
        known_tools = {tool.tool_id: tool for tool in self.tool_registry.list()}
        known_kinds = {kind.value for kind in ArtifactKind}

        for workflow in self._workflows.values():
            seen_stage_ids: set[str] = set()
            for stage in workflow.stages:
                if stage.stage_id in seen_stage_ids:
                    errors.append(
                        f"{workflow.workflow_id}: duplicate stage {stage.stage_id!r}"
                    )
                seen_stage_ids.add(stage.stage_id)
                unknown_agents = set(stage.agent_ids) - known_agents
                if unknown_agents:
                    errors.append(
                        f"{workflow.workflow_id}/{stage.stage_id}: unknown agents {sorted(unknown_agents)}"
                    )
                for kind in stage.expected_output_kinds:
                    if kind not in known_kinds:
                        errors.append(
                            f"{workflow.workflow_id}/{stage.stage_id}: unknown artifact kind {kind!r}"
                        )
                if stage.kind.value == "tool":
                    if stage.tool_stage_tool_id not in known_tools:
                        errors.append(
                            f"{workflow.workflow_id}/{stage.stage_id}: unknown tool "
                            f"{stage.tool_stage_tool_id!r}"
                        )
                    elif stage.via_agent_id not in known_tools[
                        stage.tool_stage_tool_id
                    ].allowed_agents:
                        errors.append(
                            f"{workflow.workflow_id}/{stage.stage_id}: via_agent "
                            f"{stage.via_agent_id!r} is not bound to tool "
                            f"{stage.tool_stage_tool_id!r}"
                        )
        return errors


def validate_registry_integrity(registry: WorkflowRegistry) -> list[str]:
    return registry.validate()