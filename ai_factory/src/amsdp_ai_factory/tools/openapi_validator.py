"""OpenAPI schema validator tool.

Checks OpenAPI 3.0 specifications for required fields: info, openapi version,
paths, each operation must have responses and at least one response code.
"""

from __future__ import annotations

import json
from pathlib import Path

from amsdp_ai_factory.tools.tool_registry import ToolCallResult


class OpenAPIVValidatorTool:
    """Tool id ``openapi_validator`` — structural OpenAPI contract checks."""

    tool_id = "openapi_validator"

    def run(self, spec_path: Path) -> ToolCallResult:
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return ToolCallResult(
                ok=False, tool_id=self.tool_id,
                error=f"cannot read spec: {exc}",
            )
        issues: list[str] = []
        if not isinstance(spec, dict):
            issues.append("top-level structure must be a JSON object")
            return ToolCallResult(ok=False, tool_id=self.tool_id,
                                  error="; ".join(issues))

        if "openapi" not in spec:
            issues.append("missing 'openapi' field")
        if "info" not in spec or not isinstance(spec.get("info"), dict):
            issues.append("missing or invalid 'info' section")
        elif "title" not in spec["info"]:
            issues.append("missing 'info.title'")
        paths = spec.get("paths", {})
        if not paths or not isinstance(paths, dict):
            issues.append("no 'paths' defined")
        else:
            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue
                for method, operation in methods.items():
                    if not isinstance(operation, dict):
                        issues.append(f"{path}.{method}: not a mapping")
                        continue
                    if "responses" not in operation:
                        issues.append(f"{path}.{method}: missing 'responses'")
                    responses = operation.get("responses", {})
                    if responses and not any(k.startswith("2") for k in responses):
                        issues.append(f"{path}.{method}: no 2xx response")

        output = "\n".join(issues) if issues else "(spec valid)"
        return ToolCallResult(
            ok=not issues,
            tool_id=self.tool_id,
            summary=f"{'invalid' if issues else 'valid'}: {len(issues)} issue(s)",
            output=output,
            error="" if not issues else f"{len(issues)} structural issue(s)",
        )