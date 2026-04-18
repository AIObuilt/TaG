import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TagSkillAutoloadTests(unittest.TestCase):
    def test_tag_skill_autoload_injects_context_for_planning_prompt(self) -> None:
        payload = json.dumps({"prompt": "Please plan the first TaG feature"}).encode("utf-8")
        result = subprocess.run(
            ["python3", str(ROOT / "tag" / "hooks" / "skill-autoload.py")],
            input=payload,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr.decode("utf-8"))
        data = json.loads(result.stdout.decode("utf-8"))
        context = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("writing-plans", context)
        self.assertIn("TaG", context)


if __name__ == "__main__":
    unittest.main()
