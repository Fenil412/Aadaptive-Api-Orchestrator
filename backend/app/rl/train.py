import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from app.rl.env import MicroserviceOrchestrationEnv
from app.config.settings import settings

class DBMetaCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(DBMetaCallback, self).__init__(verbose)
        self.episode = 0

    def _on_step(self) -> bool:
        if self.locals.get("dones", [False])[0]:
            self.episode += 1
        return True

def train_rl_agent(timesteps=10000):
    os.makedirs(os.path.dirname(settings.RL_MODEL_PATH), exist_ok=True)
    
    env = MicroserviceOrchestrationEnv()
    model = PPO("MlpPolicy", env, verbose=1)
    
    print(f"Training model for {timesteps} timesteps...")
    model.learn(total_timesteps=timesteps, callback=DBMetaCallback())
    
    model.save(settings.RL_MODEL_PATH)
    print(f"Model saved to {settings.RL_MODEL_PATH}")

if __name__ == "__main__":
    train_rl_agent(10000)
