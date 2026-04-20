from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from tag_config import HEARTBEAT_FILE, CONTEXT_DIR


class Heartbeat:
    def __init__(self, path: Path = HEARTBEAT_FILE):
        self.path = path

    def pulse(self, *, call_count: int = 0, files_changed: list[str] | None = None,
              files_read: list[str] | None = None, agents: list[str] | None = None,
              commands: list[str] | None = None, session_id: str = "") -> None:
        """Update the heartbeat with current session activity."""
        state = self.read()
        state["last_pulse"] = datetime.now().isoformat()
        state["call_count"] = call_count or state.get("call_count", 0)
        state["session_id"] = session_id or state.get("session_id", "")
        if files_changed:
            existing = state.get("files_changed", [])
            state["files_changed"] = list(dict.fromkeys(existing + files_changed))[-50:]
        if files_read:
            existing = state.get("files_read", [])
            state["files_read"] = list(dict.fromkeys(existing + files_read))[-50:]
        if agents:
            existing = state.get("agents", [])
            state["agents"] = list(dict.fromkeys(existing + agents))[-20:]
        if commands:
            existing = state.get("commands", [])
            state["commands"] = list(dict.fromkeys(existing + commands))[-20:]
        self._write(state)

    def read(self) -> dict:
        """Read current heartbeat state."""
        if not self.path.exists():
            return {"last_pulse": None, "call_count": 0, "session_id": "",
                    "files_changed": [], "files_read": [], "agents": [], "commands": [],
                    "cleanly_ended": False}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"last_pulse": None, "call_count": 0}

    def is_alive(self, max_age_seconds: int = 300) -> bool:
        """Check if heartbeat is recent enough to be considered alive."""
        state = self.read()
        last = state.get("last_pulse")
        if not last:
            return False
        try:
            dt = datetime.fromisoformat(last)
            age = (datetime.now() - dt).total_seconds()
            return age < max_age_seconds
        except (ValueError, TypeError):
            return False

    def end_session(self) -> None:
        """Mark session as cleanly ended."""
        state = self.read()
        state["cleanly_ended"] = True
        state["ended_at"] = datetime.now().isoformat()
        self._write(state)

    def _write(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")
