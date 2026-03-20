import random
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.database import SessionLocal, Base, engine
from app.models.db_models import APILog, RLDecision, TrainingMetrics, TrainingRun, EvaluationResult
from app.services.api_simulator import API_ECOSYSTEM
from app.utils.helpers import action_to_string
import json

def seed_database(num_logs=500, num_decisions=500, num_metrics=100):
    print("Rebuilding database schema securely...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Seeding database...")
    
    # Generate API Logs
    now = datetime.now()
    api_list = [
        ("ecommerce", "payment_A"), ("ecommerce", "payment_B"), ("ecommerce", "inventory"),
        ("user", "authentication"), ("user", "profile"),
        ("logistics", "delivery"), ("logistics", "tracking"),
        ("financial", "fraud_detection"), ("financial", "billing")
    ]
    
    for i in range(num_logs):
        cat, name = random.choice(api_list)
        prof = API_ECOSYSTEM[cat][name]
        lat = random.uniform(prof["latency_range"][0], prof["latency_range"][1])
        cost = prof["cost"]
        success = random.random() < prof["success_prob"]
        
        # Distribute over the last 7 days
        timestamp = now - timedelta(days=random.uniform(0, 7))
        
        log = APILog(
            api_name=f"{cat}.{name}",
            latency=lat,
            cost=cost,
            success=success,
            timestamp=timestamp
        )
        db.add(log)
        
    db.commit()
    print(f"Inserted {num_logs} API Logs.")
    
    # Generate RL Decisions
    for i in range(num_decisions):
        timestamp = now - timedelta(days=random.uniform(0, 7))
        action = random.randint(0, 3)
        state_dict = {
            "latency": random.random(),
            "cost": random.random(),
            "success_rate": random.uniform(0.7, 1.0),
            "system_load": random.uniform(0.5, 2.5),
            "previous_action": random.randint(0, 3)
        }
        
        # Artificial reward based on action vs latency logic to look real
        reward = random.uniform(20, 100) if action in [0, 1] else random.uniform(-20, 50)
        
        decision = RLDecision(
            state=state_dict,
            action=str(action),
            reward=reward,
            timestamp=timestamp
        )
        db.add(decision)
        
    db.commit()
    print(f"Inserted {num_decisions} RL Decisions.")
    
    # Generate Training Metrics
    # simulate an increasing reward curve over episodes
    for episode in range(1, num_metrics + 1):
        progress = episode / num_metrics
        # Base logic: Reward goes up, latency goes down, success_rate goes up as training progresses
        total_reward = 2000 + (progress * 6000) + random.uniform(-500, 500)
        avg_latency = max(20.0, 300.0 - (progress * 250) + random.uniform(-20, 20))
        success_rate = min(1.0, 0.6 + (progress * 0.38) + random.uniform(-0.05, 0.05))
        
        timestamp = now - timedelta(hours=num_metrics - episode)
        
        metric = TrainingMetrics(
            episode=episode * 10,
            total_reward=total_reward,
            avg_latency=avg_latency,
            success_rate=success_rate,
            timestamp=timestamp
        )
        db.add(metric)
        
    db.commit()
    print(f"Inserted {num_metrics} Training Metrics lines.")

    # Generate Training Runs
    run = TrainingRun(
        total_episodes=num_metrics,
        best_reward=total_reward, # last highest reward in logic
        model_path="/rl/model/ppo_model.zip",
        timestamp=now
    )
    db.add(run)
    db.commit()
    print("Inserted 1 Training Run.")

    # Generate Evaluation Results
    evals = [
        {"strategy": "PPO RL", "score": 95, "success_rate": 0.98, "avg_latency": 120, "avg_cost": 0.05},
        {"strategy": "Fastest", "score": 80, "success_rate": 0.95, "avg_latency": 50, "avg_cost": 0.20},
        {"strategy": "Cheapest", "score": 75, "success_rate": 0.85, "avg_latency": 500, "avg_cost": 0.01},
        {"strategy": "Balanced", "score": 88, "success_rate": 0.92, "avg_latency": 250, "avg_cost": 0.10},
    ]

    for ev in evals:
        result = EvaluationResult(
            strategy=ev["strategy"],
            avg_reward=ev["score"],
            avg_latency=ev["avg_latency"],
            avg_cost=ev["avg_cost"],
            success_rate=ev["success_rate"],
            timestamp=now
        )
        db.add(result)
    db.commit()
    print("Inserted 4 Evaluation Results.")
    
    db.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_database()
