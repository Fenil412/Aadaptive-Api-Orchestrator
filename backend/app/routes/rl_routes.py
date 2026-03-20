from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.request_schema import RLStateInput, ExecuteRequest
from app.schemas.response_schema import RLDecisionResponse, ExecuteResponse
from app.config.database import get_db
from app.services.db_service import insert_rl_decision, insert_api_log
from app.services.rl_agent import rl_agent_service
from app.services.api_simulator import APISimulator
from app.utils.helpers import action_to_string

router = APIRouter(prefix="/rl", tags=["RL Orchestration"])

@router.post("/get-decision", response_model=RLDecisionResponse)
def get_decision(state: RLStateInput):
    state_arr = [state.latency, state.cost, state.success_rate, state.system_load, state.previous_action]
    action = rl_agent_service.get_action(state_arr)
    action_str = action_to_string(action)
    return RLDecisionResponse(action=action, action_name=action_str)

@router.post("/execute", response_model=ExecuteResponse)
def execute_pipeline(req: ExecuteRequest, db: Session = Depends(get_db)):
    state_arr = [req.state.latency, req.state.cost, req.state.success_rate, req.state.system_load, req.state.previous_action]
    action = rl_agent_service.get_action(state_arr)
    action_str = action_to_string(action)
    
    api_res = None
    reward = 0
    actual_api = req.api_name
    
    if action == 2: # Skip
        api_res = {"api_name": actual_api, "latency": 0, "cost": 0, "success": True, "skipped": True}
        reward = -10
    else:
        is_retry = (action == 1)
        if action == 3: # Switch
            actual_api = "fallback_" + req.api_name
        
        api_res = APISimulator.call_api(req.api_category, actual_api, req.state.system_load, is_retry)
        
        lat_norm = min(api_res["latency"] / 1000.0, 1.0)
        cost = api_res["cost"]
        if api_res["success"]:
            reward = 100 - (lat_norm * 10) - (cost * 5)
        else:
            reward = -50 - (lat_norm * 10) - (cost * 5)
            
        insert_api_log(db, f"{req.api_category}.{actual_api}", api_res["latency"], api_res["cost"], api_res["success"])
        
    state_dict = req.state.model_dump()
    insert_rl_decision(db, state_dict, action_str, reward)
    
    return ExecuteResponse(
        action=action,
        action_name=action_str,
        api_response=api_res,
        reward=reward
    )
