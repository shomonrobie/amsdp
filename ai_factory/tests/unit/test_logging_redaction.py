"""Secret-redaction safety tests.

These verify the no-secrets-in-logs guarantee using synthetic secret-shaped
values only. No real credentials are used anywhere in this suite.
"""

from __future__ import annotations

import unittest

from amsdp_ai_factory.utils.logging import get_logger, redact


class RedactTests(unittest.TestCase):
    def test_key_value_assignment_scrubbed(self):
        text = "Using api_key=super-secret-value-123 for the backend."
        out = redact(text)
        self.assertNotIn("super-secret-value-123", out)
        self.assertIn("[REDACTED]", out)

    def test_token_assignment_scrubbed(self):
        out = redact("token=abcdef1234567890 token-ends-here")
        self.assertNotIn("abcdef1234567890", out)
        self.assertIn("[REDACTED]", out)

    def test_bearer_header_scrubbed(self):
        out = redact("Authorization: Bearer abcdefghij1234567890XYZ")
        self.assertNotIn("abcdefghij1234567890XYZ", out)
        self.assertIn("[REDACTED]", out)

    def test_openai_style_key_scrubbed(self):
        secret = "sk-abcdefghijklmnopqrstuvwxyz1234567890"
        out = redact(f"prefix {secret} suffix")
        self.assertNotIn(secret, out)
        self.assertIn("[REDACTED-CREDENTIAL]", out)

    def test_short_sku_like_token_not_scrubbed(self):
        self.assertEqual(redact("sku-123 line"), "sku-123 line")

    def test_private_key_block_scrubbed(self):
        pem = "-----BEGIN PRIVATE KEY-----\nSUPERSECRETBASE64\n-----END PRIVATE KEY-----"
        out = redact(pem)
        self.assertNotIn("SUPERSECRETBASE64", out)
        self.assertIn("[REDACTED-PRIVATE-KEY]", out)

    def test_normal_text_unchanged(self):
        sample = "The queue opened at 09:00 and token T-042 printed for walk-in 7."
        self.assertEqual(redact(sample), sample)

    def test_empty_and_none_safe(self):
        self.assertEqual(redact(""), "")
        self.assertEqual(redact(None if False else ""), "")


class LoggerRedactionTests(unittest.TestCase):
    def test_logger_scrubs_secret_values(self):
        logger = get_logger("redaction_test")
        secret = "sekrit-value-abc-123"
        with self.assertLogs(logger, level="INFO") as captured:
            logger.info("configured provider with api_key=%s for run 42", secret)
        joined = "\n".join(captured.output)
        self.assertNotIn(secret, joined)
        self.assertIn("[REDACTED]", joined)


if __name__ == "__main__":
    unittest.main()