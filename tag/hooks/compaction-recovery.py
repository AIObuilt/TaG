#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag_config import (
    HEARTBEAT_FILE,
    CHECKPOINT_FILE,
    COMPACTION_BUFFER_FILE,
    PROMPT_COUNTER_FILE,
)


MAX_BUFFER_AGE_MINUTES = 60


def load_heartbeat() -> dict:
    if HEARTBEAT_FILE.exists():
        try:
            return json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_compaction_buffer(state: dict) -> None:
    COMPACTION_BUFFER_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["saved_at"] = datetime.now().isoformat()
    COMPACTION_BUFFER_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def load_compaction_buffer() -> dict | None:
    if not COMPACTION_BUFFER_FILE.exists():
        return None
    try:
        data = json.loads(COMPACTION_BUFFER_FILE.read_text(encoding="utf-8"))
        saved_at = data.get("saved_at", "")
        if saved_at:
            saved_time = datetime.fromisoformat(saved_at)
            age_minutes = (datetime.now() - saved_time).total_seconds() / 60
            if age_minutes > MAX_BUFFER_AGE_MINUTES:
                return None
        return data
    except (json.JSONDecodeError, OSError, ValueError):
        return None


def consume_compaction_buffer() -> None:
    try:
        if COMPACTION_BUFFER_FILE.exists():
            COMPACTION_BUFFER_FILE.rename(COMPACTION_BUFFER_FILE.with_suffix(".consumed.json"))
    except Exception:
        pass


def load_prompt_counter() -> dict:
    if PROMPT_COUNTER_FILE.exists():
        try:
            return json.loads(PROMPT_COUNTER_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"count": 0, "session_start": datetime.now().isoformat()}


def save_prompt_counter(data: dict) -> None:
    PROMPT_COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_COUNTER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_recovery_context(buffer: dict) -> str:
    lines = ["CONTEXT RECOVERY (post-compaction):"]

    task = buffer.get("current_task", "")
    if task:
        lines.append(f"  CURRENT TASK: {task}")

    files = buffer.get("files_changed", [])
    if files:
        lines.append(f"  FILES IN PROGRESS: {', '.join(os.path.basename(f) for f in files[-10:])}")

    agents = buffer.get("agents_launched", [])
    if agents:
        lines.append(f"  AGENTS DISPATCHED: {len(agents)}")
        for agent in agents[-3:]:
            lines.append(f"    - {agent.get('desc', 'unknown')}")

    call_count = buffer.get("call_count", 0)
    if call_count:
        lines.append(f"  TOOL CALLS BEFORE COMPACTION: {call_count}")

    lines.append("")
    lines.append("  Read the TaG session checkpoint for full session state and continue where you left off.")
    return "\n".join(lines)


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    is_pre_compact = "summary" in input_data or "messages_count" in input_data

    if is_pre_compact:
        heartbeat = load_heartbeat()
        buffer = {
            "call_count": heartbeat.get("call_count", 0),
            "files_changed": heartbeat.get("files_changed", []),
            "files_read": heartbeat.get("files_read", [])[-10:],
            "agents_launched": heartbeat.get("agents_launched", []),
            "commands_run": heartbeat.get("commands_run", [])[-10:],
            "session_start": heartbeat.get("session_start", ""),
            "compacted_at": datetime.now().isoformat(),
        }

        if CHECKPOINT_FILE.exists():
            try:
                checkpoint = CHECKPOINT_FILE.read_text(encoding="utf-8")
                for line in checkpoint.split("\n"):
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or stripped.startswith("**"):
                        continue
                    buffer["current_task"] = stripped[:200]
                    break
            except Exception:
                pass

        save_compaction_buffer(buffer)
        print(json.dumps({}))
        return 0

    counter = load_prompt_counter()
    counter["count"] = counter.get("count", 0) + 1
    counter["last_prompt"] = datetime.now().isoformat()
    save_prompt_counter(counter)

    buffer = load_compaction_buffer()
    if buffer:
        recovery_context = build_recovery_context(buffer)
        consume_compaction_buffer()
        print(json.dumps({"message": recovery_context}))
        return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
