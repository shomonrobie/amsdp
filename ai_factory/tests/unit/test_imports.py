"""Package import smoke tests."""

from __future__ import annotations

import unittest


class ImportTests(unittest.TestCase):
    def test_version_metadata(self):
        import amsdp_ai_factory

        self.assertEqual(amsdp_ai_factory.__version__, "0.1.0")
        self.assertEqual(amsdp_ai_factory.VERSION, amsdp_ai_factory.__version__)
        self.assertIn("AI Factory", amsdp_ai_factory.FACTORY_NAME)

    def test_phase1_submodules_import(self):
        import amsdp_ai_factory.config.settings  # noqa: F401
        import amsdp_ai_factory.context.document_registry  # noqa: F401
        import amsdp_ai_factory.context.loader  # noqa: F401
        import amsdp_ai_factory.context.selectors  # noqa: F401
        import amsdp_ai_factory.contracts.common  # noqa: F401
        import amsdp_ai_factory.utils.logging  # noqa: F401
        import amsdp_ai_factory.utils.paths  # noqa: F401
        import amsdp_ai_factory.validation.configuration  # noqa: F401


if __name__ == "__main__":
    unittest.main()