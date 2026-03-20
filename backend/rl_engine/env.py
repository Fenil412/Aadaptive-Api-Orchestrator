"""
Custom Gymnasium Environment for Adaptive API Orchestration.

State Space (6 dimensions):
    [0] current_latency  - Normalized API latency         (0.0 - 1.0)
    [1] current_cost     - Normalized API cost             (0.0 - 1.0)
    [2] success_rate     - Recent success ratio            (0.0 - 1.0)
    [3] request_load     - Current request volume          (0.0 - 1.0)
    [4] time_of_day      - Normalized hour of day          (0.0 - 1.0)
    [5] error_rate       - Recent error ratio              (0.0 - 1.0)

Action Space (4 discrete):
    0 - Route to Provider A (Fast, Expensive)
    1 - Route to Provider B (Balanced)
    2 - Route to Provider C (Slow, Cheap)
    3 - Use Fallback / Cache
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np


# ── API Provider Profiles ──
# Each provider has characteristic latency, cost, and reliability ranges
PROVIDER_PROFILES = {
    0: {  # Provider A — Fast but Expensive
        "name": "Provider A (Fast)",
        "latency_range": (0.05, 0.25),
        "cost_range": (0.6, 0.9),
        "base_success_rate": 0.95,
    },
    1: {  # Provider B — Balanced
        "name": "Provider B (Balanced)",
        "latency_range": (0.2, 0.5),
        "cost_range": (0.3, 0.6),
        "base_success_rate": 0.90,
    },
    2: {  # Provider C — Slow but Cheap
        "name": "Provider C (Cheap)",
        "latency_range": (0.4, 0.8),
        "cost_range": (0.05, 0.3),
        "base_success_rate": 0.85,
    },
    3: {  # Fallback / Cache — Instant, Free, but stale
        "name": "Fallback/Cache",
        "latency_range": (0.01, 0.05),
        "cost_range": (0.0, 0.05),
        "base_success_rate": 0.70,  # cached data may be stale
    },
}


class APIRoutingEnv(gym.Env):
    """
    Reinforcement Learning environment that simulates an API gateway.
    The agent learns to route requests to the optimal provider based on
    current system conditions (latency, cost, load, time, errors).
    """

    metadata = {"render_modes": ["human"], "render_fps": 4}

    def __init__(self, render_mode=None, max_steps=200):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps

        # ── Spaces ──
        # State: 6 continuous features, each normalized to [0, 1]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(6,), dtype=np.float32
        )
        # Action: 4 discrete provider choices
        self.action_space = spaces.Discrete(4)

        # ── Reward Weights ──
        self.w_latency = 0.3
        self.w_cost = 0.3
        self.w_success = 0.4
        self.failure_penalty = 1.0

        # ── Internal State ──
        self.current_step = 0
        self.state = None
        self.history = []  # track episode history for analysis

        # ── Rolling metrics (simulated) ──
        self._recent_successes = []
        self._recent_errors = []

    def _generate_system_conditions(self):
        """Generate realistic system conditions with temporal patterns."""
        # Simulate time-of-day patterns (higher load during business hours)
        hour = np.random.uniform(0, 24)
        time_normalized = hour / 24.0

        # Load follows a pattern: high during day, low at night
        base_load = 0.3 + 0.5 * np.sin(np.pi * time_normalized)
        request_load = np.clip(base_load + np.random.normal(0, 0.1), 0, 1)

        # Latency and errors correlate with load
        current_latency = np.clip(
            0.1 + 0.6 * request_load + np.random.normal(0, 0.1), 0, 1
        )
        error_rate = np.clip(
            0.05 + 0.3 * request_load + np.random.normal(0, 0.05), 0, 1
        )

        # Success rate inversely related to error rate
        success_rate = np.clip(1.0 - error_rate + np.random.normal(0, 0.05), 0, 1)

        # Cost fluctuates with demand
        current_cost = np.clip(
            0.2 + 0.5 * request_load + np.random.normal(0, 0.1), 0, 1
        )

        return np.array(
            [
                current_latency,
                current_cost,
                success_rate,
                request_load,
                time_normalized,
                error_rate,
            ],
            dtype=np.float32,
        )

    def _simulate_provider_response(self, action, state):
        """
        Simulate the outcome of routing a request to the chosen provider,
        given current system conditions.
        """
        action = int(action)  # Ensure plain int (model.predict returns numpy)
        profile = PROVIDER_PROFILES[action]
        request_load = float(state[3])  # current load affects all providers

        # ── Latency: base range + load impact ──
        lat_low, lat_high = profile["latency_range"]
        load_impact = request_load * 0.2  # high load increases latency
        latency = np.clip(
            np.random.uniform(lat_low, lat_high) + load_impact, 0, 1
        )

        # ── Cost: base range + demand surge pricing ──
        cost_low, cost_high = profile["cost_range"]
        demand_surge = request_load * 0.1
        cost = np.clip(
            np.random.uniform(cost_low, cost_high) + demand_surge, 0, 1
        )

        # ── Success: base rate degraded by load ──
        load_degradation = request_load * 0.15
        success_prob = np.clip(
            profile["base_success_rate"] - load_degradation, 0.1, 1.0
        )
        success = np.random.random() < success_prob

        return latency, cost, success

    def _calculate_reward(self, latency, cost, success):
        """
        Reward = w1*(1-latency) + w2*(1-cost) + w3*success - penalty*failure

        Higher reward for: low latency, low cost, successful requests.
        Harsh penalty for failures.
        """
        if success:
            reward = (
                self.w_latency * (1.0 - latency)
                + self.w_cost * (1.0 - cost)
                + self.w_success * 1.0
            )
        else:
            reward = (
                self.w_latency * (1.0 - latency)
                + self.w_cost * (1.0 - cost)
                - self.failure_penalty
            )
        return reward

    def reset(self, seed=None, options=None):
        """Reset the environment to initial state."""
        super().reset(seed=seed)

        self.current_step = 0
        self.history = []
        self._recent_successes = []
        self._recent_errors = []

        self.state = self._generate_system_conditions()
        info = {"step": self.current_step}

        return self.state, info

    def step(self, action):
        """
        Execute one routing decision.

        Args:
            action: int (0-3) — which provider to route to

        Returns:
            observation, reward, terminated, truncated, info
        """
        action = int(action)  # Ensure plain int (model.predict returns numpy)
        self.current_step += 1

        # Simulate provider response
        latency, cost, success = self._simulate_provider_response(
            action, self.state
        )

        # Calculate reward
        reward = self._calculate_reward(latency, cost, success)

        # Track metrics
        self._recent_successes.append(float(success))
        self._recent_errors.append(float(not success))
        # Keep rolling window of 20
        if len(self._recent_successes) > 20:
            self._recent_successes.pop(0)
            self._recent_errors.pop(0)

        # Record step in history
        step_record = {
            "step": self.current_step,
            "action": action,
            "provider": PROVIDER_PROFILES[action]["name"],
            "latency": float(latency),
            "cost": float(cost),
            "success": bool(success),
            "reward": float(reward),
            "state": self.state.tolist(),
        }
        self.history.append(step_record)

        # Generate next state (new system conditions)
        self.state = self._generate_system_conditions()

        # Episode termination
        terminated = False
        truncated = self.current_step >= self.max_steps

        info = {
            "step": self.current_step,
            "latency": latency,
            "cost": cost,
            "success": success,
            "reward": reward,
            "provider": PROVIDER_PROFILES[action]["name"],
            "avg_success_rate": (
                np.mean(self._recent_successes)
                if self._recent_successes
                else 0.0
            ),
        }

        if self.render_mode == "human":
            self.render()

        return self.state, reward, terminated, truncated, info

    def render(self):
        """Print current step info to console."""
        if self.history:
            last = self.history[-1]
            status = "✅" if last["success"] else "❌"
            print(
                f"Step {last['step']:3d} | "
                f"{last['provider']:22s} | "
                f"Latency: {last['latency']:.3f} | "
                f"Cost: {last['cost']:.3f} | "
                f"{status} | "
                f"Reward: {last['reward']:+.3f}"
            )

    def get_episode_summary(self):
        """Return summary statistics for the episode."""
        if not self.history:
            return {}

        rewards = [h["reward"] for h in self.history]
        latencies = [h["latency"] for h in self.history]
        costs = [h["cost"] for h in self.history]
        successes = [h["success"] for h in self.history]

        return {
            "total_steps": len(self.history),
            "total_reward": sum(rewards),
            "avg_reward": np.mean(rewards),
            "avg_latency": np.mean(latencies),
            "avg_cost": np.mean(costs),
            "success_rate": np.mean(successes),
            "provider_distribution": {
                PROVIDER_PROFILES[i]["name"]: sum(
                    1 for h in self.history if h["action"] == i
                )
                for i in range(4)
            },
        }


# ── Register the environment with Gymnasium ──
gym.register(
    id="APIRouting-v0",
    entry_point="rl_engine.env:APIRoutingEnv",
    max_episode_steps=200,
)
