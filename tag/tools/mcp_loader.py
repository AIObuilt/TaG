#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


AVAILABLE_SERVERS = {
    "debugger": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@debugmcp/mcp-debugger"],
        "env": {},
    },
    "sequential-thinking": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        "env": {},
    },
    "memory-bridge": {
        "type": "stdio",
        "command": "python3",
        "args": ["tag/tools/memory_bridge.py"],
        "env": {},
    },
}


def load_config(path: Path) -> dict:
    if not path.exists():
        return {"mcpServers": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def cmd_available() -> int:
    print(f"Available TaG MCP servers ({len(AVAILABLE_SERVERS)}):")
    for name in sorted(AVAILABLE_SERVERS):
        print(f"  - {name}")
    return 0


def cmd_add(config_path: Path, names: list[str]) -> int:
    config = load_config(config_path)
    servers = config.setdefault("mcpServers", {})
    added = 0
    for name in names:
        if name in servers:
            continue
        spec = AVAILABLE_SERVERS.get(name)
        if not spec:
            print(f"Unknown server: {name}", file=sys.stderr)
            return 1
        servers[name] = spec
        added += 1
    save_config(config_path, config)
    print(f"Added {added} server{'s' if added != 1 else ''}")
    return 0


def cmd_remove(config_path: Path, names: list[str]) -> int:
    config = load_config(config_path)
    servers = config.setdefault("mcpServers", {})
    removed = 0
    for name in names:
        if name in servers:
            del servers[name]
            removed += 1
    save_config(config_path, config)
    print(f"Removed {removed} server{'s' if removed != 1 else ''}")
    return 0


def cmd_list(config_path: Path) -> int:
    config = load_config(config_path)
    servers = config.get("mcpServers", {})
    print(f"Configured TaG MCP servers ({len(servers)}):")
    for name in sorted(servers):
        print(f"  - {name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage product-safe TaG MCP server config.")
    parser.add_argument("--config", type=Path, default=Path("tag-runtime/config/mcp.json"))
    parser.add_argument("command", choices=["add", "remove", "list", "available"])
    parser.add_argument("names", nargs="*")
    args = parser.parse_args()

    if args.command == "available":
        return cmd_available()
    if args.command == "list":
        return cmd_list(args.config)
    if args.command == "add":
        return cmd_add(args.config, args.names)
    return cmd_remove(args.config, args.names)


if __name__ == "__main__":
    raise SystemExit(main())
