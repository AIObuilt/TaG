#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag.verification.final_claims import is_final_claim
from tag_config import VERIFICATION_EVIDENCE_FILE


def _normalize_target(value: object) -> str:
    return str(value or "").strip()


def _evidence_ids(payload: dict) -> list[str]:
    raw_ids = payload.get("evidence_ids", [])
    if isinstance(raw_ids, list):
        return [str(evidence_id) for evidence_id in raw_ids if evidence_id]
    return []


def _has_passed_security_evidence(evidence_ids: list[str], target: str) -> bool:
    evidence = {row.get("evidence_id"): row for row in load_evidence_records(VERIFICATION_EVIDENCE_FILE)}
    for evidence_id in evidence_ids:
        row = evidence.get(evidence_id)
        if (
            row
            and row.get("kind") == "security"
            and row.get("status") == "pass"
            and _normalize_target(row.get("target")) == target
        ):
            return True
    return False


def _has_skip_reason(payload: dict, protocol: dict) -> bool:
    if not protocol["browser_security"]["allow_skip_with_reason"]:
        return False
    return bool(_normalize_target(payload.get("skip_reason")))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if not is_final_claim(payload):
            print(json.dumps({}))
            return 0
        if payload.get("work_type") not in {"preview", "deploy"} or not protocol["browser_security"]["required_for_preview_or_deploy_work"]:
            print(json.dumps({}))
            return 0
        target = _normalize_target(payload.get("target"))
        if _has_skip_reason(payload, protocol):
            print(json.dumps({}))
            return 0
        if _has_passed_security_evidence(_evidence_ids(payload), target):
            print(json.dumps({}))
            return 0
        print(json.dumps({"decision": "hold", "reason": "browser-security-evidence-required"}))
        return 0
    except Exception:
        print(json.dumps({"decision": "hold", "reason": "browser-security-gate-error"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
