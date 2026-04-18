from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.policy.config_compiler import compile_framework_config, load_framework_source
import tag.policy.policy as tag_policy


FRAMEWORK_FILE = ROOT / "tag" / "config" / "framework.json"
AUTHORITY_TEMPLATE_FILE = ROOT / "tag" / "config" / "authority-matrix.template.json"


class TagPolicyModelTests(unittest.TestCase):
    def test_tag_framework_compiler_emits_policy_and_runtime_map(self) -> None:
        compiled = compile_framework_config(load_framework_source(FRAMEWORK_FILE))
        self.assertEqual(compiled["policy"]["_generated_from"], "tag/config/framework.json")
        self.assertIn("workflow", compiled["policy"])
        self.assertEqual(compiled["runtime_map"]["codex"], "code")
        self.assertEqual(compiled["runtime_map"]["voice"], "comms")

    def test_tag_policy_holds_pre_deploy_when_required_gates_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            original_build = tag_policy.BUILD_STATUS_FILE
            original_security = tag_policy.SECURITY_VERDICT_FILE
            original_deploy = tag_policy.DEPLOY_STATE_FILE
            original_workflow = tag_policy.WORKFLOW_STATE_FILE
            try:
                tag_policy.BUILD_STATUS_FILE = tmp / "build-status.json"
                tag_policy.SECURITY_VERDICT_FILE = tmp / "security-verdict.json"
                tag_policy.DEPLOY_STATE_FILE = tmp / "deploy-state.json"
                tag_policy.WORKFLOW_STATE_FILE = tmp / "workflow-state.json"
                result = tag_policy.evaluate_action(
                    {
                        "surface": "code",
                        "runtime": "codex",
                        "action_type": "deploy",
                        "normalized_target": "vercel --prod",
                        "sensitive": False,
                        "metadata": {},
                    }
                )
            finally:
                tag_policy.BUILD_STATUS_FILE = original_build
                tag_policy.SECURITY_VERDICT_FILE = original_security
                tag_policy.DEPLOY_STATE_FILE = original_deploy
                tag_policy.WORKFLOW_STATE_FILE = original_workflow
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["workflow_stage"], "pre_deploy")
        self.assertEqual(result["workflow_enforcement"], "hold")
        self.assertIn("missing_gates", result)

    def test_tag_authority_template_contains_fork_and_credential_scopes(self) -> None:
        template = json.loads(AUTHORITY_TEMPLATE_FILE.read_text(encoding="utf-8"))
        self.assertIn("forks", template)
        self.assertIn("credential_scopes", template)
        self.assertIn("shared", template["credential_scopes"]["openai"]["forks"])


if __name__ == "__main__":
    unittest.main()
