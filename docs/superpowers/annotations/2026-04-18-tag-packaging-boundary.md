# TaG Packaging Boundary

This note defines what is now ready to copy-first into a standalone `TaG` repo after the core-completion pass.

## Ready Now

The TaG core is now complete enough to split as a seed repo because it contains:

- TaG-owned namespace and config root
- operational-memory structure and provider
- final autosave hook
- release gates and environment/spending guards
- heavy governance and isolation hooks
- workflow policy/compiler surface
- shared-brain structure templates
- product-safe MCP and hook installer tooling
- fork manifest/schema templates

## Still Out Of Scope

The following are not part of the copy-first TaG seed:

- Jason memory or Vance shared-brain data
- Vance internal services and sidecars in their current form
- business fork contents
- hosted onboarding, billing, fleet, and support consoles
- local GUI installer/delivery code
- producer-side operational generators like deploy watchers and build/security producers

## Copy-First Rule

The first standalone TaG repo should be created by copying the files listed in the seed manifest, not by moving or deleting the incubation copy in `Vance`.

That preserves:

- Vance stability
- clean rollback if the seed repo boundary needs adjustment
- the ability to keep refining TaG inside Vance while packaging catches up

## Product Boundary Statement

`TaG` is now complete as a trust/governance/operational-memory core.

What remains is product packaging and delivery:

- installer/bootstrap
- local GUI
- hosted setup and support surfaces
- managed-vs-DIY product wiring

That is a separate productization phase, not unfinished core extraction.
