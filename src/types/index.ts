// Global TypeScript type definitions for the application

// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

// Authentication types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Task types
export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'bug';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  created_by_id: string;
  assigned_to_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  priority?: TaskPriority;
  assigned_to_id?: string;
}

export interface UpdateTaskData {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigned_to_id?: string;
}

// Audit log types
export type AuditEventType = 
  | 'USER_REGISTER'
  | 'USER_LOGIN'
  | 'USER_LOGOUT'
  | 'USER_LOGIN_FAILED'
  | 'TASK_CREATE'
  | 'TASK_UPDATE'
  | 'TASK_DELETE'
  | 'TASK_ASSIGN';

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  user_ip: string | null;
  user_agent: string | null;
  event_type: AuditEventType;
  resource_type: string | null;
  resource_id: string | null;
  action: string;
  changes: Record<string, any> | null;
  metadata: Record<string, any> | null;
  status: string;
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  error: string;
  detail: string | object;
  timestamp: number;
}