from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AttendanceSummary:
    employee_id: str
    start_date: date | None
    end_date: date | None
    total_records: int
    present_days: int
    half_days: int
    in_progress_days: int
    total_working_hours: float
    absent_days: int = 0
    incomplete_days: int = 0
    total_working_days: int = 0
    attendance_percentage: float = 0.0