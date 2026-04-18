# 2026-04-17 TaG Candidate File Set

This note captures the first concrete TaG extraction slice based on the governance hook set and the memory-control prompt surfaces.

## Extraction Principle

Extract the moat first:

- governance hooks
- memory-control prompts and state recovery rules

Do not extract Jason-specific memory content, personal standing orders, or Vance-only memory surfaces.

## Inventory Summary

### Governance Hook Canonical Source

Canonical hook source currently lives at:

- `/Users/jason/vance/hooks/`

Installed Claude copies currently live at:

- `/Users/jason/.claude/hooks/`

The product-safe source of truth should be the canonical source tree, not the installed copies.

### Generic Enforcement / Governance Hooks — TaG Core

These are the strongest Class A candidates because they encode reusable trust and governance behavior rather than Jason-specific memory:

- `hooks/_vance_bootstrap.py`
- `hooks/agent-enforcer.py`
- `hooks/bash-write-guard.py`
- `hooks/block-fabrication.py`
- `hooks/build-gate.py`
- `hooks/build-tracker.py`
- `hooks/credential-scope-guard.py`
- `hooks/delegate-enforcer.py`
- `hooks/deletion-guard.py`
- `hooks/deploy-gate.py`
- `hooks/deploy-watcher.py`
- `hooks/env-guard.py`
- `hooks/fork-scope-guard.py`
- `hooks/os-acl-enforcer.py`
- `hooks/qa-gate.py`
- `hooks/quality-gate.py`
- `hooks/root_daemon_notifier.py`
- `hooks/security-gate.py`
- `hooks/security-scan.py`
- `hooks/spending-guard.py`
- `hooks/webfetch-exfil-guard.py`

These form the initial TaG governance hook set.

### Memory-Control / Recovery Hooks — TaG Core, But Needs De-Vance Pass

These are also Class A candidates, but they are not cleanly product-safe yet because they are currently wired to Vance-specific names, paths, or memory sinks:

- `hooks/crash-checkpoint.py`
- `hooks/compaction-recovery.py`
- `hooks/engram-autosave.py`

What is reusable here:

- heartbeat tracking
- checkpoint summary writing
- crashed-session archiving
- compaction buffer persistence
- prompt counter persistence
- post-compaction recovery context injection
- final session autosave behavior

What must be extracted or replaced:

- `engram` naming and direct `mem_save.py` dependence
- Vance-specific file names like `~/vance/vance-context/session-checkpoint.md`
- Vance-specific project labels like `vance-prime`
- Jason-specific recovery wording
- Telegram alert assumptions

### Prompt-Control / Prompt-Injection Hooks — Split

These are partially product-safe but require boundary cleanup:

- `hooks/analysis-anonymizer.py`
- `hooks/tax-pii-guard.py`
- `hooks/skill-autoload.py`

Product-safe core:

- prompt preprocessing
- redaction or anonymization scaffolding
- PII-sensitive checkpointing rules
- configurable skill/policy injection

Required cleanup:

- remove Vance-only branding and path assumptions
- remove Jason-specific trigger language
- convert skill autoload from Vance-specific defaults into product config

### Hooks That Are Vance-Specific or Customer-Policy-Specific by Default

These are not first-slice TaG core as written:

- `hooks/email-enforcer.py`
- `hooks/email-search-guard.py`
- `hooks/no-cc-cold-outreach.py`
- `hooks/reply-to-guard.py`
- `hooks/save-to-sent.py`
- `hooks/watcher-gate.py`
- `hooks/watcher-review.py`

Reason:

- they are tied to Jason/Vance communication rules or highly opinionated workflow policies
- they may become TaG modules later, but not as part of the first clean extraction

## Memory-Control Prompt Surfaces

### Product-Safe Structural Prompt Surfaces

These define structure and recovery behavior rather than personal memory content:

- `hooks/compaction-recovery.py`
- `hooks/crash-checkpoint.py`
- `config/skill-autoload-rules.json`
- the generic prompt/state paths in `vance_config.py`

These are Class A candidates once renamed and de-Vanced.

### Vance-Specific Memory Content Surfaces — Do Not Extract

These remain Class C Vance internal:

- `shared-brain/`
- `vance-brain/`
- Jason-specific `MEMORY.md` content
- session handoff files with Jason-only operational context
- Jason standing orders and identity/priority files

TaG should keep the memory structure, not the personal memory payload.

## Foundational Config and Wiring Files for the First TaG Slice

These files are strong early TaG candidates because the hook set depends on them structurally:

- `vance_config.py`
- `config/skill-autoload-rules.json`
- `config/launchd/` as packaging references, not as final customer-specific plists
- `.claude/settings.json` only as a mapping reference for hook wiring, not as a product artifact

Important distinction:

- the hook wiring model belongs in TaG
- Jason's actual `.claude/settings.json` does not

## First TaG Candidate File List

### Class A — Immediate TaG Core Candidates

- `hooks/_vance_bootstrap.py`
- `hooks/agent-enforcer.py`
- `hooks/bash-write-guard.py`
- `hooks/block-fabrication.py`
- `hooks/build-gate.py`
- `hooks/build-tracker.py`
- `hooks/credential-scope-guard.py`
- `hooks/crash-checkpoint.py`
- `hooks/compaction-recovery.py`
- `hooks/delegate-enforcer.py`
- `hooks/deletion-guard.py`
- `hooks/deploy-gate.py`
- `hooks/deploy-watcher.py`
- `hooks/engram-autosave.py` after rename/replacement pass
- `hooks/env-guard.py`
- `hooks/fork-scope-guard.py`
- `hooks/os-acl-enforcer.py`
- `hooks/qa-gate.py`
- `hooks/quality-gate.py`
- `hooks/root_daemon_notifier.py`
- `hooks/security-gate.py`
- `hooks/security-scan.py`
- `hooks/spending-guard.py`
- `hooks/webfetch-exfil-guard.py`
- `vance_config.py`
- `config/skill-autoload-rules.json`

### Class A, But Requires De-Vance Refactor Before Extraction

- `hooks/analysis-anonymizer.py`
- `hooks/skill-autoload.py`
- `hooks/tax-pii-guard.py`

### Class C — Leave in Vance for Now

- `shared-brain/`
- `vance-brain/`
- Jason-specific `MEMORY.md` and handoff surfaces
- `vance-standing-orders.json`
- Jason-specific email and outreach guardrails
- watcher/email behavior hooks as currently written

## Key Refactor Work Before TaG Repo Extraction

The first TaG extraction cannot just copy files. It needs a de-Vance pass:

1. Rename Vance-specific concepts to TaG-neutral product names.
2. Replace `engram`-specific persistence language with memory-provider abstraction.
3. Separate generic checkpoint and compaction state from Jason-specific handoff language.
4. Convert hardcoded `~/vance/...` paths into product-local config and install-time paths.
5. Split product-safe hook defaults from Jason-only policy defaults.

## Recommendation

Start TaG extraction with:

- governance hooks
- checkpoint / compaction / session-state hooks
- minimal config needed to run them

Do not start with:

- personal memory banks
- hosted services
- customer onboarding UI
- Jason-specific communications policy

This first slice captures the actual TaG moat: trust, governance, and memory-control structure.

## Implemented First Slice

The first TaG-neutral runtime foundation now exists at:

- `/Users/jason/vance/tag/`
- `/Users/jason/vance/tag_config.py`

Implemented in this slice:

- product-neutral config root and runtime state paths
- product-neutral hook bootstrap
- TaG-owned skill autoload hook and rules config
- product-neutral session autosave hook
- product-neutral crash checkpoint hook
- product-neutral compaction recovery hook
- product-safe shared-brain schema templates
- product-safe hook manifest generator for the TaG hook namespace
- product-safe MCP loader for customer-managed runtime plugins
- first TaG fork manifest/schema templates
- TaG-owned heavy governance hooks for delegation, ACLs, credential scope, fork scope, and WebFetch exfil protection
- TaG-owned policy compiler and authority template
- TaG-owned memory provider abstraction and final autosave hook

This is no longer just the first scaffold. The TaG core now owns trust, governance, and operational-memory structure without relying on Jason-specific memory surfaces.

## Implemented Governance Slice

The first reusable TaG governance hooks now exist under the TaG-owned hook namespace:

- `/Users/jason/vance/tag/hooks/env-guard.py`
- `/Users/jason/vance/tag/hooks/spending-guard.py`
- `/Users/jason/vance/tag/hooks/build-gate.py`
- `/Users/jason/vance/tag/hooks/security-gate.py`
- `/Users/jason/vance/tag/hooks/qa-gate.py`

This extraction proves the product can own generic governance behaviors without importing Jason-specific operating rules:

- environment and secret staging protection
- spending and billing endpoint blocking
- release gating on current-session build state
- release gating on current-session security verdicts
- post-deploy QA gating with a narrow QA-tool allowlist

The product boundary is now real on both sides of the moat:

- memory-control and recovery hooks
- final session memory autosave through a product-safe provider
- first governance and release-protection hooks
- heavy governance and isolation hooks
- TaG-owned workflow policy/compiler surface

What still remains outside this implemented slice:

- producer-side status generators like build tracker / deploy watcher / security scan
- hosted onboarding / billing / fleet management
- installer packaging and local GUI delivery surfaces

## Verification Status

Verified passing with focused TaG tests:

- `python3 /Users/jason/vance/agent-enforcement/test_tag_config.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_hook_bootstrap.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_skill_autoload.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_session_autosave.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_crash_checkpoint.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_compaction_recovery.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_env_guard.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_spending_guard.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_release_gates.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_shared_brain_schema.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_hook_installer.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_mcp_loader.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_fork_schema.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_governance_hooks.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_policy_model.py`
- `python3 /Users/jason/vance/agent-enforcement/test_tag_memory_provider.py`
