from __future__ import annotations

import json
import re
from pathlib import Path

from tag.policy.config_compiler import FRAMEWORK_SOURCE_FILE, compile_framework_config, load_framework_source
from tag_config import BUILD_STATUS_FILE, DEPLOY_STATE_FILE, SECURITY_VERDICT_FILE, STATE_DIR


WORKFLOW_STATE_FILE = STATE_DIR / "workflow-state.json"
COMPILED_BASELINE = compile_framework_config(load_framework_source(FRAMEWORK_SOURCE_FILE))["policy"]


def load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def shell_workflow_stage(command: str) -> str | None:
    cmd = command.lower()
    if re.search(r"\bgit\s+commit\b", cmd):
        return "pre_commit"
    if "vercel --prod" in cmd or re.search(r"\bgit\s+push\s+(origin\s+)?(main|master|production)\b", cmd):
        return "pre_deploy"
    return None


def post_deploy_active() -> bool:
    return load_optional_json(DEPLOY_STATE_FILE).get("pending_qa") is True


def post_deploy_allowlisted(action: dict) -> bool:
    action_type = str(action.get("action_type", "")).lower()
    target = str(action.get("normalized_target", "")).lower()
    tool_name = str((action.get("metadata", {}) or {}).get("tool_name", "")).lower()
    if action_type in {"workflow_gate", "webfetch", "read", "glob", "grep"}:
        return True
    if tool_name in {"webfetch", "read", "glob", "grep"}:
        return True
    return "qa" in target


def infer_gate_state() -> dict:
    state = {}
    if load_optional_json(BUILD_STATUS_FILE).get("passed") is True:
        state["build"] = True
    security = load_optional_json(SECURITY_VERDICT_FILE)
    if security.get("decision") == "pass" or security.get("verdict") == "PASS":
        state["security"] = True
    deploy = load_optional_json(DEPLOY_STATE_FILE)
    if deploy.get("last_qa"):
        state["qa"] = True
    if deploy.get("pending_qa") is False and deploy.get("deploys"):
        state["live_qa"] = True
        state["live_security"] = True
    workflow = load_optional_json(WORKFLOW_STATE_FILE)
    for gate, entry in (workflow.get("gates", {}) or {}).items():
        if isinstance(entry, dict) and entry.get("status") == "passed":
            state[gate] = True
    return state


def required_gates_for_action(action: dict, base: dict) -> tuple[list[str], str | None]:
    workflow = base.get("workflow", {})
    if post_deploy_active() and not post_deploy_allowlisted(action):
        return workflow.get("post_deploy", []), "post_deploy"
    stage = shell_workflow_stage(str(action.get("normalized_target", "")))
    if not stage:
        return [], None
    return workflow.get(stage, []), stage


def workflow_enforcement_mode(stage: str | None, base: dict) -> str:
    if not stage:
        return "audit"
    value = (base.get("workflow_enforcement", {}) or {}).get(stage, "audit")
    return value if value in {"audit", "hold"} else "audit"


def evaluate_action(action: dict) -> dict:
    base = COMPILED_BASELINE
    required_gates, stage = required_gates_for_action(action, base)
    if required_gates:
        gate_state = infer_gate_state()
        missing_gates = [gate for gate in required_gates if not gate_state.get(gate)]
        if missing_gates:
            mode = workflow_enforcement_mode(stage, base)
            if mode == "hold":
                return {
                    "decision": "hold",
                    "reason": f"workflow-missing:{','.join(missing_gates)}",
                    "missing_gates": missing_gates,
                    "workflow_stage": stage,
                    "workflow_enforcement": mode,
                }
            return {
                "decision": "allow",
                "audit": True,
                "reason": f"workflow-missing:{','.join(missing_gates)}",
                "missing_gates": missing_gates,
                "workflow_stage": stage,
                "workflow_enforcement": mode,
            }
    if action.get("sensitive"):
        return {"decision": base["known_sensitive_default"], "reason": "sensitive-action"}
    if base.get("unknown_action_default") == "audit":
        return {"decision": "allow", "reason": "audit-first"}
    return {"decision": "allow", "reason": "default-allow"}
