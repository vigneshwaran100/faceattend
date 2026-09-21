from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class Attendance:
    attendance_id: str
    employee_id: str
    attendance_date: date
    check_in: time | None
    check_out: time | None
    status: str
    created_at: datetime
    updated_at: datetime