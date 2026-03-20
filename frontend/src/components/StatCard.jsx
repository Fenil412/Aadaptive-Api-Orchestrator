export default function StatCard({ icon, label, value, trend, trendDir, color }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <div className={`stat-card-icon ${color || 'purple'}`}>{icon}</div>
      </div>
      <div className="stat-card-value">{value}</div>
      {trend && (
        <div className={`stat-card-trend ${trendDir || 'stable'}`}>
          {trendDir === 'up' ? '▲' : trendDir === 'down' ? '▼' : '●'} {trend}
        </div>
      )}
    </div>
  );
}
