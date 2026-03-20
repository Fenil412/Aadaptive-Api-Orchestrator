import { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Activity, DollarSign, Clock, CheckCircle2, TrendingUp } from 'lucide-react';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getDashboardStats, getTrainingMetrics, getRLDecisions } from '../services/api';

const PROVIDER_COLORS = {
  'Call API': '#6366f1',
  'Retry': '#10b981',
  'Skip': '#f59e0b',
  'Switch API': '#8b5cf6',
  'Unknown': '#94a3b8'
};
const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6'];

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
  fontFamily: "'Inter', sans-serif",
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [simData, setSimData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [statsRes, metricsRes, decRes] = await Promise.allSettled([
        getDashboardStats(),
        getTrainingMetrics(),
        getRLDecisions(60)
      ]);

      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value.data);

      if (decRes.status === 'fulfilled' && decRes.value.data.length > 0) {
        const decData = decRes.value.data;
        const actionsMap = {0: 'Call API', 1: 'Retry', 2: 'Skip', 3: 'Switch API'};
        const steps = decData.reverse().map((d, i) => {
          const stateObj = typeof d.state === 'string' ? JSON.parse(d.state) : d.state;
          return {
            step: i + 1,
            provider: actionsMap[parseInt(d.action)] || d.action,
            latency: stateObj?.latency || 0,
            cost: stateObj?.cost || 0,
            success: (stateObj?.success_rate || 0) > 0.5,
            reward: d.reward
          };
        });
        setSimData({ steps });
      } else {
        generateDemoData();
      }
    } catch {
      generateDemoData();
    }
    setLoading(false);
  }

  function generateDemoData() {
    const providers = ['Call API', 'Retry', 'Skip', 'Switch API'];
    const steps = Array.from({ length: 60 }, (_, i) => {
      const provider = providers[Math.floor(Math.random() * 4)];
      const success = Math.random() > 0.15;
      return {
        step: i + 1,
        provider,
        latency: +(0.05 + Math.random() * 0.7).toFixed(3),
        cost: +(0.02 + Math.random() * 0.8).toFixed(3),
        success,
        reward: success ? +(0.2 + Math.random() * 0.6).toFixed(3) : +(-0.5 - Math.random() * 0.5).toFixed(3),
      };
    });
    setSimData({ steps });
  }

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  const steps = simData?.steps || [];
  const rewardData = steps.map((s, i) => ({
    step: s.step,
    reward: s.reward,
    avgReward: +(steps.slice(0, i + 1).reduce((a, b) => a + b.reward, 0) / (i + 1)).toFixed(3),
  }));

  const latencyCostData = steps.map(s => ({
    step: s.step,
    latency: s.latency,
    cost: s.cost,
  }));

  const providerDist = {};
  steps.forEach(s => { providerDist[s.provider] = (providerDist[s.provider] || 0) + 1; });
  const pieData = Object.entries(providerDist).map(([name, value]) => ({ name, value }));

  const providerPerf = {};
  steps.forEach(s => {
    if (!providerPerf[s.provider]) providerPerf[s.provider] = { rewards: [], latencies: [], count: 0 };
    providerPerf[s.provider].rewards.push(s.reward);
    providerPerf[s.provider].latencies.push(s.latency);
    providerPerf[s.provider].count++;
  });
  const barData = Object.entries(providerPerf).map(([name, data]) => ({
    name: name,
    avgReward: +(data.rewards.reduce((a, b) => a + b, 0) / data.count).toFixed(3),
    avgLatency: +(data.latencies.reduce((a, b) => a + b, 0) / data.count).toFixed(3),
  }));

  const trendDir = stats?.recent_trend === 'improving' ? 'up' : stats?.recent_trend === 'declining' ? 'down' : 'stable';

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1>
          <span className="gradient-text">Dashboard</span>
        </h1>
        <p>Real-time overview of the RL-powered API routing system</p>
      </div>

      <div className="stats-grid stagger-children">
        <StatCard
          icon={<Activity size={18} />}
          label="Total Decisions"
          value={stats?.total_requests?.toLocaleString() || '0'}
          trend={stats?.requests_trend || 'N/A'}
          trendDir={trendDir}
          color="purple"
        />
        <StatCard
          icon={<TrendingUp size={18} />}
          label="Total Cost Impact"
          value={stats?.total_cost?.toFixed(3) || '0.000'}
          trend="Cumulative"
          trendDir="up"
          color="green"
        />
        <StatCard
          icon={<Clock size={18} />}
          label="Avg Latency"
          value={stats?.avg_latency?.toFixed(3) || '0.000'}
          trend="Normalized"
          trendDir="down"
          color="yellow"
        />
        <StatCard
          icon={<DollarSign size={18} />}
          label="Avg Cost"
          value={stats?.avg_cost?.toFixed(3) || '0.000'}
          trend="Per request"
          trendDir="down"
          color="red"
        />
        <StatCard
          icon={<CheckCircle2 size={18} />}
          label="Success Rate"
          value={`${((stats?.success_rate || 0) * 100).toFixed(1)}%`}
          trend="Overall"
          trendDir="up"
          color="blue"
        />
      </div>

      <div className="charts-grid">
        <ChartCard title="Reward Over Time" subtitle="Running average and per-step reward">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={rewardData}>
              <defs>
                <linearGradient id="rewardGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="avgReward" stroke="#6366f1" fill="url(#rewardGrad)" strokeWidth={2} name="Avg Reward" />
              <Line type="monotone" dataKey="reward" stroke="#a78bfa" strokeWidth={1} dot={false} opacity={0.4} name="Step Reward" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Latency vs Cost" subtitle="Per-step latency and cost metrics">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={latencyCostData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line type="monotone" dataKey="latency" stroke="#f59e0b" strokeWidth={2} dot={false} name="Latency" />
              <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} name="Cost" />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Action Distribution" subtitle="How requests are routed">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={4}
                dataKey="value"
                label={({ name, percent }) => `${name.split('(')[0].trim()} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: '#64748b' }}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Action Performance" subtitle="Avg reward & latency by Action">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="avgReward" fill="#6366f1" radius={[4, 4, 0, 0]} name="Avg Reward" />
              <Bar dataKey="avgLatency" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Avg Latency" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
