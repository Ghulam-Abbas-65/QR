import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import authService from '../services/authService';
import './Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState(false);
  
  // Verification state
  const [showVerification, setShowVerification] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');
  
  const { register, verifyEmail } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const checkUsernameAvailability = async (username) => {
    if (username.length < 3) return;
    
    setCheckingUsername(true);
    try {
      const response = await authService.checkUsername(username);
      if (!response.available) {
        setErrors(prev => ({
          ...prev,
          username: 'Username is already taken'
        }));
      }
    } catch (error) {
      console.error('Username check failed:', error);
    } finally {
      setCheckingUsername(false);
    }
  };

  const checkEmailAvailability = async (email) => {
    if (!email.includes('@')) return;
    
    setCheckingEmail(true);
    try {
      const response = await authService.checkEmail(email);
      if (!response.available) {
        setErrors(prev => ({
          ...prev,
          email: 'Email is already registered'
        }));
      }
    } catch (error) {
      console.error('Email check failed:', error);
    } finally {
      setCheckingEmail(false);
    }
  };

  const handleUsernameBlur = () => {
    if (formData.username && formData.username.length >= 3) {
      checkUsernameAvailability(formData.username);
    }
  };

  const handleEmailBlur = () => {
    if (formData.email && formData.email.includes('@')) {
      checkEmailAvailability(formData.email);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, underscores, and hyphens';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Please confirm your password';
    } else if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formErrors = validateForm();
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    
    setLoading(true);
    setErrors({});
    
    try {
      const response = await register(formData);
      
      if (response.requires_verification) {
        setPendingEmail(response.email);
        setShowVerification(true);
      } else if (response.token) {
        navigate('/', { replace: true });
      }
    } catch (error) {
      if (error.username) {
        setErrors(prev => ({ ...prev, username: error.username[0] }));
      }
      if (error.email) {
        setErrors(prev => ({ ...prev, email: error.email[0] }));
      }
      if (error.password) {
        setErrors(prev => ({ ...prev, password: error.password[0] }));
      }
      if (error.confirm_password) {
        setErrors(prev => ({ ...prev, confirm_password: error.confirm_password[0] }));
      }
      if (error.error) {
        setErrors(prev => ({ ...prev, general: error.error }));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});
    
    try {
      await verifyEmail(pendingEmail, verificationCode);
      navigate('/', { replace: true });
    } catch (error) {
      setErrors({ general: error.error || 'Verification failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setLoading(true);
    try {
      await authService.resendVerification(pendingEmail);
      setErrors({ general: 'New code sent to your email' });
    } catch (error) {
      setErrors({ general: error.error || 'Failed to resend code' });
    } finally {
      setLoading(false);
    }
  };

  // Verification form
  if (showVerification) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1>Verify Your Email</h1>
            <p>We sent a 6-digit code to <strong>{pendingEmail}</strong></p>
          </div>
          
          <form onSubmit={handleVerify} className="auth-form">
            {errors.general && (
              <div className={errors.general.includes('sent') ? 'success-message' : 'error-message general-error'}>
                {errors.general}
              </div>
            )}
            
            <div className="form-group">
              <label htmlFor="code">Verification Code</label>
              <input
                type="text"
                id="code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="Enter 6-digit code"
                maxLength={6}
                className="verification-input"
                autoFocus
              />
            </div>
            
            <button type="submit" className="auth-button" disabled={loading || verificationCode.length !== 6}>
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>
          
          <div className="auth-footer">
            <p>
              Didn't receive the code?{' '}
              <button onClick={handleResendCode} className="auth-link-button" disabled={loading}>
                Resend Code
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Join QR Generator to create and manage your QR codes</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          {errors.general && (
            <div className="error-message general-error">
              {errors.general}
            </div>
          )}
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="First name (optional)"
                autoComplete="given-name"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="Last name (optional)"
                autoComplete="family-name"
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="username">
              Username {checkingUsername && <span className="checking">Checking...</span>}
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              onBlur={handleUsernameBlur}
              className={errors.username ? 'error' : ''}
              placeholder="Choose a username"
              autoComplete="username"
            />
            {errors.username && (
              <span className="error-message">{errors.username}</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="email">
              Email {checkingEmail && <span className="checking">Checking...</span>}
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onBlur={handleEmailBlur}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email"
              autoComplete="email"
            />
            {errors.email && (
              <span className="error-message">{errors.email}</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={errors.password ? 'error' : ''}
              placeholder="Create a password (min 8 characters)"
              autoComplete="new-password"
            />
            {errors.password && (
              <span className="error-message">{errors.password}</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="confirm_password">Confirm Password</label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              className={errors.confirm_password ? 'error' : ''}
              placeholder="Confirm your password"
              autoComplete="new-password"
            />
            {errors.confirm_password && (
              <span className="error-message">{errors.confirm_password}</span>
            )}
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={loading || checkingUsername || checkingEmail}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
