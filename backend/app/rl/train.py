"""
PPO training script for the app/rl integrated environment.
Run from backend/ directory:
    python -m app.rl.train
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from app.rl.env import MicroserviceOrchestrationEnv

logger = logging.getLogger(__name__)

MODEL_SAVE_PATH = Path(__file__).parent / "model" / "ppo_model.zip"
METRICS_SAVE_PATH = Path(__file__).parents[2] / "models" / "training_metrics.json"
LOG_DIR = Path(__file__).parents[2] / "logs" / "app_rl"
TOTAL_TIMESTEPS = 50_000
EVAL_FREQ = 5_000


def _make_env(api_name: str = "payment_A"):
    def _init():
        return Monitor(MicroserviceOrchestrationEnv(api_name=api_name))
    return _init


def train_rl_agent(timesteps: int = TOTAL_TIMESTEPS) -> dict:
    """Train PPO on MicroserviceOrchestrationEnv and return metrics dict."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

    vec_env = DummyVecEnv([_make_env()])

    # TensorBoard logging is optional
    try:
        import tensorboard  # noqa: F401
        tb_log = str(LOG_DIR)
    except ImportError:
        logger.warning("tensorboard not installed — skipping TB logging.")
        tb_log = None

    model = PPO(
        "MlpPolicy", vec_env, verbose=0,
        tensorboard_log=tb_log,
        learning_rate=3e-4, n_steps=2048, batch_size=64, n_epochs=10, gamma=0.99,
    )

    logger.info("Starting PPO training for %d timesteps...", timesteps)
    start_time = time.time()
    episode_rewards: list[dict] = []
    episode_count = 0

    for checkpoint in range(0, timesteps, EVAL_FREQ):
        steps = min(EVAL_FREQ, timesteps - checkpoint)
        model.learn(total_timesteps=steps, reset_num_timesteps=(checkpoint == 0))

        obs = vec_env.reset()
        ep_reward, ep_len, done = 0.0, 0, False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done_arr, _ = vec_env.step(action)
            ep_reward += float(reward[0])
            ep_len += 1
            done = bool(done_arr[0])

        episode_count += 1
        episode_rewards.append({"episode": episode_count, "reward": ep_reward, "length": ep_len})
        logger.info("Step %d/%d — episode reward: %.2f", checkpoint + steps, timesteps, ep_reward)

    elapsed = time.time() - start_time
    rewards_arr = np.array([e["reward"] for e in episode_rewards])
    metrics = {
        "total_timesteps": timesteps,
        "mean_reward": float(np.mean(rewards_arr)),
        "std_reward": float(np.std(rewards_arr)),
        "training_time_seconds": round(elapsed, 2),
        "episodes": episode_rewards,
    }

    model.save(str(MODEL_SAVE_PATH))
    logger.info("Model saved to %s", MODEL_SAVE_PATH)

    with open(METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics saved to %s", METRICS_SAVE_PATH)

    vec_env.close()
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = train_rl_agent()
    print(f"Training complete. Mean reward: {result['mean_reward']:.4f}")
