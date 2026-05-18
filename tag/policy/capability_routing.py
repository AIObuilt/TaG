"""Capability-weighted model routing policy.

Provides a generic algorithm for ranking models by weighted scores based on
task class. Deployments supply their own model registry (a JSON file); this
module defines the scoring algorithm and schema only.

JSON Registry Schema
--------------------
The registry file is a JSON array of objects, each with:

    {
        "model_id": "string — unique identifier for the model",
        "capability_rating": "float 0-5 — reasoning/quality depth",
        "speed_rating": "float 0-5 — latency/throughput",
        "cost_per_1m_tokens": "float — cost in USD per 1M tokens",
        "provider": "string — provider identifier (e.g. 'openai', 'anthropic')"
    }

Example::

    [
        {
            "model_id": "provider-a/large-v2",
            "capability_rating": 4.8,
            "speed_rating": 2.1,
            "cost_per_1m_tokens": 15.0,
            "provider": "provider-a"
        },
        {
            "model_id": "provider-b/fast-v1",
            "capability_rating": 3.0,
            "speed_rating": 4.9,
            "cost_per_1m_tokens": 0.5,
            "provider": "provider-b"
        }
    ]

Task Categories
---------------
Each task class maps to a category that determines the weighting between
capability and speed:

- SPEED_WEIGHTED: latency-sensitive tasks (default 70% speed, 30% capability)
- CAPABILITY_WEIGHTED: reasoning-heavy tasks (default 80% capability, 20% speed)
- BALANCED: tasks needing both (default 50% capability, 50% speed)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ModelCapability:
    """A single model's capability profile."""

    model_id: str
    capability_rating: float  # 0-5 scale
    speed_rating: float  # 0-5 scale
    cost_per_1m_tokens: float  # USD
    provider: str


# ---------------------------------------------------------------------------
# Task categories and default weights
# ---------------------------------------------------------------------------

SPEED_WEIGHTED = "SPEED_WEIGHTED"
CAPABILITY_WEIGHTED = "CAPABILITY_WEIGHTED"
BALANCED = "BALANCED"

# Weights are (capability_weight, speed_weight) — must sum to 1.0
DEFAULT_WEIGHTS: dict[str, tuple[float, float]] = {
    SPEED_WEIGHTED: (0.30, 0.70),
    CAPABILITY_WEIGHTED: (0.80, 0.20),
    BALANCED: (0.50, 0.50),
}

# Maps common task class names to one of the three categories.
# Deployments can extend or override this mapping.
DEFAULT_TASK_CATEGORIES: dict[str, str] = {
    # Speed-weighted tasks
    "LOOKUP": SPEED_WEIGHTED,
    "FORMAT": SPEED_WEIGHTED,
    "SEARCH": SPEED_WEIGHTED,
    "CLASSIFY": SPEED_WEIGHTED,
    "ROUTE": SPEED_WEIGHTED,
    # Capability-weighted tasks
    "REASON": CAPABILITY_WEIGHTED,
    "EMERGENCY": CAPABILITY_WEIGHTED,
    "ANALYZE": CAPABILITY_WEIGHTED,
    "PLAN": CAPABILITY_WEIGHTED,
    "DEBUG": CAPABILITY_WEIGHTED,
    # Balanced tasks
    "BUILD": BALANCED,
    "DRAFT": BALANCED,
    "REVIEW": BALANCED,
    "REFACTOR": BALANCED,
    "TEST": BALANCED,
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _resolve_weights(
    task_class: str,
    weights: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float]:
    """Resolve (capability_weight, speed_weight) for a task class.

    Parameters
    ----------
    task_class:
        A task class name (e.g. "REASON") or a category name directly
        (e.g. "CAPABILITY_WEIGHTED").
    weights:
        Optional override mapping of category -> (cap_w, speed_w).
        Falls back to DEFAULT_WEIGHTS for any missing category.
    """
    effective_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    # If task_class is itself a category key, use directly
    if task_class in effective_weights:
        return effective_weights[task_class]

    # Otherwise look up via DEFAULT_TASK_CATEGORIES
    category = DEFAULT_TASK_CATEGORIES.get(task_class.upper(), BALANCED)
    return effective_weights.get(category, DEFAULT_WEIGHTS[BALANCED])


def score_model(
    model: ModelCapability,
    task_class: str,
    weights: dict[str, tuple[float, float]] | None = None,
) -> float:
    """Compute a weighted score for a model given a task class.

    Parameters
    ----------
    model:
        The model's capability profile.
    task_class:
        The class of the current task (e.g. "REASON", "LOOKUP", "BUILD").
    weights:
        Optional override mapping of category -> (capability_weight, speed_weight).

    Returns
    -------
    float:
        Weighted score on a 0-5 scale.
    """
    cap_w, speed_w = _resolve_weights(task_class, weights)
    return (model.capability_rating * cap_w) + (model.speed_rating * speed_w)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def rank_models(
    models: list[ModelCapability],
    task_class: str,
    weights: dict[str, tuple[float, float]] | None = None,
) -> list[ModelCapability]:
    """Rank models by weighted score for the given task class.

    Returns a new list sorted descending by score (best first).
    Ties are broken by lower cost, then alphabetical model_id.

    Parameters
    ----------
    models:
        List of model capability profiles.
    task_class:
        The class of the current task.
    weights:
        Optional override mapping of category -> (capability_weight, speed_weight).

    Returns
    -------
    list[ModelCapability]:
        Models sorted best-first for the given task.
    """
    def sort_key(m: ModelCapability) -> tuple[float, float, str]:
        s = score_model(m, task_class, weights)
        # Negate score for descending; use cost ascending as tiebreaker
        return (-s, m.cost_per_1m_tokens, m.model_id)

    return sorted(models, key=sort_key)


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------


def _validate_entry(entry: dict[str, Any], index: int) -> ModelCapability:
    """Validate and convert a raw dict to ModelCapability."""
    required_fields = ("model_id", "capability_rating", "speed_rating", "cost_per_1m_tokens", "provider")
    missing = [f for f in required_fields if f not in entry]
    if missing:
        msg = f"Registry entry {index}: missing fields {missing}"
        raise ValueError(msg)

    cap = float(entry["capability_rating"])
    speed = float(entry["speed_rating"])
    if not (0.0 <= cap <= 5.0):
        msg = f"Registry entry {index}: capability_rating {cap} outside 0-5 range"
        raise ValueError(msg)
    if not (0.0 <= speed <= 5.0):
        msg = f"Registry entry {index}: speed_rating {speed} outside 0-5 range"
        raise ValueError(msg)

    return ModelCapability(
        model_id=str(entry["model_id"]),
        capability_rating=cap,
        speed_rating=speed,
        cost_per_1m_tokens=float(entry["cost_per_1m_tokens"]),
        provider=str(entry["provider"]),
    )


def load_registry(path: Path) -> list[ModelCapability]:
    """Load a model registry from a JSON file.

    Parameters
    ----------
    path:
        Path to a JSON file containing an array of model entries.

    Returns
    -------
    list[ModelCapability]:
        Validated list of model capability profiles.

    Raises
    ------
    FileNotFoundError:
        If the registry file does not exist.
    ValueError:
        If any entry is malformed or has out-of-range values.
    json.JSONDecodeError:
        If the file is not valid JSON.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"Registry at {path} must be a JSON array"
        raise ValueError(msg)

    return [_validate_entry(entry, i) for i, entry in enumerate(data)]
