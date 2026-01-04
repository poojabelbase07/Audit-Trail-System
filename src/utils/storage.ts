// LocalStorage utilities for secure token management

const TOKEN_KEY = 'audit_token'; // Key for storing JWT token

export const storage = {
  // Get JWT token from localStorage
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  // Save JWT token to localStorage
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  // Remove JWT token from localStorage (logout)
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  },

  // Check if user is authenticated (has valid token)
  hasToken(): boolean {
    return !!this.getToken();
  },
};