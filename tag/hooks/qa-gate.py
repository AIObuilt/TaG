#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import DEPLOY_STATE_FILE, audit_log_path


AUDIT_LOG = audit_log_path("qa-gate")
QA_ALLOWLIST = {"WebFetch", "Read", "Glob", "Grep"}


def audit_log_entry(tool_name: str, decision: str, reason: str) -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "decision": decision,
            "reason": reason,
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def load_deploy_state() -> dict:
    if not DEPLOY_STATE_FILE.exists():
        return {"deploys": [], "pending_qa": False}
    try:
        return json.loads(DEPLOY_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"deploys": [], "pending_qa": False}


def save_deploy_state(state: dict) -> None:
    try:
        DEPLOY_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEPLOY_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_pending_deploy_url(state: dict) -> str:
    for deploy in reversed(state.get("deploys", [])):
        if not deploy.get("qa_completed", False):
            return deploy.get("url", "unknown URL")
    return "unknown URL"


def is_playwright_tool(tool_name: str) -> bool:
    return tool_name.startswith("mcp__plugin_playwright") or tool_name.startswith("mcp__playwright")


def allow(tool_name: str, reason: str) -> int:
    audit_log_entry(tool_name, "allow", reason)
    print(json.dumps({}))
    return 0


def block(tool_name: str, reason: str) -> int:
    audit_log_entry(tool_name, "block", reason)
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = input_data.get("tool_name", "")
    state = load_deploy_state()
    if not state.get("pending_qa"):
        print(json.dumps({}))
        return 0

    if tool_name in QA_ALLOWLIST or is_playwright_tool(tool_name):
        return allow(tool_name, f"{tool_name} allowed while QA is pending")

    block_count = int(state.get("qa_gate_block_count", 0)) + 1
    state["qa_gate_block_count"] = block_count
    save_deploy_state(state)

    deploy_url = get_pending_deploy_url(state)
    reason = (
        f"QA GATE: Deployment at {deploy_url} is still pending verification. "
        "Run the TaG QA workflow before using non-QA tools."
    )
    return block(tool_name, reason)


if __name__ == "__main__":
    raise SystemExit(main())
