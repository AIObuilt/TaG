#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

python_json() {
  python3 - <<'PY' "$@"
import json
import sys
payload = json.loads(sys.argv[1])
print(json.dumps(payload))
PY
}

section() {
  printf '\n== %s ==\n' "$1"
}

run_stdin_hook() {
  local title="$1"
  local hook="$2"
  local payload="$3"
  section "$title"
  printf 'Hook: %s\n' "$hook"
  printf 'Payload: %s\n' "$payload"
  printf 'Result:\n'
  python_json "$payload" | python3 "$hook"
}

printf 'TaG 60-second governance demo\n'
printf 'Repo: %s\n' "$ROOT"

run_stdin_hook \
  "1. .env staging attempt is blocked" \
  "$ROOT/tag/hooks/env-guard.py" \
  '{"tool_name":"Bash","tool_input":{"command":"git add .env"}}'

run_stdin_hook \
  "2. Payment endpoint call is blocked" \
  "$ROOT/tag/hooks/spending-guard.py" \
  '{"tool_name":"Bash","tool_input":{"command":"curl https://api.stripe.com/v1/payment_intents"}}'

run_stdin_hook \
  "3. Final completion claim without evidence is blocked" \
  "$ROOT/tag/hooks/completion-claim-guard.py" \
  '{"claim_type":"complete","response":"Done. The issue is fixed.","work_type":"code","evidence_ids":[]}'

printf '\nDemo complete.\n'
