"""Structured, secret-safe logging.

Log lines use a compact tagged format, e.g.:
    [SCAN] scan_id=... [FACE] detection completed

A redaction filter guarantees private keys / API keys never reach the logs
even if accidentally passed into a log call.
"""
from __future__ import annotations

import logging
import re
import sys

from app.core.config import settings

# Patterns that must never appear in logs.
_SECRET_PATTERNS = [
    re.compile(r"0x[a-fA-F0-9]{64}"),          # 32-byte private keys
    re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),    # Google API keys
]


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        for pat in _SECRET_PATTERNS:
            msg = pat.sub("***REDACTED***", msg)
        record.msg = msg
        record.args = ()
        return True


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s")
    )
    handler.addFilter(RedactionFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers.
    for noisy in ("web3", "urllib3", "httpx", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
