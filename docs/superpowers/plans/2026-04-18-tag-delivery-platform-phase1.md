# TaG Delivery Platform Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build phase 1 of the TaG delivery platform: hosted onboarding, machine-scoped bootstrap generation, local setup service, local GUI shell, runtime-path choice, and governed completion gating.

**Architecture:** Add a small hosted control plane and a local delivery layer without disturbing the existing TaG core. The hosted side owns account, billing gate, and enrollment token issuance. The local side owns bootstrap pairing, setup state, governed activation, and the GUI shell. The UI is a local web app served by the setup service and opened by the bootstrap.

**Tech Stack:** Python 3, JSON, local HTTP service, static HTML/CSS/JS for the first GUI shell, git

---

### Task 1: Create Delivery Workspace Skeleton

**Files:**
- Create: `tag/delivery/__init__.py`
- Create: `tag/delivery/bootstrap/__init__.py`
- Create: `tag/delivery/bootstrap/launcher.py`
- Create: `tag/delivery/hosted/__init__.py`
- Create: `tag/delivery/local/__init__.py`
- Create: `tag/delivery/ui/`
- Test: `agent-enforcement/test_tag_delivery_paths.py`

- [ ] **Step 1: Write the failing path-and-import test**

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_delivery_paths.py`
Expected: FAIL because `tag/delivery/...` does not exist yet

- [ ] **Step 3: Create the minimal delivery package skeleton**

```python
# tag/delivery/__init__.py
from __future__ import annotations
```

```python
# tag/delivery/bootstrap/__init__.py
from __future__ import annotations
```

```python
# tag/delivery/bootstrap/launcher.py
from __future__ import annotations


def bootstrap_entrypoint() -> str:
    return "tag-delivery-bootstrap"
```

```python
# tag/delivery/hosted/__init__.py
from __future__ import annotations
```

```python
# tag/delivery/local/__init__.py
from __future__ import annotations
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_delivery_paths.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_delivery_paths.py tag/delivery
git commit -m "Add TaG delivery package skeleton"
```

### Task 2: Hosted Enrollment and Billing Gate Model

**Files:**
- Create: `tag/delivery/hosted/models.py`
- Create: `tag/delivery/hosted/enrollment.py`
- Test: `agent-enforcement/test_tag_hosted_enrollment.py`

- [ ] **Step 1: Write the failing hosted-enrollment tests**

```python
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.hosted.enrollment import create_enrollment_session


class TagHostedEnrollmentTests(unittest.TestCase):
    def test_managed_requires_billing_before_bootstrap(self) -> None:
        with self.assertRaisesRegex(ValueError, "billing"):
            create_enrollment_session(
                account_id="acct-1",
                mode="managed",
                billing_active=False,
                machine_label="jason-mac",
            )

    def test_self_managed_allows_bootstrap_without_billing(self) -> None:
        session = create_enrollment_session(
            account_id="acct-1",
            mode="self-managed",
            billing_active=False,
            machine_label="jason-mac",
        )
        self.assertEqual(session["mode"], "self-managed")
        self.assertEqual(session["machine_label"], "jason-mac")
        self.assertIn("bootstrap_token", session)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_hosted_enrollment.py`
Expected: FAIL because hosted enrollment module does not exist

- [ ] **Step 3: Implement the minimal hosted enrollment model**

```python
# tag/delivery/hosted/models.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnrollmentSession:
    account_id: str
    mode: str
    machine_label: str
    bootstrap_token: str
```

```python
# tag/delivery/hosted/enrollment.py
from __future__ import annotations

import secrets


def create_enrollment_session(*, account_id: str, mode: str, billing_active: bool, machine_label: str) -> dict:
    if mode == "managed" and not billing_active:
        raise ValueError("billing required before managed bootstrap")
    return {
        "account_id": account_id,
        "mode": mode,
        "machine_label": machine_label,
        "bootstrap_token": secrets.token_urlsafe(24),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_hosted_enrollment.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_hosted_enrollment.py tag/delivery/hosted
git commit -m "Add TaG hosted enrollment and billing gate model"
```

### Task 3: Machine-Scoped Bootstrap Manifest

**Files:**
- Create: `tag/delivery/bootstrap/manifest.py`
- Test: `agent-enforcement/test_tag_bootstrap_manifest.py`

- [ ] **Step 1: Write the failing bootstrap-manifest tests**

```python
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.bootstrap.manifest import build_bootstrap_manifest


class TagBootstrapManifestTests(unittest.TestCase):
    def test_manifest_is_machine_scoped(self) -> None:
        manifest = build_bootstrap_manifest(
            bootstrap_token="tok-1",
            enrollment_id="enr-1",
            machine_label="jason-mac",
            hosted_base_url="https://tag.example.com",
        )
        self.assertEqual(manifest["enrollment_id"], "enr-1")
        self.assertEqual(manifest["machine_label"], "jason-mac")
        self.assertTrue(manifest["bootstrap_url"].startswith("https://tag.example.com"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_bootstrap_manifest.py`
Expected: FAIL because `build_bootstrap_manifest()` does not exist

- [ ] **Step 3: Implement the bootstrap manifest builder**

```python
# tag/delivery/bootstrap/manifest.py
from __future__ import annotations


def build_bootstrap_manifest(*, bootstrap_token: str, enrollment_id: str, machine_label: str, hosted_base_url: str) -> dict:
    return {
        "bootstrap_token": bootstrap_token,
        "enrollment_id": enrollment_id,
        "machine_label": machine_label,
        "bootstrap_url": f"{hosted_base_url.rstrip('/')}/bootstrap/{bootstrap_token}",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_bootstrap_manifest.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_bootstrap_manifest.py tag/delivery/bootstrap/manifest.py
git commit -m "Add TaG machine-scoped bootstrap manifest"
```

### Task 4: Local Setup State Model

**Files:**
- Create: `tag/delivery/local/setup_state.py`
- Test: `agent-enforcement/test_tag_setup_state.py`

- [ ] **Step 1: Write the failing setup-state tests**

```python
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.setup_state import load_setup_state, save_setup_state


class TagSetupStateTests(unittest.TestCase):
    def test_setup_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "setup-state.json"
            save_setup_state(path, {"mode": "managed", "governed": False})
            loaded = load_setup_state(path)
            self.assertEqual(loaded["mode"], "managed")
            self.assertFalse(loaded["governed"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_setup_state.py`
Expected: FAIL because setup-state module does not exist

- [ ] **Step 3: Implement setup-state persistence**

```python
# tag/delivery/local/setup_state.py
from __future__ import annotations

import json
from pathlib import Path


def load_setup_state(path: Path) -> dict:
    if not path.exists():
        return {"mode": None, "runtime_path": None, "governed": False}
    return json.loads(path.read_text(encoding="utf-8"))


def save_setup_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_setup_state.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_setup_state.py tag/delivery/local/setup_state.py
git commit -m "Add TaG local setup state model"
```

### Task 5: Governed Completion Gate

**Files:**
- Create: `tag/delivery/local/governed_install.py`
- Test: `agent-enforcement/test_tag_governed_install.py`

- [ ] **Step 1: Write the failing governed-install tests**

```python
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.governed_install import can_complete_setup


class TagGovernedInstallTests(unittest.TestCase):
    def test_setup_cannot_complete_without_governed_mode(self) -> None:
        self.assertFalse(can_complete_setup({"governed": False}))

    def test_setup_can_complete_with_governed_mode(self) -> None:
        self.assertTrue(can_complete_setup({"governed": True}))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_governed_install.py`
Expected: FAIL because `can_complete_setup()` does not exist

- [ ] **Step 3: Implement the governed completion gate**

```python
# tag/delivery/local/governed_install.py
from __future__ import annotations


def can_complete_setup(state: dict) -> bool:
    return bool(state.get("governed") is True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_governed_install.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_governed_install.py tag/delivery/local/governed_install.py
git commit -m "Add TaG governed completion gate"
```

### Task 6: Local GUI Shell Assets

**Files:**
- Create: `tag/delivery/ui/index.html`
- Create: `tag/delivery/ui/app.css`
- Create: `tag/delivery/ui/app.js`
- Test: `agent-enforcement/test_tag_delivery_ui.py`

- [ ] **Step 1: Write the failing UI-shell test**

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class TagDeliveryUiTests(unittest.TestCase):
    def test_ui_shell_contains_runtime_choice_and_governance_copy(self) -> None:
        html = (ROOT / "tag" / "delivery" / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertIn("TaG-managed", html)
        self.assertIn("Self-managed local", html)
        self.assertIn("Self-managed cloud", html)
        self.assertIn("Governed mode required", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_delivery_ui.py`
Expected: FAIL because UI shell files do not exist

- [ ] **Step 3: Add the first local GUI shell**

```html
<!-- tag/delivery/ui/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>TaG Setup</title>
    <link rel="stylesheet" href="./app.css" />
  </head>
  <body>
    <main class="app">
      <section class="hero">
        <p class="eyebrow">TaG Local Setup</p>
        <h1>Governed mode required before TaG can be used</h1>
        <p class="lede">Pick your runtime path, pair this machine, and complete governed activation.</p>
      </section>
      <section class="panel">
        <h2>Runtime Path</h2>
        <div class="choices">
          <button data-runtime="managed">TaG-managed</button>
          <button data-runtime="local">Self-managed local</button>
          <button data-runtime="cloud">Self-managed cloud</button>
        </div>
        <p class="hover-note">Hover help and guided explanations land in the next implementation task.</p>
      </section>
      <section class="panel">
        <h2>Trust Status</h2>
        <p id="governance-state">Governed mode inactive</p>
      </section>
      <script src="./app.js"></script>
    </main>
  </body>
</html>
```

```css
/* tag/delivery/ui/app.css */
body {
  margin: 0;
  font-family: Georgia, serif;
  background: linear-gradient(180deg, #f4efe5 0%, #e2ddd3 100%);
  color: #1f1c17;
}

.app {
  max-width: 920px;
  margin: 0 auto;
  padding: 40px 20px 80px;
}

.panel,
.hero {
  background: rgba(255, 252, 245, 0.9);
  border: 1px solid rgba(31, 28, 23, 0.12);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 20px;
}

.choices {
  display: grid;
  gap: 12px;
}
```

```javascript
// tag/delivery/ui/app.js
document.querySelectorAll("[data-runtime]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#governance-state").textContent =
      `Runtime path selected: ${button.dataset.runtime}`;
  });
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_delivery_ui.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_delivery_ui.py tag/delivery/ui
git commit -m "Add TaG local GUI setup shell"
```

### Task 7: Local Setup Service

**Files:**
- Create: `tag/delivery/local/setup_server.py`
- Test: `agent-enforcement/test_tag_setup_server.py`

- [ ] **Step 1: Write the failing setup-server test**

```python
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.local.setup_server import build_setup_snapshot


class TagSetupServerTests(unittest.TestCase):
    def test_setup_snapshot_includes_mode_runtime_and_governance_fields(self) -> None:
        snapshot = build_setup_snapshot({"mode": "managed", "runtime_path": "managed", "governed": False})
        self.assertEqual(snapshot["mode"], "managed")
        self.assertEqual(snapshot["runtime_path"], "managed")
        self.assertFalse(snapshot["governed"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 agent-enforcement/test_tag_setup_server.py`
Expected: FAIL because setup-server module does not exist

- [ ] **Step 3: Implement the minimal setup service model**

```python
# tag/delivery/local/setup_server.py
from __future__ import annotations


def build_setup_snapshot(state: dict) -> dict:
    return {
        "mode": state.get("mode"),
        "runtime_path": state.get("runtime_path"),
        "governed": bool(state.get("governed")),
        "health": state.get("health", "unknown"),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 agent-enforcement/test_tag_setup_server.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent-enforcement/test_tag_setup_server.py tag/delivery/local/setup_server.py
git commit -m "Add TaG local setup service snapshot"
```

### Task 8: Full Phase-1 Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add delivery verification commands to the README**

```md
## Delivery Phase 1 Verification

```bash
python3 agent-enforcement/test_tag_delivery_paths.py
python3 agent-enforcement/test_tag_hosted_enrollment.py
python3 agent-enforcement/test_tag_bootstrap_manifest.py
python3 agent-enforcement/test_tag_setup_state.py
python3 agent-enforcement/test_tag_governed_install.py
python3 agent-enforcement/test_tag_delivery_ui.py
python3 agent-enforcement/test_tag_setup_server.py
```
```

- [ ] **Step 2: Run the complete verification set**

Run:

```bash
python3 agent-enforcement/test_tag_config.py
python3 agent-enforcement/test_tag_hook_bootstrap.py
python3 agent-enforcement/test_tag_skill_autoload.py
python3 agent-enforcement/test_tag_session_autosave.py
python3 agent-enforcement/test_tag_crash_checkpoint.py
python3 agent-enforcement/test_tag_compaction_recovery.py
python3 agent-enforcement/test_tag_env_guard.py
python3 agent-enforcement/test_tag_spending_guard.py
python3 agent-enforcement/test_tag_release_gates.py
python3 agent-enforcement/test_tag_shared_brain_schema.py
python3 agent-enforcement/test_tag_hook_installer.py
python3 agent-enforcement/test_tag_mcp_loader.py
python3 agent-enforcement/test_tag_fork_schema.py
python3 agent-enforcement/test_tag_governance_hooks.py
python3 agent-enforcement/test_tag_policy_model.py
python3 agent-enforcement/test_tag_memory_provider.py
python3 agent-enforcement/test_tag_delivery_paths.py
python3 agent-enforcement/test_tag_hosted_enrollment.py
python3 agent-enforcement/test_tag_bootstrap_manifest.py
python3 agent-enforcement/test_tag_setup_state.py
python3 agent-enforcement/test_tag_governed_install.py
python3 agent-enforcement/test_tag_delivery_ui.py
python3 agent-enforcement/test_tag_setup_server.py
python3 -m py_compile $(find tag -maxdepth 4 -name '*.py' | tr '\n' ' ')
```

Expected: all tests PASS, `py_compile` exits 0

- [ ] **Step 3: Commit**

```bash
git add README.md agent-enforcement
git commit -m "Document TaG delivery phase 1 verification"
```
