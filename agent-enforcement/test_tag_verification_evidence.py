import json
import sys
import tempfile
import unittest
from datetime import datetime
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

    def test_append_generates_timestamp_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_file = Path(tmp) / "verification-evidence.jsonl"
            record = EvidenceRecord(
                evidence_id="ev-2",
                kind="code",
                tool="python3",
                target="python3 -m unittest",
                status="pass",
                summary="timestamp is generated",
            )
            payload = append_evidence_record(evidence_file, record)
            loaded = load_evidence_records(evidence_file)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["timestamp"], payload["timestamp"])
            self.assertTrue(payload["timestamp"])
            datetime.fromisoformat(payload["timestamp"])

    def test_load_evidence_records_skips_malformed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_file = Path(tmp) / "verification-evidence.jsonl"
            evidence_file.write_text(
                "\n".join(
                    [
                        '{"evidence_id":"ev-3","kind":"code","tool":"python3","target":"ok","status":"pass","summary":"good","artifacts":[],"timestamp":"2026-04-19T12:00:00+00:00"}',
                        '{"evidence_id":"broken"',
                        '{"evidence_id":"ev-4","kind":"code","tool":"python3","target":"ok","status":"pass","summary":"good","artifacts":[],"timestamp":"2026-04-19T12:00:01+00:00"}',
                    ]
                ),
                encoding="utf-8",
            )
            records = load_evidence_records(evidence_file)
            self.assertEqual(len(records), 2)
            self.assertEqual([record["evidence_id"] for record in records], ["ev-3", "ev-4"])


if __name__ == "__main__":
    unittest.main()
