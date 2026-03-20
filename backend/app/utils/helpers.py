"""
Utility helpers: reward computation, state normalization, action mapping, stats.
"""
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

ACTION_MAP = {0: "call_api", 1: "retry", 2: "skip", 3: "switch_provider"}
LABEL_MAP = {v: k for k, v in ACTION_MAP.items()}


class SimulationError(Exception):
    """Raised when the API simulator encounters a catastrophic failure."""


class ModelNotLoadedError(Exception):
    """Raised when the RL model has not been loaded yet."""


class InvalidAPIError(Exception):
    """Raised when an unknown API name is requested."""


def compute_reward(result: dict, action: int) -> float:
    """
    Compute reward from a simulation result and the action taken.
    reward = +100 if success else -50
    reward -= latency * 0.10
    reward -= cost * 5.0
    retry penalty: -10, skip penalty: -5
    """
    success: bool = result.get("success", False)
    latency: float = result.get("latency", 0.0)
    cost: float = result.get("cost", 0.0)

    reward = 100.0 if success else -50.0
    reward -= latency * 0.10
    reward -= cost * 5.0

    if action == 1:   # retry
        reward -= 10.0
    elif action == 2:  # skip
        reward -= 5.0

    logger.debug("compute_reward: success=%s latency=%.2f cost=%.2f action=%d → %.4f",
                 success, latency, cost, action, reward)
    return reward


def normalize_state(state: dict) -> np.ndarray:
    """Normalize a raw state dict into a float32 array of shape (5,)."""
    latency_norm = float(state.get("latency", 0.0)) / 1000.0
    cost_norm = float(state.get("cost", 0.0)) / 20.0
    success_rate = float(state.get("success_rate", 1.0))
    system_load = float(state.get("system_load", 1.0)) / 3.0
    previous_action = float(state.get("previous_action", 0)) / 3.0

    arr = np.array(
        [latency_norm, cost_norm, success_rate, system_load, previous_action],
        dtype=np.float32,
    )
    return np.clip(arr, 0.0, 1.0)


def action_to_label(action: int) -> str:
    label = ACTION_MAP.get(action)
    if label is None:
        raise InvalidAPIError(f"Unknown action integer: {action}")
    return label


def label_to_action(label: str) -> int:
    action = LABEL_MAP.get(label)
    if action is None:
        raise InvalidAPIError(f"Unknown action label: {label}")
    return action


def calculate_stats(logs: list) -> dict[str, Any]:
    """Compute aggregate statistics from a list of API log dicts or ORM objects."""
    if not logs:
        return {"total": 0, "success_rate": 0.0, "avg_latency": 0.0, "avg_cost": 0.0, "per_api": {}}

    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    total = len(logs)
    successes = sum(1 for log in logs if _get(log, "success", False))
    latencies = [_get(log, "latency", 0.0) for log in logs]
    costs = [_get(log, "cost", 0.0) for log in logs]

    per_api: dict[str, dict] = {}
    for log in logs:
        name = _get(log, "api_name", "unknown")
        if name not in per_api:
            per_api[name] = {"total": 0, "successes": 0, "latencies": [], "costs": []}
        per_api[name]["total"] += 1
        if _get(log, "success", False):
            per_api[name]["successes"] += 1
        per_api[name]["latencies"].append(_get(log, "latency", 0.0))
        per_api[name]["costs"].append(_get(log, "cost", 0.0))

    per_api_stats = {
        name: {
            "total": d["total"],
            "success_rate": d["successes"] / d["total"] if d["total"] else 0.0,
            "avg_latency": float(np.mean(d["latencies"])) if d["latencies"] else 0.0,
            "avg_cost": float(np.mean(d["costs"])) if d["costs"] else 0.0,
        }
        for name, d in per_api.items()
    }

    return {
        "total": total,
        "success_rate": successes / total,
        "avg_latency": float(np.mean(latencies)),
        "avg_cost": float(np.mean(costs)),
        "per_api": per_api_stats,
    }
