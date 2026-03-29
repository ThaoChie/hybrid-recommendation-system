import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/auth.service';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isModalOpen: boolean;
  user: User | null;
  openModal: () => void;
  closeModal: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  // Giữ trạng thái đăng nhập khi reload trang
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setIsAuthenticated(true);
      setUser(JSON.parse(savedUser));
    }

    // Lắng nghe event bị lỗi 401 từ apiClient.ts để tự động bật Modal
    const handleUnauthorized = () => {
      logout();
      openModal();
    };
    window.addEventListener('auth-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth-unauthorized', handleUnauthorized);
  }, []);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  const login = async (email: string, password: string) => {
    const data = await authService.login(email, password);
    
    // Lưu token và user info vào storage
    localStorage.setItem('token', data.token);
    const userInfo = { id: data.userId, name: data.username, email: email };
    localStorage.setItem('user', JSON.stringify(userInfo));

    setIsAuthenticated(true);
    setUser(userInfo);
    closeModal();
  };

  const register = async (name: string, email: string, password: string) => {
    await authService.register(name, email, password);
    // Tự động login sau khi đăng ký thành công
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isModalOpen, user, openModal, closeModal, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};