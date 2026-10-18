import axios from 'axios';

const RAW_BACKEND = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL || '';
export const BACKEND_URL = RAW_BACKEND.replace(/\/+$/, '');
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api/v1` : '/api/v1';

export const getMediaUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) return url;
  return `${BACKEND_URL}${url}`;
};

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('visioninspect_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Response interceptor to handle 401s
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't auto clear if attempting demo role switch
      if (!window.location.pathname.includes('/login')) {
        // can handle token expiration
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => apiClient.post('/auth/login', { username, password }),
  register: (userData) => apiClient.post('/auth/register', userData),
  getMe: () => apiClient.get('/auth/me'),
  switchDemoRole: (role) => apiClient.post(`/auth/switch-demo-role?role=${role}`),
};

export const inspectionAPI = {
  uploadSingle: (formData) => apiClient.post('/inspections/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadBatch: (formData) => apiClient.post('/inspections/upload-batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  importMvtec: (category, split, defectType, imageName) => {
    return apiClient.post('/inspections/import-mvtec', {
      category,
      split,
      defect_type: defectType,
      image_name: imageName,
    });
  },
  getInspections: (params) => apiClient.get('/inspections', { params }),
  getInspectionDetail: (id) => apiClient.get(`/inspections/${id}`),
  updateDecision: (id, decision, severityLevel, notes) => {
    const formData = new FormData();
    formData.append('decision', decision);
    if (severityLevel) formData.append('severity_level', severityLevel);
    if (notes) formData.append('notes', notes);
    return apiClient.post(`/inspections/${id}/decision`, formData);
  },
  deleteInspection: (id) => apiClient.delete(`/inspections/${id}`),
  deleteAll: (onlyUploads = false) => apiClient.delete('/inspections/all', { params: { only_uploads: onlyUploads } }),
  reseed: () => apiClient.post('/inspections/reseed'),
  analyzeInspection: (id) => apiClient.post(`/inspections/${id}/analyze`),
  getQualityReport: (id) => apiClient.get(`/inspections/${id}/quality-report`),
  preprocessInspection: (id) => apiClient.post(`/inspections/${id}/preprocess`),
};

export const datasetAPI = {
  getCategories: () => apiClient.get('/dataset/categories'),
  getCategoryDetail: (category) => apiClient.get(`/dataset/category/${category}`),
  generateSamples: () => apiClient.post('/dataset/generate-samples'),
  trainAllModels: () => apiClient.post('/dataset/train-all'),
  trainModel: (cat) => apiClient.post(`/dataset/train/${cat}`),
  getTrainedModels: () => apiClient.get('/dataset/models'),
};

export const dashboardAPI = {
  getKPIStats: () => apiClient.get('/dashboard/stats'),
  getBatches: () => apiClient.get('/dashboard/batches'),
  getAnalytics: () => apiClient.get('/dashboard/analytics'),
  getTrends: () => apiClient.get('/dashboard/trends'),
  getQualityReport: () => apiClient.get('/dashboard/quality-report'),
};

export const auditAPI = {
  getLogs: (params) => apiClient.get('/audit/logs', { params }),
};

export default apiClient;
