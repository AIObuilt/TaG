# Vance / TaG Boundary Design

**Goal:** Define the boundary between `Vance` as Jason's personal governed operating system and `TaG` as the productized Trust and Governance framework.

**Scope:** This spec defines identity, ownership boundaries, memory boundaries, repo boundaries, hosted-vs-local responsibilities, and migration rules. It does not yet move files or create the standalone TaG product repo.

## Product Naming

### Vance

`Vance` is the personal system.

It is:

- Jason's internal governed AI operating environment
- controlled chaos
- memory-rich
- adaptive
- experimental when needed
- allowed to contain personal context and personal operational surfaces

### TaG

`TaG` is the product.

It stands for:

- Trust
- and
- Governance

It is:

- structured
- installable
- supportable
- repeatable
- memory-capable
- not allowed to contain Jason-specific personal memory

## Core Distinction

The boundary is not:

- Vance has memory, TaG does not

The boundary is:

- Vance contains Jason's personal memory and personal operating context
- TaG contains only product-required operational memory structures and customer-owned operational state

That means TaG may include:

- memory structure
- operational memory
- workflow state
- audit history
- policy state
- health and trust state

But TaG may not include:

- Jason's personal memory
- Jason-specific working context
- Jason-only standing orders
- Jason's historical experimentation artifacts unless deliberately productized

## Identity Boundary

### Vance Identity

Vance is:

- the internal governed multi-LLM operating system
- the larger workshop
- the source of invention, experimentation, and live internal operations

Vance can be messy because it is a live system under continuous use.

### TaG Identity

TaG is:

- the commercial framework customers install
- the clean trust-and-governance surface
- the repeatable local control plane
- the supportable product

TaG should never be described as Jason's internal brain or personal autonomous environment.

It should be described as:

- the structured local trust-and-governance framework
- with optional hosted support, billing, and managed routing services

## Memory Boundary

### Allowed in TaG

- machine enrollment state
- runtime inventory
- workflow gate state
- policy state
- approval queue state
- audit/event records
- operator identity records owned by the customer
- local frustration counters used for product behavior
- customer-installed workflow and runtime configuration

### Not Allowed in TaG

- Jason-specific memories
- personal handoff notes
- Jason contact relationships
- Jason-specific business priorities
- personal shared brain files
- internal Vance memory banks that only make sense inside Jason's environment

### Design Rule

If memory answers the question:

> what must this installed system remember in order to run safely and serve the customer?

it may belong in TaG.

If memory answers the question:

> what does Jason know, prefer, remember, or carry across his own operating environment?

it stays in Vance.

## Repo Boundary

### Vance Repo / Workspace

The Vance workspace is the parent environment.

It can contain:

- TaG source while TaG is still being extracted
- Jason-specific operational systems
- support tools
- experiments
- research
- memory systems
- internal services
- cross-project operational infrastructure

Vance is the workshop and the operating environment.

### TaG Repo

The TaG repo must become the product source of truth.

It should contain only what a customer installation, product build, or product support workflow requires.

That includes:

- local framework runtime
- governance and trust logic
- installer/bootstrap code
- local GUI code
- service definitions
- OS-specific install logic
- config templates
- product docs/specs/plans relevant to TaG
- tests for TaG behavior

It should not contain:

- Jason's personal memories
- Vance shared-brain material
- internal-only side experiments
- logs
- local machine state
- backups
- personal certs/keys
- customer-specific runtime debris

## Hosted Boundary

TaG should be understood as having two cooperating layers:

### 1. TaG Local

This is the actual installed product.

It owns:

- local runtime execution
- local trust and governance
- local operator console
- local workflow state
- local resilience during hosted outages

### 2. TaG Hosted

This is the commercial service layer.

It owns:

- onboarding
- account identity
- fleet view
- billing
- machine enrollment
- managed routing when enabled
- support visibility

Hosted TaG is not the same thing as Vance.

Hosted TaG is product infrastructure, not Jason's private operating system.

## Source Classification Rules

Every file or subsystem should be classed as one of these:

### Class A: TaG Product Core

Belongs in TaG.

Examples:

- governance engine
- trust layer
- installer
- local GUI
- policy compiler
- audit/event schema
- approval queue model
- supported runtime adapters

### Class B: TaG Hosted Service

Belongs in TaG hosted/service repo or the TaG platform area.

Examples:

- onboarding site
- billing service
- machine enrollment service
- managed routing API
- fleet/support dashboard

### Class C: Vance Internal

Must stay in Vance.

Examples:

- Jason-specific memory banks
- internal research loops
- personal fork management
- Jason-only standing orders
- internal multi-business orchestration
- personal operational agents

### Class D: Local Runtime State

Belongs in neither source repo as committed source.

Examples:

- logs
- caches
- pid files
- session traces
- machine-specific secrets
- generated local databases
- temporary sync output

## Migration Rule

TaG should be extracted from Vance, not cloned wholesale.

The rule is:

- do not ask “what from Vance can we ship?”
- ask “what must exist for TaG to work as a product?”

That keeps the product smaller, cleaner, and more supportable.

## Packaging Rule

TaG should be packageable without requiring:

- Vance memory surfaces
- Jason personal context
- Jason's internal support scripts
- Jason-specific launch conventions

If TaG cannot install cleanly without one of those, the boundary is still wrong.

## Support Rule

Supportable product surfaces belong to TaG.

Jason-only operator convenience surfaces belong to Vance.

If a customer success or support engineer needs it to:

- install
- recover
- diagnose
- upgrade
- pair
- verify trust state

then it should live in TaG, not in Vance-only tooling.

## Commercial Rule

TaG is the sellable thing.

Vance is the invention engine and internal operating environment behind it.

Customers may eventually know that TaG came from Vance, but they should not need Vance in order to buy, install, or trust TaG.

## Practical Repo Rule

In the near term:

- `/Users/jason/vance` remains the parent repo/workspace
- TaG is defined as an extraction boundary inside it
- the TaG file set should be identified explicitly before creating the dedicated product repo

In the next phase:

- create a dedicated TaG repo
- move Class A and Class B product code into that boundary
- keep Class C in Vance
- never commit Class D runtime state

## Recommendation

Use this model going forward:

- `Vance` = Jason's personal governed system, controlled chaos, personal memory allowed
- `TaG` = Trust and Governance product, structured and installable, no Jason-specific personal memory
- `TaG Local` = the installed local framework customers actually run
- `TaG Hosted` = onboarding, billing, managed routing, fleet, and support layer

This gives you:

- cleaner product language
- cleaner repo separation
- cleaner liability boundary
- cleaner support model
- a path to scale TaG without shipping Vance itself
