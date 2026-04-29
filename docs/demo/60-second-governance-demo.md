# TaG 60-Second Governance Demo

This demo proves three operator-safety claims with live repository hooks:

1. an agent tries to stage `.env` and gets blocked
2. an agent tries to hit a payment endpoint and gets blocked
3. an agent tries to claim final completion without evidence handles and gets
   blocked

## Run it

```bash
bash tools/tag-demo-60s.sh
```

## Transcript

The latest generated transcript is checked in at
`docs/demo/60-second-governance-demo.txt`.

## Why this matters

TaG is not selling abstract guardrails. It is enforcing concrete execution
boundaries:

- secret staging is blocked before it reaches git history
- payment and billing surfaces are blocked before spend happens
- final completion claims are blocked until evidence handles exist
