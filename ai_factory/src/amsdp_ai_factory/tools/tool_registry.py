"""Tool registry with default-deny permission enforcement.

Tools are the controlled interface between agents and their environment
(AI Factory Architecture V1.0 section 8). A tool is granted only to the
agents the agent specification authorizes; anything else is denied in code.

``enabled=False`` marks tools that are declared and bound for the approved
matrix but not yet implemented (Phase 4): calling them through the registry
is always denied with an explicit message.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from amsdp_ai_factory.agents.models import AgentDefinition
from amsdp_ai_factory.tasks.models import ArtifactRecord


class ToolCategory(str, Enum):
    READ = "read"                # read-only repository/document inspection
    WRITE = "write"              # workspace-bounded artifact writing
    EXECUTE = "execute"          # bounded local test/build execution
    VALIDATION = "validation"    # schema/contract type validation
    SECURITY = "security"        # static analysis and secret scanning
    DB = "db"                    # disposable local database
    DEPLOY = "deploy"            # deployment-adjacent (never granted)
    NETWORK = "network"          # network access (never granted)


class ToolDefinition(BaseModel):
    """One registered tool plus its least-privilege binding."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str
    name: str
    description: str
    category: ToolCategory
    enabled: bool = False
    status: str = "planned"  # "active" | "planned" | "revoked"
    allowed_agents: set[str] = Field(default_factory=set)


class ToolCallResult(BaseModel):
    """Structured result returned by a tool execution."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    tool_id: str
    summary: str = ""
    output: str | None = None
    command: str | None = None
    exit_code: int | None = None
    artifact: ArtifactRecord | None = None
    error: str = ""


class ToolPermissionError(PermissionError):
    """Raised when an agent attempts a tool it is not entitled to use."""
class ToolRegistry:
    """Default-deny tool catalogue and permission authority."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> ToolDefinition:
        if definition.tool_id in self._tools:
            raise ValueError(f"tool already registered: {definition.tool_id}")
        self._tools[definition.tool_id] = definition
        return definition

    def get(self, tool_id: str) -> ToolDefinition | None:
        return self._tools.get(tool_id)

    def require(self, tool_id: str) -> ToolDefinition:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolPermissionError(f"unknown tool: {tool_id!r}")
        return tool

    def list(self) -> list[ToolDefinition]:
        return [self._tools[key] for key in sorted(self._tools)]

    def tool_ids_for(self, agent_id: str) -> list[str]:
        """All tool ids (including planned, disabled ones) bound to an agent."""
        return sorted(
            tool_id
            for tool_id, definition in self._tools.items()
            if agent_id in definition.allowed_agents
        )

    def assert_binding(self, agent_id: str, tool_id: str) -> ToolDefinition:
        """Verify an agent is bound to a declared tool (regardless of enablement).

        Planned (declared-but-disabled) tools are still binding-checked so the
        permission matrix holds; their *execution* is separately denied by
        ``assert_allowed`` until enabled.
        """
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolPermissionError(f"unknown tool: {tool_id!r}")
        if agent_id not in tool.allowed_agents:
            raise ToolPermissionError(
                f"agent {agent_id!r} is not bound to tool {tool_id!r}; denied by default."
            )
        return tool

    def assert_allowed(self, agent_id: str, tool_id: str) -> ToolDefinition:
        """Enforce default-deny before any tool executes. Raises on denial."""
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolPermissionError(f"unknown tool: {tool_id!r}")
        if not tool.enabled:
            if tool.status == "planned":
                raise ToolPermissionError(
                    f"tool {tool_id!r} is declared but not yet enabled for this MVP "
                    f"(status={tool.status!r}); the operation is denied."
                )
            raise ToolPermissionError(
                f"tool {tool_id!r} is disabled (status={tool.status!r}); denied."
            )
        if agent_id not in tool.allowed_agents:
            raise ToolPermissionError(
                f"agent {agent_id!r} is not bound to tool {tool_id!r}; denied by default."
            )
        return tool
def register_defaults() -> ToolRegistry:
    """Build the approved tool catalogue for the MVP.

    Active tools: repo_read, doc_reader, git_read, artifact_write,
    run_tests. The remaining approved tools are declared and bound for the
    matrix but kept disabled (planned) until their implementations are
    approved in a later phase — default-deny is preserved.
    """
    registry = ToolRegistry()
    all_agents = {f"A{i:02d}" for i in range(1, 12)}

    registry.register(
        ToolDefinition(
            tool_id="repo_read",
            name="Repository read",
            description="List, read, and search repository files (read-only).",
            category=ToolCategory.READ,
            enabled=True,
            status="active",
            allowed_agents=set(all_agents),
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="doc_reader",
            name="Governed document reader",
            description="Read approved governing documents (read-only).",
            category=ToolCategory.READ,
            enabled=True,
            status="active",
            allowed_agents=set(all_agents),
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="git_read",
            name="Git read",
            description="Read-only git status/diff/log/branch inspection.",
            category=ToolCategory.READ,
            enabled=True,
            status="active",
            allowed_agents={"A02", "A03", "A05", "A06", "A07", "A08", "A10", "A11"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="artifact_write",
            name="Artifact write",
            description="Write artifact files inside the task workspace scope.",
            category=ToolCategory.WRITE,
            enabled=True,
            status="active",
            allowed_agents=set(all_agents),
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="run_tests",
            name="Bounded test runner",
            description="Execute allowlisted local test/check commands.",
            category=ToolCategory.EXECUTE,
            enabled=True,
            status="active",
            allowed_agents={"A06", "A07", "A08", "A10"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="architecture_validator",
            name="Architecture validator",
            description="Structural checks for architecture proposals.",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A02", "A03"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="doc_link_validator",
            name="Docs link validator",
            description="Validate Markdown links in the workspace.",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A11"},
        )
    )
    # Phase 5: six planned tools become active ----------------------------
    registry.register(
        ToolDefinition(
            tool_id="static_analysis",
            name="Static analysis",
            description="Pattern-based code analysis for dangerous constructs.",
            category=ToolCategory.SECURITY,
            enabled=True,
            status="active",
            allowed_agents={"A06", "A09"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="secret_scan",
            name="Secret scanner",
            description="Regex-based credential pattern detection.",
            category=ToolCategory.SECURITY,
            enabled=True,
            status="active",
            allowed_agents={"A09"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="disposable_db",
            name="Disposable local database",
            description="Run SQL against in-memory SQLite for structure validation.",
            category=ToolCategory.DB,
            enabled=True,
            status="active",
            allowed_agents={"A04", "A06", "A08"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="migration_validator",
            name="Migration validator",
            description="Check SQL migration forward/backward structure and tenant isolation.",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A04"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="contract_test_tool",
            name="Contract test tool",
            description="Compare provider and consumer API contract JSON files for compatibility.",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A05", "A08"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="ci_config_validator",
            name="CI config validator",
            description="Validate CI workflow file structure (GitHub Actions).",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A10"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="openapi_validator",
            name="OpenAPI validator",
            description="Validate OpenAPI 3.0 JSON spec structure.",
            category=ToolCategory.VALIDATION,
            enabled=True,
            status="active",
            allowed_agents={"A05"},
        )
    )
    registry.register(
        ToolDefinition(
            tool_id="patch_generator",
            name="Patch generator",
            description="Generate and apply controlled, gated source-code patches. "
                        "The only mechanism allowed to modify project files.",
            category=ToolCategory.WRITE,
            enabled=True,
            status="active",
            allowed_agents={"A04", "A06", "A07", "A08", "A10", "A11"},
        )
    )
    return registry


# ---------------------------------------------------------------------------
# Planned-tools registry (all have been enabled — tuple kept for structure)
# ---------------------------------------------------------------------------

# Declared-but-disabled tools: bound per the approved matrix, denied until
# their implementations are approved (Phase 4). Default-deny preserved.
# No remaining planned tools — all 14 are active.
_PLANNED_TOOLS: tuple[tuple[str, str, str, ToolCategory, set[str]], ...] = ()


def register_planned_tools(registry: ToolRegistry) -> ToolRegistry:
    """Register the declared-but-disabled tools on an existing registry."""
    for tool_id, name, description, category, agents in _PLANNED_TOOLS:
        registry.register(
            ToolDefinition(
                tool_id=tool_id,
                name=name,
                description=description,
                category=category,
                enabled=False,
                status="planned",
                allowed_agents=set(agents),
            )
        )
    return registry


def build_default_registry() -> ToolRegistry:
    """Active tools plus the declared planned set."""
    registry = register_defaults()
    return register_planned_tools(registry)


def validate_agent_tool_bindings(
    agents: list[AgentDefinition], registry: ToolRegistry
) -> list[str]:
    """Return binding errors (empty when every agent's tools all exist and bind).

    Every ``permitted_tool`` an agent references must exist in the registry
    and include the agent in its ``allowed_agents``, so agent definitions and
    the permission matrix stay in lockstep.
    """
    errors: list[str] = []
    known = {tool.tool_id: tool for tool in registry.list()}
    for agent in agents:
        for tool_id in agent.permitted_tools:
            tool = known.get(tool_id)
            if tool is None:
                errors.append(
                    f"agent {agent.agent_id} references unknown tool {tool_id!r}"
                )
            elif agent.agent_id not in tool.allowed_agents:
                errors.append(
                    f"agent {agent.agent_id} declares tool {tool_id!r} but the "
                    "registry does not bind it to them"
                )
    return errors
    return registry