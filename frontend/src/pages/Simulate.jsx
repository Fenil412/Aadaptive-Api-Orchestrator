import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Zap, Play, RotateCcw } from 'lucide-react';
import ChartCard from '../components/ChartCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { simulateAPI, getDecision } from '../services/api';

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
};

const PROVIDER_BADGES = {
  'Provider A (Fast)': 'provider-a',
  'Provider B (Balanced)': 'provider-b',
  'Provider C (Cheap)': 'provider-c',
  'Fallback/Cache': 'provider-fallback',
};

export default function Simulate() {
  const [state, setState] = useState({
    latency: 0.5,
    cost: 0.5,
    success_rate: 0.8,
    system_load: 1.5,
    previous_action: 0,
  });
  const [apiCategory, setApiCategory] = useState("ecommerce");
  const [apiName, setApiName] = useState("payment_A");
  const [results, setResults] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const sliders = [
    { key: 'latency', label: 'Latency', color: '#f59e0b', max: 1, step: 0.01 },
    { key: 'cost', label: 'Cost', color: '#ef4444', max: 1, step: 0.01 },
    { key: 'success_rate', label: 'Success Rate', color: '#10b981', max: 1, step: 0.01 },
    { key: 'system_load', label: 'System Load', color: '#3b82f6', max: 3, step: 0.1 },
    { key: 'previous_action', label: 'Previous Action (0-3)', color: '#8b5cf6', max: 3, step: 1 },
  ];

  async function handleSimulate() {
    setLoading(true);
    try {
      const payload = {
        state: state,
        api_category: apiCategory,
        api_name: apiName
      };
      // Use direct import or dynamic fetch
      const res = await fetch((import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001') + '/rl/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();
      
      const parsedResult = {
        action: result.action,
        provider: result.action_name,
        latency: result.api_response?.latency || 0,
        cost: result.api_response?.cost || 0,
        success: result.api_response?.success || false,
        reward: result.reward,
      };
      
      setLastResult(parsedResult);
      setResults(prev => [...prev, { ...parsedResult, step: prev.length + 1 }]);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function handleBurst() {
    setLoading(true);
    for (let i = 0; i < 20; i++) {
      const noise = () => +(Math.random() * 0.2 - 0.1).toFixed(2);
      const burstState = {
        latency: Math.min(1, Math.max(0, state.latency + noise())),
        cost: Math.min(1, Math.max(0, state.cost + noise())),
        success_rate: Math.min(1, Math.max(0, state.success_rate + noise())),
        system_load: Math.min(3, Math.max(0, state.system_load + noise()*2)),
        previous_action: Math.floor(Math.random() * 4),
      };
      try {
        const payload = { state: burstState, api_category: apiCategory, api_name: apiName };
        const res = await fetch((import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001') + '/rl/execute', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
        const result = await res.json();
        
        const parsedResult = {
          action: result.action,
          provider: result.action_name,
          latency: result.api_response?.latency || 0,
          cost: result.api_response?.cost || 0,
          success: result.api_response?.success || false,
          reward: result.reward,
        };
        setResults(prev => [...prev, { ...parsedResult, step: prev.length + 1 }]);
        setLastResult(parsedResult);
      } catch {
        break;
      }
    }
    setLoading(false);
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1><Zap size={28} className="gradient-text" /> <span className="gradient-text">Simulate</span></h1>
        <p>Send API requests with custom system conditions and observe RL decisions</p>
      </div>

      {/* Control Panel */}
      <div className="control-panel">
        <div className="control-panel-header">
          <div>
            <div className="chart-card-title">System State</div>
            <div className="chart-card-subtitle">Adjust conditions to test RL routing decisions</div>
          </div>
          <div className="btn-group">
            <button className="btn btn-secondary btn-sm" onClick={() => setResults([])}>
              <RotateCcw size={14} /> Clear
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleBurst} disabled={loading}>
              <Play size={14} /> Burst 20
            </button>
            <button className="btn btn-primary" onClick={handleSimulate} disabled={loading}>
              <Zap size={16} /> {loading ? 'Simulating...' : 'Simulate'}
            </button>
          </div>
        </div>

        <div className="control-grid" style={{marginBottom: 20}}>
          <div className="slider-container">
            <div className="control-label">API Category</div>
            <select value={apiCategory} onChange={e => setApiCategory(e.target.value)} style={{background: 'var(--bg-card)', color: 'white', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', outline: 'none'}}>
               <option value="ecommerce">E-commerce</option>
               <option value="user">User</option>
               <option value="logistics">Logistics</option>
               <option value="financial">Financial</option>
            </select>
          </div>
          <div className="slider-container">
             <div className="control-label">API Endpoint</div>
             <input value={apiName} onChange={e => setApiName(e.target.value)} style={{background: 'var(--bg-card)', color: 'white', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.1)'}} placeholder="e.g. payment_A" />
          </div>
        </div>

        <div className="control-grid">
          {sliders.map(s => (
            <div key={s.key} className="slider-container">
              <div className="slider-header">
                <span className="control-label">{s.label}</span>
                <span className="slider-value">{state[s.key].toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max={s.max || 1}
                step={s.step || 0.01}
                value={state[s.key]}
                onChange={e => setState(prev => ({ ...prev, [s.key]: parseFloat(e.target.value) }))}
                style={{ accentColor: s.color }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Last Result */}
      {lastResult && (
        <div className="stats-grid stagger-children" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-card-label">Provider Chosen</div>
            <div style={{ marginTop: 8 }}>
              <span className={`provider-badge ${PROVIDER_BADGES[lastResult.provider] || ''}`}>
                {lastResult.provider}
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Latency</div>
            <div className="stat-card-value" style={{ color: '#f59e0b' }}>{lastResult.latency?.toFixed(3)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Cost</div>
            <div className="stat-card-value" style={{ color: '#ef4444' }}>{lastResult.cost?.toFixed(3)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Status</div>
            <div style={{ marginTop: 8 }}>
              <span className={`success-badge ${lastResult.success ? 'success' : 'failure'}`}
                    style={{ padding: '4px 14px', borderRadius: 999, fontSize: 13, fontWeight: 700,
                             background: lastResult.success ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                             color: lastResult.success ? '#10b981' : '#ef4444' }}>
                {lastResult.success ? '✓ Success' : '✗ Failed'}
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Reward</div>
            <div className="stat-card-value" style={{ color: lastResult.reward >= 0 ? '#10b981' : '#ef4444' }}>
              {lastResult.reward >= 0 ? '+' : ''}{lastResult.reward?.toFixed(3)}
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      {results.length > 1 && (
        <div className="charts-grid">
          <ChartCard title="Reward Trend" subtitle="Reward per simulation step">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="reward" stroke="#6366f1" strokeWidth={2} dot={{ r: 3, fill: '#6366f1' }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Latency & Cost" subtitle="Per simulation step">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="step" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="latency" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}
    </div>
  );
}
