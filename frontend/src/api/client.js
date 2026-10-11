import axios from 'axios';

const API_BASE = '/api/v1';

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
    const formData = new FormData();
    formData.append('category', category);
    formData.append('split', split);
    formData.append('defect_type', defectType);
    formData.append('image_name', imageName);
    return apiClient.post('/inspections/import-mvtec', formData);
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
  analyzeInspection: (id) => apiClient.post(`/inspections/${id}/analyze`),
  getQualityReport: (id) => apiClient.get(`/inspections/${id}/quality-report`),
  preprocessInspection: (id) => apiClient.post(`/inspections/${id}/preprocess`),
};

export const datasetAPI = {
  getCategories: () => apiClient.get('/dataset/categories'),
  getCategoryDetail: (category) => apiClient.get(`/dataset/category/${category}`),
  generateSamples: () => apiClient.post('/dataset/generate-samples'),
};

export const dashboardAPI = {
  getKPIStats: () => apiClient.get('/dashboard/stats'),
  getBatches: () => apiClient.get('/dashboard/batches'),
};

export const auditAPI = {
  getLogs: (params) => apiClient.get('/audit/logs', { params }),
};

export default apiClient;
