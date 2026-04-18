import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "tag" / "hooks" / "spending-guard.py"


class TagSpendingGuardTests(unittest.TestCase):
    def test_spending_guard_blocks_payment_endpoint(self) -> None:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "curl https://api.stripe.com/v1/payment_intents"},
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
        self.assertIn("SPENDING BLOCKED", data["reason"])

    def test_spending_guard_allows_non_spending_command(self) -> None:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "pytest -q"},
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
