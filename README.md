<p align="center">
  <strong>TaG</strong><br>
  <em>Trust and Governance for AI Agents</em>
</p>

<p align="center">
  <a href="https://github.com/AIObuilt/TaG/stargazers"><img src="https://img.shields.io/github/stars/AIObuilt/TaG?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/AIObuilt/TaG/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-BSL%201.1-blue" alt="License"></a>
  <a href="https://github.com/AIObuilt/TaG"><img src="https://img.shields.io/github/last-commit/AIObuilt/TaG" alt="Last Commit"></a>
  <a href="https://github.com/AIObuilt/TaG"><img src="https://img.shields.io/badge/platform-any-green" alt="Platform Agnostic"></a>
</p>

---

# Your AI agents have no guardrails. TaG fixes that.

TaG is a **local-first trust and governance layer** that sits between your AI agents and the damage they can do. It enforces spending limits, blocks credential leaks, gates deployments on actual QA, and routes work across models based on cost — not vendor defaults.

No hosted dependency. No telemetry. No account. Clone it and it works.

**The hooks architecture in TaG is covered by patent filings that predate Microsoft's open-source release of similar functionality.** This isn't a reaction to Big Tech — it's what they caught up to.

> 447 clones from 2 posts. If you believe AI agents need a trust layer, **[star this repo](https://github.com/AIObuilt/TaG)** — it's how open-source projects get found.

---

## What happens without TaG

Your agent calls `stripe charges create` at 3am. Nobody stops it.

Your agent pushes to production without running tests. The deploy hook doesn't exist.

Your agent leaks your `.env` into a commit. You find out on Twitter.

Your agent burns $400 on GPT-4 when a local model could have handled it.

**TaG makes all of these impossible.**

---

## 30-Second Quick Start

```bash
git clone https://github.com/AIObuilt/TaG.git
cd TaG/tag

# See what ships out of the box
ls hooks/         # 17 governance hooks, ready to install
ls config/        # routing baseline, authority matrix, coding protocol
ls routing/       # local-first cost-aware model router

# Run the governed read-only tool loop demo
python3 tools/governed_readonly_tool_loop.py
```

That's it. No setup wizard. No API key. No Docker. Plain Python, plain JSON configs, plain trust.

---

## What TaG Enforces

17 production-tested governance hooks that run as pre-execution gates:

| Hook | What It Blocks |
|------|---------------|
| `spending-guard` | Payment API calls (Stripe, billing endpoints, purchase URLs) |
| `credential-scope-guard` | Cross-project credential exposure |
| `env-guard` | `.env` and secrets in commits or tool output |
| `webfetch-exfil-guard` | Data exfiltration via outbound requests |
| `build-gate` | Completion claims without passing builds |
| `security-gate` | Deploys without security review |
| `qa-gate` | Production pushes without QA validation |
| `fork-scope-guard` | Cross-project file access |
| `os-acl-enforcer` | OS-level permission violations |
| `delegate-enforcer` | Uncontrolled agent delegation |
| `agent-enforcer` | Unauthorized actor assignment |
| `session-autosave` | Session state loss on crash |
| `crash-checkpoint` | Execution state loss on failure |
| `compaction-recovery` | Context window compaction errors |
| `memory-autosave` | Operational memory loss |
| `skill-autoload` | Missing capability at execution time |

Every hook writes to a local audit log. Every block is traceable.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Your Agent System              │
│         (Claude, GPT, Ollama, etc.)         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│                 TaG Layer                   │
│                                             │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Hooks    │ │  Policy  │ │  Routing  │  │
│  │ (17 gates)│ │  Engine  │ │ (local-1st)│  │
│  └───────────┘ └──────────┘ └───────────┘  │
│                                             │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Memory   │ │  Audit   │ │  Config   │  │
│  │(persistent)│ │  (local) │ │  (JSON)   │  │
│  └───────────┘ └──────────┘ └───────────┘  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           Execution Targets                 │
│    Local models, cloud APIs, tools, CLI     │
└─────────────────────────────────────────────┘
```

**Platform-agnostic.** TaG doesn't care if you run Claude Code, OpenAI Codex, Ollama, or something you built yourself. The governance layer wraps execution — it doesn't replace it.

---

## Cost-Aware Routing

TaG includes a local-first routing engine that picks the cheapest capable model, not the most expensive one:

```
Local (free) → Gemini → OpenAI → xAI → Anthropic → Codex → Claude
```

- **Local execution first** when the model is healthy and the task class matches
- **Timeout-aware escalation** — if local fails, it moves up; it doesn't hang
- **Session-aware routing** — multi-turn conversations stick to session-capable backends
- **Vision-aware fallback** — image tasks route to capable models automatically

Configuration is one JSON file: [`config/routing-baseline.json`](tag/config/routing-baseline.json)

---

## Policy Engine

TaG enforces workflow gates at the policy level:

- **Pre-commit:** build, security, and QA gates must pass
- **Pre-deploy:** all pre-commit gates plus commit verification (enforcement: `hold`)
- **Post-deploy:** live QA and live security validation required

The policy engine runs in `audit-first` mode by default — it logs everything and blocks sensitive actions. You can tighten to `hold` mode per workflow stage.

Sensitive actions are held. Unknown actions are audited. Nothing runs untracked.

---

## Who This Is For

- **Developers building agent systems** who are tired of agents that can't be trusted
- **Teams running multi-model architectures** who need cost control and routing
- **Solo builders and small teams** who can't afford a $50K/year governance platform
- **Anyone shipping AI to production** who needs an audit trail that isn't "we hope it works"

---

## Project Structure

```
tag/
├── hooks/          # 17 governance hooks (Python, zero external deps)
├── config/         # Routing baseline, authority matrix, coding protocol, framework
├── routing/        # Local-first cost-aware model router
├── policy/         # Policy engine with workflow gate enforcement
├── memory/         # Persistent local memory provider
├── tools/          # Governed tool loop examples
├── shared_brain/   # Agent context templates and handoff continuity
└── forks/          # Multi-project isolation manifests
```

---

## Background

TaG was built by [Jason McCall](https://linkedin.com/in/jasonmccall1) — not an engineer, but someone who spent two decades in automotive software and now operates AI agents for real business work. When your agents handle billing, deploys, and client communications, "hope it doesn't break" isn't a strategy.

The hooks architecture in TaG is covered by patent filings. The core concepts — governance hooks as pre-execution gates, cost-aware multi-provider routing, bounded autonomy with audit trails — were filed before Microsoft released their open-source agent tooling. This is documented and timestamped.

**Built because it had to exist, not because it was trendy.**

---

## Licensing

TaG is source-available under the **Business Source License 1.1**.

- Non-production use: allowed under BSL terms
- Production use: requires a commercial agreement until the Change Date
- Change License: Apache License 2.0

The open rails are real. The managed layer (tuned routing, learned affinity, hosted monitoring) is separate and commercial.

**Open the rails. Sell the train.**

---

## Links

- **GitHub:** [github.com/AIObuilt/TaG](https://github.com/AIObuilt/TaG)
- **AIO Built:** [aiobuilt.com](https://aiobuilt.com)
- **Jason McCall:** [LinkedIn](https://linkedin.com/in/jasonmccall1) · [X / Twitter](https://x.com/jasonic00)
- **Demo:** [60-second governance proof](docs/demo/60-second-governance-demo.md)

---

<p align="center">
  <strong>If you think AI agents need guardrails before they need more features, <a href="https://github.com/AIObuilt/TaG">star this repo</a>.</strong>
</p>
