import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getQRCode } from '../services/api';

function QRResult() {
  const { id } = useParams();
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQRCode();
  }, [id]);

  const loadQRCode = async () => {
    try {
      const data = await getQRCode(id);
      setQrCode(data);
    } catch (err) {
      setError('Failed to load QR code');
    } finally {
      setLoading(false);
    }
  };

  const downloadQR = (format) => {
    window.open(`http://localhost:8000/download-qr/${id}/${format}/`, '_blank');
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
            <strong>Type:</strong> {qrCode.qr_type === 'url' ? 'URL' : 'File'}
          </p>
          {qrCode.qr_type === 'url' ? (
            <p>
              <strong>URL:</strong> {qrCode.content}
            </p>
          ) : (
            <>
              <p>
                <strong>File:</strong> {qrCode.uploaded_file.original_filename}
              </p>
              <p style={{ color: '#28a745', marginTop: '10px' }}>
                ✓ File is accessible via secure random link (completely hidden)
              </p>
              <p style={{ color: '#666', fontSize: '0.9em' }}>
                The QR code contains a random UUID - no file path is exposed
              </p>
            </>
          )}
          <p>
            <strong>Created:</strong>{' '}
            {new Date(qrCode.created_at).toLocaleString()}
          </p>
        </div>

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

        <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <Link to="/" className="btn btn-secondary" style={{ width: 'auto', display: 'inline-block' }}>
            Generate Another
          </Link>
          {qrCode.qr_type === 'file' && (
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
