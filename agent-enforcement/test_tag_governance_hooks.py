import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


TAG_HOOKS = Path(__file__).resolve().parents[1] / "tag" / "hooks"


def _run_hook(hook_name: str, payload: dict, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(TAG_HOOKS / hook_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class TagGovernanceHookTests(unittest.TestCase):
    def test_delegate_enforcer_blocks_direct_project_write_without_subagent_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            payload = {
                "tool_name": "Write",
                "tool_input": {"file_path": "/workspace/customer/project/app.py"},
                "session_id": "sess-1",
            }
            result = _run_hook("delegate-enforcer.py", payload, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("delegate", data["reason"].lower())

    def test_agent_enforcer_warns_when_session_has_no_agents_after_many_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            context = Path(tmp) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            (context / "heartbeat.json").write_text(
                json.dumps({"call_count": 18, "agents_launched": [], "calls_since_last_agent": 18}),
                encoding="utf-8",
            )
            result = _run_hook("agent-enforcer.py", {"response": "I will now inspect and edit files directly."}, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("message", data)
            self.assertIn("DELEGATION", data["message"])

    def test_os_acl_enforcer_blocks_cross_fork_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            state_dir = Path(tmp) / "tag-runtime" / "state"
            config_dir = Path(tmp) / "tag-runtime" / "config"
            state_dir.mkdir(parents=True)
            config_dir.mkdir(parents=True)
            (state_dir / "fork-scope.json").write_text(
                json.dumps({"active_fork": "sales", "last_update": "2026-04-18T10:00:00"}),
                encoding="utf-8",
            )
            (config_dir / "authority-matrix.json").write_text(
                json.dumps({"forks": {"sales": {"directory": "sales/"}, "support": {"directory": "support/"}}}),
                encoding="utf-8",
            )
            payload = {"tool_name": "Write", "tool_input": {"file_path": "/workspace/support/runbook.md"}}
            result = _run_hook("os-acl-enforcer.py", payload, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("cross-fork", data["reason"].lower())

    def test_credential_scope_guard_blocks_cross_fork_vault_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            state_dir = Path(tmp) / "tag-runtime" / "state"
            config_dir = Path(tmp) / "tag-runtime" / "config"
            state_dir.mkdir(parents=True)
            config_dir.mkdir(parents=True)
            (state_dir / "fork-scope.json").write_text(
                json.dumps({"active_fork": "sales"}),
                encoding="utf-8",
            )
            (config_dir / "authority-matrix.json").write_text(
                json.dumps(
                    {
                        "credential_scopes": {
                            "stripe": {"forks": ["sales"]},
                            "zendesk": {"forks": ["support"]},
                            "openai": {"forks": ["shared"]},
                        }
                    }
                ),
                encoding="utf-8",
            )
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 tag/tools/vault.py --key zendesk_api_key"},
            }
            result = _run_hook("credential-scope-guard.py", payload, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("support", data["reason"].lower())

    def test_fork_scope_guard_warns_on_second_fork_touch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            payload1 = {"tool_name": "Write", "tool_input": {"file_path": "/workspace/sales/app.py"}}
            payload2 = {"tool_name": "Edit", "tool_input": {"file_path": "/workspace/support/faq.md"}}

            first = _run_hook("fork-scope-guard.py", payload1, env=env)
            second = _run_hook("fork-scope-guard.py", payload2, env=env)
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertEqual(json.loads(first.stdout), {})
            data = json.loads(second.stdout)
            self.assertIn("message", data)
            self.assertIn("multiple forks", data["message"].lower())

    def test_webfetch_exfil_guard_blocks_known_capture_service(self) -> None:
        result = _run_hook(
            "webfetch-exfil-guard.py",
            {"tool_name": "WebFetch", "tool_input": {"url": "https://webhook.site/abc123"}},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["decision"], "block")
        self.assertIn("data-capture", data["reason"].lower())


if __name__ == "__main__":
    unittest.main()
