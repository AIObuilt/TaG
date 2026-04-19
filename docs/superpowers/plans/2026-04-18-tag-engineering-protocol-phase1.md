# TaG Engineering Protocol Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TaG open-core engineering protocol: evidence-backed verification, repo hygiene checks, browser QA/security protocol gates, and model-agnostic verification playbooks.

**Architecture:** Extend the current TaG hook and policy surface with a small verification subsystem. The verification subsystem owns structured local evidence records, default coding-protocol policy, baseline Playwright templates, and model-agnostic playbooks. Hooks remain protocol guards: they inspect policy and evidence, then allow, hold, or block completion/release behavior without tightly coupling to a specific agent runtime.

**Tech Stack:** Python 3, JSON, unittest, existing TaG hook runtime, static markdown playbooks, git

---

### Task 1: Create Verification Workspace and Evidence Model

**Files:**
- Modify: `tag_config.py`
- Create: `tag/verification/__init__.py`
- Create: `tag/verification/evidence.py`
- Test: `agent-enforcement/test_tag_verification_evidence.py`

- [ ] **Step 1: Write the failing evidence-model test**

```python
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.evidence import EvidenceRecord, append_evidence_record, load_evidence_records


class TagVerificationEvidenceTests(unittest.TestCase):
    def test_append_and_load_evidence_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_file = Path(tmp) / "verification-evidence.jsonl"
            record = EvidenceRecord(
                evidence_id="ev-1",
                kind="code",
                tool="python3",
                target="python3 -m unittest",
                status="pass",
                summary="core suite passed",
                artifacts=["agent-enforcement/test_tag_policy_model.py"],
            )
            append_evidence_record(evidence_file, record)
            records = load_evidence_records(evidence_file)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["evidence_id"], "ev-1")
            self.assertEqual(records[0]["kind"], "code")
            self.assertEqual(records[0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_verification_evidence.py`
Expected: FAIL because `tag.verification.evidence` does not exist

- [ ] **Step 3: Add the minimal verification workspace and evidence helpers**

```python
# tag_config.py
VERIFICATION_EVIDENCE_FILE = CONTEXT_DIR / "verification-evidence.jsonl"
VERIFICATION_STATUS_FILE = CONTEXT_DIR / "verification-status.json"
```

```python
# tag/verification/__init__.py
from __future__ import annotations
```

```python
# tag/verification/evidence.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class EvidenceRecord:
    evidence_id: str
    kind: str
    tool: str
    target: str
    status: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp or datetime.now(timezone.utc).isoformat()
        return payload


def append_evidence_record(path: Path, record: EvidenceRecord) -> dict:
    payload = record.to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return payload


def load_evidence_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_verification_evidence.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag_config.py tag/verification/__init__.py tag/verification/evidence.py agent-enforcement/test_tag_verification_evidence.py
git -C /Users/jason/TaG commit -m "Add TaG verification evidence model"
```

### Task 2: Add Coding Protocol Policy Defaults and Loader

**Files:**
- Create: `tag/config/coding-protocol.json`
- Create: `tag/policy/coding_protocol.py`
- Test: `agent-enforcement/test_tag_coding_protocol.py`

- [ ] **Step 1: Write the failing coding-protocol policy test**

```python
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.policy.coding_protocol import load_coding_protocol


class TagCodingProtocolTests(unittest.TestCase):
    def test_default_protocol_requires_evidence_handles_for_completion(self) -> None:
        protocol = load_coding_protocol()
        self.assertTrue(protocol["verification"]["required_for_completion"])
        self.assertTrue(protocol["completion"]["require_evidence_handles"])
        self.assertTrue(protocol["browser_qa"]["required_for_ui_work"])
        self.assertTrue(protocol["browser_security"]["required_for_preview_or_deploy_work"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_coding_protocol.py`
Expected: FAIL because `tag.policy.coding_protocol` does not exist

- [ ] **Step 3: Add the default policy file and loader**

```json
{
  "verification": {
    "required_for_completion": true,
    "require_evidence": true
  },
  "repo_hygiene": {
    "require_clean_release_state": true,
    "require_verification_artifacts": true,
    "require_touched_file_coverage": false
  },
  "browser_qa": {
    "required_for_ui_work": true,
    "allow_skip_with_reason": true
  },
  "browser_security": {
    "required_for_preview_or_deploy_work": true,
    "allow_skip_with_reason": true
  },
  "completion": {
    "require_evidence_handles": true,
    "allow_skip_with_reason": true
  }
}
```

```python
# tag/policy/coding_protocol.py
from __future__ import annotations

import json
from pathlib import Path

from tag_config import CONFIG_DIR


CODING_PROTOCOL_FILE = CONFIG_DIR / "coding-protocol.json"


def load_coding_protocol(path: Path | None = None) -> dict:
    target = path or CODING_PROTOCOL_FILE
    return json.loads(target.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_coding_protocol.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag/config/coding-protocol.json tag/policy/coding_protocol.py agent-enforcement/test_tag_coding_protocol.py
git -C /Users/jason/TaG commit -m "Add TaG coding protocol policy defaults"
```

### Task 3: Add Verification Gate and Completion Claim Guard

**Files:**
- Create: `tag/hooks/verification-gate.py`
- Create: `tag/hooks/completion-claim-guard.py`
- Test: `agent-enforcement/test_tag_completion_protocol.py`

- [ ] **Step 1: Write the failing verification/completion tests**

```python
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tag" / "hooks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run_hook(name: str, payload: dict, env: dict | None = None) -> dict:
    result = subprocess.run(
        ["python3", str(HOOKS / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


class TagCompletionProtocolTests(unittest.TestCase):
    def test_verification_gate_holds_when_no_code_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "verification-gate.py",
                {"claim_type": "complete", "work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data["decision"], "hold")
            self.assertIn("verification", data["reason"])

    def test_completion_claim_guard_blocks_done_claim_without_evidence_handles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook(
                "completion-claim-guard.py",
                {"response": "Done. The issue is fixed.", "work_type": "code", "evidence_ids": []},
                env=env,
            )
            self.assertEqual(data["decision"], "block")
            self.assertIn("evidence", data["reason"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_completion_protocol.py`
Expected: FAIL because the new hooks do not exist

- [ ] **Step 3: Implement the verification gate and completion guard**

```python
# tag/hooks/verification-gate.py
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag_config import VERIFICATION_EVIDENCE_FILE


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        evidence = load_evidence_records(VERIFICATION_EVIDENCE_FILE)
        evidence_ids = set(payload.get("evidence_ids", []))
        if protocol["verification"]["required_for_completion"] and not evidence_ids:
            print(json.dumps({"decision": "hold", "reason": "verification-evidence-required"}))
            return 0
        known = {row["evidence_id"] for row in evidence}
        missing = sorted(evidence_ids - known)
        if missing:
            print(json.dumps({"decision": "hold", "reason": f"verification-evidence-missing:{','.join(missing)}"}))
            return 0
        print(json.dumps({}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# tag/hooks/completion-claim-guard.py
#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol


CLAIM_PATTERN = re.compile(r"\b(done|complete|completed|fixed|shipped|ready)\b", re.IGNORECASE)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        response = str(payload.get("response", ""))
        evidence_ids = payload.get("evidence_ids", [])
        protocol = load_coding_protocol()
        if CLAIM_PATTERN.search(response) and protocol["completion"]["require_evidence_handles"] and not evidence_ids:
            print(json.dumps({"decision": "block", "reason": "completion-claim-missing-evidence-handles"}))
            return 0
        print(json.dumps({}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_completion_protocol.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag/hooks/verification-gate.py tag/hooks/completion-claim-guard.py agent-enforcement/test_tag_completion_protocol.py
git -C /Users/jason/TaG commit -m "Add TaG verification and completion protocol guards"
```

### Task 4: Add Repo Hygiene Gate

**Files:**
- Create: `tag/hooks/repo-hygiene-gate.py`
- Test: `agent-enforcement/test_tag_repo_hygiene_gate.py`

- [ ] **Step 1: Write the failing repo-hygiene gate test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_repo_hygiene_gate.py`
Expected: FAIL because `repo-hygiene-gate.py` does not exist

- [ ] **Step 3: Implement the repo hygiene gate**

```python
# tag/hooks/repo-hygiene-gate.py
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag_config import CONTEXT_DIR


REPO_HYGIENE_FILE = CONTEXT_DIR / "repo-hygiene.json"


def load_repo_hygiene() -> dict:
    if not REPO_HYGIENE_FILE.exists():
        return {"clean": True, "verification_artifacts_present": True}
    try:
        return json.loads(REPO_HYGIENE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"clean": True, "verification_artifacts_present": True}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        claim_type = payload.get("claim_type", "")
        protocol = load_coding_protocol()
        state = load_repo_hygiene()
        if claim_type in {"release", "complete"} and protocol["repo_hygiene"]["require_clean_release_state"] and not state.get("clean", True):
            print(json.dumps({"decision": "hold", "reason": "dirty-repo-state"}))
            return 0
        if protocol["repo_hygiene"]["require_verification_artifacts"] and not state.get("verification_artifacts_present", True):
            print(json.dumps({"decision": "hold", "reason": "verification-artifacts-missing"}))
            return 0
        print(json.dumps({}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_repo_hygiene_gate.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag/hooks/repo-hygiene-gate.py agent-enforcement/test_tag_repo_hygiene_gate.py
git -C /Users/jason/TaG commit -m "Add TaG repo hygiene gate"
```

### Task 5: Add Baseline Playwright Templates and Model-Agnostic Playbooks

**Files:**
- Create: `tag/verification/playwright_templates.py`
- Create: `tag/verification/playbooks/engineering.md`
- Create: `tag/verification/playbooks/playwright_qa.md`
- Create: `tag/verification/playbooks/playwright_security.md`
- Test: `agent-enforcement/test_tag_playwright_templates.py`

- [ ] **Step 1: Write the failing Playwright-template test**

```python
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.playwright_templates import build_qa_template, build_security_template


class TagPlaywrightTemplateTests(unittest.TestCase):
    def test_templates_include_expected_browser_checks(self) -> None:
        qa = build_qa_template("https://example.test")
        security = build_security_template("https://example.test")
        self.assertIn("page.goto", qa)
        self.assertIn("expect(page)", qa)
        self.assertIn("response", security)
        self.assertIn("strict-transport-security", security.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_playwright_templates.py`
Expected: FAIL because `tag.verification.playwright_templates` does not exist

- [ ] **Step 3: Add baseline templates and model-agnostic playbooks**

```python
# tag/verification/playwright_templates.py
from __future__ import annotations


def build_qa_template(base_url: str) -> str:
    return f'''import {{ test, expect }} from "@playwright/test";

test("baseline qa", async ({{ page }}) => {{
  await page.goto("{base_url}");
  await expect(page).toHaveURL(/.*/);
  await expect(page.locator("body")).toBeVisible();
}});
'''


def build_security_template(base_url: str) -> str:
    return f'''import {{ test, expect }} from "@playwright/test";

test("baseline security", async ({{ page }}) => {{
  const response = await page.goto("{base_url}");
  const headers = response ? response.headers() : {{}};
  expect(headers["strict-transport-security"] || "").not.toBe("");
  await expect(page.locator("text=Exception")).toHaveCount(0);
}});
'''
```

```markdown
# tag/verification/playbooks/engineering.md
# Engineering Verification Playbook

1. Run code-level verification.
2. Record evidence ids, status, and artifacts.
3. Do not claim completion without evidence handles.
```

```markdown
# tag/verification/playbooks/playwright_qa.md
# Playwright QA Playbook

1. Run the baseline QA template against the target surface.
2. Confirm the page loads and the critical UI shell is visible.
3. Record pass/fail/skip evidence.
```

```markdown
# tag/verification/playbooks/playwright_security.md
# Playwright Security Playbook

1. Run the baseline security template against the target surface.
2. Record obvious runtime exposure, mixed-content, or header failures.
3. Record what was checked and what was not.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_playwright_templates.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag/verification/playwright_templates.py tag/verification/playbooks agent-enforcement/test_tag_playwright_templates.py
git -C /Users/jason/TaG commit -m "Add TaG Playwright templates and verification playbooks"
```

### Task 6: Add Playwright QA and Security Gates

**Files:**
- Create: `tag/hooks/playwright-qa-gate.py`
- Create: `tag/hooks/playwright-security-gate.py`
- Test: `agent-enforcement/test_tag_browser_protocol_gates.py`

- [ ] **Step 1: Write the failing browser-gate test**

```python
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tag" / "hooks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.evidence import EvidenceRecord, append_evidence_record


def _run_hook(name: str, payload: dict, env: dict) -> dict:
    result = subprocess.run(
        ["python3", str(HOOKS / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout or "{}")


class TagBrowserProtocolGateTests(unittest.TestCase):
    def test_qa_gate_holds_ui_work_without_qa_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            data = _run_hook("playwright-qa-gate.py", {"work_type": "ui", "evidence_ids": []}, env)
            self.assertEqual(data["decision"], "hold")
            self.assertIn("qa", data["reason"])

    def test_security_gate_allows_preview_work_when_security_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TAG_HOME": tmp}
            evidence_file = Path(tmp) / "tag-runtime" / "context" / "verification-evidence.jsonl"
            append_evidence_record(
                evidence_file,
                EvidenceRecord(
                    evidence_id="ev-sec-1",
                    kind="security",
                    tool="playwright",
                    target="https://preview.example.test",
                    status="pass",
                    summary="baseline browser security passed",
                    artifacts=[],
                ),
            )
            data = _run_hook(
                "playwright-security-gate.py",
                {"work_type": "preview", "evidence_ids": ["ev-sec-1"]},
                env,
            )
            self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_browser_protocol_gates.py`
Expected: FAIL because the Playwright protocol hooks do not exist

- [ ] **Step 3: Implement the Playwright QA and security gates**

```python
# tag/hooks/playwright-qa-gate.py
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag_config import VERIFICATION_EVIDENCE_FILE


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if payload.get("work_type") != "ui" or not protocol["browser_qa"]["required_for_ui_work"]:
            print(json.dumps({}))
            return 0
        evidence = {row["evidence_id"]: row for row in load_evidence_records(VERIFICATION_EVIDENCE_FILE)}
        for evidence_id in payload.get("evidence_ids", []):
            row = evidence.get(evidence_id)
            if row and row.get("kind") == "qa" and row.get("status") == "pass":
                print(json.dumps({}))
                return 0
        print(json.dumps({"decision": "hold", "reason": "browser-qa-evidence-required"}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# tag/hooks/playwright-security-gate.py
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import _tag_bootstrap  # noqa: F401
from tag.policy.coding_protocol import load_coding_protocol
from tag.verification.evidence import load_evidence_records
from tag_config import VERIFICATION_EVIDENCE_FILE


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        protocol = load_coding_protocol()
        if payload.get("work_type") not in {"preview", "deploy"} or not protocol["browser_security"]["required_for_preview_or_deploy_work"]:
            print(json.dumps({}))
            return 0
        evidence = {row["evidence_id"]: row for row in load_evidence_records(VERIFICATION_EVIDENCE_FILE)}
        for evidence_id in payload.get("evidence_ids", []):
            row = evidence.get(evidence_id)
            if row and row.get("kind") == "security" and row.get("status") == "pass":
                print(json.dumps({}))
                return 0
        print(json.dumps({"decision": "hold", "reason": "browser-security-evidence-required"}))
        return 0
    except Exception:
        print(json.dumps({}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 /Users/jason/TaG/agent-enforcement/test_tag_browser_protocol_gates.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/jason/TaG add tag/hooks/playwright-qa-gate.py tag/hooks/playwright-security-gate.py agent-enforcement/test_tag_browser_protocol_gates.py
git -C /Users/jason/TaG commit -m "Add TaG browser QA and security protocol gates"
```

### Task 7: Verify End-to-End Protocol Behavior and Document It

**Files:**
- Modify: `README.md`
- Test: `agent-enforcement/test_tag_verification_evidence.py`
- Test: `agent-enforcement/test_tag_coding_protocol.py`
- Test: `agent-enforcement/test_tag_completion_protocol.py`
- Test: `agent-enforcement/test_tag_repo_hygiene_gate.py`
- Test: `agent-enforcement/test_tag_playwright_templates.py`
- Test: `agent-enforcement/test_tag_browser_protocol_gates.py`

- [ ] **Step 1: Add a short README section for engineering protocol**

```markdown
## Engineering Protocol

TaG open core includes universal engineering governance primitives:
- evidence-backed verification before completion
- repo hygiene checks for release/finalization
- browser QA protocol for UI-facing work
- browser security protocol for preview and deploy surfaces
- model-agnostic verification playbooks and Playwright starter templates
```

- [ ] **Step 2: Run the focused engineering-protocol suite**

Run:
```bash
python3 /Users/jason/TaG/agent-enforcement/test_tag_verification_evidence.py
python3 /Users/jason/TaG/agent-enforcement/test_tag_coding_protocol.py
python3 /Users/jason/TaG/agent-enforcement/test_tag_completion_protocol.py
python3 /Users/jason/TaG/agent-enforcement/test_tag_repo_hygiene_gate.py
python3 /Users/jason/TaG/agent-enforcement/test_tag_playwright_templates.py
python3 /Users/jason/TaG/agent-enforcement/test_tag_browser_protocol_gates.py
```
Expected: PASS for all six test files

- [ ] **Step 3: Run syntax verification across the new surfaces**

Run:
```bash
python3 -m py_compile \
  /Users/jason/TaG/tag/verification/evidence.py \
  /Users/jason/TaG/tag/verification/playwright_templates.py \
  /Users/jason/TaG/tag/policy/coding_protocol.py \
  /Users/jason/TaG/tag/hooks/verification-gate.py \
  /Users/jason/TaG/tag/hooks/completion-claim-guard.py \
  /Users/jason/TaG/tag/hooks/repo-hygiene-gate.py \
  /Users/jason/TaG/tag/hooks/playwright-qa-gate.py \
  /Users/jason/TaG/tag/hooks/playwright-security-gate.py
```
Expected: no output

- [ ] **Step 4: Commit**

```bash
git -C /Users/jason/TaG add README.md
git -C /Users/jason/TaG commit -m "Document TaG engineering protocol open core"
```
