import { useState, useEffect, useCallback } from 'react';
import { ScrollText, RefreshCcw, Filter } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getAppLogs } from '../services/api';

const API_NAMES = [
  '', 'payment_A', 'payment_B', 'inventory', 'cart', 'order', 'recommendation',
  'authentication', 'profile', 'preferences', 'delivery', 'tracking', 'warehouse',
  'fraud_detection', 'billing', 'external_payment', 'external_shipping',
];

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [limit, setLimit] = useState(200);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAppLogs(limit, filter || null);
      setLogs(res.data || []);
    } catch {
      setLogs([]);
    }
    setLoading(false);
  }, [limit, filter]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Loading API logs from database..." />;

  const successCount = logs.filter(l => l.success).length;
  const failCount = logs.length - successCount;
  const avgLatency = logs.length ? (logs.reduce((s, l) => s + (l.latency || 0), 0) / logs.length).toFixed(1) : '0';

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><ScrollText size={28} /> <span className="gradient-text">API Logs</span></h1>
          <p>All API call records stored in the database</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load}>
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      {/* Summary bar */}
      <div className="stats-grid stagger-children" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Records</div>
          <div className="stat-card-value">{logs.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Successful</div>
          <div className="stat-card-value" style={{ color: '#10b981' }}>{successCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Failed</div>
          <div className="stat-card-value" style={{ color: '#ef4444' }}>{failCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Avg Latency</div>
          <div className="stat-card-value" style={{ color: '#f59e0b' }}>{avgLatency} ms</div>
        </div>
      </div>

      {/* Filters */}
      <div className="control-panel" style={{ marginBottom: 20, padding: '14px 20px' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <Filter size={14} style={{ color: '#64748b' }} />
          <div>
            <label className="control-label" style={{ marginRight: 8 }}>API Filter</label>
            <select value={filter} onChange={e => setFilter(e.target.value)}
              style={{ background: 'var(--bg-card)', color: 'white', padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}>
              {API_NAMES.map(n => <option key={n} value={n}>{n || 'All APIs'}</option>)}
            </select>
          </div>
          <div>
            <label className="control-label" style={{ marginRight: 8 }}>Limit</label>
            <select value={limit} onChange={e => setLimit(Number(e.target.value))}
              style={{ background: 'var(--bg-card)', color: 'white', padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}>
              {[50, 100, 200, 500].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>
      </div>

      {logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No Logs Found</div>
          <div className="empty-state-text">Run simulations on the Simulate page or seed the DB first.</div>
        </div>
      ) : (
        <div className="logs-table-wrapper">
          <table className="logs-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>API Endpoint</th>
                <th>Action Taken</th>
                <th>Latency (ms)</th>
                <th>Cost ($)</th>
                <th>System Load</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={log.id || i}>
                  <td style={{ color: '#64748b' }}>{log.id || i + 1}</td>
                  <td style={{ fontSize: 12 }}>{log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}</td>
                  <td><span className="provider-badge">{log.api_name || '—'}</span></td>
                  <td><span className="provider-badge" style={{ background: 'rgba(139,92,246,0.12)', color: '#a78bfa' }}>{log.action_taken || '—'}</span></td>
                  <td style={{ color: '#f59e0b' }}>{(log.latency ?? 0).toFixed(1)}</td>
                  <td style={{ color: '#ef4444' }}>{(log.cost ?? 0).toFixed(3)}</td>
                  <td style={{ color: '#64748b' }}>{(log.system_load ?? 0).toFixed(3)}</td>
                  <td>
                    <span style={{
                      padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 700,
                      background: log.success ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                      color: log.success ? '#10b981' : '#ef4444',
                    }}>
                      {log.success ? '✓ OK' : '✗ Fail'}
                    </span>
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
