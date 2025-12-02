import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to all requests
api.interceptors.request.use(
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

export const generateDynamicQR = async (url, name = '') => {
  const response = await api.post('/generate/dynamic/', { url, name });
  return response.data;
};

export const generateDynamicFileQR = async (file, name = '') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  
  const response = await api.post('/generate/dynamic-file/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const updateDynamicQR = async (id, data) => {
  const response = await api.put(`/qr-codes/${id}/update/`, data);
  return response.data;
};

export default api;
