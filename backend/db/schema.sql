-- ===========================================
-- Adaptive API Orchestrator — Database Schema
-- ===========================================
-- Run this against your Supabase/PostgreSQL database

-- ── API Logs Table ──
-- Records every API routing decision made by the system
CREATE TABLE IF NOT EXISTS api_logs (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action          INTEGER NOT NULL,
    provider        VARCHAR(50) NOT NULL,
    latency         FLOAT NOT NULL,
    cost            FLOAT NOT NULL,
    success         BOOLEAN NOT NULL,
    reward          FLOAT NOT NULL,
    state           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── RL Decisions Table ──
-- Records high-level RL model decisions and their outcomes
CREATE TABLE IF NOT EXISTS rl_decisions (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    episode         INTEGER,
    step            INTEGER NOT NULL,
    state_latency   FLOAT NOT NULL,
    state_cost      FLOAT NOT NULL,
    state_success   FLOAT NOT NULL,
    state_load      FLOAT NOT NULL,
    state_time      FLOAT NOT NULL,
    state_error     FLOAT NOT NULL,
    action          INTEGER NOT NULL,
    provider        VARCHAR(50) NOT NULL,
    result_latency  FLOAT NOT NULL,
    result_cost     FLOAT NOT NULL,
    result_success  BOOLEAN NOT NULL,
    reward          FLOAT NOT NULL,
    cumulative_reward FLOAT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Training Runs Table ──
-- Records metadata about each training session
CREATE TABLE IF NOT EXISTS training_runs (
    id              SERIAL PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    total_timesteps INTEGER NOT NULL,
    learning_rate   FLOAT NOT NULL,
    final_avg_reward FLOAT,
    final_success_rate FLOAT,
    model_path      VARCHAR(255),
    status          VARCHAR(20) DEFAULT 'running',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Evaluation Results Table ──
-- Records comparison results between strategies
CREATE TABLE IF NOT EXISTS evaluation_results (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy        VARCHAR(50) NOT NULL,
    avg_episode_reward FLOAT NOT NULL,
    avg_latency     FLOAT NOT NULL,
    avg_cost        FLOAT NOT NULL,
    success_rate    FLOAT NOT NULL,
    num_episodes    INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes for Performance ──
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_provider ON api_logs(provider);
CREATE INDEX IF NOT EXISTS idx_rl_decisions_timestamp ON rl_decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rl_decisions_episode ON rl_decisions(episode);
CREATE INDEX IF NOT EXISTS idx_evaluation_strategy ON evaluation_results(strategy);
