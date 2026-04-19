from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.policy.coding_protocol import load_coding_protocol


class TagCodingProtocolTests(unittest.TestCase):
    def test_default_protocol_requires_evidence_handles_for_completion(self) -> None:
        protocol = load_coding_protocol()
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
            with self.assertRaises(ValueError):
                load_coding_protocol(protocol_file)


if __name__ == "__main__":
    unittest.main()
