"""Structured, secret-safe logging.

Logs: user query (truncated), retrieved document ids, which agent ran, revision
cycles, final sources, latency and errors. Deliberately never logs API keys or
full document contents (spec §22) — only identifiers and short excerpts.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..config import settings

_configured = False


def _configure_root():
    global _configured
    if _configured:
        return
    log_path = Path(settings.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    file_handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger("ai_policy_advisor")
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger("ai_policy_advisor").getChild(name)


def truncate(text: str, limit: int = 200) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "..."
