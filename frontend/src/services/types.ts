export type AttendanceStatus =
  | 'in_progress'
  | 'present'
  | 'half_day'
  | 'incomplete'
  | 'absent';

export type UserRole = 'ADMIN' | 'EMPLOYEE' | 'HR';
export type UserStatus = 'ACTIVE' | 'INACTIVE';
export type ScannerType = 'CHECK_IN' | 'CHECK_OUT' | 'SYSTEM';

export interface User {
  username: string;
  role: UserRole;
  status: UserStatus;
}

export interface Employee {
  employee_id: string;
  name: string;
  email: string;
  team_id?: string | null;
  department_id?: string | null;
  designation?: string | null;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface AttendanceRecord {
  attendance_id: string;
  employee_id: string;
  attendance_date: string;
  check_in: string | null;
  check_out: string | null;
  status: AttendanceStatus;
  working_hours?: number | null;
}

export interface AttendanceSummary {
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

export interface DailyAttendanceItem {
  employee_id: string;
  name: string;
  check_in: string | null;
  check_out: string | null;
  working_hours: number | null;
  status: AttendanceStatus;
}

export interface DailyAttendanceReport {
  attendance_date: string;
  total_employees: number;
  records: DailyAttendanceItem[];
}

export interface EndOfDaySummary {
  attendance_date: string;
  present: number;
  half_day: number;
  incomplete: number;
  absent: number;
  total_processed: number;
}

export interface AuditLogRecord {
  log_id: number;
  scanner_type: ScannerType;
  event_type: string;
  status: 'SUCCESS' | 'FAILURE';
  employee_id: string | null;
  similarity: number | null;
  message: string;
  created_at: string;
}

export interface PaginatedAuditLogs {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: AuditLogRecord[];
}

export interface Department {
  department_id: string;
  department_name: string;
  created_at: string;
  updated_at: string;
}

export interface Team {
  team_id: string;
  team_name: string;
  created_at: string;
  updated_at: string;
}

export interface DependencyStatus {
  status: 'healthy' | 'unavailable';
  critical: boolean;
  message?: string;
}

export interface ReadinessStatus {
  status: 'ready' | 'degraded' | 'not_ready';
  ready: boolean;
  dependencies: {
    database: DependencyStatus;
    milvus: DependencyStatus;
  };
}

export interface PoseStep {
  id: number;
  pose: 'FRONT' | 'LEFT' | 'RIGHT' | 'UP' | 'DOWN';
  label: string;
  instruction: string;
}

export const GUIDED_POSES: PoseStep[] = [
  { id: 1, pose: 'FRONT', label: 'Front (1/2)', instruction: 'Look straight at the camera' },
  { id: 2, pose: 'FRONT', label: 'Front (2/2)', instruction: 'Look straight at the camera' },
  { id: 3, pose: 'LEFT', label: 'Turn Left (1/2)', instruction: 'Turn your head slightly to the left' },
  { id: 4, pose: 'LEFT', label: 'Turn Left (2/2)', instruction: 'Turn your head slightly to the left' },
  { id: 5, pose: 'RIGHT', label: 'Turn Right (1/2)', instruction: 'Turn your head slightly to the right' },
  { id: 6, pose: 'RIGHT', label: 'Turn Right (2/2)', instruction: 'Turn your head slightly to the right' },
  { id: 7, pose: 'UP', label: 'Look Up (1/2)', instruction: 'Tilt your head slightly upward' },
  { id: 8, pose: 'UP', label: 'Look Up (2/2)', instruction: 'Tilt your head slightly upward' },
  { id: 9, pose: 'DOWN', label: 'Look Down (1/2)', instruction: 'Tilt your head slightly downward' },
  { id: 10, pose: 'DOWN', label: 'Look Down (2/2)', instruction: 'Tilt your head slightly downward' },
];

export interface CapturedSample {
  stepId: number;
  pose: string;
  dataUrl: string;
  blob?: Blob;
  capturedAt: string;
}
