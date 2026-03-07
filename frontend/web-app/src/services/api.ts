/**
 * API Service Configuration
 * Axios instance with interceptors for authentication and error handling
 */

import axios, { AxiosError, AxiosResponse } from 'axios';

// API base URL - change this for production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    
    // Log error for debugging
    console.error('API Error:', error.response?.data || error.message);
    
    return Promise.reject(error);
  }
);

export default api;

// API endpoints
export const endpoints = {
  // Auth
  login: '/auth/login',
  verify: '/auth/verify',
  refresh: '/auth/refresh',
  
  // Profiles
  profiles: '/profiles',
  profileById: (id: string) => `/profiles/${id}`,
  
  // Eligibility
  checkEligibility: '/eligibility/check',
  schemes: '/eligibility/schemes',
  schemeById: (id: string) => `/eligibility/schemes/${id}`,
  
  // Documents
  documents: '/documents',
  uploadDocument: '/documents/upload',
  ocrDocument: '/documents/ocr',
  validateDocument: '/documents/validate',
  documentById: (id: string) => `/documents/${id}`,
  
  // Applications
  applications: '/applications',
  applicationById: (id: string) => `/applications/${id}`,
  autoFill: '/applications/auto-fill',
  
  // Tracking
  tracking: (id: string) => `/tracking/${id}`,
  trackingHistory: (id: string) => `/tracking/${id}/history`,
  subscribe: '/tracking/subscribe',
  
  // Health
  health: '/health',
};
