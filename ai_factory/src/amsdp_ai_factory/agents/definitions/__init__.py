"""The eleven approved agent definitions (AI Agent Specification V1.0)."""

from __future__ import annotations

from amsdp_ai_factory.agents.definitions.a01_product_analyst import PRODUCT_ANALYST
from amsdp_ai_factory.agents.definitions.a02_system_architect import SYSTEM_ARCHITECT
from amsdp_ai_factory.agents.definitions.a03_service_architect import SERVICE_ARCHITECT
from amsdp_ai_factory.agents.definitions.a04_database_architect import DATABASE_ARCHITECT
from amsdp_ai_factory.agents.definitions.a05_api_contract_designer import (
    API_CONTRACT_DESIGNER,
)
from amsdp_ai_factory.agents.definitions.a06_backend_developer import BACKEND_DEVELOPER
from amsdp_ai_factory.agents.definitions.a07_frontend_developer import FRONTEND_DEVELOPER
from amsdp_ai_factory.agents.definitions.a08_qa_engineer import QA_ENGINEER
from amsdp_ai_factory.agents.definitions.a09_security_reviewer import SECURITY_REVIEWER
from amsdp_ai_factory.agents.definitions.a10_devops_engineer import DEVOPS_ENGINEER
from amsdp_ai_factory.agents.definitions.a11_technical_writer import TECHNICAL_WRITER
from amsdp_ai_factory.agents.models import AgentDefinition

ALL_AGENTS: tuple[AgentDefinition, ...] = (
    PRODUCT_ANALYST,
    SYSTEM_ARCHITECT,
    SERVICE_ARCHITECT,
    DATABASE_ARCHITECT,
    API_CONTRACT_DESIGNER,
    BACKEND_DEVELOPER,
    FRONTEND_DEVELOPER,
    QA_ENGINEER,
    SECURITY_REVIEWER,
    DEVOPS_ENGINEER,
    TECHNICAL_WRITER,
)

AGENT_INDEX: dict[str, AgentDefinition] = {a.agent_id: a for a in ALL_AGENTS}