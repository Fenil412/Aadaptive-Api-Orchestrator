import { useState } from 'react';
import { Brain, Play, CheckCircle, AlertTriangle } from 'lucide-react';
import { trainModel } from '../services/api';

export default function Train() {
  const [config, setConfig] = useState({ timesteps: 10000, learning_rate: 0.0003 });
  const [training, setTraining] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleTrain() {
    setTraining(true); setResult(null); setError(null);
    try {
      const res = await trainModel(config);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Training failed.');
    }
    setTraining(false);
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1><Brain size={28} /> <span className="gradient-text">Train Model</span></h1>
        <p>Train or retrain the PPO reinforcement learning agent</p>
      </div>
      <div className="control-panel">
        <div className="chart-card-title" style={{marginBottom:16}}>Training Configuration</div>
        <div className="control-grid" style={{maxWidth:600}}>
          <div className="control-group">
            <label className="control-label">Total Timesteps</label>
            <input type="number" className="control-input" value={config.timesteps}
              onChange={e => setConfig(p => ({...p, timesteps: parseInt(e.target.value)||1000}))} min={1000} max={500000} step={1000} />
          </div>
          <div className="control-group">
            <label className="control-label">Learning Rate</label>
            <input type="number" className="control-input" value={config.learning_rate}
              onChange={e => setConfig(p => ({...p, learning_rate: parseFloat(e.target.value)||0.0003}))} min={0.00001} max={0.01} step={0.00001} />
          </div>
        </div>
        <div style={{marginTop:24}}>
          <button className="btn btn-primary" onClick={handleTrain} disabled={training}>
            <Play size={16} /> {training ? 'Training...' : 'Start Training'}
          </button>
        </div>
        {training && (
          <div style={{marginTop:16,padding:14,background:'var(--info-bg)',borderRadius:10,border:'1px solid rgba(59,130,246,0.2)',display:'flex',alignItems:'center',gap:10}}>
            <div className="loading-spinner" style={{width:18,height:18}} />
            <span style={{color:'var(--info)',fontWeight:600,fontSize:13}}>Training {config.timesteps.toLocaleString()} timesteps...</span>
          </div>
        )}
        {result && (
          <div style={{marginTop:16,padding:14,background:'var(--success-bg)',borderRadius:10,border:'1px solid rgba(16,185,129,0.2)'}}>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <CheckCircle size={16} style={{color:'var(--success)'}} />
              <span style={{color:'var(--success)',fontWeight:700}}>Training Complete!</span>
            </div>
            <div style={{fontSize:13,color:'var(--text-secondary)',marginTop:6}}>{result.message}</div>
          </div>
        )}
        {error && (
          <div style={{marginTop:16,padding:14,background:'var(--error-bg)',borderRadius:10,border:'1px solid rgba(239,68,68,0.2)',display:'flex',alignItems:'center',gap:8}}>
            <AlertTriangle size={16} style={{color:'var(--error)'}} />
            <span style={{color:'var(--error)',fontWeight:600,fontSize:13}}>{error}</span>
          </div>
        )}
      </div>
      <div className="chart-card" style={{marginTop:24}}>
        <div className="chart-card-title" style={{marginBottom:16}}>About PPO Training</div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:14}}>
          {[
            {icon:'🧠',title:'Policy Network',desc:'MLP maps state → provider choice',color:'var(--accent-primary-light)'},
            {icon:'🎯',title:'Objective',desc:'Maximize reward: low latency + low cost + high success',color:'var(--success)'},
            {icon:'⚡',title:'State Space',desc:'6 features: latency, cost, success, load, time, errors',color:'var(--warning)'},
            {icon:'🔀',title:'Action Space',desc:'4 providers: Fast, Balanced, Cheap, Cache',color:'var(--info)'},
          ].map(c => (
            <div key={c.title} style={{padding:14,background:'var(--bg-primary)',borderRadius:10}}>
              <div style={{fontWeight:700,color:c.color,marginBottom:4}}>{c.icon} {c.title}</div>
              <div style={{fontSize:12,color:'var(--text-secondary)'}}>{c.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
