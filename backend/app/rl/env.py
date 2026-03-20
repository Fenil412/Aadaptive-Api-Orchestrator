"""
MicroserviceOrchestrationEnv — RL environment integrated with the FastAPI app layer.
Registered as 'MicroserviceOrchestrator-v0'.
"""
import logging
from collections import deque
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

logger = logging.getLogger(__name__)

try:
    from gymnasium.envs.registration import register
    register(
        id="MicroserviceOrchestrator-v0",
        entry_point="app.rl.env:MicroserviceOrchestrationEnv",
    )
except Exception:
    pass


class MicroserviceOrchestrationEnv(gym.Env):
    """
    Gymnasium environment for microservice API orchestration.

    Observation space (5-dim float32, all in [0, 1]):
        [0] latency_norm     [1] cost_norm
        [2] success_rate     [3] system_load / 3
        [4] previous_action / 3

    Action space: Discrete(4) — call_api(0), retry(1), skip(2), switch_provider(3)
    Episode terminates after 50 steps or 3 consecutive failures.
    """

    metadata = {"render_modes": []}
    MAX_STEPS = 50
    MAX_CONSECUTIVE_FAILURES = 3
    SUCCESS_WINDOW = 10
    ACTION_LABELS = {0: "call_api", 1: "retry", 2: "skip", 3: "switch_provider"}

    def __init__(self, api_name: str = "payment_A", render_mode: str | None = None):
        super().__init__()
        self.api_name = api_name
        self.render_mode = render_mode

        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(5,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

        self._step_count = 0
        self._consecutive_failures = 0
        self._previous_action = 0
        self._success_history: deque[float] = deque(maxlen=self.SUCCESS_WINDOW)
        self._current_obs = np.zeros(5, dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._step_count = 0
        self._consecutive_failures = 0
        self._previous_action = 0
        self._success_history.clear()
        for _ in range(self.SUCCESS_WINDOW):
            self._success_history.append(1.0)
        self._current_obs = self._make_obs(0.3, 0.3, 1.0)
        return self._current_obs.copy(), {"step": 0, "api_name": self.api_name}

    def step(self, action: int):
        from app.services.api_simulator import simulate_api
        from app.utils.helpers import SimulationError

        self._step_count += 1
        retry = action == 1

        try:
            result = simulate_api(self.api_name, retry=retry)
            success = result["success"]
            latency = result["latency"]
            cost = result["cost"]
            system_load = result["system_load"]
        except SimulationError as exc:
            logger.warning("SimulationError in env step: %s", exc)
            success, latency, cost, system_load = False, 500.0, 5.0, 1.5

        self._success_history.append(1.0 if success else 0.0)
        self._consecutive_failures = 0 if success else self._consecutive_failures + 1

        reward = self._compute_reward(latency, cost, success, action)
        self._previous_action = action
        self._current_obs = self._make_obs(
            min(latency / 1000.0, 1.0), min(cost / 20.0, 1.0), system_load
        )

        terminated = self._consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES
        truncated = self._step_count >= self.MAX_STEPS

        info = {
            "step": self._step_count,
            "success": success,
            "latency": latency,
            "cost": cost,
            "system_load": system_load,
            "action_label": self.ACTION_LABELS.get(action, "unknown"),
        }
        return self._current_obs.copy(), reward, terminated, truncated, info

    def _make_obs(self, latency_norm: float, cost_norm: float, system_load: float) -> np.ndarray:
        success_rate = float(np.mean(self._success_history)) if self._success_history else 1.0
        obs = np.array([
            latency_norm, cost_norm, success_rate,
            min(system_load / 3.0, 1.0), self._previous_action / 3.0,
        ], dtype=np.float32)
        return np.clip(obs, 0.0, 1.0)

    def _compute_reward(self, latency: float, cost: float, success: bool, action: int) -> float:
        reward = 100.0 if success else -50.0
        reward -= latency * 0.10
        reward -= cost * 5.0
        if action == 1:
            reward -= 10.0
        elif action == 2:
            reward -= 5.0
        return reward

    def render(self) -> None:
        pass

    def close(self) -> None:
        pass
