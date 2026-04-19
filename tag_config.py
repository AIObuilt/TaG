from __future__ import annotations

import os
from pathlib import Path


PRODUCT_NAME = "TaG"
RUNTIME_DIR_NAME = "tag-runtime"
CONFIG_DIR_NAME = "config"


def _find_tag_home() -> Path:
    env = os.environ.get("TAG_HOME")
    if env:
        candidate = Path(env)
        if candidate.is_dir():
            return candidate

    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        if (ancestor / ".tag-root").exists():
            return ancestor
        if ancestor == ancestor.parent:
            break
    return here


TAG_HOME = _find_tag_home()
RUNTIME_DIR = TAG_HOME / RUNTIME_DIR_NAME
CONTEXT_DIR = RUNTIME_DIR / "context"
STATE_DIR = RUNTIME_DIR / "state"
QUEUE_DIR = RUNTIME_DIR / "queue"
AUDIT_DIR = RUNTIME_DIR / "audit"
CONFIG_DIR = TAG_HOME / CONFIG_DIR_NAME
HOOKS_DIR = TAG_HOME / "tag" / "hooks"
RUNTIME_CONFIG_DIR = RUNTIME_DIR / "config"

HEARTBEAT_FILE = CONTEXT_DIR / "heartbeat.json"
CHECKPOINT_FILE = CONTEXT_DIR / "session-checkpoint.md"
CRASHED_SESSIONS_FILE = CONTEXT_DIR / "crashed-sessions.json"
LAST_SESSION_FILE = CONTEXT_DIR / "last-session-activity.md"
COMPACTION_BUFFER_FILE = CONTEXT_DIR / "compaction-buffer.json"
PROMPT_COUNTER_FILE = CONTEXT_DIR / "prompt-counter.json"
SESSION_MEMORY_FILE = CONTEXT_DIR / "session-memory.json"
BUILD_STATUS_FILE = CONTEXT_DIR / "build-status.json"
SECURITY_VERDICT_FILE = CONTEXT_DIR / "security-verdict.json"
DEPLOY_STATE_FILE = CONTEXT_DIR / "deploy-state.json"
VERIFICATION_EVIDENCE_FILE = CONTEXT_DIR / "verification-evidence.jsonl"
VERIFICATION_STATUS_FILE = CONTEXT_DIR / "verification-status.json"
FORK_SCOPE_STATE = STATE_DIR / "fork-scope.json"
DELEGATE_BYPASS_FILE = STATE_DIR / "delegate-bypass.json"
AUTHORITY_MATRIX_FILE = RUNTIME_CONFIG_DIR / "authority-matrix.json"


def audit_log_path(name: str) -> Path:
    return AUDIT_DIR / f"{name}.jsonl"
