import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tag" / "tools" / "hook_installer.py"


class TagHookInstallerTests(unittest.TestCase):
    def test_tag_hook_installer_emits_manifest_for_tag_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            manifest = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["product"], "TaG")
            self.assertIn("hooks", manifest)
            hook_names = {entry["name"] for entry in manifest["hooks"]}
            self.assertIn("build-gate", hook_names)
            self.assertIn("qa-gate", hook_names)
            for entry in manifest["hooks"]:
                self.assertTrue(entry["path"].startswith("tag/hooks/"))


if __name__ == "__main__":
    unittest.main()
