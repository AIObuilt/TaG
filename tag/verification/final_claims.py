from __future__ import annotations

import re


FINAL_CLAIM_PATTERNS = (
    re.compile(r"^\s*(done|complete|completed|fixed|shipped)\b", re.IGNORECASE),
    re.compile(r"\b(issue|task|bug|work)\s+(is\s+)?fixed\b", re.IGNORECASE),
    re.compile(r"\bready\s+(to|for)\s+release\b", re.IGNORECASE),
    re.compile(r"\bready\b.*\b(deploy|ship)\b", re.IGNORECASE),
)


def claim_type(payload: dict) -> str:
    return str(payload.get("claim_type", "")).strip().lower()


def response_text(payload: dict) -> str:
    return str(payload.get("response", "")).strip()


def is_final_claim(payload: dict) -> bool:
    current_claim_type = claim_type(payload)
    if current_claim_type in {"complete", "release"}:
        return True
    if current_claim_type:
        return False
    response = response_text(payload)
    return any(pattern.search(response) for pattern in FINAL_CLAIM_PATTERNS)
