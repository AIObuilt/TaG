<p align="center">
  <img src="assets/apple-icon.png" alt="TaG" width="120" />
</p>

# TaG -- Trust and Governance for AI Coding Agents

**The first local-first governance framework for AI coding agents.**

AI agents write code, run commands, manage credentials, call APIs, and deploy to production. They do all of this with broad permissions and no audit trail. TaG puts guardrails around that power.

---

## The Problem

AI coding agents operate with your credentials, your file system, and your cloud accounts. Without governance:

- An agent can spend real money on API calls with no budget enforcement
- Leaked credentials in tool calls go undetected
- Broken code gets deployed without build or security checks
- Agents cross project boundaries, reading and writing files they should not touch
- Sensitive data gets exfiltrated through web fetches
- There is no record of what the agent did or why

TaG intercepts agent tool calls via hooks and enforces policies before the action executes. Every decision is logged. Every boundary is enforced. Nothing requires a cloud service.

---

## What TaG Guards Against

| Threat | Hook |
|--------|------|
| Uncontrolled API/cloud spending | `spending-guard` |
| Credential leaks across scopes | `credential-scope-guard` |
| Deploying without passing build | `build-gate` |
| Deploying without security review | `security-gate` |
| Deploying without QA review | `qa-gate` |
| Agents reading/writing outside their fork | `fork-scope-guard` |
| Environment variable exposure | `env-guard` |
| Data exfiltration via web requests | `webfetch-exfil-guard` |
| Unauthorized OS-level access | `os-acl-enforcer` |
| Uncontrolled agent delegation | `delegate-enforcer` |
| Agent identity/role enforcement | `agent-enforcer` |

Additional operational hooks: `session-autosave`, `crash-checkpoint`, `compaction-recovery`, `memory-autosave`, `skill-autoload`.

---

## How It Works

TaG hooks into the agent's tool-call lifecycle. Before a tool call executes, TaG evaluates it against a policy defined in a JSON authority matrix. The hook either allows the call, blocks it, or flags it for human review.

All state stays local. Audit logs are append-only JSONL files on your machine. Policies are plain JSON. There is no server, no account, no telemetry.

```
Agent (Claude Code / Codex / Cursor)
  |
  v
Tool Call  --->  TaG Hook  --->  Policy Check (authority-matrix.json)
                   |                        |
                   v                        v
              Audit Log (JSONL)        Allow / Block / Flag
```

---

## At a Glance

- **11 governance hooks**, 862 lines of Python
- **Zero external dependencies** -- Python standard library only
- **Local-first** -- all state and audit logs stay on your machine
- **Append-only audit trail** -- every gate decision logged as JSONL
- **Policy-as-code** -- JSON authority matrix defines all permissions
- **Works with Claude Code today**, designed for cross-platform support (Codex, Cursor, and others)

---

## Install

TaG is pure Python with no dependencies. Clone and configure:

```bash
git clone https://github.com/aiobuilt/TaG.git
cd TaG
export TAG_HOME=$(pwd)
cp tag/config/authority-matrix.template.json tag-runtime/config/authority-matrix.json
```

### Verify

```bash
python3 agent-enforcement/test_tag_config.py
python3 agent-enforcement/test_tag_hook_bootstrap.py
python3 agent-enforcement/test_tag_governance_hooks.py
python3 agent-enforcement/test_tag_spending_guard.py
python3 agent-enforcement/test_tag_env_guard.py
python3 agent-enforcement/test_tag_release_gates.py
python3 agent-enforcement/test_tag_fork_schema.py
python3 agent-enforcement/test_tag_policy_model.py
```

All tests use the standard library. No additional packages required.

### Delivery Phase 1 Verification

```bash
python3 agent-enforcement/test_tag_delivery_paths.py
python3 agent-enforcement/test_tag_hosted_enrollment.py
python3 agent-enforcement/test_tag_bootstrap_manifest.py
python3 agent-enforcement/test_tag_setup_state.py
python3 agent-enforcement/test_tag_governed_install.py
python3 agent-enforcement/test_tag_delivery_ui.py
python3 agent-enforcement/test_tag_setup_server.py
```

---

## Authority Matrix

The authority matrix maps forks (project scopes) to permitted credentials and resources:

```json
{
  "forks": {
    "sales": { "directory": "sales/" },
    "support": { "directory": "support/" }
  },
  "credential_scopes": {
    "stripe": { "forks": ["sales"] },
    "zendesk": { "forks": ["support"] },
    "openai": { "forks": ["shared"] }
  }
}
```

The `sales` fork can access Stripe credentials but not Zendesk, and vice versa. Violations are blocked and logged to the append-only JSONL audit trail under `tag-runtime/audit/`.

---

## License

Licensed under the [Business Source License 1.1](LICENSE). Free for internal use within your organization. Commercial restrictions apply to reselling or offering TaG as a managed service.

---

## About

TaG is built by [AIO Built](https://aiobuilt.co).

Author: Jason McCall (jason@finditsales.com)

---

## Contributing

Open an issue or submit a pull request. Maintain the zero-dependency constraint -- if it is not in the Python standard library, it does not belong here.
