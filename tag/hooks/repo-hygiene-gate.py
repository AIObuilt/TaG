#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag_config import CONTEXT_DIR


REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"
DEFAULT_REPO_HYGIENE = {
    "clean": True,
    "verification_artifacts_present": True,
    "touched_file_coverage_present": True,
}


def load_repo_hygiene() -> dict | None:
    if not REPO_HYGIENE_FILE.exists():
        return DEFAULT_REPO_HYGIENE.copy()
    try:
        data = json.loads(REPO_HYGIENE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def hold(reason: str) -> int:
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

    try:
        protocol = load_coding_protocol()
    except Exception:
        print(json.dumps({}))
        return 0

    state = load_repo_hygiene()
    if state is None:
        return hold("repo-hygiene-state-invalid")

    hygiene_policy = protocol["repo_hygiene"]

    if claim_type == "release" and hygiene_policy["require_clean_release_state"] and state.get("clean") is not True:
        return hold("dirty-repo-state")

    if hygiene_policy["require_verification_artifacts"] and state.get("verification_artifacts_present") is not True:
        return hold("verification-artifacts-missing")

    if hygiene_policy["require_touched_file_coverage"] and state.get("touched_file_coverage_present") is not True:
        return hold("touched-file-coverage-missing")

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
