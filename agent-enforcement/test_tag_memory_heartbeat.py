from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.memory.heartbeat import Heartbeat


class HeartbeatTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.hb_path = self.tmp / "heartbeat.json"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_pulse_creates_file(self) -> None:
        hb = Heartbeat(self.hb_path)
        hb.pulse(
            call_count=1,
            files_changed=["a.py"],
            files_read=["b.py"],
            agents=["agent1"],
            commands=["ls"],
            session_id="sess-001",
        )
        self.assertTrue(self.hb_path.exists())
        state = hb.read()
        self.assertIn("session_id", state)
        self.assertEqual(state["session_id"], "sess-001")
        self.assertIn("call_count", state)
        self.assertIn("last_pulse", state)

    def test_read_empty(self) -> None:
        hb = Heartbeat(self.hb_path)
        state = hb.read()
        self.assertIsInstance(state, dict)

    def test_is_alive_recent(self) -> None:
        hb = Heartbeat(self.hb_path)
        hb.pulse(
            call_count=1,
            files_changed=[],
            files_read=[],
            agents=[],
            commands=[],
            session_id="sess-002",
        )
        self.assertTrue(hb.is_alive(max_age_seconds=300))

    def test_is_alive_stale(self) -> None:
        hb = Heartbeat(self.hb_path)
        hb.pulse(
            call_count=1,
            files_changed=[],
            files_read=[],
            agents=[],
            commands=[],
            session_id="sess-003",
        )
        # max_age of 0 seconds means any pulse is stale
        self.assertFalse(hb.is_alive(max_age_seconds=0))

    def test_end_session(self) -> None:
        hb = Heartbeat(self.hb_path)
        hb.pulse(
            call_count=1,
            files_changed=[],
            files_read=[],
            agents=[],
            commands=[],
            session_id="sess-004",
        )
        hb.end_session()
        state = hb.read()
        self.assertTrue(state.get("cleanly_ended"))

    def test_pulse_accumulates(self) -> None:
        hb = Heartbeat(self.hb_path)
        hb.pulse(
            call_count=1,
            files_changed=["a.py"],
            files_read=[],
            agents=[],
            commands=[],
            session_id="sess-005",
        )
        hb.pulse(
            call_count=2,
            files_changed=["b.py"],
            files_read=[],
            agents=[],
            commands=[],
            session_id="sess-005",
        )
        state = hb.read()
        files_changed = state.get("files_changed", [])
        self.assertIn("a.py", files_changed)
        self.assertIn("b.py", files_changed)


if __name__ == "__main__":
    unittest.main()
