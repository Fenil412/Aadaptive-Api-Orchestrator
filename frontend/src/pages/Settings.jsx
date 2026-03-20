import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, CheckCircle } from 'lucide-react';
import { healthCheck } from '../services/api';

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');

  useEffect(() => { checkHealth(); }, []);

  async function checkHealth() {
    try {
      const res = await healthCheck();
      setHealth(res.data);
    } catch { setHealth({ status: 'offline', model_loaded: false }); }
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1><SettingsIcon size={28} /> <span className="gradient-text">Settings</span></h1>
        <p>System configuration and health status</p>
      </div>
      <div className="control-panel">
        <div className="chart-card-title" style={{marginBottom:16}}>Backend Connection</div>
        <div className="control-grid" style={{maxWidth:500}}>
          <div className="control-group">
            <label className="control-label">API Base URL</label>
            <input className="control-input" value={apiUrl} onChange={e => setApiUrl(e.target.value)} />
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" style={{marginTop:16}} onClick={checkHealth}>Test Connection</button>
        {health && (
          <div style={{marginTop:16,display:'flex',gap:24,flexWrap:'wrap'}}>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <span className={`status-dot${health.status==='healthy'?'':' offline'}`} />
              <span style={{fontSize:13,color:'var(--text-secondary)'}}>Backend: <strong style={{color:health.status==='healthy'?'var(--success)':'var(--error)'}}>{health.status}</strong></span>
            </div>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              {health.model_loaded ? <CheckCircle size={14} style={{color:'var(--success)'}}/> : <span style={{color:'var(--error)'}}>●</span>}
              <span style={{fontSize:13,color:'var(--text-secondary)'}}>Model: <strong>{health.model_loaded ? 'Loaded' : 'Not loaded'}</strong></span>
            </div>
          </div>
        )}
      </div>
      <div className="chart-card" style={{marginTop:24}}>
        <div className="chart-card-title" style={{marginBottom:12}}>System Architecture</div>
        <div style={{fontSize:13,color:'var(--text-secondary)',lineHeight:1.8,fontFamily:'var(--font-mono)'}}>
          <div>React Dashboard → FastAPI Backend → PPO RL Engine</div>
          <div style={{marginTop:8}}>                    ↕</div>
          <div>          PostgreSQL (Supabase) — Logs & Decisions</div>
        </div>
      </div>
    </div>
  );
}
