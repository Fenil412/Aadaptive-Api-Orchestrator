-- PostgreSQL Row Level Security policies
-- Run as superuser after creating tables via schema.sql

-- ---------------------------------------------------------------
-- Enable RLS on all tables
-- ---------------------------------------------------------------
ALTER TABLE api_logs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE rl_decisions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_metrics ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------
-- api_logs policies
-- ---------------------------------------------------------------
-- Allow authenticated users to read all logs
CREATE POLICY api_logs_select_policy ON api_logs
    FOR SELECT
    USING (true);

-- Allow authenticated users to insert their own logs
CREATE POLICY api_logs_insert_policy ON api_logs
    FOR INSERT
    WITH CHECK (true);

-- ---------------------------------------------------------------
-- rl_decisions policies
-- ---------------------------------------------------------------
CREATE POLICY rl_decisions_select_policy ON rl_decisions
    FOR SELECT
    USING (true);

CREATE POLICY rl_decisions_insert_policy ON rl_decisions
    FOR INSERT
    WITH CHECK (true);

-- ---------------------------------------------------------------
-- training_metrics policies
-- ---------------------------------------------------------------
CREATE POLICY training_metrics_select_policy ON training_metrics
    FOR SELECT
    USING (true);

CREATE POLICY training_metrics_insert_policy ON training_metrics
    FOR INSERT
    WITH CHECK (true);

-- ---------------------------------------------------------------
-- Grant privileges to application role (replace 'app_user' as needed)
-- ---------------------------------------------------------------
-- GRANT SELECT, INSERT ON api_logs, rl_decisions, training_metrics TO app_user;
