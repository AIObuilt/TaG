import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.evidence import EvidenceRecord, append_evidence_record, load_evidence_records


class TagVerificationEvidenceTests(unittest.TestCase):
    def test_append_and_load_evidence_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_file = Path(tmp) / "verification-evidence.jsonl"
            record = EvidenceRecord(
                evidence_id="ev-1",
                kind="code",
                tool="python3",
                target="python3 -m unittest",
                status="pass",
                summary="core suite passed",
                artifacts=["agent-enforcement/test_tag_policy_model.py"],
            )
            append_evidence_record(evidence_file, record)
            records = load_evidence_records(evidence_file)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["evidence_id"], "ev-1")
            self.assertEqual(records[0]["kind"], "code")
            self.assertEqual(records[0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
