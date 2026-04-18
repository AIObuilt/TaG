from __future__ import annotations


def build_setup_snapshot(state: dict) -> dict:
    return {
        "mode": state.get("mode"),
        "runtime_path": state.get("runtime_path"),
        "governed": bool(state.get("governed")),
        "health": state.get("health", "unknown"),
    }
