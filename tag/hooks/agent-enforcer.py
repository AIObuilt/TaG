#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json
from tag_config import HEARTBEAT_FILE


MIN_CALLS_FOR_EVAL = 10
NO_AGENT_WARNING_THRESHOLD = 15
SEQUENTIAL_WORK_PATTERNS = [
    r"\bi('ll| will)\s+(read|write|check|fix|build|deploy|update|create|edit|review)\b",
    r"\blet me\s+(read|check|look at|fix|update|modify|write|create|build)\b",
]


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    response = str(input_data.get("response", "") or "")
    metrics = load_optional_json(HEARTBEAT_FILE, default={})
    call_count = int(metrics.get("call_count", 0) or 0)
    agent_count = len(metrics.get("agents_launched", []) or [])

    warnings: list[str] = []
    if call_count >= NO_AGENT_WARNING_THRESHOLD and agent_count == 0:
        warnings.append(
            "DELEGATION DEFICIT: session has many tool calls and no delegated agents. "
            "Dispatch executor agents for direct code work instead of doing it in the orchestrator."
        )
    if response and call_count >= MIN_CALLS_FOR_EVAL:
        for pattern in SEQUENTIAL_WORK_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append(
                    "DELEGATION OPPORTUNITY: response language indicates direct sequential work. "
                    "Prefer dispatching parallel TaG executors."
                )
                break

    if warnings:
        message = "AGENT ENFORCER:\n" + "\n".join(f"  - {item}" for item in warnings)
        audit_log_entry("agent-enforcer", "WARN", message)
        print(json.dumps({"message": message}))
        return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
