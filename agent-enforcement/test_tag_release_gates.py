import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TagReleaseGateTests(unittest.TestCase):
    def test_build_gate_blocks_push_without_current_session_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            context = Path(tmp) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            (context / "build-status.json").write_text(
                json.dumps({"passed": True, "session_id": "old-session"}),
                encoding="utf-8",
            )
            payload = json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "git push"},
                "session_id": "new-session",
            })
            result = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "build-gate.py")],
                input=payload,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("different session", data["reason"])

    def test_security_gate_blocks_commit_without_pass_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            context = Path(tmp) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            (context / "security-verdict.json").write_text(
                json.dumps({"verdict": "FAIL", "session_id": "sess-1", "summary": "secret leak"}),
                encoding="utf-8",
            )
            payload = json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m 'x'"},
                "session_id": "sess-1",
            })
            result = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "security-gate.py")],
                input=payload,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("FAILED", data["reason"])

    def test_qa_gate_blocks_non_qa_tool_when_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            context = Path(tmp) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            (context / "deploy-state.json").write_text(
                json.dumps({"pending_qa": True, "deploys": [{"url": "https://app.tag.local", "qa_completed": False}]}),
                encoding="utf-8",
            )
            payload = json.dumps({
                "tool_name": "Write",
                "tool_input": {"file_path": "tag/hooks/build-gate.py"},
            })
            result = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "qa-gate.py")],
                input=payload,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("QA GATE", data["reason"])


if __name__ == "__main__":
    unittest.main()
