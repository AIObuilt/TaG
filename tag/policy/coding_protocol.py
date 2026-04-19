from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODING_PROTOCOL_FILE = HERE.parent / "config" / "coding-protocol.json"


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_section(protocol: dict, section_name: str, field_names: tuple[str, ...]) -> dict:
    section = protocol.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"{section_name} must be an object")
    for field_name in field_names:
        _require_bool(section.get(field_name), f"{section_name}.{field_name}")
    return section


def _validate_coding_protocol(protocol: object) -> dict:
    if not isinstance(protocol, dict):
        raise ValueError("coding protocol must be a JSON object")
    _require_section(protocol, "verification", ("required_for_completion", "require_evidence"))
    _require_section(
        protocol,
        "repo_hygiene",
        ("require_clean_release_state", "require_verification_artifacts", "require_touched_file_coverage"),
    )
    _require_section(protocol, "browser_qa", ("required_for_ui_work", "allow_skip_with_reason"))
    _require_section(
        protocol,
        "browser_security",
        ("required_for_preview_or_deploy_work", "allow_skip_with_reason"),
    )
    _require_section(protocol, "completion", ("require_evidence_handles", "allow_skip_with_reason"))
    return protocol


def load_coding_protocol(path: Path | None = None) -> dict:
    target = path or CODING_PROTOCOL_FILE
    return _validate_coding_protocol(json.loads(target.read_text(encoding="utf-8")))
