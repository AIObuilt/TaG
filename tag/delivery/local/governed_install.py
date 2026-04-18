from __future__ import annotations


def can_complete_setup(state: dict) -> bool:
    return bool(state.get("governed") is True)
