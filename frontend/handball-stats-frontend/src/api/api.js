import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/',  // Django backend URL
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add interceptors for auth if needed
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;