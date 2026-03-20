import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  BarChart3,
  ScrollText,
  GitCompare,
  Settings,
  Brain,
} from 'lucide-react';

const navItems = [
  { label: 'Overview', section: 'MAIN' },
  { to: '/', icon: LayoutDashboard, text: 'Dashboard' },
  { to: '/simulate', icon: Zap, text: 'Simulate' },
  { label: 'Analysis', section: 'DATA' },
  { to: '/logs', icon: ScrollText, text: 'API Logs' },
  { to: '/compare', icon: GitCompare, text: 'Compare' },
  { to: '/metrics', icon: BarChart3, text: 'Metrics' },
  { label: 'System', section: 'SYSTEM' },
  { to: '/train', icon: Brain, text: 'Train Model' },
  { to: '/settings', icon: Settings, text: 'Settings' },
];

export default function Sidebar({ modelLoaded }) {
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
          item.label ? (
            <div key={idx} className="sidebar-section-label">
              {item.label}
            </div>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-link${isActive ? ' active' : ''}`
              }
              end={item.to === '/'}
            >
              <item.icon />
              <span>{item.text}</span>
            </NavLink>
          )
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot${modelLoaded ? '' : ' offline'}`} />
          <span>{modelLoaded ? 'Model Active' : 'No Model Loaded'}</span>
        </div>
      </div>
    </aside>
  );
}
