import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getQRCode, updateDynamicQR } from '../services/api';
import './QRResult.css';

function QRResult() {
  const { id } = useParams();
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newName, setNewName] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadQRCode();
  }, [id]);

  const loadQRCode = async () => {
    try {
      const data = await getQRCode(id);
      setQrCode(data);
      setNewUrl(data.content);
      setNewName(data.name || '');
    } catch (err) {
      setError('Failed to load QR code');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateDynamic = async () => {
    setUpdating(true);
    try {
      const response = await updateDynamicQR(id, { url: newUrl, name: newName });
      setQrCode(response.qr_code);
      setEditMode(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update QR code');
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleActive = async () => {
    setUpdating(true);
    try {
      const response = await updateDynamicQR(id, { is_active: !qrCode.is_active });
      setQrCode(response.qr_code);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update QR code');
    } finally {
      setUpdating(false);
    }
  };

  const downloadQR = (format) => {
    const baseUrl = window.location.hostname === 'localhost' 
      ? 'http://localhost:8000' 
      : 'https://ghulam.pythonanywhere.com';
    window.open(`${baseUrl}/download-qr/${id}/${format}/`, '_blank');
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!qrCode) return null;

  const getTypeLabel = (type) => {
    switch(type) {
      case 'url': return 'URL';
      case 'file': return 'File';
      case 'dynamic': return 'Dynamic';
      default: return type;
    }
  };

  return (
    <div className="card">
      <div className="qr-result-container">
        <h2 className="section-title">✨ Your QR Code is Ready!</h2>

        <div className="qr-display">
          <img
            src={qrCode.qr_image}
            alt="Generated QR Code"
            className="qr-code-image"
            onError={(e) => {
              console.error('Image failed to load:', qrCode.qr_image);
              e.target.style.display = 'none';
            }}
          />
        </div>

        <div className="qr-info-card">
          <p>
            <strong>Type:</strong>
            <span className={`type-badge ${qrCode.qr_type}`}>
              {getTypeLabel(qrCode.qr_type)}
            </span>
          </p>
          {qrCode.name && (
            <p><strong>Name:</strong> {qrCode.name}</p>
          )}
          {qrCode.qr_type === 'url' && (
            <p><strong>URL:</strong> {qrCode.content}</p>
          )}
          {qrCode.qr_type === 'file' && qrCode.uploaded_file && (
            <>
              <p><strong>File:</strong> {qrCode.uploaded_file.original_filename}</p>
              <p className="success-text">✓ File is accessible via secure random link</p>
            </>
          )}
          {qrCode.qr_type === 'dynamic' && (
            <>
              <p><strong>Destination:</strong> {qrCode.content}</p>
              <p><strong>Redirect URL:</strong> {qrCode.redirect_url}</p>
              <p>
                <strong>Status:</strong>
                <span className={qrCode.is_active ? 'status-active' : 'status-inactive'}>
                  {qrCode.is_active ? ' ✅ Active' : ' ❌ Inactive'}
                </span>
              </p>
            </>
          )}
          <p><strong>Created:</strong> {new Date(qrCode.created_at).toLocaleString()}</p>
          {qrCode.updated_at && qrCode.qr_type === 'dynamic' && (
            <p><strong>Last Updated:</strong> {new Date(qrCode.updated_at).toLocaleString()}</p>
          )}
        </div>

        {/* Dynamic QR Edit Section */}
        {qrCode.qr_type === 'dynamic' && (
          <div className="dynamic-settings">
            <h3>🔄 Dynamic QR Settings</h3>
            
            {editMode ? (
              <div className="dynamic-edit-form">
                <div className="form-group">
                  <label>Name</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="QR Code Name"
                  />
                </div>
                <div className="form-group">
                  <label>Destination URL</label>
                  <input
                    type="url"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
                <div className="dynamic-edit-actions">
                  <button onClick={handleUpdateDynamic} disabled={updating} className="btn btn-success">
                    {updating ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button onClick={() => setEditMode(false)} className="btn btn-secondary">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="dynamic-actions">
                <button onClick={() => setEditMode(true)} className="btn btn-edit">
                  ✏️ Edit Destination
                </button>
                <button
                  onClick={handleToggleActive}
                  disabled={updating}
                  className={`btn ${qrCode.is_active ? 'btn-toggle-inactive' : 'btn-toggle-active'}`}
                >
                  {updating ? 'Updating...' : qrCode.is_active ? '🚫 Disable QR' : '✅ Enable QR'}
                </button>
              </div>
            )}
          </div>
        )}

        <div className="download-section">
          <h3>📥 Download QR Code</h3>
          <div className="download-buttons">
            {['png', 'jpg', 'jpeg', 'webp', 'bmp', 'svg'].map((format) => (
              <button
                key={format}
                onClick={() => downloadQR(format)}
                className="download-btn"
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="result-nav">
          <Link to="/" className="btn btn-secondary">
            ← Generate Another
          </Link>
          {(qrCode.qr_type === 'file' || qrCode.qr_type === 'dynamic') && (
            <Link to={`/analytics/${id}`} className="btn btn-success">
              📊 View Analytics
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default QRResult;
