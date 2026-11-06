"""Rule discovery, MANIFEST validation, SHA-256 tracking."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuleDocument:
    rule_id: str
    file_name: str
    rel_path: str
    sha256_manifest: str | None = None
    sha256_actual: str | None = None
    exists: bool = False
    manifest_version: str | None = None
    parsed_name: str | None = None
    parsed_description: str | None = None


class RuleScanResult:
    def __init__(self, rules, missing, changed, unexpected, manifest_errors):
        self.rules = rules
        self.missing = missing
        self.changed = changed
        self.unexpected = unexpected
        self.manifest_errors = manifest_errors

    @property
    def ok(self):
        return not bool(self.manifest_errors or self.missing)

    @property
    def all_rule_ids(self):
        return [r.rule_id for r in self.rules if r.exists]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _detect_rule_id(file_name: str) -> str:
    """Derive rule ID from filename stem, replacing hyphens with underscores."""
    return file_name.rsplit(".", 1)[0].replace("-", "_")


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Minimal frontmatter parser - supports --- delimited key: value blocks."""
    NL = chr(10)
    if not text.startswith("---" + NL) and not text.startswith("---" + chr(13) + NL):
        return {}
    end = text.find(NL + "---", 4)
    if end == -1:
        return {}
    result: dict[str, Any] = {}
    for line in text[4:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip(chr(34) + chr(39))
    return result
def _validate_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["MANIFEST.json root is not a JSON object"]
    if "files" not in manifest:
        errors.append("MANIFEST.json missing 'files' key")
    else:
        files = manifest["files"]
        if not isinstance(files, dict):
            errors.append("MANIFEST.json 'files' is not a JSON object")
        else:
            for fname, sha in files.items():
                if not isinstance(fname, str) or not fname.endswith(".md"):
                    errors.append(f"Non-.md file in manifest: {fname!r}")
                if not isinstance(sha, str) or len(sha) != 64:
                    errors.append(f"Invalid SHA-256 for {fname!r}")
    if "purpose" not in manifest:
        errors.append("MANIFEST.json missing 'purpose' key")
    return errors


class AgentRulesRegistry:
    """Discovers and validates the agent-rules directory."""

    def __init__(self, rules_dir: str | Path) -> None:
        self.rules_dir = Path(rules_dir).resolve()
        self._manifest: dict[str, Any] | None = None

    def _load_manifest(self) -> dict[str, Any]:
        mp = self.rules_dir / "MANIFEST.json"
        if not mp.is_file():
            return {"files": {}}
        return dict(json.loads(mp.read_text(encoding="utf-8")))

    @property
    def manifest(self) -> dict[str, Any]:
        if self._manifest is None:
            self._manifest = self._load_manifest()
        return self._manifest

    def validate_manifest(self) -> list[str]:
        return _validate_manifest(self.manifest)

    def discover(self) -> RuleScanResult:
        manifest = self.manifest
        manifest_files: dict[str, str] = manifest.get("files", {})
        manifest_errors = _validate_manifest(manifest)
        on_disk = {p.name: p for p in self.rules_dir.glob("*.md")}
        rules, missing, changed, unexpected = [], [], [], []

        for fname, expected_sha in manifest_files.items():
            rule_id = _detect_rule_id(fname)
            if fname not in on_disk:
                missing.append(fname)
                rules.append(RuleDocument(
                    rule_id=rule_id, file_name=fname,
                    rel_path=str(self.rules_dir / fname),
                    sha256_manifest=expected_sha, exists=False))
                continue
            path = on_disk[fname]
            actual_sha = _sha256_file(path)
            if expected_sha and actual_sha != expected_sha:
                changed.append((fname, expected_sha, actual_sha))
            fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
            rules.append(RuleDocument(
                rule_id=rule_id, file_name=fname,
                rel_path=str(self.rules_dir / fname),
                sha256_manifest=expected_sha,
                sha256_actual=actual_sha, exists=True,
                manifest_version=str(manifest.get("version", "")),
                parsed_name=fm.get("name"),
                parsed_description=fm.get("description"),
            ))

        for fname in sorted(on_disk):
            if fname not in manifest_files:
                unexpected.append(fname)

        return RuleScanResult(
            rules=rules, missing=missing, changed=changed,
            unexpected=unexpected, manifest_errors=manifest_errors,
        )


def resolve_rule_text(rules_dir: Path, rule_id: str) -> str | None:
    """Return the full text of a rule document, or None if missing."""
    for p in rules_dir.iterdir():
        if not p.name.endswith(".md"):
            continue
        if _detect_rule_id(p.name) == rule_id:
            return p.read_text(encoding="utf-8")
    return None
