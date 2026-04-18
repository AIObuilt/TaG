import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tag" / "tools" / "mcp_loader.py"


class TagMcpLoaderTests(unittest.TestCase):
    def test_tag_mcp_loader_adds_server_to_product_safe_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            config_path.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "add",
                    "sequential-thinking",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertIn("sequential-thinking", updated["mcpServers"])
            self.assertIn("Added 1 server", result.stdout)

    def test_tag_mcp_loader_lists_available_servers(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "available",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("sequential-thinking", result.stdout)
        self.assertIn("debugger", result.stdout)


if __name__ == "__main__":
    unittest.main()
