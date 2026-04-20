from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.memory.hindsight import Hindsight


class HindsightTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.hs_path = self.tmp / "hindsight.jsonl"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_save_and_recall(self) -> None:
        hs = Hindsight(self.hs_path)
        hs.save(
            "deployment failed due to missing env var",
            source="codex",
            tags=["deploy", "env"],
            metadata={"severity": "high"},
        )
        results = hs.recall("deployment env var")
        self.assertTrue(len(results) >= 1)
        self.assertIn("deployment failed due to missing env var", results[0]["content"])

    def test_recall_filter_by_source(self) -> None:
        hs = Hindsight(self.hs_path)
        hs.save("codex made a mistake", source="codex", tags=[], metadata={})
        hs.save("voice made a mistake", source="voice", tags=[], metadata={})
        results = hs.recall("mistake", source="codex")
        self.assertTrue(all(r["source"] == "codex" for r in results))
        self.assertEqual(len(results), 1)

    def test_recent(self) -> None:
        hs = Hindsight(self.hs_path)
        hs.save("first event", source="codex", tags=[], metadata={})
        hs.save("second event", source="codex", tags=[], metadata={})
        hs.save("third event", source="codex", tags=[], metadata={})
        entries = hs.recent(limit=10)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["content"], "third event")

    def test_recent_filter_source(self) -> None:
        hs = Hindsight(self.hs_path)
        hs.save("from codex", source="codex", tags=[], metadata={})
        hs.save("from voice", source="voice", tags=[], metadata={})
        hs.save("from codex again", source="codex", tags=[], metadata={})
        entries = hs.recent(limit=10, source="codex")
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e["source"] == "codex" for e in entries))

    def test_stats(self) -> None:
        hs = Hindsight(self.hs_path)
        hs.save("entry A", source="codex", tags=["x"], metadata={})
        hs.save("entry B", source="voice", tags=["y"], metadata={})
        hs.save("entry C", source="codex", tags=["x", "z"], metadata={})
        stats = hs.stats()
        self.assertIn("total", stats)
        self.assertIn("sources", stats)
        self.assertIn("tags", stats)
        self.assertEqual(stats["total"], 3)
        self.assertIn("codex", stats["sources"])
        self.assertEqual(stats["sources"]["codex"], 2)
        self.assertEqual(stats["sources"]["voice"], 1)

    def test_empty_state(self) -> None:
        hs = Hindsight(self.hs_path)
        self.assertEqual(hs.count(), 0)
        self.assertEqual(hs.recent(limit=10), [])
        self.assertEqual(hs.recall("anything"), [])
        stats = hs.stats()
        self.assertEqual(stats["total"], 0)

    def test_count(self) -> None:
        hs = Hindsight(self.hs_path)
        self.assertEqual(hs.count(), 0)
        hs.save("one", source="codex", tags=[], metadata={})
        hs.save("two", source="codex", tags=[], metadata={})
        self.assertEqual(hs.count(), 2)
        stats = hs.stats()
        self.assertEqual(stats["total"], hs.count())


if __name__ == "__main__":
    unittest.main()
