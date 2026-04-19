#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag_config import VERIFICATION_EVIDENCE_FILE


def _has_passed_qa_evidence(evidence_ids: list[str]) -> bool:
    evidence = {row.get("evidence_id"): row for row in load_evidence_records(VERIFICATION_EVIDENCE_FILE)}
    for evidence_id in evidence_ids:
        row = evidence.get(evidence_id)
        if row and row.get("kind") == "qa" and row.get("status") == "pass":
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if payload.get("work_type") != "ui" or not protocol["browser_qa"]["required_for_ui_work"]:
            print(json.dumps({}))
            return 0
        if _has_passed_qa_evidence(payload.get("evidence_ids", [])):
            print(json.dumps({}))
            return 0
        print(json.dumps({"decision": "hold", "reason": "browser-qa-evidence-required"}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
