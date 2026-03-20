"""
RLAgent service — loads a trained PPO model and provides action inference.
"""
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.utils.helpers import ModelNotLoadedError

logger = logging.getLogger(__name__)

ACTION_MAP: dict[int, str] = {
    0: "call_api",
    1: "retry",
    2: "skip",
    3: "switch_provider",
}


class RLAgent:
    """Wraps a stable-baselines3 PPO model for inference."""

    def __init__(self, model_path: str) -> None:
        self.model_path = Path(model_path)
        self._model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the PPO model from disk."""
        try:
            from stable_baselines3 import PPO

            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            self._model = PPO.load(str(self.model_path))
            self._loaded = True
            logger.info("RLAgent: model loaded from %s", self.model_path)
        except Exception as exc:
            self._loaded = False
            logger.warning("RLAgent: failed to load model — %s. Using random fallback.", exc)

    def get_action(self, state: list[float]) -> str:
        """Return action label string. Falls back to random if model not loaded."""
        if not self._loaded or self._model is None:
            import random
            action_int = random.randint(0, 3)
            logger.warning("RLAgent: model not loaded, using random action %d", action_int)
            return ACTION_MAP[action_int]

        obs = np.array(state, dtype=np.float32).reshape(1, -1)
        action_int, _ = self._model.predict(obs, deterministic=True)
        return ACTION_MAP.get(int(action_int), "call_api")

    def get_action_with_confidence(self, state: list[float]) -> dict[str, Any]:
        """Return action label, integer, and per-action confidence scores."""
        if not self._loaded or self._model is None:
            import random
            action_int = random.randint(0, 3)
            return {
                "action": ACTION_MAP[action_int],
                "action_int": action_int,
                "confidence": {label: 0.25 for label in ACTION_MAP.values()},
            }

        import torch

        obs = np.array(state, dtype=np.float32).reshape(1, -1)
        obs_tensor = torch.tensor(obs, dtype=torch.float32)

        with torch.no_grad():
            distribution = self._model.policy.get_distribution(obs_tensor)
            probs = distribution.distribution.probs.squeeze().cpu().numpy()

        action_int = int(np.argmax(probs))
        confidence = {ACTION_MAP[i]: float(probs[i]) for i in range(len(probs))}

        return {
            "action": ACTION_MAP[action_int],
            "action_int": action_int,
            "confidence": confidence,
        }

    @property
    def is_loaded(self) -> bool:
        return self._loaded
