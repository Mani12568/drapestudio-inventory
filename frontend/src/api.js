import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_URL,
});

// Automatically attach the token to every request, if one exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const signup = (email, password) =>
  api.post('/signup', { email, password });

export const login = (email, password) =>
  api.post('/login', { email, password });

export const getProducts = () => api.get('/products');

export const getLowStock = () => api.get('/products/low-stock');

export const createProduct = (product) => api.post('/products', product);

export const updateProduct = (id, product) => api.put(`/products/${id}`, product);

export const deleteProduct = (id) => api.delete(`/products/${id}`);

export const adjustStock = (id, change) => api.patch(`/products/${id}/stock`, { change });

export default api;