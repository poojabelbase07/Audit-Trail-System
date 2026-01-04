// Authentication context - manages auth state across the app

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import { storage } from '../utils/storage';
import type { User, LoginCredentials, RegisterData } from '../types';

interface AuthContextType {
  user: User | null; // Current logged-in user
  loading: boolean; // Loading state during auth check
  login: (credentials: LoginCredentials) => Promise<void>; // Login function
  register: (data: RegisterData) => Promise<void>; // Register function
  logout: () => Promise<void>; // Logout function
  isAuthenticated: boolean; // Whether user is logged in
  isAdmin: boolean; // Whether user has admin role
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // Initially loading

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (storage.hasToken()) {
        try {
          const userData = await authAPI.getCurrentUser(); // Fetch user from backend
          setUser(userData);
        } catch (error) {
          storage.removeToken(); // Clear invalid token
        }
      }
      setLoading(false); // Done checking
    };

    checkAuth();
  }, []);

  // Login function - authenticate and store token
  const login = async (credentials: LoginCredentials) => {
    const response = await authAPI.login(credentials);
    storage.setToken(response.access_token); // Save JWT
    setUser(response.user); // Update state
  };

  // Register function - create account and auto-login
  const register = async (data: RegisterData) => {
    const response = await authAPI.register(data);
    storage.setToken(response.access_token); // Save JWT
    setUser(response.user); // Update state
  };

  // Logout function - clear token and state
  const logout = async () => {
    try {
      await authAPI.logout(); // Notify backend
    } catch (error) {
      // Continue logout even if API call fails
    }
    storage.removeToken(); // Clear token
    setUser(null); // Clear state
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user, // True if user exists
    isAdmin: user?.role === 'ADMIN', // True if user is admin
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};