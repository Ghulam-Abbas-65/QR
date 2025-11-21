import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getQRCodes } from '../services/api';

function CheckAnalytics() {
  const [qrCodes, setQrCodes] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQRCodes();
  }, []);

  const loadQRCodes = async (searchQuery = '') => {
    setLoading(true);
    try {
      const data = await getQRCodes(searchQuery);
      setQrCodes(data);
    } catch (err) {
      console.error('Failed to load QR codes', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadQRCodes(search);
  };

  return (
    <div className="card">
      <h2 className="section-title">📊 Check QR Code Analytics</h2>

      <p style={{ color: '#666', marginBottom: '20px' }}>
        Search for your QR code by ID, filename, or URL to view its analytics.
      </p>

      <form onSubmit={handleSearch} style={{ marginBottom: '30px' }}>
        <div className="form-group">
          <label htmlFor="search">Search QR Codes</label>
          <input
            type="text"
            id="search"
            className="form-control"
            placeholder="Enter QR ID, filename, or URL..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button type="submit" className="btn">
          Search
        </button>
      </form>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : qrCodes.length > 0 ? (
        <div>
          <h3 style={{ marginBottom: '15px', color: '#333' }}>
            {search ? 'Search Results' : 'Recent QR Codes'}
          </h3>
          {qrCodes.map((qr) => (
            <div
              key={qr.id}
              style={{
                background: '#f8f9fa',
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '15px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                border: '2px solid #e0e0e0',
              }}
            >
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flex: 1 }}>
                <img
                  src={qr.qr_image}
                  alt="QR Code"
                  style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '8px',
                    border: '2px solid #667eea',
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div style={{ flex: 1 }}>
                  <div>
                    <strong>ID:</strong> {qr.id}
                  </div>
                  <div>
                    <strong>Type:</strong> {qr.qr_type === 'url' ? 'URL' : 'File'}
                  </div>
                  {qr.qr_type === 'file' ? (
                    <div>
                      <strong>File:</strong> {qr.uploaded_file.original_filename}
                    </div>
                  ) : (
                    <div>
                      <strong>URL:</strong> {qr.content.substring(0, 50)}...
                    </div>
                  )}
                  <div style={{ color: '#999', fontSize: '0.9em' }}>
                    Created: {new Date(qr.created_at).toLocaleString()}
                  </div>
                  <div style={{ color: '#667eea', fontWeight: '600', marginTop: '5px' }}>
                    Total Scans: {qr.scan_count}
                  </div>
                </div>
              </div>
              <div style={{ marginLeft: '20px' }}>
                {qr.qr_type === 'file' ? (
                  <Link
                    to={`/analytics/${qr.id}`}
                    className="btn"
                    style={{ width: 'auto', padding: '8px 20px', fontSize: '0.9rem' }}
                  >
                    View Analytics
                  </Link>
                ) : (
                  <span style={{ color: '#999', fontSize: '0.9em' }}>
                    No analytics for URL QR codes
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="info-box">
          <p style={{ textAlign: 'center', color: '#999' }}>
            {search
              ? `No QR codes found matching "${search}"`
              : 'No QR codes generated yet. Create one first!'}
          </p>
        </div>
      )}

      <div className="info-box" style={{ marginTop: '30px' }}>
        <h3 style={{ marginBottom: '10px' }}>💡 Tips:</h3>
        <ul style={{ marginLeft: '20px', color: '#666' }}>
          <li>Search by QR code ID (e.g., "1", "2", "3")</li>
          <li>Search by filename (e.g., "document.pdf")</li>
          <li>Search by URL content</li>
          <li>Leave blank to see recent QR codes</li>
        </ul>
        <p style={{ color: '#999', marginTop: '15px', fontSize: '0.9em' }}>
          <strong>Note:</strong> Only file-based QR codes have analytics tracking.
        </p>
      </div>
    </div>
  );
}

export default CheckAnalytics;
