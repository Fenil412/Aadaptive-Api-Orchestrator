-- RL API Orchestration — Database Schema
-- Compatible with PostgreSQL and SQLite

-- ---------------------------------------------------------------
-- api_logs
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_logs (
    id           SERIAL PRIMARY KEY,
    api_name     TEXT        NOT NULL,
    latency      REAL        NOT NULL,
    cost         REAL        NOT NULL,
    success      BOOLEAN     NOT NULL,
    system_load  REAL,
    action_taken TEXT,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name  ON api_logs (api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_success   ON api_logs (success);

-- ---------------------------------------------------------------
-- rl_decisions
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rl_decisions (
    id        SERIAL PRIMARY KEY,
    state     JSONB,
    action    INTEGER     NOT NULL,
    reward    REAL,
    api_name  TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rl_decisions_timestamp ON rl_decisions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rl_decisions_api_name  ON rl_decisions (api_name);

-- ---------------------------------------------------------------
-- training_metrics
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_metrics (
    id           SERIAL PRIMARY KEY,
    episode      INTEGER     NOT NULL,
    total_reward REAL        NOT NULL,
    avg_latency  REAL,
    success_rate REAL,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_metrics_timestamp ON training_metrics (timestamp DESC);
