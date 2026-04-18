from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


HERE = Path(__file__).resolve().parent
TAG_ROOT = HERE.parent
FRAMEWORK_SOURCE_FILE = TAG_ROOT / "config" / "framework.json"
FRAMEWORK_SOURCE_MARKER = "tag/config/framework.json"
CANONICAL_SURFACES = ("code", "comms", "browser", "ops")
ALLOWED_RUNTIME_IDENTITIES = ("browser", "claude", "codex", "openclaw", "ops", "voice")
POLICY_BASELINE_FIELDS = ("mode", "unknown_action_default", "known_sensitive_default", "workflow", "workflow_enforcement")
WORKFLOW_FIELDS = ("pre_commit", "pre_deploy", "post_deploy")
WORKFLOW_ENFORCEMENT_FIELDS = ("pre_commit", "pre_deploy", "post_deploy")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _require_string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field_name} must be a list of non-empty strings")
    return list(value)


def _require_nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_enum_string(value: object, field_name: str, allowed_values: tuple[str, ...]) -> str:
    value = _require_nonempty_string(value, field_name)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of: {', '.join(allowed_values)}")
    return value


def _require_mapping(value: object, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    result: dict[str, str] = {}
    for key, mapped in value.items():
        result[_require_nonempty_string(key, f"{field_name} key")] = _require_nonempty_string(
            mapped, f"{field_name}.{key}"
        )
    return result


def load_framework_source(path: Path | str = FRAMEWORK_SOURCE_FILE) -> dict:
    source = _read_json(Path(path))
    return _validate_framework_source(source)


def _validate_framework_source(source: dict) -> dict:
    surfaces = _require_string_list(source.get("surfaces"), "surfaces")
    if tuple(surfaces) != CANONICAL_SURFACES:
        raise ValueError(f"surfaces must exactly match canonical TaG surfaces: {', '.join(CANONICAL_SURFACES)}")

    runtimes = _require_mapping(source.get("runtimes"), "runtimes")
    invalid_runtimes = sorted(set(runtimes) - set(ALLOWED_RUNTIME_IDENTITIES))
    if invalid_runtimes:
        raise ValueError(f"runtimes must use allowed runtime identities: {', '.join(invalid_runtimes)}")
    invalid_surfaces = sorted({surface for surface in runtimes.values() if surface not in surfaces})
    if invalid_surfaces:
        raise ValueError(f"runtime surfaces must exist in surfaces: {', '.join(invalid_surfaces)}")

    policy_baseline = source.get("policy_baseline")
    if not isinstance(policy_baseline, dict) or set(policy_baseline) != set(POLICY_BASELINE_FIELDS):
        raise ValueError(f"policy_baseline must contain exactly: {', '.join(POLICY_BASELINE_FIELDS)}")
    workflow = policy_baseline.get("workflow")
    if not isinstance(workflow, dict) or set(workflow) != set(WORKFLOW_FIELDS):
        raise ValueError(f"policy_baseline.workflow must contain exactly: {', '.join(WORKFLOW_FIELDS)}")
    workflow_enforcement = policy_baseline.get("workflow_enforcement")
    if not isinstance(workflow_enforcement, dict) or set(workflow_enforcement) != set(WORKFLOW_ENFORCEMENT_FIELDS):
        raise ValueError(
            "policy_baseline.workflow_enforcement must contain exactly: "
            + ", ".join(WORKFLOW_ENFORCEMENT_FIELDS)
        )

    return source


def compile_framework_config(source: dict) -> dict:
    validated = _validate_framework_source(source)
    policy_baseline = deepcopy(validated["policy_baseline"])
    return {
        "policy": {
            "mode": policy_baseline["mode"],
            "unknown_action_default": policy_baseline["unknown_action_default"],
            "known_sensitive_default": policy_baseline["known_sensitive_default"],
            "surfaces": validated["surfaces"],
            "workflow": policy_baseline["workflow"],
            "workflow_enforcement": policy_baseline["workflow_enforcement"],
            "_generated_from": FRAMEWORK_SOURCE_MARKER,
        },
        "runtime_map": validated["runtimes"],
    }
