import { useState, useEffect, useCallback } from 'react';
import { Globe, Play, RefreshCcw, CheckCircle, XCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getAPIConfig, simulateAppAPI } from '../services/api';

const CATEGORY_COLORS = {
  ecommerce: '#6366f1',
  user: '#10b981',
  logistics: '#f59e0b',
  financial: '#ef4444',
  external: '#8b5cf6',
};

const API_CATEGORIES = {
  ecommerce: ['payment_A', 'payment_B', 'inventory', 'cart', 'order', 'recommendation'],
  user: ['authentication', 'profile', 'preferences'],
  logistics: ['delivery', 'tracking', 'warehouse'],
  financial: ['fraud_detection', 'billing'],
  external: ['external_payment', 'external_shipping'],
};

export default function ApiExplorer() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(null);
  const [results, setResults] = useState({});
  const [retryMap, setRetryMap] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAPIConfig();
      setConfig(res.data);
    } catch {
      setConfig(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleSimulate(apiName) {
    setSimulating(apiName);
    try {
      const res = await simulateAppAPI({ api_name: apiName, retry: retryMap[apiName] || false });
      setResults(prev => ({ ...prev, [apiName]: { ...res.data, ts: new Date().toLocaleTimeString() } }));
    } catch (e) {
      setResults(prev => ({ ...prev, [apiName]: { error: e.response?.data?.detail || 'Failed', ts: new Date().toLocaleTimeString() } }));
    }
    setSimulating(null);
  }

  async function handleSimulateAll() {
    for (const apiName of Object.keys(config || {})) {
      await handleSimulate(apiName);
    }
  }

  if (loading) return <LoadingSpinner text="Loading API configuration..." />;

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><Globe size={28} /> <span className="gradient-text">API Explorer</span></h1>
          <p>Browse all 16 simulated APIs and test them individually</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={load}>
            <RefreshCcw size={14} /> Reload Config
          </button>
          <button className="btn btn-primary" onClick={handleSimulateAll} disabled={!!simulating}>
            <Play size={14} /> Simulate All
          </button>
        </div>
      </div>

      {!config ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔌</div>
          <div className="empty-state-title">Backend Unreachable</div>
          <div className="empty-state-text">Start the backend: <code>uvicorn api.main:app --port 8000 --reload</code></div>
        </div>
      ) : (
        Object.entries(API_CATEGORIES).map(([category, apis]) => (
          <div key={category} style={{ marginBottom: 28 }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14,
              paddingBottom: 8, borderBottom: `2px solid ${CATEGORY_COLORS[category]}33`,
            }}>
              <span style={{
                padding: '3px 12px', borderRadius: 999, fontSize: 12, fontWeight: 700,
                background: `${CATEGORY_COLORS[category]}22`, color: CATEGORY_COLORS[category],
                textTransform: 'uppercase', letterSpacing: '0.05em',
              }}>{category}</span>
              <span style={{ color: '#64748b', fontSize: 12 }}>{apis.length} endpoints</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
              {apis.map(apiName => {
                const cfg = config[apiName];
                const result = results[apiName];
                const isSim = simulating === apiName;

                return (
                  <div key={apiName} className="chart-card" style={{ padding: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                      <div>
                        <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 14 }}>{apiName}</div>
                        {cfg && (
                          <div style={{ fontSize: 11, color: '#64748b', marginTop: 3 }}>
                            Latency: {cfg.latency[0]}–{cfg.latency[1]} ms &nbsp;·&nbsp;
                            Cost: ${cfg.cost} &nbsp;·&nbsp;
                            Success: {(cfg.success_prob * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                      <button
                        className="btn btn-primary"
                        style={{ padding: '5px 12px', fontSize: 12 }}
                        onClick={() => handleSimulate(apiName)}
                        disabled={isSim}
                      >
                        {isSim ? '…' : <><Play size={12} /> Run</>}
                      </button>
                    </div>

                    {/* Retry toggle */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8', cursor: 'pointer', marginBottom: 10 }}>
                      <input type="checkbox" checked={retryMap[apiName] || false}
                        onChange={e => setRetryMap(p => ({ ...p, [apiName]: e.target.checked }))} />
                      Retry mode (+20ms latency)
                    </label>

                    {/* Result */}
                    {result && (
                      <div style={{
                        padding: '10px 12px', borderRadius: 8, fontSize: 12,
                        background: result.error
                          ? 'rgba(239,68,68,0.08)'
                          : result.success ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                        border: `1px solid ${result.error || !result.success ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'}`,
                      }}>
                        {result.error ? (
                          <div style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <XCircle size={13} /> {result.error}
                          </div>
                        ) : (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                              {result.success
                                ? <CheckCircle size={12} style={{ color: '#10b981' }} />
                                : <XCircle size={12} style={{ color: '#ef4444' }} />}
                              <span style={{ color: result.success ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                                {result.success ? 'Success' : 'Failed'}
                              </span>
                            </div>
                            <div style={{ color: '#94a3b8' }}>@ {result.ts}</div>
                            <div style={{ color: '#f59e0b' }}>⏱ {(result.latency ?? 0).toFixed(1)} ms</div>
                            <div style={{ color: '#ef4444' }}>💰 ${(result.cost ?? 0).toFixed(3)}</div>
                            <div style={{ color: '#64748b' }}>Load: {(result.system_load ?? 0).toFixed(3)}</div>
                            {result.log_id && <div style={{ color: '#64748b' }}>Log #{result.log_id}</div>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
