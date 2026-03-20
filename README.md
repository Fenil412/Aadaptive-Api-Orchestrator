# RL-Based Intelligent API Orchestration System

A full-stack application where a PPO (Proximal Policy Optimization) reinforcement learning agent learns to optimally route API calls across 16 simulated microservices. The agent observes real-time system conditions and selects the best action — call, retry, skip, or switch provider — to maximize reliability while minimizing latency and cost.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [File Structure](#file-structure)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Modules](#modules)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    React Frontend  (port 5173)                      │
│   Dashboard │ Simulate │ Train │ Logs │ Compare │ Metrics │ Settings│
│                   frontend/src/services/api.js                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Primary FastAPI App  backend/api/  (port 8000)         │
│                                                                     │
│  api/main.py ──► api/routes.py ──► rl_engine/  (standalone)        │
│                       │                                             │
│                       ├──► /simulate-api   (PPO routing decision)  │
│                       ├──► /train          (trigger PPO training)   │
│                       ├──► /evaluate       (strategy comparison)    │
│                       ├──► /training-metrics                        │
│                       ├──► /evaluation-results                      │
│                       ├──► /api-logs                                │
│                       └──► /dashboard-stats                         │
│                                                                     │
│  Also mounts app/ sub-routers:                                      │
│       /api/*   /rl/*   /ui/*                                        │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌──────────────────────────────────────────────────┐
│  rl_engine/ │  │         app/  (integrated service layer)          │
│  (standalone│  │                                                   │
│   no app/   │  │  app/routes/api_routes.py  ──► /api/simulate      │
│   imports)  │  │  app/routes/rl_routes.py   ──► /rl/execute        │
│             │  │  app/routes/ui_routes.py   ──► /ui/dashboard      │
│  env.py     │  │                                                   │
│  train.py   │  │  app/services/api_simulator.py  (16 APIs)         │
│  evaluate.py│  │  app/services/rl_agent.py       (PPO inference)   │
│             │  │  app/services/db_service.py     (ORM layer)       │
└──────┬──────┘  └──────────────────────┬───────────────────────────┘
       │                                │
       └──────────────┬─────────────────┘
                      ▼
        ┌─────────────────────────┐
        │       Persistence       │
        │                         │
        │  PostgreSQL (primary)   │
        │  SQLite    (fallback)   │
        │                         │
        │  models/*.zip  (PPO)    │
        │  models/training_       │
        │         metrics.json    │
        └─────────────────────────┘
```

### Key Design Decisions

- **Dual RL environment pattern** — `rl_engine/env.py` (`APIRoutingEnv`) uses a 6-dim state space with time-of-day patterns and 4 provider profiles. `app/rl/env.py` (`MicroserviceOrchestrationEnv`) uses a 5-dim state space with call/retry/skip/switch semantics. They are not interchangeable.
- **Standalone RL engine** — `rl_engine/` has zero imports from `app/`, `api/`, or `db/`. It can be trained and evaluated independently.
- **Graceful DB degradation** — both apps detect DB availability at startup and fall back to in-memory storage, so the system runs without a configured database.
- **Single port for frontend** — the frontend talks exclusively to port 8000. The primary app mounts all sub-routers (`/api`, `/rl`, `/ui`) from `app/` at startup.

---

## File Structure

```
.
├── README.md
├── .env.example
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── api/                          # Primary FastAPI app (port 8000)
│   │   ├── __init__.py
│   │   ├── main.py                   # App factory, lifespan, middleware
│   │   ├── routes.py                 # All primary route handlers
│   │   └── models.py                 # Pydantic request/response schemas
│   │
│   ├── app/                          # Secondary / integrated app (port 8001)
│   │   ├── __init__.py
│   │   ├── main.py                   # App factory, lifespan, middleware
│   │   │
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py           # Pydantic-settings (DATABASE_URL, RL_MODEL_PATH, …)
│   │   │   └── database.py           # Async SQLAlchemy engine, SessionLocal, get_db()
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── db_models.py          # ORM: APILog, RLDecision, TrainingMetrics, TrainingRun, EvaluationResult
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── request_schema.py     # SimulateRequest, StateInput, ExecuteRequest
│   │   │   └── response_schema.py    # DecisionResponse, ExecuteResponse
│   │   │
│   │   ├── routes/
│   │   │   ├── api_routes.py         # POST /api/simulate, GET /api/logs, /api/config, /api/stats
│   │   │   ├── rl_routes.py          # POST /rl/get-decision, /rl/execute, GET /rl/decisions, /rl/metrics
│   │   │   └── ui_routes.py          # GET /ui/dashboard, /ui/live-feed, /ui/performance
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── api_simulator.py      # 16-API simulator (5 categories)
│   │   │   ├── rl_agent.py           # RLAgent: load PPO, get_action, get_action_with_confidence
│   │   │   └── db_service.py         # Async ORM CRUD: insert_api_log, insert_rl_decision, fetch_logs, …
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── helpers.py            # normalize(), get_timestamp(), safe_float(), compute_reward(), …
│   │   │   └── seed_db.py            # Standalone DB seeding script
│   │   │
│   │   └── rl/
│   │       ├── __init__.py
│   │       ├── env.py                # MicroserviceOrchestrationEnv (5-dim, Gymnasium)
│   │       └── train.py              # train_rl_agent() using app RL env
│   │
│   ├── rl_engine/                    # Standalone RL engine (zero app/ imports)
│   │   ├── __init__.py
│   │   ├── env.py                    # APIRoutingEnv (6-dim, 4 provider profiles)
│   │   ├── train.py                  # train_model() → models/ppo_api_orchestrator.zip
│   │   └── evaluate.py               # evaluate_model() — PPO vs 5 static strategies
│   │
│   ├── db/                           # Raw psycopg2 connection layer (used by api/routes.py)
│   │   ├── __init__.py
│   │   ├── connection.py             # ThreadedConnectionPool, insert_api_log, get_dashboard_stats, …
│   │   └── schema.sql                # PostgreSQL DDL for all 4 tables
│   │
│   ├── models/                       # Persisted model artifacts
│   │   ├── .gitkeep
│   │   ├── ppo_api_orchestrator.zip  # Trained PPO model (git-ignored)
│   │   ├── training_metrics.json     # Per-checkpoint training stats
│   │   └── evaluation_results.json   # Strategy comparison results
│   │
│   └── logs/
│       └── rl_engine/                # TensorBoard event files
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── .env                          # VITE_API_BASE_URL=http://localhost:8000
    │
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        ├── index.css
        │
        ├── components/
        │   ├── ChartCard.jsx
        │   ├── LoadingSpinner.jsx
        │   ├── Sidebar.jsx
        │   └── StatCard.jsx
        │
        ├── pages/
        │   ├── Dashboard.jsx         # GET /ui/dashboard, /dashboard-stats
        │   ├── Simulate.jsx          # POST /rl/execute
        │   ├── Train.jsx             # POST /train
        │   ├── Logs.jsx              # GET /api-logs, /rl/decisions
        │   ├── Metrics.jsx           # GET /training-metrics, /rl/metrics
        │   ├── Compare.jsx           # GET /evaluation-results, POST /evaluate
        │   └── ApiExplorer.jsx       # GET /api/config
        │
        ├── services/
        │   └── api.js                # Axios client — all backend calls
        │
        └── assets/
```

---

## Database Schema

### `api_logs`
Stores every simulated API call result.

| Column      | Type        | Description                          |
|-------------|-------------|--------------------------------------|
| id          | SERIAL PK   | Auto-increment primary key           |
| timestamp   | TIMESTAMPTZ | Record creation time (default NOW()) |
| action      | INTEGER     | RL action taken (0–3)                |
| provider    | TEXT        | Provider name selected               |
| latency     | FLOAT       | Normalized latency [0, 1]            |
| cost        | FLOAT       | Normalized cost [0, 1]               |
| success     | BOOLEAN     | Whether the API call succeeded       |
| reward      | FLOAT       | Computed RL reward                   |
| state       | JSONB       | 6-element observation vector         |

### `rl_decisions`
Stores per-step RL agent decisions with full state breakdown.

| Column           | Type        | Description                        |
|------------------|-------------|------------------------------------|
| id               | SERIAL PK   |                                    |
| timestamp        | TIMESTAMPTZ |                                    |
| episode          | INTEGER     | Training episode number            |
| step             | INTEGER     | Step within episode                |
| state_latency    | FLOAT       | Latency component of state         |
| state_cost       | FLOAT       | Cost component of state            |
| state_success    | FLOAT       | Success rate component             |
| state_load       | FLOAT       | Request load component             |
| state_time       | FLOAT       | Time-of-day component              |
| state_error      | FLOAT       | Error rate component               |
| action           | INTEGER     | Action taken (0–3)                 |
| provider         | TEXT        | Provider selected                  |
| result_latency   | FLOAT       | Actual latency after action        |
| result_cost      | FLOAT       | Actual cost after action           |
| result_success   | BOOLEAN     | Actual success after action        |
| reward           | FLOAT       | Step reward                        |
| cumulative_reward| FLOAT       | Running total reward in episode    |

### `training_runs`
Tracks each PPO training run lifecycle.

| Column            | Type        | Description                              |
|-------------------|-------------|------------------------------------------|
| id                | SERIAL PK   |                                          |
| timestamp         | TIMESTAMPTZ | Run start time                           |
| completed_at      | TIMESTAMPTZ | Run end time (null if still running)     |
| total_timesteps   | INTEGER     | Configured training timesteps            |
| learning_rate     | FLOAT       | PPO learning rate used                   |
| final_avg_reward  | FLOAT       | Mean reward at end of training           |
| final_success_rate| FLOAT       | Success rate at end of training          |
| model_path        | TEXT        | Path to saved .zip model file            |
| status            | TEXT        | `running` \| `completed` \| `failed`    |

### `evaluation_results`
Stores strategy comparison results from `POST /evaluate`.

| Column             | Type        | Description                         |
|--------------------|-------------|-------------------------------------|
| id                 | SERIAL PK   |                                     |
| timestamp          | TIMESTAMPTZ |                                     |
| strategy           | TEXT        | e.g. `ppo`, `random`, `always_a`    |
| avg_episode_reward | FLOAT       | Mean reward across episodes         |
| avg_latency        | FLOAT       | Mean latency across episodes        |
| avg_cost           | FLOAT       | Mean cost across episodes           |
| success_rate       | FLOAT       | Fraction of successful steps        |
| num_episodes       | INTEGER     | Number of evaluation episodes run   |

---

## API Reference

All endpoints are served from port **8000**. Interactive docs available at `http://localhost:8000/docs`.

### Health

| Method | Path      | Description                              |
|--------|-----------|------------------------------------------|
| GET    | `/health` | System health — model loaded, DB status  |

### Simulation (Primary — `api/routes.py`)

| Method | Path              | Body / Params                                                                 | Description                                      |
|--------|-------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| POST   | `/simulate-api`   | `{ api_name, latency, cost, success_rate, request_load, time_of_day, error_rate }` | PPO routing decision + simulated API result |
| GET    | `/api-logs`       | `?limit=100`                                                                  | Recent in-memory API call logs                   |
| GET    | `/dashboard-stats`|                                                                               | Aggregate stats: total calls, success rate, avg latency/cost |

### Training & Evaluation (Primary — `api/routes.py`)

| Method | Path                  | Params              | Description                                      |
|--------|-----------------------|---------------------|--------------------------------------------------|
| POST   | `/train`              | `?timesteps=50000`  | Trigger PPO training (blocking)                  |
| GET    | `/training-metrics`   |                     | Read `models/training_metrics.json`              |
| POST   | `/evaluate`           | `?n_episodes=20`    | Run PPO vs 5 static strategies                   |
| GET    | `/evaluation-results` |                     | Read `models/evaluation_results.json`            |

### API Simulation (`/api` prefix — `app/routes/api_routes.py`)

| Method | Path           | Body / Params                                      | Description                                  |
|--------|----------------|----------------------------------------------------|----------------------------------------------|
| POST   | `/api/simulate`| `{ api_name, retry? }`                             | Simulate one of the 16 APIs, persist log     |
| GET    | `/api/logs`    | `?limit=100&api_name=payment_A`                    | Fetch persisted API logs (DB)                |
| GET    | `/api/config`  |                                                    | Full `API_ECOSYSTEM` configuration dict      |
| GET    | `/api/stats`   | `?limit=500`                                       | Aggregate stats from persisted logs          |

### RL Agent (`/rl` prefix — `app/routes/rl_routes.py`)

| Method | Path               | Body                                                                          | Description                                         |
|--------|--------------------|-------------------------------------------------------------------------------|-----------------------------------------------------|
| POST   | `/rl/get-decision` | `{ latency, cost, success_rate, system_load, previous_action }`              | Get RL action + confidence without executing        |
| POST   | `/rl/execute`      | `{ latency, cost, success_rate, system_load, previous_action, api_name }`    | Full pipeline: RL decision → simulate → reward → DB |
| GET    | `/rl/decisions`    | `?limit=50`                                                                   | Recent RL decision records from DB                  |
| GET    | `/rl/metrics`      | `?limit=20`                                                                   | Training metrics records from DB                    |

### UI Data (`/ui` prefix — `app/routes/ui_routes.py`)

| Method | Path              | Params       | Description                                              |
|--------|-------------------|--------------|----------------------------------------------------------|
| GET    | `/ui/dashboard`   |              | Combined stats + recent decisions for dashboard page     |
| GET    | `/ui/live-feed`   |              | Most recent RL decisions for real-time feed              |
| GET    | `/ui/performance` | `?limit=50`  | Time-series training metrics for performance charts      |

### RL Action Map

| Action | Integer | Meaning                                      |
|--------|---------|----------------------------------------------|
| call_api        | 0 | Call the requested API directly         |
| retry           | 1 | Retry with increased cost (+50%) and latency (+10%) |
| skip            | 2 | Skip the call (penalty: -5 reward)      |
| switch_provider | 3 | Switch to an alternative provider       |

---

## Modules

### `rl_engine/` — Standalone RL Engine

Zero imports from `app/`, `api/`, or `db/`. Can be run independently.

- **`env.py` — `APIRoutingEnv`** — Gymnasium env with 6-dim observation space `[latency, cost, success_rate, request_load, time_of_day, error_rate]` and 4 provider profiles (Fast/Expensive, Balanced, Cheap/Slow, Fallback/Cache). Reward: `0.3*(1-lat) + 0.3*(1-cost) + 0.4*success - 1.0*(1-success)`. Max 200 steps per episode.
- **`train.py` — `train_model()`** — Creates `APIRoutingEnv`, trains PPO with configurable hyperparameters, saves model to `models/ppo_api_orchestrator.zip` and metrics to `models/training_metrics.json`.
- **`evaluate.py` — `evaluate_model()`** — Runs 6 strategies (PPO, Random, Always-A, Always-B, Always-C, Round-Robin) for N episodes each and saves comparison JSON.

### `app/services/` — Integrated Service Layer

- **`api_simulator.py` — `APISimulator`** — Simulates 16 named APIs across 5 categories. `simulate_api(api_name, retry)` returns `{ api_name, latency, cost, success, system_load }`. System load scales latency; retry adds +20ms latency.
- **`rl_agent.py` — `RLAgent`** — Loads PPO from `settings.RL_MODEL_PATH`. `get_action(state)` returns action label string. `get_action_with_confidence(state)` returns action + per-action probability dict. Falls back to random if model not loaded.
- **`db_service.py`** — Async SQLAlchemy ORM CRUD. `insert_api_log`, `insert_rl_decision`, `insert_training_metrics`, `fetch_logs`, `fetch_rl_decisions`, `fetch_training_metrics`.

### `app/config/`

- **`settings.py`** — Pydantic-settings `Settings` class. Reads `DATABASE_URL`, `PROJECT_NAME`, `RL_MODEL_PATH`, `APP_ENV`, `LOG_LEVEL`, `CORS_ORIGINS` from `.env`. Exports singleton `settings`.
- **`database.py`** — Async SQLAlchemy engine (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite). Exports `engine`, `SessionLocal`, `get_db()` FastAPI dependency, `create_all_tables()`.

### `app/models/`

- **`db_models.py`** — SQLAlchemy 2.0 ORM models: `APILog`, `RLDecision`, `TrainingMetrics`, `TrainingRun`, `EvaluationResult`. All use `Base` from `app.config.database`. Tables auto-created on import via `Base.metadata.create_all`.

### `app/utils/`

- **`helpers.py`** — `normalize(value, min_val, max_val)`, `get_timestamp()`, `safe_float(value, default)`, `compute_reward(result, action)`, `normalize_state(state)`, `calculate_stats(logs)`, plus custom exceptions `SimulationError`, `ModelNotLoadedError`, `InvalidAPIError`.

### `db/` — Raw psycopg2 Layer

Used exclusively by `api/routes.py` for direct PostgreSQL access without ORM overhead.

- **`connection.py`** — `ThreadedConnectionPool` (min=1, max=10). Context manager `get_db_connection()`. Functions: `insert_api_log`, `get_api_logs`, `insert_rl_decision`, `get_rl_decisions`, `insert_training_run`, `complete_training_run`, `insert_evaluation_result`, `get_evaluation_results`, `get_dashboard_stats`.
- **`schema.sql`** — PostgreSQL DDL for all 4 tables with indexes.

### `frontend/src/`

- **`services/api.js`** — Axios client pointed at `VITE_API_BASE_URL` (default `http://localhost:8000`). Exports typed functions for every backend endpoint.
- **`pages/`** — 7 pages: `Dashboard`, `Simulate`, `Train`, `Logs`, `Metrics`, `Compare`, `ApiExplorer`. Each fetches its own data on mount.
- **`components/`** — `Sidebar`, `StatCard`, `ChartCard`, `LoadingSpinner`.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional — SQLite fallback is automatic)

### Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Edit .env — set DATABASE_URL if using PostgreSQL

# Train the PPO model (required before simulation)
python -m rl_engine.train

# Start the primary server
uvicorn api.main:app --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### Optional: Secondary App (port 8001)

```bash
cd backend
uvicorn app.main:app --port 8001 --reload
```

---

## Environment Variables

### Backend (`.env`)

| Variable         | Default                                      | Description                              |
|------------------|----------------------------------------------|------------------------------------------|
| `DATABASE_URL`   | `sqlite+aiosqlite:///./api_orchestrator.db`  | Async DB URL (asyncpg or aiosqlite)      |
| `PROJECT_NAME`   | `RL API Orchestration`                       | Application name                         |
| `RL_MODEL_PATH`  | `models/ppo_api_orchestrator.zip`            | Path to trained PPO model                |
| `MODEL_PATH`     | `models/ppo_api_orchestrator.zip`            | Alias used by primary app routes         |
| `APP_ENV`        | `development`                                | `development` or `production`            |
| `LOG_LEVEL`      | `INFO`                                       | Python logging level                     |
| `CORS_ORIGINS`   | `["http://localhost:3000","http://localhost:5173"]` | Allowed CORS origins (JSON array)  |
| `API_KEY`        | _(empty — auth disabled)_                    | Optional API key for route protection    |

### Frontend (`.env`)

| Variable              | Default                    | Description              |
|-----------------------|----------------------------|--------------------------|
| `VITE_API_BASE_URL`   | `http://localhost:8000`    | Backend base URL         |
