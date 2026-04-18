#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import audit_log_path


AUDIT_LOG = audit_log_path("env-guard")

SENSITIVE_FILE_PATTERNS = [
    r"\.env\b",
    r"\.env\.",
    r"credentials",
    r"\.pem$",
    r"\.key$",
    r"\.p12$",
    r"\.pfx$",
    r"secret",
    r"\.ssh/",
    r"id_rsa",
    r"id_ed25519",
    r"\.npmrc",
    r"\.pypirc",
]

BROAD_ADD_PATTERNS = [
    r"git\s+add\s+-A",
    r"git\s+add\s+\.\s",
    r"git\s+add\s+\.&&",
    r"git\s+add\s+\.$",
    r"git\s+add\s+\*",
    r"git\s+add\s+--all",
]


def audit_log_entry(action: str, detail: str) -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": "tag-env-guard",
            "detail": detail[:500],
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def check_git_command(cmd: str) -> str | None:
    if not re.search(r"git\s+(add|commit)", cmd):
        return None

    for pattern in SENSITIVE_FILE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return (
                f"BLOCKED: git command references sensitive file pattern '{pattern}'. "
                "Never stage or commit environment files, credentials, private keys, or secrets."
            )

    for pattern in BROAD_ADD_PATTERNS:
        if re.search(pattern, cmd):
            return (
                "BLOCKED: use explicit file paths with git add instead of -A/./*, "
                "to avoid accidentally staging secrets."
            )

    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        if tool_name == "Bash":
            cmd = tool_input.get("command", "")
            warning = check_git_command(cmd)
            if warning:
                audit_log_entry("BLOCK", warning)
                print(json.dumps({"decision": "block", "reason": warning}))
                return 0
        print(json.dumps({}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
