# Implementation Plan: RL-Based Intelligent API Orchestration System

## Overview

Implement the full-stack RL API orchestration system incrementally, starting from the foundation (utilities, config, DB) and building up through the RL engine, services, routes, entry points, and finally the React frontend. Each task builds on the previous and ends with all code wired together.

All files are created or modified exclusively inside `backend/` and `frontend/`.

## Tasks

- [ ] 1. Core utilities and exception helpers
  - [ ] 1.1 Implement `backend/app/utils/helpers.py`
    - Add `normalize(value, min_val, max_val)` clamp-and-normalize utility
    - Add `get_timestamp()` returning ISO 8601 UTC string
    - Add `safe_float(value, default=0.0)` for safe numeric coercion
    - _Requirements: 1.1, 3.1_

- [ ] 2. Settings and configuration
  - [ ] 2.1 Implement `backend/app/config/settings.py`
    - Define `Settings` class reading `DATABASE_URL`, `PROJECT_NAME`, `RL_MODEL_PATH` from `.env`
    - Export a singleton `settings` instance
    - _Requirements: 4.1_
  - [ ] 2.2 Implement `backend/app/config/database.py`
    - Create SQLAlchemy engine from `settings.DATABASE_URL`
    - Handle `check_same_thread=False` for SQLite
    - Expose `SessionLocal` factory and `get_db()` dependency
    - _Requirements: 4.1_

- [ ] 3. Database layer
  - [ ] 3.1 Implement `backend/app/models/db_models.py`
    - Define `APILog`, `RLDecision`, `TrainingMetrics`, `TrainingRun`, `EvaluationResult` ORM models using `declarative_base`
    - Call `Base.metadata.create_all(bind=engine)` on import
    - _Requirements: 4.1_
  - [ ] 3.2 Implement `backend/db/schema.sql`
    - Write DDL for `api_logs`, `rl_decisions`, `training_runs`, `evaluation_results` tables matching the data model in the design
    - _Requirements: 4.1, 4.2_
  - [ ] 3.3 Implement `backend/db/__init__.py` and `backend/db/connection.py`
    - `connection.py`: raw `psycopg2` connection pool with context manager
    - Expose `insert_api_log`, `get_api_logs`, `insert_rl_decision`, `get_rl_decisions`, `insert_training_run`, `complete_training_run`, `insert_evaluation_result`, `get_evaluation_results`, `get_dashboard_stats`
    - `__init__.py`: re-export public symbols
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ] 3.4 Implement `backend/app/services/db_service.py`
    - Synchronous SQLAlchemy ORM operations: `insert_api_log`, `insert_rl_decision`, `insert_training_metrics`, `fetch_logs`
    - Propagate SQLAlchemy exceptions to the caller
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ]* 3.5 Write property test for DB persistence round-trip
    - **Property 7: DB Persistence Round-Trip**
   