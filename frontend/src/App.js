import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import QRResult from './pages/QRResult';
import Analytics from './pages/Analytics';
import CheckAnalytics from './pages/CheckAnalytics';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/result/:id" element={<QRResult />} />
            <Route path="/analytics/:id" element={<Analytics />} />
            <Route path="/check-analytics" element={<CheckAnalytics />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
