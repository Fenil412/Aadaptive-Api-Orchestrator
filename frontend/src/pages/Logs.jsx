import { useState, useEffect } from 'react';
import { ScrollText, RefreshCcw } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getAPILogs } from '../services/api';

const PROVIDER_BADGES = {};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  async function loadLogs() {
    setLoading(true);
    try {
      const res = await getAPILogs(200);
      const data = res.data.map(log => ({
        ...log,
        provider: log.api_name || 'unknown',
      }));
      setLogs(data);
    } catch {
      // Empty fallback
      setLogs([]);
    }
    setLoading(false);
  }

  if (loading) return <LoadingSpinner text="Loading logs..." />;

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1><ScrollText size={28} /> <span className="gradient-text">API Logs</span></h1>
          <p>Complete history of API routing decisions and outcomes</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadLogs}>
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      {logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No Logs Yet</div>
          <div className="empty-state-text">Run some simulations to generate API logs.</div>
        </div>
      ) : (
        <div className="logs-table-wrapper">
          <table className="logs-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>API Endpoint</th>
                <th>Latency (ms)</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={log.id || i}>
                  <td>{log.id || i + 1}</td>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>
                    <span className="provider-badge">
                      {log.provider}
                    </span>
                  </td>
                  <td>{log.latency?.toFixed(1)}</td>
                  <td>${log.cost?.toFixed(3)}</td>
                  <td>
                    <span className={`success-badge ${log.success ? 'success' : 'failure'}`}>
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
