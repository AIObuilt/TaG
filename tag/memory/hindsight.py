from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from tag_config import HINDSIGHT_FILE


class Hindsight:
    def __init__(self, path: Path = HINDSIGHT_FILE):
        self.path = path

    def save(self, content: str, *, source: str = "session", tags: list[str] | None = None,
             metadata: dict | None = None) -> dict:
        """Save a memory to the long-term archive."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "source": source,
            "tags": tags or [],
            "metadata": metadata or {},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def recall(self, query: str, *, limit: int = 10, source: str | None = None) -> list[dict]:
        """Search memories by keyword matching. Optionally filter by source."""
        if not self.path.exists():
            return []
        terms = query.lower().split()
        results = []
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                if source and entry.get("source") != source:
                    continue
                text = f"{entry.get('content', '')} {' '.join(entry.get('tags', []))}".lower()
                score = sum(1 for t in terms if t in text)
                if score > 0:
                    entry["_score"] = score
                    results.append(entry)
        except (json.JSONDecodeError, OSError):
            return []
        results.sort(key=lambda x: (-x["_score"], x.get("timestamp", "")))
        return results[:limit]

    def recent(self, *, limit: int = 20, source: str | None = None) -> list[dict]:
        """Return the most recent memories, newest first."""
        if not self.path.exists():
            return []
        entries = []
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                if source and entry.get("source") != source:
                    continue
                entries.append(entry)
        except (json.JSONDecodeError, OSError):
            return []
        entries.reverse()
        return entries[:limit]

    def stats(self) -> dict:
        """Return statistics about the hindsight archive."""
        if not self.path.exists():
            return {"total": 0, "sources": {}, "tags": {}}
        total = 0
        sources: dict[str, int] = {}
        tags: dict[str, int] = {}
        try:
            for line in self.path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                total += 1
                src = entry.get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1
                for t in entry.get("tags", []):
                    tags[t] = tags.get(t, 0) + 1
        except (json.JSONDecodeError, OSError):
            return {"total": 0, "sources": {}, "tags": {}}
        return {"total": total, "sources": sources, "tags": tags}

    def count(self) -> int:
        return self.stats()["total"]
