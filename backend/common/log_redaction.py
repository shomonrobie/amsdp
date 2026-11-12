"""Log redaction filter — prevents raw tracking tokens from appearing in logs.

AMSDP non-negotiable (§3): no token leakage through logs.
Applied to uvicorn access logs and stdlib loggers globally.
"""
import logging
import re

_TRACK_PATH_RE = re.compile(r"(/api/v1/track/|/track/)[A-Za-z0-9_-]{32,}")


class TokenRedactionFilter(logging.Filter):
    """Redacts raw tracking tokens from log messages.

    Matches /api/v1/track/... and /track/... paths and replaces the
    token segment with '/track/REDACTED'.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = _TRACK_PATH_RE.sub(r"\g<1>REDACTED", record.msg)
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    arg = _TRACK_PATH_RE.sub(r"\g<1>REDACTED", arg)
                new_args.append(arg)
            record.args = tuple(new_args)
        return True


def install_token_redaction():
    """Register the token-redaction filter on uvicorn, httpx and root loggers."""
    filt = TokenRedactionFilter()
    for name in ("uvicorn.access", "uvicorn", "uvicorn.error",
                 "httpx", "httpx._client",
                 "appointment", "__main__", None):
        logger = logging.getLogger(name)
        if not any(isinstance(f, TokenRedactionFilter) for f in logger.filters):
            logger.addFilter(filt)