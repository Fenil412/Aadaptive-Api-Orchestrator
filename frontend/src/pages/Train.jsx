import { useState, useEffect } from 'react';
import { Brain, Play, CheckCircle, AlertTriangle, RefreshCcw } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import { trainModel, getTrainingMetrics, runEvaluation } from '../services/api';

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '12px',
};

export default function Train() {
  const [config, setConfig] = useState({ timesteps: 10000 });
  const [training, setTraining] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [result, setResult] = useState(null);
  const [savedMetrics, setSavedMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => { loadSavedMetrics(); }, []);

  async function loadSavedMetrics() {
    try {
      const res = await getTrainingMetrics();
      if (!res.data?.error) setSavedMetrics(res.data);
    } catch { /* no metrics yet */ }
  }

  async function handleTrain() {
    setTraining(true); setResult(null); setError(null);
    try {
      const res = await trainModel(config.timesteps);
      setResult(res.data);
      await loadSavedMetrics();
    } catch (err) {
      setError(err.response?.data?.detail || 'Training failed.');
    }
    setTraining(false);
  }

  async function handleEvaluate() {
    setEvaluating(true); setError(null);
    try {
      await runEvaluation(20);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Evaluation failed.');
    }
    setEvaluating(false);
  }

  const episodes = savedMetrics?.episodes || [];
  const episodeChart = episodes.map(e => ({
    episode: e.episode,
    reward: +e.reward.toFixed(2),
  }));

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><Brain size={28} /> <span className="gradient-text">Train Model</span></h1>
          <p>Train or retrain the PPO reinforcement learning agent</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadSavedMetrics}>
          <RefreshCcw size={14} /> Reload Metrics
        </button>
      </div>

      <div className="control-panel">
        <div className="chart-card-title" style={{ marginBottom: 16 }}>Training Configuration</div>
        <div className="control-grid" style={{ maxWidth: 500 }}>
          <div className="control-group">
            <label className="control-label">Total Timesteps</label>
            <input type="number" className="control-input" value={config.timesteps}
              onChange={e => setConfig(p => ({ ...p, timesteps: parseInt(e.target.value) || 1000 }))}
              min={1000} max={500000} step={1000} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
          <button className="btn btn-primary" onClick={handleTrain} disabled={training || evaluating}>
            <Play size={16} /> {training ? `Training ${config.timesteps.toLocaleString()} steps...` : 'Start Training'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleEvaluate} disabled={training || evaluating}>
            {evaluating ? 'Evaluating...' : 'Run Evaluation (20 eps)'}
          </button>
        </div>

        {training && (
          <div style={{ marginTop: 16, padding: 14, background: 'rgba(59,130,246,0.08)', borderRadius: 10, border: '1px solid rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="loading-spinner" style={{ width: 18, height: 18 }} />
            <span style={{ color: '#3b82f6', fontWeight: 600, fontSize: 13 }}>
              Training {config.timesteps.toLocaleString()} timesteps — this may take a few minutes...
            </span>
          </div>
        )}

        {result && (
          <div style={{ marginTop: 16, padding: 14, background: 'rgba(16,185,129,0.08)', borderRadius: 10, border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <CheckCircle size={16} style={{ color: '#10b981' }} />
              <span style={{ color: '#10b981', fontWeight: 700 }}>Training Complete</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
              {[
                { label: 'Timesteps', value: result.metrics?.total_timesteps?.toLocaleString() },
                { label: 'Mean Reward', value: result.metrics?.mean_reward?.toFixed(2) },
                { label: 'Std Reward', value: `±${result.metrics?.std_reward?.toFixed(2)}` },
                { label: 'Training Time', value: `${result.metrics?.training_time_seconds?.toFixed(1)}s` },
                { label: 'Episodes', value: result.metrics?.episodes?.length },
              ].map(item => (
                <div key={item.label} style={{ padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{item.label}</div>
                  <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15 }}>{item.value ?? '—'}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 16, padding: 14, background: 'rgba(239,68,68,0.08)', borderRadius: 10, border: '1px solid rgba(239,68,68,0.2)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} style={{ color: '#ef4444' }} />
            <span style={{ color: '#ef4444', fontWeight: 600, fontSize: 13 }}>{error}</span>
          </div>
        )}
      </div>

      {/* Saved metrics from last training run */}
      {savedMetrics && !savedMetrics.error && (
        <div style={{ marginTop: 24 }}>
          <div className="stats-grid stagger-children" style={{ marginBottom: 20 }}>
            {[
              { label: 'Last Timesteps', value: (savedMetrics.total_timesteps || 0).toLocaleString(), color: '#6366f1' },
              { label: 'Mean Reward', value: (savedMetrics.mean_reward || 0).toFixed(2), color: '#10b981' },
              { label: 'Std Reward', value: `±${(savedMetrics.std_reward || 0).toFixed(2)}`, color: '#f59e0b' },
              { label: 'Training Time', value: `${(savedMetrics.training_time_seconds || 0).toFixed(1)}s`, color: '#3b82f6' },
              { label: 'Total Episodes', value: episodes.length, color: '#8b5cf6' },
            ].map(item => (
              <div key={item.label} className="stat-card">
                <div className="stat-card-label">{item.label}</div>
                <div className="stat-card-value" style={{ color: item.color }}>{item.value}</div>
              </div>
            ))}
          </div>

          {episodeChart.length > 0 && (
            <ChartCard title="Episode Rewards (Last Training Run)" subtitle="Reward per episode from saved metrics">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={episodeChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="episode" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="reward" stroke="#6366f1" strokeWidth={2} dot={false} name="Episode Reward" />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>
      )}

      <div className="chart-card" style={{ marginTop: 24 }}>
        <div className="chart-card-title" style={{ marginBottom: 16 }}>PPO Architecture</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {[
            { icon: '🧠', title: 'Policy Network', desc: 'MLP: state → action probabilities', color: '#6366f1' },
            { icon: '🎯', title: 'Reward Function', desc: '+100 success, -50 fail, -latency×0.1, -cost×5', color: '#10b981' },
            { icon: '⚡', title: 'State Space (5D)', desc: 'latency, cost, success_rate, system_load, prev_action', color: '#f59e0b' },
            { icon: '🔀', title: 'Action Space (4)', desc: 'call_api, retry, skip, switch_provider', color: '#8b5cf6' },
          ].map(c => (
            <div key={c.title} style={{ padding: 14, background: 'var(--bg-primary)', borderRadius: 10 }}>
              <div style={{ fontWeight: 700, color: c.color, marginBottom: 4 }}>{c.icon} {c.title}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{c.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
