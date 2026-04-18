import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TagCrashCheckpointTests(unittest.TestCase):
    def test_crash_checkpoint_tracks_activity_and_writes_checkpoint_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            for _ in range(5):
                payload = json.dumps({
                    "tool_name": "Write",
                    "tool_input": {"file_path": "tag/hooks/skill-autoload.py"},
                })
                result = subprocess.run(
                    ["python3", str(ROOT / "tag" / "hooks" / "crash-checkpoint.py")],
                    input=payload,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)

            context = Path(tmp) / "tag-runtime" / "context"
            heartbeat = json.loads((context / "heartbeat.json").read_text(encoding="utf-8"))
            checkpoint = (context / "session-checkpoint.md").read_text(encoding="utf-8")

            self.assertEqual(heartbeat["call_count"], 5)
            self.assertIn("tag/hooks/skill-autoload.py", heartbeat["files_changed"])
            self.assertIn("# TaG Session Checkpoint", checkpoint)
            self.assertIn("Files Changed", checkpoint)


if __name__ == "__main__":
    unittest.main()
