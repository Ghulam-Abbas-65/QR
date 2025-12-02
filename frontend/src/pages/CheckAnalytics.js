import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getQRCodes, updateDynamicQR } from '../services/api';

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
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {['all', 'url', 'file', 'dynamic'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '20px',
              cursor: 'pointer',
              background: filter === type ? '#667eea' : '#e0e0e0',
              color: filter === type ? 'white' : '#333',
              fontWeight: '600',
            }}
          >
            {type === 'all' ? '📋 All' : getTypeLabel(type)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : filteredQRCodes.length > 0 ? (
        <div>
          <h3 style={{ marginBottom: '15px', color: '#333' }}>
            {search ? 'Search Results' : 'Your QR Codes'} ({filteredQRCodes.length})
          </h3>
          {filteredQRCodes.map((qr) => (
            <div
              key={qr.id}
              style={{
                background: '#f8f9fa',
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '15px',
                border: qr.qr_type === 'dynamic' ? '2px solid #667eea' : '2px solid #e0e0e0',
              }}
            >
              <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
                <img
                  src={qr.qr_image}
                  alt="QR Code"
                  style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '8px',
                    border: '2px solid #667eea',
                  }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '5px' }}>
                    <span style={{ 
                      background: qr.qr_type === 'dynamic' ? '#667eea' : qr.qr_type === 'file' ? '#28a745' : '#6c757d',
                      color: 'white',
                      padding: '2px 10px',
                      borderRadius: '12px',
                      fontSize: '0.8em'
                    }}>
                      {getTypeLabel(qr.qr_type)}
                    </span>
                    {qr.name && <strong>{qr.name}</strong>}
                    {qr.qr_type === 'dynamic' && (
                      <span style={{ color: qr.is_active ? '#28a745' : '#dc3545', fontSize: '0.9em' }}>
                        {qr.is_active ? '✅ Active' : '❌ Inactive'}
                      </span>
                    )}
                  </div>
                  
                  {qr.qr_type === 'file' && qr.uploaded_file && (
                    <div><strong>File:</strong> {qr.uploaded_file.original_filename}</div>
                  )}
                  
                  <div style={{ fontSize: '0.9em', color: '#666', wordBreak: 'break-all' }}>
                    <strong>Destination:</strong> {qr.content.substring(0, 60)}{qr.content.length > 60 ? '...' : ''}
                  </div>
                  
                  <div style={{ display: 'flex', gap: '20px', marginTop: '8px', fontSize: '0.9em' }}>
                    <span style={{ color: '#667eea', fontWeight: '600' }}>
                      📊 {qr.scan_count} scans
                    </span>
                    <span style={{ color: '#999' }}>
                      Created: {new Date(qr.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Dynamic QR Edit Section */}
                  {qr.qr_type === 'dynamic' && editingId === qr.id && (
                    <div style={{ marginTop: '15px', padding: '15px', background: 'white', borderRadius: '8px' }}>
                      <input
                        type="url"
                        value={editUrl}
                        onChange={(e) => setEditUrl(e.target.value)}
                        placeholder="New destination URL"
                        style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ddd', marginBottom: '10px' }}
                      />
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button
                          onClick={() => handleUpdateDynamic(qr.id)}
                          disabled={updating}
                          style={{ padding: '8px 16px', background: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                        >
                          {updating ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          style={{ padding: '8px 16px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <Link
                    to={`/analytics/${qr.id}`}
                    style={{
                      padding: '8px 16px',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      borderRadius: '6px',
                      textDecoration: 'none',
                      fontSize: '0.9em',
                      textAlign: 'center',
                    }}
                  >
                    📊 Analytics
                  </Link>
                  <Link
                    to={`/result/${qr.id}`}
                    style={{
                      padding: '8px 16px',
                      background: '#6c757d',
                      color: 'white',
                      borderRadius: '6px',
                      textDecoration: 'none',
                      fontSize: '0.9em',
                      textAlign: 'center',
                    }}
                  >
                    👁️ View
                  </Link>
                  {qr.qr_type === 'dynamic' && editingId !== qr.id && (
                    <button
                      onClick={() => { setEditingId(qr.id); setEditUrl(qr.content); }}
                      style={{
                        padding: '8px 16px',
                        background: '#ffc107',
                        color: '#333',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.9em',
                      }}
                    >
                      ✏️ Edit
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="info-box">
          <p style={{ textAlign: 'center', color: '#999' }}>
            {search ? `No QR codes found matching "${search}"` : 'No QR codes generated yet. Create one first!'}
          </p>
        </div>
      )}
    </div>
  );
}

export default CheckAnalytics;
