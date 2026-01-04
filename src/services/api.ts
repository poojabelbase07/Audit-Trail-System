// API service layer - all backend communication

import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { storage } from '../utils/storage';
import type {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  Task,
  CreateTaskData,
  UpdateTaskData,
  AuditLog,
  User,
} from '../types';

// Create axios instance with base config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to all requests automatically
apiClient.interceptors.request.use((config) => {
  const token = storage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors - redirect to login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      storage.removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};

// Tasks API
export const tasksAPI = {
  async getTasks(page = 1, pageSize = 20): Promise<{ tasks: Task[]; total: number }> {
    const response = await apiClient.get('/tasks', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async getTask(id: string): Promise<Task> {
    const response = await apiClient.get<Task>(`/tasks/${id}`);
    return response.data;
  },

  async createTask(data: CreateTaskData): Promise<Task> {
    const response = await apiClient.post<Task>('/tasks', data);
    return response.data;
  },

  async updateTask(id: string, data: UpdateTaskData): Promise<Task> {
    const response = await apiClient.put<Task>(`/tasks/${id}`, data);
    return response.data;
  },

  async deleteTask(id: string): Promise<void> {
    await apiClient.delete(`/tasks/${id}`);
  },
};

// Audit logs API
export const auditAPI = {
  async getMyHistory(page = 1, pageSize = 50): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await apiClient.get('/audit/my-history', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async getAllLogs(page = 1, pageSize = 50): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await apiClient.get('/audit/logs', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async getStats(): Promise<any> {
    const response = await apiClient.get('/audit/stats');
    return response.data;
  },
};

// Users API (admin only)
export const usersAPI = {
  async getUsers(page = 1, pageSize = 50): Promise<User[]> {
    const response = await apiClient.get<User[]>('/users', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};