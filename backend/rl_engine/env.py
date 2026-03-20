"""
APIRoutingEnv — standalone RL environment. No imports from app/.
Run from backend/ directory: python -m rl_engine.train

Observation space (6-dim float32, all in [0, 1]):
    [0] current_latency  [1] current_cost  [2] success_rate
    [3] request_load     [4] time_of_day   [5] error_rate

Action space: Discrete(4)
    0 — Provider A (Fast, Expensive):  latency [0.05,0.25], cost [0.6,0.9],  success 0.95
    1 — Provider B (Balanced):         latency [0.20,0.50], cost [0.3,0.6],  success 0.90
    2 — Provider C (Cheap, Slow):      latency [0.40,0.80], cost [0.05,0.3], success 0.85
    3 — Fallback/Cache:                latency [0.01,0.05], cost [0.0,0.05], success 0.70

Reward: 0.3*(1-latency) + 0.3*(1-cost) + 0.4*success - 1.0*(1-success)
Episode: max 200 steps, truncated=True at limit.
"""
import logging
import math
from collections import deque
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

logger = logging.getLogger(__name__)

PROVIDER_PROFILES = {
    0: {"latency": (0.05, 0.25), "cost": (0.6, 0.9),  "success": 0.95, "name": "Provider_A"},
    1: {"latency": (0.20, 0.50), "cost": (0.3, 0.6),  "success": 0.90, "name": "Provider_B"},
    2: {"latency": (0.40, 0.80), "cost": (0.05, 0.3), "success": 0.85, "name": "Provider_C"},
    3: {"latency": (0.01, 0.05), "cost": (0.0, 0.05), "success": 0.70, "name": "Fallback"},
}

MAX_STEPS = 200
SUCCESS_WINDOW = 10


class APIRoutingEnv(gym.Env):
    """Standalone RL environment for API provider routing."""

    metadata = {"render_modes": []}

    def __init__(self, render_mode: str | None = None):
        super().__init__()
        self.render_mode = render_mode
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(6,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

        self._step_count = 0
        self._success_history: deque[float] = deque(maxlen=SUCCESS_WINDOW)
        self._error_history: deque[float] = deque(maxlen=SUCCESS_WINDOW)
        self._episode_rewards: list[float] = []
        self._current_obs = np.zeros(6, dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._step_count = 0
        self._success_history.clear()
        self._error_history.clear()
        self._episode_rewards.clear()
        for _ in range(SUCCESS_WINDOW):
            self._success_history.append(1.0)
            self._error_history.append(0.0)
        self._current_obs = self._build_obs(0.3, 0.4, True)
        return self._current_obs.copy(), {"step": 0}

    def step(self, action: int):
        self._step_count += 1
        profile = PROVIDER_PROFILES[int(action)]

        lat_min, lat_max = profile["latency"]
        cost_min, cost_max = profile["cost"]

        latency = float(self.np_random.uniform(lat_min, lat_max))
        cost = float(self.np_random.uniform(cost_min, cost_max))
        success = float(self.np_random.random()) < profile["success"]

        reward = self._calculate_reward(latency, cost, success)
        self._episode_rewards.append(reward)
        self._success_history.append(1.0 if success else 0.0)
        self._error_history.append(0.0 if success else 1.0)
        self._current_obs = self._build_obs(latency, cost, success)

        terminated = False
        truncated = self._step_count >= MAX_STEPS

        info = {
            "step": self._step_count,
            "latency": latency,
            "cost": cost,
            "success": success,
            "provider": profile["name"],
            "reward": reward,
        }
        return self._current_obs.copy(), reward, terminated, truncated, info

    def _calculate_reward(self, latency: float, cost: float, success: bool) -> float:
        return (
            0.3 * (1.0 - latency)
            + 0.3 * (1.0 - cost)
            + 0.4 * float(success)
            - 1.0 * float(not success)
        )

    def _build_obs(self, latency: float, cost: float, success: bool) -> np.ndarray:
        success_rate = float(np.mean(self._success_history)) if self._success_history else 1.0
        error_rate = float(np.mean(self._error_history)) if self._error_history else 0.0
        time_of_day = (math.sin(self._step_count * 0.1) + 1.0) / 2.0
        request_load = float(np.clip(self.np_random.uniform(0.2, 0.9), 0.0, 1.0))
        obs = np.array(
            [latency, cost, success_rate, request_load, time_of_day, error_rate],
            dtype=np.float32,
        )
        return np.clip(obs, 0.0, 1.0)

    def get_episode_summary(self) -> dict[str, float]:
        if not self._episode_rewards:
            return {"total_reward": 0.0, "mean_reward": 0.0, "steps": 0}
        return {
            "total_reward": float(sum(self._episode_rewards)),
            "mean_reward": float(np.mean(self._episode_rewards)),
            "steps": self._step_count,
        }

    def render(self) -> None:
        pass

    def close(self) -> None:
        pass
