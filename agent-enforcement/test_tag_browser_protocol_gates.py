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
            data = _run_hook("playwright-qa-gate.py", {"work_type": "ui", "evidence_ids": []}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("qa", data["reason"])

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
                {"work_type": "preview", "evidence_ids": ["ev-sec-1"]},
                env,
            )
            self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
