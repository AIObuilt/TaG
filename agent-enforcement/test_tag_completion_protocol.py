from __future__ import annotations

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


def _run_hook(name: str, payload: dict, env: dict | None = None) -> dict:
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


def _write_evidence_record(tmp: str, evidence_id: str, kind: str, status: str) -> None:
    evidence_file = Path(tmp) / "tag-runtime" / "context" / "verification-evidence.jsonl"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "evidence_id": evidence_id,
        "kind": kind,
        "tool": "python3",
        "target": "test",
        "status": status,
        "summary": "test evidence",
        "artifacts": [],
        "timestamp": "2026-04-19T00:00:00+00:00",
    }
    evidence_file.write_text(json.dumps(record) + "\n", encoding="utf-8")


class TagCompletionProtocolTests(unittest.TestCase):
    def test_verification_gate_holds_when_no_code_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("verification", data["reason"])

    def test_verification_gate_ignores_non_code_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"work_type": "ui", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data, {})

    def test_verification_gate_requires_passing_code_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_evidence_record(tmp, "ev-qa-1", "qa", "pass")
            data = _run_hook(
                "verification-gate.py",
                {"work_type": "code", "evidence_ids": ["ev-qa-1"]},
                env=env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("code-evidence", data["reason"])

    def test_verification_gate_allows_passing_code_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_evidence_record(tmp, "ev-code-1", "code", "pass")
            data = _run_hook(
                "verification-gate.py",
                {"work_type": "code", "evidence_ids": ["ev-code-1"]},
                env=env,
            )
            self.assertEqual(data, {})

    def test_completion_claim_guard_blocks_done_claim_without_evidence_handles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {"response": "Done. The issue is fixed.", "work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data["decision"], "block")
            self.assertIn("evidence", data["reason"])

    def test_completion_claim_guard_ignores_non_code_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {"response": "Done. The issue is fixed.", "work_type": "ui", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
