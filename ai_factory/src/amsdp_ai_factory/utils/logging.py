"""Safe logging with secret redaction.

Rules enforced here:

- API keys, passwords, access tokens, bearer tokens, and private keys are
  scrubbed from every record emitted by Factory loggers.
- The redaction filter is attached at the *logger* level (not only at the
  handler), so any handler — including test capture handlers — sees the
  scrubbed text.
- Logging must never raise: redaction failures degrade to the original text.
"""

from __future__ import annotations

import logging
import os
import re

# (compiled pattern, replacement)
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # name=value / name:value assignments for common secret key names
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|client[_-]?secret|"
            r"refresh[_-]?token|password|passwd|secret|token)\s*[=:]\s*[^\s,;&\"']+"
        ),
        lambda m: f"{m.group(1)}=[REDACTED]",
    ),
    # Authorization: Bearer <token>
    (
        re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-+~=/]{8,}"),
        lambda m: f"{m.group(1)} [REDACTED]",
    ),
    # OpenAI-style keys sk-/pk-/rk-...
    (
        re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_\-]{12,}\b"),
        lambda m: "[REDACTED-CREDENTIAL]",
    ),
    # GitHub personal access tokens
    (
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        lambda m: "[REDACTED-CREDENTIAL]",
    ),
    # AWS access key IDs
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        lambda m: "[REDACTED-CREDENTIAL]",
    ),
    # PEM private key blocks (any key type, incl. "PRIVATE KEY" without a
    # type prefix). The optional " [A-Z]+" type group is important: a plain
    # "BEGIN PRIVATE KEY-----" must match too.
    (
        re.compile(
            r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----.*?"
            r"-----END(?: [A-Z]+)? PRIVATE KEY-----",
            re.DOTALL,
        ),
        lambda m: "[REDACTED-PRIVATE-KEY]",
    ),
)


def redact(text: str) -> str:
    """Return ``text`` with recognizable secret values scrubbed."""
    if not text:
        return text
    scrubbed = text
    for pattern, repl in _SECRET_PATTERNS:
        scrubbed = pattern.sub(repl, scrubbed)
    return scrubbed


_LOGGER_PREFIX = "amsdp_ai_factory"


class SecretRedactionFilter(logging.Filter):
    """Logging filter that scrubs secret-shaped values from a record.

    The record is formatted *first* (``getMessage`` applies any ``%``
    arguments), then the final message is redacted, then ``args`` is cleared
    so later handlers never re-format. Redaction must not corrupt log
    formatting: this ordering is what makes it safe.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            try:
                message = record.getMessage()  # str(record.msg) % record.args
            except (TypeError, ValueError):  # malformed format string: keep raw
                message = record.msg
            record.msg = redact(str(message))
            record.args = ()
        except Exception:  # pragma: no cover - logging must never fail
            pass
        return True


def _ensure_output_handler(root: logging.Logger) -> None:
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    handler.addFilter(SecretRedactionFilter())
    root.addHandler(handler)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure the Factory root logger. Idempotent; safe to call often."""
    root = logging.getLogger(_LOGGER_PREFIX)
    root.setLevel(level.upper() if isinstance(level, str) else level)
    _ensure_output_handler(root)
    return root


def get_logger(name: str) -> logging.Logger:
    """Return a Factory logger named ``amsdp_ai_factory.<name>``.

    The logger carries the redaction filter directly so every record is
    scrubbed regardless of which handler formats it.
    """
    configure_logging(os.environ.get("AMSDP_FACTORY_LOG_LEVEL", "INFO"))
    logger = logging.getLogger(f"{_LOGGER_PREFIX}.{name}")
    if not any(isinstance(f, SecretRedactionFilter) for f in logger.filters):
        logger.addFilter(SecretRedactionFilter())
    return logger