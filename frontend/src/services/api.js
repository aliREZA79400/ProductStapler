import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  register: (username, password) =>
    api.post('/auth/register', { username, password }),
  
  login: (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  
  getCurrentUser: () => api.get('/auth/me'),
};

// Product APIs
export const productAPI = {
  getLevel1Products: (sampleSize = 3, level1Id = null) => {
    const params = { sample_size: sampleSize };
    if (level1Id) params.level1_id = level1Id;
    return api.get('/', { params });
  },
  
  getLevel2Products: (level1Id, sampleSize = 3) =>
    api.get(`/sub/${level1Id}`, { params: { sample_size: sampleSize } }),
  
  getLevel3Products: (level1Id, level2Id, sampleSize = 3) =>
    api.get(`/sub/${level1Id}/sub-sub/${level2Id}`, { params: { sample_size: sampleSize } }),
  
  getProductById: (productId) => api.get(`/product/${productId}`),
};

export default api;
