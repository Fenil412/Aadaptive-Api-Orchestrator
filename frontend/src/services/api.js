import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Health ──
export const healthCheck = () => api.get('/');

// ── Simulation ──
export const simulateAPI = (state) => api.post('/simulate-api', state);

export const simulateRun = (numSteps = 50) =>
  api.post(`/simulate-run?num_steps=${numSteps}`);

// ── Decision ──
export const getDecision = (params) =>
  api.get('/get-decision', { params });

// ── Training ──
export const trainModel = (config = { timesteps: 10000 }) =>
  api.post('/train', config);

// ── Metrics & Evaluation ──
export const getTrainingMetrics = () => api.get('/training-metrics');
export const getEvaluationResults = () => api.get('/evaluation-results');
export const runEvaluation = (episodes = 20) =>
  api.post(`/evaluate?episodes=${episodes}`);

// ── Logs & Stats ──
export const getAPILogs = (limit = 100, offset = 0) =>
  api.get('/api-logs', { params: { limit, offset } });

export const getRLDecisions = (limit = 100) =>
  api.get('/rl-decisions', { params: { limit } });

export const getDashboardStats = () => api.get('/dashboard-stats');

export default api;
