"""Pydantic models for the top-level api/ layer."""
from datetime import datetime

from pydantic import BaseModel, Field


class APICallRequest(BaseModel):
    api_name: str = Field(..., min_length=1)
    latency: float = Field(default=0.3, ge=0.0, le=1.0)
    cost: float = Field(default=0.3, ge=0.0, le=1.0)
    success_rate: float = Field(default=0.9, ge=0.0, le=1.0)
    request_load: float = Field(default=0.5, ge=0.0, le=1.0)
    time_of_day: float = Field(default=0.5, ge=0.0, le=1.0)
    error_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    retry: bool = Field(default=False)


class APICallResponse(BaseModel):
    action: int = Field(..., ge=0, le=3)
    provider: str
    latency: float
    cost: float
    success: bool
    reward: float
    timestamp: datetime
    state: list[float] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    model_loaded: bool = Field(default=False)
    db_connected: bool = Field(default=False)
    version: str = Field(default="1.0.0")
    env: str = Field(default="development")
