import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAnalytics } from '../services/api';
import './Analytics.css';

function Analytics() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    country: '',
    city: '',
    device: '',
    browser: '',
  });

  useEffect(() => {
    loadAnalytics();
  }, [id]);

  const loadAnalytics = async (appliedFilters = {}) => {
    setLoading(true);
    try {
      const result = await getAnalytics(id, appliedFilters);
      setData(result);
    } catch (err) {
      console.error('Failed to load analytics', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const applyFilters = (e) => {
    e.preventDefault();
    loadAnalytics(filters);
  };

  const clearFilters = () => {
    setFilters({ country: '', city: '', device: '', browser: '' });
    loadAnalytics({});
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!data) return null;

  const { qr_code, stats, filter_options } = data;
  const hasActiveFilters = Object.values(filters).some((f) => f !== '');

  return (
    <div className="card">
      <h2 className="section-title">📊 Analytics Dashboard</h2>

      <div className="info-box" style={{ marginBottom: '20px' }}>
        <p>
          <strong>QR Code Type:</strong> {qr_code.qr_type === 'url' ? 'URL' : 'File'}
        </p>
        {qr_code.qr_type === 'file' ? (
          <p>
            <strong>File:</strong> {qr_code.uploaded_file.original_filename}
          </p>
        ) : (
          <p>
            <strong>URL:</strong> {qr_code.content}
          </p>
        )}
        <p>
          <strong>Created:</strong> {new Date(qr_code.created_at).toLocaleString()}
        </p>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <h3>🔍 Filter Analytics</h3>
        <form onSubmit={applyFilters}>
          <div className="filter-grid">
            <div className="filter-item">
              <label htmlFor="country">Country</label>
              <select
                name="country"
                id="country"
                className="form-control"
                value={filters.country}
                onChange={handleFilterChange}
              >
                <option value="">All Countries</option>
                {filter_options.countries.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-item">
              <label htmlFor="city">City</label>
              <select
                name="city"
                id="city"
                className="form-control"
                value={filters.city}
                onChange={handleFilterChange}
              >
                <option value="">All Cities</option>
                {filter_options.cities.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-item">
              <label htmlFor="device">Device</label>
              <select
                name="device"
                id="device"
                className="form-control"
                value={filters.device}
                onChange={handleFilterChange}
              >
                <option value="">All Devices</option>
                {filter_options.devices.map((device) => (
                  <option key={device} value={device}>
                    {device}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-item">
              <label htmlFor="browser">Browser</label>
              <select
                name="browser"
                id="browser"
                className="form-control"
                value={filters.browser}
                onChange={handleFilterChange}
              >
                <option value="">All Browsers</option>
                {filter_options.browsers.map((browser) => (
                  <option key={browser} value={browser}>
                    {browser}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="filter-actions">
            <button type="submit" className="btn" style={{ width: 'auto', padding: '10px 30px' }}>
              Apply Filters
            </button>
            <button
              type="button"
              onClick={clearFilters}
              className="btn btn-secondary"
              style={{ width: 'auto', padding: '10px 30px' }}
            >
              Clear Filters
            </button>
          </div>
        </form>

        {hasActiveFilters && (
          <div className="active-filters">
            <strong>Active Filters:</strong>
            {filters.country && <span className="filter-badge">Country: {filters.country}</span>}
            {filters.city && <span className="filter-badge">City: {filters.city}</span>}
            {filters.device && <span className="filter-badge">Device: {filters.device}</span>}
            {filters.browser && <span className="filter-badge">Browser: {filters.browser}</span>}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{stats.total_scans}</div>
          <div className="stat-label">Total Scans</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.unique_users}</div>
          <div className="stat-label">Unique Users</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.countries.length}</div>
          <div className="stat-label">Countries</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.cities.length}</div>
          <div className="stat-label">Cities</div>
        </div>
      </div>

      {/* Data Sections */}
      <DataSection title="🌍 Countries" data={stats.countries} labelKey="country" />
      <DataSection title="🏙️ Cities" data={stats.cities} labelKey="city" countryKey="country" />
      <DataSection title="📱 Device Types" data={stats.devices} labelKey="device_type" />
      <DataSection title="🌐 Browsers" data={stats.browsers} labelKey="browser" />

      {/* Recent Scans */}
      <div className="analytics-section">
        <h3>🕒 Recent Scans</h3>
        <div className="recent-scans">
          {stats.recent_scans.length > 0 ? (
            stats.recent_scans.map((scan) => (
              <div key={scan.id} className="scan-item">
                <div>
                  <strong>
                    {scan.city}, {scan.country}
                  </strong>
                  <span style={{ color: '#999', marginLeft: '10px' }}>{scan.device_type}</span>
                  <span style={{ color: '#999', marginLeft: '10px' }}>{scan.browser}</span>
                </div>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  {new Date(scan.scanned_at).toLocaleString()}
                </div>
              </div>
            ))
          ) : (
            <p style={{ color: '#999' }}>No scans yet</p>
          )}
        </div>
      </div>

      <div className="analytics-nav">
        <Link to={`/result/${id}`} className="btn btn-secondary">
          ← Back to QR Code
        </Link>
        <Link to="/" className="btn btn-secondary">
          🏠 Home
        </Link>
      </div>
    </div>
  );
}

function DataSection({ title, data, labelKey, countryKey }) {
  return (
    <div className="analytics-section">
      <h3>
        {title} ({data.length})
      </h3>
      <div className="data-list">
        {data.length > 0 ? (
          data.map((item, index) => (
            <div key={index} className="data-item">
              <span className="data-label">
                {item[labelKey]}
                {countryKey && `, ${item[countryKey]}`}
              </span>
              <span className="data-value">{item.count}</span>
            </div>
          ))
        ) : (
          <p style={{ color: '#999' }}>No data yet</p>
        )}
      </div>
    </div>
  );
}

export default Analytics;
