import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Header from './components/Header';
import PrivateRoute from './components/PrivateRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import QRResult from './pages/QRResult';
import Analytics from './pages/Analytics';
import CheckAnalytics from './pages/CheckAnalytics';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <div className="container">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } />
              <Route path="/result/:id" element={
                <PrivateRoute>
                  <QRResult />
                </PrivateRoute>
              } />
              <Route path="/analytics/:id" element={
                <PrivateRoute>
                  <Analytics />
                </PrivateRoute>
              } />
              <Route path="/check-analytics" element={
                <PrivateRoute>
                  <CheckAnalytics />
                </PrivateRoute>
              } />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
