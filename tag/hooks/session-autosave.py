#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import HEARTBEAT_FILE, SESSION_MEMORY_FILE, PRODUCT_NAME


def main() -> int:
    state = {}
    if HEARTBEAT_FILE.exists():
        state = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))

    if state.get("call_count", 0) < 5:
        print("{}")
        return 0

    SESSION_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "product": PRODUCT_NAME,
        "saved_at": datetime.now().isoformat(),
        "session_start": state.get("session_start"),
        "call_count": state.get("call_count", 0),
        "files_changed": state.get("files_changed", []),
        "files_read": state.get("files_read", []),
        "commands_run": state.get("commands_run", []),
        "agents_launched": state.get("agents_launched", []),
    }
    SESSION_MEMORY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
