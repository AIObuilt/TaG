# TaG Engineering Protocol Design

## Goal

Extend TaG's open governance core from execution controls into universal engineering protocol. The public repo should prove that TaG can govern not only tool access, but also the rules for verifying, validating, and declaring software work complete.

This tranche adds a model-agnostic protocol layer for:
- repository hygiene
- verification-before-completion
- browser-level QA checks
- browser-level security checks
- completion claims tied to recorded evidence

The design must stay LLM-agnostic. TaG should ship protocol, evidence shape, policy defaults, and reusable browser verification templates without depending on any single model vendor or agent runtime.

## Why This Belongs In Open Core

TaG's open core currently proves execution governance: scope guards, credential gates, spending controls, fork isolation, and memory/recovery behavior. That is necessary, but incomplete for engineering work.

Serious engineering governance also requires rules around when work is allowed to be called done. The missing open-core layer is not coding style or team taste. It is universal software protocol:
- if code changed, verification must exist
- if a release is claimed ready, repo state and browser checks must be clean
- if a final completion claim is made, it must be backed by evidence
- if a deployment surface exists, QA and security validation should reach the browser layer, not stop at source code

Open-sourcing this layer strengthens TaG's position without giving away the managed operating layer. It proves TaG governs engineering outcomes, not just commands.

## Non-Goals

This tranche does not add:
- code-style enforcement
- team-specific workflow politics
- branch naming rules
- opinionated commit message policies
- hosted dashboards or exception workflows
- enterprise routing logic
- proprietary managed service orchestration

This tranche also does not require a specific browser runner implementation beyond a baseline Playwright-first path.

## Scope

### 1. Verification Protocol

TaG should add an explicit engineering verification protocol that defines what evidence is required before a worker or runtime can declare success.

Open-core rules:
- success claims require explicit verification evidence
- verification evidence must identify what was run
- verification evidence must report pass/fail status
- verification evidence must be attached to a local state file or structured event record
- missing evidence downgrades completion status to blocked or unverified

This protocol is universal and should apply regardless of whether verification came from Python tests, shell checks, or browser automation.

### 2. Repository Hygiene Protocol

TaG should add a repo hygiene gate for universal release/finish rules.

Open-core checks:
- block release or final-complete claims from a dirty repo state when the policy requires clean state
- block completion claims when tracked verification artifacts are missing
- optionally require touched-file coverage declarations when policy is enabled
- distinguish between local development allowance and release/finalization strictness

This gate should remain generic enough to work for customer repos beyond Vance.

### 3. Browser QA Protocol

TaG should add a browser-layer QA gate designed around Playwright as the default open-core runtime.

Open-core capabilities:
- baseline QA verification template for loading an app, checking critical UI presence, and asserting no obvious runtime-break state
- structured evidence output for browser QA runs
- policy-driven requirement that browser QA passes before final completion claims on UI-facing work
- ability to mark QA as required, optional, or skipped-with-reason depending on policy

The protocol should not assume a particular SaaS domain. It should define the shape of QA evidence and provide reusable starter checks.

### 4. Browser Security Protocol

TaG should add a browser security verification gate for final delivery checks.

Open-core capabilities:
- baseline browser security template to check for obvious failures such as unsafe headers expectations where visible through response inspection, mixed-content issues, missing auth redirects where required, or exposed debug/error surfaces
- structured evidence output for browser security runs
- policy-driven requirement that browser security checks pass before final completion claims on deployed or preview-facing surfaces
- explicit recording of what was checked and what was not

This is not a substitute for a full security program. It is a universal last-mile delivery protocol.

### 5. Completion Claim Discipline

TaG should add an explicit completion-claim guard.

Open-core rules:
- a final "done", "complete", "fixed", or equivalent success claim must cite evidence handles
- if required verification records are missing, completion claims are downgraded or blocked
- completion records should show whether code verification, QA verification, and security verification were satisfied
- the policy layer should define which evidence types are mandatory for which classes of work

This closes the gap between agent output language and actual verifiable status.

### 6. Model-Agnostic Verification Playbook

TaG should ship a model-agnostic verification playbook and baseline templates so any runtime can follow the same protocol.

This should include:
- a generic engineering verification playbook
- a generic Playwright QA playbook
- a generic Playwright security playbook
- an evidence schema that any agent/runtime can write to

The goal is not to ship one model's prompt tricks. The goal is to ship a portable operational contract.

## Architecture

### New Open-Core Components

The tranche should add the following product-safe surfaces:
- `tag/hooks/verification-gate.py`
- `tag/hooks/completion-claim-guard.py`
- `tag/hooks/repo-hygiene-gate.py`
- `tag/hooks/playwright-qa-gate.py`
- `tag/hooks/playwright-security-gate.py`
- `tag/policy/coding_protocol.py`
- `tag/config/coding-protocol.json`
- `tag/verification/evidence.py`
- `tag/verification/playwright_templates.py`
- `tag/verification/playbooks/` for model-agnostic protocol text/templates

### Policy Model

The coding protocol policy should define at least:
- `verification.required_for_completion`
- `verification.require_evidence`
- `repo_hygiene.require_clean_release_state`
- `repo_hygiene.require_verification_artifacts`
- `browser_qa.required_for_ui_work`
- `browser_security.required_for_preview_or_deploy_work`
- `completion.require_evidence_handles`
- `completion.allow_skip_with_reason`

The policy layer should stay simple and explicit. This tranche is not the place for adaptive heuristics.

### Evidence Model

Evidence records should be local, structured, and append-only enough for auditing. At minimum, they should capture:
- evidence id
- timestamp
- verification kind (`code`, `qa`, `security`)
- tool/runtime used
- target surface or command
- pass/fail/skip status
- summary
- artifact references if available

The evidence model should work whether the source is:
- Python test output
- shell verification output
- Playwright result output
- future managed verification services

### Hook Boundaries

The new hooks should be protocol guards, not test runners. Their job is:
- inspect evidence and policy
- decide allow/block/degrade behavior
- emit structured status

Baseline runner templates can exist under `tag/verification/`, but the hooks should not be tightly coupled to one exact workflow implementation.

## Public Repo Boundaries

Open source in TaG:
- protocol hooks
- policy schema/defaults
- evidence schema
- baseline Playwright templates
- model-agnostic playbooks

Keep in product/service layer:
- org-wide policy distribution
- hosted enforcement/audit dashboards
- managed exception handling
- enterprise continuity/failover orchestration
- custom customer policy packs bundled as managed service features

## Testing Strategy

This tranche needs focused unit tests and template verification tests.

Required test areas:
- evidence model serialization and validation
- verification gate behavior with and without evidence
- completion claim blocking/degrading logic
- repo hygiene gate behavior on clean vs dirty states
- QA gate behavior with required vs optional policy states
- security gate behavior with required vs optional policy states
- policy parsing/default behavior
- baseline Playwright template generation validity

The tests should avoid requiring a live browser session for core protocol verification. Template generation and evidence parsing should be testable locally.

## Risks

### 1. Overcoupling to one runtime

If the verification protocol becomes "Claude Code with Playwright" rather than "portable engineering verification", the LLM-agnostic claim weakens. The design must keep the protocol separate from any one agent runtime.

### 2. Overclaiming security

Browser security protocol must be framed as baseline delivery verification, not comprehensive application security.

### 3. Over-opinionated workflow rules

Open core should enforce universal engineering discipline, not one company's SDLC politics.

### 4. Fake evidence

The system should treat evidence as structured records, but this tranche will not fully solve cryptographic proof or remote attestation. It should remain honest about that limit.

## Success Criteria

This tranche is successful when:
- TaG open core clearly governs engineering protocol, not only execution permissions
- final completion claims can be blocked or degraded when evidence is missing
- UI-facing work can require browser QA and browser security checks through policy
- baseline Playwright templates and model-agnostic playbooks exist in the public repo
- the design remains generic enough for non-Vance repos and non-Claude runtimes

## Implementation Notes

The first implementation should prefer straightforward local JSON evidence records and simple policy evaluation.

Do not add:
- hosted dependencies
- heavy browser orchestration frameworks beyond baseline Playwright templates
- organization-specific workflow abstractions

Build the smallest universal protocol that proves the point cleanly.
