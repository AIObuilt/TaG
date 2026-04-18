from __future__ import annotations

import json
from pathlib import Path


def load_setup_state(path: Path) -> dict:
    if not path.exists():
        return {"mode": None, "runtime_path": None, "governed": False}
    return json.loads(path.read_text(encoding="utf-8"))


def save_setup_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
