import { apiClient } from './apiClient';
import { DailyAttendanceReportResponse, EndOfDayResponse } from '../types/api';

export const attendanceService = {
  async getDailyReport(attendanceDate?: string): Promise<DailyAttendanceReportResponse> {
    return apiClient.get<DailyAttendanceReportResponse>('/attendance', {
      attendance_date: attendanceDate,
    });
  },

  async finalizeEndOfDay(attendanceDate?: string): Promise<EndOfDayResponse> {
    return apiClient.post<EndOfDayResponse>('/attendance/end-of-day', undefined, undefined);
  },
};
