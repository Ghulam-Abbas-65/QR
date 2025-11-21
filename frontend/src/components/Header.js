import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1>🔲 QR Code Generator</h1>
        <p>Generate QR codes from URLs or files</p>
      </div>
      <nav className="nav-links">
        <Link to="/" className="nav-link">🏠 Home</Link>
        <Link to="/check-analytics" className="nav-link">📊 Check Analytics</Link>
      </nav>
    </header>
  );
}

export default Header;
