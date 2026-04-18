from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TagDeliveryPathTests(unittest.TestCase):
    def test_delivery_packages_exist(self) -> None:
        self.assertTrue((ROOT / "tag" / "delivery").exists())
        self.assertTrue((ROOT / "tag" / "delivery" / "bootstrap").exists())
        self.assertTrue((ROOT / "tag" / "delivery" / "hosted").exists())
        self.assertTrue((ROOT / "tag" / "delivery" / "local").exists())

    def test_bootstrap_launcher_imports(self) -> None:
        from tag.delivery.bootstrap.launcher import bootstrap_entrypoint

        self.assertEqual(bootstrap_entrypoint(), "tag-delivery-bootstrap")


if __name__ == "__main__":
    unittest.main()
