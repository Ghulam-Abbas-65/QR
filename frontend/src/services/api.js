import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const generateURLQR = async (url) => {
  const response = await api.post('/generate/url/', { url });
  return response.data;
};

export const generateFileQR = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/generate/file/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getQRCode = async (id) => {
  const response = await api.get(`/qr-codes/${id}/`);
  return response.data;
};

export const getQRCodes = async (search = '') => {
  const response = await api.get('/qr-codes/', {
    params: { search },
  });
  return response.data;
};

export const getAnalytics = async (id, filters = {}) => {
  const response = await api.get(`/qr-codes/${id}/analytics/`, {
    params: filters,
  });
  return response.data;
};

export default api;
