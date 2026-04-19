#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.final_claims import is_final_claim


def _evidence_ids(payload: dict) -> list[str]:
    raw_ids = payload.get("evidence_ids", [])
    if isinstance(raw_ids, list):
        return [str(evidence_id) for evidence_id in raw_ids if evidence_id]
    return []
def _skip_reason(payload: dict) -> str:
    return str(payload.get("skip_reason", "")).strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if not is_final_claim(payload):
            print(json.dumps({}))
            return 0
        if not protocol["completion"]["require_evidence_handles"]:
            print(json.dumps({}))
            return 0
        if protocol["completion"]["allow_skip_with_reason"] and _skip_reason(payload):
            print(json.dumps({}))
            return 0
        if _evidence_ids(payload):
            print(json.dumps({}))
            return 0

        print(json.dumps({"decision": "block", "reason": "completion-claim-missing-evidence-handles"}))
        return 0
    except Exception:
        print(json.dumps({"decision": "hold", "reason": "completion-claim-guard-error"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
