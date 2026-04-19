import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tag" / "hooks"


def _run_hook(payload: dict, env: dict) -> dict:
    result = subprocess.run(
        ["python3", str(HOOKS / "repo-hygiene-gate.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


class TagRepoHygieneGateTests(unittest.TestCase):
    def test_blocks_release_claim_when_repo_marked_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            runtime = Path(tmp) / "tag-runtime" / "context"
            runtime.mkdir(parents=True)
            (runtime / "repo-hygiene.json").write_text(
                json.dumps({"clean": False, "verification_artifacts_present": True}),
                encoding="utf-8",
            )
            data = _run_hook({"claim_type": "release"}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("dirty", data["reason"])


if __name__ == "__main__":
    unittest.main()
