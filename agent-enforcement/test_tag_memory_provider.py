import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TagMemoryProviderTests(unittest.TestCase):
    def test_file_memory_provider_persists_session_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**os.environ, "TAG_HOME": tmpdir}
            script = (
                "from tag.memory.provider import resolve_provider; "
                "provider = resolve_provider(); "
                "provider.append_session_summary({'title': 'Session end', 'summary': 'worked on governance'}); "
                "print(provider.storage_path)"
            )
            result = subprocess.run(
                ["python3", "-c", script],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(ROOT),
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            storage_path = Path(result.stdout.strip())
            payload = json.loads(storage_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["entries"]), 1)
            self.assertEqual(payload["entries"][0]["title"], "Session end")

    def test_memory_autosave_writes_nontrivial_session_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**os.environ, "TAG_HOME": tmpdir}
            context = Path(tmpdir) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            heartbeat_file = context / "heartbeat.json"
            heartbeat_file.write_text(
                json.dumps(
                    {
                        "call_count": 6,
                        "session_start": "2026-04-18T12:00:00",
                        "files_changed": ["tag/hooks/delegate-enforcer.py"],
                        "files_read": ["tag/policy/policy.py"],
                        "agents_launched": [{"desc": "policy worker"}],
                        "commands_run": ["python3 test_tag_policy_model.py"],
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "memory-autosave.py")],
                input=json.dumps({"event": "SessionEnd"}),
                capture_output=True,
                text=True,
                env=env,
                cwd=str(ROOT),
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(json.loads(result.stdout), {})

            session_memory = json.loads((context / "session-memory.json").read_text(encoding="utf-8"))
            self.assertEqual(len(session_memory["entries"]), 1)
            self.assertIn("Session end", session_memory["entries"][0]["title"])

            heartbeat = json.loads(heartbeat_file.read_text(encoding="utf-8"))
            self.assertTrue(heartbeat["cleanly_ended"])


if __name__ == "__main__":
    unittest.main()
