import json
import unittest
from pathlib import Path


class TagForkSchemaTests(unittest.TestCase):
    def test_tag_fork_schema_and_template_exist(self) -> None:
        root = Path(__file__).resolve().parent.parent / "tag" / "forks"
        schema_path = root / "manifest.schema.json"
        template_path = root / "manifest.template.json"

        self.assertTrue(schema_path.exists())
        self.assertTrue(template_path.exists())

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        template = json.loads(template_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["title"], "TaG Fork Manifest")
        self.assertIn("properties", schema)
        self.assertIn("fork_id", schema["properties"])
        self.assertIn("runtime_scope", schema["properties"])
        self.assertIn("policy_scope", schema["properties"])
        self.assertIn("memory_scope", schema["properties"])

        self.assertEqual(template["version"], 1)
        self.assertIn("fork_id", template)
        self.assertIn("display_name", template)
        self.assertIn("runtime_scope", template)
        self.assertIn("policy_scope", template)
        self.assertIn("memory_scope", template)
        self.assertIn("allowed_runtimes", template)


if __name__ == "__main__":
    unittest.main()
