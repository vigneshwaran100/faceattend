import { apiClient } from './apiClient';
import {
  DepartmentCreateRequest,
  DepartmentResponse,
  TeamCreateRequest,
  TeamResponse,
} from '../types/api';

export const organizationService = {
  async createDepartment(data: DepartmentCreateRequest): Promise<DepartmentResponse> {
    return apiClient.post<DepartmentResponse>('/departments', data);
  },

  async getDepartment(departmentId: string): Promise<DepartmentResponse> {
    return apiClient.get<DepartmentResponse>(`/departments/${departmentId}`);
  },

  async createTeam(data: TeamCreateRequest): Promise<TeamResponse> {
    return apiClient.post<TeamResponse>('/teams', data);
  },

  async getTeam(teamId: string): Promise<TeamResponse> {
    return apiClient.get<TeamResponse>(`/teams/${teamId}`);
  },
};
