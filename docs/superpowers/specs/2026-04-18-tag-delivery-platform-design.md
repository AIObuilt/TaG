# TaG Delivery Platform Design

**Goal:** Define the first product-delivery phase for TaG as an installable product with hosted onboarding, machine-scoped bootstrap, local GUI setup, governed completion gating, and clear managed vs self-managed runtime choices.

**Scope:** This spec covers phase-1 delivery architecture for `TaG Local` and `TaG Hosted`. It defines the install flow, billing gate, runtime-path selection, local GUI shell, hosted responsibilities, local responsibilities, and completion criteria. It does not yet define the full task breakdown or implementation sequence.

## Product Statement

TaG is delivered as a locally hosted trust-and-governance product with a hosted onboarding and management layer.

The install experience should feel like normal modern software:

- the user starts from a hosted onboarding URL
- the user signs into one account type
- the user chooses a mode during setup
- the hosted system generates a machine-scoped bootstrap command
- the local bootstrap opens a local GUI
- setup is blocked until governed mode is active
- after governed mode is active, the local GUI becomes the product console

The governance core is local. Hosted exists to reduce install friction, manage billing, provide fleet/support visibility, and enable managed routing.

## Product Layers

### TaG Core

Already complete in the seed repo:

- trust and governance hooks
- workflow policy/compiler
- operational-memory structure and provider
- product-safe shared-brain structure
- runtime/plugin support tooling

This is the open-core foundation.

### TaG Local

Phase 1 delivery layer:

- local bootstrap receiver
- local setup service
- local GUI shell
- governed install flow
- runtime-path selection
- post-install runtime controls
- local health and trust status

TaG Local is the actual product runtime and the trust boundary.

### TaG Hosted

Phase 1 hosted layer:

- account creation and login
- unified account type
- mode selection during setup
- billing collection for managed installs
- machine-scoped bootstrap command generation
- enrollment tracking
- support visibility

Hosted is not the runtime authority for day-to-day local execution.

## Account Model

There is one account type.

Users do not pick a different account product before signup.

Instead:

- users create one account
- users choose a mode during setup
- users can switch later

This keeps the product surface simple and preserves the expected path from self-managed to managed.

## Mode Model

Mode choice happens during setup in the local GUI after pairing.

The two product modes are:

### Managed

Managed means TaG remains in the loop operationally.

Managed includes:

- TaG-managed routing
- hosted usage tracking
- billing
- support visibility
- operational help and recovery path

Managed is the recommended path.

### Self-Managed

Self-managed means the customer owns provider wiring and runtime operations.

Self-managed includes:

- customer-owned local models or cloud providers
- lower hosted involvement by default
- no managed-routing billing requirement during install

Self-managed must preserve a clean upgrade path into managed later.

## Billing Gate

The billing boundary must be strict.

### Managed

For managed installs:

- account must exist first
- billing must be collected before bootstrap is issued
- the machine is then allowed to enroll into the managed lane

Reason:

- avoids unpaid managed installs
- prevents machine-orphan and billing-cleanup problems
- stops managed routing from becoming an abuse surface

### Self-Managed

For self-managed installs:

- account must exist first
- billing is not required before bootstrap

If the user upgrades later:

- billing is collected at upgrade time
- managed services activate after billing succeeds

## Runtime Path Choice

Phase 1 setup must include a runtime-path choice inside the local GUI.

The user chooses one of:

1. `TaG-managed`
2. `Self-managed local`
3. `Self-managed cloud`

This choice should happen during setup, not before signup.

That keeps the account model unified and pushes operational detail into the product where it belongs.

## Install Flow

### 1. Hosted Entry

The user begins from the hosted TaG onboarding URL.

Hosted responsibilities at entry:

- authenticate user
- create account if needed
- show mode implications
- collect billing if managed is chosen
- create machine enrollment session
- generate machine-scoped bootstrap command

### 2. Machine-Scoped Bootstrap

The hosted system generates a short-lived machine-scoped bootstrap command.

The command must represent one enrollment event, not a reusable account token.

This improves:

- support clarity
- billing clarity
- abuse resistance
- machine ownership tracking

### 3. Userland Bootstrap

The user runs one command locally as a normal user.

The bootstrap does:

- downloads or materializes the local setup service
- verifies the payload
- binds the machine to the hosted enrollment session
- launches the local GUI in the browser

This command should not ask for privileges up front.

### 4. Local GUI Setup Shell

The local GUI becomes the setup surface.

The first GUI shell must include:

- pairing confirmation
- progress/status
- managed vs self-managed mode context
- runtime-path choice
- basic explanation of the trust model
- runtime controls with simple language
- instruction hovers for settings and controls

The runtime controls should feel approachable:

- explained in plain language
- with hover help for “what this does”
- with clear default and recommended choices

### 5. Governed Install Step

When the setup reaches trust-layer activation, the GUI requests the necessary privilege escalation.

The system must install the governed execution path for the OS.

This step is mandatory.

### 6. Completion Gate

Setup is not complete until governed mode is active.

There is no “skip for now” route that unlocks the product before governance is active.

Reason:

- keeps the trust claim honest
- avoids half-installed ambiguity
- avoids implied liability
- simplifies support posture

### 7. Post-Install Guided Flow

After governed mode is active, the user lands in a guided but skippable first-run flow.

The first screen should be:

- system health
- trust status
- governance active indicator

Only after that should the UI guide into runtime setup and operational controls.

## Local GUI Requirements

The first local GUI shell must include:

- setup progress
- trust/governance status
- runtime-path selection
- runtime controls
- simple status explanations
- instruction hovers

The first GUI shell should not try to be the full admin platform.

It needs to prove:

- TaG is running locally
- governance is active
- the user can understand and control runtime posture

## Runtime Controls

Runtime controls are required in phase 1, but should be layered.

### During Setup

The user should choose the high-level path:

- TaG-managed
- self-managed local
- self-managed cloud

Then the GUI should expose only the controls required for that choice.

### After Setup

The broader runtime controls become available:

- add/remove local runtimes
- add/remove cloud providers
- set default runtime posture
- see which path is recommended
- switch to managed later

These controls must remain simple and well-explained.

Hover help should explain:

- what the setting changes
- why it matters
- what the recommended option is

## Hosted vs Local Responsibilities

### Local Must Own

- governed execution
- trust enforcement
- runtime operation
- local health/status
- local runtime controls
- local failure handling
- local operation during hosted outages

### Hosted Must Own

- account and auth
- billing
- machine enrollment
- fleet visibility
- support visibility
- managed routing service
- usage metering
- upgrade/downgrade state

## Outage Behavior

If hosted is unavailable, local TaG must continue operating.

The local GUI should show a clear banner:

- management offline
- local governance still active
- sync/support visibility delayed until reconnect

Hosted must not be a hard dependency for governed local operation.

## DIY Upgrade Path

Self-managed users should be able to switch to managed from the local GUI later.

This path should be surfaced softly when the user struggles operationally, but phase 1 does not need the full frustration engine to be complete.

Phase 1 only needs:

- a visible managed upgrade path in the runtime controls
- clear explanation of what changes when managed is enabled

## OS Strategy

The product shape is cross-platform, but the first implementation target is macOS.

The GUI and hosted flow should be designed so Linux and Windows can reuse the same product model later.

What should vary by OS:

- bootstrap mechanics
- service registration
- privilege escalation
- governed install wiring

What should not vary by OS:

- account model
- mode model
- billing model
- GUI information architecture
- trust/gov completion gate

## Success Criteria

Phase 1 is successful when:

- a user can sign up on the hosted site
- a managed user cannot get a bootstrap command without billing
- a self-managed user can get a bootstrap command without billing
- the local bootstrap opens the local GUI
- the local GUI allows mode and runtime-path choice
- setup does not complete until governed mode is active
- after completion, the user can see health, trust status, and runtime controls
- the system remains locally operational if hosted management is unavailable

## Out of Scope

This phase does not yet require:

- polished fleet admin console
- advanced support tooling
- full frustration-based upsell automation
- Linux and Windows implementation details
- rich post-install workflow marketplace
- final visual refinement for the production GUI

## Recommendation

Build phase 1 in this order:

1. hosted onboarding and billing gate
2. machine-scoped bootstrap generation
3. local bootstrap receiver/service
4. local GUI setup shell
5. governed completion gate
6. runtime controls and mode switching surface

This keeps the phase centered on one thing:

turning the TaG core into an installable, chargeable product without weakening the local trust boundary.
