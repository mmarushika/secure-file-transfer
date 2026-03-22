import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export interface User {
  id: number;
  email: string;
  username: string;
}

export interface FileData {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authAPI = {
  login: (username: string, password: string) =>
    api.post<AuthResponse>('/token', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  register: (email: string, username: string, password: string) =>
    api.post<User>('/register', { email, username, password }),
  
  getCurrentUser: () =>
    api.get<User>('/users/me'),
};

export const fileAPI = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FileData>('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  getFiles: () =>
    api.get<FileData[]>('/files'),
  
  downloadFile: (fileId: string) =>
    api.get(`/files/${fileId}/download`, { responseType: 'blob' }),
  
  shareFile: (fileId: string, email: string) =>
    api.post(`/files/${fileId}/share`, { email }),
  
  deleteFile: (fileId: string) =>
    api.delete(`/files/${fileId}`),
  
  getFileShares: (fileId: string) =>
    api.get<{shares: string[]}>(`/files/${fileId}/shares`),
  
  unshareFile: (fileId: string, email: string) =>
    api.delete(`/files/${fileId}/share/${email}`),
  
  getSharedFiles: () =>
    api.get<FileData[]>('/shared-files'),
};
