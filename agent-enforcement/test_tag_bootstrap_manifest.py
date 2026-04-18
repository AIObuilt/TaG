import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.bootstrap.manifest import build_bootstrap_manifest


class TagBootstrapManifestTests(unittest.TestCase):
    def test_manifest_is_machine_scoped(self) -> None:
        manifest = build_bootstrap_manifest(
            bootstrap_token="tok-1",
            enrollment_id="enr-1",
            machine_label="jason-mac",
            hosted_base_url="https://tag.example.com",
        )
        self.assertEqual(manifest["enrollment_id"], "enr-1")
        self.assertEqual(manifest["machine_label"], "jason-mac")
        self.assertTrue(manifest["bootstrap_url"].startswith("https://tag.example.com"))


if __name__ == "__main__":
    unittest.main()
