from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class EvidenceRecord:
    evidence_id: str
    kind: str
    tool: str
    target: str
    status: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp or datetime.now(timezone.utc).isoformat()
        return payload


def append_evidence_record(path: Path, record: EvidenceRecord) -> dict:
    payload = record.to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return payload


def load_evidence_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
