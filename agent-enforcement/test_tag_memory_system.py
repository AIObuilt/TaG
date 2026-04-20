from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.memory.provider import MemorySystem, resolve_memory


class MemorySystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_resolve_memory(self) -> None:
        ms = resolve_memory()
        self.assertIsInstance(ms, MemorySystem)

    def test_memory_system_status(self) -> None:
        ms = resolve_memory()
        status = ms.status()
        self.assertIsInstance(status, dict)
        self.assertIn("heartbeat", status)
        self.assertIn("engram", status)
        self.assertIn("hindsight", status)

    def test_memory_system_layers(self) -> None:
        ms = resolve_memory()
        self.assertIsNotNone(ms.heartbeat)
        self.assertIsNotNone(ms.engram)
        self.assertIsNotNone(ms.hindsight)
        # verify layers are functional
        count = ms.engram.count()
        self.assertIsInstance(count, int)
        hindsight_count = ms.hindsight.count()
        self.assertIsInstance(hindsight_count, int)
        alive = ms.heartbeat.is_alive()
        self.assertIsInstance(alive, bool)


if __name__ == "__main__":
    unittest.main()
