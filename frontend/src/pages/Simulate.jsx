import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend, Cell,
} from 'recharts';
import { Zap, Play, RotateCcw, Activity } from 'lucide-react';
import ChartCard from '../components/ChartCard';
import { executeRLPipeline } from '../services/api';

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
};

const ACTION_COLORS = {
  call_api: '#6366f1',
  retry: '#f59e0b',
  skip: '#ef4444',
  switch_provider: '#10b981',
};

const ALL_APIS = [
  'payment_A','payment_B','inventory','cart','order','recommendation',
  'authentication','profile','preferences',
  'delivery','tracking','warehouse',
  'fraud_detection','billing',
  'external_payment','external_shipping',
];

export default function Simulate() {
  const [state, setState] = useState({
    latency: 0.5, cost: 0.5, success_rate: 0.8, system_load: 1.2, previous_action: 0,
  });
  const [apiName, setApiName] = useState('payment_A');
  const [results, setResults] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sliders = [
    { key: 'latency', label: 'Latency (norm)', color: '#f59e0b', max: 1, step: 0.01 },
    { key: 'cost', label: 'Cost (norm)', color: '#ef4444', max: 1, step: 0.01 },
    { key: 'success_rate', label: 'Success Rate', color: '#10b981', max: 1, step: 0.01 },
    { key: 'system_load', label: 'System Load', color: '#3b82f6', max: 3, step: 0.1 },
    { key: 'previous_action', label: 'Previous Action (0-3)', color: '#8b5cf6', max: 3, step: 1 },
  ];

  function parseResult(data, step) {
    return {
      step,
      action: data.action_taken ?? '—',
      action_int: data.action_int ?? 0,
      confidence: data.confidence ?? {},
      latency: data.api_result?.latency ?? 0,
      cost: data.api_result?.cost ?? 0,
      success: data.api_result?.success ?? false,
      system_load: data.api_result?.system_load ?? 0,
      reward: data.reward ?? 0,
      logged: data.logged ?? false,
      api_name: data.api_result?.api_name ?? apiName,
    };
  }

  async function handleSimulate() {
    setLoading(true); setError(null);
    try {
      const res = await executeRLPipeline({ ...state, api_name: apiName });
      const parsed = parseResult(res.data, results.length + 1);
      setLastResult(parsed);
      setResults(prev => [...prev, parsed]);
    } catch (e) {
      setError(e.response?.data?.detail || 'Simulation failed — is the backend running?');
    }
    setLoading(false);
  }

  async function handleBurst() {
    setLoading(true); setError(null);
    for (let i = 0; i < 20; i++) {
      const noise = () => +(Math.random() * 0.2 - 0.1).toFixed(2);
      const s = {
        latency: Math.min(1, Math.max(0, state.latency + noise())),
        cost: Math.min(1, Math.max(0, state.cost + noise())),
        success_rate: Math.min(1, Math.max(0, state.success_rate + noise())),
        system_load: Math.min(3, Math.max(0.5, state.system_load + noise() * 2)),
        previous_action: Math.floor(Math.random() * 4),
        api_name: ALL_APIS[Math.floor(Math.random() * ALL_APIS.length)],
      };
      try {
        const res = await executeRLPipeline(s);
        const parsed = parseResult(res.data, results.length + i + 1);
        setResults(prev => [...prev, parsed]);
        setLastResult(parsed);
      } catch (e) { setError(e.response?.data?.detail || 'Burst failed'); break; }
    }
    setLoading(false);
  }

  const confData = lastResult?.confidence
    ? Object.entries(lastResult.confidence).map(([action, prob]) => ({
        action, probability: +(prob * 100).toFixed(1),
      }))
    : [];

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1><Zap size={28} /> <span className="gradient-text">Simulate</span></h1>
        <p>Send requests through the RL pipeline — decisions and results logged to DB</p>
      </div>

      <div className="control-panel">
        <div className="control-panel-header">
          <div>
            <div className="chart-card-title">System State Input</div>
            <div className="chart-card-subtitle">RL agent picks action → API simulated → logged to DB</div>
          </div>
          <div className="btn-group">
            <button className="btn btn-secondary btn-sm" onClick={() => { setResults([]); setLastResult(null); setError(null); }}>
              <RotateCcw size={14} /> Clear
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleBurst} disabled={loading}>
              <Activity size={14} /> Burst 20
            </button>
            <button className="btn btn-primary" onClick={handleSimulate} disabled={loading}>
              <Zap size={16} /> {loading ? 'Running...' : 'Simulate'}
            </button>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <label className="control-label" style={{ marginBottom: 6, display: 'block' }}>Target API</label>
          <select value={apiName} onChange={e => setApiName(e.target.value)}
            style={{ background: 'var(--bg-card)', color: 'white', padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', minWidth: 200 }}>
            {ALL_APIS.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>

        <div className="control-grid">
          {sliders.map(s => (
            <div key={s.key} className="slider-container">
              <div className="slider-header">
                <span className="control-label">{s.label}</span>
                <span className="slider-value">{state[s.key].toFixed(2)}</span>
              </div>
              <input type="range" min="0" max={s.max} step={s.step} value={state[s.key]}
                onChange={e => setState(prev => ({ ...prev, [s.key]: parseFloat(e.target.value) }))}
                style={{ accentColor: s.color }} />
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ padding: 12, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, color: '#ef4444', marginBottom: 16, fontSize: 13 }}>
          {error}
        </div>
      )}

      {lastResult && (
        <div className="stats-grid stagger-children" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-card-label">RL Action</div>
            <div style={{ marginTop: 8 }}>
              <span style={{ padding: '4px 14px', borderRadius: 999, fontSize: 13, fontWeight: 700,
                background: `${ACTION_COLORS[lastResult.action] || '#6366f1'}22`,
                color: ACTION_COLORS[lastResult.action] || '#6366f1' }}>
                {lastResult.action}
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">API Called</div>
            <div className="stat-card-value" style={{ fontSize: 14, color: '#a78bfa' }}>{lastResult.api_name}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Latency</div>
            <div className="stat-card-value" style={{ color: '#f59e0b' }}>{lastResult.latency.toFixed(1)} ms</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Cost</div>
            <div className="stat-card-value" style={{ color: '#ef4444' }}>${lastResult.cost.toFixed(3)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Status</div>
            <div style={{ marginTop: 8 }}>
              <span style={{ padding: '4px 14px', borderRadius: 999, fontSize: 13, fontWeight: 700,
                background: lastResult.success ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                color: lastResult.success ? '#10b981' : '#ef4444' }}>
                {lastResult.success ? '✓ Success' : '✗ Failed'}
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Reward</div>
            <div className="stat-card-value" style={{ color: lastResult.reward >= 0 ? '#10b981' : '#ef4444' }}>
              {lastResult.reward >= 0 ? '+' : ''}{lastResult.reward.toFixed(2)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Logged to DB</div>
            <div style={{ marginTop: 8, color: lastResult.logged ? '#10b981' : '#f59e0b', fontWeight: 700, fontSize: 13 }}>
              {lastResult.logged ? '✓ Yes' : '⚠ No'}
            </div>
          </div>
        </div>
      )}

      {results.length > 1 && (
        <div className="charts-grid">
          <ChartCard title="Reward Trend" subtitle="Reward per simulation step">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="reward" stroke="#6366f1" strokeWidth={2} dot={{ r: 3, fill: '#6366f1' }} name="Reward" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Latency and Cost" subtitle="Per simulation step">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="latency" stroke="#f59e0b" strokeWidth={2} dot={false} name="Latency (ms)" />
                <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} name="Cost ($)" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          {confData.length > 0 && (
            <ChartCard title="Action Confidence" subtitle="RL agent probability per action (last step)">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={confData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="action" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                  <Tooltip contentStyle={tooltipStyle} formatter={v => [`${v}%`]} />
                  <Bar dataKey="probability" radius={[4, 4, 0, 0]} name="Confidence %">
                    {confData.map((entry, i) => (
                      <Cell key={i} fill={ACTION_COLORS[entry.action] || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div className="logs-table-wrapper" style={{ marginTop: 24 }}>
          <div className="chart-card-title" style={{ padding: '16px 20px 0' }}>Session Log ({results.length} requests)</div>
          <table className="logs-table">
            <thead>
              <tr>
                <th>#</th><th>API</th><th>Action</th><th>Latency (ms)</th>
                <th>Cost ($)</th><th>Status</th><th>Reward</th><th>DB</th>
              </tr>
            </thead>
            <tbody>
              {[...results].reverse().map(r => (
                <tr key={r.step}>
                  <td style={{ color: '#64748b' }}>{r.step}</td>
                  <td><span className="provider-badge">{r.api_name}</span></td>
                  <td><span style={{ color: ACTION_COLORS[r.action] || '#6366f1', fontWeight: 700, fontSize: 12 }}>{r.action}</span></td>
                  <td style={{ color: '#f59e0b' }}>{r.latency.toFixed(1)}</td>
                  <td style={{ color: '#ef4444' }}>{r.cost.toFixed(3)}</td>
                  <td>
                    <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700,
                      background: r.success ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                      color: r.success ? '#10b981' : '#ef4444' }}>
                      {r.success ? '✓' : '✗'}
                    </span>
                  </td>
                  <td style={{ color: r.reward >= 0 ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                    {r.reward >= 0 ? '+' : ''}{r.reward.toFixed(2)}
                  </td>
                  <td style={{ color: r.logged ? '#10b981' : '#64748b', fontSize: 12 }}>{r.logged ? '✓' : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
