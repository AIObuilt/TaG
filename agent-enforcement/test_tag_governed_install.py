import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.governed_install import can_complete_setup


class TagGovernedInstallTests(unittest.TestCase):
    def test_setup_cannot_complete_without_governed_mode(self) -> None:
        self.assertFalse(can_complete_setup({"governed": False}))

    def test_setup_can_complete_with_governed_mode(self) -> None:
        self.assertTrue(can_complete_setup({"governed": True}))


if __name__ == "__main__":
    unittest.main()
