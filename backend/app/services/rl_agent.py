import os
import numpy as np
from stable_baselines3 import PPO
from app.config.settings import settings

class RLAgent:
    def __init__(self):
        self.model = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(settings.RL_MODEL_PATH) or os.path.exists(settings.RL_MODEL_PATH + ".zip"):
            try:
                self.model = PPO.load(settings.RL_MODEL_PATH)
                print("RL Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print(f"Warning: RL Model not found at {settings.RL_MODEL_PATH}. Using random actions until trained.")
            self.model = None

    def get_action(self, state_array: list) -> int:
        if self.model is None:
            self.load_model()
            if self.model is None:
                import random
                return random.randint(0, 3)
                
        state = np.array(state_array, dtype=np.float32)
        action, _ = self.model.predict(state, deterministic=True)
        return int(action)

rl_agent_service = RLAgent()
