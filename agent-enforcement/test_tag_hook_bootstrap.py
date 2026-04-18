import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TagHookBootstrapTests(unittest.TestCase):
    def test_tag_hook_bootstrap_allows_importing_tag_config(self) -> None:
        script = f"""
import sys
sys.path.insert(0, {str(ROOT / "tag" / "hooks")!r})
import _tag_bootstrap
import tag_config
print(tag_config.PRODUCT_NAME)
"""
        result = subprocess.run(
            ["/usr/bin/python3", "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "TaG")


if __name__ == "__main__":
    unittest.main()
