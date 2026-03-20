export default function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <span className="loading-text">{text}</span>
    </div>
  );
}
