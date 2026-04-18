#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, normalize
from tag_config import AUTHORITY_MATRIX_FILE, FORK_SCOPE_STATE


WRITE_TOOLS = {"Write", "Edit"}
READ_TOOLS = {"Read", "Grep", "Glob"}


def load_fork_map() -> dict[str, list[str]]:
    matrix = load_optional_json(AUTHORITY_MATRIX_FILE, default={})
    forks = matrix.get("forks", {}) if isinstance(matrix, dict) else {}
    fork_map: dict[str, list[str]] = {}
    for name, payload in forks.items():
        if isinstance(payload, dict) and isinstance(payload.get("directory"), str):
            fork_map[name.lower()] = [normalize(payload["directory"]).rstrip("/") + "/"]
    return fork_map


def detect_fork_for_path(path: str, fork_map: dict[str, list[str]]) -> str | None:
    path_norm = normalize(path)
    for fork_name, directories in fork_map.items():
        for directory in directories:
            if f"/{directory}" in path_norm or path_norm.startswith(directory):
                return fork_name
    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = str(input_data.get("tool_name", ""))
    tool_input = input_data.get("tool_input", {}) or {}
    path = str(tool_input.get("file_path") or tool_input.get("path") or "")

    scope = load_optional_json(FORK_SCOPE_STATE, default={})
    active_fork = str(scope.get("active_fork", "") or "").lower().strip()
    fork_map = load_fork_map()
    target_fork = detect_fork_for_path(path, fork_map)

    if tool_name in READ_TOOLS and (not active_fork or not target_fork):
        print(json.dumps({}))
        return 0

    if tool_name in WRITE_TOOLS and not active_fork:
        reason = "BLOCKED: no active fork is locked for this session; establish fork scope before writing."
        audit_log_entry("os-acl-enforcer", "BLOCK", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    if tool_name in WRITE_TOOLS and target_fork and target_fork != active_fork:
        reason = (
            f"BLOCKED: cross-fork write detected. Session fork '{active_fork}' cannot write "
            f"into '{target_fork}'."
        )
        audit_log_entry("os-acl-enforcer", "BLOCK", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
