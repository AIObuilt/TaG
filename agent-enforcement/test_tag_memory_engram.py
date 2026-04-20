from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.memory.engram import Engram


class EngramTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.engram_path = self.tmp / "engram.jsonl"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_save_creates_entry(self) -> None:
        eg = Engram(self.engram_path)
        entry = eg.save(
            "always use absolute paths",
            tags=["paths", "convention"],
            source="user",
            entry_type="rule",
        )
        self.assertIn("content", entry)
        self.assertIn("tags", entry)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["content"], "always use absolute paths")
        self.assertEqual(entry["tags"], ["paths", "convention"])

    def test_recall_keyword_match(self) -> None:
        eg = Engram(self.engram_path)
        eg.save("use absolute paths", tags=["paths"], source="user", entry_type="rule")
        eg.save("avoid global variables", tags=["style"], source="user", entry_type="rule")
        results = eg.recall("absolute paths")
        self.assertTrue(len(results) >= 1)
        contents = [r["content"] for r in results]
        self.assertTrue(any("absolute" in c for c in contents))

    def test_recall_no_match(self) -> None:
        eg = Engram(self.engram_path)
        eg.save("use absolute paths", tags=["paths"], source="user", entry_type="rule")
        results = eg.recall("quantum entanglement")
        self.assertEqual(results, [])

    def test_recall_limit(self) -> None:
        eg = Engram(self.engram_path)
        for i in range(10):
            eg.save(f"rule number {i}", tags=["test"], source="auto", entry_type="rule")
        results = eg.recall("rule", limit=3)
        self.assertLessEqual(len(results), 3)

    def test_list_tags(self) -> None:
        eg = Engram(self.engram_path)
        eg.save("entry one", tags=["alpha", "beta"], source="user", entry_type="rule")
        eg.save("entry two", tags=["beta", "gamma"], source="user", entry_type="rule")
        tags = eg.list_tags()
        self.assertIn("alpha", tags)
        self.assertIn("beta", tags)
        self.assertIn("gamma", tags)
        # no duplicates
        self.assertEqual(len(tags), len(set(tags)))

    def test_count(self) -> None:
        eg = Engram(self.engram_path)
        self.assertEqual(eg.count(), 0)
        eg.save("first", tags=[], source="user", entry_type="rule")
        eg.save("second", tags=[], source="user", entry_type="rule")
        self.assertEqual(eg.count(), 2)

    def test_all_entries_newest_first(self) -> None:
        eg = Engram(self.engram_path)
        eg.save("oldest entry", tags=[], source="user", entry_type="rule")
        eg.save("middle entry", tags=[], source="user", entry_type="rule")
        eg.save("newest entry", tags=[], source="user", entry_type="rule")
        entries = eg.all_entries(limit=100)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["content"], "newest entry")
        self.assertEqual(entries[-1]["content"], "oldest entry")

    def test_recall_scores_by_relevance(self) -> None:
        eg = Engram(self.engram_path)
        eg.save("paths are important", tags=[], source="user", entry_type="rule")
        eg.save("use absolute paths always", tags=["paths"], source="user", entry_type="rule")
        eg.save("unrelated topic", tags=[], source="user", entry_type="rule")
        results = eg.recall("absolute paths")
        self.assertTrue(len(results) >= 1)
        # entry with both "absolute" and "paths" should appear before "unrelated topic"
        contents = [r["content"] for r in results]
        if "unrelated topic" in contents:
            unrelated_idx = contents.index("unrelated topic")
            absolute_idx = contents.index("use absolute paths always")
            self.assertLess(absolute_idx, unrelated_idx)


if __name__ == "__main__":
    unittest.main()
