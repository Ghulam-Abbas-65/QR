import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getQRCode, updateDynamicQR } from '../services/api';

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

  return (
    <div className="card">
      <div style={{ textAlign: 'center' }}>
        <h2 className="section-title">Your QR Code is Ready!</h2>

        <img
          src={qrCode.qr_image}
          alt="Generated QR Code"
          style={{
            maxWidth: '400px',
            width: '100%',
            border: '3px solid #667eea',
            borderRadius: '12px',
            margin: '20px 0',
          }}
          onError={(e) => {
            console.error('Image failed to load:', qrCode.qr_image);
            e.target.style.display = 'none';
          }}
        />

        <div className="info-box">
          <p>
            <strong>Type:</strong> {qrCode.qr_type === 'url' ? 'URL' : qrCode.qr_type === 'file' ? 'File' : 'Dynamic'}
          </p>
          {qrCode.name && (
            <p><strong>Name:</strong> {qrCode.name}</p>
          )}
          {qrCode.qr_type === 'url' && (
            <p>
              <strong>URL:</strong> {qrCode.content}
            </p>
          )}
          {qrCode.qr_type === 'file' && qrCode.uploaded_file && (
            <>
              <p>
                <strong>File:</strong> {qrCode.uploaded_file.original_filename}
              </p>
              <p style={{ color: '#28a745', marginTop: '10px' }}>
                ✓ File is accessible via secure random link (completely hidden)
              </p>
            </>
          )}
          {qrCode.qr_type === 'dynamic' && (
            <>
              <p>
                <strong>Current Destination:</strong> {qrCode.content}
              </p>
              <p>
                <strong>Redirect URL:</strong> {qrCode.redirect_url}
              </p>
              <p>
                <strong>Status:</strong>{' '}
                <span style={{ color: qrCode.is_active ? '#28a745' : '#dc3545' }}>
                  {qrCode.is_active ? '✅ Active' : '❌ Inactive'}
                </span>
              </p>
            </>
          )}
          <p>
            <strong>Created:</strong>{' '}
            {new Date(qrCode.created_at).toLocaleString()}
          </p>
          {qrCode.updated_at && qrCode.qr_type === 'dynamic' && (
            <p>
              <strong>Last Updated:</strong>{' '}
              {new Date(qrCode.updated_at).toLocaleString()}
            </p>
          )}
        </div>

        {/* Dynamic QR Edit Section */}
        {qrCode.qr_type === 'dynamic' && (
          <div style={{ marginTop: '20px', padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '15px', color: '#333' }}>🔄 Dynamic QR Settings</h3>
            
            {editMode ? (
              <div>
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Name</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="QR Code Name"
                    style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ddd' }}
                  />
                </div>
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>Destination URL</label>
                  <input
                    type="url"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    placeholder="https://example.com"
                    style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ddd' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={handleUpdateDynamic}
                    disabled={updating}
                    style={{ padding: '10px 20px', background: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    {updating ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={() => setEditMode(false)}
                    style={{ padding: '10px 20px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => setEditMode(true)}
                  style={{ padding: '10px 20px', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                >
                  ✏️ Edit Destination
                </button>
                <button
                  onClick={handleToggleActive}
                  disabled={updating}
                  style={{ 
                    padding: '10px 20px', 
                    background: qrCode.is_active ? '#dc3545' : '#28a745', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '6px', 
                    cursor: 'pointer' 
                  }}
                >
                  {updating ? 'Updating...' : qrCode.is_active ? '🚫 Disable QR' : '✅ Enable QR'}
                </button>
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '20px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '10px', color: '#333' }}>
            Download QR Code
          </h3>
          <div
            style={{
              display: 'flex',
              gap: '10px',
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            {['png', 'jpg', 'jpeg', 'webp', 'bmp', 'svg'].map((format) => (
              <button
                key={format}
                onClick={() => downloadQR(format)}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                }}
                onMouseOver={(e) => (e.target.style.transform = 'translateY(-2px)')}
                onMouseOut={(e) => (e.target.style.transform = 'translateY(0)')}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/" className="btn btn-secondary" style={{ width: 'auto', display: 'inline-block' }}>
            Generate Another
          </Link>
          {(qrCode.qr_type === 'file' || qrCode.qr_type === 'dynamic') && (
            <Link
              to={`/analytics/${id}`}
              className="btn"
              style={{ width: 'auto', background: '#28a745', display: 'inline-block' }}
            >
              📊 View Analytics
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default QRResult;
