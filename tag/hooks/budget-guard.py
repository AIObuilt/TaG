#!/usr/bin/env python3
"""TaG Budget Guard — daily spending limit enforcement for LLM API calls.

Tracks cumulative daily spend via a state file, resets at midnight UTC, and
blocks paid API requests once the configured budget ceiling is hit.
Free/local models (cost $0) always pass through.

Two-phase hook pattern:
    Pre-exec  (main / default):  Debits the estimated cost optimistically so
        the budget depletes in real time as requests are approved.
    Post-exec (post_main / --post):  Reconciles with actual cost reported by
        the tool, or refunds the estimate if the request was aborted/errored.
        This prevents failed or overestimated requests from permanently
        consuming budget.

Usage:
    python budget-guard.py          # pre-tool-use (optimistic debit)
    python budget-guard.py --post   # post-tool-use (reconcile or refund)

Public interface:
    check_budget(model_id, estimated_cost) -> (allowed, reason)
    record_spend(model_id, cost, task_class, estimated_cost) -> None
    refund_estimate(amount) -> None
    BudgetConfig — dataclass for configurable thresholds
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import _tag_bootstrap  # noqa: F401
from _tag_guard_common import audit_log_entry, load_optional_json, save_json
from tag_config import AUDIT_DIR, RUNTIME_DIR, audit_log_path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOOK_NAME = "budget-guard"
AUDIT_LOG = audit_log_path(HOOK_NAME)
COST_LOG = AUDIT_DIR / "budget-cost-log.jsonl"
STATE_FILE = RUNTIME_DIR / "state" / "budget-state.json"
CONFIG_FILE = RUNTIME_DIR / "config" / "budget-config.json"

# Notification event file — consumers (email, Slack, webhook, etc.) watch this
NOTIFICATION_DIR = RUNTIME_DIR / "notifications"
NOTIFICATION_FILE = NOTIFICATION_DIR / "budget-guard-events.jsonl"


@dataclass
class BudgetConfig:
    """Configurable budget thresholds.

    Attributes:
        daily_limit: Maximum spend allowed per UTC day in USD.
        warning_threshold: Fraction (0.0–1.0) of daily_limit at which a
            warning notification fires.
        block_on_exceed: If True, requests are blocked when limit is hit.
            If False, only warnings are issued.
        free_cost_threshold: Calls with estimated_cost <= this value are
            treated as free and always pass through.
    """

    daily_limit: float = 5.00
    warning_threshold: float = 0.80
    block_on_exceed: bool = True
    free_cost_threshold: float = 0.0

    @classmethod
    def load(cls) -> "BudgetConfig":
        """Load config from runtime config file, falling back to defaults."""
        raw = load_optional_json(CONFIG_FILE, {})
        kwargs = {}
        for fld in cls.__dataclass_fields__:
            if fld in raw:
                kwargs[fld] = raw[fld]
        return cls(**kwargs)

    def save(self) -> None:
        """Persist current config to disk."""
        save_json(CONFIG_FILE, asdict(self))


# ---------------------------------------------------------------------------
# Budget state management
# ---------------------------------------------------------------------------

def _utc_date_key() -> str:
    """Return today's UTC date as YYYY-MM-DD string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_state() -> dict:
    """Load daily spend state, resetting if the date has rolled over."""
    state = load_optional_json(STATE_FILE, {})
    today = _utc_date_key()
    if state.get("date") != today:
        state = {"date": today, "total_spend": 0.0, "call_count": 0, "warned": False}
        save_json(STATE_FILE, state)
    return state


def _save_state(state: dict) -> None:
    save_json(STATE_FILE, state)


# ---------------------------------------------------------------------------
# Notification system (generic, provider-agnostic)
# ---------------------------------------------------------------------------

def _fire_notification(event_type: str, payload: dict) -> None:
    """Append a notification event for downstream consumers to process.

    Events are written to a JSONL file. External integrations (email, Slack,
    webhooks, etc.) can watch/poll this file or be triggered by a cron job.
    """
    try:
        NOTIFICATION_DIR.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "source": HOOK_NAME,
            **payload,
        }
        with NOTIFICATION_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def check_budget(model_id: str, estimated_cost: float) -> Tuple[bool, str]:
    """Evaluate whether a request is allowed under the current budget.

    Uses optimistic accounting: when a request is approved, the estimated cost
    is immediately added to the daily total. This ensures the budget depletes
    as requests are approved, not only after they complete. The separate
    record_spend() function can later reconcile estimates with actual costs.

    Args:
        model_id: Identifier of the model being called.
        estimated_cost: Estimated USD cost for this request.

    Returns:
        Tuple of (allowed: bool, reason: str).
        - allowed=True means the request may proceed.
        - reason provides human-readable context.
    """
    config = BudgetConfig.load()

    # Free/local models always pass
    if estimated_cost <= config.free_cost_threshold:
        return True, "free/local model — no budget impact"

    state = _load_state()
    projected = state["total_spend"] + estimated_cost

    # Warning threshold (fire once per day)
    warning_amount = config.daily_limit * config.warning_threshold
    if projected >= warning_amount and not state.get("warned"):
        state["warned"] = True
        _save_state(state)
        _fire_notification("budget_warning", {
            "message": f"Budget warning: projected spend ${projected:.4f} "
                       f"exceeds {config.warning_threshold:.0%} of "
                       f"${config.daily_limit:.2f} daily limit",
            "current_spend": state["total_spend"],
            "estimated_cost": estimated_cost,
            "daily_limit": config.daily_limit,
            "model_id": model_id,
        })
        audit_log_entry(HOOK_NAME, "WARNING",
                        f"Budget warning fired: ${projected:.4f} / ${config.daily_limit:.2f}")

    # Block if over limit
    if projected > config.daily_limit and config.block_on_exceed:
        reason = (
            f"Daily budget exceeded: current spend ${state['total_spend']:.4f} + "
            f"estimated ${estimated_cost:.4f} = ${projected:.4f} > "
            f"limit ${config.daily_limit:.2f}"
        )
        _fire_notification("budget_blocked", {
            "message": reason,
            "current_spend": state["total_spend"],
            "estimated_cost": estimated_cost,
            "daily_limit": config.daily_limit,
            "model_id": model_id,
        })
        audit_log_entry(HOOK_NAME, "BLOCK", reason)
        return False, reason

    # Approved — optimistic accounting: debit estimated cost immediately so
    # subsequent requests within the same budget window see the depletion.
    state["total_spend"] = projected
    state["call_count"] = state.get("call_count", 0) + 1
    _save_state(state)

    audit_log_entry(HOOK_NAME, "APPROVE",
                    f"Approved ${estimated_cost:.4f} for {model_id} — "
                    f"daily total: ${projected:.4f} / ${config.daily_limit:.2f}")

    return True, f"within budget: ${projected:.4f} / ${config.daily_limit:.2f}"


def record_spend(model_id: str, cost: float, task_class: str = "unknown",
                  estimated_cost: float | None = None) -> None:
    """Record actual spend after a call completes (post-execution reconciliation).

    Because check_budget() already debited the estimated cost optimistically,
    this function adjusts the daily total by the delta between actual and
    estimated cost. If estimated_cost is None (e.g. called externally without
    a prior check_budget), the full cost is added.

    Args:
        model_id: Identifier of the model that was called.
        cost: Actual USD cost incurred.
        task_class: Category of the task (e.g. "code-gen", "chat", "embedding").
        estimated_cost: The estimate that was already debited by check_budget().
            Pass None if no prior optimistic debit was made.
    """
    state = _load_state()

    if estimated_cost is not None:
        # Reconcile: replace the estimate with actual cost
        delta = cost - estimated_cost
        state["total_spend"] = state.get("total_spend", 0.0) + delta
    else:
        # No prior estimate — add full cost (legacy / external callers)
        state["total_spend"] = state.get("total_spend", 0.0) + cost
        state["call_count"] = state.get("call_count", 0) + 1

    _save_state(state)

    # Append to cost log for historical tracking
    try:
        COST_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "date": _utc_date_key(),
            "model_id": model_id,
            "cost": cost,
            "task_class": task_class,
            "daily_total": state["total_spend"],
        }
        with COST_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

    audit_log_entry(HOOK_NAME, "SPEND",
                    f"Recorded ${cost:.4f} for {model_id} ({task_class}) — "
                    f"daily total: ${state['total_spend']:.4f}")


def refund_estimate(amount: float) -> None:
    """Refund a previously debited estimate (e.g. on abort or error).

    Subtracts the amount from the daily total spend, clamped to zero so we
    never go negative. Used by post_main() when a tool invocation was aborted
    or errored before incurring real cost.

    Args:
        amount: The estimated cost that was optimistically debited and should
            now be returned to the budget.
    """
    state = _load_state()
    previous = state.get("total_spend", 0.0)
    state["total_spend"] = max(0.0, previous - amount)
    _save_state(state)

    audit_log_entry(HOOK_NAME, "REFUND",
                    f"Refunded ${amount:.4f} — daily total: "
                    f"${state['total_spend']:.4f} (was ${previous:.4f})")


# ---------------------------------------------------------------------------
# Hook entry point (Claude Code hook protocol)
# ---------------------------------------------------------------------------

def main() -> int:
    """Process a tool invocation via stdin (Claude Code hook protocol).

    Reads JSON from stdin with tool_name and tool_input. For API-calling tools,
    evaluates budget and blocks if the daily limit is exceeded.
    """
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({}))
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Extract cost metadata if provided by the routing layer
    meta = tool_input.get("_budget_meta", {})
    model_id = meta.get("model_id", "unknown")
    estimated_cost = float(meta.get("estimated_cost", 0.0))

    # If no cost metadata, pass through (other hooks or the routing layer
    # are responsible for injecting budget metadata)
    if not meta:
        print(json.dumps({}))
        return 0

    allowed, reason = check_budget(model_id, estimated_cost)

    if not allowed:
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0

    # Allowed — pass through
    print(json.dumps({}))
    return 0


# ---------------------------------------------------------------------------
# Post-tool-use entry point
# ---------------------------------------------------------------------------

def post_main() -> int:
    """Process post-tool-use reconciliation via stdin (Claude Code hook protocol).

    Reads JSON from stdin with tool result/output. If actual cost is reported,
    reconciles with the estimate. If the tool was aborted/errored, refunds the
    optimistic debit.
    """
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({}))
        return 0

    # Look for budget metadata in the tool result
    tool_output = input_data.get("tool_output", input_data.get("tool_result", {}))
    if isinstance(tool_output, str):
        try:
            tool_output = json.loads(tool_output)
        except (json.JSONDecodeError, TypeError):
            tool_output = {}

    meta = tool_output.get("_budget_meta", {})

    # Also check top-level _budget_meta (some hook protocols put it there)
    if not meta:
        meta = input_data.get("_budget_meta", {})

    if not meta:
        # No budget metadata in post-exec payload — nothing to reconcile
        print(json.dumps({}))
        return 0

    model_id = meta.get("model_id", "unknown")
    estimated_cost = float(meta.get("estimated_cost", 0.0))
    actual_cost = meta.get("actual_cost")
    aborted = meta.get("aborted", False)

    if aborted:
        # Tool was aborted or errored — refund the full estimate
        refund_estimate(estimated_cost)
        audit_log_entry(HOOK_NAME, "POST_RECONCILE",
                        f"Aborted/errored call for {model_id} — "
                        f"refunded estimate ${estimated_cost:.4f}")
    elif actual_cost is not None:
        # Reconcile estimate with actual cost
        actual_cost = float(actual_cost)
        task_class = meta.get("task_class", "unknown")
        record_spend(model_id, actual_cost, task_class, estimated_cost=estimated_cost)
        audit_log_entry(HOOK_NAME, "POST_RECONCILE",
                        f"Reconciled {model_id}: estimated ${estimated_cost:.4f} → "
                        f"actual ${actual_cost:.4f} (delta: ${actual_cost - estimated_cost:+.4f})")

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    if "--post" in sys.argv:
        raise SystemExit(post_main())
    raise SystemExit(main())
