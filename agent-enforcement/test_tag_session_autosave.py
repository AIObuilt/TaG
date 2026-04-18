import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TagSessionAutosaveTests(unittest.TestCase):
    def test_session_autosave_writes_product_neutral_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "tag-runtime" / "context"
            runtime.mkdir(parents=True)
            heartbeat = runtime / "heartbeat.json"
            heartbeat.write_text(json.dumps({
                "call_count": 6,
                "session_start": "2026-04-17T00:00:00",
                "files_changed": ["tag/hooks/skill-autoload.py"],
                "files_read": ["tag_config.py"],
                "commands_run": ["python3 test_tag_skill_autoload.py"],
                "agents_launched": [],
            }), encoding="utf-8")

            output = Path(tmp) / "tag-runtime" / "context" / "session-memory.json"

            import os
            import subprocess

            result = subprocess.run(
                ["python3", str(ROOT / "tag" / "hooks" / "session-autosave.py")],
                env={**os.environ, "TAG_HOME": tmp},
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["product"], "TaG")
            self.assertEqual(payload["call_count"], 6)


if __name__ == "__main__":
    unittest.main()
