#!/usr/bin/env python3
"""TaG Actor Isolation Guard

Enforces memory and context boundaries between actors (operators) in a
multi-actor TaG deployment.  Each actor operates within a defined scope;
cross-actor memory reads, session access, and resource access are blocked
unless explicitly granted by policy.

Policy file: $TAG_HOME/config/actor-isolation-policy.json
State file:  $TAG_HOME/tag-runtime/state/actor-registry.json
Audit log:   $TAG_HOME/tag-runtime/audit/actor-isolation-guard.jsonl
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, normalize, save_json
from tag_config import AUDIT_DIR, CONFIG_DIR, CONTEXT_DIR, RUNTIME_DIR, STATE_DIR


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

POLICY_FILE = CONFIG_DIR / "actor-isolation-policy.json"
REGISTRY_FILE = STATE_DIR / "actor-registry.json"

GUARD_NAME = "actor-isolation-guard"

# Resource types that represent memory / context boundaries
MEMORY_RESOURCE_TYPES = {"memory", "session", "context", "engram", "checkpoint"}


# ---------------------------------------------------------------------------
# Policy helpers
# ---------------------------------------------------------------------------


def _load_policy() -> dict[str, Any]:
    """Load the actor isolation policy.

    Expected schema:
    {
      "actors": {
        "<actor_id>": {
          "scopes": ["scope_a", "scope_b"],
          "role": "operator" | "root",
          "cross_access": ["<other_actor_id>", ...]
        }
      },
      "defaults": {
        "self_access": true,
        "cross_access": false
      }
    }
    """
    return load_optional_json(POLICY_FILE, default={})


def _load_registry() -> dict[str, Any]:
    """Load the runtime actor registry (state)."""
    return load_optional_json(REGISTRY_FILE, default={})


def _save_registry(registry: dict[str, Any]) -> None:
    save_json(REGISTRY_FILE, registry)


def _get_defaults(policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("defaults", {"self_access": True, "cross_access": False})


# ---------------------------------------------------------------------------
# Public interface functions
# ---------------------------------------------------------------------------


def register_actor(actor_id: str, scopes: list[str]) -> None:
    """Register an actor with its allowed scopes in the runtime registry."""
    registry = _load_registry()
    actors = registry.setdefault("actors", {})
    actors[actor_id] = {
        "scopes": scopes,
        "registered": True,
    }
    _save_registry(registry)
    audit_log_entry(GUARD_NAME, "REGISTER", f"actor='{actor_id}' scopes={scopes}")


def get_actor_scopes(actor_id: str) -> list[str]:
    """Return the scopes assigned to an actor.

    Checks the policy file first, then falls back to the runtime registry.
    """
    policy = _load_policy()
    policy_actors = policy.get("actors", {})
    if actor_id in policy_actors:
        return list(policy_actors[actor_id].get("scopes", []))

    registry = _load_registry()
    reg_actors = registry.get("actors", {})
    if actor_id in reg_actors:
        return list(reg_actors[actor_id].get("scopes", []))

    return []


def check_access(
    actor_id: str, resource_type: str, resource_owner: str
) -> tuple[bool, str]:
    """Check whether *actor_id* may access a resource owned by *resource_owner*.

    Returns:
        (allowed, reason) -- allowed is True if access is permitted.
    """
    policy = _load_policy()
    defaults = _get_defaults(policy)
    policy_actors = policy.get("actors", {})

    # Resolve actor config from policy, then registry
    actor_cfg = policy_actors.get(actor_id, {})
    if not actor_cfg:
        registry = _load_registry()
        actor_cfg = registry.get("actors", {}).get(actor_id, {})

    # Root actors bypass all isolation checks
    if actor_cfg.get("role") == "root":
        return True, "root actor -- unrestricted access"

    # Self-access is always allowed by default
    if normalize(actor_id) == normalize(resource_owner):
        if defaults.get("self_access", True):
            return True, "self-access permitted"

    # Check explicit cross-access grants
    cross_access_list = actor_cfg.get("cross_access", [])
    if resource_owner in cross_access_list:
        return True, f"explicit cross-access grant to '{resource_owner}'"

    # Check scope overlap (actor has a scope matching the owner's id or scope)
    actor_scopes = set(actor_cfg.get("scopes", []))
    if resource_owner in actor_scopes or f"read:{resource_owner}" in actor_scopes:
        return True, f"scope grants access to '{resource_owner}'"

    # Default: block cross-actor access
    if not defaults.get("cross_access", False):
        reason = (
            f"BLOCKED: actor '{actor_id}' cannot access {resource_type} "
            f"owned by '{resource_owner}'. No cross-access grant exists."
        )
        return False, reason

    # If default cross_access is True (permissive mode), allow
    return True, "default policy permits cross-access"


# ---------------------------------------------------------------------------
# Hook entrypoint (stdin JSON from Claude Code)
# ---------------------------------------------------------------------------


def _detect_actor_id() -> str:
    """Detect the current actor from environment or state."""
    # Prefer explicit env var
    actor = os.environ.get("TAG_ACTOR_ID", "").strip()
    if actor:
        return actor

    # Fall back to runtime state
    registry = _load_registry()
    return registry.get("active_actor", "")


def _extract_resource_owner(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    """Attempt to extract the resource owner from the tool invocation context.

    Looks for owner indicators in file paths, commands, and explicit metadata.
    """
    # Explicit owner in tool_input (custom integrations may supply this)
    if "resource_owner" in tool_input:
        return str(tool_input["resource_owner"])

    # Detect from file paths: pattern  .../actors/<owner>/...  or  .../memory/<owner>/...
    path = str(
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("command")
        or ""
    )
    path_norm = normalize(path)

    for marker in ("actors/", "memory/", "sessions/", "operators/"):
        idx = path_norm.find(marker)
        if idx != -1:
            remainder = path_norm[idx + len(marker) :]
            owner = remainder.split("/")[0] if "/" in remainder else remainder
            if owner:
                return owner

    return None


def _is_under_runtime_dir(path: str) -> str | None:
    """Check if a path falls under a TaG runtime directory.

    Returns:
        "audit" if path is under tag-runtime/audit/
        "context" if path is under tag-runtime/context/
        "state" if path is under tag-runtime/state/
        None if not under any protected runtime directory
    """
    path_norm = normalize(path)
    audit_prefix = normalize(str(AUDIT_DIR))
    context_prefix = normalize(str(CONTEXT_DIR))
    state_prefix = normalize(str(STATE_DIR))
    runtime_prefix = normalize(str(RUNTIME_DIR))

    if audit_prefix and path_norm.startswith(audit_prefix):
        return "audit"
    if context_prefix and path_norm.startswith(context_prefix):
        return "context"
    if state_prefix and path_norm.startswith(state_prefix):
        return "state"

    # Also catch relative paths containing the runtime segments
    for segment, label in (
        ("tag-runtime/audit/", "audit"),
        ("tag-runtime/context/", "context"),
        ("tag-runtime/state/", "state"),
    ):
        if segment in path_norm:
            return label

    # Catch anything else under tag-runtime/ (queue, config, etc.)
    if runtime_prefix and path_norm.startswith(runtime_prefix):
        return "runtime"
    if "tag-runtime/" in path_norm:
        return "runtime"

    return None


def _classify_resource_type(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Classify the resource type being accessed."""
    path = normalize(
        str(
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("command")
            or ""
        )
    )
    for rtype in MEMORY_RESOURCE_TYPES:
        if rtype in path:
            return rtype
    return "resource"


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    tool_name = str(input_data.get("tool_name", ""))
    tool_input = input_data.get("tool_input", {}) or {}

    # Determine actor
    actor_id = _detect_actor_id()
    if not actor_id:
        # No actor context -- cannot enforce isolation, pass through
        print(json.dumps({}))
        return 0

    # Determine resource owner
    resource_owner = _extract_resource_owner(tool_name, tool_input)
    if not resource_owner:
        # Check if path falls under a protected TaG runtime directory
        path = str(
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("command")
            or ""
        )
        runtime_zone = _is_under_runtime_dir(path)
        if runtime_zone:
            # Resolve actor config to check for root role
            policy = _load_policy()
            policy_actors = policy.get("actors", {})
            actor_cfg = policy_actors.get(actor_id, {})
            if not actor_cfg:
                registry = _load_registry()
                actor_cfg = registry.get("actors", {}).get(actor_id, {})

            if actor_cfg.get("role") == "root":
                # Root actors bypass all isolation checks
                print(json.dumps({}))
                return 0

            if runtime_zone == "audit":
                # Audit logs are system-wide; only root may access
                reason = (
                    f"BLOCKED: actor '{actor_id}' cannot access audit logs "
                    f"(root-only). Path: {path}"
                )
                audit_log_entry(GUARD_NAME, "BLOCK", reason)
                print(json.dumps({"decision": "block", "reason": reason}))
                return 0

            # context/ and state/ are session-scoped runtime files owned by
            # the active actor. If TAG_ACTOR_ID (or registry) resolved an
            # actor, that actor IS the session owner -- allow self-access.
            active_actor = os.environ.get("TAG_ACTOR_ID", "").strip()
            if active_actor and normalize(active_actor) == normalize(actor_id):
                # Active actor accessing their own session state -- allow
                print(json.dumps({}))
                return 0

            # No TAG_ACTOR_ID set (actor was resolved from registry fallback
            # only) -- cannot reliably verify session ownership, block access.
            if not active_actor:
                reason = (
                    f"BLOCKED: actor '{actor_id}' cannot access {runtime_zone} "
                    f"runtime path without TAG_ACTOR_ID set (session ownership "
                    f"unverifiable). Path: {path}"
                )
                audit_log_entry(GUARD_NAME, "BLOCK", reason)
                print(json.dumps({"decision": "block", "reason": reason}))
                return 0

            # TAG_ACTOR_ID is set but doesn't match the resolved actor --
            # cross-session access attempt, block it.
            reason = (
                f"BLOCKED: actor '{actor_id}' cannot access {runtime_zone} "
                f"runtime path belonging to active session of '{active_actor}'. "
                f"Path: {path}"
            )
            audit_log_entry(GUARD_NAME, "BLOCK", reason)
            print(json.dumps({"decision": "block", "reason": reason}))
            return 0

        # Path is clearly outside all protected directories -- pass through
        print(json.dumps({}))
        return 0

    # If actor is accessing their own resources, always allow
    if normalize(actor_id) == normalize(resource_owner):
        print(json.dumps({}))
        return 0

    # Enforce isolation
    resource_type = _classify_resource_type(tool_name, tool_input)
    allowed, reason = check_access(actor_id, resource_type, resource_owner)

    if not allowed:
        audit_log_entry(GUARD_NAME, "BLOCK", reason)
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    # Access permitted (with reason logged for auditing)
    if "cross-access" in reason or "scope" in reason:
        audit_log_entry(GUARD_NAME, "ALLOW_CROSS", reason)

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
