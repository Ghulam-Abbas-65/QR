import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef(null);
  const location = useLocation();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close menu on route change
  useEffect(() => {
    setShowUserMenu(false);
  }, [location]);

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo-link">
          <span className="logo-icon">🔲</span>
          <div className="logo-text">
            <h1>QR Generator</h1>
            <p>Create & Track QR Codes</p>
          </div>
        </Link>
      </div>
      
      <nav className="nav-links">
        {isAuthenticated ? (
          <>
            <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
              <span className="nav-icon">🏠</span>
              <span className="nav-text">Home</span>
            </Link>
            <Link to="/check-analytics" className={`nav-link ${isActive('/check-analytics') ? 'active' : ''}`}>
              <span className="nav-icon">📊</span>
              <span className="nav-text">My QR Codes</span>
            </Link>
            
            <div className="user-menu" ref={menuRef}>
              <button 
                className={`user-button ${showUserMenu ? 'active' : ''}`}
                onClick={() => setShowUserMenu(!showUserMenu)}
                aria-expanded={showUserMenu}
                aria-haspopup="true"
              >
                <span className="user-avatar">👤</span>
                <span className="user-name-btn">{user?.first_name || user?.username}</span>
              </button>
              
              {showUserMenu && (
                <div className="user-dropdown" role="menu">
                  <div className="user-info">
                    <p className="user-name">{user?.first_name} {user?.last_name}</p>
                    <p className="user-email">{user?.email}</p>
                  </div>
                  <div className="dropdown-divider"></div>
                  <button 
                    onClick={handleLogout}
                    className="logout-button"
                    role="menuitem"
                  >
                    <span>🚪</span>
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">
              <span className="nav-icon">🔑</span>
              <span className="nav-text">Login</span>
            </Link>
            <Link to="/register" className="nav-link register-link">
              <span className="nav-icon">✨</span>
              <span className="nav-text">Get Started</span>
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default Header;
