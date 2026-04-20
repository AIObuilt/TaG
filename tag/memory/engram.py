from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from tag_config import ENGRAM_FILE


class Engram:
    def __init__(self, path: Path = ENGRAM_FILE):
        self.path = path

    def save(self, content: str, *, tags: list[str] | None = None,
             source: str = "system", entry_type: str = "rule") -> dict:
        """Save a rule, decision, or pattern to engram memory."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "tags": tags or [],
            "source": source,
            "type": entry_type,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def recall(self, query: str, *, limit: int = 10) -> list[dict]:
        """Search engram entries by keyword matching across content and tags."""
        if not self.path.exists():
            return []
        terms = query.lower().split()
        results = []
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                text = f"{entry.get('content', '')} {' '.join(entry.get('tags', []))}".lower()
                score = sum(1 for t in terms if t in text)
                if score > 0:
                    entry["_score"] = score
                    results.append(entry)
        except (json.JSONDecodeError, OSError):
            return []
        results.sort(key=lambda x: x["_score"], reverse=True)
        return results[:limit]

    def list_tags(self) -> list[str]:
        """Return all unique tags across engram entries."""
        if not self.path.exists():
            return []
        tags = set()
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                for t in entry.get("tags", []):
                    tags.add(t)
        except (json.JSONDecodeError, OSError):
            return []
        return sorted(tags)

    def count(self) -> int:
        """Return total number of engram entries."""
        if not self.path.exists():
            return 0
        try:
            lines = self.path.read_text(encoding="utf-8").strip().splitlines()
            return len([l for l in lines if l.strip()])
        except OSError:
            return 0

    def all_entries(self, *, limit: int = 100) -> list[dict]:
        """Return most recent entries, newest first."""
        if not self.path.exists():
            return []
        entries = []
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entries.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            return []
        entries.reverse()
        return entries[:limit]
