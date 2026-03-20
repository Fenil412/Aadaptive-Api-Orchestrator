"""Request Pydantic schemas for the app/ FastAPI layer."""
from pydantic import BaseModel, Field


class StateInput(BaseModel):
    latency: float = Field(..., ge=0, description="Normalized latency [0, 1]")
    cost: float = Field(..., ge=0, description="Normalized cost [0, 1]")
    success_rate: float = Field(..., ge=0, le=1, description="Rolling success rate [0, 1]")
    system_load: float = Field(..., ge=0, description="System load factor [0, 3]")
    previous_action: int = Field(..., ge=0, le=3, description="Previous action {0,1,2,3}")
    api_name: str = Field(..., min_length=1, description="Target API name")


class SimulateRequest(BaseModel):
    api_name: str = Field(..., min_length=1, description="API to simulate")
    retry: bool = Field(default=False, description="Whether this is a retry attempt")
