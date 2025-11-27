import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo-link">
          <h1>🔲 QR Code Generator</h1>
        </Link>
        <p>Generate QR codes from URLs or files</p>
      </div>
      
      <nav className="nav-links">
        {isAuthenticated ? (
          <>
            <Link to="/" className="nav-link">🏠 Home</Link>
            <Link to="/check-analytics" className="nav-link">📊 Analytics</Link>
            
            <div className="user-menu">
              <button 
                className="user-button"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                👤 {user?.first_name || user?.username}
              </button>
              
              {showUserMenu && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <p className="user-name">{user?.first_name} {user?.last_name}</p>
                    <p className="user-email">{user?.email}</p>
                  </div>
                  <hr />
                  <button 
                    onClick={handleLogout}
                    className="logout-button"
                  >
                    🚪 Logout
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">🔑 Login</Link>
            <Link to="/register" className="nav-link register-link">📝 Sign Up</Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default Header;
