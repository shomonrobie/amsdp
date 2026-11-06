"""Agent-to-rule mapping: which agents/workflows receive which rules."""

from __future__ import annotations

# Each rule identified by its dasherized stem after prefix removal.
# The governance rule (carbontally_agent_governance) is universal — always included.
# "*" means all agents.

RULE_MAP: dict[str, list[str]] = {
    "carbontally_agent_governance": ["*"],  # universal
    "emissions_provenance": [
        "A01", "A02", "A06", "A07", "A08", "A09", "A11",
    ],
    "saas_ai_provider_registry": [
        "A02", "A03", "A09", "A10",
    ],
    "saas_api_throttling": [
        "A02", "A05", "A06", "A09",
    ],
    "saas_application_security": [
        "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10",
    ],
    "saas_auth_and_authorisation": [
        "A02", "A03", "A04", "A05", "A06", "A09",
    ],
    "saas_cicd_workflow": [
        "A08", "A09", "A10",
    ],
    "saas_frontend_ux": [
        "A01", "A02", "A07",
    ],
    "saas_multitenant_data": [
        "A02", "A04", "A06", "A08", "A09",
    ],
    "saas_observability": [
        "A02", "A06", "A08", "A09", "A10",
    ],
}

TASK_TYPE_RULE_MAP: dict[str, list[str]] = {
    "architecture_design": [
        "saas_application_security", "saas_auth_and_authorisation",
        "saas_multitenant_data", "saas_observability",
    ],
    "security_review": [
        "saas_application_security", "saas_auth_and_authorisation",
        "saas_multitenant_data", "saas_api_throttling", "saas_ai_provider_registry",
    ],
    "deployment": [
        "saas_cicd_workflow", "saas_observability",
    ],
    "frontend_implementation": [
        "saas_frontend_ux", "saas_application_security",
    ],
    "backend_implementation": [
        "saas_application_security", "saas_auth_and_authorisation",
        "saas_multitenant_data", "saas_api_throttling", "saas_observability",
    ],
    "qa": [
        "saas_application_security", "saas_cicd_workflow",
        "saas_multitenant_data", "saas_observability",
    ],
    "assessment": [
        "saas_application_security", "saas_auth_and_authorisation",
        "saas_multitenant_data", "saas_observability", "saas_cicd_workflow",
    ],
}


def select_rule_ids(
    *, agent_id: str | None = None, task_type: str | None = None,
) -> set[str]:
    """Return rule IDs applicable for the given agent and/or task type.

    The governance rule is always included.
    """
    selected: set[str] = {"carbontally_agent_governance"}
    if agent_id:
        for rule_id, agent_ids in RULE_MAP.items():
            if "*" in agent_ids or agent_id in agent_ids:
                selected.add(rule_id)
    if task_type:
        normalized = task_type.strip().lower().replace(" ", "_").replace("-", "_")
        extra = TASK_TYPE_RULE_MAP.get(normalized, [])
        selected.update(extra)
    return selected
