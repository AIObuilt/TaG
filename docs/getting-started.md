# Getting Started with TaG

## What You Get

TaG adds governance to your AI agent. Every action your agent takes — writing files, running commands, making API calls — goes through TaG's policy engine first. Dangerous actions get blocked before they happen.

## Prerequisites

- Python 3.10+
- An AI coding agent (Claude Code, Cursor, or similar)

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

## Connect to Claude Code (5 minutes)

TaG hooks plug directly into Claude Code's hook system. Each hook is a Python script that receives tool call events via stdin, checks policy, and returns an allow or block decision via stdout.

**Step 1 — Open your Claude Code settings file:**

```bash
cat ~/.claude/settings.json
```

If the file doesn't exist yet, create it:

```bash
mkdir -p ~/.claude
touch ~/.claude/settings.json
```

**Step 2 — Add TaG hooks to the `hooks` section.**

Replace `/path/to/TaG` with the directory where you cloned TaG (e.g. `/Users/you/TaG`):

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

**Step 3 — That's it.** Claude Code will now route every tool call through TaG's guards before executing.

> **Tip:** To find your TaG directory path, run `pwd` inside the cloned TaG folder.

## Verify It Works

Ask Claude to read a `.env` file:

```
Read the file .env
```

`env-guard` will block it and Claude will report that the action was blocked. You'll also see the decision logged in the dashboard at `http://localhost:18800`.

To verify `spending-guard`, ask Claude to run a command like:

```
Run: curl https://api.stripe.com/v1/charges
```

The hook will block it before the command executes.

## How the Hooks Work

Each hook receives a JSON object on stdin describing the tool call Claude is about to make:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "curl https://api.stripe.com/v1/charges"
  }
}
```

The hook evaluates the call against its policy and prints a JSON result to stdout:

- **Allow:** `{}` (empty object — execution continues)
- **Block:** `{"decision": "block", "reason": "explanation shown to the agent"}`

Every block is also written to an audit log under `tag-runtime/logs/`.

## What Each Hook Does

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

**Operational hooks** (add to `PostToolUse` or `Stop` events):

| Hook | What it does |
|------|-------------|
| `session-autosave` | Saves session context automatically |
| `memory-autosave` | Persists memory across sessions |
| `crash-checkpoint` | Checkpoints state on unexpected stops |
| `compaction-recovery` | Recovers state after context compaction |
| `skill-autoload` | Loads relevant skills at session start |

## Customize Your Authority Matrix

The authority matrix at `tag-runtime/config/authority-matrix.json` controls which credentials belong to which project forks. The default template looks like this:

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

Edit this file to match your project layout:

- Add entries under `forks` for each sub-project or agent working area.
- Add entries under `credential_scopes` for each secret or API key, listing which forks are allowed to use it.
- Use `"forks": ["shared"]` for credentials any fork may access.

Once saved, `credential-scope-guard` enforces these boundaries automatically.

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

## Add More Hooks

To add more hooks, extend the `PreToolUse` array in `~/.claude/settings.json`:

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
      },
      {
        "type": "command",
        "command": "python3 /path/to/TaG/tag/hooks/webfetch-exfil-guard.py",
        "timeout": 5000
      },
      {
        "type": "command",
        "command": "python3 /path/to/TaG/tag/hooks/fork-scope-guard.py",
        "timeout": 5000
      }
    ]
  }
}
```

Restart Claude Code after editing `settings.json` for changes to take effect.
