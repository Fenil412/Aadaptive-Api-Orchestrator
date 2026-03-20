from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.request_schema import APIRequest
from app.config.database import get_db
from app.services.db_service import insert_api_log
from app.services.api_simulator import APISimulator

router = APIRouter(prefix="/api", tags=["API Simulation"])

@router.post("/simulate-api")
def simulate_api_call(req: APIRequest, db: Session = Depends(get_db)):
    res = APISimulator.call_api(req.api_category, req.api_name, req.system_load)
    
    log = insert_api_log(
        db=db,
        api_name=f"{req.api_category}.{req.api_name}",
        latency=res["latency"],
        cost=res["cost"],
        success=res["success"]
    )
    
    return {
        "simulation": res,
        "log_id": log.id
    }
