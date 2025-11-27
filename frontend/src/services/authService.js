import axios from 'axios';
import { API_BASE_URL } from '../config';

class AuthService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.user = JSON.parse(localStorage.getItem('user') || 'null');
    
    // Set up axios interceptor for authentication
    axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Token ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Set up response interceptor for handling auth errors
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async register(userData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/register/`, userData);
      
      if (response.data.token) {
        this.setAuthData(response.data.token, response.data.user);
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Registration failed' };
    }
  }

  async login(credentials) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login/`, credentials);
      
      if (response.data.token) {
        this.setAuthData(response.data.token, response.data.user);
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Login failed' };
    }
  }

  async logout() {
    try {
      if (this.token) {
        await axios.post(`${API_BASE_URL}/auth/logout/`);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearAuthData();
    }
  }

  async checkUsername(username) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/check-username/`, { username });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Check failed' };
    }
  }

  async checkEmail(email) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/check-email/`, { email });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Check failed' };
    }
  }

  async getProfile() {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/profile/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Failed to get profile' };
    }
  }

  async updateProfile(userData) {
    try {
      const response = await axios.put(`${API_BASE_URL}/auth/profile/update/`, userData);
      
      if (response.data.user) {
        this.user = response.data.user;
        localStorage.setItem('user', JSON.stringify(this.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Profile update failed' };
    }
  }

  setAuthData(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  }

  clearAuthData() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  getUser() {
    return this.user;
  }

  getToken() {
    return this.token;
  }
}

export default new AuthService();