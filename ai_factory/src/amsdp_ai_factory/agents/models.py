"""Agent models and execution results.

Each ``AgentDefinition`` is derived from the AI Agent Specification V1.0
sections 6-16. Definitions are data, not executable logic: the workflow
engine (Phase 4) interprets them, and the tool registry grants exactly the
``permitted_tools`` each definition declares.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

AGENT_ID_PATTERN = r"^A\d{2}$"


class AgentDefinition(BaseModel):
    """A specialist agent exactly as specified in the AI Agent Specification.

    ``permitted_tools`` names tools registered in the tool registry
    (``tools.tool_registry``); ``write_prefix`` scopes artifact writes to a
    subpath of the task workspace.
    """

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str
    mission: str
    goal: str
    responsibilities: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    permitted_tools: list[str] = Field(default_factory=list)
    write_prefix: str | None = None
    prohibited_actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    handoff: str = ""
    model_config_id: str = "default"
    enabled: bool = True

    @field_validator("agent_id")
    @classmethod
    def _agent_id_format(cls, value: str) -> str:
        if not re.fullmatch(AGENT_ID_PATTERN, value):
            raise ValueError(f"agent_id {value!r} must match {AGENT_ID_PATTERN!r}")
        return value

    @field_validator("role")
    @classmethod
    def _role_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("role must not be empty")
        return value.strip()


class AgentSummary(BaseModel):
    """Lightweight registry listing view."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str
    model_config_id: str = "default"
    enabled: bool = True
    tool_count: int = 0