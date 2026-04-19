#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag_config import CONTEXT_DIR


REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"
def load_repo_hygiene() -> tuple[str, dict | None]:
    if not REPO_HYGIENE_FILE.exists():
        return "missing", None
    try:
        data = json.loads(REPO_HYGIENE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "invalid", None
    if not isinstance(data, dict):
        return "invalid", None
    return "present", data


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
        return hold("coding-protocol-unavailable")

    state_status, state = load_repo_hygiene()
    if state_status == "missing":
        return hold("repo-hygiene-state-missing")
    if state_status == "invalid" or state is None:
        return hold("repo-hygiene-state-invalid")

    hygiene_policy = protocol["repo_hygiene"]

    if claim_type in {"release", "complete"} and hygiene_policy["require_clean_release_state"] and state.get("clean") is not True:
        return hold("dirty-repo-state")

    if hygiene_policy["require_verification_artifacts"] and state.get("verification_artifacts_present") is not True:
        return hold("verification-artifacts-missing")

    if hygiene_policy["require_touched_file_coverage"] and state.get("touched_file_coverage_present") is not True:
        return hold("touched-file-coverage-missing")

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
