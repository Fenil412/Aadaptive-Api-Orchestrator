# Backend - RL API Orchestrator

This is a FastAPI-based backend that uses Reinforcement Learning (PPO algorithm) to dynamically route microservice calls.

## Architecture Followed
- **app/config/settings.py**: Loads variables from `.env`.
- **app/schemas**: Pydantic models for incoming and outgoing data.
- **app/services/db_service.py**: SQLAlchemy engine, Session, and declarative models synced directly.
- **app/services/api_simulator.py**: Simulates 16 different API endpoints mimicking a true load-balanced system.
- **app/rl/env.py / app/rl/train.py / app/services/rl_agent.py**: Holds the complete RL ecosystem.
- **app/routes**: Separate routing files for clean implementation.
- **app/main.py**: The central entry point.

## Setup Instructions

1. **Environment Config**: Update the `DATABASE_URL` in `.env` to point to a valid Postgres instance (e.g. Supabase).
2. **Setup virtual env**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Train Model**:
   ```bash
   python -m app.rl.train
   ```
4. **Start Application**:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
