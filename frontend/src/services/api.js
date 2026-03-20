/**
 * Axios API client — single backend on port 8000.
 * All routes (simulation, RL, UI, training, evaluation) served from one server.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Health ───────────────────────────────────────────────────────────────────
export const healthCheck = () => api.get('/health');

// ── Simulation (primary rl_engine routes) ────────────────────────────────────
export const simulateAPI = (state) => api.post('/simulate-api', state);

// ── Training ─────────────────────────────────────────────────────────────────
export const trainModel = (timesteps = 50000) =>
  api.post(`/train?timesteps=${timesteps}`);

// ── Metrics & Evaluation ─────────────────────────────────────────────────────
export const getTrainingMetrics = () => api.get('/training-metrics');
export const getEvaluationResults = () => api.get('/evaluation-results');
export const runEvaluation = (episodes = 20) =>
  api.post(`/evaluate?n_episodes=${episodes}`);

// ── Logs & Stats ─────────────────────────────────────────────────────────────
export const getAPILogs = (limit = 100, apiName = null) =>
  api.get('/api-logs', { params: { limit, ...(apiName ? { api_name: apiName } : {}) } });

export const getDashboardStats = () => api.get('/dashboard-stats');

// ── RL Routes (/rl prefix from app/routes/rl_routes.py) ──────────────────────
export const getRLDecisions = (limit = 50) =>
  api.get('/rl/decisions', { params: { limit } });

export const getRLMetrics = (limit = 20) =>
  api.get('/rl/metrics', { params: { limit } });

/**
 * Full pipeline: state → RL decision → simulate → reward → log
 * Body: { latency, cost, success_rate, system_load, previous_action, api_name }
 */
export const executeRLPipeline = (stateInput) =>
  api.post('/rl/execute', stateInput);

export const getRLDecision = (stateInput) =>
  api.post('/rl/get-decision', stateInput);

// ── UI Routes (/ui prefix from app/routes/ui_routes.py) ──────────────────────
export const getUIDashboard = () => api.get('/ui/dashboard');
export const getLiveFeed = () => api.get('/ui/live-feed');
export const getPerformance = (limit = 50) =>
  api.get('/ui/performance', { params: { limit } });

// ── API Config & Stats (/api prefix from app/routes/api_routes.py) ────────────
export const getAPIConfig = () => api.get('/api/config');
export const getAPIStats = (limit = 500) =>
  api.get('/api/stats', { params: { limit } });

export const simulateAppAPI = (body) => api.post('/api/simulate', body);
export const getAppLogs = (limit = 100, apiName = null) =>
  api.get('/api/logs', {
    params: { limit, ...(apiName ? { api_name: apiName } : {}) },
  });

export default api;
