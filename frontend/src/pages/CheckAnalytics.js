import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getQRCodes, updateDynamicQR } from '../services/api';
import './CheckAnalytics.css';

function CheckAnalytics() {
  const [qrCodes, setQrCodes] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, url, file, dynamic
  const [editingId, setEditingId] = useState(null);
  const [editUrl, setEditUrl] = useState('');
  const [updating, setUpdating] = useState(false);

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

  const handleUpdateDynamic = async (qrId) => {
    setUpdating(true);
    try {
      const response = await updateDynamicQR(qrId, { url: editUrl });
      setQrCodes(qrCodes.map(qr => qr.id === qrId ? response.qr_code : qr));
      setEditingId(null);
    } catch (err) {
      alert('Failed to update QR code');
    } finally {
      setUpdating(false);
    }
  };

  const getTypeLabel = (type) => {
    switch(type) {
      case 'url': return '🔗 URL';
      case 'file': return '📁 File';
      case 'dynamic': return '🔄 Dynamic';
      default: return type;
    }
  };

  const filteredQRCodes = filter === 'all' 
    ? qrCodes 
    : qrCodes.filter(qr => qr.qr_type === filter);

  return (
    <div className="card">
      <h2 className="section-title">📊 My QR Codes & Analytics</h2>

      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <div className="form-group">
          <label htmlFor="search">Search QR Codes</label>
          <input
            type="text"
            id="search"
            className="form-control"
            placeholder="Enter QR ID, filename, name, or URL..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button type="submit" className="btn">Search</button>
      </form>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        {['all', 'url', 'file', 'dynamic'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`filter-tab ${filter === type ? 'active' : ''}`}
          >
            {type === 'all' ? '📋 All' : getTypeLabel(type)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : filteredQRCodes.length > 0 ? (
        <div>
          <div className="results-header">
            <h3 className="results-title">{search ? 'Search Results' : 'Your QR Codes'}</h3>
            <span className="results-count">{filteredQRCodes.length} items</span>
          </div>
          <div className="qr-grid">
            {filteredQRCodes.map((qr) => (
              <div key={qr.id} className={`qr-card ${qr.qr_type}`}>
                <div className="qr-card-content">
                  <img
                    src={qr.qr_image}
                    alt="QR Code"
                    className="qr-image"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                  <div className="qr-info">
                    <div className="qr-header">
                      <span className={`qr-type-badge ${qr.qr_type}`}>
                        {getTypeLabel(qr.qr_type)}
                      </span>
                      {qr.name && <span className="qr-name">{qr.name}</span>}
                      {qr.qr_type === 'dynamic' && (
                        <span className={`qr-status ${qr.is_active ? 'active' : 'inactive'}`}>
                          {qr.is_active ? '✅ Active' : '❌ Inactive'}
                        </span>
                      )}
                    </div>
                    
                    {qr.qr_type === 'file' && qr.uploaded_file && (
                      <div className="qr-destination">
                        <strong>File:</strong> {qr.uploaded_file.original_filename}
                      </div>
                    )}
                    
                    <div className="qr-destination">
                      <strong>Destination:</strong> {qr.content.substring(0, 80)}{qr.content.length > 80 ? '...' : ''}
                    </div>
                    
                    <div className="qr-meta">
                      <span className="qr-scans">📊 {qr.scan_count} scans</span>
                      <span className="qr-date">Created: {new Date(qr.created_at).toLocaleDateString()}</span>
                    </div>

                    {/* Dynamic QR Edit Section */}
                    {qr.qr_type === 'dynamic' && editingId === qr.id && (
                      <div className="edit-form">
                        <input
                          type="url"
                          value={editUrl}
                          onChange={(e) => setEditUrl(e.target.value)}
                          placeholder="New destination URL"
                        />
                        <div className="edit-actions">
                          <button
                            onClick={() => handleUpdateDynamic(qr.id)}
                            disabled={updating}
                            className="edit-btn save"
                          >
                            {updating ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="edit-btn cancel"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="qr-actions">
                    <Link to={`/analytics/${qr.id}`} className="action-btn analytics">
                      📊 Analytics
                    </Link>
                    <Link to={`/result/${qr.id}`} className="action-btn view">
                      👁️ View
                    </Link>
                    {qr.qr_type === 'dynamic' && editingId !== qr.id && (
                      <button
                        onClick={() => { setEditingId(qr.id); setEditUrl(qr.content); }}
                        className="action-btn edit"
                      >
                        ✏️ Edit
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>{search ? `No QR codes found matching "${search}"` : 'No QR codes generated yet.'}</p>
          {!search && (
            <Link to="/" className="btn">Create Your First QR Code</Link>
          )}
        </div>
      )}
    </div>
  );
}

export default CheckAnalytics;
