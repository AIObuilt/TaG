#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import (
    HEARTBEAT_FILE,
    CHECKPOINT_FILE,
)


HEARTBEAT_INTERVAL = 5


def new_heartbeat() -> dict:
    return {
        "call_count": 0,
        "calls_since_last_agent": 0,
        "session_start": datetime.now().isoformat(),
        "files_changed": [],
        "files_read": [],
        "commands_run": [],
        "agents_launched": [],
        "last_heartbeat": None,
        "cleanly_ended": False,
    }


def load_heartbeat() -> dict:
    if HEARTBEAT_FILE.exists():
        try:
            return json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return new_heartbeat()


def save_heartbeat(state: dict) -> None:
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def track_activity(state: dict, tool_name: str, tool_input: dict) -> None:
    state["call_count"] = state.get("call_count", 0) + 1
    state["calls_since_last_agent"] = state.get("calls_since_last_agent", 0) + 1

    if tool_name == "Agent":
        prompt = (tool_input.get("prompt", "") or "")
        if len(prompt) >= 50:
            state["calls_since_last_agent"] = 0

    if tool_name in ("Write", "Edit"):
        fp = tool_input.get("file_path", "")
        if fp and fp not in state.get("files_changed", []):
            state.setdefault("files_changed", []).append(fp)
            state["files_changed"] = state["files_changed"][-30:]
    elif tool_name == "Read":
        fp = tool_input.get("file_path", "")
        if fp:
            state.setdefault("files_read", []).append(fp)
            state["files_read"] = state["files_read"][-30:]
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if cmd:
            state.setdefault("commands_run", []).append(cmd[:120])
            state["commands_run"] = state["commands_run"][-20:]
    elif tool_name == "Agent":
        desc = tool_input.get("description", tool_input.get("prompt", ""))[:100]
        state.setdefault("agents_launched", []).append({
            "desc": desc,
            "time": datetime.now().isoformat(),
        })


def write_checkpoint_summary(state: dict) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# TaG Session Checkpoint\n\n",
        f"**Last heartbeat:** {ts}\n",
        f"**Tool calls:** {state.get('call_count', 0)}\n",
        f"**Session started:** {state.get('session_start', '?')}\n\n",
    ]
    files = state.get("files_changed", [])
    if files:
        lines.append("## Files Changed\n")
        for item in files[-15:]:
            lines.append(f"- `{item}`\n")
        lines.append("\n")
    agents = state.get("agents_launched", [])
    if agents:
        lines.append("## Agents\n")
        for agent in agents:
            lines.append(f"- [{agent.get('time', '')}] {agent.get('desc', '')}\n")
        lines.append("\n")
    CHECKPOINT_FILE.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    state = load_heartbeat()
    track_activity(state, tool_name, tool_input)
    state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_heartbeat(state)

    if state["call_count"] % HEARTBEAT_INTERVAL == 0:
        write_checkpoint_summary(state)

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
