# RL-based API Orchestration System

Dynamic microservice orchestration utilizing Reinforcement Learning. Rather than static load-balancing rules or hard-coded fallback mechanisms, the backend uses a Proximal Policy Optimization (PPO) agent that continually observes:
- Latency (ms)
- Cost ($)
- Success Rate (Probability distributions)
- System Load

The RL Agent actively chooses whether to:
- Call the default requested endpoint.
- Skip processing.
- Issue an immediate retry inside an active connection window.
- Switch to a Fallback/Alternative provider.

The agent's decision matrix stores decisions straight to PostgreSQL via SQLAlchemy.

## Running the Application

### Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run DB migrations/initial loading automatically
uvicorn app.main:app --reload --port 8001
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```

For detailed views, please see `backend/README.md` and `frontend/README.md`.