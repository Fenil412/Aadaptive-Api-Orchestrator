# Backend — RL API Orchestrator

FastAPI backend with a PPO reinforcement learning agent for intelligent API routing. Runs on **port 8000** (primary) and optionally **port 8001** (secondary/integrated app).

---

## Structure

```
backend/
├── api/                        # Primary FastAPI app (port 8000)
│   ├── main.py                 # App factory, lifespan, CORS, middleware
│   ├── routes.py               # Route handlers: simulate, train, evaluate, logs
│   └── models.py               # Pydantic schemas: APICallRequest, HealthResponse
│
├── app/                        # Secondary / integrated app (port 8001)
│   ├── main.py
│   ├── config/
│   │   ├── settings.py         # Pydantic-settings: DATABASE_URL, RL_MODEL_PATH, …
│   │   └── database.py         # Async SQLAlchemy engine, get_db() dependency
│   ├── models/
│   │   └── db_models.py        # ORM: APILog, RLDecision, TrainingMetrics, TrainingRun, EvaluationResult
│   ├── schemas/
│   │   ├── request_schema.py   # SimulateRequest, StateInput
│   │   └── response_schema.py  # DecisionResponse, ExecuteResponse
│   ├── routes/
│   │   ├── api_routes.py       # /api/simulate, /api/logs, /api/config, /api/stats
│   │   ├── rl_routes.py        # /rl/get-decision, /rl/execute, /rl/decisions, /rl/metrics
│   │   └── ui_routes.py        # /ui/dashboard, /ui/live-feed, /ui/performance
│   ├── services/
│   │   ├── api_simulator.py    # 16-API simulator across 5 categories
│   │   ├── rl_agent.py         # RLAgent: PPO inference with confidence scores
│   │   └── db_service.py       # Async ORM CRUD operations
│   ├── utils/
│   │   ├── helpers.py          # normalize(), get_timestamp(), safe_float(), compute_reward()
│   │   └── seed_db.py          # Standalone DB seeding script
│   └── rl/
│       ├── env.py              # MicroserviceOrchestrationEnv (5-dim Gymnasium env)
│       └── train.py            # train_rl_agent()
│
├── rl_engine/                  # Standalone RL engine (zero app/ imports)
│   ├── env.py                  # APIRoutingEnv (6-dim, 4 provider profiles)
│   ├── train.py                # train_model() → models/ppo_api_orchestrator.zip
│   └── evaluate.py             # PPO vs 5 static strategies
│
├── db/                         # Raw psycopg2 layer (used by api/routes.py)
│   ├── connection.py           # ThreadedConnectionPool + all DB functions
│   └── schema.sql              # PostgreSQL DDL
│
├── models/                     # Persisted artifacts (git-ignored except .gitkeep)
│   ├── ppo_api_orchestrator.zip
│   ├── training_metrics.json
│   └── evaluation_results.json
│
└── requirements.txt
```

---

## Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` from the repo root to `backend/.env` and configure:

```env
DATABASE_URL=sqlite+aiosqlite:///./api_orchestrator.db
RL_MODEL_PATH=models/ppo_api_orchestrator.zip
MODEL_PATH=models/ppo_api_orchestrator.zip
APP_ENV=development
LOG_LEVEL=INFO
```

For PostgreSQL (e.g. Supabase):
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

---

## Running

### Train the PPO model first

```bash
# From backend/
python -m rl_engine.train
```

This saves `models/ppo_api_orchestrator.zip` and `models/training_metrics.json`.

### Start the primary server (port 8000)

```bash
uvicorn api.main:app --port 8000 --reload
```

### Start the secondary server (port 8001, optional)

```bash
uvicorn app.main:app --port 8001 --reload
```

### Seed the database (optional)

```bash
python -m app.utils.seed_db
```

### Run evaluation

```bash
python -m rl_engine.evaluate --model models/ppo_api_orchestrator.zip --episodes 20
```

---

## API Endpoints

All served from port 8000. Full interactive docs at `http://localhost:8000/docs`.

### Primary (`api/routes.py`)

| Method | Path                  | Description                                    |
|--------|-----------------------|------------------------------------------------|
| GET    | `/health`             | Health check — model loaded, DB status         |
| POST   | `/simulate-api`       | PPO routing decision + simulated API result    |
| GET    | `/api-logs`           | Recent API call logs (`?limit=100`)            |
| GET    | `/dashboard-stats`    | Aggregate: total calls, success rate, avg latency/cost |
| POST   | `/train`              | Trigger PPO training (`?timesteps=50000`)      |
| GET    | `/training-metrics`   | Read `models/training_metrics.json`            |
| POST   | `/evaluate`           | Run PPO vs 5 strategies (`?n_episodes=20`)     |
| GET    | `/evaluation-results` | Read `models/evaluation_results.json`          |

### API Simulation (`/api/*`)

| Method | Path           | Description                                    |
|--------|----------------|------------------------------------------------|
| POST   | `/api/simulate`| Simulate one of 16 APIs, persist log to DB     |
| GET    | `/api/logs`    | Fetch persisted logs (`?limit=100&api_name=…`) |
| GET    | `/api/config`  | Full API ecosystem configuration               |
| GET    | `/api/stats`   | Aggregate stats from DB logs                   |

### RL Agent (`/rl/*`)

| Method | Path               | Description                                         |
|--------|--------------------|-----------------------------------------------------|
| POST   | `/rl/get-decision` | Get RL action + confidence (no execution)           |
| POST   | `/rl/execute`      | Full pipeline: RL → simulate → reward → persist     |
| GET    | `/rl/decisions`    | Recent RL decisions from DB (`?limit=50`)           |
| GET    | `/rl/metrics`      | Training metrics from DB (`?limit=20`)              |

### UI Data (`/ui/*`)

| Method | Path              | Description                                      |
|--------|-------------------|--------------------------------------------------|
| GET    | `/ui/dashboard`   | Combined stats + recent decisions                |
| GET    | `/ui/live-feed`   | Most recent RL decisions for real-time feed      |
| GET    | `/ui/performance` | Time-series training metrics (`?limit=50`)       |

---

## RL Environment

### `rl_engine/env.py` — `APIRoutingEnv`

| Dimension | Observation       | Range  |
|-----------|-------------------|--------|
| 0         | current_latency   | [0, 1] |
| 1         | current_cost      | [0, 1] |
| 2         | success_rate      | [0, 1] |
| 3         | request_load      | [0, 1] |
| 4         | time_of_day       | [0, 1] |
| 5         | error_rate        | [0, 1] |

| Action | Provider       | Latency       | Cost          | Success |
|--------|----------------|---------------|---------------|---------|
| 0      | Provider A     | [0.05, 0.25]  | [0.60, 0.90]  | 0.95    |
| 1      | Provider B     | [0.20, 0.50]  | [0.30, 0.60]  | 0.90    |
| 2      | Provider C     | [0.40, 0.80]  | [0.05, 0.30]  | 0.85    |
| 3      | Fallback/Cache | [0.01, 0.05]  | [0.00, 0.05]  | 0.70    |

Reward: `0.3*(1-latency) + 0.3*(1-cost) + 0.4*success - 1.0*(1-success)`

### `app/rl/env.py` — `MicroserviceOrchestrationEnv`

5-dim state: `[latency, cost, success_rate, system_load, previous_action]`  
Actions: `call_api(0)`, `retry(1)`, `skip(2)`, `switch_provider(3)`

---

## Simulated APIs

16 APIs across 5 categories:

| Category   | APIs                                                              |
|------------|-------------------------------------------------------------------|
| ecommerce  | payment_A, payment_B, inventory, cart, order, recommendation     |
| user       | authentication, profile, preferences                              |
| logistics  | delivery, tracking, warehouse                                     |
| financial  | fraud_detection, billing                                          |
| external   | external_payment, external_shipping                               |
