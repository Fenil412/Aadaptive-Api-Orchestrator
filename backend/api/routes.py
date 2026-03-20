"""
Primary API router — all route handlers for the api/ app.
Run from backend/ directory: uvicorn api.main:app --port 8000 --reload
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.models import APICallRequest, HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

MODELS_DIR = Path(__file__).parents[1] / "models"
METRICS_PATH = MODELS_DIR / "training_metrics.json"

_ppo_model = None
_rl_env = None
_in_memory_logs: list[dict] = []

try:
    from db.connection import get_db_connection as _get_db  # noqa: F401
    _db_available = True
except Exception as _e:
    logger.warning("DB layer unavailable: %s", _e)
    _db_available = False


def _get_env_and_model():
    global _ppo_model, _rl_env
    if _ppo_model is None:
        try:
            from stable_baselines3 import PPO
            model_path = os.getenv("MODEL_PATH", str(MODELS_DIR / "ppo_api_orchestrator.zip"))
            _ppo_model = PPO.load(model_path)
            logger.info("PPO model loaded from %s", model_path)
        except Exception as exc:
            logger.warning("PPO model not loaded: %s", exc)
            _ppo_model = None

    if _rl_env is None:
        try:
            from rl_engine.env import APIRoutingEnv
            _rl_env = APIRoutingEnv()
            _rl_env.reset()
        except Exception as exc:
            logger.warning("RL env not initialized: %s", exc)
            _rl_env = None

    return _rl_env, _ppo_model


@router.get("/", tags=["Health"])
async def root() -> dict[str, Any]:
    _, model = _get_env_and_model()
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "db_available": _db_available,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/simulate-api", tags=["Simulation"])
async def simulate_api_endpoint(body: APICallRequest) -> dict[str, Any]:
    import numpy as np

    env, model = _get_env_and_model()

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run POST /train first.")

    state = np.array(
        [body.latency, body.cost, body.success_rate, body.request_load, body.time_of_day, body.error_rate],
        dtype=np.float32,
    )
    action, _ = model.predict(state.reshape(1, -1), deterministic=True)
    action = int(action)

    provider_names = {0: "Provider_A", 1: "Provider_B", 2: "Provider_C", 3: "Fallback"}
    provider = provider_names.get(action, "Unknown")

    if env is not None:
        env.reset()
        obs, reward, _, _, info = env.step(action)
        latency = info.get("latency", body.latency)
        cost = info.get("cost", body.cost)
        success = info.get("success", True)
    else:
        import random
        latency, cost = body.latency, body.cost
        success = random.random() > 0.1
        reward = 0.3 * (1 - latency) + 0.3 * (1 - cost) + 0.4 * float(success) - 1.0 * float(not success)

    result = {
        "action": action,
        "provider": provider,
        "latency": latency,
        "cost": cost,
        "success": success,
        "reward": reward,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "state": state.tolist(),
    }
    _in_memory_logs.append(result)
    if len(_in_memory_logs) > 1000:
        _in_memory_logs.pop(0)
    return result


@router.get("/training-metrics", tags=["Training"])
async def get_training_metrics() -> dict[str, Any]:
    if METRICS_PATH.exists():
        try:
            with open(METRICS_PATH) as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Failed to read training_metrics.json: %s", exc)
    return {"error": "No training metrics found. Run POST /train first."}


@router.post("/train", tags=["Training"])
async def trigger_training(
    timesteps: int = Query(default=50_000, ge=1_000, le=500_000),
) -> dict[str, Any]:
    try:
        from rl_engine.train import train_model
        metrics = train_model(total_timesteps=timesteps)
        global _ppo_model
        _ppo_model = None
        _get_env_and_model()
        return {"status": "completed", "metrics": metrics}
    except Exception as exc:
        logger.error("Training failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api-logs", tags=["Logs"])
async def get_api_logs(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict]:
    return _in_memory_logs[-limit:][::-1]


@router.get("/dashboard-stats", tags=["Dashboard"])
async def dashboard_stats() -> dict[str, Any]:
    import numpy as np
    logs = _in_memory_logs
    if not logs:
        return {"total_calls": 0, "success_rate": 0.0, "avg_latency": 0.0, "avg_cost": 0.0, "avg_reward": 0.0}
    return {
        "total_calls": len(logs),
        "success_rate": float(np.mean([1.0 if l.get("success") else 0.0 for l in logs])),
        "avg_latency": float(np.mean([l.get("latency", 0.0) for l in logs])),
        "avg_cost": float(np.mean([l.get("cost", 0.0) for l in logs])),
        "avg_reward": float(np.mean([l.get("reward", 0.0) for l in logs])),
    }


@router.post("/evaluate", tags=["Evaluation"])
async def run_evaluation(n_episodes: int = Query(default=20, ge=1, le=200)) -> dict[str, Any]:
    try:
        model_path = os.getenv("MODEL_PATH", str(MODELS_DIR / "ppo_api_orchestrator.zip"))
        from rl_engine.evaluate import evaluate_model
        return evaluate_model(model_path, n_episodes=n_episodes, save_dir=str(MODELS_DIR))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/evaluation-results", tags=["Evaluation"])
async def get_evaluation_results() -> dict[str, Any]:
    eval_path = MODELS_DIR / "evaluation_results.json"
    if eval_path.exists():
        with open(eval_path) as f:
            return json.load(f)
    return {"error": "No evaluation results found. Run POST /evaluate first."}
