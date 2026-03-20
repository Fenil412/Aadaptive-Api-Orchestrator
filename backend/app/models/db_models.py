from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.config.database import Base, engine

class APILog(Base):
    __tablename__ = "api_logs"
    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String, index=True)
    latency = Column(Float)
    cost = Column(Float)
    success = Column(Boolean)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class RLDecision(Base):
    __tablename__ = "rl_decisions"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(JSON)
    action = Column(String)
    reward = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class TrainingMetrics(Base):
    __tablename__ = "training_metrics"
    id = Column(Integer, primary_key=True, index=True)
    episode = Column(Integer)
    total_reward = Column(Float)
    avg_latency = Column(Float)
    success_rate = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Initialize tables
Base.metadata.create_all(bind=engine)
