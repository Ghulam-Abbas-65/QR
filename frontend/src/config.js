// API Configuration
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000/api',
  },
  production: {
    API_BASE_URL: 'https://ghulam.pythonanywhere.com/api',
  }
};

// Detect environment
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const environment = isDevelopment ? 'development' : 'production';

export const API_BASE_URL = config[environment].API_BASE_URL;
export const BASE_URL = API_BASE_URL.replace('/api', '');

export default config;