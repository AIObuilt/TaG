from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tag_config import SESSION_MEMORY_FILE
from tag.hooks._tag_guard_common import load_optional_json, save_json


@dataclass
class FileMemoryProvider:
    storage_path: Path = SESSION_MEMORY_FILE

    def append_session_summary(self, entry: dict) -> None:
        payload = load_optional_json(self.storage_path, default={"entries": []})
        entries = list(payload.get("entries", []) or [])
        entries.append(
            {
                "timestamp": datetime.now().isoformat(),
                "title": entry.get("title", "Session"),
                "summary": entry.get("summary", ""),
                "type": entry.get("type", "session_summary"),
            }
        )
        save_json(self.storage_path, {"entries": entries})


def resolve_provider() -> FileMemoryProvider:
    return FileMemoryProvider()
