# Vance Delivery Design

**Goal:** Define the customer delivery surface for Vance as a product: one hosted onboarding entrypoint, one machine-scoped bootstrap command, one local governed GUI, and one product model that scales across macOS, Linux, and Windows while building macOS first.

**Scope:** This spec covers the customer install journey, packaging boundary, product forks, local-vs-hosted responsibilities, failure behavior, activation flow, and the first platform rollout. It does not define the full implementation task list for each OS yet.

## Product Statement

Vance is delivered as a locally hosted governed execution framework with a hosted onboarding and management layer.

The product should feel like normal modern software:

- customers start from a hosted setup URL
- customers receive one install command
- the installer opens a local GUI that feels like a normal app
- the local framework becomes the real runtime and trust boundary

The hosted surface exists to reduce install friction, improve support, handle billing, and maintain fleet visibility. It is not the runtime authority for day-to-day governed operation.

## Core Delivery Principles

- The real product must run locally.
- Full governed mode is required before setup is considered complete.
- The installer should begin in userland and escalate only when privileged setup is required.
- The hosted layer should create a seamless install experience, not replace the local framework.
- The local GUI should feel familiar enough that most customers do not need to think about localhost mechanics.
- The Mac build is first. Linux and Windows follow under the same product shape.

## Top-Level Product Fork

The primary product fork is not operating system. The primary fork is:

### 1. Managed

Vance remains in the operational loop.

Managed mode includes:

- Vance-managed routing as an available default
- Vance support visibility
- Vance usage tracking for billing
- Vance-operated cost/capability optimization
- Vance ability to help repair or stabilize the deployment

Managed mode is the recommended path because it is the shortest route to a working system and the clearest revenue path.

### 2. DIY

The customer owns the stack and the runtime wiring.

DIY mode includes:

- customer-managed providers and credentials
- customer-owned maintenance burden
- the truer self-hosted story
- less Vance operational involvement by default

DIY must still preserve a path to upgrade into managed help later.

## Routing and Runtime Posture

Both product lanes can expose multiple runtime choices, but the ownership boundary changes.

The customer may:

- install their own local/open-source LLMs
- connect their own third-party providers
- use Vance-managed routing and pay for usage

When Vance-managed routing is enabled, Vance should:

- optimize automatically for cost and capability
- prefer open-source and low-cost paths where they are sufficient
- track usage centrally for billing
- allow a manual override for customers who need to pin or force a specific runtime/model path

## Platform Selection Model

The operating system should not be a top-level customer decision.

The installer should autodetect:

- macOS
- Linux
- Windows

The product story stays the same across platforms. Only the bootstrap, service setup, privilege step, and packaging details vary by OS.

The rollout order is:

1. macOS first
2. Linux second
3. Windows third

## Customer Install Journey

### Step 1: Hosted Entry

The customer begins from a hosted Vance onboarding URL.

Hosted onboarding is responsible for:

- account creation and authentication
- plan and lane selection
- managed vs DIY selection
- generating a machine-scoped bootstrap command
- support visibility for the enrollment event
- billing identity and usage association

Account creation must happen before the bootstrap command is issued.

This avoids:

- orphaned machines
- weak ownership mapping
- pairing ambiguity
- billing confusion
- abuse of managed routing

### Step 2: Machine-Scoped Bootstrap Command

Hosted onboarding generates a short-lived machine-scoped install command.

This command should represent one enrollment event, not a reusable account secret.

The reason is operational clarity:

- better support
- cleaner billing
- clearer machine ownership
- lower abuse risk
- fewer pairing mistakes

### Step 3: Userland Bootstrap

The customer runs one command locally as a normal user.

The bootstrap command should:

- download and verify the installer payload
- start the local setup service
- open the local GUI in the browser
- bind the local machine to the hosted enrollment session

The first command should not ask for admin rights immediately.

### Step 4: Local GUI Setup

After bootstrap, the customer continues in the local GUI.

The local GUI handles:

- account pairing confirmation
- managed vs DIY confirmation
- runtime/routing setup
- health checks
- install progress
- explanation of why elevated privileges are required

The GUI should feel like a normal SaaS-style product surface, even though it is served locally.

### Step 5: Privileged Governed Install

When the setup reaches the trust-layer installation step, the installer requests elevated privileges.

This step is where the system installs the governed execution path for that operating system.

On macOS this includes the fully governed path, not just a userland demo tier.

### Step 6: Completion Gate

Setup is not complete until full governed mode is active.

This is a hard requirement.

Reasons:

- avoids ambiguity about what is actually protected
- avoids implied liability from half-installed states
- keeps the trust claim honest
- prevents support confusion about whether Vance is really active

There must be no “skip for now” path that unlocks normal product use without governed mode.

## Local vs Hosted Responsibilities

### Local Framework Must Own

- runtime execution
- trust and governance enforcement
- local status and health
- local workflow control
- local failure handling
- local frustration detection
- continued operation during hosted outages

### Hosted Layer Must Own

- onboarding
- account identity
- billing
- machine enrollment
- fleet visibility
- support visibility
- managed routing and usage metering when enabled
- exception and sync reporting

Hosted is the front door and the service layer. Local is the product runtime.

## Local GUI Model

The GUI should be installed locally and served locally.

It should feel like a normal app experience, not like a developer tool.

The customer should think of it as “the Vance app,” not “a localhost control panel,” unless they explicitly care about the technical details.

This points toward a local web app model rather than a heavy desktop wrapper for the first rollout.

Reasons:

- easier cross-platform shape
- easier hosted-to-local handoff
- easier support and UI iteration
- familiar feel for customers
- avoids unnecessary desktop-shell complexity in the first product version

## Managed Outage Behavior

If hosted management is unavailable in managed mode, the system must remain locally operational.

The local framework should continue working with governance active.

The local GUI should show a warning banner with trust/governance framing:

- management is offline
- local governance is still active
- usage/support sync will resume when reconnect occurs

The hosted layer must not be a hard dependency for governed local operation.

## Sync Behavior

When connectivity returns, sync should happen silently in the background.

Customers should not be asked to manage sync manually.

The GUI should only surface issues that actually need attention, such as:

- failed sync
- billing mismatch
- policy conflict
- governance exception requiring review

## DIY Frustration Upgrade Path

DIY installs must preserve the managed upsell path.

This should not be driven by cloud analytics or vague emotion detection.

The trigger should be purely local and narrow:

- after 3 failed attempts on the same setup or operational problem
- show a soft help card
- do not block work
- do not use a modal by default

The message should offer relief, not a sales pitch:

- continue managing this yourself
- let Vance manage routing and maintenance

This keeps the upgrade offer useful and respectful.

## First-Run Activation Flow

Once governed mode is active, the user should land in a guided first-run flow.

That flow should be skippable only after governance is fully active.

The first guided screen should be:

- system health
- trust status
- governance status

Only after that should the flow move into:

- runtime/provider connection
- workflow or agent template installation

This order reinforces the core product promise before asking the customer to configure anything.

## Initial macOS Deliverable

The first deliverable for macOS should be a coherent install surface that proves the full product motion:

- hosted onboarding site
- machine-scoped bootstrap command
- local setup web app
- privileged governed install step
- local governed runtime
- local post-install console
- managed/DIY split
- managed outage resilience
- silent sync
- local-only DIY friction detection

The initial macOS version is successful if a customer can:

1. create an account
2. get one bootstrap command
3. run it locally
4. complete governed install
5. land in the local Vance console
6. keep operating locally even if hosted management becomes unavailable

## Cross-Platform Extension Model

Linux and Windows should inherit the same product shape:

- hosted onboarding stays the same
- product fork stays the same
- machine-scoped bootstrap stays the same
- local governed GUI stays the same
- platform-specific service and privilege mechanics change underneath

The design should avoid Mac-only assumptions in the customer-facing install story, even while the first implementation targets macOS.

## Non-Goals

- shipping a CLI-first customer experience
- calling userland-only mode “complete”
- making hosted services the runtime authority for local governed execution
- exposing sync management as a normal workflow
- using cloud-based behavior tracking to detect frustration
- making OS choice the primary product fork

## Recommendation

Build Vance as a hosted-orchestrated, locally-governed product with:

- account-first onboarding
- a machine-scoped one-line bootstrap command
- a local SaaS-feeling GUI
- a hard completion gate on fully governed mode
- managed as the recommended lane
- DIY as the control lane
- silent hosted recovery and sync
- local-only, narrow upgrade prompts from DIY into managed help

This gives Vance the best chance of being:

- supportable
- commercially credible
- operationally honest
- scalable beyond technical users
