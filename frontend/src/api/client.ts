import axios from 'axios';

// Determine the API base URL (relative in production, local in development)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT Token and X-Organization-ID
apiClient.interceptors.request.use(
  (config) => {
    // 1. Attach JWT Access Token if saved
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 2. Attach Organization Context Header if selected
    const orgId = localStorage.getItem('active_organization_id');
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle authorization failures globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear credentials and redirect to login if session expires
      localStorage.removeItem('access_token');
      localStorage.removeItem('active_organization_id');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
