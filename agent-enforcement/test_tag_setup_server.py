import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.setup_server import build_setup_snapshot


class TagSetupServerTests(unittest.TestCase):
    def test_setup_snapshot_includes_mode_runtime_and_governance_fields(self) -> None:
        snapshot = build_setup_snapshot({"mode": "managed", "runtime_path": "managed", "governed": False})
        self.assertEqual(snapshot["mode"], "managed")
        self.assertEqual(snapshot["runtime_path"], "managed")
        self.assertFalse(snapshot["governed"])


if __name__ == "__main__":
    unittest.main()
