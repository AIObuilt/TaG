from __future__ import annotations

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


def _run_hook_with_policy(name: str, payload: dict, policy: dict, env: dict) -> dict:
    child_env = {
        **env,
        "TAG_COMPLETION_ROOT": str(ROOT),
        "TAG_COMPLETION_HOOK": name,
        "TAG_COMPLETION_PAYLOAD": json.dumps(payload),
        "TAG_COMPLETION_POLICY": json.dumps(policy),
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

        root = Path(os.environ["TAG_COMPLETION_ROOT"])
        hooks = root / "tag" / "hooks"
        hook_name = os.environ["TAG_COMPLETION_HOOK"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        if str(hooks) not in sys.path:
            sys.path.insert(0, str(hooks))

        payload = json.loads(os.environ["TAG_COMPLETION_PAYLOAD"])
        policy = json.loads(os.environ["TAG_COMPLETION_POLICY"])
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

    def test_verification_gate_holds_when_no_code_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"claim_type": "complete", "work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("verification", data["reason"])

    def test_verification_gate_ignores_non_code_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"claim_type": "complete", "work_type": "ui", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data, {})

    def test_verification_gate_ignores_non_completion_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"claim_type": "status", "work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data, {})

    def test_verification_gate_requires_passing_code_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_evidence_record(tmp, "ev-qa-1", "qa", "pass")
            data = _run_hook(
                "verification-gate.py",
                {"claim_type": "release", "work_type": "code", "evidence_ids": ["ev-qa-1"]},
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
                {"claim_type": "complete", "work_type": "code", "evidence_ids": ["ev-code-1"]},
                env=env,
            )
            self.assertEqual(data, {})

    def test_verification_gate_ignores_missing_evidence_when_policy_disables_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            policy = self._default_policy()
            policy["verification"]["require_evidence"] = False
            data = _run_hook_with_policy(
                "verification-gate.py",
                {"claim_type": "complete", "work_type": "code", "evidence_ids": []},
                policy,
                env,
            )
            self.assertEqual(data, {})

    def test_completion_claim_guard_blocks_final_claim_without_evidence_handles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {
                    "claim_type": "complete",
                    "response": "Done. The issue is fixed.",
                    "work_type": "code",
                    "evidence_ids": [],
                },
                env=env,
            )
            self.assertEqual(data["decision"], "block")
            self.assertIn("evidence", data["reason"])

    def test_completion_claim_guard_ignores_status_updates_with_done_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {
                    "claim_type": "status",
                    "response": "Ready for review. Fixed the flaky step, but verification is still running.",
                    "work_type": "code",
                    "evidence_ids": [],
                },
                env=env,
            )
            self.assertEqual(data, {})

    def test_completion_claim_guard_blocks_final_claim_in_response_without_claim_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {
                    "response": "Done. The issue is fixed.",
                    "work_type": "code",
                    "evidence_ids": [],
                },
                env=env,
            )
            self.assertEqual(data["decision"], "block")
            self.assertIn("evidence", data["reason"])

    def test_verification_gate_holds_final_claim_in_response_without_claim_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {
                    "response": "Done. The issue is fixed.",
                    "work_type": "code",
                    "evidence_ids": [],
                },
                env=env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("verification", data["reason"])

    def test_verification_gate_ignores_non_final_status_claim_type_even_with_strong_verbs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {
                    "claim_type": "status",
                    "response": "Fixed the flaky test; verification is still running.",
                    "work_type": "code",
                    "evidence_ids": [],
                },
                env=env,
            )
            self.assertEqual(data, {})

    def test_completion_claim_guard_allows_skip_reason_when_policy_explicitly_permits_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook_with_policy(
                "completion-claim-guard.py",
                {
                    "claim_type": "release",
                    "response": "Ready to release.",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "skip_reason": "Evidence handles are unavailable because this was validated in the upstream gated job.",
                },
                self._default_policy(),
                env,
            )
            self.assertEqual(data, {})

    def test_completion_claim_guard_blocks_skip_reason_when_policy_disallows_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            policy = self._default_policy()
            policy["completion"]["allow_skip_with_reason"] = False
            data = _run_hook_with_policy(
                "completion-claim-guard.py",
                {
                    "claim_type": "release",
                    "response": "Ready to release.",
                    "work_type": "ui",
                    "evidence_ids": [],
                    "skip_reason": "External pipeline has the evidence.",
                },
                policy,
                env,
            )
            self.assertEqual(data["decision"], "block")
            self.assertIn("evidence", data["reason"])


if __name__ == "__main__":
    unittest.main()
