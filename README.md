# TaG

TaG is the standalone trust, governance, and operational-memory core extracted from Vance.

This seed repo contains:

- local trust and governance hooks
- workflow policy/compiler surfaces
- operational-memory provider and recovery hooks
- product-safe shared-brain structure
- product-safe tooling for hook manifests and MCP configuration

This repo does not yet contain the delivery layer:

- local GUI installer
- hosted onboarding
- billing, fleet, and support surfaces

## Verify

Run the seed verification set from the repo root:

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
```
