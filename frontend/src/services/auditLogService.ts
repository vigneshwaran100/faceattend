import { apiClient } from './apiClient';
import { PaginatedAuditLogsResponse } from '../types/api';

export interface AuditLogFilters {
  employee_id?: string;
  event_type?: string;
  scanner_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export const auditLogService = {
  async getLogs(filters: AuditLogFilters = {}): Promise<PaginatedAuditLogsResponse> {
    return apiClient.get<PaginatedAuditLogsResponse>('/audit-logs', filters);
  },
};
