"""Response Pydantic schemas for the app/ FastAPI layer."""
from datetime import datetime

from pydantic import BaseModel


class APIResponse(BaseModel):
    api_name: str
    latency: float
    cost: float
    success: bool
    system_load: float


class DecisionResponse(BaseModel):
    action: str
    action_int: int
    confidence: dict[str, float]


class ExecuteResponse(BaseModel):
    action_taken: str
    api_result: APIResponse
    reward: float
    logged: bool
    timestamp: datetime


class DashboardResponse(BaseModel):
    total_calls: int
    success_rate: float
    avg_latency: float
    avg_cost: float
    top_api: str
    recent_decisions: list[dict]
