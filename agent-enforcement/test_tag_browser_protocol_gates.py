import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tag" / "hooks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.evidence import EvidenceRecord, append_evidence_record


def _run_hook(name: str, payload: dict, env: dict) -> dict:
    result = subprocess.run(
        ["python3", str(HOOKS / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


class TagBrowserProtocolGateTests(unittest.TestCase):
    def test_qa_gate_holds_ui_work_without_qa_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-qa-gate.py",
                {"work_type": "ui", "evidence_ids": [], "target": "https://app.example.test"},
                env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("qa", data["reason"])

    def test_qa_gate_holds_ui_work_with_stale_qa_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            evidence_file = Path(tmp) / "tag-runtime" / "context" / "verification-evidence.jsonl"
            append_evidence_record(
                evidence_file,
                EvidenceRecord(
                    evidence_id="ev-qa-1",
                    kind="qa",
                    tool="playwright",
                    target="https://old.example.test",
                    status="pass",
                    summary="baseline qa passed for an older target",
                    artifacts=[],
                ),
            )
            data = _run_hook(
                "playwright-qa-gate.py",
                {
                    "work_type": "ui",
                    "evidence_ids": ["ev-qa-1"],
                    "target": "https://app.example.test",
                },
                env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("qa", data["reason"])

    def test_qa_gate_allows_skip_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-qa-gate.py",
                {
                    "work_type": "ui",
                    "evidence_ids": [],
                    "target": "https://app.example.test",
                    "skip_reason": "manual QA already completed in another system",
                },
                env,
            )
            self.assertEqual(data, {})

    def test_security_gate_allows_preview_work_when_security_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            evidence_file = Path(tmp) / "tag-runtime" / "context" / "verification-evidence.jsonl"
            append_evidence_record(
                evidence_file,
                EvidenceRecord(
                    evidence_id="ev-sec-1",
                    kind="security",
                    tool="playwright",
                    target="https://preview.example.test",
                    status="pass",
                    summary="baseline browser security passed",
                    artifacts=[],
                ),
            )
            data = _run_hook(
                "playwright-security-gate.py",
                {"work_type": "preview", "evidence_ids": ["ev-sec-1"], "target": "https://preview.example.test"},
                env,
            )
            self.assertEqual(data, {})

    def test_security_gate_holds_preview_work_without_security_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-security-gate.py",
                {"work_type": "preview", "evidence_ids": [], "target": "https://preview.example.test"},
                env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("security", data["reason"])


if __name__ == "__main__":
    unittest.main()
