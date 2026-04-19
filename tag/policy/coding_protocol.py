from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODING_PROTOCOL_FILE = HERE.parent / "config" / "coding-protocol.json"


def load_coding_protocol(path: Path | None = None) -> dict:
    target = path or CODING_PROTOCOL_FILE
    return json.loads(target.read_text(encoding="utf-8"))
