from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tag_config import SESSION_MEMORY_FILE
from tag.hooks._tag_guard_common import load_optional_json, save_json
from tag.memory.heartbeat import Heartbeat
from tag.memory.engram import Engram
from tag.memory.hindsight import Hindsight


@dataclass
class FileMemoryProvider:
    """Legacy flat provider — kept for backward compatibility."""
    storage_path: Path = SESSION_MEMORY_FILE

    def append_session_summary(self, entry: dict) -> None:
        payload = load_optional_json(self.storage_path, default={"entries": []})
        entries = list(payload.get("entries", []) or [])
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "title": entry.get("title", "Session"),
            "summary": entry.get("summary", ""),
            "type": entry.get("type", "session_summary"),
        })
        save_json(self.storage_path, {"entries": entries})


@dataclass
class MemorySystem:
    """Unified 3-layer memory: heartbeat + engram + hindsight."""
    heartbeat: Heartbeat = field(default_factory=Heartbeat)
    engram: Engram = field(default_factory=Engram)
    hindsight: Hindsight = field(default_factory=Hindsight)

    def status(self) -> dict:
        return {
            "heartbeat": {"alive": self.heartbeat.is_alive(), "state": self.heartbeat.read()},
            "engram": {"count": self.engram.count(), "tags": self.engram.list_tags()},
            "hindsight": self.hindsight.stats(),
        }


def resolve_provider() -> FileMemoryProvider:
    return FileMemoryProvider()

def resolve_memory() -> MemorySystem:
    return MemorySystem()
