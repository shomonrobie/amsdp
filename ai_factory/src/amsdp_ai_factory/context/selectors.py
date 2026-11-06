"""Targeted context selection by task type.

The mapping below mirrors the minimum-required-context guidance in AI
Factory Architecture V1.0 section 7.2. The context loader passes an agent or
workflow stage only the documents relevant to its task type, rather than the
whole repository. Authoritative documents always outrank references: ordering
follows ``document_registry`` authority order.
"""

from __future__ import annotations

_DOCUMENTS_BY_TASK_TYPE: dict[str, tuple[str, ...]] = {
    "product_story": ("business_rules", "mvp_scope", "feature_list"),
    "architecture_design": ("system_architecture", "business_rules"),
    "service_design": ("system_architecture", "business_rules", "mvp_scope"),
    "database_design": ("system_architecture", "business_rules"),
    "api_design": ("system_architecture", "mvp_scope"),
    "backend_implementation": ("business_rules", "mvp_scope", "system_architecture"),
    "frontend_implementation": ("business_rules", "mvp_scope", "system_architecture"),
    "qa": ("business_rules", "mvp_scope"),
    "security_review": ("system_architecture", "business_rules"),
    "deployment": ("system_architecture",),
    "documentation": ("development_workflow", "business_rules", "mvp_scope"),
    "defect": ("business_rules", "mvp_scope"),
}

# Safe conservative default: the three highest-authority approved documents.
DEFAULT_TASK_TYPE_DOC_ROLES: tuple[str, ...] = (
    "business_rules",
    "mvp_scope",
    "system_architecture",
)


def select_document_roles(task_type: str | None) -> tuple[str, ...]:
    """Return the document roles required as minimum context for a task type.

    Unknown or empty task types resolve to the conservative default set.
    """
    if not task_type:
        return DEFAULT_TASK_TYPE_DOC_ROLES
    normalized = task_type.strip().lower().replace(" ", "_").replace("-", "_")
    roles = _DOCUMENTS_BY_TASK_TYPE.get(normalized)
    return tuple(roles) if roles is not None else DEFAULT_TASK_TYPE_DOC_ROLES


KNOWN_TASK_TYPES: tuple[str, ...] = tuple(sorted(_DOCUMENTS_BY_TASK_TYPE))