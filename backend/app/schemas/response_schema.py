from pydantic import BaseModel
from typing import Optional, Any

class APILogResponse(BaseModel):
    id: int
    api_name: str
    latency: float
    cost: float
    success: bool
    timestamp: Any

class RLDecisionResponse(BaseModel):
    action: int
    action_name: str

class ExecuteResponse(BaseModel):
    action: int
    action_name: str
    api_response: dict
    reward: float
