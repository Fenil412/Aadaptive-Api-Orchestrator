# Requirements Document

## Introduction

A production-ready Reinforcement Learning-Based Intelligent API Orchestration System. A PPO (Proximal Policy Optimization) agent learns to optimally route and orchestrate API calls across 16 simulated APIs spanning e-commerce, user services, logistics, financial, and external categories. The system exposes a FastAPI backend with async PostgreSQL/SQLite persistence and a React/Vite frontend dashboard for real-time monitoring, simulation, training control, and performance comparison.

## Glossary

- **Orchestrator**: The FastAPI backend application that coordinates RL decisions and API calls.
- **RL_Agent**: The PPO-based reinforcement learning agent that selects routing actions.
- **API_Simulator**: The component that simulates responses from the 16 modeled APIs.
- **RL_Engine**: The standalone training module (`rl_engine/`) with no dependency on `app/` imports.
- **RL_Env**: The Gymnasium-compatible environment used for RL training and inference.
- **PPO_Model**: The trained Stable-Baselines3 PPO model persisted as a `.zip` file.
- **DB_Service**: The async SQLAlchemy service layer for database read/write operations.
- **Training_Runner**: The script or service that initiates and monitors PPO training runs.
- **Dashboard**: The React frontend application providing UI for all system interactions.
- **API_Log**: A persisted record of a single API call including latency, cost, and success.
- **RL_Decision**: A persisted record of a single RL agent action and its associated reward.
- **Training_Metrics**: Persisted per-checkpoint statistics from a training run.
- **System_Load**: A float multiplier (0.5–3.0) representing current request volume pressure.
- **Episode**: A fixed-length sequence of RL steps (50 steps or 3 consecutive failures).
- **Action**: One of four discrete choices: `call_api` (0), `retry` (1), `skip` (2), `switch_provider` (3).

---

## Requirements

### Requirement 1: API Simulation

**User Story:** As a developer, I want the system to simulate 16 realistic APIs with configurable latency, cost, and reliability profiles, so that the RL agent has a meaningful environment to learn from.

#### Acceptance Criteria

1. THE API_Simulator SHALL expose 16 named APIs across five categories: `ecommerce` (payment_A, payment_B, inventory, cart, order, recommendation), `user` (authentication, profile, preferences), `logistics` (delivery, tracking, warehouse), `financial` (fraud_detection, billing), and `external` (external_payment, external_shipping).
2. WHEN an API call is made, THE API_Simulator SHALL compute latency by sampling uniformly from the API's configured `latency_range` and multiplying by a `system_load` factor.
3. WHEN `system_load` exceeds 1.5, THE API_Simulator SHALL reduce the API's base `success_prob` by 0.10, clamped to a minimum of 0.01.
4. WHEN a retry is requested (`is_retry=True`), THE API_Simulator SHALL increase latency by 10%, increase cost by 50%, and increase `success_prob` by 0.05.
5. WHEN a simulated API call fails, THE API_Simulator SHALL set the returned latency to `max_latency * system_load`.
6. IF a requested `category` or `api_name` is not found in the ecosystem, THEN THE API_Simulator SHALL return a response with `success=False` and an `"API not found"` error message.
7. THE API_Simulator SHALL return a response dict containing `api_name`, `latency` (rounded to 2 decimal places), `cost` (rounded to 4 decimal places), and `success`.

---

### Requirement 2: RL Environment (App-Integrated)

**User Story:** As an ML engineer, I want a Gymnasium-compatible RL environment integrated with the API simulator, so that the agent can learn orchestration policies using real API profiles.

#### Acceptance Criteria

1. THE RL_Env SHALL implement `gymnasium.Env` with an observation space of `Box(shape=(5,), dtype=float32)` representing `[latency_norm, cost_norm, success_rate, system_load, previous_action_norm]`.
2. THE RL_Env SHALL implement an action space of `Discrete(4)` mapping to `call_api` (0), `retry` (1), `skip` (2), and `switch_provider` (3).
3. WHEN action `skip` (2) is taken, THE RL_Env SHALL assign a reward of -5 and mark the step as successful without calling the API_Simulator.
4. WHEN action `retry` (1) is taken, THE RL_Env SHALL call the API_Simulator with `is_retry=True` and apply an additional penalty of -10 to the computed reward.
5. WHEN an API call succeeds, THE RL_Env SHALL compute reward as `+100 - (latency_norm * 10) - (cost * 5)`.
6. WHEN an API call fails, THE RL_Env SHALL compute reward as `-50 - (latency_norm * 10) - (cost * 5)`.
7. WHEN 3 consecutive failures occur within an episode, THE RL_Env SHALL terminate the episode early.
8. WHEN the step count reaches 50, THE RL_Env SHALL truncate the episode.
9. WHEN `reset()` is called, THE RL_Env SHALL initialize `system_load` to a random value in [0.5, 2.5] and set `success_rate` to 1.0.

---

### Requirement 3: RL Engine (Standalone)

**User Story:** As an ML engineer, I want a fully standalone RL engine module with no dependency on the app layer, so that training can be run independently without importing application code.

#### Acceptance Criteria

1. THE RL_Engine SHALL implement `gymnasium.Env` with an observation space of `Box(shape=(6,), dtype=float32)` representing `[latency, cost, success_rate, request_load, time_of_day, error_rate]`, all normalized to [0.0, 1.0].
2. THE RL_Engine SHALL implement an action space of `Discrete(4)` mapping to four provider profiles: Provider A (fast/expensive), Provider B (balanced), Provider C (slow/cheap), and Fallback/Cache.
3. THE RL_Engine SHALL contain zero imports from the `app/` package, ensuring it can be executed as a standalone Python module.
4. WHEN `step()` is called, THE RL_Engine SHALL simulate provider response using the selected provider's latency range, cost range, and base success rate, degraded by current `request_load`.
5. WHEN `get_episode_summary()` is called, THE RL_Engine SHALL return a dict containing `total_steps`, `total_reward`, `avg_reward`, `avg_latency`, `avg_cost`, `success_rate`, and `provider_distribution`.
6. THE RL_Engine SHALL register the environment with Gymnasium under the id `"APIRouting-v0"`.

---

### Requirement 4: PPO Training

**User Story:** As an ML engineer, I want to train a PPO agent on the RL environment with configurable hyperparameters and automatic metric persistence, so that I can iterate on model quality.

#### Acceptance Criteria

1. THE Training_Runner SHALL use `stable_baselines3.PPO` with `MlpPolicy` for all training runs.
2. WHEN training is initiated, THE Training_Runner SHALL accept configurable parameters: `total_timesteps` (default 50,000), `learning_rate` (default 3e-4), `n_steps` (default 2048), `batch_size` (default 64), `n_epochs` (default 10), and `gamma` (default 0.99).
3. WHEN training completes, THE Training_Runner SHALL save the trained model as a `.zip` file to the configured `save_dir`.
4. WHEN training completes, THE Training_Runner SHALL save per-checkpoint metrics (timesteps, mean_reward, mean_latency, mean_cost, success_rate, timestamps) to `models/training_metrics.json`.
5. WHERE TensorBoard logging is enabled, THE Training_Runner SHALL write logs to the configured `tensorboard_log` directory.
6. THE Training_Runner in `rl_engine/train.py` SHALL operate exclusively on `rl_engine.env.APIRoutingEnv` with no imports from `app/`.
7. THE Training_Runner in `app/rl/train.py` SHALL operate on `app.rl.env.MicroserviceOrchestrationEnv`.

---

### Requirement 5: RL Agent Service

**User Story:** As a backend developer, I want an RL agent service that loads the trained PPO model and provides routing decisions, so that the API can serve real-time orchestration recommendations.

#### Acceptance Criteria

1. WHEN the RL_Agent is initialized, THE RL_Agent SHALL attempt to load the PPO model from the path specified in `settings.RL_MODEL_PATH`.
2. IF the model file is not found at initialization, THEN THE RL_Agent SHALL log a warning and fall back to returning random actions in [0, 3].
3. WHEN `get_action(state_array)` is called with a valid 5-element state list, THE RL_Agent SHALL return a deterministic integer action in [0, 3].
4. WHEN `get_action()` is called and the model is not loaded, THE RL_Agent SHALL attempt to reload the model before falling back to random action selection.

---

### Requirement 6: Database Persistence

**User Story:** As a backend developer, I want all API calls, RL decisions, and training metrics persisted to a database with async I/O, so that the system can support concurrent requests without blocking.

#### Acceptance Criteria

1. THE DB_Service SHALL use async SQLAlchemy with `asyncpg` as the primary driver for PostgreSQL connections.
2. WHERE a PostgreSQL connection is unavailable, THE DB_Service SHALL fall back to `aiosqlite` for SQLite persistence.
3. THE DB_Service SHALL persist `api_logs` records containing: `id`, `api_name`, `latency`, `cost`, `success`, and `timestamp`.
4. THE DB_Service SHALL persist `rl_decisions` records containing: `id`, `state` (JSON), `action`, `reward`, and `timestamp`.
5. THE DB_Service SHALL persist `training_metrics` records containing: `id`, `episode`, `total_reward`, `avg_latency`, `success_rate`, and `timestamp`.
6. WHEN `fetch_logs(limit)` is called, THE DB_Service SHALL return API log records ordered by `timestamp` descending, limited to the specified count.
7. THE DB_Service SHALL expose all database operations as `async` functions compatible with FastAPI's async request handlers.

---

### Requirement 7: FastAPI Routes — API Endpoints

**User Story:** As a frontend developer, I want REST endpoints for simulating API calls, retrieving logs, and fetching statistics, so that the dashboard can display live system data.

#### Acceptance Criteria

1. THE Orchestrator SHALL expose `POST /api/simulate` accepting `{ api_category, api_name, system_load }` and returning the API_Simulator response with the persisted log id.
2. THE Orchestrator SHALL expose `GET /api/logs` accepting an optional `limit` query parameter (default 100) and returning a list of `APILogResponse` objects.
3. THE Orchestrator SHALL expose `GET /api/config` returning the full `API_ECOSYSTEM` configuration dict.
4. THE Orchestrator SHALL expose `GET /api/stats` returning aggregate statistics: total calls, overall success rate, average latency, and average cost.
5. WHEN a request to `/api/simulate` is received, THE Orchestrator SHALL persist the result to `api_logs` via DB_Service before returning the response.

---

### Requirement 8: FastAPI Routes — RL Endpoints

**User Story:** As a frontend developer, I want REST endpoints for getting RL decisions, executing orchestrated calls, and retrieving decision history, so that the dashboard can visualize agent behavior.

#### Acceptance Criteria

1. THE Orchestrator SHALL expose `POST /rl/get-decision` accepting an `RLStateInput` body and returning the RL_Agent's chosen action and its human-readable name.
2. THE Orchestrator SHALL expose `POST /rl/execute` accepting `{ state: RLStateInput, api_category, api_name }`, executing the RL decision against the API_Simulator, computing the reward, persisting the decision, and returning an `ExecuteResponse`.
3. THE Orchestrator SHALL expose `GET /rl/decisions` returning the most recent RL decision records.
4. THE Orchestrator SHALL expose `GET /rl/metrics` returning the contents of `models/training_metrics.json` if it exists, or an empty metrics structure if not.
5. WHEN `/rl/execute` is called, THE Orchestrator SHALL persist the RL decision to `rl_decisions` via DB_Service before returning the response.

---

### Requirement 9: FastAPI Routes — UI Endpoints

**User Story:** As a frontend developer, I want dedicated UI data endpoints that aggregate information for dashboard views, so that the frontend can fetch pre-composed data with a single request.

#### Acceptance Criteria

1. THE Orchestrator SHALL expose `GET /ui/dashboard` returning a combined payload of recent API logs, recent RL decisions, and aggregate stats.
2. THE Orchestrator SHALL expose `GET /ui/live-feed` returning the most recent API log and RL decision entries suitable for a real-time feed component.
3. THE Orchestrator SHALL expose `GET /ui/performance` returning time-series performance data (latency, cost, success rate over time) derived from persisted logs.

---

### Requirement 10: Pydantic Schemas

**User Story:** As a backend developer, I want all request and response bodies defined with Pydantic models using Field() constraints, so that the API validates inputs automatically and generates accurate OpenAPI documentation.

#### Acceptance Criteria

1. THE Orchestrator SHALL define `RLStateInput` with fields: `latency: float = Field(ge=0.0, le=1.0)`, `cost: float = Field(ge=0.0, le=1.0)`, `success_rate: float = Field(ge=0.0, le=1.0)`, `system_load: float = Field(ge=0.0, le=3.0)`, `previous_action: int = Field(ge=0, le=3)`.
2. THE Orchestrator SHALL define `APIRequest` with fields: `api_category: str = Field(min_length=1)`, `api_name: str = Field(min_length=1)`, `system_load: float = Field(ge=0.5, le=3.0)`.
3. THE Orchestrator SHALL define `ExecuteResponse` with fields: `action: int`, `action_name: str`, `api_response: dict`, `reward: float`.
4. WHEN a request body fails Pydantic validation, THE Orchestrator SHALL return HTTP 422 with a structured error body describing the violated constraints.

---

### Requirement 11: Structured Logging

**User Story:** As a DevOps engineer, I want all application components to use structured logging instead of bare print statements, so that logs can be parsed, filtered, and aggregated in production.

#### Acceptance Criteria

1. THE Orchestrator SHALL configure a root logger using Python's `logging` module with a consistent format including timestamp, level, module name, and message.
2. THE RL_Agent SHALL emit a structured `WARNING` log when the PPO model file is not found, including the expected file path.
3. THE RL_Agent SHALL emit a structured `INFO` log when the PPO model is loaded successfully.
4. THE Training_Runner SHALL emit structured `INFO` logs at each checkpoint interval including timestep count, mean reward, mean latency, mean cost, and success rate.
5. IF an unhandled exception occurs in any route handler, THEN THE Orchestrator SHALL emit a structured `ERROR` log including the exception type, message, and stack trace.
6. THE Orchestrator SHALL use no bare `print()` calls in production code paths (outside of CLI scripts and `__main__` blocks).

---

### Requirement 12: Database Seeding

**User Story:** As a developer, I want a standalone seed script that populates the database with initial data, so that the dashboard is functional immediately after setup without requiring manual API calls.

#### Acceptance Criteria

1. THE seed_db.py script SHALL be executable as a standalone Python script (`python seed_db.py`) without importing any FastAPI application instance.
2. WHEN executed, THE seed_db.py script SHALL insert a configurable number of synthetic `api_logs` records covering all 16 API names.
3. WHEN executed, THE seed_db.py script SHALL insert a configurable number of synthetic `rl_decisions` records with varied actions and rewards.
4. IF the target database tables do not exist, THEN THE seed_db.py script SHALL create them before inserting seed data.
5. THE seed_db.py script SHALL use async database operations consistent with the rest of the DB_Service layer.

---

### Requirement 13: Frontend Dashboard

**User Story:** As an end user, I want a React dashboard with pages for simulation, logs, metrics, comparison, settings, and training control, so that I can monitor and interact with the RL orchestration system from a browser.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a navigation sidebar linking to seven pages: Dashboard, Simulate, Logs, Metrics, Compare, Settings, and Train.
2. THE Dashboard SHALL communicate with the backend exclusively through `frontend/src/services/api.js`, which wraps all HTTP calls to the Orchestrator.
3. WHEN the Dashboard page loads, THE Dashboard SHALL fetch and display aggregate stats (total calls, success rate, avg latency, avg cost) and recent activity from `GET /ui/dashboard`.
4. WHEN the Simulate page is used, THE Dashboard SHALL allow the user to select an API category, API name, and system load value, submit to `POST /api/simulate`, and display the result.
5. WHEN the Logs page loads, THE Dashboard SHALL fetch and display paginated API log records from `GET /api/logs`.
6. WHEN the Metrics page loads, THE Dashboard SHALL fetch and render training metrics charts from `GET /rl/metrics`.
7. WHEN the Train page is used, THE Dashboard SHALL allow the user to initiate a training run and display live progress.
8. WHEN the Compare page is used, THE Dashboard SHALL display a side-by-side performance comparison of RL-based routing versus baseline strategies.
9. IF a backend request fails, THEN THE Dashboard SHALL display a user-visible error message rather than silently failing.

---

### Requirement 14: No Circular Imports

**User Story:** As a backend developer, I want the module dependency graph to be acyclic, so that the application starts reliably and modules can be tested in isolation.

#### Acceptance Criteria

1. THE RL_Engine module (`rl_engine/`) SHALL contain zero imports from `app/`, `api/`, or `db/` packages.
2. THE `app/rl/env.py` module SHALL import from `app/services/api_simulator.py` only, with no imports from `app/routes/`, `app/config/database.py`, or `db/`.
3. THE `app/routes/` modules SHALL import from `app/services/`, `app/schemas/`, and `app/config/` only.
4. THE `app/services/` modules SHALL import from `app/config/` and `app/models/` only, with no imports from `app/routes/`.
5. IF a circular import is introduced, THEN THE Orchestrator SHALL fail to start with a clear `ImportError` rather than silently producing incorrect behavior.

---

### Requirement 15: Parser and Serializer — Training Metrics

**User Story:** As an ML engineer, I want training metrics serialized to and deserialized from JSON reliably, so that the frontend can always render accurate training history.

#### Acceptance Criteria

1. WHEN training completes, THE Training_Runner SHALL serialize the metrics dict to `models/training_metrics.json` using `json.dump` with `indent=2`.
2. WHEN `GET /rl/metrics` is called, THE Orchestrator SHALL deserialize `models/training_metrics.json` using `json.load` and return the parsed structure.
3. THE Training_Runner SHALL format the metrics dict with keys: `timestamps` (list of ISO-8601 strings), `timesteps` (list of int), `mean_rewards` (list of float), `mean_latencies` (list of float), `mean_costs` (list of float), `success_rates` (list of float).
4. FOR ALL valid metrics dicts, serializing then deserializing SHALL produce an equivalent object (round-trip property): `json.loads(json.dumps(metrics)) == metrics`.
5. IF `models/training_metrics.json` is missing or contains invalid JSON, THEN THE Orchestrator SHALL return an empty metrics structure with all list fields set to `[]` rather than raising an exception.
