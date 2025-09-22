import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Collection APIs
export const collectionAPI = {
  list: () => api.get('/api/collections/'),
  create: (data: { name: string; description: string }) =>
    api.post('/api/collections/', data),
  get: (id: number) => api.get(`/api/collections/${id}`),
};

// Ingestion APIs
export const ingestAPI = {
  uploadFile: (collectionId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/ingest/upload?collection_id=${collectionId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  ingestURL: (data: { collection_id: number; url: string; title: string }) =>
    api.post('/api/ingest/url', data),
  getStatus: (jobId: string) => api.get(`/api/ingest/status/${jobId}`),
};

// Query APIs
export const queryAPI = {
  ask: (data: { collection_id: number; question: string; top_k?: number }) =>
    api.post('/api/ask', data),
  feedback: (queryId: number, value: number, note?: string) =>
    api.post(`/api/feedback/${queryId}`, { value, note }),
};

// Metrics API
export const metricsAPI = {
  get: () => api.get('/api/metrics'),
};