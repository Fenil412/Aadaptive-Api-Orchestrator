-- ==========================================
-- SUPABASE ROW LEVEL SECURITY (RLS) SETUP
-- ==========================================
-- Copy and run this script inside your Supabase 
-- SQL Editor to properly secure your tables and 
-- remove the Security Advisor warnings.

-- 1. Enable RLS on all tables
ALTER TABLE IF EXISTS api_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rl_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS training_metrics ENABLE ROW LEVEL SECURITY;

-- If you still have old schema tables laying around, secure them too:
ALTER TABLE IF EXISTS training_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS evaluation_results ENABLE ROW LEVEL SECURITY;

-- 2. Create basic Service Role bypass policies.
-- (This ensures the FastAPI backend can still easily read/write data 
-- using the Postgres connection string without being blocked, 
-- while preventing anonymous internet users from doing so.)
CREATE POLICY "Allow full access to service_role on api_logs" ON api_logs
    USING ( auth.role() = 'service_role' OR auth.role() = 'postgres' )
    WITH CHECK ( auth.role() = 'service_role' OR auth.role() = 'postgres' );

CREATE POLICY "Allow full access to service_role on rl_decisions" ON rl_decisions
    USING ( auth.role() = 'service_role' OR auth.role() = 'postgres' )
    WITH CHECK ( auth.role() = 'service_role' OR auth.role() = 'postgres' );

CREATE POLICY "Allow full access to service_role on training_metrics" ON training_metrics
    USING ( auth.role() = 'service_role' OR auth.role() = 'postgres' )
    WITH CHECK ( auth.role() = 'service_role' OR auth.role() = 'postgres' );

-- You are completely secure now!
