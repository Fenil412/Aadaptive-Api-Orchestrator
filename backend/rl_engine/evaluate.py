"""
Evaluation script to compare the RL agent against static routing strategies.

Runs multiple episodes with:
  1. Trained PPO Agent
  2. Random Routing (baseline)
  3. Always-Cheapest (Provider C)
  4. Always-Fastest (Provider A)
  5. Round-Robin

Outputs comparison metrics and generates plots.
"""

import os
import sys
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from rl_engine.env import APIRoutingEnv


def evaluate_model(model_path, n_episodes=20, save_dir="./models"):
    """
    Evaluate the trained RL model against static strategies.

    Args:
        model_path: Path to the saved PPO model
        n_episodes: Number of evaluation episodes
        save_dir: Directory to save evaluation results

    Returns:
        Dictionary with comparison results
    """
    os.makedirs(save_dir, exist_ok=True)
    env = APIRoutingEnv()

    # Load trained model
    print("=" * 60)
    print("📊 Adaptive API Orchestrator — Evaluation")
    print("=" * 60)

    model = PPO.load(model_path)
    print(f"✅ Loaded model from: {model_path}")

    strategies = {
        "PPO Agent": lambda obs, step: int(model.predict(obs, deterministic=True)[0]),
        "Random": lambda obs, step: env.action_space.sample(),
        "Always Fastest (A)": lambda obs, step: 0,
        "Always Balanced (B)": lambda obs, step: 1,
        "Always Cheapest (C)": lambda obs, step: 2,
        "Round Robin": lambda obs, step: step % 4,
    }

    results = {}

    for strategy_name, strategy_fn in strategies.items():
        print(f"\n🔄 Evaluating: {strategy_name}...")
        all_rewards = []
        all_latencies = []
        all_costs = []
        all_successes = []
        episode_rewards = []

        for ep in range(n_episodes):
            obs, _ = env.reset()
            ep_reward = 0
            step = 0

            while True:
                action = strategy_fn(obs, step)
                obs, reward, terminated, truncated, info = env.step(action)
                ep_reward += reward
                all_rewards.append(reward)
                all_latencies.append(info["latency"])
                all_costs.append(info["cost"])
                all_successes.append(float(info["success"]))
                step += 1

                if terminated or truncated:
                    break

            episode_rewards.append(ep_reward)

        results[strategy_name] = {
            "avg_episode_reward": float(np.mean(episode_rewards)),
            "std_episode_reward": float(np.std(episode_rewards)),
            "avg_reward_per_step": float(np.mean(all_rewards)),
            "avg_latency": float(np.mean(all_latencies)),
            "avg_cost": float(np.mean(all_costs)),
            "success_rate": float(np.mean(all_successes)),
            "episode_rewards": [float(r) for r in episode_rewards],
        }

        print(
            f"   Avg Episode Reward: {results[strategy_name]['avg_episode_reward']:+.2f} "
            f"(±{results[strategy_name]['std_episode_reward']:.2f})"
        )
        print(f"   Avg Latency:        {results[strategy_name]['avg_latency']:.3f}")
        print(f"   Avg Cost:           {results[strategy_name]['avg_cost']:.3f}")
        print(f"   Success Rate:       {results[strategy_name]['success_rate']:.1%}")

    env.close()

    # ── Print Comparison Table ──
    print("\n" + "=" * 80)
    print(f"{'Strategy':<25} {'Reward':>10} {'Latency':>10} {'Cost':>10} {'Success':>10}")
    print("-" * 80)
    for name, data in results.items():
        print(
            f"{name:<25} "
            f"{data['avg_episode_reward']:>+10.2f} "
            f"{data['avg_latency']:>10.3f} "
            f"{data['avg_cost']:>10.3f} "
            f"{data['success_rate']:>9.1%}"
        )
    print("=" * 80)

    # ── Generate Comparison Plots ──
    _generate_comparison_plots(results, save_dir)

    # ── Save Results ──
    results_path = os.path.join(save_dir, "evaluation_results.json")
    serializable_results = {
        k: {kk: vv for kk, vv in v.items()}
        for k, v in results.items()
    }
    with open(results_path, "w") as f:
        json.dump(serializable_results, f, indent=2)
    print(f"\n💾 Results saved to: {results_path}")

    return results


def _generate_comparison_plots(results, save_dir):
    """Generate comparison bar charts and save as images."""
    strategies = list(results.keys())
    colors = ["#6C5CE7", "#00B894", "#FDCB6E", "#E17055", "#0984E3", "#636E72"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "RL Agent vs Static Strategies — Comparison",
        fontsize=16,
        fontweight="bold",
        color="#2D3436",
    )

    # 1. Average Episode Reward
    ax = axes[0, 0]
    values = [results[s]["avg_episode_reward"] for s in strategies]
    bars = ax.bar(strategies, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Avg Episode Reward", fontweight="bold")
    ax.set_ylabel("Reward")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:+.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # 2. Average Latency
    ax = axes[0, 1]
    values = [results[s]["avg_latency"] for s in strategies]
    bars = ax.bar(strategies, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Avg Latency (lower is better)", fontweight="bold")
    ax.set_ylabel("Latency")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # 3. Average Cost
    ax = axes[1, 0]
    values = [results[s]["avg_cost"] for s in strategies]
    bars = ax.bar(strategies, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Avg Cost (lower is better)", fontweight="bold")
    ax.set_ylabel("Cost")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # 4. Success Rate
    ax = axes[1, 1]
    values = [results[s]["success_rate"] * 100 for s in strategies]
    bars = ax.bar(strategies, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Success Rate (%)", fontweight="bold")
    ax.set_ylabel("Success %")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plot_path = os.path.join(save_dir, "comparison_chart.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n📉 Comparison chart saved to: {plot_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate the trained RL agent")
    parser.add_argument(
        "--model",
        type=str,
        default="./models/ppo_api_orchestrator.zip",
        help="Path to saved model",
    )
    parser.add_argument(
        "--episodes", type=int, default=20, help="Number of evaluation episodes"
    )
    parser.add_argument(
        "--save-dir", type=str, default="./models", help="Results save directory"
    )

    args = parser.parse_args()
    evaluate_model(args.model, args.episodes, args.save_dir)
