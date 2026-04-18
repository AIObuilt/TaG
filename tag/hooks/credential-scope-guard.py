#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, normalize
from tag_config import AUTHORITY_MATRIX_FILE, FORK_SCOPE_STATE


def load_credential_map() -> dict[str, str]:
    matrix = load_optional_json(AUTHORITY_MATRIX_FILE, default={})
    scopes = matrix.get("credential_scopes", {}) if isinstance(matrix, dict) else {}
    result: dict[str, str] = {}
    for key, payload in scopes.items():
        if not isinstance(payload, dict):
            continue
        forks = payload.get("forks", [])
        if not isinstance(forks, list) or not forks:
            continue
        result[normalize(key).replace("-", "").replace("_", "")] = normalize(forks[0])
    return result


def classify_credential(context: str, credential_map: dict[str, str]) -> tuple[str | None, str | None]:
    ctx = normalize(context).replace("-", "").replace("_", "")
    for key, fork in credential_map.items():
        if key in ctx:
            return fork, key
    return None, None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = str(input_data.get("tool_name", ""))
    tool_input = input_data.get("tool_input", {}) or {}
    scope = load_optional_json(FORK_SCOPE_STATE, default={})
    active_fork = normalize(scope.get("active_fork", ""))
    if not active_fork or active_fork == "prime":
        print(json.dumps({}))
        return 0

    context = ""
    if tool_name == "Read":
        context = str(tool_input.get("file_path", "") or "")
    elif tool_name == "Bash":
        context = str(tool_input.get("command", "") or "")

    credential_map = load_credential_map()
    credential_fork, matched = classify_credential(context, credential_map)
    if credential_fork and credential_fork not in {active_fork, "shared"}:
        reason = (
            f"BLOCKED: credential '{matched}' belongs to fork '{credential_fork}', "
            f"but this session is locked to '{active_fork}'."
        )
        audit_log_entry("credential-scope-guard", "BLOCK", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
