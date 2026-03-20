"""
Standalone PPO training script for rl_engine.
Run from backend/ directory:
    python -m rl_engine.train
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from rl_engine.env import APIRoutingEnv

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parents[1] / "models"
MODEL_SAVE_PATH = MODELS_DIR / "ppo_api_orchestrator.zip"
METRICS_SAVE_PATH = MODELS_DIR / "training_metrics.json"
LOG_DIR = Path(__file__).parents[1] / "logs" / "rl_engine"
TOTAL_TIMESTEPS = 50_000
EVAL_FREQ = 5_000


class _EpisodeCallback(BaseCallback):
    def __init__(self, eval_freq: int = EVAL_FREQ):
        super().__init__(verbose=0)
        self.eval_freq = eval_freq
        self.episodes: list[dict] = []
        self._ep_count = 0

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "episode" in info:
                self._ep_count += 1
                self.episodes.append({
                    "episode": self._ep_count,
                    "reward": float(info["episode"]["r"]),
                    "length": int(info["episode"]["l"]),
                })
                if self._ep_count % 10 == 0:
                    logger.info(
                        "Episode %d — reward: %.2f, length: %d",
                        self._ep_count, info["episode"]["r"], info["episode"]["l"],
                    )
        return True


def train_model(
    total_timesteps: int = TOTAL_TIMESTEPS,
    save_dir: Path = MODELS_DIR,
    model_name: str = "ppo_api_orchestrator",
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
) -> dict:
    """Train PPO on APIRoutingEnv and return metrics dict."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # TensorBoard logging is optional — only enable if fully functional
    tb_log = None
    try:
        import tensorboard  # noqa: F401
        from torch.utils.tensorboard import SummaryWriter  # noqa: F401
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        tb_log = str(LOG_DIR)
    except Exception:
        logger.warning("TensorBoard not available — skipping TB logging.")

    vec_env = DummyVecEnv([lambda: Monitor(APIRoutingEnv())])
    model = PPO(
        "MlpPolicy", vec_env, verbose=0,
        tensorboard_log=tb_log,
        learning_rate=learning_rate, n_steps=n_steps,
        batch_size=batch_size, n_epochs=n_epochs, gamma=gamma,
    )

    callback = _EpisodeCallback(eval_freq=EVAL_FREQ)
    logger.info("Starting PPO training for %d timesteps...", total_timesteps)
    start_time = time.time()
    model.learn(total_timesteps=total_timesteps, callback=callback, progress_bar=False)
    elapsed = time.time() - start_time

    save_path = save_dir / f"{model_name}.zip"
    model.save(str(save_path))
    logger.info("Model saved to %s", save_path)

    rewards = [e["reward"] for e in callback.episodes] if callback.episodes else [0.0]
    metrics = {
        "total_timesteps": total_timesteps,
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "training_time_seconds": round(elapsed, 2),
        "episodes": callback.episodes,
    }

    metrics_path = save_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics saved to %s", metrics_path)

    vec_env.close()
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = train_model()
    print(f"\nTraining complete.")
    print(f"  Mean reward : {result['mean_reward']:.4f}")
    print(f"  Std reward  : {result['std_reward']:.4f}")
    print(f"  Time        : {result['training_time_seconds']:.1f}s")
    print(f"  Episodes    : {len(result['episodes'])}")
