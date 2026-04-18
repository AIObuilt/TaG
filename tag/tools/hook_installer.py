#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tag_config


def build_manifest() -> dict:
    hooks_dir = tag_config.HOOKS_DIR
    hooks = []
    for path in sorted(hooks_dir.glob("*.py")):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        hooks.append(
            {
                "name": path.stem,
                "path": str(path.relative_to(tag_config.TAG_HOME)).replace("\\", "/"),
                "runtime": "python3",
            }
        )
    return {
        "product": tag_config.PRODUCT_NAME,
        "hooks_dir": str(hooks_dir.relative_to(tag_config.TAG_HOME)).replace("\\", "/"),
        "hooks": hooks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a product-safe TaG hook manifest.")
    parser.add_argument("--output", required=True, help="Path to write the manifest JSON")
    args = parser.parse_args()

    manifest = build_manifest()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
