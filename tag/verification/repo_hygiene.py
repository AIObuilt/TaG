from __future__ import annotations

import json
from pathlib import Path

from tag_config import CONTEXT_DIR


REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"


def build_repo_hygiene_state(
    *,
    clean: bool,
    verification_artifacts_present: bool,
    touched_file_coverage_present: bool,
) -> dict:
    return {
        "clean": bool(clean),
        "verification_artifacts_present": bool(verification_artifacts_present),
        "touched_file_coverage_present": bool(touched_file_coverage_present),
    }


def write_repo_hygiene_state(
    *,
    clean: bool,
    verification_artifacts_present: bool,
    touched_file_coverage_present: bool,
    path: Path | None = None,
) -> dict:
    target = path or REPO_HYGIENE_FILE
    state = build_repo_hygiene_state(
        clean=clean,
        verification_artifacts_present=verification_artifacts_present,
        touched_file_coverage_present=touched_file_coverage_present,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state), encoding="utf-8")
    return state
