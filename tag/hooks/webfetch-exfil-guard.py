#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry


BLOCKED_DOMAINS = [
    "requestbin.com",
    "webhook.site",
    "hookbin.com",
    "pipedream.net",
    "ngrok.io",
    "ngrok.app",
    "pastebin.com",
]

PII_URL_PATTERNS = [
    r"\d{3}-\d{2}-\d{4}",
    r"[?&](api_?key|token|secret|password|credential|auth)=[A-Za-z0-9_\-]{20,}",
    r"eyJ[A-Za-z0-9_-]{20,}",
]


def extract_domain(url: str) -> str:
    domain = url.split("://", 1)[-1]
    domain = domain.split("/", 1)[0]
    domain = domain.split(":", 1)[0]
    return domain.lower()


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    if input_data.get("tool_name") != "WebFetch":
        print(json.dumps({}))
        return 0

    url = str((input_data.get("tool_input", {}) or {}).get("url", "") or "")
    domain = extract_domain(url)
    if any(domain == blocked or domain.endswith("." + blocked) for blocked in BLOCKED_DOMAINS):
        reason = (
            "BLOCKED: WebFetch to known data-capture service. "
            "This domain is commonly used for data exfiltration."
        )
        audit_log_entry("webfetch-exfil-guard", "BLOCK", f"{domain} | {url}")
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    for pattern in PII_URL_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            reason = "BLOCKED: URL contains a pattern that may encode sensitive data."
            audit_log_entry("webfetch-exfil-guard", "BLOCK", f"{pattern} | {url}")
            print(json.dumps({"decision": "block", "reason": reason}))
            return 0

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
