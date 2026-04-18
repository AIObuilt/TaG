#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import BUILD_STATUS_FILE, audit_log_path


AUDIT_LOG = audit_log_path("build-gate")
DEPLOY_PATTERNS = [
    r"git\s+push",
    r"vercel\s+--prod",
    r"vercel\s+deploy\s+--prod",
]


def audit_log_entry(command: str, decision: str, reason: str) -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command[:200],
            "decision": decision,
            "reason": reason,
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def is_deploy_command(cmd: str) -> bool:
    return any(re.search(pattern, cmd, re.IGNORECASE) for pattern in DEPLOY_PATTERNS)


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    if input_data.get("tool_name") != "Bash":
        print(json.dumps({}))
        return 0

    command = input_data.get("tool_input", {}).get("command", "")
    session_id = input_data.get("session_id", "")
    if not command or not is_deploy_command(command):
        print(json.dumps({}))
        return 0

    if not BUILD_STATUS_FILE.exists():
        reason = "BUILD GATE: No passing build found. Run the build first."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    try:
        data = json.loads(BUILD_STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        reason = "BUILD GATE: Build state file is corrupt. Re-run the build."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    if data.get("passed") is not True:
        reason = "BUILD GATE: Last build did not pass."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    if data.get("session_id") != session_id:
        reason = "BUILD GATE: Build passed in a different session. Re-run the build in this session."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    audit_log_entry(command, "allow", "Build state valid for current session")
    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
