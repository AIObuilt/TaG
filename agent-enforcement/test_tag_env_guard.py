import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "tag" / "hooks" / "env-guard.py"


class TagEnvGuardTests(unittest.TestCase):
    def test_env_guard_blocks_broad_git_add(self) -> None:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git add ."},
        })
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["decision"], "block")
        self.assertIn("explicit file paths", data["reason"])

    def test_env_guard_allows_explicit_safe_path(self) -> None:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git add tag/hooks/env-guard.py"},
        })
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
