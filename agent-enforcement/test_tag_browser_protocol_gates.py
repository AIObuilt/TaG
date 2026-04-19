import json
import os
import subprocess
import sys
import tempfile
import textwrap
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


def _run_hook_with_policy(name: str, payload: dict, policy: dict, env: dict) -> dict:
    child_env = {
        **env,
        "TAG_BROWSER_ROOT": str(ROOT),
        "TAG_BROWSER_HOOK": name,
        "TAG_BROWSER_PAYLOAD": json.dumps(payload),
        "TAG_BROWSER_POLICY": json.dumps(policy),
    }
    script = textwrap.dedent(
        """
        import contextlib
        import io
        import json
        import os
        import runpy
        import sys
        from pathlib import Path
        from unittest.mock import patch

        root = Path(os.environ["TAG_BROWSER_ROOT"])
        hooks = root / "tag" / "hooks"
        hook_name = os.environ["TAG_BROWSER_HOOK"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        if str(hooks) not in sys.path:
            sys.path.insert(0, str(hooks))

        payload = json.loads(os.environ["TAG_BROWSER_PAYLOAD"])
        policy = json.loads(os.environ["TAG_BROWSER_POLICY"])
        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with patch("tag.policy.coding_protocol.load_coding_protocol", return_value=policy):
            with patch("sys.stdin", stdin), contextlib.redirect_stdout(stdout):
                try:
                    runpy.run_path(str(hooks / hook_name), run_name="__main__")
                except SystemExit as exc:
                    if exc.code not in (0, None):
                        raise AssertionError(f"hook exited with {exc.code}")

        print(stdout.getvalue(), end="")
        """
    )
    result = subprocess.run(
        ["python3", "-c", script],
        capture_output=True,
        text=True,
        env=child_env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


class TagBrowserProtocolGateTests(unittest.TestCase):
    def _default_policy(self) -> dict:
        return {
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

    def test_qa_gate_holds_ui_work_without_qa_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-qa-gate.py",
                {
                    "claim_type": "complete",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "target": "https://app.example.test",
                },
                env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("qa", data["reason"])

    def test_qa_gate_ignores_status_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-qa-gate.py",
                {
                    "claim_type": "status",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "target": "https://app.example.test",
                },
                env,
            )
            self.assertEqual(data, {})

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
                    "claim_type": "complete",
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
                    "claim_type": "complete",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "target": "https://app.example.test",
                    "skip_reason": "manual QA already completed in another system",
                },
                env,
            )
            self.assertEqual(data, {})

    def test_qa_gate_blocks_skip_reason_when_policy_disallows_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            policy = self._default_policy()
            policy["browser_qa"]["allow_skip_with_reason"] = False
            data = _run_hook_with_policy(
                "playwright-qa-gate.py",
                {
                    "claim_type": "complete",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "target": "https://app.example.test",
                    "skip_reason": "manual QA already completed in another system",
                },
                policy,
                env,
            )
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
                {
                    "claim_type": "release",
                    "work_type": "preview",
                    "evidence_ids": ["ev-sec-1"],
                    "target": "https://preview.example.test",
                },
                env,
            )
            self.assertEqual(data, {})

    def test_security_gate_holds_preview_work_without_security_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-security-gate.py",
                {
                    "claim_type": "release",
                    "work_type": "preview",
                    "evidence_ids": [],
                    "target": "https://preview.example.test",
                },
                env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("security", data["reason"])

    def test_security_gate_ignores_in_progress_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "playwright-security-gate.py",
                {
                    "claim_type": "status",
                    "work_type": "preview",
                    "evidence_ids": [],
                    "target": "https://preview.example.test",
                },
                env,
            )
            self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
