from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tag_config


class TagSharedBrainSchemaTests(unittest.TestCase):
    def test_tag_shared_brain_templates_exist_and_are_product_safe(self) -> None:
        shared_brain_dir = tag_config.TAG_HOME / "tag" / "shared_brain"
        agent_path = shared_brain_dir / "AGENT.md"
        gotchas_path = shared_brain_dir / "gotchas.md"
        continue_path = shared_brain_dir / "CONTINUE.template.md"

        self.assertTrue(agent_path.exists())
        self.assertTrue(gotchas_path.exists())
        self.assertTrue(continue_path.exists())

        agent_text = agent_path.read_text(encoding="utf-8")
        gotchas_text = gotchas_path.read_text(encoding="utf-8")
        continue_text = continue_path.read_text(encoding="utf-8")

        self.assertIn("TaG", agent_text)
        self.assertIn("customer-installed", agent_text)
        self.assertNotIn("Jason McCall", agent_text)
        self.assertNotIn("Vance", agent_text)

        self.assertIn("Operational Gotchas", gotchas_text)
        self.assertIn("product-specific", gotchas_text)
        self.assertNotIn("Holly", gotchas_text)
        self.assertNotIn("finditsales.com", gotchas_text)

        self.assertIn("Session Continuation", continue_text)
        self.assertIn("Pending Actions", continue_text)
        self.assertIn("{{SESSION_ID}}", continue_text)


if __name__ == "__main__":
    unittest.main()
