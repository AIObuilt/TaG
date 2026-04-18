#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, normalize, save_json
from tag_config import FORK_SCOPE_STATE


WRITE_TOOLS = {"Write", "Edit", "Bash"}
KNOWN_FORKS = ("sales", "support", "ops", "engineering", "research")


def detect_fork(path: str) -> str | None:
    path_norm = normalize(path)
    for fork in KNOWN_FORKS:
        if f"/{fork}/" in path_norm or path_norm.startswith(f"{fork}/"):
            return fork
    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = str(input_data.get("tool_name", ""))
    tool_input = input_data.get("tool_input", {}) or {}
    if tool_name not in WRITE_TOOLS:
        print(json.dumps({}))
        return 0

    target = str(tool_input.get("file_path") or tool_input.get("path") or tool_input.get("command") or "")
    touched_fork = detect_fork(target)
    if not touched_fork:
        print(json.dumps({}))
        return 0

    state = load_optional_json(FORK_SCOPE_STATE, default={})
    forks_touched = list(state.get("forks_touched", []) or [])
    if touched_fork not in forks_touched:
        forks_touched.append(touched_fork)
    state["forks_touched"] = forks_touched
    state.setdefault("files_by_fork", {})
    state["files_by_fork"].setdefault(touched_fork, []).append(target)
    state.setdefault("active_fork", forks_touched[0])
    save_json(FORK_SCOPE_STATE, state)

    if len(forks_touched) > 1:
        message = (
            "FORK SCOPE WARNING: multiple forks touched in one session "
            f"({', '.join(forks_touched)}). Keep one fork per session."
        )
        audit_log_entry("fork-scope-guard", "WARN", message)
        print(json.dumps({"message": message}))
        return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
