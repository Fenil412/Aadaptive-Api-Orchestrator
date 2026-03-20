"""
Async database service layer — CRUD for api_logs, rl_decisions, training_metrics.
"""
import logging
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import ApiLog, RLDecision, TrainingMetrics

logger = logging.getLogger(__name__)


async def insert_api_log(db: AsyncSession, result: dict[str, Any]) -> ApiLog:
    log = ApiLog(
        api_name=result.get("api_name", "unknown"),
        latency=float(result.get("latency", 0.0)),
        cost=float(result.get("cost", 0.0)),
        success=bool(result.get("success", False)),
        system_load=float(result.get("system_load", 1.0)),
        action_taken=result.get("action_taken"),
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    logger.debug("Inserted api_log id=%d api=%s", log.id, log.api_name)
    return log


async def insert_rl_decision(
    db: AsyncSession,
    state: list[float] | dict,
    action: int,
    reward: float,
    api_name: str,
) -> RLDecision:
    state_payload = state if isinstance(state, dict) else {"values": state}
    decision = RLDecision(state=state_payload, action=action, reward=reward, api_name=api_name)
    db.add(decision)
    await db.flush()
    await db.refresh(decision)
    logger.debug("Inserted rl_decision id=%d action=%d reward=%.4f", decision.id, action, reward)
    return decision


async def insert_training_metrics(
    db: AsyncSession, episode: int, metrics: dict[str, Any]
) -> TrainingMetrics:
    record = TrainingMetrics(
        episode=episode,
        total_reward=float(metrics.get("total_reward", 0.0)),
        avg_latency=float(metrics.get("avg_latency", 0.0)),
        success_rate=float(metrics.get("success_rate", 0.0)),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def fetch_logs(
    db: AsyncSession, limit: int = 100, api_name: str | None = None
) -> list[ApiLog]:
    stmt = select(ApiLog).order_by(desc(ApiLog.timestamp)).limit(limit)
    if api_name:
        stmt = stmt.where(ApiLog.api_name == api_name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def fetch_rl_decisions(db: AsyncSession, limit: int = 50) -> list[RLDecision]:
    stmt = select(RLDecision).order_by(desc(RLDecision.timestamp)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def fetch_training_metrics(db: AsyncSession, limit: int = 20) -> list[TrainingMetrics]:
    stmt = select(TrainingMetrics).order_by(desc(TrainingMetrics.timestamp)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
