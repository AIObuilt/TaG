# Contributing to TaG

## Guidelines

- Keep the open core standard-library only. No external dependencies unless there is a very strong reason.
- All governance hooks must be pure Python and self-contained.
- Tests go in `agent-enforcement/` and use `unittest` (stdlib).
- Run the full test suite before submitting:

```bash
for test in agent-enforcement/test_tag_*.py; do python3 "$test"; done
```

## Reporting Issues

Open an issue on GitHub with:
- What you expected
- What happened
- Steps to reproduce

## Pull Requests

- One logical change per PR
- Include tests for new functionality
- Keep commit messages clear and concise
