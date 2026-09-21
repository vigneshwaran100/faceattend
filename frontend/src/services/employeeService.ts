import { apiClient } from './apiClient';
import {
  EmployeeCreateRequest,
  EmployeeResponse,
  EmployeeUpdateRequest,
  EmployeeStatusUpdateRequest,
  AttendanceHistoryResponse,
  AttendanceSummaryResponse,
} from '../types/api';

export const employeeService = {
  async getEmployee(employeeId: string): Promise<EmployeeResponse> {
    return apiClient.get<EmployeeResponse>(`/employees/${employeeId}`);
  },

  async createEmployee(data: EmployeeCreateRequest): Promise<EmployeeResponse> {
    return apiClient.post<EmployeeResponse>('/employees', data);
  },

  async updateEmployee(employeeId: string, data: EmployeeUpdateRequest): Promise<EmployeeResponse> {
    return apiClient.put<EmployeeResponse>(`/employees/${employeeId}`, data);
  },

  async updateStatus(employeeId: string, status: 'active' | 'inactive'): Promise<EmployeeResponse> {
    return apiClient.patch<EmployeeResponse>(`/employees/${employeeId}/status`, { status });
  },

  async getAttendanceHistory(
    employeeId: string,
    startDate?: string,
    endDate?: string
  ): Promise<AttendanceHistoryResponse> {
    return apiClient.get<AttendanceHistoryResponse>(`/employees/${employeeId}/attendance`, {
      start_date: startDate,
      end_date: endDate,
    });
  },

  async getAttendanceSummary(
    employeeId: string,
    startDate?: string,
    endDate?: string
  ): Promise<AttendanceSummaryResponse> {
    return apiClient.get<AttendanceSummaryResponse>(`/employees/${employeeId}/attendance/summary`, {
      start_date: startDate,
      end_date: endDate,
    });
  },
};
