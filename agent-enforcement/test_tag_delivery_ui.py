from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class TagDeliveryUiTests(unittest.TestCase):
    def test_ui_shell_contains_runtime_choice_and_governance_copy(self) -> None:
        html = (ROOT / "tag" / "delivery" / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertIn("TaG-managed", html)
        self.assertIn("Self-managed local", html)
        self.assertIn("Self-managed cloud", html)
        self.assertIn("Governed mode required", html)


if __name__ == "__main__":
    unittest.main()
