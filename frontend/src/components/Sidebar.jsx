import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Zap, Globe, ScrollText,
  GitCompare, BarChart3, Brain,
} from 'lucide-react';

const navItems = [
  { section: 'MAIN' },
  { to: '/', icon: LayoutDashboard, text: 'Dashboard' },
  { to: '/simulate', icon: Zap, text: 'Simulate' },
  { to: '/explorer', icon: Globe, text: 'API Explorer' },
  { section: 'ANALYSIS' },
  { to: '/logs', icon: ScrollText, text: 'API Logs' },
  { to: '/compare', icon: GitCompare, text: 'Compare' },
  { to: '/metrics', icon: BarChart3, text: 'Metrics' },
  { section: 'SYSTEM' },
  { to: '/train', icon: Brain, text: 'Train Model' },
];

export default function Sidebar({ health = {} }) {
  const { model_loaded, db_connected, status } = health;
  const online = status === 'ok' || status === 'healthy';

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">⚡</div>
        <div>
          <div className="sidebar-title">API Orchestrator</div>
          <div className="sidebar-subtitle">RL-Powered Routing</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item, idx) =>
          item.section ? (
            <div key={idx} className="sidebar-section-label">{item.section}</div>
          ) : (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <item.icon size={16} />
              <span>{item.text}</span>
            </NavLink>
          )
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status" style={{ flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`status-dot${online ? '' : ' offline'}`} />
            <span style={{ fontSize: 11 }}>Backend: {online ? 'Online' : 'Offline'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`status-dot${model_loaded ? '' : ' offline'}`} />
            <span style={{ fontSize: 11 }}>Model: {model_loaded ? 'Loaded' : 'Not loaded'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`status-dot${db_connected ? '' : ' offline'}`} />
            <span style={{ fontSize: 11 }}>DB: {db_connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
