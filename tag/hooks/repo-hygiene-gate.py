#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag_config import CONTEXT_DIR, audit_log_path


AUDIT_LOG = audit_log_path("repo-hygiene-gate")
REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"
DEFAULT_PROTOCOL = {
    "repo_hygiene": {
        "require_clean_release_state": True,
        "require_verification_artifacts": True,
        "require_touched_file_coverage": False,
    }
}


def audit_log_entry(decision: str, reason: str) -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reason": reason,
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def load_repo_hygiene() -> dict:
    if not REPO_HYGIENE_FILE.exists():
        return {"clean": True, "verification_artifacts_present": True}
    try:
        data = json.loads(REPO_HYGIENE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"clean": True, "verification_artifacts_present": True}


def load_protocol() -> dict:
    try:
        return load_coding_protocol()
    except Exception:
        return DEFAULT_PROTOCOL


def hold(reason: str) -> int:
    audit_log_entry("hold", reason)
    print(json.dumps({"decision": "hold", "reason": reason}))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    claim_type = str(payload.get("claim_type", "")).strip().lower()
    if claim_type not in {"release", "complete"}:
        print(json.dumps({}))
        return 0

    protocol = load_protocol()
    hygiene_policy = protocol.get("repo_hygiene", DEFAULT_PROTOCOL["repo_hygiene"])
    state = load_repo_hygiene()

    if hygiene_policy.get("require_clean_release_state", True) and not state.get("clean", True):
        return hold("dirty-repo-state")

    if hygiene_policy.get("require_verification_artifacts", True) and not state.get(
        "verification_artifacts_present", True
    ):
        return hold("verification-artifacts-missing")

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
