from pydantic import BaseModel
from typing import Optional, List

class RLStateInput(BaseModel):
    latency: float
    cost: float
    success_rate: float
    system_load: float
    previous_action: int

class APIRequest(BaseModel):
    api_category: str
    api_name: str
    system_load: float

class ExecuteRequest(BaseModel):
    state: RLStateInput
    api_category: str
    api_name: str
