// Application-wide constants

// API configuration
export const API_BASE_URL = 'http://localhost:8000/api'; // Backend base URL

// Task status colors for UI badges
export const STATUS_COLORS: Record<string, string> = {
  todo: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  done: 'bg-green-100 text-green-800',
  bug: 'bg-red-100 text-red-800',
};

// Task priority colors for UI badges
export const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-orange-100 text-orange-700',
  high: 'bg-red-100 text-red-800',
};

// Human-readable labels
export const STATUS_LABELS: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
  bug: 'Bug',
};

export const PRIORITY_LABELS: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

// App metadata
export const APP_NAME = 'AuditFlow';
export const APP_TAGLINE = 'Every action, tracked. Production-grade audit logging for modern applications.';