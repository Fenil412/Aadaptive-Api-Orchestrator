"""
SQLAlchemy 2.0 ORM models for api_logs, rl_decisions, and training_metrics.
"""
import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class ApiLog(Base):
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latency: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    system_load: Mapped[float] = mapped_column(Float, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "api_name": self.api_name,
            "latency": self.latency,
            "cost": self.cost,
            "success": self.success,
            "system_load": self.system_load,
            "action_taken": self.action_taken,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class RLDecision(Base):
    __tablename__ = "rl_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action: Mapped[int] = mapped_column(Integer, nullable=False)
    reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    api_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "api_name": self.api_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class TrainingMetrics(Base):
    __tablename__ = "training_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode: Mapped[int] = mapped_column(Integer, nullable=False)
    total_reward: Mapped[float] = mapped_column(Float, nullable=False)
    avg_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "episode": self.episode,
            "total_reward": self.total_reward,
            "avg_latency": self.avg_latency,
            "success_rate": self.success_rate,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
