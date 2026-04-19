from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tag.policy.coding_protocol as coding_protocol_module
from tag.policy.coding_protocol import load_coding_protocol


VALID_PROTOCOL = {
    "verification": {
        "required_for_completion": True,
        "require_evidence": True,
    },
    "repo_hygiene": {
        "require_clean_release_state": True,
        "require_verification_artifacts": True,
        "require_touched_file_coverage": False,
    },
    "browser_qa": {
        "required_for_ui_work": True,
        "allow_skip_with_reason": True,
    },
    "browser_security": {
        "required_for_preview_or_deploy_work": True,
        "allow_skip_with_reason": True,
    },
    "completion": {
        "require_evidence_handles": True,
        "allow_skip_with_reason": True,
    },
}


class TagCodingProtocolTests(unittest.TestCase):
    def test_default_protocol_requires_evidence_handles_for_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            protocol_file = Path(tmpdir) / "coding-protocol.json"
            protocol_file.write_text(json.dumps(VALID_PROTOCOL), encoding="utf-8")
            original = coding_protocol_module.CODING_PROTOCOL_FILE
            coding_protocol_module.CODING_PROTOCOL_FILE = protocol_file
            try:
                protocol = load_coding_protocol()
            finally:
                coding_protocol_module.CODING_PROTOCOL_FILE = original
        self.assertTrue(protocol["verification"]["required_for_completion"])
        self.assertTrue(protocol["completion"]["require_evidence_handles"])
        self.assertTrue(protocol["browser_qa"]["required_for_ui_work"])
        self.assertTrue(protocol["browser_security"]["required_for_preview_or_deploy_work"])

    def test_malformed_protocol_is_rejected_early(self) -> None:
        malformed = {
            "verification": {
                "required_for_completion": True,
                "require_evidence": True,
            },
            "browser_qa": {
                "required_for_ui_work": True,
                "allow_skip_with_reason": True,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            protocol_file = Path(tmpdir) / "coding-protocol.json"
            protocol_file.write_text(json.dumps(malformed), encoding="utf-8")
            original = coding_protocol_module.CODING_PROTOCOL_FILE
            coding_protocol_module.CODING_PROTOCOL_FILE = protocol_file
            try:
                with self.assertRaises(ValueError):
                    load_coding_protocol()
            finally:
                coding_protocol_module.CODING_PROTOCOL_FILE = original


if __name__ == "__main__":
    unittest.main()
