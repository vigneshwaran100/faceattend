import { apiClient } from './apiClient';
import { ReadinessResponse } from '../types/api';

export const healthService = {
  async getHealth(): Promise<{ status: string }> {
    return apiClient.get<{ status: string }>('/health');
  },

  async getReadiness(): Promise<ReadinessResponse> {
    return apiClient.get<ReadinessResponse>('/ready');
  },
};
