from sqlalchemy.orm import Session
from app.models.db_models import APILog, RLDecision, TrainingMetrics

def insert_api_log(db: Session, api_name: str, latency: float, cost: float, success: bool):
    log = APILog(api_name=api_name, latency=latency, cost=cost, success=success)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def insert_rl_decision(db: Session, state: dict, action: str, reward: float):
    decision = RLDecision(state=state, action=action, reward=reward)
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision

def insert_training_metrics(db: Session, episode: int, total_reward: float, avg_latency: float, success_rate: float):
    metric = TrainingMetrics(episode=episode, total_reward=total_reward, avg_latency=avg_latency, success_rate=success_rate)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

def fetch_logs(db: Session, limit: int = 100):
    return db.query(APILog).order_by(APILog.timestamp.desc()).limit(limit).all()
