"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request Models ──

class SimulateAPIRequest(BaseModel):
    """Request body for /simulate-api endpoint."""
    current_latency: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Current API latency (normalized)"
    )
    current_cost: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Current API cost (normalized)"
    )
    success_rate: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Recent success ratio"
    )
    request_load: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Current request volume"
    )
    time_of_day: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Normalized hour (0-1)"
    )
    error_rate: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Recent error ratio"
    )


class TrainRequest(BaseModel):
    """Request body for /train endpoint."""
    timesteps: int = Field(
        default=10000, ge=1000, le=500000, description="Training timesteps"
    )
    learning_rate: float = Field(default=3e-4, gt=0, description="Learning rate")


# ── Response Models ──

class ProviderInfo(BaseModel):
    """Information about the selected API provider."""
    id: int
    name: str
    latency: float
    cost: float
    success: bool


class DecisionResponse(BaseModel):
    """Response from /get-decision endpoint."""
    action: int
    provider: ProviderInfo
    reward: float
    state: List[float]
    timestamp: str


class SimulationResponse(BaseModel):
    """Response from /simulate-api endpoint."""
    step: int
    action: int
    provider: str
    latency: float
    cost: float
    success: bool
    reward: float
    state: List[float]


class SimulationRunResponse(BaseModel):
    """Response from /simulate-run endpoint (runs multiple steps)."""
    steps: List[SimulationResponse]
    summary: dict


class TrainingStatusResponse(BaseModel):
    """Response for training status."""
    status: str
    message: str
    model_path: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    timestamp: str


class APILogEntry(BaseModel):
    """An API log entry for the dashboard."""
    id: Optional[int] = None
    timestamp: str
    action: int
    provider: str
    latency: float
    cost: float
    success: bool
    reward: float
    state: List[float]


class EvaluationResult(BaseModel):
    """Evaluation comparison result."""
    strategy: str
    avg_episode_reward: float
    avg_latency: float
    avg_cost: float
    success_rate: float


class MetricsResponse(BaseModel):
    """Training metrics for graphs."""
    timesteps: List[int]
    mean_rewards: List[float]
    mean_latencies: List[float]
    mean_costs: List[float]
    success_rates: List[float]


class DashboardStats(BaseModel):
    """Summary statistics for the dashboard."""
    total_decisions: int
    avg_reward: float
    avg_latency: float
    avg_cost: float
    success_rate: float
    provider_distribution: dict
    recent_trend: str  # "improving", "stable", "declining"
