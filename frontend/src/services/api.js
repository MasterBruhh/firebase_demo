// indexador-demo/frontend/src/services/api.js

import axios from 'axios';

// Obtener la URL base de tu backend desde el entorno de React
// En .env.local de React, usa REACT_APP_API_BASE_URL=http://localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir el token de Firebase a cada solicitud si el usuario está logueado
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('idToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('idToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  register: (email, password) => 
    api.post('/auth/register', { email, password }),
    
  getCurrentUser: (token) => 
    api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    }),
    
  testAdminRoute: (token) => 
    api.get('/auth/admin-only-test', {
      headers: { Authorization: `Bearer ${token}` }
    })
};

// Documents API calls (to be implemented)
export const documentsAPI = {
  upload: (file, token) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`
      }
    });
  },
  
  search: (query, token) => 
    api.get(`/documents/search?query=${encodeURIComponent(query)}`, {
      headers: { Authorization: `Bearer ${token}` }
    }),
    
  list: (token) => 
    api.get('/documents/list', {
      headers: { Authorization: `Bearer ${token}` }
    }),
    
  download: (documentId, token) => 
    api.get(`/documents/download/${documentId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
};

export default api;