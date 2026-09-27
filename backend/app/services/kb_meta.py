"""Tracks the last-indexed timestamp for the knowledge base. ChromaDB doesn't
store an insert timestamp itself, so this is a tiny JSON sidecar file — enough
for a POC's "Last indexed" UI label without adding a real database."""
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings

_META_FILE = Path(settings.resolved_chroma_path()) / "_kb_meta.json"


def mark_indexed():
    _META_FILE.parent.mkdir(parents=True, exist_ok=True)
    _META_FILE.write_text(json.dumps({"last_indexed_at": datetime.now(timezone.utc).isoformat()}))


def get_last_indexed_at() -> datetime | None:
    if not _META_FILE.exists():
        return None
    try:
        data = json.loads(_META_FILE.read_text())
        return datetime.fromisoformat(data["last_indexed_at"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
