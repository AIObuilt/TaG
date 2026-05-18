"""Role-based route restriction policy for the TaG governance framework.

Provides a generic mechanism to restrict actor access to specific execution
routes (paths, endpoints, tools, or any named target). Actors are assigned
roles, and each role declares which routes it may access and which are
explicitly denied.

JSON Policy Schema
==================

The policy file is a JSON object with the following structure:

{
  "roles": {
    "<role_name>": {
      "description": "Human-readable role description",
      "allow": ["<route>", ...],
      "deny": ["<route>", ...]
    }
  },
  "actors": {
    "<actor_id>": {
      "role": "<role_name>",
      "description": "Optional human-readable note"
    }
  },
  "defaults": {
    "unregistered_role": "deny",
    "unregistered_actor": "deny"
  }
}

Field definitions:

  roles (required): Mapping of role name to role definition.
    - allow (list[str]): Route targets this role may access.
      Use "*" as a single entry to allow all routes.
    - deny (list[str]): Route targets explicitly denied for this role.
      Deny entries override allow entries (including wildcards).
      Use "*" to deny all routes (effectively disabling the role).

  actors (required): Mapping of actor_id to actor assignment.
    - role (str): The role name assigned to this actor.
      Must reference a key in the "roles" object.
    - description (str, optional): Note about the actor.

  defaults (optional): Behavior for unregistered actors/roles.
    - unregistered_role (str): "deny" or "allow". Default: "deny".
      Applied when a role referenced by an actor is not defined.
    - unregistered_actor (str): "deny" or "allow". Default: "deny".
      Applied when an actor_id is not found in the actors map.

Predefined role conventions:

  "root"      - Full access, bypasses all restrictions (allow: ["*"], deny: [])
  "operator"  - Standard access, may have selective deny entries
  "managed"   - Restricted access, narrow allow list only

These names are conventions, not hard requirements. Any role names may be used.

Route matching:

  - Routes are matched as exact strings (case-sensitive).
  - The wildcard "*" in an allow list means "all routes are allowed".
  - The wildcard "*" in a deny list means "all routes are denied".
  - A route present in both allow and deny is DENIED (deny wins).

Example policy file:

{
  "roles": {
    "root": {
      "description": "Full system access",
      "allow": ["*"],
      "deny": []
    },
    "operator": {
      "description": "Standard operator with selective restrictions",
      "allow": ["*"],
      "deny": ["admin.shutdown", "admin.config.write"]
    },
    "managed": {
      "description": "Restricted to chat-only execution paths",
      "allow": ["chat.send", "chat.receive", "status.read"],
      "deny": []
    }
  },
  "actors": {
    "actor-001": {"role": "root"},
    "actor-002": {"role": "operator", "description": "Standard user"},
    "actor-003": {"role": "managed", "description": "Managed service actor"}
  },
  "defaults": {
    "unregistered_role": "deny",
    "unregistered_actor": "deny"
  }
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RoleDefinition:
    """Defines allowed and denied routes for a single role."""

    name: str
    description: str = ""
    allow: list[str] = field(default_factory=list)
    deny: list[str] = field(default_factory=list)


@dataclass
class ActorAssignment:
    """Maps an actor to a role."""

    actor_id: str
    role: str
    description: str = ""


@dataclass
class RoutePolicy:
    """Complete route restriction policy."""

    roles: dict[str, RoleDefinition] = field(default_factory=dict)
    actors: dict[str, ActorAssignment] = field(default_factory=dict)
    default_unregistered_role: str = "deny"
    default_unregistered_actor: str = "deny"


def load_policy(path: Path | str) -> RoutePolicy:
    """Load a RoutePolicy from a JSON file.

    Args:
        path: Path to the policy JSON file.

    Returns:
        A populated RoutePolicy instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON structure is invalid.
    """
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_policy(raw)


def parse_policy(raw: dict[str, Any]) -> RoutePolicy:
    """Parse a RoutePolicy from a dictionary (already-deserialized JSON).

    Args:
        raw: Dictionary matching the policy JSON schema.

    Returns:
        A populated RoutePolicy instance.

    Raises:
        ValueError: If required fields are missing or malformed.
    """
    if not isinstance(raw, dict):
        raise ValueError("policy must be a JSON object")

    raw_roles = raw.get("roles")
    if not isinstance(raw_roles, dict):
        raise ValueError("policy.roles must be an object")

    roles: dict[str, RoleDefinition] = {}
    for role_name, role_def in raw_roles.items():
        if not isinstance(role_name, str) or not role_name:
            raise ValueError("role names must be non-empty strings")
        if not isinstance(role_def, dict):
            raise ValueError(f"roles.{role_name} must be an object")
        allow = _require_string_list(role_def.get("allow", []), f"roles.{role_name}.allow")
        deny = _require_string_list(role_def.get("deny", []), f"roles.{role_name}.deny")
        description = str(role_def.get("description", ""))
        roles[role_name] = RoleDefinition(
            name=role_name,
            description=description,
            allow=allow,
            deny=deny,
        )

    raw_actors = raw.get("actors")
    if not isinstance(raw_actors, dict):
        raise ValueError("policy.actors must be an object")

    actors: dict[str, ActorAssignment] = {}
    for actor_id, actor_def in raw_actors.items():
        if not isinstance(actor_id, str) or not actor_id:
            raise ValueError("actor IDs must be non-empty strings")
        if not isinstance(actor_def, dict):
            raise ValueError(f"actors.{actor_id} must be an object")
        role = actor_def.get("role", "")
        if not isinstance(role, str) or not role:
            raise ValueError(f"actors.{actor_id}.role must be a non-empty string")
        description = str(actor_def.get("description", ""))
        actors[actor_id] = ActorAssignment(
            actor_id=actor_id,
            role=role,
            description=description,
        )

    defaults = raw.get("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}

    default_unregistered_role = defaults.get("unregistered_role", "deny")
    if default_unregistered_role not in ("deny", "allow"):
        default_unregistered_role = "deny"

    default_unregistered_actor = defaults.get("unregistered_actor", "deny")
    if default_unregistered_actor not in ("deny", "allow"):
        default_unregistered_actor = "deny"

    return RoutePolicy(
        roles=roles,
        actors=actors,
        default_unregistered_role=default_unregistered_role,
        default_unregistered_actor=default_unregistered_actor,
    )


def check_route(actor_id: str, route_target: str, policy: RoutePolicy) -> tuple[bool, str]:
    """Evaluate whether an actor may access a given route target.

    Resolution order:
      1. If the actor is not registered, apply the unregistered_actor default.
      2. If the actor's role is not defined, apply the unregistered_role default.
      3. If the route is in the role's deny list (or deny contains "*"), DENY.
      4. If the role's allow list contains "*", ALLOW.
      5. If the route is in the role's allow list, ALLOW.
      6. Otherwise, DENY (route not explicitly allowed).

    Args:
        actor_id: Identifier for the actor requesting access.
        route_target: The route/path/tool/endpoint being accessed.
        policy: The loaded RoutePolicy to evaluate against.

    Returns:
        A tuple of (allowed: bool, reason: str) explaining the decision.
    """
    # Step 1: Check if actor is registered.
    assignment = policy.actors.get(actor_id)
    if assignment is None:
        if policy.default_unregistered_actor == "allow":
            return True, "unregistered actor; default policy is allow"
        return False, "actor not registered in policy"

    # Step 2: Resolve the role.
    role_name = assignment.role
    role = policy.roles.get(role_name)
    if role is None:
        if policy.default_unregistered_role == "allow":
            return True, f"role '{role_name}' not defined; default policy is allow"
        return False, f"role '{role_name}' not defined in policy"

    # Step 3: Check explicit deny.
    if "*" in role.deny:
        return False, f"role '{role_name}' denies all routes"
    if route_target in role.deny:
        return False, f"route '{route_target}' explicitly denied for role '{role_name}'"

    # Step 4: Check wildcard allow.
    if "*" in role.allow:
        return True, f"role '{role_name}' allows all routes"

    # Step 5: Check explicit allow.
    if route_target in role.allow:
        return True, f"route '{route_target}' allowed for role '{role_name}'"

    # Step 6: Default deny (route not in allow list).
    return False, f"route '{route_target}' not in allow list for role '{role_name}'"


def _require_string_list(value: Any, field_name: str) -> list[str]:
    """Validate that a value is a list of strings."""
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{field_name}[{i}] must be a string")
    return list(value)
