import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    _default_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    if "your-supabase-project" in _default_url:
        DATABASE_URL: str = "sqlite:///./api_orchestrator.db"
    else:
        DATABASE_URL: str = _default_url
    
    PROJECT_NAME: str = "RL-based API Orchestration System"
    RL_MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rl", "model", "ppo_model.zip")

settings = Settings()
