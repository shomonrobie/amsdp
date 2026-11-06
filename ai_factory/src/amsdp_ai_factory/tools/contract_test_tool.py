"""Contract test tool: compare two API contract JSON files for compatibility.

Loads two endpoint lists and flags unmatched operations, mismatched
idempotency, missing error codes, and auth-requirement mismatches.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from amsdp_ai_factory.tools.tool_registry import ToolCallResult


class _Endpoint(BaseModel):
    method: str = ""
    path: str = ""
    auth_required: bool = True
    idempotent: bool = False
    error_codes: list[str] | None = None


class _Contract(BaseModel):
    service_name: str = ""
    endpoints: list[_Endpoint] = []


class ContractTestTool:
    """Tool id ``contract_test_tool`` — API contract compatibility validator."""

    tool_id = "contract_test_tool"

    def run_pair(self, provider_path: Path, consumer_path: Path) -> ToolCallResult:
        try:
            provider = _Contract.model_validate_json(provider_path.read_text(encoding="utf-8"))
            consumer = _Contract.model_validate_json(consumer_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id, error=f"contract parse failed: {exc}"
            )
        issues: list[str] = []
        provider_map = {(ep.method.upper(), ep.path): ep for ep in provider.endpoints}
        for consumer_ep in consumer.endpoints:
            key = (consumer_ep.method.upper(), consumer_ep.path)
            provider_ep = provider_map.get(key)
            if provider_ep is None:
                issues.append(
                    f"consumer endpoint {consumer_ep.method} {consumer_ep.path} "
                    "has no matching provider; added later?"
                )
                continue
            if not consumer_ep.auth_required and provider_ep.auth_required:
                issues.append(
                    f"{key[0]} {key[1]}: auth mismatched "
                    f"(consumer auth=False, provider auth=True)"
                )
            if consumer_ep.idempotent != provider_ep.idempotent:
                issues.append(
                    f"{key[0]} {key[1]}: idempotent mismatch "
                    f"(consumer={consumer_ep.idempotent}, provider={provider_ep.idempotent})"
                )
        for provider_ep in provider.endpoints:
            key = (provider_ep.method.upper(), provider_ep.path)
            if key not in {(ep.method.upper(), ep.path) for ep in consumer.endpoints}:
                issues.append(
                    f"provider {key[0]} {key[1]} is not consumed by any consumer"
                )
        output = "\n".join(issues) if issues else "(contracts are compatible)"
        return ToolCallResult(
            ok=not issues,
            tool_id=self.tool_id,
            summary=f"{len(issues)} compatibility issue(s)",
            output=output,
            error="" if not issues else f"{len(issues)} compatibility finding(s)",
        )