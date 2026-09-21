from datetime import date, time

from pydantic import BaseModel


class AttendanceRecordResponse(BaseModel):
    attendance_id: str
    employee_id: str
    attendance_date: date
    check_in: time | None
    check_out: time | None
    status: str
    working_hours: float | None


class AttendanceHistoryResponse(BaseModel):
    employee_id: str
    attendance: list[AttendanceRecordResponse]


class AttendanceSummaryResponse(BaseModel):
    employee_id: str
    start_date: date | None
    end_date: date | None
    total_records: int
    total_working_days: int = 0
    present_days: int
    half_days: int
    incomplete_days: int = 0
    absent_days: int = 0
    in_progress_days: int
    total_working_hours: float
    attendance_percentage: float = 0.0


class EndOfDayResponse(BaseModel):
    date: date
    present: int
    half_day: int
    incomplete: int
    absent: int
    total_processed: int
    message: str = "End-of-day attendance finalization completed successfully"


class DailyAttendanceItemResponse(BaseModel):
    employee_id: str
    name: str
    check_in: time | None
    check_out: time | None
    working_hours: float | None
    status: str


class DailyAttendanceReportResponse(BaseModel):
    attendance_date: date
    total_employees: int
    records: list[DailyAttendanceItemResponse]


class FaceVerificationResponse(BaseModel):
    success: bool
    status: str  # ACCESS_GRANTED, ALREADY_CHECKED_IN, ALREADY_CHECKED_OUT, UNRECOGNIZED_FACE, INACTIVE_EMPLOYEE, NO_FACE_DETECTED, ERROR
    message: str
    employee_id: str | None = None
    employee_name: str | None = None
    department: str | None = None
    job_title: str | None = None
    similarity: float | None = None
    scanner_type: str = "CHECK_IN"
    timestamp: str
    attendance_id: str | None = None


class ManualPunchRequest(BaseModel):
    employee_id: str
    scanner_type: str = "CHECK_IN"


class KioskStatsResponse(BaseModel):
    date: date
    total_scans_today: int
    successful_punches: int
    rejected_scans: int
    active_employees: int
    checked_in_count: int
    checked_out_count: int