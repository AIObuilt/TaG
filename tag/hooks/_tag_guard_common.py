from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tag_config import audit_log_path


def audit_log_entry(name: str, action: str, detail: str) -> None:
    log_path = audit_log_path(name)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": f"tag-{name}",
            "detail": detail[:500],
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def load_optional_json(path: Path, default: dict | list | None = None):
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {} if default is None else default


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def normalize(value: str) -> str:
    return str(value or "").replace("\\", "/").lower().strip()
