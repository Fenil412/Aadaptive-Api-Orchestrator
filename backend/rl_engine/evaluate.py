"""
Evaluate a trained PPO model against static baseline strategies.
Run from backend/ directory:
    python -m rl_engine.evaluate --model models/ppo_api_orchestrator.zip
"""
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from rl_engine.env import APIRoutingEnv

logger = logging.getLogger(__name__)

STRATEGIES = ["ppo", "random", "always_a", "always_b", "always_c", "round_robin"]
ACTION_LABELS = {0: "call_api", 1: "retry", 2: "skip", 3: "switch_provider"}


def _run_strategy(strategy: str, n_episodes: int, model=None) -> dict[str, Any]:
    env = APIRoutingEnv()
    rewards, latencies, costs, successes = [], [], [], []
    action_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    rr_counter = 0

    for _ in range(n_episodes):
        obs, _ = env.reset()
        ep_reward = 0.0
        done = False

        while not done:
            if strategy == "ppo" and model is not None:
                action, _ = model.predict(obs.reshape(1, -1), deterministic=True)
                action = int(action)
            elif strategy == "random":
                action = env.action_space.sample()
            elif strategy == "always_a":
                action = 0
            elif strategy == "always_b":
                action = 1
            elif strategy == "always_c":
                action = 2
            elif strategy == "round_robin":
                action = rr_counter % 4
                rr_counter += 1
            else:
                action = 0

            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            latencies.append(info.get("latency", 0.0))
            costs.append(info.get("cost", 0.0))
            successes.append(1.0 if info.get("success", False) else 0.0)
            action_counts[action] = action_counts.get(action, 0) + 1
            done = terminated or truncated

        rewards.append(ep_reward)

    env.close()
    total_actions = sum(action_counts.values()) or 1

    return {
        "strategy": strategy,
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "success_rate": float(np.mean(successes)),
        "avg_latency": float(np.mean(latencies)),
        "avg_cost": float(np.mean(costs)),
        "action_distribution": {
            ACTION_LABELS[k]: round(v / total_actions * 100, 2)
            for k, v in action_counts.items()
        },
    }


def evaluate_model(
    model_path: str,
    n_episodes: int = 20,
    save_dir: str | None = None,
) -> dict[str, Any]:
    """Load a PPO model and compare it against 5 static strategies."""
    from stable_baselines3 import PPO

    model = None
    try:
        model = PPO.load(model_path)
        logger.info("Loaded model from %s", model_path)
    except Exception as exc:
        logger.warning("Could not load model: %s — PPO strategy will use random fallback.", exc)

    results = {}
    for strategy in STRATEGIES:
        logger.info("Evaluating strategy: %s (%d episodes)", strategy, n_episodes)
        results[strategy] = _run_strategy(
            strategy=strategy,
            n_episodes=n_episodes,
            model=model if strategy == "ppo" else None,
        )

    ppo_stats = results.get("ppo", {})
    output = {
        "mean_reward": ppo_stats.get("mean_reward", 0.0),
        "std_reward": ppo_stats.get("std_reward", 0.0),
        "success_rate": ppo_stats.get("success_rate", 0.0),
        "avg_latency": ppo_stats.get("avg_latency", 0.0),
        "avg_cost": ppo_stats.get("avg_cost", 0.0),
        "action_distribution": ppo_stats.get("action_distribution", {}),
        "strategy_comparison": results,
    }

    if save_dir:
        out_path = Path(save_dir) / "evaluation_results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)
        logger.info("Evaluation results saved to %s", out_path)

    return output


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/ppo_api_orchestrator.zip")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--save-dir", default="models")
    args = parser.parse_args()

    results = evaluate_model(args.model, n_episodes=args.episodes, save_dir=args.save_dir)
    print(f"\nPPO Agent Results:")
    print(f"  Mean reward  : {results['mean_reward']:.4f}")
    print(f"  Success rate : {results['success_rate']:.2%}")
    print(f"  Avg latency  : {results['avg_latency']:.4f}")
    print(f"  Avg cost     : {results['avg_cost']:.4f}")
