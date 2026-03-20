"""API simulation routes — POST /api/simulate, GET /api/logs, /api/config, /api/stats"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.request_schema import SimulateRequest
from app.services.api_simulator import API_CONFIG, simulate_api
from app.services.db_service import fetch_logs, insert_api_log
from app.utils.helpers import InvalidAPIError, SimulationError, calculate_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["API Simulation"])


@router.post("/simulate")
async def simulate_endpoint(body: SimulateRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = simulate_api(body.api_name, retry=body.retry)
    except InvalidAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimulationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        log = await insert_api_log(db, result)
        result["log_id"] = log.id
    except Exception as exc:
        logger.warning("Failed to persist api_log: %s", exc)
        result["log_id"] = None

    return result


@router.get("/logs")
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    api_name: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        logs = await fetch_logs(db, limit=limit, api_name=api_name)
        return [log.to_dict() for log in logs]
    except Exception as exc:
        logger.error("fetch_logs failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch logs") from exc


@router.get("/config")
async def get_config() -> dict[str, Any]:
    return API_CONFIG


@router.get("/stats")
async def get_stats(
    limit: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        logs = await fetch_logs(db, limit=limit)
        return calculate_stats(logs)
    except Exception as exc:
        logger.error("get_stats failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to compute stats") from exc
