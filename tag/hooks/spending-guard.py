#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import audit_log_path


AUDIT_LOG = audit_log_path("spending-guard")

BLOCKED_URL_PATTERNS = [
    r"api\.stripe\.com.*(charges|payment_intents|subscriptions|invoices|prices)",
    r"api\.bland\.ai",
    r"api\.vercel\.com.*(billing|plan|upgrade)",
    r"api\.anthropic\.com.*(billing|usage|subscription)",
    r"api\.twilio\.com.*IncomingPhoneNumbers",
    r"api\.openai\.com.*(billing|subscription)",
    r"checkout\.stripe\.com",
    r"buy\.",
    r"purchase\.",
    r"subscribe\.",
    r"api\.heroku\.com.*(dynos|addons)",
    r"api\.digitalocean\.com.*(droplets|databases)",
    r"googleapis\.com.*(compute|billing)",
]

SPENDING_COMMAND_PATTERNS = [
    r"stripe\s+(charges?|subscriptions?|payment)",
    r"vercel\s+.*(upgrade|\bpro\b|enterprise|billing)",
    r"twilio.*phone.*buy",
    r"heroku\s+(addons:create|ps:scale)",
    r"aws\s+(ec2|rds|s3).*create",
]


def audit_log_entry(action: str, detail: str, command_preview: str = "") -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": "tag-spending-guard",
            "detail": detail[:500],
            "command_preview": command_preview[:200],
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def check_bash_command(cmd: str) -> str | None:
    for pattern in BLOCKED_URL_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return f"SPENDING BLOCKED: command targets payment endpoint matching '{pattern}'"
    for pattern in SPENDING_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return f"SPENDING BLOCKED: command matches spending pattern '{pattern}'"
    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        warning = None
        command_preview = ""
        if tool_name == "Bash":
            command_preview = tool_input.get("command", "")[:200]
            warning = check_bash_command(tool_input.get("command", ""))
        if warning:
            audit_log_entry("BLOCK", warning, command_preview)
            print(json.dumps({"decision": "block", "reason": warning}))
            return 0
        print(json.dumps({}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
