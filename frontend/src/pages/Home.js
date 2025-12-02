import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateURLQR, generateFileQR } from '../services/api';
import './Home.css';

function Home() {
  const navigate = useNavigate();
  const [view, setView] = useState('main'); // main, generate, url, file
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleURLSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await generateURLQR(url);
      navigate(`/result/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.url?.[0] || 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await generateFileQR(file);
      navigate(`/result/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.file?.[0] || 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  // Main view with two buttons
  if (view === 'main') {
    return (
      <div className="home-container">
        <div className="main-buttons">
          <button className="main-btn generate-btn" onClick={() => setView('generate')}>
            <span className="btn-icon">🔲</span>
            <span className="btn-text">Generate QR Code</span>
            <span className="btn-desc">Create QR codes for URLs or files</span>
          </button>
          
          <button className="main-btn analytics-btn" onClick={() => navigate('/check-analytics')}>
            <span className="btn-icon">📊</span>
            <span className="btn-text">View Analytics</span>
            <span className="btn-desc">Track scans and view statistics</span>
          </button>
        </div>
      </div>
    );
  }

  // Generate options view
  if (view === 'generate') {
    return (
      <div className="home-container">
        <button className="back-btn" onClick={() => setView('main')}>
          ← Back
        </button>
        
        <h2 className="view-title">Choose QR Code Type</h2>
        
        <div className="option-buttons">
          <button className="option-btn" onClick={() => setView('url')}>
            <span className="option-icon">🔗</span>
            <span className="option-text">URL QR Code</span>
            <span className="option-desc">Generate QR code for any website link</span>
          </button>
          
          <button className="option-btn" onClick={() => setView('file')}>
            <span className="option-icon">📁</span>
            <span className="option-text">File QR Code</span>
            <span className="option-desc">Upload a file and generate QR code</span>
          </button>
        </div>
      </div>
    );
  }

  // URL form view
  if (view === 'url') {
    return (
      <div className="home-container">
        <button className="back-btn" onClick={() => setView('generate')}>
          ← Back
        </button>
        
        {error && <div className="error">{error}</div>}
        
        <div className="card">
          <h2 className="section-title">🔗 Generate QR from URL</h2>
          <form onSubmit={handleURLSubmit}>
            <div className="form-group">
              <label htmlFor="url">Enter URL</label>
              <input
                type="url"
                id="url"
                className="form-control"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Generating...' : 'Generate QR Code'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // File form view
  if (view === 'file') {
    return (
      <div className="home-container">
        <button className="back-btn" onClick={() => setView('generate')}>
          ← Back
        </button>
        
        {error && <div className="error">{error}</div>}
        
        <div className="card">
          <h2 className="section-title">📁 Generate QR from File</h2>
          <form onSubmit={handleFileSubmit}>
            <div className="form-group">
              <label htmlFor="file">Upload File</label>
              <input
                type="file"
                id="file"
                className="form-control"
                onChange={(e) => setFile(e.target.files[0])}
                required
              />
            </div>
            <button type="submit" className="btn" disabled={loading || !file}>
              {loading ? 'Generating...' : 'Generate QR Code'}
            </button>
          </form>
          <div className="info-box">
            <p>
              <strong>Note:</strong> A secure random link will be generated. 
              The actual file path will not be exposed.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default Home;
