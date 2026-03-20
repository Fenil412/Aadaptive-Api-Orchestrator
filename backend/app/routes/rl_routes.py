"""RL decision routes — POST /rl/get-decision, /rl/execute, GET /rl/decisions, /rl/metrics"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.request_schema import StateInput
from app.schemas.response_schema import DecisionResponse
from app.services.api_simulator import simulate_api
from app.services.db_service import (
    fetch_rl_decisions, fetch_training_metrics,
    insert_api_log, insert_rl_decision,
)
from app.utils.helpers import InvalidAPIError, SimulationError, compute_reward

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rl", tags=["RL Agent"])

_rl_agent = None


def _get_agent():
    global _rl_agent
    if _rl_agent is None:
        from app.config.settings import settings
        from app.services.rl_agent import RLAgent
        _rl_agent = RLAgent(model_path=settings.MODEL_PATH)
        _rl_agent.load_model()
    return _rl_agent


@router.post("/get-decision", response_model=DecisionResponse)
async def get_decision(body: StateInput) -> DecisionResponse:
    agent = _get_agent()
    state = [body.latency, body.cost, body.success_rate, body.system_load, body.previous_action]
    try:
        result = agent.get_action_with_confidence(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RL inference failed") from exc

    return DecisionResponse(
        action=result["action"],
        action_int=result["action_int"],
        confidence=result["confidence"],
    )


@router.post("/execute")
async def execute_pipeline(body: StateInput, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    agent = _get_agent()
    state = [body.latency, body.cost, body.success_rate, body.system_load, body.previous_action]

    try:
        decision = agent.get_action_with_confidence(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RL inference failed: {exc}") from exc

    action_int = decision["action_int"]
    retry = action_int == 1

    try:
        sim_result = simulate_api(body.api_name, retry=retry)
    except InvalidAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimulationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    reward = compute_reward(sim_result, action_int)
    logged = False

    try:
        sim_result["action_taken"] = decision["action"]
        await insert_api_log(db, sim_result)
        await insert_rl_decision(db, state, action_int, reward, body.api_name)
        logged = True
    except Exception as exc:
        logger.warning("Failed to persist execute pipeline records: %s", exc)

    return {
        "action_taken": decision["action"],
        "action_int": action_int,
        "confidence": decision["confidence"],
        "api_result": sim_result,
        "reward": reward,
        "logged": logged,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/decisions")
async def get_decisions(
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        decisions = await fetch_rl_decisions(db, limit=limit)
        return [d.to_dict() for d in decisions]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch decisions") from exc


@router.get("/metrics")
async def get_metrics(
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        metrics = await fetch_training_metrics(db, limit=limit)
        return [m.to_dict() for m in metrics]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch metrics") from exc
