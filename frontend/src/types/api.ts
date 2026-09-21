// Centralized API types and schemas matching FastAPI backend contracts

export interface ApiErrorResponse {
  detail: string | { loc: (string | number)[]; msg: string; type: string }[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'degraded' | 'not_ready';
  ready: boolean;
  dependencies: {
    database: {
      status: 'healthy' | 'unavailable';
      critical: boolean;
    };
    milvus: {
      status: 'healthy' | 'unavailable';
      critical: boolean;
      message?: string;
    };
  };
}

export interface EmployeeCreateRequest {
  employee_id: string;
  name: string;
  email: string;
  team_id?: string | null;
  department_id?: string | null;
  designation?: string | null;
}

export interface EmployeeUpdateRequest {
  name: string;
  email: string;
  team_id?: string | null;
  department_id?: string | null;
  designation?: string | null;
  status?: string | null;
}

export interface EmployeeStatusUpdateRequest {
  status: 'active' | 'inactive';
}

export interface EmployeeResponse {
  employee_id: string;
  name: string;
  email: string;
  team_id: string | null;
  department_id: string | null;
  designation: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DailyAttendanceItemResponse {
  employee_id: string;
  name: string;
  check_in: string | null;
  check_out: string | null;
  working_hours: number | null;
  status: 'in_progress' | 'present' | 'half_day' | 'incomplete' | 'absent';
}

export interface DailyAttendanceReportResponse {
  attendance_date: string;
  total_employees: number;
  records: DailyAttendanceItemResponse[];
}

export interface EndOfDayResponse {
  date: string;
  present: number;
  half_day: number;
  incomplete: number;
  absent: number;
  total_processed: number;
  message: string;
}

export interface AttendanceRecordResponse {
  attendance_id: number;
  employee_id: string;
  attendance_date: string;
  check_in: string | null;
  check_out: string | null;
  status: 'in_progress' | 'present' | 'half_day' | 'incomplete' | 'absent';
  working_hours: number | null;
}

export interface AttendanceHistoryResponse {
  employee_id: string;
  attendance: AttendanceRecordResponse[];
}

export interface AttendanceSummaryResponse {
  employee_id: string;
  start_date: string | null;
  end_date: string | null;
  total_records: number;
  total_working_days: number;
  present_days: number;
  half_days: number;
  incomplete_days: number;
  absent_days: number;
  in_progress_days: number;
  total_working_hours: number;
  attendance_percentage: number;
}

export interface FaceSamplesEnrollmentResponse {
  employee_id: string;
  samples_received: number;
  embeddings_stored: number;
  enrollment_status: string;
  message: string;
}

export interface FaceEnrollmentResponse {
  employee_id: string;
  message: string;
}

export interface AuditLogRecordResponse {
  log_id: number;
  scanner_type: string;
  event_type: string;
  status: 'SUCCESS' | 'FAILURE';
  employee_id: string | null;
  similarity: number | null;
  message: string;
  created_at: string;
}

export interface PaginatedAuditLogsResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: AuditLogRecordResponse[];
}

export interface DepartmentCreateRequest {
  department_id: string;
  department_name: string;
}

export interface DepartmentResponse {
  department_id: string;
  department_name: string;
  created_at: string;
  updated_at: string;
}

export interface TeamCreateRequest {
  team_id: string;
  team_name: string;
}

export interface TeamResponse {
  team_id: string;
  team_name: string;
  created_at: string;
  updated_at: string;
}

// Kiosk API types
export interface FaceVerificationResponse {
  success: boolean;
  status: string; // ACCESS_GRANTED | UNRECOGNIZED_FACE | NO_FACE_DETECTED | MULTIPLE_FACES_DETECTED | QUALITY_FAILED | EMPLOYEE_NOT_FOUND | INACTIVE_EMPLOYEE | NO_CHECK_IN | ERROR
  message: string;
  employee_id: string | null;
  employee_name: string | null;
  department: string | null;
  job_title: string | null;
  similarity: number | null;
  scanner_type: string;
  timestamp: string;
  attendance_id: string | null;
}

export interface ManualPunchRequest {
  employee_id: string;
  scanner_type: 'CHECK_IN' | 'CHECK_OUT';
}

export interface KioskStatsResponse {
  date: string;
  total_scans_today: number;
  successful_punches: number;
  rejected_scans: number;
  active_employees: number;
  checked_in_count: number;
  checked_out_count: number;
}
