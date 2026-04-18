# TaG Core Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the product-safe TaG core by extracting the remaining governance, policy, memory, and packaging primitives from Vance.

**Architecture:** Finish TaG in four tranches: hook enforcement, authority/policy model, memory-provider abstraction, and packaging boundary. Each tranche lands as TaG-owned code under `tag/` with focused tests in `agent-enforcement/`, and each tranche is verified before moving to the next.

**Tech Stack:** Python 3, JSON schema/templates, existing Vance test entrypoints, git

---

### Task 1: Heavy Governance Hooks

**Files:**
- Create: `tag/hooks/agent-enforcer.py`
- Create: `tag/hooks/delegate-enforcer.py`
- Create: `tag/hooks/os-acl-enforcer.py`
- Create: `tag/hooks/credential-scope-guard.py`
- Create: `tag/hooks/fork-scope-guard.py`
- Create: `tag/hooks/webfetch-exfil-guard.py`
- Create: `agent-enforcement/test_tag_governance_hooks.py`

- [ ] Write failing tests for hook bootstrap, path policy, fork isolation, credential scope, and WebFetch exfil blocking
- [ ] Run the focused test file and confirm red
- [ ] Implement the minimal TaG-neutral hook set against `tag_config.py`
- [ ] Run the focused hook test file and confirm green
- [ ] Run the broader TaG test suite to catch regressions
- [ ] Commit the tranche

### Task 2: TaG Authority and Policy Model

**Files:**
- Create: `tag/policy/__init__.py`
- Create: `tag/policy/config_compiler.py`
- Create: `tag/policy/policy.py`
- Create: `tag/config/framework.json`
- Create: `tag/config/authority-matrix.template.json`
- Create: `agent-enforcement/test_tag_policy_model.py`

- [ ] Write failing tests for framework compilation, workflow enforcement, and authority template loading
- [ ] Run the focused test file and confirm red
- [ ] Implement the TaG-owned policy/config compiler surfaces
- [ ] Run focused tests and confirm green
- [ ] Run relevant existing framework/TaG tests to confirm compatibility
- [ ] Commit the tranche

### Task 3: Memory Provider Abstraction

**Files:**
- Create: `tag/memory/__init__.py`
- Create: `tag/memory/provider.py`
- Create: `tag/hooks/memory-autosave.py`
- Create: `agent-enforcement/test_tag_memory_provider.py`

- [ ] Write failing tests for provider resolution, summary persistence, and final session autosave behavior
- [ ] Run the focused test file and confirm red
- [ ] Implement a product-safe memory provider abstraction and wire the autosave hook to it
- [ ] Run focused tests and confirm green
- [ ] Run all TaG tests to confirm the memory layer integrates with checkpoint/compaction hooks
- [ ] Commit the tranche

### Task 4: Packaging Boundary

**Files:**
- Modify: `docs/superpowers/annotations/2026-04-17-tag-candidate-file-set.md`
- Modify: `docs/superpowers/annotations/2026-04-18-tag-repo-seed-manifest.md`
- Create: `docs/superpowers/annotations/2026-04-18-tag-packaging-boundary.md`

- [ ] Update the extraction and seed-manifest docs to include the completed TaG core
- [ ] Write the packaging boundary note defining what is ready to copy-first into a standalone TaG repo
- [ ] Re-run the full TaG verification set
- [ ] Commit the tranche
