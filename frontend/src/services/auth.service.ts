import apiClient from './apiClient';

export const authService = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data; // Trả về { token, userId, username }
  },

  register: async (username: string, email: string, password: string) => {
    const response = await apiClient.post('/auth/register', { username, email, password });
    return response.data;
  }
};