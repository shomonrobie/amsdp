"""Settings parsing and validation tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from amsdp_ai_factory.config.settings import FactorySettings
from amsdp_ai_factory.contracts.common import Severity

from tests.helpers import TempRepoCase

_FACTORY_ENV_KEYS = (
    "AMSDP_FACTORY_ENVIRONMENT",
    "AMSDP_FACTORY_LOG_LEVEL",
    "AMSDP_FACTORY_REPO_ROOT",
    "AMSDP_FACTORY_TASK_STORE_DIR",
    "AMSDP_FACTORY_RUN_STORE_DIR",
    "AMSDP_FACTORY_WORKSPACE_ROOT",
    "AMSDP_FACTORY_DEFAULT_MAX_RETRIES",
    "AMSDP_FACTORY_MODEL_PROVIDER",
    "AMSDP_FACTORY_MODEL_ID",
)


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in _FACTORY_ENV_KEYS:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key in _FACTORY_ENV_KEYS:
            os.environ.pop(key, None)

    def test_defaults(self):
        settings = FactorySettings(_env_file=None)
        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.default_max_retries, 2)
        self.assertIsNone(settings.model_provider)

    def test_env_parsing(self):
        with mock.patch.dict(
            os.environ,
            {
                "AMSDP_FACTORY_ENVIRONMENT": "test",
                "AMSDP_FACTORY_LOG_LEVEL": "DEBUG",
                "AMSDP_FACTORY_DEFAULT_MAX_RETRIES": "3",
            },
        ):
            settings = FactorySettings(_env_file=None)
        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.default_max_retries, 3)

    def test_invalid_log_level_flagged(self):
        settings = FactorySettings(
            _env_file=None, environment="test", log_level="BANANA", repo_root=None
        )
        issues = settings.validate()
        codes = {issue.code for issue in issues}
        self.assertIn("invalid_log_level", codes)
        self.assertTrue(
            any(issue.severity == Severity.ERROR for issue in issues)
        )

    def test_partial_model_config_flagged(self):
        settings = FactorySettings(
            _env_file=None, environment="test", model_provider="openai", model_id=None
        )
        issues = settings.validate()
        self.assertIn("partial_model_config", {issue.code for issue in issues})

    def test_valid_basic_settings_have_no_errors(self):
        settings = FactorySettings(
            _env_file=None,
            environment="test",
            log_level="INFO",
            repo_root=str(Path.cwd()),
        )
        issues = settings.validate()
        self.assertFalse(
            [issue for issue in issues if issue.severity == Severity.ERROR]
        )


class SettingsPathTests(TempRepoCase):
    def test_effective_repo_root_uses_configured_root(self):
        settings = FactorySettings(_env_file=None, repo_root=str(self.repo_root))
        self.assertEqual(settings.effective_repo_root(), self.repo_root)

    def test_runtime_dirs_resolve_under_repo_root(self):
        settings = FactorySettings(_env_file=None, repo_root=str(self.repo_root))
        self.assertEqual(settings.task_store_path(), self.repo_root / "var" / "tasks")
        self.assertEqual(settings.run_store_path(), self.repo_root / "runs")
        self.assertEqual(
            settings.workspace_path(), self.repo_root / "var" / "workspaces"
        )


if __name__ == "__main__":
    unittest.main()