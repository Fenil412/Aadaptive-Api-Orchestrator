export default function ChartCard({ title, subtitle, children, fullWidth }) {
  return (
    <div className={`chart-card${fullWidth ? ' full-width' : ''}`}>
      <div className="chart-card-header">
        <div>
          <div className="chart-card-title">{title}</div>
          {subtitle && <div className="chart-card-subtitle">{subtitle}</div>}
        </div>
      </div>
      <div className="chart-container">{children}</div>
    </div>
  );
}
