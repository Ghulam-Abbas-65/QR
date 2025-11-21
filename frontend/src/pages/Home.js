import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateURLQR, generateFileQR } from '../services/api';

function Home() {
  const navigate = useNavigate();
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

  return (
    <>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h2 className="section-title">Generate QR from URL</h2>
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

      <div className="card">
        <h2 className="section-title">Generate QR from File</h2>
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
            <strong>Note:</strong> When you upload a file, a secure random link
            will be generated. The actual file path will not be exposed to users.
          </p>
        </div>
      </div>
    </>
  );
}

export default Home;
