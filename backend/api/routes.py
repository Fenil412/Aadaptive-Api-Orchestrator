"""
FastAPI route handlers for the Adaptive API Orchestrator.

Endpoints:
    GET  /                    - Health check
    POST /simulate-api        - Simulate a single API routing decision
    POST /simulate-run        - Run a full simulation episode
    GET  /get-decision        - Get RL decision for given state
    POST /train               - Train/retrain the RL model
    GET  /training-metrics    - Get training metrics for graphs
    GET  /evaluation-results  - Get RL vs static comparison
    GET  /api-logs            - Fetch API logs
    GET  /rl-decisions        - Fetch RL decisions
    GET  /dashboard-stats     - Get dashboard summary
"""

import os
import sys
import json
import numpy as np
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from rl_engine.env import APIRoutingEnv, PROVIDER_PROFILES
from api.models import (
    SimulateAPIRequest,
    TrainRequest,
    DecisionResponse,
    SimulationResponse,
    SimulationRunResponse,
    TrainingStatusResponse,
    HealthResponse,
    MetricsResponse,
    DashboardStats,
)

# Try to import DB functions (graceful fallback if DB not configured)
try:
    from db.connection import (
        insert_api_log,
        get_api_logs,
        get_api_logs_count,
        insert_rl_decision,
        get_rl_decisions,
        get_dashboard_stats,
        get_evaluation_results,
    )
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
    print("⚠️  Database not configured, running in memory-only mode")

router = APIRouter()

# ── Global state ──
_model = None
_env = None
_in_memory_logs = []  # Fallback when DB is unavailable
_in_memory_decisions = []

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "ppo_api_orchestrator.zip")


def _load_model():
    """Load the trained RL model (lazy loading)."""
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = PPO.load(MODEL_PATH)
            print(f"✅ Model loaded from: {MODEL_PATH}")
        else:
            print(f"⚠️  No trained model found at: {MODEL_PATH}")
    return _model


def _get_env():
    """Get or create the environment instance."""
    global _env
    if _env is None:
        _env = APIRoutingEnv()
    return _env


# ═══════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    model = _load_model()
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/simulate-api", response_model=SimulationResponse)
async def simulate_api(request: SimulateAPIRequest):
    """
    Simulate a single API routing decision.
    Uses the RL model to decide which provider to route to.
    """
    model = _load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="No trained model available. Train the model first via POST /train",
        )

    env = _get_env()

    # Build state from request
    state = np.array(
        [
            request.current_latency,
            request.current_cost,
            request.success_rate,
            request.request_load,
            request.time_of_day,
            request.error_rate,
        ],
        dtype=np.float32,
    )

    # Get RL decision
    action, _ = model.predict(state, deterministic=True)
    action = int(action)

    # Simulate the outcome
    latency, cost, success = env._simulate_provider_response(action, state)
    reward = env._calculate_reward(latency, cost, success)
    provider_name = PROVIDER_PROFILES[action]["name"]

    # Log to DB or memory
    state_list = state.tolist()
    if DB_AVAILABLE:
        insert_api_log(action, provider_name, latency, cost, success, reward, state_list)
    else:
        _in_memory_logs.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "provider": provider_name,
            "latency": float(latency),
            "cost": float(cost),
            "success": bool(success),
            "reward": float(reward),
            "state": state_list,
        })

    return SimulationResponse(
        step=len(_in_memory_logs) if not DB_AVAILABLE else 0,
        action=action,
        provider=provider_name,
        latency=float(latency),
        cost=float(cost),
        success=bool(success),
        reward=float(reward),
        state=state_list,
    )


@router.post("/simulate-run", response_model=SimulationRunResponse)
async def simulate_run(num_steps: int = Query(default=50, ge=1, le=500)):
    """
    Run a full simulation of multiple steps.
    Uses the RL model to make decisions at each step.
    """
    model = _load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="No trained model available. Train the model first.",
        )

    env = _get_env()
    obs, _ = env.reset()
    steps = []

    for i in range(num_steps):
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)
        obs, reward, terminated, truncated, info = env.step(action)

        step_data = SimulationResponse(
            step=i + 1,
            action=action,
            provider=info["provider"],
            latency=float(info["latency"]),
            cost=float(info["cost"]),
            success=bool(info["success"]),
            reward=float(info["reward"]),
            state=obs.tolist(),
        )
        steps.append(step_data)

        # Log to DB
        if DB_AVAILABLE:
            insert_api_log(
                action, info["provider"],
                info["latency"], info["cost"],
                info["success"], info["reward"],
                obs.tolist(),
            )

        if terminated or truncated:
            break

    summary = env.get_episode_summary()

    return SimulationRunResponse(steps=steps, summary=summary)


@router.get("/get-decision", response_model=DecisionResponse)
async def get_decision(
    latency: float = Query(default=0.5, ge=0, le=1),
    cost: float = Query(default=0.5, ge=0, le=1),
    success_rate: float = Query(default=0.8, ge=0, le=1),
    load: float = Query(default=0.5, ge=0, le=1),
    time: float = Query(default=0.5, ge=0, le=1),
    error_rate: float = Query(default=0.1, ge=0, le=1),
):
    """
    Get an RL routing decision for the given system state.
    Returns the chosen provider and expected outcome.
    """
    model = _load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="No trained model available.",
        )

    env = _get_env()
    state = np.array(
        [latency, cost, success_rate, load, time, error_rate],
        dtype=np.float32,
    )

    action, _ = model.predict(state, deterministic=True)
    action = int(action)

    # Simulate outcome
    result_latency, result_cost, success = env._simulate_provider_response(action, state)
    reward = env._calculate_reward(result_latency, result_cost, success)
    profile = PROVIDER_PROFILES[action]

    return DecisionResponse(
        action=action,
        provider={
            "id": action,
            "name": profile["name"],
            "latency": float(result_latency),
            "cost": float(result_cost),
            "success": bool(success),
        },
        reward=float(reward),
        state=state.tolist(),
        timestamp=datetime.now().isoformat(),
    )


@router.post("/train", response_model=TrainingStatusResponse)
async def train_model(request: TrainRequest):
    """
    Train or retrain the RL model.
    WARNING: This is a blocking operation that may take a while.
    """
    global _model

    try:
        from rl_engine.train import train_model as do_train

        os.makedirs(MODEL_DIR, exist_ok=True)
        _model = do_train(
            total_timesteps=request.timesteps,
            save_dir=MODEL_DIR,
            model_name="ppo_api_orchestrator",
            learning_rate=request.learning_rate,
        )

        return TrainingStatusResponse(
            status="completed",
            message=f"Model trained for {request.timesteps} timesteps",
            model_path=MODEL_PATH,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}",
        )


@router.get("/training-metrics", response_model=MetricsResponse)
async def get_training_metrics():
    """Get training metrics for visualization."""
    metrics_path = os.path.join(MODEL_DIR, "training_metrics.json")

    if not os.path.exists(metrics_path):
        # Return empty metrics
        return MetricsResponse(
            timesteps=[],
            mean_rewards=[],
            mean_latencies=[],
            mean_costs=[],
            success_rates=[],
        )

    with open(metrics_path, "r") as f:
        data = json.load(f)

    return MetricsResponse(
        timesteps=data.get("timesteps", []),
        mean_rewards=data.get("mean_rewards", []),
        mean_latencies=data.get("mean_latencies", []),
        mean_costs=data.get("mean_costs", []),
        success_rates=data.get("success_rates", []),
    )


@router.get("/evaluation-results")
async def evaluation_results():
    """Get RL vs static strategy comparison results."""
    # Try from DB first
    if DB_AVAILABLE:
        results = get_evaluation_results()
        if results:
            return results

    # Fallback to file
    results_path = os.path.join(MODEL_DIR, "evaluation_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)

    return {"message": "No evaluation results available. Run evaluation first."}


@router.get("/api-logs")
async def fetch_api_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Fetch API routing logs."""
    if DB_AVAILABLE:
        return get_api_logs(limit, offset)

    # In-memory fallback
    start = offset
    end = offset + limit
    return _in_memory_logs[start:end][::-1]  # newest first


@router.get("/rl-decisions")
async def fetch_rl_decisions(limit: int = Query(default=100, ge=1, le=1000)):
    """Fetch RL decision records."""
    if DB_AVAILABLE:
        return get_rl_decisions(limit)

    return _in_memory_decisions[:limit]


@router.get("/dashboard-stats", response_model=DashboardStats)
async def dashboard_stats():
    """Get aggregated dashboard statistics."""
    if DB_AVAILABLE:
        stats = get_dashboard_stats()
        return DashboardStats(**stats)

    # Compute from in-memory logs
    if not _in_memory_logs:
        return DashboardStats(
            total_decisions=0,
            avg_reward=0,
            avg_latency=0,
            avg_cost=0,
            success_rate=0,
            provider_distribution={},
            recent_trend="stable",
        )

    logs = _in_memory_logs
    provider_dist = {}
    for log in logs:
        p = log["provider"]
        provider_dist[p] = provider_dist.get(p, 0) + 1

    return DashboardStats(
        total_decisions=len(logs),
        avg_reward=np.mean([l["reward"] for l in logs]),
        avg_latency=np.mean([l["latency"] for l in logs]),
        avg_cost=np.mean([l["cost"] for l in logs]),
        success_rate=np.mean([float(l["success"]) for l in logs]),
        provider_distribution=provider_dist,
        recent_trend="stable",
    )


@router.post("/evaluate")
async def run_evaluation(episodes: int = Query(default=20, ge=5, le=100)):
    """Run evaluation comparing RL agent against static strategies."""
    model = _load_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="No trained model available.",
        )

    try:
        from rl_engine.evaluate import evaluate_model

        results = evaluate_model(
            model_path=MODEL_PATH,
            n_episodes=episodes,
            save_dir=MODEL_DIR,
        )

        # Save to DB if available
        if DB_AVAILABLE:
            for strategy_name, data in results.items():
                insert_evaluation_result(
                    strategy_name,
                    data["avg_episode_reward"],
                    data["avg_latency"],
                    data["avg_cost"],
                    data["success_rate"],
                    episodes,
                )

        # Return serializable results
        return {
            name: {
                k: v for k, v in data.items()
                if k != "episode_rewards"
            }
            for name, data in results.items()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}",
        )
