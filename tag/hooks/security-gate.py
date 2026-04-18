#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import SECURITY_VERDICT_FILE, audit_log_path


AUDIT_LOG = audit_log_path("security-gate")
GIT_PATTERNS = [
    r"git\s+commit",
    r"git\s+push",
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


def is_gated_command(cmd: str) -> bool:
    return any(re.search(pattern, cmd, re.IGNORECASE) for pattern in GIT_PATTERNS)


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
    if not command or not is_gated_command(command):
        print(json.dumps({}))
        return 0

    if not SECURITY_VERDICT_FILE.exists():
        reason = "No security scan found. Run the TaG security scan first."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    try:
        data = json.loads(SECURITY_VERDICT_FILE.read_text(encoding="utf-8"))
    except Exception:
        reason = "Security verdict file is corrupt. Re-run the TaG security scan."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    if data.get("verdict") != "PASS":
        reason = f"Security scan FAILED: {data.get('summary', 'No details provided')}"
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    if data.get("session_id") != session_id:
        reason = "Security verdict is from a different session. Re-run the TaG security scan."
        audit_log_entry(command, "block", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    audit_log_entry(command, "allow", "Security verdict PASS for current session")
    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
