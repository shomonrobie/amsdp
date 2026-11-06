"""Contract test tool tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from amsdp_ai_factory.tools.contract_test_tool import ContractTestTool

from tests.helpers import TempRepoCase


class ContractTestToolTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.tool = ContractTestTool()

    def _write_contract(self, rel: str, endpoints: list[dict]) -> Path:
        target = self.repo_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"service_name": "test", "endpoints": endpoints}), encoding="utf-8")
        return target

    def test_compatible_contracts_pass(self):
        provider = self._write_contract(
            "contracts/provider.json",
            [{"method": "POST", "path": "/patients", "auth_required": True, "idempotent": True}],
        )
        consumer = self._write_contract(
            "contracts/consumer.json",
            [{"method": "POST", "path": "/patients", "auth_required": True, "idempotent": True}],
        )
        result = self.tool.run_pair(provider, consumer)
        self.assertTrue(result.ok)

    def test_auth_mismatch_fails(self):
        provider = self._write_contract(
            "contracts/provider.json",
            [{"method": "GET", "path": "/patients", "auth_required": True}],
        )
        consumer = self._write_contract(
            "contracts/consumer.json",
            [{"method": "GET", "path": "/patients", "auth_required": False}],
        )
        result = self.tool.run_pair(provider, consumer)
        self.assertFalse(result.ok)
        self.assertIn("auth mismatched", result.output)

    def test_unmatched_endpoint_flagged(self):
        provider = self._write_contract(
            "contracts/provider.json",
            [{"method": "DELETE", "path": "/patients/1", "auth_required": True}],
        )
        consumer = self._write_contract(
            "contracts/consumer.json",
            [{"method": "DELETE", "path": "/patients/1", "auth_required": True, "idempotent": False}],
        )
        result = self.tool.run_pair(provider, consumer)
        self.assertTrue(result.ok)  # should still pass with no mismatch

    def test_missing_consumer_endpoint_flagged(self):
        provider = self._write_contract(
            "contracts/provider.json",
            [{"method": "PATCH", "path": "/patients/1", "auth_required": True}],
        )
        consumer = self._write_contract(
            "contracts/consumer.json",
            [{"method": "GET", "path": "/patients", "auth_required": True}],
        )
        result = self.tool.run_pair(provider, consumer)
        self.assertFalse(result.ok)
        self.assertIn("not consumed", result.output)


if __name__ == "__main__":
    unittest.main()