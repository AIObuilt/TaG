<p align="center">
  <img src="assets/apple-icon.png" alt="TaG" width="120" />
</p>

# TaG -- Trust and Governance for Agentic Execution

**Local-first governance for AI agents, sub-agents, and human operators working inside the same execution system.**

TaG is the open governance core for controlling what an actor can do, what evidence is required before work is considered complete, and what stays inside scope while the system is running.

The open-source core runs locally. No hosted dependency, no telemetry, no account.

---

## What TaG Enforces

### Runtime Governance

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
| Agent identity and assignment enforcement | `agent-enforcer` |

Additional operational hooks include `session-autosave`, `crash-checkpoint`, `compaction-recovery`, `memory-autosave`, and `skill-autoload`.

### Engineering Protocol

TaG open core also includes universal engineering governance primitives:

- `verification-gate` blocks final code-completion claims without passing verification evidence
- `completion-claim-guard` blocks final completion claims without evidence handles
- `repo-hygiene-gate` blocks completion and release claims when repo-hygiene state is missing, dirty, or incomplete
- `playwright-qa-gate` requires browser QA evidence for UI-facing completion claims
- `playwright-security-gate` requires browser security evidence for preview and deploy-facing completion claims

Supporting surfaces in the repo include:

- coding protocol defaults in `tag/config/coding-protocol.json`
- verification evidence models in `tag/verification/`
- Playwright starter templates
- model-agnostic verification playbooks

This is the open-core slice of workflow enforcement: verification before completion, repo hygiene before finalization, and browser QA/security evidence before UI or deploy-adjacent work can close.

---

## How It Works

TaG hooks into the execution path before a governed action runs.

For each governed action or completion claim, TaG can evaluate:

- local policy
- local runtime state
- local evidence state

The result is one of:

- allow
- hold
- block

```text
Actor
  |
  v
Action or completion claim
  |
  v
TaG hook
  |
  +--> policy check
  +--> runtime-state check
  +--> evidence check
  |
  v
Allow / Hold / Block
```

Policy is plain JSON. Governed state stays local. The open-source core does not require a server, account, or telemetry.

---

## Final Escalation

TaG keeps escalation inside the same governed system.

Models and sub-agents attempt the work first under the current policy, scope, and verification requirements. If the task still cannot be resolved, it escalates upward through more capable actors. The human is the final escalation point.

When that happens, the human inherits the context of the escalation:

- what was attempted
- what failed
- why the task escalated
- what evidence exists
- what boundaries still apply

The human is not asked to reconstruct the problem from scratch. TaG preserves the history and hands over the task with context intact.

---

## Why This Exists

AI agents now write code, run commands, manage credentials, call APIs, and move work toward release. Most systems still rely on broad permissions, weak scoping, and self-reported completion.

TaG exists to put governance in the execution path before the actor can do damage.

That means:

- before money is spent
- before credentials cross scope
- before a release moves without build, security, and QA gates
- before an actor crosses project boundaries
- before sensitive data leaves through a web request
- before work is declared complete without evidence

The actor stays useful. The actor stops being unchecked.

---

## Open Core

**TaG's governance core is open.**

This repository includes:

- local trust and governance hooks
- workflow policy/compiler surfaces
- operational-memory structure
- fork and runtime templates
- engineering protocol enforcement
- delivery phase-one primitives for setup and governed install state

The broader product layer is separate and still evolving:

- local GUI installer
- hosted onboarding
- billing, fleet, and support surfaces
- cost-aware multi-provider routing
- continuity and failover behavior across deployments

That split is intentional. The governance core should be inspectable, runnable, and useful on its own.

**TaG is model- and provider-agnostic by design, and enterprise deployments get access to cost-aware routing across latency, capability, and cost. Advanced continuity and failover behavior live in the product layer.**

---

## Example

If an agent tries to deploy without passing build, security, or QA gates, TaG blocks the action before it happens.

If an agent tries to access credentials owned by another fork, TaG blocks it and records the governed decision locally.

If an agent tries to send sensitive data to a known capture endpoint, TaG blocks the request before the data leaves.

If an actor tries to claim code is complete without verification evidence, or UI work is done without browser QA evidence, TaG can hold or block that completion path.

That is the point of the system: not post-hoc analysis, but governed execution.

---

## Install

TaG is pure Python with no external dependencies. Clone and configure:

```bash
git clone https://github.com/AIObuilt/TaG.git
cd TaG
export TAG_HOME=$(pwd)
mkdir -p tag-runtime/config
cp tag/config/authority-matrix.template.json tag-runtime/config/authority-matrix.json
```

## Verify

Run the full TaG suite:

```bash
for test in agent-enforcement/test_tag_*.py; do python3 "$test"; done
python3 -m py_compile $(find tag -maxdepth 4 -name '*.py' -print)
```

Everything in the open core is standard-library Python.

### Focused Verification

Core governance:

```bash
python3 agent-enforcement/test_tag_governance_hooks.py
python3 agent-enforcement/test_tag_spending_guard.py
python3 agent-enforcement/test_tag_env_guard.py
python3 agent-enforcement/test_tag_release_gates.py
python3 agent-enforcement/test_tag_policy_model.py
```

Engineering protocol:

```bash
python3 agent-enforcement/test_tag_verification_evidence.py
python3 agent-enforcement/test_tag_coding_protocol.py
python3 agent-enforcement/test_tag_completion_protocol.py
python3 agent-enforcement/test_tag_repo_hygiene_gate.py
python3 agent-enforcement/test_tag_playwright_templates.py
python3 agent-enforcement/test_tag_browser_protocol_gates.py
```

Delivery phase-one primitives:

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

The authority matrix maps forks and credential scopes to permitted resources:

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

The `sales` fork can access Stripe credentials but not Zendesk, and vice versa. Violations are blocked and logged to local governed state under `tag-runtime/`.

---

## License

Licensed under the [Business Source License 1.1](LICENSE). Free for internal use within your organization. Commercial restrictions apply to reselling or offering TaG as a managed service.

---

## About

TaG is built by [AIO Built](https://aiobuilt.co).

Contact: vance@aiobuilt.co

---

## Contributing

Open an issue or submit a pull request. Keep the open core standard-library only unless there is a very strong reason to break that rule.
