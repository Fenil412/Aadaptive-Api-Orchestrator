import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Simulate from './pages/Simulate';
import Logs from './pages/Logs';
import Compare from './pages/Compare';
import Metrics from './pages/Metrics';
import Train from './pages/Train';
import ApiExplorer from './pages/ApiExplorer';
import { healthCheck } from './services/api';
import './App.css';

export default function App() {
  const [health, setHealth] = useState({ model_loaded: false, db_connected: false, status: 'unknown' });

  useEffect(() => {
    healthCheck()
      .then(res => setHealth(res.data || {}))
      .catch(() => setHealth({ model_loaded: false, db_connected: false, status: 'offline' }));
  }, []);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar health={health} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/simulate" element={<Simulate />} />
            <Route path="/explorer" element={<ApiExplorer />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/train" element={<Train />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
