"""
Training script for the API Routing RL agent.

Uses PPO (Proximal Policy Optimization) from Stable-Baselines3.
Trains on the custom APIRoutingEnv and saves the model.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from rl_engine.env import APIRoutingEnv


class TrainingMetricsCallback(BaseCallback):
    """
    Custom callback to log training metrics at regular intervals.
    Saves metrics to a JSON file for visualization.
    """

    def __init__(self, log_interval=1000, save_path="./models", verbose=1):
        super().__init__(verbose)
        self.log_interval = log_interval
        self.save_path = save_path
        self.metrics = {
            "timestamps": [],
            "timesteps": [],
            "mean_rewards": [],
            "mean_latencies": [],
            "mean_costs": [],
            "success_rates": [],
        }
        self._episode_rewards = []
        self._episode_latencies = []
        self._episode_costs = []
        self._episode_successes = []

    def _on_step(self) -> bool:
        # Collect info from the environment
        infos = self.locals.get("infos", [])
        for info in infos:
            if "reward" in info:
                self._episode_rewards.append(info["reward"])
            if "latency" in info:
                self._episode_latencies.append(info["latency"])
            if "cost" in info:
                self._episode_costs.append(info["cost"])
            if "success" in info:
                self._episode_successes.append(float(info["success"]))

        if self.num_timesteps % self.log_interval == 0 and self._episode_rewards:
            mean_reward = np.mean(self._episode_rewards[-100:])
            mean_latency = np.mean(self._episode_latencies[-100:])
            mean_cost = np.mean(self._episode_costs[-100:])
            success_rate = np.mean(self._episode_successes[-100:])

            self.metrics["timestamps"].append(datetime.now().isoformat())
            self.metrics["timesteps"].append(self.num_timesteps)
            self.metrics["mean_rewards"].append(float(mean_reward))
            self.metrics["mean_latencies"].append(float(mean_latency))
            self.metrics["mean_costs"].append(float(mean_cost))
            self.metrics["success_rates"].append(float(success_rate))

            if self.verbose:
                print(
                    f"  [Step {self.num_timesteps:6d}] "
                    f"Reward: {mean_reward:+.3f} | "
                    f"Latency: {mean_latency:.3f} | "
                    f"Cost: {mean_cost:.3f} | "
                    f"Success: {success_rate:.1%}"
                )

        return True

    def _on_training_end(self) -> None:
        # Save training metrics
        metrics_path = os.path.join(self.save_path, "training_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
        if self.verbose:
            print(f"\n📊 Training metrics saved to: {metrics_path}")


def train_model(
    total_timesteps=10000,
    save_dir="./models",
    model_name="ppo_api_orchestrator",
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
):
    """
    Train a PPO agent on the API Routing environment.

    Args:
        total_timesteps: Number of training steps
        save_dir: Directory to save model and metrics
        model_name: Name for the saved model file
        learning_rate: PPO learning rate
        n_steps: Steps per rollout collection
        batch_size: Minibatch size for PPO
        n_epochs: Number of optimization epochs per rollout
        gamma: Discount factor
        verbose: Verbosity level

    Returns:
        Trained PPO model
    """
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 60)
    print("🚀 Adaptive API Orchestrator — RL Training")
    print("=" * 60)
    print(f"  Algorithm:       PPO (Proximal Policy Optimization)")
    print(f"  Total Timesteps: {total_timesteps:,}")
    print(f"  Learning Rate:   {learning_rate}")
    print(f"  Batch Size:      {batch_size}")
    print(f"  Gamma:           {gamma}")
    print(f"  Save Directory:  {save_dir}")
    print("=" * 60)

    # Create environment
    env = APIRoutingEnv()
    print("\n✅ Environment created successfully")
    print(f"   Observation Space: {env.observation_space}")
    print(f"   Action Space:      {env.action_space}")

    # Create PPO model
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        verbose=0,  # We use our custom callback for logging
        tensorboard_log=None,
    )
    print("\n✅ PPO model initialized")

    # Setup callback
    callback = TrainingMetricsCallback(
        log_interval=500, save_path=save_dir, verbose=verbose
    )

    # Train
    print("\n🏋️ Training started...\n")
    model.learn(total_timesteps=total_timesteps, callback=callback)
    print("\n✅ Training completed!")

    # Save model
    model_path = os.path.join(save_dir, model_name)
    model.save(model_path)
    print(f"\n💾 Model saved to: {model_path}.zip")

    # Run a quick evaluation
    print("\n📈 Quick Evaluation (5 episodes)...")
    evaluate_quick(model, env, n_episodes=5)

    env.close()
    return model


def evaluate_quick(model, env, n_episodes=5):
    """Run a quick evaluation of the trained model."""
    total_rewards = []
    total_successes = []

    for ep in range(n_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        episode_successes = 0
        steps = 0

        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            episode_successes += int(info.get("success", False))
            steps += 1

            if terminated or truncated:
                break

        total_rewards.append(episode_reward)
        total_successes.append(episode_successes / steps if steps > 0 else 0)
        print(
            f"  Episode {ep + 1}: "
            f"Reward={episode_reward:+.2f}, "
            f"Success Rate={total_successes[-1]:.1%}, "
            f"Steps={steps}"
        )

    print(f"\n  Average Reward:       {np.mean(total_rewards):+.2f}")
    print(f"  Average Success Rate: {np.mean(total_successes):.1%}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train the API Routing RL Agent")
    parser.add_argument(
        "--timesteps", type=int, default=10000, help="Total training timesteps"
    )
    parser.add_argument(
        "--save-dir", type=str, default="./models", help="Model save directory"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="ppo_api_orchestrator",
        help="Model filename",
    )
    parser.add_argument(
        "--lr", type=float, default=3e-4, help="Learning rate"
    )

    args = parser.parse_args()

    train_model(
        total_timesteps=args.timesteps,
        save_dir=args.save_dir,
        model_name=args.model_name,
        learning_rate=args.lr,
    )
