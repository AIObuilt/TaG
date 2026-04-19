import sys
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tag" / "hooks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


def _run_hook(payload: dict, env: dict) -> dict:
    result = subprocess.run(
        ["python3", str(HOOKS / "repo-hygiene-gate.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


def _write_hygiene_state(tmp: str, payload: str) -> None:
    runtime = Path(tmp) / "tag-runtime" / "context"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "repo-hygiene.json").write_text(payload, encoding="utf-8")


def _run_hook_with_policy(payload: dict, policy: dict, env: dict) -> dict:
    child_env = {
        **env,
        "TAG_REPO_HYGIENE_ROOT": str(ROOT),
        "TAG_REPO_HYGIENE_PAYLOAD": json.dumps(payload),
        "TAG_REPO_HYGIENE_POLICY": json.dumps(policy),
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

        root = Path(os.environ["TAG_REPO_HYGIENE_ROOT"])
        hooks = root / "tag" / "hooks"
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        if str(hooks) not in sys.path:
            sys.path.insert(0, str(hooks))

        payload = json.loads(os.environ["TAG_REPO_HYGIENE_PAYLOAD"])
        policy = json.loads(os.environ["TAG_REPO_HYGIENE_POLICY"])
        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with patch("tag.policy.coding_protocol.load_coding_protocol", return_value=policy):
            with patch("sys.stdin", stdin), contextlib.redirect_stdout(stdout):
                try:
                    runpy.run_path(str(hooks / "repo-hygiene-gate.py"), run_name="__main__")
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


class TagRepoHygieneGateTests(unittest.TestCase):
    def test_blocks_release_claim_when_repo_marked_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_hygiene_state(
                tmp,
                json.dumps(
                    {
                        "clean": False,
                        "verification_artifacts_present": True,
                        "touched_file_coverage_present": True,
                    }
                ),
            )
            data = _run_hook({"claim_type": "release"}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("dirty", data["reason"])

    def test_allows_release_claim_when_repo_hygiene_state_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook({"claim_type": "release"}, env)
            self.assertEqual(data, {})

    def test_allows_complete_claim_when_repo_is_dirty_but_artifacts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_hygiene_state(
                tmp,
                json.dumps(
                    {
                        "clean": False,
                        "verification_artifacts_present": True,
                        "touched_file_coverage_present": True,
                    }
                ),
            )
            data = _run_hook({"claim_type": "complete"}, env)
            self.assertEqual(data, {})

    def test_blocks_claim_when_verification_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            _write_hygiene_state(
                tmp,
                json.dumps(
                    {
                        "clean": True,
                        "verification_artifacts_present": False,
                        "touched_file_coverage_present": True,
                    }
                ),
            )
            data = _run_hook({"claim_type": "complete"}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("verification-artifacts", data["reason"])

    def test_missing_state_does_not_imply_touched_file_coverage_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            policy = {
                "verification": {
                    "required_for_completion": True,
                    "require_evidence": True,
                },
                "repo_hygiene": {
                    "require_clean_release_state": True,
                    "require_verification_artifacts": True,
                    "require_touched_file_coverage": True,
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
            data = _run_hook_with_policy({"claim_type": "complete"}, policy, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("touched-file-coverage", data["reason"])

    def test_fails_closed_on_malformed_repo_hygiene_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            runtime = Path(tmp) / "tag-runtime" / "context"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "repo-hygiene.json").write_text("{not-json", encoding="utf-8")
            data = _run_hook({"claim_type": "release"}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("invalid", data["reason"])


if __name__ == "__main__":
    unittest.main()
