import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Simulate from './pages/Simulate';
import Logs from './pages/Logs';
import Compare from './pages/Compare';
import Metrics from './pages/Metrics';
import Train from './pages/Train';
import Settings from './pages/Settings';
import { healthCheck } from './services/api';
import './App.css';

export default function App() {
  const [modelLoaded, setModelLoaded] = useState(false);

  useEffect(() => {
    healthCheck()
      .then(res => setModelLoaded(res.data?.model_loaded || false))
      .catch(() => setModelLoaded(false));
  }, []);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar modelLoaded={modelLoaded} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/simulate" element={<Simulate />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/train" element={<Train />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
