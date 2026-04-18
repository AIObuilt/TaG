#!/usr/bin/env python3
import json
import re
import sys

import _tag_bootstrap  # noqa: F401
from tag_config import CONFIG_DIR


CONFIG_PATH = CONFIG_DIR / "tag-skill-autoload-rules.json"

DEFAULT_RULES = [
    {
        "skill": "superpowers:writing-plans",
        "directive": "You must run the Skill(superpowers:writing-plans) tool before implementing TaG product changes.",
        "reason": "Prompt contains planning or implementation signals for the TaG product surface.",
        "keywords": ["plan", "implement", "feature", "build", "create", "design"],
    }
]


def load_rules() -> list[dict]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return DEFAULT_RULES


def find_matches(prompt: str, rules: list[dict]) -> list[dict]:
    normalized = prompt.lower()
    matched = []
    for rule in rules:
        for keyword in rule.get("keywords", []):
            if re.search(r"\b" + re.escape(keyword.lower()) + r"\b", normalized):
                matched.append(rule)
                break
    return matched


def main() -> int:
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    prompt = data.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        print("{}")
        return 0

    matches = find_matches(prompt, load_rules())
    if not matches:
        print("{}")
        return 0

    body = "\n\n".join(rule["directive"] for rule in matches)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[tag-skill-autoload] TaG product skills auto-triggered.\n\n{body}",
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
