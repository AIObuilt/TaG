#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import sys
from pathlib import Path

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, normalize
from tag_config import DELEGATE_BYPASS_FILE, TAG_HOME


WRITE_TOOLS = {"Write", "Edit"}
WRITE_VERBS = ("cat >", "cat >>", "tee ", "touch ", "cp ", "mv ", "rm ", "sed -i", "> ", ">> ")
PROTECTED_PATH_MARKERS = (
    "/tag/hooks/",
    "/tag_config.py",
    "/tag/config/",
    "/tag-runtime/state/delegate-bypass.json",
)


def bypass_active(session_id: str) -> bool:
    state = load_optional_json(DELEGATE_BYPASS_FILE, default={})
    if not isinstance(state, dict):
        return False
    if state.get("session_id") != session_id:
        return False
    expires_at = float(state.get("expires_at", 0) or 0)
    return expires_at > time.time()


def path_is_protected(path: str) -> bool:
    path_norm = normalize(path)
    return any(marker in path_norm for marker in PROTECTED_PATH_MARKERS)


def path_is_local_control_plane(path: str) -> bool:
    try:
        resolved = Path(path).resolve()
    except Exception:
        return False
    return str(resolved).startswith(str(TAG_HOME.resolve()))


def bash_targets_workspace_write(command: str) -> bool:
    cmd = normalize(command)
    return "/workspace/" in cmd and any(verb in cmd for verb in WRITE_VERBS)


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = str(input_data.get("tool_name", ""))
    tool_input = input_data.get("tool_input", {}) or {}
    session_id = str(input_data.get("session_id", "") or "")

    if session_id and bypass_active(session_id):
        print(json.dumps({}))
        return 0

    if tool_name in WRITE_TOOLS:
        file_path = str(tool_input.get("file_path", "") or "")
        if path_is_protected(file_path):
            reason = "BLOCKED: TaG governance files are self-protected and cannot be modified from inside the runtime."
            audit_log_entry("delegate-enforcer", "BLOCK", reason)
            print(json.dumps({"decision": "block", "reason": reason}))
            return 0
        if file_path and not path_is_local_control_plane(file_path):
            reason = (
                "BLOCKED: direct write into a customer workspace detected. "
                "Delegate execution into the target fork/runtime instead of direct orchestrator editing."
            )
            audit_log_entry("delegate-enforcer", "BLOCK", reason)
            print(json.dumps({"decision": "block", "reason": reason}))
            return 0

    if tool_name == "Bash":
        command = str(tool_input.get("command", "") or "")
        if bash_targets_workspace_write(command):
            reason = (
                "BLOCKED: direct workspace write via Bash detected. "
                "Delegate execution into the target fork/runtime."
            )
            audit_log_entry("delegate-enforcer", "BLOCK", reason)
            print(json.dumps({"decision": "block", "reason": reason}))
            return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
