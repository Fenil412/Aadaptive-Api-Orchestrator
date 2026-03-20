"""UI aggregation routes — GET /ui/dashboard, /ui/live-feed, /ui/performance"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.db_service import fetch_logs, fetch_rl_decisions, fetch_training_metrics
from app.utils.helpers import calculate_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ui", tags=["UI Data"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        logs = await fetch_logs(db, limit=500)
        decisions = await fetch_rl_decisions(db, limit=20)
        stats = calculate_stats(logs)
        top_api = max(stats["per_api"], key=lambda k: stats["per_api"][k]["total"]) if stats["per_api"] else ""
        return {
            "total_calls": stats["total"],
            "success_rate": stats["success_rate"],
            "avg_latency": stats["avg_latency"],
            "avg_cost": stats["avg_cost"],
            "top_api": top_api,
            "recent_decisions": [d.to_dict() for d in decisions],
            "per_api_stats": stats["per_api"],
        }
    except Exception as exc:
        logger.error("dashboard endpoint failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to build dashboard") from exc


@router.get("/live-feed")
async def live_feed(db: AsyncSession = Depends(get_db)) -> list[dict]:
    try:
        decisions = await fetch_rl_decisions(db, limit=20)
        return [d.to_dict() for d in decisions]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch live feed") from exc


@router.get("/performance")
async def performance(
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        metrics = await fetch_training_metrics(db, limit=limit)
        return [m.to_dict() for m in metrics]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch performance data") from exc
