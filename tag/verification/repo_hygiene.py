from __future__ import annotations

import json
import sys
from pathlib import Path

from tag_config import CONTEXT_DIR


REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def build_repo_hygiene_state(
    *,
    clean: bool,
    verification_artifacts_present: bool,
    touched_file_coverage_present: bool,
) -> dict:
    return {
        "clean": _require_bool(clean, "clean"),
        "verification_artifacts_present": _require_bool(
            verification_artifacts_present, "verification_artifacts_present"
        ),
        "touched_file_coverage_present": _require_bool(
            touched_file_coverage_present, "touched_file_coverage_present"
        ),
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in {3, 4}:
        print(
            "usage: python -m tag.verification.repo_hygiene <clean:true|false> "
            "<verification_artifacts_present:true|false> <touched_file_coverage_present:true|false> [output_path]",
            file=sys.stderr,
        )
        return 2

    def parse_bool(raw: str, field_name: str) -> bool:
        value = raw.strip().lower()
        if value == "true":
            return True
        if value == "false":
            return False
        raise ValueError(f"{field_name} must be true or false")

    try:
        state = write_repo_hygiene_state(
            clean=parse_bool(args[0], "clean"),
            verification_artifacts_present=parse_bool(args[1], "verification_artifacts_present"),
            touched_file_coverage_present=parse_bool(args[2], "touched_file_coverage_present"),
            path=Path(args[3]) if len(args) == 4 else None,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
