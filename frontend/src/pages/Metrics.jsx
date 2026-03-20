import { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { BarChart3, RefreshCcw } from 'lucide-react';
import ChartCard from '../components/ChartCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getTrainingMetrics, getAPIStats } from '../services/api';

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
};

export default function Metrics() {
  const [trainMetrics, setTrainMetrics] = useState(null);
  const [apiStats, setApiStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [tmRes, statsRes] = await Promise.allSettled([
      getTrainingMetrics(),
      getAPIStats(500),
    ]);
    if (tmRes.status === 'fulfilled') setTrainMetrics(tmRes.value.data);
    if (statsRes.status === 'fulfilled') setApiStats(statsRes.value.data);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Loading metrics..." />;

  // Training metrics from JSON file (episodes array)
  const episodes = trainMetrics?.episodes || [];
  const episodeChart = episodes.map(e => ({
    episode: e.episode,
    reward: +e.reward.toFixed(2),
    length: e.length,
  }));

  // Running average
  const runningAvg = episodeChart.map((e, i) => ({
    ...e,
    avgReward: +(episodeChart.slice(0, i + 1).reduce((s, x) => s + x.reward, 0) / (i + 1)).toFixed(2),
  }));

  // Per-API stats from DB
  const perApi = Object.entries(apiStats?.per_api || {})
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 10)
    .map(([name, s]) => ({
      name: name.length > 14 ? name.slice(0, 12) + '…' : name,
      fullName: name,
      total: s.total,
      successRate: +(s.success_rate * 100).toFixed(1),
      avgLatency: +s.avg_latency.toFixed(1),
      avgCost: +s.avg_cost.toFixed(3),
    }));

  const hasTraining = episodeChart.length > 0;
  const hasApiStats = perApi.length > 0;

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><BarChart3 size={28} /> <span className="gradient-text">Metrics</span></h1>
          <p>Training performance &amp; live API statistics from the database</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load}>
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      {/* Training summary cards */}
      {trainMetrics && !trainMetrics.error && (
        <div className="stats-grid stagger-children" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-card-label">Total Timesteps</div>
            <div className="stat-card-value">{(trainMetrics.total_timesteps || 0).toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Mean Reward</div>
            <div className="stat-card-value" style={{ color: '#6366f1' }}>{(trainMetrics.mean_reward || 0).toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Std Reward</div>
            <div className="stat-card-value" style={{ color: '#f59e0b' }}>±{(trainMetrics.std_reward || 0).toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Training Time</div>
            <div className="stat-card-value" style={{ color: '#10b981' }}>{(trainMetrics.training_time_seconds || 0).toFixed(1)}s</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Episodes</div>
            <div className="stat-card-value">{episodes.length}</div>
          </div>
        </div>
      )}

      {trainMetrics?.error && (
        <div style={{ padding: 14, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, color: '#ef4444', marginBottom: 20, fontSize: 13 }}>
          ⚠ {trainMetrics.error} — go to Train Model to run training first.
        </div>
      )}

      <div className="charts-grid">
        {hasTraining && (
          <ChartCard title="Episode Reward" subtitle="Reward per training episode + running average">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={runningAvg}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="episode" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="reward" stroke="#a78bfa" strokeWidth={1} dot={false} opacity={0.5} name="Episode Reward" />
                <Line type="monotone" dataKey="avgReward" stroke="#6366f1" strokeWidth={2.5} dot={false} name="Running Avg" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {hasTraining && (
          <ChartCard title="Episode Length" subtitle="Steps per training episode">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={episodeChart}>
                <defs>
                  <linearGradient id="lenGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="episode" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="length" stroke="#10b981" fill="url(#lenGrad)" strokeWidth={2} name="Episode Length" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {hasApiStats && (
          <ChartCard title="API Success Rate" subtitle="Per-endpoint success % from DB">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perApi} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis type="number" stroke="#64748b" fontSize={11} domain={[0, 100]} />
                <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={10} width={90} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [`${v}%`, p.payload.fullName]} />
                <Bar dataKey="successRate" fill="#10b981" radius={[0, 4, 4, 0]} name="Success %" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {hasApiStats && (
          <ChartCard title="Avg Latency by API" subtitle="Milliseconds per endpoint from DB">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perApi} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={10} width={90} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [`${v} ms`, p.payload.fullName]} />
                <Bar dataKey="avgLatency" fill="#f59e0b" radius={[0, 4, 4, 0]} name="Avg Latency (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </div>

      {!hasTraining && !hasApiStats && (
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <div className="empty-state-title">No Metrics Yet</div>
          <div className="empty-state-text">Train the model and run simulations to see metrics here.</div>
        </div>
      )}
    </div>
  );
}
