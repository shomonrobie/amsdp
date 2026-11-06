"""Agent Rules — governed engineering rules for agent execution."""
from __future__ import annotations

from amsdp_ai_factory.rules.registry import (
    AgentRulesRegistry,
    RuleDocument,
    RuleScanResult,
    resolve_rule_text,
)
from amsdp_ai_factory.rules.mapping import (
    RULE_MAP,
    TASK_TYPE_RULE_MAP,
    select_rule_ids,
)
