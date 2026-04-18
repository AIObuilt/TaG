import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.setup_state import load_setup_state, save_setup_state


class TagSetupStateTests(unittest.TestCase):
    def test_setup_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "setup-state.json"
            save_setup_state(path, {"mode": "managed", "governed": False})
            loaded = load_setup_state(path)
            self.assertEqual(loaded["mode"], "managed")
            self.assertFalse(loaded["governed"])


if __name__ == "__main__":
    unittest.main()
