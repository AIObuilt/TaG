import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TagCompactionRecoveryTests(unittest.TestCase):
    def test_compaction_recovery_saves_and_injects_recovery_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            context = Path(tmp) / "tag-runtime" / "context"
            context.mkdir(parents=True)
            (context / "heartbeat.json").write_text(
                json.dumps({
                    "call_count": 7,
                    "files_changed": ["tag/hooks/crash-checkpoint.py"],
                    "files_read": ["tag_config.py"],
                    "agents_launched": [],
                    "commands_run": ["python3 test_tag_crash_checkpoint.py"],
                    "session_start": "2026-04-17T00:00:00",
                }),
                encoding="utf-8",
            )
            (context / "session-checkpoint.md").write_text(
                "# TaG Session Checkpoint\n\nCurrent task: extract compaction recovery\n",
                encoding="utf-8",
            )

            precompact = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "compaction-recovery.py")],
                input=json.dumps({"summary": "compact now", "messages_count": 50}),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(precompact.returncode, 0, msg=precompact.stderr)

            recover = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "compaction-recovery.py")],
                input=json.dumps({"prompt": "continue"}),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(recover.returncode, 0, msg=recover.stderr)

            payload = json.loads(recover.stdout)
            message = payload["message"]
            self.assertIn("CONTEXT RECOVERY", message)
            self.assertIn("extract compaction recovery", message)
            self.assertIn("crash-checkpoint.py", message)


if __name__ == "__main__":
    unittest.main()
