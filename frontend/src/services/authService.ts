import { apiClient } from './apiClient';
import { LoginRequest, TokenResponse } from '../types/api';

export const authService = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    if (response.access_token) {
      apiClient.setToken(response.access_token);
    }
    return response;
  },

  logout(): void {
    apiClient.clearToken();
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('faceattend_token');
  },
};
