# TaG Operational Gotchas

This file is a product-safe durable record of mistakes, surprises, and operational edge cases that matter across customer installations.

Use it for:

- installer pitfalls
- runtime adapter quirks
- policy and workflow edge cases
- sync and recovery gotchas

Do not use it for:

- personal operator notes
- business-specific customer incidents
- project-specific deployment trivia unless it generalizes into product-specific guidance

## How To Write Entries

Each entry should capture:

- symptom
- root cause
- fix
- how to avoid repeating it

Each entry should be generic enough to help another customer-installed TaG system, not just one internal workspace.

## Example Categories

- local installer privilege escalation issues
- adapter/runtime config drift
- policy compiler/source-of-truth mismatch
- workflow gate behavior after deploy
- memory sync edge cases during reconnect

If a lesson is product-specific and likely to recur, it belongs here.
