# Frontend — RL API Orchestrator Dashboard

React + Vite dashboard for monitoring and interacting with the RL API Orchestration backend.

**Stack**: React 19, Vite, React Router v7, Recharts, Axios, Lucide React, Framer Motion

---

## Structure

```
frontend/src/
├── main.jsx
├── App.jsx
│
├── pages/
│   ├── Dashboard.jsx     # Aggregate stats + recent activity  →  GET /ui/dashboard, /dashboard-stats
│   ├── Simulate.jsx      # Run RL pipeline interactively      →  POST /rl/execute
│   ├── Train.jsx         # Trigger PPO training               →  POST /train
│   ├── Logs.jsx          # Browse API + RL decision logs      →  GET /api-logs, /rl/decisions
│   ├── Metrics.jsx       # Training metrics charts            →  GET /training-metrics, /rl/metrics
│   ├── Compare.jsx       # Strategy comparison                →  GET /evaluation-results, POST /evaluate
│   └── ApiExplorer.jsx   # Browse API ecosystem config        →  GET /api/config
│
├── components/
│   ├── Sidebar.jsx       # Navigation sidebar
│   ├── StatCard.jsx      # KPI stat card
│   ├── ChartCard.jsx     # Recharts wrapper card
│   └── LoadingSpinner.jsx
│
└── services/
    └── api.js            # Axios client — all backend calls
```

---

## Setup

```bash
cd frontend
npm install
```

Create a `.env` file (or copy from `.env.example`):

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Running

```bash
npm run dev
```

Open `http://localhost:5173`.

Make sure the backend is running on port 8000 first:
```bash
# from backend/
uvicorn api.main:app --port 8000 --reload
```

---

## API Client (`services/api.js`)

All HTTP calls go through a single Axios instance pointed at `VITE_API_BASE_URL`.

| Export                  | Method | Endpoint                  | Used by         |
|-------------------------|--------|---------------------------|-----------------|
| `healthCheck`           | GET    | `/health`                 | —               |
| `simulateAPI`           | POST   | `/simulate-api`           | Simulate        |
| `trainModel`            | POST   | `/train`                  | Train           |
| `getTrainingMetrics`    | GET    | `/training-metrics`       | Metrics, Train  |
| `getEvaluationResults`  | GET    | `/evaluation-results`     | Compare         |
| `runEvaluation`         | POST   | `/evaluate`               | Compare         |
| `getAPILogs`            | GET    | `/api-logs`               | Logs            |
| `getDashboardStats`     | GET    | `/dashboard-stats`        | Dashboard       |
| `getRLDecisions`        | GET    | `/rl/decisions`           | Logs            |
| `getRLMetrics`          | GET    | `/rl/metrics`             | Metrics         |
| `executeRLPipeline`     | POST   | `/rl/execute`             | Simulate        |
| `getRLDecision`         | POST   | `/rl/get-decision`        | Simulate        |
| `getUIDashboard`        | GET    | `/ui/dashboard`           | Dashboard       |
| `getLiveFeed`           | GET    | `/ui/live-feed`           | Dashboard       |
| `getPerformance`        | GET    | `/ui/performance`         | Metrics         |
| `getAPIConfig`          | GET    | `/api/config`             | ApiExplorer     |
| `getAPIStats`           | GET    | `/api/stats`              | Dashboard       |
| `simulateAppAPI`        | POST   | `/api/simulate`           | Simulate        |
| `getAppLogs`            | GET    | `/api/logs`               | Logs            |

---

## Build

```bash
npm run build
```

Output goes to `dist/`. Serve with any static file server or configure Vite's preview:

```bash
npm run preview
```
