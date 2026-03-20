import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from app.services.api_simulator import APISimulator

class MicroserviceOrchestrationEnv(gym.Env):
    def __init__(self):
        super(MicroserviceOrchestrationEnv, self).__init__()
        
        # Latency, cost, success_rate, load, previous_action
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 3.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )
        # 0: call, 1: retry, 2: skip, 3: switch
        self.action_space = spaces.Discrete(4)
        
        self.current_step = 0
        self.max_steps = 100
        self.state = np.zeros(5, dtype=np.float32)
        
        self.episode_reward = 0
        self.episode_latency = []
        self.episode_successes = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_reward = 0
        self.episode_latency = []
        self.episode_successes = []
        
        self.state = np.array([0.0, 0.0, 1.0, random.uniform(0.5, 2.5), 0.0], dtype=np.float32)
        return self.state, {}

    def step(self, action):
        self.current_step += 1
        action = int(action)
        
        _, _, success_rate, system_load, _ = self.state
        
        reward = 0
        success = False
        api_lat = 0
        api_cost = 0
        
        if action == 2: # Skip
            success = True
            reward = -10
        else:
            category = "ecommerce"
            api_name = "payment_A" if action != 3 else "payment_B" 
            is_retry = (action == 1)
            
            res = APISimulator.call_api(category, api_name, system_load, is_retry)
            success = res["success"]
            api_lat = res["latency"]
            api_cost = res["cost"]
            
            lat_norm = min(api_lat / 1000.0, 1.0)
            
            if success:
                reward = 100 - (lat_norm * 10) - (api_cost * 5)
            else:
                reward = -50 - (lat_norm * 10) - (api_cost * 5)
                
        self.episode_reward += reward
        self.episode_latency.append(api_lat)
        self.episode_successes.append(1 if success else 0)
        
        new_latency = min(api_lat / 1000.0, 1.0)
        new_cost = min(api_cost, 1.0)
        new_success_rate = success_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        new_system_load = max(0.1, min(3.0, system_load + random.uniform(-0.2, 0.2)))
        new_previous_action = action / 3.0
        
        self.state = np.array([new_latency, new_cost, new_success_rate, new_system_load, new_previous_action], dtype=np.float32)
        
        done = self.current_step >= self.max_steps
        truncated = False
        
        info = {"api_latency": api_lat, "api_cost": api_cost, "success": success}
        
        return self.state, float(reward), done, truncated, info

gym.register(
    id="MicroserviceOrchestrator-v0",
    entry_point="app.rl.env:MicroserviceOrchestrationEnv",
    max_episode_steps=100,
)
