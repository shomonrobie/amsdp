"""Agent registry: discoverable, validated registration of the eleven agents.

Registration enforces the stable ``A0X`` identifier format and uniqueness.
Cross-validation of tool bindings is provided separately by
``tools.tool_registry.validate_agent_tool_bindings`` so that an agent can
never reference an unregistered tool.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from amsdp_ai_factory.agents.models import (
    AGENT_ID_PATTERN,
    AgentDefinition,
    AgentSummary,
)


class AgentRegistryError(ValueError):
    """Raised for duplicate/unknown/invalid agent registrations."""


class AgentRegistry:
    """Stores and serves the AI Factory's approved agent catalogue."""

    def __init__(self, agents: Sequence[AgentDefinition] | None = None) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        if agents:
            for agent in agents:
                self.register(agent)

    def register(self, agent: AgentDefinition) -> AgentDefinition:
        """Register one agent. Rejects duplicates and malformed ids."""
        if not agent.agent_id or not re.fullmatch(AGENT_ID_PATTERN, agent.agent_id):
            raise AgentRegistryError(f"invalid agent id: {agent.agent_id!r}")
        if agent.agent_id in self._agents:
            raise AgentRegistryError(
                f"agent already registered: {agent.agent_id} ({agent.role})"
            )
        self._agents[agent.agent_id] = agent
        return agent

    # --- reads ----------------------------------------------------------------

    def get(self, agent_id: str) -> AgentDefinition | None:
        return self._agents.get(agent_id)

    def require(self, agent_id: str) -> AgentDefinition:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise AgentRegistryError(f"unknown agent id: {agent_id!r}")
        return agent

    def list(self) -> list[AgentDefinition]:
        """All registered agents, sorted by stable id."""
        return [self._agents[key] for key in sorted(self._agents)]

    def summaries(self) -> list[AgentSummary]:
        return [
            AgentSummary(
                agent_id=agent.agent_id,
                role=agent.role,
                model_config_id=agent.model_config_id,
                enabled=agent.enabled,
                tool_count=len(agent.permitted_tools),
            )
            for agent in self.list()
        ]

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents