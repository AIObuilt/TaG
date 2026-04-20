from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class TagDeliveryUiTests(unittest.TestCase):
    def test_ui_shell_contains_runtime_choice_and_governance_copy(self) -> None:
        html = (ROOT / "tag" / "delivery" / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Trust and Governance", html)
        self.assertIn("TaG Dashboard", html)
        self.assertIn("governance-panel", html)
        self.assertIn("Governed Mode", html)
        self.assertIn("memory-panel", html)
        self.assertIn("decisions-panel", html)
        self.assertIn("hooks-panel", html)


if __name__ == "__main__":
    unittest.main()
