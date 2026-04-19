#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag_config import VERIFICATION_EVIDENCE_FILE


def _evidence_ids(payload: dict) -> set[str]:
    raw_ids = payload.get("evidence_ids", [])
    if isinstance(raw_ids, list):
        return {str(evidence_id) for evidence_id in raw_ids if evidence_id}
    return set()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if payload.get("claim_type") not in {"complete", "release"}:
            print(json.dumps({}))
            return 0
        if payload.get("work_type") != "code":
            print(json.dumps({}))
            return 0
        if not protocol["verification"]["required_for_completion"]:
            print(json.dumps({}))
            return 0
        if not protocol["verification"]["require_evidence"]:
            print(json.dumps({}))
            return 0

        evidence_ids = _evidence_ids(payload)
        if not evidence_ids:
            print(json.dumps({"decision": "hold", "reason": "verification-evidence-required"}))
            return 0

        evidence = load_evidence_records(VERIFICATION_EVIDENCE_FILE)
        evidence_by_id = {
            str(row.get("evidence_id", "")): row
            for row in evidence
            if row.get("evidence_id")
        }
        for evidence_id in evidence_ids:
            row = evidence_by_id.get(evidence_id)
            if row and row.get("kind") == "code" and row.get("status") == "pass":
                print(json.dumps({}))
                return 0

        print(json.dumps({"decision": "hold", "reason": "verification-code-evidence-required"}))
        return 0
    except Exception:
        print(json.dumps({"decision": "hold", "reason": "verification-gate-error"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
