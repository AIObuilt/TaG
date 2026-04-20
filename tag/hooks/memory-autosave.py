#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, save_json
from tag.memory.provider import resolve_provider
from tag_config import HEARTBEAT_FILE

try:
    from tag.memory.hindsight import Hindsight
    from tag.memory.heartbeat import Heartbeat
    _memory_available = True
except ImportError:
    _memory_available = False


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    state = load_optional_json(HEARTBEAT_FILE, default={})
    call_count = int(state.get("call_count", 0) or 0)
    if call_count < 5:
        audit_log_entry("memory-autosave", "SKIP", f"trivial session ({call_count} calls)")
        print(json.dumps({}))
        return 0

    files = state.get("files_changed", []) or []
    agents = state.get("agents_launched", []) or []
    commands = state.get("commands_run", []) or []
    reads = state.get("files_read", []) or []

    summary = (
        f"{call_count} tool calls. "
        f"Files changed: {', '.join(os.path.basename(str(path)) for path in files[-10:]) or 'none'}. "
        f"Files read: {', '.join(os.path.basename(str(path)) for path in reads[-10:]) or 'none'}. "
        f"Agents: {', '.join(str(agent.get('desc', '?')) for agent in agents[-5:]) or 'none'}. "
        f"Commands: {', '.join(str(cmd) for cmd in commands[-5:]) or 'none'}."
    )

    provider = resolve_provider()
    provider.append_session_summary(
        {
            "title": f"Session end ({call_count} calls, {datetime.now().strftime('%Y-%m-%d %H:%M')})",
            "summary": summary,
            "type": "session_summary",
        }
    )

    if _memory_available:
        try:
            hindsight = Hindsight()
            hindsight.save(summary, source="memory-autosave", tags=["session", "autosave"])
            heartbeat = Heartbeat()
            heartbeat.end_session()
        except Exception:
            pass
    else:
        state["cleanly_ended"] = True
        save_json(HEARTBEAT_FILE, state)

    audit_log_entry("memory-autosave", "SAVED", f"{call_count} calls")
    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
