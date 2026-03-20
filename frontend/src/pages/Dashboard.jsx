import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Activity, DollarSign, Clock, CheckCircle2, TrendingUp, RefreshCcw } from 'lucide-react';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getUIDashboard, getRLDecisions } from '../services/api';

const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6'];
const ACTION_LABELS = { 0: 'call_api', 1: 'retry', 2: 'skip', 3: 'switch_provider' };

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
};

export default function Dashboard() {
  const [dash, setDash] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashRes, decRes] = await Promise.allSettled([
        getUIDashboard(),
        getRLDecisions(100),
      ]);
      if (dashRes.status === 'fulfilled') setDash(dashRes.value.data);
      else setError('Could not load dashboard stats from DB.');
      if (decRes.status === 'fulfilled') setDecisions(decRes.value.data);
    } catch (e) {
      setError('Backend unreachable.');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Loading dashboard from database..." />;

  // Build chart data from real RL decisions
  const decisionRows = [...decisions].reverse();
  const rewardData = decisionRows.map((d, i) => {
    const r = d.reward ?? 0;
    const running = decisionRows.slice(0, i + 1).reduce((s, x) => s + (x.reward ?? 0), 0) / (i + 1);
    return { step: i + 1, reward: +r.toFixed(3), avgReward: +running.toFixed(3) };
  });

  const actionDist = {};
  decisions.forEach(d => {
    const label = ACTION_LABELS[d.action] ?? String(d.action);
    actionDist[label] = (actionDist[label] || 0) + 1;
  });
  const pieData = Object.entries(actionDist).map(([name, value]) => ({ name, value }));

  // Per-API bar from dashboard stats
  const perApiBar = Object.entries(dash?.per_api_stats || {})
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 8)
    .map(([name, s]) => ({
      name: name.length > 14 ? name.slice(0, 12) + '…' : name,
      fullName: name,
      calls: s.total,
      successRate: +(s.success_rate * 100).toFixed(1),
      avgLatency: +s.avg_latency.toFixed(1),
    }));

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><span className="gradient-text">Dashboard</span></h1>
          <p>Live overview from database — API logs &amp; RL decisions</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load}>
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      {error && (
        <div style={{ padding: 14, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, color: '#ef4444', marginBottom: 20, fontSize: 13 }}>
          ⚠ {error} — run <code>python -m app.utils.seed_db</code> or simulate some requests first.
        </div>
      )}

      <div className="stats-grid stagger-children">
        <StatCard icon={<Activity size={18} />} label="Total API Calls" value={(dash?.total_calls ?? 0).toLocaleString()} trend="From DB" trendDir="up" color="purple" />
        <StatCard icon={<CheckCircle2 size={18} />} label="Success Rate" value={`${((dash?.success_rate ?? 0) * 100).toFixed(1)}%`} trend="Overall" trendDir="up" color="green" />
        <StatCard icon={<Clock size={18} />} label="Avg Latency" value={`${(dash?.avg_latency ?? 0).toFixed(1)} ms`} trend="Normalized" trendDir="down" color="yellow" />
        <StatCard icon={<DollarSign size={18} />} label="Avg Cost" value={`$${(dash?.avg_cost ?? 0).toFixed(3)}`} trend="Per request" trendDir="down" color="red" />
        <StatCard icon={<TrendingUp size={18} />} label="RL Decisions" value={decisions.length.toLocaleString()} trend="Logged" trendDir="up" color="blue" />
      </div>

      {decisions.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-title">No Data Yet</div>
          <div className="empty-state-text">Go to Simulate to run API requests — data will appear here.</div>
        </div>
      )}

      {decisions.length > 0 && (
        <div className="charts-grid">
          <ChartCard title="RL Reward Over Time" subtitle="Per-decision reward from DB">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rewardData}>
                <defs>
                  <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="avgReward" stroke="#6366f1" fill="url(#rg)" strokeWidth={2} name="Avg Reward" />
                <Area type="monotone" dataKey="reward" stroke="#a78bfa" fill="none" strokeWidth={1} opacity={0.4} name="Step Reward" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Action Distribution" subtitle="How the RL agent routes requests">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={95} paddingAngle={4} dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#64748b' }}>
                  {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {perApiBar.length > 0 && (
            <ChartCard title="API Call Volume" subtitle="Total calls per API endpoint (from DB)">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={perApiBar}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [v, p.payload.fullName || n]} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="calls" fill="#6366f1" radius={[4, 4, 0, 0]} name="Total Calls" />
                  <Bar dataKey="successRate" fill="#10b981" radius={[4, 4, 0, 0]} name="Success %" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {perApiBar.length > 0 && (
            <ChartCard title="Avg Latency by API" subtitle="Milliseconds per endpoint">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={perApiBar}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [`${v} ms`, p.payload.fullName || n]} />
                  <Bar dataKey="avgLatency" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Avg Latency (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>
      )}

      {/* Recent Decisions Table */}
      {decisions.length > 0 && (
        <div className="logs-table-wrapper" style={{ marginTop: 24 }}>
          <div className="chart-card-title" style={{ padding: '16px 20px 0' }}>Recent RL Decisions</div>
          <table className="logs-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>API</th>
                <th>Action</th>
                <th>Reward</th>
              </tr>
            </thead>
            <tbody>
              {decisions.slice(0, 15).map((d, i) => (
                <tr key={d.id || i}>
                  <td>{d.id || i + 1}</td>
                  <td>{d.timestamp ? new Date(d.timestamp).toLocaleString() : '—'}</td>
                  <td><span className="provider-badge">{d.api_name || '—'}</span></td>
                  <td><span className="provider-badge">{ACTION_LABELS[d.action] ?? d.action}</span></td>
                  <td style={{ color: (d.reward ?? 0) >= 0 ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                    {(d.reward ?? 0) >= 0 ? '+' : ''}{(d.reward ?? 0).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
