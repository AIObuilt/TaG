# Getting Started with TaG

## What You Get

TaG adds governance to your AI agent. Every action your agent takes — writing files, running commands, making API calls — goes through TaG's policy engine first. Dangerous actions get blocked before they happen.

TaG works with any LLM agent that supports shell-based pre-execution hooks: Claude Code, Codex CLI, Cursor, or any agent you build yourself using the Anthropic SDK or other provider SDKs.

## Prerequisites

- Python 3.10+
- An AI agent with pre-execution hook support

## Install (2 minutes)

```bash
git clone https://github.com/AIObuilt/TaG.git
cd TaG
export TAG_HOME=$(pwd)
mkdir -p tag-runtime/config
cp tag/config/authority-matrix.template.json tag-runtime/config/authority-matrix.json
python3 tag_serve.py
```

The dashboard opens at `http://localhost:18800` after setup.

## How the Hook Interface Works

TaG hooks are plain Python scripts. The integration pattern is identical regardless of which agent you use:

1. Your agent is about to execute a tool call (read a file, run a command, fetch a URL, etc.)
2. The agent pipes a JSON description of that call to the hook's stdin
3. The hook evaluates it against policy and prints a result to stdout
4. The agent reads the result: empty object `{}` means allow, a `decision: block` object means stop

**Input** (what the agent sends to stdin):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "curl https://api.stripe.com/v1/charges"
  }
}
```

**Output** (what the hook prints to stdout):
- Allow: `{}`
- Block: `{"decision": "block", "reason": "SPENDING BLOCKED: command targets payment endpoint"}`

Every block is also written to an audit log under `tag-runtime/logs/`.

## Test a Hook Standalone (No Agent Required)

Before wiring TaG into any agent, verify it works directly from the terminal. Run from your TaG directory:

```bash
# Should be blocked — .env file access
echo '{"tool_name": "Read", "tool_input": {"file_path": ".env"}}' | python3 tag/hooks/env-guard.py

# Should be blocked — payment API call
echo '{"tool_name": "Bash", "tool_input": {"command": "curl https://api.stripe.com/v1/charges"}}' | python3 tag/hooks/spending-guard.py

# Should be allowed — ordinary file read
echo '{"tool_name": "Read", "tool_input": {"file_path": "README.md"}}' | python3 tag/hooks/env-guard.py
```

A blocked call prints something like:
```json
{"decision": "block", "reason": "BLOCKED: ..."}
```

An allowed call prints:
```json
{}
```

## Connect to Your Agent

### Claude Code

Claude Code reads pre-execution hooks from `~/.claude/settings.json`. Add a `PreToolUse` entry for each hook you want active:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 /path/to/TaG/tag/hooks/spending-guard.py",
        "timeout": 5000
      },
      {
        "type": "command",
        "command": "python3 /path/to/TaG/tag/hooks/env-guard.py",
        "timeout": 5000
      },
      {
        "type": "command",
        "command": "python3 /path/to/TaG/tag/hooks/credential-scope-guard.py",
        "timeout": 5000
      }
    ]
  }
}
```

Replace `/path/to/TaG` with your actual TaG directory (run `pwd` inside the cloned folder to get it). Restart Claude Code after saving.

### Codex CLI

Codex CLI supports a `exec` hook in its config file. Add TaG hooks to the `hooks.preExec` array in your Codex config:

```json
{
  "hooks": {
    "preExec": [
      "python3 /path/to/TaG/tag/hooks/spending-guard.py",
      "python3 /path/to/TaG/tag/hooks/env-guard.py"
    ]
  }
}
```

Codex pipes the tool call JSON to stdin and expects the same allow/block response on stdout.

### Any Agent (Generic Pattern)

If your agent supports shell-based pre-execution hooks, the pattern is:

1. Before executing a tool, pipe the call as JSON to `python3 /path/to/TaG/tag/hooks/<hook>.py`
2. Read stdout. If it contains `"decision": "block"`, abort the tool call and surface the `reason` to the user
3. Otherwise, proceed

To integrate TaG into a custom agent built with the Anthropic SDK or any other framework, add a pre-execution step that calls each hook script and checks the result before invoking the tool.

## Verify It Works with Your Agent

Once hooks are configured, test from inside your agent session:

**Test env-guard** — ask your agent to read a `.env` file:
```
Read the file .env
```
The agent should report the action was blocked.

**Test spending-guard** — ask your agent to run:
```
Run: curl https://api.stripe.com/v1/charges
```
The hook blocks it before the command executes. You'll also see the decision in the dashboard at `http://localhost:18800`.

## What Each Hook Does

**Governance hooks** (block dangerous actions before they happen):

| Hook | What it blocks |
|------|---------------|
| `spending-guard` | Commands targeting payment APIs (Stripe, Twilio, Vercel billing, etc.) |
| `env-guard` | Reading or staging `.env` files, private keys, credentials, and secrets |
| `credential-scope-guard` | Credentials crossing fork boundaries (e.g. Stripe key used outside `sales/`) |
| `build-gate` | Deploying without a passing build |
| `security-gate` | Deploying without a security review |
| `qa-gate` | Deploying without QA sign-off |
| `fork-scope-guard` | Agents reading or writing outside their assigned project fork |
| `webfetch-exfil-guard` | Web requests that look like data exfiltration |
| `os-acl-enforcer` | Unauthorized OS-level access |
| `delegate-enforcer` | Uncontrolled agent delegation |
| `agent-enforcer` | Agent identity and assignment enforcement |
| `verification-gate` | Completion claims without passing verification evidence |
| `completion-claim-guard` | Completion claims without evidence handles |
| `repo-hygiene-gate` | Completion claims when repo state is dirty or incomplete |
| `playwright-qa-gate` | UI completion claims without browser QA evidence |
| `playwright-security-gate` | Deploy-adjacent claims without browser security evidence |

**Operational hooks** (run on post-execution or stop events):

| Hook | What it does |
|------|-------------|
| `session-autosave` | Saves session context automatically |
| `memory-autosave` | Persists memory across sessions |
| `crash-checkpoint` | Checkpoints state on unexpected stops |
| `compaction-recovery` | Recovers state after context compaction |
| `skill-autoload` | Loads relevant skills at session start |

## Customize Your Authority Matrix

`tag-runtime/config/authority-matrix.json` controls which credentials belong to which project forks. The default template:

```json
{
  "forks": {
    "sales": {
      "directory": "sales/"
    },
    "support": {
      "directory": "support/"
    }
  },
  "credential_scopes": {
    "stripe": {
      "forks": ["sales"]
    },
    "zendesk": {
      "forks": ["support"]
    },
    "openai": {
      "forks": ["shared"]
    }
  }
}
```

Edit this to match your project layout:

- Add entries under `forks` for each sub-project or agent working area.
- Add entries under `credential_scopes` for each secret or API key, listing which forks are allowed to use it.
- Use `"forks": ["shared"]` for credentials any fork may access.

`credential-scope-guard` enforces these boundaries automatically once the file is saved.

## Launch the Dashboard

```bash
python3 tag_serve.py
```

The dashboard at `http://localhost:18800` shows:

- **Governance status** — which hooks are active, current authority matrix
- **Memory layers** — heartbeat pulse, engram entries, hindsight archive
- **Recent decisions** — live allow/block log for every governed action
- **Hook status** — installation state for each hook

Set `TAG_UI_PORT` to run on a different port:

```bash
TAG_UI_PORT=9000 python3 tag_serve.py
```
