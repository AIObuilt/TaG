from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tag_config


class TagConfigTests(unittest.TestCase):
    def test_tag_config_exposes_product_neutral_paths(self) -> None:
        self.assertEqual(tag_config.PRODUCT_NAME, "TaG")
        self.assertEqual(tag_config.RUNTIME_DIR_NAME, "tag-runtime")
        self.assertEqual(tag_config.CONFIG_DIR_NAME, "config")
        self.assertEqual(tag_config.TAG_HOME, ROOT)
        self.assertEqual(tag_config.CONTEXT_DIR, tag_config.RUNTIME_DIR / "context")
        self.assertEqual(tag_config.BUILD_STATUS_FILE, tag_config.CONTEXT_DIR / "build-status.json")
        self.assertEqual(tag_config.SECURITY_VERDICT_FILE, tag_config.CONTEXT_DIR / "security-verdict.json")
        self.assertEqual(tag_config.DEPLOY_STATE_FILE, tag_config.CONTEXT_DIR / "deploy-state.json")
        self.assertEqual(tag_config.audit_log_path("env-guard"), tag_config.AUDIT_DIR / "env-guard.jsonl")


if __name__ == "__main__":
    unittest.main()
