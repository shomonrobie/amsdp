"""Disposable DB and migration validator tool tests."""

from __future__ import annotations

import unittest

from amsdp_ai_factory.tools.db_tools import DisposableDBTool, MigrationValidatorTool


class DisposableDBTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = DisposableDBTool()
        self.validator = MigrationValidatorTool()

    def test_valid_sqlite_runs_ok(self):
        result = self.tool.run("CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);")
        self.assertTrue(result.ok)

    def test_invalid_sql_fails(self):
        result = self.tool.run("CREATE TABLE t (id INTEGER); CREAT TABLE x;")
        self.assertFalse(result.ok)

    def test_migration_validator_ok(self):
        sql = "ALTER TABLE t ADD COLUMN x INTEGER;"
        result = self.validator.validate(sql, label="forward")
        self.assertTrue(result.ok)

    def test_destructive_drop_flagged(self):
        sql = "DROP TABLE patients;"
        result = self.validator.validate(sql)
        self.assertFalse(result.ok)
        self.assertIn("DROP", result.output)

    def test_unscoped_delete_flagged(self):
        sql = "DELETE FROM appointments;"
        result = self.validator.validate(sql)
        self.assertFalse(result.ok)
        self.assertIn("unscoped", result.output)


if __name__ == "__main__":
    unittest.main()